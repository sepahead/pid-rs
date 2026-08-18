#!/usr/bin/env python3
"""Capture bounded GitHub observations for the composite-v6 correction lifecycle.

The two capture phases are intentionally disjoint. ``predecessor_failure`` preserves the exact
C5 failure boundary and can never qualify a receipt. ``successor_qualification`` observes a
caller-supplied C6 subject and requires three attempt-1 terminal-success runs. On success the
command writes one canonical JSON document to stdout; callers must discard stdout after any
nonzero exit. Supply the token on an already-open descriptor, never in argv.

This tool executes checksum-bound primitives from the immutable v5 capture tool. It neither
modifies the repository nor authenticates provider claims.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import types
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: capture-ksg-m1a-composite-v6.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v6.py"
V5_RELATIVE = "scripts/capture-ksg-m1a-composite-v5.py"
V5_PATH = ROOT / V5_RELATIVE
V5_SHA256 = "a0e955c9645c852276a3750ee24c49c8feb029d748a73909461d4f71777b3a11"
V5_SIZE_BYTES = 41_566
REPOSITORY = "sepahead/pid-rs"
PREDECESSOR_COMMIT = "be862b155d710573ec95356fc1cbe9a96a2b83b9"
PREDECESSOR_TREE = "37ae61554284a2fabb460d3a20a731b6ade5f8f4"
PREDECESSOR_RUNS = {
    "predecessor_ci": 32_107_469_096,
    "predecessor_codeql": 32_107_469_060,
    "predecessor_contract": 32_107_469_077,
}
PREDECESSOR_CONCLUSIONS = {
    "predecessor_ci": "failure",
    "predecessor_codeql": "success",
    "predecessor_contract": "failure",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
REDIRECT_HOST_SUFFIXES = (
    ".blob.core.windows.net",
    ".githubusercontent.com",
)
REDIRECT_HOST_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:blob\.core\.windows\.net|githubusercontent\.com)$"
)
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
    "The two retrieval repetitions are correlated observations of provider state, not independent replications.",
    "The predecessor failure phase records C5's terminal hosted failure; it grants no hosted-success, R5-receipt, mathematical, estimator, or application-validation credit.",
    "A successful successor run is not mathematical, estimator, security, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to the workflow run or its historical execution window.",
    "Failed-job log bytes record provider output but do not by themselves establish a unique defect cause, generic portability defect, or remediation.",
    "Capture time, network completeness, provider response order, and trusted provider time are not claimed.",
    "The capture makes no claim about any PID functional, objective, estimator, or downstream use.",
]


class _BootstrapError(RuntimeError):
    """The immutable primitive source could not be safely loaded."""


def _bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise _BootstrapError(message)


def _read_bound_primitive(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise _BootstrapError(
            f"cannot stat immutable v5 primitive source: {error}"
        ) from None
    _bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V5_SIZE_BYTES,
        "immutable v5 primitive source metadata changed",
    )
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as error:
        raise _BootstrapError(
            f"cannot open immutable v5 primitive source: {error}"
        ) from None
    try:
        opened = os.fstat(descriptor)
        _bootstrap_require(
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
            "opened immutable v5 primitive identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            _bootstrap_require(chunk != b"", "short immutable v5 primitive read")
            chunks.append(chunk)
            remaining -= len(chunk)
        _bootstrap_require(
            os.read(descriptor, 1) == b"",
            "immutable v5 primitive source grew during read",
        )
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    identity = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    _bootstrap_require(
        all(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field)
            for field in identity
        ),
        "immutable v5 primitive source changed during read",
    )
    raw = b"".join(chunks)
    _bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V5_SHA256,
        "immutable v5 primitive source digest changed",
    )
    return raw


def _load_bound_v5(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_capture_ksg_m1a_composite_v5_primitives")
    module.__file__ = os.fspath(V5_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V5_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


try:
    _V5_RAW = _read_bound_primitive(V5_PATH)
    V5 = _load_bound_v5(_V5_RAW)
except (_BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected immutable-v5 primitive load failure", file=sys.stderr)
    raise SystemExit(2) from None


CaptureError = V5.CaptureError
require = V5.require
sha256 = V5.sha256
canonical_json = V5.canonical_json
retain_capture = V5.retain_capture
strict_json = V5.strict_json
read_regular = V5.read_regular
read_token = V5.read_token
bounded_response = V5.bounded_response
open_without_proxy = V5.open_without_proxy
MAX_CAPTURE_BYTES = V5.MAX_CAPTURE_BYTES
MAX_CAPTURE_BODY_BYTES = V5.MAX_CAPTURE_BODY_BYTES
MAX_CAPTURE_ROWS = V5.MAX_CAPTURE_ROWS
MAX_PAGES = V5.MAX_PAGES
API_ROOT = V5.API_ROOT


def _download_class(path: str) -> str | None:
    if (
        re.fullmatch(
            rf"/repos/{re.escape(REPOSITORY)}/actions/artifacts/[0-9]+/zip", path
        )
        is not None
    ):
        return "artifact"
    if (
        re.fullmatch(rf"/repos/{re.escape(REPOSITORY)}/actions/jobs/[0-9]+/logs", path)
        is not None
    ):
        return "job_log"
    return None


def request_once(
    path: str, token: bytes
) -> tuple[int, str, bytes, dict[str, Any] | None]:
    require(
        path.startswith(f"/repos/{REPOSITORY}/"), "request path leaves repository scope"
    )
    request = urllib.request.Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token.decode("ascii"),
            "User-Agent": "pid-rs-composite-v6-capture",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    redirect: dict[str, Any] | None = None
    try:
        response = open_without_proxy(request)
    except urllib.error.HTTPError as error:
        if error.code not in {301, 302, 303, 307, 308}:
            raise
        location = error.headers.get("Location")
        error.close()
        require(type(location) is str, "download redirect has no Location header")
        require(
            _download_class(path) is not None,
            "non-download request attempted to redirect",
        )
        decoded_location = urllib.parse.unquote_to_bytes(location)
        require(
            token not in location.encode("utf-8") and token not in decoded_location,
            "download redirect URL contains the authentication token",
        )
        parsed = urllib.parse.urlsplit(location)
        try:
            target_port = parsed.port
        except ValueError as port_error:
            raise CaptureError(
                f"download redirect has an invalid port: {port_error}"
            ) from None
        require(
            parsed.scheme == "https"
            and parsed.hostname is not None
            and REDIRECT_HOST_RE.fullmatch(parsed.hostname) is not None
            and any(
                parsed.hostname.endswith(suffix) for suffix in REDIRECT_HOST_SUFFIXES
            )
            and parsed.username is None
            and parsed.password is None
            and target_port in {None, 443}
            and parsed.fragment == "",
            "download redirect leaves the reviewed HTTPS host set",
        )
        redirect = {
            "status_code": error.code,
            "target_host": parsed.hostname,
            "target_url_sha256": sha256(location.encode("utf-8")),
        }
        redirected = urllib.request.Request(
            location,
            headers={"User-Agent": "pid-rs-composite-v6-capture"},
            method="GET",
        )
        response = open_without_proxy(redirected)
    with response:
        body = bounded_response(response)
        media_type = response.headers.get_content_type()
        return response.status, media_type, body, redirect


def fetch(
    path: str,
    token: bytes,
    logical_request: str,
    repetition: int,
    page: int,
    response_kind: str,
    retry_events: list[dict[str, Any]],
) -> tuple[dict[str, Any], bytes]:
    for attempt in range(1, 4):
        try:
            status_code, media_type, body, redirect = request_once(path, token)
        except urllib.error.HTTPError as error:
            body = bounded_response(error)
            require(token not in body, "provider error response contains the token")
            retryable = error.code in {429, 502, 503, 504}
            if not retryable or attempt == 3:
                raise CaptureError(
                    f"provider HTTP failure for {logical_request}: {error.code}"
                ) from None
            retry_events.append(
                {
                    "attempt": attempt,
                    "category": f"http_{error.code}",
                    "logical_request": logical_request,
                    "page": page,
                    "path": path,
                    "repetition": repetition,
                    "response_sha256": sha256(body),
                    "response_size_bytes": len(body),
                }
            )
            V5.V4.time.sleep(0.25 * (2 ** (attempt - 1)))
            continue
        except (TimeoutError, urllib.error.URLError) as error:
            failure = str(error).encode("utf-8", errors="replace")
            require(token not in failure, "transport failure contains the token")
            if attempt == 3:
                raise CaptureError(
                    f"provider transport failure for {logical_request}"
                ) from None
            retry_events.append(
                {
                    "attempt": attempt,
                    "category": "transport",
                    "logical_request": logical_request,
                    "page": page,
                    "path": path,
                    "repetition": repetition,
                    "response_sha256": sha256(failure),
                    "response_size_bytes": len(failure),
                }
            )
            V5.V4.time.sleep(0.25 * (2 ** (attempt - 1)))
            continue
        require(status_code == 200, f"provider status changed for {logical_request}")
        require(token not in body, "provider response contains the token")
        if response_kind == "json":
            strict_json(body, logical_request)
            require(
                media_type in {"application/json", "application/octet-stream"},
                "JSON media type changed",
            )
        elif response_kind == "zip":
            require(
                media_type in {"application/zip", "application/octet-stream"},
                "ZIP media type changed",
            )
            require(body.startswith(b"PK"), "artifact response is not a ZIP archive")
        else:
            require(response_kind == "log", "unknown response kind")
            require(
                media_type in {"text/plain", "application/octet-stream"},
                "job-log media type changed",
            )
            require(body != b"", "failed-job log is empty")
        return (
            {
                "body_base64": V5.V4.base64.b64encode(body).decode("ascii"),
                "body_sha256": sha256(body),
                "body_size_bytes": len(body),
                "logical_request": logical_request,
                "media_type": media_type,
                "page": page,
                "path": path,
                "redirect": redirect,
                "repetition": repetition,
                "response_kind": response_kind,
                "status_code": status_code,
            },
            body,
        )
    raise CaptureError("unreachable provider retry state")


def paged(
    path_prefix: str,
    logical_request: str,
    field: str | None,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> list[Any]:
    combined: list[Any] = []
    for page in range(1, MAX_PAGES + 1):
        separator = "&" if "?" in path_prefix else "?"
        path = f"{path_prefix}{separator}per_page=100&page={page}"
        row, body = fetch(
            path,
            token,
            logical_request,
            repetition,
            page,
            "json",
            retry_events,
        )
        retain_capture(captures, row)
        value = strict_json(body, logical_request)
        if field is None:
            require(type(value) is list, f"{logical_request} page is not an array")
            items = value
        else:
            require(
                type(value) is dict and type(value.get(field)) is list,
                f"{logical_request} page shape changed",
            )
            items = value[field]
        if not items:
            return combined
        require(
            len(combined) + len(items) <= MAX_CAPTURE_ROWS,
            f"{logical_request} row count exceeds bound",
        )
        combined.extend(items)
    raise CaptureError(f"{logical_request} pagination exceeds bound")


def workflow_identity(role: str) -> tuple[str, str, str]:
    if role.endswith("_ci"):
        return "CI", ".github/workflows/ci.yml", "push"
    if role.endswith("_codeql"):
        return "Push on main", "dynamic/github-code-scanning/codeql", "dynamic"
    require(role.endswith("_contract"), f"unknown run role {role}")
    if role.startswith("predecessor_"):
        return (
            "KSG M1a composite v5",
            ".github/workflows/ksg-m1a-composite-v5.yml",
            "push",
        )
    return (
        "KSG M1a composite v6",
        ".github/workflows/ksg-m1a-composite-v6.yml",
        "push",
    )


def validate_run_document(
    run: Any,
    role: str,
    run_id: int,
    head: str,
    expected_conclusion: str,
) -> int:
    repository = run.get("repository") if type(run) is dict else None
    head_repository = run.get("head_repository") if type(run) is dict else None
    repository_id = repository.get("id") if type(repository) is dict else None
    expected_name, expected_path, expected_event = workflow_identity(role)
    require(
        type(run) is dict
        and run.get("id") == run_id
        and type(run.get("id")) is int
        and run.get("run_attempt") == 1
        and type(run.get("run_attempt")) is int
        and run.get("head_sha") == head
        and run.get("head_branch") == "main"
        and run.get("status") == "completed"
        and run.get("conclusion") == expected_conclusion
        and run.get("name") == expected_name
        and run.get("path") == expected_path
        and run.get("event") == expected_event
        and type(repository) is dict
        and repository.get("full_name") == REPOSITORY
        and type(repository_id) is int
        and repository_id > 0
        and type(head_repository) is dict
        and head_repository.get("full_name") == REPOSITORY
        and head_repository.get("id") == repository_id
        and type(head_repository.get("id")) is int,
        f"{role} run is not its exact terminal-{expected_conclusion} subject",
    )
    return repository_id


def validate_jobs(
    jobs: list[Any],
    role: str,
    run_id: int,
    head: str,
    expected_conclusion: str,
) -> list[int]:
    require(jobs != [], f"{role} job roster is empty")
    ids: list[int] = []
    failed: list[int] = []
    for job in jobs:
        require(type(job) is dict, f"{role} job is not an object")
        job_id = job.get("id")
        conclusion = job.get("conclusion")
        require(
            type(job_id) is int
            and job_id > 0
            and job.get("run_id") == run_id
            and type(job.get("run_id")) is int
            and job.get("run_attempt") == 1
            and type(job.get("run_attempt")) is int
            and job.get("head_sha") == head
            and job.get("status") == "completed"
            and conclusion in {"success", "failure", "cancelled", "skipped"},
            f"{role} job is not joined to the exact terminal run",
        )
        ids.append(job_id)
        if conclusion == "failure":
            failed.append(job_id)
    require(len(ids) == len(set(ids)), f"{role} job IDs are duplicated")
    if expected_conclusion == "success":
        require(
            failed == [] and all(job.get("conclusion") == "success" for job in jobs),
            f"{role} successful run contains a non-successful job",
        )
    else:
        require(
            expected_conclusion == "failure" and failed != [],
            f"{role} failed run has no failed job",
        )
    return sorted(failed)


def capture_run(
    role: str,
    run_id: int,
    head: str,
    expected_conclusion: str,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> tuple[list[Any], list[int], int]:
    run_path = f"/repos/{REPOSITORY}/actions/runs/{run_id}"
    row, body = fetch(
        run_path, token, f"{role}_run", repetition, 0, "json", retry_events
    )
    run = strict_json(body, f"{role} run")
    repository_id = validate_run_document(run, role, run_id, head, expected_conclusion)
    retain_capture(captures, row)
    jobs = paged(
        f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs",
        f"{role}_jobs",
        "jobs",
        token,
        repetition,
        captures,
        retry_events,
    )
    failed = validate_jobs(jobs, role, run_id, head, expected_conclusion)
    artifacts = paged(
        f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts",
        f"{role}_artifacts",
        "artifacts",
        token,
        repetition,
        captures,
        retry_events,
    )
    return artifacts, failed, repository_id


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
    return {f"ksg-m1a-composite-v6-static-{head}"}


def capture_artifacts(
    role: str,
    artifacts: list[Any],
    run_id: int,
    repository_id: int,
    head: str,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> None:
    ids: list[int] = []
    names: list[str] = []
    for artifact in artifacts:
        require(type(artifact) is dict, f"{role} artifact is not an object")
        artifact_id = artifact.get("id")
        name = artifact.get("name")
        workflow_run = artifact.get("workflow_run")
        require(
            type(artifact_id) is int
            and artifact_id > 0
            and type(name) is str
            and name != ""
            and artifact.get("expired") is False
            and type(artifact.get("size_in_bytes")) is int
            and artifact.get("size_in_bytes") > 0
            and type(workflow_run) is dict
            and workflow_run.get("id") == run_id
            and type(workflow_run.get("id")) is int
            and workflow_run.get("head_sha") == head
            and workflow_run.get("head_branch") == "main"
            and workflow_run.get("repository_id") == repository_id
            and type(workflow_run.get("repository_id")) is int
            and workflow_run.get("head_repository_id") == repository_id
            and type(workflow_run.get("head_repository_id")) is int,
            f"{role} artifact is not downloadable and joined to the requested run/head",
        )
        ids.append(artifact_id)
        names.append(name)
    require(len(ids) == len(set(ids)), f"{role} artifact IDs are duplicated")
    require(len(names) == len(set(names)), f"{role} artifact names are duplicated")
    if role == "predecessor_codeql" or role == "predecessor_contract":
        require(names == [], f"{role} unexpectedly published an artifact")
    if role.startswith("successor_"):
        require(
            set(names) == expected_successor_artifact_names(role, head),
            f"{role} artifact inventory changed",
        )
    for artifact_id in sorted(ids):
        path = f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
        row, _body = fetch(
            path,
            token,
            f"{role}_artifact_{artifact_id}",
            repetition,
            0,
            "zip",
            retry_events,
        )
        retain_capture(captures, row)


def capture_failed_logs(
    role: str,
    failed_job_ids: list[int],
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> None:
    for job_id in failed_job_ids:
        path = f"/repos/{REPOSITORY}/actions/jobs/{job_id}/logs"
        row, _body = fetch(
            path,
            token,
            f"{role}_failed_job_{job_id}_log",
            repetition,
            0,
            "log",
            retry_events,
        )
        retain_capture(captures, row)


def capture_codeql(
    head: str,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> None:
    analyses = paged(
        f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
        "successor_codeql_analyses",
        None,
        token,
        repetition,
        captures,
        retry_events,
    )
    require(
        any(
            type(analysis) is dict
            and analysis.get("commit_sha") == head
            and analysis.get("ref") == "refs/heads/main"
            for analysis in analyses
        ),
        "CodeQL current-state observation contains no successor-head analysis",
    )
    for state in ("open", "dismissed", "fixed"):
        paged(
            f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}",
            f"successor_codeql_alerts_{state}",
            None,
            token,
            repetition,
            captures,
            retry_events,
        )


class _FixtureHeaders(dict[str, str]):
    def get_content_type(self) -> str:
        return self.get("Content-Type", "application/octet-stream")


class _FixtureResponse:
    def __init__(self, body: bytes, media_type: str = "application/json") -> None:
        self._stream = V5.V4.io.BytesIO(body)
        self.headers = _FixtureHeaders({"Content-Type": media_type})
        self.status = 200

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __enter__(self) -> _FixtureResponse:
        return self

    def __exit__(self, *_arguments: Any) -> None:
        self._stream.close()


def _expect_capture_error(function: Any, message: str) -> None:
    try:
        function()
    except CaptureError:
        return
    raise CaptureError(message)


def _fixture_run(role: str, run_id: int, head: str, conclusion: str) -> dict[str, Any]:
    name, path, event = workflow_identity(role)
    return {
        "conclusion": conclusion,
        "event": event,
        "head_branch": "main",
        "head_repository": {"full_name": REPOSITORY, "id": 17},
        "head_sha": head,
        "id": run_id,
        "name": name,
        "path": path,
        "repository": {"full_name": REPOSITORY, "id": 17},
        "run_attempt": 1,
        "status": "completed",
    }


def offline_self_test() -> dict[str, Any]:
    primitive_result = V5.offline_self_test()
    require(
        type(primitive_result) is dict and primitive_result.get("result") == "pass",
        "immutable v5 primitive self-test failed",
    )
    token = b"fixture-secret-token"
    log_path = f"/repos/{REPOSITORY}/actions/jobs/17/logs"
    target = "https://fixture.blob.core.windows.net/job-log?sig=redacted"
    original_open = globals()["open_without_proxy"]
    observed_requests: list[urllib.request.Request] = []

    def redirect_then_log(request: urllib.request.Request) -> Any:
        observed_requests.append(request)
        if len(observed_requests) == 1:
            headers = _FixtureHeaders({"Location": target})
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "fixture redirect",
                headers,
                V5.V4.io.BytesIO(b""),
            )
        return _FixtureResponse(b"\xef\xbb\xbffixtures\n", "text/plain")

    globals()["open_without_proxy"] = redirect_then_log
    try:
        status, media_type, body, redirect = request_once(log_path, token)
    finally:
        globals()["open_without_proxy"] = original_open
    second_headers = {
        key.lower(): value for key, value in observed_requests[1].header_items()
    }
    require(
        status == 200
        and media_type == "text/plain"
        and body == b"\xef\xbb\xbffixtures\n"
        and redirect
        == {
            "status_code": 302,
            "target_host": "fixture.blob.core.windows.net",
            "target_url_sha256": sha256(target.encode("utf-8")),
        }
        and "authorization" not in second_headers,
        "safe job-log redirect did not strip authorization and bind its route",
    )

    unsafe_redirects = (
        (f"/repos/{REPOSITORY}/actions/runs/1", target),
        (
            log_path,
            f"https://fixture.blob.core.windows.net/log?token={token.decode('ascii')}",
        ),
        (
            log_path,
            "https://fixture.blob.core.windows.net/log?token="
            + "".join(f"%{byte:02X}" for byte in token),
        ),
        (log_path, "http://fixture.blob.core.windows.net/log"),
        (log_path, "https://user@fixture.blob.core.windows.net/log"),
        (log_path, "https://fixture.example.com/log"),
        (log_path, "https://-fixture.blob.core.windows.net/log"),
        (log_path, "https://é.blob.core.windows.net/log"),
        (log_path, "https://fixture.blob.core.windows.net:444/log"),
        (log_path, "https://fixture.blob.core.windows.net/log#fragment"),
    )
    for path, location in unsafe_redirects:

        def always_redirect(
            request: urllib.request.Request, target_url: str = location
        ) -> Any:
            headers = _FixtureHeaders({"Location": target_url})
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "fixture redirect",
                headers,
                V5.V4.io.BytesIO(b""),
            )

        globals()["open_without_proxy"] = always_redirect
        try:
            _expect_capture_error(
                lambda requested_path=path: request_once(requested_path, token),
                "unsafe job-log redirect fixture was accepted",
            )
        finally:
            globals()["open_without_proxy"] = original_open

    head = "1" * 40
    success_run = _fixture_run("successor_ci", 101, head, "success")
    failure_run = _fixture_run("predecessor_ci", 102, head, "failure")
    require(
        validate_run_document(success_run, "successor_ci", 101, head, "success") == 17
        and validate_run_document(failure_run, "predecessor_ci", 102, head, "failure")
        == 17,
        "valid run-semantic fixtures were rejected",
    )
    run_mutations: list[tuple[dict[str, Any], str, int, str, str]] = []
    mutated = dict(success_run)
    mutated["conclusion"] = "failure"
    run_mutations.append((mutated, "successor_ci", 101, head, "success"))
    mutated = dict(failure_run)
    mutated["conclusion"] = "success"
    run_mutations.append((mutated, "predecessor_ci", 102, head, "failure"))
    mutated = dict(success_run)
    mutated["run_attempt"] = 2
    run_mutations.append((mutated, "successor_ci", 101, head, "success"))
    mutated = dict(success_run)
    mutated["head_sha"] = "2" * 40
    run_mutations.append((mutated, "successor_ci", 101, head, "success"))
    mutated = dict(success_run)
    mutated["status"] = "in_progress"
    run_mutations.append((mutated, "successor_ci", 101, head, "success"))
    for run, role, run_id, expected_head, conclusion in run_mutations:
        _expect_capture_error(
            lambda fixture=run, fixture_role=role, fixture_id=run_id, fixture_head=expected_head, fixture_conclusion=conclusion: (
                validate_run_document(
                    fixture,
                    fixture_role,
                    fixture_id,
                    fixture_head,
                    fixture_conclusion,
                )
            ),
            "invalid run-semantic fixture was accepted",
        )

    success_job = {
        "conclusion": "success",
        "head_sha": head,
        "id": 201,
        "run_attempt": 1,
        "run_id": 101,
        "status": "completed",
    }
    failed_job = {
        "conclusion": "failure",
        "head_sha": head,
        "id": 202,
        "run_attempt": 1,
        "run_id": 102,
        "status": "completed",
    }
    require(
        validate_jobs([success_job], "successor_ci", 101, head, "success") == []
        and validate_jobs([failed_job], "predecessor_ci", 102, head, "failure")
        == [202],
        "valid job-semantic fixtures were rejected",
    )
    _expect_capture_error(
        lambda: validate_jobs([failed_job], "successor_ci", 102, head, "success"),
        "failed job was accepted for successor qualification",
    )
    _expect_capture_error(
        lambda: validate_jobs([success_job], "predecessor_ci", 101, head, "failure"),
        "all-success roster was accepted for predecessor failure",
    )

    return {
        "immutable_v5_primitives_sha256": V5_SHA256,
        "nonretryable_failures_rejected": primitive_result[
            "nonretryable_failures_rejected"
        ],
        "proxy_redirect_handlers_verified": primitive_result[
            "proxy_redirect_handlers_verified"
        ],
        "redirect_mutations_rejected": len(unsafe_redirects),
        "result": "pass",
        "retry_events_observed": primitive_result["retry_events_observed"],
        "run_semantic_mutations_rejected": len(run_mutations) + 2,
        "safe_log_redirects_verified": 1,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v6-capture-self-test/v1",
        "v5_primitive_self_test": "pass",
    }


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
        return (
            dict(PREDECESSOR_RUNS),
            dict(PREDECESSOR_CONCLUSIONS),
            {role: PREDECESSOR_COMMIT for role in PREDECESSOR_RUNS},
            {
                "predecessor_commit": PREDECESSOR_COMMIT,
                "predecessor_tree": PREDECESSOR_TREE,
            },
        )
    require(
        arguments.phase == "successor_qualification",
        "capture phase is required",
    )
    require(
        type(arguments.successor_commit) is str
        and SHA1_RE.fullmatch(arguments.successor_commit) is not None,
        "successor commit is malformed",
    )
    require(
        type(arguments.successor_tree) is str
        and SHA1_RE.fullmatch(arguments.successor_tree) is not None,
        "successor tree is malformed",
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
            "predecessor_commit": PREDECESSOR_COMMIT,
            "predecessor_tree": PREDECESSOR_TREE,
            "successor_commit": arguments.successor_commit,
            "successor_tree": arguments.successor_tree,
        },
    )


def main() -> int:
    arguments = parse_arguments()
    try:
        require(
            all(key not in os.environ for key in FORBIDDEN_TLS_ENVIRONMENT),
            "ambient TLS-routing or key-log environment is unsupported",
        )
        current_v5 = read_regular(V5_PATH, V5_SIZE_BYTES, 0o644)
        require(
            current_v5 == _V5_RAW and sha256(current_v5) == V5_SHA256,
            "immutable v5 primitive source changed after bound import",
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
            len(set(runs.values())) == len(runs),
            "run IDs must be globally unique within the phase",
        )
        token = read_token(arguments.token_fd)
        script_raw = read_regular(SCRIPT, 1024 * 1024, 0o644)
        captures: list[dict[str, Any]] = []
        retry_events: list[dict[str, Any]] = []
        repository_ids: list[int] = []
        failed_by_role: dict[str, list[int]] = {}
        for repetition in (1, 2):
            for role in sorted(runs):
                artifacts, failed_job_ids, repository_id = capture_run(
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
                previous_failed = failed_by_role.setdefault(role, failed_job_ids)
                require(
                    previous_failed == failed_job_ids,
                    f"{role} failed-job identity changed between repetitions",
                )
                capture_artifacts(
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
                    capture_failed_logs(
                        role,
                        failed_job_ids,
                        token,
                        repetition,
                        captures,
                        retry_events,
                    )
                if role == "successor_codeql":
                    capture_codeql(
                        heads[role],
                        token,
                        repetition,
                        captures,
                        retry_events,
                    )
        require(
            len(repository_ids) == len(runs) * 2 and len(set(repository_ids)) == 1,
            "captured runs disagree on repository numeric identity",
        )
        if arguments.phase == "predecessor_failure":
            require(
                failed_by_role["predecessor_ci"] != []
                and failed_by_role["predecessor_contract"] != []
                and failed_by_role["predecessor_codeql"] == [],
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
            "immutable_v5_primitives": {
                "path": V5_RELATIVE,
                "sha256": V5_SHA256,
                "size_bytes": V5_SIZE_BYTES,
            },
            "nonimplications": NONIMPLICATIONS,
            "phase": arguments.phase,
            "repository": REPOSITORY,
            "retry_events": retry_events,
            "runs": runs,
            "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v6",
            "schema_revision": 6,
            "subject": subject,
        }
        require(
            len(captures) <= MAX_CAPTURE_ROWS,
            "capture response count exceeds bound",
        )
        retained_body_bytes = sum(row["body_size_bytes"] for row in captures)
        require(
            retained_body_bytes <= MAX_CAPTURE_BODY_BYTES,
            "retained provider bodies exceed the serialized-capture budget",
        )
        rendered = canonical_json(result)
        require(len(rendered) <= MAX_CAPTURE_BYTES, "capture document exceeds bound")
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
