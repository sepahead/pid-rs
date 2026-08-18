#!/usr/bin/env python3
"""Capture one bounded, fail-closed local composite-v6 closure observation.

The tool accepts no caller-selected command.  From an exact clean committed C6
checkout it runs exactly ``just ksg-composite-v6`` under a constructed minimal
environment, retains bounded stdout/stderr, checks the repository again, and
writes canonical JSON to a newly created mode-0600 path outside the repository.
The record is operational evidence, not authentication or scientific evidence.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import re
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: capture-ksg-m1a-composite-v6-local-closure.py requires "
        "Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"
C5_COMMIT = "be862b155d710573ec95356fc1cbe9a96a2b83b9"
C6_MESSAGE = "Repair KSG M1a composite v6 contract\n"
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json"
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v6-local-closure.py"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v6.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v6-self-test.py"
JUSTFILE_RELATIVE = "justfile"

COMMAND_ARGV = ("just", "ksg-composite-v6")
COMMAND_TIMEOUT_SECONDS = 14_400
MAX_STREAM_BYTES = 8 * 1024 * 1024
MAX_VERSION_STREAM_BYTES = 64 * 1024
MAX_RECORD_BYTES = 32 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
SECRET_KEY_RE = re.compile(
    r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|COOKIE|AUTHORIZATION|"
    r"API_KEY|PRIVATE_KEY)(?:$|_)",
    re.IGNORECASE,
)
SECRET_OUTPUT_PATTERNS = (
    re.compile(rb"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(rb"(?i)github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"(?i)gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"(?i)(?:password|passwd|secret|credential|api[_-]?key)\s*[=:]\s*\S+"),
    re.compile(rb"/(?:Users|home)/[^/\x00\r\n ]+/"),
)
FORBIDDEN_AMBIENT_KEYS = {
    "ALL_PROXY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GH_TOKEN",
    "GIT_ASKPASS",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "NO_PROXY",
    "OPENAI_API_KEY",
    "SSH_ASKPASS",
}

NORMALIZED_ENVIRONMENT = {
    "GIT_CONFIG_GLOBAL": "<NULL_DEVICE>",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "<SANITIZED_TOOL_PATH>",
    "PYTHONDONTWRITEBYTECODE": "1",
    "TEXMFCACHE": "<PRIVATE_TEMP_TEXMF_CACHE>",
    "TEXMFCONFIG": "<PRIVATE_TEMP_TEXMF_CONFIG>",
    "TEXMFHOME": "<PRIVATE_TEMP_TEXMF_HOME>",
    "TEXMFVAR": "<PRIVATE_TEMP_TEXMF_VAR>",
    "TMPDIR": "<PRIVATE_TEMP_ROOT>",
    "TZ": "UTC",
    "XDG_CACHE_HOME": "<PRIVATE_TEMP_XDG_CACHE>",
    "XDG_CONFIG_HOME": "<PRIVATE_TEMP_XDG_CONFIG>",
    "XDG_DATA_HOME": "<PRIVATE_TEMP_XDG_DATA>",
}

NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C6 checkout and is neither an independent replication nor a first-attempt authority.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude unobserved interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, shell builtins, libraries, TeX helpers, or transitive processes.",
    "The redacted environment-route digest is an opaque correlated capture-time fingerprint, not a publicly recomputable path authority.",
    "HOME is absent from the constructed environment; isolated XDG and TeX roots reduce but do not prove the absence of every passwd-derived user-path fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove that every descendant process was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove that output contains no sensitive information.",
    "The clean endpoints use ordinary Git status plus selected metadata checks; rejecting core.excludesFile removes one ignore-routing overlay, but repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure.",
    "A local closure pass is operational evidence only; it is not PID, KSG, mathematical, scientific, security, application, PDF/UA, renderer-independence, or cross-platform reproducibility evidence.",
]

AUTHORITY_ROLES = {
    JUSTFILE_RELATIVE: "local_command_wiring",
    SCHEMA_RELATIVE: "local_l6_closure_schema",
    SCRIPT_RELATIVE: "bounded_local_l6_closure_capture_tool",
    SELF_TEST_RELATIVE: "composite_v6_hostile_suite",
    CHECKER_RELATIVE: "composite_v6_semantic_gate",
}

TOOL_SPECS = {
    "bash": ("--version",),
    "chktex": ("--version",),
    "fc-match": ("--version",),
    "git": ("--version",),
    "just": ("--version",),
    "lacheck": ("--version",),
    "latexmk": ("--version",),
    "lualatex": ("--version",),
    "pdfinfo": ("-v",),
    "pdffonts": ("-v",),
    "pdftocairo": ("-v",),
    "pdftotext": ("-v",),
    "python3": ("--version",),
    "rsvg-convert": ("--version",),
    "xmllint": ("--version",),
}


class CaptureError(RuntimeError):
    """A bounded local-capture contract failed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise CaptureError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def read_regular(path: Path, maximum: int, mode: int | None = None) -> bytes:
    metadata = path.lstat()
    require(
        stat.S_ISREG(metadata.st_mode)
        and not path.is_symlink()
        and metadata.st_nlink == 1
        and 0 < metadata.st_size <= maximum,
        "required authority is not one bounded regular file",
    )
    if mode is not None:
        require(stat.S_IMODE(metadata.st_mode) == mode, "authority mode changed")
    raw = path.read_bytes()
    require(len(raw) == metadata.st_size, "authority changed while read")
    return raw


