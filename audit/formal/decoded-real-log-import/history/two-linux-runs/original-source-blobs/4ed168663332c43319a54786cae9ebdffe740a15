"""Measure one Linux process group at a time and retain its native streams."""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

GIB = 2**30
RSS_LIMIT = 4 * GIB
DISK_GROWTH_LIMIT = 18 * GIB
MIN_FREE = GIB
STREAM_LIMIT = 16 * 2**20
TOTAL_SECONDS = 75 * 60
STEP_SECONDS = 600
SETUP_SECONDS = 1200


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    temp.replace(path)


def group_rss(group):
    pages = 0
    for directory in Path("/proc").iterdir():
        if not directory.name.isdecimal():
            continue
        try:
            fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group:
                pages += max(0, int(fields[21]))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return pages * os.sysconf("SC_PAGE_SIZE")


class Run:
    def __init__(self, evidence, work, records):
        self.output = evidence
        self.work = work
        self.records = records
        self.start = time.monotonic()
        self.initial_free = shutil.disk_usage(work).free

    def limits(self, current_rss, start, seconds, output_bytes):
        now = time.monotonic()
        free = shutil.disk_usage(self.work).free
        if current_rss > RSS_LIMIT:
            return "sampled process group exceeded 4 GiB"
        if free < MIN_FREE or self.initial_free - free > DISK_GROWTH_LIMIT:
            return "scratch volume exceeded storage limit"
        if now - self.start > TOTAL_SECONDS or now - start > seconds:
            return "wall time exceeded"
        if output_bytes > STREAM_LIMIT:
            return "native stream exceeded limit"
        return None

    def command(self, name, argv, directory, environment, *, secs=STEP_SECONDS, expected=0):
        require(name not in self.records, "duplicate command " + name)
        start = time.monotonic()
        require(not self.limits(0, start, secs, 0), "resources unavailable before " + name)
        out = self.output / (name + ".stdout")
        err = self.output / (name + ".stderr")
        argv = [str(a) for a in argv]
        record = {"argv": argv, "cwd": str(directory), "status": "running", "limit_seconds": secs}
        self.records[name] = record
        save(self.output / "COMMANDS.json", self.records)
        peak = samples = 0
        reason = None
        with out.open("xb") as stdout, err.open("xb") as stderr:
            proc = subprocess.Popen(argv, cwd=directory, env=environment, stdout=stdout, stderr=stderr,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
            try:
                while True:
                    rss = group_rss(proc.pid)
                    peak = max(peak, rss)
                    samples += 1
                    reason = self.limits(rss, start, secs, max(out.stat().st_size, err.stat().st_size))
                    if reason or proc.poll() is not None:
                        break
                    time.sleep(0.10)
            finally:
                # A surviving member is never part of a subsequent command.
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                code = proc.wait()
        record.update(status="returned", returncode=code, reason=reason, elapsed_s=time.monotonic()-start,
                      peak_sampled_group_rss=peak, samples=samples, free_bytes=shutil.disk_usage(self.work).free,
                      stdout_sha256=digest(out), stderr_sha256=digest(err))
        save(self.output / "COMMANDS.json", self.records)
        require(reason is None and code == expected, f"{name} returned {code}, {reason or 'native status'}")
        return out.read_bytes(), err.read_bytes()
