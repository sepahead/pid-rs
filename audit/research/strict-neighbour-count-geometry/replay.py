"""Check the strict neighbour-count Lean proof with stock Lean 4.34.1, one process at a time."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

STUDY = Path(__file__).resolve().parent
REVISION = "5045d0056413266e57c625dcd7c365b10e377c52"
AXIOMS = {
    "inner_pair": ("propext", "Quot.sound"),
    "counts": ("propext", "Classical.choice", "Quot.sound"),
    "necessary": ("propext", "Classical.choice", "Quot.sound"),
    "constructed": ("propext", "Classical.choice", "Quot.sound"),
    "attainable_iff": ("propext", "Classical.choice", "Quot.sound"),
}
FALSE_TEXT = (
    "Contradiction.lean:4:43: error: Tactic `decide` proved that the proposition\n"
    "  Realizes [{ left := 1, right := 4, target := 2 }] 2 1 1 1\nis false\n"
)


def require(condition, label):
    if not condition:
        raise ValueError(label)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_check(folder, hashes):
    for name, expected in hashes.items():
        path = folder / name
        require(path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == expected,
                "source identity " + name)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--toolchain", type=Path, required=True, help="root of the unmodified Lean 4.34.1 release")
    cli.add_argument("--evidence", type=Path, help="new directory for source, stock objects and exact streams")
    cli.add_argument("--self-test", action="store_true", help="also exercise the source-witness rejection")
    args = cli.parse_args()
    tc = args.toolchain.resolve()
    lean, checker = (tc / "bin" / n for n in ("lean", "leanchecker"))
    require(lean.is_file() and checker.is_file(), "stock compiler and fresh checker required")
    pins = json.loads((STUDY / "proof-inputs.json").read_bytes())
    source_check(STUDY, pins)
    if args.evidence:
        out = args.evidence.resolve()
        out.mkdir(exist_ok=False)
        run(tc, lean, checker, out, args.self_test, pins)
    else:
        with tempfile.TemporaryDirectory(prefix="neighbour-count-replay-") as tmp:
            run(tc, lean, checker, Path(tmp), args.self_test, pins)


def run(tc, lean, checker, out, test, pins):
    src = out / "source"
    obj = out / "objects"
    src.mkdir()
    obj.mkdir()
    for mod in ("Model", "Proof", "Observer", "Contradiction", "FullDisplay"):
        shutil.copyfile(STUDY / "lean" / (mod + ".lean"), src / (mod + ".lean"))
    if test:
        scratch = out / "bad-source"
        scratch.mkdir()
        (scratch / "Proof.lean").write_bytes((src / "Proof.lean").read_bytes() + b"\n")
        try:
            source_check(scratch, {"Proof.lean": pins["lean/Proof.lean"]})
        except ValueError as error:
            require(str(error) == "source identity Proof.lean", "wrong hostile source refusal")
        else:
            raise ValueError("changed proof bytes accepted")
    env = {"PATH": str(tc / "bin") + os.pathsep + os.defpath, "LC_ALL": "C", "LANG": "C",
           "LEAN_PATH": str(obj), "LEAN_NUM_THREADS": "1"}

    def invoke(label, argv, expected=0):
        result = subprocess.run(list(map(str, argv)), cwd=src, env=env, capture_output=True, timeout=90)
        for suffix, data in ((".stdout", result.stdout), (".stderr", result.stderr)):
            (out / (label + suffix)).write_bytes(data)
        require(result.returncode == expected, f"{label} exit {result.returncode}")
        return result.stdout + result.stderr

    version = invoke("version", [lean, "--version"]).decode()
    require("4.34.1" in version and REVISION in version, "stock version and source revision")
    compiler = [lean, "-j", "1", "-DwarningAsError=true", "-R", src]
    for name in ("Model", "Proof", "Observer", "FullDisplay"):
        stream = invoke(name + "-compile", [*compiler, "-o", obj / (name + ".olean"), name + ".lean"])
        require((obj / (name + ".olean")).is_file(), "missing " + name)
        if name in ("Observer", "FullDisplay"):
            reference = "proof-display.txt" if name == "Observer" else "expanded-proof-display.txt"
            require(stream == (STUDY / reference).read_bytes(), "printed declarations and axioms")
            if name == "FullDisplay":
                require(all(mark not in stream.decode() for mark in ("⋯", "…")), "expanded display omits a part")
            for nm, axs in AXIOMS.items():
                line = f"'W7.{nm}' depends on axioms: [{', '.join(axs)}]\n"
                require(stream.count(line.encode()) == 1 and b"\ntheorem W7." + nm.encode() + b" :" in stream,
                        "actual theorem or axioms " + nm)
        else:
            require(not stream, "unexpected compiler diagnostic in " + name)
        require(not invoke(name + "-fresh", [checker, "--fresh", name]), "fresh replay diagnostic " + name)
    bad = invoke("false-count", [*compiler, "Contradiction.lean"], 1)
    require(bad == FALSE_TEXT.encode(), "false count must fail for its exact proposition")
    report = {"source_revision": REVISION, "axioms": AXIOMS, "named_theorems": 5, "exact_row_controls": 8,
              "false_proposition_rejected": True, "source_mutation_rejected": test,
              "compiler": digest(lean.read_bytes()), "fresh_checker": digest(checker.read_bytes()),
              "expanded_display": digest((STUDY / "expanded-proof-display.txt").read_bytes())}
    raw = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    (out / "result.json").write_text(raw, encoding="utf-8")
    print(raw, end="")


if __name__ == "__main__":
    main()
