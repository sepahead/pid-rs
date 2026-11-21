"""Read the archived failed finite-index calibration and its retained positive checks. No Lean execution."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


HERE = Path(__file__).resolve().parent
PACKAGE = "audit/research/index-family-control"
PARENT = "7e7085c9d24195d4f78428af99bcecdb4c7ce92d"
CHILD = "39cecc889f81f62608cf4f836cfcef20b730a80c"
REGISTRATION = "5e0c0214afe37863f0fe70fd9b489f75eb85a628289238bffd7be93a7a9c7010"
ARCHIVE = "85ccfa1c1e746b51df96a6529dea25137bb36c286fd1d03d0e45fb555ac342bc"
STOCK = "5045d0056413266e57c625dcd7c365b10e377c52"
STOCK_ARCHIVE = "47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4"
RUN, JOB, ARTIFACT = 44862925463, 136720115700, 14690508470
ORDINARY = ["IndexSpec", "IndexProofs", "IndexInline", "IndexConsumer"]
START = ["extract-official", "stock-version", "stock-commit"]
REACHED = START + [k+"-"+n for n in ORDINARY for k in ("compile", "fresh")] + ["inspect-IndexAxioms", "inspect-IndexTerms"]
UNREACHED = ["inspect-IndexTrace", "refuse-RefuseUnready", "refuse-RefuseZero", "refuse-RefuseLast"]
NAMES = ["IndexExample.leaf"+f"{i:02}" for i in range(83)] + ["IndexExample.cover"+f"{i:02}" for i in range(83, -1, -1)]
NAMES += ["IndexExample.inlineComplete", "IndexExample.namedResult", "IndexExample.singleSlotResult"]
COUNT = {"native_commands_reached": 13, "successful_native_commands": 12, "ordinary_modules": 4,
         "successful_fresh_replays": 4, "printed_transitive_axiom_rows": 170, "term_rows_emitted": 0,
         "registered_edges_confirmed_by_term_observer": 0, "native_finite_trace_rows": 0,
         "native_negative_closings": 0, "original_formulas_tested": 0}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def decode(content):
    def unique(items):
        result = dict(items)
        require(len(result) == len(items), "duplicate JSON field")
        return result
    return json.loads(content, object_pairs_hook=unique)


def info(content):
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def read_archive(path):
    require(path.stat().st_size == 534167, "archive size")
    require(info(path.read_bytes())["sha256"] == ARCHIVE, "exact hosted archive digest")
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        require(len(entries) == len({f.filename for f in entries}) == 58 and
                sum(f.file_size for f in entries) == 1608186, "exact complete ZIP size and membership")
        contents = {}
        for entry in entries:
            name = PurePosixPath(entry.filename)
            require(name.parts and str(name) == entry.filename and not name.is_absolute() and
                    ".." not in name.parts and "\\" not in entry.filename and not entry.flag_bits & 1 and
                    stat.S_IFMT(entry.external_attr >> 16) in (0, stat.S_IFREG), "ordinary ZIP data member")
            contents[entry.filename] = z.read(entry)
    return contents


def check_sources(contents, root, reg, plan):
    package = root / PACKAGE
    registered_bytes = contents["result/registration.json"]
    require(info(registered_bytes)["sha256"] == REGISTRATION and
            (root/(PACKAGE+"-registration.json")).read_bytes() == registered_bytes, "original registered source")
    require(reg["stock_git"] == STOCK and reg["stock_archive"] == STOCK_ARCHIVE and
            reg["limits"] == plan["limits"] == {"campaign_seconds": 2700, "subprocess_seconds": 900,
                "group_rss_bytes": 4 << 30, "retained_bytes": 1 << 30}, "original stock and limits")
    require(plan["ordinary"] == ORDINARY and plan["observers"] == ["IndexAxioms", "IndexTerms", "IndexTrace"] and
            list(plan["refusals"]) == [s.removeprefix("refuse-") for s in UNREACHED[1:]] and
            list(plan["targets"]) == NAMES and sum(map(len, plan["edges"].values())) == 254, "registered questions")
    manifest_bytes = (package/"manifest.json").read_bytes()
    require(info(manifest_bytes)["sha256"] == reg["judge_manifest"], "registered judge")
    for name, descriptor in decode(manifest_bytes)["files"].items():
        require(info((package/name).read_bytes()) == descriptor, "fixed judge file "+name)
    for name, descriptor in decode((package/"reuse.json").read_bytes())["files"].items():
        require(info((root/name).read_bytes()) == descriptor, "fixed reused source "+name)
    supplied = (HERE/"submitted.json").read_bytes()
    require(info(supplied) == reg["submission"], "exact supplied artificial payload")
    slots = decode(supplied)
    require(list(slots) == plan["slots"] and len(slots) == 84, "84 registered proof slots")
    sources = {k.rsplit("/", 1)[1]: v for k, v in contents.items() if k.startswith("result/sources/")}
    require({n: info(b)["sha256"] for n, b in sources.items()} == reg["materialized_sources"] and len(sources) == 10,
            "all ten source units")
    seen = []
    for name, content in sources.items():
        if name in ("IndexProofs.lean", "IndexInline.lean"):
            template = (package/"lean"/(name+".in")).read_text()
            def insert(match):
                key = match[1]
                seen.append(key)
                return "\n".join("  "+line for line in slots[key])
            expected = re.sub(r"^@@PROOF ([A-Za-z0-9_.]+)@@$", insert, template, flags=re.M).encode()
        else:
            expected = (package/"lean"/name).read_bytes()
        require(content == expected, "source assembly "+name)
    require(len(seen) == len(set(seen)) == 84 and set(seen) == set(slots), "each submitted slot used once")
    return sources


def axiom_names(text):
    expected = [f"'{name}' depends on axioms: [propext]" if name != "IndexExample.cover83"
                else "'IndexExample.cover83' does not depend on any axioms" for name in NAMES]
    require(text.splitlines() == expected, "all ordered native axiom statements")
    return len(expected)


def terminal_outcome(terminal):
    require(terminal["status"] == "failed invented calibration" and
            terminal["attempt"] == "INVENTED-83-POSITION-CONSTRUCTIVE-20261121-01" and
            terminal["error"] == "RuntimeError: unexpected native outcome or diagnostics at inspect-IndexTerms" and
            terminal["elapsed_seconds"] == 212.168555506, "actual failed native disposition")


def native_outcome(row):
    require(row["tag"] == "inspect-IndexTerms" and row["exit"] == -9 and row["stop"] == "observed process-group RSS" and
            row["max_observed_group_rss_bytes"] == row["direct_wait4_maxrss_bytes"] == 4438499328 > (4 << 30) and
            row["group_rss_sample_count"] == 31 and row["stdout_bytes"] == row["stderr_bytes"] == 0 and
            row["post_group_absent"] is True and row["residual_after_wait4"] is False, "term observer memory stop")


def counts(counts):
    require(set(counts) == set(COUNT) and all(type(counts[k]) is int and counts[k] == v for k, v in COUNT.items()),
            "actual reached, completed and missing predicates")


def presence(members, expected):
    require(set(members) == expected, "all partial archive members and no fabricated completion")


def read(root, archive):
    contents = read_archive(archive)
    record_bytes = (HERE/"record.json").read_bytes()
    require(info(record_bytes)["sha256"] == "76fcf3226ea47ff9bd6e7f2086a81a5774f69fce882b68d15ef3d10e0fbc988b", "fixed portable register")
    record = decode(record_bytes)
    inventory = {k: info(b) for k, b in contents.items()}
    require(record["schema"] == "archived-invented-index-control-v1" and record["complete_inventory"] == inventory and
            record["archive"] == {"bytes": 534167, "sha256": ARCHIVE} and
            record["submitted_source"] == info((HERE/"submitted.json").read_bytes()), "published object and complete contents")
    require(record["status"] == "failed invented calibration" and record["enrolled_artificial_pushes"] == 1 and
            record["blocked_next_route"] == "any original contingent on this calibration", "publication disposition")
    counts(record["counts"])
    remote = record["provenance"]
    branch = "review/index-family-control/"+PARENT+"-"+REGISTRATION
    require(remote["run"]["id"] == remote["job"]["run_id"] == RUN and remote["job"]["id"] == JOB and
            remote["run"]["workflow_id"] == 425667077 and remote["run"]["event"] == "push" and
            remote["run"]["run_attempt"] == remote["job"]["run_attempt"] == 1 and
            remote["run"]["head_sha"] == remote["job"]["head_sha"] == CHILD and
            remote["run"]["head_branch"] == remote["job"]["head_branch"] == branch and
            remote["run"]["status"] == remote["job"]["status"] == "completed" and
            remote["run"]["conclusion"] == remote["job"]["conclusion"] == "failure" and
            remote["branch-runs"]["total_count"] == 1 and remote["artifact"]["id"] == ARTIFACT and
            remote["artifact"]["digest"] == "sha256:"+ARCHIVE and remote["artifact"]["size_in_bytes"] == 534167,
            "publication identifies the failed first hosted attempt")
    require(decode(contents["launch.json"]) == {"run": RUN, "attempt": 1, "commit": CHILD, "registration_commit": PARENT,
                                                "registration_sha256": REGISTRATION}, "archived launch envelope")
    get = lambda name: contents["result/"+name]
    reg = decode(get("registration.json"))
    plan = decode((root/PACKAGE/"plan.json").read_bytes())
    sources = check_sources(contents, root, reg, plan)
    terminal = decode(get("terminal.json"))
    terminal_outcome(terminal)
    objects = {n.rsplit("/", 1)[1]: info(b) for n, b in contents.items() if n.startswith("result/objects/")}
    require(set(objects) == {n+".olean" for n in [*ORDINARY, "IndexAxioms"]}, "five compiled objects")
    expected = {"launch.json", "result/registration.json", "result/stages.json", "result/terminal.json"}
    expected.update("result/sources/"+n for n in sources)
    expected.update("result/objects/"+n for n in objects)
    expected.update(f"result/commands/{tag}/{file}" for tag in REACHED for file in ("result.json", "stdout", "stderr"))
    presence(contents, expected)
    stages = decode(get("stages.json"))
    require(len(stages) == 10, "all attempted source and import transitions")
    prior, receipts, last_elapsed = {}, {}, 0
    for i, tag in enumerate(REACHED):
        prefix = "commands/"+tag+"/"
        native = decode(get(prefix+"result.json"))
        receipts[tag] = info(get(prefix+"result.json"))
        require(native["tag"] == tag and native["stage"] == "invented finite-index qualification" and
                native["post_group_absent"] is True and native["residual_after_wait4"] is False and
                0 < native["elapsed_seconds"] <= 900 and last_elapsed <= native["campaign_elapsed_seconds"] <= terminal["elapsed_seconds"] and
                native["retained_before_receipt_bytes"] <= 1 << 30, "native resource and cleanup "+tag)
        last_elapsed = native["campaign_elapsed_seconds"]
        for stream in ("stderr", "stdout"):
            require(info(get(prefix+stream)) == {"bytes": native[stream+"_bytes"], "sha256": native[stream+"_sha256"]}, "native stream "+tag)
        require(native["stderr_bytes"] == 0 and (native["stdout_bytes"] > 0) == (tag in ("stock-version", "stock-commit", "inspect-IndexAxioms")),
                "native diagnostic coverage "+tag)
        if tag == "inspect-IndexTerms":
            native_outcome(native)
        else:
            require(native["exit"] == 0 and native["stop"] is None and
                    max(native["max_observed_group_rss_bytes"], native["direct_wait4_maxrss_bytes"]) <= 4 << 30,
                    "successful preceding command "+tag)
        if i < 3:
            continue
        kind, module = tag.split("-", 1)
        imports = re.findall(r"^import (\S+)$", sources[module+".lean"].decode(), re.M)
        local = {x+".olean": prior[x+".olean"] for x in imports if x+".lean" in sources}
        require(stages[i-3] == {"kind": kind, "module": module, "source": info(sources[module+".lean"]),
                                "local_imports": local, "preceding": prior}, "source and compiled import identities")
        argv = native["argv"]
        if kind == "fresh":
            require(PurePosixPath(argv[0]).name == "leanchecker" and argv[1:] == ["--fresh", module] and module+".olean" in prior,
                    "fresh check of prior output "+module)
        else:
            require(PurePosixPath(argv[0]).name == "lean" and argv[1:3] == ["-DwarningAsError=true", "-R"] and
                    argv[4] == "-o" and PurePosixPath(argv[5]).name == module+".olean" and argv[6] == module+".lean",
                    "ordinary native compiler "+module)
            if tag != "inspect-IndexTerms":
                prior[module+".olean"] = objects[module+".olean"]
    require(prior == objects and receipts == record["native_command_receipts"], "complete native command receipts and outputs")
    require(get("commands/stock-commit/stdout").decode().strip() == STOCK and
            get("commands/stock-version/stdout").decode().strip() == f"Lean (version 4.34.1, x86_64-unknown-linux-gnu, commit {STOCK}, Release)",
            "stock release identity")
    ax = get("commands/inspect-IndexAxioms/stdout").decode()
    axiom_names(ax)
    return {"status": record["status"], "run": RUN, "artifact": ARTIFACT, "counts": COUNT,
            "resource_stop_bytes": 4438499328, "rss_limit_bytes": 4 << 30, "unreached": UNREACHED,
            "expanded_files": len(contents), "archive_sha256": ARCHIVE}, (terminal, native, ax, expected)


def self_test(observations):
    terminal, row, ax, expected = observations
    variants = [
        ("terminal changed to accepted", terminal_outcome, {**terminal, "status": "accepted invented calibration"}),
        ("native kill changed to success", native_outcome, {**row, "exit": 0}),
        ("missing observer output marked present", native_outcome, {**row, "stdout_bytes": 1}),
        ("resource stop changed to timeout", native_outcome, {**row, "stop": "native or campaign time"}),
        ("memory claim reduced to limit", native_outcome, {**row, "max_observed_group_rss_bytes": 4 << 30}),
        ("leftover child hidden", native_outcome, {**row, "residual_after_wait4": True}),
        ("axiom replaced", axiom_names, ax.replace("propext", "sorryAx", 1)),
        ("empty-tail disposition removed", axiom_names, "\n".join(s for s in ax.splitlines() if "'IndexExample.cover83'" not in s)),
        ("doubled leaf row", axiom_names, ax+ax.splitlines()[0]+"\n"),
        ("edges promoted", counts, {**COUNT, "registered_edges_confirmed_by_term_observer": 254}),
        ("finite rows promoted", counts, {**COUNT, "native_finite_trace_rows": 332}),
        ("negative controls promoted", counts, {**COUNT, "native_negative_closings": 3}),
        ("original evaluation promoted", counts, {**COUNT, "original_formulas_tested": 1}),
        ("archived object removed", lambda n: presence(n, expected), expected-{"result/objects/IndexConsumer.olean"}),
        ("completion file added", lambda n: presence(n, expected), expected|{"result/observed.json"}),
    ]
    refused = []
    for name, check, value in variants:
        try:
            check(deepcopy(value))
        except ValueError:
            refused.append(name)
        else:
            raise ValueError("admitted adverse interpretation: "+name)
    return refused


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=HERE.parents[2], help="checkout containing the registered judge sources")
    parser.add_argument("--archive", type=Path, default=HERE/"native-evidence.zip", help="exact original public GitHub ZIP")
    parser.add_argument("--self-test", action="store_true", help="reject altered interpretations of the same record")
    args = parser.parse_args()
    result, observations = read(args.repository, args.archive)
    if args.self_test:
        result["adverse_interpretations_rejected"] = self_test(observations)
    print(json.dumps(result, sort_keys=True))
