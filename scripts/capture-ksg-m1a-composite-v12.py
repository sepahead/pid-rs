#!/usr/bin/env python3
"""Capture bounded attempt-1 hosted observations for exact composite-v12.

Only the successor-qualification phase exists here. The consumed C11 local
failure is a separately reviewed repository diagnostic, not a GitHub run and
not an input to this capture. Transport is reused from one exact frozen v11
source file; this wrapper supplies and tests the v12 workflow semantics.
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
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: capture-ksg-m1a-composite-v12.py requires GIL-enabled "
        "CPython 3.14.6 -I -S -B and at most one -O",
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
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v12.py"
V11_RELATIVE = "scripts/capture-ksg-m1a-composite-v11.py"
V11_PATH = ROOT / V11_RELATIVE
V11_SHA256 = "2602fc868b92621e1109658845779d70fc870d6522222128c427ba5cfea7b191"
V11_SIZE_BYTES = 25_607
REPOSITORY = "sepahead/pid-rs"
C11_COMMIT = "91d954160a7e717ae46b6088175ae52e92570127"
C11_TREE = "97841c6eda10573ddc3537c9e3b2ca41a93a3fa1"
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
    "The consumed failed L11, false Q11, and permanently unissued R11 grant no C12 qualification credit.",
    "Repository-CI, CodeQL, and dedicated-v12 are separate correlated provider observations; no common cause is inferred.",
    "A successful capture is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "The capture binds the wrapper and frozen transport bytes, but cannot prove which bytes the operating system executed or exclude interference.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]


class BootstrapError(RuntimeError):
    """The exact frozen v11 hosted transport could not be loaded."""


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v11(path: Path = V11_PATH) -> bytes:
    before = path.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V11_SIZE_BYTES,
        "frozen v11 hosted primitive metadata changed",
    )
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
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
            "opened frozen v11 hosted primitive identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "short frozen v11 hosted primitive read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(
            os.read(descriptor, 1) == b"", "frozen v11 hosted primitive grew"
        )
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
        bootstrap_require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "frozen v11 hosted primitive changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V11_SHA256,
        "frozen v11 hosted primitive digest changed",
    )
    return raw


def load_bound_v11(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_capture_ksg_m1a_composite_v11_frozen")
    module.__file__ = os.fspath(V11_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V11_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


try:
    V11_RAW = read_bound_v11()
    V11 = load_bound_v11(V11_RAW)
    V11_SELF_TEST = V11.offline_self_test()
    bootstrap_require(
        V11_SELF_TEST.get("result") == "pass",
        "frozen v11 hosted primitive self-test failed",
    )
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected frozen-v11 hosted primitive load failure", file=sys.stderr)
    raise SystemExit(2) from None


CaptureError = V11.CaptureError
require = V11.require
sha256 = V11.sha256
canonical_json = V11.canonical_json
V8 = V11.V8


def workflow_identity(role: str) -> tuple[str, str, str]:
    if role == "successor_ci":
        return "CI", ".github/workflows/ci.yml", "push"
    if role == "successor_codeql":
        return "Push on main", "dynamic/github-code-scanning/codeql", "dynamic"
    require(role == "successor_contract", f"unknown run role {role}")
    return (
        "KSG M1a composite v12",
        ".github/workflows/ksg-m1a-composite-v12.yml",
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
    return {f"ksg-m1a-composite-v12-static-{head}"}


# The frozen transport resolves these two semantic functions through globals.
# Only v12 workflow identity and expected artifact names are rebound; all HTTP,
# retry, size, descriptor, and canonicalization primitives remain frozen.
V8.V7.V6.workflow_identity = workflow_identity
V8.V7.V6.expected_successor_artifact_names = expected_successor_artifact_names


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
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
            "predecessor_commit": C11_COMMIT,
            "predecessor_tree": C11_TREE,
            "successor_commit": arguments.successor_commit,
            "successor_tree": arguments.successor_tree,
        },
    )


def offline_self_test() -> dict[str, Any]:
    namespace = argparse.Namespace(
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
        and subject
        == {
            "predecessor_commit": C11_COMMIT,
            "predecessor_tree": C11_TREE,
            "successor_commit": "1" * 40,
            "successor_tree": "2" * 40,
        },
        "v12 successor configuration changed",
    )
    rejected = 0
    for mutation in (
        {"successor_ci_run": 0},
        {"successor_codeql_run": 101},
        {"successor_commit": "z" * 40},
        {"successor_tree": None},
    ):
        try:
            capture_configuration(argparse.Namespace(**(vars(namespace) | mutation)))
        except CaptureError:
            rejected += 1
    require(rejected == 4, "v12 successor configuration mutation escaped")

    repository = {"full_name": REPOSITORY, "id": 17}
    run = {
        "conclusion": "success",
        "event": "push",
        "head_branch": "main",
        "head_repository": repository,
        "head_sha": "1" * 40,
        "id": 103,
        "name": "KSG M1a composite v12",
        "path": ".github/workflows/ksg-m1a-composite-v12.yml",
        "repository": repository,
        "run_attempt": 1,
        "status": "completed",
    }
    require(
        V8.V7.V6.validate_run_document(
            run, "successor_contract", 103, "1" * 40, "success"
        )
        == 17,
        "v12 workflow route positive control failed",
    )
    stale = dict(run)
    stale["name"] = "KSG M1a composite v11"
    stale["path"] = ".github/workflows/ksg-m1a-composite-v11.yml"
    try:
        V8.V7.V6.validate_run_document(
            stale, "successor_contract", 103, "1" * 40, "success"
        )
    except CaptureError:
        stale_rejected = 1
    else:
        stale_rejected = 0
    require(stale_rejected == 1, "retired v11 workflow route was accepted")
    require(
        expected_successor_artifact_names("successor_contract", "1" * 40)
        == {f"ksg-m1a-composite-v12-static-{'1' * 40}"},
        "v12 static artifact identity changed",
    )
    return {
        "configuration_mutations_rejected": rejected,
        "frozen_v11_capture_self_test": "pass",
        "result": "pass",
        "retired_v11_workflow_routes_rejected": stale_rejected,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-capture-self-test/v1",
    }


def main() -> int:
    arguments = parse_arguments()
    try:
        require(
            all(key not in os.environ for key in FORBIDDEN_TLS_ENVIRONMENT),
            "ambient TLS-routing or key-log environment is unsupported",
        )
        current_v11 = read_bound_v11()
        require(current_v11 == V11_RAW, "frozen v11 transport changed after load")
        if arguments.self_test:
            require(
                all(
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
        token = V8.V7.V6.read_token(arguments.token_fd)
        script_raw = V8.V7.V6.read_regular(SCRIPT, 1024 * 1024, 0o644)
        captures: list[dict[str, Any]] = []
        retry_events: list[dict[str, Any]] = []
        repository_ids: list[int] = []
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
                require(failed_job_ids == [], f"{role} retained a failed job")
                repository_ids.append(repository_id)
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
                if role == "successor_codeql":
                    V8.V7.V6.capture_codeql(
                        heads[role], token, repetition, captures, retry_events
                    )
        require(
            len(repository_ids) == len(runs) * 2 and len(set(repository_ids)) == 1,
            "captured runs disagree on repository numeric identity",
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
                "path": V11.V8_RELATIVE,
                "sha256": V11.V8_SHA256,
                "size_bytes": V11.V8_SIZE_BYTES,
            },
            "immutable_v11_primitives": {
                "path": V11_RELATIVE,
                "sha256": V11_SHA256,
                "size_bytes": V11_SIZE_BYTES,
            },
            "nonimplications": NONIMPLICATIONS,
            "phase": "successor_qualification",
            "repository": REPOSITORY,
            "retry_events": retry_events,
            "runs": runs,
            "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v12",
            "schema_revision": 12,
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
    except (BootstrapError, CaptureError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: unexpected bounded v12 capture failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
