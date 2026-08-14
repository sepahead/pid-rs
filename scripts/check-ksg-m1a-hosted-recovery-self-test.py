#!/usr/bin/env python3
"""CLI-only hostile tests for the KSG M1a hosted-recovery checker."""

# ruff: noqa: E402 -- the isolation guard intentionally precedes imports.

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
        "ERROR: check-ksg-m1a-hosted-recovery-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Callable


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-ksg-m1a-hosted-recovery.py"
POLICY = ROOT / "audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json"
BOUNDARY = ROOT / "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md"
LEAN_R7 = (
    ROOT
    / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json"
)
ACTIVE_PACKET = ROOT / "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
CURRENT_SOURCE = ROOT / "audit/evidence/current-source-state-v1.json"
IMPLEMENTATION = "cb3f58f0b190454cb3f1090de8798261ec78f194"
CORRECTION = "7473e62acef6077c2c1147e09d5d1297f2a2874b"
CORRECTION_TREE = "d0b2613e678a89318550c1797ba9cc59a4ec9478"
PROTECTED_SHA = "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843"
R6_SHA = "f14e7a33c01909055cc868fc955e6b2520ae15ebf0d598730911ec57a7f4c5ea"
R7_SHA = "3dd2df7d7064bac93cf4806cdeac28d9ecc747444689162a4636029228822abb"
ACTIVE_PACKET_SHA = "360e070d2f92e141e0f1ab672e6f6dd8a8d41bc1f193b735cae93d44ed8ab32e"
EMPTY_TRACKED_RELATIVE = (
    "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout"
)
EMPTY_BLOB_OID = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
RETIRED_RECOVERY_CHECKPOINT = "37473f8fa9470fcec0bd419ec3df18ea4a6d805b"
RETIRED_RECOVERY_TREE = "66f33f467f2bc661795599fa53ef81681ecd8406"
RETIRED_RECOVERY_INDEX_SHA256 = (
    "fb892aeaac2091e1d4c6b619a4ce0053771d8aeb0ee147105017613a3b46a56d"
)
SELF_TEST_SCHEMA = "pid-rs/ksg-rev4-m1a-hosted-recovery-self-test-vector/v1"
PASS = b'{"result":"pass"}\n'
FAIL = b'{"result":"fail"}\n'
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_REQUEST_BYTES = 24 * 1024 * 1024
PYTHON_CHILD_PREFIX = (
    (sys.executable, "-O", "-I", "-S", "-B")
    if sys.flags.optimize == 1
    else (sys.executable, "-I", "-S", "-B")
)

EXPECTED_OPTIONS = {
    "--allow-provisional-diagnostic",
    "--alternate-index-entry-count",
    "--alternate-index-sha256",
    "--checkpoint-commit",
    "--expected-candidate-tree",
    "--mode",
    "--self-test-vectors",
    "--validate-composite-receipt",
    "--validate-policy-only",
}
EXPECTED_IMPORTS = {
    "argparse",
    "ast",
    "copy",
    "dataclasses",
    "datetime",
    "fcntl",
    "hashlib",
    "json",
    "os",
    "pathlib",
    "re",
    "stat",
    "subprocess",
    "sys",
    "tempfile",
    "typing",
    "__future__",
}

EXPECTED_BOOLEAN_FIELDS = {
    "all_green_applies_only_to_recovery_head",
    "all_jobs_successful",
    "authentication_claimed",
    "author_and_committer_headers_identical",
    "candidate_equals_anchor",
    "causation_claimed",
    "commit_message_trailer_matches",
    "correction_heads_equal",
    "credit_permitted",
    "current_manifest_checker_passed",
    "decision_v4_absent_at_recovery",
    "deletions_permitted",
    "distinct_from_correction",
    "distinct_from_implementation_anchor",
    "evidence_matrix_v4_absent_at_recovery",
    "expired",
    "failed_correction_ci_must_remain_failed",
    "failed_correction_codeql_must_remain_separate",
    "final_decision_absent",
    "final_evidence_matrix_absent",
    "future_composite_receipt_absent",
    "future_retained_indexes_absent",
    "head_tree_matches_index",
    "implementation_heads_equal",
    "input_descriptor_read_only",
    "later_descendant_required",
    "lifecycle_validation_permitted",
    "manifest_is_tracked_head_blob",
    "mechanical_resealing_permitted",
    "no_new_alerts_observed",
    "one_parent",
    "pagination_complete",
    "pair_normalized_equal",
    "path_or_residency_claimed",
    "post_commit_checker_is_tracked_head_blob",
    "post_commit_schema_is_tracked_head_blob",
    "precommit_descriptor_observation_authenticated",
    "reconstructs_tree_twice",
    "recovery_heads_equal",
    "recovery_subject_must_not_contain_receipt",
    "recovery_subject_must_not_contain_retained_indexes",
    "remains_implementation_after_recovery",
    "repeated_endpoint_observations_match",
    "repetitions_equal",
    "retained_negative_evidence",
    "runner_authenticity_claimed",
    "scientific_authority_unchanged",
    "self_excluding_projection_matches_head_tree",
    "signature_headers_permitted",
    "single_link",
    "three_subject_heads_distinct",
    "tracked_worktree_matches_head",
    "truncated",
    "trusted_time_claimed",
    "unsigned",
    "workflow_fetch_depth_zero",
}
EXPECTED_INTEGER_FIELDS = {
    "alert_number",
    "analysis_id",
    "archive_size_bytes",
    "artifact_id",
    "attempt",
    "ci_attempt",
    "ci_run_id",
    "codeql_attempt",
    "codeql_run_id",
    "content_size_bytes",
    "dismissed",
    "entry_count",
    "failed_ci_run_id",
    "failed_job_count",
    "failed_jobs",
    "fixed",
    "job_id",
    "jobs_successful",
    "jobs_total",
    "log_size_bytes",
    "maximum_alert_number",
    "minimum_alert_number",
    "new_alerts",
    "number",
    "observed_new_alerts",
    "open",
    "open_gate_count",
    "parent_count",
    "results_count",
    "rules_count",
    "run_id",
    "runtime_mode",
    "sealed_index_size_bytes",
    "size_bytes",
    "size_in_bytes",
    "source_projection_entry_count",
    "step_number",
    "total",
}
EXPECTED_INTEGER_LIST_FIELDS = {
    "baseline_alert_numbers",
    "dismissed_alert_numbers",
    "fixed_alert_numbers",
    "new_alert_numbers",
    "observed_alert_numbers",
    "open_alert_numbers",
}

CHECKER_STDIN_BOOTSTRAP = """import hashlib
import os
import stat
import sys
import tempfile

PREFIX = "hosted-recovery checker stdin launcher failed: "
MAX_SOURCE = 4 * 1024 * 1024
MAX_REQUEST = 24 * 1024 * 1024

def fail(message):
    print(PREFIX + message, file=sys.stderr)
    raise SystemExit(2)

def size(text, maximum, label, zero):
    if not text.isascii() or not text.isdecimal() or (text != "0" and text.startswith("0")):
        fail(label + " size is not canonical decimal")
    value = int(text, 10)
    if value > maximum or (not zero and value == 0):
        fail(label + " size is outside bound")
    return value

def digest(text, label):
    if len(text) != 64 or any(item not in "0123456789abcdef" for item in text):
        fail(label + " digest malformed")
    return text

def exact(count, label):
    chunks = []
    remaining = count
    while remaining:
        chunk = os.read(0, min(remaining, 65536))
        if not chunk:
            fail(label + " frame short")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)

if len(sys.argv) < 7:
    fail("argument inventory differs")
logical_file, logical_root = sys.argv[1], sys.argv[2]
if not os.path.isabs(logical_root) or os.path.realpath(logical_root) != logical_root or os.path.realpath(os.getcwd()) != logical_root:
    fail("logical root differs")
if logical_file != os.path.join(logical_root, "scripts", "check-ksg-m1a-hosted-recovery.py"):
    fail("logical file differs")
source_size = size(sys.argv[3], MAX_SOURCE, "source", False)
source_sha = digest(sys.argv[4], "source")
request_size = size(sys.argv[5], MAX_REQUEST, "request", True)
request_sha = digest(sys.argv[6], "request")
arguments = sys.argv[7:]
source = exact(source_size, "source")
request = exact(request_size, "request")
if hashlib.sha256(source).hexdigest() != source_sha or hashlib.sha256(request).hexdigest() != request_sha:
    fail("framed digest differs")
if os.read(0, 1) != b"":
    fail("trailing input")
temp_root = os.path.realpath("/tmp")
temp_state = os.lstat(temp_root)
if not (os.path.isabs(temp_root) and stat.S_ISDIR(temp_state.st_mode) and temp_state.st_uid == 0 and bool(temp_state.st_mode & stat.S_ISVTX)):
    fail("temporary root differs")
holder = tempfile.TemporaryDirectory(prefix="pid-rs-recovery-stdin-", dir=temp_root)
os.chmod(holder.name, 0o700)
request_path = os.path.join(holder.name, "request")
descriptor = os.open(request_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600)
offset = 0
while offset < len(request):
    written = os.write(descriptor, request[offset:])
    if written <= 0:
        fail("request write short")
    offset += written
os.fsync(descriptor)
os.close(descriptor)
os.chmod(request_path, 0o400)
descriptor = os.open(request_path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
before = os.fstat(descriptor)
if not (stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o400 and before.st_nlink == 1 and before.st_size == len(request)):
    fail("request descriptor custody differs")
staged_chunks = []
remaining = len(request)
while remaining:
    chunk = os.read(descriptor, min(remaining, 65536))
    if not chunk:
        fail("staged request frame short")
    staged_chunks.append(chunk)
    remaining -= len(chunk)
staged = b"".join(staged_chunks)
if os.read(descriptor, 1) != b"":
    fail("staged request grew")
os.lseek(descriptor, 0, os.SEEK_SET)
if staged != request:
    fail("staged request differs")
os.dup2(descriptor, 0)
if descriptor != 0:
    os.close(descriptor)
sys.stdin = open(0, "r", encoding="utf-8", errors="strict", closefd=False)
os.chdir(logical_root)
sys.argv = [logical_file, *arguments]
namespace = {"__builtins__": __builtins__, "__cached__": None, "__file__": logical_file, "__name__": "__main__", "__package__": None, "__spec__": None}
exec(compile(source, logical_file, "exec", dont_inherit=True), namespace)
"""


