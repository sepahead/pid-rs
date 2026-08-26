#!/usr/bin/env python3
"""Validate source-ready, prospective, or preserved SxPID3 audit-expression evidence.

The source state S has no receipt.  A prospective state has exactly one untracked receipt created
by the capture command.  A committed-or-preserved state derives the unique introduction commit E
from non-shallow Git history, requires E to be a receipt-only direct child of S, and requires the
same receipt bytes at E, HEAD, and the live path.  Descendants may legitimately evolve other files.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import types
from typing import Any, Final

if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.no_site == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: checker requires CPython 3.11+ started with -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CAPTURE_SUPPORT_PATH: Final[Path] = (
    ROOT
    / "scripts"
    / "capture-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.py"
)
CAPTURE_SUPPORT_SHA256: Final[str] = (
    "449d62d65be8a7a6a108bb86f6a5cb9c7ef932fd8e242876931b34c4eb029c42"
)


def bootstrap_read_source(path: Path, expected_mode: int) -> bytes:
    before = path.lstat()
    if not (
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == expected_mode
        and 0 < before.st_size <= 4 * 1024 * 1024
    ):
        raise RuntimeError("bootstrap source metadata rejected")
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("bootstrap O_NOFOLLOW is unavailable")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        metadata_fields = (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
        if not all(
            getattr(opened, field) == getattr(before, field)
            for field in metadata_fields
        ):
            raise RuntimeError("bootstrap source identity changed")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if chunk == b"":
                raise RuntimeError("short bootstrap source read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1) != b"":
            raise RuntimeError("bootstrap source grew")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if not all(
        getattr(before, field)
        == getattr(opened, field)
        == getattr(after_fd, field)
        == getattr(after, field)
        for field in metadata_fields
    ):
        raise RuntimeError("bootstrap source changed during read")
    return b"".join(chunks)


def load_source_module(
    path: Path, name: str, expected_mode: int, expected_sha256: str
) -> types.ModuleType:
    raw = bootstrap_read_source(path, expected_mode)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("bootstrap source SHA-256 differs from the frozen S generator")
    module = types.ModuleType(name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    sys.modules[name] = module
    code = compile(
        raw,
        os.fspath(path),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


CAPTURE_SUPPORT = load_source_module(
    CAPTURE_SUPPORT_PATH,
    "pid_rs_sxpid3_audit_expression_capture_support_v1",
    0o755,
    CAPTURE_SUPPORT_SHA256,
)
InstanceValidationError = CAPTURE_SUPPORT.InstanceValidationError
SchemaDefinitionError = CAPTURE_SUPPORT.SchemaDefinitionError
validate_schema = CAPTURE_SUPPORT.validate_schema
SCHEMA_RELATIVE: Final[str] = (
    "audit/schemas/"
    "sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.schema.json"
)
GENERATOR_RELATIVE: Final[str] = (
    "scripts/"
    "capture-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.py"
)
RECEIPT_RELATIVE: Final[str] = (
    "audit/evidence/"
    "sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-2026-08-26.json"
)
RECEIPT_PATH: Final[Path] = ROOT / RECEIPT_RELATIVE
BASE_COMMIT: Final[str] = "9d1cdf287147e66f7ebbbf67bd9b5ed177d28ac3"
BASE_TREE: Final[str] = "ab57c76ec584e0d91b830ebd02561b248444e5e0"
P1_COMMIT: Final[str] = "c829dfb4c1683e6b3749b0642fdd1f0de64cdcea"
P1_TREE: Final[str] = "a326dbf538342a4c1f0c449234025f042e08bed8"
RESULT_ID: Final[str] = "SXPID3-BOUNDED-KEYED-SCALAR-AUDIT-EXPRESSIONS"
EMPTY_SHA256: Final[str] = hashlib.sha256(b"").hexdigest()
TOOL_TIMEOUT_SECONDS: Final[int] = 60
TOOL_OUTPUT_CAP_BYTES: Final[int] = 32 * 1024 * 1024
MINIMUM_GIT_VERSION: Final[tuple[int, int, int]] = (2, 41, 0)

SOURCE_DELTA: Final[dict[str, tuple[str, str]]] = {
    ".github/workflows/sxpid3-bounded-keyed-scalar-audit-expressions.yml": ("A", "100644"),
    "CHANGELOG.md": ("M", "100644"),
    SCHEMA_RELATIVE: ("A", "100644"),
    GENERATOR_RELATIVE: ("A", "100755"),
    "scripts/capture-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-self-test.py": (
        "A",
        "100755",
    ),
    "scripts/check-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.py": (
        "A",
        "100755",
    ),
    "scripts/check-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-self-test.py": (
        "A",
        "100755",
    ),
}
INFRASTRUCTURE_PATHS: Final[tuple[str, ...]] = tuple(
    sorted(path for path, (status, _mode) in SOURCE_DELTA.items() if status == "A")
)

INPUT_ROLES: Final[dict[str, str]] = {
    SCHEMA_RELATIVE: "closed_receipt_schema",
    GENERATOR_RELATIVE: "no_clobber_receipt_generator",
    "crates/pid-core/src/discrete_pid.rs": "three_source_antichain_and_mobius_source",
    "crates/pid-core/src/sxpid.rs": "fixed_three_source_lexical_route_source",
    "scripts/check-sxpid3-all108-independent.py": "independent_exact_lane",
    "scripts/check-sxpid3-all108-independent-self-test.py": "independent_exact_lane_self_test",
    "scripts/check-sxpid3-bounded-full-coordinates.py": "primary_exact_lane",
    "scripts/check-sxpid3-bounded-full-coordinates-self-test.py": "primary_exact_lane_self_test",
    "scripts/check-sxpid3-p5-rust-source-route.py": "lexical_rust_route_lane",
    "scripts/check-sxpid3-p5-rust-source-route-self-test.py": "lexical_rust_route_lane_self_test",
}

P1_PATHS: Final[tuple[str, ...]] = (
    ".github/workflows/sxpid3-informative-invariance.yml",
    "audit/formal/lean-sxpid3-informative-invariance/AGENTS.md",
    "audit/formal/lean-sxpid3-informative-invariance/PidSxPid3InformativeInvariance.lean",
    "crates/pid-core/tests/sxpid_informative_invariance.rs",
    "justfile.sxpid3-informative-invariance",
    "scripts/check-lean-sxpid3-informative-invariance-parity.py",
    "scripts/check-lean-sxpid3-informative-invariance-self-test.py",
    "scripts/check-lean-sxpid3-informative-invariance.py",
    "scripts/check-sxpid3-informative-invariance-self-test.py",
    "scripts/check-sxpid3-informative-invariance.py",
)

COMMAND_ROSTER: Final[tuple[tuple[str, str, str, str, int], ...]] = (
    (
        "primary_checker",
        "scripts/check-sxpid3-bounded-full-coordinates.py",
        "69e0844fccff4b28b34bcc9f9f8b8edc04a73a14fbfcced1fdd2edd27da6498f",
        "/pid-rs/sxpid3-bounded-full-coordinates/v2",
        12_237,
    ),
    (
        "primary_self_test",
        "scripts/check-sxpid3-bounded-full-coordinates-self-test.py",
        "971aaca8d31230b775f69d0f5f1e91e5f9ef9579dc853cff1b6d1c845dfa7e10",
        "/pid-rs/sxpid3-bounded-full-coordinates-self-test/v2",
        1_106,
    ),
    (
        "independent_checker",
        "scripts/check-sxpid3-all108-independent.py",
        "63e1470075f7fca88e9a8d82d52cdfcb56d389b4b3c7ac4d5ccba5071d6c2212",
        "pid-rs.sxpid3-all108-independent-result.v2",
        16_808,
    ),
    (
        "independent_self_test",
        "scripts/check-sxpid3-all108-independent-self-test.py",
        "1ee40d697aebd1b6d01ad5781ab46ad7a5265a50f1918cff67cda5e08775d8ae",
        "pid-rs.sxpid3-all108-independent-mutations.v2",
        2_788,
    ),
    (
        "rust_source_route_checker",
        "scripts/check-sxpid3-p5-rust-source-route.py",
        "a8cdab4307bf3bc46b03ad6487282a5ab4f0768959d1370f008860de978f22d0",
        "/pid-rs/sxpid3-p5-rust-source-route/v2",
        11_054,
    ),
    (
        "rust_source_route_self_test",
        "scripts/check-sxpid3-p5-rust-source-route-self-test.py",
        "67ad8be5b31bb93a0c64df8a6a3cf91a8a0a669d82b73d8556b98060a93f0487",
        "/pid-rs/sxpid3-p5-rust-source-route-self-test/v2",
        593,
    ),
)

ROUTE_BOUNDARIES: Final[list[str]] = [
    "lexical_source_route_only",
    "rust_name_resolution_not_formally_verified",
    "compiled_rust_refinement_open",
    "rust_numeric_values_not_compared",
    "binary64_refinement_not_established",
    "108_keyed_scalar_audit_expressions_not_108_atoms_or_nodes",
    "108_keyed_scalar_audit_expressions_not_108_independent_degrees_of_freedom",
    "git_commit_identity_not_established",
    "release_identity_not_established",
    "source_authenticity_not_established",
    "artifact_authenticity_not_established",
    "GO_is_lane_local_lexical_obligations_only_not_scientific_validation",
    "bounded_repeated_read_race_detection_not_atomic_snapshot_live_monitor_or_authenticity",
    "claimed_construct_outer_attributes_are_exactly_bounded",
    "module_level_inner_cfg_and_cfg_attr_are_rejected",
    "attribute_guard_is_conservative_lexical_not_full_Rust_parsing_or_cfg_evaluation",
]

SIGN_CENSUS: Final[dict[str, dict[str, int]]] = {
    "cumulative.informative": {"negative": 0, "positive": 321_856, "zero": 44_408},
    "cumulative.misinformative": {"negative": 0, "positive": 278_984, "zero": 87_280},
    "cumulative.net": {"negative": 29_496, "positive": 252_816, "zero": 83_952},
    "atom.informative": {"negative": 0, "positive": 145_100, "zero": 221_164},
    "atom.misinformative": {"negative": 0, "positive": 71_468, "zero": 294_796},
    "atom.net": {"negative": 31_284, "positive": 96_768, "zero": 238_212},
}

NONCLAIMS: Final[list[str]] = [
    "The bounded census is not an arbitrary-alphabet, arbitrary-total, population, estimator-calibration, or general theorem.",
    "The human transcription of MGW equations is an external premise; paper-to-code correspondence is not established.",
    "The lexical Rust route does not establish Rust parsing, name resolution, compilation, execution, or numeric agreement.",
    "No binary64 or certified-logarithm refinement is established.",
    "The source and receipt bindings provide repository custody, not authenticity, authorship, priority, release identity, or attestation.",
    "Sequential bounded reads and repeated configuration, attribute, source, index, and status checks are not an atomic snapshot, adversarial execution boundary, or live monitor and cannot exclude a transient change completed between observations; in particular, a concurrent Git/common info-attributes or configuration insertion could affect an in-flight Git process before a later check detects it.",
    "Git status does not report ignored paths, writes outside the worktree, or transient changes that begin and end between observations.",
    "Implementation-disjoint routes retain shared semantic premises, conventions, runtime, and human transcription.",
    "SHA-256 bindings do not by themselves authenticate artifacts or exclude hash or host compromise.",
    "GO statuses are lane-local checks, not scientific or application validation.",
    "P1 is adjacent provenance only and was neither consumed nor replayed by this receipt.",
    "The receipt does not output pointwise atom values; local event ratios appear only as factors in averaged exact products.",
    "The receipt's two-route agreement observation is a matching neutral-v2 SHA-256 value plus six matching exact census blocks; it is not a direct record-by-record receipt comparison or a claim of logical independence.",
    "Process-group cleanup cannot detect a child that deliberately escapes into another session; the six exact entrypoint sources were lexically screened for common escape primitives, not proven incapable of escape.",
    "POSIX provides no atomic compare-and-unlink primitive; a caught pre-release write or postwrite exception attempts to invalidate the exact retained O_RDWR inode into a non-JSON mode-0600 tombstone (affecting every hard link to that inode), and O_EXCL prevents automatic overwrite; after finalized bytes, mode, path, source, status, host, file fsync, and parent fsync are verified, a descriptor-release error instead retains those bytes for prospective validation and never claims WROTE; process kill, power loss, crash atomicity, and close-error durability semantics are not covered.",
    "Repeated executable-byte and version observations do not prove which interpreter bytes launched the already-running process and are not an atomic or authentic host snapshot.",
    "captured_at_utc is a local wall-clock observation, not a trusted timestamp or external time attestation.",
    "Receipt-v1 deliberately rejects any local filter, attribute, or include configuration route, every effective filter attribute on the probed path roster, and stage-0 gitlinks as verifier compatibility and nested-metadata bounds; a future repository adoption of LFS, another clean filter, or submodules requires a reviewed versioned verifier migration rather than weakening this evidence retrospectively.",
    "Receipt preservation covers only the current non-shallow HEAD-reachable graph; it cannot detect absent, unreachable, or force-rewritten history and is not a transparency log or externally anchored immutability proof.",
]


class CheckError(RuntimeError):
    """A closed receipt, source topology, or preservation obligation failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    ).encode("utf-8")


