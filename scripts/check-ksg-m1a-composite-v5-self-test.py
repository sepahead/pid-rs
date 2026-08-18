#!/usr/bin/env python3
"""Adversarial bounded-repair tests for the composite-v5 contract checker."""

from __future__ import annotations

import base64
import copy
import importlib.util
import os
from pathlib import Path
import sys
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
        "ERROR: check-ksg-m1a-composite-v5-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v5.py"


class SelfTestError(RuntimeError):
    """A positive vector failed or an adverse mutation was accepted."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_checker() -> Any:
    specification = importlib.util.spec_from_file_location(
        "_pid_rs_composite_v5_self_test_target", CHECKER
    )
    require(
        specification is not None and specification.loader is not None,
        "checker import route is unavailable",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


V5 = load_checker()


def rejected(operation: Callable[[], Any], label: str) -> None:
    try:
        operation()
    except V5.ContractError:
        return
    raise SelfTestError(f"mutation was accepted: {label}")


def descriptor(path: str, digest: str = "a" * 64) -> dict[str, Any]:
    return {"path": path, "sha256": digest, "size_bytes": 1}


def run(role: str, conclusion: str, run_id: int = 101) -> dict[str, Any]:
    kind = V5.ROLE_KIND[role]
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
        version = "v4" if role.startswith("predecessor_") else "v5"
        name = f"KSG M1a composite {version}"
        path = f".github/workflows/ksg-m1a-composite-{version}.yml"
        event = "push"
        workflow_id = 411
    return {
        "conclusion": conclusion,
        "event": event,
        "head_branch": "main",
        "head_repository": {"full_name": V5.REPOSITORY, "id": 77},
        "head_sha": V5.C4_COMMIT,
        "id": run_id,
        "name": name,
        "path": path,
        "repository": {"full_name": V5.REPOSITORY, "id": 77},
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
    if V5.ROLE_KIND[role] == "contract":
        name = (
            "Validate the composite-v4 contract"
            if role.startswith("predecessor_")
            else "Validate the composite-v5 correction contract"
        )
    else:
        name = "unused"
    if role == "predecessor_contract":
        step_values = [
            ("Validate static contract in normal and optimized modes", "failure"),
            ("Reject the adversarial contract and capture vectors", "skipped"),
            ("Upload the exact static result", "skipped"),
        ]
    elif role == "successor_contract":
        step_values = [
            ("Normalize only the reviewed inert checkout residue", "success"),
            ("Install the hash-pinned PDF verifier dependency", "success"),
            ("Install the runner PDF toolchain", "success"),
            ("Recheck every bounded C4 failure surface", "success"),
            ("Validate the bounded successor publication", "success"),
            ("Validate fresh replay and current-source custody", "success"),
            ("Validate static v5 contract in normal and optimized modes", "success"),
            ("Upload the exact v5 static result", "success"),
        ]
    else:
        step_values = [("bounded failure surface", conclusion)]
    return {
        "completed_at": "2026-08-18T00:00:01Z",
        "conclusion": conclusion,
        "head_sha": V5.C4_COMMIT,
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
    normalized = V5.normalized_run(
        run(role, conclusion, run_id), role, run_id, V5.C4_COMMIT
    )
    logs = (
        [
            {
                "failed_steps": ["bounded failure surface"],
                "job_id": 700 + run_id,
                "job_name": "failed boundary",
                "observed_markers": ["bounded failure surface"],
                "sha256": "f" * 64,
                "size_bytes": 1,
            }
        ]
        if conclusion == "failure"
        else []
    )
    return {
        "artifacts": [],
        "artifacts_sha256": "a" * 64,
        "codeql_alerts_sha256": None,
        "codeql_analysis_ids": [],
        "codeql_analyses_sha256": None,
        "failed_job_logs": logs,
        "failed_job_logs_sha256": "b" * 64,
        "job_count": 1,
        "job_ids": [5000 + run_id],
        "jobs_sha256": "c" * 64,
        "kind": V5.ROLE_KIND[role],
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
                **descriptor(V5.PREDECESSOR_CAPTURE_RELATIVE, "d" * 64),
                "phase": "predecessor_failure",
            },
            {
                **descriptor(V5.SUCCESSOR_CAPTURE_RELATIVE, "e" * 64),
                "phase": "successor_qualification",
            },
        ],
        "contract_authorities": authorities,
        "nonimplications": V5.RECEIPT_NONIMPLICATIONS,
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
        "repository": V5.REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v5",
        "schema_revision": 5,
        "subject": {
            "c4_commit": V5.C4_COMMIT,
            "c4_tree": V5.C4_TREE,
            "c5_commit": "1" * 40,
            "c5_tree": "2" * 40,
        },
        "verdict": {
            "c4_hosted_qualification": "failed_zero_credit",
            "c4_publication": "published",
            "c5_bounded_repair": "pass",
            "c5_hosted_observation": "pass",
            "r4_receipt_issued": False,
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
            "commit": V5.C4_COMMIT,
            "r4_status": "permanently_unissued",
            "reserved_absent_paths": list(V5.FORBIDDEN_R4_PATHS),
            "tree": V5.C4_TREE,
        },
        "c5": {
            "delta": render(V5.C5_POLICY_ROWS),
            "direct_parent_role": "published_c4_contract",
            "message": V5.C5_MESSAGE,
        },
        "nonimplications": V5.POLICY_NONIMPLICATIONS,
        "r5": {
            "delta": render(V5.R5_POLICY_ROWS),
            "direct_parent_role": "c5_contract_repair",
            "message": V5.R5_MESSAGE,
        },
        "repository": V5.REPOSITORY,
        "schema": "pid-rs/ksg-m1a-composite-v5-path-policy",
        "schema_revision": 1,
    }


def test_capture_rows() -> int:
    body = b"terminal failure log\n"
    row = {
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": V5.sha256(body),
        "body_size_bytes": len(body),
        "logical_request": "predecessor_contract_failed_job_95540602684_log",
        "media_type": "text/plain",
        "page": 0,
        "path": f"/repos/{V5.REPOSITORY}/actions/jobs/95540602684/logs",
        "redirect": {
            "status_code": 302,
            "target_host": "safe.blob.core.windows.net",
            "target_url_sha256": "a" * 64,
        },
        "repetition": 1,
        "response_kind": "log",
        "status_code": 200,
    }
    V5.decode_capture_row(row, "positive failed-job log")
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
    changed["path"] = f"/repos/{V5.REPOSITORY}/actions/jobs/7/logs"
    mutations.append((changed, "job/path mismatch"))
    for changed, label in mutations:
        rejected(lambda changed=changed: V5.decode_capture_row(changed, label), label)
    return len(mutations)


def test_runs_and_jobs() -> tuple[int, int]:
    valid = run("successor_ci", "success")
    V5.normalized_run(valid, "successor_ci", 101, V5.C4_COMMIT)
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
            lambda changed=changed: V5.normalized_run(
                changed, "successor_ci", 101, V5.C4_COMMIT
            ),
            label,
        )

    predecessor = job("predecessor_contract", "failure", 95540602684)
    successor = job("successor_contract", "success", 901)
    V5.normalized_jobs([predecessor], "predecessor_contract", 101, V5.C4_COMMIT)
    V5.normalized_jobs([successor], "successor_contract", 101, V5.C4_COMMIT)
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
        if item["name"] == "Recheck every bounded C4 failure surface"
    )["conclusion"] = "skipped"
    job_vectors.append(([changed], "successor_contract", "bounded step skipped"))
    changed = copy.deepcopy(predecessor)
    changed["steps"][0]["name"] = "different failed step"
    job_vectors.append(([changed], "predecessor_contract", "failure step renamed"))
    for values, role, label in job_vectors:
        rejected(
            lambda values=values, role=role: V5.normalized_jobs(
                values, role, 101, V5.C4_COMMIT
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
        V5.normalized_job_timestamps(valid, "success", "timestamp-positive")
        == ("2026-08-18T00:00:00Z", "2026-08-18T00:00:01Z"),
        "ordinary job timestamps were not preserved",
    )
    skipped = {"completed_at": None, "started_at": None}
    require(
        V5.normalized_job_timestamps(skipped, "skipped", "timestamp-skipped")
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
            lambda changed=changed, conclusion=conclusion: V5.normalized_job_timestamps(
                changed, conclusion, label
            ),
            label,
        )
    return len(mutations)


def test_v5_workflow_prerequisites() -> int:
    raw = (ROOT / V5.V5_WORKFLOW_RELATIVE).read_bytes()
    V5.validate_v5_workflow_prerequisites(raw)
    first, second = V5.V5_PDF_PREREQUISITE_BLOCKS
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
    ]
    for changed, label in mutations:
        require(changed != raw, f"workflow mutation did not reach its target: {label}")
        rejected(
            lambda changed=changed: V5.validate_v5_workflow_prerequisites(changed),
            label,
        )
    return len(mutations)


def test_policy() -> int:
    require(V5.C5_POLICY_ROWS, "C5 policy rows have not been frozen")
    policy = policy_fixture()
    V5.validate_policy_value(policy)
    mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(policy)
    changed["base"]["r4_status"] = "issued"
    mutations.append((changed, "R4 status"))
    changed = copy.deepcopy(policy)
    changed["base"]["reserved_absent_paths"] = list(reversed(V5.FORBIDDEN_R4_PATHS))
    mutations.append((changed, "reserved-path order"))
    changed = copy.deepcopy(policy)
    changed["c5"]["message"] = "Repair something else\n"
    mutations.append((changed, "C5 message"))
    changed = copy.deepcopy(policy)
    changed["c5"]["delta"] = changed["c5"]["delta"][:-1]
    mutations.append((changed, "C5 missing row"))
    changed = copy.deepcopy(policy)
    changed["r5"]["delta"][0]["status"] = "A"
    mutations.append((changed, "R5 current-source status"))
    changed = copy.deepcopy(policy)
    changed["nonimplications"] = changed["nonimplications"][:-1]
    mutations.append((changed, "policy nonclaim"))
    for changed, label in mutations:
        rejected(lambda changed=changed: V5.validate_policy_value(changed), label)
    return len(mutations)


def test_receipt_schema() -> int:
    raw = (ROOT / V5.RECEIPT_SCHEMA_RELATIVE).read_bytes()
    schema = V5._closed_schema(
        raw,
        "self-test composite-v5 receipt",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-receipt-v5.schema.json",
        [
            "capture_bindings",
            "contract_authorities",
            "nonimplications",
            "observations",
            "repository",
            "schema",
            "schema_revision",
            "subject",
            "verdict",
        ],
        V5.RECEIPT_SCHEMA_SHA256,
        V5.RECEIPT_SCHEMA_SIZE_BYTES,
    )
    receipt = receipt_fixture()
    V5.validate_schema_instance(receipt, schema, "positive receipt fixture")
    V5.parse_json(
        V5.canonical_json(receipt, pretty=True), "positive stored receipt fixture"
    )
    mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(receipt)
    changed["verdict"]["c4_hosted_qualification"] = "pass"
    mutations.append((changed, "C4 hosted-qualification verdict upgrade"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["c4_publication"] = "failed"
    mutations.append((changed, "C4 publication erasure"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["r4_receipt_issued"] = True
    mutations.append((changed, "R4 issued"))
    changed = copy.deepcopy(receipt)
    changed["verdict"]["scientific_validation"] = "pass"
    mutations.append((changed, "scientific overclaim"))
    changed = copy.deepcopy(receipt)
    changed["capture_bindings"][1] = copy.deepcopy(changed["capture_bindings"][0])
    mutations.append((changed, "duplicate capture binding"))
    changed = copy.deepcopy(receipt)
    changed["subject"]["c5_tree"] = "bad"
    mutations.append((changed, "tree identity"))
    changed = copy.deepcopy(receipt)
    del changed["observations"][0]["roles"][0]["failed_job_logs"][0]["job_name"]
    mutations.append((changed, "failed-job name"))
    changed = copy.deepcopy(receipt)
    del changed["observations"][0]["roles"][0]["failed_job_logs"][0]["observed_markers"]
    mutations.append((changed, "observed failure marker"))
    changed = copy.deepcopy(receipt)
    changed["observations"][0]["roles"][0]["job_ids"] *= 2
    mutations.append((changed, "duplicate job identifier"))
    changed = copy.deepcopy(receipt)
    changed["unexpected"] = True
    mutations.append((changed, "open root"))
    changed = copy.deepcopy(receipt)
    changed["nonimplications"][1] = changed["nonimplications"][0]
    mutations.append((changed, "duplicate nonclaim"))
    for changed, label in mutations:
        rejected(
            lambda changed=changed: V5.validate_schema_instance(changed, schema, label),
            label,
        )
    rejected(
        lambda: V5.parse_json(
            V5.canonical_json(receipt, pretty=False), "compact stored receipt fixture"
        ),
        "noncanonical compact stored receipt",
    )
    return len(mutations) + 1


def test_replay_and_delta() -> tuple[int, int]:
    r9_raw = b"immutable prior r9 bytes"
    replay = {
        "prior_replay_preservation_sha256": {V5.LEAN_R9_RELATIVE: V5.sha256(r9_raw)},
        "prior_replay_schema": {
            V5.LEAN_R9_RELATIVE: "pid-rs/lean-current-project-replay/v2"
        },
        "schema": "pid-rs/lean-current-project-replay/v2",
        "status": "passed",
    }
    V5.validate_replay_values(r9_raw, replay)
    replay_mutations: list[tuple[dict[str, Any], str]] = []
    changed = copy.deepcopy(replay)
    changed["status"] = "failed"
    replay_mutations.append((changed, "r10 status"))
    changed = copy.deepcopy(replay)
    changed["prior_replay_preservation_sha256"][V5.LEAN_R9_RELATIVE] = "0" * 64
    replay_mutations.append((changed, "r9 prior digest"))
    changed = copy.deepcopy(replay)
    changed["prior_replay_schema"][V5.LEAN_R9_RELATIVE] = "v3"
    replay_mutations.append((changed, "r9 prior schema"))
    for changed, label in replay_mutations:
        rejected(
            lambda changed=changed: V5.validate_replay_values(r9_raw, changed), label
        )

    expected = tuple(
        (path, status, mode) for path, status, mode, _role in V5.R5_POLICY_ROWS
    )
    V5.validate_exact_delta(expected, expected, "positive R5")
    delta_mutations = [
        expected[:-1],
        tuple(reversed(expected)),
        (*expected, expected[0]),
    ]
    for index, changed in enumerate(delta_mutations):
        rejected(
            lambda changed=changed: V5.validate_exact_delta(changed, expected, "R5"),
            f"R5 delta {index}",
        )
    return len(replay_mutations), len(delta_mutations)


def test_identifier_domains() -> int:
    phases = receipt_fixture()["observations"]
    V5.validate_identifier_domains(phases, "positive phases")
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
            lambda changed=changed: V5.validate_identifier_domains(changed, label),
            label,
        )
    return len(mutations)


def test_predecessor_failure_surface() -> int:
    known_ci = set(V5.PREDECESSOR_REQUIRED_FAILED_JOB_IDS["predecessor_ci"])
    V5.validate_predecessor_failed_set("predecessor_ci", known_ci)
    V5.validate_predecessor_failed_set("predecessor_ci", known_ci | {99999999999})
    known_contract = set(V5.PREDECESSOR_REQUIRED_FAILED_JOB_IDS["predecessor_contract"])
    V5.validate_predecessor_failed_set("predecessor_contract", known_contract)
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
        for job_id, (name, failed_steps) in V5.PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[
            "predecessor_ci"
        ].items()
    ]
    V5.validate_predecessor_failure_identities("predecessor_ci", jobs, known_ci)
    set_mutations: list[tuple[str, set[int]]] = [
        ("missing known CI failure", known_ci - {min(known_ci)}),
        ("extra dedicated failure", known_contract | {99999999998}),
    ]
    for label, failed in set_mutations:
        role = (
            "predecessor_ci"
            if label == "missing known CI failure"
            else "predecessor_contract"
        )
        rejected(
            lambda role=role, failed=failed: V5.validate_predecessor_failed_set(
                role, failed
            ),
            label,
        )
    identity_mutations: list[tuple[list[dict[str, Any]], str]] = []
    changed = copy.deepcopy(jobs)
    changed[0]["name"] = "different job"
    identity_mutations.append((changed, "required failure job renamed"))
    changed = copy.deepcopy(jobs)
    changed[0]["steps"][0]["name"] = "different failed step"
    identity_mutations.append((changed, "required failed step renamed"))
    for changed, label in identity_mutations:
        rejected(
            lambda changed=changed: V5.validate_predecessor_failure_identities(
                "predecessor_ci", changed, known_ci
            ),
            label,
        )
    release_marker = V5.PREDECESSOR_REQUIRED_LOG_MARKERS[95540603816][0]
    require(
        V5.observed_failure_markers(
            95540603816,
            f"provider prefix\n{release_marker}\nprovider suffix".encode("ascii"),
            "predecessor_ci",
        )
        == [release_marker],
        "required raw-log marker was not preserved",
    )
    rejected(
        lambda: V5.observed_failure_markers(
            95540603816, b"different provider output\n", "predecessor_ci"
        ),
        "required raw-log marker missing",
    )
    return len(set_mutations) + len(identity_mutations) + 1


def test_forbidden_r4_history() -> int:
    V5.validate_no_r4_tree_message({}, V5.C5_MESSAGE, "1" * 40)
    mutations: list[tuple[dict[str, Any], str, str]] = [
        (
            {V5.V4_CAPTURE_RELATIVE: object()},
            V5.C5_MESSAGE,
            "forbidden v4 capture path",
        ),
        (
            {V5.V4_RECEIPT_RELATIVE: object()},
            V5.C5_MESSAGE,
            "forbidden v4 receipt path",
        ),
        ({}, V5.FORBIDDEN_R4_MESSAGE, "forbidden R4 commit message"),
    ]
    for entries, message, label in mutations:
        rejected(
            lambda entries=entries, message=message: V5.validate_no_r4_tree_message(
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
        workflow_count = test_v5_workflow_prerequisites()
        policy_count = test_policy()
        receipt_count = test_receipt_schema()
        replay_count, delta_count = test_replay_and_delta()
        identifier_count = test_identifier_domains()
        failure_surface_count = test_predecessor_failure_surface()
        forbidden_history_count = test_forbidden_r4_history()
        result = {
            "capture_mutations_rejected": capture_count,
            "delta_mutations_rejected": delta_count,
            "forbidden_r4_history_mutations_rejected": forbidden_history_count,
            "job_mutations_rejected": job_count,
            "identifier_domain_mutations_rejected": identifier_count,
            "job_timestamp_mutations_rejected": timestamp_count,
            "policy_mutations_rejected": policy_count,
            "predecessor_failure_surface_mutations_rejected": failure_surface_count,
            "receipt_schema_mutations_rejected": receipt_count,
            "replay_mutations_rejected": replay_count,
            "result": "pass",
            "run_mutations_rejected": run_count,
            "schema": "pid-rs/ksg-rev4-m1a-composite-v5-self-test/v1",
            "v4_primitives_sha256": V5.V4_CHECKER_SHA256,
            "workflow_prerequisite_mutations_rejected": workflow_count,
        }
        sys.stdout.buffer.write(V5.canonical_json(result, pretty=True))
        return 0
    except (SelfTestError, V5.ContractError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
