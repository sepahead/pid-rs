#!/usr/bin/env python3
"""Validate and render the pid-rs 1.0 public claim/symbol inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tomllib
import types
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
JSON_SCHEMA_SUBSET_SHA256 = (
    "067e6d6b10d33f5b9c1bab6bc621735267a06f2461d6c0da3c8342ac8bd391a6"
)


def load_schema_validator() -> tuple[type[ValueError], Any]:
    """Compile the pinned script-local validator without relying on ``sys.path``."""

    path = ROOT / "scripts/json_schema_subset.py"
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise RuntimeError("validator is not a single-link regular file")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            source = bytearray()
            while chunk := os.read(descriptor, 1024 * 1024):
                source.extend(chunk)
            closed = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = os.lstat(path)
    except OSError as error:
        errno = "none" if error.errno is None else str(error.errno)
        raise RuntimeError(
            "cannot read pinned local validator: "
            f"os_error_type={type(error).__name__} os_errno={errno}"
        ) from error

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size
    ):
        raise RuntimeError("pinned local validator changed during exact-source read")
    observed_sha256 = hashlib.sha256(source).hexdigest()
    if observed_sha256 != JSON_SCHEMA_SUBSET_SHA256:
        raise RuntimeError(
            "pinned local validator digest mismatch: "
            f"expected {JSON_SCHEMA_SUBSET_SHA256}, got {observed_sha256}"
        )

    module = types.ModuleType("pid_rs_release_scope_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source),
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


try:
    SchemaValidationError, validate_json_schema = load_schema_validator()
except RuntimeError as error:
    print(f"release scope bootstrap error: {error}", file=sys.stderr)
    raise SystemExit(2) from error


DEFAULT_SCOPE = ROOT / "release-scope-1.0.json"
DEFAULT_MARKDOWN = ROOT / "RELEASE_SCOPE_1_0.md"
DEFAULT_SCHEMA = ROOT / "audit/schemas/release-scope.schema.json"
DEFAULT_SIGNATURE_REGISTRY = (
    ROOT / "audit/api/public-api/pid-core-signature-revisions.json"
)
DEFAULT_SIGNATURE_REGISTRY_SCHEMA = (
    ROOT / "audit/schemas/public-rust-api-signature-revisions.schema.json"
)
DEFAULT_SOFTWARE_IDENTITY_REFERENCE = (
    ROOT / "crates/pid-core/identity/software-identity-reference-v1.json"
)
DEFAULT_LIB_RS = ROOT / "crates/pid-core/src/lib.rs"
DEFAULT_CARGO = ROOT / "crates/pid-core/Cargo.toml"
SCHEMA = "pid-rs/release-scope"
SCHEMA_REVISION = 1
API_SNAPSHOT_GENERATION = {
    "host_triple": "aarch64-apple-darwin",
    "rustdoc_target_triple": "aarch64-apple-darwin",
    "snapshot_format": "cargo-public-api simplified level 3, color disabled",
    "tool": "cargo-public-api 0.52.0",
    "toolchain": "rustc 1.98.0-nightly (01dfd7924 2026-06-15)",
}
SOURCE_EVIDENCE_TOPOLOGY_REVISION = (0, 4)
SOURCE_EVIDENCE_TOPOLOGY = {
    "logical_profile_count": 10,
    "physical_snapshot_count": 9,
    "policy": "snapshot_first_add_direct_child_of_source",
    "shared_snapshot_profile_ids": [
        "pid-core-all-features",
        "pid-core-experimental-all",
    ],
}
SOURCE_EVIDENCE_RELATION_FORMAT = "pid-rs/public-api-source-evidence-relation/v1"
SIGNATURE_REGISTRY_SCHEMA = "pid-rs/public-rust-api-signature-revisions"
SIGNATURE_REGISTRY_SCHEMA_REVISION = 1
SIGNATURE_REGISTRY_PATH = "audit/api/public-api/pid-core-signature-revisions.json"
SIGNATURE_SNAPSHOT_ROOT = "audit/api/public-api/revisions"
SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT = "633d4e2e77f7c74ff6e34054fd005706069ed7f8"
SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE = "70a233b7c4225a81e5eef78af7ffba13ce057108"
SIGNATURE_GENERATION_FIELDS = (
    "host_triple",
    "rustdoc_target_triple",
    "snapshot_format",
    "tool",
    "toolchain",
)
EXPECTED_MAINTAINER = "Sepehr Mahmoudian"
STABILITIES = {"stable", "experimental", "research-only", "unsupported"}
CLAIM_STATUSES = {
    "not_claimed",
    "claimed_pending",
    "qualified",
    "operationally_validated",
}
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MODULE_RE_TEMPLATE = r"\bpub\s+mod\s+{name}\s*\{{"
MODULE_FEATURES = {
    "experimental::continuous": "experimental-continuous",
    "experimental::continuous::raw_scalars": "experimental-continuous",
    "experimental::isx_heuristics": "experimental-heuristics",
    "experimental::mixed_dimension_pid3": "research-mixed-dimension-pid3",
    "experimental::hyperbolic": "experimental-hyperbolic",
    "experimental::hierarchy": "experimental-hierarchy",
    "experimental::pipelines": "experimental-pipelines",
}
PRIVATE_FAILURE_TEXT_RE = re.compile(
    r"(?:file://|/(?:Users|home)/|/(?:private/)?(?:tmp|var/folders|var/tmp)/|"
    r"[A-Za-z]:[\\/])",
    re.IGNORECASE,
)


class ScopeError(RuntimeError):
    """The machine scope, source exports, or rendered view disagree."""


def byte_observation(label: str, raw: bytes) -> str:
    """Describe untrusted bytes without reproducing their contents."""

    return f"{label}_sha256={hashlib.sha256(raw).hexdigest()} {label}_bytes={len(raw)}"


def text_observation(label: str, value: str) -> str:
    """Bind untrusted text without reproducing it."""

    return byte_observation(label, value.encode("utf-8", "surrogatepass"))


def path_observation(value: os.PathLike[str] | str) -> str:
    """Bind a local or repository path without printing private path material."""

    return byte_observation("path", os.fsencode(value))


def os_error_observation(error: OSError) -> str:
    """Retain the error class/number while suppressing filenames and messages."""

    errno = "none" if error.errno is None else str(error.errno)
    fields = [f"os_error_type={type(error).__name__}", f"os_errno={errno}"]
    for index, filename in enumerate(
        (getattr(error, "filename", None), getattr(error, "filename2", None)), start=1
    ):
        if filename is not None:
            fields.append(
                byte_observation(f"os_filename{index}", os.fsencode(filename))
            )
    return " ".join(fields)


def process_observation(
    operation: str,
    *,
    returncode: int,
    stdout: bytes,
    stderr: bytes,
) -> str:
    """Return the privacy-safe failure form for one bounded subprocess."""

    return (
        f"operation={operation} returncode={returncode} "
        f"{byte_observation('stdout', stdout)} "
        f"{byte_observation('stderr', stderr)}"
    )


def run_git_subprocess(
    operation: str, command: list[str], **kwargs: Any
) -> subprocess.CompletedProcess[bytes]:
    """Spawn Git without exposing an ``OSError`` filename or ambient message."""

    try:
        return subprocess.run(command, **kwargs)
    except OSError as error:
        raise ScopeError(
            f"operation={operation} spawn failed; {os_error_observation(error)}; "
            f"{byte_observation('stdout', b'')} "
            f"{byte_observation('stderr', b'')}"
        ) from error


def public_failure_message(error: BaseException) -> str:
    """Suppress any residual machine-private material in a CLI diagnostic."""

    message = str(error)
    forbidden_literals = (str(ROOT), str(Path.home()), sys.executable)
    if PRIVATE_FAILURE_TEXT_RE.search(message) or any(
        literal and literal in message for literal in forbidden_literals
    ):
        return (
            "privacy-sensitive diagnostic suppressed; "
            f"{text_observation('diagnostic', message)}"
        )
    return message


GIT_ENVIRONMENT_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_ATTR_NOSYSTEM",
    "GIT_ATTR_SOURCE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_EXEC_PATH",
    "GIT_GLOB_PATHSPECS",
    "GIT_GRAFT_FILE",
    "GIT_ICASE_PATHSPECS",
    "GIT_INDEX_FILE",
    "GIT_INDEX_VERSION",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_LITERAL_PATHSPECS",
    "GIT_NAMESPACE",
    "GIT_NOGLOB_PATHSPECS",
    "GIT_NO_LAZY_FETCH",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_QUARANTINE_PATH",
    "GIT_REFERENCE_BACKEND",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_SUPER_PREFIX",
    "GIT_WORK_TREE",
}
GIT_ENVIRONMENT_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


def scrubbed_git_environment() -> dict[str, str]:
    """Return a deterministic read-only Git environment for repository evidence."""

    environment = dict(os.environ)
    for name in tuple(environment):
        if name in GIT_ENVIRONMENT_KEYS or name.startswith(GIT_ENVIRONMENT_PREFIXES):
            environment.pop(name)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def read_utf8_with_sha256(
    path: Path,
    *,
    label: str,
    observations: dict[Path, tuple[str, str]],
) -> tuple[str, str]:
    """Decode and hash exactly one byte observation, cached by resolved path."""

    try:
        resolved = path.resolve(strict=True)
        cached = observations.get(resolved)
        if cached is not None:
            return cached
        raw = resolved.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        detail = (
            os_error_observation(error)
            if isinstance(error, OSError)
            else "decode_error=unicode"
        )
        raise ScopeError(
            f"{label}: cannot read UTF-8 snapshot bytes; "
            f"{path_observation(path)}; {detail}"
        ) from error
    observed = (text, hashlib.sha256(raw).hexdigest())
    observations[resolved] = observed
    return observed


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScopeError(
                f"duplicate JSON object key; {text_observation('duplicate_key', key)}"
            )
        result[key] = value
    return result


def reject_non_finite_json_constant(token: str) -> None:
    """Reject Python's non-standard JSON spellings for non-finite numbers."""

    raise ScopeError(f"non-finite JSON number is forbidden: {token}")


def load_json(path: Path, *, canonical: bool = False, label: str = "JSON input") -> Any:
    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except OSError as error:
        raise ScopeError(
            f"{label}: cannot read JSON input; {path_observation(path)}; "
            f"{os_error_observation(error)}"
        ) from error
    except UnicodeDecodeError as error:
        raise ScopeError(
            f"{label}: JSON input is not UTF-8; {path_observation(path)}; "
            f"decode_start={error.start} decode_end={error.end}"
        ) from error
    except json.JSONDecodeError as error:
        raise ScopeError(
            f"{label}: cannot parse JSON; line={error.lineno} column={error.colno}; "
            f"{byte_observation('input', raw_bytes)}"
        ) from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw != expected:
            raise ScopeError(
                f"{label} is not canonical sorted two-space JSON with one final LF; "
                f"{byte_observation('input', raw_bytes)}"
            )
    return value


