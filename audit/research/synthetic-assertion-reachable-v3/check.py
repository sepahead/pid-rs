"""Check a synthetic qualification of assertion-reachable projection on stock Lean."""
from __future__ import annotations

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
import time

HERE = Path(__file__).resolve().parent
PACKAGE = "audit/research/synthetic-assertion-reachable-v3"
REGISTRATION = PACKAGE + "-registration.json"
WORKFLOW = ".github/workflows/synthetic-assertion-reachable-v3.yml"
CANDIDATE = PACKAGE + "/proofs.json"
AUX = "audit/research/three-source-synthetic-projection"
W02 = "audit/research/three-source-w02"
PRIOR = "audit/research/three-source-original-first-three"
ALLOWED = ["Classical.choice", "Quot.sound", "propext"]
ORDINARY = ["W02Semantics", "ProjectionCore", "RouteSpec", "RoutePrefix", "RouteTail",
            "RouteLeaves", "RouteResult", "RouteConsumer", "RouteTransport"]
OBSERVERS = ["RouteAxioms", "RouteInspect", "RouteTrace"]
TEMPLATES = ["RoutePrefix", "RouteTail", "RouteLeaves"]
RESOURCE_PLAN = dict(group_rss_bytes=2**32, subprocess_seconds=900,
                     campaign_seconds=5400, retained_bytes=2**30)
STOCK = dict(version="4.34.1", git="5045d0056413266e57c625dcd7c365b10e377c52",
             linux_tar_zst_sha256="47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4")
TASK_DIGEST = "bbdd9a8226748d63e28fee3d90f5eb93ab54e70ebdf628ea4329897110d1974f"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def unique(items):
    obj = {}
    for k, v in items:
        require(k not in obj, "duplicate JSON key")
        obj[k] = v
    return obj


