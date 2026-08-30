#!/usr/bin/env python3
"""Recompute the bounded revision-1 Python source and launch inventory.

This checker reads exact Git blobs from the reviewed ``eb9c21a`` tree.  It does
not execute any inventoried source and it does not claim execution custody,
launch closure, import resolution, or completeness outside its declared seed.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import tokenize
import types
from typing import Any, Iterable


if sys.version_info < (3, 11):
    raise SystemExit("check-python-verifier-custody-inventory.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "audit/python-verifier-custody/registry-v1.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/python-verifier-custody-registry-v1.schema.json"
FORMAT = "pid-rs/python-verifier-custody-registry/v1"
SCHEMA_REVISION = 1
REPOSITORY = "https://github.com/sepahead/pid-rs"
REVIEW_COMMIT = "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9"
REVIEW_TREE = "d3d247270822fe477862c80ba8b6a9041ac8f6bc"
GENERATOR = "scripts/check-python-verifier-custody-inventory.py"
# Method catalog: validation.python-verifier-custody-inventory

SOURCE_KINDS = (
    "file",
    "inline_stdin",
    "inline_argv",
    "module_tool",
    "dynamic_fixture",
)
SOURCE_STATUSES = (
    "closed",
    "open_blocking",
    "unsupported_blocking",
    "historical_nonoperational",
    "library_helper",
)
IMPORT_CLASSES = (
    "stdlib_profile",
    "local_candidate",
    "third_party_declared",
    "unresolved_open_blocking",
)
DYNAMIC_DIRECT_NAMES = ("__import__", "compile", "exec")
DYNAMIC_ATTRIBUTE_NAMES = ("module_from_spec", "spec_from_file_location")
THIRD_PARTY_ROOTS = ("csxpid", "numpy", "pid_core_rs", "pypdf", "pytest")
LOCAL_IMPORT_ROOTS = ("_exact_product", "json_schema_subset")
STDLIB_ROOTS = (
    "__future__",
    "argparse",
    "array",
    "ast",
    "atexit",
    "base64",
    "binascii",
    "builtins",
    "collections",
    "concurrent",
    "contextlib",
    "copy",
    "csv",
    "ctypes",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "errno",
    "fcntl",
    "fractions",
    "functools",
    "hashlib",
    "importlib",
    "io",
    "itertools",
    "json",
    "logging",
    "marshal",
    "math",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "pwd",
    "py_compile",
    "random",
    "re",
    "secrets",
    "selectors",
    "shlex",
    "shutil",
    "signal",
    "stat",
    "struct",
    "subprocess",
    "sys",
    "tarfile",
    "tempfile",
    "textwrap",
    "threading",
    "time",
    "tomllib",
    "types",
    "typing",
    "unicodedata",
    "unittest",
    "urllib",
    "xml",
    "zipfile",
    "zlib",
)
PROJECTION_OFFICIAL = "repo-owned-official-verifier-source-entry/v1"
PROJECTION_ALL = "all-repository-python-processes/v1"
INVOCATION_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"(?P<interpreter>python(?:3(?:\.[0-9]+)?)?|pypy3?|\$\{?PYTHON(?:_[A-Z0-9_]+)?\}?)"
    r"(?![A-Za-z0-9_.-])"
)
PYTHON_FILE_TOKEN_RE = re.compile(r"(?P<path>[A-Za-z0-9_./${}:+@~-]+\.py)\b")
HEREDOC_RE = re.compile(
    r"<<(?P<strip_tabs>-)?\s*(?P<quote>['\"]?)(?P<delimiter>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?P=quote)"
)
SUBPROCESS_CALL_NAMES = {
    "Popen",
    "call",
    "check_call",
    "check_output",
    "execv",
    "execve",
    "run",
    "system",
}


class InventoryError(RuntimeError):
    """The bounded inventory cannot be reproduced exactly."""


@dataclass(frozen=True)
class TreeEntry:
    path: str
    mode: str
    object_type: str
    oid: str
    data: bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--emit", action="store_true", help="write the deterministic registry to stdout"
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the selected registry with deterministic canonical bytes",
    )
    return parser.parse_args()


def reject_constant(value: str) -> Any:
    raise InventoryError(f"non-finite JSON constant is forbidden: {value}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError(f"duplicate JSON object key is forbidden: {key!r}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise InventoryError(f"cannot canonicalize JSON: {error}") from error
    return (rendered + "\n").encode("utf-8")


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
        raise InventoryError(f"cannot encode compact JSON: {error}") from error


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stat_identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def load_json(path: Path, label: str, *, canonical: bool) -> tuple[Any, bytes]:
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise InventoryError(f"{label} must be a single-link regular file: {path}")
        raw = path.read_bytes()
        after = os.lstat(path)
    except OSError as error:
        raise InventoryError(f"cannot read {label} {path}: {error}") from error
    if stat_identity(before) != stat_identity(after) or len(raw) != before.st_size:
        raise InventoryError(f"{label} changed during exact read: {path}")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, InventoryError) as error:
        raise InventoryError(f"cannot parse {label} {path}: {error}") from error
    if canonical and raw != canonical_bytes(value):
        raise InventoryError(f"{label} is not canonical sorted UTF-8 JSON: {path}")
    return value, raw


def load_schema_validator(root: Path) -> tuple[type[ValueError], Any]:
    """Load the checked-in subset validator from exact source bytes."""
    path = root / "scripts/json_schema_subset.py"
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise InventoryError("JSON-schema validator is not a single-link regular file")
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
    if not (
        stat_identity(before)
        == stat_identity(opened)
        == stat_identity(closed)
        == stat_identity(after)
        and len(source) == before.st_size
    ):
        raise InventoryError("JSON-schema validator changed during exact-source read")
    module = types.ModuleType("python_custody_json_schema_subset")
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


def git_environment() -> dict[str, str]:
    forbidden_exact = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_SYSTEM",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_NAMESPACE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
    forbidden_prefixes = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in forbidden_exact
        and not any(key.startswith(prefix) for prefix in forbidden_prefixes)
    }
    environment.update(
        {
            "GIT_CONFIG_COUNT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return environment


def run_git(
    root: Path, arguments: Iterable[str], *, input_bytes: bytes | None = None
) -> bytes:
    command = [
        "git",
        "-C",
        os.fspath(root),
        "-c",
        "core.useReplaceRefs=false",
        "-c",
        "core.hooksPath=/dev/null",
        *arguments,
    ]
    completed = subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=git_environment(),
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", "replace").strip()
        raise InventoryError(f"Git command failed ({' '.join(arguments)}): {stderr}")
    return completed.stdout


def ensure_canonical_path(path: str) -> None:
    pure = PurePosixPath(path)
    if (
        not path
        or path.startswith("/")
        or pure.as_posix() != path
        or "." in pure.parts
        or ".." in pure.parts
        or "\x00" in path
    ):
        raise InventoryError(f"noncanonical Git path: {path!r}")


def read_review_tree(root: Path) -> dict[str, TreeEntry]:
    top = run_git(root, ("rev-parse", "--show-toplevel")).decode("utf-8").strip()
    if Path(top).resolve(strict=True) != root.resolve(strict=True):
        raise InventoryError(f"Git root mismatch: expected {root}, observed {top}")
    object_format = (
        run_git(root, ("rev-parse", "--show-object-format")).decode("ascii").strip()
    )
    if object_format != "sha1":
        raise InventoryError(
            f"review repository object format is not SHA-1: {object_format}"
        )
    commit = (
        run_git(root, ("rev-parse", f"{REVIEW_COMMIT}^{{commit}}")).decode().strip()
    )
    if commit != REVIEW_COMMIT:
        raise InventoryError(f"review commit resolved unexpectedly: {commit}")
    raw_commit = run_git(root, ("cat-file", "commit", REVIEW_COMMIT))
    first = raw_commit.splitlines()[0] if raw_commit else b""
    if first != f"tree {REVIEW_TREE}".encode("ascii"):
        raise InventoryError("review commit does not name the pinned tree")
    listing = run_git(root, ("ls-tree", "-r", "-z", "--full-tree", REVIEW_COMMIT))
    records = listing.split(b"\0")
    if records[-1] != b"":
        raise InventoryError("Git ls-tree output lacks its NUL terminator")
    entries: dict[str, TreeEntry] = {}
    for raw in records[:-1]:
        try:
            header, path_raw = raw.split(b"\t", 1)
            mode_raw, object_type_raw, oid_raw = header.split(b" ", 2)
            path = path_raw.decode("utf-8", "strict")
            mode = mode_raw.decode("ascii")
            object_type = object_type_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise InventoryError("malformed or non-UTF-8 Git tree record") from error
        ensure_canonical_path(path)
        if path in entries:
            raise InventoryError(f"duplicate tree path: {path}")
        if object_type != "blob":
            data = b""
        else:
            data = run_git(root, ("cat-file", "blob", oid))
            if len(oid) == 40:
                framed = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                if hashlib.sha1(framed).hexdigest() != oid:  # noqa: S324 - Git SHA-1 identity
                    raise InventoryError(f"Git blob identity mismatch: {path}")
        entries[path] = TreeEntry(path, mode, object_type, oid, data)
    return entries


def source_encoding(data: bytes, path: str) -> tuple[str, str]:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        return encoding, data.decode(encoding)
    except (SyntaxError, UnicodeDecodeError, LookupError) as error:
        raise InventoryError(f"cannot decode Python source {path}: {error}") from error


def anchor(node: ast.AST, source: str) -> dict[str, Any]:
    segment = ast.get_source_segment(source, node) or ""
    return {
        "column": int(getattr(node, "col_offset", 0)),
        "end_column": int(getattr(node, "end_col_offset", 0)),
        "end_line": int(getattr(node, "end_lineno", getattr(node, "lineno", 0))),
        "line": int(getattr(node, "lineno", 0)),
        "source_segment_sha256": sha256_bytes(segment.encode("utf-8")),
    }


def callable_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = callable_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def expression_shape(node: ast.AST | None) -> str:
    if node is None:
        return "absent"
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "literal_string"
        if node.value is None:
            return "literal_none"
        return "literal_other"
    if isinstance(node, ast.Name):
        return "name"
    if isinstance(node, ast.Attribute):
        return "attribute"
    if isinstance(node, ast.Call):
        return "call"
    if isinstance(node, (ast.List, ast.Tuple)):
        return "sequence"
    return type(node).__name__.lower()


def import_class(root_name: str) -> str:
    if root_name in STDLIB_ROOTS:
        return "stdlib_profile"
    if root_name in LOCAL_IMPORT_ROOTS:
        return "local_candidate"
    if root_name in THIRD_PARTY_ROOTS:
        return "third_party_declared"
    return "unresolved_open_blocking"


def ast_details(
    source_id: str,
    path_label: str,
    data: bytes,
    *,
    content_is_python: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], ast.AST | None]:
    if not content_is_python:
        return (
            {
                "encoding": None,
                "node_count": 0,
                "other_call_count": 0,
                "other_call_resolution_status": "open_blocking",
                "status": "not_available_open_blocking",
            },
            [],
            [],
            None,
        )
    try:
        encoding, source = source_encoding(data, path_label)
        tree = ast.parse(source, filename=path_label, mode="exec", type_comments=True)
    except (InventoryError, SyntaxError) as error:
        return (
            {
                "encoding": None,
                "node_count": 0,
                "other_call_count": 0,
                "other_call_resolution_status": "open_blocking",
                "status": "syntax_error_open_blocking",
                "diagnostic_sha256": sha256_bytes(str(error).encode("utf-8")),
            },
            [],
            [],
            None,
        )

    imports: list[dict[str, Any]] = []
    dynamics: list[dict[str, Any]] = []
    all_calls = 0
    selected_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias_index, alias in enumerate(node.names):
                root_name = alias.name.split(".", 1)[0]
                imports.append(
                    {
                        "alias": alias.asname,
                        "anchor": anchor(node, source),
                        "class": import_class(root_name),
                        "execution_resolution_status": "open_blocking",
                        "id": f"{source_id}#import-{len(imports) + 1:04d}",
                        "imported_name": alias.name,
                        "level": 0,
                        "root_name": root_name,
                        "statement_kind": "import",
                        "statement_member_index": alias_index,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root_name = module.split(".", 1)[0] if module else ""
            for alias_index, alias in enumerate(node.names):
                imported = f"{module}.{alias.name}" if module else alias.name
                imports.append(
                    {
                        "alias": alias.asname,
                        "anchor": anchor(node, source),
                        "class": import_class(root_name),
                        "execution_resolution_status": "open_blocking",
                        "id": f"{source_id}#import-{len(imports) + 1:04d}",
                        "imported_name": imported,
                        "level": node.level,
                        "root_name": root_name,
                        "statement_kind": "from_import",
                        "statement_member_index": alias_index,
                    }
                )
        if isinstance(node, ast.Call):
            all_calls += 1
            primitive_class: str | None = None
            primitive_name: str | None = None
            if isinstance(node.func, ast.Name) and node.func.id in DYNAMIC_DIRECT_NAMES:
                primitive_class = "direct_builtin_name"
                primitive_name = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in DYNAMIC_ATTRIBUTE_NAMES
            ):
                primitive_class = "selected_attribute_name"
                primitive_name = node.func.attr
            if primitive_class is not None and primitive_name is not None:
                selected_calls += 1
                dynamics.append(
                    {
                        "anchor": anchor(node, source),
                        "argument_count": len(node.args),
                        "first_argument_shape": expression_shape(
                            node.args[0] if node.args else None
                        ),
                        "id": f"{source_id}#dynamic-{len(dynamics) + 1:04d}",
                        "keyword_names": sorted(
                            keyword.arg if keyword.arg is not None else "**"
                            for keyword in node.keywords
                        ),
                        "primitive_class": primitive_class,
                        "primitive_name": primitive_name,
                        "resolution_status": "open_blocking",
                        "target_source_id": None,
                    }
                )
    return (
        {
            "encoding": encoding,
            "node_count": sum(1 for _ in ast.walk(tree)),
            "other_call_count": all_calls - selected_calls,
            "other_call_resolution_status": "open_blocking",
            "status": "parsed",
        },
        imports,
        dynamics,
        tree,
    )


def file_source(entry: TreeEntry) -> tuple[dict[str, Any], ast.AST | None]:
    source_id = f"file:{entry.path}"
    details, imports, dynamics, tree = ast_details(source_id, entry.path, entry.data)
    source = {
        "ast": details,
        "blockers": [
            "M0 does not execute this source or bind its interpreter, imports, environment, or child processes.",
            "Calls outside the five selected dynamic-source spellings remain unresolved and open blocking.",
        ],
        "content": {
            "availability": "exact_git_blob",
            "bytes": len(entry.data),
            "git_blob_oid": entry.oid,
            "git_mode": entry.mode,
            "sha256": sha256_bytes(entry.data),
        },
        "dynamic_edges": dynamics,
        "id": source_id,
        "import_edges": imports,
        "kind": "file",
        "nonimplications": [
            "AST parsing is not execution, semantic review, import resolution, or source-to-process custody."
        ],
        "origin": {"path": entry.path, "type": "review_tree_blob"},
        "status": "open_blocking",
    }
    return source, tree


def auxiliary_source(
    source_id: str,
    kind: str,
    origin: dict[str, Any],
    content: bytes | None,
    *,
    parse_python: bool,
) -> dict[str, Any]:
    if kind not in SOURCE_KINDS:
        raise InventoryError(f"invalid auxiliary source kind: {kind}")
    details, imports, dynamics, _ = ast_details(
        source_id,
        source_id,
        content or b"",
        content_is_python=parse_python and content is not None,
    )
    availability = (
        "exact_static_fragment" if content is not None else "unresolved_open_blocking"
    )
    return {
        "ast": details,
        "blockers": [
            "The launch fragment is statically inventoried but is not executed or resolved by M0."
        ],
        "content": {
            "availability": availability,
            "bytes": len(content) if content is not None else None,
            "git_blob_oid": None,
            "git_mode": None,
            "sha256": sha256_bytes(content) if content is not None else None,
        },
        "dynamic_edges": dynamics,
        "id": source_id,
        "import_edges": imports,
        "kind": kind,
        "nonimplications": [
            "Static fragment capture does not establish the bytes supplied to a future interpreter."
        ],
        "origin": origin,
        "status": "open_blocking",
    }


def local_module_records(python_paths: list[str]) -> list[dict[str, Any]]:
    candidates: defaultdict[str, list[str]] = defaultdict(list)
    for path in python_paths:
        stem = PurePosixPath(path).stem
        if stem.isidentifier():
            candidates[stem].append(f"file:{path}")
        parts = list(PurePosixPath(path).with_suffix("").parts)
        if parts and all(part.isidentifier() for part in parts):
            candidates[".".join(parts)].append(f"file:{path}")
    records = []
    for name in sorted(candidates):
        source_ids = sorted(set(candidates[name]))
        records.append(
            {
                "candidate_source_ids": source_ids,
                "module_name": name,
                "resolution_status": "open_blocking",
                "why_open": (
                    "Import resolution depends on argv[0], cwd, sys.path, package markers, "
                    "environment, hooks, and interpreter state that M0 does not bind."
                ),
            }
        )
    return records


def root_kind(path: str) -> str | None:
    if path == "AGENTS.md":
        return "agents_document"
    if path == "justfile":
        return "just_recipe_file"
    if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
        return "workflow_yaml"
    if path.endswith(".sh"):
        return "shell_script"
    return None


def flags_after_invocation(fragment: str) -> list[str]:
    return [flag for flag in ("-B", "-I", "-O", "-S") if flag in fragment]


def classify_command_source(
    fragment: str,
    python_paths: set[str],
) -> tuple[str, str | None, bytes | None, str]:
    """Return source kind, resolved file path, exact fragment bytes, reason."""
    try:
        tokens = shlex.split(fragment, comments=False, posix=True)
    except ValueError:
        tokens = fragment.split()
    if "-c" in tokens:
        index = tokens.index("-c")
        content = tokens[index + 1].encode("utf-8") if index + 1 < len(tokens) else None
        return "inline_argv", None, content, "selected -c token"
    if "-m" in tokens:
        index = tokens.index("-m")
        module = tokens[index + 1].encode("utf-8") if index + 1 < len(tokens) else None
        return "module_tool", None, module, "selected -m token"
    if "<<" in fragment:
        return "inline_stdin", None, None, "selected heredoc operator"
    matches = list(PYTHON_FILE_TOKEN_RE.finditer(fragment))
    if matches:
        raw_path = matches[0].group("path")
        normalized = raw_path[2:] if raw_path.startswith("./") else raw_path
        if normalized in python_paths:
            return "file", normalized, None, "exact review-tree path token"
        return "file", None, raw_path.encode("utf-8"), "unresolved .py path token"
    return (
        "dynamic_fixture",
        None,
        fragment.encode("utf-8"),
        "unresolved command fragment",
    )


def launch_record(
    *,
    edge_id: str,
    caller_path: str,
    caller_entry: TreeEntry,
    caller_kind: str,
    source_id: str,
    source_kind: str,
    line: int,
    column: int,
    segment: str,
    modes: list[str],
    interpreter_token: str,
) -> dict[str, Any]:
    return {
        "argv": {
            "observed_flags": modes,
            "status": "open_blocking",
        },
        "blockers": [
            "M0 records a static candidate launch but does not execute it or bind runtime argv/cwd/stdin/environment.",
            "Variable expansion, quoting, conditionals, wrappers, and platform command resolution remain open blocking.",
        ],
        "caller": {
            "anchor": {
                "column": column,
                "line": line,
                "source_segment_sha256": sha256_bytes(segment.encode("utf-8")),
            },
            "blob_oid": caller_entry.oid,
            "kind": caller_kind,
            "path": caller_path,
            "sha256": sha256_bytes(caller_entry.data),
        },
        "claim_membership": [PROJECTION_ALL],
        "cwd": {"status": "open_blocking", "value": None},
        "dynamic_edge_ids": [],
        "environment_profile_ids": ["environment-unresolved/v1"],
        "execution_custody_status": "open_blocking",
        "external_tool_profile_ids": ["external-tool-unresolved/v1"],
        "id": edge_id,
        "import_edge_ids": [],
        "interpreter_profile_ids": ["python-command-token-unresolved/v1"],
        "interpreter_token": interpreter_token,
        "modes": ["optimized" if "-O" in modes else "normal"],
        "nonimplications": [
            "A text or AST launch candidate is not proof that the command runs, reaches the named bytes, or succeeds."
        ],
        "platforms": ["unresolved_open_blocking"],
        "source_id": source_id,
        "source_kind": source_kind,
        "stdin": {"status": "open_blocking", "value_sha256": None},
        "third_party_import_edge_ids": [],
    }


def scan_operational_roots(
    roots: list[TreeEntry],
    python_paths: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    launches: list[dict[str, Any]] = []
    auxiliary: list[dict[str, Any]] = []
    for entry in roots:
        try:
            text = entry.data.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise InventoryError(
                f"operational root is not UTF-8: {entry.path}"
            ) from error
        kind = root_kind(entry.path)
        if kind is None:
            raise InventoryError(f"untyped operational root: {entry.path}")
        lines = text.splitlines(keepends=True)
        for line_index, raw_line in enumerate(lines):
            line_number = line_index + 1
            line = raw_line.rstrip("\r\n")
            for match in INVOCATION_RE.finditer(line):
                fragment = line[match.start() :]
                source_kind, resolved, content, _ = classify_command_source(
                    fragment, python_paths
                )
                if source_kind == "inline_stdin":
                    heredoc = HEREDOC_RE.search(fragment)
                    if heredoc is not None:
                        delimiter = heredoc.group("delimiter")
                        strip_tabs = heredoc.group("strip_tabs") is not None
                        body: list[str] = []
                        terminated = False
                        for candidate in lines[line_index + 1 :]:
                            comparison = candidate.rstrip("\r\n")
                            if strip_tabs:
                                comparison = comparison.lstrip("\t")
                            if comparison == delimiter:
                                terminated = True
                                break
                            body.append(candidate)
                        if terminated:
                            content = "".join(body).encode("utf-8")
                launch_index = len(launches) + 1
                edge_id = f"launch-{launch_index:05d}"
                if source_kind == "file" and resolved is not None:
                    source_id = f"file:{resolved}"
                else:
                    source_id = (
                        f"{source_kind}:{entry.path}:{line_number}:{match.start()}"
                    )
                    auxiliary.append(
                        auxiliary_source(
                            source_id,
                            source_kind,
                            {
                                "column": match.start(),
                                "line": line_number,
                                "path": entry.path,
                                "type": "operational_root_fragment",
                            },
                            content,
                            parse_python=source_kind in {"inline_argv", "inline_stdin"},
                        )
                    )
                launches.append(
                    launch_record(
                        edge_id=edge_id,
                        caller_path=entry.path,
                        caller_entry=entry,
                        caller_kind=kind,
                        source_id=source_id,
                        source_kind=source_kind,
                        line=line_number,
                        column=match.start(),
                        segment=fragment,
                        modes=flags_after_invocation(fragment),
                        interpreter_token=match.group("interpreter"),
                    )
                )
    return launches, auxiliary


def constants_in(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def has_python_runtime_reference(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Attribute)
            and callable_name(child) == "sys.executable"
        ):
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if INVOCATION_RE.search(child.value):
                return True
    return False


def scan_python_child_launches(
    file_sources: list[dict[str, Any]],
    trees: dict[str, ast.AST | None],
    entries: dict[str, TreeEntry],
    python_paths: set[str],
    starting_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    launches: list[dict[str, Any]] = []
    auxiliary: list[dict[str, Any]] = []
    sources_by_id = {source["id"]: source for source in file_sources}
    for source_id in sorted(trees):
        tree = trees[source_id]
        if tree is None:
            continue
        path = source_id.removeprefix("file:")
        entry = entries[path]
        _, source_text = source_encoding(entry.data, path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = callable_name(node.func)
            if called.rsplit(".", 1)[-1] not in SUBPROCESS_CALL_NAMES:
                continue
            if not has_python_runtime_reference(node):
                continue
            constants = constants_in(node)
            resolved = next(
                (
                    candidate[2:] if candidate.startswith("./") else candidate
                    for candidate in constants
                    if candidate.endswith(".py")
                    and (candidate[2:] if candidate.startswith("./") else candidate)
                    in python_paths
                ),
                None,
            )
            source_kind = "file" if resolved is not None else "dynamic_fixture"
            line = int(getattr(node, "lineno", 0))
            column = int(getattr(node, "col_offset", 0))
            segment = ast.get_source_segment(source_text, node) or called
            if resolved is not None:
                target_source_id = f"file:{resolved}"
            else:
                target_source_id = f"dynamic_fixture:{path}:{line}:{column}"
                auxiliary.append(
                    auxiliary_source(
                        target_source_id,
                        "dynamic_fixture",
                        {
                            "column": column,
                            "line": line,
                            "path": path,
                            "type": "python_child_launch_expression",
                        },
                        segment.encode("utf-8"),
                        parse_python=False,
                    )
                )
            edge_id = f"launch-{starting_index + len(launches):05d}"
            modes = [value for value in constants if value in {"-B", "-I", "-O", "-S"}]
            record = launch_record(
                edge_id=edge_id,
                caller_path=path,
                caller_entry=entry,
                caller_kind="python_subprocess_api",
                source_id=target_source_id,
                source_kind=source_kind,
                line=line,
                column=column,
                segment=segment,
                modes=modes,
                interpreter_token="sys.executable-or-static-python-token",
            )
            record["interpreter_profile_ids"] = ["python-child-api-unresolved/v1"]
            if source_id in sources_by_id:
                record["external_tool_profile_ids"] = [
                    "external-tool-unresolved/v1",
                    "python-subprocess-api/v1",
                ]
            launches.append(record)
    return launches, auxiliary


def attach_source_edges(
    launches: list[dict[str, Any]], sources: list[dict[str, Any]]
) -> None:
    by_id = {source["id"]: source for source in sources}
    for launch in launches:
        source = by_id[launch["source_id"]]
        if source["content"]["availability"] == "exact_git_blob" and source[
            "id"
        ].startswith("file:"):
            path = source["id"].removeprefix("file:")
            basename = PurePosixPath(path).name
            if basename.startswith("check-") or "/check-" in path:
                launch["claim_membership"] = sorted(
                    [*launch["claim_membership"], PROJECTION_OFFICIAL]
                )
        import_ids = [edge["id"] for edge in source["import_edges"]]
        launch["import_edge_ids"] = import_ids
        launch["dynamic_edge_ids"] = [edge["id"] for edge in source["dynamic_edges"]]
        launch["third_party_import_edge_ids"] = [
            edge["id"]
            for edge in source["import_edges"]
            if edge["class"] == "third_party_declared"
        ]


def root_record(entry: TreeEntry) -> dict[str, Any]:
    kind = root_kind(entry.path)
    if kind is None:
        raise InventoryError(f"missing operational-root kind: {entry.path}")
    return {
        "bytes": len(entry.data),
        "git_blob_oid": entry.oid,
        "git_mode": entry.mode,
        "kind": kind,
        "path": entry.path,
        "sha256": sha256_bytes(entry.data),
        "status": "open_blocking",
    }


def build_registry(root: Path) -> dict[str, Any]:
    entries = read_review_tree(root)
    python_paths = sorted(path for path in entries if path.endswith(".py"))
    operational_paths = sorted(path for path in entries if root_kind(path) is not None)
    if not python_paths:
        raise InventoryError("selected tree has no tracked Python source")
    for path in python_paths + operational_paths:
        if entries[path].object_type != "blob":
            raise InventoryError(f"seed entry is not a blob: {path}")

    file_sources: list[dict[str, Any]] = []
    trees: dict[str, ast.AST | None] = {}
    for path in python_paths:
        source, tree = file_source(entries[path])
        file_sources.append(source)
        trees[source["id"]] = tree

    roots = [entries[path] for path in operational_paths]
    launch_edges, root_auxiliary = scan_operational_roots(roots, set(python_paths))
    child_edges, child_auxiliary = scan_python_child_launches(
        file_sources,
        trees,
        entries,
        set(python_paths),
        len(launch_edges) + 1,
    )
    launch_edges.extend(child_edges)
    sources = sorted(
        [*file_sources, *root_auxiliary, *child_auxiliary], key=lambda item: item["id"]
    )
    attach_source_edges(launch_edges, sources)

    import_edges = [edge for source in sources for edge in source["import_edges"]]
    dynamic_edges = [edge for source in sources for edge in source["dynamic_edges"]]
    tracked_file_import_edges = [
        edge for source in file_sources for edge in source["import_edges"]
    ]
    tracked_file_dynamic_edges = [
        edge for source in file_sources for edge in source["dynamic_edges"]
    ]

    def import_statement_key(edge: dict[str, Any]) -> tuple[Any, ...]:
        edge_source_id = edge["id"].split("#import-", 1)[0]
        location = edge["anchor"]
        return (
            edge_source_id,
            edge["statement_kind"],
            location["line"],
            location["column"],
            location["end_line"],
            location["end_column"],
        )

    tracked_file_import_statements = {
        import_statement_key(edge) for edge in tracked_file_import_edges
    }
    tracked_file_third_party_edges = [
        edge
        for edge in tracked_file_import_edges
        if edge["class"] == "third_party_declared"
    ]
    tracked_file_third_party_statements = {
        import_statement_key(edge) for edge in tracked_file_third_party_edges
    }

    def import_root_counts(
        selected_edges: list[dict[str, Any]], roots: tuple[str, ...]
    ) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for root_name in roots:
            root_edges = [
                edge for edge in selected_edges if edge["root_name"] == root_name
            ]
            result[root_name] = {
                "binding_edges": len(root_edges),
                "files": len(
                    {edge["id"].split("#import-", 1)[0] for edge in root_edges}
                ),
                "statements": len({import_statement_key(edge) for edge in root_edges}),
            }
        return result

    dynamic_counts = Counter(edge["primitive_name"] for edge in dynamic_edges)
    source_status_counts = Counter(source["status"] for source in sources)
    source_kind_counts = Counter(source["kind"] for source in sources)
    ast_status_counts = Counter(source["ast"]["status"] for source in sources)
    import_class_counts = Counter(edge["class"] for edge in import_edges)
    launch_kind_counts = Counter(edge["source_kind"] for edge in launch_edges)

    projections = []
    for projection_id, meaning in (
        (
            PROJECTION_OFFICIAL,
            "Static candidates whose resolved source path has a check-* verifier spelling.",
        ),
        (
            PROJECTION_ALL,
            "All candidate Python launches found by the bounded M0 seed and grammars.",
        ),
    ):
        edge_ids = sorted(
            edge["id"]
            for edge in launch_edges
            if projection_id in edge["claim_membership"]
        )
        projections.append(
            {
                "blockers": [
                    "The seed and static grammars are bounded and do not prove that every runtime launch is represented.",
                    "No launch edge has execution custody, resolved environment, or a closed import/dynamic-source chain at M0.",
                ],
                "edge_count": len(edge_ids),
                "edge_ids_sha256": sha256_bytes(compact_bytes(edge_ids)),
                "id": projection_id,
                "meaning": meaning,
                "status": "open_blocking",
            }
        )

    return {
        "bootstrap": {
            "checker_source_binding": "placeholder_open",
            "independent_custody": "none",
            "schema_validator_binding": "placeholder_open",
            "status": "open_blocking",
            "why": (
                "The M0 checker and schema are descendants of the selected review tree and have "
                "no independent bootstrap or execution-custody binding."
            ),
        },
        "closure_claims": projections,
        "external_tool_profiles": [
            {
                "id": "external-tool-unresolved/v1",
                "status": "open_blocking",
                "scope": "Command wrappers, module tools, shells, and external executable identities are unresolved.",
            },
            {
                "id": "git-object-reader/v1",
                "status": "open_blocking",
                "scope": "Exact selected-tree blob retrieval; Git executable identity is not authenticated.",
            },
            {
                "id": "python-subprocess-api/v1",
                "status": "open_blocking",
                "scope": "Selected AST child-process call spellings; runtime behavior is not resolved.",
            },
        ],
        "format": FORMAT,
        "interpreter_profiles": [
            {
                "id": "python-command-token-unresolved/v1",
                "status": "open_blocking",
                "scope": "Textual python/python3/pypy/$PYTHON command token without executable identity.",
            },
            {
                "id": "python-child-api-unresolved/v1",
                "status": "open_blocking",
                "scope": "Selected sys.executable or static Python token in a Python child-process AST call.",
            },
            {
                "id": "scanner-parser-cpython-3.11-plus/v1",
                "status": "open_blocking",
                "scope": "AST parser requirement only; it is not interpreter authenticity or target-runtime identity.",
            },
        ],
        "environment_profiles": [
            {
                "id": "environment-unresolved/v1",
                "status": "open_blocking",
                "scope": "cwd, variables, sys.path, site state, file descriptors, signals, and platform are unresolved.",
            }
        ],
        "inventory": {
            "ast_status_counts": dict(sorted(ast_status_counts.items())),
            "dynamic_edge_count": len(dynamic_edges),
            "dynamic_primitive_counts": dict(sorted(dynamic_counts.items())),
            "import_class_counts": dict(sorted(import_class_counts.items())),
            "import_edge_count": len(import_edges),
            "launch_edge_count": len(launch_edges),
            "launch_source_kind_counts": dict(sorted(launch_kind_counts.items())),
            "local_module_record_count": len(local_module_records(python_paths)),
            "operational_root_count": len(operational_paths),
            "operational_roots": [
                root_record(entries[path]) for path in operational_paths
            ],
            "python_source_path_list_sha256": sha256_bytes(compact_bytes(python_paths)),
            "python_source_paths": python_paths,
            "scanner_policy": {
                "ast_mode": "exec-with-type-comments",
                "child_process_call_names": sorted(SUBPROCESS_CALL_NAMES),
                "dynamic_attribute_names": list(DYNAMIC_ATTRIBUTE_NAMES),
                "dynamic_direct_names": list(DYNAMIC_DIRECT_NAMES),
                "heredoc_regex": HEREDOC_RE.pattern,
                "import_classes": list(IMPORT_CLASSES),
                "invocation_regex": INVOCATION_RE.pattern,
                "other_call_resolution": "open_blocking",
                "unknown_import_resolution": "open_blocking",
            },
            "seed_policy": {
                "operational_roots": [
                    "tracked .github/workflows/*.yml or *.yaml",
                    "every tracked *.sh path",
                    "root AGENTS.md",
                    "root justfile",
                ],
                "python_sources": "every tracked *.py path in the selected review tree",
                "unscanned_examples": [
                    "Rust/native sources outside the declared operational-root seed",
                    "untracked, ignored, generated-at-runtime, external, or absent-history sources",
                ],
            },
            "source_kind_counts": dict(sorted(source_kind_counts.items())),
            "source_status_counts": dict(sorted(source_status_counts.items())),
            "total_python_source_records": len(sources),
            "tracked_file_dynamic_edge_count": len(tracked_file_dynamic_edges),
            "tracked_file_dynamic_source_file_count": len(
                {
                    edge["id"].split("#dynamic-", 1)[0]
                    for edge in tracked_file_dynamic_edges
                }
            ),
            "tracked_file_dynamic_primitive_counts": dict(
                sorted(
                    Counter(
                        edge["primitive_name"] for edge in tracked_file_dynamic_edges
                    ).items()
                )
            ),
            "tracked_file_import_edge_count": len(tracked_file_import_edges),
            "tracked_file_import_class_counts": dict(
                sorted(
                    Counter(edge["class"] for edge in tracked_file_import_edges).items()
                )
            ),
            "tracked_file_import_statement_count": len(tracked_file_import_statements),
            "tracked_file_local_candidate_root_counts": import_root_counts(
                tracked_file_import_edges, LOCAL_IMPORT_ROOTS
            ),
            "tracked_file_third_party_import_edge_count": len(
                tracked_file_third_party_edges
            ),
            "tracked_file_third_party_import_file_count": len(
                {
                    edge["id"].split("#import-", 1)[0]
                    for edge in tracked_file_third_party_edges
                }
            ),
            "tracked_file_third_party_import_statement_count": len(
                tracked_file_third_party_statements
            ),
            "tracked_file_third_party_root_counts": import_root_counts(
                tracked_file_import_edges, THIRD_PARTY_ROOTS
            ),
            "tracked_python_ast_status_counts": dict(
                sorted(
                    Counter(source["ast"]["status"] for source in file_sources).items()
                )
            ),
            "tracked_python_file_count": len(python_paths),
            "tracked_tree_entry_count": len(entries),
        },
        "launch_edges": launch_edges,
        "local_modules": local_module_records(python_paths),
        "nonimplications": [
            "Inventory coherence is not execution custody or evidence that any verifier ran.",
            "The bounded seed is not a repository-wide process-launch closure theorem.",
            "AST and lexical matches do not resolve aliases, wrappers, eval-generated names, import hooks, sys.path, shell expansion, or native launchers.",
            "A classified standard-library or third-party name is not dependency authenticity, version identity, availability, safety, or semantic review.",
            "No mathematical, statistical, estimator, PID, application, release, authenticity, or security conclusion follows.",
        ],
        "python_sources": sources,
        "repository": REPOSITORY,
        "review_revision": {
            "commit": REVIEW_COMMIT,
            "object_format": "sha1",
            "tree": REVIEW_TREE,
        },
        "schema_revision": SCHEMA_REVISION,
    }


def validate_semantics(registry: dict[str, Any]) -> None:
    if (
        registry.get("format") != FORMAT
        or registry.get("schema_revision") != SCHEMA_REVISION
    ):
        raise InventoryError("registry format or schema revision mismatch")
    sources = registry["python_sources"]
    source_ids = [source["id"] for source in sources]
    if source_ids != sorted(source_ids) or len(source_ids) != len(set(source_ids)):
        raise InventoryError("Python source IDs must be sorted and unique")
    source_by_id = {source["id"]: source for source in sources}
    if any(source["kind"] not in SOURCE_KINDS for source in sources):
        raise InventoryError("unknown Python source kind")
    if any(source["status"] == "closed" for source in sources):
        raise InventoryError("M0 must not close a Python source")
    if any(
        source["ast"]["other_call_resolution_status"] != "open_blocking"
        for source in sources
    ):
        raise InventoryError("unselected calls must remain open blocking")
    for source in sources:
        for edge in source["import_edges"]:
            if edge["class"] not in IMPORT_CLASSES:
                raise InventoryError("unknown import class")
            if edge["execution_resolution_status"] != "open_blocking":
                raise InventoryError("M0 must not close import resolution")
        for edge in source["dynamic_edges"]:
            if edge["resolution_status"] != "open_blocking":
                raise InventoryError("M0 must not close dynamic-source resolution")
    launches = registry["launch_edges"]
    launch_ids = [edge["id"] for edge in launches]
    expected_ids = [f"launch-{index:05d}" for index in range(1, len(launches) + 1)]
    if launch_ids != expected_ids:
        raise InventoryError("launch IDs are not contiguous and deterministic")
    for edge in launches:
        if edge["source_id"] not in source_by_id:
            raise InventoryError(f"launch references unknown source: {edge['id']}")
        if edge["execution_custody_status"] != "open_blocking":
            raise InventoryError("M0 launch edge was improperly closed")
        source = source_by_id[edge["source_id"]]
        if edge["source_kind"] != source["kind"]:
            raise InventoryError("launch source-kind reference mismatch")
        valid_imports = {item["id"] for item in source["import_edges"]}
        valid_dynamics = {item["id"] for item in source["dynamic_edges"]}
        if not set(edge["import_edge_ids"]).issubset(valid_imports):
            raise InventoryError("launch import-edge reference mismatch")
        if not set(edge["dynamic_edge_ids"]).issubset(valid_dynamics):
            raise InventoryError("launch dynamic-edge reference mismatch")
    claims = registry["closure_claims"]
    if [claim["id"] for claim in claims] != [PROJECTION_OFFICIAL, PROJECTION_ALL]:
        raise InventoryError("named projection set or order mismatch")
    if any(claim["status"] != "open_blocking" for claim in claims):
        raise InventoryError("M0 must leave both named projections open blocking")
    inventory = registry["inventory"]
    file_paths = [
        source["origin"]["path"]
        for source in sources
        if source["kind"] == "file"
        and source["content"]["availability"] == "exact_git_blob"
    ]
    if file_paths != inventory["python_source_paths"]:
        raise InventoryError("file-source paths do not match inventory path list")
    if len(file_paths) != inventory["tracked_python_file_count"]:
        raise InventoryError("tracked Python count is not recomputed from sources")
    if (
        sha256_bytes(compact_bytes(file_paths))
        != inventory["python_source_path_list_sha256"]
    ):
        raise InventoryError("Python path-list projection digest mismatch")
    if registry["bootstrap"]["status"] != "open_blocking":
        raise InventoryError("M0 bootstrap must remain open blocking")


def validate_registry(
    registry: dict[str, Any],
    schema: dict[str, Any],
    expected: dict[str, Any],
    root: Path,
) -> None:
    schema_error, validator = load_schema_validator(root)
    try:
        validator(registry, schema, name="Python verifier custody registry")
    except schema_error:
        raise
    validate_semantics(registry)
    if canonical_bytes(registry) != canonical_bytes(expected):
        raise InventoryError("registry differs from deterministic selected-tree scan")


def write_registry(path: Path, raw: bytes, root: Path) -> None:
    expected_path = root / "audit/python-verifier-custody/registry-v1.json"
    if path.absolute() != expected_path.absolute():
        raise InventoryError(
            "--write is restricted to audit/python-verifier-custody/registry-v1.json "
            "under the selected --root"
        )
    parent = path.parent
    try:
        parent_stat = os.lstat(parent)
    except OSError as error:
        raise InventoryError(
            f"registry parent is unavailable: {parent}: {error}"
        ) from error
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise InventoryError(f"registry parent is not a directory: {parent}")
    if path.exists() or path.is_symlink():
        current = os.lstat(path)
        if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1:
            raise InventoryError(
                "registry destination must be a single-link regular file"
            )
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".registry-v1.", dir=parent, delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o644)
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def main() -> int:
    arguments = parse_args()
    root = arguments.root.resolve(strict=True)
    expected = build_registry(root)
    validate_semantics(expected)
    schema, _ = load_json(arguments.schema, "registry schema", canonical=True)
    validate_registry(expected, schema, expected, root)
    if arguments.emit and arguments.write:
        raise InventoryError("--emit and --write are mutually exclusive")
    if arguments.emit:
        sys.stdout.buffer.write(canonical_bytes(expected))
        return 0
    if arguments.write:
        target = arguments.registry
        write_registry(target, canonical_bytes(expected), root)
        print(
            "wrote Python verifier custody registry: "
            f"files={expected['inventory']['tracked_python_file_count']} "
            f"sources={expected['inventory']['total_python_source_records']} "
            f"launches={expected['inventory']['launch_edge_count']}"
        )
        return 0
    registry, _ = load_json(
        arguments.registry, "Python custody registry", canonical=True
    )
    validate_registry(registry, schema, expected, root)
    inventory = registry["inventory"]
    print(
        "Python verifier custody M0 inventory coherent: "
        f"files={inventory['tracked_python_file_count']} "
        f"sources={inventory['total_python_source_records']} "
        f"imports={inventory['import_edge_count']} "
        f"dynamic={inventory['dynamic_edge_count']} "
        f"launches={inventory['launch_edge_count']} "
        "closure=0 (both projections open_blocking)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as error:
        raise SystemExit(
            f"Python verifier custody inventory failed: {error}"
        ) from error