class SelfTestError(RuntimeError):
    """The hostile suite observed an unexpected result."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def canonical(value: Any, *, pretty: bool = True) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


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


def stable_read(path: Path) -> tuple[bytes, tuple[int, ...]]:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        before = os.fstat(descriptor)
        path_before = path.lstat()
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= MAX_SOURCE_BYTES
            and identity(before) == identity(path_before),
            f"source custody invalid: {path}",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65536))
            require(bool(chunk), f"source short read: {path}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"source grew: {path}")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    require(
        identity(before) == identity(after) == identity(path.lstat()),
        f"source changed during read: {path}",
    )
    return b"".join(chunks), identity(after)


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


CHECKER_SOURCE: bytes | None = None


def invoke(
    arguments: list[str], request: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    source = CHECKER_SOURCE
    require(source is not None, "checker source snapshot not initialized")
    require(
        len(source) <= MAX_SOURCE_BYTES and len(request) <= MAX_REQUEST_BYTES,
        "framed input exceeds bound",
    )
    completed = subprocess.run(
        [
            *PYTHON_CHILD_PREFIX,
            "-c",
            CHECKER_STDIN_BOOTSTRAP,
            os.fspath(CHECKER),
            os.fspath(ROOT),
            str(len(source)),
            hashlib.sha256(source).hexdigest(),
            str(len(request)),
            hashlib.sha256(request).hexdigest(),
            *arguments,
        ],
        cwd=ROOT,
        env=safe_environment(),
        input=source + request,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=240,
        check=False,
    )
    require(
        len(completed.stdout) <= 4 * 1024 * 1024
        and len(completed.stderr) <= 4 * 1024 * 1024,
        "checker output exceeded bound",
    )
    return completed


def vector(validator: str, payload: Any) -> bytes:
    return canonical(
        {"payload": payload, "schema": SELF_TEST_SCHEMA, "validator": validator}
    )


def accepted(validator: str, payload: Any) -> None:
    completed = invoke(["--self-test-vectors"], vector(validator, payload))
    require(
        completed.returncode == 0 and completed.stdout == PASS and not completed.stderr,
        f"accepted vector failed: {validator}: {completed.stderr!r}",
    )


def rejected(label: str, validator: str, payload: Any) -> None:
    completed = invoke(["--self-test-vectors"], vector(validator, payload))
    require(
        completed.returncode == 0 and completed.stdout == FAIL and not completed.stderr,
        f"hostile vector escaped: {label}: {completed.stdout!r} {completed.stderr!r}",
    )


def malformed_rejected(label: str, raw: bytes) -> None:
    try:
        completed = invoke(["--self-test-vectors"], raw)
    except SelfTestError:
        require(
            len(raw) > MAX_REQUEST_BYTES,
            f"transport rejected in-bound request: {label}",
        )
        return
    require(
        completed.returncode == 0 and completed.stdout == FAIL and not completed.stderr,
        f"malformed request escaped: {label}",
    )


def mutate(value: Any, operation: Callable[[Any], None]) -> Any:
    result = copy.deepcopy(value)
    operation(result)
    return result


def update_all_package_revisions(value: dict[str, Any], replacement: Any) -> None:
    for package in value["package_pins"].values():
        package["revision"] = copy.deepcopy(replacement)


def observed_field_kinds(
    values: tuple[Any, ...], fields: set[str]
) -> dict[str, set[str]]:
    observed = {field: set() for field in fields}
    pending = list(values)
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                if key in observed:
                    if type(child) is bool:
                        kind = "bool"
                    elif type(child) is int:
                        kind = "int"
                    elif isinstance(child, list):
                        kind = "list"
                    elif isinstance(child, dict):
                        kind = "object"
                    else:
                        kind = type(child).__name__
                    observed[key].add(kind)
                pending.append(child)
        elif isinstance(item, list):
            pending.extend(item)
    return observed


def replace_once_field(value: dict[str, Any], field: str, old: str, new: str) -> None:
    text = value[field]
    require(
        isinstance(text, str) and text.count(old) == 1,
        f"fixture replacement is not unique: {field}: {old!r}",
    )
    value[field] = text.replace(old, new, 1)


def checker_literal(name: str) -> Any:
    source = CHECKER_SOURCE
    require(source is not None, "checker source snapshot not initialized")
    tree = ast.parse(source.decode("utf-8"), filename=os.fspath(CHECKER))
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        )
    ]
    require(len(matches) == 1, f"checker constant not unique: {name}")
    return ast.literal_eval(matches[0].value)


def git_show(path: str) -> bytes:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "--no-optional-locks",
            "-c",
            "core.attributesFile=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.ignoreCase=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "diff.external=",
            "show",
            f"{CORRECTION}:{path}",
        ],
        cwd=ROOT,
        env=safe_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    require(
        completed.returncode == 0 and not completed.stderr,
        f"cannot read correction fixture: {path}",
    )
    return completed.stdout


def terminal_negative_fixture() -> dict[str, Any]:
    path = (
        ROOT
        / "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json"
    )
    require(path.is_file(), "committed terminal negative fixture is absent")
    return json.loads(path.read_bytes())


def static_custody(checker_raw: bytes, selftest_raw: bytes) -> None:
    forbidden_imports = {"importlib", "runpy"}
    forbidden_calls = {"__import__", "eval"}
    options: set[str] = set()
    abbreviations_disabled = False
    for path, raw in ((CHECKER, checker_raw), (SCRIPT, selftest_raw)):
        tree = ast.parse(raw.decode("utf-8", errors="strict"), filename=os.fspath(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            require(
                not isinstance(node, ast.Assert),
                f"optimization-sensitive assert in {path}",
            )
            if isinstance(node, ast.Import):
                imports.update(alias.name.partition(".")[0] for alias in node.names)
                require(
                    not imports & forbidden_imports, f"dynamic loader import in {path}"
                )
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").partition(".")[0])
                require(
                    (node.module or "").partition(".")[0] not in forbidden_imports,
                    f"dynamic loader import in {path}",
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    require(
                        node.func.id not in forbidden_calls,
                        f"dynamic code call in {path}",
                    )
                elif isinstance(node.func, ast.Attribute) and path == CHECKER:
                    if node.func.attr == "ArgumentParser":
                        abbreviations_disabled = any(
                            keyword.arg == "allow_abbrev"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is False
                            for keyword in node.keywords
                        )
                    elif node.func.attr == "add_argument" and node.args:
                        option = node.args[0]
                        if isinstance(option, ast.Constant) and isinstance(
                            option.value, str
                        ):
                            options.add(option.value)
        require(
            imports <= EXPECTED_IMPORTS,
            f"unexpected import surface in {path}: {imports - EXPECTED_IMPORTS}",
        )
    require(options == EXPECTED_OPTIONS, "checker CLI option inventory changed")
    require(abbreviations_disabled, "checker CLI abbreviations enabled")
    bootstrap_tree = ast.parse(CHECKER_STDIN_BOOTSTRAP, filename="<stdin-bootstrap>")
    calls = {
        node.func.id
        for node in ast.walk(bootstrap_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(
        {"compile", "exec"} <= calls
        and CHECKER_STDIN_BOOTSTRAP.count("exec(compile(") == 1
        and CHECKER_STDIN_BOOTSTRAP.count("os.dup2(descriptor, 0)") == 1,
        "stdin bootstrap exact-source transport changed",
    )


def recovery_message(
    tree: str = "2" * 40, digest: str = "7" * 64, size: str = "32768"
) -> bytes:
    timestamp = "1786640000"
    return (
        f"tree {tree}\n"
        f"parent {CORRECTION}\n"
        f"author Sepehr Mahmoudian <sepmhn@gmail.com> {timestamp} +0200\n"
        f"committer Sepehr Mahmoudian <sepmhn@gmail.com> {timestamp} +0200\n\n"
        "Repair KSG M1a hosted recovery wiring\n\n"
        f"Sealed-index-SHA256: {digest}\n"
        f"Sealed-index-Size: {size}\n"
    ).encode("utf-8")


def tree_oid(raw: bytes) -> str:
    return hashlib.sha1(f"tree {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def raw_tree_fixture(*, empty: bool = False, repeated: bool = False) -> dict[str, Any]:
    blob_a = "1" * 40
    blob_b = "2" * 40
    nested_raw = b"" if empty else b"100644 leaf.txt\0" + bytes.fromhex(blob_b)
    nested_oid = tree_oid(nested_raw)
    root_raw = (
        b"100644 a.txt\0"
        + bytes.fromhex(blob_a)
        + b"40000 nested\0"
        + bytes.fromhex(nested_oid)
    )
    expected: dict[str, Any] = {
        "a.txt": {"mode": "100644", "oid": blob_a},
    }
    if not empty:
        expected["nested/leaf.txt"] = {"mode": "100644", "oid": blob_b}
    if repeated:
        root_raw += b"40000 repeated\0" + bytes.fromhex(nested_oid)
        expected["repeated/leaf.txt"] = {"mode": "100644", "oid": blob_b}
    root_oid = tree_oid(root_raw)
    return {
        "expected": expected,
        "objects": {root_oid: root_raw.hex(), nested_oid: nested_raw.hex()},
        "root": root_oid,
    }


def workflow_fixture() -> tuple[str, str]:
    anchor = (
        "  certified-sxpid-reference:\n"
        "    steps:\n"
        "      - uses: actions/checkout@fixed\n"
        "        with:\n"
        "          persist-credentials: false\n"
        "  next-job:\n"
    )
    candidate = anchor.replace(
        "          persist-credentials: false\n",
        "          fetch-depth: 0\n          persist-credentials: false\n",
    )
    return anchor, candidate


def policy_fixture() -> dict[str, Any]:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def historical_correction_output(mode: str, optimize: int) -> dict[str, Any]:
    require(mode in {"precommit", "postcommit"}, "historical phase mode invalid")
    require(optimize in {0, 1}, "historical optimization mode invalid")
    old_policy = json.loads(
        git_show("audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json")
    )
    delta = [
        {"mode": "100644", "path": row["path"], "status": row["status"]}
        for row in old_policy["entries"]
    ]
    alternate = {
        "entry_count": 724,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "retained_index_artifact": {
            "git_blob_oid_sha1": "79f0eaf13969008a8a31c2e47f3fbb06ba2055c6",
            "path": "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin",
            "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
            "size_bytes": 87963,
        },
        "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
        "single_link": True,
        "size_bytes": 87963,
    }
    envelope = {
        "author": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
        "committer": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
        "message": (
            "Correct KSG M1a hosted custody wiring\n\n"
            "Sealed-index-SHA256: "
            "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc\n"
            "Sealed-index-Size: 87963\n"
        ),
        "sealed_index_sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
        "sealed_index_size_bytes": 87963,
    }
    return {
        "candidate": {
            "alternate_index_custody": alternate if mode == "precommit" else None,
            "checkpoint_commit": CORRECTION,
            "commit_envelope": envelope,
            "delta": delta,
            "tree": CORRECTION_TREE,
        },
        "certified_sxpid_correction": {
            "cli_only_selftest_sha256": "bb27185f13f373fe3d4d0f2d3eb94255c3ba522d91520f368cd1fbaa39950324",
            "scientific_authority_unchanged": True,
            "three_container_digest_literals": {
                ".github/workflows/ci.yml": "be1ce389b90b613defc86d1aafd6a17fce641f187eb83b55b43b0f537dd9deb6",
                "justfile": "dfd5e270e8c7f84b5e9887bf9556384280d3d9ca933403d65170d5980a972212",
                "scripts/README.md": "87a27ec193bf29a2e769c2dba143a86a9d4d56c37051376c1b85d0abb493f2ca",
            },
        },
        "child_output_sha256": {
            "scripts/check-certified-sxpid2-claim-self-test.py": "46fdca8535622ac6a78e6c86c3293da3be6a60dac7dadb73f7dc9e60252889bf",
            "scripts/check-certified-sxpid2-claim.py": "09dacad5bd95e7f0fbab262c8f15997fe7bee00c4fe14f32c7dd975a700bcea5",
            "scripts/check-lean-toolchain-freeze-self-test.py": "5bd94f3359146c92e2077c1dec280377a3fa385cd2461c994d19aaa6371cdd0f",
            "scripts/check-lean-toolchain-freeze.py": "a89f6a70578cec68954b43f2edf7bb74851bf664e8c47de203b1d3d36c0aa7ad",
        },
        "credit": "none_local_custody_match_hosted_pending",
        "current_source_manifest_sha256": "c66c51282faabd6746838714e07862e722f3da6a2ca77d78cd093167d5f50c24",
        "disposition": "local_hosted_pending_no_credit",
        "implementation_anchor": {
            "commit": IMPLEMENTATION,
            "direct_parent": "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9",
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": 83,
                "sha256": PROTECTED_SHA,
            },
            "tree": "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
        },
        "lean_r6": {
            "schema": "pid-rs/lean-current-project-replay/v2",
            "sha256": R6_SHA,
            "status": "passed",
        },
        "lifecycle": (
            "implementation_plus_exact_correction_overlay"
            if mode == "precommit"
            else "clean_main_direct_child_postcommit_no_credit"
        ),
        "mode": mode,
        "negative_evidence": {
            "codeql_run_id": 31686106737,
            "failed_ci_run_id": 31686107959,
            "failed_jobs": 1,
            "jobs": 45,
            "sha256": "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5",
        },
        "policy_sha256": "8797335e0f23240f6f018c4403caff1a6c209f9c110ffeaa91fb47503bf331ed",
        "preclosure": {
            "final_decision_absent": True,
            "final_evidence_matrix_absent": True,
            "future_composite_receipt_absent": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        "repository_state": {"active_git_operations": [], "branch": "main"},
        "runtime_mode": optimize,
        "schema": "pid-rs/ksg-rev4-m1a-custody-correction-phase-validation/v1",
        "static_artifact_sha256": {
            "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md": "591bccc8e770b9b51ab34ce8cce9d2ac54973c50185141e1a598fd90260dcc16",
            "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json": "797e7c5a0dc7122aff6c16319749c3a18683ebbe21e94dd039cdc5b7a330d42c",
            "scripts/check-ksg-m1a-custody-correction-self-test.py": "a466461b9eecd4afd3f839aa8137a6fc6b4de13e1aa6e18dc81b0862c6f0fdcb",
            "scripts/check-ksg-m1a-custody-correction.py": "e504fb1617fc93abd096ced451d82c74745011edb4a3b4673bd2dd8c4cea3147",
        },
    }


def synthetic_receipt() -> dict[str, Any]:
    checker_tree = ast.parse(
        CHECKER_SOURCE.decode("utf-8"), filename=os.fspath(CHECKER)
    )

    def checker_constant(name: str) -> Any:
        matches = [
            node
            for node in checker_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        ]
        require(len(matches) == 1, f"checker constant not unique: {name}")
        return ast.literal_eval(matches[0].value)

    def compact(value: Any) -> bytes:
        return canonical(value, pretty=False)

    def capture(endpoint: str, projection: Any) -> dict[str, Any]:
        raw = compact(projection)
        return {
            "endpoint_class": endpoint,
            "format": "canonical-compact-sorted-key-ascii-json-plus-lf/v1",
            "pagination_complete": True,
            "repetitions_equal": True,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }

    def roster_projection(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "encoding": "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
            "entry_count": len(rows),
            "sha256": hashlib.sha256(compact(rows)).hexdigest(),
        }

    def analysis_projection(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "encoding": "canonical compact sorted-key ASCII JSON plus LF over analysis-id-sorted rows",
            "entry_count": len(rows),
            "sha256": hashlib.sha256(compact(rows)).hexdigest(),
        }

    installed_correction_negative = terminal_negative_fixture()
    installed_implementation_negative = json.loads(
        git_show("audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json")
    )

    def recovery_ci_success(head: str, tree: str) -> dict[str, Any]:
        ci = copy.deepcopy(installed_correction_negative["ci_failure"])
        for key in (
            "artifact_contents_projection",
            "artifact_inventory",
            "artifact_inventory_projection",
            "failed_diagnostics",
        ):
            ci.pop(key)
        ci.update(
            all_jobs_successful=True,
            conclusion="success",
            failed_diagnostic=None,
            failed_job_count=0,
            head_sha=head,
            head_tree=tree,
            jobs_successful=45,
            retained_negative_evidence=False,
            run_id=40000000001,
            success_credit="hosted_success_observation_only",
        )
        for job in ci["job_roster"]:
            job["job_id"] += 100_000_000
            job["conclusion"] = "success"
            for step in job["steps"]:
                if step["conclusion"] == "failure":
                    step["conclusion"] = "success"
        ci["job_roster_projection"] = roster_projection(ci["job_roster"])
        content = {
            "binding": {
                "commit_oid": head,
                "git_object_format": "sha1",
                "manifest": {
                    "blob_oid": "5" * 40,
                    "path": "audit/evidence/current-source-state-v1.json",
                    "schema": "pid-rs/current-source-state",
                    "schema_revision": 1,
                    "sha256": "6" * 64,
                    "size_bytes": 12345,
                    "source_projection_entries_sha256": "7" * 64,
                    "source_projection_entry_count": 749,
                },
                "tree_oid": tree,
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
                "commit_cycle": "none; the committed manifest excludes itself and this artifact is generated only after commit",
                "generated_at": "omitted_for_determinism",
                "storage_custody": "caller_owned_not_bound_by_this_artifact",
            },
            "evidence_class": "post_commit_identity_evidence_only",
            "generated_by": "scripts/check-post-commit-source-state-v2.py",
            "nonimplications": list(checker_constant("POST_COMMIT_NONIMPLICATIONS")),
            "repository": "sepahead/pid-rs",
            "schema": "pid-rs/post-commit-source-state",
            "schema_revision": 2,
        }
        content_raw = canonical(content, pretty=True)
        artifact = dict(ci["postcommit_source_state_v2"])
        artifact["artifact_id"] += 100_000_000
        artifact["name"] = f"post-commit-source-state-v2-{head}"
        artifact["sha256"] = "a" * 64
        artifact["content_sha256"] = hashlib.sha256(content_raw).hexdigest()
        artifact["content_size_bytes"] = len(content_raw)
        ci["postcommit_source_state_v2"] = artifact
        ci["postcommit_source_state_v2_content"] = content
        summary_keys = (
            "all_jobs_successful",
            "attempt",
            "conclusion",
            "failed_job_count",
            "head_sha",
            "head_tree",
            "jobs_successful",
            "jobs_total",
            "pagination_complete",
            "ref",
            "repository",
            "run_id",
            "runner_authenticity_claimed",
            "source_event",
            "status",
            "workflow",
            "workflow_path",
        )
        summary = {key: ci[key] for key in summary_keys}
        ci["api_captures"] = [
            capture("ci_job_step_roster", ci["job_roster"]),
            capture("ci_run_summary", summary),
            capture("postcommit_source_state_v2_content", content),
        ]
        return ci

    def recovery_codeql_success(head: str, tree: str) -> dict[str, Any]:
        ql = copy.deepcopy(installed_correction_negative["codeql_success"])
        ql.update(head_sha=head, head_tree=tree, run_id=40000000002)
        id_map: dict[int, int] = {}
        for job in ql["job_roster"]:
            old = job["job_id"]
            job["job_id"] += 200_000_000
            id_map[old] = job["job_id"]
        ql["job_roster_projection"] = roster_projection(ql["job_roster"])
        for analysis in ql["analysis_roster"]:
            analysis["job_id"] = id_map[analysis["job_id"]]
            analysis["analysis_id"] += 200_000_000
            analysis["commit_sha"] = head
        ql["analysis_roster_projection"] = analysis_projection(ql["analysis_roster"])
        summary_keys = (
            "all_jobs_successful",
            "attempt",
            "conclusion",
            "head_sha",
            "head_tree",
            "jobs_successful",
            "jobs_total",
            "new_alerts",
            "pagination_complete",
            "ref",
            "repository",
            "run_id",
            "runner_authenticity_claimed",
            "source_event",
            "status",
            "workflow",
        )
        ql["api_captures"] = [
            capture("codeql_alert_state", ql["alert_state"]),
            capture(
                "codeql_job_analysis_roster",
                {"analyses": ql["analysis_roster"], "jobs": ql["job_roster"]},
            ),
            capture("codeql_run_summary", {key: ql[key] for key in summary_keys}),
        ]
        return ql

    def correction_group(mode: str) -> dict[str, Any]:
        result: dict[str, Any] = {"pair_normalized_equal": True}
        for label, optimize in (("normal", 0), ("optimized", 1)):
            output = historical_correction_output(mode, optimize)
            raw = canonical(output, pretty=False)
            result[label] = {
                "output": output,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        return result

    def artifact(path: str, revision: str = CORRECTION) -> dict[str, Any]:
        raw = git_show(path) if revision == CORRECTION else (ROOT / path).read_bytes()
        return {
            "git_blob_oid_sha1": hashlib.sha1(  # noqa: S324 -- synthetic Git blob.
                f"blob {len(raw)}\0".encode() + raw
            ).hexdigest(),
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }

    alternate = {
        "entry_count": 724,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "retained_index_artifact": {
            "git_blob_oid_sha1": "79f0eaf13969008a8a31c2e47f3fbb06ba2055c6",
            "path": "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin",
            "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
            "size_bytes": 87963,
        },
        "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
        "single_link": True,
        "size_bytes": 87963,
    }
    correction_custody = {
        "alternate_index": alternate,
        "boundary": artifact(
            "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md"
        ),
        "checker": artifact("scripts/check-ksg-m1a-custody-correction.py"),
        "policy": artifact(
            "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json"
        ),
        "postcommit_outputs": correction_group("postcommit"),
        "precommit_outputs": correction_group("precommit"),
        "self_test": artifact("scripts/check-ksg-m1a-custody-correction-self-test.py"),
    }
    recovery_output: dict[str, Any] = {
        "candidate": {},
        "certified_sxpid_recovery": {},
        "child_output_sha256": {},
        "credit": "none_local_custody_match_hosted_pending",
        "current_source_manifest_sha256": "a" * 64,
        "disposition": "local_hosted_pending_no_credit",
        "failed_correction_anchor": {},
        "implementation_anchor": {},
        "lean_r8": {},
        "lifecycle": "failed_correction_plus_exact_recovery_overlay",
        "mode": "precommit",
        "negative_evidence": {},
        "policy_sha256": "b" * 64,
        "preclosure": {},
        "repository_state": {},
        "runtime_mode": 0,
        "schema": "pid-rs/ksg-rev4-m1a-hosted-recovery-phase-validation/v1",
        "static_artifact_sha256": {},
    }

    def recovery_group(mode: str) -> dict[str, Any]:
        normal = copy.deepcopy(recovery_output)
        normal["mode"] = mode
        normal["lifecycle"] = (
            "failed_correction_plus_exact_recovery_overlay"
            if mode == "precommit"
            else "clean_main_sole_child_recovery_no_credit"
        )
        if mode == "postcommit":
            normal["candidate"]["alternate_index_custody"] = None
        optimized = copy.deepcopy(normal)
        optimized["runtime_mode"] = 1
        return {
            "normal": {
                "output": normal,
                "sha256": hashlib.sha256(canonical(normal, pretty=False)).hexdigest(),
            },
            "optimized": {
                "output": optimized,
                "sha256": hashlib.sha256(
                    canonical(optimized, pretty=False)
                ).hexdigest(),
            },
            "pair_normalized_equal": True,
        }

    recovery_index_raw = b"synthetic recovery sealed index"
    recovery_index_sha = hashlib.sha256(recovery_index_raw).hexdigest()
    recovery_alternate = {
        **alternate,
        "entry_count": 732,
        "retained_index_artifact": {
            "git_blob_oid_sha1": hashlib.sha1(  # noqa: S324 -- synthetic Git blob.
                f"blob {len(recovery_index_raw)}\0".encode() + recovery_index_raw
            ).hexdigest(),
            "path": "audit/evidence/ksg-rev4-m1a-hosted-recovery-sealed-index.bin",
            "sha256": recovery_index_sha,
            "size_bytes": 90000,
        },
        "sha256": recovery_index_sha,
        "size_bytes": 90000,
    }
    recovery_commit = "3" * 40
    recovery_tree = "4" * 40
    recovery_delta = [
        {"mode": "100644", "path": row["path"], "status": row["status"]}
        for row in policy_fixture()["entries"]
    ]
    recovery_envelope = {
        "author": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
        "committer": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
        "message": "Repair KSG M1a hosted recovery wiring\n\nSealed-index-SHA256: "
        + recovery_index_sha
        + "\nSealed-index-Size: 90000\n",
        "sealed_index_sha256": recovery_index_sha,
        "sealed_index_size_bytes": 90000,
    }
    protected_phase = {
        "candidate_equals_anchor": True,
        "entry_count": 83,
        "sha256": PROTECTED_SHA,
    }
    implementation_phase = {
        "commit": IMPLEMENTATION,
        "direct_parent": "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9",
        "protected_projection": protected_phase,
        "tree": "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
    }
    correction_phase = {
        "commit": CORRECTION,
        "direct_parent": IMPLEMENTATION,
        "full_tree_projection": {
            "entry_count": 724,
            "sha256": "d6b6ea6f43bba0f240269fe16ba4a40ae87663f1185e6201c8a0d300b605f7fa",
            "size_bytes": 173969,
        },
        "protected_projection": protected_phase,
        "sealed_index": {
            "entry_count": 724,
            "git_blob_oid_sha1": "79f0eaf13969008a8a31c2e47f3fbb06ba2055c6",
            "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
            "size_bytes": 87963,
        },
        "tree": CORRECTION_TREE,
    }
    cert_digests = {
        "certified_checker": "1" * 64,
        "certified_self_test": "2" * 64,
        "just_recipe": "3" * 64,
        "workflow_job": "4" * 64,
    }
    child_digests = {
        "scripts/check-certified-sxpid2-claim-self-test.py": "5" * 64,
        "scripts/check-certified-sxpid2-claim.py": "6" * 64,
        "scripts/check-lean-toolchain-freeze-self-test.py": "7" * 64,
        "scripts/check-lean-toolchain-freeze.py": "8" * 64,
    }
    static_digests = {
        "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json": "9"
        * 64,
        "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md": "a" * 64,
        "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json": "b" * 64,
        "scripts/check-ksg-m1a-hosted-recovery-self-test.py": "c" * 64,
    }
    replay_phase = {
        "prior_r6_sha256": R6_SHA,
        "prior_r7_sha256": R7_SHA,
        "receipt_sha256": "d" * 64,
        "replay_projection_sha256": "e" * 64,
    }
    recovery_output.update(
        candidate={
            "alternate_index_custody": recovery_alternate,
            "checkpoint_commit": recovery_commit,
            "commit_envelope": recovery_envelope,
            "delta": recovery_delta,
            "tree": recovery_tree,
        },
        certified_sxpid_recovery={
            "four_container_digest_literals": cert_digests,
            "scientific_authority_unchanged": True,
            "self_test_sha256": cert_digests["certified_self_test"],
            "workflow_fetch_depth_zero": True,
        },
        child_output_sha256=child_digests,
        current_source_manifest_sha256="f" * 64,
        failed_correction_anchor=correction_phase,
        implementation_anchor=implementation_phase,
        lean_r8=replay_phase,
        negative_evidence={
            "ci_run_id": 31724449805,
            "codeql_run_id": 31724449083,
            "failed_jobs": 2,
            "jobs": 45,
            "sha256": "d9ec2ef753ee8f8f4f3d1d3bcc11aab791b4c127445088f250e7a53d71d896f5",
        },
        policy_sha256="0" * 64,
        preclosure={
            "final_decision_absent": True,
            "final_evidence_matrix_absent": True,
            "future_composite_receipt_absent": True,
            "future_retained_indexes_absent": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        repository_state={"active_git_operations": [], "branch": "main"},
        static_artifact_sha256=static_digests,
    )
    recovery_custody = {
        "alternate_index": recovery_alternate,
        "boundary": artifact(
            "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md",
            "fixture",
        ),
        "checker": artifact("scripts/check-ksg-m1a-hosted-recovery.py", "fixture"),
        "policy": artifact(
            "audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json", "fixture"
        ),
        "postcommit_outputs": recovery_group("postcommit"),
        "precommit_outputs": recovery_group("precommit"),
        "self_test": artifact(
            "scripts/check-ksg-m1a-hosted-recovery-self-test.py", "fixture"
        ),
    }
    for group in (
        recovery_custody["precommit_outputs"],
        recovery_custody["postcommit_outputs"],
    ):
        for runtime_name in ("normal", "optimized"):
            wrapper = group[runtime_name]
            candidate = wrapper["output"]["candidate"]
            candidate.update(
                checkpoint_commit=recovery_commit,
                commit_envelope=copy.deepcopy(recovery_envelope),
                tree=recovery_tree,
            )
            wrapper["sha256"] = hashlib.sha256(
                canonical(wrapper["output"], pretty=False)
            ).hexdigest()
    ci_success = recovery_ci_success(recovery_commit, recovery_tree)
    ql_success = recovery_codeql_success(recovery_commit, recovery_tree)
    correction_sealed = {
        "commit_message_trailer_matches": True,
        "entry_count": 724,
        "git_blob_oid_sha1": "79f0eaf13969008a8a31c2e47f3fbb06ba2055c6",
        "path": "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "reconstructs_tree_twice": True,
        "sha256": "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc",
        "size_bytes": 87963,
    }
    recovery_sealed = {
        "commit_message_trailer_matches": True,
        "entry_count": 732,
        "git_blob_oid_sha1": recovery_alternate["retained_index_artifact"][
            "git_blob_oid_sha1"
        ],
        "path": "audit/evidence/ksg-rev4-m1a-hosted-recovery-sealed-index.bin",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "reconstructs_tree_twice": True,
        "sha256": recovery_index_sha,
        "size_bytes": 90000,
    }
    correction_negative_raw = canonical(installed_correction_negative)
    implementation_negative_raw = canonical(installed_implementation_negative)

    def negative_artifact(path: str, raw: bytes) -> dict[str, Any]:
        return {
            "git_blob_oid_sha1": hashlib.sha1(  # noqa: S324 -- synthetic Git blob.
                f"blob {len(raw)}\0".encode() + raw
            ).hexdigest(),
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }

    return {
        "claim": {"id": "KSG-INTEGER-HARMONIC-001", "revision": 4},
        "correction_local_phase_custody": correction_custody,
        "custody_correction": {
            "author": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "commit": CORRECTION,
            "commit_message": "Correct KSG M1a hosted custody wiring\n\nSealed-index-SHA256: f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc\nSealed-index-Size: 87963\n",
            "committer": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "tree": CORRECTION_TREE,
            "direct_parent": IMPLEMENTATION,
            "implementation_identity_after_correction": IMPLEMENTATION,
            "distinct_from_implementation_anchor": True,
            "object_format": "sha1",
            "one_parent": True,
            "sealed_index": correction_sealed,
            "unsigned": True,
        },
        "evidence_class": "m1a_three_subject_hosted_recovery_custody_not_scientific_evidence",
        "hosted_observations": {
            "all_green_applies_only_to_recovery_head": True,
            "correction_ci_failure": installed_correction_negative["ci_failure"],
            "correction_codeql_success": installed_correction_negative[
                "codeql_success"
            ],
            "correction_heads_equal": True,
            "correction_negative_evidence_artifact": negative_artifact(
                "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json",
                correction_negative_raw,
            ),
            "implementation_ci_failure": installed_implementation_negative[
                "ci_failure"
            ],
            "implementation_codeql_success": installed_implementation_negative[
                "codeql_success"
            ],
            "implementation_heads_equal": True,
            "implementation_negative_evidence_artifact": negative_artifact(
                "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json",
                implementation_negative_raw,
            ),
            "recovery_ci_success": ci_success,
            "recovery_codeql_success": ql_success,
            "recovery_heads_equal": True,
            "three_subject_heads_distinct": True,
        },
        "hosted_recovery": {
            "author": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "commit": recovery_commit,
            "commit_message": "Repair KSG M1a hosted recovery wiring\n\nSealed-index-SHA256: "
            + recovery_index_sha
            + "\nSealed-index-Size: 90000\n",
            "committer": {"email": "sepmhn@gmail.com", "name": "Sepehr Mahmoudian"},
            "tree": recovery_tree,
            "direct_parent": CORRECTION,
            "implementation_identity_after_recovery": IMPLEMENTATION,
            "distinct_from_correction": True,
            "object_format": "sha1",
            "one_parent": True,
            "sealed_index": recovery_sealed,
            "unsigned": True,
        },
        "implementation_anchor": {
            "commit": IMPLEMENTATION,
            "tree": "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
            "direct_parent": "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9",
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": 83,
                "format": "canonical compact sorted-key ASCII JSON plus LF over sorted {path,git_mode,git_blob_oid_sha1,sha256,size_bytes} rows",
                "sha256": PROTECTED_SHA,
            },
            "remains_implementation_after_recovery": True,
        },
        "milestone": {
            "gate_id": "G1",
            "implementation_phase": "M1a",
            "integration_status": "integration_no_go",
            "status": "implementation_failed_correction_and_hosted_recovery_observed",
        },
        "negative_evidence_semantics": list(
            checker_constant("NEGATIVE_EVIDENCE_SEMANTICS")
        ),
        "nonimplications": list(checker_constant("COMPOSITE_NONIMPLICATIONS")),
        "recovery_local_phase_custody": recovery_custody,
        "remote_observations": {
            "branch": "main",
            "implementation_commit": IMPLEMENTATION,
            "correction_commit": CORRECTION,
            "recovery_commit": recovery_commit,
            "observed_remote_head": recovery_commit,
            "observed_at": "2099-12-31T23:59:59Z",
        },
        "repository": "sepahead/pid-rs",
        "revision4_integration": {
            "decision_v4_absent_at_recovery": True,
            "evidence_matrix_v4_absent_at_recovery": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v3",
        "schema_revision": 3,
    }


def reseal_recovery_ci(receipt: dict[str, Any]) -> None:
    ci = receipt["hosted_observations"]["recovery_ci_success"]
    rows = ci["job_roster"]
    ci["job_roster_projection"] = {
        "encoding": "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "entry_count": len(rows),
        "sha256": hashlib.sha256(canonical(rows, pretty=False)).hexdigest(),
    }
    summary_keys = (
        "all_jobs_successful",
        "attempt",
        "conclusion",
        "failed_job_count",
        "head_sha",
        "head_tree",
        "jobs_successful",
        "jobs_total",
        "pagination_complete",
        "ref",
        "repository",
        "run_id",
        "runner_authenticity_claimed",
        "source_event",
        "status",
        "workflow",
        "workflow_path",
    )
    projections = (
        rows,
        {key: ci[key] for key in summary_keys},
        ci["postcommit_source_state_v2_content"],
    )
    endpoints = (
        "ci_job_step_roster",
        "ci_run_summary",
        "postcommit_source_state_v2_content",
    )
    ci["api_captures"] = [
        {
            "endpoint_class": endpoint,
            "format": "canonical-compact-sorted-key-ascii-json-plus-lf/v1",
            "pagination_complete": True,
            "repetitions_equal": True,
            "sha256": hashlib.sha256(canonical(projection, pretty=False)).hexdigest(),
            "size_bytes": len(canonical(projection, pretty=False)),
        }
        for endpoint, projection in zip(endpoints, projections, strict=True)
    ]


def reseal_recovery_codeql(receipt: dict[str, Any]) -> None:
    ql = receipt["hosted_observations"]["recovery_codeql_success"]
    jobs, analyses = ql["job_roster"], ql["analysis_roster"]
    ql["job_roster_projection"] = {
        "encoding": "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "entry_count": len(jobs),
        "sha256": hashlib.sha256(canonical(jobs, pretty=False)).hexdigest(),
    }
    ql["analysis_roster_projection"] = {
        "encoding": "canonical compact sorted-key ASCII JSON plus LF over analysis-id-sorted rows",
        "entry_count": len(analyses),
        "sha256": hashlib.sha256(canonical(analyses, pretty=False)).hexdigest(),
    }
    summary_keys = (
        "all_jobs_successful",
        "attempt",
        "conclusion",
        "head_sha",
        "head_tree",
        "jobs_successful",
        "jobs_total",
        "new_alerts",
        "pagination_complete",
        "ref",
        "repository",
        "run_id",
        "runner_authenticity_claimed",
        "source_event",
        "status",
        "workflow",
    )
    projections = {
        "codeql_alert_state": ql["alert_state"],
        "codeql_job_analysis_roster": {"analyses": analyses, "jobs": jobs},
        "codeql_run_summary": {key: ql[key] for key in summary_keys},
    }
    ql["api_captures"] = [
        {
            "endpoint_class": endpoint,
            "format": "canonical-compact-sorted-key-ascii-json-plus-lf/v1",
            "pagination_complete": True,
            "repetitions_equal": True,
            "sha256": hashlib.sha256(
                canonical(projections[endpoint], pretty=False)
            ).hexdigest(),
            "size_bytes": len(canonical(projections[endpoint], pretty=False)),
        }
        for endpoint in sorted(projections)
    ]


def coordinated_ci_mutation(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    operation(receipt["hosted_observations"]["recovery_ci_success"])
    reseal_recovery_ci(receipt)


def coordinated_content_mutation(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    ci = receipt["hosted_observations"]["recovery_ci_success"]
    content = ci["postcommit_source_state_v2_content"]
    operation(content)
    raw = canonical(content, pretty=True)
    ci["postcommit_source_state_v2"].update(
        content_sha256=hashlib.sha256(raw).hexdigest(),
        content_size_bytes=len(raw),
    )
    reseal_recovery_ci(receipt)


def coordinated_codeql_mutation(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    operation(receipt["hosted_observations"]["recovery_codeql_success"])
    reseal_recovery_codeql(receipt)


def permute_analysis_job_ids(ql: dict[str, Any]) -> None:
    identifiers = [row["job_id"] for row in ql["analysis_roster"]]
    for index, row in enumerate(ql["analysis_roster"]):
        row["job_id"] = identifiers[(index + 1) % len(identifiers)]


def overlap_alert_categories(ql: dict[str, Any]) -> None:
    state = ql["alert_state"]
    values = sorted(
        set(state["open_alert_numbers"]) | {state["dismissed_alert_numbers"][0]}
    )
    state.update(open_alert_numbers=values, open=len(values))


def coordinated_phase_mutation(
    vector_value: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    custody = vector_value["custody"]
    for phase_name in ("precommit_outputs", "postcommit_outputs"):
        for runtime_name in ("normal", "optimized"):
            wrapper = custody[phase_name][runtime_name]
            operation(wrapper["output"])
            wrapper["sha256"] = hashlib.sha256(
                canonical(wrapper["output"], pretty=False)
            ).hexdigest()


def coordinated_receipt_phase_mutation(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    coordinated_phase_mutation(
        {"custody": receipt["recovery_local_phase_custody"]}, operation
    )


def coordinated_lean_phase_mutation(
    vector_value: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    coordinated_phase_mutation(
        vector_value, lambda output: operation(output["lean_r8"])
    )
    operation(vector_value["expected"]["replay"])


def coordinated_receipt_lean_phase_mutation(
    receipt: dict[str, Any], operation: Callable[[dict[str, Any]], None]
) -> None:
    coordinated_receipt_phase_mutation(
        receipt, lambda output: operation(output["lean_r8"])
    )


def coordinated_receipt_alternate_replacement(
    receipt: dict[str, Any], phase_name: str, replacement: Any
) -> None:
    group = receipt["recovery_local_phase_custody"][phase_name]
    for runtime_name in ("normal", "optimized"):
        wrapper = group[runtime_name]
        wrapper["output"]["candidate"]["alternate_index_custody"] = copy.deepcopy(
            replacement
        )
        wrapper["sha256"] = hashlib.sha256(
            canonical(wrapper["output"], pretty=False)
        ).hexdigest()


def coordinated_receipt_alternate_key_removal(
    receipt: dict[str, Any], key: str
) -> None:
    group = receipt["recovery_local_phase_custody"]["precommit_outputs"]
    for runtime_name in ("normal", "optimized"):
        wrapper = group[runtime_name]
        wrapper["output"]["candidate"]["alternate_index_custody"].pop(key)
        wrapper["sha256"] = hashlib.sha256(
            canonical(wrapper["output"], pretty=False)
        ).hexdigest()


def coordinated_recovery_index_reseal(receipt: dict[str, Any]) -> None:
    digest, blob, size = "6" * 64, "7" * 40, 90_001
    message = (
        "Repair KSG M1a hosted recovery wiring\n\n"
        f"Sealed-index-SHA256: {digest}\nSealed-index-Size: {size}\n"
    )
    sealed = receipt["hosted_recovery"]["sealed_index"]
    sealed.update(git_blob_oid_sha1=blob, sha256=digest, size_bytes=size)
    receipt["hosted_recovery"]["commit_message"] = message
    alternate = receipt["recovery_local_phase_custody"]["alternate_index"]
    alternate.update(sha256=digest, size_bytes=size)
    alternate["retained_index_artifact"].update(
        git_blob_oid_sha1=blob, sha256=digest, size_bytes=size
    )
    for phase_name in ("precommit_outputs", "postcommit_outputs"):
        group = receipt["recovery_local_phase_custody"][phase_name]
        for runtime_name in ("normal", "optimized"):
            wrapper = group[runtime_name]
            candidate = wrapper["output"]["candidate"]
            if candidate["alternate_index_custody"] is not None:
                candidate["alternate_index_custody"] = copy.deepcopy(alternate)
            candidate["commit_envelope"].update(
                message=message,
                sealed_index_sha256=digest,
                sealed_index_size_bytes=size,
            )
            wrapper["sha256"] = hashlib.sha256(
                canonical(wrapper["output"], pretty=False)
            ).hexdigest()


def coordinated_recovery_identity_reseal(receipt: dict[str, Any]) -> None:
    head, tree = "5" * 40, "6" * 40
    receipt["hosted_recovery"].update(commit=head, tree=tree)
    receipt["remote_observations"].update(
        observed_remote_head=head, recovery_commit=head
    )
    ci = receipt["hosted_observations"]["recovery_ci_success"]
    ci.update(head_sha=head, head_tree=tree)
    ci["postcommit_source_state_v2"]["name"] = f"post-commit-source-state-v2-{head}"
    content = ci["postcommit_source_state_v2_content"]
    content["binding"].update(commit_oid=head, tree_oid=tree)
    content_raw = canonical(content)
    ci["postcommit_source_state_v2"].update(
        content_sha256=hashlib.sha256(content_raw).hexdigest(),
        content_size_bytes=len(content_raw),
    )
    reseal_recovery_ci(receipt)
    ql = receipt["hosted_observations"]["recovery_codeql_success"]
    ql.update(head_sha=head, head_tree=tree)
    for analysis in ql["analysis_roster"]:
        analysis["commit_sha"] = head
    reseal_recovery_codeql(receipt)
    for phase_name in ("precommit_outputs", "postcommit_outputs"):
        group = receipt["recovery_local_phase_custody"][phase_name]
        for runtime_name in ("normal", "optimized"):
            wrapper = group[runtime_name]
            wrapper["output"]["candidate"].update(checkpoint_commit=head, tree=tree)
            wrapper["sha256"] = hashlib.sha256(
                canonical(wrapper["output"], pretty=False)
            ).hexdigest()


def phase_vector(receipt: dict[str, Any]) -> dict[str, Any]:
    custody = copy.deepcopy(receipt["recovery_local_phase_custody"])
    pre = custody["precommit_outputs"]["normal"]["output"]
    alternate = custody["alternate_index"]
    expected = {
        "certified": copy.deepcopy(pre["certified_sxpid_recovery"]),
        "checkpoint": "3" * 40,
        "children": copy.deepcopy(pre["child_output_sha256"]),
        "current_source": pre["current_source_manifest_sha256"],
        "delta": tuple(
            (row["path"], row["status"], row["mode"])
            for row in pre["candidate"].get("delta", [])
        ),
        "envelope": copy.deepcopy(pre["candidate"].get("commit_envelope", {})),
        "failed_correction_anchor": copy.deepcopy(pre["failed_correction_anchor"]),
        "implementation_anchor": copy.deepcopy(pre["implementation_anchor"]),
        "negative_sha256": pre["negative_evidence"].get("sha256", "d" * 64),
        "negative_summary": {
            key: value
            for key, value in pre["negative_evidence"].items()
            if key != "sha256"
        },
        "policy_sha256": pre["policy_sha256"],
        "replay": copy.deepcopy(pre["lean_r8"]),
        "static": copy.deepcopy(pre["static_artifact_sha256"]),
        "tree": "4" * 40,
    }
    for phase_name, mode, lifecycle, phase_alternate in (
        (
            "precommit_outputs",
            "precommit",
            "failed_correction_plus_exact_recovery_overlay",
            alternate,
        ),
        (
            "postcommit_outputs",
            "postcommit",
            "clean_main_sole_child_recovery_no_credit",
            None,
        ),
    ):
        for runtime_name, runtime_mode in (("normal", 0), ("optimized", 1)):
            output = custody[phase_name][runtime_name]["output"]
            output.update(
                candidate={
                    "alternate_index_custody": phase_alternate,
                    "checkpoint_commit": expected["checkpoint"],
                    "commit_envelope": expected["envelope"],
                    "delta": [
                        {"mode": mode_value, "path": path, "status": status}
                        for path, status, mode_value in expected["delta"]
                    ],
                    "tree": expected["tree"],
                },
                lifecycle=lifecycle,
                mode=mode,
                negative_evidence={
                    "sha256": expected["negative_sha256"],
                    **expected["negative_summary"],
                },
                preclosure={
                    "final_decision_absent": True,
                    "final_evidence_matrix_absent": True,
                    "future_composite_receipt_absent": True,
                    "future_retained_indexes_absent": True,
                    "open_gate_count": 13,
                    "status": "integration_no_go",
                },
                repository_state={"active_git_operations": [], "branch": "main"},
                runtime_mode=runtime_mode,
            )
            custody[phase_name][runtime_name]["sha256"] = hashlib.sha256(
                canonical(output, pretty=False)
            ).hexdigest()
    return {"custody": custody, "expected": expected}


def main() -> int:
    global CHECKER_SOURCE
    checker_raw, checker_identity = stable_read(CHECKER)
    selftest_raw, selftest_identity = stable_read(SCRIPT)
    lean_r7_raw, lean_r7_identity = stable_read(LEAN_R7)
    active_packet_raw, active_packet_identity = stable_read(ACTIVE_PACKET)
    current_source_raw, current_source_identity = stable_read(CURRENT_SOURCE)
    implementation_negative_raw = git_show(
        "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
    )
    require(
        len(lean_r7_raw) == 127_246
        and hashlib.sha256(lean_r7_raw).hexdigest() == R7_SHA,
        "Lean r7 positive fixture identity changed",
    )
    require(
        len(active_packet_raw) == 30_687
        and hashlib.sha256(active_packet_raw).hexdigest() == ACTIVE_PACKET_SHA,
        "active-packet positive fixture identity changed",
    )
    require(
        len(implementation_negative_raw) == 484_959
        and hashlib.sha256(implementation_negative_raw).hexdigest()
        == "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5",
        "implementation-negative positive fixture identity changed",
    )
    lean_r7 = json.loads(lean_r7_raw)
    active_packet = json.loads(active_packet_raw)
    current_source = json.loads(current_source_raw)
    implementation_negative = json.loads(implementation_negative_raw)
    CHECKER_SOURCE = checker_raw
    static_custody(checker_raw, selftest_raw)

    policy = policy_fixture()
    accepted("policy", policy)
    for label, operation in (
        (
            "policy parent",
            lambda item: item["failed_correction_anchor"].update(
                direct_parent="0" * 40
            ),
        ),
        ("policy deletion", lambda item: item.update(deletions_permitted=True)),
        ("policy row missing", lambda item: item["entries"].pop()),
        ("policy row status", lambda item: item["entries"][0].update(status="D")),
        (
            "policy protected digest",
            lambda item: item["implementation_anchor"]["protected_projection"].update(
                sha256="0" * 64
            ),
        ),
        (
            "policy receipt route",
            lambda item: item["receipt_contract"].update(receipt_path="wrong.json"),
        ),
        (
            "policy schema revision bool alias",
            lambda item: item.update(schema_revision=True),
        ),
        (
            "policy schema revision string alias",
            lambda item: item.update(schema_revision="1"),
        ),
        (
            "policy schema revision container alias",
            lambda item: item.update(schema_revision=[]),
        ),
        (
            "policy schema revision wrong integer",
            lambda item: item.update(schema_revision=2),
        ),
        (
            "policy stray nested revision",
            lambda item: item["authority"].update(revision=1),
        ),
        (
            "policy stray nested schema revision",
            lambda item: item["authority"].update(schema_revision=1),
        ),
    ):
        rejected(label, "policy", mutate(policy, operation))

    commit_payload = {"raw_hex": recovery_message().hex(), "tree": "2" * 40}
    accepted("commit", commit_payload)
    for label, raw in (
        (
            "commit parent",
            recovery_message().replace(CORRECTION.encode(), IMPLEMENTATION.encode(), 1),
        ),
        (
            "commit merge",
            recovery_message().replace(
                b"author ", b"parent " + IMPLEMENTATION.encode() + b"\nauthor ", 1
            ),
        ),
        (
            "commit signature",
            recovery_message().replace(b"author ", b"gpgsig hostile\nauthor ", 1),
        ),
        ("commit subject", recovery_message().replace(b"Repair KSG", b"Retry KSG", 1)),
        ("commit index digest", recovery_message(digest="A" * 64)),
        ("commit index size", recovery_message(size="032768")),
        (
            "commit identity",
            recovery_message().replace(b"Sepehr Mahmoudian", b"Agent", 1),
        ),
    ):
        rejected(label, "commit", {"raw_hex": raw.hex(), "tree": "2" * 40})

    delta = [
        {"mode": "100644", "path": path, "status": status}
        for path, (status, _) in sorted(
            {
                row["path"]: (row["status"], row["review_class"])
                for row in policy["entries"]
            }.items()
        )
    ]
    accepted("delta", {"observed": delta})
    rejected(
        "delta deletion",
        "delta",
        {"observed": [*delta, {"mode": "000000", "path": "victim", "status": "D"}]},
    )
    rejected("delta omitted", "delta", {"observed": delta[:-1]})
    rejected("delta reordered", "delta", {"observed": list(reversed(delta))})

    protected = {"count": 83, "sha256": PROTECTED_SHA}
    accepted("protected", protected)
    rejected("protected count", "protected", {**protected, "count": 82})
    rejected("protected digest", "protected", {**protected, "sha256": "0" * 64})

    history = {
        "correction": CORRECTION,
        "implementation": IMPLEMENTATION,
        "parent": IMPLEMENTATION,
        "tree": CORRECTION_TREE,
    }
    accepted("history", history)
    for key in history:
        rejected(f"history {key}", "history", {**history, key: "0" * 40})

    negative = terminal_negative_fixture()
    accepted("negative", negative)
    for label, operation in (
        ("negative CI key", lambda item: item["ci_failure"].update(unreviewed=True)),
        (
            "negative failed count",
            lambda item: item["ci_failure"].update(failed_job_count=1),
        ),
        (
            "negative failed diagnostic",
            lambda item: item["ci_failure"]["failed_diagnostics"][1].update(
                exception_class="locally_inferred"
            ),
        ),
        (
            "negative raw log",
            lambda item: item["ci_failure"]["failed_diagnostics"][0]["raw_log"].update(
                sha256="0" * 64
            ),
        ),
        (
            "negative roster",
            lambda item: item["ci_failure"]["job_roster"][0].update(name="hostile"),
        ),
        (
            "negative capture endpoint",
            lambda item: item["ci_failure"]["api_captures"][0].update(
                endpoint_class="ci_run_summary"
            ),
        ),
        (
            "negative artifact member",
            lambda item: item["capture_boundary"]["artifact_contents"][0]["members"][
                0
            ].update(size_bytes=1),
        ),
        ("negative semantics", lambda item: item["negative_semantics"].pop()),
        (
            "negative CodeQL alert",
            lambda item: item["codeql_success"].update(new_alerts=1),
        ),
        (
            "negative schema revision bool alias",
            lambda item: item.update(schema_revision=True),
        ),
        (
            "negative schema revision string alias",
            lambda item: item.update(schema_revision="1"),
        ),
        (
            "negative schema revision container alias",
            lambda item: item.update(schema_revision=[]),
        ),
        (
            "negative schema revision wrong integer",
            lambda item: item.update(schema_revision=2),
        ),
        (
            "negative stray nested revision",
            lambda item: item["subject"].update(revision=1),
        ),
        (
            "negative stray nested schema revision",
            lambda item: item["subject"].update(schema_revision=1),
        ),
    ):
        rejected(label, "negative", mutate(negative, operation))

    replay = {
        "prior_r6_sha256": R6_SHA,
        "prior_r7_sha256": R7_SHA,
        "schema": "pid-rs/lean-current-project-replay/v2",
        "status": "passed",
    }
    accepted("replay", replay)
    rejected("replay r6", "replay", {**replay, "prior_r6_sha256": "0" * 64})
    rejected("replay r7", "replay", {**replay, "prior_r7_sha256": "0" * 64})
    rejected("replay status", "replay", {**replay, "status": "failed"})

    accepted("lean_v2", lean_r7)
    package_names = sorted(lean_r7["package_pins"])
    require(
        package_names
        == [
            "Cli",
            "LeanSearchClient",
            "Qq",
            "aesop",
            "batteries",
            "importGraph",
            "mathlib",
            "plausible",
            "proofwidgets",
        ],
        "Lean-v2 package fixture inventory changed",
    )
    for package_name in package_names:
        for alias_name, replacement in (
            ("bool", False),
            ("integer", 4),
            ("container", []),
        ):
            rejected(
                f"Lean-v2 {package_name} revision {alias_name} alias",
                "lean_v2",
                mutate(
                    lean_r7,
                    lambda item, package_name=package_name, replacement=replacement: (
                        item["package_pins"][package_name].update(
                            revision=copy.deepcopy(replacement)
                        )
                    ),
                ),
            )
    rejected(
        "Lean-v2 all package revisions bool alias",
        "lean_v2",
        mutate(
            lean_r7,
            lambda item: update_all_package_revisions(item, True),
        ),
    )
    rejected(
        "Lean-v2 package revision malformed string",
        "lean_v2",
        mutate(
            lean_r7,
            lambda item: item["package_pins"]["mathlib"].update(
                revision="not-a-40-hex-revision"
            ),
        ),
    )
    rejected(
        "Lean-v2 package missing",
        "lean_v2",
        mutate(lean_r7, lambda item: item["package_pins"].pop("Cli")),
    )
    rejected(
        "Lean-v2 package extra",
        "lean_v2",
        mutate(
            lean_r7,
            lambda item: item["package_pins"].update(
                extra=copy.deepcopy(item["package_pins"]["Cli"])
            ),
        ),
    )
    rejected(
        "Lean-v2 package revision moved outside package pins",
        "lean_v2",
        mutate(
            lean_r7,
            lambda item: item.update(
                revision=item["package_pins"]["Cli"].pop("revision")
            ),
        ),
    )
    rejected(
        "Lean-v2 stray root revision with valid package pins",
        "lean_v2",
        mutate(lean_r7, lambda item: item.update(revision="0" * 40)),
    )
    rejected(
        "Lean-v2 stray nested revision with valid package pins",
        "lean_v2",
        mutate(
            lean_r7,
            lambda item: item["active_configuration"].update(revision="0" * 40),
        ),
    )
    rejected(
        "Lean-v2 stray schema revision",
        "lean_v2",
        mutate(lean_r7, lambda item: item.update(schema_revision=1)),
    )

    accepted("active_packet", active_packet)
    for alias_name, replacement in (
        ("bool", True),
        ("string", "4"),
        ("container", []),
        ("wrong integer", 3),
    ):
        rejected(
            f"active-packet active revision {alias_name} alias",
            "active_packet",
            mutate(
                active_packet,
                lambda item, replacement=replacement: item.update(
                    active_revision=copy.deepcopy(replacement)
                ),
            ),
        )
    rejected(
        "active-packet active marker mismatch",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["revision_history"][2].update(active=True),
        ),
    )
    for alias_name, replacement in (
        ("bool", False),
        ("string", "1"),
        ("container", []),
        ("wrong integer", 2),
    ):
        rejected(
            f"active-packet schema revision {alias_name} alias",
            "active_packet",
            mutate(
                active_packet,
                lambda item, replacement=replacement: item.update(
                    schema_revision=copy.deepcopy(replacement)
                ),
            ),
        )
    for row_index in range(4):
        rejected(
            f"active-packet history revision {row_index + 1} bool alias",
            "active_packet",
            mutate(
                active_packet,
                lambda item, row_index=row_index: item["revision_history"][
                    row_index
                ].update(revision=False),
            ),
        )
    for alias_name, replacement in (("string", "1"), ("container", [])):
        rejected(
            f"active-packet history revision 1 {alias_name} alias",
            "active_packet",
            mutate(
                active_packet,
                lambda item, replacement=replacement: item["revision_history"][
                    0
                ].update(revision=copy.deepcopy(replacement)),
            ),
        )
    rejected(
        "active-packet history revision 4 true alias",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["revision_history"][3].update(revision=True),
        ),
    )
    rejected(
        "active-packet history revision wrong integer",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["revision_history"][0].update(revision=2),
        ),
    )
    rejected(
        "active-packet history revision extra key",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["revision_history"][0].update(extra=1),
        ),
    )
    rejected(
        "active-packet stray root revision",
        "active_packet",
        mutate(active_packet, lambda item: item.update(revision=4)),
    )
    rejected(
        "active-packet stray nested revision",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["facts"].update(revision=4),
        ),
    )
    rejected(
        "active-packet stray nested schema revision",
        "active_packet",
        mutate(
            active_packet,
            lambda item: item["facts"].update(schema_revision=1),
        ),
    )

    accepted("current_source", current_source)
    for alias_name, replacement in (
        ("bool", True),
        ("string", "1"),
        ("container", []),
        ("wrong integer", 2),
    ):
        rejected(
            f"current-source schema revision {alias_name} alias",
            "current_source",
            mutate(
                current_source,
                lambda item, replacement=replacement: item.update(
                    schema_revision=copy.deepcopy(replacement)
                ),
            ),
        )
    rejected(
        "current-source stray root revision",
        "current_source",
        mutate(current_source, lambda item: item.update(revision=1)),
    )
    rejected(
        "current-source stray nested schema revision",
        "current_source",
        mutate(
            current_source,
            lambda item: item["binding"].update(schema_revision=1),
        ),
    )
    rejected(
        "current-source stray nested revision",
        "current_source",
        mutate(
            current_source,
            lambda item: item["binding"].update(revision=1),
        ),
    )

    accepted("implementation_negative", implementation_negative)
    for alias_name, replacement in (
        ("bool", True),
        ("string", "1"),
        ("container", []),
        ("wrong integer", 2),
    ):
        rejected(
            f"implementation-negative schema revision {alias_name} alias",
            "implementation_negative",
            mutate(
                implementation_negative,
                lambda item, replacement=replacement: item.update(
                    schema_revision=copy.deepcopy(replacement)
                ),
            ),
        )
    rejected(
        "implementation-negative stray root revision",
        "implementation_negative",
        mutate(implementation_negative, lambda item: item.update(revision=1)),
    )
    rejected(
        "implementation-negative stray nested schema revision",
        "implementation_negative",
        mutate(
            implementation_negative,
            lambda item: item["subject"].update(schema_revision=1),
        ),
    )
    rejected(
        "implementation-negative stray nested revision",
        "implementation_negative",
        mutate(
            implementation_negative,
            lambda item: item["subject"].update(revision=1),
        ),
    )
    for alias_name, replacement in (
        ("integer", 4),
        ("bool", True),
        ("object", {}),
        ("scalar list", [2]),
    ):
        rejected(
            f"implementation-negative API jobs {alias_name} alias",
            "implementation_negative",
            mutate(
                implementation_negative,
                lambda item, replacement=replacement: item["codeql_success"][
                    "api_captures"
                ][1]["projection"].update(jobs=copy.deepcopy(replacement)),
            ),
        )
    rejected(
        "implementation-negative capture-boundary API jobs scalar list",
        "implementation_negative",
        mutate(
            implementation_negative,
            lambda item: item["capture_boundary"]["api_responses"][3][
                "projection"
            ].update(jobs=[2]),
        ),
    )

    anchor_workflow, candidate_workflow = workflow_fixture()
    workflow = {"anchor": anchor_workflow, "candidate": candidate_workflow}
    accepted("workflow", workflow)
    rejected(
        "workflow shallow removal",
        "workflow",
        {"anchor": anchor_workflow, "candidate": anchor_workflow},
    )
    rejected(
        "workflow finite depth",
        "workflow",
        {
            "anchor": anchor_workflow,
            "candidate": candidate_workflow.replace("fetch-depth: 0", "fetch-depth: 2"),
        },
    )
    rejected(
        "workflow credentials",
        "workflow",
        {
            "anchor": anchor_workflow,
            "candidate": candidate_workflow.replace(
                "persist-credentials: false", "persist-credentials: true"
            ),
        },
    )
    rejected(
        "workflow extra change",
        "workflow",
        {
            "anchor": anchor_workflow,
            "candidate": candidate_workflow.replace("steps:", "steps: # hostile"),
        },
    )

    wiring = {
        "workflow": stable_read(ROOT / ".github/workflows/ci.yml")[0].decode("utf-8"),
        "just": stable_read(ROOT / "justfile")[0].decode("utf-8"),
        "readme": stable_read(ROOT / "scripts/README.md")[0].decode("utf-8"),
    }
    accepted("wiring", wiring)
    for label, field, old, new in (
        (
            "wiring composite parent guard",
            "workflow",
            '              && [[ "$direct_parent" == "$receipt_recovery" ]]\n',
            '              && [[ "$direct_parent" == "$failed_correction" ]]\n',
        ),
        (
            "wiring composite duplicate-key parser",
            "workflow",
            "              value = json.loads(raw, object_pairs_hook=unique)\n",
            "              value = json.loads(raw)\n",
        ),
        (
            "wiring composite attachment",
            "workflow",
            "              if git symbolic-ref -q HEAD >/dev/null\n",
            "              git switch main\n              if git symbolic-ref -q HEAD >/dev/null\n",
        ),
        (
            "wiring composite later-descendant skip",
            "workflow",
            "composite receipt is retained outside its exact direct-child push; sole-child validation is not applicable and no credit is granted",
            "composite receipt will be validated on every later descendant",
        ),
        (
            "wiring global default shell",
            "workflow",
            "name: CI\n",
            "name: CI\ndefaults:\n  run:\n    shell: bash\n",
        ),
        (
            "wiring step if false",
            "workflow",
            "      - name: Verify the KSG M1a hosted-recovery lifecycle\n        run: |\n",
            "      - name: Verify the KSG M1a hosted-recovery lifecycle\n        if: false\n        run: |\n",
        ),
        (
            "wiring Just shell",
            "just",
            "ksg-revision:\n",
            'set shell := ["false"]\n\nksg-revision:\n',
        ),
        (
            "wiring README outer fence",
            "readme",
            "<!-- BEGIN KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n",
            "```text\n<!-- BEGIN KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n",
        ),
        (
            "wiring README contradiction",
            "readme",
            "<!-- END KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n",
            "shallow checkout is sufficient\n<!-- END KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n",
        ),
    ):
        rejected(
            label,
            "wiring",
            mutate(
                wiring,
                lambda item, field=field, old=old, new=new: replace_once_field(
                    item, field, old, new
                ),
            ),
        )

    accepted("raw_tree", raw_tree_fixture())
    rejected("raw tree empty nested subtree", "raw_tree", raw_tree_fixture(empty=True))
    rejected("raw tree repeated subtree", "raw_tree", raw_tree_fixture(repeated=True))

    candidate_empty = {
        "mode": "100644",
        "oid": EMPTY_BLOB_OID,
        "path": EMPTY_TRACKED_RELATIVE,
        "role": "candidate",
    }
    accepted("worktree_leaf", candidate_empty)
    rejected(
        "worktree empty candidate nonempty mismatch",
        "worktree_leaf",
        {**candidate_empty, "oid": "1" * 40},
    )
    rejected(
        "empty authority remains forbidden",
        "worktree_leaf",
        {**candidate_empty, "role": "authority"},
    )
    regular_mode = stat.S_IFREG | 0o644
    snapshot = [1, 2, regular_mode, 1, 0, 3, 4]
    snapshot_vector = {
        "after": snapshot,
        "allow_empty": True,
        "before": snapshot,
        "maximum": 1,
        "path_after": snapshot,
        "path_before": snapshot,
        "required_mode": 0o644,
    }
    accepted("regular_snapshot", snapshot_vector)
    rejected(
        "regular snapshot symlink",
        "regular_snapshot",
        {
            **snapshot_vector,
            **{
                key: [1, 2, stat.S_IFLNK | 0o777, 1, 0, 3, 4]
                for key in ("before", "path_before", "after", "path_after")
            },
        },
    )
    rejected(
        "regular snapshot hardlink",
        "regular_snapshot",
        {
            **snapshot_vector,
            **{
                key: [1, 2, regular_mode, 2, 0, 3, 4]
                for key in ("before", "path_before", "after", "path_after")
            },
        },
    )
    rejected(
        "regular snapshot wrong mode",
        "regular_snapshot",
        {
            **snapshot_vector,
            **{
                key: [1, 2, stat.S_IFREG | 0o600, 1, 0, 3, 4]
                for key in ("before", "path_before", "after", "path_after")
            },
        },
    )
    rejected(
        "regular snapshot unstable identity",
        "regular_snapshot",
        {**snapshot_vector, "after": [1, 9, regular_mode, 1, 0, 3, 4]},
    )
    rejected(
        "regular snapshot default positive",
        "regular_snapshot",
        {**snapshot_vector, "allow_empty": False},
    )
    oversized_snapshot = [1, 2, regular_mode, 1, 2, 3, 4]
    rejected(
        "regular snapshot maximum",
        "regular_snapshot",
        {
            **snapshot_vector,
            **{
                key: oversized_snapshot
                for key in ("before", "path_before", "after", "path_after")
            },
        },
    )

    fresh_attempt = {
        "checkpoint": "3" * 40,
        "entry_count": 732,
        "index_sha256": "4" * 64,
        "index_size": 90_000,
        "tree": "5" * 40,
    }
    accepted("retired_attempt", fresh_attempt)
    for label, replacement in (
        ("checkpoint", RETIRED_RECOVERY_CHECKPOINT),
        ("tree", RETIRED_RECOVERY_TREE),
    ):
        rejected(
            f"retired attempt {label}",
            "retired_attempt",
            {**fresh_attempt, label: replacement},
        )
    rejected(
        "retired attempt index tuple",
        "retired_attempt",
        {
            **fresh_attempt,
            "entry_count": 731,
            "index_sha256": RETIRED_RECOVERY_INDEX_SHA256,
            "index_size": 88_875,
        },
    )

    transport = {
        "bootstrap_sha256": hashlib.sha256(
            CHECKER_STDIN_BOOTSTRAP.replace(
                "hosted-recovery checker stdin launcher", "isolated source bootstrap"
            ).encode()
        ).hexdigest(),
        "contains_compile_exec": True,
        "isolated_flags": ["-I", "-S", "-B"],
    }
    # The checker validates its own smaller child bootstrap, not this outer launcher.
    checker_tree = ast.parse(checker_raw.decode("utf-8"), filename=os.fspath(CHECKER))
    bootstrap_assignment = next(
        node
        for node in checker_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "PYTHON_SOURCE_BOOTSTRAP"
            for target in node.targets
        )
    )
    transport["bootstrap_sha256"] = hashlib.sha256(
        ast.literal_eval(bootstrap_assignment.value).encode()
    ).hexdigest()
    accepted("source_transport", transport)
    rejected(
        "transport digest",
        "source_transport",
        {**transport, "bootstrap_sha256": "0" * 64},
    )
    rejected(
        "transport flags",
        "source_transport",
        {**transport, "isolated_flags": ["-I", "-B"]},
    )

    correction_cert_checker = git_show("scripts/check-certified-sxpid2-claim.py")
    correction_cert_selftest = git_show(
        "scripts/check-certified-sxpid2-claim-self-test.py"
    )
    old_ci_digest = b"5b34fa8061b525efdddd813aea936300718d56d3e8402fe2796a63cc70cae5c9"
    require(
        correction_cert_selftest.count(old_ci_digest) == 1,
        "certified CI authority digest moved",
    )
    candidate_cert_selftest = correction_cert_selftest.replace(
        old_ci_digest, b"0" * 64, 1
    )

    def cert_payload(checker: bytes, selftest: bytes) -> dict[str, str]:
        return {
            "candidate_checker_hex": checker.hex(),
            "candidate_selftest_hex": selftest.hex(),
            "correction_checker_hex": correction_cert_checker.hex(),
            "correction_selftest_hex": correction_cert_selftest.hex(),
        }

    accepted(
        "cert_protocol", cert_payload(correction_cert_checker, candidate_cert_selftest)
    )
    for label, checker, selftest in (
        (
            "cert protocol ast dump premise",
            correction_cert_checker + b"\nimport ast\nast.dump(ast.parse('x = 1'))\n",
            candidate_cert_selftest,
        ),
        (
            "cert protocol marshal premise",
            correction_cert_checker + b"\nimport marshal\n",
            candidate_cert_selftest,
        ),
        (
            "cert protocol bootstrap bytes",
            correction_cert_checker.replace(
                b"sys.flags.safe_path", b"sys.flags.safe_path ", 1
            ),
            candidate_cert_selftest,
        ),
        (
            "cert protocol private bytes",
            correction_cert_checker.replace(
                b"SELF_TEST_VECTOR_SCHEMA", b"SELF_TEST_VECTOR_SCHEMa", 1
            ),
            candidate_cert_selftest,
        ),
        (
            "cert protocol source launcher",
            correction_cert_checker,
            candidate_cert_selftest.replace(
                b"exec(compile(_source", b"exec(compile(_sourcE", 1
            ),
        ),
        (
            "cert protocol source size control",
            correction_cert_checker,
            candidate_cert_selftest.replace(
                b"EXPECTED_CHECKER_BOOTSTRAP_SIZE_BYTES = 668",
                b"EXPECTED_CHECKER_BOOTSTRAP_SIZE_BYTES = 669",
                1,
            ),
        ),
        (
            "cert protocol wrong old/new scope",
            correction_cert_checker,
            correction_cert_selftest,
        ),
    ):
        rejected(label, "cert_protocol", cert_payload(checker, selftest))

    provisional_freeze = {
        "digests": ["__FREEZE_STILL_PROVISIONAL__"],
        "sizes": [-1],
        "source_hex": b"__FREEZE_STILL_PROVISIONAL__".hex(),
        "state": "provisional",
    }
    frozen_freeze = {
        "digests": ["0" * 64],
        "sizes": [1],
        "source_hex": b"frozen source without placeholder".hex(),
        "state": "frozen",
    }
    accepted("freeze_inventory", provisional_freeze)
    accepted("freeze_inventory", frozen_freeze)
    require(
        CHECKER_SOURCE is not None, "checker source absent for finalized freeze vector"
    )
    finalized_checker = re.sub(rb"__FREEZE_[A-Z0-9_]+__", b"0" * 64, CHECKER_SOURCE)
    require(
        (b"__" + b"FREEZE_") not in finalized_checker,
        "synthetic finalized checker still contains a freeze placeholder",
    )
    accepted(
        "freeze_inventory",
        {**frozen_freeze, "source_hex": finalized_checker.hex()},
    )
    rejected(
        "frozen placeholder source",
        "freeze_inventory",
        {**frozen_freeze, "source_hex": b"surviving __FREEZE_TOKEN__".hex()},
    )
    rejected(
        "frozen placeholder digest",
        "freeze_inventory",
        {**frozen_freeze, "digests": ["__FREEZE_DIGEST__"]},
    )
    rejected(
        "frozen nonpositive size",
        "freeze_inventory",
        {**frozen_freeze, "sizes": [-1]},
    )

    receipt = synthetic_receipt()
    accepted("receipt", receipt)
    for alias_name, replacement in (
        ("bool", True),
        ("string", "3"),
        ("container", []),
        ("wrong integer", 2),
    ):
        rejected(
            f"receipt root schema revision {alias_name} alias",
            "receipt",
            mutate(
                receipt,
                lambda item, replacement=replacement: item.update(
                    schema_revision=copy.deepcopy(replacement)
                ),
            ),
        )
    for alias_name, replacement in (
        ("bool", False),
        ("string", "4"),
        ("container", []),
        ("wrong integer", 3),
    ):
        rejected(
            f"receipt claim revision {alias_name} alias",
            "receipt",
            mutate(
                receipt,
                lambda item, replacement=replacement: item["claim"].update(
                    revision=copy.deepcopy(replacement)
                ),
            ),
        )
    for role, aliases in (
        (
            "content",
            (
                ("bool", True),
                ("string", "2"),
                ("container", []),
                ("wrong integer", 1),
            ),
        ),
        (
            "manifest",
            (
                ("bool", True),
                ("string", "1"),
                ("container", []),
                ("wrong integer", 2),
            ),
        ),
    ):
        for alias_name, replacement in aliases:

            def mutate_receipt_content_revision(
                item: dict[str, Any],
                *,
                role: str = role,
                replacement: Any = replacement,
            ) -> None:
                def update(content: dict[str, Any]) -> None:
                    target = (
                        content if role == "content" else content["binding"]["manifest"]
                    )
                    target["schema_revision"] = copy.deepcopy(replacement)

                coordinated_content_mutation(item, update)

            rejected(
                f"receipt coordinated postcommit {role} schema revision "
                f"{alias_name} alias",
                "receipt",
                mutate(receipt, mutate_receipt_content_revision),
            )
    rejected(
        "receipt stray nested revision",
        "receipt",
        mutate(receipt, lambda item: item["milestone"].update(revision=4)),
    )
    rejected(
        "receipt stray nested schema revision",
        "receipt",
        mutate(receipt, lambda item: item["milestone"].update(schema_revision=3)),
    )
    rejected(
        "receipt implementation API jobs bool alias",
        "receipt",
        mutate(
            receipt,
            lambda item: item["hosted_observations"]["implementation_codeql_success"][
                "api_captures"
            ][1]["projection"].update(jobs=True),
        ),
    )
    rejected(
        "receipt implementation API jobs integer alias",
        "receipt",
        mutate(
            receipt,
            lambda item: item["hosted_observations"]["implementation_codeql_success"][
                "api_captures"
            ][1]["projection"].update(jobs=4),
        ),
    )
    phase = phase_vector(receipt)
    accepted("recovery_phase", phase)
    rejected(
        "phase outer role swap",
        "recovery_phase",
        mutate(
            phase,
            lambda item: item["custody"].update(
                precommit_outputs=item["custody"]["postcommit_outputs"],
                postcommit_outputs=item["custody"]["precommit_outputs"],
            ),
        ),
    )
    rejected(
        "phase duplicate precommit role",
        "recovery_phase",
        mutate(
            phase,
            lambda item: item["custody"].update(
                postcommit_outputs=copy.deepcopy(item["custody"]["precommit_outputs"])
            ),
        ),
    )
    rejected(
        "phase outer descriptor reseal",
        "recovery_phase",
        mutate(
            phase,
            lambda item: item["custody"]["policy"].update(path="wrong/policy.json"),
        ),
    )
    rejected(
        "phase all-four policy reseal",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item, lambda output: output.update(policy_sha256="1" * 64)
            ),
        ),
    )
    rejected(
        "phase all-four candidate reseal",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item, lambda output: output["candidate"].update(tree="2" * 40)
            ),
        ),
    )
    rejected(
        "phase coordinated negative jobs bool alias",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output["negative_evidence"].update(jobs=True),
            ),
        ),
    )
    rejected(
        "phase coordinated negative jobs container alias",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output["negative_evidence"].update(jobs=[]),
            ),
        ),
    )
    rejected(
        "phase coordinated stray nested revision",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output["negative_evidence"].update(revision=4),
            ),
        ),
    )
    rejected(
        "phase coordinated stray nested schema revision",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output["negative_evidence"].update(schema_revision=1),
            ),
        ),
    )
    rejected(
        "phase all-four child reseal",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output["child_output_sha256"].update(
                    {"scripts/check-certified-sxpid2-claim.py": "2" * 64}
                ),
            ),
        ),
    )
    rejected(
        "phase coordinated missing prior r7",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_lean_phase_mutation(
                item, lambda replay_item: replay_item.pop("prior_r7_sha256")
            ),
        ),
    )
    rejected(
        "phase coordinated wrong prior r7",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_lean_phase_mutation(
                item,
                lambda replay_item: replay_item.update(prior_r7_sha256="0" * 64),
            ),
        ),
    )
    rejected(
        "phase coordinated extra lean r8 property",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_lean_phase_mutation(
                item, lambda replay_item: replay_item.update(extra="0" * 64)
            ),
        ),
    )
    rejected(
        "phase coordinated old lean r7 role",
        "recovery_phase",
        mutate(
            phase,
            lambda item: coordinated_phase_mutation(
                item,
                lambda output: output.__setitem__("lean_r7", output.pop("lean_r8")),
            ),
        ),
    )
    rejected(
        "phase alternate cross-bind",
        "recovery_phase",
        mutate(
            phase,
            lambda item: item["custody"]["alternate_index"].update(
                sha256="2" * 64,
                retained_index_artifact={
                    **item["custody"]["alternate_index"]["retained_index_artifact"],
                    "sha256": "2" * 64,
                },
            ),
        ),
    )

    postcommit_vector = {
        "content": copy.deepcopy(
            receipt["hosted_observations"]["recovery_ci_success"][
                "postcommit_source_state_v2_content"
            ]
        ),
        "expected_manifest": copy.deepcopy(
            receipt["hosted_observations"]["recovery_ci_success"][
                "postcommit_source_state_v2_content"
            ]["binding"]["manifest"]
        ),
        "head": receipt["hosted_recovery"]["commit"],
        "tree": receipt["hosted_recovery"]["tree"],
    }
    accepted("postcommit_content", postcommit_vector)
    rejected(
        "postcommit content manifest reseal",
        "postcommit_content",
        mutate(
            postcommit_vector,
            lambda item: item["content"]["binding"]["manifest"].update(sha256="2" * 64),
        ),
    )
    rejected(
        "postcommit content tree",
        "postcommit_content",
        mutate(
            postcommit_vector,
            lambda item: item["content"]["binding"].update(tree_oid="2" * 40),
        ),
    )
    for role, path, aliases in (
        (
            "content",
            ("content",),
            (
                ("bool", True),
                ("string", "2"),
                ("container", []),
                ("wrong integer", 1),
            ),
        ),
        (
            "manifest",
            ("content", "binding", "manifest"),
            (
                ("bool", True),
                ("string", "1"),
                ("container", []),
                ("wrong integer", 2),
            ),
        ),
    ):
        for alias_name, replacement in aliases:

            def mutate_schema_revision(
                item: dict[str, Any],
                *,
                path: tuple[str, ...] = path,
                replacement: Any = replacement,
            ) -> None:
                target = item
                for component in path:
                    target = target[component]
                target["schema_revision"] = copy.deepcopy(replacement)

            rejected(
                f"postcommit {role} schema revision {alias_name} alias",
                "postcommit_content",
                mutate(postcommit_vector, mutate_schema_revision),
            )
    rejected(
        "postcommit content stray nested revision",
        "postcommit_content",
        mutate(
            postcommit_vector,
            lambda item: item["content"]["checks"].update(revision=1),
        ),
    )
    rejected(
        "postcommit content stray nested schema revision",
        "postcommit_content",
        mutate(
            postcommit_vector,
            lambda item: item["content"]["checks"].update(schema_revision=1),
        ),
    )
    boolean_fields = checker_literal("BOOLEAN_JSON_FIELDS")
    integer_fields = checker_literal("INTEGER_JSON_FIELDS")
    integer_list_fields = checker_literal("INTEGER_JSON_LIST_FIELDS")
    require(
        boolean_fields == EXPECTED_BOOLEAN_FIELDS
        and integer_fields == EXPECTED_INTEGER_FIELDS
        and integer_list_fields == EXPECTED_INTEGER_LIST_FIELDS
        and not boolean_fields & integer_fields
        and not boolean_fields & integer_list_fields
        and not integer_fields & integer_list_fields,
        "scalar field inventories overlap or changed type",
    )
    scalar_payload = {
        **{field: True for field in boolean_fields},
        **{field: 2 for field in integer_fields},
        **{field: [2] for field in integer_list_fields},
    }
    accepted("scalar_types", scalar_payload)
    positive_corpus = (
        policy,
        negative,
        lean_r7,
        active_packet,
        current_source,
        implementation_negative,
        receipt,
        phase,
        postcommit_vector,
        scalar_payload,
    )
    integer_kinds = observed_field_kinds(positive_corpus, integer_fields)
    boolean_kinds = observed_field_kinds(positive_corpus, boolean_fields)
    integer_list_kinds = observed_field_kinds(positive_corpus, integer_list_fields)
    jobs_kinds = observed_field_kinds(positive_corpus, {"jobs"})["jobs"]
    require(
        jobs_kinds == {"int", "list"}
        and all(kinds == {"int"} for kinds in integer_kinds.values())
        and all(kinds == {"bool"} for kinds in boolean_kinds.values())
        and all(kinds == {"list"} for kinds in integer_list_kinds.values()),
        "positive scalar corpus gained an unreviewed name/type collision",
    )
    for field in sorted(boolean_fields):
        rejected(
            f"boolean alias {field}",
            "scalar_types",
            {**scalar_payload, field: 1},
        )
    for field in sorted(integer_fields):
        rejected(
            f"integer boolean alias {field}",
            "scalar_types",
            {**scalar_payload, field: True},
        )
        rejected(
            f"integer list alias {field}",
            "scalar_types",
            {**scalar_payload, field: [2]},
        )
        rejected(
            f"integer object alias {field}",
            "scalar_types",
            {**scalar_payload, field: {}},
        )
        rejected(
            f"integer string alias {field}",
            "scalar_types",
            {**scalar_payload, field: "2"},
        )
        malformed_rejected(
            f"integer float alias {field}",
            vector("scalar_types", scalar_payload).replace(
                f'"{field}": 2'.encode(), f'"{field}": 2.0'.encode(), 1
            ),
        )
    for field in sorted(integer_list_fields):
        rejected(
            f"integer-list boolean alias {field}",
            "scalar_types",
            {**scalar_payload, field: [True]},
        )
        rejected(
            f"integer-list nested list alias {field}",
            "scalar_types",
            {**scalar_payload, field: [[2]]},
        )
        rejected(
            f"integer-list nested empty-list alias {field}",
            "scalar_types",
            {**scalar_payload, field: [[]]},
        )
        rejected(
            f"integer-list object element alias {field}",
            "scalar_types",
            {**scalar_payload, field: [{}]},
        )
        rejected(
            f"integer-list string element alias {field}",
            "scalar_types",
            {**scalar_payload, field: ["2"]},
        )
        rejected(
            f"integer-list object alias {field}",
            "scalar_types",
            {**scalar_payload, field: {}},
        )
        rejected(
            f"integer-list scalar alias {field}",
            "scalar_types",
            {**scalar_payload, field: 2},
        )
        malformed_rejected(
            f"integer-list float alias {field}",
            vector("scalar_types", scalar_payload).replace(
                f'"{field}": [\n      2\n    ]'.encode(),
                f'"{field}": [\n      2.0\n    ]'.encode(),
                1,
            ),
        )
    jobs_payload = {"api_jobs": [{"job_id": 2}], "phase_jobs": 45}
    accepted("jobs", jobs_payload)
    for alias_name, replacement in (
        ("integer", 45),
        ("bool", True),
        ("object", {}),
        ("scalar-list", [2]),
        ("string-list", ["job"]),
    ):
        rejected(
            f"API jobs {alias_name} alias",
            "jobs",
            {**jobs_payload, "api_jobs": replacement},
        )
    for alias_name, replacement in (
        ("list", []),
        ("object", {}),
        ("bool", True),
        ("string", "45"),
    ):
        rejected(
            f"phase jobs {alias_name} alias",
            "jobs",
            {**jobs_payload, "phase_jobs": replacement},
        )
    malformed_rejected(
        "phase jobs float alias",
        vector("jobs", jobs_payload).replace(
            b'"phase_jobs": 45', b'"phase_jobs": 45.0'
        ),
    )
    for label, operation in (
        (
            "receipt full coordinated recovery index reseal",
            coordinated_recovery_index_reseal,
        ),
        (
            "receipt full coordinated recovery identity reseal",
            coordinated_recovery_identity_reseal,
        ),
        (
            "receipt coordinated recovery CI attempt bool alias",
            lambda item: coordinated_ci_mutation(
                item, lambda ci: ci.update(attempt=True)
            ),
        ),
        (
            "receipt coordinated recovery manifest revision bool alias",
            lambda item: coordinated_content_mutation(
                item,
                lambda content: content["binding"]["manifest"].update(
                    schema_revision=True
                ),
            ),
        ),
        (
            "receipt coordinated recovery CodeQL alert bound bool alias",
            lambda item: coordinated_codeql_mutation(
                item,
                lambda ql: ql["alert_state"].update(minimum_alert_number=True),
            ),
        ),
        (
            "receipt coordinated recovery CodeQL attempt bool alias",
            lambda item: coordinated_codeql_mutation(
                item, lambda ql: ql.update(attempt=True)
            ),
        ),
        (
            "receipt coordinated phase const reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output.update(credit="local_credit")
            ),
        ),
        (
            "receipt coordinated phase enum reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output.update(lifecycle="unknown_lifecycle")
            ),
        ),
        (
            "receipt coordinated phase extension reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output["certified_sxpid_recovery"].update(extra=True),
            ),
        ),
        (
            "receipt coordinated lean r8 missing prior r7",
            lambda item: coordinated_receipt_lean_phase_mutation(
                item, lambda replay_item: replay_item.pop("prior_r7_sha256")
            ),
        ),
        (
            "receipt coordinated lean r8 wrong prior r7",
            lambda item: coordinated_receipt_lean_phase_mutation(
                item,
                lambda replay_item: replay_item.update(prior_r7_sha256="0" * 64),
            ),
        ),
        (
            "receipt coordinated lean r8 extra property",
            lambda item: coordinated_receipt_lean_phase_mutation(
                item, lambda replay_item: replay_item.update(extra="0" * 64)
            ),
        ),
        (
            "receipt coordinated old lean r7 role",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output.__setitem__("lean_r7", output.pop("lean_r8")),
            ),
        ),
        (
            "receipt coordinated phase max-items reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output["candidate"]["delta"].append(
                    {"mode": "100644", "path": "extra/path", "status": "A"}
                ),
            ),
        ),
        (
            "receipt coordinated phase min-items reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output["candidate"]["delta"].pop()
            ),
        ),
        (
            "receipt coordinated phase unique-items reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output["candidate"]["delta"].__setitem__(
                    1, copy.deepcopy(output["candidate"]["delta"][0])
                ),
            ),
        ),
        (
            "receipt coordinated phase maximum reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output["negative_evidence"].update(failed_jobs=46)
            ),
        ),
        (
            "receipt coordinated phase minimum reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output["negative_evidence"].update(failed_jobs=0)
            ),
        ),
        (
            "receipt coordinated phase pattern reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output["certified_sxpid_recovery"][
                    "four_container_digest_literals"
                ].update(certified_checker="G" * 64),
            ),
        ),
        (
            "receipt coordinated phase required reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: output["child_output_sha256"].pop(
                    "scripts/check-certified-sxpid2-claim.py"
                ),
            ),
        ),
        (
            "receipt coordinated phase type reseal",
            lambda item: coordinated_receipt_phase_mutation(
                item, lambda output: output.update(repository_state=[])
            ),
        ),
        (
            "receipt coordinated phase alternate residency bool alias",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: (
                    output["candidate"]["alternate_index_custody"].update(
                        path_or_residency_claimed=0
                    )
                    if output["candidate"]["alternate_index_custody"] is not None
                    else None
                ),
            ),
        ),
        (
            "receipt coordinated phase alternate observation bool alias",
            lambda item: coordinated_receipt_phase_mutation(
                item,
                lambda output: (
                    output["candidate"]["alternate_index_custody"].update(
                        precommit_descriptor_observation_authenticated=0
                    )
                    if output["candidate"]["alternate_index_custody"] is not None
                    else None
                ),
            ),
        ),
        (
            "receipt coordinated precommit alternate object type",
            lambda item: coordinated_receipt_alternate_replacement(
                item, "precommit_outputs", []
            ),
        ),
        (
            "receipt coordinated precommit alternate residency missing",
            lambda item: coordinated_receipt_alternate_key_removal(
                item, "path_or_residency_claimed"
            ),
        ),
        (
            "receipt coordinated precommit alternate observation missing",
            lambda item: coordinated_receipt_alternate_key_removal(
                item, "precommit_descriptor_observation_authenticated"
            ),
        ),
        (
            "receipt coordinated postcommit alternate null type",
            lambda item: coordinated_receipt_alternate_replacement(
                item, "postcommit_outputs", "not-null"
            ),
        ),
        *(
            (
                f"receipt correction custody {artifact_key} oversize",
                lambda item, artifact_key=artifact_key: item[
                    "correction_local_phase_custody"
                ][artifact_key].update(size_bytes=33_554_433),
            )
            for artifact_key in ("boundary", "checker", "policy", "self_test")
        ),
        (
            "receipt correction sealed residency bool alias",
            lambda item: item["custody_correction"]["sealed_index"].update(
                path_or_residency_claimed=0
            ),
        ),
        (
            "receipt correction sealed observation bool alias",
            lambda item: item["custody_correction"]["sealed_index"].update(
                precommit_descriptor_observation_authenticated=0
            ),
        ),
        (
            "receipt recovery sealed residency bool alias",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                path_or_residency_claimed=0
            ),
        ),
        (
            "receipt recovery sealed observation bool alias",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                precommit_descriptor_observation_authenticated=0
            ),
        ),
        (
            "receipt recovery CI object type",
            lambda item: item["hosted_observations"].update(recovery_ci_success=[]),
        ),
        (
            "receipt recovery CI capture item type",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ].__setitem__(0, []),
        ),
        (
            "receipt recovery CI capture maximum",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ].append(None),
        ),
        (
            "receipt recovery CodeQL object type",
            lambda item: item["hosted_observations"].update(recovery_codeql_success=[]),
        ),
        (
            "receipt recovery CodeQL capture item type",
            lambda item: item["hosted_observations"]["recovery_codeql_success"][
                "api_captures"
            ].__setitem__(0, []),
        ),
        (
            "receipt recovery CodeQL capture maximum",
            lambda item: item["hosted_observations"]["recovery_codeql_success"][
                "api_captures"
            ].append(None),
        ),
        (
            "receipt correction sealed path",
            lambda item: item["custody_correction"]["sealed_index"].update(
                path="wrong/correction-index.bin"
            ),
        ),
        (
            "receipt correction sealed digest",
            lambda item: item["custody_correction"]["sealed_index"].update(
                sha256="2" * 64
            ),
        ),
        (
            "receipt correction sealed size",
            lambda item: item["custody_correction"]["sealed_index"].update(
                size_bytes=87_964
            ),
        ),
        (
            "receipt correction sealed count",
            lambda item: item["custody_correction"]["sealed_index"].update(
                entry_count=725
            ),
        ),
        (
            "receipt correction sealed blob",
            lambda item: item["custody_correction"]["sealed_index"].update(
                git_blob_oid_sha1="2" * 40
            ),
        ),
        (
            "receipt correction sealed reconstruction",
            lambda item: item["custody_correction"]["sealed_index"].update(
                reconstructs_tree_twice=False
            ),
        ),
        (
            "receipt recovery sealed correction path",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                path="audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin"
            ),
        ),
        (
            "receipt recovery sealed digest",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                sha256="2" * 64
            ),
        ),
        (
            "receipt recovery sealed size",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                size_bytes=90_001
            ),
        ),
        (
            "receipt recovery sealed count",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                entry_count=733
            ),
        ),
        (
            "receipt recovery sealed blob",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                git_blob_oid_sha1="2" * 40
            ),
        ),
        (
            "receipt recovery sealed reconstruction",
            lambda item: item["hosted_recovery"]["sealed_index"].update(
                reconstructs_tree_twice=False
            ),
        ),
        (
            "receipt reciprocal sealed descriptor swap",
            lambda item: item.update(
                custody_correction={
                    **item["custody_correction"],
                    "sealed_index": copy.deepcopy(
                        item["hosted_recovery"]["sealed_index"]
                    ),
                },
                hosted_recovery={
                    **item["hosted_recovery"],
                    "sealed_index": copy.deepcopy(
                        item["custody_correction"]["sealed_index"]
                    ),
                },
            ),
        ),
        (
            "receipt recovery trailer digest",
            lambda item: item["hosted_recovery"].update(
                commit_message=item["hosted_recovery"]["commit_message"].replace(
                    "Sealed-index-SHA256: ", "Sealed-index-SHA256: " + "2" * 64 + "#"
                )
            ),
        ),
        (
            "receipt recovery trailer size",
            lambda item: item["hosted_recovery"].update(
                commit_message=item["hosted_recovery"]["commit_message"].replace(
                    "Sealed-index-Size: 90000", "Sealed-index-Size: 90001"
                )
            ),
        ),
        (
            "receipt correction negative artifact path",
            lambda item: item["hosted_observations"][
                "correction_negative_evidence_artifact"
            ].update(path="wrong/correction-negative.json"),
        ),
        (
            "receipt correction negative artifact digest",
            lambda item: item["hosted_observations"][
                "correction_negative_evidence_artifact"
            ].update(sha256="2" * 64),
        ),
        (
            "receipt correction negative artifact size",
            lambda item: item["hosted_observations"][
                "correction_negative_evidence_artifact"
            ].update(size_bytes=1),
        ),
        (
            "receipt implementation negative artifact path",
            lambda item: item["hosted_observations"][
                "implementation_negative_evidence_artifact"
            ].update(path="wrong/implementation-negative.json"),
        ),
        (
            "receipt implementation negative artifact digest",
            lambda item: item["hosted_observations"][
                "implementation_negative_evidence_artifact"
            ].update(sha256="2" * 64),
        ),
        (
            "receipt recovery alternate retained path",
            lambda item: item["recovery_local_phase_custody"]["alternate_index"][
                "retained_index_artifact"
            ].update(
                path="audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin"
            ),
        ),
        (
            "receipt recovery alternate parent digest",
            lambda item: item["recovery_local_phase_custody"]["alternate_index"].update(
                sha256="2" * 64
            ),
        ),
        (
            "receipt recovery custody boundary path",
            lambda item: item["recovery_local_phase_custody"]["boundary"].update(
                path="wrong/recovery-boundary.md"
            ),
        ),
        (
            "receipt recovery custody checker digest",
            lambda item: item["recovery_local_phase_custody"]["checker"].update(
                sha256="2" * 64
            ),
        ),
        (
            "receipt correction diagnostic class rewrite",
            lambda item: item["hosted_observations"]["correction_ci_failure"][
                "failed_diagnostics"
            ][0].update(exception_class="rewritten"),
        ),
        (
            "receipt correction diagnostic message rewrite",
            lambda item: item["hosted_observations"]["correction_ci_failure"][
                "failed_diagnostics"
            ][0].update(exception_message="rewritten"),
        ),
        (
            "receipt correction parent",
            lambda item: item["custody_correction"].update(direct_parent="0" * 40),
        ),
        (
            "receipt recovery parent",
            lambda item: item["hosted_recovery"].update(direct_parent=IMPLEMENTATION),
        ),
        (
            "receipt head transfer",
            lambda item: item["hosted_observations"]["correction_ci_failure"].update(
                head_sha=IMPLEMENTATION
            ),
        ),
        (
            "receipt failed relabel",
            lambda item: item["hosted_observations"]["correction_ci_failure"].update(
                conclusion="success"
            ),
        ),
        (
            "receipt recovery failure",
            lambda item: item["hosted_observations"]["recovery_ci_success"].update(
                conclusion="failure"
            ),
        ),
        (
            "receipt recovery capture endpoint",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ][0].update(endpoint_class="ci_artifact_inventory"),
        ),
        (
            "receipt recovery capture digest",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ][1].update(sha256="0" * 64),
        ),
        (
            "receipt recovery capture order",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ].reverse(),
        ),
        (
            "receipt recovery job name",
            lambda item: coordinated_ci_mutation(
                item, lambda ci: ci["job_roster"][0].update(name="fabricated job")
            ),
        ),
        (
            "receipt recovery timestamp",
            lambda item: coordinated_ci_mutation(
                item, lambda ci: ci["job_roster"][0].update(started_at="not-time")
            ),
        ),
        (
            "receipt recovery interval",
            lambda item: coordinated_ci_mutation(
                item,
                lambda ci: ci["job_roster"][0].update(
                    started_at="2099-01-01T00:00:00Z"
                ),
            ),
        ),
        (
            "receipt recovery alert baseline",
            lambda item: coordinated_codeql_mutation(
                item,
                lambda ql: ql["alert_state"].update(
                    baseline_alert_numbers=[999],
                    observed_alert_numbers=[999],
                    open_alert_numbers=[999],
                    dismissed_alert_numbers=[],
                    fixed_alert_numbers=[],
                    open=1,
                    dismissed=0,
                    fixed=0,
                    total=1,
                    minimum_alert_number=999,
                    maximum_alert_number=999,
                ),
            ),
        ),
        (
            "receipt recovery run reuse",
            lambda item: coordinated_ci_mutation(
                item, lambda ci: ci.update(run_id=31686107959)
            ),
        ),
        (
            "receipt recovery CI job reuse",
            lambda item: coordinated_ci_mutation(
                item,
                lambda ci: ci["job_roster"][0].update(
                    job_id=item["hosted_observations"]["correction_ci_failure"][
                        "job_roster"
                    ][0]["job_id"]
                ),
            ),
        ),
        (
            "receipt cross CI-CodeQL job reuse",
            lambda item: coordinated_ci_mutation(
                item,
                lambda ci: ci["job_roster"][0].update(
                    job_id=item["hosted_observations"]["implementation_codeql_success"][
                        "job_roster"
                    ][0]["job_id"]
                ),
            ),
        ),
        (
            "receipt recovery analysis duplicate",
            lambda item: coordinated_codeql_mutation(
                item,
                lambda ql: ql["analysis_roster"][1].update(
                    analysis_id=ql["analysis_roster"][0]["analysis_id"]
                ),
            ),
        ),
        (
            "receipt recovery analysis reorder",
            lambda item: coordinated_codeql_mutation(
                item, lambda ql: ql["analysis_roster"].reverse()
            ),
        ),
        (
            "receipt recovery analysis reuse",
            lambda item: coordinated_codeql_mutation(
                item,
                lambda ql: ql["analysis_roster"][0].update(
                    analysis_id=item["hosted_observations"][
                        "correction_codeql_success"
                    ]["analysis_roster"][0]["analysis_id"]
                ),
            ),
        ),
        (
            "receipt recovery analysis job permutation",
            lambda item: coordinated_codeql_mutation(item, permute_analysis_job_ids),
        ),
        (
            "receipt recovery analysis category",
            lambda item: coordinated_codeql_mutation(
                item,
                lambda ql: ql["analysis_roster"][0].update(category="/language:python"),
            ),
        ),
        (
            "receipt recovery alert category overlap",
            lambda item: coordinated_codeql_mutation(item, overlap_alert_categories),
        ),
        (
            "receipt recovery successful step failure",
            lambda item: coordinated_ci_mutation(
                item,
                lambda ci: ci["job_roster"][0]["steps"][0].update(conclusion="failure"),
            ),
        ),
        (
            "receipt recovery artifact reuse",
            lambda item: coordinated_ci_mutation(
                item,
                lambda ci: ci["postcommit_source_state_v2"].update(
                    artifact_id=item["hosted_observations"]["correction_ci_failure"][
                        "postcommit_source_state_v2"
                    ]["artifact_id"]
                ),
            ),
        ),
        (
            "receipt content constant reseal",
            lambda item: coordinated_content_mutation(
                item,
                lambda content: content.update(evidence_class="scientific_evidence"),
            ),
        ),
        (
            "receipt legacy content digest",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "postcommit_source_state_v2"
            ].update(content_sha256="2" * 64),
        ),
        (
            "receipt legacy content size",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "postcommit_source_state_v2"
            ].update(content_size_bytes=1),
        ),
        (
            "receipt content capture digest",
            lambda item: item["hosted_observations"]["recovery_ci_success"][
                "api_captures"
            ][2].update(sha256="2" * 64),
        ),
        (
            "receipt remote timestamp order",
            lambda item: item["remote_observations"].update(
                observed_at="2000-01-01T00:00:00Z"
            ),
        ),
        (
            "receipt recovery equals correction",
            lambda item: item["hosted_recovery"].update(commit=CORRECTION),
        ),
        (
            "receipt revision bool alias",
            lambda item: item["revision4_integration"].update(
                decision_v4_absent_at_recovery=1
            ),
        ),
        (
            "receipt postcommit bool alias",
            lambda item: coordinated_content_mutation(
                item,
                lambda content: content["checks"].update(
                    current_manifest_checker_passed=1
                ),
            ),
        ),
        (
            "receipt remote split",
            lambda item: item["remote_observations"].update(
                observed_remote_head="0" * 40
            ),
        ),
        (
            "receipt local phase hash",
            lambda item: item["correction_local_phase_custody"]["precommit_outputs"][
                "normal"
            ].update(sha256="0" * 64),
        ),
        (
            "receipt r6 output",
            lambda item: item["correction_local_phase_custody"]["postcommit_outputs"][
                "normal"
            ]["output"]["lean_r6"].update(receipt_sha256="0" * 64),
        ),
        ("receipt route", lambda item: item.update(schema="wrong")),
        (
            "receipt evidence class",
            lambda item: item.update(evidence_class="scientific_evidence"),
        ),
        ("receipt milestone", lambda item: item["milestone"].update(status="complete")),
        (
            "receipt integration",
            lambda item: item["revision4_integration"].update(status="integration_go"),
        ),
        ("receipt semantics", lambda item: item["negative_evidence_semantics"].pop()),
        ("receipt nonclaims", lambda item: item.update(nonimplications=[])),
    ):
        rejected(label, "receipt", mutate(receipt, operation))

    malformed_rejected(
        "duplicate key", b'{"payload":{},"payload":{},"schema":"x","validator":"x"}\n'
    )
    malformed_rejected("trailing bytes", vector("history", history) + b"x")
    malformed_rejected(
        "float",
        b'{"payload":1.0,"schema":"pid-rs/ksg-rev4-m1a-hosted-recovery-self-test-vector/v1","validator":"history"}\n',
    )
    malformed_rejected(
        "huge integer",
        (
            b'{"payload":{"count":'
            + b"9" * 5000
            + b'},"schema":"pid-rs/ksg-rev4-m1a-hosted-recovery-self-test-vector/v1","validator":"protected"}\n'
        ),
    )
    malformed_rejected("oversize", b" " * (MAX_REQUEST_BYTES + 1))

    plain = invoke(["--validate-policy-only"])
    provisional = invoke(["--validate-policy-only", "--allow-provisional-diagnostic"])
    selected = plain
    require(
        plain.returncode == provisional.returncode == 0
        and not plain.stderr
        and not provisional.stderr
        and plain.stdout == provisional.stdout,
        "policy compatibility-flag/no-flag matrix changed",
    )
    report = json.loads(selected.stdout)
    require(
        report.get("disposition") == "local_hosted_pending_no_credit"
        and report.get("entry_count") == 27
        and report.get("correction_commit") == CORRECTION
        and report.get("protected_projection")
        == {"entry_count": 83, "sha256": PROTECTED_SHA},
        "policy CLI overcredited or lost exact anchors",
    )
    require(
        stable_read(CHECKER) == (checker_raw, checker_identity)
        and stable_read(SCRIPT) == (selftest_raw, selftest_identity)
        and stable_read(LEAN_R7) == (lean_r7_raw, lean_r7_identity)
        and stable_read(ACTIVE_PACKET) == (active_packet_raw, active_packet_identity)
        and stable_read(CURRENT_SOURCE)
        == (current_source_raw, current_source_identity),
        "checker/self-test fixture source changed during suite",
    )
    print("OK: KSG M1a hosted-recovery CLI hostile suite passed")
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
        print(f"KSG M1a hosted-recovery self-test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