def load_json_with_sha256(
    path: Path, *, canonical: bool = False, label: str = "JSON input"
) -> tuple[Any, str]:
    """Parse and hash one immutable byte observation of a JSON artifact."""

    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except OSError as error:
        raise ScopeError(
            f"{label}: cannot read JSON input; {path_observation(path)}; "
            f"{os_error_observation(error)}"
        ) from error
    except UnicodeDecodeError as error:
        raise ScopeError(
            f"{label}: JSON input is not UTF-8; {path_observation(path)}; "
            f"decode_start={error.start} decode_end={error.end}"
        ) from error
    except json.JSONDecodeError as error:
        raise ScopeError(
            f"{label}: cannot parse JSON; line={error.lineno} column={error.colno}; "
            f"{byte_observation('input', raw_bytes)}"
        ) from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw != expected:
            raise ScopeError(
                f"{label} is not canonical sorted two-space JSON with one final LF; "
                f"{byte_observation('input', raw_bytes)}"
            )
    return value, hashlib.sha256(raw_bytes).hexdigest()


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ScopeError(
            f"{label}: path must be a non-empty repository-relative string"
        )
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise ScopeError(
            f"{label}: unsafe repository path; {path_observation(relative)}"
        )
    candidate = root / candidate_relative
    current = root
    for component in candidate_relative.parts:
        current = current / component
        if current.is_symlink():
            raise ScopeError(
                f"{label}: symlink paths are forbidden; {path_observation(relative)}"
            )
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        detail = (
            os_error_observation(error)
            if isinstance(error, OSError)
            else "path_error=outside_repository"
        )
        raise ScopeError(
            f"{label}: file is missing or escapes the repository; "
            f"{path_observation(relative)}; {detail}"
        ) from error
    if not resolved.is_file():
        raise ScopeError(
            f"{label}: expected a regular file; {path_observation(relative)}"
        )
    return resolved