def strict_json(raw: bytes, label: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise CheckError(f"duplicate JSON key in {label}: {key}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> Any:
        raise CheckError(f"non-finite JSON constant in {label}: {token}")

    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CheckError(f"invalid JSON: {label}") from error


def clean_environment(*, attribute_source: str | None = None) -> dict[str, str]:
    environment = {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
    }
    if attribute_source is not None:
        environment["GIT_ATTR_SOURCE"] = attribute_source
    return environment


def git_executable() -> Path:
    found = shutil.which("git", path=clean_environment()["PATH"])
    require(found is not None, "git executable is absent")
    return Path(found).resolve()


def bootstrap_head_oid() -> str:
    try:
        status, stdout, stderr, timed_out = CAPTURE_SUPPORT.run_capped(
            [
                os.fspath(git_executable()),
                "--no-pager",
                "--literal-pathspecs",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-c",
                "core.ignoreStat=false",
                "-c",
                "core.commitGraph=false",
                "-c",
                f"core.attributesFile={os.devnull}",
                "-c",
                "core.filemode=true",
                "-c",
                "core.symlinks=true",
                "-c",
                "core.checkStat=default",
                "-c",
                "core.trustctime=true",
                "rev-parse",
                "--verify",
                "HEAD^{commit}",
            ],
            cwd=ROOT,
            timeout_seconds=TOOL_TIMEOUT_SECONDS,
            stdout_cap=256,
            stderr_cap=TOOL_OUTPUT_CAP_BYTES,
            environment=clean_environment(attribute_source=None),
        )
    except CAPTURE_SUPPORT.ReceiptError as error:
        raise CheckError("exact HEAD bootstrap process failed closed") from error
    require(
        status == 0
        and not timed_out
        and stderr == b""
        and re.fullmatch(rb"[0-9a-f]{40}\n", stdout) is not None,
        "exact HEAD bootstrap failed closed",
    )
    return stdout[:-1].decode("ascii")


def run_git(
    arguments: list[str],
    *,
    stdin_bytes: bytes | None = None,
    attribute_source: str | None = None,
    pin_attributes: bool = True,
) -> tuple[int, bytes, bytes]:
    require(
        pin_attributes or attribute_source is None,
        "an explicit attribute source cannot be combined with an effective probe",
    )
    exact_attribute_source = None
    if pin_attributes:
        exact_attribute_source = (
            bootstrap_head_oid() if attribute_source is None else attribute_source
        )
    try:
        status, stdout, stderr, timed_out = CAPTURE_SUPPORT.run_capped(
            [
                os.fspath(git_executable()),
                "--no-pager",
                "--literal-pathspecs",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-c",
                "core.ignoreStat=false",
                "-c",
                "core.commitGraph=false",
                "-c",
                f"core.attributesFile={os.devnull}",
                "-c",
                "core.filemode=true",
                "-c",
                "core.symlinks=true",
                "-c",
                "core.checkStat=default",
                "-c",
                "core.trustctime=true",
                "-c",
                "core.quotePath=false",
                "-c",
                "diff.renames=false",
                *arguments,
            ],
            cwd=ROOT,
            timeout_seconds=TOOL_TIMEOUT_SECONDS,
            stdout_cap=TOOL_OUTPUT_CAP_BYTES,
            stderr_cap=TOOL_OUTPUT_CAP_BYTES,
            stdin_bytes=stdin_bytes,
            environment=clean_environment(attribute_source=exact_attribute_source),
        )
    except CAPTURE_SUPPORT.ReceiptError as error:
        raise CheckError("guarded Git process failed closed") from error
    require(not timed_out, "git command timed out")
    return status, stdout, stderr


def git_bytes(
    arguments: list[str],
    *,
    stdin_bytes: bytes | None = None,
    attribute_source: str | None = None,
    pin_attributes: bool = True,
) -> bytes:
    status, stdout, stderr = run_git(
        arguments,
        stdin_bytes=stdin_bytes,
        attribute_source=attribute_source,
        pin_attributes=pin_attributes,
    )
    require(status == 0 and stderr == b"", f"git command failed: {' '.join(arguments[:2])}")
    return stdout


def git_line(arguments: list[str]) -> str:
    output = git_bytes(arguments)
    require(output.endswith(b"\n") and output.count(b"\n") == 1, "Git line shape drifted")
    return output[:-1].decode("ascii", errors="strict")


STATUS_ARGUMENTS: Final[list[str]] = [
    "status",
    "--porcelain=v1",
    "-z",
    "--untracked-files=all",
    "--ignore-submodules=all",
    "--no-renames",
]


def require_supported_git_version(head_oid: str) -> None:
    raw = git_bytes(["version"], attribute_source=head_oid)
    match = re.fullmatch(rb"git version ([0-9]+)\.([0-9]+)\.([0-9]+)(?:[^\n]*)\n", raw)
    require(match is not None, "Git version output is unsupported")
    observed = tuple(int(component) for component in match.groups())
    require(
        observed >= MINIMUM_GIT_VERSION,
        "Git 2.41.0 or newer is required for exact attribute-source custody",
    )


def require_status_attribute_closure(head_oid: str) -> None:
    def require_configuration_closed() -> None:
        config_keys = git_bytes(
            ["config", "--no-includes", "--null", "--name-only", "--list"],
            attribute_source=head_oid,
        )
        keys = [
            raw_key.decode("utf-8", errors="strict").lower()
            for raw_key in config_keys.split(b"\0")
            if raw_key != b""
        ]
        require(
            keys.count("core.attributesfile") == 1,
            "the sole command-line core.attributesFile guard is not observable",
        )
        for key in keys:
            require(
                not key.startswith("filter.")
                and key != "attr.tree"
                and key != "include.path"
                and not (key.startswith("includeif.") and key.endswith(".path")),
                "Git filter, attribute, or include configuration is unsupported",
            )
        for selector in ("--git-common-dir", "--git-dir"):
            raw = git_bytes(["rev-parse", selector], attribute_source=head_oid)
            require(
                raw.endswith(b"\n") and raw.count(b"\n") == 1,
                "Git metadata-directory line shape drifted",
            )
            raw_directory = Path(raw[:-1].decode("ascii", errors="strict"))
            unresolved = (
                raw_directory if raw_directory.is_absolute() else ROOT / raw_directory
            )
            require(
                not os.path.lexists(unresolved / "info" / "attributes"),
                "Git info/attributes state is unsupported",
            )

    require_configuration_closed()
    tracked_raw = git_bytes(["ls-files", "-z"], attribute_source=head_oid)
    require(tracked_raw.endswith(b"\0"), "tracked-path attribute roster lacks NUL framing")
    tracked_list = tracked_raw[:-1].split(b"\0")
    tracked = set(tracked_list)
    require(
        tracked and b"" not in tracked and len(tracked) == len(tracked_list),
        "tracked-path attribute roster is empty or duplicated",
    )
    receipt_raw = RECEIPT_RELATIVE.encode("utf-8")
    requested = sorted(tracked | {receipt_raw})
    requested_raw = b"\0".join(requested) + b"\0"

    def reject_filter_triples(output: bytes, label: str) -> None:
        if output == b"":
            return
        require(output.endswith(b"\0"), "check-attr output lacks NUL framing")
        tokens = output[:-1].split(b"\0")
        require(len(tokens) % 3 == 0, "check-attr output shape drifted")
        records: set[tuple[bytes, bytes]] = set()
        for index in range(0, len(tokens), 3):
            raw_path, attribute, _value = tokens[index : index + 3]
            require(raw_path in requested, "check-attr reported an unrequested path")
            require(
                (raw_path, attribute) not in records,
                "check-attr repeated a path/attribute record",
            )
            records.add((raw_path, attribute))
            require(attribute != b"filter", f"a requested path declares the filter attribute in {label}")

    head_explicit = git_bytes(
        ["check-attr", "-z", f"--source={head_oid}", "--stdin", "--all"],
        stdin_bytes=requested_raw,
        attribute_source=head_oid,
    )
    head_environment = git_bytes(
        ["check-attr", "-z", "--stdin", "--all"],
        stdin_bytes=requested_raw,
        attribute_source=head_oid,
    )
    require(
        head_environment == head_explicit,
        "GIT_ATTR_SOURCE and explicit --source attribute observations differ",
    )
    effective = git_bytes(
        ["check-attr", "-z", "--stdin", "--all"],
        stdin_bytes=requested_raw,
        pin_attributes=False,
    )
    reject_filter_triples(head_explicit, "exact HEAD attributes")
    reject_filter_triples(effective, "effective worktree/index attributes")
    require_configuration_closed()


def require_index_state_closed(head_oid: str) -> None:
    index_rows = git_bytes(["ls-files", "-v", "-z"], attribute_source=head_oid)
    index_paths: set[bytes] = set()
    for row in index_rows.split(b"\0"):
        if row == b"":
            continue
        require(
            len(row) >= 3
            and row[1:2] == b" "
            and not (b"a" <= row[0:1] <= b"z")
            and row[0:2] != b"S ",
            "tracked index contains assume-unchanged or skip-worktree state",
        )
        raw_path = row[2:]
        require(
            raw_path != b"" and raw_path not in index_paths,
            "tracked index path roster is empty or duplicated",
        )
        index_paths.add(raw_path)
    require(index_paths, "tracked index path roster is empty")
    sparse_rows = git_bytes(
        ["ls-files", "--sparse", "--stage", "-z"],
        attribute_source=head_oid,
    )
    stage_paths: set[bytes] = set()
    for row in sparse_rows.split(b"\0"):
        if row == b"":
            continue
        require(row.count(b"\t") == 1, "tracked stage row framing drifted")
        metadata, raw_path = row.split(b"\t", 1)
        fields = metadata.split(b" ")
        require(
            len(fields) == 3
            and fields[0] in {b"100644", b"100755", b"120000", b"040000", b"160000"}
            and re.fullmatch(rb"[0-9a-f]{40,64}", fields[1]) is not None
            and fields[2] == b"0"
            and raw_path != b"",
            "tracked stage row is malformed or unmerged",
        )
        require(raw_path not in stage_paths, "tracked stage path is duplicated")
        stage_paths.add(raw_path)
        require(
            fields[0] in {b"100644", b"100755", b"120000"},
            "tracked index contains a sparse-directory, gitlink, or unsupported entry",
        )
    require(stage_paths == index_paths, "tracked stage and index path rosters differ")


def status_bytes() -> bytes:
    head_oid = bootstrap_head_oid()
    require_supported_git_version(head_oid)
    require_status_attribute_closure(head_oid)
    require_index_state_closed(head_oid)
    observed = git_bytes(STATUS_ARGUMENTS, attribute_source=head_oid)
    require(
        bootstrap_head_oid() == head_oid,
        "HEAD changed across the exact-attribute-source status observation",
    )
    require_status_attribute_closure(head_oid)
    require_index_state_closed(head_oid)
    require(
        bootstrap_head_oid() == head_oid,
        "HEAD changed across the post-status attribute observation",
    )
    return observed


def safe_read_regular(path: Path, *, mode: int, cap: int = 32 * 1024 * 1024) -> bytes:
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == mode
        and 0 < before.st_size <= cap,
        f"regular-file metadata rejected: {path.name}",
    )
    require(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW is unavailable")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        require(
            (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink, opened.st_size)
            == (before.st_dev, before.st_ino, before.st_mode, before.st_nlink, before.st_size),
            "opened file identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", "short regular-file read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "regular file grew while read")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    for field in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns"):
        require(
            getattr(before, field) == getattr(opened, field) == getattr(after_fd, field) == getattr(after, field),
            "regular file changed during bounded read",
        )
    return b"".join(chunks)


def ls_tree_entry(commit: str, relative: str) -> tuple[str, str, bytes] | None:
    listing = git_bytes(["ls-tree", "-z", commit, "--", relative])
    if listing == b"":
        return None
    require(listing.count(b"\0") == 1 and listing.endswith(b"\0"), "ls-tree shape drifted")
    metadata, raw_path = listing[:-1].split(b"\t", 1)
    mode, object_type, oid = metadata.decode("ascii").split(" ")
    require(raw_path.decode("utf-8", errors="strict") == relative and object_type == "blob", "ls-tree path/type drifted")
    return mode, oid, git_bytes(["cat-file", "blob", oid])


def parse_name_status(raw: bytes) -> list[tuple[str, str]]:
    if raw == b"":
        return []
    require(raw.endswith(b"\0"), "diff-tree output lacks NUL framing")
    tokens = raw[:-1].split(b"\0")
    require(len(tokens) % 2 == 0, "diff-tree framing drifted")
    return [
        (
            tokens[index].decode("ascii", errors="strict"),
            tokens[index + 1].decode("utf-8", errors="strict"),
        )
        for index in range(0, len(tokens), 2)
    ]


def canonical_repository() -> None:
    exact_head = bootstrap_head_oid()
    require_supported_git_version(exact_head)
    require(Path(git_line(["rev-parse", "--show-toplevel"])).resolve() == ROOT, "noncanonical repository root")
    raw_common = Path(git_line(["rev-parse", "--git-common-dir"]))
    raw_git_dir = Path(git_line(["rev-parse", "--git-dir"]))
    unresolved_common = raw_common if raw_common.is_absolute() else ROOT / raw_common
    unresolved_git_dir = raw_git_dir if raw_git_dir.is_absolute() else ROOT / raw_git_dir
    for unresolved in {unresolved_common, unresolved_git_dir}:
        require(not unresolved.is_symlink(), "Git metadata directory symlinks are unsupported")
    common = unresolved_common.resolve()
    git_dir = unresolved_git_dir.resolve()
    for directory in {common, git_dir}:
        metadata = directory.lstat()
        require(stat.S_ISDIR(metadata.st_mode) and not directory.is_symlink(), "Git metadata directory is not canonical")
        require(not os.path.lexists(directory / "info" / "grafts"), "Git graft state is unsupported")
        require(not os.path.lexists(directory / "info" / "sparse-checkout"), "Git sparse-checkout state is unsupported")
        require(not os.path.lexists(directory / "info" / "attributes"), "Git info/attributes state is unsupported")
    objects = common / "objects"
    for index, directory in enumerate((objects, objects / "info", objects / "pack")):
        if index > 0 and not os.path.lexists(directory):
            continue
        metadata = directory.lstat()
        require(
            stat.S_ISDIR(metadata.st_mode) and not directory.is_symlink(),
            "Git object storage directories must be real local directories",
        )
    for relative in ("objects/info/alternates", "objects/info/http-alternates"):
        require(not os.path.lexists(common / relative), "Git object alternates are unsupported")
    require(not any((common / "objects" / "pack").glob("*.promisor")), "promisor object packs are unsupported")
    config_keys = git_bytes(["config", "--no-includes", "--null", "--name-only", "--list"])
    keys = [
        raw_key.decode("utf-8", errors="strict").lower()
        for raw_key in config_keys.split(b"\0")
        if raw_key != b""
    ]
    require(
        keys.count("core.attributesfile") == 1,
        "the sole command-line core.attributesFile guard is not observable",
    )
    for key in keys:
        require(
            key not in {"extensions.partialclone", "core.sparsecheckout", "core.sparsecheckoutcone"}
            and key != "include.path"
            and not key.startswith("filter.")
            and key != "attr.tree"
            and not (key.startswith("includeif.") and key.endswith(".path"))
            and not (key.startswith("remote.") and key.endswith(".promisor"))
            and not (key.startswith("remote.") and key.endswith(".partialclonefilter")),
            "partial-clone, promisor, or sparse Git configuration is unsupported",
        )
    require(
        git_bytes(["for-each-ref", "--format=%(refname)", "refs/replace"]) == b"",
        "dormant Git replacement refs are unsupported",
    )
    require(git_line(["rev-parse", "--is-shallow-repository"]) == "false", "shallow history is unsupported")
    require(git_line(["rev-parse", f"{BASE_COMMIT}^{{tree}}"] ) == BASE_TREE, "base tree drifted")
    require_status_attribute_closure(exact_head)
    require(
        bootstrap_head_oid() == exact_head,
        "HEAD changed across canonical repository validation",
    )


def source_package(source_commit: str, *, require_live: bool) -> dict[str, Any]:
    parents = git_line(["rev-list", "--parents", "-n", "1", source_commit]).split()
    require(parents == [source_commit, BASE_COMMIT], "source topology drifted")
    source_tree = git_line(["rev-parse", f"{source_commit}^{{tree}}"])
    observed = parse_name_status(
        git_bytes(
            [
                "diff-tree",
                "--no-commit-id",
                "--name-status",
                "--no-renames",
                "-r",
                "-z",
                BASE_COMMIT,
                source_commit,
            ]
        )
    )
    expected = sorted((status, path) for path, (status, _mode) in SOURCE_DELTA.items())
    require(sorted(observed) == expected, "source delta roster drifted")
    delta: list[dict[str, Any]] = []
    for relative in sorted(SOURCE_DELTA):
        expected_status, expected_mode = SOURCE_DELTA[relative]
        base = ls_tree_entry(BASE_COMMIT, relative)
        source = ls_tree_entry(source_commit, relative)
        require(source is not None and source[0] == expected_mode, f"source path drifted: {relative}")
        if expected_status == "A":
            require(base is None, f"added source path existed at base: {relative}")
            base_mode = None
        else:
            require(base is not None and base[0] == expected_mode and base[1] != source[1], f"modified path drifted: {relative}")
            base_mode = base[0]
        if require_live:
            mode = 0o755 if source[0] == "100755" else 0o644
            require(safe_read_regular(ROOT / relative, mode=mode) == source[2], f"live source path drifted: {relative}")
        delta.append(
            {
                "path": relative,
                "status": expected_status,
                "base_mode": base_mode,
                "source_mode": source[0],
                "source_blob_oid": source[1],
                "source_sha256": sha256_bytes(source[2]),
                "source_bytes": len(source[2]),
            }
        )
    require(git_bytes(["ls-tree", "-z", source_commit, "--", RECEIPT_RELATIVE]) == b"", "receipt exists at S")
    return {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "sole_parent": BASE_COMMIT,
        "base_tree": BASE_TREE,
        "direct_child_of_required_base": True,
        "source_delta": delta,
        "receipt_path": RECEIPT_RELATIVE,
        "receipt_absent_from_source_commit": True,
    }


def execution_input(relative: str, role: str, source_commit: str, *, require_live: bool) -> dict[str, Any]:
    source = ls_tree_entry(source_commit, relative)
    require(source is not None and source[0] in {"100644", "100755"}, f"execution input drifted: {relative}")
    mode = 0o755 if source[0] == "100755" else 0o644
    if require_live:
        require(safe_read_regular(ROOT / relative, mode=mode) == source[2], f"live execution input drifted: {relative}")
    return {
        "path": relative,
        "role": role,
        "source_blob_oid": source[1],
        "git_mode": source[0],
        "live_mode": f"0{mode:o}",
        "byte_count": len(source[2]),
        "sha256": sha256_bytes(source[2]),
        "source_blob_matches_live_file": True,
    }


def execution_inputs(source_commit: str, *, require_live: bool) -> list[dict[str, Any]]:
    return [
        execution_input(relative, INPUT_ROLES[relative], source_commit, require_live=require_live)
        for relative in sorted(INPUT_ROLES)
    ]


def p1_binding(source_commit: str) -> dict[str, Any]:
    require(
        git_line(["rev-list", "--parents", "-n", "1", BASE_COMMIT]).split()
        == [BASE_COMMIT, P1_COMMIT],
        "P1 is not the sole raw parent of the P5 core base commit",
    )
    status, stdout, stderr = run_git(["merge-base", "--is-ancestor", P1_COMMIT, source_commit])
    require(status == 0 and stdout == b"" and stderr == b"", "P1 is not an ancestor of S")
    require(git_line(["rev-parse", f"{P1_COMMIT}^{{tree}}"] ) == P1_TREE, "P1 tree drifted")
    paths: list[dict[str, Any]] = []
    for relative in P1_PATHS:
        baseline = ls_tree_entry(P1_COMMIT, relative)
        source = ls_tree_entry(source_commit, relative)
        require(baseline is not None and source == baseline, f"P1 path drifted: {relative}")
        paths.append(
            {
                "path": relative,
                "baseline_blob_oid": baseline[1],
                "source_blob_oid": source[1],
                "git_mode": baseline[0],
                "byte_count": len(baseline[2]),
                "sha256": sha256_bytes(baseline[2]),
                "unchanged_at_source": True,
            }
        )
    return {
        "baseline_commit": P1_COMMIT,
        "baseline_tree": P1_TREE,
        "adjacent_child_commit": BASE_COMMIT,
        "adjacent_child_has_p1_as_sole_parent": True,
        "baseline_is_ancestor_of_source": True,
        "path_count": 10,
        "paths": paths,
        "consumed": False,
        "replayed": False,
        "fresh_execution_credit": "none",
        "semantic_transfer": "none",
        "relationship": "adjacent_separate_lane_provenance_only",
    }


def expected_findings() -> dict[str, Any]:
    return {
        "domain": {
            "object_kind": "keyed_scalar_audit_expression",
            "labeled_binary_tables": 20_348,
            "total_count_minimum": 1,
            "total_count_maximum": 5,
            "tables_by_total": [16, 136, 816, 3_876, 15_504],
            "primitive_rational_laws": 20_164,
            "nonprimitive_rescaled_count_vectors": 184,
            "full_support_16_cell_laws": 0,
            "maximum_positive_cells": 5,
            "antichain_positions": 18,
            "representation_stages": ["cumulative_values", "mobius_atoms"],
            "components": ["informative", "misinformative", "net"],
            "expressions_per_table": 108,
            "expression_evaluations": 2_197_584,
            "strictly_positive_exact_products": 2_197_584,
            "pointwise_atom_values_output": 0,
            "local_event_ratios_used_only_as_averaged_product_factors": True,
            "census_weighting": "one_vote_per_labelled_count_vector_not_prevalence_or_probability",
        },
        "sign_semantics": {
            "exact_product_Q_strictly_positive": True,
            "negative": "Q_lt_1",
            "zero": "Q_eq_1_and_log_expression_eq_0_not_product_zero",
            "positive": "Q_gt_1",
        },
        "sign_census": SIGN_CENSUS,
        "digests": {
            "route_neutral_v2_expression_stream_sha256": "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8",
            "primary_route_native_stream_sha256": "315592501f49021ed86218ba1c277b9e9b764ace9621c8b4df61bb5868f3ead0",
            "independent_route_native_stream_sha256": "4996153f04315852492bbff45548ad241f8aeaacad11e25ab510bc86267c201a",
            "primary_corpus_stream_sha256": "5eb678eba27eea449ea5c0875c2a930ec5fcd0764718aaddfae8283fbdfc6309",
            "independent_corpus_stream_sha256": "474da2048645445d5f221f50c7d0992cadc8819eba3674107f2a69059ced9b4e",
            "primary_audit_registry_sha256": "6ada33aa90382316ae0757ed7f449e9fa9a35db3a7d4aec8aa3660a4c6e3c3d5",
            "independent_audit_registry_sha256": "da4d8e7ea2793983f8758a7c72dfa8b0ac1ffaeb67fba57711064f1ceb6840d4",
            "primary_neutral_v2_framing_unit_sha256": "035c467bcf756e4009db452ec43f48747ce0f70ebdb43780d9925bf5124c24d2",
            "independent_table_bound_framing_probe_sha256": "f115265206099bac95b22149dc83c98fed2de93c4265a001c232266e02f4d813",
            "lexical_rust_route_manifest_sha256": "e0ef5a05bbade1ccbd83767ee0e1e39f05276790bb2b433dd8e5fff7ea83046a",
        },
        "lexical_rust_route": {
            "classification": "lexical_source_route_only",
            "anchor_count": 21,
            "route_manifest_sha256": "e0ef5a05bbade1ccbd83767ee0e1e39f05276790bb2b433dd8e5fff7ea83046a",
            "numeric_rust_expressions_compared": 0,
            "boundaries": ROUTE_BOUNDARIES,
        },
        "algebraic_dependencies": {
            "cumulative_net_equals_informative_minus_misinformative_per_position": 18,
            "atom_net_equals_informative_minus_misinformative_per_position": 18,
            "zeta_cumulative_from_atom_identities": 54,
            "component_base_rank_or_independence_adjudicated": False,
        },
        "classification": {
            "bounded_exact_two_route_agreement": True,
            "agreement_observation": "matching_neutral_v2_sha256_plus_six_exact_census_blocks_not_direct_record_by_record_receipt_comparison_or_logical_independence",
            "route_and_representation_neutrality_scope": "explicit_v2_only",
            "paper_correspondence": "external_premise_open",
            "compiled_rust_refinement": "open",
            "scientific_validation": False,
            "new_pid_measure_or_priority_claim": False,
        },
    }


EXPECTED_VALIDATION: Final[dict[str, bool]] = {
    "all_commands_exit_zero": True,
    "all_entrypoint_source_sha256_values_bound": True,
    "entrypoint_escape_primitives_lexically_absent": True,
    "all_stderr_empty": True,
    "all_stdout_nonempty": True,
    "all_stdout_sha256_values_pinned": True,
    "execution_inputs_match_source_blobs_and_live_files": True,
    "normal_optimized_pairs_byte_identical": True,
    "prewrite_host_boundary_reverified": True,
    "pending_placeholder_only_untracked": True,
    "pending_placeholder_live_mode_0600": True,
    "pending_placeholder_reread_exact": True,
    "pre_finalization_source_reverified": True,
    "pre_finalization_host_boundary_reverified": True,
    "pre_finalization_status_exact": True,
    "receipt_absent_from_source_commit": True,
    "source_status_empty_before_input_selection": True,
    "source_status_empty_immediately_before_pending_create": True,
}


def validate_schema_definition(schema: Any) -> None:
    try:
        validate_schema({}, schema, name="schema-definition probe")
    except InstanceValidationError:
        return
    except SchemaDefinitionError as error:
        raise CheckError("receipt schema definition is unsupported") from error
    raise CheckError("receipt schema unexpectedly accepts an empty object")


def validate_commands(commands: Any, inputs: list[dict[str, Any]]) -> None:
    require(isinstance(commands, list) and len(commands) == 12, "command roster length drifted")
    input_by_path = {entry["path"]: entry for entry in inputs}
    expected_index = 0
    for base_id, relative, stdout_sha, stdout_format, stdout_bytes in COMMAND_ROSTER:
        pair: list[dict[str, Any]] = []
        for mode in ("normal", "optimized"):
            observed = commands[expected_index]
            expected_index += 1
            require(isinstance(observed, dict), "command entry is not an object")
            public_argv = ["$PYTHON"]
            if mode == "optimized":
                public_argv.append("-O")
            public_argv.extend(["-I", "-S", "-B", f"$REPOSITORY/{relative}"])
            require(
                observed.get("id") == f"{base_id}_{mode}"
                and observed.get("entrypoint") == relative
                and observed.get("mode") == mode
                and observed.get("argv") == public_argv
                and observed.get("timeout_seconds") == 7_200
                and observed.get("stdout_cap_bytes") == 4 * 1024 * 1024
                and observed.get("stderr_cap_bytes") == 1024 * 1024
                and observed.get("exit_status") == 0
                and observed.get("timed_out") is False
                and observed.get("stdout_bytes") == stdout_bytes
                and observed.get("stdout_sha256") == stdout_sha
                and observed.get("stdout_format") == stdout_format
                and observed.get("stderr_bytes") == 0
                and observed.get("stderr_sha256") == EMPTY_SHA256
                and observed.get("entrypoint_source_sha256") == input_by_path[relative]["sha256"],
                f"command binding drifted: {base_id}/{mode}",
            )
            pair.append(observed)
        require(
            pair[0]["stdout_sha256"] == pair[1]["stdout_sha256"]
            and pair[0]["stdout_bytes"] == pair[1]["stdout_bytes"],
            f"normal/optimized receipt pair drifted: {base_id}",
        )


def validate_receipt_document(
    receipt: Any,
    schema: Any,
    source: dict[str, Any],
    inputs: list[dict[str, Any]],
    adjacent: dict[str, Any],
) -> None:
    require(isinstance(receipt, dict), "receipt root is not an object")
    try:
        validate_schema(receipt, schema, name="SxPID3 audit-expression receipt")
    except (InstanceValidationError, SchemaDefinitionError) as error:
        raise CheckError("receipt does not satisfy the closed source schema") from error
    captured_at = receipt.get("captured_at_utc")
    require(isinstance(captured_at, str), "capture wall-clock field is absent")
    try:
        parsed_capture_time = datetime.strptime(captured_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise CheckError(
            "capture wall-clock field is not a real canonical UTC calendar time"
        ) from error
    require(
        parsed_capture_time.strftime("%Y-%m-%dT%H:%M:%SZ") == captured_at,
        "capture wall-clock field does not round-trip canonically",
    )
    require(receipt.get("result_id") == RESULT_ID, "result identity drifted")
    require(receipt.get("source_package") == source, "source package binding drifted")
    require(receipt.get("execution_inputs") == inputs, "execution-input roster drifted")
    require(receipt.get("p1_adjacent_lane") == adjacent, "P1 adjacent binding drifted")
    validate_commands(receipt.get("commands"), inputs)
    require(receipt.get("findings") == expected_findings(), "closed findings drifted")
    require(receipt.get("validation") == EXPECTED_VALIDATION, "validation booleans drifted")
    require(receipt.get("nonclaims") == NONCLAIMS, "nonclaim boundary drifted")


def load_schema_at(source_commit: str) -> Any:
    entry = ls_tree_entry(source_commit, SCHEMA_RELATIVE)
    require(entry is not None and entry[0] == "100644", "source schema blob is absent")
    schema = strict_json(entry[2], "source receipt schema")
    validate_schema_definition(schema)
    return schema


def source_context(source_commit: str, *, require_live: bool) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], Any]:
    source = source_package(source_commit, require_live=require_live)
    inputs = execution_inputs(source_commit, require_live=require_live)
    adjacent = p1_binding(source_commit)
    schema = load_schema_at(source_commit)
    return source, inputs, adjacent, schema


