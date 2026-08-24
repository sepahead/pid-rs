#!/usr/bin/env python3
"""Validate the terminal, zero-credit composite-v12 preservation boundary."""

from __future__ import annotations

import sys


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-m1a-composite-v12-terminal.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, NoReturn

ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
JSON_SCHEMA_SUBSET_PATH = ROOT / "scripts/json_schema_subset.py"
_schema_specification = importlib.util.spec_from_file_location(
    "pid_rs_ksg_v12_terminal_json_schema_subset", JSON_SCHEMA_SUBSET_PATH
)
if _schema_specification is None or _schema_specification.loader is None:
    print("ERROR: cannot load the local JSON-schema subset validator", file=sys.stderr)
    raise SystemExit(2)
_schema_module = importlib.util.module_from_spec(_schema_specification)
sys.modules[_schema_specification.name] = _schema_module
_schema_specification.loader.exec_module(_schema_module)
SchemaValidationError = _schema_module.SchemaValidationError
validate_json_schema = _schema_module.validate

REPOSITORY = "sepahead/pid-rs"
C11 = "91d954160a7e717ae46b6088175ae52e92570127"
C12 = "01466e88b0550333c2718f1716289e9642e30dc6"
C12_TREE = "c445a647963ac12fbe1c352cc042956a82c7d69e"
C12_MESSAGE = "Repair KSG M1a composite v12 contract\n"
R12_MESSAGE = "Record KSG M1a composite v12 receipt\n"
RECORD = "audit/evidence/ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json"
SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-v12-terminal-failure.schema.json"
CHECKER = "scripts/check-ksg-m1a-composite-v12-terminal.py"
SELF_TEST = "scripts/check-ksg-m1a-composite-v12-terminal-self-test.py"
WORKFLOW = ".github/workflows/ksg-m1a-composite-v12.yml"
JUSTFILE = "justfile"
RECORD_SHA256 = "375bf287c73dea35c70d21c74be58e54fe17ae27b4c38ebd9cdf543c8beab47c"
RECORD_SIZE = 13_644
SCHEMA_SHA256 = "2152411c804df3a75f6b106ae97761f4812adf2ae8ca963a98a296df812c0e5e"
SCHEMA_SIZE = 12_907
R12_EVIDENCE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v12-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v12-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v12-2026-08-23.json",
)

EXPECTED_DELTA = (
    ("M", ".github/workflows/ksg-m1a-composite-v11.yml", "100644"),
    ("A", ".github/workflows/ksg-m1a-composite-v12.yml", "100644"),
    ("M", "CHANGELOG.md", "100644"),
    ("M", "audit/evidence/current-source-state-v1.json", "100644"),
    (
        "A",
        "audit/evidence/ksg-rev4-m1a-composite-v11-local-closure-failure-v12-2026-08-23.json",
        "100644",
    ),
    (
        "A",
        "audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md",
        "100644",
    ),
    (
        "A",
        "audit/evidence/ksg-rev4-m1a-composite-v12-path-policy-v1.json",
        "100644",
    ),
    (
        "A",
        "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v12.schema.json",
        "100644",
    ),
    (
        "A",
        "audit/schemas/ksg-rev4-m1a-composite-local-closure-v12.schema.json",
        "100644",
    ),
    (
        "A",
        "audit/schemas/ksg-rev4-m1a-composite-receipt-v12.schema.json",
        "100644",
    ),
    (
        "A",
        "audit/schemas/ksg-rev4-m1a-composite-v11-failure-v12.schema.json",
        "100644",
    ),
    ("M", "justfile", "100644"),
    ("A", "scripts/capture-ksg-m1a-composite-v12-local-closure.py", "100644"),
    ("A", "scripts/capture-ksg-m1a-composite-v12.py", "100644"),
    ("M", "scripts/check-certified-sxpid2-claim-self-test.py", "100644"),
    ("M", "scripts/check-certified-sxpid2-claim.py", "100644"),
    ("A", "scripts/check-ksg-m1a-composite-v12-self-test.py", "100644"),
    ("A", "scripts/check-ksg-m1a-composite-v12.py", "100644"),
    ("M", "scripts/check-lean-toolchain-freeze-self-test.py", "100644"),
    ("M", "scripts/check-lean-toolchain-freeze.py", "100644"),
)

