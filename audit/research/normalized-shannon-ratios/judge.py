"""Verify the public normalized-ratio fixture, source selection and native observations."""

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "0f3122a96e48a099581ad4faf3e3d5d9138367f6"
PKG = "audit/research/normalized-shannon-ratios/"
TEST = "crates/pid-core/tests/normalized_shannon_ratio.rs"
FIX = "crates/pid-core/tests/fixtures/normalized_shannon_ratio.json"
FLOW = ".github/workflows/normalized-shannon-ratio.yml"
PRODUCTION = {"crates/pid-core/src/invariants.rs", "crates/pid-core/src/exact_binary64.rs"}
PIN = {
    ".github/workflows/ci.yml": "a7399b7f3b029bcc81271d71926d4cbf8050b6d20f651ded9e86b53303f1b5d1",
    "Cargo.lock": "2a390c1a3f468ed938e8c2e6597e78b26b933761c6200b0bf5e01d4b75f3c81d",
    "crates/pid-core/Cargo.toml": "da8c4f5f4b32954df5c654ecf40cddc69b4367403f01a2b87e81c1bab9723063",
    "crates/pid-core/src/exact_binary64.rs": "6e7d6be525878638e4be253aff9bd74d25dd94afb53f1b520fb8e4e1a0a8cdfb",
    "crates/pid-core/src/invariants.rs": "cfca1591153f5cd69795c9f7a9734fbbf9fd078280245a713489b544450b3876",
}
MEMBERS = {TEST, FIX, FLOW, *(PKG+k for k in ("README.md", "oracle.py", "judge.py"))}
MANIFEST = PKG + "manifest.json"
VERSION = "1.99.1"
TEST_NAME = "normalized_reports_match_exact_represented_inputs"
TARGET = re.compile(r"review/normalized-shannon-(?:baseline-([0-9a-f]{64})|fix-([0-9a-f]{40})-([0-9a-f]{64}))")
SPEC = importlib.util.spec_from_file_location("ratio_oracle", HERE/"oracle.py")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


class Refusal(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        obj = {}
        for key, val in items:
            require(key not in obj, "duplicate JSON key")
            obj[key] = val
        return obj
    def bad(_):
        raise Refusal("nonfinite JSON number")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad)


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def checked_fixture():
    raw = (ROOT/FIX).read_bytes()
    data = ORACLE.fixture(check_round=True)
    require(raw == ORACLE.canonical(data), "fixture identity differs from recomputed exact expectations")
    require(len(data["rows"]) == 184, "incorrect case count")
    return data, sha(raw)


def compare(record, fixture, identity):
    require(type(record) is dict and set(record) == {"schema","fixture_sha256","rows"}, "record envelope")
    require(record["schema"] == "normalized-shannon-observations-v1" and record["fixture_sha256"] == identity, "observation fixture identity")
    rows = record["rows"]
    require(type(rows) is list and len(rows) == len(fixture["rows"]), "incomplete row count")
    changes = {}
    for observed, case in zip(rows, fixture["rows"]):
        require(type(observed) is dict and set(observed) == {"id","report"}, "observation row envelope")
        require(observed["id"] == case["id"], "case selection or order")
        actual, expected = observed["report"], case["expected"]
        require(type(actual) is dict and set(actual) == set(expected), "incomplete report fields")
        for field in ("definition","unit","minimum_denominator_nats"):
            require(actual[field] == expected[field], "report metadata "+field)
        require(actual["status"] in {"Defined","EmptyTerms","NonFiniteInput","NonPositiveDenominator",
                                    "DenominatorBelowPolicyThreshold","NumericallyUnrepresentable"}, "unknown report status")
        for field in ("value","numerator_nats","denominator_nats"):
            x = actual[field]
            require(x is None or (type(x) is str and re.fullmatch(r"[0-9a-f]{16}",x) and
                    int(x,16)&0x7ff0000000000000 != 0x7ff0000000000000), "nonfinite or malformed word "+field)
        require(actual["denominator_nats"] == expected["denominator_nats"], "denominator readback")
        changed = {f:{"actual":actual[f],"expected":expected[f]} for f in expected if expected[f] != actual[f]}
        if changed:
            changes[case["id"]] = changed
    return changes


# These are required native observations on the bound original source. The complete mismatch set
# is retained, including discrepancies outside these predeclared anchors.
ORIGINAL_VALUES = {
    "r-min-over-two": "0000000000000000",
    "r-min-over-three-halves": "0000000000000002",
    "r-signed-cancellation": "0000000000000000",
}


