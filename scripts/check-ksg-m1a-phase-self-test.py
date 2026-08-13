#!/usr/bin/env python3
"""Bounded hostile tests for the KSG revision-4 M1a phase checker."""

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
        "ERROR: check-ksg-m1a-phase-self-test.py requires Python 3.11+ -I -S -B and at most one -O",
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
CHECKER_PATH = ROOT / "scripts/check-ksg-m1a-phase.py"
POLICY_PATH = ROOT / "audit/evidence/ksg-rev4-m1a-path-policy-v1.json"
SCHEMA_PATH = ROOT / "audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json"
BOUNDARY_PATH = ROOT / "audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md"
EXPECTED_POLICY_SCHEMA_MUTATIONS = 42
MAX_SOURCE_BYTES = 4 * 1024 * 1024
SELF_TEST_VECTOR_SCHEMA = "pid-rs/ksg-rev4-m1a-self-test-vector/v1"
PASS_OUTPUT = b'{"result":"pass"}\n'
FAIL_OUTPUT = b'{"result":"fail"}\n'
CHECKER_OPTIONS = {
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
}
PYC_MAGIC_BY_MINOR = {
    (3, 11): bytes.fromhex("a70d0d0a"),
    (3, 12): bytes.fromhex("cb0d0d0a"),
    (3, 13): bytes.fromhex("f30d0d0a"),
    (3, 14): bytes.fromhex("2b0e0d0a"),
}


