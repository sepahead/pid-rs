#!/usr/bin/env python3
"""Capture bounded GitHub observations for the fresh composite-v11 lifecycle.

``predecessor_failure`` freshly observes exact C9 attempt-1 outcomes and can
never qualify C10 or R10. ``successor_qualification`` requires three fresh
attempt-1 terminal-success runs for one caller-supplied C11 subject. The tool
does not reuse the rejected C10 capture or its R15. The implementation reuses only
checksum-bound immutable-v8 transport primitives. Provider bytes do not
authenticate themselves. Supply the token through an already-open descriptor.
"""

from __future__ import annotations

import sys


if not (
    sys.implementation.name == "cpython"
    and sys.version_info == (3, 14, 6, "final", 0)
    and sys._is_gil_enabled()
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: capture-ksg-m1a-composite-v11.py requires GIL-enabled CPython 3.14.6 -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import types
from typing import Any


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v11.py"
V8_RELATIVE = "scripts/capture-ksg-m1a-composite-v8.py"
V8_PATH = ROOT / V8_RELATIVE
V8_SHA256 = "79ffbe59dc57ed99d2b4032aa71cac300448d0978a42a52fcf7b40b08236ae6f"
V8_SIZE_BYTES = 24_111
REPOSITORY = "sepahead/pid-rs"
C9_COMMIT = "337fe9b7f7cf30a8f00138310ce0398d9e95b9c5"
C9_TREE = "325f9fb463e2ec8ed36f0c7b1d61c119e6861d9c"
PREDECESSOR_RUNS = {
    "predecessor_ci": 32_600_674_974,
    "predecessor_codeql": 32_600_674_616,
    "predecessor_contract": 32_600_674_991,
}
PREDECESSOR_CONCLUSIONS = {
    "predecessor_ci": "failure",
    "predecessor_codeql": "success",
    "predecessor_contract": "failure",
}
C9_CI_FAILED_JOBS = (97_098_355_474, 97_098_355_544, 97_098_355_596)
C9_CONTRACT_FAILED_JOB = 97_098_355_185
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_TLS_ENVIRONMENT = (
    "CURL_CA_BUNDLE",
    "OPENSSL_CONF",
    "PYTHONHTTPSVERIFY",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SSLKEYLOGFILE",
)
NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Two retrieval repetitions are correlated provider observations, not independent replications.",
    "The predecessor phase freshly records three separate C9 operational outcomes and cannot issue R9, qualify C10, or qualify C11.",
    "The C9 dedicated-v9 route failed its static checker; that does not identify or transfer a cause to the distinct repository-CI failures.",
    "The C9 repository CI Clippy, secret-scan, and SemVer failures remain distinct observations; no secret, API break, numerical defect, theorem defect, or common cause is inferred.",
    "Same-generation repository-CI and dedicated-workflow executions in either phase are correlated GitHub observations, not independent replications.",
    "Rejected C10 bytes, its unissued L10/R10, and its rejected R15 have zero C11 credit and are not inputs to this fresh capture.",
    "A successful successor phase is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "A newly emitted capture binds the current capture-tool descriptor and repeated response bytes, but freshness is controlled operator process rather than authenticated collection time; the format cannot distinguish live collection from manual reconstruction of identical public response bytes plus a changed descriptor.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]


