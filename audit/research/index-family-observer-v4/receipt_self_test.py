"""Use passive ordinary file metadata, model command records and the exact archived earlier failure."""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("parser_model",HERE/"parser_self_test.py")
T=importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
V,S,C,R=T.V,T.S,T.V.C,T.R


@contextmanager
def changed(path, value):
    original=path.read_bytes()
    try:
        path.write_bytes(T.encoded(value))
        yield
    finally:
        path.write_bytes(original)


def tests():
    refused=[]; admitted=[]
    def reject(label, function, expected):
        try:
            function()
        except ValueError as error:
            S.require(expected in str(error),label+" refused for another reason: "+str(error))
            refused.append(label)
        else:
            raise ValueError("accepted incorrect description: "+label)

    def header(mode=stat.S_IFREG, size=1, name="plain.txt", dos=0):
        item=zipfile.ZipInfo(name)
        item.create_system=3; item.external_attr=((mode|0o600)<<16)|dos; item.file_size=size
        return item
    for mode in (0,stat.S_IFREG):
        S.require(C.headers([header(mode)])==1,"ordinary positive in-memory header")
    admitted.extend(["regular header","unspecified header"])
    for label,item in (("directory type for plain filename",header(stat.S_IFDIR)),
                       ("directory attribute for plain filename",header(dos=0x10)),
                       ("directory entry with regular type",header(name="folder/"))):
        reject(label,lambda:C.headers([item]),"ordinary regular or unspecified")
    reject("repeated ordinary descriptor",lambda:C.headers([header(),header()]),"unique ordinary")
    reject("over limit expanded header",lambda:C.headers([header(size=(1<<30)+1)]),"expanded ZIP ceiling")
    S.require(C.headers([header(size=1<<30)])==1<<30,"bounded metadata without allocation")
    admitted.append("expanded byte limit in metadata without allocating its contents")

    archive=R/S.PRIOR/"native-evidence.zip"
    S.require(S.info(archive)=={"bytes":534167,"sha256":S.HISTORICAL},"prior ZIP identity")
    with zipfile.ZipFile(archive) as z:
        items=z.infolist()
        S.require(len(items)==58 and C.headers(items)==sum(x.file_size for x in items),"58 ordinary archived files")
    old=S.load(R/S.PRIOR/"check.py")
    negative,observations=old.read(R,archive)
    prior_refused=old.self_test(observations)
    S.require(len(prior_refused)==15 and negative["resource_stop_bytes"]==4438499328 and negative["expanded_files"]==58,
              "earlier native failure")
    admitted.append("authentic 58-member earlier archive with its original negative interpretation")

    reg=S.read(R/S.REGISTER)
    source=S.from_payload(R,(R/S.PRIOR/"submitted.json").read_bytes(),reg)
    with tempfile.TemporaryDirectory(prefix="ordinary-report-checks-") as w:
        w=Path(w); model=w/"complete"; model.mkdir()
        full,launch,_,_=T.fixture(model,reg,source)
        good=lambda:V.complete(full,R,launch,reg,source)
        raw=S.read(full/"terminal.json"); tags=list(S.schedule(R)); stages=S.read(full/"stages.json")
        def vary_record(label,which,patch,fragment,call=good,where=full):
            f=where/"commands"/which/"result.json"; value=S.read(f);value.update(patch)
            with changed(f,value):reject(label,call,fragment)
        vary_record("negative implied first command start",tags[0],{"elapsed_seconds":1.5},"native interval")
        vary_record("second native interval overlaps first",tags[1],{"elapsed_seconds":1.75},"native interval")
        vary_record("native end later than wrapper return",tags[2],{"campaign_elapsed_seconds":3.3},"native interval")
        vary_record("boolean output count posing as zero",tags[0],{"stdout_bytes":False},"integer receipt")
        vary_record("invented sampler count",tags[0],{"group_rss_sample_count":500},"sampler metadata")
        vary_record("nonzero group peak without a sample",tags[0],{"group_rss_sample_count":0},"sampler metadata")
        vary_record("impossible direct RSS unit",tags[0],{"direct_wait4_maxrss_bytes":512},"sampler metadata")
        vary_record("unknown native result metadata",tags[0],{"unregistered_field":"test"},"complete native receipt")
        vary_record("receipt records less storage than its streams",tags[1],{"retained_before_receipt_bytes":1},"stream sizes")
        vary_record("reported evidence cannot contain its already present source",tags[0],{"retained_before_receipt_bytes":128},"already present source")
        vary_record("relative release path",tags[0],{"argv":["/usr/bin/tar","--zstd","--no-same-owner","-xf","release","-C","/FIXTURE/temp/index-observer-v4-stock"]},"canonical absolute")
        vary_record("wrong release filename under the same root",tags[0],{"argv":["/usr/bin/tar","--zstd","--no-same-owner","-xf","/FIXTURE/other","-C","/FIXTURE/temp/index-observer-v4-stock"]},"fixed release")
        tail=list(S.read(full/"commands"/S.POST/"result.json")["argv"])
        changed_python=tail.copy();changed_python[0]="/OTHER/python3"
        changed_script=tail.copy();changed_script[4]="/OTHER/checkout/"+S.PACKAGE+"/frames.py"
        vary_record("same-named interpreter outside launch identity",S.POST,{"argv":changed_python},"same-capped")
        vary_record("same suffix outside the launch checkout",S.POST,{"argv":changed_script},"same-capped")
        different=["/usr/bin/tar","--zstd","--no-same-owner","-xf","/OTHER/index-observer-v4-release.tar.zst","-C","/OTHER/index-observer-v4-stock"]
        vary_record("same release names outside launch temp",tags[0],{"argv":different},"fixed release")
        for label,i,key,new,fragment in (("overlapping wrapper intervals",1,"begin",0.9,"serial dispatch"),
                                            ("dispatch ends after the terminal",103,"end",200,"serial dispatch"),
                                            ("dispatch name genuinely out of sequence",1,"tag",tags[2],"ordered dispatch"),
                                            ("clock bracket omits a required endpoint",1,"[remove]",None,"ordered dispatch")):
            value=deepcopy(raw); row=value["dispatch_intervals"][i]
            if key=="[remove]":del row["begin"]
            else:row[key]=new
            with changed(full/"terminal.json",value):reject(label,good,fragment)
        file0=full/"commands"/tags[0]/"result.json"; row=S.read(file0);row.update(group_rss_sample_count=0,max_observed_group_rss_bytes=0)
        with changed(file0,row):
            last=full/"commands"/S.POST/"result.json"; value=S.read(last)
            value["retained_before_receipt_bytes"]=T.fixture_storage_before_last(full,S.POST)
            with changed(last,value):
                S.require(good()["terms"]==170,"zero-sample direct-only path")
        admitted.append("quick process with zero samples and separately measured direct peak")

        def prefix(name, commands, phase, stage, *, bad=False, prepared=False, incomplete=False):
            dest=w/name/"result";dest.mkdir(parents=True)
            shutil.copyfile(full.parent/"launch.json",dest.parent/"launch.json")
            shutil.copytree(full/"sources",dest/"sources");(dest/"objects").mkdir()
            shutil.copyfile(full/"registration.json",dest/"registration.json")
            for i,tag in enumerate(tags[:commands]):
                d=dest/"commands"/tag; d.mkdir(parents=True)
                if incomplete and i==commands-1:
                    (d/"stdout").write_bytes(b"");(d/"stderr").write_bytes(b"")
                    continue
                for a in ("stdout","stderr","result.json"):shutil.copyfile(full/"commands"/tag/a,d/a)
                if bad and i==commands-1:
                    r=S.read(d/"result.json");r["exit"]=2
                    (d/"result.json").write_bytes(T.encoded(r))
                elif tag.startswith(("compile-","inspect-")):
                    q=tag.split("-",1)[1]+".olean";shutil.copyfile(full/"objects"/q,dest/"objects"/q)
            finished=sum(V.is_unit(t) for t in tags[:commands])
            if finished or prepared:S.write(dest/"stages.json",stages[:finished+int(prepared)])
            if commands==104 and not incomplete:
                for a in ("joined-terms.stdout","term-shards.json","observed.json"):shutil.copyfile(full/a,dest/a)
            err=("RuntimeError: unexpected native outcome or diagnostics at "+stage) if bad else "ValueError: modeled boundary check"
            terminal={"status":S.FAILED,"attempt":S.ATTEMPT,"original_evaluations":0,"stage":stage,"phase":phase,"error":err,
                      "elapsed_seconds":105,"dispatch_intervals":raw["dispatch_intervals"][:commands]}
            S.write(dest/"terminal.json",terminal)
            if commands and phase in ("invoke","after-command","final") and not incomplete:
                tag=tags[commands-1]; path=dest/"commands"/tag/"result.json"; row=S.read(path)
                row["retained_before_receipt_bytes"]=T.fixture_storage_before_last(dest,tag)
                path.write_bytes(T.encoded(row))
            return dest,lambda:V.failure(dest,R,reg,source)

        f,negative_read=prefix("early",1,"invoke",tags[0],bad=True)
        accepted=negative_read()
        S.require(accepted["assigned_theorems"]==[] and accepted["observed_command_prefix"][0]["exit"]==2,"realistic descriptive prefix")
        admitted.append("failed first command with matched arguments and empty assignment")
        t=S.read(f/"terminal.json")
        for label,patch,fragment in (("distant theorem from a terminal label",{"stage":"inspect-IndexTermsPart085"},"adjacent recorded dispatch"),
                                    ("failure cause contradicts recorded invocation",{"error":"RuntimeError: absent unrelated proof"},"reason and native receipt"),
                                    ("false final-stage label",{"stage":C.FINAL,"phase":"final"},"full dispatch prefix"),
                                    ("boolean original count",{"original_evaluations":False},"disclosed failed terminal"),
                                    ("empty cause",{"error":""},"disclosed failed terminal"),
                                    ("extra failed status claim",{"accepted_checks":170},"disclosed failed terminal")):
            with changed(f/"terminal.json",{**t,**patch}):reject(label,negative_read,fragment)
        fs=f/"stages.json"
        try:
            S.write(fs,[{"module":"earlier"},{"module":"unentered"}]);reject("two unentered stage records",negative_read,"surplus or absent")
        finally:fs.unlink()
        vary_record("bogus failed extraction argument",tags[0],{"argv":["absent"]},"stock extraction",negative_read,f)
        vary_record("bogus memory-stop description",tags[0],{"stop":"observed process-group RSS"},"unsupported process-group RSS",negative_read,f)
        vary_record("bogus resource reason",tags[0],{"stop":"unknown reason"},"native process metadata",negative_read,f)
        vary_record("bogus cleanup claimed without a retained child",tags[0],{"stop":"unreaped process-group member"},"unsupported cleanup",negative_read,f)
        vary_record("terminal hides observed unclean group",tags[0],{"post_group_absent":False},"unreported resource",negative_read,f)
        q=f/"objects/Unobserved.olean";q.write_bytes(b"ordinary fixture")
        try:reject("unexplained object under the earliest failure",negative_read,"additional object")
        finally:q.unlink()
        f2,two=prefix("two",2,"invoke",tags[1],bad=True)
        vary_record("bogus arguments in a preceding successful command",tags[0],{"argv":["absent"]},"stock extraction",two,f2)
        vary_record("descending command end times in failed prefix",tags[1],{"campaign_elapsed_seconds":0.75},"native interval",two,f2)
        vary_record("implied time overlap in failed prefix",tags[1],{"elapsed_seconds":1.75},"native interval",two,f2)
        partial,look=prefix("prepared",3,"before-command",tags[3],prepared=True)
        record=look()
        S.require(record["additional_precommand_stages"]==1 and not record["assigned_theorems"],"one exact precommand stage")
        admitted.append("one corroborated prepared stage before any native receipt")
        partial_stages=S.read(partial/"stages.json");partial_stages[0]["module"]="IndexInline"
        with changed(partial/"stages.json",partial_stages):reject("wrong next prepared stage",look,"prior objects")
        other,look=prefix("absent",4,"invoke",tags[3],incomplete=True)
        current=look()
        S.require(current["observed_command_prefix"][-1]["receipt"]=="absent" and not current["assigned_theorems"],"last invocation has no native receipt")
        admitted.append("opened stream files without the final native receipt")
        shutil.rmtree(other/"commands"/tags[3])
        S.require(look()["observed_command_prefix"][-1]["retained_streams"]=={},"attempt entering provider may predate folder")
        admitted.append("callee can stop before it creates command files")
        setup=w/"pre-setup"/"result";setup.mkdir(parents=True)
        shutil.copyfile(full.parent/"launch.json",setup.parent/"launch.json")
        empty={"status":S.FAILED,"attempt":S.ATTEMPT,"original_evaluations":0,"stage":C.SETUP,"phase":"setup",
               "error":"ValueError: modeled setup prerequisite","elapsed_seconds":0.25,"dispatch_intervals":[]}
        S.write(setup/"terminal.json",empty)
        setup_facts=V.failure(setup,R,reg,source)
        S.require(setup_facts["observed_command_prefix"]==[] and setup_facts["source_files_verified"]==0,"zero-command setup")
        admitted.append("setup prerequisite fails before registration copy or a command")
        bad_version,read_version=prefix("version-text",2,"after-command",tags[1])
        vf=bad_version/"commands"/tags[1];alternate=b"Other observed version string\n"
        (vf/"stdout").write_bytes(alternate)
        vr=S.read(vf/"result.json");vr.update(stdout_bytes=len(alternate),stdout_sha256=S.digest_bytes(alternate))
        vr["retained_before_receipt_bytes"]=T.fixture_storage_before_last(bad_version,tags[1])
        (vf/"result.json").write_bytes(T.encoded(vr))
        S.require(read_version()["observed_command_prefix"][-1]["stock_identity_matches"] is False,"wrong output retained as a failed after-command check")
        admitted.append("completed version command followed by a failed stock text check")
        possible,look=prefix("unqualified-object",4,"invoke",tags[3],bad=True)
        incomplete_object=possible/"objects/IndexSpec.olean";incomplete_object.write_bytes(b"test bytes")
        authored=possible/"commands"/tags[3]/"result.json";pr=S.read(authored)
        pr["retained_before_receipt_bytes"]=T.fixture_storage_before_last(possible,tags[3])
        authored.write_bytes(T.encoded(pr))
        found=look()
        S.require(found["additional_observed_object_files"]==["IndexSpec.olean"] and not found["successful_objects_linked"],
                  "failed compiler can leave its current object")
        admitted.append("owning failed compile leaves an explicitly unqualified object")
        final,look=prefix("final",104,"final",C.FINAL)
        report=look()
        S.require(len(report["observed_command_prefix"])==104 and report["permitted_original_issues"]==0 and
                  report["assigned_theorems"]==[],"separate final validation failure")
        admitted.append("final validation error after all 104 expected command outcomes")
        fin=S.read(final/"terminal.json")
        with changed(final/"terminal.json",{**fin,"phase":"invoke","stage":S.POST}):
            reject("successful command mislabeled failed invocation",look,"successful receipt labeled")
        physical=T.fixture_storage_before_last(full,S.POST)
        actual=S.read(full/"commands"/S.POST/"result.json")["retained_before_receipt_bytes"]
        S.require(actual==physical==good()["final_storage"]["recomputed_from_closed_files_bytes"],
                  "full positive storage measured at provider write point")
        admitted.append("exact final measured storage equals all 507 pre-receipt file lengths")
        for label,value in (("one-byte final storage shortfall",physical-1),("one-byte final storage surplus",physical+1),
                            ("exclude closed term frame metadata",physical-(full/"term-shards.json").stat().st_size),
                            ("expense ceiling substituted for measured final file lengths",1<<30)):
            vary_record(label,S.POST,{"retained_before_receipt_bytes":value},"storage reading differs")
        rf=f/"commands"/tags[0]/"result.json"; baseline=S.read(rf); terminal=S.read(f/"terminal.json")
        def reason_for(cause,fields,bracket=None,campaign_elapsed=105):
            row={**baseline,**fields,"stop":cause}
            term=deepcopy(terminal)
            term["elapsed_seconds"]=campaign_elapsed
            if bracket is not None:term["dispatch_intervals"][0].update(begin=bracket[0],end=bracket[1])
            with changed(f/"terminal.json",term), changed(rf,row):
                return negative_read()["observed_command_prefix"][0]["stop_evidence"]
        reject("final limit excluded by all three resource conditions",
               lambda:reason_for("final native resource limit",{}),"no possible resource condition")
        reject("command deadline reached exactly, no strict final excess",
               lambda:reason_for("final native resource limit",{"campaign_elapsed_seconds":900.0},(0,900.75),901),
               "no possible resource condition")
        reject("campaign deadline reached exactly, no strict final excess",
               lambda:reason_for("final native resource limit",{"campaign_elapsed_seconds":2700.0},(2699.0,2700.1),2700.25),
               "no possible resource condition")
        supported=reason_for("final native resource limit",{"direct_wait4_maxrss_bytes":(4<<30)+1024})
        S.require(supported["measured_excess"]==["direct process peak"],"actual direct reading")
        admitted.append("reported final limit supported by the direct peak")
        supported=reason_for("final native resource limit",{"elapsed_seconds":900.1,"campaign_elapsed_seconds":901.0},(0.25,901.5),902)
        S.require(supported["measured_excess"]==["elapsed native duration"],"observed duration")
        admitted.append("reported final limit supported by measured duration")
        for label,end,bracket,final_end in (("unobserved final scan can cross the command deadline",900.5,(0,900.75),901),
                                             ("unobserved final scan can cross the campaign deadline",2700.5,(2699,2700.75),2701)):
            reading=reason_for("final native resource limit",{"campaign_elapsed_seconds":end},bracket,final_end)
            S.require(reading["measured_excess"]==[] and reading["time_may_have_crossed"] is True,label)
            admitted.append(label)
        actual_storage=baseline["retained_before_receipt_bytes"]
        vary_record("one-byte difference at last complete failed receipt",tags[0],
                    {"retained_before_receipt_bytes":actual_storage+1},"storage reading differs",negative_read,f)
        reject("final storage excess incompatible with retained failure bytes",
               lambda:reason_for("final native resource limit",{"retained_before_receipt_bytes":(1<<30)+1}),"storage reading differs")
        sampled=reason_for("retained storage",{})
        S.require("peak size was not retained" in sampled["interpretation"],"transient observation label")
        admitted.append("sampled storage report with no claimed peak measurement")
        shutil.copyfile(full/"registration.json",setup/"registration.json");(setup/"sources").mkdir()
        registered_name=sorted(source)[len(source)//2];(setup/"sources"/registered_name).write_bytes(source[registered_name])
        order_free=V.failure(setup,R,reg,dict(reversed(list(source.items()))))
        S.require(order_free==V.failure(setup,R,reg,source) and order_free["retained_source_files"]=={registered_name:S.info_bytes(source[registered_name])},
                  "partial setup verifies exact bytes in any mapping order")
        admitted.append("identical partial source set under opposite enumeration orders")
        extra=setup/"sources"/"Extra.lean";extra.write_bytes(b"ordinary test data")
        try:reject("unregistered source in unordered partial setup",lambda:V.failure(setup,R,reg,source),"failed prefix source changed")
        finally:extra.unlink()
        regcopy=setup/"registration.json";regcopy.unlink()
        reject("partial setup source without registration",lambda:V.failure(setup,R,reg,source),"registration before any retained source")
        status=S.read(f/"terminal.json")
        with changed(f/"terminal.json",{**status,"elapsed_seconds":float("nan")}):reject("nonfinite failed campaign time",negative_read,"finite clock")
    return {"complete_positive_final_bytes":actual,"scope":"in-memory ordinary metadata, modeled command records, authentic previous bounded failure",
            "native_executions":0,"admitted":admitted,"rejected":refused,"actual_earlier_archive":negative,
            "earlier_reader_rejections":prior_refused}


if __name__=="__main__":
    print(json.dumps(tests(),sort_keys=True))
