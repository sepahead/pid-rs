"""Read the published failure evidence, optionally against the original hosted ZIP. No Lean execution."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import zipfile


HERE = Path(__file__).resolve().parent
PACKAGE = "audit/research/three-source-original-reachable-v3"
STOCK = "5045d0056413266e57c625dcd7c365b10e377c52"
SUMMARY = "40e4a02b404f92c277133bf0b01fa26ba710aa49026ca7e7b52850552a1d34de"
ARCHIVE = "4191e5d0a52b5c2f0abe538403e527d82b6c13f51373e1e6bc3c3acfd944621f"
REGISTER = "0e7ef52332da92c229205198efe112d197d21a7d2f8bb9d5bfa2a3f0f816c939"
EMPTY = hashlib.sha256(b"").hexdigest()
PREFIX = "OriginalReach.prefixInstallation"
CASES = {"W01": ("ReachMethod.callA", 0, 128, 187),
         "W03": ("ReachMethod.callA", 0, 128, 179),
         "W15": ("ReachMethod.callK", 6, 256, 185)}


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON key")
        out[key] = value
    return out


def read(data):
    return json.loads(data, object_pairs_hook=pairs)


def check_isolated(slot, item, candidate, case, start):
    native = item["native"]
    key = {PREFIX: "prefix", "ReachMethod.callA": "call-a", "ReachMethod.callK": "call-k"}[slot]
    src = HERE / "diagnostics" / (key + ".lean.txt")
    out = HERE / "diagnostics" / (key + ".stdout.txt")
    require(item["source"] == src.relative_to(HERE).as_posix() and item["stdout"] == out.relative_to(HERE).as_posix(),
            "portable diagnostic paths")
    unit, stdout = src.read_bytes(), out.read_bytes()
    require(sha(unit) == item["source_sha256"] and sha(stdout) == native["stdout_sha256"] and
            len(stdout) == native["stdout_bytes"], "source or diagnostic bytes")
    submitted = "\n".join("  " + line for line in candidate[slot])
    require((item["statement"] + "\n" + submitted + "\n").encode() in unit and
            not re.search(r"\bsorry(?:Ax)?\b", submitted), "submitted proof and published isolated statement")
    require(native["tag"] == case + "-isolate-" + slot and native["stop"] is None and
            native["post_group_absent"] is True and native["residual_after_wait4"] is False and
            native["stderr_bytes"] == 0 and native["stderr_sha256"] == EMPTY and
            item["retained_olean"] is False, "ordinary isolated result and poststate")
    if slot == PREFIX:
        require(native["exit"] == 0 and item["isolated_checkpoint_passed"] is True and
                item["observed_axioms"] == ["Quot.sound", "propext"] and
                stdout.decode().strip() == "'" + PREFIX + "' depends on axioms: [propext, Quot.sound]",
                "prefix elaboration and its own axiom list")
    else:
        msg = stdout.decode()
        require(native["exit"] == 1 and item["isolated_checkpoint_passed"] is False and item["observed_axioms"] is None,
                "a failed proof has no accepted axiom list")
        require("One.lean:11:50: error(lean.synthInstanceFailed)" in msg and "Decidable\n" in msg and
                f"({start} < ↑k →" in msg and "One.lean:8:84: error: unsolved goals" in msg and
                msg.rstrip().endswith("'" + slot + "' depends on axioms: [propext, sorryAx]"),
                "decidability failure, remaining goal and error recovery")


def check_summary(data, root):
    registration = (root / (PACKAGE + "-registration.json")).read_bytes()
    require(sha(registration) == data["registration_sha256"] == REGISTER, "issued registration")
    reg = read(registration)
    bindings = read((root / PACKAGE / "bindings.json").read_bytes())
    require(data["run"] == 44847287927 and data["job"] == 136670022819 and data["run_attempt"] == 1 and
            data["artifact_id"] == 14685698407 and data["hosted_artifact"]["sha256"] == ARCHIVE and
            data["attempt_id"] == reg["attempt_id"] and data["candidate_commit"] == "1f0d2a9570f87b3e407dbfb5ae627e8d0607795f" and
            data["registration_commit"] == "37e0913096e2d1fdf136278c18161ed8ede1d5e7", "registered run")
    require(data["judge_manifest_sha256"] == reg["judge_manifest_sha256"] == sha((root/PACKAGE/"manifest.json").read_bytes())
            and data["workflow_sha256"] == reg["workflow_sha256"] == sha((root/".github/workflows/three-source-original-reachable-v3.yml").read_bytes())
            and data["official_lean_archive_sha256"] == reg["stock_archive_sha256"] and STOCK in data["release"],
            "stock release and judge bytes")
    require(data["all_case_status"] == "failed" and data["all_case_error"] == "ValueError: one or more registered cases failed" and
            data["original_cases_accepted"] == 0 and data["main_commands"] == 162 and data["main_exit_counts"] == {"0":155,"1":7} and
            set(data["cases"]) == set(CASES), "campaign outcome and all three cases")
    limits = reg["limits"]
    require(data["elapsed_seconds"] < limits["campaign_seconds"] and
            max(data["max_sampled_group_rss_bytes"], data["max_direct_wait4_rss_bytes"]) < limits["group_rss_bytes"] and
            data["retained_before_final_bytes"] < limits["retained_bytes"] and
            data["scheduler"]["schedule"] == reg["schedule"] and
            data["scheduler"]["native_worker_affinity"]["during_native"] == [0], "observed resource envelope")
    require(data["allowed_axioms"] == ["Classical.choice", "Quot.sound", "propext"], "axiom policy")
    artificial = data["artificial_controls"]
    plan = read((root / "audit/research/three-source-synthetic-projection/plan.json").read_bytes())
    expected_refusals = plan["refusal_diagnostics"]
    require(artificial["fresh_modules"] == ["ConsumerSynthetic", "SyntheticRefusalsProved", "TraceCode"] and
            artificial["ordered_trace"]["codes"] == [0, 1, 2, 3, 4, 4, 4] and
            set(artificial["native_refusals"]) == set(expected_refusals), "artificial positive and negative roster")
    for name, expected in expected_refusals.items():
        row = artificial["native_refusals"][name]
        require(row["module"] == name and row["line"] == expected["line"] and
                row["diagnostic"].startswith(expected["prefix"]) and all(x in row["diagnostic"] for x in expected["contains"]),
                "artificial refusal signature " + name)
    for key, status in {"single-cpu": (0, None), "rss": (-9, "observed process-group RSS"),
                        "wall": (-9, "native or campaign time"), "next-worker": (0, None)}.items():
        r = data["cpu_control_outcomes"][key]
        require((r["exit"], r["stop"]) == status and r["post_group_absent"] is True and
                r["residual_after_wait4"] is False, "separate scheduling control " + key)
    modules = data["ordinary_module_order"]
    require(len(set(modules)) == len(modules) == data["scientific_stock_modules"] == 22 and
            modules[-2:] == ["ReachRightInverse", "ReachCheckedBody"] and "ReachCalls" in data["remaining_owners"],
            "last positive owners")
    for case, (failed, start, points, terms) in CASES.items():
        c = data["cases"][case]
        expected = reg["frozen_case_requirements"][case]
        raw = bindings["cases"][case]["input"]
        require(raw == c["raw"] and len((root/raw["relative_path"]).read_bytes()) == raw["bytes"] and
                sha((root/raw["relative_path"]).read_bytes()) == raw["sha256"] == expected["raw"] and
                c["typed_sha256"] == expected["typed"] and c["literal_sha256"] == expected["literal"] and
                c["assertions"] == bindings["cases"][case]["assertions"] and c["projected_slots"] == bindings["cases"][case]["slots"],
                "original input and assertion scope " + case)
        require(c["finite_count_required"] == points and c["finite_count_observed"] == 0 and c["named_terms_required"] == terms and
                c["named_terms_final_observed"] == 0 and c["targets_whose_ordinary_owner_was_replayed"] == 107 and
                c["case_outcome"]["status"] == "failed registered case" and c["transition"] == "continue after ordinary failed case"
                and c["case_outcome"]["error"].endswith(case + "-isolate-" + failed), "terminal stage " + case)
        require(len(c["module_fingerprints"]) == len(modules) and all(len(v) == 4 and
                all(isinstance(h,str) and re.fullmatch("[a-f0-9]{64}",h) for h in v) for v in c["module_fingerprints"]), "22 module pairs")
        require(c["case_clock"]["available_seconds"] == reg["schedule"]["case_seconds"] and
                0 < c["case_elapsed_seconds_including_custody"] < c["case_clock"]["available_seconds"] and
                max(c["max_observed_case_group_rss_bytes"],c["max_wait4_case_rss_bytes"]) < limits["group_rss_bytes"],
                "case resource scope " + case)
        payload = (HERE/"submitted"/(case+".json")).read_bytes()
        require(sha(payload) == c["submitted_sha256"] and len(read(payload)) == c["named_slots_submitted"] == expected["new_candidate_slots"],
                "candidate bytes and slots")
        require(set(c["isolated"]) == {PREFIX,failed}, "exact two isolated probes")
        for slot in (PREFIX, failed):
            check_isolated(slot, c["isolated"][slot], read(payload), case, start)
    return registration


def check_archive(path, data, registration):
    require(path.stat().st_size == data["hosted_artifact"]["bytes"] == 12508619, "original ZIP size")
    with path.open("rb") as f:
        require(hashlib.file_digest(f, "sha256").hexdigest() == ARCHIVE, "original ZIP identity")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        require(len(names) == len(archive.infolist()) == 1039 and sum(i.file_size for i in archive.infolist()) == 44837095
                and archive.testzip() is None and archive.read("registration.json") == registration, "complete native ZIP")
        get = lambda n: read(archive.read(n))
        digest = lambda n: sha(archive.read(n))
        terminal = get("result/terminal.json")
        inputs = get("result/inputs.json")
        require(inputs["science_commit"] == data["candidate_commit"] and inputs["registration_commit"] == data["registration_commit"] and
                inputs["stock_git"] == STOCK and inputs["anchors"] == data["stock_anchors"] and
                digest("result/final-custody.json") == data["final_custody_sha256"] and
                terminal["status"] == data["all_case_status"] and terminal["error"] == data["all_case_error"], "host and final custody")
        require(terminal["elapsed_seconds"] == data["elapsed_seconds"] and get("result/shared-setup-clock.json") == data["scheduler"] and
                get("result/final-custody.json")["postrun_payloads"] == inputs["payloads"] and
                get("result/artificial-controls/refusals.json") == data["artificial_controls"]["native_refusals"] and
                get("result/artificial-controls/reduction-control.json") == data["artificial_controls"]["ordered_trace"],
                "native clock, post-run inputs and synthetic controls")
        stream_rows = []
        for c in terminal["commands"]:
            p = "commands/"+c["tag"]+"/"
            require(get(p+"result.json") == c, "native command record")
            for field in ("stdout","stderr"):
                raw = archive.read(p+field)
                require(sha(raw) == c[field+"_sha256"] and len(raw) == c[field+"_bytes"], "native command output")
            stream_rows.append([c[k] for k in ("tag","exit","stdout_bytes","stdout_sha256","stderr_bytes","stderr_sha256")]+[digest(p+"result.json")])
        encoded = (json.dumps(stream_rows, indent=2, ensure_ascii=False)+"\n").encode()
        require(len(stream_rows) == 162 and sha(encoded) == data["all_main_command_streams_sha256"], "ordered complete execution")
        for case, (failed, _, _, _) in CASES.items():
            per = data["cases"][case]
            p = "result/"+case+"/"
            actions = [r for r in terminal["commands"] if r["tag"].startswith(case+"-")]
            tag = lambda action, module: case+"-"+action+"-"+module
            expected = [tag(a,m) for m in data["ordinary_module_order"] for a in ("compile","fresh")]
            expected += [tag("isolate",PREFIX),tag("isolate",failed)]
            require([r["tag"] for r in actions] == expected and all(r["exit"] == 0 for r in actions[:-1]) and
                    actions[-1]["exit"] == 1, "ordered stage results and exits")
            require(terminal["cases"][case] == get(p+"terminal.json") == per["case_outcome"] and
                    digest(p+"case-transition.json") == per["case_outcome"]["transition_sha256"], "case transition")
            require(digest(p+"source-structure.json") == per["source_structure_sha256"] and
                    digest(p+"proof-source-identities.json") == per["all_sources_sha256"] and
                    get(p+"case-transition.json")["disposition"] == per["transition"] and
                    get(p+"case-window.json") == per["case_clock"], "source structures and case window")
            for i, module in enumerate(data["ordinary_module_order"]):
                sg = "result/stage-inputs/"
                paths = [p+"sources/"+module+".lean",p+"modules/"+module+".olean",
                         sg+tag("compile",module)+".json",sg+tag("fresh",module)+".json"]
                require([digest(n) for n in paths] == per["module_fingerprints"][i] and
                        actions[2*i+1]["argv"][1:] == ["--fresh",module], "source, import receipt and fresh object")
            for slot, item in per["isolated"].items():
                probe = p+"isolated-elaborations/ReachCalls/"+slot+"/"
                cmd = "commands/"+tag("isolate",slot)+"/"
                require(archive.read(probe+"One.lean") == (HERE/item["source"]).read_bytes() and
                        archive.read(cmd+"stdout") == (HERE/item["stdout"]).read_bytes() and
                        digest(probe+"input.json") == item["input_receipt_sha256"] and
                        get(probe+"input.json")["imports"] == item["local_imports"] and
                        (probe+"result.json" in names) == item["isolated_checkpoint_passed"] and
                        probe+"One.olean" not in names, "isolated source, import and output")
            require(all(p+n not in names for n in ("modules/ReachCalls.olean","finite-ordered-output.json","readback.json")),
                    "unreached scientific stages")


def self_test(data, root):
    """Exercise meaning checks on modified in-memory records, independent of the summary digest."""
    def reject(change):
        altered=deepcopy(data)
        change(altered)
        try:
            check_summary(altered,root)
        except ValueError:
            return
        raise ValueError("incorrect summary accepted")
    reject(lambda d: d.update(original_cases_accepted=1))
    reject(lambda d: d["cases"]["W03"].update(finite_count_observed=128))
    reject(lambda d: d["cases"]["W15"].update(named_terms_final_observed=185))
    reject(lambda d: d["cases"]["W15"]["isolated"]["ReachMethod.callK"].update(observed_axioms=["propext","sorryAx"]))
    reject(lambda d: d["cases"]["W01"]["isolated"][PREFIX].update(isolated_checkpoint_passed=False))
    reject(lambda d: d["cases"]["W01"]["isolated"]["ReachMethod.callA"]["native"].update(stop="observed process-group RSS"))
    reject(lambda d: d["cases"]["W03"]["isolated"]["ReachMethod.callA"].update(retained_olean=True))
    reject(lambda d: d["cases"]["W15"]["assertions"].pop())
    reject(lambda d: d["ordinary_module_order"].pop())
    reject(lambda d: d["artificial_controls"]["ordered_trace"]["codes"].pop())
    reject(lambda d: d["artificial_controls"]["native_refusals"]["ControlWrongProjection"].update(line=3))
    reject(lambda d: d["cpu_control_outcomes"]["next-worker"].update(stop="native or campaign time"))
    reject(lambda d: d["cases"]["W15"].update(max_wait4_case_rss_bytes=1 << 34))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,help="compare the complete original hosted ZIP")
    parser.add_argument("--repository",type=Path,default=HERE.parents[2],help="checkout containing the unmodified registration and original formulas")
    parser.add_argument("--self-test",action="store_true",help="reject thirteen altered interpretations of the same records")
    args=parser.parse_args()
    raw=(HERE/"result.json").read_bytes()
    require(sha(raw)==SUMMARY,"published summary bytes")
    records=read(raw)
    reg=check_summary(records,args.repository)
    if args.archive: check_archive(args.archive,records,reg)
    if args.self_test: self_test(records,args.repository)
    print("Three ordinary proof failures, 66 compile/fresh pairs, three isolated prefix successes, zero original output rows.")
    if args.archive: print("1,039 archive members, 162 ordered native commands and their 324 output streams agree.")
    if args.self_test: print("Thirteen altered interpretations rejected.")
