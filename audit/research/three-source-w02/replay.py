"""Check the archived W02 transcription and replay the later Lean proof with stock 4.34.1."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEAN = HERE / "lean"
ORIGINAL = ROOT / "audit/formal/finite-smt39-qualification-v1/raw/W02-exactly-18-distinct/generator.stdout.smt2"
MODULES = ("W02Semantics", "W02OriginalData", "W02Candidate", "W02Consumer", "W02AxiomReadback")
SYNTHETIC = ("W02SyntheticData", "W02SyntheticChecks", "W02SyntheticRejection")
NAMES = ("W02.sourceWellFormed", "W02.assertionsAtAllValuations", "W02.noSatisfyingValuation",
         "W02.sourceRanksHaveValuation", "W02Readback.valid", "W02Readback.evaluated",
         "W02Readback.hasNoModel", "W02Readback.hasAssignments")
STOCK_COMMIT = "5045d0056413266e57c625dcd7c365b10e377c52"
INPUT_SHA = "e503d85f5b6fe842c0900043283147f23055a4c5f4cf19e2914080cfbab692a0"
TYPED_SHA = "930417ff3a668fac765ac123b82bcccf6e797330eb59550600128e2ba35d78e5"
TERM_STREAM_SHA = "0db63ffe25564c68555504ea567e17e39234b466f7d395177825f924f9c64e82"
SEMANTICS_SHA = "e47fecb9c4221c594c623551fbc018037f827fe1418741a7393fda2027ccc6e3"

def load_module(stem):
    spec = importlib.util.spec_from_file_location(stem, HERE / (stem + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

writer = load_module("source_writer")
reader = load_module("source_reader")
literals = load_module("lean_literals")

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"

def parse_both(raw):
    tree, spans = writer.neutral(raw)
    other, other_spans = reader.read(raw)
    require(encoded(tree) == encoded(other), "different command trees")
    require(encoded(spans) == encoded(other_spans), "different source spans")
    require(spans and spans[0][1] == 0 and spans[-1][2] == len(raw)
            and all(a[2] == b[1] for a, b in zip(spans, spans[1:])), "source coverage")
    annotated = writer.typed_script(tree)
    require(encoded(annotated) == encoded(reader.checked_script(other)), "different typed commands")
    return tree, spans, annotated

def check_input(raw, lean_data, expected):
    require(len(raw) == expected["bytes"] == 43261 and digest(raw) == expected["sha256"] == INPUT_SHA,
            "archived input bytes")
    tree, spans, typed = parse_both(raw)
    for obj, field in ((tree, "neutral_sha256"), (spans, "spans_sha256"), (typed, "typed_sha256")):
        require(digest(encoded(obj)) == expected[field], field)
    require(expected["typed_sha256"] == TYPED_SHA and len(tree) == 89 and len(spans) == 29795, "file scope")
    require(collections.Counter(item[0] for item in typed) ==
            {"logic": 1, "option": 1, "constant": 25, "define": 57, "echo": 1,
             "assertion": 2, "check": 1, "exit": 1}, "command counts")
    prefix = "import W02Semantics\n\nset_option maxRecDepth 8192\nnamespace SmtW02\n\n"
    emitted = prefix + writer.lean_definition("originalScript", typed) + "\nend SmtW02\n"
    require(emitted.encode() == lean_data, "generated literal declaration")
    require(literals.matches(lean_data, encoded(typed)) == (89, TYPED_SHA), "independent Lean literal readback")

def check_rows(rows):
    require(tuple(row["name"] for row in rows) == NAMES, "ordered theorem roster")
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    for idx, row in enumerate(rows):
        require(row["kind"] == "theorem" and row["owner"] == ("W02Candidate" if idx < 4 else "W02Consumer"),
                "theorem and module")
        require(row["universe_parameters"] == [] and type(row["ordinary_import_trust"]) is int, "theorem header")
        require(set(row["axioms"]) <= allowed and row["axioms"] == sorted(set(row["axioms"])), "axiom set")
        for key in ("type_constructor_representation", "value_constructor_representation"):
            rep = row[key]
            require(isinstance(rep, str) and "Lean.Expr." in rep and
                    not any(x in rep for x in ("<opaque>", "<unknown>", "...", "…")), "full kernel expression")
        if idx >= 4:
            require(NAMES[idx - 4] in row["value_constants"], "typed use must refer to named proof")

def local_records():
    meta = json.loads((HERE / "observations.json").read_bytes())
    require(meta["stock_commit"] == STOCK_COMMIT, "stock revision")
    files = {file.name: digest(file.read_bytes()) for file in LEAN.glob("*.lean")}
    require(files == meta["source_sha256"] and files["W02Semantics.lean"] == SEMANTICS_SHA,
            "published Lean sources and frozen evaluator")
    check_input(ORIGINAL.read_bytes(), (LEAN / "W02OriginalData.lean").read_bytes(), meta["original"])
    data = (HERE / "declarations.jsonl").read_bytes()
    require(digest(data) == meta["term_file_sha256"], "published theorem records")
    lines = data.splitlines(keepends=True)
    require(digest(b"".join(b"W02_TERM " + line for line in lines)) ==
            meta["term_raw_sha256"] == TERM_STREAM_SHA, "original term stream")
    rows = [json.loads(line) for line in lines]
    check_rows(rows)
    require({row["name"]: row["axioms"] for row in rows} ==
            {name: sorted(deps) for name, deps in meta["axioms"].items()}, "recorded axiom reports")
    return meta, rows

def refused(operation, label):
    try:
        operation()
    except (ValueError, TypeError, KeyError):
        return
    raise ValueError("accepted altered input: " + label)

def controls(meta):
    cases = json.loads((HERE / "structural-controls.json").read_bytes())["fixtures"]
    counts = collections.Counter()
    for case in cases:
        raw = case["source"].encode("ascii")
        require(len(raw) == case["bytes"] and digest(raw) == case["sha256"], case["id"])
        if case["kind"] == "valid":
            parse_both(raw)
            counts["accepted"] += 1
        else:
            for read in (lambda: writer.typed_script(writer.neutral(raw)[0]),
                         lambda: reader.checked_script(reader.read(raw)[0])):
                refused(read, case["id"])
            counts["refused"] += 1
    require(counts == {"accepted": 13, "refused": 12}, "synthetic fixture roster")
    raw = ORIGINAL.read_bytes()
    lean_data = (LEAN / "W02OriginalData.lean").read_bytes()
    tree = encoded(reader.checked_script(reader.read(raw)[0]))
    changes = ((b'(Cmd.constant "a" (Ty.bv 7))', b'(Cmd.constant "a" (Ty.bv 4))'),
               (b'(Term.numeral 18)', b'(Term.numeral 19)'),
               (b'(Cmd.constant "tau"', b'(Cmd.constant "sigma"'),
               (b'(Ty.bool) "distinct"', b'(Ty.bool) "="'),
               (b'(Term.bits 7 127)', b'(Term.bits 6 127)'),
               (b'("u", (Ty.bv 3))', b'("p", (Ty.bv 3))'),
               (b'"extract" [0, 0]', b'"extract" [1, 0]'),
               (b'  (Cmd.check),\n', b''), (b'(Cmd.exit)', b'(Cmd.logic "ALL")'),
               (b'\nend SmtW02\n', b'\nextra\nend SmtW02\n'),
               (b'import W02Semantics', b'import W02Altered'),
               (b'W02-exactly-18-distinct', b'W03-exactly-18-distinct'))
    for before, after in changes:
        require(before in lean_data, "transcription control preimage")
        refused(lambda: literals.matches(lean_data.replace(before, after, 1), tree), before.decode())
    refused(lambda: check_input(raw + b" ", lean_data, meta["original"]), "source byte")
    rows = [json.loads(line) for line in (HERE / "declarations.jsonl").read_bytes().splitlines()]
    for field, value in (("kind", "definition"), ("name", "wrong"), ("owner", "W02Candidate"),
                         ("axioms", ["unknown"]), ("value_constants", []),
                         ("type_constructor_representation", "..."),
                         ("value_constructor_representation", "<opaque>"),
                         ("universe_parameters", ["wrong"]), ("ordinary_import_trust", True)):
        altered = [dict(row) for row in rows]
        altered[4][field] = value
        refused(lambda: check_rows(altered), "observer field " + field)
    refused(lambda: check_rows(rows[:-1]), "missing final theorem")
    print("89 commands and 29,795 lexical spans; 13 accepted and 12 rejected synthetic inputs; 12 altered Lean transcriptions rejected")

def native(lean_bin, meta, expected):
    lean = lean_bin / "lean"
    checker = lean_bin / "leanchecker"
    with tempfile.TemporaryDirectory(prefix="three-source-w02-") as name:
        work = Path(name)
        src = work / "sources"
        mods = work / "modules"
        mods.mkdir()
        shutil.copytree(LEAN, src)
        env = {"PATH": str(lean_bin) + os.pathsep + os.defpath, "LEAN_PATH": str(mods), "LC_ALL":"C",
               "TZ":"UTC", "TMPDIR":str(work)}

        def run(*args):
            result = subprocess.run(list(map(str, args)), cwd=src, env=env, capture_output=True, timeout=900)
            if result.returncode or result.stderr:
                raise RuntimeError(f"{args[0]} failed ({result.returncode}): "
                                   + (result.stdout + result.stderr).decode(errors="replace")[-3000:])
            return result.stdout

        require(run(lean, "--githash").decode().strip() == STOCK_COMMIT, "executing Lean revision")
        version = run(lean, "--version").decode().strip()
        require(version.startswith("Lean (version 4.34.1,"), "executing release")
        for module in (*MODULES, *SYNTHETIC):
            stream = run(lean, "-R", src, "-o", mods / (module + ".olean"), src / (module + ".lean"))
            if module == "W02AxiomReadback":
                actual = {}
                for line in stream.decode().splitlines():
                    match = re.fullmatch(r"'([^']+)' (?:depends on axioms: \[([^\]]+)\]|does not depend on any axioms)", line)
                    require(match and match[1] not in actual, "native axiom row")
                    actual[match[1]] = [] if match[2] is None else match[2].split(", ")
                require(tuple(actual) == NAMES and actual == meta["axioms"], "native axioms")
            else:
                require(not stream, "unexpected compiler diagnostics for " + module)
        for module in (*MODULES, *SYNTHETIC):
            require(not run(checker, "--fresh", module), "unexpected fresh replay diagnostics")
        stream = run(lean, "-R", src, src / "W02Inspect.lean").splitlines()
        require(len(stream) == len(NAMES) and all(line.startswith(b"W02_TERM ") for line in stream),
                "native observer stream")
        actual_rows = [json.loads(line.removeprefix(b"W02_TERM ")) for line in stream]
        check_rows(actual_rows)
        require(actual_rows == expected, "native statements, proof expressions or dependencies changed")
        print(version)
        print("Eight compiled modules and eight fresh replays passed; eight complete named type and proof records matched.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-sources", action="store_true", help="check the original input, published term record and structural controls")
    mode.add_argument("--lean-bin", type=Path, help="bin directory of an official Lean 4.34.1 installation")
    args = parser.parse_args()
    meta, rows = local_records()
    controls(meta)
    if args.lean_bin:
        native(args.lean_bin.resolve(), meta, rows)

if __name__ == "__main__":
    main()