def byte_binding(raw: bytes) -> dict[str, Any]:
    return {
        "body_base64": base64.b64encode(raw).decode("ascii"),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def decode_binding(value: Any, label: str, maximum: int) -> bytes:
    require(
        type(value) is dict
        and set(value) == {"body_base64", "sha256", "size_bytes"}
        and type(value["body_base64"]) is str
        and type(value["sha256"]) is str
        and SHA256_RE.fullmatch(value["sha256"]) is not None
        and type(value["size_bytes"]) is int
        and 0 <= value["size_bytes"] <= maximum,
        f"{label} binding shape changed",
    )
    try:
        raw = base64.b64decode(value["body_base64"], validate=True)
    except (ValueError, base64.binascii.Error):
        raise CaptureError(f"{label} is not canonical base64") from None
    require(
        base64.b64encode(raw).decode("ascii") == value["body_base64"]
        and len(raw) == value["size_bytes"]
        and sha256(raw) == value["sha256"],
        f"{label} byte binding changed",
    )
    return raw


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def reject_ambient_secrets(environment: dict[str, str]) -> None:
    for key, value in environment.items():
        if value and (
            key.upper() in FORBIDDEN_AMBIENT_KEYS or SECRET_KEY_RE.search(key)
        ):
            raise CaptureError("ambient secret-bearing environment is unsupported")


def reject_sensitive_output(
    raw: bytes, private_prefixes: tuple[bytes, ...], label: str
) -> None:
    require(len(raw) <= MAX_STREAM_BYTES, f"{label} exceeds the public-output bound")
    for prefix in private_prefixes:
        if prefix and prefix in raw:
            raise CaptureError(f"{label} contains a private absolute path")
    if any(pattern.search(raw) is not None for pattern in SECRET_OUTPUT_PATTERNS):
        raise CaptureError(f"{label} contains a credential-like pattern")


def fixed_path_directories() -> tuple[Path, ...]:
    passwd_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    candidates = [
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin"),
        Path("/Library/TeX/texbin"),
        Path("/usr/bin"),
        Path("/bin"),
        Path("/usr/sbin"),
        Path("/sbin"),
        passwd_home / ".elan" / "bin",
    ]
    values: list[Path] = []
    for candidate in candidates:
        if candidate.is_dir() and candidate not in values:
            values.append(candidate)
    require(values != [], "sanitized tool path is empty")
    return tuple(values)


def resolve_executable(name: str, directories: tuple[Path, ...]) -> Path:
    require(re.fullmatch(r"[A-Za-z0-9._+-]+", name) is not None, "tool name changed")
    for directory in directories:
        candidate = directory / name
        if (
            os.access(candidate, os.X_OK)
            and candidate.exists()
            and not candidate.is_dir()
        ):
            return candidate
    raise CaptureError(f"required executable is absent: {name}")


def normalized_tool_route(path: Path) -> str:
    parent = path.parent
    prefixes = {
        Path("/opt/homebrew/bin"): "<HOMEBREW_BIN>",
        Path("/usr/local/bin"): "<USR_LOCAL_BIN>",
        Path("/Library/TeX/texbin"): "<TEXLIVE_BIN>",
        Path("/usr/bin"): "<SYSTEM_BIN>",
        Path("/bin"): "<SYSTEM_BIN>",
        Path("/usr/sbin"): "<SYSTEM_BIN>",
        Path("/sbin"): "<SYSTEM_BIN>",
    }
    require(parent in prefixes, "versioned tool is outside the reviewed route set")
    return f"{prefixes[parent]}/{path.name}"


def minimal_environment(
    directories: tuple[Path, ...], temporary_root: Path
) -> tuple[dict[str, str], str]:
    private_roots = {
        "TEXMFCACHE": temporary_root / "texmf-cache",
        "TEXMFCONFIG": temporary_root / "texmf-config",
        "TEXMFHOME": temporary_root / "texmf-home",
        "TEXMFVAR": temporary_root / "texmf-var",
        "XDG_CACHE_HOME": temporary_root / "xdg-cache",
        "XDG_CONFIG_HOME": temporary_root / "xdg-config",
        "XDG_DATA_HOME": temporary_root / "xdg-data",
    }
    for path in private_roots.values():
        path.mkdir(mode=0o700)
        metadata = path.lstat()
        require(
            stat.S_ISDIR(metadata.st_mode)
            and not path.is_symlink()
            and stat.S_IMODE(metadata.st_mode) == 0o700,
            "private configuration root is not one mode-0700 directory",
        )
    actual = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join(os.fspath(path) for path in directories),
        "PYTHONDONTWRITEBYTECODE": "1",
        **{key: os.fspath(path) for key, path in private_roots.items()},
        "TMPDIR": os.fspath(temporary_root),
        "TZ": "UTC",
    }
    require(set(actual) == set(NORMALIZED_ENVIRONMENT), "minimal environment changed")
    require(
        all(
            type(key) is str
            and type(value) is str
            and key
            and "\x00" not in key + value
            and "\r" not in key + value
            and "\n" not in key + value
            and SECRET_KEY_RE.search(key) is None
            for key, value in actual.items()
        ),
        "minimal environment contains an unsafe key or value",
    )
    routes = canonical_json(
        {
            "GIT_CONFIG_GLOBAL": actual["GIT_CONFIG_GLOBAL"],
            "PATH": actual["PATH"],
            **{key: actual[key] for key in sorted(private_roots)},
            "TMPDIR": actual["TMPDIR"],
        }
    )
    return actual, sha256(routes)


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()


