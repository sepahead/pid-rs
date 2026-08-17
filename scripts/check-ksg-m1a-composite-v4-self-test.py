#!/usr/bin/env python3
"""Adversarial normal/-O tests for the composite-v4 contract checker."""

from __future__ import annotations

import hashlib
import base64
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import zipfile


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v4-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-composite-v4.py"
MAX_CHILD_OUTPUT = 1024 * 1024
MAX_CAPTURE_BODY_BYTES = 22 * 1024 * 1024
MAX_JSON_BYTES = 32 * 1024 * 1024
REPOSITORY = "sepahead/pid-rs"
BASE_COMMIT = "bc3aa80fb6025e709c2906a08bce25a4fac40578"
BASE_TREE = "7d87f87953a42edb91e40880d918471c7cbe4414"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v4.py"
CAPTURE_TOOL = ROOT / CAPTURE_TOOL_RELATIVE
FORBIDDEN_TLS_ENVIRONMENT = (
    "CURL_CA_BUNDLE",
    "OPENSSL_CONF",
    "PYTHONHTTPSVERIFY",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SSLKEYLOGFILE",
)
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v4.yml"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v4-path-policy-v1.json"
ROLE_ORDER = (
    "recovery_ci",
    "recovery_codeql",
    "migration_ci",
    "migration_codeql",
    "migration_contract",
)
RUN_IDS = {
    "recovery_ci": 31773937366,
    "recovery_codeql": 31773937102,
    "migration_ci": 41000000001,
    "migration_codeql": 41000000002,
    "migration_contract": 41000000003,
}
LANGUAGE_ORDER = ("actions", "javascript-typescript", "python", "rust")
RECOVERY_ANALYSIS_IDS = {
    "actions": 1617732991,
    "javascript-typescript": 1617732745,
    "python": 1617735963,
    "rust": 1617735749,
}
RECOVERY_ANALYSIS_COUNTS = {
    "actions": (0, 17),
    "javascript-typescript": (0, 87),
    "python": (44, 43),
    "rust": (113, 25),
}
CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Capture time, network completeness, and provider response order are not claimed.",
    "Code-scanning alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to a workflow run or to that run's historical execution window.",
    "A successful hosted run is not mathematical, estimator, or application validation.",
    "The capture makes no claim about any PID functional, estimator, objective, or downstream use.",
]
POSTCOMMIT_NONIMPLICATIONS = [
    "This post-commit identity artifact is not authentication, authenticity, attestation, provenance, or proof of repository origin.",
    "It does not establish line review, human review, independent review, institutional review, or review completion.",
    "It does not establish scientific validity, estimator validity, formal correctness, source-to-formal correspondence, implementation refinement, numerical correctness, or application validity.",
    "Commit, tree, blob, and SHA-256 identifiers bind exact bytes under named algorithms; they do not confer trust or authenticity.",
    "Generation is bounded execution evidence for one committed state, not a CI-pass, release, tag, or fact about any other commit.",
    "Repeated endpoint checks are not an atomic history against concurrent filesystem or repository mutation.",
    "Repository-ignored products and Git object-store internals are outside this committed-tree identity projection.",
    "Emission uses standard output and validation uses standard input; this artifact does not bind storage location, filesystem identity, durability, or upload custody.",
]
EXPECTED_CI_JOB_NAMES = (
    "All features / macos-latest",
    "All features / windows-latest",
    "Core all-features",
    "Core experimental-all",
    "Core experimental-continuous",
    "Core experimental-heuristics",
    "Core experimental-hierarchy",
    "Core experimental-hyperbolic",
    "Core experimental-pipelines",
    "Core no-default-features",
    "Core parallel",
    "Core research-mixed-dimension-pid3",
    "Coverage threshold",
    "Deterministic property and identity suites",
    "Exact-count SxPID2 reference / MSRV 1.89",
    "Exact-count directed-rounding SxPID2 reference",
    "Examples + exp0 + run-log replay",
    "Fixed fuzz corpus smoke",
    "Formal LaTeX / PDF inventory and cross-toolchain structure",
    "Formal proof cores, frozen Lean 4.33.0 replay, and historical packet custody",
    "KSG integer-harmonic arithmetic and phase isolation",
    "MSRV 1.89 / all-features",
    "MSRV 1.89 / default",
    "MSRV 1.89 / no-default-features",
    "Miri / pure safe-Rust boundaries",
    "Package + semver + unused dependencies",
    "Python 3.11 / NumPy 1.26.4 / macos-latest",
    "Python 3.11 / NumPy 1.26.4 / ubuntu-latest",
    "Python 3.11 / NumPy 1.26.4 / windows-latest",
    "Python 3.12 / NumPy 1.26.4 / ubuntu-latest",
    "Python 3.13 / NumPy 2.5.1 / ubuntu-latest",
    "Python 3.14 / NumPy 2.5.1 / macos-latest",
    "Python 3.14 / NumPy 2.5.1 / ubuntu-latest",
    "Python 3.14 / NumPy 2.5.1 / windows-latest",
    "Python experimental namespace smoke",
    "Release scope and scientific evidence coherence",
    "Release-mode numerical fixtures",
    "Rustdoc + docs.rs configuration",
    "Rustfmt + Clippy",
    "Secret scan (full history)",
    "Supply chain without advisory exceptions",
    "Workspace CycloneDX SBOM",
    "Workspace default / macos-latest",
    "Workspace default / ubuntu-latest",
    "Workspace default / windows-latest",
)