HISTORICAL_SOURCES = (
    {
        "git_blob_oid": "05f8659dafd2ab07c0e03278c26c2cbf920996b7",
        "path": WORKFLOW,
        "role": "historical_exact_c12_dedicated_workflow_source",
        "sha256": "f6e58072ba2fdd3a7346b638fec4f671b8d256bd8ffbde469f295c331f945bab",
        "size_bytes": 5_577,
    },
    {
        "git_blob_oid": "827b33aced620110e55576987e5a064adda16643",
        "path": "scripts/check-ksg-m1a-composite-v12.py",
        "role": "historical_exact_c12_checker_source_not_reached_by_dedicated_failure",
        "sha256": "fb28f2a4e1c27c1f8f15def1ff4dfa16647f21a555888c46371614695dcb897c",
        "size_bytes": 81_394,
    },
)

EXPECTED_QUALIFICATION = {
    "ci12_attempt_1": "terminal_failure",
    "codeql12_attempt_1": "terminal_success",
    "dedicated12_attempt_1": "terminal_failure",
    "formula": (
        "Q12 = L12 AND CI12_attempt1 AND CodeQL12_attempt1 AND Dedicated12_attempt1"
    ),
    "hosted_qualification_credit": "zero",
    "l12": "not_adjudicated",
    "q12": False,
    "q12_evaluation": (
        "false_for_either_boolean_value_of_L12_because_CI12_attempt1_and_"
        "Dedicated12_attempt1_are_false"
    ),
    "r12": "permanently_unissued",
}

EXPECTED_RUNS = {
    "codeql": {
        "attempt": 1,
        "conclusion": "success",
        "event": "dynamic",
        "head_sha": C12,
        "job_counts": {"failure": 0, "other": 0, "success": 4, "total": 4},
        "run_attempt": 1,
        "run_id": 32665994793,
        "run_number": 138,
        "status": "completed",
        "workflow_id": 310582096,
        "workflow_definition_name": "CodeQL",
    },
    "dedicated_v12": {
        "attempt": 1,
        "conclusion": "failure",
        "event": "push",
        "head_sha": C12,
        "job_counts": {"failure": 1, "other": 0, "success": 0, "total": 1},
        "run_attempt": 1,
        "run_id": 32665995620,
        "run_number": 1,
        "status": "completed",
        "workflow_id": 340771655,
        "workflow_definition_name": "KSG M1a composite v12",
    },
    "repository_ci": {
        "attempt": 1,
        "conclusion": "failure",
        "event": "push",
        "head_sha": C12,
        "job_counts": {"failure": 4, "other": 0, "success": 41, "total": 45},
        "run_attempt": 1,
        "run_id": 32665995643,
        "run_number": 204,
        "status": "completed",
        "workflow_id": 297369773,
        "workflow_definition_name": "CI",
    },
}

EXPECTED_LOGS = {
    97259335595: (
        "Validate fresh C11-to-C12 bounded contract",
        "ERROR: git exclude mode changed",
        18_127,
        "c538c753e823f32dad7865f5fda61a763dd0972f2283fd052903764c5dfa0387",
    ),
    97259335615: (
        "Formal proof cores, frozen Lean 4.33.0 replay, and historical packet custody",
        "ERROR: git exclude mode changed",
        15_674,
        "e341d9602c79bf08bcea689ad6090255065efd5e100ec454c3e22813074e050c",
    ),
    97259335637: (
        "Formal LaTeX / PDF inventory and cross-toolchain structure",
        "ERROR: git exclude mode changed",
        15_664,
        "ed322ede641abd781aaa326e1052c1507b2a8ee2080767e9fea97cbbb8f30930",
    ),
    97259335845: (
        "Release scope and scientific evidence coherence",
        "Markdown math check failed with 6 finding(s)",
        108_732,
        "39d73fd91f09e933991d9b5aa1b03ddc69991a9531cc458f2a0bf7c39038fc0f",
    ),
    97259335897: (
        "Secret scan (full history)",
        "leaks found: 1",
        33_225,
        "c3441e9d78a95c26489165e3d11a419e395507b914ce9cd75223f6f05dcb2d22",
    ),
}


class ContractError(RuntimeError):
    """The terminal preservation contract is not satisfied."""


def refuse(message: str) -> NoReturn:
    raise ContractError(message)


