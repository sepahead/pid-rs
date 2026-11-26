"""Run the exact numerical calculations against their full recorded outputs."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE/"formal/fixed/arithmetic.py"
EXPECTED = {
    "scalar_width": "1449f415de2b49bed0f4e1af31c67ab99a61a1a558647d9ee35f47afd84980b5",
    "order": "5786b59020d291e82f82e68f1ad62834a683dc4d8de71951eb01ac05e0bf93ad",
    "counted": "e4064d202075824beb40756cc516523217d26804cf254375e45fe0bcc7c93e04",
    "padding": "fe54800b7d7f11eac6ed132a2fd13e0ded7407367787251f9301c5b9cd1cb2b2",
    "outer": "9bd9c8f9a1ca4e29cbafb1ece10fb00f164fa823aa107721f99612c151d729e3",
    "tail": "6cf31a303b7f57b282a626e6c5baf0fe627e35e4bd565e363a339b105103e8f0",
    "trace": "419716f1bd406a9397feec5ecc8e82cb63e6004b474c0cb8fc7936a1b9e54c3e",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(len(sys.argv) == 1, "usage: python3 check.py")
    require(sha256(ORIGINAL.read_bytes()).hexdigest()
            == "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2", "six-table source")
    launcher = [sys.executable, "-I", "-S", "-B"]
    if sys.flags.optimize:
        launcher.append("-O")
    summary = {}
    for name, digest in EXPECTED.items():
        command = [*launcher, HERE/"numerical"/(name + ".py")]
        if name != "tail":
            command.append(ORIGINAL)
        result = subprocess.run(command, capture_output=True, check=True, timeout=90)
        reference = (HERE/"numerical"/(name + ".json")).read_bytes()
        require(sha256(reference).hexdigest() == digest, name + " original reference")
        require(result.stdout == reference, name + " complete original output")
        require(not result.stderr, name + " standard error")
        summary[name] = digest
    print(json.dumps(summary, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
