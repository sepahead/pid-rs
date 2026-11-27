"""Check the original finite regression or repeat its corrected public Rust call."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(check, message):
    if not check:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_cases(cases, raw):
    import runpy
    reader = runpy.run_path(str(HERE / "read.py"))
    return reader["rows"](cases.decode(), raw.decode())


def recorded():
    cases = (HERE / "cases.txt").read_bytes()
    generated = subprocess.check_output([sys.executable, "-B", str(HERE / "make_cases.py")])
    require(cases == generated, "registered source cases")
    reference = json.loads((HERE / "INDEPENDENT.json").read_bytes())
    for name, key, failed in (("before", "original", 228), ("after", "candidate", 0)):
        raw = (HERE / (name + ".stdout")).read_bytes()
        require(sha(raw) == reference[key + "_raw"], "native " + name)
        result = read_cases(cases, raw)
        exact = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
        require(exact == (HERE / (name + ".json")).read_bytes(), "rational " + name)
        require(sha(exact) == reference[key + "_two_mode_exact_receiver"], "bound " + name)
        require(result["failed_fields"] == failed and result["success"] == (failed == 0),
                "recorded disposition " + name)
    true_four = subprocess.check_output([sys.executable, "-B", str(HERE / "four_point_reference.py")])
    require(true_four == (HERE / "four-point.json").read_bytes(), "four-point comparison")

    lines = (HERE / "after.stdout").read_text().splitlines()
    key = "down0-012"
    index = next(i for i, line in enumerate(lines) if line.split("\t")[0] == key)
    row = lines[index].split("\t")
    outputs = row[3].split()
    outputs[3] = "0000000000000000"
    row[3] = " ".join(outputs)
    lines[index] = "\t".join(row)
    altered = read_cases(cases, ("\n".join(lines) + "\n").encode())
    require(altered["failed_fields"] == 1 and key in altered["inputs"] and
            "pair_sd" in altered["inputs"][key]["outside"], "wrong zero spread escaped")
    try:
        read_cases(cases, ("\n".join(lines[1:]) + "\n").encode())
    except (KeyError, ValueError):
        pass
    else:
        raise ValueError("missing native input escaped")


def compile_and_read():
    with tempfile.TemporaryDirectory(prefix="pid-geometry-spread-") as staging:
        target = Path(staging)
        env = dict(os.environ, CARGO_NET_OFFLINE="true", CARGO_BUILD_JOBS="1",
                   CARGO_INCREMENTAL="0", CARGO_PROFILE_DEV_DEBUG="0",
                   CARGO_TARGET_DIR=str(target / "target"))
        command = ["cargo", "build", "--offline", "--locked", "--no-default-features",
                   "-p", "pid-core", "--lib", "--message-format=json"]
        output = subprocess.check_output(command, cwd=ROOT, env=env, text=True)
        libraries = []
        for line in output.splitlines():
            message = json.loads(line)
            if message.get("reason") == "compiler-artifact" and message["target"]["name"] == "pid_core":
                libraries.extend(Path(path) for path in message["filenames"] if path.endswith(".rlib"))
        require(len(libraries) == 1, "compiled pid-core library")
        deps = target / "target/debug/deps"
        client = target / "moments-client"
        subprocess.run(["rustc", "--edition=2021", "--extern", "pid_core=" + str(libraries[0]),
                        "-L", "dependency=" + str(deps), str(HERE / "public_moments.rs"),
                        "-o", str(client)], cwd=ROOT, env=env, check=True)
        cases = (HERE / "cases.txt").read_bytes()
        raw = subprocess.check_output([str(client)], input=cases)
        result = read_cases(cases, raw)
        require(result["success"] and result["failed_fields"] == 0, "fresh Rust numerical return")
        require(raw == (HERE / "after.stdout").read_bytes(), "fresh native output bytes")


def main():
    args = argparse.ArgumentParser(description=__doc__)
    mode = args.add_mutually_exclusive_group(required=True)
    mode.add_argument("--recorded", action="store_true")
    mode.add_argument("--build", action="store_true")
    options = args.parse_args()
    recorded()
    if options.build:
        compile_and_read()
    print("102 inputs, 990 numerical fields, 12 refusals, 228 original discrepancies, 0 corrected discrepancies")


if __name__ == "__main__":
    main()
