"""Run one Linux process group at a time and retain bounded native observations."""

import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def record(path, value):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        json.dump(value,file,indent=2,sort_keys=True)
        file.write("\n")
    tmp.replace(path)

def retained_bytes(root):
    total = 0
    for directory, _, files in os.walk(root):
        for name in files:
            try:
                total += os.stat(os.path.join(directory, name), follow_symlinks=False).st_size
            except FileNotFoundError:
                # The compiler may atomically install an object between enumeration and stat.
                continue
    return total

def sample_group(group, page):
    resident = 0
    for ent in os.scandir("/proc"):
        if not ent.name.isdigit():
            continue
        try:
            # comm may itself contain spaces or parentheses. Field 5 is pgrp, 24 is rss.
            fields = Path(ent.path,"stat").read_bytes().rsplit(b")",1)[1].split()
            if int(fields[2]) == group:
                resident += max(0,int(fields[21])) * page
        except (FileNotFoundError,ProcessLookupError,PermissionError):
            continue
    return resident

def kill_group(pgid):
    try:
        os.killpg(pgid,signal.SIGKILL)
    except ProcessLookupError:
        pass

class Campaign:
    def __init__(self, root, begin, plan, env, digest):
        self.root = root
        self.begin = begin
        self.plan = plan
        self.env = env
        self.digest = digest
        self.page = os.sysconf("SC_PAGE_SIZE")
        self.commands = []
        self.stage = "provision"
        self.command_root = root / "commands"
        self.command_root.mkdir()

    def run(self, tag, argv, cwd, mode="silent", expected=0):
        now = time.monotonic()
        deadline = min(self.begin+self.plan["campaign_seconds"], now+self.plan["subprocess_seconds"])
        if now >= deadline or retained_bytes(self.root) >= self.plan["retained_bytes"]:
            raise RuntimeError("campaign limit before "+tag)
        step = self.command_root / tag
        step.mkdir()
        stdout = step/"stdout"
        stderr = step/"stderr"
        max_rss = self.plan["group_rss_bytes"]
        def limits():
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            cap = self.plan["retained_bytes"]
            resource.setrlimit(resource.RLIMIT_FSIZE,(cap,cap))
        peak = count = direct = 0
        stop = None
        with stdout.open("xb") as so, stderr.open("xb") as se:
            proc = subprocess.Popen([str(v) for v in argv],stdin=subprocess.DEVNULL,stdout=so,stderr=se,
                                    cwd=cwd,env=self.env,close_fds=True,start_new_session=True,preexec_fn=limits)
            last_budget_check = now
            try:
                while True:
                    pid, status, usage = os.wait4(proc.pid,os.WNOHANG)
                    if pid:
                        code = os.waitstatus_to_exitcode(status)
                        proc.returncode = code
                        direct = usage.ru_maxrss * 1024
                        break
                    peak = max(peak,sample_group(proc.pid,self.page))
                    count += 1
                    current = time.monotonic()
                    if peak > max_rss:
                        stop = "observed process-group RSS"
                    elif current >= deadline:
                        stop = "native or campaign time"
                    elif current - last_budget_check >= 0.2:
                        if retained_bytes(self.root) > self.plan["retained_bytes"]:
                            stop = "retained storage"
                        last_budget_check = current
                    if stop:
                        kill_group(proc.pid)
                    time.sleep(0.08)
            finally:
                if proc.returncode is None:
                    kill_group(proc.pid)
                    os.wait4(proc.pid,0)
                else:
                    # The stock commands must leave no process they created in this group.
                    try:
                        os.killpg(proc.pid,0)
                    except ProcessLookupError:
                        pass
                    else:
                        stop = stop or "unreaped process-group member"
                        kill_group(proc.pid)
        elapsed = time.monotonic() - now
        storage = retained_bytes(self.root)
        if direct > max_rss or storage > self.plan["retained_bytes"] or time.monotonic() > deadline:
            stop = stop or "final native resource limit"
        row = {"tag":tag,"stage":self.stage,"argv":[str(v) for v in argv],"exit":code,
               "elapsed_seconds":elapsed,"campaign_elapsed_seconds":time.monotonic()-self.begin,
               "group_rss_sample_count":count,"max_observed_group_rss_bytes":peak,
               "direct_wait4_maxrss_bytes":direct,"retained_before_receipt_bytes":storage,"stop":stop,
               "stdout_sha256":self.digest(stdout),"stderr_sha256":self.digest(stderr),
               "stdout_bytes":stdout.stat().st_size,"stderr_bytes":stderr.stat().st_size}
        self.commands.append(row)
        record(step/"result.json",row)
        if stop or code != expected or row["stderr_bytes"] or (mode == "silent" and row["stdout_bytes"]):
            raise RuntimeError("unexpected native outcome or diagnostics at "+tag)
        if mode != "silent" and not row["stdout_bytes"]:
            raise RuntimeError("missing expected stdout at "+tag)
        return stdout