def require(predicate: bool, message: str) -> None:
    if not predicate:
        refuse(message)


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    require(type(value) is dict and set(value) == expected, f"{label} keys changed")
    return value


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def parse_json(raw: bytes, label: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"), object_pairs_hook=reject_duplicates
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        refuse(f"{label} is not strict canonical JSON: {error}")


def stable_read(relative: str, expected_size: int, expected_sha256: str) -> bytes:
    path = ROOT / relative
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == expected_size,
        f"{relative} metadata changed",
    )
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        require(
            (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
                opened.st_nlink,
                opened.st_size,
            )
            == (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_nlink,
                before.st_size,
            ),
            f"{relative} opened identity changed",
        )
        chunks: list[bytes] = []
        remaining = expected_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", f"{relative} short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"{relative} grew while read")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            f"{relative} changed while read",
        )
    raw = b"".join(chunks)
    require(
        hashlib.sha256(raw).hexdigest() == expected_sha256,
        f"{relative} digest changed",
    )
    return raw


def git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
    path = os.environ.get("PATH")
    require(type(path) is str and bool(path), "PATH is absent")
    environment = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": path,
        "TZ": "UTC",
        "XDG_CONFIG_HOME": "/nonexistent",
    }
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        env=environment,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    require(
        completed.returncode == 0,
        f"Git command failed closed: {' '.join(arguments)}",
    )
    return completed.stdout


def git_success(*arguments: str) -> bool:
    path = os.environ.get("PATH")
    require(type(path) is str and bool(path), "PATH is absent")
    environment = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": path,
        "TZ": "UTC",
        "XDG_CONFIG_HOME": "/nonexistent",
    }
    completed = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )
    require(completed.returncode in {0, 1}, "Git ancestry probe failed closed")
    return completed.returncode == 0


def tree_entry(commit: str, path: str) -> tuple[str, str] | None:
    raw = git("ls-tree", commit, "--", path)
    if raw == b"":
        return None
    line = raw.decode("utf-8", errors="strict").rstrip("\n")
    metadata, returned_path = line.split("\t", 1)
    mode, kind, oid = metadata.split(" ")
    require(kind == "blob" and returned_path == path, f"unexpected tree entry: {path}")
    return mode, oid


def validate_subject(value: Any) -> None:
    subject = exact_keys(
        value,
        {
            "c11_parent",
            "c12_commit",
            "c12_delta_count",
            "c12_delta_paths",
            "c12_message",
            "c12_tree",
            "c12_unsigned",
        },
        "subject",
    )
    expected_rows = [
        {"change": change, "mode": mode, "path": path}
        for change, path, mode in EXPECTED_DELTA
    ]
    require(
        subject
        == {
            "c11_parent": C11,
            "c12_commit": C12,
            "c12_delta_count": len(EXPECTED_DELTA),
            "c12_delta_paths": expected_rows,
            "c12_message": C12_MESSAGE,
            "c12_tree": C12_TREE,
            "c12_unsigned": True,
        },
        "exact C12 subject changed",
    )


def validate_runs(value: Any) -> None:
    hosted = exact_keys(
        value, {"codeql", "dedicated_v12", "repository_ci"}, "hosted attempt-1"
    )
    for role, expected in EXPECTED_RUNS.items():
        run = hosted[role]
        require(type(run) is dict, f"{role} run is not an object")
        for key, expected_value in expected.items():
            require(run.get(key) == expected_value, f"{role} {key} changed")
        require(
            run.get("head_branch") == "main"
            and run.get("html_url")
            == f"https://github.com/sepahead/pid-rs/actions/runs/{expected['run_id']}",
            f"{role} branch or URL changed",
        )

    codeql = hosted["codeql"]
    require(
        codeql.get("logs_captured_by_this_record") is False
        and type(codeql.get("jobs")) is list
        and len(codeql["jobs"]) == 4
        and {job.get("job_id") for job in codeql["jobs"]}
        == {97259336021, 97259336162, 97259336240, 97259336277}
        and all(job.get("conclusion") == "success" for job in codeql["jobs"]),
        "CodeQL job preservation changed",
    )

    failed = [
        *hosted["dedicated_v12"].get("failed_jobs", []),
        *hosted["repository_ci"].get("failed_jobs", []),
    ]
    require(len(failed) == 5, "failed hosted job count changed")
    require(
        [job.get("job_id") for job in hosted["dedicated_v12"]["failed_jobs"]]
        == [97259335595]
        and [job.get("job_id") for job in hosted["repository_ci"]["failed_jobs"]]
        == [97259335615, 97259335637, 97259335845, 97259335897],
        "failed hosted job ordering changed",
    )
    for job in failed:
        job_id = job.get("job_id")
        require(job_id in EXPECTED_LOGS, "unexpected failed hosted job")
        name, marker, size_bytes, digest = EXPECTED_LOGS[job_id]
        require(
            job.get("name") == name
            and job.get("bounded_log_marker") == marker
            and job.get("conclusion") == "failure"
            and job.get("log_retrieval")
            == {
                "classification": "unauthenticated_retrieval_bytes",
                "sha256": digest,
                "size_bytes": size_bytes,
            },
            f"failed hosted job binding changed: {job_id}",
        )
    for job_id in (97259335595, 97259335615, 97259335637):
        job = next(item for item in failed if item["job_id"] == job_id)
        require(
            job.get("mode_or_cause_adjudication") == "not_adjudicated",
            "git-exclude diagnostic was over-adjudicated",
        )
    secret = next(item for item in failed if item["job_id"] == 97259335897)
    require(
        secret.get("finding_adjudication") == "not_adjudicated",
        "secret-scan finding was over-adjudicated",
    )


