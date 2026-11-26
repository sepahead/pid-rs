"""Replay the original six fixed obligations with the byte-identified Apple arm64 release."""
import argparse
from hashlib import file_digest
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    tools = args.toolchain.resolve(strict=True)
    out = args.out.resolve()
    require(tools.is_dir(), "Lean release directory")
    out.mkdir(mode=0o700, exist_ok=False)
    original = package / "contract"
    require(digest(original / "FROZEN.json") == "97ae5508036093f371d3a24a166f9a734834e8ef138e5edfd860e95bcadc090b", "fixed source identity")
    for name, value in json.loads((original / "FROZEN.json").read_bytes()).items():
        require(digest(original / name) == value, name)
    dest = out / "fresh"
    command = [sys.executable, "-I", "-S", "-B"]
    if sys.flags.optimize:
        command.append("-O")
    subprocess.run([*command, original / "judge.py", package / "candidate/r02.json", dest, tools], check=True, timeout=300)
    result = json.loads((dest / "RESULT.json").read_bytes())
    reference = json.loads((package / "observed/r02/RESULT.json").read_bytes())
    for field in ("success", "reason", "payload", "axioms", "sources", "objects"):
        require(result[field] == reference[field], field)
    require(result["fixed"] == digest(original / "FROZEN.json"), "current replay predicate")
    require(reference["fixed"] == digest(package / "original-contract-hashes.json"), "original predicate")
    observed = [{k: v for k, v in event.items() if k != "argv"} for event in result["commands"]]
    require(observed == reference["commands"], "native output or status")
    for name, value in result["sources"].items():
        require(digest(package / name) == value, name)
    extra_sources = package / "additional"
    auxiliary = extra_sources / "IndependentExamples.lean"
    require(digest(auxiliary) == "95544a5fee1b6e321588af518da0fb1af7ffdec1e2d01d56172866a0f0b160fa", "independent control source")
    extra = out / "additional"
    extra.mkdir()
    shutil.copyfile(auxiliary, extra / auxiliary.name)
    control_object = extra / "IndependentExamples.olean"
    environment = {"HOME": str(extra), "LC_ALL": "C", "TZ": "UTC",
                   "PATH": str(tools / "bin") + os.pathsep + os.defpath,
                   "LEAN_PATH": str(extra) + os.pathsep + str(dest / "objects")}
    controls = [
        [tools / "bin/lean", "-j", "1", "-DwarningAsError=true", "-R", extra, "-o", control_object, auxiliary.name],
        [tools / "bin/leanchecker", "--fresh", "IndependentExamples"],
    ]
    for index, cmd in enumerate(controls, 1):
        completed = subprocess.run(cmd, cwd=extra, env=environment, capture_output=True, timeout=80)
        (extra / f"command-{index}.stdout").write_bytes(completed.stdout)
        (extra / f"command-{index}.stderr").write_bytes(completed.stderr)
        require(completed.returncode == 0 and not completed.stdout and not completed.stderr, "independent native control")
    require(digest(control_object) == "4f3e4643e93d360fff8f9e25c23f37f610c263694a75719d0875f9bdf68fe461", "independent control object")
    print("Six named propositions, three stock replays, twenty observer examples and one rejected equation.")
    print("Additional five-outcome controls compiled and passed a separate stock replay.")

if __name__ == "__main__":
    main()