def require_head_tree(expected_head: str, expected_tree: str, label: str) -> None:
    require(
        git_line(["rev-parse", "HEAD"]) == expected_head
        and git_line(["rev-parse", "HEAD^{tree}"]) == expected_tree,
        f"{label} HEAD or tree changed during validation",
    )


def source_side() -> dict[str, Any]:
    canonical_repository()
    require(status_bytes() == b"", "source-side repository is not exactly clean")
    source_commit = git_line(["rev-parse", "HEAD"])
    source, inputs, adjacent, schema = source_context(source_commit, require_live=True)
    require(not os.path.lexists(RECEIPT_PATH), "receipt exists in source-side filesystem")
    require(git_bytes(["ls-tree", "-z", source_commit, "--", RECEIPT_RELATIVE]) == b"", "receipt is tracked at source side")
    final_context = source_context(source_commit, require_live=True)
    require(
        final_context == (source, inputs, adjacent, schema),
        "source-side package changed during validation",
    )
    require(not os.path.lexists(RECEIPT_PATH), "receipt appeared during source-side validation")
    require(
        git_bytes(["ls-tree", "-z", source_commit, "--", RECEIPT_RELATIVE]) == b"",
        "receipt appeared in the source commit during validation",
    )
    schema_entry = ls_tree_entry(source_commit, SCHEMA_RELATIVE)
    require(schema_entry is not None, "source schema blob disappeared")
    canonical_repository()
    require(status_bytes() == b"", "source-side repository changed during validation")
    require_head_tree(source_commit, source["source_tree"], "source-side")
    return {
        "input_count": len(inputs),
        "mode": "source-side",
        "p1_path_count": adjacent["path_count"],
        "receipt_state": "absent",
        "schema_blob_sha256": sha256_bytes(schema_entry[2]),
        "source_commit": source_commit,
        "source_tree": source["source_tree"],
        "status": "GO",
    }