def run_bounded(
    argv: tuple[str, ...],
    executable: Path,
    environment: dict[str, str],
    cwd: Path,
    timeout_seconds: float,
    maximum_stream_bytes: int,
    post_exit_drain_seconds: float = 2.0,
) -> tuple[int, bytes, bytes, bool]:
    require(argv and argv[0] == executable.name, "process argv/executable join changed")
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=environment,
        executable=os.fspath(executable),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
    )
    require(
        process.stdout is not None and process.stderr is not None, "pipe setup failed"
    )
    selector = selectors.DefaultSelector()
    stdout_fd = process.stdout.fileno()
    stderr_fd = process.stderr.fileno()
    os.set_blocking(stdout_fd, False)
    os.set_blocking(stderr_fd, False)
    streams = {stdout_fd: bytearray(), stderr_fd: bytearray()}
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    drain_deadline: float | None = None
    try:
        while selector.get_map():
            now = time.monotonic()
            if not timed_out and process.poll() is None and now >= deadline:
                timed_out = True
                terminate_process_group(process)
                drain_deadline = now + post_exit_drain_seconds
            if process.poll() is not None and drain_deadline is None:
                drain_deadline = now + post_exit_drain_seconds
            if drain_deadline is not None and now >= drain_deadline:
                terminate_process_group(process)
                for key in list(selector.get_map().values()):
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                raise CaptureError(
                    "subprocess pipe remained open beyond the drain bound"
                )
            events = selector.select(0.1)
            for key, _mask in events:
                try:
                    chunk = os.read(key.fd, 65_536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                destination = streams[key.fd]
                destination.extend(chunk)
                if len(destination) > maximum_stream_bytes:
                    terminate_process_group(process)
                    raise CaptureError(
                        "subprocess output exceeds the bounded stream size"
                    )
        return_code = process.wait(timeout=5)
    except Exception:
        terminate_process_group(process)
        process.wait(timeout=5)
        raise
    finally:
        selector.close()
    return return_code, bytes(streams[stdout_fd]), bytes(streams[stderr_fd]), timed_out


def internal_command(
    executable: Path,
    argv: tuple[str, ...],
    environment: dict[str, str],
    *,
    allowed_exit_codes: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes, bytes]:
    code, stdout, stderr, timed_out = run_bounded(
        argv,
        executable,
        environment,
        ROOT,
        60,
        MAX_VERSION_STREAM_BYTES,
    )
    require(
        not timed_out and code in allowed_exit_codes, "bounded internal command failed"
    )
    return code, stdout, stderr


def git_output(git_path: Path, environment: dict[str, str], *arguments: str) -> bytes:
    _code, stdout, stderr = internal_command(
        git_path,
        ("git", *arguments),
        environment,
    )
    require(stderr == b"", "isolated Git command wrote stderr")
    return stdout


def parse_commit_envelope(raw: bytes) -> tuple[str, str, str]:
    require(b"\n\n" in raw, "commit object has no message boundary")
    headers, message = raw.split(b"\n\n", 1)
    lines = headers.splitlines()
    tree_lines = [line for line in lines if line.startswith(b"tree ")]
    parent_lines = [line for line in lines if line.startswith(b"parent ")]
    require(
        len(tree_lines) == 1
        and len(parent_lines) == 1
        and not any(line.startswith((b"gpgsig ", b"gpgsig-sha256 ")) for line in lines),
        "C6 commit is not one unsigned direct-child envelope",
    )
    try:
        tree = tree_lines[0][5:].decode("ascii")
        parent = parent_lines[0][7:].decode("ascii")
        message_text = message.decode("utf-8")
    except UnicodeDecodeError:
        raise CaptureError("C6 commit envelope encoding changed") from None
    require(
        SHA1_RE.fullmatch(tree) is not None
        and parent == C5_COMMIT
        and message_text == C6_MESSAGE,
        "C6 commit tree, parent, or message changed",
    )
    return tree, parent, message_text


def require_absent(path: Path, label: str) -> None:
    require(not path.exists() and not path.is_symlink(), f"{label} is present")


def validate_repository_config_bytes(raw: bytes) -> None:
    lowered = raw.lower()
    require(
        all(
            token not in lowered
            for token in (
                b"[include",
                b"worktree =",
                b"hookspath =",
                b"attributesfile =",
                b"excludesfile =",
            )
        ),
        "repository config contains an unsupported routing overlay",
    )


def validate_repository_config_names(raw: bytes) -> None:
    try:
        config_names = raw.decode("ascii").splitlines()
    except UnicodeDecodeError:
        raise CaptureError("repository config key encoding changed") from None
    require(
        all(config_names) and len(config_names) == len(set(config_names)),
        "repository config key set is empty or duplicated",
    )
    forbidden_names = {
        "core.attributesfile",
        "core.excludesfile",
        "core.fsmonitor",
        "core.hookspath",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "core.splitindex",
        "core.untrackedcache",
        "core.worktree",
        "extensions.objectformat",
        "extensions.partialclone",
        "extensions.refstorage",
        "extensions.worktreeconfig",
        "index.sparse",
    }
    require(
        all(
            name.lower() not in forbidden_names
            and not name.lower().startswith(
                (
                    "alias.",
                    "filter.",
                    "include.",
                    "includeif.",
                    "submodule.",
                    "url.",
                )
            )
            and not (
                name.lower().startswith("remote.")
                and name.lower().endswith(".promisor")
            )
            for name in config_names
        ),
        "repository config key set contains an unsupported routing overlay",
    )


def validate_effective_excludes_probe(code: int, stdout: bytes, stderr: bytes) -> None:
    require(
        code == 1 and stdout == b"" and stderr == b"",
        "effective local core.excludesFile route is present",
    )


def validate_repository_local_rules(raw: bytes, label: str) -> None:
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise CaptureError(f"{label} is not UTF-8") from None
    effective = [
        line for line in decoded.splitlines() if line and not line.startswith("#")
    ]
    require(not effective, f"{label} contains effective repository-local rules")


def validate_optional_repository_rule_file(path: Path, label: str) -> None:
    if not path.exists() and not path.is_symlink():
        return
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and 0 <= before.st_size <= 1024 * 1024,
        f"{label} is not one bounded mode-0644 regular file",
    )
    raw = path.read_bytes()
    after = path.lstat()
    require(
        len(raw) == before.st_size
        and (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ),
        f"{label} changed while read",
    )
    validate_repository_local_rules(raw, label)


