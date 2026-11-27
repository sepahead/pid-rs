"""Read the two original import families separately and together on Linux."""
import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tarfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bounded import Run, SETUP_SECONDS, digest, require, save

BASIC = "Mathlib.Analysis.SpecialFunctions.Log.Basic"
REAL_NAMES = ("Real.log_one", "Real.log_mul", "Real.log_div", "Real.log_pow", "Real.log_zpow",
              "Real.log_prod", "Real.log_pos_iff", "Real.log_neg_iff", "Real.eq_one_of_pos_of_log_eq_zero")
JOINT_NAMES = ("A2.Decoded.positive_value", "A2.Decoded.true_lower_interval", "A2.Decoded.signed_from_counts",
               "Real.log_mul", "Real.log_div")
AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
URL = "https://github.com/leanprover/lean4/releases/download/v4.34.1/lean-4.34.1-linux.tar.zst"


def unpack_stock(archive, directory, pins):
    require(digest(archive) == pins["stock_bundle_sha256"], "stock bundle")
    found = set()
    with tarfile.open(archive, "r:gz") as reader:
        for member in reader:
            name = member.name
            require(re.fullmatch(r"[A-Za-z][-A-Za-z0-9]*\.(?:lean|stdout)", name) is not None
                    and member.isreg() and member.size <= 512_000 and name not in found
                    and name in pins["stock_members"], "unexpected stock member")
            data = reader.extractfile(member).read()
            require(hashlib.sha256(data).hexdigest() == pins["stock_members"][name], "stock member " + name)
            with (directory / name).open("xb") as target:
                target.write(data)
            found.add(name)
    require(found == set(pins["stock_members"]) and len(found) == 30, "complete stock inputs")