def prospective() -> dict[str, Any]:
    canonical_repository()
    expected_status = b"?? " + RECEIPT_RELATIVE.encode("utf-8") + b"\0"
    require(status_bytes() == expected_status, "prospective state is not the sole untracked receipt")
    source_commit = git_line(["rev-parse", "HEAD"])
    require(git_bytes(["ls-tree", "-z", source_commit, "--", RECEIPT_RELATIVE]) == b"", "prospective receipt is already tracked")
    source, inputs, adjacent, schema = source_context(source_commit, require_live=True)
    raw = safe_read_regular(RECEIPT_PATH, mode=0o600)
    receipt = strict_json(raw, "prospective receipt")
    require(canonical_json(receipt) == raw, "prospective receipt encoding is not canonical")
    validate_receipt_document(receipt, schema, source, inputs, adjacent)
    require(
        source_context(source_commit, require_live=True)
        == (source, inputs, adjacent, schema),
        "source package changed during prospective validation",
    )
    require(
        safe_read_regular(RECEIPT_PATH, mode=0o600) == raw,
        "prospective receipt changed during validation",
    )
    canonical_repository()
    require(status_bytes() == expected_status, "prospective status changed during validation")
    require_head_tree(source_commit, source["source_tree"], "prospective")
    return {
        "evidence_commit": None,
        "mode": "prospective",
        "receipt_sha256": sha256_bytes(raw),
        "receipt_state": "sole_untracked_file",
        "source_commit": source_commit,
        "status": "GO",
    }


