#!/usr/bin/env python3
"""Recompile the four exact modules, replay their loaded safe declarations and inspect the named objects."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
EXTENSIONS = (".olean", ".olean.server", ".olean.private", ".ir", ".ir.sig")
OWNED = ("Contract", "CountRaw", "AlphabetCounts", "CountEvidence")
STANDARD = {"Classical.choice", "Quot.sound", "propext"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(items):
    result = {}
    for key, value in items:
        require(key not in result, f"duplicate JSON field {key}")
        result[key] = value
    return result


def decode(data):
    return json.loads(data, object_pairs_hook=unique)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    require(path.is_file() and path.resolve(strict=True) == path, f"expected regular file {path}")
    with path.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        return [size, hashlib.file_digest(stream, "sha256").hexdigest()]


def original():
    meta = decode((HERE / "observations.json").read_bytes())
    declarations = (HERE / "declarations.txt").read_bytes()
    compressed = (HERE / "original-disk-inputs.json.gz").read_bytes()
    require(digest(compressed) == meta["disk_projection_sha256"], "original disk inventory digest")
    payload = gzip.decompress(compressed)
    require(digest(payload) == meta["disk_projection_uncompressed_sha256"], "original disk inventory content")
    require(len(declarations) == meta["source_path_independent_declaration_bytes"] and
            digest(declarations) == meta["declarations_sha256"], "original declarations changed")
    require(list(meta["ordered_modules"]) == list(OWNED), "unexpected module order")
    sources = {p.name: p.read_bytes() for p in (HERE / "lean").iterdir()}
    require(set(sources) == {m + ".lean" for m in OWNED} and
            {n: digest(data) for n, data in sources.items()} == meta["source_sha256"], "four source hashes")
    return meta, declarations, decode(payload), sources


def invoke(command, *, cwd, env, timeout):
    start = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        result = subprocess.run(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=out,
                                stderr=err, timeout=timeout, check=False)
        require(out.tell() <= 32 * 1024**2 and err.tell() <= 1024**2, "unexpected stream size")
        out.seek(0)
        err.seek(0)
        stdout, stderr = out.read(), err.read()
    if result.returncode or stderr:
        detail = (stdout[:2200] + stderr[:2200]).decode(errors="replace")
        raise ValueError(f"{Path(command[0]).name} exited {result.returncode} or emitted stderr: {detail}")
    return stdout, round(time.monotonic() - start, 3)


def roots_and_versions(lean_bin, mathlib, meta, env):
    lean, checker = lean_bin / "lean", lean_bin / "leanchecker"
    require(lean.is_file() and checker.is_file(), "stock lean and leanchecker are required")
    out, _ = invoke([lean, "--githash"], cwd=mathlib, env=env, timeout=30)
    require(out.decode().strip() == meta["toolchain"]["revision"], "wrong observed Lean revision")
    out, _ = invoke([lean, "--version"], cwd=mathlib, env=env, timeout=30)
    version = out.decode().strip()
    expected = "Lean \\(version " + re.escape(meta["toolchain"]["version"]) + ", [A-Za-z0-9_.+\\-]+, commit " + meta["toolchain"]["revision"] + ", Release\\)"
    require(re.fullmatch(expected, version), "wrong stock release identity")
    spec = meta["mathlib"]
    require(identity(mathlib / "lake-manifest.json")[1] == spec["lake_manifest_sha256"], "Mathlib manifest")
    roots = {}
    deps = {"mathlib": (mathlib, spec["revision"])}
    deps.update({n: (mathlib / ".lake/packages" / n, v) for n, v in spec["dependencies"].items()})
    for name, (directory, required) in deps.items():
        git_root, _ = invoke(["git", "rev-parse", "--show-toplevel"], cwd=directory, env=env, timeout=30)
        require(Path(git_root.decode().strip()).resolve(strict=True) == directory, f"package root {name}")
        head, _ = invoke(["git", "rev-parse", "HEAD"], cwd=directory, env=env, timeout=30)
        require(head.decode().strip() == required, f"package revision {name}")
        library = directory / ".lake/build/lib/lean"
        if library.is_dir():
            roots[name] = library.resolve(strict=True)
    require("mathlib" in roots, "prebuilt Mathlib required")
    roots["lean"] = (lean_bin.parent / "lib/lean").resolve(strict=True)
    require(roots["lean"].is_dir(), "missing stock library")
    return roots, version


def inventory(roots):
    rows = {}
    for label, root in roots.items():
        for file in root.rglob("*"):
            if file.name.endswith(EXTENSIONS):
                key = label + "/" + file.relative_to(root).as_posix()
                rows[key] = identity(file)
    return rows


def resolve_observed(path, scratch, roots):
    require(type(path) is str and path, "nonempty region or module path required")
    supplied = Path(path)
    resolved = (supplied if supplied.is_absolute() else scratch / supplied).resolve(strict=True)
    matches = [(label, root) for label, root in roots.items() if resolved.is_relative_to(root)]
    require(len(matches) == 1, "reported path outside or ambiguous within the selected roots")
    label, root = matches[0]
    return label + "/" + resolved.relative_to(root).as_posix(), resolved


def check_imports(report, baseline, meta, scratch, roots, known, products):
    require(report["schema"] == "count22-exact-objects-helper-v3" and report["main_module"] == "CountEvidence"
            and report["lean_githash"] == meta["toolchain"]["revision"] and
            report["lean_version"] == meta["toolchain"]["version"], "unexpected native import report")
    require(report["direct_imports"] == meta["original_direct_imports"], "direct imports differ")
    require(type(report["header_trust_level"]) is int, "missing integer trust observation")
    sources = {**roots, "project": scratch}
    available = {**known, **products}
    modules, required_paths = [], set()
    for row in report["modules"]:
        expected = {"module", "olean", "meta", "exported", "all", "has_data"}
        require(set(row) == expected and type(row["module"]) is str and row["has_data"] is True and
                all(type(row[x]) is bool for x in ("meta", "exported", "all")), "malformed module report")
        local, _ = resolve_observed(row["olean"], scratch, sources)
        modules.append([row["module"], local, row["meta"], row["exported"], row["all"], row["has_data"]])
        required_paths.add(local)
    require(modules == baseline["loaded_modules"], "effective module names, owners or flags differ")
    seen = set()
    mapped = 0
    for row in report["regions"]:
        require(set(row) == {"path", "mapped_bytes", "memory_mapped"} and
                type(row["memory_mapped"]) is bool and type(row["mapped_bytes"]) is int and
                row["mapped_bytes"] > 0, "invalid region metadata")
        local, path = resolve_observed(row["path"], scratch, sources)
        require(local not in seen and local in available, "duplicate or unbound reported region")
        id_current = identity(path)
        require(row["mapped_bytes"] == id_current[0] and id_current == available[local],
                "reported length or captured disk hash differs")
        seen.add(local)
        mapped += int(row["memory_mapped"])
    require(required_paths <= seen, "a reported module has no OLean region")
    return {"modules": len(modules), "reported_regions": len(seen), "file_mapped_regions": mapped,
            "non_file_mapped_regions": len(seen) - mapped, "ordinary_trust_header": report["header_trust_level"]}


def dependency_roster(declarations):
    expect = []
    for line in declarations.splitlines():
        tag, raw = line.split(b" ", 1)
        row = decode(raw)
        if tag == b"COUNT22_HELPER":
            expect.extend([(row["candidate_helper"], row["axioms"]), (row["raw_helper"], row["raw_axioms"])])
        elif tag == b"COUNT22_DEFINITION":
            expect.extend([(row["definition"], row["axioms"]), (row["raw_definition"], row["raw_axioms"])])
        elif tag == b"COUNT22_THEOREM":
            expect.extend([(row["theorem"], row["axioms"]), (row["raw_target"], None),
                           (row["consumer"], row["consumer_axioms"])])
        else:
            raise ValueError("unexpected declaration tag")
    require(len(expect) == len({name for name, _ in expect}) == 86, "dependency roster")
    return expect


def dependencies(raw, expected):
    result = []
    lines = raw.splitlines(keepends=True)
    require(len(lines) == len(expected), "missing dependency rows")
    for line, (name, observed_axioms) in zip(lines, expected, strict=True):
        require(line.startswith(b"COUNT_DEPENDENCIES ") and line.endswith(b"\n"), "dependency row framing")
        row = decode(line.split(b" ", 1)[1])
        require(set(row) == {"name","kind","module","type_constants","value_constants","transitive_axioms"} and
                row["name"] == name, "wrong dependency row")
        module = {"PidFin3CountRaw":"CountRaw", "PidFin3AlphabetCounts":"AlphabetCounts",
                  "PidFin3CountConsumers":"CountEvidence"}[name.split(".",1)[0]]
        require(row["module"] == module and row["kind"] in {"definition","theorem"}, "dependency owner or kind")
        for key in ("type_constants", "value_constants", "transitive_axioms"):
            values = row[key]
            require(type(values) is list and all(type(v) is str for v in values) and
                    values == sorted(set(values)), "malformed dependency name list")
        require(set(row["transitive_axioms"]) <= STANDARD and (observed_axioms is None or
                row["transitive_axioms"] == observed_axioms), "dependency axiom scope")
        result.append(row)
    return result


def replay(lean_bin, mathlib, output_directory):
    meta, declarations, baseline, sources = original()
    env = {"PATH": str(lean_bin) + os.pathsep + os.defpath, "LC_ALL":"C", "LANG":"C",
           "GIT_OPTIONAL_LOCKS":"0","GIT_TERMINAL_PROMPT":"0","LEAN_NUM_THREADS":"1"}
    roots, version = roots_and_versions(lean_bin, mathlib, meta, env)
    known = inventory(roots)
    program_ids = {k: identity(lean_bin / k) for k in ("lean","leanchecker")}
    original_runtime = {k: baseline["runtime"].get("bin/"+k) for k in program_ids}
    inspected = (HERE/"inspection/Dependencies.lean").read_bytes()
    steps = []
    with tempfile.TemporaryDirectory(prefix="pid-alphabet-counts-") as temp:
        scratch=Path(temp).resolve()
        personal, temporary = scratch/"home", scratch/"temp"
        personal.mkdir()
        temporary.mkdir()
        env.update(HOME=str(personal), TMPDIR=str(temporary), LEAN_PATH=os.pathsep.join(
            [str(scratch)]+[str(v) for k,v in roots.items() if k!="lean"]))
        for name, data in sources.items():
            (scratch/name).write_bytes(data)
        def products():
            return {"project/"+f.name:identity(f) for f in scratch.iterdir() if f.name.endswith(EXTENSIONS)}
        for module in OWNED:
            before = products()
            stdout, elapsed = invoke([lean_bin/"lean","-j1","-DwarningAsError=true","-o",module+".olean",module+".lean"],
                                     cwd=scratch, env=env, timeout=240 if module=="CountEvidence" else 120)
            now = products()
            require("project/"+module+".olean" in now and all(now.get(k)==v for k,v in before.items()),
                    "required module output missing or earlier output changed")
            steps.append({"operation":"compile "+module,"seconds":elapsed})
            if module != "CountEvidence":
                require(not stdout, "unexpected compiler output")
                continue
            require(stdout.startswith(declarations), "32 semantic rows differ from original execution")
            line=stdout[len(declarations):]
            tag=b"COUNT22_IMPORTS "
            require(line.startswith(tag) and line.count(b"\n")==1 and line.endswith(b"\n"),"malformed 33rd row")
            checks=check_imports(decode(line[len(tag):]),baseline,meta,scratch,roots,known,now)
        fixed = products()
        out, elapsed = invoke([lean_bin/"leanchecker","--fresh","CountEvidence"],cwd=scratch,env=env,timeout=600)
        require(out==b"", "unexpected fresh replay output")
        steps.append({"operation":"leanchecker --fresh CountEvidence","seconds":elapsed})
        (scratch/"Dependencies.lean").write_bytes(inspected)
        out, elapsed=invoke([lean_bin/"lean","-j1","-DwarningAsError=true","Dependencies.lean"],cwd=scratch,env=env,timeout=120)
        graph=dependencies(out,dependency_roster(declarations))
        steps.append({"operation":"supplementary read-only dependency query","seconds":elapsed})
        require(products()==fixed and all((scratch/n).read_bytes()==buf for n,buf in sources.items()),
                "own source or product changed during replay")
    require(known==inventory(roots) and program_ids=={k:identity(lean_bin/k) for k in program_ids},
            "library or tool bytes changed across replay")
    require(original()[3]==sources and (HERE/"inspection/Dependencies.lean").read_bytes()==inspected,
            "publication inputs changed")
    receipt={"scope":"ordinary portable replay of previously observed proof; separate from historical scored receipt",
             "executing_version":version,"checks":checks,"source_sha256":meta["source_sha256"],
             "declarations_sha256":digest(declarations), "dependency_query_sha256":digest(inspected),
             "local_provider_count":len(known),"complete_provider_file_map_equals_original":known==baseline["providers"],
             "local_lean_and_leanchecker":program_ids,"two_tool_executables_equal_original":program_ids==original_runtime,
             "owned_products_equal_original":{k.removeprefix("project/"):v for k,v in fixed.items()}==baseline["project_products"],
             "steps":steps}
    if output_directory is not None:
        output_directory.mkdir(exist_ok=False)
        (output_directory/"dependencies.json").write_text(json.dumps(graph,indent=2)+"\n")
        receipt["dependencies_sha256"]=digest((output_directory/"dependencies.json").read_bytes())
        (output_directory/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-bin",type=Path,required=True)
    parser.add_argument("--mathlib",type=Path,required=True)
    parser.add_argument("--output",type=Path,help="new directory for a run receipt and declaration dependencies")
    args=parser.parse_args()
    try:
        receipt=replay(args.lean_bin.resolve(strict=True),args.mathlib.resolve(strict=True),args.output)
        print(json.dumps(receipt,sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as error:
        sys.exit(str(error))
