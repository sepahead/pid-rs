#!/usr/bin/env python3
"""CLI-only hostile tests for the KSG M1a custody-correction checker."""

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
        "ERROR: check-ksg-m1a-custody-correction-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
import copy
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
CHECKER = ROOT / "scripts/check-ksg-m1a-custody-correction.py"
POLICY = ROOT / "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json"
SCHEMA = ROOT / "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json"
BOUNDARY = (
    ROOT / "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md"
)
NEGATIVE = ROOT / "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
IMPLEMENTATION = "cb3f58f0b190454cb3f1090de8798261ec78f194"
IMPLEMENTATION_TREE = "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0"
FIXTURE_CORRECTION_MESSAGE = (
    "Correct KSG M1a hosted custody wiring\n\n"
    f"Sealed-index-SHA256: {'7' * 64}\n"
    "Sealed-index-Size: 32768\n"
)
BOOLEAN_FIELD_NAMES = (
    "all_green_applies_only_to_correction_head",
    "all_jobs_successful",
    "authentication_claimed",
    "author_and_committer_headers_identical",
    "bounded_private_cli_protocol_exact",
    "candidate_equals_anchor",
    "candidate_tree_matches_checkpoint",
    "causation_claimed",
    "checkpoint_became_correction_commit",
    "cli_only_selftest_transport",
    "correction_heads_equal",
    "correction_subject_must_not_contain_receipt",
    "correction_subject_must_not_contain_retained_index",
    "correction_tree_excludes_receipt",
    "correction_tree_excludes_retained_index",
    "credit_permitted",
    "decision_v4_absent_at_correction",
    "deletions_permitted",
    "distinct_from_implementation_anchor",
    "evidence_matrix_v4_absent_at_correction",
    "final_decision_absent",
    "final_evidence_matrix_absent",
    "future_composite_receipt_absent",
    "head_equals_correction_commit",
    "head_tree_equals_correction_tree",
    "implementation_and_correction_heads_distinct",
    "implementation_heads_equal",
    "implementation_subject_must_not_contain_receipt",
    "implementation_subject_must_not_contain_retained_index",
    "implementation_tree_excludes_receipt",
    "implementation_tree_excludes_retained_index",
    "independently_recorded_before_ref_update",
    "input_descriptor_read_only",
    "later_descendant_required",
    "lifecycle_validation_permitted",
    "mechanical_resealing_permitted",
    "no_new_alerts_observed",
    "one_parent",
    "pagination_complete",
    "pair_normalized_equal",
    "path_or_residency_claimed",
    "precommit_descriptor_observation_authenticated",
    "receipt_claims_its_own_commit",
    "receipt_hashes_itself",
    "receipt_subjects_preexist_receipt",
    "remains_implementation_after_correction",
    "repeated_observations_equal",
    "repetitions_equal",
    "retained_index_commit_message_trailer_required",
    "retained_negative_evidence",
    "runner_authenticity_claimed",
    "scientific_authority_unchanged",
    "signature_headers_permitted",
    "single_link",
    "three_container_digest_rebind_exact",
    "trusted_time_claimed",
    "truncated",
    "unsigned",
)
CORRECTION_COMMIT = "1111111111111111111111111111111111111111"
CORRECTION_TREE = "2222222222222222222222222222222222222222"
JOB_PROJECTION_ENCODING = (
    "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with "
    "number-sorted steps"
)
ANALYSIS_PROJECTION_ENCODING = (
    "canonical compact sorted-key ASCII JSON plus LF over language-sorted analysis rows"
)
COMPOSITE_NONIMPLICATIONS = [
    "This composite receipt is bounded lifecycle custody for an exact M1a implementation "
    "anchor and its exact direct-child custody correction; it is not scientific, formal, "
    "estimator, PID, calibration, support, application, package, release, or identity evidence.",
    "The correction does not change the implementation identity cb3f58f0 or the protected "
    "83-path projection and does not turn revision 4 into an integration decision.",
    "Commit, tree, blob, SHA-256, remote, run, job, and artifact identifiers bind named "
    "observations but do not establish authenticity, authorship, trusted time, "
    "transparency-log inclusion, or repository origin.",
    "The KSG runtime witnesses remain fixed-input implementation correspondence only; they "
    "do not establish general neighbor-search correctness, estimator consistency, population "
    "support, or transfer to continuous PID, categorical SxPID, I_min, PID3, wrappers, or consumers.",
    "The receipt is absent from both subject trees and cannot attest its own bytes or "
    "containing descendant commit.",
]
SELF_TEST_SCHEMA = "pid-rs/ksg-rev4-m1a-custody-correction-self-test-vector/v1"
PASS = b'{"result":"pass"}\n'
FAIL = b'{"result":"fail"}\n'
EXPECTED_FIXED_GIT_CONFIG = [
    "core.attributesFile=/dev/null",
    "core.fsmonitor=false",
    "core.hooksPath=/dev/null",
    "core.ignoreCase=false",
    "core.untrackedCache=false",
    "diff.external=",
]
EXPECTED_OPTIONS = {
    "--allow-provisional-diagnostic",
    "--alternate-index-entry-count",
    "--alternate-index-sha256",
    "--checkpoint-commit",
    "--emit-observed-delta",
    "--expected-candidate-tree",
    "--mode",
    "--self-test-sealed-index",
    "--self-test-vectors",
    "--validate-policy-only",
    "--validate-composite-receipt",
}
PYC_MAGIC_BY_MINOR = {
    (3, 11): bytes.fromhex("a70d0d0a"),
    (3, 12): bytes.fromhex("cb0d0d0a"),
    (3, 13): bytes.fromhex("f30d0d0a"),
    (3, 14): bytes.fromhex("2b0e0d0a"),
}
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_REQUEST_BYTES = 8 * 1024 * 1024
CHECKER_STDIN_BOOTSTRAP = """\
import hashlib
import os
import stat
import sys
import tempfile

_PREFIX = "custody-correction checker stdin launcher failed: "
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
if _logical_file != os.path.join(_logical_root, "scripts", "check-ksg-m1a-custody-correction.py"):
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
_temp_link = "/tmp"
_temp_root = os.path.realpath(_temp_link)
_temp_state = os.lstat(_temp_root)
if not (os.path.isabs(_temp_root) and stat.S_ISDIR(_temp_state.st_mode) and _temp_state.st_uid == 0 and bool(_temp_state.st_mode & stat.S_ISVTX)):
    _fail("fixed temporary root custody differs")
_input_dir = tempfile.TemporaryDirectory(prefix="pid-rs-correction-stdin-", dir=_temp_root)
os.chmod(_input_dir.name, 0o700)
_input_path = os.path.join(_input_dir.name, "request")
_write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
_write_fd = os.open(_input_path, _write_flags, 0o600)
_offset = 0
while _offset < len(_request):
    _written = os.write(_write_fd, _request[_offset:])
    if _written <= 0:
        _fail("request staging write was short")
    _offset += _written
os.fsync(_write_fd)
os.close(_write_fd)
os.chmod(_input_path, 0o400)
_read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
_input_fd = os.open(_input_path, _read_flags)
_input_state = os.fstat(_input_fd)
if not (stat.S_ISREG(_input_state.st_mode) and stat.S_IMODE(_input_state.st_mode) == 0o400 and _input_state.st_nlink == 1 and _input_state.st_size == len(_request)):
    _fail("staged request descriptor custody differs")
_staged = b""
_remaining = len(_request)
while _remaining:
    _chunk = os.read(_input_fd, min(_remaining, 65536))
    if not _chunk:
        _fail("staged request is short")
    _staged += _chunk
    _remaining -= len(_chunk)
if _staged != _request or os.read(_input_fd, 1) != b"":
    _fail("staged request bytes differ")
os.lseek(_input_fd, 0, os.SEEK_SET)
os.dup2(_input_fd, 0)
if _input_fd != 0:
    os.close(_input_fd)
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
EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE_BYTES = 4296
EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256 = (
    "bd83081c2f7fa13401dcc7d07b3560787f5a1864421c61eac467adc4afde673a"
)
_CHECKER_SOURCE_SNAPSHOT: bytes | None = None


class SelfTestError(RuntimeError):
    """The hostile suite observed an unexpected result."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def canonical_json(value: Any, *, pretty: bool) -> bytes:
    rendered = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
        allow_nan=False,
    )
    return (rendered + "\n").encode("ascii")


def strict_json(path: Path) -> Any:
    pairs_seen: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"duplicate key in fixture: {key}")
            result[key] = value
            pairs_seen.append(key)
        return result

    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=hook)
    require(
        raw == canonical_json(value, pretty=True), f"fixture is not canonical: {path}"
    )
    require(bool(pairs_seen), f"fixture did not contain JSON object keys: {path}")
    return value


