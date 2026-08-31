#!/usr/bin/env python3
"""Check the current KSG revision-4 index against the terminal C12 boundary.

This is a narrow current-reader successor check.  It does not replace or modify
the historical packet checker, and it grants no qualification credit.
"""

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
        "ERROR: check-ksg-revision4-terminal-index.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any, NoReturn


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent

INDEX = "claims/KSG-INTEGER-HARMONIC-001/revision-index.md"
BOUNDARY = "audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md"
RECORD = "audit/evidence/ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json"
SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-v12-terminal-failure.schema.json"
TERMINAL_CHECKER = "scripts/check-ksg-m1a-composite-v12-terminal.py"
TERMINAL_CHECKER_SCHEMA_HELPER = "scripts/json_schema_subset.py"

C12 = "01466e88b0550333c2718f1716289e9642e30dc6"
C12_TREE = "c445a647963ac12fbe1c352cc042956a82c7d69e"
REPOSITORY = "sepahead/pid-rs"

INDEX_SIZE = 5_367
INDEX_SHA256 = "a48f35d6d4ece09595d793ee4af0dd7d2c0dbbb8e6aff0d5d05a96f26409c1bc"
BOUNDARY_SIZE = 11_197
BOUNDARY_SHA256 = "4930810e053fda866f4f1b356e07902b9cc8c8797a012fbe4bf40562899b835c"
RECORD_SIZE = 13_644
RECORD_SHA256 = "375bf287c73dea35c70d21c74be58e54fe17ae27b4c38ebd9cdf543c8beab47c"
SCHEMA_SIZE = 12_907
SCHEMA_SHA256 = "2152411c804df3a75f6b106ae97761f4812adf2ae8ca963a98a296df812c0e5e"
TERMINAL_CHECKER_SIZE = 30_210
TERMINAL_CHECKER_SHA256 = (
    "df32b05c01015a3d224988463776e45983314f93b999a2f60e02e619434ce4ce"
)
TERMINAL_CHECKER_SCHEMA_HELPER_SIZE = 16_960
TERMINAL_CHECKER_SCHEMA_HELPER_SHA256 = (
    "067e6d6b10d33f5b9c1bab6bc621735267a06f2461d6c0da3c8342ac8bd391a6"
)

R12_EVIDENCE = [
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v12-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v12-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v12-2026-08-23.json",
]

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

EXPECTED_TERMINAL_RESULT = {
    "c12_commit": C12,
    "c12_tree": C12_TREE,
    "historical_c12_sources_recovered": 2,
    "hosted_attempt_1": {
        "codeql": "terminal_success",
        "dedicated_v12": "terminal_failure",
        "repository_ci": "terminal_failure",
    },
    "l12": "not_adjudicated",
    "preservation_phase": "committed_preservation",
    "q12": False,
    "r12": "permanently_unissued",
    "record_sha256": RECORD_SHA256,
    "result": "pass",
    "schema": "pid-rs/ksg-rev4-m1a-composite-v12-terminal-check/v1",
}
EXPECTED_TERMINAL_STDOUT = (
    json.dumps(EXPECTED_TERMINAL_RESULT, sort_keys=True, separators=(",", ":")) + "\n"
).encode("utf-8")

INDEX_TABLE_ROWS = (
    "| 1 | `claim-v1.md` | `obligations.md` | `routes.md` | `decision.md` | retained conditional integration design |",
    "| 2 | `claim-v2.md` | `obligations-v2.md` | `routes-v2.md` | `decision-v2.md` | retained evidence/integration correction; completion stayed open |",
    "| 3 | `claim-v3.md` | `obligations-v3.md` | `routes-v3.md` | deliberately absent | frozen preclosure NO-GO; never silently repaired |",
    "| 4 | `claim-v4.md` | `obligations-v4.md` | `routes-v4.md` | deliberately absent | scoped core GO; integration NO-GO; exact v12 qualification route terminal |",
)

INDEX_REQUIRED_TEXT = (
    "Revision 4 remains the active scientific packet.",
    "repository and publication integration\nremain NO-GO.",
    "`Q12 = false`, `R12 = permanently_unissued`, and `L12 = not_adjudicated`.",
    "The terminal result is\nan operational lifecycle conclusion, not a refutation of the scoped mathematics.",
    "could not inherit\nqualification credit from v12.",
    "The packet's earlier direction to\nimplement a separately reviewed M1c checker was a pre-C12 lifecycle design, not a live instruction\nafter the exact v12 route became terminal.",
    "Final `evidence-matrix-v4.md` and `decision-v4.md` remain\nabsent; the terminal v12 route cannot issue or authorize them.",
    "That sequence is retained as historical design context, not as an\nexecutable current route: exact-C12 v12 qualification ended terminally with zero qualification\ncredit and no R12 receipt.",
)