class BootstrapError(RuntimeError):
    """The immutable v8 primitive source could not be loaded exactly."""


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v8() -> bytes:
    before = V8_PATH.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not V8_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V8_SIZE_BYTES,
        "immutable v8 capture primitive metadata changed",
    )
    descriptor = os.open(V8_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        bootstrap_require(
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
            "opened immutable v8 primitive identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "short immutable v8 primitive read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(os.read(descriptor, 1) == b"", "immutable v8 primitive grew")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = V8_PATH.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        bootstrap_require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "immutable v8 primitive changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V8_SHA256,
        "immutable v8 capture primitive digest changed",
    )
    return raw


def load_bound_v8(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_capture_ksg_m1a_composite_v8_primitives")
    module.__file__ = os.fspath(V8_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V8_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


try:
    V8_RAW = read_bound_v8()
    V8 = load_bound_v8(V8_RAW)
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected immutable-v8 primitive load failure", file=sys.stderr)
    raise SystemExit(2) from None

try:
    V8_SELF_TEST_BASELINE = V8.offline_self_test()
    bootstrap_require(
        V8_SELF_TEST_BASELINE.get("result") == "pass",
        "immutable v8 capture self-test failed before the v11 rebind",
    )
except Exception:
    print(
        "ERROR: immutable-v8 capture self-test failed before v11 rebind",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CaptureError = V8.CaptureError
require = V8.require
sha256 = V8.sha256
canonical_json = V8.canonical_json


def workflow_identity(role: str) -> tuple[str, str, str]:
    if role.endswith("_ci"):
        return "CI", ".github/workflows/ci.yml", "push"
    if role.endswith("_codeql"):
        return "Push on main", "dynamic/github-code-scanning/codeql", "dynamic"
    require(role.endswith("_contract"), f"unknown run role {role}")
    if role == "predecessor_contract":
        return (
            "KSG M1a composite v9",
            ".github/workflows/ksg-m1a-composite-v9.yml",
            "push",
        )
    require(role == "successor_contract", f"unknown contract role {role}")
    return (
        "KSG M1a composite v11",
        ".github/workflows/ksg-m1a-composite-v11.yml",
        "push",
    )


def expected_successor_artifact_names(role: str, head: str) -> set[str]:
    if role == "successor_ci":
        return {
            "coverage-lcov",
            f"post-commit-source-state-v2-{head}",
            "workspace-sbom",
        }
    if role == "successor_codeql":
        return set()
    require(role == "successor_contract", "unknown successor artifact role")
    return {f"ksg-m1a-composite-v11-static-{head}"}


# The checksum-bound transport and validators look these identities up through
# their module globals. Rebind only those phase identities in memory; never
# mutate the immutable v8 primitive bytes or its other bounds/transport rules.
V8.V7.V6.workflow_identity = workflow_identity
V8.V7.V6.expected_successor_artifact_names = expected_successor_artifact_names


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--phase", choices=("predecessor_failure", "successor_qualification")
    )
    parser.add_argument("--successor-commit")
    parser.add_argument("--successor-tree")
    parser.add_argument("--successor-ci-run", type=int)
    parser.add_argument("--successor-codeql-run", type=int)
    parser.add_argument("--successor-contract-run", type=int)
    parser.add_argument("--token-fd", type=int, default=3)
    return parser.parse_args()


def capture_configuration(
    arguments: argparse.Namespace,
) -> tuple[dict[str, int], dict[str, str], dict[str, str], dict[str, str]]:
    successor_values = (
        arguments.successor_commit,
        arguments.successor_tree,
        arguments.successor_ci_run,
        arguments.successor_codeql_run,
        arguments.successor_contract_run,
    )
    if arguments.phase == "predecessor_failure":
        require(
            all(value is None for value in successor_values),
            "predecessor failure capture does not accept successor subjects",
        )
        require(
            all(
                type(value) is int and value > 0 for value in PREDECESSOR_RUNS.values()
            ),
            "terminal C9 predecessor run roster is unresolved",
        )
        require(
            all(
                value in {"failure", "success"}
                for value in PREDECESSOR_CONCLUSIONS.values()
            ),
            "terminal C9 predecessor conclusions are unresolved",
        )
        return (
            dict(PREDECESSOR_RUNS),
            dict(PREDECESSOR_CONCLUSIONS),
            {role: C9_COMMIT for role in PREDECESSOR_RUNS},
            {"predecessor_commit": C9_COMMIT, "predecessor_tree": C9_TREE},
        )
    require(arguments.phase == "successor_qualification", "capture phase is required")
    require(
        type(arguments.successor_commit) is str
        and SHA1_RE.fullmatch(arguments.successor_commit) is not None
        and type(arguments.successor_tree) is str
        and SHA1_RE.fullmatch(arguments.successor_tree) is not None,
        "successor commit or tree is malformed",
    )
    runs = {
        "successor_ci": arguments.successor_ci_run,
        "successor_codeql": arguments.successor_codeql_run,
        "successor_contract": arguments.successor_contract_run,
    }
    require(
        all(type(value) is int and value > 0 for value in runs.values())
        and len(set(runs.values())) == len(runs),
        "successor run IDs must be positive and unique",
    )
    return (
        runs,
        {role: "success" for role in runs},
        {role: arguments.successor_commit for role in runs},
        {
            "predecessor_commit": C9_COMMIT,
            "predecessor_tree": C9_TREE,
            "successor_commit": arguments.successor_commit,
            "successor_tree": arguments.successor_tree,
        },
    )


def offline_self_test() -> dict[str, Any]:
    require(
        V8_SELF_TEST_BASELINE.get("result") == "pass",
        "immutable v8 primitive self-test failed",
    )
    namespace = argparse.Namespace(
        phase="successor_qualification",
        successor_commit="1" * 40,
        successor_tree="2" * 40,
        successor_ci_run=101,
        successor_codeql_run=102,
        successor_contract_run=103,
    )
    runs, conclusions, heads, subject = capture_configuration(namespace)
    require(
        runs
        == {"successor_ci": 101, "successor_codeql": 102, "successor_contract": 103}
        and set(conclusions.values()) == {"success"}
        and set(heads.values()) == {"1" * 40}
        and subject["successor_tree"] == "2" * 40,
        "successor configuration self-test changed",
    )
    rejected = 0
    for mutation in (
        {"successor_ci_run": 0},
        {"successor_codeql_run": 101},
        {"successor_commit": "z" * 40},
        {"successor_tree": None},
    ):
        values = vars(namespace) | mutation
        try:
            capture_configuration(argparse.Namespace(**values))
        except CaptureError:
            rejected += 1
    require(rejected == 4, "successor configuration mutations were accepted")
    predecessor_namespace = argparse.Namespace(
        phase="predecessor_failure",
        successor_commit=None,
        successor_tree=None,
        successor_ci_run=None,
        successor_codeql_run=None,
        successor_contract_run=None,
    )
    (
        predecessor_runs,
        predecessor_conclusions,
        predecessor_heads,
        predecessor_subject,
    ) = capture_configuration(predecessor_namespace)
    require(
        predecessor_runs == PREDECESSOR_RUNS
        and predecessor_conclusions
        == {
            "predecessor_ci": "failure",
            "predecessor_codeql": "success",
            "predecessor_contract": "failure",
        }
        and set(predecessor_heads.values()) == {C9_COMMIT}
        and predecessor_subject
        == {"predecessor_commit": C9_COMMIT, "predecessor_tree": C9_TREE},
        "terminal predecessor configuration self-test changed",
    )
    head = "1" * 40
    run_id = 101
    repository = {"full_name": REPOSITORY, "id": 17}

    def run_fixture(
        role: str, name: str, path: str, event: str, conclusion: str
    ) -> dict[str, Any]:
        return {
            "conclusion": conclusion,
            "event": event,
            "head_branch": "main",
            "head_repository": repository,
            "head_sha": head,
            "id": run_id,
            "name": name,
            "path": path,
            "repository": repository,
            "run_attempt": 1,
            "status": "completed",
        }

    exact_routes = {
        "predecessor_ci": ("CI", ".github/workflows/ci.yml", "push", "failure"),
        "predecessor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
            "success",
        ),
        "predecessor_contract": (
            "KSG M1a composite v9",
            ".github/workflows/ksg-m1a-composite-v9.yml",
            "push",
            "failure",
        ),
        "successor_ci": ("CI", ".github/workflows/ci.yml", "push", "success"),
        "successor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
            "success",
        ),
        "successor_contract": (
            "KSG M1a composite v11",
            ".github/workflows/ksg-m1a-composite-v11.yml",
            "push",
            "success",
        ),
    }
    route_fixtures: dict[str, dict[str, Any]] = {}
    for role, (name, path, event, conclusion) in exact_routes.items():
        fixture = run_fixture(role, name, path, event, conclusion)
        require(
            V8.V7.V6.validate_run_document(fixture, role, run_id, head, conclusion)
            == 17,
            f"hardcoded workflow identity rejected for {role}",
        )
        route_fixtures[role] = fixture
    stale_routes_rejected = 0
    for role, fixture, stale_name, stale_path, conclusion in (
        (
            "predecessor_contract",
            route_fixtures["predecessor_contract"],
            "KSG M1a composite v8",
            ".github/workflows/ksg-m1a-composite-v8.yml",
            "failure",
        ),
        (
            "successor_contract",
            route_fixtures["successor_contract"],
            "KSG M1a composite v9",
            ".github/workflows/ksg-m1a-composite-v9.yml",
            "success",
        ),
    ):
        stale = dict(fixture)
        stale["name"] = stale_name
        stale["path"] = stale_path
        try:
            V8.V7.V6.validate_run_document(stale, role, run_id, head, conclusion)
        except CaptureError:
            stale_routes_rejected += 1
    require(
        stale_routes_rejected == 2, "an adjacent-generation workflow route was accepted"
    )

    exact_artifact_sets = {
        "successor_ci": {
            "coverage-lcov",
            f"post-commit-source-state-v2-{head}",
            "workspace-sbom",
        },
        "successor_codeql": set(),
        "successor_contract": {f"ksg-m1a-composite-v11-static-{head}"},
    }
    require(
        all(
            expected_successor_artifact_names(role, head) == expected
            for role, expected in exact_artifact_sets.items()
        ),
        "hardcoded successor artifact sets changed",
    )

    stale_artifact = {
        "expired": False,
        "id": 201,
        "name": f"ksg-m1a-composite-v9-static-{head}",
        "size_in_bytes": 1,
        "workflow_run": {
            "head_branch": "main",
            "head_repository_id": 17,
            "head_sha": head,
            "id": run_id,
            "repository_id": 17,
        },
    }
    stale_artifacts_rejected = 0
    for role in exact_artifact_sets:
        hostile = dict(stale_artifact)
        hostile["name"] = (
            f"ksg-m1a-composite-v9-static-{head}"
            if role == "successor_contract"
            else "wrong-artifact"
        )
        try:
            V8.V7.V6.capture_artifacts(
                role,
                [hostile],
                run_id,
                17,
                head,
                b"fixture-token",
                1,
                [],
                [],
            )
        except CaptureError:
            stale_artifacts_rejected += 1
    require(
        stale_artifacts_rejected == 3,
        "an incorrect successor artifact set was accepted",
    )
    return {
        "configuration_mutations_rejected": rejected,
        "immutable_v8_capture_self_test": "pass",
        "phase_aware_workflow_routes_verified": 6,
        "predecessor_terminal_roster_bound": PREDECESSOR_RUNS
        == {
            "predecessor_ci": 32_600_674_974,
            "predecessor_codeql": 32_600_674_616,
            "predecessor_contract": 32_600_674_991,
        },
        "predecessor_failed_job_partition_bound": {
            "predecessor_ci": list(C9_CI_FAILED_JOBS),
            "predecessor_codeql": [],
            "predecessor_contract": [C9_CONTRACT_FAILED_JOB],
        },
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-capture-self-test/v1",
        "stale_artifact_routes_rejected": stale_artifacts_rejected,
        "stale_workflow_routes_rejected": stale_routes_rejected,
    }


def main() -> int:
    arguments = parse_arguments()
    try:
        require(
            all(key not in os.environ for key in FORBIDDEN_TLS_ENVIRONMENT),
            "ambient TLS-routing or key-log environment is unsupported",
        )
        current_v8 = V8.V7.V6.read_regular(V8_PATH, V8_SIZE_BYTES, 0o644)
        require(
            current_v8 == V8_RAW and sha256(current_v8) == V8_SHA256,
            "immutable v8 primitives changed",
        )
        if arguments.self_test:
            require(
                arguments.phase is None
                and all(
                    value is None
                    for value in (
                        arguments.successor_commit,
                        arguments.successor_tree,
                        arguments.successor_ci_run,
                        arguments.successor_codeql_run,
                        arguments.successor_contract_run,
                    )
                ),
                "offline self-test does not accept capture subjects",
            )
            sys.stdout.buffer.write(canonical_json(offline_self_test()))
            return 0

        runs, conclusions, heads, subject = capture_configuration(arguments)
        require(
            len(set(runs.values())) == len(runs), "run IDs overlap within the phase"
        )
        token = V8.V7.V6.read_token(arguments.token_fd)
        script_raw = V8.V7.V6.read_regular(SCRIPT, 1024 * 1024, 0o644)
        captures: list[dict[str, Any]] = []
        retry_events: list[dict[str, Any]] = []
        repository_ids: list[int] = []
        failed_by_role: dict[str, list[int]] = {}
        for repetition in (1, 2):
            for role in sorted(runs):
                artifacts, failed_job_ids, repository_id = V8.V7.V6.capture_run(
                    role,
                    runs[role],
                    heads[role],
                    conclusions[role],
                    token,
                    repetition,
                    captures,
                    retry_events,
                )
                repository_ids.append(repository_id)
                previous = failed_by_role.setdefault(role, failed_job_ids)
                require(
                    previous == failed_job_ids, f"{role} failed-job identity changed"
                )
                V8.V7.V6.capture_artifacts(
                    role,
                    artifacts,
                    runs[role],
                    repository_id,
                    heads[role],
                    token,
                    repetition,
                    captures,
                    retry_events,
                )
                if arguments.phase == "predecessor_failure":
                    V8.V7.V6.capture_failed_logs(
                        role,
                        failed_job_ids,
                        token,
                        repetition,
                        captures,
                        retry_events,
                    )
                if role == "successor_codeql":
                    V8.V7.V6.capture_codeql(
                        heads[role], token, repetition, captures, retry_events
                    )
        require(
            len(repository_ids) == len(runs) * 2 and len(set(repository_ids)) == 1,
            "captured runs disagree on repository numeric identity",
        )
        if arguments.phase == "predecessor_failure":
            require(
                failed_by_role["predecessor_ci"] == list(C9_CI_FAILED_JOBS)
                and failed_by_role["predecessor_codeql"] == []
                and failed_by_role["predecessor_contract"] == [C9_CONTRACT_FAILED_JOB],
                "predecessor failed-job partition changed",
            )
        else:
            require(
                all(failed == [] for failed in failed_by_role.values()),
                "successor qualification retained a failed job",
            )
        captures.sort(
            key=lambda row: (
                row["logical_request"],
                row["repetition"],
                row["page"],
                row["path"],
            )
        )
        retry_events.sort(
            key=lambda row: (
                row["logical_request"],
                row["repetition"],
                row["page"],
                row["path"],
                row["attempt"],
            )
        )
        result = {
            "capture_tool": {
                "path": SCRIPT_RELATIVE,
                "sha256": sha256(script_raw),
                "size_bytes": len(script_raw),
            },
            "captures": captures,
            "immutable_v8_primitives": {
                "path": V8_RELATIVE,
                "sha256": V8_SHA256,
                "size_bytes": V8_SIZE_BYTES,
            },
            "nonimplications": NONIMPLICATIONS,
            "phase": arguments.phase,
            "repository": REPOSITORY,
            "retry_events": retry_events,
            "runs": runs,
            "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v11",
            "schema_revision": 11,
            "subject": subject,
        }
        require(
            len(captures) <= V8.V7.V6.MAX_CAPTURE_ROWS,
            "capture response count exceeds bound",
        )
        require(
            sum(row["body_size_bytes"] for row in captures)
            <= V8.V7.V6.MAX_CAPTURE_BODY_BYTES,
            "retained provider bodies exceed bound",
        )
        rendered = canonical_json(result)
        require(
            len(rendered) <= V8.V7.V6.MAX_CAPTURE_BYTES,
            "capture document exceeds bound",
        )
        sys.stdout.buffer.write(rendered)
        return 0
    except (CaptureError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: unexpected bounded capture failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