def stable_source_snapshot(path: Path) -> tuple[bytes, tuple[int, ...]]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        path_before = path.lstat()
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= MAX_SOURCE_BYTES,
            f"source custody invalid: {path}",
        )
        require(
            (path_before.st_dev, path_before.st_ino) == (before.st_dev, before.st_ino),
            f"source path/descriptor identity differs: {path}",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            require(bool(chunk), f"source descriptor ended early: {path}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"source descriptor grew: {path}")
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
    return b"".join(chunks), identity(after)


def stable_source(path: Path) -> bytes:
    return stable_source_snapshot(path)[0]


def validate_checker_stdin_bootstrap() -> None:
    raw = CHECKER_STDIN_BOOTSTRAP.encode("utf-8")
    require(
        len(raw) == EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256,
        "checker stdin bootstrap reviewed bytes changed",
    )
    tree = ast.parse(CHECKER_STDIN_BOOTSTRAP, filename="<checker-stdin-bootstrap>")
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(
        {"compile", "exec"} <= calls
        and CHECKER_STDIN_BOOTSTRAP.count("exec(compile(") == 1
        and CHECKER_STDIN_BOOTSTRAP.count("os.dup2(_input_fd, 0)") == 1,
        "checker stdin bootstrap exact-source execution structure changed",
    )


def validate_static_cli_custody(checker_raw: bytes, self_test_raw: bytes) -> None:
    forbidden_imports = {"importlib", "runpy"}
    forbidden_calls = {"__import__", "compile", "eval", "exec"}
    forbidden_attributes = {
        "exec_module",
        "module_from_spec",
        "run_module",
        "run_path",
        "spec_from_file_location",
    }
    options: set[str] = set()
    abbreviations_disabled = False
    for path, raw in ((CHECKER, checker_raw), (SCRIPT, self_test_raw)):
        tree = ast.parse(raw.decode("utf-8", errors="strict"), filename=os.fspath(path))
        for node in ast.walk(tree):
            require(
                not isinstance(node, ast.Assert),
                f"optimization-sensitive assert in {path}",
            )
            if isinstance(node, ast.Import):
                require(
                    not {alias.name.partition(".")[0] for alias in node.names}
                    & forbidden_imports,
                    f"dynamic loader import in {path}",
                )
            elif isinstance(node, ast.ImportFrom):
                require(
                    (node.module or "").partition(".")[0] not in forbidden_imports,
                    f"dynamic loader import in {path}",
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    require(
                        node.func.id not in forbidden_calls,
                        f"dynamic source call in {path}",
                    )
                elif isinstance(node.func, ast.Attribute):
                    require(
                        node.func.attr not in forbidden_attributes,
                        f"dynamic loader call in {path}",
                    )
                    if path == CHECKER and node.func.attr == "ArgumentParser":
                        abbreviations_disabled = any(
                            keyword.arg == "allow_abbrev"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is False
                            for keyword in node.keywords
                        )
                    if (
                        path == CHECKER
                        and node.func.attr == "add_argument"
                        and node.args
                    ):
                        option = node.args[0]
                        if isinstance(option, ast.Constant) and isinstance(
                            option.value, str
                        ):
                            options.add(option.value)
    require(
        options == EXPECTED_OPTIONS,
        "checker CLI option inventory changed or acquired path CLI",
    )
    require(abbreviations_disabled, "checker CLI abbreviations are enabled")


def private_interpreter_directory_body(tree: ast.Module) -> list[ast.stmt]:
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run_candidate_source_python"
    ]
    require(len(functions) == 1, "private interpreter runner definition changed")
    contexts = [
        node
        for node in functions[0].body
        if isinstance(node, ast.With)
        and len(node.items) == 1
        and isinstance(node.items[0].context_expr, ast.Call)
        and isinstance(node.items[0].context_expr.func, ast.Attribute)
        and isinstance(node.items[0].context_expr.func.value, ast.Name)
        and node.items[0].context_expr.func.value.id == "tempfile"
        and node.items[0].context_expr.func.attr == "TemporaryDirectory"
        and isinstance(node.items[0].optional_vars, ast.Name)
        and node.items[0].optional_vars.id == "temporary"
    ]
    require(len(contexts) == 1, "private interpreter temporary context changed")
    return contexts[0].body


def assigned_call_index(
    body: list[ast.stmt], target: str, receiver: str | None, callee: str
) -> int:
    matches: list[int] = []
    for index, statement in enumerate(body):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == target
            and isinstance(statement.value, ast.Call)
        ):
            continue
        function = statement.value.func
        if receiver is None:
            matched = isinstance(function, ast.Name) and function.id == callee
        else:
            matched = (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == receiver
                and function.attr == callee
            )
        if matched:
            matches.append(index)
    require(len(matches) == 1, f"private interpreter {target} assignment changed")
    return matches[0]


def validate_private_directory_baseline_order(tree: ast.Module) -> None:
    body = private_interpreter_directory_body(tree)
    write_index = assigned_call_index(
        body, "private_state", None, "write_private_interpreter"
    )
    baseline_index = assigned_call_index(
        body, "temporary_state", "temporary_root", "lstat"
    )
    run_index = assigned_call_index(body, "completed", "subprocess", "run")
    require(
        baseline_index == write_index + 1 and run_index == baseline_index + 1,
        "private directory execution baseline is not post-materialization/pre-exec",
    )
    stores = [
        node
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
        and node.id == "temporary_state"
        and isinstance(node.ctx, ast.Store)
    ]
    loads_before_run = [
        node
        for statement in body[:run_index]
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
        and node.id == "temporary_state"
        and isinstance(node.ctx, ast.Load)
    ]
    loads_after_run = [
        node
        for statement in body[run_index + 1 :]
        for node in ast.walk(statement)
        if isinstance(node, ast.Name)
        and node.id == "temporary_state"
        and isinstance(node.ctx, ast.Load)
    ]
    require(
        len(stores) == 1 and not loads_before_run and len(loads_after_run) == 1,
        "private directory baseline store/load custody changed",
    )


def validate_private_directory_baseline_regression(checker_raw: bytes) -> None:
    tree = ast.parse(
        checker_raw.decode("utf-8", errors="strict"), filename=str(CHECKER)
    )
    validate_private_directory_baseline_order(tree)
    hostile = copy.deepcopy(tree)
    body = private_interpreter_directory_body(hostile)
    write_index = assigned_call_index(
        body, "private_state", None, "write_private_interpreter"
    )
    baseline_index = assigned_call_index(
        body, "temporary_state", "temporary_root", "lstat"
    )
    baseline = body.pop(baseline_index)
    body.insert(write_index, baseline)
    hostile_body = private_interpreter_directory_body(hostile)
    require(
        assigned_call_index(hostile_body, "temporary_state", "temporary_root", "lstat")
        < assigned_call_index(
            hostile_body, "private_state", None, "write_private_interpreter"
        )
        < assigned_call_index(hostile_body, "completed", "subprocess", "run"),
        "pre-write private-directory hostile was not constructed",
    )
    try:
        validate_private_directory_baseline_order(hostile)
    except SelfTestError:
        return
    raise SelfTestError("pre-write private-directory baseline mutation accepted")


def safe_environment() -> dict[str, str]:
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
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }


def invoke(
    arguments: list[str], *, stdin: bytes = b"", cwd: Path = ROOT
) -> subprocess.CompletedProcess[bytes]:
    require(cwd == ROOT, "fixed checker invocation root changed")
    checker_source = _CHECKER_SOURCE_SNAPSHOT
    require(checker_source is not None, "checker source snapshot is not initialized")
    require(len(stdin) <= MAX_REQUEST_BYTES, "checker request exceeds byte bound")
    completed = subprocess.run(
        [
            *PYTHON_CHILD_PREFIX,
            "-c",
            CHECKER_STDIN_BOOTSTRAP,
            os.fspath(CHECKER),
            os.fspath(ROOT),
            str(len(checker_source)),
            hashlib.sha256(checker_source).hexdigest(),
            str(len(stdin)),
            hashlib.sha256(stdin).hexdigest(),
            *arguments,
        ],
        cwd=cwd,
        env=safe_environment(),
        input=checker_source + stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    require(
        len(completed.stdout) <= 2 * 1024 * 1024
        and len(completed.stderr) <= 2 * 1024 * 1024,
        "checker output exceeded bound",
    )
    return completed


def vector(validator: str, payload: Any) -> bytes:
    return canonical_json(
        {"payload": payload, "schema": SELF_TEST_SCHEMA, "validator": validator},
        pretty=True,
    )


def accepted(validator: str, payload: Any) -> None:
    completed = invoke(["--self-test-vectors"], stdin=vector(validator, payload))
    require(
        completed.returncode == 0 and completed.stdout == PASS and not completed.stderr,
        f"accepted vector failed: {validator}: {completed.stderr!r}",
    )


def rejected(label: str, validator: str, payload: Any) -> None:
    completed = invoke(["--self-test-vectors"], stdin=vector(validator, payload))
    require(
        completed.returncode == 0 and completed.stdout == FAIL and not completed.stderr,
        f"hostile vector accepted or transport failed: {label}: {completed.stdout!r} {completed.stderr!r}",
    )


def malformed_rejected(label: str, raw: bytes) -> None:
    completed = invoke(["--self-test-vectors"], stdin=raw)
    require(
        completed.returncode == 0 and completed.stdout == FAIL and not completed.stderr,
        f"malformed vector was not safely rejected: {label}",
    )


def mutate(value: Any, operation: Callable[[Any], None]) -> Any:
    result = copy.deepcopy(value)
    operation(result)
    return result


def boolean_leaf_paths(value: Any) -> list[tuple[Any, ...]]:
    paths: list[tuple[Any, ...]] = []

    def visit(item: Any, path: tuple[Any, ...]) -> None:
        if type(item) is bool:
            paths.append(path)
        elif isinstance(item, dict):
            for key, child in item.items():
                visit(child, (*path, key))
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, (*path, index))

    visit(value, ())
    return paths


def replace_leaf(value: Any, path: tuple[Any, ...], replacement: Any) -> Any:
    result = copy.deepcopy(value)
    current = result
    for component in path[:-1]:
        current = current[component]
    current[path[-1]] = replacement
    return result


def reject_boolean_integer_aliases(validator: str, value: Any, label: str) -> None:
    paths = boolean_leaf_paths(value)
    require(bool(paths), f"{label} has no boolean leaves")
    for index, path in enumerate(paths):
        current = value
        for component in path:
            current = current[component]
        rejected(
            f"{label} boolean-as-integer leaf {index}",
            validator,
            replace_leaf(value, path, 1 if current else 0),
        )


def malicious_adjacent_cache_payload() -> None:
    with open("adjacent-pyc-executed", "wb") as stream:  # noqa: PTH123 -- hostile payload.
        stream.write(b"unchecked adjacent bytecode executed")


def validate_adjacent_unchecked_pyc_nonexecution() -> None:
    version = (sys.version_info.major, sys.version_info.minor)
    magic = PYC_MAGIC_BY_MINOR.get(version)
    require(magic is not None, f"unsupported Python minor for pyc control: {version}")
    with tempfile.TemporaryDirectory(prefix="pid-rs-correction-pyc-") as directory_text:
        directory = Path(directory_text)
        checker = directory / CHECKER.name
        checker_source = _CHECKER_SOURCE_SNAPSHOT
        require(
            checker_source is not None, "checker source snapshot is not initialized"
        )
        checker.write_bytes(checker_source)
        cache = directory / "__pycache__"
        cache.mkdir(mode=0o700)
        code = malicious_adjacent_cache_payload.__code__.replace(
            co_filename=os.fspath(checker), co_name="<module>", co_qualname="<module>"
        )
        header = (
            magic
            + (1).to_bytes(4, "little")
            + hashlib.sha256(checker.read_bytes()).digest()[:8]
        )
        tag = getattr(sys.implementation, "cache_tag", None)
        require(isinstance(tag, str) and tag, "Python cache tag unavailable")
        optimization = ".opt-1" if sys.flags.optimize == 1 else ""
        (cache / f"{checker.stem}.{tag}{optimization}.pyc").write_bytes(
            header + marshal.dumps(code)
        )
        completed = subprocess.run(
            [*PYTHON_CHILD_PREFIX, os.fspath(checker), "--help"],
            cwd=directory,
            env=safe_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        require(
            completed.returncode == 0,
            f"source execution control failed: {completed.stderr!r}",
        )
        require(
            not (directory / "adjacent-pyc-executed").exists(),
            "adjacent unchecked pyc executed",
        )


def git(*arguments: str, environment: dict[str, str] | None = None) -> bytes:
    env = safe_environment()
    if environment:
        env.update(environment)
    command = ["/usr/bin/git"]
    for assignment in EXPECTED_FIXED_GIT_CONFIG:
        command.extend(("-c", assignment))
    command.extend(("-C", os.fspath(ROOT), *arguments))
    completed = subprocess.run(
        command,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"self-test Git failed: {arguments!r}: {completed.stderr!r}",
    )
    return completed.stdout


def validate_sealed_index_route() -> None:
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-correction-index-"
    ) as directory_text:
        index = Path(directory_text) / "index"
        index.write_bytes(b"")
        git(
            "read-tree",
            IMPLEMENTATION_TREE,
            environment={"GIT_INDEX_FILE": os.fspath(index)},
        )
        tree = (
            git("write-tree", environment={"GIT_INDEX_FILE": os.fspath(index)})
            .decode()
            .strip()
        )
        count = len(
            git(
                "ls-files",
                "--stage",
                "-z",
                environment={"GIT_INDEX_FILE": os.fspath(index)},
            )
            .rstrip(b"\0")
            .split(b"\0")
        )
        raw = index.read_bytes()
        os.chmod(index, 0o400)
        completed = invoke(
            [
                "--self-test-sealed-index",
                "--expected-candidate-tree",
                tree,
                "--alternate-index-sha256",
                hashlib.sha256(raw).hexdigest(),
                "--alternate-index-entry-count",
                str(count),
            ],
            stdin=raw,
        )
        require(
            completed.returncode == 0
            and completed.stdout == PASS
            and not completed.stderr,
            f"sealed-index positive control failed: {completed.stderr!r}",
        )
        completed = invoke(
            [
                "--self-test-sealed-index",
                "--expected-candidate-tree",
                tree,
                "--alternate-index-sha256",
                "0" * 64,
                "--alternate-index-entry-count",
                str(count),
            ],
            stdin=raw,
        )
        require(
            completed.returncode == 0
            and completed.stdout == FAIL
            and not completed.stderr,
            "sealed-index wrong digest was accepted",
        )
        # The parent tree is a valid, distinct object; using a malformed object
        # would test transport failure rather than reconstruction mismatch.
        wrong_tree = git("rev-parse", f"{IMPLEMENTATION}^1^{{tree}}").decode().strip()
        for label, hostile_tree, hostile_count in (
            ("tree", wrong_tree, count),
            ("count", tree, count + 1),
        ):
            completed = invoke(
                [
                    "--self-test-sealed-index",
                    "--expected-candidate-tree",
                    hostile_tree,
                    "--alternate-index-sha256",
                    hashlib.sha256(raw).hexdigest(),
                    "--alternate-index-entry-count",
                    str(hostile_count),
                ],
                stdin=raw,
            )
            require(
                completed.returncode == 0
                and completed.stdout == FAIL
                and not completed.stderr,
                f"sealed-index wrong {label} was accepted",
            )


