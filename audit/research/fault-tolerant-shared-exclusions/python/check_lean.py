"""Compile the fault-tolerance Lean file and record its axiom receipt.

Usage: check_lean.py <repository-root>

The Lean file lives outside the frozen project in audit/formal/lean. This script checks that the
project pins Lean 4.33.0, compiles lean/FaultTolerantInformation.lean with `lake env lean` from that
project directory (which only reads its built libraries), then compiles a temporary copy with the
`#print axioms` commands of lean/AxiomReceipt.lean appended. Every listed theorem must depend only
on the standard axioms propext, Classical.choice and Quot.sound. The receipt is printed on standard
output. The script exits with status 1 on any compiler error, missing theorem or other axiom.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def main():
    root = Path(sys.argv[1]).resolve()
    project = root / "audit/formal/lean"
    toolchain = (project / "lean-toolchain").read_text().strip()
    if toolchain != "leanprover/lean4:v4.33.0":
        raise SystemExit(f"unexpected Lean toolchain: {toolchain}")
    source = HERE / "lean/FaultTolerantInformation.lean"
    receipt = (HERE / "lean/AxiomReceipt.lean").read_text()
    prints = [line for line in receipt.splitlines() if line.startswith("#print axioms ")]
    names = [line.split()[-1] for line in prints]

    compiled = subprocess.run(["lake", "env", "lean", str(source)], cwd=project,
                              capture_output=True, text=True)
    if compiled.returncode != 0 or compiled.stdout.strip() or compiled.stderr.strip():
        raise SystemExit(f"Lean compile failed:\n{compiled.stdout}{compiled.stderr}")

    with tempfile.TemporaryDirectory() as tmp:
        combined = Path(tmp) / "FaultTolerantInformationReceipt.lean"
        combined.write_text(source.read_text() + "\n" + "\n".join(prints) + "\n")
        result = subprocess.run(["lake", "env", "lean", str(combined)], cwd=project,
                                capture_output=True, text=True)
    if result.returncode != 0 or result.stderr.strip():
        raise SystemExit(f"Lean receipt failed:\n{result.stdout}{result.stderr}")

    messages = re.split(r"\n(?='FaultTolerantInformation\.)", result.stdout.strip())
    seen = {}
    for message in messages:
        match = re.match(r"'(FaultTolerantInformation\.[\w.]+)' depends on axioms: \[(.*)\]",
                         " ".join(message.split()))
        if not match:
            raise SystemExit(f"unexpected receipt line: {message!r}")
        axioms = {a.strip() for a in match.group(2).split(",") if a.strip()}
        seen[match.group(1)] = axioms
    missing = [n for n in names if n not in seen]
    extra = {n: a - STANDARD for n, a in seen.items() if a - STANDARD}
    print(f"Lean toolchain: {toolchain}; source compiles without messages")
    for name in names:
        print(f"{name}: {', '.join(sorted(seen.get(name, set())))}")
    if missing or extra:
        print(f"FAIL: missing {missing}; nonstandard axioms {extra}")
        return 1
    print(f"PASS: {len(names)} theorems use only propext, Classical.choice and Quot.sound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
