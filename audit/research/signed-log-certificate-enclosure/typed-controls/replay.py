"""Check a positive stock witness and two false endpoint equalities against the finite proof."""
import argparse
from hashlib import file_digest
import json
import os
from pathlib import Path
import shutil
import subprocess


HERE = Path(__file__).resolve().parent


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, required=True)
    parser.add_argument("--proof-output", type=Path, required=True,
                        help="output root from formal/replay.py")
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    toolchain = args.toolchain.resolve(strict=True)
    objects = (args.proof_output/"trial-v2/objects").resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(mode=0o700, exist_ok=False)
    formal = HERE.parent/"formal"
    pins = json.loads((formal/"fixed/RUNTIME.json").read_bytes())
    for name, expected in pins.items():
        require(digest(toolchain/name) == expected, name)
    expected_objects = json.loads((formal/"observed/v2.json").read_bytes())["objects"]
    for name, expected in expected_objects.items():
        require(digest(objects/name) == expected, name)
    cases = {"positive": "Witness", "wrong-power": "WrongPower", "wrong-zero": "WrongZero"}
    for name in cases.values():
        shutil.copyfile(HERE/(name + ".lean"), out/(name + ".lean"))
    env = {"HOME": str(out), "PATH": str(toolchain/"bin")+os.pathsep+os.defpath,
           "LEAN_PATH": str(out)+os.pathsep+str(objects), "LC_ALL": "C", "TZ": "UTC"}
    expected = json.loads((HERE/"RESULT.json").read_bytes())
    commands = []
    for label, name in cases.items():
        command = [toolchain/"bin/lean", "-j", "1", "-DwarningAsError=true", "-R", out]
        if label == "positive":
            command += ["-o", out/"Witness.olean"]
        commands.append((label, [*command, name + ".lean"]))
        if label == "positive":
            commands.append(("fresh", [toolchain/"bin/leanchecker", "--fresh", "Witness"]))
    result = {}
    for label, command in commands:
        proc = subprocess.run(command, cwd=out, env=env, capture_output=True, timeout=80)
        (out/(label + ".stdout")).write_bytes(proc.stdout)
        (out/(label + ".stderr")).write_bytes(proc.stderr)
        output = (proc.stdout+proc.stderr).decode().strip()
        result[label] = {"exit": proc.returncode, "native_text": output}
        require(result[label] == expected[label], label + " native result")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