def read_axioms(raw, names):
    text = raw.decode()
    entries = {}
    for line in text.splitlines():
        row = re.fullmatch(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", line)
        if not row:
            continue
        name = row[1]
        parts = (row[2] or "").replace(" ", "").split(",") if row[2] else []
        require(name not in entries and set(parts) <= AXIOMS and len(parts) == len(set(parts)), "axiom row " + name)
        entries[name] = sorted(parts)
    require(tuple(entries) == names, "expected named transitive axiom rows")
    before = text.split("'" + names[0] + "'", 1)[0]
    require(all(name in before for name in names) and "sorryAx" not in text and ": error:" not in text,
            "named type observations")
    return entries


def rejected_real(name, raw):
    text = raw.decode()
    line = 3 if name == "WrongRealValue" else 5
    require(text.count(": error:") == 1 and re.search(rf"{name}\.lean:{line}:\d+: error: ", text),
            "source position of expected negative")
    require(re.search("type mismatch", text, flags=re.I) is not None
            and "unknown" not in text.lower() and "file not found" not in text.lower(), "intended type mismatch")
    if name == "WrongRealValue":
        require(re.search(r"(?:Real\.)?log 1 = 0", text) and re.search(r"(?:Real\.)?log 1 = 1", text),
                "expected zero and rejected one")
    else:
        require(("ℝ" in text or "Real" in text) and ("ℕ" in text or "Nat" in text)
                and "log" in text and "make" in text, "real expression required as a natural number")


def check_target_cache(library, pins):
    raw = HERE / "basic-cache-identities.json.gz"
    require(digest(raw) == pins["cache_manifest_sha256"], "previous native cache record")
    listed = json.loads(gzip.decompress(raw.read_bytes()))
    roots = {name: library / ".lake/packages" / name / ".lake/build/lib/lean"
             for name in pins["package_revisions"]}
    roots["mathlib"] = library / ".lake/build/lib/lean"
    require(len(listed) == pins["cache_files_count"] == 9715
            and sum(name.endswith(".olean") for name in listed) == pins["public_olean_count"] == 1943,
            "scoped prior cache roster")
    for name, (size, sha) in listed.items():
        package, rel = name.split("/", 1)
        root = roots[package].resolve()
        path = root / rel
        require(path.resolve(strict=True) == path and path.is_relative_to(root) and path.stat().st_size == size
                and digest(path) == sha, "compiled dependency " + name)
    return roots


def main(directory):
    require(platform.system() == "Linux" and platform.machine() == "x86_64", "Ubuntu x86-64 required")
    work = directory / "work"
    output = directory / "evidence"
    work.mkdir()
    output.mkdir(exist_ok=True)
    source = work / "source"
    objects = work / "stock-objects"
    basic_objects = work / "basic-objects"
    joint_objects = work / "joint-objects"
    library = work / "mathlib"
    stock = work / "lean-4.34.1-linux/bin"
    home = work / "home"
    temp = work / "temp"
    for path in (source, objects, basic_objects, joint_objects, home, temp):
        path.mkdir()
    environment = {"PATH": str(stock) + ":/usr/local/bin:/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(temp),
                   "LC_ALL": "C.UTF-8", "TZ": "UTC", "LEAN_NUM_THREADS": "1", "MATHLIB_NO_CACHE_ON_UPDATE": "1",
                   "GIT_CONFIG_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
                   "GIT_CONFIG_GLOBAL": os.devnull}
    names = ("source", "tools", "mathlib-source", "stock-build", "stock-controls", "stock-audit", "stock-fresh",
             "stock-negative", "target-cache", "basic-read", "basic-fresh", "real-negative", "joint-read",
             "joint-fresh", "joint-negative")
    data = {"scope": "Linux import and three separate fresh replays", "status": "running",
            "event": {k: os.environ.get(k) for k in ("GITHUB_SHA","GITHUB_RUN_ID","GITHUB_RUN_ATTEMPT","GITHUB_REF")},
            "stages": {n: {"status": "pending"} for n in names}, "facts": {}, "commands": {}}
    allowed = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {allowed[0]})
    data["facts"]["original_cpu_affinity"] = allowed
    data["facts"]["active_cpu"] = sorted(os.sched_getaffinity(0))
    result = output / "RESULT.json"
    run = Run(output, work, data["commands"])
    pins = json.loads((HERE / "origins.json").read_bytes())
    def checkpoint():
        save(result, data)
    def stage(name, parents, operate):
        missing = [parent for parent in parents if data["stages"][parent]["status"] != "passed"]
        if missing:
            data["stages"][name] = {"status": "blocked", "prerequisites": missing}
        else:
            try:
                operate()
                data["stages"][name] = {"status": "passed"}
            except Exception as error:
                data["stages"][name] = {"status": "failed", "exception": type(error).__name__, "detail": str(error)}
                (output / (name + ".exception")).write_text(traceback.format_exc())
        checkpoint()
    def call(name, argv, cwd=work, *, libs=None, seconds=600, code=0):
        env = environment.copy()
        if libs is not None:
            env["LEAN_PATH"] = os.pathsep.join(str(p) for p in libs)
        return run.command(name, argv, cwd, env, secs=seconds, expected=code)
    def identity(name, root, args):
        return call(name, ["git", "-C", root, *args])[0].decode().strip()
    def source_inputs():
        binding = json.loads((HERE / "BINDINGS.json").read_bytes())
        for name, value in binding.items():
            require((HERE / name).parent == HERE and digest(HERE / name) == value, "frozen input " + name)
        unpack_stock(HERE / "stock-sources.tar.gz", source, pins)
        for name in ("BasicRead","JointRead","WrongRealValue","WrongResultType"):
            shutil.copyfile(HERE / (name + ".lean"), source / (name + ".lean"))
        data["facts"]["stock_sources"] = pins["stock_members"]
        data["facts"]["observer_bindings_sha256"] = digest(HERE / "BINDINGS.json")
    def acquire_tools():
        arc = work / "lean.tar.zst"
        call("download-release", ["curl","--fail","--show-error","--silent","--location","--retry","3",
                                  "--proto","=https","--tlsv1.2","--output",arc,URL], seconds=SETUP_SECONDS)
        require(digest(arc) == pins["stock_archive_sha256"], "exact official archive")
        call("extract-release", ["tar","--zstd","--no-same-owner","-xf",arc,"-C",work], seconds=SETUP_SECONDS)
        for name, sha in pins["linux_bins"].items():
            require(digest(stock / name) == sha, "Linux executable " + name)
        version = call("lean-version", [stock/"lean","--version"])[0].decode().strip()
        git_hash = call("lean-githash", [stock/"lean","--githash"])[0].decode().strip()
        require("Lean (version 4.34.1," in version and git_hash == pins["stock_commit"], "compiler revision")
        data["facts"]["official_release"] = [URL, digest(arc), git_hash, version, pins["linux_bins"]]
    def acquire_source():
        call("mathlib-init", ["git","init","--quiet",library])
        call("mathlib-remote", ["git","-C",library,"remote","add","origin","https://github.com/leanprover-community/mathlib4.git"])
        call("mathlib-fetch", ["git","-C",library,"fetch","--no-tags","--depth","1","origin",pins["source_commit"]], seconds=SETUP_SECONDS)
        call("mathlib-checkout", ["git","-C",library,"checkout","--detach","FETCH_HEAD"])
        require(identity("mathlib-commit",library,["rev-parse","HEAD"]) == pins["source_commit"]
                and digest(library/"lake-manifest.json") == pins["manifest_sha256"]
                and digest(library/"Mathlib/Analysis/SpecialFunctions/Log/Basic.lean") == pins["basic_source_sha256"],
                "source and package pins")
        packages = json.loads((library/"lake-manifest.json").read_bytes())["packages"]
        require(len(packages) == len(pins["package_revisions"]) == 8
                and {p["name"]:p["rev"] for p in packages} == pins["package_revisions"], "dependency manifest")
    cache_paths = []
    def acquire_cache():
        call("targeted-cache", [stock/"lake","exe","cache","get","--cache-from=master",BASIC],
             library, seconds=SETUP_SECONDS)
        for name, revision in pins["package_revisions"].items():
            root = library / ".lake/packages" / name
            require(identity("package-"+name,root,["rev-parse","HEAD"]) == revision, "actual dependency " + name)
        roots = check_target_cache(library, pins)
        cache_paths.extend(path for path in roots.values() if path.is_dir())
        data["facts"]["verified_cache"] = [pins["cache_files_count"],pins["public_olean_count"],pins["cache_manifest_sha256"]]
    def compile_module(name, libs, *, expected=0):
        obj = libs[0] / (name+".olean")
        require(not obj.exists(), "unexpected prior object " + name)
        command = [stock/"lean","-j","1","-DwarningAsError=true","-R",source,"-o",obj,name+".lean"]
        stdout, stderr = call("compile-"+name, command, source, libs=libs, code=expected)
        require(not stderr and obj.is_file() == (expected == 0), "stderr or object status for " + name)
        return stdout
    def fresh(name, libs):
        a, b = call("fresh-"+name,[stock/"leanchecker","--fresh",name],source,libs=libs)
        require(not a.strip() and not b.strip(), "fresh replay diagnostics for " + name)
    def original_stock():
        for name in pins["stock_compile_order"]:
            compile_module(name,[objects])
        data["facts"]["stock_objects"] = {n:digest(objects/(n+".olean")) for n in pins["stock_compile_order"]}
    def stock_audit():
        observed = compile_module("JoinAudit",[objects])
        require(observed == (source/"compile-JoinAudit.stdout").read_bytes(), "original seven types and axiom rows")
    def stock_negative():
        observed = compile_module("WrongSignedValue",[objects],expected=1)
        require(observed == (source/"WrongSignedValue.stdout").read_bytes(), "original rejected 16/9")
    def basic_read():
        data["facts"]["log_axioms"] = read_axioms(compile_module("BasicRead",basic()), REAL_NAMES)
    def joint_read():
        text = compile_module("JointRead",joint())
        require(b"Real.log" in text and b"A2.make" in text and b"D1Whole.Table" in text, "actual joint expression")
        data["facts"]["combined_axioms"] = read_axioms(text,JOINT_NAMES)
    def basic():
        return [basic_objects, *cache_paths]
    def joint():
        return [joint_objects, objects, *cache_paths]
    checkpoint()
    stage("source", [], source_inputs)
    stage("tools", ["source"], acquire_tools)
    stage("mathlib-source", ["source"], acquire_source)
    stage("stock-build", ["tools"], original_stock)
    stage("stock-controls", ["stock-build"], lambda: compile_module("JoinControl",[objects]))
    stage("stock-audit", ["stock-build"], stock_audit)
    stage("stock-fresh", ["stock-audit"], lambda: fresh("JoinAudit",[objects]))
    stage("stock-negative", ["stock-build"], stock_negative)
    stage("target-cache", ["mathlib-source","tools"], acquire_cache)
    stage("basic-read", ["target-cache"], basic_read)
    stage("basic-fresh", ["basic-read"], lambda: fresh("BasicRead",basic()))
    stage("real-negative", ["target-cache"],
          lambda: rejected_real("WrongRealValue",compile_module("WrongRealValue",basic(),expected=1)))
    stage("joint-read", ["target-cache","stock-build"], joint_read)
    stage("joint-fresh", ["joint-read"], lambda: fresh("JointRead",joint()))
    stage("joint-negative", ["target-cache","stock-build"],
          lambda: rejected_real("WrongResultType",compile_module("WrongResultType",joint(),expected=1)))
    data["status"] = "passed" if all(s["status"]=="passed" for s in data["stages"].values()) else "failed"
    data["facts"]["outputs"] = {d.name+"/"+p.name:digest(p) for d in (objects,basic_objects,joint_objects)
                                for p in sorted(d.iterdir()) if p.is_file()}
    checkpoint()
    print(json.dumps({name:value["status"] for name,value in data["stages"].items()},sort_keys=True))
    return data["status"]=="passed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    sys.exit(0 if main(parser.parse_args().root.resolve(strict=True)) else 1)