def load(path):
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def save(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.replace(path)


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def module(path):
    spec = importlib.util.spec_from_file_location("fixed_" + path.stem, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def regular(root, rel):
    require(isinstance(rel, str) and rel and not rel.startswith("/") and
            all(p not in ("", ".", "..") for p in rel.split("/")), "relative member")
    dest = root / rel
    current = root
    for part in rel.split("/"):
        current = current / part
        require(not current.is_symlink(), "symbolic member or parent")
    require(dest.is_file(), "missing regular member")
    return dest


def inherited_predicate(repo, roster):
    previous = "audit/research/synthetic-assertion-reachable-v2"
    old = load(regular(repo, previous + "/manifest.json"))
    stable = [
        "helpers.json", "lean/RouteSpec.lean", "lean/RoutePrefix.lean.template",
        "lean/RouteTail.lean.template", "lean/RouteLeaves.lean.template",
        "lean/RouteResult.lean", "lean/RouteConsumer.lean", "lean/RouteTrace.lean",
        "negative/RefuseWholeState.lean", "negative/RefuseConstant.lean",
        "negative/RefuseFailureAsFalse.lean",
    ]
    require(all(digest(regular(HERE, rel)) == old[rel] for rel in stable),
            "historical mathematical or negative source changed")
    old_roster = load(regular(repo, previous + "/roster.json"))
    require(list(roster["targets"].items())[:22] == list(old_roster["targets"].items()) and
            roster["consumer_uses"] == old_roster["consumer_uses"] and
            all(roster["direct_internal_edges"][k] == v for k,v in old_roster["direct_internal_edges"].items()),
            "historical declarations or protected edges changed")
    old_expected = load(regular(repo, previous + "/negative.json"))
    current = load(regular(HERE, "negative.json"))
    chosen = "RefuseReachedInteger"
    require(list(current) == list(old_expected) and
            all(current[key] == old_expected[key] for key in old_expected if key != chosen),
            "historical refusal order or unaffected reason changed")
    prior_source = regular(repo, previous + "/negative/" + chosen + ".lean").read_text().splitlines()
    new_source = regular(HERE, "negative/" + chosen + ".lean").read_text().splitlines()
    require(prior_source[-1].endswith(" := by rfl") and
            new_source == ["import RouteTransport", *prior_source[1:3], prior_source[-1].removesuffix(" rfl"),
                           "  refine RouteTransport.reached.mpr ?_", "  rfl"],
            "exact source proposition and only the designated transport")


def transported_negative(path):
    record = load(path)
    message = record["data"]
    # Test the two residual sides separately. An unrelated failed reflexivity goal cannot pass.
    sides = re.search(r"The left-hand side\s+(.*?)\s+is not definitionally equal to the right-hand side\s+(.*?)(?:\n\n|$)",
                      message, flags=re.S)
    require(record["kind"] == "[anonymous]" and record["pos"]["column"] == 2 and sides is not None and
            sides[1].strip() == "some [false, true]" and sides[2].strip() == "some [true, false]",
            "actual false literal sides and direction")





def source_profile(repo, expected_manifest, native=False):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_manifest), "fixed manifest digest")
    manifest_path = regular(HERE, "manifest.json")
    require(digest(manifest_path) == expected_manifest and digest(regular(HERE, "task.json")) == TASK_DIGEST,
            "qualification manifest or task digest")
    manifest = load(manifest_path)
    present = {f.relative_to(HERE).as_posix() for f in HERE.rglob("*") if not f.is_dir()}
    extras = {"manifest.json", "proofs.json"} if native else {"manifest.json"}
    require(present == set(manifest) | extras, "exact qualification file inventory")
    for rel, expected in manifest.items():
        require(digest(regular(HERE, rel)) == expected, "qualification file changed: " + rel)
    external = load(HERE / "external.json")
    for rel, expected in external.items():
        require(digest(regular(repo, rel)) == expected, "fixed external source changed: " + rel)
    task = load(HERE / "task.json")
    require(all(external.get(k) == v for k, v in task["dependency_sha256"].items()) and
            task["stock"] == STOCK and
            all(task["limits"].get(k) == v for k, v in RESOURCE_PLAN.items()), "task authority")
    helpers, roster = load(HERE / "helpers.json"), load(HERE / "roster.json")
    templates = {name: (HERE / "lean" / (name + ".lean.template")).read_text() for name in TEMPLATES}
    found = []
    for name, template in templates.items():
        marks = re.findall(r"^@@PROOF ([A-Za-z0-9_.]+)@@$", template, re.M)
        require(marks and all(helpers["owners"].get(m) == name for m in marks), "protected proof slots")
        found.extend(marks)
    require(found == helpers["slots"] and len(set(found)) == len(found) == 9 and
            len(roster["targets"]) == 26 and len(roster["consumer_uses"]) == 8 and
            set(helpers["owners"]).issubset(roster["targets"]), "exact target inventory")
    require(len(load(HERE / "negative.json")) == 4, "four targeted native refusals")
    inherited_predicate(repo, roster)
    return helpers, roster, templates, external


def git(repo, *args):
    return subprocess.check_output(["/usr/bin/git", "-C", repo, *args])


def admit(repo, args, external):
    require(repo.resolve() == HERE.parents[2] and os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ.get("GITHUB_RUN_ATTEMPT") == "1" and os.environ.get("GITHUB_EVENT_NAME") == "push" and
            platform.system() == "Linux" and platform.machine() == "x86_64", "fresh first Linux push execution")
    regcommit = args.registration_commit
    require(re.fullmatch(r"[0-9a-f]{40}", regcommit) and re.fullmatch(r"[0-9a-f]{64}", args.registration_sha256),
            "registration identity")
    ref = "refs/heads/review/synthetic-route-v3/" + regcommit + "-" + args.registration_sha256
    event = load(Path(os.environ["GITHUB_EVENT_PATH"]))
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    require(os.environ["GITHUB_REF"] == ref == event.get("ref") and
            os.environ["GITHUB_SHA"] == event.get("after") == head, "event, checkout or reserved branch")
    require(git(repo, "rev-list", "--parents", "-n", "1", head).decode().split() == [head, regcommit],
            "candidate must be the sole direct descendant")
    require(git(repo, "diff", "--name-status", "--no-renames", regcommit, head).decode().strip() == "A\t" + CANDIDATE,
            "only one new synthetic candidate file")
    seal_path = regular(repo, REGISTRATION)
    require(digest(seal_path) == args.registration_sha256 and seal_path.read_bytes() == git(repo, "show", regcommit + ":" + REGISTRATION),
            "earlier registration bytes")
    seal = load(seal_path)
    expected = dict(schema="pid-rs/synthetic-assertion-reachable-hosted/v3", task_sha256=TASK_DIGEST,
                    manifest_sha256=args.manifest, workflow_sha256=digest(regular(repo, WORKFLOW)),
                    candidate=CANDIDATE, stock=STOCK, limits=RESOURCE_PLAN,
                    fixed_candidate_sha256="a8d2092e9406b46700167bb0c9ab24f72ab0a9186725d12df0a0e6e13c56315e",
                    diagnostic_decision_sha256="4034e9f129ed1a69122718d4c3e19e3ecead9867ebe40c5e695f2bcf1345882b",
                    trigger="exact registered push, first run attempt; one candidate and one stock worker")
    require(seal == expected and digest(regular(repo, CANDIDATE)) == seal["fixed_candidate_sha256"],
            "registration fields and exact previous scientific proof bytes")
    require(not git(repo, "status", "--porcelain=v1", "--untracked-files=all"), "dirty checkout")
    return dict(commit=head, registration=regcommit, registration_sha256=args.registration_sha256,
                run=os.environ["GITHUB_RUN_ID"], workflow=seal["workflow_sha256"], external=external,
                candidate_sha256=digest(regular(repo, CANDIDATE)))


