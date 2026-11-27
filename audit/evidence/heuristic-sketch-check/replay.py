"""Replay the retained finite field or run the same source-bound Rust client offline."""
from __future__ import annotations
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

def read_scores(data: Path) -> bytes:
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-O")
    command += ["-I", "-S", "-B", str(HERE / "check_results.py"), str(data)]
    return subprocess.check_output(command)

def compile_and_run(work: Path):
    target = work / "target"
    environment = dict(os.environ, CARGO_NET_OFFLINE="true", CARGO_BUILD_JOBS="1",
                       CARGO_TARGET_DIR=str(target), CARGO_INCREMENTAL="0", CARGO_PROFILE_DEV_DEBUG="0")
    subprocess.run(["cargo", "build", "--offline", "--locked", "--no-default-features",
                    "--features", "experimental-heuristics", "-p", "pid-core", "--lib"],
                   cwd=ROOT, env=environment, check=True)
    deps = target / "debug/deps"
    libraries = list(deps.glob("libpid_core-*.rlib"))
    if len(libraries) != 1:
        raise RuntimeError(f"expected one fresh pid-core library, received {len(libraries)}")
    binary = work / ("probe.exe" if os.name == "nt" else "probe")
    subprocess.run(["rustc", "--edition=2021", "--extern", "pid_core="+str(libraries[0]),
                    "-L", "dependency="+str(deps), str(HERE / "probe.rs"), "-o", str(binary)],
                   cwd=ROOT, env=environment, check=True)
    raw = work / "native.tsv"
    with raw.open("wb") as out:
        subprocess.run([str(binary)], cwd=work, stdout=out, check=True)
    return read_scores(raw)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--recorded", action="store_true")
    choice.add_argument("--build", action="store_true")
    args = parser.parse_args()
    recorded = (HERE/"RESULT.json").read_bytes()
    if read_scores(HERE / "native.tsv") != recorded:
        raise ValueError("retained native file and checked result differ")
    result = recorded
    if args.build:
        with tempfile.TemporaryDirectory(prefix="pid-heuristic-sketch-") as tmp:
            result = compile_and_run(Path(tmp))
    fields = json.loads(result)
    print(json.dumps({"mode":"fresh" if args.build else "recorded",
                      "endpoint_calls":len(fields["endpoints"]),
                      "additional_prefixes":len(fields["stream_prefixes"]),
                      "typed_input_refusals":len(fields["refusals"]),
                      "stream_mutations_refused":len(fields["active_mutations"]),
                      "scientific_json_sha256":hashlib.sha256(result).hexdigest(),
                      "byte_match_with_retained_result":result==recorded},sort_keys=True))
if __name__=="__main__":
    main()
