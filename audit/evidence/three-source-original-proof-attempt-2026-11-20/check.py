"""Compare the retained records of the first three-input proof attempt."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REGISTRATION = REPO / "audit/research/three-source-original-first-three-attempt.json"
CONTROL = {"ControlWrongProjection", "ControlFixedVector", "ControlSatWrongSource", "ControlFalseOnFailure"}
ARCHIVE_DIGEST = "ad493f45a89be70f62c9dc5c965f2dc3ffd8b0bc162f891cbe11df8e1c41c365"
REGISTRATION_DIGEST = "c01a877dbe6adc40ec9cb699cabe4b11ae3c5f9fe37a93f8381b3e6d3e8523a6"
SUMMARY_DIGEST = "befccab0caecb6e3cd9b3feb21597c7ea3adf0505b61db74ca258556644876e6"


def require(condition, label):
    if not condition:
        raise ValueError(label)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_retained(result):
    registration_bytes = REGISTRATION.read_bytes()
    require(digest(registration_bytes) == result["registration_sha256"] == REGISTRATION_DIGEST, "registration")
    registration = json.loads(registration_bytes)
    cases = registration["cases"]
    require(cases == ["W01", "W03", "W15"] and set(result["cases"]) == set(cases), "original cases")
    require(result["attempt_id"] == registration["attempt_id"] and result["new_accepted_original_statements"] == 0,
            "attempt and outcome")
    require(result["qualified_original_archive_commit"] == registration["original_qualified_archive_commit"]
            and result["prior_input_commit"] == registration["prior_input_commit"], "source revisions")
    require(result["registered_limits"] == registration["limits"] and result["archive_sha256"] == ARCHIVE_DIGEST,
            "resource limits and archive digest")
    require(set(result["submitted_payload_sha256"]) == set(registration["allowed_write_files"]), "submitted roster")
    for name, original in registration["raw_inputs"].items():
        require(digest((REPO / original["relative_path"]).read_bytes())
                == original["sha256"] == result["original_input_sha256"][name], name)
    for path, expected in result["submitted_payload_sha256"].items():
        require(digest((HERE / "submitted" / Path(path).name).read_bytes()) == expected, path)

    commands = result["commands"]
    tags = [entry["tag"] for entry in commands]
    require(len(commands) == len(set(tags)) == result["native_commands"] == 63, "command membership")
    require(Counter(entry["exit"] for entry in commands) == {0: 58, 1: 4, -9: 1}
            and result["successful_commands"] == 58, "exit counts")
    refusals = {"controls-refuse-" + name for name in CONTROL}
    require(set(result["expected_refusals"]) == CONTROL
            and {entry["tag"] for entry in commands if entry["exit"] == 1} == refusals, "artificial controls")
    require(all(entry["stop"] is None for entry in commands[:-1]), "first stop")
    compiled = {tag.removeprefix("W01-compile-") for tag in tags[:-1] if tag.startswith("W01-compile-")}
    replayed = {tag.removeprefix("W01-fresh-") for tag in tags if tag.startswith("W01-fresh-")}
    require(compiled == replayed and len(compiled) == 19 and not any(tag.startswith(("W03-", "W15-")) for tag in tags),
            "original compilation and replay")
    require(result["case_compile_replay_pairs"] == {"W01": 19, "W03": 0, "W15": 0}, "per-case totals")
    last = result["final_command"]
    require(all(commands[-1][key] == last[key] for key in last if key in commands[-1]), "last command")
    require(last["tag"] == "W01-compile-OriginalDynamic" and last["exit"] == -9
            and last["stop"] == "observed process-group RSS", "recorded stop")
    require(last["max_observed_group_rss_bytes"] > registration["limits"]["group_rss_bytes"]
            and last["elapsed_seconds"] < registration["limits"]["subprocess_seconds"]
            and result["elapsed_seconds"] < registration["limits"]["campaign_seconds"], "resource thresholds")
    return registration_bytes


def check_archive(path, result, registration):
    require(path.stat().st_size == result["archive_bytes"] == 4597418, "archive size")
    require(digest(path.read_bytes()) == ARCHIVE_DIGEST, "original archive")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) == result["archive_members"] == 345, "archive members")
        require(archive.testzip() is None and sum(x.file_size for x in archive.infolist())
                == result["archive_uncompressed_bytes"], "archive contents")
        require(archive.read("registration.json") == registration, "archived registration")
        inputs = json.loads(archive.read("result/inputs.json"))
        require(inputs["payloads"] == result["submitted_payload_sha256"] and inputs["version"] == result["toolchain"]
                and inputs["science_commit"] == result["candidate_commit"]
                and inputs["registration_commit"] == result["registration_commit"], "native inputs")
        terminal = json.loads(archive.read("result/terminal.json"))
        require(terminal["status"] == "failed" and terminal["active_case"] == "W01"
                and set(terminal["cases"]) == {"W01"} and terminal["elapsed_seconds"] == result["elapsed_seconds"],
                "terminal result")
        require(set(terminal["commands"][-1]) >= set(result["final_command"])
                and all(terminal["commands"][-1][k] == v for k, v in result["final_command"].items()),
                "complete final measurements")
        for entry, retained in zip(terminal["commands"], result["commands"], strict=True):
            tag = entry["tag"]
            require(all(entry[key] == value for key, value in retained.items()), tag)
            require(json.loads(archive.read("commands/" + tag + "/result.json")) == entry, tag)
            for stream in ("stdout", "stderr"):
                data = archive.read("commands/" + tag + "/" + stream)
                require(len(data) == entry[stream + "_bytes"] and digest(data) == entry[stream + "_sha256"],
                        tag + " " + stream)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_archive", type=Path, nargs="?")
    args = parser.parse_args()
    summary = (HERE / "result.json").read_bytes()
    require(digest(summary) == SUMMARY_DIGEST, "retained summary of this run")
    record = json.loads(summary)
    registration = check_retained(record)
    print("63 retained command records, 19 W01 module pairs, zero completed original cases")
    if args.original_archive:
        check_archive(args.original_archive, record, registration)
        print("345 original archive members and 126 command output streams agree")
