"""Record native cgroup settings before and after the fixed qualification command."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


CAP = 4 << 30
FIELD = "4773c2363ced0c069cf0bb3cc17baae51ca94f9599be7fbf4656a589a21a8067"


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
    require(
        group["uid"] == 0
        and 0 < int(values["memory.max"]) <= CAP
        and int(values["memory.swap.max"]) == 0
        and 0 < quota <= period,
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
    require(re.fullmatch(r"W03Q-[0-9]+-1", args.run_id), "provider run ID")
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
