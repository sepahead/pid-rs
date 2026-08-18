#!/usr/bin/env python3
"""Adversarial bounded-repair tests for the composite-v6 contract checker."""

from __future__ import annotations

import base64
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v6-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v6.py"


class SelfTestError(RuntimeError):
    """A positive vector failed or an adverse mutation was accepted."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_checker() -> Any:
    specification = importlib.util.spec_from_file_location(
        "_pid_rs_composite_v6_self_test_target", CHECKER
    )
    require(
        specification is not None and specification.loader is not None,
        "checker import route is unavailable",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


V6 = load_checker()


def rejected(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except V6.ContractError:
        return
    raise SelfTestError(f"mutation was accepted: {label}")


def descriptor(path: str, digest: str = "a" * 64) -> dict[str, Any]:
    return {"path": path, "sha256": digest, "size_bytes": 1}


def byte_binding(raw: bytes) -> dict[str, Any]:
    return {
        "body_base64": base64.b64encode(raw).decode("ascii"),
        "sha256": V6.sha256(raw),
        "size_bytes": len(raw),
    }


def local_record_fixture() -> tuple[dict[str, Any], dict[str, bytes]]:
    c6 = "1" * 40
    c6_tree = "2" * 40
    authority_entries = {
        path: f"fixture authority: {path}\n".encode("utf-8")
        for path in V6.LOCAL_AUTHORITY_ROLES
    }
    authorities = [
        {
            "path": path,
            "role": V6.LOCAL_AUTHORITY_ROLES[path],
            "sha256": V6.sha256(authority_entries[path]),
            "size_bytes": len(authority_entries[path]),
        }
        for path in sorted(V6.LOCAL_AUTHORITY_ROLES)
    ]
    empty = byte_binding(b"")

    def snapshot(observed_at: str) -> dict[str, Any]:
        return {
            "alternates": "absent",
            "common_dir": "<REPOSITORY_ROOT>/.git",
            "config_overlays": "absent",
            "git_dir": "<REPOSITORY_ROOT>/.git",
            "grafts": "absent",
            "head": c6,
            "http_alternates": "absent",
            "info_attributes_rules": "absent",
            "info_exclude_rules": "absent",
            "message": V6.C6_MESSAGE,
            "object_format": "sha1",
            "observed_at": observed_at,
            "parent": V6.C5_COMMIT,
            "replacement_refs": [],
            "shallow": "absent",
            "status": copy.deepcopy(empty),
            "tree": c6_tree,
            "worktree_root": "<REPOSITORY_ROOT>",
        }

    reviewed = []
    for index, name in enumerate(sorted(V6.LOCAL_TOOL_SPECS), start=1):
        output = f"{name} fixture version\n".encode("ascii")
        reviewed.append(
            {
                "executable_sha256": format(index % 16, "x") * 64,
                "executable_size_bytes": index,
                "name": name,
                "route": f"<SYSTEM_BIN>/{name}",
                "version_argv": V6.LOCAL_TOOL_SPECS[name],
                "version_exit_code": 0,
                "version_stderr": copy.deepcopy(empty),
                "version_stdout": byte_binding(output),
            }
        )
    record = {
        "authorities": authorities,
        "invocation": {
            "argv": ["just", "ksg-composite-v6"],
            "cwd": "<REPOSITORY_ROOT>",
            "elapsed_monotonic_ns": 100,
            "environment": V6.LOCAL_NORMALIZED_ENVIRONMENT,
            "environment_routes_sha256": "3" * 64,
            "exit_code": 0,
            "finished_at": "2026-08-18T00:00:03.000000Z",
            "monotonic_finish_ns": 100,
            "monotonic_start_ns": 0,
            "signal": None,
            "started_at": "2026-08-18T00:00:02.000000Z",
            "stderr": copy.deepcopy(empty),
            "stdout": byte_binding(b"fixture L6 closure pass\n"),
            "timed_out": False,
            "timeout_seconds": 14400,
            "umask": "0077",
        },
        "nonimplications": V6.LOCAL_CLOSURE_NONIMPLICATIONS,
        "platform": {
            "architecture": "arm64",
            "operating_system": "Darwin",
            "operating_system_release": "25.6.0",
            "python_implementation": "CPython",
            "python_version": "3.14.0",
        },
        "repository": V6.REPOSITORY,
        "repository_state": {
            "after": snapshot("2026-08-18T00:00:04.000000Z"),
            "before": snapshot("2026-08-18T00:00:01.000000Z"),
        },
        "reviewed_executables": reviewed,
        "schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v1",
        "schema_revision": 1,
        "subject": {
            "c5_parent": V6.C5_COMMIT,
            "c6_commit": c6,
            "c6_message": V6.C6_MESSAGE,
            "c6_tree": c6_tree,
        },
    }
    return record, authority_entries


def local_qualification_fixture() -> dict[str, Any]:
    record, _entries = local_record_fixture()
    invocation = record["invocation"]
    state = record["repository_state"]
    raw = V6.canonical_json(record, pretty=True)
    return {
        "observation": {
            "authorities_sha256": V6.sha256(
                V6.canonical_json(record["authorities"], pretty=False)
            ),
            "command": {
                "argv": invocation["argv"],
                "elapsed_monotonic_ns": invocation["elapsed_monotonic_ns"],
                "environment_routes_sha256": invocation["environment_routes_sha256"],
                "exit_code": invocation["exit_code"],
                "finished_at": invocation["finished_at"],
                "started_at": invocation["started_at"],
                "stderr_sha256": invocation["stderr"]["sha256"],
                "stderr_size_bytes": invocation["stderr"]["size_bytes"],
                "stdout_sha256": invocation["stdout"]["sha256"],
                "stdout_size_bytes": invocation["stdout"]["size_bytes"],
                "timed_out": invocation["timed_out"],
                "umask": invocation["umask"],
            },
            "platform": record["platform"],
            "repository_state": {
                "after_observed_at": state["after"]["observed_at"],
                "after_status_sha256": state["after"]["status"]["sha256"],
                "after_status_size_bytes": state["after"]["status"]["size_bytes"],
                "before_observed_at": state["before"]["observed_at"],
                "before_status_sha256": state["before"]["status"]["sha256"],
                "before_status_size_bytes": state["before"]["status"]["size_bytes"],
                "c6_commit": record["subject"]["c6_commit"],
                "c6_tree": record["subject"]["c6_tree"],
                "http_alternates": state["before"]["http_alternates"],
                "info_attributes_rules": state["before"]["info_attributes_rules"],
                "info_exclude_rules": state["before"]["info_exclude_rules"],
            },
            "reviewed_executables_sha256": V6.sha256(
                V6.canonical_json(record["reviewed_executables"], pretty=False)
            ),
            "schema": "pid-rs/ksg-rev4-m1a-composite-local-qualification-observation/v1",
        },
        "record_binding": {
            "path": V6.LOCAL_CLOSURE_RELATIVE,
            "sha256": V6.sha256(raw),
            "size_bytes": len(raw),
        },
    }


def run(role: str, conclusion: str, run_id: int = 101) -> dict[str, Any]:
    kind = V6.ROLE_KIND[role]
    if kind == "ci":
        name = "CI"
        path = ".github/workflows/ci.yml"
        event = "push"
        workflow_id = 297369773
    elif kind == "codeql":
        name = "Push on main"
        path = "dynamic/github-code-scanning/codeql"
        event = "dynamic"
        workflow_id = 310582096
    else:
        version = "v5" if role.startswith("predecessor_") else "v6"
        name = f"KSG M1a composite {version}"
        path = f".github/workflows/ksg-m1a-composite-{version}.yml"
        event = "push"
        workflow_id = 411
    return {
        "conclusion": conclusion,
        "event": event,
        "head_branch": "main",
        "head_repository": {"full_name": V6.REPOSITORY, "id": 77},
        "head_sha": V6.C5_COMMIT,
        "id": run_id,
        "name": name,
        "path": path,
        "repository": {"full_name": V6.REPOSITORY, "id": 77},
        "run_attempt": 1,
        "status": "completed",
        "workflow_id": workflow_id,
    }


def job(
    role: str,
    conclusion: str,
    job_id: int,
    *,
    run_id: int = 101,
) -> dict[str, Any]:
    if V6.ROLE_KIND[role] == "contract":
        name = (
            "Validate the composite-v5 correction contract"
            if role.startswith("predecessor_")
            else "Validate the composite-v6 correction contract"
        )
    else:
        name = "unused"
    if role == "predecessor_contract":
        step_values = [
            ("Validate the bounded successor publication", "failure"),
            ("Validate fresh replay and current-source custody", "skipped"),
            ("Validate static v5 contract in normal and optimized modes", "skipped"),
            ("Upload the exact v5 static result", "skipped"),
        ]
    elif role == "successor_contract":
        step_values = [
            ("Normalize only the reviewed inert checkout residue", "success"),
            ("Refuse retries and non-main qualification events", "success"),
            ("Install the hash-pinned PDF verifier dependency", "success"),
            ("Install the runner PDF toolchain", "success"),
            ("Recheck retained C5 operational surfaces", "success"),
            (
                "Validate immutable predecessor PDF portability and the bounded successor publication",
                "success",
            ),
            ("Validate fresh replay and current-source custody", "success"),
            ("Validate static v6 contract in normal and optimized modes", "success"),
            ("Upload the exact v6 static result", "success"),
        ]
    else:
        step_values = [("bounded failure surface", conclusion)]
    return {
        "completed_at": "2026-08-18T00:00:01Z",
        "conclusion": conclusion,
        "head_sha": V6.C5_COMMIT,
        "id": job_id,
        "name": name,
        "run_attempt": 1,
        "run_id": run_id,
        "started_at": "2026-08-18T00:00:00Z",
        "status": "completed",
        "steps": [
            {
                "conclusion": step_conclusion,
                "name": step_name,
                "number": index,
                "status": "completed",
            }
            for index, (step_name, step_conclusion) in enumerate(step_values, start=1)
        ],
    }


def receipt_observation(role: str, conclusion: str, run_id: int) -> dict[str, Any]:
    normalized = V6.normalized_run(
        run(role, conclusion, run_id), role, run_id, V6.C5_COMMIT
    )
    logs = []
    if conclusion == "failure" and role.startswith("predecessor_"):
        for job_id, (job_name, failed_steps) in sorted(
            V6.PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[role].items()
        ):
            logs.append(
                {
                    "failed_steps": list(failed_steps),
                    "job_id": job_id,
                    "job_name": job_name,
                    "observed_markers": list(
                        V6.PREDECESSOR_REQUIRED_LOG_MARKERS[job_id]
                    ),
                    "sha256": V6.sha256(str(job_id).encode("ascii")),
                    "size_bytes": 1,
                }
            )
    job_ids = [item["job_id"] for item in logs] or [5000 + run_id]
    return {
        "artifacts": [],
        "artifacts_sha256": "a" * 64,
        "codeql_alerts_sha256": None,
        "codeql_analysis_ids": [],
        "codeql_analyses_sha256": None,
        "failed_job_logs": logs,
        "failed_job_logs_sha256": "b" * 64,
        "job_count": len(job_ids),
        "job_ids": job_ids,
        "jobs_sha256": "c" * 64,
        "kind": V6.ROLE_KIND[role],
        "role": role,
        "run": normalized,
    }


def receipt_fixture() -> dict[str, Any]:
    authorities = []
    for index in range(8):
        item = descriptor(f"authority/{index}.json", format(index, "x") * 64)
        item["role"] = f"authority_{index}"
        authorities.append(item)
    predecessor_roles = [
        receipt_observation("predecessor_ci", "failure", 101),
        receipt_observation("predecessor_codeql", "success", 102),
        receipt_observation("predecessor_contract", "failure", 103),
    ]
    successor_roles = [
        receipt_observation("successor_ci", "success", 201),
        receipt_observation("successor_codeql", "success", 202),
        receipt_observation("successor_contract", "success", 203),
    ]
    return {
        "capture_bindings": [
            {
                **descriptor(V6.PREDECESSOR_CAPTURE_RELATIVE, "d" * 64),
                "phase": "predecessor_failure",
            },
            {
                **descriptor(V6.SUCCESSOR_CAPTURE_RELATIVE, "e" * 64),
                "phase": "successor_qualification",
            },
        ],
        "contract_authorities": authorities,
        "local_qualification": local_qualification_fixture(),
        "nonimplications": V6.RECEIPT_NONIMPLICATIONS,
        "observations": [
            {
                "capture_sha256": "d" * 64,
                "phase": "predecessor_failure",
                "roles": predecessor_roles,
            },
            {
                "capture_sha256": "e" * 64,
                "phase": "successor_qualification",
                "roles": successor_roles,
            },
        ],
        "repository": V6.REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v6",
        "schema_revision": 6,
        "subject": {
            "c5_commit": V6.C5_COMMIT,
            "c5_tree": V6.C5_TREE,
            "c6_commit": "1" * 40,
            "c6_tree": "2" * 40,
        },
        "verdict": {
            "c5_hosted_qualification": "failed_zero_credit",
            "c5_publication": "published",
            "c6_bounded_repair": "pass",
            "c6_hosted_observation": "pass",
            "c6_local_qualification": "pass",
            "r5_receipt_issued": False,
            "r6_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
    }


def policy_fixture() -> dict[str, Any]:
    def render(rows: tuple[tuple[str, str, str, str], ...]) -> list[dict[str, str]]:
        return [
            {"mode": mode, "path": path, "role": role, "status": status}
            for path, status, mode, role in rows
        ]

    return {
        "base": {
            "commit": V6.C5_COMMIT,
            "r4_status": "permanently_unissued",
            "r5_status": "permanently_unissued",
            "reserved_absent_paths": list(V6.FORBIDDEN_R4_R5_EVIDENCE_PATHS),
            "tree": V6.C5_TREE,
        },
        "c6": {
            "delta": render(V6.C6_POLICY_ROWS),
            "direct_parent_role": "published_c5_contract",
            "message": V6.C6_MESSAGE,
        },
        "nonimplications": V6.POLICY_NONIMPLICATIONS,
        "r6": {
            "delta": render(V6.R6_POLICY_ROWS),
            "direct_parent_role": "c6_contract_repair",
            "message": V6.R6_MESSAGE,
        },
        "repository": V6.REPOSITORY,
        "schema": "pid-rs/ksg-m1a-composite-v6-path-policy",
        "schema_revision": 1,
    }


def test_capture_rows() -> int:
    body = b"terminal failure log\n"
    row = {
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": V6.sha256(body),
        "body_size_bytes": len(body),
        "logical_request": "predecessor_contract_failed_job_95619716898_log",
        "media_type": "text/plain",
        "page": 0,
        "path": f"/repos/{V6.REPOSITORY}/actions/jobs/95619716898/logs",
        "redirect": {
            "status_code": 302,
            "target_host": "safe.blob.core.windows.net",
            "target_url_sha256": "a" * 64,
        },
        "repetition": 1,
        "response_kind": "log",
        "status_code": 200,
    }
    V6.decode_capture_row(row, "positive failed-job log")
    mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(row)
    changed["body_sha256"] = "b" * 64
    mutations.append((changed, "body digest"))
    changed = copy.deepcopy(row)
    changed["body_base64"] += "="
    mutations.append((changed, "noncanonical base64"))
    changed = copy.deepcopy(row)
    changed["redirect"]["target_host"] = "attacker.example"
    mutations.append((changed, "redirect host"))
    changed = copy.deepcopy(row)
    changed["response_kind"] = "json"
    mutations.append((changed, "kind/media mismatch"))
    changed = copy.deepcopy(row)
    changed["path"] = f"/repos/{V6.REPOSITORY}/actions/jobs/7/logs"
    mutations.append((changed, "job/path mismatch"))
    for changed, label in mutations:
        rejected(lambda changed=changed: V6.decode_capture_row(changed, label), label)
    return len(mutations)


def test_runs_and_jobs() -> tuple[int, int]:
    valid = run("successor_ci", "success")
    V6.normalized_run(valid, "successor_ci", 101, V6.C5_COMMIT)
    run_mutations: list[tuple[dict[str, Any], str]] = []
    for key, replacement in (
        ("run_attempt", 2),
        ("head_sha", "0" * 40),
        ("conclusion", "failure"),
        ("path", ".github/workflows/other.yml"),
    ):
        changed = copy.deepcopy(valid)
        changed[key] = replacement
        run_mutations.append((changed, key))
    changed = copy.deepcopy(valid)
    changed["repository"]["id"] = 78
    run_mutations.append((changed, "repository join"))
    for changed, label in run_mutations:
        rejected(
            lambda changed=changed: V6.normalized_run(
                changed, "successor_ci", 101, V6.C5_COMMIT
            ),
            label,
        )

    predecessor = job("predecessor_contract", "failure", 95619716898)
    successor = job("successor_contract", "success", 901)
    V6.normalized_jobs([predecessor], "predecessor_contract", 101, V6.C5_COMMIT)
    V6.normalized_jobs([successor], "successor_contract", 101, V6.C5_COMMIT)
    job_vectors: list[tuple[list[dict[str, Any]], str, str]] = []
    changed = copy.deepcopy(predecessor)
    changed["conclusion"] = "success"
    changed["steps"][0]["conclusion"] = "success"
    job_vectors.append(([changed], "predecessor_contract", "failure erased"))
    changed = copy.deepcopy(successor)
    changed["conclusion"] = "failure"
    changed["steps"][0]["conclusion"] = "failure"
    job_vectors.append(([changed], "successor_contract", "failure injected"))
    changed = copy.deepcopy(predecessor)
    changed["steps"][0]["conclusion"] = "success"
    job_vectors.append(([changed], "predecessor_contract", "failed step erased"))
    changed = copy.deepcopy(successor)
    changed["run_attempt"] = 2
    job_vectors.append(([changed], "successor_contract", "attempt changed"))
    changed = copy.deepcopy(successor)
    changed["steps"] = []
    job_vectors.append(([changed], "successor_contract", "successful steps absent"))
    changed = copy.deepcopy(successor)
    changed["started_at"] = "2026-08-18T00:00:02Z"
    job_vectors.append(([changed], "successor_contract", "time reversed"))
    changed = copy.deepcopy(successor)
    changed["steps"] = changed["steps"][1:]
    job_vectors.append(([changed], "successor_contract", "bounded step omitted"))
    changed = copy.deepcopy(successor)
    next(
        item
        for item in changed["steps"]
        if item["name"] == "Recheck retained C5 operational surfaces"
    )["conclusion"] = "skipped"
    job_vectors.append(([changed], "successor_contract", "bounded step skipped"))
    changed = copy.deepcopy(predecessor)
    changed["steps"][0]["name"] = "different failed step"
    job_vectors.append(([changed], "predecessor_contract", "failure step renamed"))
    for values, role, label in job_vectors:
        rejected(
            lambda values=values, role=role: V6.normalized_jobs(
                values, role, 101, V6.C5_COMMIT
            ),
            label,
        )
    return len(run_mutations), len(job_vectors)


def test_job_timestamps() -> int:
    valid = {
        "completed_at": "2026-08-18T00:00:01Z",
        "started_at": "2026-08-18T00:00:00Z",
    }
    require(
        V6.normalized_job_timestamps(valid, "success", "timestamp-positive")
        == ("2026-08-18T00:00:00Z", "2026-08-18T00:00:01Z"),
        "ordinary job timestamps were not preserved",
    )
    skipped = {"completed_at": None, "started_at": None}
    require(
        V6.normalized_job_timestamps(skipped, "skipped", "timestamp-skipped")
        == (None, None),
        "explicit null timestamps for a skipped job were not preserved",
    )
    mutations: list[tuple[dict[str, Any], str, str]] = []
    changed = copy.deepcopy(valid)
    del changed["started_at"]
    mutations.append((changed, "success", "timestamp field omitted"))
    changed = copy.deepcopy(skipped)
    changed["completed_at"] = "2026-08-18T00:00:01Z"
    mutations.append((changed, "skipped", "only one skipped timestamp is null"))
    mutations.append(
        (copy.deepcopy(skipped), "success", "successful job timestamps null")
    )
    changed = copy.deepcopy(valid)
    changed["started_at"] = "2026-08-18T00:00:02Z"
    mutations.append((changed, "success", "job timestamps reversed"))
    for changed, conclusion, label in mutations:
        rejected(
            lambda changed=changed, conclusion=conclusion: V6.normalized_job_timestamps(
                changed, conclusion, label
            ),
            label,
        )
    return len(mutations)


def test_v6_workflow_prerequisites() -> int:
    raw = (ROOT / V6.V6_WORKFLOW_RELATIVE).read_bytes()
    V6.validate_v6_workflow_prerequisites(raw)
    first, second = V6.V6_PDF_PREREQUISITE_BLOCKS
    hosted_recovery = V6.V6_CURRENT_HOSTED_RECOVERY_SELF_TEST_BLOCK
    hosted_normal, hosted_optimized, empty = hosted_recovery.split(b"\n")
    require(
        empty == b"" and hosted_normal != hosted_optimized,
        "hosted-recovery workflow prerequisite fixture changed",
    )
    local_capture = V6.HOSTED_L6_CAPTURE_SELF_TEST_BLOCK
    local_normal, local_optimized, local_compare, empty = local_capture.split(b"\n")
    require(
        empty == b"" and local_normal != local_optimized and local_compare != b"",
        "local-closure workflow prerequisite fixture changed",
    )
    mutations: list[tuple[bytes, str]] = [
        (raw.replace(first, b"", 1), "PDF verifier setup removed"),
        (
            raw.replace(
                b"Install the hash-pinned PDF verifier dependency",
                b"Install an unbound PDF dependency",
                1,
            ),
            "PDF verifier setup renamed",
        ),
        (raw.replace(second, b"", 1), "PDF system toolchain setup removed"),
        (
            raw.replace(
                b"Install the runner PDF toolchain",
                b"Install a partial PDF toolchain",
                1,
            ),
            "PDF system toolchain setup renamed",
        ),
        (
            raw.replace(first + second, second + first, 1),
            "PDF prerequisite setup reordered",
        ),
        (
            raw.replace(b"--require-hashes", b"--no-compile", 1),
            "PDF requirement hash enforcement removed",
        ),
        (raw.replace(b"            lacheck \\\n", b"", 1), "PDF tool omitted"),
        (
            raw.replace(hosted_normal + b"\n", b"", 1),
            "hosted-recovery normal self-test removed",
        ),
        (
            raw.replace(hosted_optimized + b"\n", b"", 1),
            "hosted-recovery optimized self-test removed",
        ),
        (
            raw.replace(
                hosted_recovery,
                hosted_optimized + b"\n" + hosted_normal + b"\n",
                1,
            ),
            "hosted-recovery self-test modes reordered",
        ),
        (
            raw.replace(hosted_recovery, b"", 1).replace(
                V6.V6_PUBLICATION_STEP_MARKER,
                V6.V6_PUBLICATION_STEP_MARKER + hosted_recovery,
                1,
            ),
            "hosted-recovery self-test moved after publication validation",
        ),
        (
            raw.replace(local_normal + b"\n", b"", 1),
            "local-closure normal self-test removed",
        ),
        (
            raw.replace(local_optimized + b"\n", b"", 1),
            "local-closure optimized self-test removed",
        ),
        (
            raw.replace(local_compare + b"\n", b"", 1),
            "local-closure mode comparison removed",
        ),
        (
            raw.replace(
                local_capture,
                local_optimized + b"\n" + local_normal + b"\n" + local_compare + b"\n",
                1,
            ),
            "local-closure self-test modes reordered",
        ),
        (
            raw.replace(local_capture, b"", 1).replace(
                V6.V6_PUBLICATION_STEP_MARKER,
                V6.V6_PUBLICATION_STEP_MARKER + local_capture,
                1,
            ),
            "local-closure self-test moved after publication validation",
        ),
        (
            raw.replace(
                local_capture,
                local_capture.replace(
                    b"--self-test", b"--output /tmp/forbidden.json", 1
                ),
                1,
            ),
            "hosted real local capture invoked",
        ),
        (
            raw.replace(V6.V6_ATTEMPT_1_REFUSAL_BLOCK, b"", 1),
            "attempt-1 refusal removed",
        ),
        (
            raw.replace(V6.V6_PORTABILITY_BLOCK, b"", 1),
            "immutable predecessor portability pair removed",
        ),
        (
            raw.replace(V6.V6_BOUNDARY_BLOCK, b"", 1),
            "v6 boundary-publication pair removed",
        ),
        (
            raw.replace(
                V6.V6_PORTABILITY_BLOCK,
                V6.V6_PORTABILITY_BLOCK.replace(b"--cross-toolchain", b"--exact", 1),
                1,
            ),
            "hosted portability mode changed to maintainer exact",
        ),
        (
            raw.replace(
                V6.V6_PORTABILITY_BLOCK + V6.V6_BOUNDARY_BLOCK,
                V6.V6_BOUNDARY_BLOCK + V6.V6_PORTABILITY_BLOCK,
                1,
            ),
            "hosted portability and boundary pairs reordered",
        ),
    ]
    mutations.extend(
        (
            raw + b"# stale semantic token: " + token + b"\n",
            f"stale composite-v3 semantic token {index}",
        )
        for index, token in enumerate(V6.V6_STALE_V3_SEMANTIC_TOKENS, start=1)
    )
    for changed, label in mutations:
        require(changed != raw, f"workflow mutation did not reach its target: {label}")
        rejected(
            lambda changed=changed: V6.validate_v6_workflow_prerequisites(changed),
            label,
        )
    return len(mutations)


def test_frozen_authority_values() -> int:
    retired_v5 = (ROOT / V6.V5_WORKFLOW_RELATIVE).read_bytes()
    successor_v6 = (ROOT / V6.V6_WORKFLOW_RELATIVE).read_bytes()
    hosted_self_test = (
        ROOT / V6.CURRENT_HOSTED_RECOVERY_SELF_TEST_RELATIVE
    ).read_bytes()
    hosted_checker = (ROOT / V6.CURRENT_HOSTED_RECOVERY_CHECKER_RELATIVE).read_bytes()
    local_capture = (ROOT / V6.LOCAL_CLOSURE_TOOL_RELATIVE).read_bytes()
    V6.validate_frozen_workflow_values(retired_v5, successor_v6)
    V6.validate_current_hosted_recovery_values(hosted_self_test, hosted_checker)
    V6.validate_frozen_local_closure_tool(local_capture)
    mutations: list[tuple[Callable[[], Any], str]] = [
        (
            lambda: V6.validate_frozen_workflow_values(
                retired_v5 + b"\n", successor_v6
            ),
            "retired-v5 workflow bytes",
        ),
        (
            lambda: V6.validate_frozen_workflow_values(
                retired_v5, successor_v6 + b"\n"
            ),
            "successor-v6 workflow bytes",
        ),
        (
            lambda: V6.validate_current_hosted_recovery_values(
                hosted_self_test + b"\n", hosted_checker
            ),
            "current hosted-recovery hostile-suite bytes",
        ),
        (
            lambda: V6.validate_current_hosted_recovery_values(
                hosted_self_test, hosted_checker + b"\n"
            ),
            "current hosted-recovery gate bytes",
        ),
        (
            lambda: V6.validate_frozen_local_closure_tool(local_capture + b"\n"),
            "local-closure capture tool bytes",
        ),
    ]
    for operation, label in mutations:
        rejected(operation, label)
    return len(mutations)


def test_local_l6_values() -> int:
    raw = (ROOT / V6.JUSTFILE_RELATIVE).read_bytes()
    V6.validate_local_l6_values(raw)
    block = V6.LOCAL_L6_EXACT_PDF_BLOCK
    capture_block = V6.LOCAL_L6_CAPTURE_SELF_TEST_BLOCK
    capture_normal, capture_optimized, capture_compare, empty = capture_block.split(
        b"\n"
    )
    require(
        empty == b"" and capture_normal != capture_optimized and capture_compare != b"",
        "local capture self-test fixture changed",
    )
    static_marker = (
        b"    python3 -I -S -B scripts/check-ksg-m1a-composite-v6.py "
        b'--validate-static > "$result_root/static.json"\n'
    )
    mutations = [
        (raw.replace(capture_normal + b"\n", b"", 1), "local capture normal removed"),
        (
            raw.replace(capture_optimized + b"\n", b"", 1),
            "local capture optimized removed",
        ),
        (
            raw.replace(capture_compare + b"\n", b"", 1),
            "local capture comparison removed",
        ),
        (
            raw.replace(
                capture_block,
                capture_optimized
                + b"\n"
                + capture_normal
                + b"\n"
                + capture_compare
                + b"\n",
                1,
            ),
            "local capture modes reordered",
        ),
        (
            raw.replace(
                capture_block,
                capture_block.replace(
                    b"--self-test", b"--output /tmp/forbidden.json", 1
                ),
                1,
            ),
            "local recipe invokes real capture",
        ),
        (raw.replace(block, b"", 1), "local exact PDF block removed"),
        (
            raw.replace(block, block.replace(b"--exact", b"--cross-toolchain", 1), 1),
            "local exact mode weakened",
        ),
        (
            raw.replace(block, b"", 1).replace(static_marker, static_marker + block, 1),
            "local exact PDF block moved after static validation",
        ),
        (
            raw.replace(b" ksg-composite-v6 ", b" ksg-composite-v5 ", 1),
            "release audit restored retired v5 selector",
        ),
    ]
    for changed, label in mutations:
        require(changed != raw, f"local L6 mutation missed its target: {label}")
        rejected(lambda changed=changed: V6.validate_local_l6_values(changed), label)
    return len(mutations)


def test_local_closure_record() -> int:
    schema = V6._closed_schema(
        (ROOT / V6.LOCAL_CLOSURE_SCHEMA_RELATIVE).read_bytes(),
        "self-test local-closure schema",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json",
        [
            "authorities",
            "invocation",
            "nonimplications",
            "platform",
            "repository",
            "repository_state",
            "reviewed_executables",
            "schema",
            "schema_revision",
            "subject",
        ],
        V6.LOCAL_CLOSURE_SCHEMA_SHA256,
        V6.LOCAL_CLOSURE_SCHEMA_SIZE_BYTES,
    )
    record, authority_entries = local_record_fixture()
    c6 = record["subject"]["c6_commit"]
    c6_tree = record["subject"]["c6_tree"]

    def validate(changed: dict[str, Any]) -> dict[str, Any]:
        original = V6.authority_descriptor

        def fixture_authority(
            entries: dict[str, bytes], path: str, role: str
        ) -> dict[str, Any]:
            raw = entries[path]
            return {
                "path": path,
                "role": role,
                "sha256": V6.sha256(raw),
                "size_bytes": len(raw),
            }

        V6.authority_descriptor = fixture_authority
        try:
            return V6.validate_local_closure_record(
                V6.canonical_json(changed, pretty=True),
                authority_entries,
                c6,
                c6_tree,
                schema,
            )
        finally:
            V6.authority_descriptor = original

    projection = validate(record)
    require(
        projection == local_qualification_fixture()["observation"],
        "local closure projection fixture changed",
    )
    expected_qualification = local_qualification_fixture()
    qualification_mutations: list[tuple[dict[str, Any], str]] = []
    changed_qualification = copy.deepcopy(expected_qualification)
    changed_qualification["record_binding"]["path"] = V6.SUCCESSOR_CAPTURE_RELATIVE
    qualification_mutations.append((changed_qualification, "local record path binding"))
    changed_qualification = copy.deepcopy(expected_qualification)
    changed_qualification["record_binding"]["sha256"] = "f" * 64
    qualification_mutations.append((changed_qualification, "local record byte binding"))
    changed_qualification = copy.deepcopy(expected_qualification)
    changed_qualification["record_binding"]["size_bytes"] += 1
    qualification_mutations.append((changed_qualification, "local record size binding"))
    changed_qualification = copy.deepcopy(expected_qualification)
    changed_qualification["observation"]["command"]["stdout_sha256"] = "e" * 64
    qualification_mutations.append((changed_qualification, "local output projection"))
    for changed_qualification, label in qualification_mutations:
        rejected(
            lambda changed_qualification=changed_qualification: V6.require(
                changed_qualification == expected_qualification,
                "local qualification differs from raw-record derivation",
            ),
            label,
        )
    mutations: list[tuple[dict[str, Any], str]] = []

    def add(path: tuple[Any, ...], replacement: Any, label: str) -> None:
        changed = copy.deepcopy(record)
        target: Any = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = replacement
        mutations.append((changed, label))

    add(("invocation", "exit_code"), 1, "forged zero exit")
    add(("invocation", "signal"), 15, "signal erased")
    add(("invocation", "timed_out"), True, "timeout erased")
    add(("invocation", "argv"), ["just", "other"], "alternate command")
    add(
        ("invocation", "argv"),
        ["ksg-composite-v6", "just"],
        "reordered command",
    )
    add(("invocation", "cwd"), "<OTHER_ROOT>", "wrong cwd")
    environment = dict(record["invocation"]["environment"])
    environment["HOME"] = "<PRIVATE_TEMP_HOME>"
    add(("invocation", "environment"), environment, "unexpected HOME route")
    environment = dict(record["invocation"]["environment"])
    environment["XDG_CONFIG_HOME"] = "<AMBIENT_CONFIG>"
    add(("invocation", "environment"), environment, "XDG route drift")
    add(("invocation", "umask"), "0022", "umask drift")
    add(("invocation", "environment_routes_sha256"), "bad", "route digest")
    add(("invocation", "monotonic_finish_ns"), 101, "monotonic mismatch")
    add(
        ("invocation", "started_at"),
        "2026-08-18T00:00:05.000000Z",
        "wall-clock reversal",
    )
    add(
        ("invocation", "started_at"),
        "2026-08-18T00:00:02",
        "naive timestamp",
    )
    add(("subject", "c6_commit"), "4" * 40, "wrong C6")
    add(("subject", "c6_tree"), "5" * 40, "wrong C6 tree")
    add(
        ("repository_state", "before", "common_dir"),
        "<OTHER_ROOT>/.git",
        "common-dir overlay",
    )
    add(
        ("repository_state", "before", "object_format"),
        "sha256",
        "object-format drift",
    )
    add(
        ("repository_state", "before", "http_alternates"),
        "present",
        "HTTP alternates hidden",
    )
    add(
        ("repository_state", "before", "info_attributes_rules"),
        "present",
        "info attributes hidden",
    )
    add(
        ("repository_state", "before", "info_exclude_rules"),
        "present",
        "info excludes hidden",
    )
    add(
        ("repository_state", "after", "head"),
        "6" * 40,
        "post-command HEAD drift",
    )
    dirty = byte_binding(b"? untracked\n")
    add(("repository_state", "before", "status"), dirty, "dirty pre-state")
    add(("repository_state", "after", "status"), dirty, "dirty post-state")
    add(
        ("authorities", 0, "sha256"),
        "7" * 64,
        "authority preimage drift",
    )
    add(
        ("reviewed_executables", 0, "route"),
        "<SYSTEM_BIN>/python3",
        "reviewed route/name mismatch",
    )
    add(
        ("reviewed_executables", 0, "version_argv"),
        [record["reviewed_executables"][0]["name"], "-V"],
        "reviewed version command drift",
    )
    add(
        ("reviewed_executables", 0, "executable_sha256"),
        "bad",
        "reviewed executable digest grammar",
    )
    add(
        ("reviewed_executables", 0, "version_stdout", "sha256"),
        "8" * 64,
        "version output digest drift",
    )
    add(
        ("reviewed_executables", 0, "version_stdout", "size_bytes"),
        record["reviewed_executables"][0]["version_stdout"]["size_bytes"] + 1,
        "version output size drift",
    )
    add(
        ("invocation", "stdout", "sha256"),
        "9" * 64,
        "command stdout digest drift",
    )
    add(
        ("invocation", "stdout", "size_bytes"),
        record["invocation"]["stdout"]["size_bytes"] + 1,
        "command stdout size drift",
    )
    add(
        ("invocation", "stdout", "body_base64"),
        record["invocation"]["stdout"]["body_base64"] + "=",
        "command stdout noncanonical base64",
    )
    add(
        ("invocation", "stdout"),
        byte_binding(b"Authorization: Bearer fixture-secret-value"),
        "token-like command output",
    )
    add(
        ("invocation", "stderr"),
        byte_binding(b"/Users/private-user/repository/file"),
        "private absolute path output",
    )
    add(
        ("platform", "operating_system_release"),
        "25.6.0\nprivate",
        "unsafe platform release",
    )
    add(("platform", "python_version"), "3.10.9", "unexpected Python version")
    add(
        ("nonimplications",),
        record["nonimplications"][:-1],
        "local nonclaim removed",
    )
    add(
        ("nonimplications",),
        [
            item
            for item in record["nonimplications"]
            if item != V6.GIT_CLEAN_NONHERMETIC_NONCLAIM
        ],
        "ignored-products nonclaim removed",
    )
    changed = copy.deepcopy(record)
    del changed["reviewed_executables"][-1]
    mutations.append((changed, "reviewed executable omitted"))
    changed = copy.deepcopy(record)
    changed["reviewed_executables"] = list(reversed(changed["reviewed_executables"]))
    mutations.append((changed, "reviewed executables reordered"))
    changed = copy.deepcopy(record)
    del changed["invocation"]["stdout"]
    mutations.append((changed, "command output omitted"))
    changed = copy.deepcopy(record)
    changed["unexpected"] = True
    mutations.append((changed, "open local record root"))
    for changed, label in mutations:
        rejected(lambda changed=changed: validate(changed), label)
    compact = V6.canonical_json(record, pretty=False)
    original = V6.authority_descriptor
    try:
        rejected(
            lambda: V6.validate_local_closure_record(
                compact, authority_entries, c6, c6_tree, schema
            ),
            "noncanonical compact local record",
        )
    finally:
        V6.authority_descriptor = original
    return len(mutations) + len(qualification_mutations) + 1


def test_local_input_descriptors() -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-c6-fd-self-test-") as root_text:
        path = Path(root_text) / "input.json"
        path.write_bytes(b'{"fixture":true}\n')
        path.chmod(0o600)
        descriptor_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            require(
                V6.bounded_regular_fd(descriptor_fd, "positive fixture")
                == b'{"fixture":true}\n',
                "bounded evidence descriptor changed bytes",
            )
        finally:
            os.close(descriptor_fd)

        descriptor_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            os.read(descriptor_fd, 1)
            rejected(
                lambda: V6.bounded_regular_fd(descriptor_fd, "offset fixture"),
                "nonzero evidence descriptor offset",
            )
        finally:
            os.close(descriptor_fd)

        path.chmod(0o644)
        descriptor_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            rejected(
                lambda: V6.bounded_regular_fd(descriptor_fd, "mode fixture"),
                "non-0600 evidence descriptor",
            )
        finally:
            os.close(descriptor_fd)

        read_fd, write_fd = os.pipe()
        try:
            rejected(
                lambda: V6.bounded_regular_fd(read_fd, "pipe fixture"),
                "nonregular evidence descriptor",
            )
        finally:
            os.close(read_fd)
            os.close(write_fd)

        rejected(
            lambda: V6.derive_receipt_command(3, 3),
            "reused local/successor evidence descriptor",
        )
    return 4


def test_policy() -> int:
    require(V6.C6_POLICY_ROWS, "C6 policy rows have not been frozen")
    require(
        len(V6.C6_POLICY_ROWS) == 43
        and sum(row[1] == "M" for row in V6.C6_POLICY_ROWS) == 21
        and sum(row[1] == "A" for row in V6.C6_POLICY_ROWS) == 22,
        "C6 policy does not have the exact 43-row 21-M/22-A inventory",
    )
    require(
        len(V6.R6_POLICY_ROWS) == 4
        and V6.R6_POLICY_ROWS[1]
        == (
            V6.LOCAL_CLOSURE_RELATIVE,
            "A",
            "100644",
            "durable_local_l6_closure",
        ),
        "R6 policy does not have the exact four-row local-evidence inventory",
    )
    portability_rows = tuple(
        row
        for row in V6.C6_POLICY_ROWS
        if row[0].startswith("scripts/check-ksg-m1a-composite-v6-pdf-portability")
    )
    require(
        portability_rows
        == (
            (
                "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh",
                "A",
                "100755",
                "immutable_predecessor_pdf_portability_hostile_suite",
            ),
            (
                "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh",
                "A",
                "100755",
                "immutable_predecessor_pdf_portability_gate",
            ),
        ),
        "immutable predecessor portability rows changed",
    )
    expected_policy = policy_fixture()
    policy = V6.parse_json(
        (ROOT / V6.POLICY_RELATIVE).read_bytes(), "stored composite-v6 path policy"
    )
    require(policy == expected_policy, "stored composite-v6 path policy bytes drifted")
    V6.validate_policy_value(policy)
    mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(policy)
    changed["base"]["r4_status"] = "issued"
    mutations.append((changed, "R4 status"))
    changed = copy.deepcopy(policy)
    changed["base"]["r5_status"] = "issued"
    mutations.append((changed, "R5 status"))
    changed = copy.deepcopy(policy)
    changed["base"]["reserved_absent_paths"] = list(
        reversed(V6.FORBIDDEN_R4_R5_EVIDENCE_PATHS)
    )
    mutations.append((changed, "reserved-path order"))
    changed = copy.deepcopy(policy)
    changed["c6"]["message"] = "Repair something else\n"
    mutations.append((changed, "C6 message"))
    changed = copy.deepcopy(policy)
    changed["c6"]["delta"] = changed["c6"]["delta"][:-1]
    mutations.append((changed, "C6 missing row"))
    changed = copy.deepcopy(policy)
    changed["c6"]["delta"] = [
        row
        for row in changed["c6"]["delta"]
        if row["path"]
        != "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh"
    ]
    mutations.append((changed, "C6 missing portability hostile suite"))
    changed = copy.deepcopy(policy)
    next(
        row
        for row in changed["c6"]["delta"]
        if row["path"] == "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh"
    )["role"] = "immutable_v5_only_portability_gate"
    mutations.append((changed, "C6 narrowed portability role"))
    changed = copy.deepcopy(policy)
    first_index = next(
        index
        for index, row in enumerate(changed["c6"]["delta"])
        if row["path"]
        == "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh"
    )
    changed["c6"]["delta"][first_index : first_index + 2] = reversed(
        changed["c6"]["delta"][first_index : first_index + 2]
    )
    mutations.append((changed, "C6 portability rows reordered"))
    changed = copy.deepcopy(policy)
    changed["r6"]["delta"][0]["status"] = "A"
    mutations.append((changed, "R6 current-source status"))
    changed = copy.deepcopy(policy)
    del changed["r6"]["delta"][1]
    mutations.append((changed, "R6 local closure omitted"))
    changed = copy.deepcopy(policy)
    changed["nonimplications"] = changed["nonimplications"][:-1]
    mutations.append((changed, "policy nonclaim"))
    changed = copy.deepcopy(policy)
    changed["nonimplications"] = [
        item
        for item in changed["nonimplications"]
        if item != V6.GIT_CLEAN_NONHERMETIC_NONCLAIM
    ]
    mutations.append((changed, "ignored-products policy nonclaim"))
    for changed, label in mutations:
        rejected(lambda changed=changed: V6.validate_policy_value(changed), label)
    return len(mutations)


def test_receipt_schema() -> int:
    raw = (ROOT / V6.RECEIPT_SCHEMA_RELATIVE).read_bytes()
    schema = V6._closed_schema(
        raw,
        "self-test composite-v6 receipt",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-receipt-v6.schema.json",
        [
            "capture_bindings",
            "contract_authorities",
            "local_qualification",
            "nonimplications",
            "observations",
            "repository",
            "schema",
            "schema_revision",
            "subject",
            "verdict",
        ],
        V6.RECEIPT_SCHEMA_SHA256,
        V6.RECEIPT_SCHEMA_SIZE_BYTES,
    )
    receipt = receipt_fixture()
    V6.validate_schema_instance(receipt, schema, "positive receipt fixture")
    V6.parse_json(
        V6.canonical_json(receipt, pretty=True), "positive stored receipt fixture"
    )
    mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(receipt)
    changed["verdict"]["c5_hosted_qualification"] = "pass"
    mutations.append((changed, "C5 hosted-qualification verdict upgrade"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["c5_publication"] = "failed"
    mutations.append((changed, "C5 publication erasure"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["r5_receipt_issued"] = True
    mutations.append((changed, "R5 issued"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["r6_receipt_issued"] = False
    mutations.append((changed, "R6 erased"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["c6_local_qualification"] = "not_observed"
    mutations.append((changed, "local qualification erased"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["scientific_validation"] = "pass"
    mutations.append((changed, "scientific overclaim"))
    changed = copy.deepcopy(receipt)
    changed["capture_bindings"][1] = copy.deepcopy(changed["capture_bindings"][0])
    mutations.append((changed, "duplicate capture binding"))
    changed = copy.deepcopy(receipt)
    del changed["local_qualification"]
    mutations.append((changed, "local qualification binding omitted"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["record_binding"]["path"] = (
        V6.SUCCESSOR_CAPTURE_RELATIVE
    )
    mutations.append((changed, "local qualification path changed"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["record_binding"]["sha256"] = "bad"
    mutations.append((changed, "local qualification digest malformed"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["observation"]["command"]["exit_code"] = 1
    mutations.append((changed, "local command exit upgraded"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["observation"]["command"]["argv"] = [
        "just",
        "other",
    ]
    mutations.append((changed, "local command projection changed"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["observation"]["repository_state"][
        "before_status_size_bytes"
    ] = 1
    mutations.append((changed, "local clean-state projection changed"))
    changed = copy.deepcopy(receipt)
    changed["local_qualification"]["observation"]["repository_state"][
        "http_alternates"
    ] = "present"
    mutations.append((changed, "local HTTP-alternates projection changed"))
    changed = copy.deepcopy(receipt)
    changed["subject"]["c6_tree"] = "bad"
    mutations.append((changed, "tree identity"))
    changed = copy.deepcopy(receipt)
    del changed["observations"][0]["roles"][0]["failed_job_logs"][0]["job_name"]
    mutations.append((changed, "failed-job name"))
    changed = copy.deepcopy(receipt)
    del changed["observations"][0]["roles"][0]["failed_job_logs"][0]["observed_markers"]
    mutations.append((changed, "observed failure marker"))
    changed = copy.deepcopy(receipt)
    ci_failure_log = next(
        item
        for item in changed["observations"][0]["roles"][0]["failed_job_logs"]
        if item["job_id"] == 95619717365
    )
    ci_failure_log["observed_markers"] = ["different PDF symptom"]
    mutations.append((changed, "CI failure marker"))
    changed = copy.deepcopy(receipt)
    changed["observations"][0]["roles"][0]["job_ids"] *= 2
    mutations.append((changed, "duplicate job identifier"))
    changed = copy.deepcopy(receipt)
    changed["unexpected"] = True
    mutations.append((changed, "open root"))
    changed = copy.deepcopy(receipt)
    changed["nonimplications"][1] = changed["nonimplications"][0]
    mutations.append((changed, "duplicate nonclaim"))
    changed = copy.deepcopy(receipt)
    changed["nonimplications"] = [
        item
        for item in changed["nonimplications"]
        if item != V6.GIT_CLEAN_NONHERMETIC_NONCLAIM
    ]
    mutations.append((changed, "ignored-products receipt nonclaim removed"))
    for changed, label in mutations:
        rejected(
            lambda changed=changed: V6.validate_schema_instance(changed, schema, label),
            label,
        )
    rejected(
        lambda: V6.parse_json(
            V6.canonical_json(receipt, pretty=False), "compact stored receipt fixture"
        ),
        "noncanonical compact stored receipt",
    )
    return len(mutations) + 1


def test_replay_and_delta() -> tuple[int, int]:
    r10_raw = b"immutable prior r10 bytes"
    replay = {
        "prior_replay_preservation_sha256": {V6.LEAN_R10_RELATIVE: V6.sha256(r10_raw)},
        "prior_replay_schema": {
            V6.LEAN_R10_RELATIVE: "pid-rs/lean-current-project-replay/v2"
        },
        "schema": "pid-rs/lean-current-project-replay/v2",
        "status": "passed",
    }
    V6.validate_replay_values(r10_raw, replay)
    replay_mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(replay)
    changed["status"] = "failed"
    replay_mutations.append((changed, "r11 status"))
    changed = copy.deepcopy(replay)
    changed["prior_replay_preservation_sha256"][V6.LEAN_R10_RELATIVE] = "0" * 64
    replay_mutations.append((changed, "r10 prior digest"))
    changed = copy.deepcopy(replay)
    changed["prior_replay_schema"][V6.LEAN_R10_RELATIVE] = "v3"
    replay_mutations.append((changed, "r10 prior schema"))
    for changed, label in replay_mutations:
        rejected(
            lambda changed=changed: V6.validate_replay_values(r10_raw, changed), label
        )

    expected = tuple(
        (path, status, mode) for path, status, mode, _role in V6.R6_POLICY_ROWS
    )
    V6.validate_exact_delta(expected, expected, "positive R6")
    delta_mutations = [
        expected[:-1],
        tuple(reversed(expected)),
        (*expected, expected[0]),
    ]
    for index, changed in enumerate(delta_mutations):
        rejected(
            lambda changed=changed: V6.validate_exact_delta(changed, expected, "R6"),
            f"R6 delta {index}",
        )
    return len(replay_mutations), len(delta_mutations)


def test_lean_r11_checksum_cut() -> int:
    projection = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    scalar = 'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "0" * 64'
    operational = '    "scripts/check-ksg-m1a-composite-v6.py": "0" * 64,'
    normalized_lean = (projection + "\n" + scalar + "\n" + operational + "\n").encode(
        "utf-8"
    )
    normalized_digest = V6.sha256(normalized_lean)
    checker_raw = (
        'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "' + normalized_digest + '"\n'
    ).encode("utf-8")

    def seal_lean(checker: bytes, projection_value: str = "1" * 64) -> bytes:
        checker_digest = V6.sha256(checker)
        return (
            normalized_lean.replace(
                projection.encode("utf-8"),
                (
                    'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
                    + projection_value
                    + '"'
                ).encode("utf-8"),
                1,
            )
            .replace(
                scalar.encode("utf-8"),
                (
                    'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "'
                    + checker_digest
                    + '"'
                ).encode("utf-8"),
                1,
            )
            .replace(
                operational.encode("utf-8"),
                (
                    '    "scripts/check-ksg-m1a-composite-v6.py": "'
                    + checker_digest
                    + '",'
                ).encode("utf-8"),
                1,
            )
        )

    checker_digest = V6.sha256(checker_raw)
    replay_lean_raw = normalized_lean.replace(
        scalar.encode("utf-8"),
        (
            'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "'
            + checker_digest
            + '"'
        ).encode("utf-8"),
        1,
    ).replace(
        operational.encode("utf-8"),
        (
            '    "scripts/check-ksg-m1a-composite-v6.py": "' + checker_digest + '",'
        ).encode("utf-8"),
        1,
    )
    self_test_path = "scripts/check-lean-toolchain-freeze-self-test.py"
    r11 = {
        "custody_gate_sha256": {
            self_test_path: "a" * 64,
            V6.LEAN_CHECKER_RELATIVE: "0" * 64,
        },
        "operational_wiring_sha256": {V6.CHECKER_RELATIVE: checker_digest},
        "prior_replay_preservation_sha256": {V6.LEAN_R10_RELATIVE: "b" * 64},
        "prior_replay_schema": {
            V6.LEAN_R10_RELATIVE: "pid-rs/lean-current-project-replay/v2"
        },
        "replay_custody_gate_sha256": {
            self_test_path: "a" * 64,
            V6.LEAN_CHECKER_RELATIVE: V6.sha256(replay_lean_raw),
        },
        "schema": "pid-rs/lean-current-project-replay/v2",
        "status": "passed",
    }
    projection_value = V6.lean_replay_projection_sha256(r11)
    lean_raw = seal_lean(checker_raw, projection_value)
    r11["custody_gate_sha256"][V6.LEAN_CHECKER_RELATIVE] = V6.sha256(lean_raw)
    V6.validate_lean_r11_checksum_cut(checker_raw, lean_raw)
    V6.validate_lean_r11_receipt_cuts(checker_raw, lean_raw, r11, projection_value)
    mismatched_checker = checker_raw.replace(
        normalized_digest.encode("ascii"), b"3" * 64, 1
    )
    placeholder_checker = checker_raw.replace(
        normalized_digest.encode("ascii"), b"0" * 64, 1
    )
    mutations = (
        (checker_raw + b"# post-seal drift\n", lean_raw, "v6 checker causal drift"),
        (
            checker_raw,
            lean_raw.replace(
                (
                    'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "'
                    + checker_digest
                    + '"'
                ).encode("utf-8"),
                (
                    'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "'
                    + "2" * 64
                    + '"'
                ).encode("utf-8"),
                1,
            ),
            "v6 scalar cut",
        ),
        (
            checker_raw,
            lean_raw.replace(
                (
                    '    "scripts/check-ksg-m1a-composite-v6.py": "'
                    + checker_digest
                    + '",'
                ).encode("utf-8"),
                (
                    '    "scripts/check-ksg-m1a-composite-v6.py": "' + "2" * 64 + '",'
                ).encode("utf-8"),
                1,
            ),
            "v6 operational cut",
        ),
        (mismatched_checker, seal_lean(mismatched_checker), "normalized Lean cut"),
        (placeholder_checker, seal_lean(placeholder_checker), "normalized placeholder"),
        (
            checker_raw + checker_raw,
            seal_lean(checker_raw + checker_raw),
            "duplicate cut",
        ),
        (checker_raw, lean_raw + b"# normalized-source drift\n", "Lean source drift"),
    )
    for changed_checker, changed_lean, label in mutations:
        rejected(
            lambda changed_checker=changed_checker, changed_lean=changed_lean: (
                V6.validate_lean_r11_checksum_cut(changed_checker, changed_lean)
            ),
            label,
        )
    receipt_mutations: list[tuple[bytes, dict[str, Any], str, str]] = []
    changed = copy.deepcopy(r11)
    changed["operational_wiring_sha256"][V6.CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append((lean_raw, changed, projection_value, "r11 v6 map"))
    changed = copy.deepcopy(r11)
    changed["custody_gate_sha256"][V6.LEAN_CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append((lean_raw, changed, projection_value, "r11 final custody"))
    changed = copy.deepcopy(r11)
    changed["replay_custody_gate_sha256"][V6.LEAN_CHECKER_RELATIVE] = "0" * 64
    receipt_mutations.append(
        (lean_raw, changed, projection_value, "r11 replay custody")
    )
    receipt_mutations.append((lean_raw, r11, "2" * 64, "r11 projection"))
    for changed_lean, changed_r11, changed_projection, label in receipt_mutations:
        rejected(
            lambda changed_lean=changed_lean, changed_r11=changed_r11, changed_projection=changed_projection: (
                V6.validate_lean_r11_receipt_cuts(
                    checker_raw, changed_lean, changed_r11, changed_projection
                )
            ),
            label,
        )
    return len(mutations) + len(receipt_mutations)


def test_identifier_domains() -> int:
    phases = receipt_fixture()["observations"]
    V6.validate_identifier_domains(phases, "positive phases")
    mutations: list[tuple[list[dict[str, Any]], str]] = []
    changed = copy.deepcopy(phases)
    changed[1]["roles"][0]["run"]["repository_id"] = 78
    mutations.append((changed, "repository join"))
    changed = copy.deepcopy(phases)
    changed[1]["roles"][0]["run"]["run_id"] = changed[0]["roles"][0]["run"]["run_id"]
    mutations.append((changed, "run domain"))
    changed = copy.deepcopy(phases)
    changed[1]["roles"][0]["job_ids"] = changed[0]["roles"][0]["job_ids"]
    mutations.append((changed, "job domain"))
    changed = copy.deepcopy(phases)
    changed[0]["roles"][0]["codeql_analysis_ids"] = [88]
    changed[1]["roles"][1]["codeql_analysis_ids"] = [88]
    mutations.append((changed, "analysis domain"))
    changed = copy.deepcopy(phases)
    artifact = {
        "archive_sha256": "a" * 64,
        "archive_size_bytes": 1,
        "artifact_id": 99,
        "members_sha256": "b" * 64,
        "name": "fixture",
    }
    changed[0]["roles"][0]["artifacts"] = [copy.deepcopy(artifact)]
    changed[1]["roles"][0]["artifacts"] = [copy.deepcopy(artifact)]
    mutations.append((changed, "artifact domain"))
    for changed, label in mutations:
        rejected(
            lambda changed=changed: V6.validate_identifier_domains(changed, label),
            label,
        )
    return len(mutations)


def test_predecessor_failure_surface() -> int:
    known_ci = set(V6.PREDECESSOR_REQUIRED_FAILED_JOB_IDS["predecessor_ci"])
    V6.validate_predecessor_failed_set("predecessor_ci", known_ci)
    known_contract = set(V6.PREDECESSOR_REQUIRED_FAILED_JOB_IDS["predecessor_contract"])
    V6.validate_predecessor_failed_set("predecessor_contract", known_contract)
    jobs = [
        {
            "conclusion": "failure",
            "job_id": job_id,
            "name": name,
            "steps": [
                {"conclusion": "failure", "name": step_name}
                for step_name in failed_steps
            ],
        }
        for job_id, (name, failed_steps) in V6.PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[
            "predecessor_ci"
        ].items()
    ]
    V6.validate_predecessor_failure_identities("predecessor_ci", jobs, known_ci)
    groups: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]] = {}
    for repetition in (1, 2):
        for job_id in sorted(known_ci):
            marker = V6.PREDECESSOR_REQUIRED_LOG_MARKERS[job_id][0]
            logical = f"predecessor_ci_failed_job_{job_id}_log"
            groups[(logical, repetition)] = [
                (
                    {
                        "page": 0,
                        "path": f"/repos/{V6.REPOSITORY}/actions/jobs/{job_id}/logs",
                        "response_kind": "log",
                    },
                    f"provider prefix\n{marker}\nprovider suffix\n".encode("ascii"),
                )
            ]
    retained_logs = V6.failed_job_logs(
        V6.CaptureRows(copy.deepcopy(groups)), "predecessor_ci", known_ci, jobs
    )
    require(
        [item["job_id"] for item in retained_logs] == sorted(known_ci)
        and len(retained_logs) == 1,
        "predecessor capture did not retain the exact CI failure log",
    )
    missing_ci_groups = copy.deepcopy(groups)
    ci_job_id = next(iter(known_ci))
    del missing_ci_groups[(f"predecessor_ci_failed_job_{ci_job_id}_log", 2)]
    rejected(
        lambda: V6.failed_job_logs(
            V6.CaptureRows(missing_ci_groups), "predecessor_ci", known_ci, jobs
        ),
        "CI failure log absent",
    )
    set_mutations: list[tuple[str, set[int]]] = [
        ("missing known CI failure", known_ci - {min(known_ci)}),
        ("extra CI failure", known_ci | {99999999999}),
        ("extra dedicated failure", known_contract | {99999999998}),
    ]
    for label, failed in set_mutations:
        role = (
            "predecessor_ci"
            if label in {"missing known CI failure", "extra CI failure"}
            else "predecessor_contract"
        )
        rejected(
            lambda role=role, failed=failed: V6.validate_predecessor_failed_set(
                role, failed
            ),
            label,
        )
    identity_mutations: list[tuple[list[dict[str, Any]], str]] = []
    changed = copy.deepcopy(jobs)
    ci_index = next(
        index for index, item in enumerate(changed) if item["job_id"] == ci_job_id
    )
    changed[ci_index]["name"] = "different job"
    identity_mutations.append((changed, "CI failure job renamed"))
    changed = copy.deepcopy(jobs)
    changed[ci_index]["steps"][0]["name"] = "different failed step"
    identity_mutations.append((changed, "CI failed step renamed"))
    for changed, label in identity_mutations:
        rejected(
            lambda changed=changed: V6.validate_predecessor_failure_identities(
                "predecessor_ci", changed, known_ci
            ),
            label,
        )
    marker_jobs = (
        (95619717365, "predecessor_ci"),
        (95619716898, "predecessor_contract"),
    )
    for job_id, role in marker_jobs:
        marker = V6.PREDECESSOR_REQUIRED_LOG_MARKERS[job_id][0]
        require(
            V6.observed_failure_markers(
                job_id,
                f"provider prefix\n{marker}\nprovider suffix".encode("ascii"),
                role,
            )
            == [marker],
            f"required raw-log marker was not preserved for job {job_id}",
        )
        rejected(
            lambda job_id=job_id: V6.observed_failure_markers(
                job_id, b"different provider output\n", role
            ),
            f"required raw-log marker missing for job {job_id}",
        )
    return len(set_mutations) + len(identity_mutations) + len(marker_jobs) + 1


def test_forbidden_r4_r5_history() -> int:
    V6.validate_no_r4_r5_tree_message({}, V6.C6_MESSAGE, "1" * 40)
    mutations: list[tuple[dict[str, Any], str, str]] = [
        ({path: object()}, V6.C6_MESSAGE, f"forbidden path {path}")
        for path in V6.FORBIDDEN_R4_R5_EVIDENCE_PATHS
    ]
    mutations.extend(
        [
            ({}, V6.FORBIDDEN_R4_MESSAGE, "forbidden R4 commit message"),
            ({}, V6.FORBIDDEN_R5_MESSAGE, "forbidden R5 commit message"),
        ]
    )
    for entries, message, label in mutations:
        rejected(
            lambda entries=entries, message=message: V6.validate_no_r4_r5_tree_message(
                entries, message, "2" * 40
            ),
            label,
        )
    return len(mutations)


def main() -> int:
    try:
        capture_count = test_capture_rows()
        run_count, job_count = test_runs_and_jobs()
        timestamp_count = test_job_timestamps()
        workflow_count = test_v6_workflow_prerequisites()
        frozen_authority_count = test_frozen_authority_values()
        local_l6_count = test_local_l6_values()
        local_closure_count = test_local_closure_record()
        local_descriptor_count = test_local_input_descriptors()
        policy_count = test_policy()
        receipt_count = test_receipt_schema()
        replay_count, delta_count = test_replay_and_delta()
        lean_cut_count = test_lean_r11_checksum_cut()
        identifier_count = test_identifier_domains()
        failure_surface_count = test_predecessor_failure_surface()
        forbidden_history_count = test_forbidden_r4_r5_history()
        result = {
            "capture_mutations_rejected": capture_count,
            "delta_mutations_rejected": delta_count,
            "forbidden_r4_r5_history_mutations_rejected": forbidden_history_count,
            "frozen_authority_mutations_rejected": frozen_authority_count,
            "job_mutations_rejected": job_count,
            "identifier_domain_mutations_rejected": identifier_count,
            "job_timestamp_mutations_rejected": timestamp_count,
            "lean_checksum_cut_mutations_rejected": lean_cut_count,
            "local_closure_record_mutations_rejected": local_closure_count,
            "local_input_descriptor_mutations_rejected": local_descriptor_count,
            "local_l6_mutations_rejected": local_l6_count,
            "policy_mutations_rejected": policy_count,
            "predecessor_failure_surface_mutations_rejected": failure_surface_count,
            "receipt_schema_mutations_rejected": receipt_count,
            "replay_mutations_rejected": replay_count,
            "result": "pass",
            "run_mutations_rejected": run_count,
            "schema": "pid-rs/ksg-rev4-m1a-composite-v6-self-test/v1",
            "v5_primitives_sha256": V6.V5_CHECKER_SHA256,
            "workflow_prerequisite_mutations_rejected": workflow_count,
        }
        sys.stdout.buffer.write(V6.canonical_json(result, pretty=True))
        return 0
    except (SelfTestError, V6.ContractError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