BOUNDARY_REQUIRED_TEXT = (
    "State: terminal hosted failure; Q12 is false and R12 is permanently unissued. L12 is not\n  adjudicated by the terminal record.",
    "Therefore Q12 is\nfalse for either Boolean value of L12.",
    "`L12 = not_adjudicated` is not a failure claim.",
    "Later pushes cannot create L12, another hosted\nattempt-1 term, qualification credit, or receipt authority.",
    "The failed hosted conjunction permanently prevents steps 7 and 8.",
    "This boundary is operational source and evidence custody. It does not validate a PID functional,\nKSG estimator, theorem, numerical result, scientific claim, application, security property,",
)


class ContractError(RuntimeError):
    """The current-reader terminal-index contract is not satisfied."""


def refuse(message: str) -> NoReturn:
    raise ContractError(message)


def require(predicate: bool, message: str) -> None:
    if not predicate:
        refuse(message)


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def parse_json(raw: bytes, label: str) -> Any:
    def reject_constant(value: str) -> NoReturn:
        refuse(f"{label} contains non-finite number {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        refuse(f"{label} is not strict JSON: {error}")


def exact_dict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(type(value) is dict and set(value) == keys, f"{label} keys changed")
    return value


def stable_read(
    root: Path,
    relative: str,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    path = root / relative
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
            require(chunk != b"", f"{relative} ended during read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"{relative} grew during read")
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
            f"{relative} changed during read",
        )
    raw = b"".join(chunks)
    require(
        hashlib.sha256(raw).hexdigest() == expected_sha256,
        f"{relative} digest changed",
    )
    return raw


def require_regular_target(root: Path, relative: str) -> None:
    path = root / relative
    metadata = path.lstat()
    require(
        stat.S_ISREG(metadata.st_mode)
        and not path.is_symlink()
        and metadata.st_nlink == 1
        and stat.S_IMODE(metadata.st_mode) == 0o644,
        f"index target is not a direct regular mode-0644 single-link file: {relative}",
    )


def validate_index_semantics(raw: bytes, root: Path, *, check_targets: bool) -> None:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        refuse(f"revision index is not UTF-8: {error}")
    require(text.endswith("\n") and "\r" not in text, "revision index framing changed")
    require(
        text.count("## Current reader boundary") == 1, "current boundary count changed"
    )
    require(
        text.count("| Revision | Claim | Obligations | Routes | Decision | Status |")
        == 1,
        "revision table header changed",
    )
    for row in INDEX_TABLE_ROWS:
        require(text.count(row) == 1, f"revision table row changed: {row[:12]}")
    for required in INDEX_REQUIRED_TEXT:
        require(
            text.count(required) == 1,
            f"current-reader statement changed: {required[:48]}",
        )

    expected_link = (
        "../../audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md"
    )
    links = re.findall(r"\[([^\]\n]+)\]\(([^)\n]+)\)", text)
    require(
        links == [(f"`{C12}`", expected_link)], "revision-index Markdown links changed"
    )

    forbidden_current = (
        "revision 3 remains the active",
        "revision 4 is inactive",
        "q12 = true",
        "r12 = issued",
        "r12 = conditionally",
        "l12 = true",
        "l12 = false",
        "qualification credit transfers",
        "qualification credit may transfer",
        "reactivate attempt 1",
        "revive q12",
        "issue r12",
        "m1c checker is a live instruction",
        "final `evidence-matrix-v4.md` and `decision-v4.md` are present",
    )
    lowered = text.lower()
    for phrase in forbidden_current:
        require(
            phrase not in lowered,
            f"revision index reactivates terminal route: {phrase}",
        )

    if not check_targets:
        return
    claim_directory = "claims/KSG-INTEGER-HARMONIC-001"
    for name in (
        "claim-v1.md",
        "obligations.md",
        "routes.md",
        "decision.md",
        "claim-v2.md",
        "obligations-v2.md",
        "routes-v2.md",
        "decision-v2.md",
        "claim-v3.md",
        "obligations-v3.md",
        "routes-v3.md",
        "claim-v4.md",
        "obligations-v4.md",
        "routes-v4.md",
    ):
        require_regular_target(root, f"{claim_directory}/{name}")
    for absent in ("decision-v3.md", "evidence-matrix-v4.md", "decision-v4.md"):
        require(
            not os.path.lexists(root / claim_directory / absent),
            f"reserved absent revision artifact exists: {absent}",
        )

    index_parent = (root / INDEX).parent.resolve(strict=True)
    linked = (index_parent / expected_link).resolve(strict=True)
    expected = (root / BOUNDARY).resolve(strict=True)
    require(
        linked == expected, "terminal boundary link resolves outside its exact target"
    )
    require_regular_target(root, BOUNDARY)


def validate_boundary_semantics(raw: bytes) -> None:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        refuse(f"terminal boundary is not UTF-8: {error}")
    require(
        text.endswith("\n") and "\r" not in text, "terminal boundary framing changed"
    )
    for required in BOUNDARY_REQUIRED_TEXT:
        require(
            text.count(required) == 1, f"terminal boundary changed: {required[:48]}"
        )
    lowered = text.lower()
    for forbidden in (
        "q12 is true",
        "r12 is issued",
        "l12 succeeded",
        "l12 failed",
        "qualification credit can transfer",
        "qualification credit may transfer",
        "later pushes can create l12",
        "validates a pid functional",
        "validates the ksg estimator",
    ):
        require(
            forbidden not in lowered,
            f"terminal boundary overclaim appeared: {forbidden}",
        )


def validate_record_semantics(record: Any) -> dict[str, Any]:
    root = exact_dict(
        record,
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
    subject = root["subject"]
    require(
        type(subject) is dict
        and subject.get("c12_commit") == C12
        and subject.get("c12_tree") == C12_TREE
        and subject.get("c12_unsigned") is True,
        "terminal subject changed",
    )

    qualification = root["qualification"]
    require(qualification == EXPECTED_QUALIFICATION, "terminal qualification changed")
    hosted = root["hosted_attempt_1"]
    require(
        type(hosted) is dict
        and set(hosted) == {"codeql", "dedicated_v12", "repository_ci"},
        "terminal hosted run set changed",
    )
    expected_conclusions = {
        "codeql": "success",
        "dedicated_v12": "failure",
        "repository_ci": "failure",
    }
    terms: dict[str, bool] = {}
    for name, conclusion in expected_conclusions.items():
        run = hosted[name]
        require(
            type(run) is dict
            and run.get("attempt") == 1
            and run.get("run_attempt") == 1
            and run.get("status") == "completed"
            and run.get("head_sha") == C12
            and run.get("conclusion") == conclusion,
            f"terminal attempt-1 run changed: {name}",
        )
        counts = run.get("job_counts")
        require(
            type(counts) is dict
            and type(counts.get("total")) is int
            and counts.get("total", 0) > 0
            and counts.get("success", 0)
            + counts.get("failure", 0)
            + counts.get("other", 0)
            == counts.get("total"),
            f"terminal job counts changed: {name}",
        )
        terms[name] = conclusion == "success"

    for l12 in (False, True):
        derived_q12 = (
            l12
            and terms["repository_ci"]
            and terms["codeql"]
            and terms["dedicated_v12"]
        )
        require(derived_q12 is False, "terminal Q12 can become true")
    require(
        qualification["q12"] is False
        and qualification["r12"] == "permanently_unissued"
        and qualification["l12"] == "not_adjudicated"
        and qualification["hosted_qualification_credit"] == "zero",
        "terminal disposition changed",
    )

    custody = root["custody"]
    require(
        type(custody) is dict
        and custody.get("record_path") == RECORD
        and custody.get("schema_path") == SCHEMA
        and custody.get("checker_path") == TERMINAL_CHECKER
        and custody.get("successor_workflow_role")
        == "nonqualifying_terminal_preservation_only"
        and custody.get("forbidden_r12_message")
        == "Record KSG M1a composite v12 receipt\n"
        and custody.get("forbidden_r12_evidence_paths") == R12_EVIDENCE,
        "terminal custody or nonqualification boundary changed",
    )
    nonimplications = root["nonimplications"]
    require(
        type(nonimplications) is list
        and any("L12" in item and "not adjudicated" in item for item in nonimplications)
        and any(
            "cannot become an exact-C12 attempt-1 term" in item
            for item in nonimplications
        )
        and any("validate no PID functional" in item for item in nonimplications),
        "terminal nonimplications changed",
    )
    return root


def validate_schema_semantics(schema: Any, record: dict[str, Any]) -> None:
    root = exact_dict(
        schema,
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
    properties = root["properties"]
    require(
        root["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        and root["additionalProperties"] is False
        and root["type"] == "object"
        and type(properties) is dict,
        "terminal schema root changed",
    )
    require(
        properties.get("repository") == {"const": REPOSITORY}
        and properties.get("qualification") == {"const": EXPECTED_QUALIFICATION}
        and properties["qualification"]["const"] == record["qualification"],
        "terminal schema qualification binding changed",
    )
    subject = properties.get("subject", {}).get("properties", {})
    custody = properties.get("custody", {}).get("properties", {})
    require(
        subject.get("c12_commit") == {"const": C12}
        and subject.get("c12_tree") == {"const": C12_TREE}
        and subject.get("c12_unsigned") == {"const": True}
        and custody.get("record_path") == {"const": RECORD}
        and custody.get("schema_path") == {"const": SCHEMA}
        and custody.get("checker_path") == {"const": TERMINAL_CHECKER}
        and custody.get("successor_workflow_role")
        == {"const": "nonqualifying_terminal_preservation_only"}
        and custody.get("forbidden_r12_evidence_paths") == {"const": R12_EVIDENCE},
        "terminal schema identity or custody binding changed",
    )


def validate_terminal_results(
    normal: subprocess.CompletedProcess[bytes],
    optimized: subprocess.CompletedProcess[bytes],
) -> None:
    for label, completed in (("normal", normal), ("optimized", optimized)):
        require(completed.returncode == 0, f"terminal checker {label} status changed")
        require(completed.stderr == b"", f"terminal checker {label} emitted stderr")
        require(
            completed.stdout == EXPECTED_TERMINAL_STDOUT,
            f"terminal checker {label} canonical output changed",
        )
        parsed = parse_json(completed.stdout, f"terminal checker {label} output")
        require(
            parsed == EXPECTED_TERMINAL_RESULT,
            f"terminal checker {label} result changed",
        )
    require(
        normal.stdout == optimized.stdout,
        "terminal checker normal and optimized outputs differ",
    )


def run_terminal_checker_pair(
    root: Path,
) -> tuple[subprocess.CompletedProcess[bytes], subprocess.CompletedProcess[bytes]]:
    environment = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
        "XDG_CONFIG_HOME": "/nonexistent",
    }
    results: list[subprocess.CompletedProcess[bytes]] = []
    for optimization in ((), ("-O",)):
        completed = subprocess.run(
            [
                sys.executable,
                *optimization,
                "-I",
                "-S",
                "-B",
                os.fspath(root / TERMINAL_CHECKER),
            ],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        results.append(completed)
    return results[0], results[1]


def check(root: Path = ROOT) -> dict[str, Any]:
    index_raw = stable_read(root, INDEX, INDEX_SIZE, INDEX_SHA256)
    boundary_raw = stable_read(root, BOUNDARY, BOUNDARY_SIZE, BOUNDARY_SHA256)
    record_raw = stable_read(root, RECORD, RECORD_SIZE, RECORD_SHA256)
    schema_raw = stable_read(root, SCHEMA, SCHEMA_SIZE, SCHEMA_SHA256)
    stable_read(
        root,
        TERMINAL_CHECKER,
        TERMINAL_CHECKER_SIZE,
        TERMINAL_CHECKER_SHA256,
    )
    stable_read(
        root,
        TERMINAL_CHECKER_SCHEMA_HELPER,
        TERMINAL_CHECKER_SCHEMA_HELPER_SIZE,
        TERMINAL_CHECKER_SCHEMA_HELPER_SHA256,
    )

    validate_index_semantics(index_raw, root, check_targets=True)
    validate_boundary_semantics(boundary_raw)
    record = parse_json(record_raw, "terminal record")
    schema = parse_json(schema_raw, "terminal schema")
    require(
        record_raw == canonical_json(record), "terminal record is not canonical JSON"
    )
    require(
        schema_raw == canonical_json(schema), "terminal schema is not canonical JSON"
    )
    validated_record = validate_record_semantics(record)
    validate_schema_semantics(schema, validated_record)
    terminal_results = run_terminal_checker_pair(root)
    validate_terminal_results(*terminal_results)
    return {
        "boundary_sha256": BOUNDARY_SHA256,
        "c12_commit": C12,
        "index_sha256": INDEX_SHA256,
        "l12": "not_adjudicated",
        "q12": False,
        "r12": "permanently_unissued",
        "result": "pass",
        "schema": "pid-rs/ksg-revision4-terminal-index-check/v1",
        "terminal_checker_schema": EXPECTED_TERMINAL_RESULT["schema"],
    }


def main() -> int:
    if len(sys.argv) != 1:
        print("ERROR: this checker accepts no arguments", file=sys.stderr)
        return 2
    try:
        result = check()
    except (ContractError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
