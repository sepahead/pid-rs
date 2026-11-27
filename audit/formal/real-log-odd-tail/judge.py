"""Check one restricted proof body against the frozen real-logarithm statement."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
BASE_OBSERVER = "26477074e6a493982062374e06bdd3c1172e2bcf285f94e13713e6fa2a86bd30"
BASE_PINS = "2db805da313cabbd8360920c0f292bbe2222ac65b3ac61dff451628c5eff8ec0"
AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
THEOREMS = ("sharp", "fullStatement", "equalityAtZero", "atOneThird", "tooSmallAtHalf")
MAX_BYTES = 40_000
BASE_CACHE = "c7135def08d55fb84fb1e2c01ca078607fa0855c1ee197bca74db1fa8ff96b33"


def require(value, meaning):
    if not value:
        raise ValueError(meaning)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_payload(text, allowed):
    encoded = text.encode("utf-8")
    require(0 < len(encoded) <= MAX_BYTES and text.endswith("\n"), "proof body size or final line")
    require(text == unicodedata.normalize("NFC", text), "noncanonical source")
    require(all(c == "\n" or (c.isprintable() and c not in "\t\r") for c in text), "control character")
    require(all(line.startswith("  ") for line in text.splitlines() if line.strip()), "proof indentation")
    require(not any(s in text for s in ('#', '@', '"', "'", '\x60', '\\', '/-', '-/', '--', '/*')),
            "directives, comments, quotation or attributes")
    for token in re.findall(r"[^\W\d][\w.]*", text, re.UNICODE):
        for part in token.rstrip(".").split("."):
            require(part in allowed or re.fullmatch(r"h_[a-z][a-z0-9_]{0,35}", part),
                    f"unregistered proof identifier {part}")
    require(all(c.isalnum() or c.isspace() or c in "_()[]{}:.,=<>+*-^/|;&!⟨⟩⟩⟶→←↔∧∨≤≥≠·∘₂₃₄₅₆₇₈₉₀₁∈⊢ℝℕ↑↦⟪⟫∑∀" for c in text),
            "unregistered proof syntax")
    return encoded


def axioms(output, names):
    found = {}
    for name in names:
        pattern = r"^'PIDRealTail\." + re.escape(name) + r"' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)$"
        rows = re.findall(pattern, output, re.MULTILINE)
        require(len(rows) == 1, f"missing or repeated axiom result for {name}")
        used = set(rows[0].split(", ")) if rows[0] else set()
        require(used <= AXIOMS, f"unpermitted transitive axioms for {name}: {used-AXIOMS}")
        found[name] = sorted(used)
    return found


def text_stream(raw):
    require(len(raw.encode("utf-8")) <= 16 * 1024 * 1024, "native transcript exceeds the registered limit")
    return raw


def main(args, result):
    fixed = json.loads((HERE / "frozen.json").read_bytes())
    for name, expected in fixed["sources"].items():
        path = HERE / name
        require(path.is_file() and not path.is_symlink() and digest(path) == expected, f"fixed source changed at {name}")
    workflow = HERE.parents[2] / ".github/workflows/real-log-odd-tail.yml"
    require(workflow.is_file() and not workflow.is_symlink() and
            digest(workflow) == digest(HERE / "workflow.source.yml"), "executed workflow differs from the frozen workflow")
    for field in ("attempt.json", "candidate-proof.txt"):
        require((HERE/field).is_file() and not (HERE/field).is_symlink(), "regular enrolled proof and receipt")
    parent = (HERE.parent / "real-log-library-read").resolve(strict=True)
    observer = parent / "observe.py"
    require(digest(observer) == BASE_OBSERVER and digest(parent / "identities.json") == BASE_PINS, "original environment reader")
    spec = importlib.util.spec_from_file_location("fixed_runtime", observer)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ctx = json.loads((parent / "identities.json").read_bytes())
    out = args.out.resolve(strict=True)
    tc = args.lean_bin.resolve(strict=True)
    lib = args.mathlib.resolve(strict=True)
    require((platform.system(), platform.machine()) == ("Linux", "x86_64"), "registered platform")
    require(digest(args.archive) == ctx["stock_archive_sha256"] and
            digest(lib / ctx["module"]) == ctx["module_sha256"] and
            digest(lib / "lake-manifest.json") == ctx["manifest_sha256"], "original stock archive, source or package manifest")
    lean, checker = tc / "lean", tc / "leanchecker"
    require(digest(lean) == "e8baaa71855a616dc351028f3ad2200051b0671f423a1696a100e809302d5550" and
            digest(checker) == "ccef1bfe9bfeecea65137d94a69033c1a89f360711f50fa3178e7ba3e696fcbe", "original Linux executable identities")
    require(subprocess.check_output([lean, "--githash"], text=True, timeout=30).strip() == ctx["stock_commit"], "stock commit")
    require({p["name"]:p["rev"] for p in json.loads((lib/"lake-manifest.json").read_bytes())["packages"]} ==
            ctx["package_revisions"], "every package identity")
    roots = {}
    deps = [(k, lib/".lake/packages"/k, oid) for k, oid in ctx["package_revisions"].items()] + [("mathlib",lib,ctx["source_commit"])]
    for name, path, oid in deps:
        require(base.git(path, "rev-parse", "HEAD") == oid and Path(base.git(path, "rev-parse", "--show-toplevel")).resolve() == path,
                "dependency revision and working root")
        root = path / ".lake/build/lib/lean"
        if root.is_dir():
            roots[name] = root.resolve(strict=True)
    cached = {}
    for name, root in sorted(roots.items()):
        for file in sorted(root.rglob("*")):
            if file.is_file() and file.name.endswith((".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig")):
                require(not file.is_symlink(), "symlinked cache object")
                cached[name+"/"+file.relative_to(root).as_posix()] = [file.stat().st_size, digest(file)]
    base.save(out / "cache-files.json", cached)
    require(len(cached) == 10823 and digest(out/"cache-files.json") == BASE_CACHE, "original observed compiled imports")
    enrollment = json.loads((HERE/"attempt.json").read_bytes())
    require(enrollment["contract_sha256"] == digest(HERE/"frozen.json") and
            enrollment["candidate_sha256"] == digest(HERE/"candidate-proof.txt"), "attempt enrollment")
    raw = source_payload((HERE/"candidate-proof.txt").read_text(), set((HERE/"allowed-identifiers.txt").read_text().split()))
    work = out / "modules"
    obj = out / "objects"
    work.mkdir()
    obj.mkdir()
    for name in ("Model.lean", "Check.lean", "False.lean"):
        shutil.copyfile(HERE/name, work/name)
    (work/"Proof.lean").write_bytes((HERE/"ProofPrefix.txt").read_bytes() + raw + (HERE/"ProofSuffix.txt").read_bytes())
    result.update(stock={k:digest(f) for k,f in (("lean",lean),("leanchecker",checker))},
                  cache=digest(out/"cache-files.json"), candidate=digest(HERE/"candidate-proof.txt"),
                  contract=digest(HERE/"frozen.json"), enrollment=digest(HERE/"attempt.json"),
                  complete_modules={f.name:digest(f) for f in sorted(work.iterdir())}, upstream=ctx)
    env = dict(HOME=str(out), TMPDIR=str(out), PATH=str(tc)+":/usr/bin:/bin", LC_ALL="C.UTF-8", TZ="UTC",
               LEAN_NUM_THREADS="1", LEAN_PATH=os.pathsep.join(map(str,[obj,*roots.values()])))
    prefix = [lean, "-j","1","-DwarningAsError=true","-R",work]
    def call(label, argv, expected):
        status, stdout, stderr = base.bounded(argv,cwd=work,env=env,output=out,label=label,records=result["commands"])
        require(status==expected and not stderr, f"native return for {label}: {status}")
        return text_stream(stdout)
    for name in ("Model","Proof","Check"):
        s = call(name.lower(), [*prefix,"-o",obj/(name+".olean"),name+".lean"],0)
        require((obj/(name+".olean")).is_file(), f"missing compiled {name}")
        if name == "Proof":
            require("theorem PIDRealTail.sharp" in s and " :=\n" in s and "sorryAx" not in s and "⋯" not in s, "complete candidate proof print")
            result["candidate_axioms"] = axioms(s, ["sharp"])
        if name == "Check":
            require(all("theorem PIDRealTail."+nm in s for nm in THEOREMS[1:]), "independent positive controls")
            result["checked_axioms"] = axioms(s, THEOREMS)
    # The command names these modules explicitly. The compiled cache is trusted at load.
    for name in ("Model", "Proof", "Check"):
        require(not call("fresh-"+name.lower(), [checker,"--fresh",name],0).strip(), "unexpected fresh output")
    bad = call("false",[*prefix,"False.lean"],1)
    require(bad.count("error:")==1 and "error: Type mismatch" in bad and "PIDRealTail.tooSmallAtHalf" in bad and
            "has type" in bad and "but is expected to have type" in bad and "¬" in bad.split("but is expected to have type",1)[1],
            "wrong negative diagnostic")
    result["objects"] = {p.name:digest(p) for p in sorted(obj.iterdir()) if p.is_file()}
    result["success"] = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("lean-bin", "mathlib", "archive", "out"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(mode=0o700,exist_ok=False)
    result={"success":False,"commands":[]}
    try:
        main(args,result)
    except Exception as exc:
        result["error"]=str(exc)
        raise
    finally:
        save(args.out/"RESULT.json",result)

