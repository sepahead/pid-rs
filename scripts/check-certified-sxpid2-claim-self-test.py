#!/usr/bin/env python3
"""Mutation tests for the certified-SxPID2 claim revision checker."""

# ruff: noqa: E402 -- isolation is checked before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-certified-sxpid2-claim-self-test.py requires Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
import copy
from dataclasses import dataclass
import hashlib
import json
import marshal
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable


PYTHON_CHILD_PREFIX = (
    (sys.executable, "-O", "-I", "-S", "-B")
    if sys.flags.optimize == 1
    else (sys.executable, "-I", "-S", "-B")
)
SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-certified-sxpid2-claim.py"
CHECKER_ANCHOR = "cb3f58f0b190454cb3f1090de8798261ec78f194"
SELF_TEST_VECTOR_SCHEMA = "pid-rs/certified-sxpid2-claim-self-test-vector/v1"
METHOD_ID = "validation.certified-sxpid2-reference"
REPORT_SCHEMA = "pid-rs/certified-sxpid-report/v2"
VERIFICATION_SCHEMA_V2 = "pid-rs/certified-sxpid-independent-verification/v2"
VERIFICATION_SCHEMA = "pid-rs/certified-sxpid-independent-verification/v3"
INCIDENT_PATH = (
    "audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md"
)
INCIDENT_LOG_SHA256 = "7c9aa8c1c5f08506dc9dacfb54a9826fecf38393fc823e39dd0460bc1d0094db"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SELF_TEST_VECTOR_BYTES = 8 * 1024 * 1024
MAX_CHECKER_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_CHECKER_STDERR_BYTES = 64 * 1024
PASS_OUTPUT = b'{"result":"pass"}\n'
CHECKER_OPTIONS = {"--self-test-vectors"}
CHECKER_STDIN_BOOTSTRAP = """\
import hashlib
import os
import sys
import tempfile

_PREFIX = "certified checker stdin launcher failed: "
_MAX_SOURCE = 4 * 1024 * 1024
_MAX_REQUEST = 8 * 1024 * 1024

def _fail(message):
    print(_PREFIX + message, file=sys.stderr)
    raise SystemExit(2)

def _size(raw, limit, label, allow_zero):
    if not raw.isascii() or not raw.isdecimal() or (raw != "0" and raw.startswith("0")):
        _fail(label + " size is not canonical decimal")
    value = int(raw)
    if value > limit or (not allow_zero and value == 0):
        _fail(label + " size is outside its byte bound")
    return value

def _digest(raw, label):
    if len(raw) != 64 or any(character not in "0123456789abcdef" for character in raw):
        _fail(label + " SHA-256 is malformed")
    return raw

def _read_exact(size, label):
    chunks = []
    remaining = size
    while remaining:
        chunk = os.read(0, min(remaining, 65536))
        if not chunk:
            _fail(label + " frame is short")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)

if len(sys.argv) < 7:
    _fail("argument inventory differs")
_logical_file, _logical_root = sys.argv[1], sys.argv[2]
if not os.path.isabs(_logical_root) or os.path.realpath(_logical_root) != _logical_root:
    _fail("logical root is not canonical")
if os.path.realpath(os.getcwd()) != _logical_root:
    _fail("working directory differs from the logical root")
if _logical_file != os.path.join(_logical_root, "scripts", "check-certified-sxpid2-claim.py"):
    _fail("logical checker path differs")
_source_size = _size(sys.argv[3], _MAX_SOURCE, "source", False)
_source_digest = _digest(sys.argv[4], "source")
_request_size = _size(sys.argv[5], _MAX_REQUEST, "request", True)
_request_digest = _digest(sys.argv[6], "request")
_checker_arguments = sys.argv[7:]
_source = _read_exact(_source_size, "source")
if hashlib.sha256(_source).hexdigest() != _source_digest:
    _fail("source SHA-256 mismatch")
_request = _read_exact(_request_size, "request")
if hashlib.sha256(_request).hexdigest() != _request_digest:
    _fail("request SHA-256 mismatch")
if os.read(0, 1) != b"":
    _fail("unexpected trailing input")
_input = tempfile.TemporaryFile(mode="w+b")
if _input.write(_request) != len(_request):
    _fail("request staging write was short")
_input.flush()
_input.seek(0)
os.dup2(_input.fileno(), 0)
sys.stdin = open(0, "r", encoding="utf-8", errors="strict", closefd=False)
os.chdir(_logical_root)
sys.argv = [_logical_file, *_checker_arguments]
_globals = {
    "__builtins__": __builtins__,
    "__cached__": None,
    "__file__": _logical_file,
    "__name__": "__main__",
    "__package__": None,
    "__spec__": None,
}
exec(compile(_source, _logical_file, "exec", dont_inherit=True), _globals)
"""
EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE_BYTES = 2776
EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256 = (
    "e843b76db3f67b3bb331be12b346423a10e748edaf119c920d06b71318de95e8"
)
PRIVATE_BLOCK_BEGIN = b"# BEGIN KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
PRIVATE_BLOCK_END = b"# END KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
BOOTSTRAP_BLOCK_BEGIN = b"# BEGIN KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
BOOTSTRAP_BLOCK_END = b"# END KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
EXPECTED_CHECKER_BOOTSTRAP_SIZE_BYTES = 668
EXPECTED_CHECKER_BOOTSTRAP_SHA256 = (
    "1129a9c3987603fbf16507edc8adebc54a69f7a9acf68494a099247bf41a6106"
)
EXECUTION_CONTAINER_ASSIGNMENT = "EXPECTED_EXECUTION_CONTAINER_SHA256"
REVIEWED_DOCUMENTATION_ASSIGNMENT = "EXPECTED_REVIEWED_DOCUMENTATION_SHA256"
JUST_RELEASE_AUDIT_ASSIGNMENT = "EXPECTED_JUST_RELEASE_AUDIT_LINE_SHA256"
SUPPORT_GATE_ASSIGNMENT = "EXPECTED_SUPPORT_GATE_SHA256"
GATE_COMMANDS_ASSIGNMENT = "GATE_COMMANDS"
CI_JOB_DIGEST_ASSIGNMENT = "EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256"
JUST_RECIPE_DIGEST_ASSIGNMENT = "EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256"
EXPECTED_CI_JOB_DIGEST = (
    "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda"
)
EXPECTED_JUST_RECIPE_DIGEST = (
    "fbd80548b0c62cb46f646e77e5f1df37d439299e71faec9bd05656839f660ae7"
)
EXECUTION_CONTAINER_PATHS = frozenset({".github/workflows/ci.yml", "justfile"})
REVIEWED_DOCUMENTATION_PATHS = frozenset(
    {"audit/tools/certified-sxpid/README.md", "scripts/README.md"}
)
SUPPORT_GATE_PATHS = frozenset({"scripts/check-formal-pdf-set.sh"})
AUDIT_TOOL_README = "audit/tools/certified-sxpid/README.md"
SCRIPTS_README = "scripts/README.md"
ANCHOR_GATE_COMMANDS = (
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "python3 scripts/check-lean-exact-log-product.py",
    "python3 scripts/check-certified-sxpid2-claim.py",
    "python3 scripts/check-certified-sxpid2-claim-self-test.py",
)
CANDIDATE_GATE_COMMANDS = (
    *ANCHOR_GATE_COMMANDS[:5],
    "python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
)
EXPECTED_SNAPSHOT_MUTATIONS = 117
EXPECTED_NEW_SOURCE_MUTATIONS = 6
EXPECTED_NEW_HUGE_INTEGER_MUTATIONS = 1
PYC_MAGIC_BY_MINOR = {
    (3, 11): bytes.fromhex("a70d0d0a"),
    (3, 12): bytes.fromhex("cb0d0d0a"),
    (3, 13): bytes.fromhex("f30d0d0a"),
    (3, 14): bytes.fromhex("2b0e0d0a"),
}