def repository_snapshot(git_path: Path, environment: dict[str, str]) -> dict[str, Any]:
    git_directory = ROOT / ".git"
    require(
        git_directory.is_dir() and not git_directory.is_symlink(),
        "repository does not use one real canonical .git directory",
    )
    require_absent(git_directory / "config.worktree", "Git worktree config overlay")
    require_absent(git_directory / "commondir", "Git common-directory redirect")
    require_absent(git_directory / "info" / "grafts", "Git graft overlay")
    require_absent(git_directory / "objects" / "info" / "alternates", "Git alternates")
    require_absent(
        git_directory / "objects" / "info" / "http-alternates",
        "Git HTTP alternates",
    )
    require_absent(git_directory / "shallow", "shallow history boundary")
    validate_optional_repository_rule_file(
        git_directory / "info" / "attributes", "Git info attributes"
    )
    validate_optional_repository_rule_file(
        git_directory / "info" / "exclude", "Git info exclude"
    )
    config_raw = read_regular(git_directory / "config", 1024 * 1024)
    validate_repository_config_bytes(config_raw)
    config_names_raw = git_output(
        git_path,
        environment,
        "config",
        "--local",
        "--no-includes",
        "--name-only",
        "--list",
    )
    validate_repository_config_names(config_names_raw)
    excludes_code, excludes_stdout, excludes_stderr = internal_command(
        git_path,
        (
            "git",
            "config",
            "--local",
            "--no-includes",
            "--get-all",
            "core.excludesFile",
        ),
        environment,
        allowed_exit_codes=frozenset({0, 1}),
    )
    validate_effective_excludes_probe(excludes_code, excludes_stdout, excludes_stderr)
    toplevel = git_output(git_path, environment, "rev-parse", "--show-toplevel")
    git_dir_observed = git_output(
        git_path, environment, "rev-parse", "--absolute-git-dir"
    )
    common_dir_observed = git_output(
        git_path, environment, "rev-parse", "--git-common-dir"
    )
    object_format = git_output(
        git_path, environment, "rev-parse", "--show-object-format=storage"
    )
    require(
        Path(os.fsdecode(toplevel.rstrip(b"\n"))).resolve() == ROOT.resolve()
        and Path(os.fsdecode(git_dir_observed.rstrip(b"\n"))).resolve()
        == git_directory.resolve(),
        "Git repository root routing changed",
    )
    common_path = Path(os.fsdecode(common_dir_observed.rstrip(b"\n")))
    if not common_path.is_absolute():
        common_path = ROOT / common_path
    require(
        common_path.resolve() == git_directory.resolve() and object_format == b"sha1\n",
        "Git common directory or object format changed",
    )
    head_raw = git_output(git_path, environment, "rev-parse", "--verify", "HEAD")
    try:
        head = head_raw.strip().decode("ascii")
    except UnicodeDecodeError:
        raise CaptureError("HEAD encoding changed") from None
    require(SHA1_RE.fullmatch(head) is not None, "HEAD is malformed")
    commit_raw = git_output(git_path, environment, "cat-file", "commit", head)
    tree, parent, message = parse_commit_envelope(commit_raw)
    replacements = git_output(
        git_path,
        environment,
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace/",
    )
    require(replacements == b"", "Git replacement refs are present")
    status_raw = git_output(
        git_path,
        environment,
        "status",
        "--porcelain=v2",
        "--untracked-files=all",
        "-z",
    )
    require(status_raw == b"", "tracked or untracked worktree state is not empty")
    return {
        "alternates": "absent",
        "common_dir": "<REPOSITORY_ROOT>/.git",
        "config_overlays": "absent",
        "git_dir": "<REPOSITORY_ROOT>/.git",
        "grafts": "absent",
        "head": head,
        "http_alternates": "absent",
        "info_attributes_rules": "absent",
        "info_exclude_rules": "absent",
        "message": message,
        "object_format": "sha1",
        "observed_at": utc_now(),
        "parent": parent,
        "replacement_refs": [],
        "shallow": "absent",
        "status": byte_binding(status_raw),
        "tree": tree,
        "worktree_root": "<REPOSITORY_ROOT>",
    }