def validate_record_semantics(value: Any) -> None:
    root = exact_keys(
        value,
        {
            "custody",
            "historical_c12_source",
            "hosted_attempt_1",
            "nonimplications",
            "qualification",
            "repository",
            "schema",
            "schema_revision",
            "subject",
        },
        "terminal record",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-v12-terminal-failure/v1"
        and root["schema_revision"] == 1,
        "terminal record identity changed",
    )
    validate_subject(root["subject"])
    validate_runs(root["hosted_attempt_1"])
    require(root["qualification"] == EXPECTED_QUALIFICATION, "Q12 boundary changed")

    custody = root["custody"]
    require(
        custody.get("record_path") == RECORD
        and custody.get("schema_path") == SCHEMA
        and custody.get("checker_path") == CHECKER
        and custody.get("self_test_path") == SELF_TEST
        and custody.get("forbidden_r12_message") == R12_MESSAGE
        and tuple(custody.get("forbidden_r12_evidence_paths", ())) == R12_EVIDENCE
        and custody.get("raw_logs_retained_in_repository") is False
        and custody.get("successor_workflow_role")
        == "nonqualifying_terminal_preservation_only",
        "terminal custody boundary changed",
    )
    historical = root["historical_c12_source"]
    require(
        type(historical) is dict
        and tuple(historical.get("sources", ())) == HISTORICAL_SOURCES
        and "not execution" in historical.get("recovery_boundary", "").lower(),
        "historical C12 source binding changed",
    )
    nonimplications = root["nonimplications"]
    require(
        type(nonimplications) is list
        and len(nonimplications) == 11
        and len(set(nonimplications)) == 11
        and any("L12" in item and "not adjudicated" in item for item in nonimplications)
        and any("actual hosted mode" in item for item in nonimplications)
        and any("not adjudicated here" in item for item in nonimplications),
        "terminal nonimplications changed",
    )


def validate_schema_semantics(value: Any) -> None:
    root = exact_keys(
        value,
        {
            "$defs",
            "$id",
            "$schema",
            "additionalProperties",
            "properties",
            "required",
            "title",
            "type",
        },
        "terminal schema",
    )
    require(
        root["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        and root["$id"].endswith(
            "/audit/schemas/ksg-rev4-m1a-composite-v12-terminal-failure.schema.json"
        )
        and root["additionalProperties"] is False
        and root["type"] == "object"
        and root["required"]
        == [
            "custody",
            "historical_c12_source",
            "hosted_attempt_1",
            "nonimplications",
            "qualification",
            "repository",
            "schema",
            "schema_revision",
            "subject",
        ],
        "terminal schema root changed",
    )
    properties = root["properties"]
    definitions = root["$defs"]
    require(
        type(properties) is dict
        and set(properties) == set(root["required"])
        and type(definitions) is dict
        and set(definitions)
        == {
            "codeqlJob",
            "codeqlRun",
            "failedJob",
            "jobCounts",
            "logRetrieval",
            "terminalRun",
        }
        and all(
            definitions[name].get("additionalProperties") is False
            for name in definitions
        )
        and properties["hosted_attempt_1"]["properties"]
        == {
            "codeql": {"$ref": "#/$defs/codeqlRun"},
            "dedicated_v12": {"$ref": "#/$defs/terminalRun"},
            "repository_ci": {"$ref": "#/$defs/terminalRun"},
        }
        and properties["qualification"] == {"const": EXPECTED_QUALIFICATION}
        and properties["repository"] == {"const": REPOSITORY}
        and properties["subject"]["properties"]["c12_commit"] == {"const": C12}
        and properties["subject"]["properties"]["c12_tree"] == {"const": C12_TREE}
        and properties["custody"]["properties"]["forbidden_r12_message"]
        == {"const": R12_MESSAGE}
        and properties["custody"]["properties"]["forbidden_r12_evidence_paths"]
        == {"const": list(R12_EVIDENCE)},
        "terminal schema critical contract changed",
    )


