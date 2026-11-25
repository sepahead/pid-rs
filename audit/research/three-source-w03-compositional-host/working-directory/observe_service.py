"""Record native cgroup settings before and after the fixed qualification command."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


CAP = 4 << 30
FIELD = "a1f23f4805c2de8dcbe8551b7bf0fb2ce606b0eb510582a824c60565c5e54978"


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read_group():
    names = [
        s[3:]
        for s in Path("/proc/self/cgroup").read_text().splitlines()
        if s.startswith("0::")
    ]
    require(len(names) == 1, "cgroup v2")
    root = Path("/sys/fs/cgroup")
    group = next(
        (
            p
            for p in (root / names[0].lstrip("/"), root)
            if (p / "cgroup.procs").is_file()
            and str(os.getpid()) in (p / "cgroup.procs").read_text().split()
        ),
        None,
    )
    require(group is not None, "current service process in reported group")
    values = {
        name: (group / name).read_text().strip()
        for name in ("memory.max", "memory.swap.max", "cpu.max", "memory.current")
    }
    peak = group / "memory.peak"
    return {
        "name": names[0],
        "limits": values,
        "peak_bytes": int(peak.read_text()) if peak.exists() else None,
        "uid": os.geteuid(),
        "pid": os.getpid(),
    }


def limits(group):
    values = group["limits"]
    quota, period = map(int, values["cpu.max"].split())
    cap = int(values["memory.max"])
    current = int(values["memory.current"])
    peak = group["peak_bytes"]
    require(
        type(group["uid"]) is int and group["uid"] == 0
        and type(group["pid"]) is int and group["pid"] > 0
        and quota == period and period > 0
        and 0 < cap <= CAP and values["memory.swap.max"] == "0"
        and type(peak) is int and 0 <= current <= peak <= cap,
        "live hard limits",
    )


def save(filename, group):
    with filename.open("x") as stream:
        json.dump(group, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    require(
        root.owner() == "root" and root.stat().st_mode & 0o022 == 0,
        "operator input ownership",
    )
    require(re.fullmatch(r"W03D-[0-9]+-1", args.run_id), "provider run ID")
    before = read_group()
    save(root / "host-limit-before.json", before)
    limits(before)
    try:
        result = subprocess.run(
            [
                "/usr/bin/python3",
                "-I",
                "-S",
                "-B",
                root / "field/judge.py",
                "qualify",
                "--field-sha",
                FIELD,
                "--archive",
                root / "lean.tar.zst",
                "--store",
                root / "stock",
                "--out",
                root / "evidence",
                "--run-id",
                args.run_id,
            ]
        )
    finally:
        after = read_group()
        save(root / "host-limit-after.json", after)
        limits(after)
        require(
            before["name"] == after["name"] and before["pid"] == after["pid"],
            "service identity changed",
        )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
