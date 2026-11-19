"""Check the published Lean-receipt reader on ordinary synthetic output strings."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("study_axioms", HERE / "check_lean.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def rejected(function, value):
    try:
        function(value)
    except ValueError:
        return
    raise RuntimeError(f"{function.__name__} unexpectedly accepted altered input")


def main():
    version = f"Lean (version 4.33.0, aarch64-linux-gnu, commit {reader.LEAN_REVISION}, Release)\n"
    reader.check_version(version)
    for changed in (version.replace("4.33.0", "4.33.1"),
                    version.replace(reader.LEAN_REVISION, "a" * 40),
                    version.replace("Release", "Debug"), version + "additional output\n"):
        rejected(reader.check_version, changed)

    commands = (HERE.parent / "lean/AxiomReceipt.lean").read_text()
    if len(reader.receipt_commands(commands)) != 12:
        raise RuntimeError("the published query roster must have twelve distinct records")
    first = "#print axioms " + reader.THEOREMS[0]
    rejected(reader.receipt_commands, commands.replace(first, ""))
    rejected(reader.receipt_commands, commands + first + "\n")

    rows = [f"'{name}' depends on axioms: [propext,\n Classical.choice, Quot.sound]"
            for name in reader.THEOREMS]
    rows[0] = f"'{reader.THEOREMS[0]}' does not depend on any axioms"
    output = "\n".join(rows) + "\n"
    expected = {name: set(reader.STANDARD) for name in reader.THEOREMS}
    expected[reader.THEOREMS[0]] = set()
    if reader.parse_axioms(output) != expected:
        raise RuntimeError("wrapped and empty axiom lists must preserve the complete roster")

    variants = (rows[:-1], [*rows[:-1], rows[0]], [rows[1], rows[0], *rows[2:]],
                [rows[0].replace(reader.THEOREMS[0], "Unrelated.export"), *rows[1:]],
                [*rows[:-1], rows[-1] + " unrelated trailing text"],
                [*rows[:-1], rows[-1].replace("Quot.sound", "extraAssumption")],
                [*rows[:-1], rows[-1].replace("Quot.sound", "")],
                [*rows[:-1], rows[-1].replace("Quot.sound", "propext")],
                [*rows[:-1], rows[-1][:-1]])
    for rows_variant in variants:
        rejected(reader.parse_axioms, "\n".join(rows_variant) + "\n")
    rejected(reader.parse_axioms, output[:-1])
    print("PASS: exact Lean release, every published query, and complete ordered axiom records")


if __name__ == "__main__":
    main()