def receipt_introduction_frontiers(head: str) -> list[str]:
    """Use the raw full parent graph; never trust path-simplified parent lists."""

    output = git_bytes(["rev-list", "--parents", head])
    parent_rows: list[tuple[str, list[str]]] = []
    for line in output.decode("ascii", errors="strict").splitlines():
        fields = line.split()
        require(
            fields
            and all(
                len(field) == 40
                and all(character in "0123456789abcdef" for character in field)
                for field in fields
            ),
            "raw full-history parent row is malformed",
        )
        commit, *parents = fields
        parent_rows.append((commit, parents))
    entry_cache: dict[str, tuple[str, str, bytes] | None] = {}

    def entry(commit: str) -> tuple[str, str, bytes] | None:
        if commit not in entry_cache:
            entry_cache[commit] = ls_tree_entry(commit, RECEIPT_RELATIVE)
        return entry_cache[commit]

    frontiers: list[str] = []
    for commit, parents in parent_rows:
        child_entry = entry(commit)
        if child_entry is None:
            continue
        if not parents or all(entry(parent) is None for parent in parents):
            frontiers.append(commit)
    return sorted(set(frontiers))


def unique_introduction_commit(head: str) -> str:
    frontiers = receipt_introduction_frontiers(head)
    require(
        len(frontiers) == 1,
        "receipt introduction is not one unique raw-full-history frontier",
    )
    return frontiers[0]