def verify_c12_git_identity(record: dict[str, Any]) -> dict[str, Any]:
    head = git("rev-parse", "--verify", "HEAD").decode("ascii", errors="strict").strip()
    require(
        git_success("merge-base", "--is-ancestor", C12, head), "C12 is not an ancestor"
    )

    raw_commit = git("cat-file", "commit", C12)
    require(b"\n\n" in raw_commit, "C12 commit object is malformed")
    header, message = raw_commit.split(b"\n\n", 1)
    header_lines = header.splitlines()
    require(
        header_lines[0] == f"tree {C12_TREE}".encode("ascii")
        and [line for line in header_lines if line.startswith(b"parent ")]
        == [f"parent {C11}".encode("ascii")]
        and not any(
            line.startswith((b"gpgsig ", b"mergetag ")) for line in header_lines
        )
        and message.decode("utf-8", errors="strict") == C12_MESSAGE,
        "exact unsigned C12 commit envelope changed",
    )

    delta_lines = (
        git(
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            "--no-renames",
            C11,
            C12,
        )
        .decode("utf-8", errors="strict")
        .splitlines()
    )
    observed_delta: list[tuple[str, str, str]] = []
    for line in delta_lines:
        change, path = line.split("\t", 1)
        current = tree_entry(C12, path)
        require(current is not None, f"C12 delta path is absent: {path}")
        mode, _ = current
        observed_delta.append((change, path, mode))
        parent = tree_entry(C11, path)
        require(
            (change == "A" and parent is None)
            or (change == "M" and parent is not None and parent[0] == "100644"),
            f"C12 parent delta semantics changed: {path}",
        )
    require(tuple(observed_delta) == EXPECTED_DELTA, "exact C11-to-C12 delta changed")

    for expected, recorded in zip(
        HISTORICAL_SOURCES,
        record["historical_c12_source"]["sources"],
        strict=True,
    ):
        require(recorded == expected, "historical source record changed")
        entry = tree_entry(C12, expected["path"])
        require(
            entry == ("100644", expected["git_blob_oid"]),
            f"historical C12 source entry changed: {expected['path']}",
        )
        raw = git("cat-file", "blob", f"{C12}:{expected['path']}")
        require(
            len(raw) == expected["size_bytes"]
            and hashlib.sha256(raw).hexdigest() == expected["sha256"],
            f"historical C12 source bytes changed: {expected['path']}",
        )
    return {"head": head, "c12_commit": C12, "c12_tree": C12_TREE}


def verify_r12_absence() -> None:
    messages = git("log", "--format=%B%x00", "HEAD").split(b"\x00")
    normalized = [message.rstrip(b"\n") + b"\n" for message in messages if message]
    require(R12_MESSAGE.encode("utf-8") not in normalized, "R12 message is reachable")
    for path in R12_EVIDENCE:
        require(
            git("rev-list", "HEAD", "--", path) == b"",
            f"R12 evidence is reachable: {path}",
        )


def verify_record_history(record_raw: bytes, head: str) -> str:
    expected_oid = (
        git("hash-object", "-t", "blob", "--stdin", input_bytes=record_raw)
        .decode("ascii", errors="strict")
        .strip()
    )
    introductions = [
        line
        for line in git("log", "--format=%H", "--diff-filter=A", "HEAD", "--", RECORD)
        .decode("ascii", errors="strict")
        .splitlines()
        if line
    ]
    if not introductions:
        require(
            head == C12, "terminal record is absent from committed descendant history"
        )
        require(
            tree_entry(C12, RECORD) is None,
            "terminal record unexpectedly exists at C12",
        )
        return "authoring_pending_introduction"

    require(len(introductions) == 1, "terminal record was introduced more than once")
    introduction = introductions[0]
    require(
        git_success("merge-base", "--is-ancestor", C12, introduction)
        and git_success("merge-base", "--is-ancestor", introduction, head),
        "terminal record introduction is outside the C12-to-HEAD ancestry path",
    )
    descendants = [introduction]
    descendants.extend(
        line
        for line in git("rev-list", "--ancestry-path", f"{introduction}..{head}")
        .decode("ascii", errors="strict")
        .splitlines()
        if line
    )
    for commit in descendants:
        require(
            tree_entry(commit, RECORD) == ("100644", expected_oid),
            f"terminal record was not preserved by descendant {commit}",
        )
    return "committed_preservation"


