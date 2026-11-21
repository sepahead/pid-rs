"""Replay the frozen attribution reader on the original ZIP. No native Lean execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


HERE = Path(__file__).resolve().parent
RECORD_SHA256 = "9e38ac29917c310df1678edddb0c210a7e5c115182cd037c095abfa5fa3a17da"
SELF_TEST_STDOUT = "e709e33deb0ccff94c2e53b477d3be2db655086eae11f2379aafebdd40e1e4ec"
OPERATOR = "audit/research/index-family-native-attribution-v1/check.py"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def info(data):
    return {"bytes":len(data), "sha256":hashlib.sha256(data).hexdigest()}


def checked_file(path, expected):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size == expected["bytes"],
            "regular file and size: " + str(path))
    with path.open("rb") as stream:
        data = stream.read(expected["bytes"] + 1)
    require(info(data) == expected, "file identity: " + str(path))
    return data


def git(cwd, env, *args, content=None):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(cwd), *args],
                                   input=content, env=env, timeout=30)


def git_environment():
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(key, None)
    env.update(GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")
    return env


def source_view(repository, view, record, env):
    issue = record["registration"]
    directory = Path(git(repository, env, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
    # Four objects became reachable in the child. The pack also contains the earlier submission blob.
    store = view / ".git"
    (store / "objects/info").mkdir(parents=True)
    (store / "refs").mkdir()
    (store / "config").write_text("[core]\n\trepositoryformatversion = 0\n\tbare = false\n")
    (store / "HEAD").write_text(issue["child"] + "\n")
    (store / "objects/info/alternates").write_text(str(directory / "objects") + "\n")
    git(view, env, "cat-file", "-e", issue["registration_commit"] + "^{commit}")
    frozen = checked_file(HERE / "issued-child.pack", record["published_inputs"]["issued-child.pack"])
    require(frozen[:12] == bytes.fromhex("5041434b0000000200000005")
            and hashlib.sha1(frozen[:-20]).digest() == frozen[-20:], "five entries in the original Git pack")
    pack_id = frozen[-20:].hex()
    index_output = git(view, env, "index-pack", "--stdin", "--fix-thin", content=frozen)
    require(index_output == ("pack\t" + pack_id + "\n").encode(), "verified pack identity")
    index = store / "objects" / "pack" / ("pack-" + pack_id + ".idx")
    packed = {}
    for line in git(view, env, "verify-pack", "-v", str(index)).splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[1] in {b"commit", b"tree", b"blob", b"tag"}:
            packed[fields[0].decode("ascii")] = fields[1].decode("ascii")
    parent, child = issue["registration_commit"], issue["child"]
    earlier_name = "audit/evidence/index-family-control-attempt-2026-11-21/submitted.json"
    issued_name = "audit/research/index-family-observer-v4-submission.json"
    previous = git(view, env, "rev-parse", parent + ":" + earlier_name).decode("ascii").strip()
    added = git(view, env, "rev-parse", child + ":" + issued_name).decode("ascii").strip()
    new = {row.split()[0] for row in git(view, env, "rev-list", "--objects", child, "^" + parent).decode("ascii").splitlines()}
    require(previous == added and packed.get(previous) == "blob" and previous not in new
            and set(packed) == new | {previous} and sorted(packed[key] for key in new) == ["commit", "tree", "tree", "tree"],
            "four newly reachable objects and one reused submission")
    require(git(view, env, "rev-list", "--parents", "-n", "1", "HEAD").decode().split()
            == [issue["child"], issue["registration_commit"]], "one authorized child and parent")
    for name, expected in record["checkout_files"].items():
        spec = issue["child"] + ":" + name
        require(int(git(view, env, "cat-file", "-s", spec)) == expected["bytes"], "Git size: " + name)
        data = git(view, env, "cat-file", "blob", spec)
        require(info(data) == expected, "frozen source: " + name)
        dst = view / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)


def unique_fields(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "duplicate native row field")
    return result


def raw_term_prefix(archive_path, plan, record):
    """Read only the names and bytes of the completed prefix, independently of its uses."""
    wanted = record["supported"]["completed_term_observers"]
    rows, size, joined = [], 0, hashlib.sha256()
    max_total = record["original_zip"]["expanded_bytes"]
    with zipfile.ZipFile(archive_path) as archive:
        for part in plan["shards"][:wanted]:
            member = archive.getinfo("result/commands/inspect-" + part["module"] + "/stdout")
            require(0 < member.file_size <= max_total - size, "bounded original part")
            with archive.open(member) as stream:
                for name in part["targets"]:
                    line = stream.readline(member.file_size + 1)
                    require(line.startswith(b"W02_TERM ") and line.endswith(b"\n"), "complete native row")
                    row = json.loads(line[len(b"W02_TERM "):], object_pairs_hook=unique_fields)
                    require(row["name"] == name, "name and order in native part")
                    rows.append(name)
                    size += len(line)
                    joined.update(line)
                require(not stream.read(1), "extra native row")
    require(len(rows) == len(set(rows)) == record["supported"]["raw_rows_expected_from_first_84_command_outputs"],
            "registered prefix name count")
    prefix = {"named_rows":len(rows), "bytes":size, "sha256":joined.hexdigest()}
    require(prefix == record["supported"]["checked_raw_prefix"], "exact names and bytes of the observed prefix")
    return prefix


def replay(repository, record, self_test):
    mode = {0:"normal", 1:"optimized"}.get(sys.flags.optimize)
    require(mode is not None, "choose ordinary Python or -O")
    receipt = record["mode_receipts"][mode]
    env = git_environment()
    with tempfile.TemporaryDirectory(prefix="index-family-record-") as directory:
        tmp = Path(directory)
        view, evidence, output = (tmp / n for n in ("source", "evidence", "output"))
        source_view(repository, view, record, env)
        evidence.mkdir()
        for name in ("run.json", "job.json", "branch-runs.json", "artifacts.json", "artifact.json"):
            shutil.copyfile(HERE / "hosted" / name, evidence / name)
        shutil.copyfile(HERE / "native-evidence.zip", evidence / "native.zip")
        options = ["-O"] if mode == "optimized" else []
        command = [sys.executable, "-I", "-S", "-B", *options, str(view / OPERATOR),
                   "--addendum-sha256", record["registration"]["addendum_sha256"]]
        if self_test:
            controls = subprocess.run([*command, "--self-test"], env=env, cwd=view,
                                      capture_output=True, timeout=60, check=True)
            require(info(controls.stdout)["sha256"] == SELF_TEST_STDOUT and not controls.stderr,
                    "archived reader control outcome")
        process = subprocess.run([*command, "--issue", str(HERE/"issue.json"), "--ids", str(HERE/"ids.json"),
                                  "--evidence", str(evidence), "--output", str(output)],
                                 env=env, cwd=view, capture_output=True, timeout=180)
        require(process.returncode == receipt["exit"] == 2 and info(process.stdout) == receipt["stdout"]
                and info(process.stderr) == receipt["stderr"], "frozen native readback disposition")
        files = receipt["frozen_reader_output_files"]
        require({p.name for p in output.iterdir()} == set(files), "all five original output files")
        for name, expected in files.items():
            actual = checked_file(output/name, expected)
            if name in ("attribution.json", "v4.original-readback.json"):
                require(actual == (HERE/"readback"/mode/name).read_bytes(), "archived mode result: " + name)
        plan = json.loads((view/"audit/research/index-family-observer-v4/plan.json").read_bytes())
        prefix = raw_term_prefix(HERE/"native-evidence.zip", plan, record)
        return (json.loads((output/"attribution.json").read_bytes()),
                json.loads((output/"v4.original-readback.json").read_bytes()), prefix)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=HERE.parents[2],
                        help="full pid-rs clone containing the original registration parent")
    parser.add_argument("--self-test", action="store_true", help="also replay the frozen reader controls")
    args = parser.parse_args()
    record = json.loads(checked_file(HERE/"record.json", {"bytes":20240, "sha256":RECORD_SHA256}))
    for name, expected in record["published_inputs"].items():
        checked_file(HERE/name, expected)
    attribution, result, prefix = replay(args.repository.resolve(), record, args.self_test)
    with zipfile.ZipFile(HERE/"native-evidence.zip") as archive:
        directory = archive.infolist()
        require(len(directory) == record["original_zip"]["members"] and
                sum(v.file_size for v in directory) == record["original_zip"]["expanded_bytes"], "bounded original ZIP")
        member = archive.getinfo("result/commands/inspect-IndexTermsPart085/result.json")
        require(0 < member.file_size < 65536, "bounded failed command receipt")
        command = json.loads(archive.read(member))
    row = result["observed_command_prefix"][-1]
    expected = record["supported"]
    require(command["direct_wait4_maxrss_bytes"] == expected["direct_wait4_bytes"] and
            command["max_observed_group_rss_bytes"] == row["observed_group_rss"] == expected["sampled_process_group_bytes"]
            and row["stop"] == expected["stop"] and row["exit"] == expected["exit"], "observed failing invocation")
    print(json.dumps({"calibration":result["status"], "native_attribution":attribution["status"],
                      "run":record["event"]["run"], "completed_term_observers":expected["completed_term_observers"],
                      "failed_command":row["command"], "assigned":result["assigned_theorems"],
                      "observed_group_rss_bytes":row["observed_group_rss"],
                      "printed_axiom_sets":attribution["axiom_output"]["sets"]["value"],
                      "raw_term_prefix":prefix, "originals":attribution["native_scientific_originals"]}, sort_keys=True))


if __name__ == "__main__":
    main()