def verdict(changes, mode):
    if mode == "fixed":
        require(not changes, "field differences on corrected source")
        return
    require(mode == "baseline", "unknown grading mode")
    for stem, value in ORIGINAL_VALUES.items():
        for wrapper in ("default","explicit"):
            diff = changes.get(stem+"-"+wrapper,{})
            require(set(diff)=={"value"} and diff["value"]["actual"] == value, "missing directed original failure "+stem)
    for wrapper in ("default","explicit"):
        require("r-overflowed-numerator-"+wrapper not in changes, "original overflow control")
        require("v-three-next-down-"+wrapper not in changes, "original near-equality control")


def ensure_base(oid):
    require(oid == BASE, "stale original baseline")


def require_production_diff(changes):
    require(changes == {p:"M" for p in PRODUCTION}, "candidate may change exactly two production files")


def require_judge_diff(changes):
    require(changes == {p:"A" for p in MEMBERS|{MANIFEST}}, "judge-only publication diff")


def self_test():
    data, digest = checked_fixture()
    clean = {"schema":"normalized-shannon-observations-v1","fixture_sha256":digest,
             "rows":[{"id":r["id"],"report":r["expected"].copy()} for r in data["rows"]]}
    positions = {r["id"]:i for i,r in enumerate(clean["rows"])}
    def run(obs, mode="fixed"):
        changes = compare(obs,data,digest)
        verdict(changes,mode)
        return changes
    def row(obs,id):
        return obs["rows"][positions[id]]["report"]
    refused = {}
    def refusal(test, reason, function):
        try:
            function()
        except Refusal as err:
            require(str(err).startswith(reason), "wrong reason for "+test+": "+str(err))
            refused[test] = str(err)
            return
        raise ValueError("accepted negative control "+test)
    run(clean)
    original = copy.deepcopy(clean)
    for stem, value in ORIGINAL_VALUES.items():
        for suffix in ("-default","-explicit"):
            row(original,stem+suffix)["value"] = value
    run(original,"baseline")
    refusal("fixed-as-original","missing directed original failure",lambda:run(clean,"baseline"))
    refusal("original-as-fixed","field differences",lambda:run(original))
    refusal("stale-baseline","stale original baseline",lambda:ensure_base("0"*40))
    right_changes = {p:"M" for p in PRODUCTION}
    judge_changes = {p:"A" for p in MEMBERS|{MANIFEST}}
    require_production_diff(right_changes)
    require_judge_diff(judge_changes)
    refusal("candidate-modifies-judge","candidate may change exactly two",lambda:require_production_diff({**right_changes,FIX:"M"}))
    refusal("candidate-adds-source","candidate may change exactly two",lambda:require_production_diff({**right_changes,TEST:"A"}))
    refusal("judge-only-ref-modifies-production","judge-only publication diff",lambda:require_judge_diff({**judge_changes,**right_changes}))
    refusal("duplicate-json-key","duplicate JSON key",lambda:strict_json('{"x":1,"x":2}'))
    refusal("nonfinite-json-number","nonfinite JSON number",lambda:strict_json('{"x":NaN}'))
    altered = copy.deepcopy(clean)
    altered["rows"] = altered["rows"][:-1]
    refusal("partial-capture","incomplete row count",lambda:run(altered))
    altered = copy.deepcopy(clean)
    altered["rows"][1] = copy.deepcopy(altered["rows"][0])
    refusal("duplicate-selected-row","case selection",lambda:run(altered))
    altered = copy.deepcopy(clean)
    altered["rows"][0:2] = list(reversed(altered["rows"][0:2]))
    refusal("permuted-same-size","case selection",lambda:run(altered))
    altered = copy.deepcopy(clean)
    a = row(altered,"r-swapping-method-changes-value-default")
    b = row(altered,"v-swapping-method-changes-value-default")
    a["value"], b["value"] = b["value"], a["value"]
    refusal("swapped-calculation","field differences",lambda:run(altered))
    altered = copy.deepcopy(clean)
    row(altered,"v-nonzero-positive-numerator-zero-value-default")["numerator_nats"] = "0"*16
    refusal("rounded-numerator-from-quotient","field differences",lambda:run(altered))
    altered = copy.deepcopy(clean)
    row(altered,"v-nonzero-negative-numerator-signed-zero-value-default")["value"] = "0"*16
    refusal("negative-zero-sign-lost","field differences",lambda:run(altered))
    altered = copy.deepcopy(clean)
    row(altered,"r-policy-empty-before-nan-default")["status"] = "NonFiniteInput"
    refusal("invalid-status-precedence","field differences",lambda:run(altered))
    altered = copy.deepcopy(clean)
    row(altered,"r-min-over-two-default")["unit"] = "Nats"
    refusal("wrong-unit","report metadata unit",lambda:run(altered))
    altered = copy.deepcopy(clean)
    row(altered,"r-min-over-two-default")["denominator_nats"] = None
    refusal("lost-denominator","denominator readback",lambda:run(altered))
    altered = copy.deepcopy(clean)
    altered["fixture_sha256"] = "0"*64
    refusal("swapped-fixture-identity","observation fixture identity",lambda:run(altered))
    altered_inputs = copy.deepcopy(data)
    altered_inputs["rows"][0]["expected"]["value"] = "f"*16
    def stale_fixture():
        require(ORACLE.canonical(altered_inputs)==(ROOT/FIX).read_bytes(), "fixture identity differs")
    refusal("corrupted-expectation","fixture identity differs",stale_fixture)
    return {"rows":len(data["rows"]),"positive_controls":["matching synthetic record","directed synthetic old record"],
            "refused":refused,"fixture_sha256":digest}


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git","-C",str(cwd),*args],timeout=45)


