"""Reconstruct the fixed synthetic sources, or run their pinned stock-Linux qualification."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKFLOW = ".github/workflows/three-source-synthetic-projection.yml"

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()

def local_module(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+".py"))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper

def verify_package(expected):
    require(re.fullmatch(r"[a-f0-9]{64}",expected) and digest(HERE/"manifest.json") == expected,
            "package manifest SHA differs")
    manifest = json.loads((HERE/"manifest.json").read_bytes())
    actual = {str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file() and p != HERE/"manifest.json"}
    require(actual == set(manifest["package_files"]), "package source membership differs")
    for name, value in manifest["package_files"].items():
        file = HERE/name
        require(file.resolve() == file and file.stat().st_size == value["bytes"] and digest(file) == value["sha256"],
                "changed package source "+name)
    return manifest

def source_roster(src):
    return {p.name:digest(p) for p in sorted(src.iterdir()) if p.is_file()}

def prepare_sources(out, shared, manifest):
    maker = local_module("make_sources")
    bindings = {n:digest(shared/n) for n in maker.SHARED_FILES}
    require(bindings == manifest["shared_w02_sources"] == maker.SHARED_FILES, "shared public W02 identities")
    require(all((shared/n).resolve() == shared/n for n in bindings), "aliased shared source")
    src = out/"sources"
    src.mkdir()
    maker.write_sources(src, shared)
    expected = json.loads((HERE/"generated.json").read_bytes())
    require(source_roster(src) == expected, "generated Lean module roster or byte identity differs")
    for p in src.iterdir():
        p.chmod(0o444)
    return src, expected

def checked_tree(revision, manifest, shared):
    require(re.fullmatch(r"[0-9a-f]{40}",revision) and shared == HERE.parent/"three-source-w02",
            "native mode uses the exact checked-in shared source relative to this package")
    def git(*argv):
        return subprocess.check_output(["git","-C",REPO,*argv],stderr=subprocess.STDOUT)
    require(git("rev-parse","HEAD").decode().strip() == revision, "checkout SHA")
    tracked = [str((HERE/n).relative_to(REPO)) for n in [*manifest["package_files"],"manifest.json"]]
    tracked += [str((shared/n).relative_to(REPO)) for n in manifest["shared_w02_sources"]]
    tracked += [WORKFLOW]
    require(set(git("ls-files","-z","--",*tracked).decode().rstrip("\0").split("\0"))==set(tracked),
            "all qualification sources must be tracked")
    git("diff","--quiet",revision,"--",*tracked)
    return digest(REPO/WORKFLOW)

def run_hosted(args, root, manifest, src, expected, readers, system, begin, plan, stage_state):
    require(platform.system()=="Linux" and platform.machine()=="x86_64" and Path("/proc/self/stat").is_file(),
            "native measurements require Linux x86-64 and procfs")
    require(begin <= time.monotonic() < begin+plan["campaign_seconds"], "expired campaign before native calls")
    workflow_sha = checked_tree(args.commit,manifest,args.shared)
    require(args.archive.is_file() and not args.stock_root.exists() and not args.stock_root.is_relative_to(root)
            and not args.stock_root.is_relative_to(REPO), "fresh separate supplier root")
    require(digest(args.archive) == plan["release"]["sha256"], "official Linux archive SHA-256")
    args.stock_root.mkdir(mode=0o700)
    modules = root/"modules"
    scratch = root/"scratch"
    modules.mkdir()
    scratch.mkdir()
    env = {"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C","TZ":"UTC","HOME":str(scratch),
           "TMPDIR":str(scratch),"LEAN_PATH":str(modules)}
    campaign = system.Campaign(root,begin,plan,env,digest)
    stage_state["commands"] = campaign.commands
    sol = args.stock_root/"lean-4.34.1-linux"
    data = {"commit":args.commit,"manifest_sha256":args.expected_manifest,"workflow_sha256":workflow_sha,
            "archive_sha256":plan["release"]["sha256"],"stock_git_commit":plan["release"]["stock_git"],
            "linux_release":platform.release(),"machine":platform.machine(),"source_sha256":expected}
    system.record(root/"inputs.json",data)
    campaign.run("extract-official-stock",["/usr/bin/tar","--zstd","--no-same-owner","-xf",args.archive,
                                          "-C",args.stock_root],src)
    lean, checker = sol/"bin/lean", sol/"bin/leanchecker"
    require(lean.is_file() and checker.is_file(), "official release tool paths")
    anchors = ["bin/lean","bin/leanchecker","src/lean/LeanChecker.lean","src/lean/Lean/Replay.lean",
               "src/lean/Lean/Environment.lean"]
    data["observed_official_files"] = {n:digest(sol/n) for n in anchors}
    env["PATH"] = str(sol/"bin") + os.pathsep + os.defpath
    githash = campaign.run("stock-source-revision",[lean,"--githash"],src,mode="text")
    require(githash.read_text().strip() == plan["release"]["stock_git"], "stock binary source revision")
    version = campaign.run("stock-version",[lean,"--version"],src,mode="text")
    require(version.read_text().startswith("Lean (version "+plan["release"]["version"]+","),
            "stock version text")
    system.record(root/"inputs.json",data)
    known = {}
    def build(module, mode="silent"):
        object_file = modules/(module+".olean")
        require(not object_file.exists() and (src/(module+".lean")).is_file(), "once-only module compile")
        stream = campaign.run("compile-"+module,[lean,"-DwarningAsError=true","-R",src,"-o",object_file,
                                                module+".lean"],src,mode=mode)
        require(object_file.is_file() and object_file.stat().st_size > 0,"missing object "+module)
        known[object_file.name] = digest(object_file)
        return stream
    for stage in plan["stages"]:
        name = stage["stage"]
        stage_state["active"] = name
        campaign.stage = name
        started = time.monotonic()
        system.record(root/"progress.json",stage_state)
        for module in stage["compile"]:
            build(module)
        for module in stage["fresh"]:
            require(module+".olean" in known, "unbuilt fresh module")
            campaign.run("fresh-"+module,[checker,"--fresh",module],src)
        if stage["refuse"]:
            refused = {}
            for module in stage["refuse"]:
                stream = campaign.run("reject-"+module,[lean,"--json","-DwarningAsError=true","-R",src,
                                      "-o",modules/(module+".olean"),module+".lean"],src,mode="diagnostic",expected=1)
                require(not (modules/(module+".olean")).exists(), "unexpected object for a false declaration")
                refused[module] = readers.verify_negative(module,stream,plan["refusal_diagnostics"][module])
                system.record(root/"four-refusals.json",refused)
        if stage["observer"]:
            label = stage["observer"]
            axes = build(label+"Axioms","text")
            terms = build(label+"Terms","text")
            observation = readers.verify_terms(label,terms,axes,plan)
            require(observation["checked"] == plan[label.lower()+"_observed_theorems"], "observer scope")
            system.record(root/(label.lower()+"-observations.json"),observation)
        require(source_roster(src) == expected and source_roster(modules) == known,
                "source or compiled module membership changed")
        stage_state["completed"].append({"stage":name,"elapsed_seconds":time.monotonic()-started,
                                        "retained_temporary_bytes":system.retained_bytes(scratch),
                                        "compiled_object_count":len(known)})
        system.record(root/"object-identities.json",known)
        system.record(root/"progress.json",stage_state)
    require(data["observed_official_files"] == {n:digest(sol/n) for n in anchors}, "stock tool or checker source drift")
    require(checked_tree(args.commit,manifest,args.shared) == workflow_sha, "post-run checked-out source drift")
    require(time.monotonic()-begin <= plan["campaign_seconds"] and
            system.retained_bytes(root) < plan["retained_bytes"], "campaign totals")
    stage_state["active"] = None
    stage_state["status"] = "complete synthetic qualification"
    stage_state["retained_bytes_before_final_receipt"] = system.retained_bytes(root)
    stage_state["elapsed_seconds"] = time.monotonic()-begin
    stage_state["original_scientific_assertion_evaluations"] = 0

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-sources",action="store_true",help="source binding and generation without invoking Lean")
    mode.add_argument("--native",action="store_true",help="run the registered bounded campaign on Linux")
    ap.add_argument("--expected-manifest",required=True)
    ap.add_argument("--output",required=True,type=Path,help="new result directory")
    ap.add_argument("--shared",type=Path,default=HERE.parent/"three-source-w02",
                    help="published W02 package, with all five pinned source identities")
    ap.add_argument("--archive",type=Path,help="official v4.34.1 Linux archive")
    ap.add_argument("--stock-root",type=Path,help="new supplier directory for the verified large upstream release")
    ap.add_argument("--commit",help="exact checked-out 40-hex Git revision")
    ap.add_argument("--started",type=float,help="earlier monotonic timestamp from the same running Linux host")
    args=ap.parse_args()
    manifest = verify_package(args.expected_manifest)
    system, readers = local_module("resources"), local_module("readback")
    args.shared = args.shared.resolve()
    root = args.output.resolve()
    require(not root.exists() and not root.is_relative_to(HERE), "fresh evidence directory outside the package")
    root.mkdir(mode=0o700)
    plan = readers.read_json(HERE/"plan.json")
    state = {"status":"incomplete","active":"source preparation","completed":[]}
    begin = args.started if args.started is not None else time.monotonic()
    try:
        src, expected = prepare_sources(root,args.shared,manifest)
        if args.check_sources:
            state.update(status="source identities and generated source only",active=None,
                         generated_lean_files=len(expected),source_sha256=expected,native_commands=0)
        else:
            require(args.archive is not None and args.stock_root is not None and args.commit,
                    "native mode requires the official archive, a new supplier path and the checked-out revision")
            args.archive = args.archive.resolve()
            args.stock_root = args.stock_root.resolve()
            run_hosted(args,root,manifest,src,expected,readers,system,begin,plan,state)
    except BaseException as exc:
        state.update(status="stopped without acceptance",reason=str(exc),elapsed_seconds=time.monotonic()-begin)
        system.record(root/"terminal.json",state)
        raise
    system.record(root/"terminal.json",state)
    if args.native and system.retained_bytes(root) > plan["retained_bytes"]:
        state.update(status="stopped without acceptance",reason="final receipt exceeds storage limit")
        system.record(root/"terminal.json",state)
        raise ValueError(state["reason"])
    print(state["status"])

if __name__ == "__main__":
    main()