def authority_descriptors(
    git_path: Path, environment: dict[str, str], head: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative, role in sorted(AUTHORITY_ROLES.items()):
        raw = read_regular(ROOT / relative, 2 * 1024 * 1024, 0o644)
        committed = git_output(git_path, environment, "show", f"{head}:{relative}")
        require(raw == committed, "local authority differs from the C6 tree")
        result.append(
            {
                "path": relative,
                "role": role,
                "sha256": sha256(raw),
                "size_bytes": len(raw),
            }
        )
    return result


def toolchain_observation(
    directories: tuple[Path, ...],
    environment: dict[str, str],
    private_prefixes: tuple[bytes, ...],
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    records: list[dict[str, Any]] = []
    resolved: dict[str, Path] = {}
    for name, version_arguments in sorted(TOOL_SPECS.items()):
        executable = resolve_executable(name, directories)
        resolved[name] = executable
        actual = executable.resolve(strict=True)
        raw = read_regular(actual, MAX_EXECUTABLE_BYTES)
        code, stdout, stderr = internal_command(
            executable,
            (name, *version_arguments),
            environment,
        )
        require(code == 0 and stdout + stderr != b"", "tool version output is empty")
        reject_sensitive_output(stdout, private_prefixes, f"{name} version stdout")
        reject_sensitive_output(stderr, private_prefixes, f"{name} version stderr")
        records.append(
            {
                "executable_sha256": sha256(raw),
                "executable_size_bytes": len(raw),
                "name": name,
                "route": normalized_tool_route(executable),
                "version_argv": [name, *version_arguments],
                "version_exit_code": 0,
                "version_stderr": byte_binding(stderr),
                "version_stdout": byte_binding(stdout),
            }
        )
    validate_toolchain_records(records)
    return records, resolved


def validate_toolchain_records(records: Any) -> None:
    require(
        type(records) is list and len(records) == len(TOOL_SPECS), "tool roster changed"
    )
    names = [record.get("name") if type(record) is dict else None for record in records]
    require(
        names == sorted(TOOL_SPECS), "tool roster is missing, reordered, or unexpected"
    )
    for record in records:
        name = record["name"]
        require(
            set(record)
            == {
                "executable_sha256",
                "executable_size_bytes",
                "name",
                "route",
                "version_argv",
                "version_exit_code",
                "version_stderr",
                "version_stdout",
            }
            and type(record["executable_sha256"]) is str
            and SHA256_RE.fullmatch(record["executable_sha256"]) is not None
            and type(record["executable_size_bytes"]) is int
            and 0 < record["executable_size_bytes"] <= MAX_EXECUTABLE_BYTES
            and type(record["route"]) is str
            and re.fullmatch(
                rf"<(?:SYSTEM|USR_LOCAL|HOMEBREW|TEXLIVE)_BIN>/{re.escape(name)}",
                record["route"],
            )
            is not None
            and record["version_argv"] == [name, *TOOL_SPECS[name]]
            and record["version_exit_code"] == 0,
            "tool identity or version command changed",
        )
        require(
            decode_binding(
                record["version_stdout"],
                f"{name} version stdout",
                MAX_VERSION_STREAM_BYTES,
            )
            + decode_binding(
                record["version_stderr"],
                f"{name} version stderr",
                MAX_VERSION_STREAM_BYTES,
            )
            != b"",
            "tool version output is empty",
        )


def validate_snapshot_value(value: Any, c6: str, tree: str, label: str) -> None:
    require(
        type(value) is dict
        and set(value)
        == {
            "alternates",
            "common_dir",
            "config_overlays",
            "git_dir",
            "grafts",
            "head",
            "http_alternates",
            "info_attributes_rules",
            "info_exclude_rules",
            "message",
            "object_format",
            "observed_at",
            "parent",
            "replacement_refs",
            "shallow",
            "status",
            "tree",
            "worktree_root",
        }
        and value["alternates"] == "absent"
        and value["common_dir"] == "<REPOSITORY_ROOT>/.git"
        and value["config_overlays"] == "absent"
        and value["git_dir"] == "<REPOSITORY_ROOT>/.git"
        and value["grafts"] == "absent"
        and value["head"] == c6
        and value["http_alternates"] == "absent"
        and value["info_attributes_rules"] == "absent"
        and value["info_exclude_rules"] == "absent"
        and value["message"] == C6_MESSAGE
        and value["object_format"] == "sha1"
        and value["parent"] == C5_COMMIT
        and value["replacement_refs"] == []
        and value["shallow"] == "absent"
        and value["tree"] == tree
        and value["worktree_root"] == "<REPOSITORY_ROOT>",
        f"{label} repository snapshot changed",
    )
    require(
        decode_binding(value["status"], f"{label} status", 0) == b"",
        f"{label} worktree is not clean",
    )
    try:
        require(
            type(value["observed_at"]) is str
            and UTC_TIMESTAMP_RE.fullmatch(value["observed_at"]) is not None,
            f"{label} timestamp grammar changed",
        )
        observed = datetime.fromisoformat(value["observed_at"].replace("Z", "+00:00"))
        require(observed.utcoffset() is not None, f"{label} timestamp is not UTC-aware")
    except (AttributeError, ValueError):
        raise CaptureError(f"{label} timestamp changed") from None


def validate_record_value(value: Any) -> None:
    require(
        type(value) is dict
        and set(value)
        == {
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
        }
        and value["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v1"
        and value["schema_revision"] == 1
        and value["repository"] == REPOSITORY
        and value["nonimplications"] == NONIMPLICATIONS,
        "local closure root identity changed",
    )
    subject = value["subject"]
    require(
        type(subject) is dict
        and set(subject) == {"c5_parent", "c6_commit", "c6_message", "c6_tree"}
        and subject["c5_parent"] == C5_COMMIT
        and type(subject["c6_commit"]) is str
        and SHA1_RE.fullmatch(subject["c6_commit"]) is not None
        and subject["c6_message"] == C6_MESSAGE
        and type(subject["c6_tree"]) is str
        and SHA1_RE.fullmatch(subject["c6_tree"]) is not None,
        "local closure subject changed",
    )
    authorities = value["authorities"]
    require(
        type(authorities) is list
        and [item.get("path") for item in authorities] == sorted(AUTHORITY_ROLES)
        and all(
            type(item) is dict
            and set(item) == {"path", "role", "sha256", "size_bytes"}
            and item["role"] == AUTHORITY_ROLES[item["path"]]
            and SHA256_RE.fullmatch(item["sha256"]) is not None
            and type(item["size_bytes"]) is int
            and item["size_bytes"] > 0
            for item in authorities
        ),
        "local closure authority inventory changed",
    )
    state = value["repository_state"]
    require(
        type(state) is dict and set(state) == {"after", "before"},
        "repository state pair changed",
    )
    validate_snapshot_value(
        state["before"], subject["c6_commit"], subject["c6_tree"], "before"
    )
    validate_snapshot_value(
        state["after"], subject["c6_commit"], subject["c6_tree"], "after"
    )
    invocation = value["invocation"]
    require(
        type(invocation) is dict
        and set(invocation)
        == {
            "argv",
            "cwd",
            "elapsed_monotonic_ns",
            "environment",
            "environment_routes_sha256",
            "exit_code",
            "finished_at",
            "monotonic_finish_ns",
            "monotonic_start_ns",
            "signal",
            "started_at",
            "stderr",
            "stdout",
            "timeout_seconds",
            "timed_out",
            "umask",
        }
        and invocation["argv"] == list(COMMAND_ARGV)
        and invocation["cwd"] == "<REPOSITORY_ROOT>"
        and invocation["environment"] == NORMALIZED_ENVIRONMENT
        and type(invocation["environment_routes_sha256"]) is str
        and SHA256_RE.fullmatch(invocation["environment_routes_sha256"]) is not None
        and invocation["exit_code"] == 0
        and invocation["signal"] is None
        and invocation["timeout_seconds"] == COMMAND_TIMEOUT_SECONDS
        and invocation["timed_out"] is False
        and invocation["umask"] == "0077"
        and invocation["monotonic_start_ns"] == 0
        and type(invocation["monotonic_finish_ns"]) is int
        and invocation["monotonic_finish_ns"] > 0
        and invocation["elapsed_monotonic_ns"] == invocation["monotonic_finish_ns"],
        "local closure invocation changed",
    )
    stdout = decode_binding(invocation["stdout"], "command stdout", MAX_STREAM_BYTES)
    stderr = decode_binding(invocation["stderr"], "command stderr", MAX_STREAM_BYTES)
    require(stdout + stderr != b"", "local command retained no output")
    try:
        require(
            all(
                type(timestamp) is str
                and UTC_TIMESTAMP_RE.fullmatch(timestamp) is not None
                for timestamp in (
                    invocation["started_at"],
                    invocation["finished_at"],
                )
            ),
            "local closure timestamp grammar changed",
        )
        before_time = datetime.fromisoformat(
            state["before"]["observed_at"].replace("Z", "+00:00")
        )
        started = datetime.fromisoformat(
            invocation["started_at"].replace("Z", "+00:00")
        )
        finished = datetime.fromisoformat(
            invocation["finished_at"].replace("Z", "+00:00")
        )
        after_time = datetime.fromisoformat(
            state["after"]["observed_at"].replace("Z", "+00:00")
        )
    except (AttributeError, ValueError):
        raise CaptureError("local closure timestamp changed") from None
    require(
        before_time <= started <= finished <= after_time,
        "local closure wall-clock ordering changed",
    )
    platform_value = value["platform"]
    require(
        type(platform_value) is dict
        and set(platform_value)
        == {
            "architecture",
            "operating_system",
            "operating_system_release",
            "python_implementation",
            "python_version",
        }
        and platform_value["operating_system"] == "Darwin"
        and platform_value["architecture"] in {"arm64", "aarch64"}
        and platform_value["python_implementation"] == "CPython",
        "local closure platform changed",
    )
    require(
        type(platform_value["operating_system_release"]) is str
        and re.fullmatch(
            r"[0-9A-Za-z._+-]{1,128}",
            platform_value["operating_system_release"],
        )
        is not None
        and type(platform_value["python_version"]) is str
        and re.fullmatch(
            r"3\.(?:1[1-9]|[2-9][0-9])\.[0-9]+",
            platform_value["python_version"],
        )
        is not None,
        "local closure platform version changed",
    )
    validate_toolchain_records(value["reviewed_executables"])


def create_output(path_text: str) -> tuple[int, Path]:
    require(
        type(path_text) is str
        and path_text != ""
        and "\x00" not in path_text
        and "\r" not in path_text
        and "\n" not in path_text,
        "output path is malformed",
    )
    path = Path(path_text)
    require(path.is_absolute(), "output path must be absolute")
    parent = path.parent.resolve(strict=True)
    require(
        parent.is_dir()
        and not is_within(parent, ROOT.resolve())
        and not path.exists()
        and not path.is_symlink(),
        "output must be a new file outside the repository",
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    validate_output_descriptor(descriptor)
    return descriptor, path


def validate_output_descriptor(descriptor: int) -> None:
    metadata = os.fstat(descriptor)
    require(
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_nlink == 1
        and stat.S_IMODE(metadata.st_mode) == 0o600,
        "output destination is not one mode-0600 regular file",
    )


def fixture_tool_records() -> list[dict[str, Any]]:
    return [
        {
            "executable_sha256": format((index + 1) % 16, "x") * 64,
            "executable_size_bytes": index + 1,
            "name": name,
            "route": f"<SYSTEM_BIN>/{name}",
            "version_argv": [name, *arguments],
            "version_exit_code": 0,
            "version_stderr": byte_binding(b""),
            "version_stdout": byte_binding(f"{name} fixture version\n".encode()),
        }
        for index, (name, arguments) in enumerate(sorted(TOOL_SPECS.items()))
    ]


def expect_capture_error(operation: Any, label: str) -> None:
    try:
        operation()
    except CaptureError:
        return
    raise CaptureError(f"hostile fixture survived: {label}")


def under_fixed_umask(operation: Any) -> Any:
    previous_umask = os.umask(0o077)
    try:
        return operation()
    finally:
        os.umask(previous_umask)


def offline_self_test() -> dict[str, Any]:
    caller_umask = os.umask(0o022)
    os.umask(caller_umask)

    def observe_fixed_umask() -> None:
        observed = os.umask(0o077)
        os.umask(observed)
        require(observed == 0o077, "fixed child umask changed")

    under_fixed_umask(observe_fixed_umask)
    observed_after_success = os.umask(caller_umask)
    os.umask(observed_after_success)
    require(observed_after_success == caller_umask, "caller umask was not restored")

    def fail_under_fixed_umask() -> None:
        observe_fixed_umask()
        raise CaptureError("fixture failure")

    expect_capture_error(
        lambda: under_fixed_umask(fail_under_fixed_umask),
        "fixed-umask failure path",
    )
    observed_after_failure = os.umask(caller_umask)
    os.umask(observed_after_failure)
    require(
        observed_after_failure == caller_umask,
        "caller umask was not restored after failure",
    )
    environment = dict(NORMALIZED_ENVIRONMENT)
    require(
        set(environment) == set(NORMALIZED_ENVIRONMENT), "environment fixture drift"
    )
    secret_environment = {"GH_TOKEN": "fixture-secret"}
    expect_capture_error(
        lambda: reject_ambient_secrets(secret_environment), "forbidden environment key"
    )
    validate_repository_config_bytes(b"[core]\n\trepositoryformatversion = 0\n")
    validate_repository_config_names(b"core.repositoryformatversion\n")
    validate_effective_excludes_probe(1, b"", b"")
    expect_capture_error(
        lambda: validate_repository_config_bytes(
            b"[core]\n\texcludesFile = /private/ignore\n"
        ),
        "raw core.excludesFile route",
    )
    expect_capture_error(
        lambda: validate_repository_config_names(b"core.excludesFile\n"),
        "named core.excludesFile route",
    )
    expect_capture_error(
        lambda: validate_effective_excludes_probe(0, b"/private/ignore\n", b""),
        "effective core.excludesFile route",
    )
    forbidden_config_names = (
        "core.splitIndex",
        "extensions.objectFormat",
        "extensions.partialClone",
        "extensions.refStorage",
        "filter.fixture.clean",
        "index.sparse",
        "remote.fixture.promisor",
    )
    for name in forbidden_config_names:
        expect_capture_error(
            lambda name=name: validate_repository_config_names(
                f"core.repositoryformatversion\n{name}\n".encode("ascii")
            ),
            f"forbidden local config {name}",
        )
    validate_repository_local_rules(b"# comment only\n\n", "comment fixture")
    local_rule_hostiles = (
        (b"*.tmp\n", "effective info exclude"),
        (b"*.pdf filter=fixture\n", "effective info attributes"),
        (b"\xff\n", "non-UTF8 local rule"),
    )
    for raw, label in local_rule_hostiles:
        expect_capture_error(
            lambda raw=raw, label=label: validate_repository_local_rules(raw, label),
            label,
        )
    private_prefix = b"/private/fixture-root"
    reject_sensitive_output(
        b"bounded clean output\n", (private_prefix,), "clean fixture"
    )
    output_hostiles = (
        b"Authorization: Bearer fixture-secret-value",
        b"github_pat_abcdefghijklmnopqrstuvwxyz123456",
        private_prefix + b"/artifact",
    )
    for index, raw in enumerate(output_hostiles, start=1):
        expect_capture_error(
            lambda raw=raw: reject_sensitive_output(
                raw, (private_prefix,), "hostile fixture"
            ),
            f"secret/private output {index}",
        )
    binding = byte_binding(b"fixture bytes")
    require(
        decode_binding(binding, "fixture", 1024) == b"fixture bytes", "binding drift"
    )
    changed = dict(binding)
    changed["size_bytes"] += 1
    expect_capture_error(
        lambda: decode_binding(changed, "changed fixture", 1024),
        "truncated binding",
    )
    records = fixture_tool_records()
    validate_toolchain_records(records)
    expect_capture_error(
        lambda: validate_toolchain_records(records[:-1]), "missing tool version"
    )
    changed_records = [dict(item) for item in records]
    changed_records[0]["name"] = "unexpected"
    expect_capture_error(
        lambda: validate_toolchain_records(changed_records), "unexpected executable"
    )
    changed_routes = [dict(item) for item in records]
    changed_routes[0]["route"] = "<SYSTEM_BIN>/python3"
    expect_capture_error(
        lambda: validate_toolchain_records(changed_routes), "tool route/name mismatch"
    )

    directories = fixed_path_directories()
    with tempfile.TemporaryDirectory(prefix="pid-rs-c6-local-self-test-") as temp_text:
        temp_root = Path(temp_text)
        actual_environment, _routes = minimal_environment(directories, temp_root)
        python_path = resolve_executable("python3", directories)
        code, stdout, stderr, timed_out = run_bounded(
            ("python3", "-I", "-S", "-B", "-c", "print('fixture-pass')"),
            python_path,
            actual_environment,
            ROOT,
            10,
            1024,
        )
        require(
            code == 0
            and stdout == b"fixture-pass\n"
            and stderr == b""
            and not timed_out,
            "bounded runner success fixture changed",
        )
        code, _stdout, _stderr, timed_out = run_bounded(
            ("python3", "-I", "-S", "-B", "-c", "raise SystemExit(7)"),
            python_path,
            actual_environment,
            ROOT,
            10,
            1024,
        )
        require(code == 7 and not timed_out, "nonzero fixture changed")
        code, _stdout, _stderr, timed_out = run_bounded(
            (
                "python3",
                "-I",
                "-S",
                "-B",
                "-c",
                "import os,signal; os.kill(os.getpid(), signal.SIGTERM)",
            ),
            python_path,
            actual_environment,
            ROOT,
            10,
            1024,
        )
        require(code == -signal.SIGTERM and not timed_out, "signal fixture changed")
        code, _stdout, _stderr, timed_out = run_bounded(
            (
                "python3",
                "-I",
                "-S",
                "-B",
                "-c",
                "import time; time.sleep(1)",
            ),
            python_path,
            actual_environment,
            ROOT,
            0.05,
            1024,
        )
        require(timed_out and code < 0, "timeout fixture changed")
        expect_capture_error(
            lambda: run_bounded(
                (
                    "python3",
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    "import os,time\n"
                    "pid=os.fork()\n"
                    "if pid == 0:\n"
                    " os.setsid(); time.sleep(0.5); os._exit(0)\n",
                ),
                python_path,
                actual_environment,
                ROOT,
                10,
                1024,
                0.05,
            ),
            "escaped background pipe holder",
        )
        expect_capture_error(
            lambda: run_bounded(
                (
                    "python3",
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    "import sys; sys.stdout.write('x' * 4096)",
                ),
                python_path,
                actual_environment,
                ROOT,
                10,
                128,
            ),
            "output overflow",
        )
        destination = temp_root / "record.json"
        descriptor, _path = create_output(os.fspath(destination))
        try:
            validate_output_descriptor(descriptor)
            os.fchmod(descriptor, 0o644)
            expect_capture_error(
                lambda: validate_output_descriptor(descriptor),
                "non-0600 destination",
            )
        finally:
            os.close(descriptor)
            destination.unlink()
        http_alternates = temp_root / "http-alternates"
        require_absent(http_alternates, "self-test HTTP alternates")
        http_alternates.write_text(
            "https://example.invalid/objects\n", encoding="ascii"
        )
        expect_capture_error(
            lambda: require_absent(http_alternates, "self-test HTTP alternates"),
            "HTTP alternates routing file",
        )
        http_alternates.unlink()

    return {
        "binding_mutations_rejected": 1,
        "environment_mutations_rejected": 1,
        "output_mutations_rejected": len(output_hostiles) + 1,
        "process_failures_observed": 5,
        "repository_config_mutations_rejected": 3 + len(forbidden_config_names),
        "repository_local_rule_mutations_rejected": len(local_rule_hostiles),
        "repository_routing_file_mutations_rejected": 1,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v6-local-closure-capture-self-test/v1",
        "reviewed_executable_mutations_rejected": 3,
        "umask_paths_verified": 2,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--output")
    return parser.parse_args()


def _capture_under_fixed_umask(output_path: str) -> None:
    reject_ambient_secrets(dict(os.environ))
    require(
        platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"}
        and platform.python_implementation() == "CPython",
        "local closure capture requires the reviewed Darwin arm64 CPython lane",
    )
    descriptor = -1
    destination: Path | None = None
    rendered = b""
    try:
        descriptor, destination = create_output(output_path)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-c6-local-closure-",
            dir="/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
        ) as temporary_text:
            temporary_root = Path(temporary_text)
            directories = fixed_path_directories()
            environment, route_digest = minimal_environment(directories, temporary_root)
            private_prefixes = tuple(
                prefix
                for prefix in {
                    os.fsencode(ROOT.resolve()),
                    os.fsencode(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()),
                    os.fsencode(temporary_root.resolve()),
                    os.fsencode(temporary_root.parent.resolve()),
                    os.fsencode(Path(tempfile.gettempdir()).resolve()),
                }
                if prefix
            )
            toolchain, executables = toolchain_observation(
                directories, environment, private_prefixes
            )
            before = repository_snapshot(executables["git"], environment)
            authorities = authority_descriptors(
                executables["git"], environment, before["head"]
            )
            started_at = utc_now()
            monotonic_start = time.monotonic_ns()
            code, stdout, stderr, timed_out = run_bounded(
                COMMAND_ARGV,
                executables["just"],
                environment,
                ROOT,
                COMMAND_TIMEOUT_SECONDS,
                MAX_STREAM_BYTES,
            )
            monotonic_end = time.monotonic_ns()
            finished_at = utc_now()
            require(not timed_out, "local closure command timed out")
            require(code == 0, "local closure command did not exit zero")
            reject_sensitive_output(stdout, private_prefixes, "local command stdout")
            reject_sensitive_output(stderr, private_prefixes, "local command stderr")
            require(stdout + stderr != b"", "local closure command retained no output")
            after = repository_snapshot(executables["git"], environment)
            require(
                {key: before[key] for key in before if key != "observed_at"}
                == {key: after[key] for key in after if key != "observed_at"},
                "repository endpoint changed during local closure",
            )
            elapsed = monotonic_end - monotonic_start
            require(elapsed > 0, "monotonic command interval changed")
            value = {
                "authorities": authorities,
                "invocation": {
                    "argv": list(COMMAND_ARGV),
                    "cwd": "<REPOSITORY_ROOT>",
                    "elapsed_monotonic_ns": elapsed,
                    "environment": NORMALIZED_ENVIRONMENT,
                    "environment_routes_sha256": route_digest,
                    "exit_code": 0,
                    "finished_at": finished_at,
                    "monotonic_finish_ns": elapsed,
                    "monotonic_start_ns": 0,
                    "signal": None,
                    "started_at": started_at,
                    "stderr": byte_binding(stderr),
                    "stdout": byte_binding(stdout),
                    "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
                    "timed_out": False,
                    "umask": "0077",
                },
                "nonimplications": NONIMPLICATIONS,
                "platform": {
                    "architecture": platform.machine(),
                    "operating_system": platform.system(),
                    "operating_system_release": platform.release(),
                    "python_implementation": platform.python_implementation(),
                    "python_version": platform.python_version(),
                },
                "repository": REPOSITORY,
                "repository_state": {"after": after, "before": before},
                "schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v1",
                "schema_revision": 1,
                "subject": {
                    "c5_parent": C5_COMMIT,
                    "c6_commit": before["head"],
                    "c6_message": C6_MESSAGE,
                    "c6_tree": before["tree"],
                },
                "reviewed_executables": toolchain,
            }
            validate_record_value(value)
            rendered = canonical_json(value)
            require(
                0 < len(rendered) <= MAX_RECORD_BYTES,
                "local closure record exceeds the bound",
            )
        validate_output_descriptor(descriptor)
        written = 0
        while written < len(rendered):
            count = os.write(descriptor, rendered[written:])
            require(count > 0, "local closure output write made no progress")
            written += count
        os.fsync(descriptor)
        validate_output_descriptor(descriptor)
        os.close(descriptor)
        descriptor = -1
        require(destination is not None, "output destination disappeared")
        metadata = destination.lstat()
        require(
            metadata.st_size == len(rendered)
            and stat.S_IMODE(metadata.st_mode) == 0o600
            and destination.read_bytes() == rendered,
            "installed local closure bytes changed",
        )
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        if destination is not None and (
            destination.exists() or destination.is_symlink()
        ):
            try:
                destination.unlink()
            except OSError:
                pass
        raise


def capture(output_path: str) -> None:
    under_fixed_umask(lambda: _capture_under_fixed_umask(output_path))


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.self_test:
            sys.stdout.buffer.write(canonical_json(offline_self_test()))
        else:
            require(type(arguments.output) is str, "output path is required")
            capture(arguments.output)
        return 0
    except (CaptureError, OSError, subprocess.SubprocessError):
        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
