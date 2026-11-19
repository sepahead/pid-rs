"""Compile the twelve fault-tolerance theorems and report their transitive axioms.

Usage: check_lean.py <repository-root>

The study uses the built Mathlib imports of audit/formal/lean. The same Lake
route reports the executing Lean release, compiles the study and queries each
theorem. This check assumes trusted tools and stable local inputs.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TOOLCHAIN = "leanprover/lean4:v4.33.0"
LEAN_REVISION = "d8b18978322de05a8f3dba51ef03cf5461676c17"
STANDARD = {"propext", "Classical.choice", "Quot.sound"}
THEOREMS = tuple("FaultTolerantInformation." + name for name in (
    "mgwEvent_iff_tolerates", "disagree_comm", "tolerates_powersetCard_iff",
    "mgwEvent_powersetCard_iff", "mgwEvent_mono", "tolerates_mono",
    "eventMass_le_one", "forecast_ge_true_mass", "forecast_valid_under_tolerated_faults",
    "parity_ball_one", "parity_ball_two", "parity_class_size",
))


def run_lean(project, *arguments):
    result = subprocess.run(["lake", "env", "lean", *map(str, arguments)],
                            cwd=project, stdin=subprocess.DEVNULL, capture_output=True,
                            encoding="utf-8", check=False)
    if result.returncode != 0 or result.stderr:
        raise ValueError(f"Lean failed for {arguments}:\n{result.stdout}{result.stderr}")
    return result.stdout


def check_version(output):
    expected = (r"Lean \(version 4\.33\.0, [A-Za-z0-9_][A-Za-z0-9_.+-]*, commit "
                + LEAN_REVISION + r", Release\)\n")
    if not re.fullmatch(expected, output):
        raise ValueError(f"unexpected executing Lean release: {output!r}")


def receipt_commands(source):
    commands = [line for line in source.splitlines() if line.lstrip().startswith("#print")]
    expected = [f"#print axioms {name}" for name in THEOREMS]
    if commands != expected:
        raise ValueError("the axiom query differs from the twelve published theorem names and order")
    return commands


def parse_axioms(output):
    if not output.endswith("\n"):
        raise ValueError("incomplete Lean axiom output")
    messages = re.split(r"\n(?=')", output[:-1])
    if len(messages) != len(THEOREMS):
        raise ValueError(f"received {len(messages)} axiom records, expected {len(THEOREMS)}")
    basis = {}
    for name, message in zip(THEOREMS, messages):
        text = " ".join(message.split())
        if text == f"'{name}' does not depend on any axioms":
            basis[name] = set()
            continue
        row = re.fullmatch(re.escape(f"'{name}' depends on axioms: ") + r"\[([^\[\]]+)\]", text)
        if not row:
            raise ValueError(f"missing or malformed axiom record for {name}: {message!r}")
        assumptions = [part.strip() for part in row.group(1).split(",")]
        axioms = set(assumptions)
        if len(assumptions) != len(axioms) or not axioms <= STANDARD:
            raise ValueError(f"unexpected or repeated axiom for {name}: {assumptions!r}")
        basis[name] = axioms
    return basis


def main():
    project = Path(sys.argv[1]).resolve() / "audit/formal/lean"
    if (project / "lean-toolchain").read_text().strip() != TOOLCHAIN:
        raise ValueError("unexpected project toolchain pin")
    check_version(run_lean(project, "--version"))
    source = HERE / "lean/FaultTolerantInformation.lean"
    queries = receipt_commands((HERE / "lean/AxiomReceipt.lean").read_text())
    output = run_lean(project, source)
    if output:
        raise ValueError(f"expected a silent theorem compilation: {output!r}")
    with tempfile.TemporaryDirectory() as tmp:
        combined = Path(tmp) / "FaultTolerantInformationReceipt.lean"
        combined.write_text(source.read_text() + "\n" + "\n".join(queries) + "\n")
        basis = parse_axioms(run_lean(project, combined))
    print(f"Lean toolchain: {TOOLCHAIN}; source compiles without messages")
    for name, axioms in basis.items():
        print(f"{name}: {', '.join(sorted(axioms))}")
    print(f"PASS: {len(basis)} theorems use only propext, Classical.choice and Quot.sound")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(str(error))
