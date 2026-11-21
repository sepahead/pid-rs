"""Bound one serial Linux proof worker and adjudicate a case stop without changing its result."""

import math
import os

LIMITS={"campaign_seconds":18000,"subprocess_seconds":900,"retained_bytes":1073741824,"group_rss_bytes":4294967296}
CASES=("W01","W03","W15")
SCHEDULE={"workers":1,"allowed_logical_cpus":1,"shared_setup_seconds":1500,"case_seconds":5400,
          "final_reserve_seconds":300,"workflow_timeout_minutes":320,"case_order":list(CASES)}


def require(ok,why):
    if not ok:
        raise ValueError(why)


def number(v):
    return type(v) in (int,float) and math.isfinite(v)


def bind_one_cpu():
    before=sorted(os.sched_getaffinity(0))
    require(bool(before),"available Linux CPU")
    os.sched_setaffinity(0,{before[0]})
    after=sorted(os.sched_getaffinity(0))
    require(after==[before[0]],"one actual allowed logical CPU")
    return {"before":before,"during_native":after}


def check_configuration():
    require(SCHEDULE["shared_setup_seconds"]+len(CASES)*SCHEDULE["case_seconds"]+
            SCHEDULE["final_reserve_seconds"]==LIMITS["campaign_seconds"],"full clock reservation")
    require(SCHEDULE["workers"]==SCHEDULE["allowed_logical_cpus"]==1 and
            SCHEDULE["workflow_timeout_minutes"]*60>LIMITS["campaign_seconds"],"single worker and archive allowance")


def window(case,begin,now):
    check_configuration()
    require(case in CASES and number(now) and number(begin) and now>=begin,"case clock identity")
    position=CASES.index(case)
    if position==0:
        require(now<=begin+SCHEDULE["shared_setup_seconds"],"shared setup is over its reserved clock")
    following=(len(CASES)-position-1)*SCHEDULE["case_seconds"]
    latest=begin+LIMITS["campaign_seconds"]-SCHEDULE["final_reserve_seconds"]-following
    deadline=min(now+SCHEDULE["case_seconds"],latest)
    require(deadline>now,"no reserved time left for this case")
    return {"case":case,"start_s_since_campaign":now-begin,"deadline_s_since_campaign":deadline-begin,
            "available_seconds":deadline-now,"reserved_for_later_case_seconds":following,
            "final_seconds_reserved":SCHEDULE["final_reserve_seconds"]}


def continuation(case_clock,now_offset,storage,proof_failure,last_command,case_attempt_count,limits=LIMITS):
    """Return a scheduling disposition. A case stopped on a limit always remains a failed case."""
    require(number(now_offset) and type(storage) is int and storage>=0 and type(case_attempt_count) is int and
            case_attempt_count>=0 and case_clock["case"] in CASES,"numerical transition record")
    if storage>=limits["retained_bytes"]:
        return "stop shared retained bytes"
    if now_offset>=limits["campaign_seconds"]:
        return "stop aggregate wall clock"
    command=last_command if case_attempt_count else None
    if not proof_failure and command is None:
        return "stop completed case without final native command"
    if command is not None:
        if command.get("post_group_absent") is not True or command.get("residual_after_wait4") is not False:
            return "stop unverifiable or lingering native group"
        reason=command.get("stop")
        if not proof_failure:
            if reason is not None or command.get("exit")!=0:
                return "stop inconsistent successful native result"
            return "continue after completed case"
        if reason and ("storage" in reason or reason=="unreaped process-group member"):
            return "stop shared storage or native process"
        if reason not in {None,"observed process-group RSS","native or campaign time","final native resource limit"}:
            return "stop unregistered native stop reason"
        if reason:
            if command["retained_before_receipt_bytes"]>=limits["retained_bytes"]:
                return "stop shared retained bytes"
            if reason=="observed process-group RSS" and command["max_observed_group_rss_bytes"]<=limits["group_rss_bytes"]:
                return "stop unclassified native resource boundary"
            if (reason=="observed process-group RSS" or command["direct_wait4_maxrss_bytes"]>limits["group_rss_bytes"]):
                return "continue after failed case memory bound"
            if now_offset>=case_clock["deadline_s_since_campaign"]:
                return "continue after failed case clock"
            if command["elapsed_seconds"]>=limits["subprocess_seconds"]:
                return "continue after failed per-command clock"
            return "stop unclassified native resource boundary"
    if now_offset>=case_clock["deadline_s_since_campaign"]:
        return "continue after failed case clock"
    return "continue after ordinary failed case"


