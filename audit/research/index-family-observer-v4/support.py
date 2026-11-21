"""Fixed providers, source assembly and schedule for the separate, exposed synthetic control."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
PACKAGE = "audit/research/index-family-observer-v4"
WORKFLOW = ".github/workflows/index-family-observer-v4.yml"
REGISTER = PACKAGE + "-registration.json"
PAYLOAD = PACKAGE + "-submission.json"
REF_PREFIX = "review/index-family-observer-v4/"
BASE = "c416ace7a92d9859917cf3bd56b67b43f1fc3614"
ATTEMPT = "INVENTED-83-POSITION-OBSERVATION-20261121-04"
STAGE = "fixed 87-process artificial index observation"
POST = "assemble-and-check"
JOB = "Observe 170 synthetic declarations on one Linux CPU"
ARTIFACT_PREFIX = "index-family-observer-v4"
ACCEPTED = "accepted sharded artificial observation"
FAILED = "failed sharded artificial observation"
PRIOR = "audit/evidence/index-family-control-attempt-2026-11-21"
HISTORICAL = "85ccfa1c1e746b51df96a6529dea25137bb36c286fd1d03d0e45fb555ac342bc"
STOCK_VERSION = "Lean (version 4.34.1, x86_64-unknown-linux-gnu, commit 5045d0056413266e57c625dcd7c365b10e377c52, Release)"
OLD_COMMON = "25f55dff4729dbc80ddf6b177c6d01be2848424484aafa0ff0fc20e6391f26ba"
FRESH = ["IndexSpec", "IndexProofs", "IndexInline", "IndexConsumer"]
SAFE_LIMITS = {"campaign_seconds": 2700, "subprocess_seconds": 900, "group_rss_bytes": 4 << 30, "retained_bytes": 1 << 30}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    selected = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(selected)
    return selected


old_source = REPOSITORY/"audit/research/index-family-control/common.py"
require(digest_bytes(old_source.read_bytes()) == OLD_COMMON, "previous observation provider")
V1 = load(old_source)
read, write, info, digest, members, git = V1.read, V1.write, V1.info, V1.digest, V1.member_info, V1.git
STOCK, STOCK_GIT, ANCHORS = V1.STOCK, V1.STOCK_GIT, V1.ANCHORS


def verify_provider_bytes(repo, *, checkout=None):
    registry = read(HERE/"providers.json")
    require(registry["base"] == BASE, "unchanged historical publication")
    for name, item in registry["files"].items():
        f = repo/name
        require(info(f) == item and f.read_bytes() == git(repo, "show", BASE+":"+name), "bound provider "+name)
        if checkout:
            for rev in checkout:
                require(f.read_bytes() == git(repo, "show", rev+":"+name), "provider at submitted or registered commit "+name)
    for name, tree in registry["protected_trees"].items():
        for rev in (BASE, *(checkout or [])):
            require(git(repo, "rev-parse", rev+":"+name).decode().strip() == tree, "historic subtree "+name)
    require(digest(repo/PRIOR/"native-evidence.zip") == HISTORICAL and
            read(repo/PRIOR/"record.json")["status"] == "failed invented calibration", "retain true earlier failure")
    return registry["files"]


def verify_manifest(expected):
    require(digest(HERE/"manifest.json") == expected, "observation manifest")
    actual = members(HERE)
    del actual["manifest.json"]
    require(read(HERE/"manifest.json")["files"] == actual, "exact package membership")
    return actual


def groups(plan):
    names = list(plan["targets"])
    leaves = ["IndexExample.leaf"+f"{k:02}" for k in range(83)]
    covers = ["IndexExample.cover"+f"{k:02}" for k in range(83,-1,-1)]
    final = ["IndexExample.inlineComplete","IndexExample.namedResult","IndexExample.singleSlotResult"]
    require(names == leaves + covers + final, "original complete target roster")
    result = [rows[i:i+2] for rows in (leaves,covers) for i in range(0,len(rows),2)] + [[n] for n in final]
    require(len(result) == 87 and sum(result,[]) == names and len(set(names)) == 170, "unique ordered groups")
    return [("IndexTermsPart"+f"{i+1:03}", n) for i,n in enumerate(result)]


def target_line(names):
    return "  let targets : List Name := [" + ", ".join(chr(96)+n for n in names) + "]"


def materialize(repo, submission):
    current = read(HERE/"plan.json")
    old = read(repo/V1.PACKAGE/"plan.json")
    source = V1.fixed_sources(repo, submission)
    old_registration = read(repo/V1.REGISTER)
    require({n:digest_bytes(b) for n,b in source.items()} == old_registration["materialized_sources"], "unchanged ten sources")
    original = source["IndexTerms.lean"].decode()
    whole = target_line(list(old["targets"]))
    require(original.count(whole) == 1 and whole in original.splitlines(), "unique original target selection")
    roster = groups(old)
    require([{"module":m,"targets":n} for m,n in roster] == [{"module":e["module"],"targets":e["targets"]} for e in current["shards"]], "frozen partition")
    for (module, names), pinned in zip(roster, current["shards"], strict=True):
        line = target_line(names)
        derived = original.replace(whole, line)
        content = derived.encode()
        require(derived.replace(line, whole) == original and info_bytes(content) == pinned["source"],
                "exact original observer body "+module)
        source[module+".lean"] = content
    require(len(source) == 97, "all original sources plus 87 observers")
    return source


def info_bytes(data):
    return {"bytes":len(data),"sha256":digest_bytes(data)}


def validate_registration(reg, repo):
    old = read(repo/V1.REGISTER)
    require(reg["schema"] == 4 and reg["unissued_v3"] == {"registration_sha256":"38ba8ad8b593dcf1b2845bcb57bf5ec2af6bec3440d698061d6ad70189b3d3e8","manifest_sha256":"9356d6e51f3f004176208e574af70e1f954705a9b44ccb5e8fed03987329e12f","status":"source-only, never issued; final storage and stop readings and setup ordering require correction"} and reg["unissued_v2"] == {"registration_sha256":"8c84a6dfb42a1720b18cac207218f326f214604f29a2dadc161e68ef7de17e01","manifest_sha256":"0d9e632cd4ecbdf2a7bd246f52bf053199d00dd611601004b6fd32ed9848cf74","status":"source-only, never issued"} and
            reg["attempt"] == ATTEMPT and reg["base_commit"] == BASE and reg["v1_native"] == HISTORICAL and
            reg["stock_archive"] == STOCK and reg["stock_git"] == STOCK_GIT and reg["limits"] == SAFE_LIMITS and
            reg["stock_source_anchors"] == old["stock_source_anchors"] and reg["submission"] == old["submission"] == info(repo/PRIOR/"submitted.json") and
            reg["write_paths"] == [PAYLOAD] and reg["workflow_sha256"] == digest(repo/WORKFLOW) and
            reg["cpu_count"] == reg["workers"] == 1 and reg["workflow_minutes"] == 55 and reg["maximum_zip_members"] == 550 and
            reg["mathematical_targets"] == [170,254,332,3] and reg["complete_file_count"] == 509,
            "exact revised administrative and unmodified mathematical contract")
    verify_manifest(reg["judge_manifest"])
    return reg


def from_payload(repo, content, reg):
    require(info_bytes(content) == reg["submission"] and content == (repo/PRIOR/"submitted.json").read_bytes(),
            "same fully exposed artificial submission")
    source = materialize(repo, json.loads(content,object_pairs_hook=V1.pairs))
    require({n:digest_bytes(b) for n,b in source.items()} == reg["materialized_sources"],
            "all 97 exact registered source units")
    return source


def schedule(repo):
    p = read(repo/V1.PACKAGE/"plan.json")
    work = {"extract-official": (0,"silent"), "stock-version": (0,"text"), "stock-commit": (0,"text")}
    for name in FRESH:
        work["compile-"+name] = (0,"silent")
        work["fresh-"+name] = (0,"silent")
    for name in ["IndexAxioms",*[m for m,n in groups(p)],"IndexTrace"]:
        work["inspect-"+name] = (0,"text")
    for name in p["refusals"]:
        work["refuse-"+name] = (1,"diagnostic")
    require(len(work) == 103, "stock/provisioning commands")
    work[POST] = (0,"silent")
    return work


def all_files(repo, sources):
    p = read(repo/V1.PACKAGE/"plan.json")
    objects = [*FRESH,"IndexAxioms",*[m for m,n in groups(p)],"IndexTrace"]
    files = {"launch.json","result/registration.json","result/stages.json","result/observed.json","result/terminal.json",
             "result/joined-terms.stdout","result/term-shards.json"}
    files.update("result/sources/"+n for n in sources)
    files.update("result/objects/"+n+".olean" for n in objects)
    files.update("result/commands/"+n+"/"+f for n in schedule(repo) for f in ("result.json","stdout","stderr"))
    require(len(files) == 509, "complete prospective archive")
    return files


def bound_sources(repo, parent, head, reg_hash, manifest):
    require(repo.resolve() == REPOSITORY and V1.re.fullmatch("[0-9a-f]{40}",parent) and
            V1.re.fullmatch("[0-9a-f]{40}",head) and V1.re.fullmatch("[0-9a-f]{64}",reg_hash) and
            V1.re.fullmatch("[0-9a-f]{64}",manifest), "exact source identities")
    require(git(repo,"rev-list","--parents","-n","1",head).decode().strip() == head+" "+parent, "one direct registered parent")
    git(repo,"merge-base","--is-ancestor",BASE,parent)
    expected = verify_manifest(manifest)
    verify_provider_bytes(repo,checkout=(parent,head))
    for name in [*[PACKAGE+"/"+p for p in expected], PACKAGE+"/manifest.json", REGISTER, WORKFLOW]:
        require((repo/name).read_bytes() == git(repo,"show",parent+":"+name) == git(repo,"show",head+":"+name),
                "every frozen new driver byte "+name)
    require(git(repo,"diff","--name-only","-z",parent,head) == PAYLOAD.encode()+b"\0" and
            not git(repo,"ls-tree",parent,"--",PAYLOAD) and
            git(repo,"ls-tree",head,"--",PAYLOAD).decode().startswith("100644 blob "), "only the new exposed input")
    reg = validate_registration(read(repo/REGISTER),repo)
    require(digest(repo/REGISTER) == reg_hash and reg["judge_manifest"] == manifest, "externally fixed registration")
    content = git(repo,"show",head+":"+PAYLOAD)
    return reg,from_payload(repo,content,reg)


def write_counted(root, path, obj, *, transient=True):
    """Charge new metadata in addition to the existing evidence, including replaced bytes during a safe write."""
    content = (json.dumps(obj,indent=2,sort_keys=True)+"\n").encode()
    require(tree_bytes(root) + len(content) <= SAFE_LIMITS["retained_bytes"], "cumulative evidence metadata budget")
    if transient:
        temp=path.with_suffix(path.suffix+".tmp")
        with temp.open("xb") as f:
            f.write(content)
        temp.replace(path)
    else:
        with path.open("xb") as f:
            f.write(content)


def tree_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