def changes_between(prior, target):
    fields = git("diff","--no-renames","--name-status","-z",prior,target,"--").decode().split("\0")
    require(fields.pop()=="" and len(fields)%2==0, "git diff format")
    return {path:op for op,path in zip(fields[::2],fields[1::2])}


def check_manifest(identity):
    content=(ROOT/MANIFEST).read_bytes()
    require(sha(content)==identity, "manifest differs from external branch commitment")
    m=strict_json(content)
    require(set(m)=={"schema","files"} and m["schema"]=="normalized-shannon-judge-manifest-v1" and
            type(m["files"]) is dict and set(m["files"])==MEMBERS, "judge manifest membership")
    for path, digest in m["files"].items():
        p=ROOT/path
        require(not p.is_symlink() and p.is_file() and sha(p.read_bytes())==digest, "judge member identity "+path)
    return m


def bind(ref, head):
    require(re.fullmatch(r"[0-9a-f]{40}",head) and git("rev-parse","HEAD").decode().strip()==head, "checked-out commit")
    match=TARGET.fullmatch(ref)
    require(match is not None, "verification branch")
    b, judge, linked = match.groups()
    digest = b or linked
    mode="baseline" if b else "fixed"
    manifest=check_manifest(digest)
    if mode=="baseline":
        judge=head
    else:
        require(git("rev-list","--parents","-n","1",head).decode().split()==[head,judge], "fixed source must be direct child of frozen judge")
        require_production_diff(changes_between(judge,head))
        remote_base="refs/remotes/origin/review/normalized-shannon-baseline-"+digest
        require(git("rev-parse","--verify",remote_base).decode().strip()==judge, "independently published judge reference")
    ancestry=git("rev-list","--parents","-n","1",judge).decode().split()
    require(len(ancestry)==2 and ancestry[0]==judge, "judge must have one parent")
    ensure_base(ancestry[1])
    require_judge_diff(changes_between(BASE,judge))
    for path in MEMBERS|{MANIFEST}|PRODUCTION:
        entry=git("ls-tree",head,"--",path).decode().split()
        require(entry[:2]==["100644","blob"] and entry[-1]==path and git("show",head+":"+path)==(ROOT/path).read_bytes(),
                "committed ordinary bytes "+path)
    for path,digest0 in PIN.items():
        require(sha(git("show",BASE+":"+path))==digest0, "registered original bytes "+path)
    return {"mode":mode,"base":BASE,"judge":judge,"head":head,"manifest_sha256":digest,
            "judge_files":manifest["files"],"original_sha256":PIN,"head_production":{p:sha((ROOT/p).read_bytes()) for p in sorted(PRODUCTION)}}