def recipe(source: str, name: str) -> str:
    marker = f"{name}:"
    start = source.find(marker)
    require(
        start >= 0 and (start == 0 or source[start - 1] == "\n"),
        f"missing Just target {name}",
    )
    tail = source[start:]
    lines = tail.splitlines()
    selected = [lines[0]]
    for line in lines[1:]:
        if line and not line[0].isspace() and line.endswith(":"):
            break
        selected.append(line)
    return "\n".join(selected)


def verify_successor_wiring() -> None:
    workflow = (ROOT / WORKFLOW).read_text(encoding="utf-8", errors="strict")
    just = (ROOT / JUSTFILE).read_text(encoding="utf-8", errors="strict")
    require(
        "name: KSG M1a composite v12 terminal preservation" in workflow
        and "push:" in workflow
        and "workflow_dispatch:" in workflow
        and "nonqualifying" in workflow.lower()
        and f"python3 -I -S -B {CHECKER}" in workflow
        and f"python3 -O -I -S -B {CHECKER}" in workflow
        and f"python3 -I -S -B {SELF_TEST}" in workflow
        and f"python3 -O -I -S -B {SELF_TEST}" in workflow
        and "GITHUB_RUN_ATTEMPT" not in workflow
        and "capture-ksg-m1a-composite-v12" not in workflow
        and "check-ksg-m1a-composite-v12.py --workflow" not in workflow,
        "dedicated-v12 successor is not preservation-only",
    )
    refusal = recipe(just, "ksg-composite-v12")
    preservation = recipe(just, "ksg-composite-v12-preservation")
    release_line = next(
        (line for line in just.splitlines() if line.startswith("release-audit:")), ""
    )
    require(
        "permanently closed" in refusal
        and "refusing replay" in refusal
        and "exit 1" in refusal
        and CHECKER in preservation
        and SELF_TEST in preservation
        and "python3 -O -I -S -B" in preservation
        and "ksg-composite-v12-authoring:" not in just
        and "capture-ksg-m1a-composite-v12" not in just
        and "check-ksg-m1a-composite-v12.py --auto" not in just
        and "check-ksg-m1a-composite-v12.py --authoring" not in just
        and "ksg-composite-v12-preservation" in release_line
        and " ksg-composite-v12 " not in f" {release_line} ",
        "Just v12 refusal or preservation wiring changed",
    )


def check() -> dict[str, Any]:
    record_raw = stable_read(RECORD, RECORD_SIZE, RECORD_SHA256)
    schema_raw = stable_read(SCHEMA, SCHEMA_SIZE, SCHEMA_SHA256)
    record = parse_json(record_raw, "terminal record")
    schema = parse_json(schema_raw, "terminal schema")
    require(
        record_raw == canonical_json(record), "terminal record is not canonical JSON"
    )
    require(
        schema_raw == canonical_json(schema), "terminal schema is not canonical JSON"
    )
    validate_record_semantics(record)
    validate_schema_semantics(schema)
    try:
        validate_json_schema(record, schema)
    except SchemaValidationError as error:
        refuse(f"terminal record does not satisfy its schema: {error}")
    identity = verify_c12_git_identity(record)
    verify_r12_absence()
    phase = verify_record_history(record_raw, identity["head"])
    verify_successor_wiring()
    return {
        "c12_commit": C12,
        "c12_tree": C12_TREE,
        "historical_c12_sources_recovered": len(HISTORICAL_SOURCES),
        "hosted_attempt_1": {
            "codeql": "terminal_success",
            "dedicated_v12": "terminal_failure",
            "repository_ci": "terminal_failure",
        },
        "l12": "not_adjudicated",
        "preservation_phase": phase,
        "q12": False,
        "r12": "permanently_unissued",
        "record_sha256": RECORD_SHA256,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-terminal-check/v1",
    }


def main() -> int:
    try:
        result = check()
    except (ContractError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