def refused(callback, marker):
    try:
        callback()
    except (ValueError, RuntimeError) as exc:
        require(marker in str(exc), "unexpected control failure: " + str(exc))
        return
    raise ValueError("mutant unexpectedly passed: " + marker)


def native(args):
    repo = args.repo.resolve()
    helpers, roster, templates, external = source_profile(repo, args.manifest, native=True)
    start = args.started
    require(start <= time.monotonic() < start + RESOURCE_PLAN["campaign_seconds"], "job start")
    host = admit(repo, args, external)
    output = args.output.resolve()
    stock_root = args.stock_dir.resolve()
    require(output != repo and not output.is_relative_to(repo) and not output.exists() and
            not stock_root.exists() and not stock_root.is_relative_to(repo) and
            not output.is_relative_to(stock_root) and not stock_root.is_relative_to(output), "fresh, separate output roots")
    output.mkdir(parents=True)
    evidence = output.parent
    require({p.name for p in evidence.iterdir()} == {output.name, "host.txt", "registration.json"},
            "dedicated retained evidence root")
    status = dict(status="failed or incomplete", native=False, stages={})
    save(output / "terminal.json", status)
    res = module(regular(repo, AUX + "/resources.py"))
    reader = module(regular(repo, AUX + "/readback.py"))
    checker = module(regular(repo, PRIOR + "/observations.py"))
    proof = module(regular(repo, PRIOR + "/proof_interface.py"))
    home = output / "isolated-home"
    home.mkdir()
    objects = output / "objects"
    objects.mkdir()
    src = output / "src"
    src.mkdir()
    env = dict(PATH=os.defpath, HOME=str(home), TMPDIR=str(home), LC_ALL="C.UTF-8", LANG="C.UTF-8", TZ="UTC",
               LEAN_PATH=str(objects), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    campaign = res.Campaign(evidence, start, RESOURCE_PLAN, env, digest)
    try:
        require(digest(args.archive) == STOCK["linux_tar_zst_sha256"], "stock archive bytes")
        stock_root.mkdir()
        campaign.run("extract-stock", ["/usr/bin/tar", "--zstd", "--no-same-owner", "-xf", args.archive, "-C",stock_root], home)
        stock = stock_root / "lean-4.34.1-linux"
        lean, fresh = stock / "bin/lean", stock / "bin/leanchecker"
        env["PATH"] = str(stock / "bin") + os.pathsep + os.defpath
        version = campaign.run("stock-version", [lean, "--version"], home, mode="text").read_text().strip()
        revision = campaign.run("stock-revision", [lean, "--githash"], home, mode="text").read_text().strip()
        require(version.startswith("Lean (version 4.34.1,") and revision == STOCK["git"], "stock binary release")
        anchors = ["bin/lean", "bin/leanchecker", "src/lean/LeanChecker.lean", "src/lean/Lean/Replay.lean","src/lean/Lean/Environment.lean"]
        stock_ids = {rel:digest(regular(stock, rel)) for rel in anchors}
        save(output / "inputs.json", dict(host=host, stock_anchors=stock_ids, stock_version=version))
        payload = load(regular(repo, CANDIDATE))
        built = proof.fill(templates, payload, helpers["slots"])
        first = helpers["slots"][0]
        refused(lambda: proof.fill(templates, dict(payload, unexpected=["rfl"]), helpers["slots"]), "exact roster")
        refused(lambda: proof.fill(templates, dict(payload, **{first:["exact sorryAx"]}), helpers["slots"]), "unregistered proof language")
        status["stages"]["proof_input_negatives"] = ["extra slot", "forbidden axiom"]
        for mod, rel in [("W02Semantics", W02 + "/lean/W02Semantics.lean"), ("ProjectionCore", AUX + "/lean/ProjectionCore.lean")]:
            shutil.copyfile(regular(repo, rel), src / (mod + ".lean"))
        for mod in ORDINARY[2:] + OBSERVERS:
            target = src / (mod + ".lean")
            if mod in built:
                target.write_text(built[mod])
            else:
                shutil.copyfile(regular(HERE, "lean/" + mod + ".lean"), target)
        negatives = load(HERE / "negative.json")
        for mod in negatives:
            shutil.copyfile(regular(HERE, "negative/" + mod + ".lean"), src / (mod + ".lean"))
        for path in src.iterdir():
            path.chmod(0o444)
        source_ids = {p.name:digest(p) for p in sorted(src.iterdir())}
        save(output / "source-identities.json", source_ids)
        object_ids = {}
        def compile_lean(mod, printing=False):
            obj = objects / (mod + ".olean")
            require(not obj.exists(), "object path must start empty")
            stdout = campaign.run("compile-" + mod, [lean, "-DwarningAsError=true", "-R", src, "-o", obj, mod + ".lean"],
                                  src, mode="text" if printing else "silent")
            require(obj.is_file() and not obj.is_symlink(), "new ordinary Lean module")
            object_ids[obj.name] = digest(obj)
            return stdout

        for mod in ORDINARY:
            campaign.stage = mod
            compile_lean(mod)
            require(object_ids[mod + ".olean"] == digest(objects / (mod + ".olean")), "fresh replay object identity")
            campaign.run("fresh-" + mod, [fresh, "--fresh", mod], src)
        status["stages"]["stock_fresh"] = ORDINARY
        campaign.stage = "independent term, axiom and finite readback"
        axioms = compile_lean("RouteAxioms", True)
        terms = compile_lean("RouteInspect", True)
        trace = compile_lean("RouteTrace", True)
        require(trace.read_text().strip() == "[1, 2, 2, 1, 0]", "five ordered typed control evaluations")
        detail = checker.read_records(terms, axioms, roster, reader, ALLOWED)
        rows = [json.loads(s[len(reader.PREFIX):], object_pairs_hook=unique) for s in terms.read_text().splitlines()]
        by_name = {r["name"]:r for r in rows}
        for origin, targets in roster["direct_internal_edges"].items():
            require(set(targets).issubset(by_name[origin]["value_constants"]), "missing helper edge: " + origin)
        save(output / "term-readback.json", detail)
        # Force the actual transitive-axiom reader to reject one clearly marked synthetic stream.
        name = next(iter(roster["targets"]))
        bad_stream = output / "synthetic-unapproved-axiom.txt"
        lines = axioms.read_text().splitlines()
        parts = reader.AXIOM_ROW.fullmatch(lines[0])
        require(parts and parts[1] == name, "first genuine axiom row")
        lines[0] = "'" + name + "' depends on axioms: [Synthetic.unapproved]"
        bad_stream.write_text("\n".join(lines) + "\n")
        refused(lambda: reader.verify_axioms(bad_stream, roster["targets"], set(ALLOWED)), "unexpected transitive axiom")
        status["stages"]["declared_targets"] = detail["checked"]
        status["stages"]["finite_codes"] = [1,2,2,1,0]
        campaign.stage = "four negative theorem controls"
        refusal = {}
        for mod, expected in negatives.items():
            obj = objects / (mod + ".olean")
            raw = campaign.run("refuse-" + mod, [lean, "--json", "-DwarningAsError=true", "-R", src, "-o", obj, mod + ".lean"],
                               src, mode="text", expected=1)
            refusal[mod] = reader.verify_negative(mod, raw, expected)
            if mod == "RefuseReachedInteger":
                transported_negative(raw)
            require(not obj.exists(), "refused theorem created an object")
        save(output / "native-refusals.json", refusal)
        status["stages"]["native_refusals"] = list(refusal)
        campaign.stage = "synthetic resource controls"
        # One small positive and two reduced thresholds qualify the Linux monitor.
        # The scientific 4 GiB limit stays in force for every production Lean command.
        positive_root = output / "monitor-ordinary"
        positive_root.mkdir()
        positive = res.Campaign(positive_root, start, dict(RESOURCE_PLAN, group_rss_bytes=96*2**20), env, digest)
        positive.stage = "synthetic ordinary command"
        positive.run("ordinary", [sys.executable, "-I", "-S", "-B", "-c", "import time; time.sleep(0.20)"], home)
        ordinary = positive.commands[-1]
        require(ordinary["exit"] == 0 and ordinary["stop"] is None and ordinary["group_rss_sample_count"] > 0,
                "ordinary synthetic monitor control")
        resource_rows = {"ordinary": ordinary}
        for name, flags, code, reason in [
                ("rss", {"group_rss_bytes":96*2**20}, "import time; b=bytearray(144*2**20); time.sleep(2)", "observed process-group RSS"),
                ("wall", {"subprocess_seconds":1}, "import time; time.sleep(4)", "native or campaign time")]:
            control_root = output / ("monitor-" + name)
            control_root.mkdir()
            control = res.Campaign(control_root, start, dict(RESOURCE_PLAN, **flags), env, digest)
            control.stage = "synthetic monitor probe"
            refused(lambda: control.run("expected-stop", [sys.executable,"-I","-S","-B","-c",code], home), "unexpected native outcome")
            row = control.commands[-1]
            require(row["stop"] == reason and row["exit"] == -9 and row["group_rss_sample_count"] > 0,
                    "resource refusal did not reach its registered predicate")
            if name == "rss":
                require(row["max_observed_group_rss_bytes"] > 96*2**20 and row["direct_wait4_maxrss_bytes"] < RESOURCE_PLAN["group_rss_bytes"], "memory control envelope")
            resource_rows[name] = row
        status["stages"]["resource_controls"] = resource_rows
        require({p.name:digest(p) for p in src.iterdir()} == source_ids and
                {p.name:digest(p) for p in objects.iterdir()} == object_ids and
                {rel:digest(regular(stock, rel)) for rel in anchors} == stock_ids, "post-run source/object/tool identities")
        require(source_profile(repo, args.manifest, native=True)[3] == external and admit(repo, args, external) == host,
                "final bound inputs")
        save(output / "object-identities.json", object_ids)
        status.update(status="synthetic qualification passed", native=True)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        status["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        status["commands"] = campaign.commands
        status["elapsed_seconds"] = time.monotonic() - start
        if status["elapsed_seconds"] > RESOURCE_PLAN["campaign_seconds"]:
            status.update(status="resource or terminal custody failure", native=False)
        save(output / "terminal.json", status)
        if time.monotonic()-start > RESOURCE_PLAN["campaign_seconds"] or res.retained_bytes(evidence) >= RESOURCE_PLAN["retained_bytes"]:
            status.update(status="resource or terminal custody failure", native=False)
            save(output / "terminal.json", status)
    require(status["native"], "final resource and custody")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["source","native"])
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--manifest",required=True)
    for flag, kind in [("output",Path),("archive",Path),("stock-dir",Path),("started",float),
                       ("registration-commit",str),("registration-sha256",str)]:
        p.add_argument("--"+flag,type=kind)
    args=p.parse_args()
    if args.mode == "source":
        helpers,roster,_,_ = source_profile(args.repo.resolve(),args.manifest)
        print(json.dumps(dict(stage="source only, no proof payload or native evaluation",helpers=len(helpers["slots"]),
                              targets=len(roster["targets"]),consumers=len(roster["consumer_uses"]),manifest=args.manifest)))
    else:
        require(all(getattr(args,key) is not None for key in
                    ("output","archive","stock_dir","started","registration_commit","registration_sha256")), "native arguments")
        native(args)


if __name__ == "__main__":
    main()