def capture(tree, label, out, temp):
    work=temp/(label+"-source")
    git("worktree","add","--quiet","--detach",str(work),tree)
    if label=="baseline":
        for path in (TEST,FIX):
            target=work/path
            require(not target.exists(), "baseline overlay collision")
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/path,target)
        require(set(git("ls-files","--others","--exclude-standard",cwd=work).decode().splitlines())=={TEST,FIX},
                "original overlay membership")
    require(all((ROOT/p).read_bytes()==(work/p).read_bytes() for p in (TEST,FIX)), "identical compiled observer")
    capture_dir=out/label
    capture_dir.mkdir()
    target_dir=temp/(label+"-target")
    env={**os.environ,"CARGO_TARGET_DIR":str(target_dir),"CARGO_BUILD_JOBS":"2","RUST_TEST_THREADS":"1",
         "CARGO_INCREMENTAL":"0","CARGO_TERM_COLOR":"never","RUSTFLAGS":"-D warnings",
         "PID_RS_RATIO_OBSERVATIONS":str(capture_dir/"observation.json")}
    argv=["cargo","+"+VERSION,"test","--locked","--jobs","2","-p","pid-core","--test","normalized_shannon_ratio",
          "--","--test-threads=1","--nocapture"]
    # Stream build and test output to disk. Retain partial logs on infrastructure failure.
    with (capture_dir/"cargo.stdout").open("xb") as so,(capture_dir/"cargo.stderr").open("xb") as se:
        result=subprocess.run(argv,cwd=work,env=env,stdout=so,stderr=se,timeout=850)
    write(capture_dir/"command.json",{"argv":argv,"returncode":result.returncode,"git_commit":tree,
          "source_sha256":{p:sha((work/p).read_bytes()) for p in sorted(PRODUCTION|{TEST,FIX})}})
    text=(capture_dir/"cargo.stdout").read_text()
    obs=capture_dir/"observation.json"
    require(obs.is_file() and obs.stat().st_size<=1024*1024, "missing or oversized native observation")
    data,digest=checked_fixture()
    differences=compare(strict_json(obs.read_bytes()),data,digest)
    write(capture_dir/"comparison.json",{"row_count":len(data["rows"]),"mismatching_rows":len(differences),
           "differences":differences,"observation_sha256":sha(obs.read_bytes())})
    verdict(differences,label)
    n=len(data["rows"])
    require(f"normalized-ratio rows={n} mismatches={len(differences)}" in text, "native final row marker")
    require("running 1 test" in text and TEST_NAME in text, "native test selection")
    if label=="baseline":
        require(result.returncode==101 and "normalized-ratio field mismatch:" in text+(capture_dir/"cargo.stderr").read_text()
                and "test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out" in text, "expected native assertion failure")
    else:
        require(result.returncode==0 and "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out" in text,
                "successful corrected native test")
    # Reuse the freshly built source for the pre-existing default invariant suite; its 16 tests
    # include the established overflow/cancellation examples and the original policy checks.
    regress_argv=["cargo","+"+VERSION,"test","--locked","--jobs","2","-p","pid-core","--test","invariants",
                  "--","--test-threads=1"]
    regress_env=dict(env)
    del regress_env["PID_RS_RATIO_OBSERVATIONS"]
    with (capture_dir/"invariants.stdout").open("xb") as so,(capture_dir/"invariants.stderr").open("xb") as se:
        old_tests=subprocess.run(regress_argv,cwd=work,env=regress_env,stdout=so,stderr=se,timeout=90)
    write(capture_dir/"invariants-command.json",{"argv":regress_argv,"returncode":old_tests.returncode})
    require(old_tests.returncode==0 and "test result: ok. 16 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
            in (capture_dir/"invariants.stdout").read_text(), "existing invariant regressions")
    return {"mode":label,"git_commit":tree,"cases":n,"mismatch_count":len(differences),"returncode":result.returncode,
            "existing_invariant_tests_passed":16,
            "observation_sha256":sha(obs.read_bytes())}


def run_host(ref,head,out,temp):
    require(sys.platform=="linux" and os.environ.get("GITHUB_ACTIONS")=="true", "native route requires hosted Linux")
    # Store the outer bindings and event identity before attempting either build.
    out.mkdir(parents=True,exist_ok=False)
    temp.mkdir(parents=True,exist_ok=False)
    bindings=bind(ref,head)
    write(out/"bindings.json",bindings)
    tests=self_test()
    write(out/"controls.json",tests)
    rust=subprocess.check_output(["rustc","+"+VERSION,"-vV"],text=True,timeout=20)
    cargo=subprocess.check_output(["cargo","+"+VERSION,"-vV"],text=True,timeout=20)
    require("release: "+VERSION+"\n" in rust and "commit-hash: 58cf8f9c35b355199727627d07ae34a4e2846d67\n" in rust and
            "host: x86_64-unknown-linux-gnu" in rust and cargo.startswith("cargo "+VERSION+" "), "pinned toolchain")
    (out/"versions.txt").write_text(rust+"\n"+cargo)
    complete=[capture(BASE,"baseline",out,temp)]
    if bindings["mode"]=="fixed":
        complete.append(capture(head,"fixed",out,temp))
    write(out/"result.json",{"branch":ref,"commit":head,"workflow_run_id":os.environ["GITHUB_RUN_ID"],
          "run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],"mode":bindings["mode"],"complete":complete})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    cmd=parser.add_subparsers(dest="action",required=True)
    cmd.add_parser("self-test")
    native=cmd.add_parser("hosted")
    for arg in ("ref","head","out","temp"):
        native.add_argument("--"+arg,required=True)
    args=parser.parse_args()
    if args.action=="self-test":
        print(json.dumps(self_test(),sort_keys=True))
    else:
        run_host(args.ref,args.head,Path(args.out).resolve(),Path(args.temp).resolve())
