#!/usr/bin/env python3
"""Check the historical projection and exercise the reader with tiny synthetic disk observations."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("alphabet_replay", HERE / "replay.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def must_reject(name, operation):
    try:
        operation()
    except (ValueError, KeyError, TypeError, OSError):
        return name
    raise ValueError("accepted malformed input " + name)


def retained_observations(meta, declarations, baseline):
    checks = meta["original_checks"]
    available = {**baseline["providers"], **{"project/"+n:v for n,v in baseline["project_products"].items()}}
    regions = baseline["loaded_regions"]
    replay.require(all(type(flag) is bool and key in available and available[key][0] > 0
                       and len(available[key][1]) == 64 for key, flag in regions), "original disk bindings")
    keys = {key for key, _ in regions}
    mapped = sum(flag for _, flag in regions)
    replay.require(len(keys) == len(regions) == checks["reported_regions"] and
                   mapped == checks["file_mapped_regions"] and len(keys)-mapped == checks["non_file_mapped_regions"],
                   "original region counts")
    replay.require(len(baseline["runtime"]) == meta["original_bound_runtime_files"] and
                   len(baseline["providers"]) == meta["original_bound_provider_files"] and
                   len(baseline["loaded_modules"]) == checks["modules"] and
                   all(row[1] in keys for row in baseline["loaded_modules"]), "original import inventory")
    directory = HERE / "portable-run"
    receipt = replay.decode((directory/"receipt.json").read_bytes())
    data = (directory/"dependencies.json").read_bytes()
    replay.require(receipt["dependencies_sha256"] == replay.digest(data) and
                   receipt["dependency_query_sha256"] == replay.digest((HERE/"inspection/Dependencies.lean").read_bytes())
                   and receipt["source_sha256"] == meta["source_sha256"] and
                   receipt["declarations_sha256"] == meta["declarations_sha256"], "supplement provenance")
    rows = replay.decode(data)
    roster = replay.dependency_roster(declarations)
    encoded = b"".join(b"COUNT_DEPENDENCIES "+json.dumps(row).encode()+b"\n" for row in rows)
    replay.dependencies(encoded, roster)
    theorems = set(meta["theorem_stems"])
    for row in rows:
        parts = row["name"].split(".")
        theorem = parts[0] == "PidFin3CountConsumers" or (parts[0] == "PidFin3AlphabetCounts" and parts[1] in theorems)
        replay.require(row["kind"] == ("theorem" if theorem else "definition"), "declaration kind")
        if parts[0] == "PidFin3CountConsumers":
            replay.require(row["type_constants"] == ["PidFin3CountRaw."+parts[1]] and
                           row["value_constants"] == ["PidFin3AlphabetCounts."+parts[1]], "typed consumer")
    replay.require([step["status"] for step in meta["original_steps"]] == [0]*5 and
                   meta["original_steps"][-1]["label"] == "fresh-CountEvidence" and
                   all(item["accepted_exports"] == 0 for item in meta["prior_failures"]), "historical status")


def main():
    meta, declarations, baseline, _ = replay.original()
    roster = replay.dependency_roster(declarations)
    retained_observations(meta, declarations, baseline)
    replay.require(len(roster) == 86 and len(baseline["loaded_modules"]) == 2292 and
                   len(baseline["providers"]) == 16395, "incomplete original observation")
    observed = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        a = root / "A.olean"
        a.write_bytes(b"example")
        original = {"loaded_modules": [["A","project/A.olean",False,True,False,True]]}
        known = {"project/A.olean":replay.identity(a)}
        report = {"schema":"count22-exact-objects-helper-v3","main_module":"CountEvidence",
                  "lean_githash":meta["toolchain"]["revision"],"lean_version":meta["toolchain"]["version"],
                  "direct_imports":meta["original_direct_imports"],"header_trust_level":1025,
                  "modules":[dict(zip(("module","olean","meta","exported","all","has_data"),
                                      ("A","A.olean",False,True,False,True)))],
                  "regions":[{"path":"A.olean","mapped_bytes":7,"memory_mapped":False}]}
        def check(obj, ids=known):
            return replay.check_imports(obj, original, meta, root, {}, ids, {})
        for flag in (True,False):
            report["regions"][0]["memory_mapped"] = flag
            replay.require(check(report)["file_mapped_regions"] == int(flag), "valid backing flag")
        for label, area, key, value in [
                ("missing path","regions","path","unavailable"),("size","regions","mapped_bytes",6),
                ("bool used as size","regions","mapped_bytes",True),("integer flag","regions","memory_mapped",0),
                ("effective name","modules","module","B"),("module data","modules","has_data",False),
                ("module flags","modules","all",True)]:
            changed=copy.deepcopy(report)
            changed[area][0][key]=value
            observed.append(must_reject(label, lambda:check(changed)))
        changed=copy.deepcopy(report); changed["regions"] *= 2
        observed.append(must_reject("duplicate region", lambda:check(changed)))
        changed=copy.deepcopy(report); changed["regions"]=[]
        observed.append(must_reject("missing module region",lambda:check(changed)))
        observed.append(must_reject("unbound path",lambda:check(report,{})))
        observed.append(must_reject("different disk digest",lambda:check(report,{"project/A.olean":[7,"0"*64]})))
        changed=copy.deepcopy(report); changed["lean_version"]="another version"
        observed.append(must_reject("version",lambda:check(changed)))
        observed.append(must_reject("duplicate field",lambda:replay.decode('{"a":1,"a":1}')))
    print(json.dumps({"original_semantic_rows":len(declarations.splitlines()),"supplementary_names":len(roster),
                      "accepted_mapped_flags":[True,False],"synthetic_rejections":observed}))


if __name__ == "__main__":
    main()