def require_preserved_receipt_chain(
    observations: list[tuple[str, tuple[str, str, bytes] | None]],
    expected: tuple[str, str, bytes],
) -> None:
    require(bool(observations), "receipt preservation chain is empty")
    for _commit, observed in observations:
        require(
            observed == expected,
            "an ancestry-path commit does not preserve the exact receipt blob and mode",
        )


def ancestry_path(source_commit: str, head: str) -> list[str]:
    if source_commit == head:
        return [source_commit]
    status, stdout, stderr = run_git(
        ["merge-base", "--is-ancestor", source_commit, head]
    )
    require(status == 0 and stdout == b"" and stderr == b"", "required ancestor is not in HEAD history")
    raw = git_bytes(
        ["rev-list", "--reverse", "--ancestry-path", f"{source_commit}..{head}"]
    )
    commits = raw.decode("ascii", errors="strict").splitlines()
    require(commits and commits[-1] == head, "ancestry-path traversal did not reach HEAD")
    return [source_commit, *commits]


def require_source_infrastructure_preserved(source_commit: str, head: str) -> None:
    expected = {
        relative: ls_tree_entry(source_commit, relative)
        for relative in INFRASTRUCTURE_PATHS
    }
    require(all(entry is not None for entry in expected.values()), "S infrastructure blob is absent")
    for commit in ancestry_path(source_commit, head):
        for relative, source_entry in expected.items():
            require(
                ls_tree_entry(commit, relative) == source_entry,
                "versioned S receipt infrastructure changed on the ancestry path",
            )


