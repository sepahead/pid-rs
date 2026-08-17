#!/usr/bin/env python3
"""Capture the bounded raw GitHub observations for the composite-v4 receipt.

On success the command writes one canonical JSON document to stdout. Callers must discard stdout
on any nonzero exit. It does
not write the repository, infer scientific validity, or authenticate GitHub's
claims.  Supply the token on an already-open descriptor, never in argv.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
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
        "ERROR: capture-ksg-m1a-composite-v4.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v4.py"
REPOSITORY = "sepahead/pid-rs"
BASE_COMMIT = "bc3aa80fb6025e709c2906a08bce25a4fac40578"
BASE_TREE = "7d87f87953a42edb91e40880d918471c7cbe4414"
RECOVERY_ANALYSIS_IDS = (
    1617732991,
    1617732745,
    1617735963,
    1617735749,
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BODY_BYTES = 22 * 1024 * 1024
MAX_CAPTURE_ROWS = 4096
MAX_PAGES = 64
MAX_TOKEN_BYTES = 4096
API_ROOT = "https://api.github.com"
REDIRECT_HOST_SUFFIXES = (
    ".blob.core.windows.net",
    ".githubusercontent.com",
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


class CaptureError(RuntimeError):
    """The bounded capture could not be completed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise CaptureError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (RecursionError, TypeError, ValueError) as error:
        raise CaptureError(f"cannot canonicalize capture: {error}") from None
    return (rendered + "\n").encode("ascii")


def retain_capture(captures: list[dict[str, Any]], row: dict[str, Any]) -> None:
    require(len(captures) < MAX_CAPTURE_ROWS, "capture response count exceeds bound")
    body_size = row.get("body_size_bytes")
    require(type(body_size) is int and body_size >= 0, "capture body size changed")
    retained = sum(item["body_size_bytes"] for item in captures)
    require(
        retained + body_size <= MAX_CAPTURE_BODY_BYTES,
        "retained provider bodies exceed the serialized-capture budget",
    )
    captures.append(row)


def strict_json(raw: bytes, label: str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{label} contains duplicate key {key!r}")
            value[key] = item
        return value

    def integer(token: str) -> int:
        require(len(token.lstrip("-")) <= 32, f"{label} integer token is oversized")
        return int(token)

    def reject_float(_token: str) -> Any:
        raise CaptureError(f"{label} contains a floating-point token")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique,
            parse_int=integer,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as error:
        raise CaptureError(f"cannot parse {label}: {error}") from None


def read_regular(path: Path, maximum: int, mode: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise CaptureError(f"cannot stat {path}: {error}") from None
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == mode
        and 0 < before.st_size <= maximum,
        f"unsafe file metadata: {path}",
    )
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as error:
        raise CaptureError(f"cannot open {path}: {error}") from None
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
            f"opened file identity changed: {path}",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", f"short read: {path}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"file grew during read: {path}")
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
    require(
        all(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field)
            for field in identity
        ),
        f"file identity changed during read: {path}",
    )
    return b"".join(chunks)


def read_token(descriptor: int) -> bytes:
    require(descriptor >= 3, "token descriptor must be 3 or greater")
    try:
        raw = os.read(descriptor, MAX_TOKEN_BYTES + 1)
        require(os.read(descriptor, 1) == b"", "token descriptor exceeds bound")
    except OSError as error:
        raise CaptureError(f"cannot read token descriptor: {error}") from None
    token = raw.strip()
    require(
        0 < len(token) <= MAX_TOKEN_BYTES
        and b"\n" not in token
        and b"\r" not in token
        and all(0x21 <= byte <= 0x7E for byte in token),
        "token descriptor is not one bounded printable token",
    )
    return token