class SelfTestError(RuntimeError):
    """The certified-SxPID2 hostile suite produced an unexpected result."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


@dataclass(frozen=True)
class Snapshot:
    text: dict[str, str]
    json_values: dict[str, Any]
    sha256: dict[str, str]
    raw_text_sha256: dict[str, str]


def canonical_json(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise SelfTestError("self-test value cannot be canonically encoded") from error
    return (rendered + "\n").encode("utf-8")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key in checker response: {key!r}")
        value[key] = item
    return value


def reject_nonfinite_json_constant(value: str) -> None:
    raise SelfTestError(f"non-finite JSON constant in checker response: {value}")


def parse_canonical_json(raw: bytes, label: str) -> Any:
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelfTestError(f"{label} is not strict JSON: {error}") from error
    require(raw == canonical_json(value), f"{label} is not canonical JSON")
    return value


def exact_mapping(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} is not an object")
    require(set(value) == keys, f"{label} key inventory differs")
    return value


def stable_source(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise SelfTestError(f"cannot open source descriptor {path}: {error}") from error
    try:
        before = os.fstat(descriptor)
        path_before = path.lstat()
        require(stat.S_ISREG(before.st_mode), f"source is not regular: {path}")
        require(before.st_nlink == 1, f"source is hard-linked: {path}")
        require(
            0 < before.st_size <= MAX_SOURCE_BYTES,
            f"source size is invalid: {path}",
        )
        require(
            (path_before.st_dev, path_before.st_ino) == (before.st_dev, before.st_ino),
            f"source path and descriptor differ: {path}",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            require(chunk != b"", f"source descriptor read was short: {path}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"source grew while read: {path}")
        after = os.fstat(descriptor)
        path_after = path.lstat()
    finally:
        os.close(descriptor)

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

    require(
        identity(before)
        == identity(after)
        == identity(path_before)
        == identity(path_after),
        f"source changed while descriptor was read: {path}",
    )
    raw = b"".join(chunks)
    require(len(raw) == before.st_size, f"source descriptor read was short: {path}")
    return raw


def parse_python_source(raw: bytes, label: str) -> tuple[str, ast.Module]:
    try:
        source = raw.decode("utf-8", errors="strict")
        tree = ast.parse(source, filename=label)
    except (SyntaxError, UnicodeDecodeError) as error:
        raise SelfTestError(f"cannot parse {label}: {error}") from error
    return source, tree


def top_level_literal_assignment(
    source: str, tree: ast.Module, name: str
) -> tuple[str, Any]:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    require(len(matches) == 1, f"checker assignment is not unique: {name}")
    segment = ast.get_source_segment(source, matches[0])
    require(isinstance(segment, str) and segment, f"cannot recover assignment: {name}")
    try:
        value = ast.literal_eval(matches[0].value)
    except (TypeError, ValueError) as error:
        raise SelfTestError(f"checker assignment is not literal: {name}") from error
    return segment, value


def top_level_assignment(
    source: str, tree: ast.Module, name: str
) -> tuple[str, dict[str, str]]:
    segment, value = top_level_literal_assignment(source, tree, name)
    require(
        isinstance(value, dict)
        and all(
            isinstance(key, str) and isinstance(item, str)
            for key, item in value.items()
        ),
        f"checker assignment is not a string mapping: {name}",
    )
    return segment, value


def top_level_function_segment(source: str, tree: ast.Module, name: str) -> str:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(len(matches) == 1, f"checker function is not unique: {name}")
    segment = ast.get_source_segment(source, matches[0])
    require(isinstance(segment, str) and segment, f"cannot recover function: {name}")
    return segment


def replace_once(source: str, old: str, new: str, label: str) -> str:
    require(source.count(old) == 1, f"source segment is not unique: {label}")
    return source.replace(old, new, 1)


def validate_digest_mapping(
    value: dict[str, str], expected_paths: frozenset[str], label: str
) -> None:
    require(set(value) == expected_paths, f"{label} path inventory changed")
    require(
        all(re.fullmatch(r"[0-9a-f]{64}", item) is not None for item in value.values()),
        f"{label} contains a non-SHA-256 value",
    )


def validate_checker_source_reconstruction(
    anchor_raw: bytes, candidate_raw: bytes
) -> ast.Module:
    require(
        candidate_raw.count(BOOTSTRAP_BLOCK_BEGIN) == 1
        and candidate_raw.count(BOOTSTRAP_BLOCK_END) == 1,
        "checker bootstrap marker inventory changed",
    )
    bootstrap_begin = candidate_raw.index(BOOTSTRAP_BLOCK_BEGIN)
    bootstrap_end = candidate_raw.index(BOOTSTRAP_BLOCK_END, bootstrap_begin) + len(
        BOOTSTRAP_BLOCK_END
    )
    require(bootstrap_begin < bootstrap_end, "checker bootstrap markers are reversed")
    require(
        candidate_raw[bootstrap_begin - 2 : bootstrap_begin] == b"\n\n"
        and candidate_raw[bootstrap_end : bootstrap_end + 2] == b"\n\n",
        "checker bootstrap blank-line convention changed",
    )
    bootstrap_raw = candidate_raw[
        bootstrap_begin : bootstrap_end - len(BOOTSTRAP_BLOCK_END)
    ]
    require(
        len(bootstrap_raw) == EXPECTED_CHECKER_BOOTSTRAP_SIZE_BYTES
        and hashlib.sha256(bootstrap_raw).hexdigest()
        == EXPECTED_CHECKER_BOOTSTRAP_SHA256,
        "checker bootstrap exact bytes changed",
    )
    _bootstrap_source, bootstrap_tree = parse_python_source(
        bootstrap_raw, "<certified-sxpid2-checker-bootstrap>"
    )
    require(
        sum(
            isinstance(node, ast.Import)
            and len(node.names) == 1
            and node.names[0].name == "sys"
            and node.names[0].asname == "_bootstrap_sys"
            for node in bootstrap_tree.body
        )
        == 1,
        "checker bootstrap lost its fixed sys import",
    )
    without_bootstrap = (
        candidate_raw[:bootstrap_begin] + candidate_raw[bootstrap_end + 2 :]
    )
    require(
        without_bootstrap.count(PRIVATE_BLOCK_BEGIN) == 1
        and without_bootstrap.count(PRIVATE_BLOCK_END) == 1,
        "checker private-vector marker inventory changed",
    )
    begin = without_bootstrap.index(PRIVATE_BLOCK_BEGIN)
    end = without_bootstrap.index(PRIVATE_BLOCK_END, begin) + len(PRIVATE_BLOCK_END)
    require(begin < end, "checker private-vector markers are reversed")
    require(
        without_bootstrap[begin - 2 : begin] == b"\n\n"
        and without_bootstrap[end : end + 1] == b"\n",
        "checker private-vector blank-line convention changed",
    )
    reconstructed_raw = without_bootstrap[: begin - 2] + without_bootstrap[end + 1 :]
    anchor_source, anchor_tree = parse_python_source(
        anchor_raw, "<cb3f-certified-checker>"
    )
    candidate_source, candidate_tree = parse_python_source(
        reconstructed_raw, "<reconstructed-certified-checker>"
    )

    anchor_execution_segment, anchor_execution = top_level_assignment(
        anchor_source, anchor_tree, EXECUTION_CONTAINER_ASSIGNMENT
    )
    candidate_execution_segment, candidate_execution = top_level_assignment(
        candidate_source, candidate_tree, EXECUTION_CONTAINER_ASSIGNMENT
    )
    anchor_documentation_segment, anchor_documentation = top_level_assignment(
        anchor_source, anchor_tree, REVIEWED_DOCUMENTATION_ASSIGNMENT
    )
    candidate_documentation_segment, candidate_documentation = top_level_assignment(
        candidate_source, candidate_tree, REVIEWED_DOCUMENTATION_ASSIGNMENT
    )
    anchor_release_segment, anchor_release_digest = top_level_literal_assignment(
        anchor_source, anchor_tree, JUST_RELEASE_AUDIT_ASSIGNMENT
    )
    candidate_release_segment, candidate_release_digest = top_level_literal_assignment(
        candidate_source, candidate_tree, JUST_RELEASE_AUDIT_ASSIGNMENT
    )
    anchor_support_segment, anchor_support = top_level_assignment(
        anchor_source, anchor_tree, SUPPORT_GATE_ASSIGNMENT
    )
    candidate_support_segment, candidate_support = top_level_assignment(
        candidate_source, candidate_tree, SUPPORT_GATE_ASSIGNMENT
    )
    anchor_gate_segment, anchor_gate_commands = top_level_literal_assignment(
        anchor_source, anchor_tree, GATE_COMMANDS_ASSIGNMENT
    )
    candidate_gate_segment, candidate_gate_commands = top_level_literal_assignment(
        candidate_source, candidate_tree, GATE_COMMANDS_ASSIGNMENT
    )
    anchor_ci_segment, anchor_ci_digest = top_level_literal_assignment(
        anchor_source, anchor_tree, CI_JOB_DIGEST_ASSIGNMENT
    )
    candidate_ci_segment, candidate_ci_digest = top_level_literal_assignment(
        candidate_source, candidate_tree, CI_JOB_DIGEST_ASSIGNMENT
    )
    anchor_just_segment, anchor_just_digest = top_level_literal_assignment(
        anchor_source, anchor_tree, JUST_RECIPE_DIGEST_ASSIGNMENT
    )
    candidate_just_segment, candidate_just_digest = top_level_literal_assignment(
        candidate_source, candidate_tree, JUST_RECIPE_DIGEST_ASSIGNMENT
    )
    require(
        anchor_gate_commands == ANCHOR_GATE_COMMANDS,
        "anchor certified gate-command inventory changed",
    )
    require(
        candidate_gate_commands == CANDIDATE_GATE_COMMANDS,
        "candidate certified gate-command inventory changed",
    )
    require(
        isinstance(anchor_ci_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", anchor_ci_digest) is not None
        and candidate_ci_digest == EXPECTED_CI_JOB_DIGEST,
        "candidate certified workflow-job digest changed",
    )
    require(
        isinstance(anchor_just_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", anchor_just_digest) is not None
        and candidate_just_digest == EXPECTED_JUST_RECIPE_DIGEST,
        "candidate certified Just-recipe digest changed",
    )
    validate_digest_mapping(
        anchor_execution, EXECUTION_CONTAINER_PATHS, "anchor execution-container rebind"
    )
    validate_digest_mapping(
        candidate_execution,
        EXECUTION_CONTAINER_PATHS,
        "candidate execution-container rebind",
    )
    validate_digest_mapping(
        anchor_documentation,
        REVIEWED_DOCUMENTATION_PATHS,
        "anchor reviewed-documentation rebind",
    )
    validate_digest_mapping(
        candidate_documentation,
        REVIEWED_DOCUMENTATION_PATHS,
        "candidate reviewed-documentation rebind",
    )
    require(
        isinstance(anchor_release_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", anchor_release_digest) is not None
        and isinstance(candidate_release_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", candidate_release_digest) is not None,
        "release-audit-line rebind is not a SHA-256 value",
    )
    validate_digest_mapping(
        anchor_support, SUPPORT_GATE_PATHS, "anchor support-gate rebind"
    )
    validate_digest_mapping(
        candidate_support, SUPPORT_GATE_PATHS, "candidate support-gate rebind"
    )
    require(
        candidate_documentation[AUDIT_TOOL_README]
        == anchor_documentation[AUDIT_TOOL_README],
        "audit-tool README digest changed",
    )

    normalized_anchor = anchor_source
    normalized_candidate = candidate_source
    for label, anchor_segment, candidate_segment in (
        (
            "execution-container-rebind",
            anchor_execution_segment,
            candidate_execution_segment,
        ),
        (
            "reviewed-documentation-rebind",
            anchor_documentation_segment,
            candidate_documentation_segment,
        ),
        (
            "release-audit-line-rebind",
            anchor_release_segment,
            candidate_release_segment,
        ),
        (
            "support-gate-rebind",
            anchor_support_segment,
            candidate_support_segment,
        ),
        ("isolated-gate-commands", anchor_gate_segment, candidate_gate_segment),
        ("workflow-job-digest", anchor_ci_segment, candidate_ci_segment),
        ("just-recipe-digest", anchor_just_segment, candidate_just_segment),
    ):
        placeholder = f"<NORMALIZED-{label}>"
        normalized_anchor = replace_once(
            normalized_anchor, anchor_segment, placeholder, f"anchor {label}"
        )
        normalized_candidate = replace_once(
            normalized_candidate, candidate_segment, placeholder, f"candidate {label}"
        )
    require(
        normalized_anchor == normalized_candidate,
        "checker bytes outside the marked block, four digest-rebind assignments, "
        "and separately enumerated gate bindings differ from cb3f",
    )
    private_raw = without_bootstrap[
        begin + len(PRIVATE_BLOCK_BEGIN) : end - len(PRIVATE_BLOCK_END)
    ]
    _private_source, private_tree = parse_python_source(
        private_raw, "<certified-sxpid2-private-vector-block>"
    )
    return private_tree


def replace_checker_mapping(raw: bytes, name: str, value: dict[str, str]) -> bytes:
    source, tree = parse_python_source(raw, "<checker-source-mutant>")
    segment, _current = top_level_assignment(source, tree, name)
    replacement = f"{name} = {value!r}"
    return replace_once(source, segment, replacement, name).encode("utf-8")


def replace_checker_literal(raw: bytes, name: str, value: object) -> bytes:
    source, tree = parse_python_source(raw, "<checker-source-mutant>")
    segment, _current = top_level_literal_assignment(source, tree, name)
    replacement = f"{name} = {value!r}"
    return replace_once(source, segment, replacement, name).encode("utf-8")


def expect_checker_source_rejection(
    name: str, anchor_raw: bytes, candidate_raw: bytes, expected: str
) -> None:
    try:
        validate_checker_source_reconstruction(anchor_raw, candidate_raw)
    except SelfTestError as error:
        require(expected in str(error), f"{name}: wrong source rejection: {error}")
        return
    raise SelfTestError(f"{name}: checker source mutation unexpectedly passed")


def validate_checker_source_mutations(anchor_raw: bytes, candidate_raw: bytes) -> int:
    candidate_source, candidate_tree = parse_python_source(
        candidate_raw, "<live-certified-checker>"
    )
    _execution_segment, execution = top_level_assignment(
        candidate_source, candidate_tree, EXECUTION_CONTAINER_ASSIGNMENT
    )
    _documentation_segment, documentation = top_level_assignment(
        candidate_source, candidate_tree, REVIEWED_DOCUMENTATION_ASSIGNMENT
    )
    _support_segment, support = top_level_assignment(
        candidate_source, candidate_tree, SUPPORT_GATE_ASSIGNMENT
    )

    bootstrap_guard = b"and _bootstrap_sys.flags.isolated == 1"
    require(
        candidate_raw.count(bootstrap_guard) == 1,
        "checker bootstrap isolation guard is not unique",
    )
    expect_checker_source_rejection(
        "checker-bootstrap-isolation-weakened",
        anchor_raw,
        candidate_raw.replace(
            bootstrap_guard,
            b"and _bootstrap_sys.flags.isolated >= 0",
            1,
        ),
        "checker bootstrap exact bytes changed",
    )

    fourth = dict(execution)
    fourth["unreviewed/fourth-container"] = "0" * 64
    expect_checker_source_rejection(
        "fourth-container-rebind",
        anchor_raw,
        replace_checker_mapping(candidate_raw, EXECUTION_CONTAINER_ASSIGNMENT, fourth),
        "candidate execution-container rebind path inventory changed",
    )

    moved_execution = dict(execution)
    moved_execution[SCRIPTS_README] = documentation[SCRIPTS_README]
    moved_documentation = dict(documentation)
    del moved_documentation[SCRIPTS_README]
    moved = replace_checker_mapping(
        candidate_raw, EXECUTION_CONTAINER_ASSIGNMENT, moved_execution
    )
    moved = replace_checker_mapping(
        moved, REVIEWED_DOCUMENTATION_ASSIGNMENT, moved_documentation
    )
    expect_checker_source_rejection(
        "scripts-readme-rebind-moved",
        anchor_raw,
        moved,
        "candidate execution-container rebind path inventory changed",
    )

    audit_drift = dict(documentation)
    audit_drift[AUDIT_TOOL_README] = "0" * 64
    expect_checker_source_rejection(
        "audit-tool-readme-rebind-drift",
        anchor_raw,
        replace_checker_mapping(
            candidate_raw, REVIEWED_DOCUMENTATION_ASSIGNMENT, audit_drift
        ),
        "audit-tool README digest changed",
    )

    expanded_support = dict(support)
    expanded_support["scripts/unreviewed-support-gate.sh"] = "0" * 64
    expect_checker_source_rejection(
        "support-gate-rebind-inventory-expanded",
        anchor_raw,
        replace_checker_mapping(candidate_raw, SUPPORT_GATE_ASSIGNMENT, expanded_support),
        "candidate support-gate rebind path inventory changed",
    )

    expect_checker_source_rejection(
        "release-audit-line-rebind-malformed",
        anchor_raw,
        replace_checker_literal(
            candidate_raw, JUST_RELEASE_AUDIT_ASSIGNMENT, "not-a-sha256"
        ),
        "release-audit-line rebind is not a SHA-256 value",
    )
    return EXPECTED_NEW_SOURCE_MUTATIONS


def validate_checker_stdin_bootstrap() -> None:
    raw = CHECKER_STDIN_BOOTSTRAP.encode("utf-8")
    require(
        len(raw) == EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256,
        "checker stdin bootstrap exact bytes changed",
    )
    _source, tree = parse_python_source(
        raw, "<certified-sxpid2-checker-stdin-bootstrap>"
    )
    imports = [
        tuple(alias.name for alias in node.names)
        for node in tree.body
        if isinstance(node, ast.Import)
    ]
    require(
        imports == [("hashlib",), ("os",), ("sys",), ("tempfile",)],
        "checker stdin bootstrap import inventory changed",
    )
    require(
        not any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)),
        "checker stdin bootstrap acquired a from-import",
    )
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    require(
        functions == ["_fail", "_size", "_digest", "_read_exact"],
        "checker stdin bootstrap function inventory changed",
    )
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    named_calls = [node.func.id for node in calls if isinstance(node.func, ast.Name)]
    require(
        named_calls.count("compile") == 1 and named_calls.count("exec") == 1,
        "checker stdin bootstrap exact-source execution route changed",
    )
    require(
        not any(name in {"__import__", "eval"} for name in named_calls),
        "checker stdin bootstrap acquired dynamic source loading",
    )
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        "checker stdin bootstrap acquired an optimization-sensitive assert",
    )
    required_attributes = {
        "chdir",
        "dup2",
        "read",
        "sha256",
        "TemporaryFile",
    }
    attributes = {
        node.func.attr for node in calls if isinstance(node.func, ast.Attribute)
    }
    require(
        required_attributes <= attributes,
        "checker stdin bootstrap lost descriptor or digest custody",
    )


def validate_static_cli_custody(checker_source: bytes) -> int:
    validate_checker_stdin_bootstrap()
    forbidden_imports = {"importlib", "runpy", "zipimport"}
    forbidden_calls = {"__import__", "compile", "eval", "exec"}
    forbidden_attributes = {
        "SourceFileLoader",
        "SourcelessFileLoader",
        "exec_module",
        "load_module",
        "module_from_spec",
        "run_module",
        "run_path",
        "spec_from_file_location",
    }
    checker_options: set[str] = set()
    checker_abbreviations_disabled = False
    checker_help_disabled = False
    source_mutation_count = 0
    for path in (CHECKER, SCRIPT):
        raw = checker_source if path == CHECKER else stable_source(path)
        if path == CHECKER:
            anchor = subprocess.run(
                [
                    "/usr/bin/git",
                    "-C",
                    os.fspath(ROOT),
                    "show",
                    f"{CHECKER_ANCHOR}:scripts/check-certified-sxpid2-claim.py",
                ],
                cwd=ROOT,
                env=safe_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
            )
            require(
                anchor.returncode == 0 and anchor.stderr == b"",
                "cannot read the fixed cb3f certified-checker authority",
            )
            private_tree = validate_checker_source_reconstruction(anchor.stdout, raw)
            source_mutation_count = validate_checker_source_mutations(
                anchor.stdout, raw
            )
            require(
                sum(
                    isinstance(node, ast.Import)
                    and [alias.name for alias in node.names] == ["argparse"]
                    for node in private_tree.body
                )
                == 1,
                "private checker block lost its fixed argparse import",
            )
        try:
            tree = ast.parse(
                raw.decode("utf-8", errors="strict"), filename=os.fspath(path)
            )
        except (SyntaxError, UnicodeDecodeError) as error:
            raise SelfTestError(
                f"cannot parse fixed CLI source {path}: {error}"
            ) from error
        if path == SCRIPT:
            direct_routes: dict[str, list[ast.Call]] = {}
            for function in (
                node for node in tree.body if isinstance(node, ast.FunctionDef)
            ):
                calls = [
                    node
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "run_direct_checker"
                ]
                if calls:
                    direct_routes[function.name] = calls
            require(
                {name: len(calls) for name, calls in direct_routes.items()}
                == {
                    "validate_adjacent_unchecked_hash_pyc_nonexecution": 1,
                    "validate_cli_controls": 1,
                },
                "direct-script control inventory changed",
            )
            for name, calls in direct_routes.items():
                for call in calls:
                    segment = ast.get_source_segment(
                        raw.decode("utf-8", errors="strict"), call
                    )
                    expected_target = (
                        "os.fspath(fixture_checker)"
                        if name == "validate_adjacent_unchecked_hash_pyc_nonexecution"
                        else "os.fspath(SCRIPT)"
                    )
                    require(
                        isinstance(segment, str)
                        and "os.fspath(CHECKER)" not in segment,
                        f"live checker regained direct-path execution in {name}",
                    )
                    require(
                        expected_target in segment,
                        f"direct-script control target changed in {name}",
                    )
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                raise SelfTestError(f"optimization-sensitive assert in {path}")
            if isinstance(node, ast.Import):
                roots = {alias.name.partition(".")[0] for alias in node.names}
                require(
                    not roots & forbidden_imports, f"dynamic loader import in {path}"
                )
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").partition(".")[0]
                require(
                    root not in forbidden_imports, f"dynamic loader import in {path}"
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    require(
                        node.func.id not in forbidden_calls,
                        f"dynamic source execution call in {path}",
                    )
                elif isinstance(node.func, ast.Attribute):
                    require(
                        node.func.attr not in forbidden_attributes,
                        f"dynamic loader call in {path}",
                    )
                if path == CHECKER and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "ArgumentParser":
                        for keyword in node.keywords:
                            if keyword.arg == "allow_abbrev":
                                checker_abbreviations_disabled = (
                                    isinstance(keyword.value, ast.Constant)
                                    and keyword.value.value is False
                                )
                            if keyword.arg == "add_help":
                                checker_help_disabled = (
                                    isinstance(keyword.value, ast.Constant)
                                    and keyword.value.value is False
                                )
                    if node.func.attr == "add_argument" and node.args:
                        option = node.args[0]
                        if isinstance(option, ast.Constant) and isinstance(
                            option.value, str
                        ):
                            checker_options.add(option.value)
    require(
        checker_options == CHECKER_OPTIONS,
        "checker CLI option inventory changed or acquired a path-valued argument",
    )
    require(checker_abbreviations_disabled, "checker CLI re-enabled abbreviations")
    require(checker_help_disabled, "checker CLI acquired an unreviewed help route")
    require(
        source_mutation_count == EXPECTED_NEW_SOURCE_MUTATIONS,
        "checker source-mutation count drifted",
    )
    return source_mutation_count


def safe_environment() -> dict[str, str]:
    return {
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
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }


def run_checker_source(
    checker_source: bytes,
    request: bytes,
    *,
    checker_arguments: tuple[str, ...] = ("--self-test-vectors",),
    python_prefix: tuple[str, ...] = PYTHON_CHILD_PREFIX,
    logical_file: Path = CHECKER,
    logical_root: Path = ROOT,
    declared_source_size: str | None = None,
    declared_source_sha256: str | None = None,
    declared_request_size: str | None = None,
    declared_request_sha256: str | None = None,
    stdin_payload: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    require(
        len(checker_source) <= MAX_SOURCE_BYTES,
        "checker source exceeds launcher byte bound",
    )
    require(
        len(request) <= MAX_SELF_TEST_VECTOR_BYTES,
        "checker request exceeds launcher byte bound",
    )
    source_size = (
        str(len(checker_source))
        if declared_source_size is None
        else declared_source_size
    )
    source_sha256 = (
        hashlib.sha256(checker_source).hexdigest()
        if declared_source_sha256 is None
        else declared_source_sha256
    )
    request_size = (
        str(len(request)) if declared_request_size is None else declared_request_size
    )
    request_sha256 = (
        hashlib.sha256(request).hexdigest()
        if declared_request_sha256 is None
        else declared_request_sha256
    )
    payload = checker_source + request if stdin_payload is None else stdin_payload
    try:
        completed = subprocess.run(
            [
                *python_prefix,
                "-c",
                CHECKER_STDIN_BOOTSTRAP,
                os.fspath(logical_file),
                os.fspath(logical_root),
                source_size,
                source_sha256,
                request_size,
                request_sha256,
                *checker_arguments,
            ],
            cwd=ROOT,
            env=safe_environment(),
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SelfTestError(f"fixed checker invocation failed: {error}") from error
    require(
        len(completed.stdout) <= MAX_CHECKER_OUTPUT_BYTES,
        "checker response exceeds byte bound",
    )
    require(
        len(completed.stderr) <= MAX_CHECKER_STDERR_BYTES,
        "checker standard error exceeds byte bound",
    )
    return completed


def invoke_checker(
    checker_source: bytes, request: dict[str, Any]
) -> subprocess.CompletedProcess[bytes]:
    return run_checker_source(checker_source, canonical_json(request))


def vector(operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "arguments": arguments,
        "operation": operation,
        "schema": SELF_TEST_VECTOR_SCHEMA,
    }


def decode_snapshot(value: Any) -> Snapshot:
    values = exact_mapping(
        value,
        {"json_values", "raw_text_sha256", "sha256", "text"},
        "checker snapshot",
    )
    for name in ("json_values", "raw_text_sha256", "sha256", "text"):
        require(
            isinstance(values[name], dict), f"checker snapshot {name} is not an object"
        )
    for name in ("raw_text_sha256", "sha256", "text"):
        require(
            all(
                isinstance(key, str) and isinstance(item, str)
                for key, item in values[name].items()
            ),
            f"checker snapshot {name} contains a non-string entry",
        )
    require(
        all(isinstance(key, str) for key in values["json_values"]),
        "checker snapshot JSON map contains a non-string path",
    )
    return Snapshot(
        text=values["text"],
        json_values=values["json_values"],
        sha256=values["sha256"],
        raw_text_sha256=values["raw_text_sha256"],
    )


def read_snapshot(checker_source: bytes) -> Snapshot:
    completed = invoke_checker(checker_source, vector("snapshot", {}))
    require(
        completed.returncode == 0 and completed.stderr == b"",
        "fixed checker snapshot route failed: "
        + completed.stderr.decode("utf-8", errors="replace"),
    )
    response = exact_mapping(
        parse_canonical_json(completed.stdout, "checker snapshot response"),
        {"result", "snapshot"},
        "checker snapshot response",
    )
    require(response["result"] == "snapshot", "checker snapshot result differs")
    return decode_snapshot(response["snapshot"])


def snapshot_delta(baseline: Snapshot, candidate: Snapshot) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    for name in ("json_values", "raw_text_sha256", "sha256", "text"):
        before = getattr(baseline, name)
        after = getattr(candidate, name)
        require(
            set(before) == set(after), f"mutation changed the {name} path inventory"
        )
        delta[name] = {
            path: after[path] for path in sorted(after) if before[path] != after[path]
        }
    return delta


def validate_snapshot(
    checker_source: bytes, snapshot: Snapshot, baseline: Snapshot
) -> tuple[bool, str | None]:
    completed = invoke_checker(
        checker_source,
        vector("validate", {"delta": snapshot_delta(baseline, snapshot)}),
    )
    require(
        completed.stderr == b"", "snapshot validator wrote unexpected standard error"
    )
    response = parse_canonical_json(completed.stdout, "snapshot validation response")
    if completed.returncode == 0:
        values = exact_mapping(response, {"result"}, "passing validation response")
        require(values["result"] == "pass", "passing validation result differs")
        return True, None
    if completed.returncode == 1:
        values = exact_mapping(
            response, {"error", "result"}, "failing validation response"
        )
        require(
            values["result"] == "fail" and isinstance(values["error"], str),
            "failing validation result differs",
        )
        return False, values["error"]
    raise SelfTestError(
        "snapshot validator returned a noncanonical status: "
        f"rc={completed.returncode}, stdout={completed.stdout!r}"
    )


def mutated_text(snapshot: Any, path: str, old: str, new: str) -> Any:
    text = dict(snapshot.text)
    count = text[path].count(old)
    if count != 1:
        raise RuntimeError(
            f"self-test fixture token count in {path} is {count}, expected 1: {old!r}"
        )
    text[path] = text[path].replace(old, new, 1)
    raw_text_hashes = dict(snapshot.raw_text_sha256)
    raw_text_hashes[path] = hashlib.sha256(text[path].encode("utf-8")).hexdigest()
    source_hashes = dict(snapshot.sha256)
    if path in source_hashes:
        source_hashes[path] = raw_text_hashes[path]
    return Snapshot(
        text=text,
        json_values=copy.deepcopy(snapshot.json_values),
        sha256=source_hashes,
        raw_text_sha256=raw_text_hashes,
    )


def transformed_text(snapshot: Any, path: str, transform: Callable[[str], str]) -> Any:
    text = dict(snapshot.text)
    text[path] = transform(text[path])
    raw_text_hashes = dict(snapshot.raw_text_sha256)
    raw_text_hashes[path] = hashlib.sha256(text[path].encode("utf-8")).hexdigest()
    source_hashes = dict(snapshot.sha256)
    if path in source_hashes:
        source_hashes[path] = raw_text_hashes[path]
    return Snapshot(
        text=text,
        json_values=copy.deepcopy(snapshot.json_values),
        sha256=source_hashes,
        raw_text_sha256=raw_text_hashes,
    )


def mutated_json(snapshot: Any, path: str, mutate: Callable[[Any], None]) -> Any:
    values = copy.deepcopy(snapshot.json_values)
    mutate(values[path])
    return Snapshot(
        text=dict(snapshot.text),
        json_values=values,
        sha256=dict(snapshot.sha256),
        raw_text_sha256=dict(snapshot.raw_text_sha256),
    )


def method(catalog: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in catalog["methods"] if item["id"] == METHOD_ID)


def expect_failure(
    checker_source: bytes,
    name: str,
    snapshot: Snapshot,
    expected: str,
    baseline: Snapshot,
) -> None:
    passed, error = validate_snapshot(checker_source, snapshot, baseline)
    if passed:
        raise SelfTestError(f"{name}: mutation unexpectedly passed")
    require(error is not None, f"{name}: rejected mutation omitted its error")
    if expected not in error:
        raise SelfTestError(f"{name}: wrong failure: {error}")


def run_direct_checker(
    command: list[str], raw: bytes, *, cwd: Path = ROOT
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=safe_environment(),
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SelfTestError(f"direct checker control failed: {error}") from error


def write_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        0o600,
    )
    try:
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "short write while constructing hostile cache")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def malicious_adjacent_cache_payload() -> None:
    """Payload embedded in an unchecked-hash cache; it must never execute."""

    with open(  # noqa: PTH123 -- intentionally self-contained hostile bytecode.
        "adjacent-pyc-executed", "wb"
    ) as stream:
        stream.write(b"unchecked hash cache executed")


def validate_adjacent_unchecked_hash_pyc_nonexecution(runtime_request: bytes) -> None:
    version = (sys.version_info.major, sys.version_info.minor)
    magic = PYC_MAGIC_BY_MINOR.get(version)
    require(magic is not None, f"unregistered Python bytecode magic: {version}")
    cache_tag = sys.implementation.cache_tag
    require(isinstance(cache_tag, str) and cache_tag, "Python cache tag is absent")
    unchecked_hash_header = magic + (1).to_bytes(4, "little") + b"\0" * 8
    malicious_cache = unchecked_hash_header + marshal.dumps(
        malicious_adjacent_cache_payload.__code__
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-certified-sxpid2-pyc-custody-"
    ) as temporary:
        fixture_root = Path(temporary).resolve(strict=True)
        fixture_scripts = fixture_root / "scripts"
        fixture_scripts.mkdir(mode=0o700)
        fixture_checker = fixture_scripts / CHECKER.name
        checker_source = stable_source(CHECKER)
        write_exclusive(fixture_checker, checker_source)
        require(
            stable_source(fixture_checker) == checker_source,
            "temporary checker fixture differs from the live checker source",
        )
        cache_directory = fixture_scripts / "__pycache__"
        cache_directory.mkdir(mode=0o700)
        optimization_suffix = ".opt-1" if sys.flags.optimize == 1 else ""
        cache_path = (
            cache_directory
            / f"{fixture_checker.stem}.{cache_tag}{optimization_suffix}.pyc"
        )
        write_exclusive(cache_path, malicious_cache)
        before_cache = hashlib.sha256(cache_path.read_bytes()).hexdigest()
        completed = run_direct_checker(
            [
                *PYTHON_CHILD_PREFIX,
                os.fspath(fixture_checker),
                "--self-test-vectors",
            ],
            runtime_request,
            cwd=fixture_root,
        )
        marker = fixture_root / "adjacent-pyc-executed"
        require(not marker.exists(), "adjacent unchecked-hash checker cache executed")
        require(
            completed.returncode == 0
            and completed.stdout == PASS_OUTPUT
            and completed.stderr == b"",
            "adjacent unchecked-hash cache changed fixed direct-script execution",
        )
        require(
            hashlib.sha256(cache_path.read_bytes()).hexdigest() == before_cache,
            "direct checker invocation rewrote the adjacent hostile cache",
        )


def expect_launcher_rejection(
    completed: subprocess.CompletedProcess[bytes], expected: bytes, label: str
) -> None:
    require(
        completed.returncode == 2
        and completed.stdout == b""
        and completed.stderr
        == b"certified checker stdin launcher failed: " + expected + b"\n",
        f"{label} did not produce the exact bounded launcher rejection: "
        f"rc={completed.returncode}, stdout={completed.stdout!r}, "
        f"stderr={completed.stderr!r}",
    )


def validate_launcher_controls(checker_source: bytes, runtime_request: bytes) -> None:
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            declared_source_size=str(MAX_SOURCE_BYTES + 1),
        ),
        b"source size is outside its byte bound",
        "oversize source declaration",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            declared_source_size="00",
        ),
        b"source size is not canonical decimal",
        "noncanonical source-size declaration",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            declared_source_sha256="0" * 64,
        ),
        b"source SHA-256 mismatch",
        "wrong source digest",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            b"",
            stdin_payload=checker_source[:-1],
        ),
        b"source frame is short",
        "truncated source frame",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            declared_request_size=str(MAX_SELF_TEST_VECTOR_BYTES + 1),
        ),
        b"request size is outside its byte bound",
        "oversize request declaration",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            declared_request_sha256="0" * 64,
        ),
        b"request SHA-256 mismatch",
        "wrong request digest",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            stdin_payload=checker_source + runtime_request + b"x",
        ),
        b"unexpected trailing input",
        "trailing extra byte",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            stdin_payload=checker_source + b"x" + runtime_request,
        ),
        b"request SHA-256 mismatch",
        "inter-frame extra byte",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            logical_file=ROOT / "scripts/not-the-certified-checker.py",
        ),
        b"logical checker path differs",
        "logical checker path drift",
    )
    expect_launcher_rejection(
        run_checker_source(
            checker_source,
            runtime_request,
            logical_root=ROOT / "scripts",
        ),
        b"working directory differs from the logical root",
        "logical checker root drift",
    )


def validate_cli_controls(checker_source: bytes) -> int:
    runtime_request = canonical_json(
        vector("runtime_mode", {"optimize": sys.flags.optimize})
    )
    runtime = run_checker_source(
        checker_source,
        runtime_request,
    )
    require(
        runtime.returncode == 0
        and runtime.stdout == PASS_OUTPUT
        and runtime.stderr == b"",
        "fixed isolated runtime-mode vector failed",
    )
    validate_launcher_controls(checker_source, runtime_request)
    nonisolated_checker = run_checker_source(
        checker_source,
        b"",
        checker_arguments=(),
        python_prefix=(sys.executable, "-B"),
    )
    require(
        nonisolated_checker.returncode == 2
        and nonisolated_checker.stdout == b""
        and b"check-certified-sxpid2-claim.py requires Python 3.11+ -I -S -B"
        in nonisolated_checker.stderr,
        "certified checker accepted a nonisolated production invocation",
    )
    twice_optimized_checker = run_checker_source(
        checker_source,
        b"",
        checker_arguments=(),
        python_prefix=(sys.executable, "-OO", "-I", "-S", "-B"),
    )
    require(
        twice_optimized_checker.returncode == 2
        and twice_optimized_checker.stdout == b""
        and b"at most one -O" in twice_optimized_checker.stderr,
        "certified checker accepted a twice-optimized production invocation",
    )
    nonisolated_self_test = run_direct_checker(
        [sys.executable, "-B", os.fspath(SCRIPT)],
        b"",
    )
    require(
        nonisolated_self_test.returncode == 2
        and nonisolated_self_test.stdout == b""
        and b"requires Python 3.11+ -I -S -B" in nonisolated_self_test.stderr,
        "certified self-test accepted a nonisolated direct invocation",
    )
    optimized_twice = run_checker_source(
        checker_source,
        runtime_request,
        python_prefix=(sys.executable, "-OO", "-I", "-S", "-B"),
    )
    require(
        optimized_twice.returncode == 2
        and optimized_twice.stdout == b""
        and b"check-certified-sxpid2-claim.py requires Python 3.11+ -I -S -B and at most one -O"
        in optimized_twice.stderr,
        "checker accepted -OO or rejected it noncanonically",
    )
    nonisolated = run_checker_source(
        checker_source,
        runtime_request,
        python_prefix=(sys.executable, "-B"),
    )
    require(
        nonisolated.returncode == 2
        and nonisolated.stdout == b""
        and b"check-certified-sxpid2-claim.py requires Python 3.11+ -I -S -B"
        in nonisolated.stderr,
        "checker accepted a nonisolated invocation",
    )
    abbreviated = run_checker_source(
        checker_source,
        runtime_request,
        checker_arguments=("--self-test-vector",),
    )
    require(
        abbreviated.returncode == 2
        and abbreviated.stdout == b""
        and b"unrecognized arguments: --self-test-vector" in abbreviated.stderr,
        "checker accepted an abbreviated private option",
    )
    for hostile_arguments in (
        ["--help"],
        ["unexpected-positional"],
        ["--self-test-vectors", "--self-test-vectors"],
        ["--self-test-vectors", "unexpected-positional"],
    ):
        hostile = run_checker_source(
            checker_source,
            runtime_request,
            checker_arguments=tuple(hostile_arguments),
        )
        require(
            hostile.returncode == 2 and hostile.stdout == b"" and hostile.stderr,
            "checker argument inventory admitted a non-exact private route: "
            + repr(hostile_arguments),
        )
    noncanonical = json.dumps(
        vector("runtime_mode", {"optimize": sys.flags.optimize}),
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    malformed = run_checker_source(
        checker_source,
        noncanonical,
    )
    require(
        malformed.returncode == 2
        and malformed.stdout == b""
        and malformed.stderr.startswith(
            b"certified SxPID2 self-test vector protocol failed:"
        ),
        "checker accepted noncanonical private-protocol JSON",
    )
    huge_integer = invoke_checker(
        checker_source, vector("strict_json", {"raw": "9" * 5_000})
    )
    require(
        huge_integer.returncode == 1
        and huge_integer.stderr == b""
        and len(huge_integer.stdout) <= 1_024
        and b"Traceback" not in huge_integer.stdout,
        "5000-digit JSON integer did not produce a bounded canonical failure",
    )
    huge_response = exact_mapping(
        parse_canonical_json(huge_integer.stdout, "huge-integer failure response"),
        {"error", "result"},
        "huge-integer failure response",
    )
    require(
        huge_response["result"] == "fail"
        and isinstance(huge_response["error"], str)
        and "invalid strict JSON" in huge_response["error"]
        and "9" * 100 not in huge_response["error"],
        "5000-digit JSON integer failure was unbounded or noncanonical",
    )
    validate_adjacent_unchecked_hash_pyc_nonexecution(runtime_request)
    return EXPECTED_NEW_HUGE_INTEGER_MUTATIONS


def main() -> int:
    checker_source = stable_source(CHECKER)
    source_mutation_count = validate_static_cli_custody(checker_source)
    huge_integer_mutation_count = validate_cli_controls(checker_source)
    baseline = read_snapshot(checker_source)
    structural = invoke_checker(
        checker_source, vector("validate_structural_baseline", {})
    )
    require(
        structural.returncode == 0
        and structural.stdout == PASS_OUTPUT
        and structural.stderr == b"",
        "structural baseline was rejected before the three container pins froze: "
        + structural.stderr.decode("utf-8", errors="replace"),
    )
    mutations: list[tuple[str, Any, str]] = [
        (
            "producer-report-schema-downgrade",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/src/report.rs",
                REPORT_SCHEMA,
                "pid-rs/certified-sxpid-report/v1",
            ),
            "report schema missing",
        ),
        (
            "verifier-schema-downgrade",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/verify_certificate.py",
                VERIFICATION_SCHEMA,
                "pid-rs/certified-sxpid-independent-verification/v1",
            ),
            "verification schema missing",
        ),
        (
            "producer-manifest-omits-product",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/src/lib.rs",
                '("src/product.rs", include_bytes!("product.rs")),',
                "",
            ),
            "producer source manifest missing",
        ),
        (
            "erase-v1-readjudication-trigger",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md",
                "Revision 1 must be re-adjudicated",
                "Revision 1 may be reused",
            ),
            "historical trigger missing",
        ),
        (
            "broaden-v2-product-premise",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                "exact-product record has status `compared`",
                "exact-product record is present",
            ),
            "claim product premise missing",
        ),
        (
            "erase-v2-abstention",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                "no exact-product zero/sign claim is available",
                "a sign may be inferred",
            ),
            "claim abstention boundary missing",
        ),
        (
            "downgrade-v3-claim-schema",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                VERIFICATION_SCHEMA,
                VERIFICATION_SCHEMA_V2,
            ),
            "revision-3 verification schema missing",
        ),
        (
            "erase-v3-cache-normalization-boundary",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                "not a portable semantic hash",
                "portable identity",
            ),
            "digest portability exclusion missing",
        ),
        (
            "erase-v3-cache-control",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_loaded_execution_cache_stability",
                "def check_loaded_execution_cache",
            ),
            "cache-stability control missing",
        ),
        (
            "erase-v3-live-code-control",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_post_import_execution_mutation",
                "def check_post_import_execution",
            ),
            "live-code mutation control missing",
        ),
        (
            "erase-v3-semantic-constant-controls",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_post_import_semantic_constant_mutations",
                "def check_post_import_constant_mutations",
            ),
            "semantic-constant mutation controls missing",
        ),
        (
            "erase-v3-normalization-source-mutant",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_cache_normalization_source_mutation",
                "def check_cache_normalization_mutation",
            ),
            "cache-normalization source-mutation control missing",
        ),
        (
            "erase-v3-index-row",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
                "| 3 |",
                "| three |",
            ),
            "revision-3 index row missing",
        ),
        (
            "forge-v3-verifier-source-binding",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                baseline.sha256[
                    "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                ],
                "0" * 64,
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "swap-v3-source-digest-assignments",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: (
                    text.replace(
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                        ],
                        "__VERIFIER_DIGEST__",
                        1,
                    )
                    .replace(
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                        ],
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                        ],
                        1,
                    )
                    .replace(
                        "__VERIFIER_DIGEST__",
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                        ],
                        1,
                    )
                ),
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "move-v3-source-digest-from-row-to-prose",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: (
                    text.replace(
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                        ],
                        "0" * 64,
                        1,
                    )
                    + "\nRetained token: "
                    + baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ]
                    + "\n"
                ),
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "duplicate-v3-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    1,
                ),
            ),
            "revision-3 verifier source digest must have exactly one table row",
        ),
        (
            "hide-v3-source-binding-row-in-html-comment",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "<!--\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "-->"
                    ),
                    1,
                ),
            ),
            "HTML comments are forbidden in structured Markdown authority",
        ),
        (
            "hide-v3-source-binding-row-in-fenced-block",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "```text\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "```"
                    ),
                    1,
                ),
            ),
            "revision-3 verifier source digest must have exactly one table row",
        ),
        (
            "duplicate-v3-source-binding-without-outer-pipes",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: (
                    text
                    + "\n`audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                    + "| `"
                    + baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                    ]
                    + "`\n"
                ),
            ),
            "noncanonical pipe-table row in structured Markdown authority",
        ),
        (
            "swap-incident-candidate-source-digests",
            transformed_text(
                baseline,
                INCIDENT_PATH,
                lambda text: (
                    text.replace(
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                        ],
                        "__INCIDENT_VERIFIER_DIGEST__",
                        1,
                    )
                    .replace(
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                        ],
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                        ],
                        1,
                    )
                    .replace(
                        "__INCIDENT_VERIFIER_DIGEST__",
                        baseline.sha256[
                            "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                        ],
                        1,
                    )
                ),
            ),
            "incident candidate verifier digest table row differs",
        ),
        (
            "promote-portable-digest-to-supported",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
                (
                    "| Digests are portable semantic hashes across runtimes. "
                    "| No evidence; explicitly excluded | Unsupported "
                    "| Runtime implementation/version and marshal format can matter |"
                ),
                (
                    "| Digests are portable semantic hashes across runtimes. "
                    "| No evidence; explicitly excluded | Supported "
                    "| Runtime implementation/version and marshal format can matter |"
                ),
            ),
            "unsupported digest claim table row differs",
        ),
        (
            "duplicate-contradictory-portable-digest-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
                lambda text: (
                    text + "\n| Digests are portable semantic hashes across runtimes. "
                    "| Claimed without evidence | Supported | Contradiction |\n"
                ),
            ),
            "unsupported digest claim must have exactly one table row",
        ),
        (
            "move-green-run-wording-under-supported",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "- “the observed CI run was green”; or\n",
                    "",
                    1,
                ).replace(
                    "## Why the verifier revision is justified",
                    "The observed CI run was green.\n\n"
                    "## Why the verifier revision is justified",
                    1,
                ),
            ),
            "prohibited green-run wording missing",
        ),
        (
            "hide-supported-section-boundary-in-html-comment",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "<!--\n"
                        "## Why the verifier revision is justified\n"
                        "-->\n"
                        "The observed CI run was green.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "HTML comments are forbidden in structured Markdown authority",
        ),
        (
            "hide-supported-section-boundary-in-fenced-block",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "```text\n"
                        "## Why the verifier revision is justified\n"
                        "```\n"
                        "The observed CI run was green.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "prohibited green-run wording entered the supported section",
        ),
        (
            "duplicate-equivalent-supported-heading",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: (
                    text
                    + "\n## Supported wording ##\n"
                    + "The observed CI run was green.\n"
                ),
            ),
            "expected one '## Supported wording' section",
        ),
        (
            "portable-hash-wording-entered-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "The loaded-execution digest is a portable semantic hash.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "prohibited wording entered the supported section",
        ),
        (
            "erase-retained-ci-runtime",
            mutated_text(
                baseline,
                INCIDENT_PATH,
                "used CPython 3.11.15 on",
                "unspecified Python",
            ),
            "incident runtime missing",
        ),
        (
            "forge-retained-ci-log-digest",
            mutated_text(
                baseline,
                INCIDENT_PATH,
                INCIDENT_LOG_SHA256,
                "0" * 64,
            ),
            "incident retrieved-log digest missing",
        ),
        (
            "promote-lean-witness-to-end-to-end-refinement",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
                "the retained five-factor rational identity; exact-rational and Rust routes separately bind that",
                "Lean alone binds",
            ),
            "revision-2 formal non-refinement boundary missing",
        ),
        (
            "remove-product-source-from-catalog",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog)["source_files"].remove(
                    "audit/tools/certified-sxpid/src/product.rs"
                ),
            ),
            "catalog omits revision-3 source/evidence",
        ),
        (
            "remove-v3-incident-from-catalog",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog)["source_files"].remove(INCIDENT_PATH),
            ),
            "catalog omits revision-3 source/evidence",
        ),
        (
            "invent-scientific-novelty",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {"scientific_novelty_claim": "new exact PID"}
                ),
            ),
            "acquired a scientific novelty claim",
        ),
        (
            "catalog-summary-universal-overclaim",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {
                        "summary": method(catalog)["summary"]
                        + " This universally proves all PID atoms nonnegative "
                        "and formally verifies pid-rs."
                    }
                ),
            ),
            "certifier catalog method exact reviewed projection changed",
        ),
        (
            "catalog-new-in-scientific-novelty-overclaim",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {
                        "new_in_pid_rs": method(catalog)["new_in_pid_rs"]
                        + " This is a scientifically novel universal PID theorem."
                    }
                ),
            ),
            "certifier catalog method exact reviewed projection changed",
        ),
        (
            "catalog-method-nonfinite-json-number",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {"nonfinite": {"__pid_rs_self_test_nonfinite__": "NaN"}}
                ),
            ),
            "certifier catalog method cannot be canonically projected",
        ),
        (
            "qualification-count-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value["checks"].update({"expression_products": 11_855}),
            ),
            "qualification product count drifted",
        ),
        (
            "mutation-subtotals-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update({"total_adversaries": 22}),
            ),
            "adversary count drifted",
        ),
        (
            "mutation-breakdown-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update({"certificate_mutations_killed": 10}),
            ),
            "certificate-mutation count drifted",
        ),
        (
            "preflight-before-powering-control-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"preflight_before_powering_controls_passed": 1}
                ),
            ),
            "preflight-before-powering control count drifted",
        ),
        (
            "boundary-evidence-projection-control-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"boundary_evidence_projection_controls_passed": 50}
                ),
            ),
            "boundary-evidence projection control count drifted",
        ),
        (
            "boundary-receipt-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"boundary_receipt_scalar_leaf_mutations_checked": 275}
                ),
            ),
            "boundary-receipt scalar-leaf projection partition drifted",
        ),
        (
            "certificate-replay-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"certificate_replay_retained_leaf_changes_detected": 955}
                ),
            ),
            "certificate-replay scalar-leaf projection partition drifted",
        ),
        (
            "boundary-replay-process-status-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value.update({"status": "failed"}),
            ),
            "boundary-replay process is not passed",
        ),
        (
            "boundary-replay-exhaustive-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"][
                    "exhaustive_scalar_leaf_partition"
                ].update({"total_scalar_leaf_mutations_checked": 1_235}),
            ),
            "boundary-replay exhaustive scalar-leaf partition drifted",
        ),
        (
            "boundary-replay-process-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["bindings"].update(
                    {"boundary_script_sha256": "0" * 64}
                ),
            ),
            "boundary-replay process binding boundary_script_sha256",
        ),
        (
            "boundary-replay-complete-binding-inventory-erased",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"]["binding_inventory"].pop(),
            ),
            "boundary-replay complete binding inventory drifted",
        ),
        (
            "boundary-replay-outer-exclusion-broadened",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"]["dynamic_replay_bindings"].append(
                    "exact_product_source_sha256"
                ),
            ),
            "boundary-replay dynamic outer-binding inventory drifted",
        ),
        (
            "boundary-replay-inner-exclusion-erased",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"][
                    "certificate_projection_excluded_paths"
                ].pop(),
            ),
            "boundary-replay certificate exclusion inventory drifted",
        ),
        (
            "boundary-replay-ordinary-mode-made-writing",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"].update(
                    {"ordinary_mode": "write_tracked_evidence"}
                ),
            ),
            "boundary-replay ordinary mode drifted",
        ),
        (
            "boundary-replay-update-mode-made-implicit",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"].update(
                    {"update_mode": "ordinary_execution"}
                ),
            ),
            "boundary-replay update mode drifted",
        ),
        (
            "boundary-replay-platform-boundary-overstated",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"].replace(
                            "No second operating system or architecture was executed",
                            "Every operating system and architecture was executed",
                        )
                    }
                ),
            ),
            "boundary-replay claim boundary omits",
        ),
        (
            "boundary-replay-platform-execution-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"cross_platform_execution_performed": True}
                ),
            ),
            "boundary-replay platform-execution boundary drifted",
        ),
        (
            "boundary-replay-current-live-retention-overstated",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"current_live_receipt_retention": "full_external_custody"}
                ),
            ),
            "boundary-replay current-live retention boundary drifted",
        ),
        (
            "boundary-replay-historical-stdout-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"historical_refresh_stdout_sha256": "0" * 64}
                ),
            ),
            "boundary-replay historical stdout/evidence binding drifted",
        ),
        (
            "boundary-replay-historical-certificate-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["failure"].update(
                    {"historical_certificate_sha256": "0" * 64}
                ),
            ),
            "boundary-replay historical execution bindings drifted",
        ),
        (
            "qualification-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value["bindings"].update(
                    {"exact_product_source_sha256": "0" * 64}
                ),
            ),
            "qualification binding exact_product_source_sha256",
        ),
        (
            "mutation-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value["bindings"].update(
                    {"self_test_source_sha256": "0" * 64}
                ),
            ),
            "mutation evidence self-test source binding drifted",
        ),
        (
            "boundary-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value["bindings"].update(
                    {"boundary_script_sha256": "0" * 64}
                ),
            ),
            "boundary evidence script binding drifted",
        ),
        (
            "evolutionary-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value["bindings"].update(
                    {"challenge_source_sha256": "0" * 64}
                ),
            ),
            "evolutionary evidence script binding drifted",
        ),
        (
            "counterexample-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value["findings"]["minimized_witness"].update(
                    {"interval_decision": "certified_exact_zero"}
                ),
            ),
            "counterexample interval boundary drifted",
        ),
        (
            "lean-boundary-broadened",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update(
                    {"boundary": "Complete certifier verification."}
                ),
            ),
            "Lean boundary broadened",
        ),
        (
            "lean-theorem-count-erased",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update({"theorems_kernel_checked": 6}),
            ),
            "Lean theorem count drifted",
        ),
        (
            "current-lean-boundary-broadened",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
                lambda value: value.update(
                    {"boundary": "Complete certifier verification."}
                ),
            ),
            "Lean boundary broadened",
        ),
        (
            "current-lean-theorem-count-erased",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
                lambda value: value.update({"theorems_kernel_checked": 6}),
            ),
            "Lean theorem count drifted",
        ),
        (
            "current-lean-checker-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json",
                lambda value: value.update({"checker_source_sha256": "0" * 64}),
            ),
            "current Lean 4.33 evidence checker/toolchain binding drifted",
        ),
        (
            "evolutionary-search-promoted-to-proof",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value.update({"negative_boundary": "Universal theorem."}),
            ),
            "evolutionary negative boundary broadened",
        ),
        (
            "qualification-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"]
                        + " This end-to-end formally verifies pid-rs and proves "
                        "universal SxPID nonnegativity."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "nonsyntactic-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"]
                        + " This is also a universal population theorem."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "evolutionary-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value.update(
                    {
                        "negative_boundary": value["negative_boundary"]
                        + " Nevertheless it is a universal nonnegativity proof "
                        "and validates all PID definitions."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "lean-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update(
                    {
                        "boundary": value["boundary"]
                        + " This formally verifies the complete SxPID2 certifier "
                        "and Python runtime."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "mutation-evidence-injected-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {
                        "claim_boundary": (
                            "End-to-end formal verification of all PID software "
                            "and mathematics."
                        )
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "just-gate-removed",
            mutated_text(
                baseline,
                "justfile",
                "python3 scripts/check-lean-exact-log-product.py",
                "true # removed",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "workflow-boundary-gate-writes-historical-evidence",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                (
                    "      - run: python3 "
                    "audit/tools/certified-sxpid/scripts/"
                    "check-nonsyntactic-zero-boundary.py"
                ),
                (
                    "      - run: python3 "
                    "audit/tools/certified-sxpid/scripts/"
                    "check-nonsyntactic-zero-boundary.py --update-evidence"
                ),
            ),
            "ordinary gate container must not update historical evidence",
        ),
        (
            "just-gate-moved-to-unused-recipe",
            transformed_text(
                mutated_text(
                    baseline,
                    "justfile",
                    (
                        "    python3 scripts/check-lean-exact-log-product.py\n"
                        "    python3 -I -S -B scripts/check-certified-sxpid2-claim.py\n"
                        "    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py\n"
                        "    python3 -I -S -B "
                        "scripts/check-certified-sxpid2-claim-self-test.py\n"
                    ),
                    (
                        "    python3 scripts/check-lean-exact-log-product.py\n"
                        "    true # claim gate removed\n"
                        "    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py\n"
                        "    python3 -I -S -B "
                        "scripts/check-certified-sxpid2-claim-self-test.py\n"
                    ),
                ),
                "justfile",
                lambda text: text
                + "\nunused-retained-claim-gate:\n"
                + "    python3 -I -S -B scripts/check-certified-sxpid2-claim.py\n",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "release-audit-certified-sxpid-dependency-removed",
            mutated_text(
                baseline,
                "justfile",
                (
                    " formal-finite-convergence lean-toolchain-freeze "
                    "ksg-composite-v5 certified-sxpid citation-edge-countermodel "
                ),
                (
                    " formal-finite-convergence lean-toolchain-freeze "
                    "ksg-composite-v5 citation-edge-countermodel "
                ),
            ),
            "revision-3 release-audit dependency missing",
        ),
        (
            "release-audit-line-framing-changed-with-membership-preserved",
            mutated_text(
                baseline,
                "justfile",
                (
                    "lean-toolchain-freeze ksg-composite-v5 certified-sxpid "
                    "citation-edge-countermodel formal-pdfs"
                ),
                (
                    "lean-toolchain-freeze ksg-composite-v5  certified-sxpid "
                    "citation-edge-countermodel formal-pdfs"
                ),
            ),
            "release-audit just dependency line exact digest changed",
        ),
        (
            "ci-gate-removed",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
                "true # removed",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-commented-but-token-retained",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                "      # - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-moved-into-block-scalar",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                (
                    "    retained_gate_text: |\n"
                    "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-moved-into-explicit-indent-block-scalar",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                (
                    "  retained_gate_text: |4\n"
                    "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-disabled-by-step-condition",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                (
                    "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py\n"
                    "        if: ${{ false }}"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "invalid-commonmark-fence-cannot-hide-supported-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: (
                    text
                    + "\n```not-a-fence`\n"
                    + "## Supported wording\n"
                    + "the observed CI run was green\n"
                    + "```\n"
                ),
            ),
            "unclosed fenced block in structured Markdown authority",
        ),
        (
            "setext-heading-cannot-duplicate-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: (
                    text
                    + "\nSupported wording\n"
                    + "--\n"
                    + "the observed CI run was green\n"
                ),
            ),
            "setext/horizontal headings are forbidden",
        ),
        (
            "markdown-emphasis-cannot-split-supported-overclaim",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                "## Why the verifier revision is justified",
                (
                    "The loaded-execution digest is a portable "
                    "**semantic hash**.\n\n"
                    "## Why the verifier revision is justified"
                ),
            ),
            "prohibited wording entered the supported section",
        ),
        (
            "raw-html-block-cannot-hide-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        '<script type="text/plain">\n'
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "</script>"
                    ),
                    1,
                ),
            ),
            "raw HTML is forbidden in structured Markdown authority",
        ),
        (
            "linked-label-cannot-hide-contradictory-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| [`audit/tools/certified-sxpid/scripts/verify_certificate.py`]"
                        "(../../audit/tools/certified-sxpid/scripts/verify_certificate.py) "
                        "| `0000000000000000000000000000000000000000000000000000000000000000` |"
                    ),
                    1,
                ),
            ),
            "linked pipe-table cells are forbidden",
        ),
        (
            "workflow-job-level-false-condition",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "  certified-sxpid-msrv:",
                "    if: ${{ false }}\n\n  certified-sxpid-msrv:",
            ),
            "certified-sxpid-reference workflow job exact digest changed",
        ),
        (
            "workflow-command-hidden-in-multiline-name",
            transformed_text(
                baseline,
                ".github/workflows/ci.yml",
                lambda text: text.replace(
                    "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                    "",
                    1,
                ).replace(
                    "    name: Exact-count directed-rounding SxPID2 reference",
                    (
                        '    name: "Exact-count directed-rounding SxPID2 reference\n'
                        "      - run: python3 -I -S -B scripts/check-certified-sxpid2-claim.py\n"
                        '      "'
                    ),
                    1,
                ),
            ),
            "certified-sxpid-reference workflow job exact digest changed",
        ),
        (
            "just-shebang-exits-before-gates",
            mutated_text(
                baseline,
                "justfile",
                "certified-sxpid:\n",
                "certified-sxpid:\n    #!/bin/sh\n    exit 0\n",
            ),
            "certified-sxpid just recipe exact digest changed",
        ),
        (
            "workflow-jobs-container-disabled",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "\njobs:\n",
                "\ndisabled_jobs:\n",
            ),
            "reviewed revision-3 execution container digest changed",
        ),
        (
            "just-global-shell-replaced-by-true",
            transformed_text(
                baseline,
                "justfile",
                lambda text: 'set shell := ["true"]\n\n' + text,
            ),
            "reviewed revision-3 execution container digest changed",
        ),
        (
            "html-entity-cannot-split-supported-overclaim",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                "## Why the verifier revision is justified",
                (
                    "The loaded-execution digest is a portable semantic "
                    "h&#97;sh.\n\n"
                    "## Why the verifier revision is justified"
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "emphasized-heading-cannot-duplicate-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: (
                    text
                    + "\n## Supported **wording**\n\n"
                    + "the observed CI run was green\n"
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "equivalent-code-span-cannot-hide-duplicate-source-binding",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| `` audit/tools/certified-sxpid/scripts/verify_certificate.py `` "
                        "| `0000000000000000000000000000000000000000000000000000000000000000` |"
                    ),
                    1,
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "token-retained-in-comment-cannot-reverse-claim-boundary",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                lambda text: (
                    text.replace(
                        "not a portable semantic hash",
                        "is a portable semantic hash",
                        1,
                    )
                    + "\n<!-- retained checker token: not a portable semantic hash -->\n"
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "multiline-raw-html-cannot-hide-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "<script\n"
                        'type="text/plain"\n'
                        ">\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "</script\n"
                        ">"
                    ),
                    1,
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "crlf-authority-byte-drift",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                lambda text: text.replace("\n", "\r\n"),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "historical-revision1-claim-rewrite",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v1.md",
                lambda _text: (
                    "# Claim revision 1\n\n"
                    "Revision 1 unconditionally proves every PID implementation correct.\n"
                ),
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-decision-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
                lambda text: (
                    text
                    + "\n## Superseding statement\n\n"
                    + "Revision 2 is unconditional formal verification and release authority.\n"
                ),
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-scope-expansion",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                lambda text: (
                    text
                    + "\n## Expanded scope\n\n"
                    + "Revision 2 certifies continuous PID and all downstream applications.\n"
                ),
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-evidence-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
                lambda text: (
                    text
                    + "\n| End-to-end formal verification | Assumed | Supported | Unbounded |\n"
                ),
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "certifier-readme-formal-verification-overclaim",
            transformed_text(
                baseline,
                "audit/tools/certified-sxpid/README.md",
                lambda text: (
                    text
                    + "\nThe verifier is formally verified and all SxPID atoms "
                    + "have a proved sign.\n"
                ),
            ),
            "immutable reviewed certified-SxPID documentation digest changed",
        ),
        (
            "scripts-readme-formal-verification-overclaim",
            transformed_text(
                baseline,
                "scripts/README.md",
                lambda text: (
                    text
                    + "\nThe certified SxPID2 verifier is end-to-end formally verified.\n"
                ),
            ),
            "immutable reviewed certified-SxPID documentation digest changed",
        ),
        (
            "formal-pdf-set-early-exit",
            mutated_text(
                baseline,
                "scripts/check-formal-pdf-set.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed certified-SxPID support-gate digest changed",
        ),
        (
            "certified-assurance-pdf-leaf-early-exit",
            mutated_text(
                baseline,
                "scripts/check-certified-sxpid2-assurance-pdf.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-pdf-leaf-early-exit",
            mutated_text(
                baseline,
                "scripts/check-exact-log-product-sxpid2-pdf.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-policy-checker-early-exit",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-static-policy.py",
                "#!/usr/bin/env python3\n",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-policy-self-test-early-exit",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py",
                "#!/usr/bin/env python3\n",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-deny-policy-weakened",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/deny.toml",
                'multiple-versions = "deny"',
                'multiple-versions = "allow"',
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "certified-assurance-tex-overclaim",
            transformed_text(
                baseline,
                "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
                lambda text: (
                    text + "\n% Contradictory mutant: end-to-end formal verification.\n"
                ),
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-assurance-tex-overclaim",
            transformed_text(
                baseline,
                "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
                lambda text: (
                    text + "\n% Contradictory mutant: universal population theorem.\n"
                ),
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-tex-stale-current-lean",
            mutated_text(
                baseline,
                "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
                "current pinned Lean 4.33.0 project",
                "current pinned Lean 4.32.0 project",
            ),
            "exact-log current/historical Lean boundary missing",
        ),
        (
            "exact-product-tex-current-evidence-erased",
            mutated_text(
                baseline,
                "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
                "The current execution receipt is the versioned\n"
                "\\texttt{sxpid2-exact-product-lean-check-4.33.0.json}.",
                "The current execution receipt is the versioned\n"
                "\\texttt{sxpid2-exact-product-lean-check.json}.",
            ),
            "exact-log current/historical Lean boundary missing",
        ),
        (
            "exact-product-assurance-markdown-overclaim",
            transformed_text(
                baseline,
                "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
                lambda text: (
                    text
                    + "\nThis formally verifies all PID software and mathematics.\n"
                ),
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "formal-paper-inventory-removed",
            mutated_text(
                baseline,
                "scripts/check-formal-pdf-set.sh",
                '"exact-log-product-sxpid2-assurance"',
                '"unregistered-exact-product-paper"',
            ),
            "formal PDF inventory missing",
        ),
    ]

    require(
        len(mutations) == EXPECTED_SNAPSHOT_MUTATIONS,
        "certified-SxPID2 snapshot-mutation count drifted",
    )
    for name, snapshot, expected in mutations:
        expect_failure(checker_source, name, snapshot, expected, baseline)
    total = len(mutations) + source_mutation_count + huge_integer_mutation_count
    require(
        total
        == EXPECTED_SNAPSHOT_MUTATIONS
        + EXPECTED_NEW_SOURCE_MUTATIONS
        + EXPECTED_NEW_HUGE_INTEGER_MUTATIONS,
        "certified-SxPID2 total mutation count drifted",
    )
    print(f"OK: {total} certified-SxPID2 revision mutations were rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