class SelfTestError(RuntimeError):
    """A mutation was accepted or a positive control failed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def compact(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def git_bytes(*arguments: str) -> bytes:
    command = (
        "/usr/bin/git",
        "--no-optional-locks",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.excludesFile=/dev/null",
        "-C",
        os.fspath(ROOT),
        *arguments,
    )
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
        env={
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.defpath,
            "TZ": "UTC",
        },
    )
    require(
        result.returncode == 0 and result.stderr == b"",
        "bounded Git fixture query failed",
    )
    require(len(result.stdout) <= 32 * 1024 * 1024, "Git fixture output exceeded bound")
    return result.stdout


def git_text(*arguments: str) -> str:
    raw = git_bytes(*arguments)
    require(raw.endswith(b"\n") and b"\n" not in raw[:-1], "Git fixture text changed")
    return raw[:-1].decode("ascii")


def git_blob(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_zip(path: str, body: bytes) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        info.external_attr = (0o100644 & 0xFFFF) << 16
        archive.writestr(info, body)
    return stream.getvalue()


def capture_row(
    logical: str,
    repetition: int,
    page: int,
    path: str,
    body: bytes,
    *,
    kind: str = "json",
) -> dict[str, Any]:
    return {
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": sha256(body),
        "body_size_bytes": len(body),
        "logical_request": logical,
        "media_type": "application/json" if kind == "json" else "application/zip",
        "page": page,
        "path": path,
        "redirect": None
        if kind == "json"
        else {
            "status_code": 302,
            "target_host": "fixture.blob.core.windows.net",
            "target_url_sha256": "0" * 64,
        },
        "repetition": repetition,
        "response_kind": kind,
        "status_code": 200,
    }


def add_single(
    captures: list[dict[str, Any]],
    logical: str,
    repetition: int,
    path: str,
    value: Any,
) -> None:
    captures.append(capture_row(logical, repetition, 0, path, compact(value)))


def add_pages(
    captures: list[dict[str, Any]],
    logical: str,
    repetition: int,
    path_prefix: str,
    values: list[Any],
    field: str | None,
) -> None:
    pages = [values[index : index + 100] for index in range(0, len(values), 100)]
    pages.append([])
    for page, items in enumerate(pages, start=1):
        separator = "&" if "?" in path_prefix else "?"
        path = f"{path_prefix}{separator}per_page=100&page={page}"
        value: Any = (
            items if field is None else {field: items, "total_count": len(values)}
        )
        captures.append(capture_row(logical, repetition, page, path, compact(value)))


def replace_row_body(row: dict[str, Any], raw: bytes) -> None:
    row["body_base64"] = base64.b64encode(raw).decode("ascii")
    row["body_sha256"] = sha256(raw)
    row["body_size_bytes"] = len(raw)


def mutate_json_rows(
    capture: dict[str, Any],
    logical: str,
    transform: Any,
    repetitions: tuple[int, ...] = (1, 2),
) -> None:
    matched = 0
    for row in capture["captures"]:
        if row["logical_request"] == logical and row["repetition"] in repetitions:
            value = json.loads(base64.b64decode(row["body_base64"]))
            transform(value)
            replace_row_body(row, compact(value))
            matched += 1
    require(matched > 0, f"fixture mutation did not find {logical}")


def manifest_artifact(commit: str, tree: str) -> bytes:
    manifest_raw = git_blob(commit, CURRENT_SOURCE_RELATIVE)
    manifest = json.loads(manifest_raw)
    manifest_oid = git_text("rev-parse", f"{commit}:{CURRENT_SOURCE_RELATIVE}")
    value = {
        "binding": {
            "commit_oid": commit,
            "git_object_format": "sha1",
            "manifest": {
                "blob_oid": manifest_oid,
                "path": CURRENT_SOURCE_RELATIVE,
                "schema": "pid-rs/current-source-state",
                "schema_revision": 1,
                "sha256": sha256(manifest_raw),
                "size_bytes": len(manifest_raw),
                "source_projection_entries_sha256": manifest["source_projection"][
                    "entries_sha256"
                ],
                "source_projection_entry_count": manifest["source_projection"][
                    "entry_count"
                ],
            },
            "tree_oid": tree,
        },
        "checks": {
            "current_manifest_checker_passed": True,
            "head_tree_matches_index": True,
            "manifest_is_tracked_head_blob": True,
            "post_commit_checker_is_tracked_head_blob": True,
            "post_commit_schema_is_tracked_head_blob": True,
            "repeated_endpoint_observations_match": True,
            "repository_visible_untracked_paths": [],
            "self_excluding_projection_matches_head_tree": True,
            "tracked_worktree_matches_head": True,
        },
        "determinism": {
            "artifact_transport": "canonical_json_stdout_or_stdin_only",
            "commit_cycle": "none; the committed manifest excludes itself and this artifact is generated only after commit",
            "generated_at": "omitted_for_determinism",
            "storage_custody": "caller_owned_not_bound_by_this_artifact",
        },
        "evidence_class": "post_commit_identity_evidence_only",
        "generated_by": "scripts/check-post-commit-source-state-v2.py",
        "nonimplications": POSTCOMMIT_NONIMPLICATIONS,
        "repository": REPOSITORY,
        "schema": "pid-rs/post-commit-source-state",
        "schema_revision": 2,
    }
    return canonical(value)


def job_row(
    job_id: int,
    name: str,
    run_id: int,
    head: str,
    step_names: tuple[str, ...] = ("Fixture success",),
) -> dict[str, Any]:
    return {
        "completed_at": "2026-08-15T00:00:01Z",
        "conclusion": "success",
        "head_sha": head,
        "id": job_id,
        "name": name,
        "run_attempt": 1,
        "run_id": run_id,
        "started_at": "2026-08-15T00:00:00Z",
        "status": "completed",
        "steps": [
            {
                "conclusion": "success",
                "name": step,
                "number": index,
                "status": "completed",
            }
            for index, step in enumerate(step_names, start=1)
        ],
    }


def run_row(role: str, run_id: int, head: str, repository_id: int) -> dict[str, Any]:
    kind = (
        "ci"
        if role.endswith("ci")
        else "codeql"
        if role.endswith("codeql")
        else "contract"
    )
    if kind == "ci":
        name, path, event, workflow_id = (
            "CI",
            ".github/workflows/ci.yml",
            "push",
            297369773,
        )
    elif kind == "codeql":
        name, path, event, workflow_id = (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
            310582096,
        )
    else:
        name, path, event, workflow_id = (
            "KSG M1a composite v4",
            WORKFLOW_RELATIVE,
            "push",
            41000000400,
        )
    return {
        "conclusion": "success",
        "event": event,
        "head_branch": "main",
        "head_repository": {"full_name": REPOSITORY, "id": repository_id},
        "head_sha": head,
        "id": run_id,
        "name": name,
        "path": path,
        "repository": {"full_name": REPOSITORY, "id": repository_id},
        "run_attempt": 1,
        "status": "completed",
        "workflow_id": workflow_id,
    }


def artifact_row(
    artifact_id: int,
    name: str,
    archive: bytes,
    run_id: int,
    head: str,
    repository_id: int,
) -> dict[str, Any]:
    return {
        "digest": f"sha256:{sha256(archive)}",
        "expired": False,
        "id": artifact_id,
        "name": name,
        "size_in_bytes": len(archive),
        "workflow_run": {
            "head_branch": "main",
            "head_repository_id": repository_id,
            "head_sha": head,
            "id": run_id,
            "repository_id": repository_id,
        },
    }


def build_capture(c4: str, c4_tree: str) -> dict[str, Any]:
    captures: list[dict[str, Any]] = []
    repository_id = 991337
    role_index = {role: index for index, role in enumerate(ROLE_ORDER, start=1)}
    for repetition in (1, 2):
        for role in ROLE_ORDER:
            run_id = RUN_IDS[role]
            head = BASE_COMMIT if role.startswith("recovery_") else c4
            tree = BASE_TREE if role.startswith("recovery_") else c4_tree
            add_single(
                captures,
                f"{role}_run",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}",
                run_row(role, run_id, head, repository_id),
            )
            if role.endswith("ci"):
                job_names = EXPECTED_CI_JOB_NAMES
                step_names = ("Fixture success",)
            elif role.endswith("codeql"):
                job_names = tuple(
                    f"Analyze ({language})" for language in LANGUAGE_ORDER
                )
                step_names = ("Fixture success",)
            else:
                job_names = ("Validate the composite-v4 contract",)
                step_names = (
                    "Validate static contract in normal and optimized modes",
                    "Reject the adversarial contract and capture vectors",
                    "Upload the exact static result",
                )
            jobs = [
                job_row(
                    role_index[role] * 100000 + index,
                    name,
                    run_id,
                    head,
                    step_names,
                )
                for index, name in enumerate(job_names, start=1)
            ]
            add_pages(
                captures,
                f"{role}_jobs",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs",
                jobs,
                "jobs",
            )

            archives: list[tuple[int, str, bytes]] = []
            artifact_base = role_index[role] * 1000000
            if role.endswith("ci"):
                archives = [
                    (
                        artifact_base + 1,
                        "coverage-lcov",
                        make_zip("lcov.info", b"TN:\n"),
                    ),
                    (
                        artifact_base + 2,
                        f"post-commit-source-state-v2-{head}",
                        make_zip(
                            "pid-rs-post-commit-source-state-v2.json",
                            manifest_artifact(head, tree),
                        ),
                    ),
                    (
                        artifact_base + 3,
                        "workspace-sbom",
                        make_zip("sbom.json", b"{}\n"),
                    ),
                ]
            elif role == "migration_contract":
                static = {
                    "c4_commit": c4,
                    "head": c4,
                    "r4_commit": None,
                    "result": "pass",
                    "schema": "pid-rs/ksg-rev4-m1a-composite-v4-static-validation/v1",
                    "tree": c4_tree,
                }
                archives = [
                    (
                        artifact_base + 1,
                        f"ksg-m1a-composite-v4-static-{c4}",
                        make_zip("ksg-m1a-composite-v4-static.json", compact(static)),
                    )
                ]
            artifact_values = [
                artifact_row(
                    artifact_id,
                    name,
                    archive,
                    run_id,
                    head,
                    repository_id,
                )
                for artifact_id, name, archive in archives
            ]
            add_pages(
                captures,
                f"{role}_artifacts",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts",
                artifact_values,
                "artifacts",
            )
            for artifact_id, _name, archive in archives:
                captures.append(
                    capture_row(
                        f"{role}_artifact_{artifact_id}",
                        repetition,
                        0,
                        f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip",
                        archive,
                        kind="zip",
                    )
                )

            if not role.endswith("codeql"):
                continue
            analyses = []
            for language_index, language in enumerate(LANGUAGE_ORDER, start=1):
                if role == "recovery_codeql":
                    analysis_id = RECOVERY_ANALYSIS_IDS[language]
                    results_count, rules_count = RECOVERY_ANALYSIS_COUNTS[language]
                else:
                    analysis_id = 8100000000 + language_index
                    results_count, rules_count = language_index, 20 + language_index
                analysis = {
                    "category": f"/language:{language}",
                    "commit_sha": head,
                    "error": None,
                    "id": analysis_id,
                    "ref": "refs/heads/main",
                    "results_count": results_count,
                    "rules_count": rules_count,
                    "warning": None,
                }
                analyses.append(analysis)
                if role == "recovery_codeql":
                    add_single(
                        captures,
                        f"{role}_analysis_{analysis_id}",
                        repetition,
                        f"/repos/{REPOSITORY}/code-scanning/analyses/{analysis_id}",
                        analysis,
                    )
            if role == "migration_codeql":
                add_pages(
                    captures,
                    f"{role}_analyses",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
                    analyses,
                    None,
                )
            alert_numbers = {
                "dismissed": range(1, 47),
                "fixed": range(158, 192),
                "open": range(47, 158),
            }
            for state, numbers in alert_numbers.items():
                add_pages(
                    captures,
                    f"{role}_alerts_{state}",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}",
                    [{"number": number, "state": state} for number in numbers],
                    None,
                )
    captures.sort(
        key=lambda row: (
            row["logical_request"],
            row["repetition"],
            row["page"],
            row["path"],
        )
    )
    tool = git_blob(c4, CAPTURE_TOOL_RELATIVE)
    return {
        "capture_tool": {
            "path": CAPTURE_TOOL_RELATIVE,
            "sha256": sha256(tool),
            "size_bytes": len(tool),
        },
        "captures": captures,
        "nonimplications": CAPTURE_NONIMPLICATIONS,
        "repository": REPOSITORY,
        "retry_events": [],
        "runs": RUN_IDS,
        "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v4",
        "schema_revision": 4,
        "subject": {
            "contract_commit": c4,
            "contract_tree": c4_tree,
            "recovery_commit": BASE_COMMIT,
            "recovery_tree": BASE_TREE,
        },
    }


def artifact_id_for(capture: dict[str, Any], role: str, name_prefix: str) -> int:
    found: set[int] = set()
    for row in capture["captures"]:
        if row["logical_request"] != f"{role}_artifacts":
            continue
        value = json.loads(base64.b64decode(row["body_base64"]))
        for artifact in value["artifacts"]:
            if artifact["name"].startswith(name_prefix):
                found.add(artifact["id"])
    require(len(found) == 1, f"fixture artifact is not unique: {role}/{name_prefix}")
    return found.pop()


def replace_artifact(
    capture: dict[str, Any], role: str, artifact_id: int, archive: bytes
) -> None:
    logical = f"{role}_artifact_{artifact_id}"
    for row in capture["captures"]:
        if row["logical_request"] == logical:
            replace_row_body(row, archive)

    def update(value: dict[str, Any]) -> None:
        for artifact in value["artifacts"]:
            if artifact["id"] == artifact_id:
                artifact["digest"] = f"sha256:{sha256(archive)}"
                artifact["size_in_bytes"] = len(archive)

    mutate_json_rows(capture, f"{role}_artifacts", update)


def capture_negatives(
    positive: dict[str, Any], c4: str, c4_tree: str
) -> list[dict[str, Any]]:
    negatives: list[dict[str, Any]] = []

    mismatch = copy.deepcopy(positive)

    def rename_valid_ci_step(value: dict[str, Any]) -> None:
        if value["jobs"]:
            value["jobs"][0]["steps"][0]["name"] = "Alternate valid CI step"

    mutate_json_rows(
        mismatch,
        "migration_ci_jobs",
        rename_valid_ci_step,
        (2,),
    )
    negatives.append(mismatch)

    missing_page = copy.deepcopy(positive)
    missing_page["captures"] = [
        row
        for row in missing_page["captures"]
        if not (
            row["logical_request"] == "migration_ci_jobs"
            and row["repetition"] == 2
            and row["page"] == 2
        )
    ]
    negatives.append(missing_page)

    duplicate_page = copy.deepcopy(positive)
    duplicate = copy.deepcopy(duplicate_page["captures"][0])
    replace_row_body(duplicate, base64.b64decode(duplicate["body_base64"]) + b" ")
    duplicate_page["captures"].append(duplicate)
    duplicate_page["captures"].sort(
        key=lambda row: (
            row["logical_request"],
            row["repetition"],
            row["page"],
            row["path"],
        )
    )
    negatives.append(duplicate_page)

    prefix = f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain"
    too_many_rows = copy.deepcopy(positive)
    exact_head_analyses: list[dict[str, Any]] = []
    for row in positive["captures"]:
        if (
            row["logical_request"] == "migration_codeql_analyses"
            and row["repetition"] == 1
        ):
            values = json.loads(base64.b64decode(row["body_base64"]))
            exact_head_analyses.extend(
                value
                for value in values
                if value.get("commit_sha") == c4
                and value.get("ref") == "refs/heads/main"
            )
    require(len(exact_head_analyses) == 4, "fixture exact-head analyses changed")
    overflow_analyses = exact_head_analyses + [
        {
            "category": "/language:actions",
            "commit_sha": "0" * 40,
            "error": None,
            "id": 9000000000 + index,
            "ref": "refs/heads/main",
            "results_count": 0,
            "rules_count": 1,
            "warning": None,
        }
        for index in range(4096)
    ]
    too_many_rows["captures"] = [
        row
        for row in too_many_rows["captures"]
        if row["logical_request"] != "migration_codeql_analyses"
    ]
    for repetition in (1, 2):
        add_pages(
            too_many_rows["captures"],
            "migration_codeql_analyses",
            repetition,
            prefix,
            overflow_analyses,
            None,
        )
    too_many_rows["captures"].sort(
        key=lambda row: (
            row["logical_request"],
            row["repetition"],
            row["page"],
            row["path"],
        )
    )
    negatives.append(too_many_rows)

    retry = copy.deepcopy(positive)
    retry["retry_events"] = [
        {
            "attempt": 1,
            "category": "transport",
            "logical_request": "migration_ci_run",
            "page": 0,
            "path": f"/repos/{REPOSITORY}/actions/runs/999",
            "repetition": 1,
            "response_sha256": "0" * 64,
            "response_size_bytes": 1,
        }
    ]
    negatives.append(retry)

    repository = copy.deepcopy(positive)
    mutate_json_rows(
        repository,
        "migration_contract_run",
        lambda value: (
            value["repository"].__setitem__("id", 991338),
            value["head_repository"].__setitem__("id", 991338),
        ),
    )

    def mutate_artifact_repository(value: dict[str, Any]) -> None:
        for artifact in value["artifacts"]:
            artifact["workflow_run"]["repository_id"] = 991338
            artifact["workflow_run"]["head_repository_id"] = 991338

    mutate_json_rows(
        repository, "migration_contract_artifacts", mutate_artifact_repository
    )
    negatives.append(repository)

    attempt = copy.deepcopy(positive)
    mutate_json_rows(
        attempt,
        "migration_ci_run",
        lambda value: value.__setitem__("run_attempt", 2),
    )
    negatives.append(attempt)

    roster = copy.deepcopy(positive)

    def rename_job(value: dict[str, Any]) -> None:
        if value["jobs"]:
            value["jobs"][0]["name"] = "Unreviewed replacement job"

    mutate_json_rows(roster, "migration_ci_jobs", rename_job)
    negatives.append(roster)

    duplicate_artifact = copy.deepcopy(positive)

    def duplicate_first_artifact(value: dict[str, Any]) -> None:
        if value["artifacts"]:
            value["artifacts"].append(copy.deepcopy(value["artifacts"][0]))
        value["total_count"] += 1

    mutate_json_rows(
        duplicate_artifact, "migration_ci_artifacts", duplicate_first_artifact
    )
    negatives.append(duplicate_artifact)

    digest = copy.deepcopy(positive)

    def corrupt_digest(value: dict[str, Any]) -> None:
        if value["artifacts"]:
            value["artifacts"][0]["digest"] = "sha256:" + "f" * 64

    mutate_json_rows(digest, "migration_ci_artifacts", corrupt_digest)
    negatives.append(digest)

    detail = copy.deepcopy(positive)
    detail_id = RECOVERY_ANALYSIS_IDS["actions"]
    mutate_json_rows(
        detail,
        f"recovery_codeql_analysis_{detail_id}",
        lambda value: value.__setitem__("id", detail_id + 1),
    )
    negatives.append(detail)

    analysis_join = copy.deepcopy(positive)

    def duplicate_category(value: list[dict[str, Any]]) -> None:
        if len(value) > 1:
            value[1]["category"] = "/language:actions"

    mutate_json_rows(analysis_join, "migration_codeql_analyses", duplicate_category)
    negatives.append(analysis_join)

    alert_overlap = copy.deepcopy(positive)
    for row in alert_overlap["captures"]:
        if (
            row["logical_request"] == "migration_codeql_alerts_open"
            and row["page"] == 2
        ):
            value = json.loads(base64.b64decode(row["body_base64"]))
            value.append({"number": 1, "state": "open"})
            replace_row_body(row, compact(value))
    negatives.append(alert_overlap)

    duplicate_analysis_id = copy.deepcopy(positive)

    def reuse_analysis_id(value: list[dict[str, Any]]) -> None:
        if len(value) > 1:
            value[1]["id"] = value[0]["id"]

    mutate_json_rows(
        duplicate_analysis_id, "migration_codeql_analyses", reuse_analysis_id
    )
    negatives.append(duplicate_analysis_id)

    cross_role_analysis_id = copy.deepcopy(positive)
    recovery_analysis_id = RECOVERY_ANALYSIS_IDS["actions"]

    def reuse_cross_role_analysis_id(value: list[dict[str, Any]]) -> None:
        for analysis in value:
            if analysis.get("commit_sha") == c4:
                analysis["id"] = recovery_analysis_id
                return

    mutate_json_rows(
        cross_role_analysis_id,
        "migration_codeql_analyses",
        reuse_cross_role_analysis_id,
    )
    negatives.append(cross_role_analysis_id)

    cross_role_job_id = copy.deepcopy(positive)
    recovery_ci_job_id: int | None = None
    for row in positive["captures"]:
        if row["logical_request"] == "recovery_ci_jobs" and row["repetition"] == 1:
            value = json.loads(base64.b64decode(row["body_base64"]))
            if value["jobs"]:
                recovery_ci_job_id = value["jobs"][0]["id"]
                break
    require(recovery_ci_job_id is not None, "fixture recovery CI job is absent")

    def reuse_cross_role_job_id(value: dict[str, Any]) -> None:
        if value["jobs"]:
            value["jobs"][0]["id"] = recovery_ci_job_id

    mutate_json_rows(cross_role_job_id, "migration_ci_jobs", reuse_cross_role_job_id)
    negatives.append(cross_role_job_id)

    cross_role_artifact_id = copy.deepcopy(positive)
    recovery_ci_artifact_id = artifact_id_for(
        positive, "recovery_ci", "post-commit-source-state-v2-"
    )
    migration_contract_artifact_id = artifact_id_for(
        positive, "migration_contract", "ksg-m1a-composite-v4-static-"
    )

    def reuse_cross_role_artifact_id(value: dict[str, Any]) -> None:
        require(len(value["artifacts"]) <= 1, "fixture contract artifact changed")
        if value["artifacts"]:
            value["artifacts"][0]["id"] = recovery_ci_artifact_id

    mutate_json_rows(
        cross_role_artifact_id,
        "migration_contract_artifacts",
        reuse_cross_role_artifact_id,
    )
    for row in cross_role_artifact_id["captures"]:
        if row["logical_request"] == (
            f"migration_contract_artifact_{migration_contract_artifact_id}"
        ):
            row["logical_request"] = (
                f"migration_contract_artifact_{recovery_ci_artifact_id}"
            )
            row["path"] = (
                f"/repos/{REPOSITORY}/actions/artifacts/"
                f"{recovery_ci_artifact_id}/zip"
            )
    cross_role_artifact_id["captures"].sort(
        key=lambda row: (
            row["logical_request"],
            row["repetition"],
            row["page"],
            row["path"],
        )
    )
    negatives.append(cross_role_artifact_id)

    postcommit = copy.deepcopy(positive)
    post_id = artifact_id_for(
        postcommit, "migration_ci", "post-commit-source-state-v2-"
    )
    invalid_postcommit = json.loads(manifest_artifact(c4, c4_tree))
    invalid_postcommit["binding"]["tree_oid"] = "0" * 40
    replace_artifact(
        postcommit,
        "migration_ci",
        post_id,
        make_zip(
            "pid-rs-post-commit-source-state-v2.json", canonical(invalid_postcommit)
        ),
    )
    negatives.append(postcommit)

    contract_steps = copy.deepcopy(positive)

    def remove_self_test_step(value: dict[str, Any]) -> None:
        if value["jobs"]:
            value["jobs"][0]["steps"] = [
                step
                for step in value["jobs"][0]["steps"]
                if step["name"] != "Reject the adversarial contract and capture vectors"
            ]

    mutate_json_rows(contract_steps, "migration_contract_jobs", remove_self_test_step)
    negatives.append(contract_steps)

    wrong_tool = copy.deepcopy(positive)
    wrong_tool["capture_tool"]["sha256"] = "f" * 64
    negatives.append(wrong_tool)

    wrong_subject = copy.deepcopy(positive)
    wrong_subject["subject"]["contract_tree"] = "0" * 40
    negatives.append(wrong_subject)

    extra = copy.deepcopy(positive)
    extra["self_authentication"] = True
    negatives.append(extra)

    pid_boundary = copy.deepcopy(positive)
    pid_boundary["nonimplications"][-1] = (
        "This workflow validates every PID functional and downstream objective."
    )
    negatives.append(pid_boundary)

    duplicate_run = copy.deepcopy(positive)
    duplicate_run["runs"]["migration_ci"] = duplicate_run["runs"]["migration_codeql"]
    negatives.append(duplicate_run)

    return negatives


def run_checker(
    optimized: bool, mode: str, stdin: bytes = b"", expected_status: int = 0
) -> bytes:
    command = [os.fspath(Path(sys.executable))]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", os.fspath(CHECKER), mode))
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TZ": "UTC",
    }
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SelfTestError(f"checker child failed to run: {error}") from None
    require(
        len(result.stdout) <= MAX_CHILD_OUTPUT
        and len(result.stderr) <= MAX_CHILD_OUTPUT,
        "checker child output exceeded the bound",
    )
    require(
        result.returncode == expected_status,
        f"checker child returned {result.returncode}: "
        + result.stderr.decode("utf-8", errors="replace"),
    )
    if expected_status == 0:
        require(result.stderr == b"", "checker self-test child emitted stderr")
    return result.stdout


def run_capture_tool(
    optimized: bool,
    *,
    expected_status: int,
    extra_environment: dict[str, str] | None = None,
) -> bytes:
    command = [os.fspath(Path(sys.executable))]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", os.fspath(CAPTURE_TOOL), "--self-test"))
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TZ": "UTC",
    }
    if extra_environment:
        environment.update(extra_environment)
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    require(
        result.returncode == expected_status, "capture-tool self-test status changed"
    )
    require(
        len(result.stdout) <= MAX_CHILD_OUTPUT
        and len(result.stderr) <= MAX_CHILD_OUTPUT,
        "capture-tool self-test output exceeded the bound",
    )
    if expected_status == 0:
        require(result.stderr == b"", "capture-tool self-test emitted stderr")
    else:
        require(result.stdout == b"", "rejected capture-tool invocation emitted stdout")
    return result.stdout


def expect_vector(raw: bytes, expected: str) -> None:
    outputs = []
    for optimized in (False, True):
        output = run_checker(optimized, "--self-test-vector", raw)
        parsed = json.loads(output)
        require(parsed.get("result") == expected, "JSON vector disposition changed")
        outputs.append(output)
    require(outputs[0] == outputs[1], "JSON vector normal/-O outputs differ")


def expect_schema(instance: Any, schema: Any, expected: str) -> None:
    raw = canonical({"instance": instance, "schema": schema})
    outputs = []
    for optimized in (False, True):
        output = run_checker(optimized, "--self-test-schema-vector", raw)
        parsed = json.loads(output)
        require(parsed == {"result": expected}, "schema vector disposition changed")
        outputs.append(output)
    require(outputs[0] == outputs[1], "schema vector normal/-O outputs differ")


def expect_schema_definition(
    schema: Any,
    expected_id: str,
    expected_required: list[str],
    expected: str,
    *,
    authority_schema: Any | None = None,
) -> None:
    authority_raw = canonical(schema if authority_schema is None else authority_schema)
    raw = canonical(
        {
            "expected_id": expected_id,
            "expected_required": expected_required,
            "expected_sha256": sha256(authority_raw),
            "expected_size_bytes": len(authority_raw),
            "schema": schema,
        }
    )
    outputs = []
    for optimized in (False, True):
        output = run_checker(optimized, "--self-test-schema-definition-vector", raw)
        require(
            json.loads(output) == {"result": expected},
            "schema-definition vector disposition changed",
        )
        outputs.append(output)
    require(
        outputs[0] == outputs[1],
        "schema-definition vector normal/-O outputs differ",
    )


def expect_policy(policy: Any, expected: str) -> None:
    outputs = []
    for optimized in (False, True):
        output = run_checker(optimized, "--self-test-policy-vector", canonical(policy))
        require(
            json.loads(output) == {"result": expected},
            "policy vector disposition changed",
        )
        outputs.append(output)
    require(outputs[0] == outputs[1], "policy vector normal/-O outputs differ")


def main() -> int:
    try:
        positive = {"alpha": [1, True, None, "fixed"]}
        expected_digest = (
            "f34df4d2c7763241ff8cefb2b91ac7036f0adb01453ca21769ac095193f7ffdb"
        )
        expected_current_source_digest = (
            "11c4727ee4e1896bd01cef7127b313c3d2642777b53defd66767fd244908675c"
        )
        require(
            hashlib.sha256(compact(positive)).hexdigest() == expected_digest
            and hashlib.sha256(compact(positive)[:-1]).hexdigest()
            == expected_current_source_digest
            and expected_digest != expected_current_source_digest,
            "self-test compact-framing anchors changed",
        )
        outputs = []
        for optimized in (False, True):
            output = run_checker(optimized, "--self-test-vector", canonical(positive))
            require(
                json.loads(output)
                == {
                    "current_source_compact_sha256": expected_current_source_digest,
                    "result": "pass",
                    "value_sha256": expected_digest,
                },
                "positive JSON vector changed",
            )
            outputs.append(output)
        require(outputs[0] == outputs[1], "positive JSON normal/-O outputs differ")

        invalid_json = (
            b'{"a":1,"a":2}\n',
            b'{\n  "a": 1.0\n}\n',
            b'{\n  "a": NaN\n}\n',
            (b'{\n  "a": ' + b"1" * 33 + b"\n}\n"),
            b"[" * 97 + b"0" + b"]" * 97 + b"\n",
            compact(positive),
            b"\xff\n",
            b"",
        )
        for raw in invalid_json:
            expect_vector(raw, "fail")

        schema = {
            "additionalProperties": False,
            "properties": {
                "name": {
                    "pattern": "^[a-z]+(?![\\s\\S])",
                    "type": "string",
                },
                "values": {
                    "items": {"minimum": 1, "type": "integer"},
                    "maxItems": 2,
                    "minItems": 1,
                    "type": "array",
                    "uniqueItems": True,
                },
            },
            "required": ["name", "values"],
            "type": "object",
        }
        expect_schema({"name": "fixed", "values": [1, 2]}, schema, "pass")
        schema_mutations = (
            {"name": "fixed", "values": [True]},
            {"name": "fixed", "values": [1, 1]},
            {"name": "fixed", "values": [1, 2, 3]},
            {"name": "fixed\n", "values": [1]},
            {"name": "fixed", "values": []},
            {"name": "fixed", "values": [0]},
            {"name": "fixed", "values": [1], "self_claim": True},
            {"values": [1]},
        )
        for instance in schema_mutations:
            expect_schema(instance, schema, "fail")
        expect_schema({}, {"type": "object", "unsupportedKeyword": True}, "fail")
        expect_schema(
            {},
            {"$defs": {"loop": {"$ref": "#/$defs/loop"}}, "$ref": "#/$defs/loop"},
            "fail",
        )
        schema_definition = {
            "$id": "https://example.invalid/closed.schema.json",
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "additionalProperties": False,
            "properties": {"value": {"type": "integer"}},
            "required": ["value"],
            "type": "object",
        }
        expect_schema_definition(
            schema_definition,
            "https://example.invalid/closed.schema.json",
            ["value"],
            "pass",
        )
        for mutation in (
            {**schema_definition, "$id": "https://example.invalid/other.json"},
            {
                **schema_definition,
                "$schema": "https://json-schema.org/draft/2019-09/schema",
            },
            {**schema_definition, "additionalProperties": True},
            {**schema_definition, "required": []},
            {
                **schema_definition,
                "properties": {
                    **schema_definition["properties"],
                    "optional": {"type": "string"},
                },
            },
        ):
            expect_schema_definition(
                mutation,
                "https://example.invalid/closed.schema.json",
                ["value"],
                "fail",
                authority_schema=schema_definition,
            )
        widened_schema_definition = copy.deepcopy(schema_definition)
        widened_schema_definition["properties"]["value"]["type"] = [
            "integer",
            "string",
        ]
        expect_schema_definition(
            widened_schema_definition,
            "https://example.invalid/closed.schema.json",
            ["value"],
            "fail",
            authority_schema=schema_definition,
        )
        nested_schema_definition = {
            **schema_definition,
            "properties": {
                "value": {
                    "additionalProperties": False,
                    "properties": {"leaf": {"type": "integer"}},
                    "required": ["leaf"],
                    "type": "object",
                }
            },
        }
        expect_schema_definition(
            nested_schema_definition,
            "https://example.invalid/closed.schema.json",
            ["value"],
            "pass",
        )
        for nested_mutation in (
            {
                **nested_schema_definition["properties"]["value"],
                "additionalProperties": True,
            },
            {
                **nested_schema_definition["properties"]["value"],
                "properties": {
                    "leaf": {"type": "integer"},
                    "optional": {"type": "string"},
                },
            },
        ):
            mutation = copy.deepcopy(nested_schema_definition)
            mutation["properties"]["value"] = nested_mutation
            expect_schema_definition(
                mutation,
                "https://example.invalid/closed.schema.json",
                ["value"],
                "fail",
                authority_schema=nested_schema_definition,
            )

        policy = json.loads((ROOT / POLICY_RELATIVE).read_bytes())
        expect_policy(policy, "pass")
        policy_mutations = []
        for field, replacement in (
            ("path", "crates/pid-core/src/ksg.rs"),
            ("mode", "100755"),
            ("role", "scientific_change"),
            ("status", "D"),
        ):
            mutation = copy.deepcopy(policy)
            mutation["c4"]["delta"][0][field] = replacement
            policy_mutations.append(mutation)
        mutation = copy.deepcopy(policy)
        mutation["nonimplications"][0] = "Scientific changes are permitted."
        policy_mutations.append(mutation)
        mutation = copy.deepcopy(policy)
        mutation["c4"]["message"] = "Migrate and change scientific behavior\n"
        policy_mutations.append(mutation)
        mutation = copy.deepcopy(policy)
        mutation["r4"]["delta"].reverse()
        policy_mutations.append(mutation)
        for mutation in policy_mutations:
            expect_policy(mutation, "fail")

        capture_tool_outputs = [
            run_capture_tool(optimized, expected_status=0)
            for optimized in (False, True)
        ]
        require(
            capture_tool_outputs[0] == capture_tool_outputs[1]
            and json.loads(capture_tool_outputs[0]).get("result") == "pass",
            "capture-tool offline normal/-O controls changed",
        )
        for variable in FORBIDDEN_TLS_ENVIRONMENT:
            for optimized in (False, True):
                run_capture_tool(
                    optimized,
                    expected_status=1,
                    extra_environment={variable: "/untrusted/fixture"},
                )

        static_outputs = [
            run_checker(optimized, "--validate-static") for optimized in (False, True)
        ]
        require(
            static_outputs[0] == static_outputs[1], "static normal/-O outputs differ"
        )
        static = json.loads(static_outputs[0])
        require(
            static.get("result") == "pass"
            and static.get("schema")
            == "pid-rs/ksg-rev4-m1a-composite-v4-static-validation/v1",
            "static positive control changed",
        )
        c4 = static.get("c4_commit")
        require(type(c4) is str and len(c4) == 40, "static C4 identity changed")
        c4_tree = git_text("rev-parse", f"{c4}^{{tree}}")
        positive_capture = build_capture(c4, c4_tree)
        negative_captures = capture_negatives(positive_capture, c4, c4_tree)
        capture_vector = canonical(
            {"negative": negative_captures, "positive": positive_capture}
        )
        capture_outputs = [
            run_checker(optimized, "--self-test-capture-vectors", capture_vector)
            for optimized in (False, True)
        ]
        require(
            capture_outputs[0] == capture_outputs[1],
            "capture semantic normal/-O outputs differ",
        )
        capture_result = json.loads(capture_outputs[0])
        require(
            capture_result.get("result") == "pass"
            and capture_result.get("negative_count") == len(negative_captures)
            and type(capture_result.get("receipt")) is dict,
            "capture semantic vectors changed",
        )
        mixed_zip_capture = copy.deepcopy(positive_capture)
        redirected_zip_rows = [
            row
            for row in mixed_zip_capture["captures"]
            if row["response_kind"] == "zip"
        ]
        require(redirected_zip_rows, "mixed-ZIP fixture has no ZIP responses")
        original_redirect = copy.deepcopy(redirected_zip_rows[0]["redirect"])
        for row in redirected_zip_rows:
            row["redirect"] = None
        restored_redirect = False
        for row in mixed_zip_capture["captures"]:
            if (
                row["response_kind"] == "zip"
                and row["logical_request"]
                == redirected_zip_rows[0]["logical_request"]
                and row["repetition"] == 1
            ):
                row["redirect"] = original_redirect
                restored_redirect = True
                break
        require(restored_redirect, "mixed-ZIP safe redirect row is absent")
        unsafe_zip_redirect = copy.deepcopy(mixed_zip_capture)
        unsafe_redirect_mutated = False
        for row in unsafe_zip_redirect["captures"]:
            if type(row["redirect"]) is dict:
                row["redirect"]["target_host"] = "example.invalid"
                unsafe_redirect_mutated = True
                break
        require(unsafe_redirect_mutated, "unsafe ZIP redirect row is absent")
        mixed_zip_vector = canonical(
            {
                "negative": [unsafe_zip_redirect],
                "positive": mixed_zip_capture,
            }
        )
        mixed_zip_outputs = [
            run_checker(
                optimized,
                "--self-test-capture-vectors",
                mixed_zip_vector,
            )
            for optimized in (False, True)
        ]
        require(
            mixed_zip_outputs[0] == mixed_zip_outputs[1]
            and json.loads(mixed_zip_outputs[0]).get("result") == "pass"
            and json.loads(mixed_zip_outputs[0]).get("negative_count") == 1,
            "mixed direct/redirect ZIP response contract changed",
        )
        body_budget_capture = copy.deepcopy(positive_capture)
        retained_body_bytes = sum(
            len(base64.b64decode(row["body_base64"]))
            for row in body_budget_capture["captures"]
        )
        padding_size = MAX_CAPTURE_BODY_BYTES - retained_body_bytes + 1
        require(padding_size > 0, "positive capture already exceeds the body budget")
        padded = False
        for row in body_budget_capture["captures"]:
            if (
                row["logical_request"] == "migration_ci_run"
                and row["repetition"] == 1
            ):
                replace_row_body(
                    row,
                    base64.b64decode(row["body_base64"]) + b" " * padding_size,
                )
                padded = True
                break
        require(padded, "body-budget fixture row is absent")
        body_budget_vector = canonical(
            {"negative": [body_budget_capture], "positive": positive_capture}
        )
        require(
            len(body_budget_vector) <= MAX_JSON_BYTES,
            "body-budget vector exceeds the checker's input bound",
        )
        body_budget_outputs = [
            run_checker(
                optimized,
                "--self-test-capture-vectors",
                body_budget_vector,
            )
            for optimized in (False, True)
        ]
        require(
            body_budget_outputs[0] == body_budget_outputs[1]
            and json.loads(body_budget_outputs[0]).get("result") == "pass"
            and json.loads(body_budget_outputs[0]).get("negative_count") == 1,
            "aggregate retained-body budget mutation was accepted",
        )
        del body_budget_capture, body_budget_vector, body_budget_outputs
        receipt = capture_result["receipt"]
        receipt_positive = canonical({"capture": positive_capture, "receipt": receipt})
        receipt_outputs = [
            run_checker(optimized, "--self-test-receipt-vector", receipt_positive)
            for optimized in (False, True)
        ]
        require(
            receipt_outputs[0] == receipt_outputs[1]
            and json.loads(receipt_outputs[0]) == {"result": "pass"},
            "derived-receipt positive control changed",
        )
        wrong_receipt = copy.deepcopy(receipt)
        wrong_receipt["capture_binding"]["sha256"] = "f" * 64
        receipt_negative = canonical(
            {"capture": positive_capture, "receipt": wrong_receipt}
        )
        wrong_receipt_outputs = [
            run_checker(optimized, "--self-test-receipt-vector", receipt_negative)
            for optimized in (False, True)
        ]
        require(
            wrong_receipt_outputs[0] == wrong_receipt_outputs[1]
            and json.loads(wrong_receipt_outputs[0]) == {"result": "fail"},
            "capture-to-receipt binding mutation was accepted",
        )
        result = {
            "capture_mutations_rejected": len(negative_captures),
            "capture_body_budget_mutations_rejected": 1,
            "capture_mixed_zip_modes_passed": 2,
            "capture_unsafe_zip_redirects_rejected": 1,
            "capture_tool_modes_passed": 2,
            "capture_tool_tls_routes_rejected": 2
            * len(FORBIDDEN_TLS_ENVIRONMENT),
            "json_mutations_rejected": len(invalid_json),
            "receipt_mutations_rejected": 1,
            "result": "pass",
            "policy_mutations_rejected": len(policy_mutations),
            "schema_mutations_rejected": len(schema_mutations) + 10,
            "static_modes_passed": 2,
        }
        sys.stdout.buffer.write(compact(result))
        return 0
    except (SelfTestError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