def bounded_response(stream: Any) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = stream.read(min(1024 * 1024, MAX_RESPONSE_BYTES + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        require(total <= MAX_RESPONSE_BYTES, "provider response exceeds bound")
        chunks.append(chunk)
    return b"".join(chunks)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def open_without_proxy(request: urllib.request.Request) -> Any:
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
    )
    return opener.open(request, timeout=45)


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
            "User-Agent": "pid-rs-composite-v4-capture",
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
        require(type(location) is str, "artifact redirect has no Location header")
        require(
            re.fullmatch(
                rf"/repos/{re.escape(REPOSITORY)}/actions/artifacts/[0-9]+/zip", path
            )
            is not None,
            "non-artifact request attempted to redirect",
        )
        require(
            token.decode("ascii") not in location,
            "artifact redirect URL contains the authentication token",
        )
        parsed = urllib.parse.urlsplit(location)
        try:
            target_port = parsed.port
        except ValueError as port_error:
            raise CaptureError(
                f"artifact redirect has an invalid port: {port_error}"
            ) from None
        require(
            parsed.scheme == "https"
            and parsed.hostname is not None
            and any(
                parsed.hostname.endswith(suffix) for suffix in REDIRECT_HOST_SUFFIXES
            )
            and parsed.username is None
            and parsed.password is None
            and target_port in {None, 443}
            and parsed.fragment == "",
            "artifact redirect leaves the reviewed HTTPS host set",
        )
        redirect = {
            "status_code": error.code,
            "target_host": parsed.hostname,
            "target_url_sha256": sha256(location.encode("utf-8")),
        }
        redirected = urllib.request.Request(
            location,
            headers={"User-Agent": "pid-rs-composite-v4-capture"},
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
            time.sleep(0.25 * (2 ** (attempt - 1)))
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
            time.sleep(0.25 * (2 ** (attempt - 1)))
            continue
        require(status_code == 200, f"provider status changed for {logical_request}")
        require(token not in body, "provider response contains the token")
        if response_kind == "json":
            strict_json(body, logical_request)
            require(
                media_type in {"application/json", "application/octet-stream"},
                "JSON media type changed",
            )
        else:
            require(
                media_type in {"application/zip", "application/octet-stream"},
                "ZIP media type changed",
            )
            require(body.startswith(b"PK"), "artifact response is not a ZIP archive")
        return (
            {
                "body_base64": base64.b64encode(body).decode("ascii"),
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


def capture_run(
    role: str,
    run_id: int,
    head: str,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    # The run-wide artifact endpoint has no attempt selector.  Capturing the latest-run
    # resource and requiring run_attempt == 1 prevents a later rerun's artifacts from being
    # silently paired with an older attempt-1 run body.
    run_path = f"/repos/{REPOSITORY}/actions/runs/{run_id}"
    row, body = fetch(
        run_path, token, f"{role}_run", repetition, 0, "json", retry_events
    )
    run = strict_json(body, f"{role} run")
    repository = run.get("repository") if type(run) is dict else None
    head_repository = run.get("head_repository") if type(run) is dict else None
    repository_id = repository.get("id") if type(repository) is dict else None
    require(
        type(run) is dict
        and run.get("id") == run_id
        and type(run.get("id")) is int
        and run.get("run_attempt") == 1
        and type(run.get("run_attempt")) is int
        and run.get("head_sha") == head
        and run.get("head_branch") == "main"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and type(repository) is dict
        and repository.get("full_name") == REPOSITORY
        and type(repository_id) is int
        and repository_id > 0
        and type(head_repository) is dict
        and head_repository.get("full_name") == REPOSITORY
        and head_repository.get("id") == repository_id
        and type(head_repository.get("id")) is int,
        f"{role} run is not the exact terminal-success subject",
    )
    retain_capture(captures, row)
    paged(
        f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs",
        f"{role}_jobs",
        "jobs",
        token,
        repetition,
        captures,
        retry_events,
    )
    artifacts = paged(
        f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts",
        f"{role}_artifacts",
        "artifacts",
        token,
        repetition,
        captures,
        retry_events,
    )
    return artifacts, repository_id


class _FixtureHeaders(dict[str, str]):
    def get_content_type(self) -> str:
        return self.get("Content-Type", "application/octet-stream")


class _FixtureResponse:
    def __init__(self, body: bytes, media_type: str = "application/json") -> None:
        self._stream = io.BytesIO(body)
        self.headers = _FixtureHeaders({"Content-Type": media_type})
        self.status = 200

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __enter__(self) -> _FixtureResponse:
        return self

    def __exit__(self, *_arguments: Any) -> None:
        self._stream.close()


def offline_self_test() -> dict[str, Any]:
    token = b"fixture-secret-token"
    artifact_path = f"/repos/{REPOSITORY}/actions/artifacts/17/zip"
    target = "https://fixture.blob.core.windows.net/archive?sig=redacted"
    original_build_opener = urllib.request.build_opener
    opener_observation: dict[str, Any] = {}

    class _FixtureOpener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> Any:
            opener_observation["request"] = request
            opener_observation["timeout"] = timeout
            return _FixtureResponse(b"{}\n")

    def fixture_build_opener(*handlers: Any) -> _FixtureOpener:
        opener_observation["handlers"] = handlers
        return _FixtureOpener()

    urllib.request.build_opener = fixture_build_opener
    try:
        probe_request = urllib.request.Request(f"{API_ROOT}/rate_limit")
        with open_without_proxy(probe_request) as probe_response:
            require(
                bounded_response(probe_response) == b"{}\n",
                "proxy-isolation fixture response changed",
            )
    finally:
        urllib.request.build_opener = original_build_opener
    handlers = opener_observation.get("handlers")
    require(
        type(handlers) is tuple
        and len(handlers) == 2
        and isinstance(handlers[0], urllib.request.ProxyHandler)
        and handlers[0].proxies == {}
        and isinstance(handlers[1], NoRedirect)
        and opener_observation.get("request") is probe_request
        and opener_observation.get("timeout") == 45,
        "proxy or redirect suppression fixture changed",
    )
    original_open = globals()["open_without_proxy"]
    observed_requests: list[urllib.request.Request] = []

    def redirect_then_zip(request: urllib.request.Request) -> Any:
        observed_requests.append(request)
        if len(observed_requests) == 1:
            headers = _FixtureHeaders({"Location": target})
            raise urllib.error.HTTPError(
                request.full_url, 302, "fixture redirect", headers, io.BytesIO(b"")
            )
        return _FixtureResponse(b"PK\x03\x04fixture", "application/zip")

    globals()["open_without_proxy"] = redirect_then_zip
    try:
        status, media_type, body, redirect = request_once(artifact_path, token)
    finally:
        globals()["open_without_proxy"] = original_open
    second_headers = {
        key.lower(): value for key, value in observed_requests[1].header_items()
    }
    require(
        status == 200
        and media_type == "application/zip"
        and body.startswith(b"PK")
        and redirect
        == {
            "status_code": 302,
            "target_host": "fixture.blob.core.windows.net",
            "target_url_sha256": sha256(target.encode("utf-8")),
        }
        and "authorization" not in second_headers,
        "artifact redirect did not strip authorization or bind its route",
    )

    def rejected_redirect(path: str, location: str) -> None:
        def always_redirect(request: urllib.request.Request) -> Any:
            headers = _FixtureHeaders({"Location": location})
            raise urllib.error.HTTPError(
                request.full_url, 302, "fixture redirect", headers, io.BytesIO(b"")
            )

        globals()["open_without_proxy"] = always_redirect
        try:
            request_once(path, token)
        except CaptureError:
            return
        finally:
            globals()["open_without_proxy"] = original_open
        raise CaptureError("unsafe redirect fixture was accepted")

    rejected_redirect(
        f"/repos/{REPOSITORY}/actions/runs/1",
        target,
    )
    rejected_redirect(
        artifact_path,
        f"https://fixture.blob.core.windows.net/archive?token={token.decode('ascii')}",
    )
    rejected_redirect(
        artifact_path,
        "https://fixture.blob.core.windows.net:444/archive",
    )

    original_request_once = globals()["request_once"]
    original_sleep = time.sleep
    attempts = 0

    def retry_once(_path: str, _token: bytes) -> tuple[int, str, bytes, None]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise urllib.error.HTTPError(
                API_ROOT,
                503,
                "fixture unavailable",
                _FixtureHeaders(),
                io.BytesIO(b"busy"),
            )
        return 200, "application/json", b"{}\n", None

    globals()["request_once"] = retry_once
    time.sleep = lambda _seconds: None
    retry_events: list[dict[str, Any]] = []
    try:
        row, raw = fetch(
            f"/repos/{REPOSITORY}/actions/runs/1",
            token,
            "migration_ci_run",
            1,
            0,
            "json",
            retry_events,
        )
    finally:
        globals()["request_once"] = original_request_once
        time.sleep = original_sleep
    require(
        attempts == 2
        and raw == b"{}\n"
        and row["status_code"] == 200
        and retry_events
        == [
            {
                "attempt": 1,
                "category": "http_503",
                "logical_request": "migration_ci_run",
                "page": 0,
                "path": f"/repos/{REPOSITORY}/actions/runs/1",
                "repetition": 1,
                "response_sha256": sha256(b"busy"),
                "response_size_bytes": 4,
            }
        ],
        "bounded retry fixture changed",
    )

    denied_attempts = 0

    def deny_once(_path: str, _token: bytes) -> tuple[int, str, bytes, None]:
        nonlocal denied_attempts
        denied_attempts += 1
        raise urllib.error.HTTPError(
            API_ROOT,
            403,
            "fixture forbidden",
            _FixtureHeaders(),
            io.BytesIO(b"forbidden"),
        )

    globals()["request_once"] = deny_once
    denied_events: list[dict[str, Any]] = []
    try:
        try:
            fetch(
                f"/repos/{REPOSITORY}/actions/runs/1",
                token,
                "migration_ci_run",
                1,
                0,
                "json",
                denied_events,
            )
        except CaptureError:
            pass
        else:
            raise CaptureError("authorization failure fixture was accepted")
    finally:
        globals()["request_once"] = original_request_once
    require(
        denied_attempts == 1 and denied_events == [],
        "authorization failure was retried or retained as an observation",
    )
    return {
        "redirect_mutations_rejected": 3,
        "nonretryable_failures_rejected": 1,
        "proxy_redirect_handlers_verified": 1,
        "result": "pass",
        "retry_events_observed": 1,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v4-capture-self-test/v1",
    }


def capture_codeql(
    role: str,
    token: bytes,
    repetition: int,
    captures: list[dict[str, Any]],
    retry_events: list[dict[str, Any]],
) -> None:
    if role == "recovery_codeql":
        for analysis_id in RECOVERY_ANALYSIS_IDS:
            path = f"/repos/{REPOSITORY}/code-scanning/analyses/{analysis_id}"
            row, _body = fetch(
                path,
                token,
                f"{role}_analysis_{analysis_id}",
                repetition,
                0,
                "json",
                retry_events,
            )
            retain_capture(captures, row)
    else:
        paged(
            f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
            f"{role}_analyses",
            None,
            token,
            repetition,
            captures,
            retry_events,
        )
    for state in ("open", "dismissed", "fixed"):
        paged(
            f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}",
            f"{role}_alerts_{state}",
            None,
            token,
            repetition,
            captures,
            retry_events,
        )


def capture_artifacts(
    role: str,
    artifacts: list[dict[str, Any]],
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
        require(
            type(artifact_id) is int and artifact_id > 0, f"{role} artifact ID changed"
        )
        ids.append(artifact_id)
        name = artifact.get("name")
        workflow_run = artifact.get("workflow_run")
        require(
            type(name) is str
            and name != ""
            and type(workflow_run) is dict
            and workflow_run.get("id") == run_id
            and type(workflow_run.get("id")) is int
            and workflow_run.get("head_sha") == head
            and workflow_run.get("head_branch") == "main"
            and workflow_run.get("repository_id") == repository_id
            and type(workflow_run.get("repository_id")) is int
            and workflow_run.get("head_repository_id") == repository_id
            and type(workflow_run.get("head_repository_id")) is int,
            f"{role} artifact is not joined to the requested run/head",
        )
        names.append(name)
    require(len(ids) == len(set(ids)), f"{role} artifact IDs are duplicated")
    require(len(names) == len(set(names)), f"{role} artifact names are duplicated")
    if role.endswith("_ci"):
        expected_names = {
            "coverage-lcov",
            f"post-commit-source-state-v2-{head}",
            "workspace-sbom",
        }
    elif role.endswith("_codeql"):
        expected_names = set()
    else:
        expected_names = {f"ksg-m1a-composite-v4-static-{head}"}
    require(set(names) == expected_names, f"{role} artifact inventory changed")
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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--contract-commit")
    parser.add_argument("--contract-tree")
    parser.add_argument("--migration-ci-run", type=int)
    parser.add_argument("--migration-codeql-run", type=int)
    parser.add_argument("--migration-contract-run", type=int)
    parser.add_argument("--token-fd", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        require(
            all(key not in os.environ for key in FORBIDDEN_TLS_ENVIRONMENT),
            "ambient TLS-routing or key-log environment is unsupported",
        )
        if arguments.self_test:
            require(
                all(
                    value is None
                    for value in (
                        arguments.contract_commit,
                        arguments.contract_tree,
                        arguments.migration_ci_run,
                        arguments.migration_codeql_run,
                        arguments.migration_contract_run,
                    )
                ),
                "offline self-test does not accept capture subjects",
            )
            sys.stdout.buffer.write(canonical_json(offline_self_test()))
            return 0
        require(
            type(arguments.contract_commit) is str
            and SHA1_RE.fullmatch(arguments.contract_commit) is not None,
            "contract commit is malformed",
        )
        require(
            type(arguments.contract_tree) is str
            and SHA1_RE.fullmatch(arguments.contract_tree) is not None,
            "contract tree is malformed",
        )
        run_ids = {
            "migration_ci": arguments.migration_ci_run,
            "migration_codeql": arguments.migration_codeql_run,
            "migration_contract": arguments.migration_contract_run,
            "recovery_ci": 31773937366,
            "recovery_codeql": 31773937102,
        }
        require(
            all(type(value) is int and value > 0 for value in run_ids.values())
            and len(set(run_ids.values())) == len(run_ids),
            "run IDs must be positive and globally unique",
        )
        token = read_token(arguments.token_fd)
        script_raw = read_regular(SCRIPT, 1024 * 1024, 0o644)
        captures: list[dict[str, Any]] = []
        retry_events: list[dict[str, Any]] = []
        repository_ids: list[int] = []
        for repetition in (1, 2):
            for role in (
                "recovery_ci",
                "recovery_codeql",
                "migration_ci",
                "migration_codeql",
                "migration_contract",
            ):
                artifacts, repository_id = capture_run(
                    role,
                    run_ids[role],
                    BASE_COMMIT
                    if role.startswith("recovery_")
                    else arguments.contract_commit,
                    token,
                    repetition,
                    captures,
                    retry_events,
                )
                repository_ids.append(repository_id)
                capture_artifacts(
                    role,
                    artifacts,
                    run_ids[role],
                    repository_id,
                    BASE_COMMIT
                    if role.startswith("recovery_")
                    else arguments.contract_commit,
                    token,
                    repetition,
                    captures,
                    retry_events,
                )
                if role.endswith("codeql"):
                    capture_codeql(role, token, repetition, captures, retry_events)
        require(
            len(repository_ids) == 10 and len(set(repository_ids)) == 1,
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
            "nonimplications": [
                "Captured HTTPS response bytes do not authenticate themselves.",
                "Capture time, network completeness, and provider response order are not claimed.",
                "Code-scanning alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to a workflow run or to that run's historical execution window.",
                "A successful hosted run is not mathematical, estimator, or application validation.",
                "The capture makes no claim about any PID functional, estimator, objective, or downstream use.",
            ],
            "repository": REPOSITORY,
            "retry_events": retry_events,
            "runs": run_ids,
            "schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v4",
            "schema_revision": 4,
            "subject": {
                "contract_commit": arguments.contract_commit,
                "contract_tree": arguments.contract_tree,
                "recovery_commit": BASE_COMMIT,
                "recovery_tree": BASE_TREE,
            },
        }
        require(
            len(captures) <= MAX_CAPTURE_ROWS, "capture response count exceeds bound"
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