def inventory(assembly,source_dir,objects,known,complete,source_authority):
    """Keep partial failed outputs and ensure that no verified earlier input changes."""
    require(assembly.tree_hashes(source_dir)==source_authority,"case sources changed at transition")
    if objects is None:
        return {"sources":source_authority,"known_objects":{},"additional_unaccepted_objects":{}}
    require(objects.parent==source_dir.parent and objects.name=="modules" and
            all(p.is_file() and not p.is_symlink() for p in objects.iterdir()),"case-specific regular object directory")
    actual=assembly.tree_hashes(objects)
    require(all(actual.get(k)==h for k,h in known.items()),"earlier compiled object changed at transition")
    extras={k:v for k,v in actual.items() if k not in known}
    require(not complete or not extras,"unregistered successful case objects")
    return {"sources":source_authority,"known_objects":known,"additional_unaccepted_objects":extras}


def monitor_controls(assembly,resource,root,begin,env,home,chosen_cpu):
    """Check real group exit and the smaller, explicitly synthetic limit classifications on Linux."""
    import sys
    import time
    controls={}
    cases=(
        ("single-cpu",{},'import os; print(",".join(map(str,sorted(os.sched_getaffinity(0)))))',None),
        ("rss",{"group_rss_bytes":96*2**20},"import time; b=bytearray(144*2**20); time.sleep(2)","observed process-group RSS"),
        ("wall",{"subprocess_seconds":1},"import time; time.sleep(4)","native or campaign time"),
        ("next-worker",{},"import time; time.sleep(0.20)",None))
    for name,changes,code,expected in cases:
        path=root/("native-schedule-control-"+name);path.mkdir()
        limits=dict(LIMITS,**changes)
        meter=resource.Campaign(path,begin,dict(limits,campaign_seconds=SCHEDULE["shared_setup_seconds"]),env,assembly.digest)
        meter.stage="invented Linux worker and resource control"
        failed=False
        try:
            stream=meter.run(name,[sys.executable,"-I","-S","-B","-c",code],home,
                             mode="text" if name=="single-cpu" else "silent")
        except RuntimeError:
            failed=True
        require(len(meter.commands)==1,"complete synthetic process group")
        row=meter.commands[0]
        require(row["post_group_absent"] and not row["residual_after_wait4"] and row["stop"]==expected
                and failed==(expected is not None),"registered reason and verified cleanup")
        if name=="single-cpu":
            require(stream.read_text().strip()==str(chosen_cpu) and row["exit"]==0,"child inherited the single CPU")
        elif expected:
            require(row["exit"]==-9 and row["group_rss_sample_count"]>0,"actual resource refusal")
            if name=="rss":
                require(row["max_observed_group_rss_bytes"]>changes["group_rss_bytes"] and
                        row["direct_wait4_maxrss_bytes"]<LIMITS["group_rss_bytes"],"small RSS test envelope")
            decision=continuation({"case":"W01","deadline_s_since_campaign":LIMITS["campaign_seconds"]-300},
                                  time.monotonic()-begin,resource.retained_bytes(root.parent),True,row,1,limits)
            require(decision==("continue after failed case memory bound" if name=="rss" else
                                "continue after failed per-command clock"),"actual small stop classification")
        controls[name]=row
        assembly.write(root/"schedule-controls.json",controls)
    return controls