def committed_or_preserved() -> dict[str, Any]:
    canonical_repository()
    require(status_bytes() == b"", "committed evidence worktree is not exactly clean")
    head = git_line(["rev-parse", "HEAD"])
    head_tree = git_line(["rev-parse", "HEAD^{tree}"])
    evidence_commit = unique_introduction_commit(head)
    parents = git_line(["rev-list", "--parents", "-n", "1", evidence_commit]).split()
    require(len(parents) == 2, "evidence commit does not have exactly one parent")
    source_commit = parents[1]
    require_source_infrastructure_preserved(source_commit, head)
    source, inputs, adjacent, schema = source_context(
        source_commit,
        require_live=head == evidence_commit,
    )
    require(
        parse_name_status(
            git_bytes(
                [
                    "diff-tree",
                    "--no-commit-id",
                    "--name-status",
                    "--no-renames",
                    "-r",
                    "-z",
                    source_commit,
                    evidence_commit,
                ]
            )
        )
        == [("A", RECEIPT_RELATIVE)],
        "evidence commit is not receipt-only",
    )
    status, stdout, stderr = run_git(["merge-base", "--is-ancestor", evidence_commit, head])
    require(status == 0 and stdout == b"" and stderr == b"", "evidence commit is not an ancestor of HEAD")
    at_evidence = ls_tree_entry(evidence_commit, RECEIPT_RELATIVE)
    at_head = ls_tree_entry(head, RECEIPT_RELATIVE)
    require(
        at_evidence is not None
        and at_head is not None
        and at_evidence[0] == "100644"
        and at_head == at_evidence,
        "receipt bytes or mode are not preserved from E through HEAD",
    )
    ancestry = ancestry_path(evidence_commit, head)[1:]
    require_preserved_receipt_chain(
        [
            (commit, ls_tree_entry(commit, RECEIPT_RELATIVE))
            for commit in [evidence_commit, *ancestry]
        ],
        at_evidence,
    )
    live = safe_read_regular(RECEIPT_PATH, mode=0o644)
    require(live == at_evidence[2], "live receipt differs from preserved Git blob")
    receipt = strict_json(live, "committed receipt")
    require(canonical_json(receipt) == live, "committed receipt encoding is not canonical")
    validate_receipt_document(receipt, schema, source, inputs, adjacent)
    require(receipt["source_package"]["source_commit"] == source_commit, "receipt names the wrong S")
    canonical_repository()
    require(status_bytes() == b"", "worktree changed during committed validation")
    require_head_tree(head, head_tree, "committed evidence")
    require(
        unique_introduction_commit(head) == evidence_commit,
        "receipt introduction frontier changed during validation",
    )
    require_source_infrastructure_preserved(source_commit, head)
    require(
        source_context(source_commit, require_live=head == evidence_commit)
        == (source, inputs, adjacent, schema),
        "historical source context changed during committed validation",
    )
    final_evidence = ls_tree_entry(evidence_commit, RECEIPT_RELATIVE)
    final_head = ls_tree_entry(head, RECEIPT_RELATIVE)
    require(
        final_evidence == at_evidence and final_head == at_evidence,
        "receipt Git blobs changed during committed validation",
    )
    require_preserved_receipt_chain(
        [
            (commit, ls_tree_entry(commit, RECEIPT_RELATIVE))
            for commit in ancestry_path(evidence_commit, head)
        ],
        at_evidence,
    )
    require(
        safe_read_regular(RECEIPT_PATH, mode=0o644) == live,
        "live receipt changed during final committed replay",
    )
    canonical_repository()
    require(status_bytes() == b"", "final committed replay changed the worktree")
    require_head_tree(head, head_tree, "final committed replay")
    return {
        "evidence_commit": evidence_commit,
        "head_commit": head,
        "mode": "committed-or-preserved",
        "preserved_descendant": head != evidence_commit,
        "receipt_sha256": sha256_bytes(live),
        "source_infrastructure_preserved": True,
        "source_commit": source_commit,
        "status": "GO",
    }


def workflow_mode() -> dict[str, Any]:
    canonical_repository()
    head = git_line(["rev-parse", "HEAD"])
    tracked = git_bytes(["ls-tree", "-z", head, "--", RECEIPT_RELATIVE])
    if tracked != b"":
        return committed_or_preserved()
    if os.path.lexists(RECEIPT_PATH):
        return prospective()
    return source_side()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--source-side", action="store_true")
    modes.add_argument("--prospective", action="store_true")
    modes.add_argument("--committed-or-preserved", action="store_true")
    modes.add_argument("--workflow", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.source_side:
            result = source_side()
        elif arguments.prospective:
            result = prospective()
        elif arguments.committed_or_preserved:
            result = committed_or_preserved()
        else:
            result = workflow_mode()
        sys.stdout.buffer.write(canonical_json(result))
        return 0
    except (CheckError, OSError, ValueError) as error:
        detail = str(error).replace(os.fspath(ROOT), "$REPOSITORY")
        print(f"ERROR: receipt validation failed closed: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