def git_output(root: Path, *args: str) -> str:
    operation = args[0] if args and re.fullmatch(r"[a-z-]+", args[0]) else "read"
    process = run_git_subprocess(
        f"git-{operation}",
        [
            "git",
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            *args,
        ],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise ScopeError(
            f"Git {operation} failed; "
            + process_observation(
                f"git-{operation}",
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        )
    if process.stderr:
        raise ScopeError(
            f"Git {operation} emitted stderr despite success; "
            + process_observation(
                f"git-{operation}",
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        )
    try:
        return process.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise ScopeError(
            f"Git {operation} output is not UTF-8; "
            f"decode_start={error.start} decode_end={error.end}; "
            f"{byte_observation('stdout', process.stdout)}"
        ) from error


def git_commit_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    """Return Git ancestry without a shell; distinguish 'not ancestor' from Git failure."""

    process = run_git_subprocess(
        "git-merge-base-is-ancestor",
        [
            "git",
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode == 0:
        if process.stdout or process.stderr:
            raise ScopeError(
                "Git ancestry check emitted output; "
                + process_observation(
                    "git-merge-base-is-ancestor",
                    returncode=process.returncode,
                    stdout=process.stdout,
                    stderr=process.stderr,
                )
            )
        return True
    if process.returncode == 1:
        if process.stdout or process.stderr:
            raise ScopeError(
                "Git ancestry negative result emitted output; "
                + process_observation(
                    "git-merge-base-is-ancestor",
                    returncode=process.returncode,
                    stdout=process.stdout,
                    stderr=process.stderr,
                )
            )
        return False
    raise ScopeError(
        "Git merge-base --is-ancestor failed; "
        + process_observation(
            "git-merge-base-is-ancestor",
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )
    )


def validate_git_repository_context(root: Path) -> None:
    """Require Git's own worktree root to be the canonical repository being checked."""

    try:
        expected_root = root.resolve(strict=True)
        reported_root = Path(git_output(root, "rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as error:
        raise ScopeError(
            "cannot resolve release-scope Git worktree root; "
            f"{os_error_observation(error)}"
        ) from error
    if reported_root != expected_root:
        raise ScopeError("release-scope Git worktree root mismatch")


def checkout_path_history_commits(
    root: Path, relative: str, *, touch_label: str
) -> list[tuple[str, str]]:
    """Return HEAD boundaries and full-history touch witnesses for one path."""

    head = git_output(root, "rev-parse", "HEAD^{commit}")
    fields = git_output(root, "rev-list", "--parents", "-n", "1", head).split()
    if (
        not fields
        or fields[0] != head
        or any(not re.fullmatch(r"[0-9a-f]{40}", item) for item in fields)
    ):
        raise ScopeError(
            "cannot resolve exact HEAD and direct-parent history boundaries"
        )

    candidates = [("HEAD", head)]
    candidates.extend(
        (f"HEAD^{parent_index}", parent)
        for parent_index, parent in enumerate(fields[1:], start=1)
    )
    touched_raw = git_output(
        root,
        "rev-list",
        "--full-history",
        head,
        "--",
        relative,
    )
    touched = touched_raw.splitlines() if touched_raw else []
    if any(not re.fullmatch(r"[0-9a-f]{40}", commit) for commit in touched):
        raise ScopeError(f"cannot resolve exact {touch_label} history boundaries")
    candidates.extend(
        (f"{touch_label}[{index}]", commit) for index, commit in enumerate(touched)
    )

    commits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, commit in candidates:
        if commit not in seen:
            commits.append((label, commit))
            seen.add(commit)
    return commits


def checkout_history_commits(root: Path) -> list[tuple[str, str]]:
    """Return bounded witnesses for every relevant HEAD-reachable registry state."""

    return checkout_path_history_commits(
        root,
        SIGNATURE_REGISTRY_PATH,
        touch_label="registry-touch",
    )


def checkout_path_addition_commits(root: Path, relative: str) -> list[str]:
    """Return every HEAD-reachable commit that Git classifies as adding ``relative``."""

    raw = git_output(
        root,
        "log",
        "--format=%H",
        "--diff-filter=A",
        "--full-history",
        "HEAD",
        "--",
        relative,
    )
    commits = raw.splitlines() if raw else []
    if any(not re.fullmatch(r"[0-9a-f]{40}", commit) for commit in commits):
        raise ScopeError(
            "cannot resolve exact first-add history for signature snapshot; "
            f"{path_observation(relative)}"
        )
    return list(dict.fromkeys(commits))


def git_file_bytes_at_commit(root: Path, commit: str, relative: str) -> bytes | None:
    """Read exact tracked bytes, returning ``None`` when the path did not yet exist."""

    listed = git_output(root, "ls-tree", "--name-only", commit, "--", relative)
    if not listed:
        return None
    if listed != relative:
        raise ScopeError(
            "unexpected Git tree result; "
            f"expected_{path_observation(relative)}; "
            f"observed_{path_observation(listed)}"
        )
    process = run_git_subprocess(
        "git-show-tracked-bytes",
        [
            "git",
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "show",
            f"{commit}:{relative}",
        ],
        cwd=root,
        env=scrubbed_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise ScopeError(
            "cannot read tracked bytes; "
            f"{path_observation(relative)}; "
            + process_observation(
                "git-show-tracked-bytes",
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        )
    if process.stderr:
        raise ScopeError(
            "Git show emitted stderr despite success; "
            f"{path_observation(relative)}; "
            + process_observation(
                "git-show-tracked-bytes",
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        )
    return process.stdout


def git_file_at_commit(root: Path, commit: str, relative: str) -> str | None:
    """Read one tracked UTF-8 file, returning ``None`` when the path did not yet exist."""

    raw = git_file_bytes_at_commit(root, commit, relative)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ScopeError(
            "tracked file is not UTF-8; "
            f"{path_observation(relative)}; "
            f"decode_start={error.start} decode_end={error.end}; "
            f"{byte_observation('content', raw)}"
        ) from error


def load_canonical_json_text(raw: str, *, label: str) -> Any:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except json.JSONDecodeError as error:
        raise ScopeError(f"cannot parse {label}: {error}") from error
    expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if raw != expected:
        raise ScopeError(
            f"{label} is not canonical sorted two-space JSON with one final LF"
        )
    return value


def sanitize_rust(source: str) -> str:
    """Replace comments and literals with spaces while preserving positions/newlines."""

    output = list(source)
    index = 0
    length = len(source)

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if output[position] != "\n":
                output[position] = " "

    while index < length:
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            if end == -1:
                end = length
            blank(index, end)
            index = end
            continue
        if source.startswith("/*", index):
            start = index
            depth = 1
            index += 2
            while index < length and depth:
                if source.startswith("/*", index):
                    depth += 1
                    index += 2
                elif source.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth:
                raise ScopeError("unterminated Rust block comment")
            blank(start, index)
            continue

        raw = re.match(r'(?:br|r)(#{0,255})"', source[index:])
        if raw:
            hashes = raw.group(1)
            start = index
            index += raw.end()
            terminator = '"' + hashes
            end = source.find(terminator, index)
            if end == -1:
                raise ScopeError("unterminated Rust raw string")
            index = end + len(terminator)
            blank(start, index)
            continue

        if source[index] == '"' or (
            source[index] == "b" and index + 1 < length and source[index + 1] == '"'
        ):
            start = index
            if source[index] == "b":
                index += 1
            index += 1
            escaped = False
            while index < length:
                character = source[index]
                index += 1
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    break
            else:
                raise ScopeError("unterminated Rust string")
            blank(start, index)
            continue

        if source[index] == "'":
            # Lifetimes (`'a`) are syntax, while short quoted forms are char literals.
            char_match = re.match(r"'(?:\\.|[^\\'\n])'", source[index:])
            if char_match:
                start = index
                index += char_match.end()
                blank(start, index)
                continue
        index += 1

    return "".join(output)


class RustModuleExports:
    def __init__(self, source: str) -> None:
        self.source = source
        self.sanitized = sanitize_rust(source)
        self.depths = self._brace_depths()
        self.brace_pairs = self._brace_pairs()

    def _brace_depths(self) -> list[int]:
        depths = [0] * (len(self.sanitized) + 1)
        depth = 0
        for index, character in enumerate(self.sanitized):
            depths[index] = depth
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth < 0:
                    raise ScopeError("unbalanced Rust closing brace")
        depths[len(self.sanitized)] = depth
        if depth:
            raise ScopeError("unbalanced Rust opening brace")
        return depths

    def _brace_pairs(self) -> dict[int, int]:
        stack: list[int] = []
        pairs: dict[int, int] = {}
        for index, character in enumerate(self.sanitized):
            if character == "{":
                stack.append(index)
            elif character == "}":
                if not stack:
                    raise ScopeError("unbalanced Rust closing brace")
                pairs[stack.pop()] = index
        if stack:
            raise ScopeError("unbalanced Rust opening brace")
        return pairs

    def module_span(self, module: str) -> tuple[int, int, int]:
        if module == "crate":
            return 0, len(self.source), 0
        start = 0
        end = len(self.source)
        direct_depth = 0
        for component in module.split("::"):
            if not IDENTIFIER_RE.fullmatch(component):
                raise ScopeError(f"invalid Rust module component: {component!r}")
            pattern = re.compile(MODULE_RE_TEMPLATE.format(name=re.escape(component)))
            match = next(
                (
                    candidate
                    for candidate in pattern.finditer(self.sanitized, start, end)
                    if self.depths[candidate.start()] == direct_depth
                ),
                None,
            )
            if match is None:
                raise ScopeError(f"public inline module {module!r} is missing")
            opening = self.sanitized.find("{", match.start(), match.end())
            closing = self.brace_pairs[opening]
            start = opening + 1
            end = closing
            direct_depth += 1
        return start, end, direct_depth

    @staticmethod
    def _split_top_level(value: str) -> list[str]:
        items = []
        start = 0
        depth = 0
        for index, character in enumerate(value):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            elif character == "," and depth == 0:
                items.append(value[start:index])
                start = index + 1
        items.append(value[start:])
        return [item.strip() for item in items if item.strip()]

    @classmethod
    def _use_names(cls, value: str) -> list[str]:
        value = value.strip()
        if "*" in value:
            raise ScopeError(
                f"glob re-exports are forbidden in the frozen API: {value}"
            )
        opening = value.find("{")
        if opening != -1:
            closing = value.rfind("}")
            if closing < opening:
                raise ScopeError(f"malformed pub use tree: {value}")
            names: list[str] = []
            for item in cls._split_top_level(value[opening + 1 : closing]):
                names.extend(cls._use_names(item))
            return names
        alias = re.search(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", value)
        if alias:
            return [alias.group(1)]
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", value)
        if not identifiers:
            raise ScopeError(f"cannot identify exported name in: {value}")
        if identifiers[-1] == "self" and len(identifiers) >= 2:
            return [identifiers[-2]]
        return [identifiers[-1]]

    def symbols(self, module: str) -> list[str]:
        start, end, direct_depth = self.module_span(module)
        function = r"(?:const\s+)?(?:async\s+)?(?:unsafe\s+)?(?:extern\s+)?fn"
        declaration = re.compile(
            rf"\bpub\s+(use|extern\s+crate|{function}|const|static|type|struct|enum|union|trait|macro)\b"
        )
        symbols: list[str] = []
        for match in declaration.finditer(self.sanitized, start, end):
            if self.depths[match.start()] != direct_depth:
                continue
            kind = match.group(1)
            normalized_kind = " ".join(kind.split())
            if normalized_kind in {"use", "extern crate"}:
                semicolon = next(
                    (
                        index
                        for index in range(match.end(), end)
                        if self.sanitized[index] == ";"
                        and self.depths[index] == direct_depth
                    ),
                    None,
                )
                if semicolon is None:
                    raise ScopeError(f"unterminated pub use in {module}")
                value = self.source[match.end() : semicolon]
                if normalized_kind == "extern crate":
                    alias = re.search(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", value)
                    if alias:
                        symbols.append(alias.group(1))
                    else:
                        name = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", value)
                        if name is None:
                            raise ScopeError(
                                f"cannot parse public extern crate in {module}"
                            )
                        symbols.append(name.group(1))
                else:
                    symbols.extend(self._use_names(value))
            else:
                name_match = re.match(
                    r"\s*([A-Za-z_][A-Za-z0-9_]*)", self.sanitized[match.end() :]
                )
                if name_match is None:
                    raise ScopeError(f"cannot parse public {kind} in {module}")
                symbols.append(name_match.group(1))
        if module == "crate":
            # `#[macro_export] macro_rules!` is public at the crate root even when its physical
            # declaration is nested. It has no `pub` token, so inventory it explicitly.
            exported_macro = re.compile(
                r"#\s*\[\s*macro_export(?:\s*\([^\]]*\))?\s*\]"
                r"(?:\s*#\s*\[[^\]]*\])*\s*"
                r"macro_rules\s*!\s*([A-Za-z_][A-Za-z0-9_]*)"
            )
            symbols.extend(
                match.group(1) for match in exported_macro.finditer(self.sanitized)
            )
        duplicates = sorted(name for name in set(symbols) if symbols.count(name) > 1)
        if duplicates:
            raise ScopeError(
                f"duplicate direct exports in {module}: {', '.join(duplicates)}"
            )
        return sorted(symbols)

    def child_modules(self, module: str) -> list[str]:
        start, end, direct_depth = self.module_span(module)
        # Include out-of-line declarations (`pub mod name;`). They are not used by the frozen
        # facade, but silently omitting them would let an unscoped public module evade this check.
        # If one is ever added to the declared module tree, `module_span` will fail closed because
        # this parser intentionally inventories only the authoritative inline facade in lib.rs.
        declaration = re.compile(r"\bpub\s+mod\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\{;]")
        modules = [
            match.group(1)
            for match in declaration.finditer(self.sanitized, start, end)
            if self.depths[match.start()] == direct_depth
        ]
        duplicates = sorted(name for name in set(modules) if modules.count(name) > 1)
        if duplicates:
            raise ScopeError(
                f"duplicate public modules in {module}: {', '.join(duplicates)}"
            )
        return sorted(modules)


def validate_stable_profile_diff(
    profile_id: str,
    active_features: set[str],
    default_snapshot: str,
    profile_snapshot: str,
    conditional_members: list[dict[str, Any]],
) -> None:
    """Require the exact stable-namespace delta for one complete activation profile."""

    expected_added = {
        member["added_api_line"]
        for member in conditional_members
        if member["feature"] in active_features
    }
    expected_removed = {
        member["removed_api_line"]
        for member in conditional_members
        if member["feature"] in active_features
        and member["removed_api_line"] is not None
    }
    default_stable_lines = stable_namespace_lines(default_snapshot)
    profile_stable_lines = stable_namespace_lines(profile_snapshot)
    actual_added = profile_stable_lines - default_stable_lines
    actual_removed = default_stable_lines - profile_stable_lines
    if actual_added != expected_added or actual_removed != expected_removed:
        raise ScopeError(
            f"{profile_id}: stable-namespace diff disagrees with conditional_members; "
            f"unlisted added={sorted(actual_added - expected_added)!r}; "
            f"stale added={sorted(expected_added - actual_added)!r}; "
            f"unlisted removed={sorted(actual_removed - expected_removed)!r}; "
            f"stale removed={sorted(expected_removed - actual_removed)!r}"
        )


def feature_closure(features: dict[str, list[str]], requested: list[str]) -> list[str]:
    closure: set[str] = set()
    stack = list(requested)
    while stack:
        feature = stack.pop()
        if feature in closure:
            continue
        if feature not in features:
            raise ScopeError(f"unknown Cargo feature in scope: {feature}")
        closure.add(feature)
        for dependency in features[feature]:
            if dependency.startswith("dep:") or "/" in dependency:
                continue
            stack.append(dependency)
    return sorted(closure)


PID_PATH_RE = re.compile(r"pid_core(?:::[A-Za-z_][A-Za-z0-9_]*)*")
IMPL_RE = re.compile(r"^impl\b")


def is_experimental_pid_path(path: str) -> bool:
    return path == "pid_core::experimental" or path.startswith(
        "pid_core::experimental::"
    )


def impl_trait_and_self_subject(api_line: str) -> str:
    """Remove ``impl`` generics and trailing bounds from a normalized impl line."""

    subject = api_line[4:].lstrip()
    if subject.startswith("<"):
        depth = 0
        for index, character in enumerate(subject):
            if character == "<":
                depth += 1
            elif character == ">":
                depth -= 1
                if depth == 0:
                    subject = subject[index + 1 :].lstrip()
                    break
        else:
            return ""
    return subject.split(" where ", 1)[0]


def primary_pid_path(api_line: str) -> str | None:
    """Return the namespace-classifying pid-core path from one public-API line."""

    subject = (
        impl_trait_and_self_subject(api_line) if IMPL_RE.match(api_line) else api_line
    )
    matches = list(PID_PATH_RE.finditer(subject))
    if not matches:
        return None
    if IMPL_RE.match(api_line):
        # An impl contributes to both its trait and self type. Treat it as stable when
        # either side names a non-experimental pid-core path, including ``impl<T>`` forms.
        for match in matches:
            if not is_experimental_pid_path(match.group(0)):
                return match.group(0)
    return matches[0].group(0)


def stable_namespace_lines(snapshot: str) -> set[str]:
    lines: set[str] = set()
    for line in snapshot.splitlines():
        path = primary_pid_path(line)
        if path is None:
            continue
        if is_experimental_pid_path(path):
            continue
        lines.add(line)
    return lines


def validate_public_api_profile_alias_contract(profiles: list[dict[str, Any]]) -> None:
    """Keep ten activation semantics distinct while permitting nine retained files."""

    by_id = {
        profile.get("id"): profile
        for profile in profiles
        if isinstance(profile, dict) and isinstance(profile.get("id"), str)
    }
    if len(profiles) != SOURCE_EVIDENCE_TOPOLOGY["logical_profile_count"]:
        raise ScopeError(
            "public API profile roster must contain exactly ten logical activation profiles"
        )
    shared_ids = SOURCE_EVIDENCE_TOPOLOGY["shared_snapshot_profile_ids"]
    try:
        all_features = by_id[shared_ids[0]]
        experimental_all = by_id[shared_ids[1]]
    except KeyError as error:
        raise ScopeError(
            "public API profile roster omits the all-features/experimental-all pair"
        ) from error

    if (
        all_features.get("all_features") is not True
        or all_features.get("requested_features") != []
        or all_features.get("generation_arguments", [])[-1:] != ["--all-features"]
    ):
        raise ScopeError(
            "pid-core-all-features must retain distinct --all-features activation semantics"
        )
    if (
        experimental_all.get("all_features") is not False
        or experimental_all.get("requested_features") != ["experimental-all"]
        or experimental_all.get("generation_arguments", [])[-2:]
        != ["--features", "experimental-all"]
    ):
        raise ScopeError(
            "pid-core-experimental-all must retain explicit umbrella-feature activation semantics"
        )
    if all_features.get("generation_arguments") == experimental_all.get(
        "generation_arguments"
    ):
        raise ScopeError(
            "all-features and experimental-all activation commands were conflated"
        )
    if set(all_features.get("feature_closure", [])) != set(
        experimental_all.get("feature_closure", [])
    ) | {"default", "parallel"}:
        raise ScopeError(
            "all-features closure must add exactly default and parallel to experimental-all"
        )

    shared_path = experimental_all.get("public_api_snapshot")
    shared_digest = experimental_all.get("public_api_snapshot_sha256")
    if (
        all_features.get("public_api_snapshot") != shared_path
        or all_features.get("public_api_snapshot_sha256") != shared_digest
    ):
        raise ScopeError(
            "all-features and experimental-all must share one byte-identical retained snapshot"
        )
    paths = [profile.get("public_api_snapshot") for profile in profiles]
    if len(set(paths)) != SOURCE_EVIDENCE_TOPOLOGY["physical_snapshot_count"]:
        raise ScopeError(
            "ten public API activation profiles must bind exactly nine physical snapshots"
        )
    if sum(path == shared_path for path in paths) != 2:
        raise ScopeError(
            "only all-features and experimental-all may share a public API snapshot path"
        )


def validate_signature_entry_profile_topology(entry: dict[str, Any]) -> None:
    """Validate the revision-4 logical-to-physical snapshot mapping."""

    profiles = entry.get("profiles")
    if not isinstance(profiles, list):
        raise ScopeError("revision-4 signature profiles must be an array")
    profile_ids = [
        profile.get("id") for profile in profiles if isinstance(profile, dict)
    ]
    if len(profile_ids) != len(profiles) or profile_ids != sorted(set(profile_ids)):
        raise ScopeError("revision-4 signature profiles must have sorted unique ids")
    if len(profiles) != SOURCE_EVIDENCE_TOPOLOGY["logical_profile_count"]:
        raise ScopeError(
            "revision-4 signature evidence omits a logical public API profile"
        )
    by_id = {profile.get("id"): profile for profile in profiles}
    shared_ids = SOURCE_EVIDENCE_TOPOLOGY["shared_snapshot_profile_ids"]
    if any(profile_id not in by_id for profile_id in shared_ids):
        raise ScopeError(
            "revision-4 signature evidence omits the all-features/experimental-all pair"
        )
    left = by_id[shared_ids[0]]
    right = by_id[shared_ids[1]]
    if left.get("public_api_snapshot") != right.get("public_api_snapshot") or left.get(
        "public_api_snapshot_sha256"
    ) != right.get("public_api_snapshot_sha256"):
        raise ScopeError(
            "revision-4 all-features and experimental-all evidence must share exact bytes"
        )
    paths = [profile.get("public_api_snapshot") for profile in profiles]
    if len(set(paths)) != SOURCE_EVIDENCE_TOPOLOGY["physical_snapshot_count"]:
        raise ScopeError(
            "revision-4 signature evidence must contain exactly nine physical snapshots"
        )
    shared_path = left.get("public_api_snapshot")
    if sum(path == shared_path for path in paths) != 2:
        raise ScopeError(
            "revision-4 shared snapshot path may bind only the two declared logical profiles"
        )


def validate_signature_registry_genesis(
    snapshot_source: dict[str, Any], *, historical_registry_present: bool
) -> None:
    """Permit a missing historical registry only at the immutable revision-1 source."""

    if historical_registry_present:
        return
    source = (snapshot_source.get("commit_sha"), snapshot_source.get("tree_sha"))
    genesis = (
        SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT,
        SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE,
    )
    if source != genesis:
        raise ScopeError(
            "a missing historical signature registry is permitted only at the immutable genesis source"
        )


def profile_signature(entry: dict[str, Any]) -> tuple[tuple[Any, Any], ...]:
    """Return declaration-signature identity, deliberately excluding storage paths."""

    profiles = entry.get("profiles", [])
    return tuple(
        (profile.get("id"), profile.get("public_api_snapshot_sha256"))
        for profile in profiles
        if isinstance(profile, dict)
    )


def signature_transition_is_meaningful(
    previous: dict[str, Any], current: dict[str, Any]
) -> bool:
    return (
        profile_signature(previous) != profile_signature(current)
        or previous.get("epoch") != current.get("epoch")
        or previous.get("scope") != current.get("scope")
        or previous.get("status") != current.get("status")
    )


def validate_signature_registry_extension(
    entries: list[dict[str, Any]],
    historical_entries: list[dict[str, Any]],
    *,
    history_label: str = "historical registry",
) -> None:
    """Require a first record or one exact append after a preserved historical prefix."""

    if not historical_entries:
        if len(entries) != 1:
            raise ScopeError(
                "the first signature registry update must contain exactly revision 1"
            )
        return
    validate_signature_registry_prefix(
        entries,
        historical_entries,
        history_label=history_label,
    )
    if len(entries) == len(historical_entries):
        return
    if len(entries) != len(historical_entries) + 1:
        raise ScopeError(
            "a signature evidence transition must append at most one contiguous registry entry"
        )
    historical_latest = historical_entries[-1]
    latest = entries[-1]
    if not signature_transition_is_meaningful(historical_latest, latest):
        raise ScopeError(
            "a pure signature revision-number bump without a profile, scope, status, or epoch change is forbidden"
        )


def validate_signature_registry_prefix(
    entries: list[dict[str, Any]],
    historical_entries: list[dict[str, Any]],
    *,
    history_label: str,
) -> None:
    """Require an exact retained prefix without limiting later append count."""

    if (
        len(entries) < len(historical_entries)
        or entries[: len(historical_entries)] != historical_entries
    ):
        raise ScopeError(
            f"signature registry does not preserve the {history_label} entry prefix"
        )


def signature_snapshot_directory(epoch: int, revision: int) -> str:
    return f"{SIGNATURE_SNAPSHOT_ROOT}/{epoch}-{revision}"


def validate_signature_registry_header(
    registry: dict[str, Any], historical: dict[str, Any], *, history_label: str
) -> None:
    for field in (
        "append_policy",
        "genesis_source_commit_sha",
        "genesis_source_tree_sha",
        "package",
        "schema",
        "schema_revision",
    ):
        if registry.get(field) != historical.get(field):
            raise ScopeError(
                f"signature registry header changed at {field} relative to {history_label}"
            )


def validate_signature_registry_history_text(
    registry: dict[str, Any],
    raw: str,
    *,
    registry_schema: Any,
    history_label: str,
) -> dict[str, Any]:
    historical = load_canonical_json_text(raw, label=history_label)
    try:
        validate_json_schema(
            historical,
            registry_schema,
            name=f"signature registry at {history_label}",
        )
    except SchemaValidationError as error:
        raise ScopeError(
            f"historical signature registry JSON Schema validation failed at {history_label}: {error}"
        ) from error
    validate_signature_registry_header(
        registry,
        historical,
        history_label=history_label,
    )
    validate_signature_registry_prefix(
        registry["entries"],
        historical["entries"],
        history_label=history_label,
    )
    return historical


def validate_signature_registry_historical_lineage(
    histories: dict[str, tuple[str, dict[str, Any] | None]], *, root: Path
) -> None:
    """Reject deletion, truncation, or rewrite across comparable retained baselines."""

    items = list(histories.items())
    for ancestor_commit, (ancestor_label, ancestor_registry) in items:
        for descendant_commit, (descendant_label, descendant_registry) in items:
            if ancestor_commit == descendant_commit or not git_commit_is_ancestor(
                root, ancestor_commit, descendant_commit
            ):
                continue
            if ancestor_registry is None:
                continue
            if descendant_registry is None:
                raise ScopeError(
                    "signature registry was deleted between comparable history boundaries: "
                    f"{ancestor_label} -> {descendant_label}"
                )
            ancestor_entries = ancestor_registry["entries"]
            descendant_entries = descendant_registry["entries"]
            if (
                len(descendant_entries) < len(ancestor_entries)
                or descendant_entries[: len(ancestor_entries)] != ancestor_entries
            ):
                raise ScopeError(
                    "signature registry history contains a truncation or rewrite between "
                    f"{ancestor_label} and {descendant_label}"
                )


def registry_snapshot_bindings(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Return the unique immutable path-to-digest bindings in registry entries."""

    bindings: dict[str, str] = {}
    for entry in entries:
        for profile in entry["profiles"]:
            relative = profile["public_api_snapshot"]
            digest = profile["public_api_snapshot_sha256"]
            prior = bindings.get(relative)
            if prior is not None and prior != digest:
                raise ScopeError(
                    "signature snapshot path has conflicting registry digests; "
                    f"{path_observation(relative)}"
                )
            bindings[relative] = digest
    return bindings


def validate_signature_snapshot_history(
    entries: list[dict[str, Any]],
    *,
    histories: dict[str, tuple[str, dict[str, Any] | None]],
    root: Path,
) -> None:
    """Reject any reachable snapshot mutation after its first committed binding."""

    for relative, expected_digest in registry_snapshot_bindings(entries).items():
        binding_commits: list[tuple[str, str]] = []
        for commit, (label, historical_registry) in histories.items():
            if historical_registry is None:
                continue
            historical_bindings = registry_snapshot_bindings(
                historical_registry["entries"]
            )
            if historical_bindings.get(relative) == expected_digest:
                binding_commits.append((label, commit))

        # A path first bound by the working-tree registry has no committed binding yet. Its
        # checked-out bytes were validated above; earlier path history remains pre-binding.
        if not binding_commits:
            continue

        candidates = [(f"{label} binding", commit) for label, commit in binding_commits]
        candidates.extend(
            checkout_path_history_commits(
                root,
                relative,
                touch_label="snapshot-touch",
            )
        )
        seen: set[str] = set()
        for label, commit in candidates:
            if commit in seen:
                continue
            seen.add(commit)
            binding_label = next(
                (
                    candidate_label
                    for candidate_label, binding_commit in binding_commits
                    if git_commit_is_ancestor(root, binding_commit, commit)
                ),
                None,
            )
            if binding_label is None:
                continue
            raw = git_file_bytes_at_commit(root, commit, relative)
            if raw is None:
                raise ScopeError(
                    "immutable signature snapshot was absent after registry binding; "
                    f"{path_observation(relative)}; binding={binding_label}; "
                    f"observation={label}; commit={commit}"
                )
            observed_digest = hashlib.sha256(raw).hexdigest()
            if observed_digest != expected_digest:
                raise ScopeError(
                    "immutable signature snapshot changed after registry binding; "
                    f"{path_observation(relative)}; binding={binding_label}; "
                    f"observation={label}; commit={commit}; "
                    f"expected_sha256={expected_digest}; observed_sha256={observed_digest}"
                )


def validate_revision_four_source_evidence_topology(
    entry: dict[str, Any],
    registry: dict[str, Any],
    *,
    root: Path,
) -> dict[str, Any] | None:
    """Bind revision 0-4 evidence to one direct child of its exact source commit."""

    shallow = git_output(root, "rev-parse", "--is-shallow-repository")
    if shallow not in {"true", "false"}:
        raise ScopeError(f"unexpected Git shallow-repository state: {shallow!r}")
    if shallow == "true":
        raise ScopeError(
            "revision-4 source/evidence relation requires Git to report a non-shallow "
            "repository; that report does not establish local object completeness or "
            "exclude promisor-backed objects"
        )
    if (entry.get("epoch"), entry.get("revision")) != SOURCE_EVIDENCE_TOPOLOGY_REVISION:
        raise ScopeError(
            "revision-4 topology validator received the wrong registry entry"
        )
    if entry.get("evidence_topology") != SOURCE_EVIDENCE_TOPOLOGY:
        raise ScopeError("revision-4 source/evidence topology declaration mismatch")
    if entry.get("generation") != API_SNAPSHOT_GENERATION:
        raise ScopeError("revision-4 public API generation toolchain drifted")
    validate_signature_entry_profile_topology(entry)

    source_commit = entry["snapshot_source_commit_sha"]
    source_tree = entry["snapshot_source_tree_sha"]
    if git_output(root, "rev-parse", f"{source_commit}^{{tree}}") != source_tree:
        raise ScopeError("revision-4 source tree does not match its source commit")

    target_index = SOURCE_EVIDENCE_TOPOLOGY_REVISION[1] - 1
    if (
        len(registry["entries"]) <= target_index
        or registry["entries"][target_index] != entry
    ):
        raise ScopeError("revision-4 entry is not in its contiguous registry slot")
    expected_parent_registry = {
        **registry,
        "entries": registry["entries"][:target_index],
    }
    head = git_output(root, "rev-parse", "HEAD^{commit}")
    committed_registry_raw = git_file_at_commit(root, head, SIGNATURE_REGISTRY_PATH)
    if committed_registry_raw is None:
        raise ScopeError(
            "revision-4 topology requires a committed predecessor registry"
        )
    committed_registry = load_canonical_json_text(
        committed_registry_raw,
        label=f"{SIGNATURE_REGISTRY_PATH} at HEAD {head}",
    )
    committed_revision_four = (
        len(committed_registry.get("entries", [])) > target_index
        and committed_registry["entries"][target_index] == entry
    )

    snapshot_paths = sorted(
        {profile["public_api_snapshot"] for profile in entry["profiles"]}
    )
    if not committed_revision_four:
        # This is the only permitted pre-commit candidate state: the clean source commit is HEAD,
        # its registry is the exact retained prefix, and none of the evidence paths exists there.
        if head != source_commit:
            raise ScopeError(
                "uncommitted revision-4 evidence is permitted only at the exact source HEAD"
            )
        if committed_registry != expected_parent_registry:
            raise ScopeError(
                "uncommitted revision-4 registry does not extend the exact source prefix"
            )
        for relative in snapshot_paths:
            if git_file_bytes_at_commit(root, source_commit, relative) is not None:
                raise ScopeError(
                    "revision-4 snapshot already exists in the source commit; "
                    f"{path_observation(relative)}"
                )
        return None

    addition_commit_by_path: dict[str, str] = {}
    for relative in snapshot_paths:
        additions = checkout_path_addition_commits(root, relative)
        if len(additions) != 1:
            raise ScopeError(
                "revision-4 snapshot must have exactly one reachable first-add commit; "
                f"{path_observation(relative)}"
            )
        addition_commit_by_path[relative] = additions[0]
    evidence_commits = set(addition_commit_by_path.values())
    if len(evidence_commits) != 1:
        raise ScopeError(
            "all nine revision-4 snapshots must first appear in one evidence commit"
        )
    evidence_commit = next(iter(evidence_commits))
    evidence_fields = git_output(
        root, "rev-list", "--parents", "-n", "1", evidence_commit
    ).split()
    if len(evidence_fields) != 2 or evidence_fields[0] != evidence_commit:
        raise ScopeError("revision-4 evidence commit must have exactly one parent")
    if evidence_fields[1] != source_commit:
        raise ScopeError(
            "revision-4 evidence commit sole parent is not the registered source commit"
        )

    evidence_registry_raw = git_file_at_commit(
        root, evidence_commit, SIGNATURE_REGISTRY_PATH
    )
    source_registry_raw = git_file_at_commit(
        root, source_commit, SIGNATURE_REGISTRY_PATH
    )
    if evidence_registry_raw is None or source_registry_raw is None:
        raise ScopeError("revision-4 source/evidence registry boundary is incomplete")
    evidence_registry = load_canonical_json_text(
        evidence_registry_raw,
        label=f"{SIGNATURE_REGISTRY_PATH} at evidence commit {evidence_commit}",
    )
    source_registry = load_canonical_json_text(
        source_registry_raw,
        label=f"{SIGNATURE_REGISTRY_PATH} at source commit {source_commit}",
    )
    if source_registry != expected_parent_registry:
        raise ScopeError(
            "revision-4 source commit does not contain the exact registry prefix"
        )
    expected_evidence_registry = {
        **registry,
        "entries": registry["entries"][: target_index + 1],
    }
    if evidence_registry != expected_evidence_registry:
        raise ScopeError(
            "revision-4 evidence commit does not add exactly the contiguous registry entry"
        )

    digest_by_path = registry_snapshot_bindings([entry])
    for relative, expected_digest in digest_by_path.items():
        raw = git_file_bytes_at_commit(root, evidence_commit, relative)
        if raw is None or hashlib.sha256(raw).hexdigest() != expected_digest:
            raise ScopeError(
                "revision-4 evidence commit bytes do not match derived digest; "
                f"{path_observation(relative)}"
            )
    return {
        "evidence_commit": evidence_commit,
        "evidence_parent_count": len(evidence_fields) - 1,
        "source_commit": source_commit,
    }


def validate_signature_registry_entries(
    entries: list[dict[str, Any]],
    *,
    root: Path,
    observations: dict[Path, tuple[str, str]],
) -> None:
    """Validate sequence, immutable bytes, source identity, and source ancestry."""

    validate_git_repository_context(root)
    shallow = git_output(root, "rev-parse", "--is-shallow-repository")
    if shallow not in {"true", "false"}:
        raise ScopeError(f"unexpected Git shallow-repository state: {shallow!r}")
    if shallow == "true":
        raise ScopeError(
            "signature registry ancestry requires Git to report a non-shallow repository; "
            "that report does not establish local object completeness or exclude "
            "promisor-backed objects"
        )
    head = git_output(root, "rev-parse", "HEAD^{commit}")
    previous_key: tuple[int, int] | None = None
    previous_entry: dict[str, Any] | None = None
    previous_source: str | None = None
    path_bindings: dict[str, str] = {}
    for index, entry in enumerate(entries):
        epoch = entry.get("epoch")
        revision = entry.get("revision")
        if (
            not isinstance(epoch, int)
            or isinstance(epoch, bool)
            or epoch < 0
            or not isinstance(revision, int)
            or isinstance(revision, bool)
            or revision < 1
        ):
            raise ScopeError(
                f"signature registry entry {index}: epoch must be non-negative and revision positive integers"
            )
        key = (epoch, revision)
        if previous_key is None:
            if key != (0, 1):
                raise ScopeError(
                    "signature revision registry must begin at epoch 0 revision 1"
                )
        else:
            same_epoch_next = key == (previous_key[0], previous_key[1] + 1)
            next_epoch_first = key == (previous_key[0] + 1, 1)
            if not (same_epoch_next or next_epoch_first):
                raise ScopeError(
                    "signature revision entries must be contiguous by epoch and revision"
                )
            assert previous_entry is not None
            if not signature_transition_is_meaningful(previous_entry, entry):
                raise ScopeError(
                    f"signature registry entry {index}: pure revision-number bumps are forbidden"
                )
        previous_key = key

        if key == SOURCE_EVIDENCE_TOPOLOGY_REVISION:
            if entry.get("evidence_topology") != SOURCE_EVIDENCE_TOPOLOGY:
                raise ScopeError(
                    "signature registry revision 0-4 lacks the exact source/evidence topology"
                )
            validate_signature_entry_profile_topology(entry)
        elif key < SOURCE_EVIDENCE_TOPOLOGY_REVISION and "evidence_topology" in entry:
            raise ScopeError(
                f"signature registry entry {index}: historical revisions must not be retrofitted with revision-4 topology"
            )

        profiles = entry.get("profiles")
        if not isinstance(profiles, list):
            raise ScopeError(
                f"signature registry entry {index}: profiles must be an array"
            )
        profile_ids = [item.get("id") for item in profiles if isinstance(item, dict)]
        if len(profile_ids) != len(profiles) or profile_ids != sorted(set(profile_ids)):
            raise ScopeError(
                f"signature registry entry {index}: profiles must have sorted unique ids"
            )

        expected_directory = signature_snapshot_directory(epoch, revision)
        for profile in profiles:
            profile_id = profile["id"]
            relative = profile["public_api_snapshot"]
            if Path(relative).parent.as_posix() != expected_directory:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: snapshot path must be in {expected_directory}"
                )
            declared_digest = profile["public_api_snapshot_sha256"]
            prior_digest = path_bindings.get(relative)
            # Identical profiles may intentionally share one immutable file. Any conflicting
            # binding for the same path remains invalid.
            if prior_digest is not None and prior_digest != declared_digest:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: shared snapshot path has conflicting digests"
                )
            path_bindings[relative] = declared_digest
            snapshot_path = safe_repo_file(
                root,
                relative,
                label=f"signature registry entry {index} profile {profile_id} snapshot",
            )
            _, observed_digest = read_utf8_with_sha256(
                snapshot_path,
                label=f"signature registry entry {index} profile {profile_id} snapshot",
                observations=observations,
            )
            if observed_digest != declared_digest:
                raise ScopeError(
                    f"signature registry entry {index} profile {profile_id}: retained snapshot digest mismatch"
                )

        commit = entry.get("snapshot_source_commit_sha")
        tree = entry.get("snapshot_source_tree_sha")
        if git_output(root, "rev-parse", f"{commit}^{{commit}}") != commit:
            raise ScopeError(
                f"signature registry entry {index}: source commit is not exact"
            )
        if git_output(root, "rev-parse", f"{commit}^{{tree}}") != tree:
            raise ScopeError(
                f"signature registry entry {index}: source tree does not match its commit"
            )
        if not git_commit_is_ancestor(root, commit, head):
            raise ScopeError(
                f"signature registry entry {index}: source commit is not an ancestor of HEAD"
            )
        if previous_source is not None and not git_commit_is_ancestor(
            root, previous_source, commit
        ):
            raise ScopeError(
                f"signature registry entry {index}: source commits are not monotone by ancestry"
            )
        if (
            previous_entry is not None
            and previous_source == commit
            and previous_entry.get("generation") == entry.get("generation")
            and profile_signature(previous_entry) != profile_signature(entry)
        ):
            raise ScopeError(
                f"signature registry entry {index}: unchanged source and generation cannot produce a different declaration signature"
            )
        previous_source = commit
        previous_entry = entry


def validate_signature_revision_registry(
    scope: dict[str, Any],
    *,
    registry: Any,
    registry_path: Path,
    registry_sha256: str,
    registry_schema: Any,
    identity_reference: Any,
    root: Path,
    observations: dict[Path, tuple[str, str]],
) -> dict[str, Any] | None:
    """Bind the runtime signature revision to exact, append-only snapshot evidence."""

    try:
        validate_json_schema(
            registry,
            registry_schema,
            name="pid-core-signature-revisions.json",
        )
    except SchemaValidationError as error:
        raise ScopeError(
            f"signature registry JSON Schema validation failed: {error}"
        ) from error

    pointer = scope.get("public_rust_api_signature_revision_registry")
    if not isinstance(pointer, dict):
        raise ScopeError(
            "public Rust API signature revision registry pointer is missing"
        )
    expected_pointer = {
        "repository_path": SIGNATURE_REGISTRY_PATH,
        "schema": SIGNATURE_REGISTRY_SCHEMA,
        "schema_revision": SIGNATURE_REGISTRY_SCHEMA_REVISION,
    }
    for field, expected in expected_pointer.items():
        if pointer.get(field) != expected:
            raise ScopeError(
                f"signature registry pointer {field} mismatch: "
                f"expected {expected!r}, got {pointer.get(field)!r}"
            )
    if registry_path == DEFAULT_SIGNATURE_REGISTRY:
        safe_repo_file(
            root,
            pointer["repository_path"],
            label="public Rust API signature revision registry",
        )
    if registry_sha256 != pointer.get("canonical_json_sha256"):
        raise ScopeError("public Rust API signature revision registry digest mismatch")
    if (
        registry.get("schema") != SIGNATURE_REGISTRY_SCHEMA
        or registry.get("schema_revision") != SIGNATURE_REGISTRY_SCHEMA_REVISION
    ):
        raise ScopeError("unsupported public Rust API signature revision registry")
    if (
        registry.get("genesis_source_commit_sha")
        != SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT
        or registry.get("genesis_source_tree_sha")
        != SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE
    ):
        raise ScopeError("signature registry genesis source changed")

    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ScopeError("signature revision registry must contain at least one entry")
    validate_signature_registry_entries(
        entries,
        root=root,
        observations=observations,
    )

    latest = entries[-1]
    identity = (
        identity_reference.get("api_signature_identity")
        if isinstance(identity_reference, dict)
        else None
    )
    latest_identity = {
        field: latest.get(field) for field in ("epoch", "revision", "scope", "status")
    }
    if identity != latest_identity:
        raise ScopeError(
            "embedded software identity does not equal the latest signature revision entry"
        )

    snapshot_source = scope["api_snapshot_source"]
    if (
        latest.get("snapshot_source_commit_sha") != snapshot_source["commit_sha"]
        or latest.get("snapshot_source_tree_sha") != snapshot_source["tree_sha"]
    ):
        raise ScopeError(
            "latest signature revision source does not equal api_snapshot_source"
        )
    expected_generation = {
        field: snapshot_source[field] for field in SIGNATURE_GENERATION_FIELDS
    }
    if latest.get("generation") != expected_generation:
        raise ScopeError(
            "latest signature revision generation metadata does not equal api_snapshot_source"
        )
    expected_profiles = sorted(
        (
            {
                "id": profile["id"],
                "public_api_snapshot": profile["public_api_snapshot"],
                "public_api_snapshot_sha256": profile["public_api_snapshot_sha256"],
            }
            for profile in scope["feature_profiles"]
        ),
        key=lambda item: item["id"],
    )
    if latest.get("profiles") != expected_profiles:
        raise ScopeError(
            "latest signature revision profile evidence does not exactly match feature_profiles"
        )

    # The source commit precedes the evidence update. The history witnesses also include HEAD,
    # every direct HEAD parent, and every HEAD-reachable commit reported by Git's full path history
    # for the registry. Deduplication keeps the work bounded to relevant commit states.
    history_candidates = [
        ("api_snapshot_source", snapshot_source["commit_sha"]),
        *checkout_history_commits(root),
    ]
    history_requests: list[tuple[str, str]] = []
    requested_commits: set[str] = set()
    for history_name, history_commit in history_candidates:
        if history_commit not in requested_commits:
            history_requests.append((history_name, history_commit))
            requested_commits.add(history_commit)
    raw_by_commit: dict[str, str | None] = {}
    for _, history_commit in history_requests:
        if history_commit not in raw_by_commit:
            raw_by_commit[history_commit] = git_file_at_commit(
                root,
                history_commit,
                SIGNATURE_REGISTRY_PATH,
            )

    historical_raw = raw_by_commit[snapshot_source["commit_sha"]]
    validate_signature_registry_genesis(
        snapshot_source,
        historical_registry_present=historical_raw is not None,
    )

    # Every retained state must be a prefix of the checked-out registry. Comparable historical
    # states must preserve one another too, which exposes buried drops, rewrites, and divergent
    # merge-side reissues instead of checking only the checkout tip.
    histories: dict[str, tuple[str, dict[str, Any] | None]] = {}
    for history_name, history_commit in history_requests:
        history_label = f"{history_name} {history_commit}"
        history_raw = raw_by_commit[history_commit]
        if history_raw is None:
            histories.setdefault(history_commit, (history_label, None))
            continue
        historical_registry = validate_signature_registry_history_text(
            registry,
            history_raw,
            registry_schema=registry_schema,
            history_label=f"{SIGNATURE_REGISTRY_PATH} at {history_label}",
        )
        histories.setdefault(history_commit, (history_label, historical_registry))
    validate_signature_registry_historical_lineage(histories, root=root)
    validate_signature_snapshot_history(entries, histories=histories, root=root)

    # The source-to-evidence and committed-HEAD-to-working-tree boundaries each permit no more
    # than one append. Older path-history witnesses may legitimately be several revisions behind.
    transition_commits = [snapshot_source["commit_sha"]]
    head_commit = git_output(root, "rev-parse", "HEAD^{commit}")
    if head_commit not in transition_commits:
        transition_commits.append(head_commit)
    for transition_commit in transition_commits:
        transition_label, transition_registry = histories[transition_commit]
        validate_signature_registry_extension(
            entries,
            [] if transition_registry is None else transition_registry["entries"],
            history_label=transition_label,
        )

    revision_four = next(
        (
            entry
            for entry in entries
            if (entry.get("epoch"), entry.get("revision"))
            == SOURCE_EVIDENCE_TOPOLOGY_REVISION
        ),
        None,
    )
    relation = None
    if revision_four is not None:
        relation = validate_revision_four_source_evidence_topology(
            revision_four,
            registry,
            root=root,
        )
    return relation


def validate_scope(
    scope: Any,
    *,
    schema: Any,
    lib_rs: Path,
    cargo_toml: Path,
    signature_registry: Any,
    signature_registry_path: Path,
    signature_registry_sha256: str,
    signature_registry_schema: Any,
    identity_reference: Any,
    root: Path,
) -> dict[str, Any] | None:
    if not isinstance(scope, dict):
        raise ScopeError("scope root must be an object")
    try:
        validate_json_schema(scope, schema, name="release-scope-1.0.json")
    except SchemaValidationError as error:
        raise ScopeError(f"JSON Schema validation failed: {error}") from error
    if scope.get("schema") != SCHEMA or scope.get("schema_revision") != SCHEMA_REVISION:
        raise ScopeError("unsupported release-scope schema")
    if scope.get("release") != "1.0.0":
        raise ScopeError("release scope must identify 1.0.0")
    blockers = scope.get("acceptance_blockers")
    if (
        not isinstance(blockers, list)
        or not blockers
        or any(not isinstance(item, str) or not item for item in blockers)
    ):
        raise ScopeError(
            "acceptance_blockers must disclose at least one concrete blocker"
        )

    families = scope.get("families")
    if not isinstance(families, list) or not families:
        raise ScopeError("families must be a non-empty array")
    family_ids: set[str] = set()
    expected_by_module: dict[str, set[str]] = {}
    for family in families:
        if not isinstance(family, dict):
            raise ScopeError("every family must be an object")
        family_id = family.get("id")
        if not isinstance(family_id, str) or not family_id or family_id in family_ids:
            raise ScopeError(f"family id must be unique and non-empty: {family_id!r}")
        family_ids.add(family_id)
        if family.get("software_stability") not in STABILITIES:
            raise ScopeError(f"{family_id}: invalid software_stability")
        module = family.get("public_module")
        if not isinstance(module, str) or not module:
            raise ScopeError(f"{family_id}: public_module is required")
        symbols = family.get("symbols")
        if (
            not isinstance(symbols, list)
            or any(
                not isinstance(symbol, str) or not IDENTIFIER_RE.fullmatch(symbol)
                for symbol in symbols
            )
            or symbols != sorted(set(symbols))
        ):
            raise ScopeError(
                f"{family_id}: symbols must be sorted unique Rust identifiers"
            )
        overlap = expected_by_module.setdefault(module, set()).intersection(symbols)
        if overlap:
            raise ScopeError(
                f"{family_id}: symbols assigned twice within {module}: {', '.join(sorted(overlap))}"
            )
        expected_by_module[module].update(symbols)
        expected_feature = MODULE_FEATURES.get(module)
        stability = family["software_stability"]
        if stability == "stable":
            if expected_feature is not None or family.get("cargo_feature") is not None:
                raise ScopeError(
                    f"{family_id}: stable families cannot require research features"
                )
            if family.get("semver_1x") is not True:
                raise ScopeError(
                    f"{family_id}: stable families must enter the proposed 1.x SemVer scope"
                )
        elif stability in {"experimental", "research-only"}:
            if (
                family.get("cargo_feature") != expected_feature
                or expected_feature is None
            ):
                raise ScopeError(
                    f"{family_id}: feature label disagrees with its public module"
                )
            if family.get("semver_1x") is not False:
                raise ScopeError(
                    f"{family_id}: research/experimental symbols cannot enter the proposed 1.x SemVer scope"
                )
        if str(family.get("definition_revision", "")).startswith("multiple-") or str(
            family.get("estimator_revision", "")
        ).startswith("multiple-"):
            raise ScopeError(
                f"{family_id}: definition and estimator revisions must be unambiguous"
            )
        for field in (
            "mathematical_family",
            "definition_revision",
            "estimator_revision",
            "support_domain",
            "required_provenance",
            "known_failure_states",
            "rust_exposure",
            "python_exposure",
            "intended_ecosystem_consumers",
            "semver_1x",
        ):
            if field not in family:
                raise ScopeError(f"{family_id}: missing {field}")

    source_observations: dict[Path, tuple[str, str]] = {}
    lib_rs_text, _ = read_utf8_with_sha256(
        lib_rs,
        label="pid-core public module source",
        observations=source_observations,
    )
    parser = RustModuleExports(lib_rs_text)

    public_modules = scope.get("public_modules")
    if (
        not isinstance(public_modules, list)
        or public_modules != sorted(set(public_modules))
        or any(not isinstance(module, str) or not module for module in public_modules)
    ):
        raise ScopeError(
            "public_modules must be a sorted unique non-empty string array"
        )
    family_modules = {family["public_module"] for family in families} - {"crate"}
    if family_modules - set(public_modules):
        raise ScopeError(
            "family modules absent from public_modules: "
            + ", ".join(sorted(family_modules - set(public_modules)))
        )
    expected_children: dict[str, set[str]] = {"crate": set()}
    for module in public_modules:
        parent, separator, child = module.rpartition("::")
        expected_children.setdefault(parent if separator else "crate", set()).add(
            child if separator else module
        )
        expected_children.setdefault(module, set())
    for parent, expected in sorted(expected_children.items()):
        actual = set(parser.child_modules(parent))
        if actual != expected:
            details = []
            if actual - expected:
                details.append(
                    "unscoped public modules: " + ", ".join(sorted(actual - expected))
                )
            if expected - actual:
                details.append(
                    "missing public modules: " + ", ".join(sorted(expected - actual))
                )
            raise ScopeError(f"{parent}: " + "; ".join(details))

    # Every public facade module is checked, including structural parents such as `stable` and
    # `experimental`. Parent modules may be symbol-empty without their own family row, but a direct
    # export added there must never remain unassigned.
    modules_to_check = set(public_modules) | {"crate"}
    for module in sorted(modules_to_check):
        expected = expected_by_module.get(module, set())
        actual = set(parser.symbols(module))
        added = sorted(actual - expected)
        missing = sorted(expected - actual)
        if added or missing:
            details = []
            if added:
                details.append("unscoped exports: " + ", ".join(added))
            if missing:
                details.append("missing exports: " + ", ".join(missing))
            raise ScopeError(f"{module}: " + "; ".join(details))

    snapshot_source = scope.get("api_snapshot_source", {})
    generation_differences = [
        f"{field}: expected {expected!r}, got {snapshot_source.get(field)!r}"
        for field, expected in API_SNAPSHOT_GENERATION.items()
        if snapshot_source.get(field) != expected
    ]
    if generation_differences:
        raise ScopeError(
            "api snapshot generation identity drifted: "
            + "; ".join(generation_differences)
        )
    unexpected_source_fields = set(snapshot_source) - {
        "commit_sha",
        "tree_sha",
        *API_SNAPSHOT_GENERATION,
    }
    if unexpected_source_fields:
        raise ScopeError(
            "api snapshot source has unexpected fields: "
            + ", ".join(sorted(unexpected_source_fields))
        )
    if set(snapshot_source) != {
        "commit_sha",
        "tree_sha",
        *API_SNAPSHOT_GENERATION,
    }:
        differences = [
            field
            for field in ("commit_sha", "tree_sha", *API_SNAPSHOT_GENERATION)
            if field not in snapshot_source
        ]
        raise ScopeError(
            "api snapshot source is missing fields: " + ", ".join(differences)
        )
    source_commit = snapshot_source.get("commit_sha")
    source_tree = snapshot_source.get("tree_sha")
    if git_output(root, "rev-parse", f"{source_commit}^{{commit}}") != source_commit:
        raise ScopeError("api snapshot source commit does not resolve to itself")
    if git_output(root, "rev-parse", f"{source_commit}^{{tree}}") != source_tree:
        raise ScopeError("api snapshot source tree does not match its commit")

    cargo_toml_text, _ = read_utf8_with_sha256(
        cargo_toml,
        label="pid-core Cargo manifest",
        observations=source_observations,
    )
    try:
        cargo = tomllib.loads(cargo_toml_text)
    except tomllib.TOMLDecodeError as error:
        raise ScopeError("pid-core Cargo manifest is not valid TOML") from error
    features = cargo.get("features")
    if not isinstance(features, dict):
        raise ScopeError("pid-core Cargo features table is missing")
    normalized_features = {
        name: list(values)
        for name, values in features.items()
        if isinstance(values, list)
    }
    if normalized_features.get("default") != []:
        raise ScopeError("pid-core default features must remain empty")

    profiles = scope.get("feature_profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ScopeError("feature_profiles must be a non-empty array")
    profile_ids: set[str] = set()
    requested_single_features: set[str] = set()
    snapshot_text_by_id: dict[str, str] = {}
    snapshot_observations: dict[Path, tuple[str, str]] = {}
    expected_profile_ids = {
        "pid-core-default",
        "pid-core-all-features",
        *(
            f"pid-core-{feature}"
            for feature in normalized_features
            if feature != "default"
        ),
    }
    for profile in profiles:
        profile_id = profile.get("id")
        if (
            not isinstance(profile_id, str)
            or not profile_id
            or profile_id in profile_ids
        ):
            raise ScopeError(f"feature profile id must be unique: {profile_id!r}")
        profile_ids.add(profile_id)
        requested = profile.get("requested_features")
        if not isinstance(requested, list) or requested != sorted(set(requested)):
            raise ScopeError(
                f"{profile_id}: requested_features must be sorted and unique"
            )
        all_features = profile.get("all_features")
        if not isinstance(all_features, bool):
            raise ScopeError(f"{profile_id}: all_features must be Boolean")
        if all_features:
            if profile_id != "pid-core-all-features" or requested:
                raise ScopeError(
                    "only pid-core-all-features may activate --all-features"
                )
            actual_closure = sorted(normalized_features)
        else:
            actual_closure = feature_closure(normalized_features, requested)
        expected_arguments = [
            "--package",
            "pid-core",
            "--no-default-features",
            "-sss",
            "--color",
            "never",
        ]
        if all_features:
            expected_arguments.append("--all-features")
        elif requested:
            expected_arguments.extend(["--features", ",".join(requested)])
        if profile.get("generation_arguments") != expected_arguments:
            raise ScopeError(
                f"{profile_id}: cargo-public-api generation arguments mismatch"
            )
        if profile.get("feature_closure") != actual_closure:
            raise ScopeError(
                f"{profile_id}: feature closure mismatch: expected {actual_closure!r}"
            )
        if not all_features and len(requested) == 1:
            requested_single_features.add(requested[0])
        snapshot_path = safe_repo_file(
            root,
            profile.get("public_api_snapshot"),
            label=f"{profile_id} public API snapshot",
        )
        snapshot, observed_digest = read_utf8_with_sha256(
            snapshot_path,
            label=f"{profile_id} public API snapshot",
            observations=snapshot_observations,
        )
        if observed_digest != profile.get("public_api_snapshot_sha256"):
            raise ScopeError(f"{profile_id}: public API snapshot digest mismatch")
        snapshot_text_by_id[profile_id] = snapshot
        for forbidden in profile.get("forbidden_public_paths", []):
            if forbidden in snapshot:
                raise ScopeError(
                    f"{profile_id}: forbidden public path is present; "
                    f"{text_observation('public_path', forbidden)}"
                )
        for required in profile.get("required_public_paths", []):
            if required not in snapshot:
                raise ScopeError(
                    f"{profile_id}: required public path is absent; "
                    f"{text_observation('public_path', required)}"
                )

    if profile_ids != expected_profile_ids:
        raise ScopeError(
            "feature profile set mismatch; missing="
            + ",".join(sorted(expected_profile_ids - profile_ids))
            + "; unexpected="
            + ",".join(sorted(profile_ids - expected_profile_ids))
        )

    validate_public_api_profile_alias_contract(profiles)

    research_features = set(normalized_features) - {
        "default",
        "parallel",
        "experimental-all",
    }
    if research_features - requested_single_features:
        raise ScopeError(
            "missing individual feature profiles: "
            + ", ".join(sorted(research_features - requested_single_features))
        )

    conditional = scope.get("conditional_members")
    if not isinstance(conditional, list):
        raise ScopeError("conditional_members must be an array")
    conditional_paths: set[str] = set()
    profile_by_feature = {
        profile["requested_features"][0]: profile
        for profile in profiles
        if len(profile["requested_features"]) == 1
    }
    default_profile = next(
        (profile for profile in profiles if profile["id"] == "pid-core-default"), None
    )
    if default_profile is None:
        raise ScopeError("a default/no-default feature profile is required")
    default_snapshot = snapshot_text_by_id[default_profile["id"]]
    for member in conditional:
        path = member.get("public_path")
        feature = member.get("feature")
        if not isinstance(path, str) or not path or path in conditional_paths:
            path_text = path if isinstance(path, str) else type(path).__name__
            raise ScopeError(
                "conditional public_path must be unique; "
                f"{text_observation('public_path', path_text)}"
            )
        conditional_paths.add(path)
        if member.get("stable_namespace_leak") is not True:
            raise ScopeError(
                "conditional member must disclose stable_namespace_leak; "
                f"{text_observation('public_path', path)}"
            )
        profile = profile_by_feature.get(feature)
        if profile is None:
            raise ScopeError(
                "conditional member has no individual profile for feature; "
                f"{text_observation('public_path', path)}"
            )
        feature_snapshot = snapshot_text_by_id[profile["id"]]
        added_line = member.get("added_api_line")
        removed_line = member.get("removed_api_line")
        if not isinstance(added_line, str) or not added_line:
            raise ScopeError(
                "conditional member exact added_api_line is required; "
                f"{text_observation('public_path', path)}"
            )
        if added_line in default_snapshot or added_line not in feature_snapshot:
            raise ScopeError(
                "conditional member exact added API line disagrees with compiled snapshots; "
                f"{text_observation('public_path', path)}"
            )
        if removed_line is not None:
            if not isinstance(removed_line, str) or not removed_line:
                raise ScopeError(
                    "conditional member removed_api_line must be null or non-empty; "
                    f"{text_observation('public_path', path)}"
                )
            if removed_line not in default_snapshot or removed_line in feature_snapshot:
                raise ScopeError(
                    "conditional member exact removed API line disagrees with compiled snapshots; "
                    f"{text_observation('public_path', path)}"
                )

    # Check complete activation profiles, not only one-feature requests. This catches public API
    # that appears under `cfg(all(feature = ...))` and would otherwise be invisible in every
    # individual feature comparison.
    for profile in profiles:
        validate_stable_profile_diff(
            profile["id"],
            set(profile["feature_closure"]),
            default_snapshot,
            snapshot_text_by_id[profile["id"]],
            conditional,
        )

    source_evidence_relation = validate_signature_revision_registry(
        scope,
        registry=signature_registry,
        registry_path=signature_registry_path,
        registry_sha256=signature_registry_sha256,
        registry_schema=signature_registry_schema,
        identity_reference=identity_reference,
        root=root,
        observations=snapshot_observations,
    )

    integrations = scope.get("integration_claims")
    required_integrations = {
        "prisoma",
        "galadriel",
        "crebain",
        "external-authority",
        "haldir",
    }
    if not isinstance(integrations, list):
        raise ScopeError("integration_claims must be an array")
    integration_ids = {item.get("integration_id") for item in integrations}
    if integration_ids != required_integrations:
        raise ScopeError(
            "integration_claims must name every optional downstream integration"
        )
    for integration in integrations:
        if integration.get("claim_status") not in CLAIM_STATUSES:
            raise ScopeError(f"invalid integration claim status: {integration!r}")
        if integration.get("claim_status") != "not_claimed":
            raise ScopeError(
                f"{integration['integration_id']}: this core-only candidate must remain not_claimed"
            )

    prohibited = scope.get("prohibited_claims")
    if not isinstance(prohibited, list) or len(prohibited) < 8:
        raise ScopeError("at least eight explicit prohibited 1.0 claims are required")

    approvals = scope.get("review_approvals")
    required_roles = {"maintainer", "independent_scientific_reviewer"}
    if (
        not isinstance(approvals, list)
        or {item.get("role") for item in approvals} != required_roles
    ):
        raise ScopeError(
            "review_approvals must name maintainer and independent reviewer roles"
        )
    reviewers_by_role: dict[str, str] = {}
    for approval in approvals:
        status = approval.get("status")
        if status not in {"pending", "approved", "rejected"}:
            raise ScopeError(f"invalid review approval status: {approval!r}")
        if approval.get("commit_binding") != "api_snapshot_source_commit":
            raise ScopeError(f"{approval['role']}: unsupported approval commit binding")
        role = approval["role"]
        detail_fields = (
            "reviewer",
            "commit_sha",
            "evidence",
            "conflict_disclosure",
        )
        approval_details = {field: approval.get(field) for field in detail_fields}
        independence = approval.get("independence_statement")

        commit_sha = approval.get("commit_sha")
        if commit_sha is not None:
            if git_output(root, "rev-parse", f"{commit_sha}^{{commit}}") != commit_sha:
                raise ScopeError(f"{role}: review commit does not resolve to itself")
            if commit_sha != source_commit:
                raise ScopeError(
                    f"{role}: review commit must equal the frozen api_snapshot_source commit"
                )
        evidence = approval.get("evidence")
        if evidence is not None:
            safe_repo_file(root, evidence, label=f"{role} review evidence")

        if status == "pending":
            if any(
                value is not None
                for value in (*approval_details.values(), independence)
            ):
                raise ScopeError(f"{role}: pending review fields must all remain null")
            continue

        if any(
            not isinstance(value, str) or not value
            for value in approval_details.values()
        ):
            raise ScopeError(
                f"{role}: a decided review requires reviewer, commit, evidence, and conflict disclosure"
            )
        reviewer = approval_details["reviewer"]
        reviewers_by_role[role] = reviewer
        if role == "maintainer":
            if reviewer != EXPECTED_MAINTAINER:
                raise ScopeError(
                    f"maintainer review must be recorded by {EXPECTED_MAINTAINER}"
                )
            if independence is not None:
                raise ScopeError(
                    "maintainer review independence_statement must be null"
                )
        else:
            if reviewer == EXPECTED_MAINTAINER:
                raise ScopeError("independent reviewer cannot be the maintainer/author")
            if not isinstance(independence, str) or not independence:
                raise ScopeError(
                    "independent reviewer decision requires an independence_statement"
                )

    if len(set(reviewers_by_role.values())) != len(reviewers_by_role):
        raise ScopeError("maintainer and independent reviewer must be different people")
    return source_evidence_relation


def markdown_cell(value: Any) -> str:
    if isinstance(value, list):
        rendered = "; ".join(str(item) for item in value)
    elif isinstance(value, bool):
        rendered = "yes" if value else "no"
    elif value is None:
        rendered = "—"
    else:
        rendered = str(value)
    return rendered.replace("|", "\\|").replace("\n", " ")


def render_markdown(scope: dict[str, Any], signature_registry: dict[str, Any]) -> str:
    lines = [
        "# pid-rs 1.0 release scope",
        "",
        "> **Scope state:** proposed 1.0 boundary for external review. The software publication",
        "> target is 0.9.0 first. This document does not claim 1.0 publication, registry availability,",
        "> independent acceptance, application validity, or a 1.x compatibility promise.",
        "",
        "The machine-readable source is `release-scope-1.0.json`. The scope checker regenerates",
        "this rendered view; the coherence job also rebuilds every compiled API profile and rejects",
        "unlisted `pid-core` exports/modules, stable-namespace drift, feature-closure changes, snapshot",
        "changes, schema violations, or ambiguous integration status.",
        "",
        "Enabling a research feature changes only software availability. It does **not** promote",
        "scientific maturity, widen support, establish calibration, or create a 1.x SemVer promise.",
        "",
        "## Capability matrix",
        "",
        "| ID | Public module | Cargo feature | Stability | Mathematical family / definition | Estimator revision | Support domain | Required provenance | Known failures | Rust | Python | Intended consumers | Proposed 1.x SemVer scope |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for family in scope["families"]:
        lines.append(
            "| {id} | `{module}` | {feature} | {stability} | {math} / `{definition}` | `{estimator}` | {support} | {provenance} | {failures} | {rust} | {python} | {consumers} | {semver} |".format(
                id=family["id"],
                module=family["public_module"],
                feature=markdown_cell(family["cargo_feature"]),
                stability=family["software_stability"],
                math=markdown_cell(family["mathematical_family"]),
                definition=family["definition_revision"],
                estimator=family["estimator_revision"],
                support=markdown_cell(family["support_domain"]),
                provenance=markdown_cell(family["required_provenance"]),
                failures=markdown_cell(family["known_failure_states"]),
                rust=markdown_cell(family["rust_exposure"]),
                python=markdown_cell(family["python_exposure"]),
                consumers=markdown_cell(family["intended_ecosystem_consumers"]),
                semver=markdown_cell(family["semver_1x"]),
            )
        )

    lines.extend(["", "## Exact public symbols", ""])
    for family in scope["families"]:
        lines.extend(
            [
                f"### `{family['id']}`",
                "",
                f"Module: `{family['public_module']}`. Export count: {len(family['symbols'])}.",
                "",
                "```text",
                *family["symbols"],
                "```",
                "",
            ]
        )

    conditional_members = scope["conditional_members"]
    if conditional_members:
        lines.extend(
            [
                "## Known stable-namespace leaks that block API freeze",
                "",
                "These members appear only when a research feature is enabled but mutate types also",
                "exported through stable/top-level paths. They are recorded as blockers, not approved",
                "1.x stable API. They must move behind a research-only type or entry point before the",
                "1.x API can freeze.",
                "",
                "| Public path | Feature | Kind | Removed default signature | 1.x promise |",
                "|---|---|---|---|---|",
            ]
        )
        for member in conditional_members:
            lines.append(
                f"| `{member['public_path']}` | `{member['feature']}` | {member['kind']} | {markdown_cell(member['removed_api_line'])} | no |"
            )
    else:
        lines.extend(
            [
                "## Stable-namespace feature isolation",
                "",
                "No checked feature profile adds or removes a stable or top-level public API line",
                "relative to the default snapshot. Feature-only APIs are isolated under the",
                "experimental namespace.",
            ]
        )

    registry_pointer = scope["public_rust_api_signature_revision_registry"]
    lines.extend(
        [
            "",
            "## Public Rust declaration-signature revision evidence",
            "",
            "The runtime declaration-signature identity is bound to the append-only registry",
            f"`{registry_pointer['repository_path']}` (SHA-256",
            f"`{registry_pointer['canonical_json_sha256']}`). Each revision records the exact",
            "source commit/tree, generation context, and every proposed feature-profile snapshot",
            "digest. Here *signature* means a normalized list of public Rust declarations; it is",
            "not cryptographic signing. The source commit/tree identifies the code whose",
            "declarations were generated. In the two-phase evidence flow, the immutable snapshot",
            "bytes live at the revision-scoped paths added by the evidence update and need not",
            "exist in that earlier source commit. This is declaration-signature evidence only:",
            "equality does not establish compatibility, behavior,",
            "scientific validity, application validity, executable identity, or numeric parity.",
            "Append preservation is checked against the source anchor, HEAD, every direct HEAD",
            "parent, and every registry-touch commit reachable from HEAD through Git's full path",
            "history. Once a committed registry binding is an ancestor, each snapshot path's exact",
            "byte digest is checked at binding states, HEAD/direct-parent boundaries, and every",
            "reachable commit in that snapshot's full path history. Pre-binding states and paths",
            "first bound only in the working tree are outside that historical interval; current",
            "working-tree bytes are still checked exactly. Git queries discard ambient routing,",
            "object, configuration, namespace, shallow-file, replacement, and pathspec inputs;",
            "replacement/graft overlays are disabled, and Git's canonical worktree root must",
            "equal the repository whose current files are checked. This covers only the reachable",
            "objects",
            "presented to the checker. It cannot observe a never-merged branch that is no longer",
            "reachable, deleted references, or an externally replaced history without an",
            "independent remote or transparency witness.",
            "Revision 0-4 additionally binds ten logical activations to nine physical files.",
            "The all-features and experimental-all commands remain semantically distinct and",
            "are generated independently; they share a path only because their exact outputs",
            "match. All nine files must first appear together in one single-parent evidence",
            "commit whose sole parent is the registered source commit. The source/evidence pair",
            "therefore fails closed after squash, rebase, split addition, or cherry-pick onto a",
            "different parent; no unknown future evidence-commit hash is embedded in source.",
            "",
            "| Epoch | Revision | Status | Scope | Source commit | Source tree | Profiles |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for entry in signature_registry["entries"]:
        lines.append(
            "| {epoch} | {revision} | `{status}` | `{scope}` | `{commit}` | `{tree}` | {profiles} |".format(
                epoch=entry["epoch"],
                revision=entry["revision"],
                status=entry["status"],
                scope=entry["scope"],
                commit=entry["snapshot_source_commit_sha"],
                tree=entry["snapshot_source_tree_sha"],
                profiles=len(entry["profiles"]),
            )
        )

    lines.extend(["", "## Optional integration claims", ""])
    for integration in scope["integration_claims"]:
        lines.append(
            f"- `{integration['integration_id']}`: **{integration['claim_status']}** — {integration['reason']}"
        )

    lines.extend(["", "## Acceptance blockers", ""])
    lines.extend(f"- {blocker}" for blocker in scope["acceptance_blockers"])
    lines.extend(["", "## Review approvals", ""])
    for approval in scope["review_approvals"]:
        lines.append(
            "- `{role}`: **{status}**; binding: `{binding}`; reviewer: {reviewer}; "
            "commit: {commit}; evidence: {evidence}; conflicts: {conflicts}; "
            "independence: {independence}".format(
                role=approval["role"],
                status=approval["status"],
                binding=approval["commit_binding"],
                reviewer=markdown_cell(approval["reviewer"]),
                commit=markdown_cell(approval["commit_sha"]),
                evidence=markdown_cell(approval["evidence"]),
                conflicts=markdown_cell(approval["conflict_disclosure"]),
                independence=markdown_cell(approval["independence_statement"]),
            )
        )

    lines.extend(["", "## Prohibited 1.0 claims", ""])
    lines.extend(f"- {claim}" for claim in scope["prohibited_claims"])
    lines.extend(["", "## Unsupported in 1.0", ""])
    lines.extend(f"- {claim}" for claim in scope["unsupported_in_1_0"])

    lines.extend(
        [
            "",
            "## Compiled public-API snapshots",
            "",
            "Snapshots were generated with the pinned tool recorded in this scope file. They are",
            "ten logical activation results retained as nine physical files; they are signature",
            "evidence, not scientific-validation evidence.",
            "",
            "| Profile | Activation | Requested features | Feature closure | Snapshot | SHA-256 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for profile in scope["feature_profiles"]:
        lines.append(
            "| `{id}` | {activation} | {requested} | {closure} | `{path}` | `{digest}` |".format(
                id=profile["id"],
                activation="`--all-features`"
                if profile["all_features"]
                else "explicit feature set",
                requested=markdown_cell(profile["requested_features"]),
                closure=markdown_cell(profile["feature_closure"]),
                path=profile["public_api_snapshot"],
                digest=profile["public_api_snapshot_sha256"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def require_isolated_source_evidence_invocation() -> None:
    """Require the publication bridge's exact supported Python execution modes."""

    if not (
        sys.version_info >= (3, 11)
        and sys.flags.isolated == 1
        and sys.flags.safe_path
        and sys.flags.no_site == 1
        and sys.flags.ignore_environment == 1
        and sys.dont_write_bytecode
        and sys.flags.optimize in {0, 1}
    ):
        raise ScopeError(
            "--source-evidence-relation-json requires Python 3.11+ -I -S -B "
            "and at most one -O"
        )


def require_canonical_source_evidence_inputs(args: argparse.Namespace) -> None:
    """Forbid alternate fixture inputs from producing a canonical bridge result."""

    expected_paths = {
        "scope": DEFAULT_SCOPE,
        "schema": DEFAULT_SCHEMA,
        "markdown": DEFAULT_MARKDOWN,
        "signature_registry": DEFAULT_SIGNATURE_REGISTRY,
        "signature_registry_schema": DEFAULT_SIGNATURE_REGISTRY_SCHEMA,
        "software_identity_reference": DEFAULT_SOFTWARE_IDENTITY_REFERENCE,
        "lib_rs": DEFAULT_LIB_RS,
        "cargo_toml": DEFAULT_CARGO,
    }
    for field, expected in expected_paths.items():
        actual = Path(os.path.abspath(os.fspath(getattr(args, field))))
        if actual != expected:
            raise ScopeError(
                "--source-evidence-relation-json accepts only canonical repository inputs"
            )


def source_evidence_result(relation: dict[str, Any] | None) -> dict[str, Any]:
    """Build the bounded publication bridge, refusing the pre-evidence candidate state."""

    if relation is None:
        raise ScopeError(
            "revision-4 source/evidence relation is pending; no passing relation is available"
        )
    if set(relation) != {
        "source_commit",
        "evidence_commit",
        "evidence_parent_count",
    }:
        raise ScopeError("revision-4 source/evidence relation has an unexpected shape")
    source_commit = relation["source_commit"]
    evidence_commit = relation["evidence_commit"]
    evidence_parent_count = relation["evidence_parent_count"]
    if (
        not isinstance(source_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
        or not isinstance(evidence_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", evidence_commit) is None
        or source_commit == evidence_commit
        or not isinstance(evidence_parent_count, int)
        or isinstance(evidence_parent_count, bool)
        or evidence_parent_count != 1
    ):
        raise ScopeError("revision-4 source/evidence relation is invalid")
    return {
        "format": SOURCE_EVIDENCE_RELATION_FORMAT,
        "source_evidence_relation": relation,
        "status": "pass",
    }


def canonical_json(value: Any) -> str:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--signature-registry", type=Path, default=DEFAULT_SIGNATURE_REGISTRY
    )
    parser.add_argument(
        "--signature-registry-schema",
        type=Path,
        default=DEFAULT_SIGNATURE_REGISTRY_SCHEMA,
    )
    parser.add_argument(
        "--software-identity-reference",
        type=Path,
        default=DEFAULT_SOFTWARE_IDENTITY_REFERENCE,
    )
    parser.add_argument("--lib-rs", type=Path, default=DEFAULT_LIB_RS)
    parser.add_argument("--cargo-toml", type=Path, default=DEFAULT_CARGO)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--print-markdown", action="store_true")
    output.add_argument("--source-evidence-relation-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.source_evidence_relation_json:
            require_isolated_source_evidence_invocation()
            require_canonical_source_evidence_inputs(args)
        scope = load_json(args.scope, canonical=True, label="release scope")
        schema = load_json(args.schema, label="release scope schema")
        signature_registry, signature_registry_sha256 = load_json_with_sha256(
            args.signature_registry,
            canonical=True,
            label="signature registry",
        )
        signature_registry_schema = load_json(
            args.signature_registry_schema,
            label="signature registry schema",
        )
        identity_reference = load_json(
            args.software_identity_reference,
            canonical=True,
            label="software identity reference",
        )
        source_evidence_relation = validate_scope(
            scope,
            schema=schema,
            lib_rs=args.lib_rs,
            cargo_toml=args.cargo_toml,
            signature_registry=signature_registry,
            signature_registry_path=args.signature_registry,
            signature_registry_sha256=signature_registry_sha256,
            signature_registry_schema=signature_registry_schema,
            identity_reference=identity_reference,
            root=ROOT,
        )
        rendered = render_markdown(scope, signature_registry)
        if args.print_markdown:
            print(rendered, end="")
        else:
            try:
                committed = args.markdown.read_text(encoding="utf-8")
            except OSError as error:
                raise ScopeError(
                    "cannot read rendered scope; "
                    f"{path_observation(args.markdown)}; {os_error_observation(error)}"
                ) from error
            if committed != rendered:
                raise ScopeError(
                    "rendered scope is stale; regenerate it with --print-markdown; "
                    f"{path_observation(args.markdown)}"
                )
            if args.source_evidence_relation_json:
                latest_entry = signature_registry["entries"][-1]
                if (
                    latest_entry.get("epoch"),
                    latest_entry.get("revision"),
                ) != SOURCE_EVIDENCE_TOPOLOGY_REVISION:
                    raise ScopeError(
                        "source/evidence relation output requires revision 0-4 to be "
                        "the current canonical API revision"
                    )
                print(
                    canonical_json(source_evidence_result(source_evidence_relation)),
                    end="",
                )
            else:
                print(
                    f"OK: {len(scope['families'])} capability rows and "
                    f"{sum(len(item['symbols']) for item in scope['families'])} source exports match"
                )
        return 0
    except ScopeError as error:
        print(
            "release scope error: " + public_failure_message(error),
            file=sys.stderr,
        )
        return 1
    except OSError as error:
        print(
            "release scope error: unexpected filesystem failure; "
            + os_error_observation(error),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
