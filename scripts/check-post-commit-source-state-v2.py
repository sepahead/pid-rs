#!/usr/bin/env python3
"""Emit or validate the deterministic post-commit source-state artifact v2.

The tracked ``current-source-state-v1`` manifest deliberately excludes itself and
contains no commit identifier.  After that manifest is committed, this checker
validates it against the exact ``HEAD`` tree and emits canonical JSON on standard
output.  Validation consumes canonical JSON from standard input.  Storage and
publication are deliberately caller-owned and outside this artifact's claims.
The artifact is identity evidence only: it is not authenticity, review, or
scientific evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-post-commit-source-state-v2.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
GIT_EXECUTABLE = Path("/usr/bin/git")
POST_SCHEMA_RELATIVE = "audit/schemas/post-commit-source-state-v2.schema.json"
DEFAULT_SCHEMA = ROOT / POST_SCHEMA_RELATIVE
CURRENT_MANIFEST_RELATIVE = "audit/evidence/current-source-state-v1.json"
CURRENT_SCHEMA_RELATIVE = "audit/schemas/current-source-state-v1.schema.json"
CURRENT_CHECKER_RELATIVE = "scripts/check-current-source-state-v1.py"
SCHEMA_NAME = "pid-rs/post-commit-source-state"
SCHEMA_REVISION = 2
CURRENT_SCHEMA_NAME = "pid-rs/current-source-state"
CURRENT_SCHEMA_REVISION = 1
GENERATOR = "scripts/check-post-commit-source-state-v2.py"
REPOSITORY = "sepahead/pid-rs"
HEX_RE = re.compile(r"^[0-9a-f]+$")
MAX_ARTIFACT_BYTES = 1024 * 1024
EXPECTED_CURRENT_SCHEMA_SHA256 = (
    "1027cc3826aa6933a23dea1736b5d007b9c5bc1568f41ac87dea98e5f2924a97"
)
EXPECTED_POST_SCHEMA_SHA256 = (
    "2f4531f4cde575d3bbb573d09a85a27664fef5c4f0fde32b232498460c9a198a"
)
NONIMPLICATIONS = (
    "This post-commit identity artifact is not authentication, authenticity, "
    "attestation, provenance, or proof of repository origin.",
    "It does not establish line review, human review, independent review, "
    "institutional review, or review completion.",
    "It does not establish scientific validity, estimator validity, formal "
    "correctness, source-to-formal correspondence, implementation refinement, "
    "numerical correctness, or application validity.",
    "Commit, tree, blob, and SHA-256 identifiers bind exact bytes under named "
    "algorithms; they do not confer trust or authenticity.",
    "Generation is bounded execution evidence for one committed state, not a "
    "CI-pass, release, tag, or fact about any other commit.",
    "Repeated endpoint checks are not an atomic history against concurrent "
    "filesystem or repository mutation.",
    "Repository-ignored products and Git object-store internals are outside this "
    "committed-tree identity projection.",
    "Emission uses standard output and validation uses standard input; this artifact "
    "does not bind storage location, filesystem identity, durability, or upload custody.",
)


class PostCommitStateError(RuntimeError):
    """Post-commit source-state collection or validation failed."""


def exact_regular_bytes(path: Path, label: str) -> bytes:
    """Read one single-link regular file while checking endpoint identity."""
    try:
        before = path.lstat()
    except OSError as error:
        raise PostCommitStateError(f"cannot stat {label} {path}: {error}") from error
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise PostCommitStateError(f"{label} is not a single-link regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise PostCommitStateError(f"cannot open {label} {path}: {error}") from error
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        raise PostCommitStateError(f"cannot restat {label} {path}: {error}") from error

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

    data = b"".join(chunks)
    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(data) == before.st_size
    ):
        raise PostCommitStateError(f"{label} changed during exact read: {path}")
    return data


OBSERVED_CHECKER_SOURCE = exact_regular_bytes(
    ROOT / GENERATOR, "post-commit source-state checker"
)


def parse_mode(arguments: list[str]) -> str:
    if arguments == ["--emit"]:
        return "emit"
    if arguments == ["--validate-stdin"]:
        return "validate-stdin"
    raise PostCommitStateError(
        "usage: check-post-commit-source-state-v2.py (--emit | --validate-stdin)"
    )


def reject_constant(value: str) -> Any:
    raise PostCommitStateError(f"non-finite JSON constant is forbidden: {value}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PostCommitStateError(f"cannot canonicalize JSON: {error}") from error


def compact_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PostCommitStateError(
            f"cannot canonicalize compact JSON: {error}"
        ) from error


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_canonical_json_bytes(data: bytes, label: str) -> Any:
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, PostCommitStateError) as error:
        raise PostCommitStateError(f"cannot parse {label}: {error}") from error
    if data != canonical_bytes(value):
        raise PostCommitStateError(f"{label} is not canonical sorted UTF-8 JSON")
    return value


def load_canonical_json(path: Path, label: str) -> tuple[Any, bytes]:
    data = exact_regular_bytes(path, label)
    return parse_canonical_json_bytes(data, label), data


def safe_environment() -> dict[str, str]:
    """Construct a narrow environment for every Git and child-checker call."""
    return {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
    }


def git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    try:
        before = GIT_EXECUTABLE.lstat()
        resolved = GIT_EXECUTABLE.resolve(strict=True)
    except OSError as error:
        raise PostCommitStateError(
            f"cannot inspect fixed Git executable {GIT_EXECUTABLE}: {error}"
        ) from error
    if resolved != GIT_EXECUTABLE or not stat.S_ISREG(before.st_mode):
        raise PostCommitStateError(
            f"fixed Git executable is not a canonical regular file: {GIT_EXECUTABLE}"
        )
    command = [
        os.fspath(GIT_EXECUTABLE),
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        f"core.attributesFile={os.devnull}",
        "-C",
        str(root),
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            env=safe_environment(),
            input=b"" if input_bytes is None else input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PostCommitStateError(
            f"cannot run fixed Git executable: {error}"
        ) from error
    try:
        after = GIT_EXECUTABLE.lstat()
    except OSError as error:
        raise PostCommitStateError(
            f"cannot recheck fixed Git executable {GIT_EXECUTABLE}: {error}"
        ) from error
    if filesystem_identity(before) != filesystem_identity(after):
        raise PostCommitStateError("fixed Git executable changed across invocation")
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PostCommitStateError(
            f"Git command failed ({completed.returncode}): {arguments}: {stderr}"
        )
    return completed.stdout


def ensure_git_root(root: Path) -> None:
    reported_raw = git(root, "rev-parse", "--show-toplevel")
    try:
        reported = Path(reported_raw.decode("utf-8").strip()).resolve(strict=True)
    except (UnicodeDecodeError, OSError) as error:
        raise PostCommitStateError(
            f"Git root is not a resolvable UTF-8 path: {error}"
        ) from error
    if reported != root.resolve(strict=True):
        raise PostCommitStateError(
            f"requested root {root} is not canonical Git root {reported}"
        )


def oid_length(object_format: str) -> int:
    if object_format == "sha1":
        return 40
    if object_format == "sha256":
        return 64
    raise PostCommitStateError(f"unsupported Git object format: {object_format!r}")


def require_oid(value: str, object_format: str, label: str) -> None:
    if len(value) != oid_length(object_format) or HEX_RE.fullmatch(value) is None:
        raise PostCommitStateError(
            f"{label} is not a canonical {object_format} object identifier"
        )


def decode_repository_path(raw: bytes, label: str) -> str:
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PostCommitStateError(f"{label} is not UTF-8: {error}") from error
    pure = PurePosixPath(value)
    if (
        not value
        or value.startswith("/")
        or ".." in pure.parts
        or pure.as_posix() != value
    ):
        raise PostCommitStateError(f"unsafe or noncanonical repository path: {value!r}")
    return value


def decode_z_paths(raw: bytes, label: str) -> list[str]:
    if raw and not raw.endswith(b"\0"):
        raise PostCommitStateError(f"{label} output lacks NUL termination")
    records = raw[:-1].split(b"\0") if raw else []
    paths = [decode_repository_path(record, label) for record in records]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise PostCommitStateError(f"{label} paths are not sorted unique")
    return paths


def parse_head_tree(root: Path, object_format: str) -> list[dict[str, str]]:
    raw = git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    if raw and not raw.endswith(b"\0"):
        raise PostCommitStateError("HEAD tree output lacks NUL termination")
    records = raw[:-1].split(b"\0") if raw else []
    entries: list[dict[str, str]] = []
    for record in records:
        try:
            prefix, raw_path = record.split(b"\t", 1)
            raw_mode, raw_type, raw_oid = prefix.split(b" ", 2)
            mode = raw_mode.decode("ascii")
            object_type = raw_type.decode("ascii")
            oid = raw_oid.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PostCommitStateError(
                f"cannot parse HEAD tree record: {error}"
            ) from error
        path = decode_repository_path(raw_path, "HEAD tree path")
        if object_type != "blob" or mode not in {"100644", "100755", "120000"}:
            raise PostCommitStateError(
                f"unsupported HEAD tree entry {mode} {object_type} for {path!r}"
            )
        require_oid(oid, object_format, f"HEAD blob for {path!r}")
        entries.append({"mode": mode, "oid": oid, "path": path})
    paths = [entry["path"] for entry in entries]
    if not entries or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise PostCommitStateError("HEAD tree paths are not nonempty sorted unique")
    return entries


def parse_index(root: Path, object_format: str) -> list[dict[str, str]]:
    raw = git(root, "ls-files", "--stage", "-z")
    if raw and not raw.endswith(b"\0"):
        raise PostCommitStateError("Git index output lacks NUL termination")
    records = raw[:-1].split(b"\0") if raw else []
    entries: list[dict[str, str]] = []
    for record in records:
        try:
            prefix, raw_path = record.split(b"\t", 1)
            raw_mode, raw_oid, raw_stage = prefix.split(b" ", 2)
            mode = raw_mode.decode("ascii")
            oid = raw_oid.decode("ascii")
            stage = raw_stage.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PostCommitStateError(
                f"cannot parse Git index record: {error}"
            ) from error
        path = decode_repository_path(raw_path, "Git index path")
        if stage != "0" or mode not in {"100644", "100755", "120000"}:
            raise PostCommitStateError(
                f"unmerged or unsupported Git index entry for {path!r}"
            )
        require_oid(oid, object_format, f"index blob for {path!r}")
        entries.append({"mode": mode, "oid": oid, "path": path})
    paths = [entry["path"] for entry in entries]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise PostCommitStateError("Git index paths are not sorted unique")
    return entries


def read_head_blobs(
    root: Path, entries: list[dict[str, str]], object_format: str
) -> list[bytes]:
    query = b"".join(entry["oid"].encode("ascii") + b"\n" for entry in entries)
    output = git(root, "cat-file", "--batch", input_bytes=query)
    offset = 0
    blobs: list[bytes] = []
    for entry in entries:
        newline = output.find(b"\n", offset)
        if newline < 0:
            raise PostCommitStateError("Git cat-file batch response lacks a header")
        try:
            raw_oid, raw_type, raw_size = output[offset:newline].split(b" ", 2)
            oid = raw_oid.decode("ascii")
            object_type = raw_type.decode("ascii")
            size = int(raw_size.decode("ascii"), 10)
        except (ValueError, UnicodeDecodeError) as error:
            raise PostCommitStateError(
                f"cannot parse Git cat-file header: {error}"
            ) from error
        require_oid(oid, object_format, "cat-file blob")
        if oid != entry["oid"] or object_type != "blob" or size < 0:
            raise PostCommitStateError(
                f"Git cat-file returned the wrong object for {entry['path']!r}"
            )
        start = newline + 1
        end = start + size
        if end >= len(output) or output[end : end + 1] != b"\n":
            raise PostCommitStateError(
                f"Git cat-file response is truncated for {entry['path']!r}"
            )
        blobs.append(output[start:end])
        offset = end + 1
    if offset != len(output):
        raise PostCommitStateError("Git cat-file batch response has trailing bytes")
    return blobs


def filesystem_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_worktree_entry(root: Path, entry: dict[str, str]) -> bytes:
    path = entry["path"]
    absolute = root.joinpath(*PurePosixPath(path).parts)
    try:
        before = absolute.lstat()
    except OSError as error:
        raise PostCommitStateError(
            f"cannot stat tracked path {path!r}: {error}"
        ) from error
    if entry["mode"] == "120000":
        if not stat.S_ISLNK(before.st_mode):
            raise PostCommitStateError(f"tracked symlink is not a symlink: {path!r}")
        try:
            data = os.readlink(os.fsencode(absolute))
        except OSError as error:
            raise PostCommitStateError(
                f"cannot read tracked symlink {path!r}: {error}"
            ) from error
        actual_mode = "120000"
        try:
            after = absolute.lstat()
        except OSError as error:
            raise PostCommitStateError(
                f"cannot restat tracked symlink {path!r}: {error}"
            ) from error
        if filesystem_identity(before) != filesystem_identity(after):
            raise PostCommitStateError(
                f"tracked symlink changed during exact read: {path!r}"
            )
    else:
        if not stat.S_ISREG(before.st_mode):
            raise PostCommitStateError(f"tracked path is not regular: {path!r}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(absolute, flags)
        except OSError as error:
            raise PostCommitStateError(
                f"cannot open tracked path {path!r}: {error}"
            ) from error
        try:
            opened = os.fstat(descriptor)
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 1024 * 1024):
                chunks.append(chunk)
            closed = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        try:
            after = absolute.lstat()
        except OSError as error:
            raise PostCommitStateError(
                f"cannot restat tracked path {path!r}: {error}"
            ) from error
        data = b"".join(chunks)
        if not (
            filesystem_identity(before)
            == filesystem_identity(opened)
            == filesystem_identity(closed)
            == filesystem_identity(after)
            and len(data) == before.st_size
        ):
            raise PostCommitStateError(
                f"tracked path changed during exact read: {path!r}"
            )
        actual_mode = "100755" if before.st_mode & 0o111 else "100644"
    if actual_mode != entry["mode"]:
        raise PostCommitStateError(
            f"tracked worktree mode differs from HEAD for {path!r}: "
            f"{actual_mode} != {entry['mode']}"
        )
    return data


def collect_committed_state(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    ensure_git_root(root)
    try:
        object_format = (
            git(root, "rev-parse", "--show-object-format").decode("ascii").strip()
        )
        commit_oid = (
            git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        )
        tree_oid = (
            git(root, "rev-parse", "--verify", "HEAD^{tree}").decode("ascii").strip()
        )
    except UnicodeDecodeError as error:
        raise PostCommitStateError(
            f"Git identity output is not ASCII: {error}"
        ) from error
    require_oid(commit_oid, object_format, "HEAD commit")
    require_oid(tree_oid, object_format, "HEAD tree")

    tree_entries = parse_head_tree(root, object_format)
    index_entries = parse_index(root, object_format)
    if index_entries != tree_entries:
        raise PostCommitStateError(
            "Git index does not exactly equal the committed HEAD tree"
        )

    untracked = decode_z_paths(
        git(root, "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"),
        "repository-visible untracked files",
    )
    if untracked:
        rendered = ", ".join(repr(path) for path in untracked[:8])
        suffix = " ..." if len(untracked) > 8 else ""
        raise PostCommitStateError(
            f"repository-visible untracked paths prevent post-commit binding: "
            f"{rendered}{suffix}"
        )

    blobs = read_head_blobs(root, tree_entries, object_format)
    for entry, blob in zip(tree_entries, blobs):
        observed = read_worktree_entry(root, entry)
        if observed != blob:
            raise PostCommitStateError(
                f"tracked worktree bytes differ from HEAD blob for {entry['path']!r}"
            )

    if (
        git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        != commit_oid
        or git(root, "rev-parse", "--verify", "HEAD^{tree}").decode("ascii").strip()
        != tree_oid
        or parse_index(root, object_format) != index_entries
        or decode_z_paths(
            git(
                root,
                "ls-files",
                "--others",
                "--exclude-per-directory=.gitignore",
                "-z",
            ),
            "repository-visible untracked files",
        )
        != untracked
    ):
        raise PostCommitStateError(
            "repository state changed during committed-state endpoint checks"
        )

    return {
        "blobs": blobs,
        "commit_oid": commit_oid,
        "git_object_format": object_format,
        "tree_entries": tree_entries,
        "tree_oid": tree_oid,
    }


def state_blob_map(state: dict[str, Any]) -> dict[str, tuple[dict[str, str], bytes]]:
    mapping = {
        entry["path"]: (entry, blob)
        for entry, blob in zip(state["tree_entries"], state["blobs"])
    }
    if len(mapping) != len(state["tree_entries"]):
        raise PostCommitStateError("committed tree contains duplicate paths")
    return mapping


def validate_post_commit_dependencies(root: Path, state: dict[str, Any]) -> None:
    mapping = state_blob_map(state)
    for relative, label in (
        (GENERATOR, "post-commit source-state checker"),
        (POST_SCHEMA_RELATIVE, "post-commit source-state schema"),
    ):
        try:
            entry, head_bytes = mapping[relative]
        except KeyError as error:
            raise PostCommitStateError(
                f"required committed post-commit path is absent: {relative}"
            ) from error
        if entry["mode"] not in {"100644", "100755"}:
            raise PostCommitStateError(f"committed {label} is not regular")
        if exact_regular_bytes(root / relative, f"committed {label}") != head_bytes:
            raise PostCommitStateError(f"committed {label} differs from its HEAD blob")
        if relative == GENERATOR and head_bytes != OBSERVED_CHECKER_SOURCE:
            raise PostCommitStateError(
                "committed post-commit checker differs from the exact loaded source"
            )


def validate_current_manifest(state: dict[str, Any]) -> dict[str, Any]:
    mapping = state_blob_map(state)
    try:
        manifest_entry, manifest_bytes = mapping[CURRENT_MANIFEST_RELATIVE]
        schema_entry, schema_bytes = mapping[CURRENT_SCHEMA_RELATIVE]
    except KeyError as error:
        raise PostCommitStateError(
            f"required committed source-state path is absent: {error.args[0]}"
        ) from error
    if manifest_entry["mode"] not in {"100644", "100755"}:
        raise PostCommitStateError(
            "committed current-source-state manifest is not regular"
        )
    if schema_entry["mode"] not in {"100644", "100755"}:
        raise PostCommitStateError(
            "committed current-source-state schema is not regular"
        )

    schema = parse_canonical_json_bytes(
        schema_bytes, "committed current-source-state schema"
    )
    manifest = parse_canonical_json_bytes(
        manifest_bytes, "committed current-source-state manifest"
    )
    if not isinstance(schema, dict):
        raise PostCommitStateError(
            "committed current-source-state schema is not an object"
        )
    if sha256_bytes(schema_bytes) != EXPECTED_CURRENT_SCHEMA_SHA256:
        raise PostCommitStateError(
            "committed current-source-state schema bytes changed"
        )

    expected_entries = [
        {
            "git_mode": entry["mode"],
            "path": entry["path"],
            "sha256": sha256_bytes(blob),
            "size_bytes": len(blob),
        }
        for entry, blob in zip(state["tree_entries"], state["blobs"])
        if entry["path"] != CURRENT_MANIFEST_RELATIVE
    ]
    try:
        binding = manifest["binding"]
        projection = manifest["source_projection"]
        manifest_entries = projection["entries"]
    except (KeyError, TypeError) as error:
        raise PostCommitStateError(
            "committed current-source-state manifest lacks its projection"
        ) from error
    if (
        manifest.get("schema") != CURRENT_SCHEMA_NAME
        or manifest.get("schema_revision") != CURRENT_SCHEMA_REVISION
        or binding.get("excluded_paths") != [CURRENT_MANIFEST_RELATIVE]
        or binding.get("scope_kind") != "self_excluding_worktree_source_projection"
        or CURRENT_MANIFEST_RELATIVE
        in {entry.get("path") for entry in manifest_entries if isinstance(entry, dict)}
    ):
        raise PostCommitStateError(
            "committed current-source-state self-exclusion contract changed"
        )
    if manifest_entries != expected_entries:
        raise PostCommitStateError(
            "committed current-source-state entries do not equal HEAD tree minus self"
        )
    if projection.get("entry_count") != len(expected_entries) or projection.get(
        "entries_sha256"
    ) != sha256_bytes(compact_bytes(expected_entries)):
        raise PostCommitStateError(
            "committed current-source-state projection count or digest is stale"
        )

    return {
        "blob_oid": manifest_entry["oid"],
        "path": CURRENT_MANIFEST_RELATIVE,
        "schema": CURRENT_SCHEMA_NAME,
        "schema_revision": CURRENT_SCHEMA_REVISION,
        "sha256": sha256_bytes(manifest_bytes),
        "size_bytes": len(manifest_bytes),
        "source_projection_entries_sha256": projection["entries_sha256"],
        "source_projection_entry_count": projection["entry_count"],
    }


def run_current_manifest_checker(root: Path, state: dict[str, Any]) -> None:
    mapping = state_blob_map(state)
    for relative in (
        CURRENT_CHECKER_RELATIVE,
        CURRENT_MANIFEST_RELATIVE,
        CURRENT_SCHEMA_RELATIVE,
    ):
        if relative not in mapping:
            raise PostCommitStateError(
                f"current-source-state validation dependency is absent: {relative}"
            )

    checker_path = root / CURRENT_CHECKER_RELATIVE
    checker_source = exact_regular_bytes(
        checker_path, "committed current-source-state checker"
    )
    if checker_source != mapping[CURRENT_CHECKER_RELATIVE][1]:
        raise PostCommitStateError(
            "current-source-state checker worktree bytes differ from its HEAD blob"
        )
    trusted_checker_path = ROOT / CURRENT_CHECKER_RELATIVE
    trusted_checker_source = exact_regular_bytes(
        trusted_checker_path, "trusted current-source-state checker"
    )
    if checker_source != trusted_checker_source:
        raise PostCommitStateError(
            "requested root current-source-state checker differs from trusted checker bytes"
        )
    arguments = [sys.executable]
    if sys.flags.optimize:
        arguments.append("-O")
    arguments.extend(("-I", "-S", "-B", str(trusted_checker_path), "--emit"))
    try:
        completed = subprocess.run(
            arguments,
            cwd=ROOT,
            env=safe_environment(),
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PostCommitStateError(
            f"cannot run trusted current-source-state checker: {error}"
        ) from error
    current_manifest_bytes = mapping[CURRENT_MANIFEST_RELATIVE][1]
    if (
        completed.returncode != 0
        or completed.stderr
        or completed.stdout != current_manifest_bytes
    ):
        raise PostCommitStateError(
            "trusted current-source-state checker did not reproduce the committed manifest"
        )


def build_artifact(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    first = collect_committed_state(root)
    validate_post_commit_dependencies(root, first)
    first_manifest = validate_current_manifest(first)
    run_current_manifest_checker(root, first)
    second = collect_committed_state(root)
    validate_post_commit_dependencies(root, second)
    second_manifest = validate_current_manifest(second)
    if first != second or first_manifest != second_manifest:
        raise PostCommitStateError(
            "committed source state changed across repeated post-commit validation"
        )

    return {
        "binding": {
            "commit_oid": first["commit_oid"],
            "git_object_format": first["git_object_format"],
            "manifest": first_manifest,
            "tree_oid": first["tree_oid"],
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
            "commit_cycle": (
                "none; the committed manifest excludes itself and this artifact is "
                "generated only after commit"
            ),
            "generated_at": "omitted_for_determinism",
            "storage_custody": "caller_owned_not_bound_by_this_artifact",
        },
        "evidence_class": "post_commit_identity_evidence_only",
        "generated_by": GENERATOR,
        "nonimplications": list(NONIMPLICATIONS),
        "repository": REPOSITORY,
        "schema": SCHEMA_NAME,
        "schema_revision": SCHEMA_REVISION,
    }


def validate_artifact(value: Any, schema: Any, expected: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise PostCommitStateError("post-commit schema root must be an object")
    if sha256_bytes(canonical_bytes(schema)) != EXPECTED_POST_SCHEMA_SHA256:
        raise PostCommitStateError("post-commit source-state schema bytes changed")
    if canonical_bytes(value) != canonical_bytes(expected):
        raise PostCommitStateError(
            "post-commit source-state artifact is stale or does not bind this exact HEAD"
        )
    binding = value["binding"]
    object_format = binding["git_object_format"]
    for label, oid in (
        ("commit", binding["commit_oid"]),
        ("tree", binding["tree_oid"]),
        ("manifest blob", binding["manifest"]["blob_oid"]),
    ):
        require_oid(oid, object_format, f"artifact {label}")
    if value["nonimplications"] != list(NONIMPLICATIONS):
        raise PostCommitStateError("post-commit nonimplication boundary changed")


def read_bounded_standard_input() -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = sys.stdin.buffer.read(min(64 * 1024, MAX_ARTIFACT_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_ARTIFACT_BYTES:
            raise PostCommitStateError("standard-input artifact exceeds its byte bound")
    return b"".join(chunks)


def main() -> int:
    mode = parse_mode(sys.argv[1:])
    schema, raw_schema = load_canonical_json(
        ROOT / POST_SCHEMA_RELATIVE, "post-commit source-state schema"
    )
    if sha256_bytes(raw_schema) != EXPECTED_POST_SCHEMA_SHA256:
        raise PostCommitStateError("post-commit source-state schema raw bytes changed")
    expected = build_artifact(ROOT)
    validate_artifact(expected, schema, expected)
    expected_bytes = canonical_bytes(expected)

    if mode == "emit":
        sys.stdout.buffer.write(expected_bytes)
        return 0

    raw = read_bounded_standard_input()
    observed = parse_canonical_json_bytes(raw, "standard-input post-commit artifact")
    validate_artifact(observed, schema, expected)
    if raw != expected_bytes:
        raise PostCommitStateError("standard-input artifact byte comparison changed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PostCommitStateError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
