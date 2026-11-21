"""Invented clock, resource and object records for the prospective scheduling rules."""
from pathlib import Path


def check(schedule,assembly,location):
    passed={}
    def equal(name,actual,want):
        assembly.require(actual==want,"schedule test "+name+" differs")
        passed[name]={"observed":actual,"expected":want}
    def refused(name,fn,why):
        try:
            fn()
        except ValueError as error:
            assembly.require(why in str(error),"different refusal "+name)
            passed[name]={"refused":str(error)}
        else:
            raise ValueError("wrong scheduling acceptance "+name)
    begin=40.0
    first=schedule.window("W01",begin,begin+1500)
    second=schedule.window("W03",begin,begin+6900)
    third=schedule.window("W15",begin,begin+12300)
    equal("case-one-limit",(first["available_seconds"],first["deadline_s_since_campaign"]),(5400,6900))
    equal("case-two-limit",(second["available_seconds"],second["deadline_s_since_campaign"]),(5400,12300))
    equal("case-three-limit",(third["available_seconds"],third["deadline_s_since_campaign"]),(5400,17700))
    equal("three-windows-before-final-reserve",third["deadline_s_since_campaign"]+300,18000)
    late=schedule.window("W03",begin,begin+6904)
    equal("transition-overhead-preserves-later-window",late["available_seconds"],5396)
    equal("early-case-release",schedule.window("W03",begin,begin+2000)["available_seconds"],5400)
    refused("shared-setup-overrun",lambda:schedule.window("W01",begin,begin+1501),"shared setup")
    refused("invalid-case",lambda:schedule.window("W02",begin,begin+100),"case clock identity")
    refused("negative-offset",lambda:schedule.window("W03",begin,begin-1),"case clock identity")
    refused("time-nan",lambda:schedule.window("W03",begin,float("nan")),"case clock identity")
    refused("no-final-window",lambda:schedule.window("W15",begin,begin+17700),"no reserved time")
    valid={"post_group_absent":True,"residual_after_wait4":False,"stop":None,"exit":0,"max_observed_group_rss_bytes":1000,
           "direct_wait4_maxrss_bytes":1200,"retained_before_receipt_bytes":2000,"elapsed_seconds":4}
    def judge(row=valid,now=2000,storage=2000,failure=True,count=1):
        return schedule.continuation(first,now,storage,failure,row,count)
    equal("ordinary-mathematical-failure",judge(),"continue after ordinary failed case")
    equal("valid-complete",judge(failure=False),"continue after completed case")
    equal("cannot-accept-without-final-process",judge(None,failure=False,count=0),"stop completed case without final native command")
    equal("cannot-accept-failed-final-process",judge({**valid,"exit":1},failure=False),"stop inconsistent successful native result")
    equal("cannot-accept-hanging-group",judge({**valid,"post_group_absent":False},failure=False),"stop unverifiable or lingering native group")
    equal("same-size-storage-before-next-case",judge(storage=2**30),"stop shared retained bytes")
    equal("over-global-clock",judge(now=18000),"stop aggregate wall clock")
    equal("missing-verified-group",judge({**valid,"post_group_absent":False}),"stop unverifiable or lingering native group")
    equal("lingering-after-wait",judge({**valid,"residual_after_wait4":True}),"stop unverifiable or lingering native group")
    equal("missing-telemetry",judge({}),"stop unverifiable or lingering native group")
    equal("guard-detected-orphan",judge({**valid,"stop":"unreaped process-group member"}),"stop shared storage or native process")
    equal("guard-detected-storage",judge({**valid,"stop":"retained storage"}),"stop shared storage or native process")
    equal("unrecognized-reason",judge({**valid,"stop":"other"}),"stop unregistered native stop reason")
    positive_rss={**valid,"stop":"observed process-group RSS","max_observed_group_rss_bytes":2**32+4096}
    equal("genuine-observed-rss",judge(positive_rss),"continue after failed case memory bound")
    equal("unsubstantiated-rss",judge({**valid,"stop":"observed process-group RSS"}),"stop unclassified native resource boundary")
    equal("raw-cap-overrides-local-stop",judge({**positive_rss,"retained_before_receipt_bytes":2**30}),"stop shared retained bytes")
    equal("measured-direct-rss",judge({**valid,"stop":"final native resource limit","direct_wait4_maxrss_bytes":2**32+4096}),
          "continue after failed case memory bound")
    equal("subprocess-time",judge({**valid,"stop":"native or campaign time","elapsed_seconds":900.01}),
          "continue after failed per-command clock")
    equal("case-time",judge({**valid,"stop":"native or campaign time"},now=6900),"continue after failed case clock")
    equal("before-first-process-case-time",judge(None,now=6901,count=0),"continue after failed case clock")
    equal("unclassified-end-boundary",judge({**valid,"stop":"final native resource limit"}),"stop unclassified native resource boundary")
    refused("bad-bytes",lambda:judge(storage=True),"numerical transition")
    refused("bad-clock",lambda:judge(now=float("nan")),"numerical transition")
    root=location/"schedule-case-fixture";root.mkdir()
    sources=root/"sources";sources.mkdir()
    objects=root/"modules";objects.mkdir()
    (sources/"Toy.lean").write_text("def b := true\n")
    (objects/"Toy.olean").write_bytes(b"synthetic-custody-fixture")
    source=assembly.tree_hashes(sources);known=assembly.tree_hashes(objects)
    equal("installed-case-object",schedule.inventory(assembly,sources,objects,known,True,source)["known_objects"],known)
    (objects/"Refused.olean").write_bytes(b"retained rejected toy bytes")
    result=schedule.inventory(assembly,sources,objects,known,False,source)
    equal("quarantined-partial",list(result["additional_unaccepted_objects"]),["Refused.olean"])
    refused("accepted-extra-object",lambda:schedule.inventory(assembly,sources,objects,known,True,source),"unregistered successful")
    (objects/"Toy.olean").write_bytes(b"changed prior accepted bytes")
    refused("changed-earlier-known-object",lambda:schedule.inventory(assembly,sources,objects,known,False,source),"earlier compiled")
    (sources/"Toy.lean").write_text("def b := false\n")
    refused("changed-source",lambda:schedule.inventory(assembly,sources,None,{},False,source),"sources changed")
    return {"controls":passed,"count":len(passed),"original_evaluations":0,
            "scope":"Source-only transition fixtures. Actual Linux affinity and group cleanup require the separately registered hosted controls."}