def checkpoint_payload(
    *, parent: str = IMPLEMENTATION, message: str = FIXTURE_CORRECTION_MESSAGE
) -> str:
    identity = "Sepehr Mahmoudian <sepmhn@gmail.com> 1786611807 +0200"
    return (
        f"tree {IMPLEMENTATION_TREE}\nparent {parent}\nauthor {identity}\n"
        f"committer {identity}\n\n{message}"
    )


def projection_record(rows: list[dict[str, Any]], encoding: str) -> dict[str, Any]:
    return {
        "encoding": encoding,
        "entry_count": len(rows),
        "sha256": hashlib.sha256(canonical_json(rows, pretty=False)).hexdigest(),
    }


def capture_record(endpoint: str, projection: Any) -> dict[str, Any]:
    raw = canonical_json(projection, pretty=False)
    return {
        "endpoint_class": endpoint,
        "projection": copy.deepcopy(projection),
        "repetitions_equal": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def scalar_projection(value: dict[str, Any], omissions: set[str]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in omissions}


def refresh_ci_observation(run: dict[str, Any]) -> None:
    roster = run["job_roster"]
    for job in roster:
        job["steps"].sort(key=lambda row: row["number"])
    roster.sort(key=lambda row: row["job_id"])
    run["job_roster_projection"] = projection_record(roster, JOB_PROJECTION_ENCODING)
    omissions = {
        "api_captures",
        "failed_diagnostic",
        "job_roster",
        "job_roster_projection",
        "negative_evidence_sha256",
        "postcommit_source_state_v2",
    }
    run["api_captures"] = [
        capture_record("ci_job_step_roster", roster),
        capture_record("ci_run_summary", scalar_projection(run, omissions)),
        capture_record(
            "postcommit_source_state_v2_artifact",
            run["postcommit_source_state_v2"],
        ),
    ]


def refresh_codeql_observation(run: dict[str, Any]) -> None:
    jobs = run["job_roster"]
    for job in jobs:
        job["steps"].sort(key=lambda row: row["number"])
    jobs.sort(key=lambda row: row["job_id"])
    analyses = run["analysis_roster"]
    analyses.sort(key=lambda row: row["language"])
    run["job_roster_projection"] = projection_record(jobs, JOB_PROJECTION_ENCODING)
    run["analysis_roster_projection"] = projection_record(
        analyses, ANALYSIS_PROJECTION_ENCODING
    )
    omissions = {
        "alert_state",
        "analysis_roster",
        "analysis_roster_projection",
        "api_captures",
        "job_roster",
        "job_roster_projection",
    }
    run["api_captures"] = [
        capture_record("codeql_alert_state", run["alert_state"]),
        capture_record(
            "codeql_job_analysis_roster", {"analyses": analyses, "jobs": jobs}
        ),
        capture_record("codeql_run_summary", scalar_projection(run, omissions)),
    ]


def fixture_artifact(path: str) -> dict[str, Any]:
    raw = path.encode("ascii")
    return {
        "git_blob_oid_sha1": hashlib.sha1(raw).hexdigest(),  # noqa: S324 -- fixture object id.
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def correction_ci_fixture(implementation_ci: dict[str, Any]) -> dict[str, Any]:
    run = copy.deepcopy(implementation_ci)
    for key in (
        "failed_diagnostic",
        "failed_job_count",
        "negative_evidence_sha256",
        "retained_negative_evidence",
        "success_credit",
    ):
        del run[key]
    run.update(
        {
            "all_jobs_successful": True,
            "conclusion": "success",
            "head_equals_correction_commit": True,
            "head_sha": CORRECTION_COMMIT,
            "head_tree": CORRECTION_TREE,
            "head_tree_equals_correction_tree": True,
            "jobs_successful": 45,
            "run_id": 41686107959,
        }
    )
    for job in run["job_roster"]:
        job["job_id"] += 100_000_000_000
        job["conclusion"] = "success"
        for step in job["steps"]:
            if step["conclusion"] != "skipped":
                step["conclusion"] = "success"
    source_artifact = run["postcommit_source_state_v2"]
    source_artifact.update(
        {
            "artifact_id": source_artifact["artifact_id"] + 1,
            "content_sha256": "a" * 64,
            "name": f"post-commit-source-state-v2-{CORRECTION_COMMIT}",
            "sha256": "b" * 64,
        }
    )
    refresh_ci_observation(run)
    return run


def correction_codeql_fixture(implementation_codeql: dict[str, Any]) -> dict[str, Any]:
    run = copy.deepcopy(implementation_codeql)
    run.update(
        {
            "head_equals_correction_commit": True,
            "head_sha": CORRECTION_COMMIT,
            "head_tree": CORRECTION_TREE,
            "head_tree_equals_correction_tree": True,
            "run_id": 41686106737,
            "source_event": "push",
        }
    )
    job_id_map: dict[int, int] = {}
    for job in run["job_roster"]:
        old = job["job_id"]
        job["job_id"] += 200_000_000_000
        job_id_map[old] = job["job_id"]
    for analysis in run["analysis_roster"]:
        analysis["job_id"] = job_id_map[analysis["job_id"]]
        analysis["analysis_id"] += 20_000_000_000
        analysis["commit_sha"] = CORRECTION_COMMIT
    alert_state = run["alert_state"]
    alert_state["baseline_alert_numbers"] = copy.deepcopy(
        alert_state["observed_alert_numbers"]
    )
    alert_state["new_alert_numbers"] = []
    alert_state["observed_new_alerts"] = 0
    run["new_alerts"] = 0
    refresh_codeql_observation(run)
    return run


def phase_output(
    phase: str,
    runtime_mode: int,
    negative_sha256: str,
    alternate_index: dict[str, Any],
) -> dict[str, Any]:
    human = {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"}
    return {
        "candidate": {
            "alternate_index_custody": alternate_index
            if phase == "precommit"
            else None,
            "checkpoint_commit": CORRECTION_COMMIT,
            "commit_envelope": {
                "author": human,
                "committer": human,
                "message": FIXTURE_CORRECTION_MESSAGE,
                "sealed_index_sha256": "7" * 64,
                "sealed_index_size_bytes": 32768,
            },
            "delta": [],
            "tree": CORRECTION_TREE,
        },
        "certified_sxpid_correction": {
            "cli_only_selftest_sha256": "3" * 64,
            "scientific_authority_unchanged": True,
            "three_container_digest_literals": {
                ".github/workflows/ci.yml": "8" * 64,
                "justfile": "9" * 64,
                "scripts/README.md": "a" * 64,
            },
        },
        "child_output_sha256": {
            "scripts/check-certified-sxpid2-claim-self-test.py": "b" * 64,
            "scripts/check-certified-sxpid2-claim.py": "c" * 64,
            "scripts/check-lean-toolchain-freeze-self-test.py": "e" * 64,
            "scripts/check-lean-toolchain-freeze.py": "d" * 64,
        },
        "credit": "none_local_custody_match_hosted_pending",
        "current_source_manifest_sha256": "4" * 64,
        "disposition": "local_hosted_pending_no_credit",
        "implementation_anchor": {
            "commit": IMPLEMENTATION,
            "direct_parent": "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9",
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": 83,
                "sha256": "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843",
            },
            "tree": IMPLEMENTATION_TREE,
        },
        "lean_r6": {
            "schema": "pid-rs/lean-current-project-replay/v2",
            "sha256": "5" * 64,
            "status": "passed",
        },
        "lifecycle": (
            "implementation_plus_exact_correction_overlay"
            if phase == "precommit"
            else "clean_main_direct_child_postcommit_no_credit"
        ),
        "mode": phase,
        "negative_evidence": {
            "codeql_run_id": 31686106737,
            "failed_ci_run_id": 31686107959,
            "failed_jobs": 1,
            "jobs": 45,
            "sha256": negative_sha256,
        },
        "policy_sha256": "6" * 64,
        "preclosure": {
            "final_decision_absent": True,
            "final_evidence_matrix_absent": True,
            "future_composite_receipt_absent": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        "repository_state": {"active_git_operations": [], "branch": "main"},
        "runtime_mode": runtime_mode,
        "schema": "pid-rs/ksg-rev4-m1a-custody-correction-phase-validation/v1",
        "static_artifact_sha256": {
            "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md": "e"
            * 64,
            "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json": "f" * 64,
            "scripts/check-ksg-m1a-custody-correction-self-test.py": "1" * 64,
            "scripts/check-ksg-m1a-custody-correction.py": "2" * 64,
        },
    }


def phase_output_group(
    phase: str, negative_sha256: str, alternate_index: dict[str, Any]
) -> dict[str, Any]:
    normal = phase_output(phase, 0, negative_sha256, alternate_index)
    optimized = phase_output(phase, 1, negative_sha256, alternate_index)
    return {
        "normal": {
            "output": normal,
            "sha256": hashlib.sha256(canonical_json(normal, pretty=False)).hexdigest(),
        },
        "optimized": {
            "output": optimized,
            "sha256": hashlib.sha256(
                canonical_json(optimized, pretty=False)
            ).hexdigest(),
        },
        "pair_normalized_equal": True,
    }


def reseal_phase_outputs(receipt: dict[str, Any]) -> None:
    local = receipt["local_phase_custody"]
    for phase in ("precommit", "postcommit"):
        group = local[f"{phase}_outputs"]
        for label in ("normal", "optimized"):
            output = group[label]["output"]
            group[label]["sha256"] = hashlib.sha256(
                canonical_json(output, pretty=False)
            ).hexdigest()


def normalize_lean_cycle_fixture_cuts(candidate_source: str) -> str:
    operational_placeholder = (
        '    "scripts/check-ksg-m1a-custody-correction.py": PENDING_OPERATIONAL_SHA256,'
    )
    operational_final_pattern = re.compile(
        r'^    "scripts/check-ksg-m1a-custody-correction\.py": "[0-9a-f]{64}",$',
        flags=re.MULTILINE,
    )
    projection_placeholder = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    projection_final_pattern = re.compile(
        r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "[0-9a-f]{64}"$',
        flags=re.MULTILINE,
    )
    operational_placeholder_count = candidate_source.count(operational_placeholder)
    operational_final_matches = list(
        operational_final_pattern.finditer(candidate_source)
    )
    projection_placeholder_count = candidate_source.count(projection_placeholder)
    projection_final_matches = list(projection_final_pattern.finditer(candidate_source))
    require(
        operational_placeholder_count + len(operational_final_matches) == 1
        and projection_placeholder_count + len(projection_final_matches) == 1,
        "Lean cycle fixture cut forms are absent, duplicate, or ambiguous",
    )
    source = candidate_source
    if operational_final_matches:
        match = operational_final_matches[0]
        source = (
            source[: match.start()] + operational_placeholder + source[match.end() :]
        )
    if projection_final_matches:
        match = projection_final_pattern.search(source)
        require(match is not None, "Lean cycle final projection cut disappeared")
        source = (
            source[: match.start()] + projection_placeholder + source[match.end() :]
        )
    require(
        source.count(operational_placeholder) == 1
        and source.count(projection_placeholder) == 1,
        "Lean cycle fixture cut normalization failed",
    )
    return source


def lean_cycle_fixture(candidate_source: str) -> dict[str, Any]:
    operational_placeholder = (
        '    "scripts/check-ksg-m1a-custody-correction.py": PENDING_OPERATIONAL_SHA256,'
    )
    operational_final = (
        f'    "scripts/check-ksg-m1a-custody-correction.py": "{"a" * 64}",'
    )
    provisional_source = normalize_lean_cycle_fixture_cuts(candidate_source)
    replay_source = provisional_source.replace(
        operational_placeholder, operational_final, 1
    )
    replay_checker_sha = hashlib.sha256(replay_source.encode("utf-8")).hexdigest()
    receipt = {
        "custody_gate_sha256": {
            "scripts/check-lean-toolchain-freeze-self-test.py": "b" * 64,
            "scripts/check-lean-toolchain-freeze.py": "0" * 64,
        },
        "operational_wiring_sha256": {
            "scripts/check-ksg-m1a-custody-correction.py": "a" * 64,
            "scripts/generate-lean-4.33-replay.py": "c" * 64,
        },
        "prior_replay_preservation_sha256": {
            "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json": "872175ca504efb24752633704fe13e57802e43ae25bb3c463c4fb8c9dfd073f7"
        },
        "prior_replay_schema": {
            "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json": "pid-rs/lean-current-project-replay/v2"
        },
        "replay_custody_gate_sha256": {
            "scripts/check-lean-toolchain-freeze-self-test.py": "b" * 64,
            "scripts/check-lean-toolchain-freeze.py": replay_checker_sha,
        },
        "schema": "pid-rs/lean-current-project-replay/v2",
        "status": "passed",
    }
    fixture = {"checker_source": replay_source, "receipt": receipt}
    reseal_lean_cycle_fixture(fixture)
    return fixture


def lean_cycle_fixture_source_rejected(label: str, source: str) -> None:
    try:
        normalize_lean_cycle_fixture_cuts(source)
    except SelfTestError:
        return
    raise SelfTestError(f"Lean cycle fixture source hostile accepted: {label}")


def reseal_lean_cycle_fixture(fixture: dict[str, Any]) -> None:
    source = fixture["checker_source"]
    match = re.search(
        r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "[0-9a-f]{64}"$',
        source,
        flags=re.MULTILINE,
    )
    if match is not None:
        source = (
            source[: match.start()]
            + 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
            + source[match.end() :]
        )
    require(
        source.count('EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64') == 1,
        "Lean cycle fixture projection cut is not unique",
    )
    receipt = fixture["receipt"]
    receipt["replay_custody_gate_sha256"]["scripts/check-lean-toolchain-freeze.py"] = (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
    )
    projected = copy.deepcopy(receipt)
    projected["custody_gate_sha256"] = {
        "scripts/check-lean-toolchain-freeze-self-test.py": receipt[
            "custody_gate_sha256"
        ]["scripts/check-lean-toolchain-freeze-self-test.py"]
    }
    projection_sha = hashlib.sha256(
        json.dumps(
            projected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    final_source = source.replace(
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
        f'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "{projection_sha}"',
        1,
    )
    receipt["custody_gate_sha256"]["scripts/check-lean-toolchain-freeze.py"] = (
        hashlib.sha256(final_source.encode("utf-8")).hexdigest()
    )
    fixture["checker_source"] = final_source


def mutate_all_phase_outputs(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    local = receipt["local_phase_custody"]
    for phase in ("precommit", "postcommit"):
        for label in ("normal", "optimized"):
            operation(local[f"{phase}_outputs"][label]["output"])
    reseal_phase_outputs(receipt)


def composite_fixture(negative: dict[str, Any]) -> dict[str, Any]:
    negative_raw = canonical_json(negative, pretty=True)
    negative_sha256 = hashlib.sha256(negative_raw).hexdigest()
    implementation_ci = copy.deepcopy(negative["ci_failure"])
    implementation_ci["negative_evidence_sha256"] = negative_sha256
    implementation_codeql = copy.deepcopy(negative["codeql_success"])
    correction_ci = correction_ci_fixture(implementation_ci)
    correction_codeql = correction_codeql_fixture(implementation_codeql)
    alternate_index = {
        "entry_count": 109,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "retained_index_artifact": {
            "git_blob_oid_sha1": "4" * 40,
            "path": "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin",
            "sha256": "7" * 64,
            "size_bytes": 32768,
        },
        "sha256": "7" * 64,
        "single_link": True,
        "size_bytes": 32768,
    }
    local = {
        name: fixture_artifact(path)
        for name, path in {
            "boundary_memo": "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md",
            "checker": "scripts/check-ksg-m1a-custody-correction.py",
            "current_source_manifest": "audit/evidence/current-source-state-v1.json",
            "lean_r6_receipt": "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json",
            "policy": "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json",
            "schema": "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json",
            "self_test": "scripts/check-ksg-m1a-custody-correction-self-test.py",
        }.items()
    }
    local.update(
        {
            "alternate_index": alternate_index,
            "candidate_tree_matches_checkpoint": True,
            "certified_sxpid_correction": {
                "bounded_private_cli_protocol_exact": True,
                "checker": fixture_artifact("scripts/check-certified-sxpid2-claim.py"),
                "cli_only_selftest_transport": True,
                "scientific_authority_unchanged": True,
                "self_test": fixture_artifact(
                    "scripts/check-certified-sxpid2-claim-self-test.py"
                ),
                "three_container_digest_rebind_exact": True,
            },
            "checkpoint_became_correction_commit": True,
            "detached_checkpoint_commit": CORRECTION_COMMIT,
            "independently_recorded_before_ref_update": True,
            "lean_r5_preserved_sha256": "872175ca504efb24752633704fe13e57802e43ae25bb3c463c4fb8c9dfd073f7",
            "postcommit_disposition": "local_hosted_pending_no_credit",
            "postcommit_outputs": phase_output_group(
                "postcommit", negative_sha256, alternate_index
            ),
            "precommit_disposition": "local_hosted_pending_no_credit",
            "precommit_outputs": phase_output_group(
                "precommit", negative_sha256, alternate_index
            ),
        }
    )
    return {
        "acyclic_boundary": {
            "correction_tree_excludes_receipt": True,
            "correction_tree_excludes_retained_index": True,
            "implementation_tree_excludes_receipt": True,
            "implementation_tree_excludes_retained_index": True,
            "later_descendant_required": True,
            "receipt_claims_its_own_commit": False,
            "receipt_hashes_itself": False,
            "receipt_subjects_preexist_receipt": True,
        },
        "claim": {"id": "KSG-INTEGER-HARMONIC-001", "revision": 4},
        "custody_correction": {
            "author": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "branch": "main",
            "commit": CORRECTION_COMMIT,
            "commit_message": FIXTURE_CORRECTION_MESSAGE,
            "committer": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "direct_parent": IMPLEMENTATION,
            "distinct_from_implementation_anchor": True,
            "implementation_identity_after_correction": IMPLEMENTATION,
            "object_format": "sha1",
            "one_parent": True,
            "tree": CORRECTION_TREE,
            "unsigned": True,
        },
        "evidence_class": "m1a_composite_lifecycle_custody_not_scientific_evidence",
        "hosted_observations": {
            "all_green_applies_only_to_correction_head": True,
            "correction_ci_success": correction_ci,
            "correction_codeql_success": correction_codeql,
            "correction_heads_equal": True,
            "implementation_and_correction_heads_distinct": True,
            "implementation_ci_failure": implementation_ci,
            "implementation_codeql_success": implementation_codeql,
            "implementation_heads_equal": True,
            "negative_evidence_artifact": {
                **fixture_artifact(
                    "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
                ),
                "sha256": negative_sha256,
                "size_bytes": len(negative_raw),
            },
        },
        "implementation_anchor": {
            "commit": IMPLEMENTATION,
            "direct_parent": "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9",
            "object_format": "sha1",
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": 83,
                "format": "canonical compact sorted-key ASCII JSON plus LF over sorted {path,git_mode,git_blob_oid_sha1,sha256,size_bytes} rows",
                "sha256": "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843",
            },
            "remains_implementation_after_correction": True,
            "tree": IMPLEMENTATION_TREE,
        },
        "local_phase_custody": local,
        "milestone": {
            "gate_id": "G1",
            "implementation_phase": "M1a",
            "integration_status": "integration_no_go",
            "status": "implementation_anchor_and_custody_correction_observed",
        },
        "negative_evidence_semantics": copy.deepcopy(negative["negative_semantics"]),
        "nonimplications": COMPOSITE_NONIMPLICATIONS,
        "remote_observations": {
            "authentication_claimed": False,
            "correction_commit": CORRECTION_COMMIT,
            "implementation_commit": IMPLEMENTATION,
            "ref": "refs/heads/main",
            "remote": "origin",
            "repeated_observations_equal": True,
        },
        "repository": "sepahead/pid-rs",
        "revision4_integration": {
            "decision_v4_absent_at_correction": True,
            "evidence_matrix_v4_absent_at_correction": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v2",
        "schema_revision": 2,
    }


def main() -> int:
    global _CHECKER_SOURCE_SNAPSHOT
    require(
        _CHECKER_SOURCE_SNAPSHOT is None, "checker source snapshot initialized twice"
    )
    checker_source_snapshot, checker_path_identity = stable_source_snapshot(CHECKER)
    self_test_source_snapshot, self_test_path_identity = stable_source_snapshot(SCRIPT)
    _CHECKER_SOURCE_SNAPSHOT = checker_source_snapshot
    validate_checker_stdin_bootstrap()
    validate_static_cli_custody(checker_source_snapshot, self_test_source_snapshot)
    validate_private_directory_baseline_regression(checker_source_snapshot)
    validate_adjacent_unchecked_pyc_nonexecution()
    policy = strict_json(POLICY)
    schema = strict_json(SCHEMA)
    boundary = BOUNDARY.read_text(encoding="utf-8")
    state = policy["authority"]["inventory_status"]
    require(state in {"provisional", "frozen"}, "fixture policy state is invalid")
    accepted("policy", policy)
    for label, container, field, hostile_scalar in (
        (
            "policy integer author/committer equality",
            "commit_envelope",
            "author_and_committer_headers_identical",
            1,
        ),
        (
            "policy integer signature permission",
            "commit_envelope",
            "signature_headers_permitted",
            0,
        ),
        (
            "policy integer later-descendant requirement",
            "receipt_contract",
            "later_descendant_required",
            1,
        ),
    ):
        rejected(
            label,
            "policy",
            mutate(
                policy,
                lambda value, container=container, field=field, hostile_scalar=hostile_scalar: (
                    value[container].update({field: hostile_scalar})
                ),
            ),
        )
    accepted("schema", schema)
    accepted("schema_numeric_types", schema)
    rejected(
        "schema numeric const loses explicit integer type",
        "schema_numeric_types",
        mutate(
            schema,
            lambda value: value["properties"]["schema_revision"].pop("type"),
        ),
    )
    rejected(
        "schema boolean const loses explicit boolean type",
        "schema_numeric_types",
        mutate(
            schema,
            lambda value: value["properties"]["acyclic_boundary"]["properties"][
                "correction_tree_excludes_receipt"
            ].update(const=1, type="integer"),
        ),
    )
    rejected(
        "schema root additional-properties integer alias",
        "schema_numeric_types",
        mutate(schema, lambda value: value.update(additionalProperties=0)),
    )
    rejected(
        "schema unique-items integer alias",
        "schema_numeric_types",
        mutate(
            schema,
            lambda value: value["$defs"]["alertState"]["properties"][
                "baseline_alert_numbers"
            ].update(uniqueItems=1),
        ),
    )
    coordinated_const_swap = copy.deepcopy(schema)
    coordinated_const_swap["$defs"]["apiCapture"]["properties"][
        "repetitions_equal"
    ].update(const=1, type="integer")
    coordinated_const_swap["$defs"]["alertState"]["properties"][
        "observed_new_alerts"
    ].update(const=True, type="boolean")
    rejected(
        "schema coordinated boolean/integer const-slot swap",
        "schema_numeric_types",
        coordinated_const_swap,
    )
    coordinated_control_swap = copy.deepcopy(schema)
    coordinated_control_swap["additionalProperties"] = True
    coordinated_control_swap["$defs"]["alertState"]["properties"][
        "baseline_alert_numbers"
    ]["uniqueItems"] = False
    rejected(
        "schema coordinated boolean-control value swap",
        "schema_numeric_types",
        coordinated_control_swap,
    )
    boolean_type_fixture = {
        field: index % 2 == 0 for index, field in enumerate(BOOLEAN_FIELD_NAMES)
    }
    accepted("json_scalar_types", boolean_type_fixture)
    reject_boolean_integer_aliases(
        "json_scalar_types", boolean_type_fixture, "reviewed boolean field inventory"
    )
    accepted("boundary", {"state": state, "text": boundary})
    authority_artifacts = {
        "boundary": boundary,
        "self_test": self_test_source_snapshot.decode("utf-8", errors="strict"),
    }
    accepted("correction_authority_artifacts", authority_artifacts)
    rejected(
        "trivial correction self-test replacement",
        "correction_authority_artifacts",
        mutate(
            authority_artifacts,
            lambda value: value.update(
                self_test=(
                    "#!/usr/bin/env python3\n"
                    "print('OK: KSG M1a custody-correction CLI hostile suite passed')\n"
                )
            ),
        ),
    )
    accepted(
        "runtime_mode",
        {"isolated": True, "no_site": True, "optimize": sys.flags.optimize},
    )
    rejected(
        "runtime isolated integer alias",
        "runtime_mode",
        {"isolated": 1, "no_site": True, "optimize": sys.flags.optimize},
    )
    rejected(
        "runtime no-site integer alias",
        "runtime_mode",
        {"isolated": True, "no_site": 1, "optimize": sys.flags.optimize},
    )
    accepted("checkpoint", {"raw": checkpoint_payload(), "tree": IMPLEMENTATION_TREE})
    accepted(
        "lifecycle_metadata",
        {"active_operations": [], "branch": "main", "mode": "postcommit"},
    )
    accepted(
        "lifecycle_metadata",
        {"active_operations": [], "branch": None, "mode": "candidate-commit"},
    )
    accepted("fixed_git_config", EXPECTED_FIXED_GIT_CONFIG)
    rejected(
        "fixed Git case-sensitive classification removed",
        "fixed_git_config",
        [
            assignment
            for assignment in EXPECTED_FIXED_GIT_CONFIG
            if assignment != "core.ignoreCase=false"
        ],
    )
    rejected(
        "fixed Git ambient ignore-case classification enabled",
        "fixed_git_config",
        [
            "core.ignoreCase=true"
            if assignment == "core.ignoreCase=false"
            else assignment
            for assignment in EXPECTED_FIXED_GIT_CONFIG
        ],
    )
    accepted(
        "repository_security",
        {"config_keys": ["core.bare", "remote.origin.url"], "is_shallow": "false"},
    )
    accepted(
        "temporary_root_security",
        {
            "is_directory": True,
            "is_symlink": False,
            "owner_uid": 0,
            "sticky": True,
        },
    )
    stable_identity = [1, 2, 0o100500, 1, 1024, 3, 4]
    accepted(
        "path_descriptor_identity",
        {
            "descriptor_after": stable_identity,
            "descriptor_before": stable_identity,
            "path_after": stable_identity,
            "path_before": stable_identity,
        },
    )
    rejected(
        "path/descriptor swapped inode",
        "path_descriptor_identity",
        {
            "descriptor_after": [1, 9, 0o100500, 1, 1024, 3, 4],
            "descriptor_before": [1, 9, 0o100500, 1, 1024, 3, 4],
            "path_after": stable_identity,
            "path_before": stable_identity,
        },
    )
    accepted("git_predicate_status", {"returncode": 0})
    leaf_blob_oid = "3" * 40
    leaf_tree_raw = b"100644 leaf\0" + bytes.fromhex(leaf_blob_oid)
    leaf_tree_oid = hashlib.sha1(  # noqa: S324 -- synthetic Git tree identity.
        f"tree {len(leaf_tree_raw)}\0".encode("ascii") + leaf_tree_raw
    ).hexdigest()
    nested_root_raw = b"40000 sub\0" + bytes.fromhex(leaf_tree_oid)
    nested_root_oid = hashlib.sha1(  # noqa: S324 -- synthetic Git tree identity.
        f"tree {len(nested_root_raw)}\0".encode("ascii") + nested_root_raw
    ).hexdigest()
    accepted(
        "raw_tree_graph",
        {
            "objects": {
                leaf_tree_oid: leaf_tree_raw.hex(),
                nested_root_oid: nested_root_raw.hex(),
            },
            "root": nested_root_oid,
        },
    )
    empty_tree_raw = b""
    empty_tree_oid = hashlib.sha1(  # noqa: S324 -- synthetic Git tree identity.
        b"tree 0\0"
    ).hexdigest()
    empty_root_raw = b"40000 empty\0" + bytes.fromhex(empty_tree_oid)
    empty_root_oid = hashlib.sha1(  # noqa: S324 -- synthetic Git tree identity.
        f"tree {len(empty_root_raw)}\0".encode("ascii") + empty_root_raw
    ).hexdigest()
    rejected(
        "nested empty tree",
        "raw_tree_graph",
        {
            "objects": {
                empty_tree_oid: empty_tree_raw.hex(),
                empty_root_oid: empty_root_raw.hex(),
            },
            "root": empty_root_oid,
        },
    )
    anchor_cert_source = git(
        "show", f"{IMPLEMENTATION}:scripts/check-certified-sxpid2-claim.py"
    ).decode("utf-8", errors="strict")
    candidate_cert_source = (
        ROOT / "scripts/check-certified-sxpid2-claim.py"
    ).read_text(encoding="utf-8")
    accepted(
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source,
        },
    )
    anchor_lean_source = git(
        "show", f"{IMPLEMENTATION}:scripts/check-lean-toolchain-freeze.py"
    ).decode("utf-8", errors="strict")
    candidate_lean_source = (ROOT / "scripts/check-lean-toolchain-freeze.py").read_text(
        encoding="utf-8"
    )
    accepted(
        "lean_checker_structure",
        {
            "anchor_source": anchor_lean_source,
            "candidate_source": candidate_lean_source,
        },
    )
    operational_placeholder = (
        '    "scripts/check-ksg-m1a-custody-correction.py": PENDING_OPERATIONAL_SHA256,'
    )
    projection_placeholder = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    normalized_lean_source = normalize_lean_cycle_fixture_cuts(candidate_lean_source)
    l0_lean_source = normalized_lean_source.replace(
        operational_placeholder,
        f'    "scripts/check-ksg-m1a-custody-correction.py": "{"e" * 64}",',
        1,
    )
    finalized_lean_source = l0_lean_source.replace(
        projection_placeholder,
        f'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "{"f" * 64}"',
        1,
    )
    require(
        normalize_lean_cycle_fixture_cuts(candidate_lean_source)
        == normalized_lean_source
        and normalize_lean_cycle_fixture_cuts(l0_lean_source) == normalized_lean_source
        and normalize_lean_cycle_fixture_cuts(finalized_lean_source)
        == normalized_lean_source,
        "Lean cycle fixture provisional/L0/final cut normalization changed",
    )
    lean_cycle = lean_cycle_fixture(candidate_lean_source)
    accepted("lean_cycle_relations", lean_cycle)
    for label, source in (
        ("L0", l0_lean_source),
        ("final", finalized_lean_source),
    ):
        accepted(
            "lean_checker_structure",
            {
                "anchor_source": anchor_lean_source,
                "candidate_source": source,
            },
        )
        alternate_cycle = lean_cycle_fixture(source)
        require(
            canonical_json(alternate_cycle, pretty=False)
            == canonical_json(lean_cycle, pretty=False),
            f"Lean cycle fixture provisional/{label} forms diverged",
        )
        accepted("lean_cycle_relations", alternate_cycle)
    for label, source in (
        (
            "duplicate operational placeholder",
            normalized_lean_source.replace(
                operational_placeholder,
                f"{operational_placeholder}\n{operational_placeholder}",
                1,
            ),
        ),
        (
            "ambiguous operational placeholder/final pair",
            normalized_lean_source.replace(
                operational_placeholder,
                operational_placeholder
                + "\n"
                + f'    "scripts/check-ksg-m1a-custody-correction.py": "{"e" * 64}",',
                1,
            ),
        ),
        (
            "duplicate projection placeholder",
            normalized_lean_source.replace(
                projection_placeholder,
                f"{projection_placeholder}\n{projection_placeholder}",
                1,
            ),
        ),
        (
            "ambiguous projection placeholder/final pair",
            normalized_lean_source.replace(
                projection_placeholder,
                projection_placeholder
                + "\n"
                + f'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "{"f" * 64}"',
                1,
            ),
        ),
    ):
        lean_cycle_fixture_source_rejected(label, source)
    rejected(
        "Lean cycle wrong correction cut",
        "lean_cycle_relations",
        mutate(
            lean_cycle,
            lambda value: value.update(
                checker_source=value["checker_source"].replace(
                    f'"{"a" * 64}",', f'"{"d" * 64}",', 1
                )
            ),
        ),
    )
    wrong_projection = copy.deepcopy(lean_cycle)
    wrong_projection["checker_source"] = re.sub(
        r'(EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = ")[0-9a-f]{64}("$)',
        r"\g<1>" + "d" * 64 + r"\g<2>",
        wrong_projection["checker_source"],
        count=1,
        flags=re.MULTILINE,
    )
    rejected(
        "Lean cycle wrong projection cut", "lean_cycle_relations", wrong_projection
    )
    wrong_both = copy.deepcopy(wrong_projection)
    wrong_both["checker_source"] = wrong_both["checker_source"].replace(
        f'"{"a" * 64}",', f'"{"d" * 64}",', 1
    )
    rejected("Lean cycle both cuts wrong", "lean_cycle_relations", wrong_both)
    third_byte = copy.deepcopy(lean_cycle)
    third_byte["checker_source"] = third_byte["checker_source"].replace(
        "Bind all replay observations except", "Bind replay observations except", 1
    )
    rejected("Lean cycle unrelated third byte", "lean_cycle_relations", third_byte)
    placeholder = copy.deepcopy(lean_cycle)
    placeholder["checker_source"] = re.sub(
        r'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "[0-9a-f]{64}"',
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
        placeholder["checker_source"],
        count=1,
    )
    rejected("Lean cycle placeholder retained", "lean_cycle_relations", placeholder)
    duplicate_assignment = copy.deepcopy(lean_cycle)
    duplicate_assignment["checker_source"] = duplicate_assignment[
        "checker_source"
    ].replace(
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 =",
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64\n'
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 =",
        1,
    )
    rejected(
        "Lean cycle duplicate projection assignment",
        "lean_cycle_relations",
        duplicate_assignment,
    )
    coordinated_selftest = copy.deepcopy(lean_cycle)
    coordinated_selftest["receipt"]["custody_gate_sha256"][
        "scripts/check-lean-toolchain-freeze-self-test.py"
    ] = "d" * 64
    coordinated_selftest["receipt"]["replay_custody_gate_sha256"][
        "scripts/check-lean-toolchain-freeze-self-test.py"
    ] = "d" * 64
    reseal_lean_cycle_fixture(coordinated_selftest)
    rejected(
        "Lean coordinated selftest/receipt reseal",
        "lean_cycle_relations",
        coordinated_selftest,
    )
    coordinated_generator = copy.deepcopy(lean_cycle)
    coordinated_generator["receipt"]["operational_wiring_sha256"][
        "scripts/generate-lean-4.33-replay.py"
    ] = "d" * 64
    reseal_lean_cycle_fixture(coordinated_generator)
    rejected(
        "Lean coordinated generator/receipt reseal",
        "lean_cycle_relations",
        coordinated_generator,
    )
    for label, container, key in (
        (
            "Lean final custody checker drift",
            "custody_gate_sha256",
            "scripts/check-lean-toolchain-freeze.py",
        ),
        (
            "Lean replay checker drift",
            "replay_custody_gate_sha256",
            "scripts/check-lean-toolchain-freeze.py",
        ),
        (
            "Lean r5 preservation digest drift",
            "prior_replay_preservation_sha256",
            "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json",
        ),
        (
            "Lean r5 preservation schema drift",
            "prior_replay_schema",
            "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json",
        ),
    ):
        hostile = copy.deepcopy(lean_cycle)
        hostile["receipt"][container][key] = "d" * 64
        if container == "replay_custody_gate_sha256":
            # Keep the hostile replay digest while resealing the projection and
            # final checker custody around that false replay observation.
            wrong_replay = hostile["receipt"][container][key]
            reseal_lean_cycle_fixture(hostile)
            hostile["receipt"][container][key] = wrong_replay
            source = hostile["checker_source"]
            source = re.sub(
                r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "[0-9a-f]{64}"$',
                'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
                source,
                count=1,
                flags=re.MULTILINE,
            )
            projected = copy.deepcopy(hostile["receipt"])
            projected["custody_gate_sha256"] = {
                "scripts/check-lean-toolchain-freeze-self-test.py": projected[
                    "custody_gate_sha256"
                ]["scripts/check-lean-toolchain-freeze-self-test.py"]
            }
            projection_sha = hashlib.sha256(
                json.dumps(
                    projected,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            final_source = source.replace(
                'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
                f'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "{projection_sha}"',
                1,
            )
            hostile["checker_source"] = final_source
            hostile["receipt"]["custody_gate_sha256"][
                "scripts/check-lean-toolchain-freeze.py"
            ] = hashlib.sha256(final_source.encode("utf-8")).hexdigest()
        elif container != "custody_gate_sha256":
            reseal_lean_cycle_fixture(hostile)
        rejected(label, "lean_cycle_relations", hostile)
    wiring_sources = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in (".github/workflows/ci.yml", "justfile", "scripts/README.md")
    }
    accepted("correction_wiring", wiring_sources)

    rejected(
        "policy credit before freeze",
        "policy",
        mutate(policy, lambda value: value["authority"].update(credit_permitted=True)),
    )
    provisional_policy = mutate(
        policy,
        lambda value: value["authority"].update(
            credit_permitted=False,
            inventory_status="provisional",
            lifecycle_validation_permitted=False,
        ),
    )
    frozen_policy = mutate(
        policy,
        lambda value: value["authority"].update(
            credit_permitted=False,
            inventory_status="frozen",
            lifecycle_validation_permitted=True,
        ),
    )
    accepted("policy", provisional_policy)
    accepted("policy", frozen_policy)
    rejected(
        "frozen policy overcredits",
        "policy",
        mutate(
            frozen_policy,
            lambda value: value["authority"].update(credit_permitted=True),
        ),
    )
    rejected(
        "provisional lifecycle enabled",
        "policy",
        mutate(
            provisional_policy,
            lambda value: value["authority"].update(
                lifecycle_validation_permitted=True
            ),
        ),
    )
    rejected(
        "policy freeze order weakened",
        "policy",
        mutate(
            policy,
            lambda value: value["authority"].update(
                freeze_instruction=value["authority"]["freeze_instruction"].replace(
                    "Patch the checker and prospective Lean maps first", "Patch files"
                )
            ),
        ),
    )
    rejected(
        "policy protected count",
        "policy",
        mutate(
            policy,
            lambda value: value["implementation_anchor"]["protected_projection"].update(
                entry_count=82
            ),
        ),
    )
    for label, target, hostile_scalar in (
        ("policy float protected count", "projection", 83.0),
        ("policy float parent count", "parent", 1.0),
        ("policy boolean parent count", "parent", True),
    ):
        hostile_policy = copy.deepcopy(policy)
        if target == "projection":
            hostile_policy["implementation_anchor"]["protected_projection"][
                "entry_count"
            ] = hostile_scalar
        else:
            hostile_policy["commit_envelope"]["parent_count"] = hostile_scalar
        rejected(label, "policy", hostile_policy)
    rejected(
        "policy implementation identity",
        "policy",
        mutate(
            policy, lambda value: value["implementation_anchor"].update(commit="0" * 40)
        ),
    )
    rejected(
        "policy omits negative evidence",
        "policy",
        mutate(
            policy,
            lambda value: value["entries"].__setitem__(
                7, {**value["entries"][7], "path": "audit/evidence/renamed.json"}
            ),
        ),
    )
    rejected(
        "policy moves certified selftest class",
        "policy",
        mutate(
            policy,
            lambda value: next(
                row
                for row in value["entries"]
                if row["path"] == "scripts/check-certified-sxpid2-claim-self-test.py"
            ).update(review_class="certified_sxpid_rebind_and_cli_protocol_custody"),
        ),
    )
    rejected(
        "schema implementation anchor",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["implementation_anchor"]["properties"][
                "commit"
            ].update(const="0" * 40),
        ),
    )
    rejected(
        "schema one-parent weakened",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["custody_correction"]["properties"][
                "one_parent"
            ].update(const=False),
        ),
    )
    rejected(
        "schema required deletion",
        "schema",
        mutate(schema, lambda value: value["required"].pop()),
    )
    rejected(
        "schema root extensions",
        "schema",
        mutate(schema, lambda value: value.update(additionalProperties=True)),
    )
    rejected(
        "schema hosted extensions",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["hosted_observations"].update(
                additionalProperties=True
            ),
        ),
    )
    rejected(
        "schema analysis ref",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["hosted_observations"]["properties"][
                "implementation_codeql_success"
            ]["allOf"][1]["properties"]["analysis_roster_projection"].update(
                {"$ref": "#/$defs/jobProjection"}
            ),
        ),
    )
    rejected(
        "schema failed run relabeled",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["hosted_observations"]["properties"][
                "implementation_ci_failure"
            ]["properties"]["conclusion"].update(const="success"),
        ),
    )
    rejected(
        "schema receipt in correction",
        "schema",
        mutate(
            schema,
            lambda value: value["properties"]["acyclic_boundary"]["properties"][
                "correction_tree_excludes_receipt"
            ].update(const=False),
        ),
    )
    rejected(
        "boundary loses failed run",
        "boundary",
        {"state": state, "text": boundary.replace("31686107959", "31686107958")},
    )
    rejected(
        "boundary freeze order weakened",
        "boundary",
        {
            "state": state,
            "text": boundary.replace(
                "no authored byte may change", "bytes should remain stable"
            ),
        },
    )
    rejected(
        "boundary contradictory lifecycle-credit append",
        "boundary",
        {
            "state": state,
            "text": boundary
            + "\nThe correction grants M1a lifecycle credit and hosted success.\n",
        },
    )
    rejected(
        "boundary mismatched state marker",
        "boundary",
        {
            "state": "frozen" if state == "provisional" else "provisional",
            "text": boundary,
        },
    )
    rejected(
        "wrong parent",
        "checkpoint",
        {"raw": checkpoint_payload(parent="0" * 40), "tree": IMPLEMENTATION_TREE},
    )
    rejected(
        "checkpoint missing sealed-index trailer",
        "checkpoint",
        {
            "raw": checkpoint_payload(
                message="Correct KSG M1a hosted custody wiring\n"
            ),
            "tree": IMPLEMENTATION_TREE,
        },
    )
    rejected(
        "checkpoint malformed sealed-index digest",
        "checkpoint",
        {
            "raw": checkpoint_payload(
                message=FIXTURE_CORRECTION_MESSAGE.replace("7" * 64, "G" * 64)
            ),
            "tree": IMPLEMENTATION_TREE,
        },
    )
    rejected(
        "checkpoint noncanonical sealed-index size",
        "checkpoint",
        {
            "raw": checkpoint_payload(
                message=FIXTURE_CORRECTION_MESSAGE.replace("32768", "032768")
            ),
            "tree": IMPLEMENTATION_TREE,
        },
    )
    rejected(
        "checkpoint extra message trailer",
        "checkpoint",
        {
            "raw": checkpoint_payload(
                message=FIXTURE_CORRECTION_MESSAGE + "Unreviewed: yes\n"
            ),
            "tree": IMPLEMENTATION_TREE,
        },
    )
    rejected(
        "detached strict postcommit",
        "lifecycle_metadata",
        {"active_operations": [], "branch": None, "mode": "postcommit"},
    )
    rejected(
        "attached candidate diagnostic",
        "lifecycle_metadata",
        {"active_operations": [], "branch": "main", "mode": "candidate-commit"},
    )
    rejected(
        "PR merge branch",
        "lifecycle_metadata",
        {"active_operations": [], "branch": "pull/123/merge", "mode": "postcommit"},
    )
    rejected(
        "active rebase",
        "lifecycle_metadata",
        {"active_operations": ["rebase-merge"], "branch": "main", "mode": "postcommit"},
    )
    rejected(
        "shallow repository",
        "repository_security",
        {"config_keys": ["core.bare"], "is_shallow": "true"},
    )
    rejected(
        "partial clone",
        "repository_security",
        {"config_keys": ["extensions.partialclone"], "is_shallow": "false"},
    )
    rejected(
        "promisor remote",
        "repository_security",
        {"config_keys": ["remote.origin.promisor"], "is_shallow": "false"},
    )
    rejected(
        "local config include",
        "repository_security",
        {"config_keys": ["include.path"], "is_shallow": "false"},
    )
    rejected(
        "local excludes-file config",
        "repository_security",
        {"config_keys": ["core.excludesfile"], "is_shallow": "false"},
    )
    rejected(
        "conditional local config include",
        "repository_security",
        {"config_keys": ["includeif.gitdir:/tmp/.path"], "is_shallow": "false"},
    )
    for label, field, hostile in (
        ("temporary root symlink", "is_symlink", True),
        ("temporary root non-directory", "is_directory", False),
        ("temporary root non-root owner", "owner_uid", 1),
        ("temporary root lacks sticky bit", "sticky", False),
    ):
        rejected(
            label,
            "temporary_root_security",
            mutate(
                {
                    "is_directory": True,
                    "is_symlink": False,
                    "owner_uid": 0,
                    "sticky": True,
                },
                lambda value, field=field, hostile=hostile: value.update(
                    {field: hostile}
                ),
            ),
        )
    rejected("Git predicate error", "git_predicate_status", {"returncode": 128})
    rejected(
        "certified protocol function mutation",
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source.replace(
                'raise ClaimPacketError("self-test operation is not registered")',
                'raise ClaimPacketError("unknown private operation")',
                1,
            ),
        },
    )
    rejected(
        "certified semantic-core mutation",
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source.replace(
                'raise ClaimPacketError(f"duplicate JSON object key: {key!r}")',
                'raise ClaimPacketError(f"duplicate JSON key: {key!r}")',
                1,
            ),
        },
    )
    rejected(
        "certified fourth execution key",
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source.replace(
                '    "justfile": (',
                '    "README.md": ("0" * 64),\n    "justfile": (',
                1,
            ),
        },
    )
    rejected(
        "certified README moved into execution map",
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source.replace(
                '    "justfile": (',
                '    "scripts/README.md": ("0" * 64),\n    "justfile": (',
                1,
            ),
        },
    )
    rejected(
        "certified audit README authority drift",
        "certified_protocol",
        {
            "anchor_source": anchor_cert_source,
            "candidate_source": candidate_cert_source.replace(
                "61171ae73138570ecede4b1607b04f576807b6e92af1538539b38a0fca21f063",
                "0" * 64,
                1,
            ),
        },
    )
    for label, old, new in (
        (
            "Lean unchanged semantic check shortcut",
            "def check_all() -> None:\n",
            "def check_all() -> None:\n    return\n",
        ),
        (
            "Lean added top-level authority",
            "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 =",
            "UNREVIEWED_LEAN_AUTHORITY = True\nEXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 =",
        ),
        (
            "Lean renamed operational correction slot",
            '    "scripts/check-ksg-m1a-custody-correction.py":',
            '    "scripts/renamed-correction.py":',
        ),
        (
            "Lean generator function semantic shortcut",
            "def check_static_without_receipt() -> None:\n",
            "def check_static_without_receipt() -> None:\n    return\n",
        ),
    ):
        require(
            old in candidate_lean_source, f"Lean hostile source token absent: {label}"
        )
        rejected(
            label,
            "lean_checker_structure",
            {
                "anchor_source": anchor_lean_source,
                "candidate_source": candidate_lean_source.replace(old, new, 1),
            },
        )
    wiring_hostiles = (
        (
            "workflow top-level shell override",
            ".github/workflows/ci.yml",
            "permissions:\n  contents: read\n",
            'defaults:\n  run:\n    shell: "true {0}"\n\npermissions:\n  contents: read\n',
        ),
        (
            "workflow correction marker deleted",
            ".github/workflows/ci.yml",
            "# BEGIN KSG_M1A_CUSTODY_CORRECTION_WORKFLOW_V1",
            "# REMOVED KSG_M1A_CUSTODY_CORRECTION_WORKFLOW_V1",
        ),
        (
            "workflow correction job disabled",
            ".github/workflows/ci.yml",
            "  ksg-harmonic-assurance:\n",
            "  ksg-harmonic-assurance:\n    if: ${{ false }}\n",
        ),
        (
            "workflow event checkout SHA fail-open",
            ".github/workflows/ci.yml",
            "checked-out HEAD does not equal the event-specific exact source SHA",
            "checkout mismatch ignored",
        ),
        (
            "workflow parent resolution weakened",
            ".github/workflows/ci.yml",
            'parent_record="$(git rev-list --parents -n 1 "$head")"',
            'parent_record="$head cb3f58f0b190454cb3f1090de8798261ec78f194"',
        ),
        (
            "workflow candidate optimized gate deleted",
            ".github/workflows/ci.yml",
            "python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \\\n              --mode candidate-commit",
            "true # optimized candidate gate removed \\\n              --mode candidate-commit",
        ),
        (
            "workflow detached hard-failure weakened",
            ".github/workflows/ci.yml",
            "exact direct-child source checkout is unexpectedly attached before candidate validation",
            "attached checkout accepted",
        ),
        (
            "workflow push-main ref weakened",
            ".github/workflows/ci.yml",
            '[[ "$GITHUB_REF" == "refs/heads/main" ]]',
            '[[ "$GITHUB_REF" == refs/heads/* ]]',
        ),
        (
            "workflow postcommit optimized gate deleted",
            ".github/workflows/ci.yml",
            "python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \\\n              --mode postcommit",
            "true # optimized postcommit removed \\\n              --mode postcommit",
        ),
        (
            "workflow no-credit fallback weakened",
            ".github/workflows/ci.yml",
            "strict postcommit replay is not applicable and no credit is granted",
            "strict postcommit replay skipped",
        ),
        (
            "Just correction marker deleted",
            "justfile",
            "# BEGIN KSG_M1A_CUSTODY_CORRECTION_JUST_V1",
            "# REMOVED KSG_M1A_CUSTODY_CORRECTION_JUST_V1",
        ),
        (
            "Just global shell override",
            "justfile",
            "# List available recipes\n",
            'set shell := ["true", "-c"]\n\n# List available recipes\n',
        ),
        (
            "Just duplicate parameterized correction override",
            "justfile",
            "# List available recipes\n",
            "set allow-duplicate-recipes := true\n\n"
            "ksg-revision *args:\n"
            "    true\n\n"
            "# List available recipes\n",
        ),
        (
            "Just correction recipe moved dead",
            "justfile",
            "ksg-revision:\n",
            "dead-ksg-revision:\n",
        ),
        (
            "Just release dependency removed",
            "justfile",
            " ksg-revision ",
            " ",
        ),
        (
            "README composite parser authority weakened",
            "scripts/README.md",
            "The JSON Schema alone is insufficient",
            "The JSON Schema is sufficient",
        ),
        (
            "README correction section moved inside outer code fence",
            "scripts/README.md",
            "<!-- BEGIN KSG_M1A_CUSTODY_CORRECTION_README_V1 -->",
            "```text\n<!-- BEGIN KSG_M1A_CUSTODY_CORRECTION_README_V1 -->",
        ),
        (
            "README local no-credit weakened",
            "scripts/README.md",
            "local_hosted_pending_no_credit",
            "local_success",
        ),
    )
    for label, path, old, new in wiring_hostiles:
        require(old in wiring_sources[path], f"wiring hostile token absent: {label}")
        hostile = copy.deepcopy(wiring_sources)
        hostile[path] = hostile[path].replace(old, new, 1)
        rejected(label, "correction_wiring", hostile)

    malformed_rejected(
        "duplicate key",
        b'{"payload":{},"payload":{},"schema":"'
        + SELF_TEST_SCHEMA.encode()
        + b'","validator":"policy"}\n',
    )
    malformed_rejected("noncanonical", b' {"payload":{}}\n')
    malformed_rejected("invalid UTF-8", b"\xff\n")
    malformed_rejected(
        "oversized integer literal",
        b'{"payload":'
        + b"9" * 5000
        + b',"schema":"'
        + SELF_TEST_SCHEMA.encode()
        + b'","validator":"runtime_mode"}\n',
    )
    malformed_rejected("unknown validator", vector("unknown", {}))
    validate_sealed_index_route()

    if NEGATIVE.exists():
        negative = strict_json(NEGATIVE)
        accepted("negative", negative)
        rejected(
            "negative integer authentication nonclaim",
            "negative",
            mutate(
                negative,
                lambda value: value["capture_boundary"].update(
                    authentication_claimed=0
                ),
            ),
        )
        for label, hostile_scalar in (("boolean", True), ("float", 1.0)):
            rejected(
                f"negative {label} schema revision",
                "negative",
                mutate(
                    negative,
                    lambda value, hostile_scalar=hostile_scalar: value.update(
                        schema_revision=hostile_scalar
                    ),
                ),
            )
        rejected(
            "negative failed run relabeled",
            "negative",
            mutate(
                negative, lambda value: value["ci_failure"].update(conclusion="success")
            ),
        )
        rejected(
            "negative roster deletion",
            "negative",
            mutate(negative, lambda value: value["ci_failure"]["job_roster"].pop()),
        )
        rejected(
            "negative CodeQL head",
            "negative",
            mutate(
                negative,
                lambda value: value["codeql_success"].update(head_sha="0" * 40),
            ),
        )
        rejected(
            "negative provider authenticity",
            "negative",
            mutate(
                negative,
                lambda value: value["capture_boundary"].update(
                    authentication_claimed=True
                ),
            ),
        )
        rejected(
            "negative root extension",
            "negative",
            mutate(negative, lambda value: value.update(unreviewed=True)),
        )
        rejected(
            "negative duplicate CodeQL job id",
            "negative",
            mutate(
                negative,
                lambda value: value["codeql_success"]["job_roster"][1].update(
                    job_id=value["codeql_success"]["job_roster"][0]["job_id"]
                ),
            ),
        )
        rejected(
            "negative capture digest swap",
            "negative",
            mutate(
                negative,
                lambda value: value["capture_boundary"]["api_responses"][0].update(
                    sha256="0" * 64
                ),
            ),
        )
        rejected(
            "negative alert extrema",
            "negative",
            mutate(
                negative,
                lambda value: value["codeql_success"]["alert_state"].update(
                    maximum_alert_number=190
                ),
            ),
        )
        resealed = mutate(
            negative,
            lambda value: value["ci_failure"]["job_roster"][0].update(
                started_at="2020-01-01T00:00:00Z",
                completed_at="2020-01-01T00:00:00Z",
            ),
        )
        roster = resealed["ci_failure"]["job_roster"]
        roster_raw = canonical_json(roster, pretty=False)
        roster_digest = hashlib.sha256(roster_raw).hexdigest()
        resealed["ci_failure"]["job_roster_projection"]["sha256"] = roster_digest
        for capture_owner in (
            resealed["ci_failure"]["api_captures"],
            resealed["capture_boundary"]["api_responses"],
        ):
            capture = next(
                item
                for item in capture_owner
                if item["endpoint_class"] == "ci_job_step_roster"
            )
            capture["projection"] = copy.deepcopy(roster)
            capture["sha256"] = roster_digest
            capture["size_bytes"] = len(roster_raw)
        rejected("negative coordinated roster reseal", "negative", resealed)

        composite = composite_fixture(negative)
        accepted("composite_receipt_semantics", composite)
        for label, operation in (
            (
                "composite integer receipt self-hash nonclaim",
                lambda value: value["acyclic_boundary"].update(receipt_hashes_itself=0),
            ),
            (
                "composite integer remote authentication nonclaim",
                lambda value: value["remote_observations"].update(
                    authentication_claimed=0
                ),
            ),
            (
                "composite integer absent decision flag",
                lambda value: value["revision4_integration"].update(
                    decision_v4_absent_at_correction=1
                ),
            ),
            (
                "composite integer protected equality flag",
                lambda value: value["implementation_anchor"][
                    "protected_projection"
                ].update(candidate_equals_anchor=1),
            ),
        ):
            rejected(
                label,
                "composite_receipt_semantics",
                mutate(composite, operation),
            )
        for label, owner, field, hostile_scalar in (
            (
                "composite refreshed integer CI pagination flag",
                "implementation_ci_failure",
                "pagination_complete",
                1,
            ),
            (
                "composite refreshed integer CodeQL authenticity flag",
                "implementation_codeql_success",
                "runner_authenticity_claimed",
                0,
            ),
        ):
            hosted_bool = copy.deepcopy(composite)
            hosted_bool["hosted_observations"][owner][field] = hostile_scalar
            if owner.endswith("ci_failure"):
                refresh_ci_observation(hosted_bool["hosted_observations"][owner])
            else:
                refresh_codeql_observation(hosted_bool["hosted_observations"][owner])
            rejected(label, "composite_receipt_semantics", hosted_bool)
        float_hostiles: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
            (
                "composite float root schema revision",
                lambda value: value.update(schema_revision=2.0),
            ),
            (
                "composite float claim revision",
                lambda value: value["claim"].update(revision=4.0),
            ),
            (
                "composite float integration open-gate count",
                lambda value: value["revision4_integration"].update(
                    open_gate_count=13.0
                ),
            ),
            (
                "composite float protected projection count",
                lambda value: value["implementation_anchor"][
                    "protected_projection"
                ].update(entry_count=83.0),
            ),
            (
                "composite float CI projection count",
                lambda value: value["hosted_observations"]["implementation_ci_failure"][
                    "job_roster_projection"
                ].update(entry_count=45.0),
            ),
            (
                "composite float API capture size",
                lambda value: value["hosted_observations"]["implementation_ci_failure"][
                    "api_captures"
                ][0].update(
                    size_bytes=float(
                        value["hosted_observations"]["implementation_ci_failure"][
                            "api_captures"
                        ][0]["size_bytes"]
                    )
                ),
            ),
            (
                "composite float failed diagnostic step",
                lambda value: value["hosted_observations"]["implementation_ci_failure"][
                    "failed_diagnostic"
                ].update(step_number=22.0),
            ),
            (
                "composite float phase negative run ID",
                lambda value: value["local_phase_custody"]["precommit_outputs"][
                    "normal"
                ]["output"]["negative_evidence"].update(codeql_run_id=31686106737.0),
            ),
            (
                "composite float phase protected count",
                lambda value: value["local_phase_custody"]["postcommit_outputs"][
                    "optimized"
                ]["output"]["implementation_anchor"]["protected_projection"].update(
                    entry_count=83.0
                ),
            ),
        )
        for label, operation in float_hostiles:
            rejected(
                label,
                "composite_receipt_semantics",
                mutate(composite, operation),
            )
        for label, owner, field, hostile_scalar in (
            (
                "composite CI boolean attempt",
                "implementation_ci_failure",
                "attempt",
                True,
            ),
            ("composite CI float attempt", "implementation_ci_failure", "attempt", 1.0),
            (
                "composite CodeQL boolean attempt",
                "implementation_codeql_success",
                "attempt",
                True,
            ),
            (
                "composite CodeQL float attempt",
                "implementation_codeql_success",
                "attempt",
                1.0,
            ),
            (
                "composite CodeQL boolean new-alert count",
                "implementation_codeql_success",
                "new_alerts",
                False,
            ),
            (
                "composite CodeQL float new-alert count",
                "implementation_codeql_success",
                "new_alerts",
                0.0,
            ),
            (
                "composite CI boolean failed-job count",
                "implementation_ci_failure",
                "failed_job_count",
                True,
            ),
            (
                "composite CI float failed-job count",
                "implementation_ci_failure",
                "failed_job_count",
                1.0,
            ),
        ):
            typed_hostile = copy.deepcopy(composite)
            typed_hostile["hosted_observations"][owner][field] = hostile_scalar
            if owner.endswith("ci_failure"):
                refresh_ci_observation(typed_hostile["hosted_observations"][owner])
            else:
                refresh_codeql_observation(typed_hostile["hosted_observations"][owner])
            rejected(
                label,
                "composite_receipt_semantics",
                typed_hostile,
            )
        rejected(
            "composite cross-head marker",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["hosted_observations"].update(
                    correction_heads_equal=False
                ),
            ),
        )
        rejected(
            "composite correction tree split",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["custody_correction"].update(tree="0" * 40),
            ),
        )
        rejected(
            "composite run identity overlap",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["hosted_observations"][
                    "correction_codeql_success"
                ].update(
                    run_id=value["hosted_observations"]["correction_ci_success"][
                        "run_id"
                    ]
                ),
            ),
        )
        duplicate_job = mutate(
            composite,
            lambda value: value["hosted_observations"]["correction_ci_success"][
                "job_roster"
            ][0].update(
                job_id=value["hosted_observations"]["implementation_ci_failure"][
                    "job_roster"
                ][0]["job_id"]
            ),
        )
        refresh_ci_observation(
            duplicate_job["hosted_observations"]["correction_ci_success"]
        )
        rejected(
            "composite job identity overlap",
            "composite_receipt_semantics",
            duplicate_job,
        )
        duplicate_analysis = mutate(
            composite,
            lambda value: value["hosted_observations"]["correction_codeql_success"][
                "analysis_roster"
            ][0].update(
                analysis_id=value["hosted_observations"][
                    "implementation_codeql_success"
                ]["analysis_roster"][0]["analysis_id"]
            ),
        )
        refresh_codeql_observation(
            duplicate_analysis["hosted_observations"]["correction_codeql_success"]
        )
        rejected(
            "composite analysis identity overlap",
            "composite_receipt_semantics",
            duplicate_analysis,
        )
        duplicate_artifact = mutate(
            composite,
            lambda value: value["hosted_observations"]["correction_ci_success"][
                "postcommit_source_state_v2"
            ].update(
                artifact_id=value["hosted_observations"]["implementation_ci_failure"][
                    "postcommit_source_state_v2"
                ]["artifact_id"]
            ),
        )
        refresh_ci_observation(
            duplicate_artifact["hosted_observations"]["correction_ci_success"]
        )
        rejected(
            "composite artifact identity overlap",
            "composite_receipt_semantics",
            duplicate_artifact,
        )
        rejected(
            "composite capture digest reseal",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["hosted_observations"]["correction_ci_success"][
                    "api_captures"
                ][0].update(sha256="0" * 64),
            ),
        )
        rejected(
            "composite projection digest reseal",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["hosted_observations"]["correction_ci_success"][
                    "job_roster_projection"
                ].update(sha256="0" * 64),
            ),
        )
        coordinated_reseal = mutate(
            composite,
            lambda value: value["hosted_observations"]["implementation_ci_failure"][
                "job_roster"
            ][0].update(
                started_at="2020-01-01T00:00:00Z",
                completed_at="2020-01-01T00:00:00Z",
            ),
        )
        refresh_ci_observation(
            coordinated_reseal["hosted_observations"]["implementation_ci_failure"]
        )
        rejected(
            "composite coordinated implementation projection reseal",
            "composite_receipt_semantics",
            coordinated_reseal,
        )
        rejected(
            "composite alert extrema",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["hosted_observations"]["correction_codeql_success"][
                    "alert_state"
                ].update(maximum_alert_number=190),
            ),
        )
        new_alert = copy.deepcopy(composite)
        new_alert_run = new_alert["hosted_observations"]["correction_codeql_success"]
        new_alert_state = new_alert_run["alert_state"]
        new_alert_state["new_alert_numbers"] = [192]
        new_alert_state["observed_new_alerts"] = 1
        new_alert_state["open_alert_numbers"].append(192)
        new_alert_state["observed_alert_numbers"].append(192)
        new_alert_state["open"] += 1
        new_alert_state["total"] += 1
        new_alert_state["maximum_alert_number"] = 192
        new_alert_run["new_alerts"] = 1
        refresh_codeql_observation(new_alert_run)
        rejected(
            "composite observed new alert", "composite_receipt_semantics", new_alert
        )
        rejected(
            "composite local artifact path",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["local_phase_custody"]["checker"].update(
                    path="scripts/renamed.py"
                ),
            ),
        )
        rejected(
            "composite alternate index count bound",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["local_phase_custody"]["alternate_index"].update(
                    entry_count=0
                ),
            ),
        )
        rejected(
            "composite boolean alternate integer",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["local_phase_custody"]["alternate_index"].update(
                    size_bytes=True
                ),
            ),
        )
        rejected(
            "composite integer correction boolean",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["custody_correction"].update(one_parent=1),
            ),
        )
        rejected(
            "composite phase output shape",
            "composite_receipt_semantics",
            mutate(
                composite,
                lambda value: value["local_phase_custody"]["precommit_outputs"][
                    "normal"
                ]["output"].pop("preclosure"),
            ),
        )
        phase_drift = mutate(
            composite,
            lambda value: value["local_phase_custody"]["postcommit_outputs"][
                "optimized"
            ]["output"]["child_output_sha256"].update(
                {"scripts/check-lean-toolchain-freeze.py": "0" * 64}
            ),
        )
        drift_output = phase_drift["local_phase_custody"]["postcommit_outputs"][
            "optimized"
        ]["output"]
        phase_drift["local_phase_custody"]["postcommit_outputs"]["optimized"][
            "sha256"
        ] = hashlib.sha256(canonical_json(drift_output, pretty=False)).hexdigest()
        rejected(
            "composite coordinated phase-output reseal",
            "composite_receipt_semantics",
            phase_drift,
        )
        four_policy_reseal = copy.deepcopy(composite)
        mutate_all_phase_outputs(
            four_policy_reseal,
            lambda output: output.update(policy_sha256="0" * 64),
        )
        rejected(
            "composite coordinated four-output policy reseal",
            "composite_receipt_semantics",
            four_policy_reseal,
        )
        four_current_source_reseal = copy.deepcopy(composite)
        mutate_all_phase_outputs(
            four_current_source_reseal,
            lambda output: output.update(current_source_manifest_sha256="0" * 64),
        )
        rejected(
            "composite coordinated four-output current-source reseal",
            "composite_receipt_semantics",
            four_current_source_reseal,
        )
        for label, operation in (
            (
                "composite coordinated four-output integer preclosure flag",
                lambda output: output["preclosure"].update(
                    future_composite_receipt_absent=1
                ),
            ),
            (
                "composite coordinated four-output integer projection flag",
                lambda output: output["implementation_anchor"][
                    "protected_projection"
                ].update(candidate_equals_anchor=1),
            ),
        ):
            four_bool_alias = copy.deepcopy(composite)
            mutate_all_phase_outputs(four_bool_alias, operation)
            rejected(
                label,
                "composite_receipt_semantics",
                four_bool_alias,
            )
        four_envelope_reseal = copy.deepcopy(composite)
        hostile_message = FIXTURE_CORRECTION_MESSAGE.replace("7" * 64, "8" * 64)
        for phase in ("precommit", "postcommit"):
            for label in ("normal", "optimized"):
                envelope = four_envelope_reseal["local_phase_custody"][
                    f"{phase}_outputs"
                ][label]["output"]["candidate"]["commit_envelope"]
                envelope.update(
                    message=hostile_message,
                    sealed_index_sha256="8" * 64,
                )
        reseal_phase_outputs(four_envelope_reseal)
        rejected(
            "composite coordinated four-output commit-envelope reseal",
            "composite_receipt_semantics",
            four_envelope_reseal,
        )
        for label, hostile_scalar in (
            ("boolean", True),
            ("float", 1.0),
        ):
            four_typed_negative = copy.deepcopy(composite)
            mutate_all_phase_outputs(
                four_typed_negative,
                lambda output, hostile_scalar=hostile_scalar: output[
                    "negative_evidence"
                ].update(failed_jobs=hostile_scalar),
            )
            rejected(
                f"composite coordinated four-output {label} failed-job count",
                "composite_receipt_semantics",
                four_typed_negative,
            )
        four_child_reseal = copy.deepcopy(composite)
        mutate_all_phase_outputs(
            four_child_reseal,
            lambda output: output["child_output_sha256"].update(
                {"scripts/check-certified-sxpid2-claim.py": "0" * 64}
            ),
        )
        rejected(
            "composite coordinated four-output child reseal",
            "composite_receipt_semantics",
            four_child_reseal,
        )
        four_static_reseal = copy.deepcopy(composite)
        mutate_all_phase_outputs(
            four_static_reseal,
            lambda output: output["static_artifact_sha256"].update(
                {
                    "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md": "0"
                    * 64
                }
            ),
        )
        rejected(
            "composite coordinated four-output static reseal",
            "composite_receipt_semantics",
            four_static_reseal,
        )
        four_delta_reseal = copy.deepcopy(composite)
        mutate_all_phase_outputs(
            four_delta_reseal,
            lambda output: output["candidate"].update(
                delta=[{"mode": "100644", "path": "AGENTS.md", "status": "M"}]
            ),
        )
        rejected(
            "composite coordinated four-output delta reseal",
            "composite_receipt_semantics",
            four_delta_reseal,
        )
        alternate_reseal = copy.deepcopy(composite)
        alternate_reseal["local_phase_custody"]["alternate_index"]["sha256"] = "0" * 64
        for label in ("normal", "optimized"):
            alternate_reseal["local_phase_custody"]["precommit_outputs"][label][
                "output"
            ]["candidate"]["alternate_index_custody"]["sha256"] = "0" * 64
        reseal_phase_outputs(alternate_reseal)
        rejected(
            "composite coordinated alternate-index reseal",
            "composite_receipt_semantics",
            alternate_reseal,
        )

        production = invoke(
            ["--validate-composite-receipt"],
            stdin=canonical_json(composite, pretty=True),
        )
        require(
            production.returncode != 0
            and not production.stdout
            and b"Traceback" not in production.stderr
            and production.stderr.startswith(
                b"KSG M1a custody-correction check failed: "
            ),
            "production composite CLI accepted a semantic-only fixture or leaked a traceback/output",
        )
    else:
        require(
            state == "provisional",
            "frozen correction suite requires retained negative evidence",
        )

    # Production policy-only must remain red until the coordinated policy freezes;
    # the explicit diagnostic succeeds and grants no credit.
    plain = invoke(["--validate-policy-only"])
    flagged = invoke(["--validate-policy-only", "--allow-provisional-diagnostic"])
    selected = flagged if state == "provisional" else plain
    require(
        selected.returncode == 0 and not selected.stderr,
        f"state-appropriate policy validation failed: {selected.stderr!r}",
    )
    rejected_mode = plain if state == "provisional" else flagged
    require(
        rejected_mode.returncode != 0 and not rejected_mode.stdout,
        "wrong provisional/frozen policy CLI disposition succeeded",
    )
    report = json.loads(selected.stdout)
    expected_credit = (
        "none_policy_inventory_provisional"
        if state == "provisional"
        else "none_policy_frozen_lifecycle_validation_only"
    )
    require(
        report.get("credit") == expected_credit
        and report.get("disposition") == "local_hosted_pending_no_credit"
        and report.get("protected_projection")
        == {
            "entry_count": 83,
            "sha256": "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843",
        },
        "policy diagnostic overcredited or lost protected projection",
    )
    require(
        stable_source_snapshot(CHECKER)
        == (checker_source_snapshot, checker_path_identity)
        and stable_source_snapshot(SCRIPT)
        == (self_test_source_snapshot, self_test_path_identity),
        "checker/self-test source changed across the hostile suite",
    )
    print("OK: KSG M1a custody-correction CLI hostile suite passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        SelfTestError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"KSG M1a custody-correction self-test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
