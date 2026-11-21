"""Read the fixed mathematical roster and check all invented observations, without invoking Lean."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PACKAGE = "audit/research/index-family-control"
PAYLOAD = PACKAGE + "-submission.json"
REGISTER = PACKAGE + "-registration.json"
WORKFLOW = ".github/workflows/index-family-control.yml"
OLD = "audit/research/three-source-original-reachable-v3"
BASE = "37e0913096e2d1fdf136278c18161ed8ede1d5e7"
STOCK = "47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4"
STOCK_GIT = "5045d0056413266e57c625dcd7c365b10e377c52"
ATTEMPT = "INVENTED-83-POSITION-CONSTRUCTIVE-20261121-01"
ANCHORS = ("bin/lean", "bin/leanchecker", "src/lean/LeanChecker.lean", "src/lean/Lean/Replay.lean",
           "src/lean/Lean/Environment.lean", "src/lean/Init/Data/Fin/Basic.lean",
           "src/lean/Init/Data/Fin/Lemmas.lean", "src/lean/Lean/Elab/Tactic/Decide.lean")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON key")
        out[key] = value
    return out

def read(path):
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)

def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def info(path):
    require(path.is_file() and not path.is_symlink(), "expected ordinary file")
    return {"bytes": path.stat().st_size, "sha256": digest(path)}

def write(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    temp.replace(path)

def module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])

def member_info(folder):
    return {p.relative_to(folder).as_posix(): info(p) for p in sorted(folder.rglob("*")) if p.is_file()}

def require_manifest(wanted):
    require(re.fullmatch("[0-9a-f]{64}", wanted) and digest(HERE/"manifest.json") == wanted, "control manifest hash")
    expected = read(HERE/"manifest.json")["files"]
    observed = member_info(HERE)
    del observed["manifest.json"]
    require(expected == observed, "control source membership or bytes")
    return expected

def reuse(repo):
    pinned = read(HERE/"reuse.json")
    require(pinned["source_commit"] == BASE, "immutable common store")
    for name, expected in pinned["files"].items():
        f = repo/name
        require(info(f) == expected and f.read_bytes() == git(repo, "show", BASE+":"+name), "common source drift "+name)
    return pinned["files"]

def fixed_sources(repo, submitted):
    plan = read(HERE/"plan.json")
    allowed = module(repo/"audit/research/three-source-original-first-three/proof_interface.py")
    templates = {n: (HERE/"lean"/(n+".lean.in")).read_text() for n in ("IndexProofs", "IndexInline")}
    require(list(submitted) == plan["slots"], "proof roster or order")
    result = {v.name: v.read_bytes() for v in (HERE/"lean").glob("*.lean")}
    for key, val in allowed.fill(templates, submitted, plan["slots"]).items():
        result[key+".lean"] = val.encode("utf-8")
    require(len(submitted) == 84, "all 83 branch proofs and the single-slot proof")
    single = submitted["IndexExample.inlineComplete"]
    require(len(single) == 333 and sum(s.startswith("refine Fin.cases ") for s in single) == 83
            and all("cover" not in s and "leaf" not in s for s in single), "independent single-slot elimination")
    return result

def original_free_rows():
    for k in range(83):
        for ready in (False, True):
            for arg in (0, 7):
                left = 3*k + 2 + arg
                right = ((3*k + 2) if k else 37) + arg + int(not ready)
                yield f"INDEX_ROW {k},{str(ready).lower()},{arg},{left},{right}"

def check_rows(lines):
    wanted = list(original_free_rows())
    require(len(lines) == 332 and lines == wanted, "complete ordered invented rows")
    for pos, line in enumerate(lines):
        k, flag, arg, left, right = line.removeprefix("INDEX_ROW ").split(",")
        require((left == right) == (flag == "true" and int(k) > 0), "readiness and positive-index equivalence")
    return {"rows": 332, "supported_equalities": 164, "unequal_comparisons": 168,
            "guarded_indices": list(range(1, 83)), "extremes": [0, 1, 82]}

def inspect(repo, stdout):
    plan = read(HERE/"plan.json")
    common = module(repo/"audit/research/three-source-synthetic-projection/readback.py")
    expr = module(repo/"audit/research/three-source-original-first-three/observations.py")
    parsed = expr.read_records(stdout("inspect-IndexTerms"), stdout("inspect-IndexAxioms"),
                               plan, common, plan["allowed_axioms"])
    actual = {}
    for line in stdout("inspect-IndexTerms").read_text().splitlines():
        require(line.startswith(common.PREFIX), "unexpected term output")
        row = json.loads(line[len(common.PREFIX):], object_pairs_hook=pairs)
        name = row["name"]
        if name in plan["edges"]:
            constants = set(row["value_constants"])
            need = set(plan["edges"][name])
            require(need <= constants, "missing constructive proof edge "+name)
            if name.endswith(".inlineComplete"):
                require(not any(x.startswith(("IndexExample.cover", "IndexExample.leaf")) for x in constants),
                        "single slot borrowed a named proof")
            actual[name] = sorted(need)
    require(set(actual) == set(plan["edges"]) and parsed["checked"] == 170
            and sum(map(len, actual.values())) == 254, "all 170 named terms and 254 required edges")
    rows = check_rows(stdout("inspect-IndexTrace").read_text().splitlines())
    refused = {n: common.verify_negative(n, stdout("refuse-"+n), expected)
               for n, expected in plan["refusals"].items()}
    return {"terms": parsed, "edges": actual, "finite": rows, "refused": refused}

def expected_commands():
    plan = read(HERE/"plan.json")
    out = {"extract-official": (0,"silent"), "stock-version": (0,"text"), "stock-commit": (0,"text")}
    for name in plan["ordinary"]:
        out["compile-"+name] = (0,"silent")
        out["fresh-"+name] = (0,"silent")
    for name in plan["observers"]:
        out["inspect-"+name] = (0,"text")
    for name in plan["refusals"]:
        out["refuse-"+name] = (1,"diagnostic")
    return out