class SelfTestError(RuntimeError):
    """The M1a hostile suite produced an unexpected result."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


class PhaseError(RuntimeError):
    """A validator rejected one CLI self-test vector."""


@dataclass(frozen=True)
class Entry:
    mode: str
    oid: str


@dataclass(frozen=True)
class PolicyEntry:
    path: str
    status: str
    review_class: str


def malicious_adjacent_cache_payload() -> None:
    """Payload embedded in an unchecked-hash cache; it must never execute."""

    with open(  # noqa: PTH123 -- intentionally self-contained hostile bytecode.
        "adjacent-pyc-executed", "wb"
    ) as stream:
        stream.write(b"unchecked hash cache executed")


def canonical_json(value: Any, *, pretty: bool) -> bytes:
    if pretty:
        rendered = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
    else:
        rendered = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    return (rendered + "\n").encode("utf-8")


def stable_source(path: Path) -> bytes:
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f"source is not regular: {path}")
    require(before.st_nlink == 1, f"source is hard-linked: {path}")
    require(0 < before.st_size <= MAX_SOURCE_BYTES, f"source size is invalid: {path}")
    raw = path.read_bytes()
    after = path.lstat()
    identity = lambda item: (  # noqa: E731 -- compact immutable stat projection.
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )
    require(identity(before) == identity(after), f"source changed while read: {path}")
    require(len(raw) == before.st_size, f"source read was short: {path}")
    return raw


def validate_static_cli_custody() -> None:
    forbidden_imports = {"importlib", "runpy"}
    forbidden_calls = {"__import__", "compile", "eval", "exec"}
    forbidden_attributes = {
        "exec_module",
        "module_from_spec",
        "run_module",
        "run_path",
        "spec_from_file_location",
    }
    checker_options: set[str] = set()
    checker_abbreviations_disabled = False
    for path in (CHECKER_PATH, SCRIPT):
        raw = stable_source(path)
        try:
            tree = ast.parse(
                raw.decode("utf-8", errors="strict"), filename=os.fspath(path)
            )
        except (SyntaxError, UnicodeDecodeError) as error:
            raise SelfTestError(
                f"cannot parse fixed CLI source {path}: {error}"
            ) from error
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                raise SelfTestError(f"optimization-sensitive assert in {path}")
            if isinstance(node, ast.Import):
                roots = {alias.name.partition(".")[0] for alias in node.names}
                require(
                    not roots & forbidden_imports,
                    f"dynamic loader import in {path}",
                )
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").partition(".")[0]
                require(
                    root not in forbidden_imports, f"dynamic loader import in {path}"
                )
            elif isinstance(node, ast.Call):
                if path == CHECKER_PATH and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "ArgumentParser":
                        for keyword in node.keywords:
                            if keyword.arg == "allow_abbrev":
                                checker_abbreviations_disabled = (
                                    isinstance(keyword.value, ast.Constant)
                                    and keyword.value.value is False
                                )
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
                if path == CHECKER_PATH and isinstance(node.func, ast.Attribute):
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
    require(
        checker_abbreviations_disabled,
        "checker CLI re-enabled abbreviated options",
    )


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


def invoke_checker(
    arguments: list[str],
    *,
    stdin_bytes: bytes | None = None,
    stdin_descriptor: int | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[bytes]:
    require(
        (stdin_bytes is None) != (stdin_descriptor is None),
        "checker invocation needs exactly one standard-input source",
    )
    command = [*PYTHON_CHILD_PREFIX, os.fspath(CHECKER_PATH), *arguments]
    try:
        if stdin_bytes is not None:
            return subprocess.run(
                command,
                cwd=ROOT,
                env=safe_environment(),
                input=stdin_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        require(
            stdin_descriptor is not None,
            "checker descriptor source disappeared after validation",
        )
        return subprocess.run(
            command,
            cwd=ROOT,
            env=safe_environment(),
            stdin=stdin_descriptor,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SelfTestError(f"fixed checker invocation failed: {error}") from error


def create_anchor_index(path: Path, tree: str) -> None:
    environment = safe_environment()
    environment["GIT_INDEX_FILE"] = os.fspath(path)
    command = [
        "/usr/bin/git",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.untrackedCache=false",
        "-C",
        os.fspath(ROOT),
        "read-tree",
        tree,
    ]
    try:
        completed = subprocess.run(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SelfTestError(f"cannot construct sealed anchor index: {error}") from error
    require(
        completed.returncode == 0
        and completed.stdout == b""
        and completed.stderr == b"",
        "fixed Git could not construct the sealed anchor index",
    )


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


def validate_adjacent_unchecked_hash_pyc_nonexecution(
    baseline_vector: bytes,
) -> None:
    version = (sys.version_info.major, sys.version_info.minor)
    magic = PYC_MAGIC_BY_MINOR.get(version)
    require(magic is not None, f"unregistered Python bytecode magic: {version}")
    cache_tag = sys.implementation.cache_tag
    require(isinstance(cache_tag, str) and cache_tag, "Python cache tag is absent")
    unchecked_hash_header = magic + (1).to_bytes(4, "little") + b"\0" * 8
    malicious_cache = unchecked_hash_header + marshal.dumps(
        malicious_adjacent_cache_payload.__code__
    )
    with tempfile.TemporaryDirectory(prefix="pid-rs-ksg-m1a-pyc-custody-") as temporary:
        fixture_root = Path(temporary).resolve(strict=True)
        fixture_scripts = fixture_root / "scripts"
        fixture_scripts.mkdir(mode=0o700)
        fixture_checker = fixture_scripts / CHECKER_PATH.name
        checker_source = stable_source(CHECKER_PATH)
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
        marker = fixture_root / "adjacent-pyc-executed"
        command = [
            *PYTHON_CHILD_PREFIX,
            os.fspath(fixture_checker),
            "--self-test-vectors",
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=fixture_root,
                env=safe_environment(),
                input=baseline_vector,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise SelfTestError(
                f"temporary direct checker invocation failed: {error}"
            ) from error
        require(not marker.exists(), "adjacent unchecked-hash checker cache executed")
        require(
            completed.returncode == 0
            and completed.stdout == PASS_OUTPUT
            and completed.stderr == b"",
            "adjacent unchecked-hash cache changed fixed direct-script execution",
        )


class CheckerCli:
    """Typed proxy whose validators always cross the fixed checker CLI."""

    PhaseError = PhaseError
    Entry = Entry
    PolicyEntry = PolicyEntry
    FINAL_MATRIX = "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md"
    FUTURE_RECEIPT = (
        "audit/evidence/ksg-rev4-m1a-implementation-receipt-2026-08-13.json"
    )
    EXPECTED_PACKET_GATES = (
        "claim_custody_final_replay",
        "git_phase_isolation",
        "compiled_debug_release_witnesses",
        "serial_parallel_recapture",
        "catalog_reverse_closure",
        "release_family_closure",
        "audience_artifact_regeneration",
        "software_identity_rebind",
        "settled_full_ci",
        "final_hostile_review",
        "immutable_evidence_matrix_v4",
        "immutable_decision_v4",
        "unsigned_main_commit_and_receipt",
    )

    def __init__(self, policy: dict[str, Any]) -> None:
        self.ANCHOR = policy["anchor"]["commit"]
        self.ANCHOR_TREE = policy["anchor"]["tree"]
        self.ANCHOR_ENTRY_COUNT = policy["anchor"]["tree_entry_count"]
        self.EXPECTED_LIVE_POLICY_STATE = policy["authority"]["inventory_status"]
        self.EXPECTED_MESSAGE = policy["commit_envelope"]["message"]
        self._expected_rejection = False
        self._expectation_observed = False

    def expect_rejection(self, enabled: bool) -> None:
        if enabled:
            self._expectation_observed = False
        self._expected_rejection = enabled

    def require_expected_rejection_observed(self, label: str) -> None:
        require(
            self._expectation_observed,
            f"{label} did not reach a hostile fixed-CLI validator",
        )

    def observe_expected_rejection(self) -> bool:
        if self._expected_rejection:
            self._expectation_observed = True
        return self._expected_rejection

    def vector(
        self,
        validator: str,
        arguments: dict[str, Any],
    ) -> None:
        if self._expected_rejection:
            self._expectation_observed = True
        raw = canonical_json(
            {
                "arguments": arguments,
                "schema": SELF_TEST_VECTOR_SCHEMA,
                "validator": validator,
            },
            pretty=True,
        )
        completed = invoke_checker(["--self-test-vectors"], stdin_bytes=raw)
        require(
            completed.stderr == b"",
            "self-test vector wrote unexpected standard error: "
            + completed.stderr.decode("utf-8", errors="replace"),
        )
        if completed.returncode == 0 and completed.stdout == PASS_OUTPUT:
            if self._expected_rejection:
                raise SelfTestError(
                    "hostile vector was unexpectedly accepted by its validator"
                )
            return
        if completed.returncode == 1 and completed.stdout == FAIL_OUTPUT:
            if self._expected_rejection:
                return
            raise PhaseError("fixed checker rejected a baseline vector")
        raise SelfTestError(
            "self-test vector returned a noncanonical result: "
            f"rc={completed.returncode}, stdout={completed.stdout!r}"
        )

    def validate_policy_data(
        self, value: Any, *, verify_anchor: bool
    ) -> tuple[PolicyEntry, ...]:
        require(
            not verify_anchor, "pure policy vector cannot request Git anchor replay"
        )
        self.vector("policy", {"value": value})
        return tuple(
            PolicyEntry(row["path"], row["status"], row["review_class"])
            for row in value["entries"]
        )

    def validate_receipt_schema_data(self, value: Any) -> None:
        self.vector("receipt_schema", {"value": value})

    def validate_boundary_state_data(
        self, boundary: str, inventory_status: str
    ) -> None:
        self.vector(
            "boundary_state",
            {"boundary": boundary, "inventory_status": inventory_status},
        )

    def validate_policy_only(self) -> None:
        completed = invoke_checker(["--validate-policy-only"], stdin_bytes=b"")
        require(
            completed.returncode == 0 and completed.stderr == b"",
            "fixed checker policy-only route failed: "
            + completed.stderr.decode("utf-8", errors="replace"),
        )
        output = json.loads(completed.stdout)
        require(
            completed.stdout == canonical_json(output, pretty=False)
            and output.get("schema") == "pid-rs/ksg-rev4-m1a-policy-validation/v1",
            "fixed checker policy-only output is not canonical",
        )

    def load_policy(self, *, verify_anchor: bool) -> None:
        require(not verify_anchor, "self-test baseline uses the production CLI replay")
        self.validate_policy_only()

    def validate_static_artifacts(self, inventory_status: str) -> None:
        require(
            inventory_status == self.EXPECTED_LIVE_POLICY_STATE,
            "static-artifact state differs from live policy",
        )
        self.validate_policy_only()

    def parse_checkpoint_bytes(self, raw: bytes, expected_tree: str) -> dict[str, Any]:
        self.vector(
            "checkpoint",
            {"expected_tree": expected_tree, "raw": raw.decode("utf-8")},
        )
        return {"message": self.EXPECTED_MESSAGE}

    def validate_lifecycle_observation(self, **values: Any) -> str:
        arguments = {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in values.items()
        }
        self.vector("lifecycle_observation", arguments)
        if values["mode"] == "precommit":
            return "anchor_plus_exact_worktree_overlay"
        return "clean_committed_direct_child"

    def validate_lifecycle_metadata(
        self, branch: str | None, active_operations: tuple[str, ...]
    ) -> None:
        self.vector(
            "lifecycle_metadata",
            {"active_operations": list(active_operations), "branch": branch},
        )

    @staticmethod
    def entry_map(value: dict[str, Entry]) -> dict[str, dict[str, str]]:
        return {
            path: {"mode": entry.mode, "oid": entry.oid}
            for path, entry in value.items()
        }

    def validate_delta(
        self,
        policy_entries: tuple[PolicyEntry, ...],
        anchor: dict[str, Entry],
        candidate: dict[str, Entry],
    ) -> None:
        self.vector(
            "delta",
            {
                "anchor": self.entry_map(anchor),
                "candidate": self.entry_map(candidate),
                "policy_entries": [
                    {
                        "path": entry.path,
                        "review_class": entry.review_class,
                        "status": entry.status,
                    }
                    for entry in policy_entries
                ],
            },
        )

    def validate_preclosure_data(self, packet: Any) -> None:
        self.vector("preclosure", {"packet": packet})

    def validate_manifest_replay(
        self, *, actual: bytes, emitted: bytes, returncode: int, stderr: bytes
    ) -> str:
        self.vector(
            "manifest_replay",
            {
                "actual": actual.decode("utf-8"),
                "emitted": emitted.decode("utf-8"),
                "returncode": returncode,
                "stderr": stderr.decode("utf-8"),
            },
        )
        return hashlib.sha256(actual).hexdigest()

    def validate_credit_request(
        self, inventory_status: str, allow_provisional: bool
    ) -> bool:
        self.vector(
            "credit",
            {
                "allow_provisional": allow_provisional,
                "inventory_status": inventory_status,
            },
        )
        return inventory_status != "frozen"

    def validate_runtime_mode(self) -> None:
        self.vector("runtime_mode", {"optimize": sys.flags.optimize})

    def parse_json_bytes(
        self, raw: bytes, _label: str, *, require_canonical: bool
    ) -> Any:
        self.vector(
            "strict_json",
            {
                "raw": raw.decode("utf-8"),
                "require_canonical": require_canonical,
            },
        )
        return json.loads(raw)


def load_checker(policy: dict[str, Any]) -> CheckerCli:
    validate_static_cli_custody()
    return CheckerCli(policy)


def validate_proxy_expectation_nonvacuity(checker: CheckerCli) -> None:
    accepted_arguments = {
        "allow_provisional": True,
        "inventory_status": "provisional_anticipated_paths_not_frozen",
    }
    checker.expect_rejection(True)
    try:
        try:
            checker.vector("credit", accepted_arguments)
        except SelfTestError as error:
            require(
                str(error)
                == "hostile vector was unexpectedly accepted by its validator",
                "accepted-hostile nonvacuity control failed for the wrong reason",
            )
        else:
            raise SelfTestError("accepted hostile proxy control did not fail")
    finally:
        checker.expect_rejection(False)

    rejected_arguments = {
        "allow_provisional": False,
        "inventory_status": "provisional_anticipated_paths_not_frozen",
    }
    try:
        checker.vector("credit", rejected_arguments)
    except PhaseError:
        pass
    else:
        raise SelfTestError("rejected baseline proxy control did not fail")


def load_strict_json(path: Path) -> Any:
    pairs_seen: list[str] = []

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in out, f"duplicate key in {path}: {key}")
            out[key] = value
            pairs_seen.append(key)
        return out

    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=reject_duplicates)
    canonical = (
        json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    require(raw == canonical, f"noncanonical JSON: {path}")
    require(bool(pairs_seen), f"empty JSON object graph: {path}")
    return value


def expect_rejected(
    label: str,
    action: Callable[[], None],
    phase_error: type[Exception],
    checker: CheckerCli,
) -> None:
    checker.expect_rejection(True)
    try:
        action()
    except phase_error:
        raise SelfTestError(
            f"{label} used baseline-rejection semantics instead of a hostile vector"
        ) from None
    except Exception as error:
        raise SelfTestError(f"{label} raised the wrong exception: {error!r}") from error
    else:
        checker.require_expected_rejection_observed(label)
    finally:
        checker.expect_rejection(False)


def mutate_policy(
    checker: Any,
    baseline: dict[str, Any],
    label: str,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    candidate = copy.deepcopy(baseline)
    mutate(candidate)
    expect_rejected(
        label,
        lambda: checker.validate_policy_data(candidate, verify_anchor=False),
        checker.PhaseError,
        checker,
    )


def schema_path(value: dict[str, Any], *parts: str) -> Any:
    current: Any = value
    for part in parts:
        current = current[part]
    return current


def main() -> int:
    policy_raw = POLICY_PATH.read_bytes()
    schema_raw = SCHEMA_PATH.read_bytes()
    policy = load_strict_json(POLICY_PATH)
    schema = load_strict_json(SCHEMA_PATH)
    boundary = BOUNDARY_PATH.read_text(encoding="utf-8")
    checker = load_checker(policy)
    checker.validate_runtime_mode()
    validate_proxy_expectation_nonvacuity(checker)
    abbreviated = invoke_checker(["--alternate-index"], stdin_bytes=b"")
    require(
        abbreviated.returncode == 2
        and abbreviated.stdout == b""
        and b"unrecognized arguments: --alternate-index" in abbreviated.stderr,
        "removed --alternate-index spelling was accepted or abbreviated",
    )
    runtime_vector = canonical_json(
        {
            "arguments": {"optimize": sys.flags.optimize},
            "schema": SELF_TEST_VECTOR_SCHEMA,
            "validator": "runtime_mode",
        },
        pretty=True,
    )
    mixed_vector = invoke_checker(
        ["--self-test-vectors", "--mode", "precommit"],
        stdin_bytes=runtime_vector,
    )
    require(
        mixed_vector.returncode == 2
        and mixed_vector.stdout == b""
        and mixed_vector.stderr.startswith(
            b"KSG M1a self-test vector protocol failed:"
        ),
        "self-test vector mode accepted a production lifecycle argument",
    )
    malformed_protocol = canonical_json(
        {
            "arguments": {},
            "schema": "pid-rs/unknown-self-test-vector/v1",
            "validator": "credit",
        },
        pretty=True,
    )
    protocol_result = invoke_checker(
        ["--self-test-vectors"], stdin_bytes=malformed_protocol
    )
    require(
        protocol_result.returncode == 2
        and protocol_result.stdout == b""
        and protocol_result.stderr.startswith(
            b"KSG M1a self-test vector protocol failed:"
        ),
        "malformed vector protocol collapsed to an ordinary hostile result",
    )
    nonvacuity_vector = canonical_json(
        {
            "arguments": {
                "allow_provisional": True,
                "inventory_status": "provisional_anticipated_paths_not_frozen",
            },
            "schema": SELF_TEST_VECTOR_SCHEMA,
            "validator": "credit",
        },
        pretty=True,
    )
    nonvacuity_result = invoke_checker(
        ["--self-test-vectors"], stdin_bytes=nonvacuity_vector
    )
    require(
        nonvacuity_result.returncode == 0
        and nonvacuity_result.stdout == PASS_OUTPUT
        and nonvacuity_result.stderr == b"",
        "accepted validator control did not produce canonical pass",
    )
    validate_adjacent_unchecked_hash_pyc_nonexecution(runtime_vector)
    require(
        b"credit" not in PASS_OUTPUT + FAIL_OUTPUT,
        "self-test result protocol acquired a credit claim",
    )
    entries = checker.validate_policy_data(policy, verify_anchor=False)
    checker.validate_receipt_schema_data(schema)
    checker.validate_boundary_state_data(
        boundary, policy["authority"]["inventory_status"]
    )
    checker.load_policy(verify_anchor=False)
    require(
        len(entries) == len(policy["entries"]), "baseline policy entry count changed"
    )
    require(
        policy["authority"]["inventory_status"] == checker.EXPECTED_LIVE_POLICY_STATE,
        "live policy state differs from the checker freeze state",
    )
    alternate_state = copy.deepcopy(policy)
    if checker.EXPECTED_LIVE_POLICY_STATE == "frozen":
        alternate_state["authority"]["inventory_status"] = (
            "provisional_anticipated_paths_not_frozen"
        )
        alternate_state["authority"]["credit_permitted"] = False
    else:
        alternate_state["authority"]["inventory_status"] = "frozen"
        alternate_state["authority"]["credit_permitted"] = True
    checker.validate_policy_data(alternate_state, verify_anchor=False)
    live_state = policy["authority"]["inventory_status"]
    other_state = alternate_state["authority"]["inventory_status"]
    state_line = {
        "provisional_anticipated_paths_not_frozen": (
            "- Current policy state: **provisional inventory; no M1a credit**"
        ),
        "frozen": (
            "- Current policy state: **frozen reviewed inventory; M1a credit "
            "eligible only with external custody**"
        ),
    }
    state_marker = {
        state: f"<!-- ksg-m1a-policy-state: {state} -->" for state in state_line
    }
    alternate_boundary = boundary.replace(
        state_line[live_state], state_line[other_state]
    ).replace(state_marker[live_state], state_marker[other_state])
    checker.validate_boundary_state_data(alternate_boundary, other_state)
    boundary_attacks = (
        (
            "boundary_dual_human_state",
            boundary + "\n" + state_line[other_state] + "\n",
            live_state,
        ),
        (
            "boundary_dual_machine_state",
            boundary + "\n" + state_marker[other_state] + "\n",
            live_state,
        ),
        (
            "boundary_missing_human_state",
            boundary.replace(state_line[live_state], ""),
            live_state,
        ),
        (
            "boundary_missing_machine_state",
            boundary.replace(state_marker[live_state], ""),
            live_state,
        ),
        (
            "boundary_state_mismatch",
            boundary,
            other_state,
        ),
    )
    for label, hostile_boundary, requested_state in boundary_attacks:
        expect_rejected(
            label,
            lambda hostile_boundary=hostile_boundary, requested_state=requested_state: (
                checker.validate_boundary_state_data(hostile_boundary, requested_state)
            ),
            checker.PhaseError,
            checker,
        )

    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "anchor_commit",
            lambda value: value["anchor"].__setitem__("commit", "0" * 40),
        ),
        ("anchor_tree", lambda value: value["anchor"].__setitem__("tree", "0" * 40)),
        (
            "anchor_count_bool",
            lambda value: value["anchor"].__setitem__("tree_entry_count", True),
        ),
        (
            "anchor_listing",
            lambda value: value["anchor"].__setitem__("tree_listing_sha256", "0" * 64),
        ),
        (
            "credit_state_mismatch",
            lambda value: value["authority"].__setitem__(
                "credit_permitted",
                value["authority"]["inventory_status"] != "frozen",
            ),
        ),
        (
            "unknown_inventory_state",
            lambda value: value["authority"].__setitem__(
                "inventory_status", "review_pending"
            ),
        ),
        (
            "mechanical_reseal",
            lambda value: value["authority"].__setitem__(
                "mechanical_resealing_permitted", True
            ),
        ),
        (
            "deletion_permitted",
            lambda value: value.__setitem__("deletions_permitted", True),
        ),
        (
            "message",
            lambda value: value["commit_envelope"].__setitem__("message", "wrong\n"),
        ),
        (
            "signature",
            lambda value: value["commit_envelope"].__setitem__(
                "signature_headers_permitted", True
            ),
        ),
        (
            "identity",
            lambda value: value["commit_envelope"]["author"].__setitem__(
                "name", "Agent"
            ),
        ),
        (
            "timezone",
            lambda value: value["commit_envelope"].__setitem__("timezone", "+0000"),
        ),
        (
            "remove_runtime_path",
            lambda value: value["entries"].__setitem__(
                slice(None),
                [
                    row
                    for row in value["entries"]
                    if row["path"] != "crates/pid-core/src/nn.rs"
                ],
            ),
        ),
        (
            "add_m1c_decision",
            lambda value: value["entries"].append(
                {
                    "path": "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md",
                    "review_class": "ksg_preclosure_authority",
                    "status": "A",
                }
            ),
        ),
        (
            "classify_checker_modified",
            lambda value: next(
                row
                for row in value["entries"]
                if row["path"] == "scripts/check-ksg-m1a-phase.py"
            ).__setitem__("status", "M"),
        ),
        (
            "duplicate_path",
            lambda value: value["entries"].append(copy.deepcopy(value["entries"][0])),
        ),
        (
            "unsafe_path",
            lambda value: value["entries"][0].__setitem__("path", "../escape"),
        ),
        (
            "unknown_review_class",
            lambda value: value["entries"][0].__setitem__("review_class", "unknown"),
        ),
        ("delete_status", lambda value: value["entries"][0].__setitem__("status", "D")),
        (
            "receipt_path",
            lambda value: value["receipt_contract"].__setitem__(
                "final_descendant_receipt_path", "wrong.json"
            ),
        ),
        (
            "review_class_semantics",
            lambda value: value["review_classes"].__setitem__(
                "ksg_runtime_boundary", "Looks plausible."
            ),
        ),
        (
            "forbidden_context_semantics",
            lambda value: value["forbidden_contexts"].__setitem__(0, "PID2 changes"),
        ),
    ]
    require(len(mutations) == 22, "policy mutation inventory changed")
    for label, mutate in mutations:
        mutate_policy(checker, policy, label, mutate)

    schema_mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "schema_id",
            lambda value: value.__setitem__(
                "$id", "https://example.invalid/schema.json"
            ),
        ),
        (
            "schema_extra_properties",
            lambda value: value.__setitem__("additionalProperties", True),
        ),
        (
            "receipt_status",
            lambda value: schema_path(
                value, "properties", "milestone", "properties", "status"
            ).__setitem__("const", "complete"),
        ),
        (
            "receipt_evidence_class",
            lambda value: schema_path(
                value, "properties", "evidence_class"
            ).__setitem__("const", "scientific_evidence"),
        ),
        ("receipt_required_field", lambda value: schema_path(value, "required").pop()),
        (
            "receipt_nonimplication",
            lambda value: schema_path(
                value, "properties", "nonimplications", "const"
            ).pop(),
        ),
        (
            "receipt_commit_message",
            lambda value: schema_path(
                value, "properties", "subject", "properties", "commit_message"
            ).__setitem__(
                "const", "Harden KSG integer-harmonic runtime correspondence"
            ),
        ),
        (
            "receipt_human_identity",
            lambda value: schema_path(
                value, "$defs", "humanIdentity", "properties", "name"
            ).__setitem__("const", "Agent"),
        ),
        (
            "receipt_remote_ref",
            lambda value: schema_path(
                value, "properties", "remote_observation", "properties", "ref"
            ).__setitem__("const", "refs/heads/topic"),
        ),
        (
            "receipt_hosted_conclusion",
            lambda value: schema_path(
                value, "properties", "hosted_validation", "properties", "conclusion"
            ).__setitem__("const", "neutral"),
        ),
        (
            "receipt_subject_tree_presence",
            lambda value: schema_path(
                value,
                "properties",
                "acyclic_boundary",
                "properties",
                "receipt_absent_from_subject_tree",
            ).__setitem__("const", False),
        ),
        (
            "receipt_nonimplication_text",
            lambda value: schema_path(
                value, "properties", "nonimplications", "const"
            ).__setitem__(0, "No implications."),
        ),
        (
            "sha1_pattern",
            lambda value: schema_path(value, "$defs", "sha1").__setitem__(
                "pattern", "[0-9a-f]+"
            ),
        ),
        (
            "sha1_min_length",
            lambda value: schema_path(value, "$defs", "sha1").__setitem__(
                "minLength", 39
            ),
        ),
        (
            "sha1_max_length",
            lambda value: schema_path(value, "$defs", "sha1").__setitem__(
                "maxLength", 41
            ),
        ),
        (
            "sha256_pattern",
            lambda value: schema_path(value, "$defs", "sha256").__setitem__(
                "pattern", "[0-9a-f]+"
            ),
        ),
        (
            "sha256_min_length",
            lambda value: schema_path(value, "$defs", "sha256").__setitem__(
                "minLength", 63
            ),
        ),
        (
            "sha256_max_length",
            lambda value: schema_path(value, "$defs", "sha256").__setitem__(
                "maxLength", 65
            ),
        ),
        (
            "artifact_size_minimum",
            lambda value: schema_path(
                value, "$defs", "artifact", "properties", "size_bytes"
            ).__setitem__("minimum", 0),
        ),
        (
            "artifact_size_maximum",
            lambda value: schema_path(
                value, "$defs", "artifact", "properties", "size_bytes"
            ).__setitem__("maximum", 16777217),
        ),
    ]
    require(len(schema_mutations) == 20, "schema mutation inventory changed")
    for label, mutate in schema_mutations:
        candidate = copy.deepcopy(schema)
        mutate(candidate)
        expect_rejected(
            label,
            lambda candidate=candidate: checker.validate_receipt_schema_data(candidate),
            checker.PhaseError,
            checker,
        )

    tree = "1" * 40
    identity = b"Sepehr Mahmoudian <sepmhn@gmail.com> 1786597200 +0200"
    commit = (
        f"tree {tree}\nparent {checker.ANCHOR}\n".encode("ascii")
        + b"author "
        + identity
        + b"\ncommitter "
        + identity
        + b"\n\n"
        + checker.EXPECTED_MESSAGE.encode("utf-8")
    )
    parsed = checker.parse_checkpoint_bytes(commit, tree)
    require(
        parsed["message"] == checker.EXPECTED_MESSAGE,
        "baseline commit message lost terminal LF",
    )
    for label, bad in (
        (
            "commit_signature_header",
            commit.replace(b"author ", b"gpgsig x\nauthor ", 1),
        ),
        (
            "commit_merge_parent",
            commit.replace(
                b"parent ",
                b"parent " + checker.ANCHOR.encode("ascii") + b"\nparent ",
                1,
            ),
        ),
        ("commit_wrong_message", commit[:-1]),
        (
            "commit_agent_identity",
            commit.replace(b"Sepehr Mahmoudian", b"Agent Name", 1),
        ),
    ):
        expect_rejected(
            label,
            lambda bad=bad: checker.parse_checkpoint_bytes(bad, tree),
            checker.PhaseError,
            checker,
        )

    precommit_observation = {
        "mode": "precommit",
        "head": checker.ANCHOR,
        "checkpoint": "2" * 40,
        "index_clean": True,
        "tracked_clean": False,
        "modified": ("tracked.rs",),
        "untracked": ("new.json",),
        "expected_modified": ("tracked.rs",),
        "expected_added": ("new.json",),
    }
    require(
        checker.validate_lifecycle_observation(**precommit_observation)
        == "anchor_plus_exact_worktree_overlay",
        "baseline precommit lifecycle observation failed",
    )
    lifecycle_attacks: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        ("precommit_wrong_head", precommit_observation, {"head": "0" * 40}),
        ("precommit_dirty_index", precommit_observation, {"index_clean": False}),
        ("precommit_missing_modified", precommit_observation, {"modified": ()}),
        (
            "precommit_extra_modified",
            precommit_observation,
            {"modified": ("extra.rs", "tracked.rs")},
        ),
        ("precommit_missing_added", precommit_observation, {"untracked": ()}),
        (
            "precommit_extra_untracked",
            precommit_observation,
            {"untracked": ("extra.json", "new.json")},
        ),
    ]
    postcommit_observation = {
        "mode": "postcommit",
        "head": "2" * 40,
        "checkpoint": "2" * 40,
        "index_clean": True,
        "tracked_clean": True,
        "modified": (),
        "untracked": (),
        "expected_modified": ("tracked.rs",),
        "expected_added": ("new.json",),
    }
    require(
        checker.validate_lifecycle_observation(**postcommit_observation)
        == "clean_committed_direct_child",
        "baseline postcommit lifecycle observation failed",
    )
    lifecycle_attacks.extend(
        [
            ("postcommit_wrong_head", postcommit_observation, {"head": "3" * 40}),
            ("postcommit_dirty_index", postcommit_observation, {"index_clean": False}),
            (
                "postcommit_dirty_tracked",
                postcommit_observation,
                {"tracked_clean": False},
            ),
            (
                "postcommit_modified_path",
                postcommit_observation,
                {"modified": ("tracked.rs",)},
            ),
            (
                "postcommit_untracked_path",
                postcommit_observation,
                {"untracked": ("new.json",)},
            ),
            ("unknown_lifecycle_mode", postcommit_observation, {"mode": "other"}),
        ]
    )
    for label, baseline, mutation in lifecycle_attacks:
        hostile = dict(baseline)
        hostile.update(mutation)
        expect_rejected(
            label,
            lambda hostile=hostile: checker.validate_lifecycle_observation(**hostile),
            checker.PhaseError,
            checker,
        )

    checker.validate_lifecycle_metadata("main", ())
    metadata_attacks = (
        ("detached_head", None, ()),
        ("wrong_branch", "topic", ()),
        ("merge_state", "main", ("MERGE_HEAD",)),
        ("rebase_state", "main", ("rebase-merge",)),
        ("cherry_pick_state", "main", ("CHERRY_PICK_HEAD",)),
        ("sequencer_state", "main", ("sequencer",)),
    )
    for label, branch, active in metadata_attacks:
        expect_rejected(
            label,
            lambda branch=branch, active=active: checker.validate_lifecycle_metadata(
                branch, active
            ),
            checker.PhaseError,
            checker,
        )

    synthetic_anchor = {
        "tracked.rs": checker.Entry("100644", "1" * 40),
    }
    synthetic_candidate = {
        "new.json": checker.Entry("100644", "3" * 40),
        "tracked.rs": checker.Entry("100644", "2" * 40),
    }
    synthetic_policy = (
        checker.PolicyEntry("new.json", "A", "phase_authority"),
        checker.PolicyEntry("tracked.rs", "M", "ksg_runtime_boundary"),
    )
    checker.validate_delta(synthetic_policy, synthetic_anchor, synthetic_candidate)
    delta_attacks: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        (
            "delta_missing_addition",
            synthetic_anchor,
            {"tracked.rs": checker.Entry("100644", "2" * 40)},
        ),
        (
            "delta_extra_addition",
            synthetic_anchor,
            {
                **synthetic_candidate,
                "extra.md": checker.Entry("100644", "4" * 40),
            },
        ),
        (
            "delta_executable_mode",
            synthetic_anchor,
            {
                **synthetic_candidate,
                "new.json": checker.Entry("100755", "3" * 40),
            },
        ),
        (
            "delta_deletion",
            synthetic_anchor,
            {"new.json": checker.Entry("100644", "3" * 40)},
        ),
    ]
    unchanged_final = checker.Entry("100644", "5" * 40)
    for label, forbidden_path in (
        ("delta_final_matrix", checker.FINAL_MATRIX),
        ("delta_future_receipt", checker.FUTURE_RECEIPT),
    ):
        hostile_anchor = {**synthetic_anchor, forbidden_path: unchanged_final}
        hostile_candidate = {**synthetic_candidate, forbidden_path: unchanged_final}
        delta_attacks.append((label, hostile_anchor, hostile_candidate))
    for label, hostile_anchor, hostile_candidate in delta_attacks:
        expect_rejected(
            label,
            lambda hostile_anchor=hostile_anchor, hostile_candidate=hostile_candidate: (
                checker.validate_delta(
                    synthetic_policy, hostile_anchor, hostile_candidate
                )
            ),
            checker.PhaseError,
            checker,
        )

    baseline_packet = {
        "active_revision": 4,
        "claim_id": "KSG-INTEGER-HARMONIC-001",
        "status": "integration_no_go",
        "packet_stage": "preclosure_core_manifest_must_be_regenerated_at_m1c",
        "open_integration_gates": list(checker.EXPECTED_PACKET_GATES),
    }
    checker.validate_preclosure_data(baseline_packet)
    packet_attacks: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "packet_status",
            lambda value: value.__setitem__("status", "integration_go"),
        ),
        (
            "packet_stage",
            lambda value: value.__setitem__("packet_stage", "final"),
        ),
        (
            "packet_gate_removed",
            lambda value: value["open_integration_gates"].pop(),
        ),
        (
            "packet_claim",
            lambda value: value.__setitem__("claim_id", "PID2"),
        ),
    ]
    for label, mutation in packet_attacks:
        hostile_packet = copy.deepcopy(baseline_packet)
        mutation(hostile_packet)
        expect_rejected(
            label,
            lambda hostile_packet=hostile_packet: checker.validate_preclosure_data(
                hostile_packet
            ),
            checker.PhaseError,
            checker,
        )

    manifest = b'{"schema":"control"}\n'
    require(
        checker.validate_manifest_replay(
            actual=manifest, emitted=manifest, returncode=0, stderr=b""
        )
        == hashlib.sha256(manifest).hexdigest(),
        "baseline manifest replay binding failed",
    )
    manifest_attacks = (
        (
            "manifest_stale",
            lambda: checker.validate_manifest_replay(
                actual=manifest, emitted=manifest + b" ", returncode=0, stderr=b""
            ),
        ),
        (
            "manifest_emitter_failed",
            lambda: checker.validate_manifest_replay(
                actual=manifest, emitted=manifest, returncode=1, stderr=b"failed"
            ),
        ),
    )
    for label, action in manifest_attacks:
        expect_rejected(label, action, checker.PhaseError, checker)

    require(
        checker.validate_credit_request(
            "provisional_anticipated_paths_not_frozen", True
        )
        is True,
        "provisional diagnostic credit path changed",
    )
    require(
        checker.validate_credit_request("frozen", False) is False,
        "frozen credit path changed",
    )
    credit_attacks = (
        (
            "provisional_without_diagnostic_flag",
            lambda: checker.validate_credit_request(
                "provisional_anticipated_paths_not_frozen", False
            ),
        ),
        (
            "frozen_with_diagnostic_flag",
            lambda: checker.validate_credit_request("frozen", True),
        ),
    )
    for label, action in credit_attacks:
        expect_rejected(label, action, checker.PhaseError, checker)

    alternate_index_attacks = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-ksg-m1a-selftest-") as temp:
        directory = Path(temp).resolve(strict=True)
        sealed = directory / "sealed-index"
        create_anchor_index(sealed, checker.ANCHOR_TREE)
        sealed.chmod(0o400)
        raw_index = sealed.read_bytes()
        digest = hashlib.sha256(raw_index).hexdigest()

        def validate_sealed_descriptor(
            descriptor: int,
            expected_digest: str,
            expected_count: int,
            expected_tree: str,
        ) -> None:
            expected_rejection = checker.observe_expected_rejection()
            completed = invoke_checker(
                [
                    "--self-test-sealed-index",
                    "--expected-candidate-tree",
                    expected_tree,
                    "--alternate-index-sha256",
                    expected_digest,
                    "--alternate-index-entry-count",
                    str(expected_count),
                ],
                stdin_descriptor=descriptor,
            )
            require(
                completed.stderr == b"",
                "sealed-index self-test wrote unexpected standard error: "
                + completed.stderr.decode("utf-8", errors="replace"),
            )
            if completed.returncode == 0 and completed.stdout == PASS_OUTPUT:
                if expected_rejection:
                    raise SelfTestError(
                        "hostile sealed index was unexpectedly accepted"
                    )
                return
            if completed.returncode == 1 and completed.stdout == FAIL_OUTPUT:
                if expected_rejection:
                    return
                raise PhaseError("fixed checker rejected the sealed index")
            raise SelfTestError(
                "sealed-index self-test returned a noncanonical result: "
                f"rc={completed.returncode}, stdout={completed.stdout!r}"
            )

        def validate_sealed(
            source: Path,
            expected_digest: str,
            expected_count: int,
            expected_tree: str,
            *,
            initial_offset: int = 0,
        ) -> None:
            flags = (
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            )
            descriptor = os.open(source, flags)
            try:
                if initial_offset:
                    os.lseek(descriptor, initial_offset, os.SEEK_SET)
                validate_sealed_descriptor(
                    descriptor,
                    expected_digest,
                    expected_count,
                    expected_tree,
                )
            finally:
                os.close(descriptor)

        isolation_descriptor = os.open(
            sealed,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            mixed_sealed = invoke_checker(
                [
                    "--self-test-sealed-index",
                    "--mode",
                    "precommit",
                    "--expected-candidate-tree",
                    checker.ANCHOR_TREE,
                    "--alternate-index-sha256",
                    digest,
                    "--alternate-index-entry-count",
                    str(checker.ANCHOR_ENTRY_COUNT),
                ],
                stdin_descriptor=isolation_descriptor,
            )
        finally:
            os.close(isolation_descriptor)
        require(
            mixed_sealed.returncode == 2
            and mixed_sealed.stdout == b""
            and mixed_sealed.stderr.startswith(
                b"KSG M1a sealed-index test protocol failed:"
            ),
            "sealed-index self-test mode accepted a production lifecycle argument",
        )

        validate_sealed(sealed, digest, checker.ANCHOR_ENTRY_COUNT, checker.ANCHOR_TREE)
        alternate_cases: list[tuple[str, Callable[[], None]]] = [
            (
                "alternate_index_digest",
                lambda: validate_sealed(
                    sealed,
                    "0" * 64,
                    checker.ANCHOR_ENTRY_COUNT,
                    checker.ANCHOR_TREE,
                ),
            ),
            (
                "alternate_index_entry_count",
                lambda: validate_sealed(
                    sealed,
                    digest,
                    checker.ANCHOR_ENTRY_COUNT - 1,
                    checker.ANCHOR_TREE,
                ),
            ),
            (
                "alternate_index_tree",
                lambda: validate_sealed(
                    sealed,
                    digest,
                    checker.ANCHOR_ENTRY_COUNT,
                    "1" * 40,
                ),
            ),
        ]
        for label, action in alternate_cases:
            expect_rejected(label, action, checker.PhaseError, checker)
            alternate_index_attacks += 1
        sealed.chmod(0o600)
        expect_rejected(
            "alternate_index_writable_mode",
            lambda: validate_sealed(
                sealed,
                digest,
                checker.ANCHOR_ENTRY_COUNT,
                checker.ANCHOR_TREE,
            ),
            checker.PhaseError,
            checker,
        )
        alternate_index_attacks += 1
        sealed.chmod(0o400)
        writable = directory / "writable-descriptor-index"
        writable.write_bytes(raw_index)
        writable_descriptor = os.open(
            writable,
            os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        writable.chmod(0o400)
        try:
            expect_rejected(
                "alternate_index_writable_descriptor",
                lambda: validate_sealed_descriptor(
                    writable_descriptor,
                    digest,
                    checker.ANCHOR_ENTRY_COUNT,
                    checker.ANCHOR_TREE,
                ),
                checker.PhaseError,
                checker,
            )
        finally:
            os.close(writable_descriptor)
        alternate_index_attacks += 1
        expect_rejected(
            "alternate_index_nonzero_offset",
            lambda: validate_sealed(
                sealed,
                digest,
                checker.ANCHOR_ENTRY_COUNT,
                checker.ANCHOR_TREE,
                initial_offset=1,
            ),
            checker.PhaseError,
            checker,
        )
        alternate_index_attacks += 1
        hard_source = directory / "hard-source"
        hard_source.write_bytes(raw_index)
        hard_source.chmod(0o400)
        os.link(hard_source, directory / "hard-peer")
        expect_rejected(
            "alternate_index_hardlink",
            lambda: validate_sealed(
                hard_source,
                digest,
                checker.ANCHOR_ENTRY_COUNT,
                checker.ANCHOR_TREE,
            ),
            checker.PhaseError,
            checker,
        )
        alternate_index_attacks += 1

    strict_json_controls = (
        b'{"a":1,"a":1}\n',
        b'{"a":NaN}\n',
        b'{"a":true}\n',
    )
    expect_rejected(
        "duplicate_json",
        lambda: checker.parse_json_bytes(
            strict_json_controls[0], "mutant", require_canonical=False
        ),
        checker.PhaseError,
        checker,
    )
    expect_rejected(
        "nonfinite_json",
        lambda: checker.parse_json_bytes(
            strict_json_controls[1], "mutant", require_canonical=False
        ),
        checker.PhaseError,
        checker,
    )
    require(
        checker.parse_json_bytes(
            strict_json_controls[2], "typed-control", require_canonical=False
        )
        == {"a": True},
        "strict JSON control changed bool typing",
    )
    duplicate_artifact_controls = (
        (
            "duplicate_policy_member",
            policy_raw.replace(
                b'      "review_class": "phase_hosted_wiring",\n',
                b'      "review_class": "phase_hosted_wiring",\n'
                b'      "review_class": "phase_hosted_wiring",\n',
                1,
            ),
            "M1a path policy mutant",
        ),
        (
            "duplicate_schema_member",
            schema_raw.replace(
                b'  "$id": "https://github.com/sepahead/pid-rs/blob/main/'
                b'audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json",\n',
                b'  "$id": "https://github.com/sepahead/pid-rs/blob/main/'
                b'audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json",\n'
                b'  "$id": "https://github.com/sepahead/pid-rs/blob/main/'
                b'audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json",\n',
                1,
            ),
            "M1a receipt schema mutant",
        ),
        (
            "duplicate_receipt_member",
            (
                b'{"schema":"pid-rs/ksg-rev4-m1a-implementation-receipt/v1",'
                b'"schema":"pid-rs/ksg-rev4-m1a-implementation-receipt/v1"}\n'
            ),
            "M1a implementation receipt mutant",
        ),
    )
    for label, hostile_raw, artifact_label in duplicate_artifact_controls:
        require(
            hostile_raw not in {policy_raw, schema_raw},
            f"{label} fixture did not mutate its artifact",
        )
        expect_rejected(
            label,
            lambda hostile_raw=hostile_raw, artifact_label=artifact_label: (
                checker.parse_json_bytes(
                    hostile_raw, artifact_label, require_canonical=False
                )
            ),
            checker.PhaseError,
            checker,
        )

    require(
        EXPECTED_POLICY_SCHEMA_MUTATIONS == len(mutations) + len(schema_mutations),
        "registered hostile mutation total changed",
    )
    checker.validate_static_artifacts(policy["authority"]["inventory_status"])
    print(
        "OK: KSG M1a phase hostile suite rejected "
        f"{EXPECTED_POLICY_SCHEMA_MUTATIONS} policy/schema mutations, 4 commit-envelope "
        f"attacks, {len(lifecycle_attacks)} lifecycle observations, "
        f"{len(metadata_attacks)} branch/operation states, and "
        f"{len(delta_attacks)} exact-delta, {len(packet_attacks)} preclosure, "
        f"{len(manifest_attacks)} manifest, {len(credit_attacks)} credit-mode, and "
        f"{len(boundary_attacks)} boundary-state, and {alternate_index_attacks} "
        f"sealed-index attacks plus {len(duplicate_artifact_controls)} artifact-specific "
        "duplicate-member attacks; live policy state is "
        f"{checker.EXPECTED_LIVE_POLICY_STATE}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"KSG M1a phase self-test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
