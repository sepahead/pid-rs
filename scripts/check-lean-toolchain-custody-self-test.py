#!/usr/bin/env python3
"""Bounded negative controls for the Lean 4.32.2 release-asset custody gate."""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if _bootstrap_sys.version_info < (3, 11):
    print(
        "ERROR: check-lean-toolchain-custody-self-test.py requires Python >= 3.11",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
if not (
    _bootstrap_sys.flags.isolated == 1
    and getattr(_bootstrap_sys.flags, "safe_path", False) is True
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.flags.dont_write_bytecode == 1
):
    print(
        "ERROR: check-lean-toolchain-custody-self-test.py requires Python -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
import copy
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import types
from typing import Callable, Final


SELF_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SELF_PATH.parent.parent
CHECKER_PATH = ROOT / "scripts/check-lean-toolchain-custody.py"
METADATA_PATH = ROOT / "audit/formal/lean/toolchain-release-v4.32.2.json"
OBSERVATION_RAW_PATH = (
    ROOT / "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.raw.json"
)
OBSERVATION_RECEIPT_PATH = (
    ROOT
    / "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.receipt.json"
)
Q1_FAILURE_PATH = (
    ROOT
    / "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.failure.json"
)
Q1_STDERR_PATH = (
    ROOT
    / "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stderr"
)
Q1_STDOUT_PATH = (
    ROOT
    / "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout"
)
EXPECTED_CHECKER_SHA256: Final = (
    "8ae51bd1a0ec1bd0007a0d4ab09e5f81004a4a3439e1baa3483d2fe3ce65a4e3"
)
EXPECTED_METADATA_SHA256: Final = (
    "c9cfcd4c38c0d73a1e765c1abaaf8b36e73bb230fbb6b700047abf0fb58e590f"
)
EXPECTED_PRODUCTION_ROUTE_AST_SHA256: Final = (
    "cbdea368a0ae6104245c78bcc1d56ca88774c569032022a18a67d82e805c37b7"
)
EXPECTED_CHECKER_MODULE_AST_SHA256: Final = (
    "f7e977b2c2cefc3ddc676110d8afb7aa41baeb4e708091aae31a3757568c017a"
)
EXPECTED_OBSERVATION_RAW_SHA256: Final = (
    "374bc2eb53881cae4c7b989944dff3daff0fc02c2340ce39bd920a4ddb08723a"
)
EXPECTED_OBSERVATION_RECEIPT_SHA256: Final = (
    "4720cb4b6d0be274d52f36e2a16d63dcf6542ed47520b9370b956cc1d7d2a903"
)
EXPECTED_Q1_FAILURE_SHA256: Final = (
    "9dfa00952af0ac6d28be6e0401d5406b05858e729a65ade6c59805351ce511df"
)
EXPECTED_Q1_STDERR_SHA256: Final = (
    "08f1429a37d040d20ea1c1a470cc6d779d8a06a1f45627867b5fe59827c8d93c"
)
EXPECTED_Q1_STDOUT_SHA256: Final = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
EXPECTED_OBSERVATION_RECEIPT_POLICY_SHA256: Final = (
    "be144ac003a4c922bba24dcd30de4b7b184603f43319abd235f7b0b3dd6bf57b"
)
SYNTHETIC_MANIFEST_SHA256: Final = (
    "da13da306bb0633479728b18e1f3e0483166e5ae109ca464d3cab1162e3b8d31"
)
_MISSING_CHECKER_GLOBAL: Final = object()


class SelfTestError(RuntimeError):
    """A positive baseline or separately named negative control failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def source_parent_identities(
    path: Path, role: str
) -> tuple[tuple[str, int, int, int], ...]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    identities: list[tuple[str, int, int, int]] = []
    for parent in reversed(absolute.parents):
        observed = parent.lstat()
        require(
            stat.S_ISDIR(observed.st_mode) and not stat.S_ISLNK(observed.st_mode),
            f"{role} traverses a symbolic-link or non-directory parent",
        )
        identities.append(
            (os.fspath(parent), observed.st_dev, observed.st_ino, observed.st_mode)
        )
    return tuple(identities)


def source_stat_identity(
    observed: os.stat_result,
) -> tuple[int, int, int, int, int, int, int]:
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_nlink,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
    )


def read_all(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def exact_source(path: Path, expected_sha256: str, role: str) -> bytes:
    absolute = Path(os.path.abspath(os.fspath(path)))
    parents_before = source_parent_identities(absolute, role)
    try:
        before = absolute.lstat()
    except OSError as error:
        raise SelfTestError(f"cannot lstat {role}: {error}") from error
    require(stat.S_ISREG(before.st_mode), f"{role} is not regular")
    require(not absolute.is_symlink(), f"{role} is symbolic link")
    require(before.st_nlink == 1, f"{role} must have one hard link")
    require(stat.S_IMODE(before.st_mode) == 0o644, f"{role} mode must be 0644")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
        descriptor_before = os.fstat(descriptor)
        first = read_all(descriptor)
        middle = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = read_all(descriptor)
        descriptor_after = os.fstat(descriptor)
    except OSError as error:
        raise SelfTestError(f"cannot read {role}: {error}") from error
    finally:
        if "descriptor" in locals():
            os.close(descriptor)
    after = absolute.lstat()
    identities = tuple(
        source_stat_identity(item)
        for item in (before, descriptor_before, middle, descriptor_after, after)
    )
    require(
        all(identity == identities[0] for identity in identities[1:]),
        f"{role} metadata changed during double read",
    )
    require(first == second, f"{role} bytes changed during double read")
    require(len(first) == before.st_size, f"{role} byte length changed during read")
    require(
        source_parent_identities(absolute, role) == parents_before,
        f"{role} parent identity changed during double read",
    )
    require(
        hashlib.sha256(first).hexdigest() == expected_sha256,
        f"{role} exact digest differs",
    )
    return first


def load_checker() -> tuple[types.ModuleType, bytes]:
    raw = exact_source(CHECKER_PATH, EXPECTED_CHECKER_SHA256, "custody checker")
    module_name = "_pid_rs_lean_toolchain_custody_" + EXPECTED_CHECKER_SHA256
    code = compile(
        raw,
        os.fspath(CHECKER_PATH),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(CHECKER_PATH)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module, raw


checker, CHECKER_SOURCE = load_checker()
METADATA_SOURCE = exact_source(
    METADATA_PATH, EXPECTED_METADATA_SHA256, "custody metadata"
)
METADATA = checker.parse_json_object(METADATA_SOURCE, "custody metadata")
OBSERVATION_RAW_SOURCE = exact_source(
    OBSERVATION_RAW_PATH,
    EXPECTED_OBSERVATION_RAW_SHA256,
    "Darwin observation raw result",
)
OBSERVATION_RECEIPT_SOURCE = exact_source(
    OBSERVATION_RECEIPT_PATH,
    EXPECTED_OBSERVATION_RECEIPT_SHA256,
    "Darwin observation receipt",
)
OBSERVATION_RECEIPT = checker.parse_json_object(
    OBSERVATION_RECEIPT_SOURCE, "Darwin observation receipt"
)
LEGACY_V4_AUTHORITY = checker.parse_legacy_v4_authority(
    OBSERVATION_RAW_SOURCE,
    OBSERVATION_RECEIPT_SOURCE,
    enforce_published_seals=True,
)
_LEGACY_V4_RAW_BASELINE = checker.parse_json_object(
    OBSERVATION_RAW_SOURCE, "frozen legacy-v4 raw baseline"
)
LEGACY_V4_CONSTANTS: Final = {
    "authentication_boundary": copy.deepcopy(
        _LEGACY_V4_RAW_BASELINE["authentication_boundary"]
    ),
    "acyclic_policy": _LEGACY_V4_RAW_BASELINE["source_binding"]["acyclic_policy"],
    "archive": copy.deepcopy(_LEGACY_V4_RAW_BASELINE["archive"]),
    "archive_root": _LEGACY_V4_RAW_BASELINE["safe_preflight"]["single_expected_root"],
    "github_asset": copy.deepcopy(
        _LEGACY_V4_RAW_BASELINE["archive"]["advertised_github_asset"]
    ),
    "historical_receipt_binding": copy.deepcopy(
        _LEGACY_V4_RAW_BASELINE["source_binding"][
            "historical_nontransferable_receipt_binding"
        ]
    ),
    "limits": copy.deepcopy(
        _LEGACY_V4_RAW_BASELINE["safe_preflight"]["resource_limits"]
    ),
    "nested_checker_binding": copy.deepcopy(
        _LEGACY_V4_RAW_BASELINE["source_binding"]["nested_checker_binding"]
    ),
    "release_identity": copy.deepcopy(_LEGACY_V4_RAW_BASELINE["release_identity"]),
    "required_next_step": _LEGACY_V4_RAW_BASELINE["candidate_receipt"][
        "required_next_step"
    ],
}
del _LEGACY_V4_RAW_BASELINE
ASSETS = checker.validate_metadata(METADATA, LEGACY_V4_AUTHORITY)
LIMITS = METADATA["limits"]


def expect_failure(
    name: str,
    operation: Callable[[], object],
    expected: str,
    *,
    exception_type: type[BaseException] = checker.CustodyError,
) -> dict[str, object]:
    try:
        operation()
    except exception_type as error:
        observed = str(error)
        require(
            expected in observed,
            f"{name} failed for wrong reason: expected {expected!r}, found {observed!r}",
        )
        return {"name": name, "rejected": True, "reason_contains": expected}
    raise SelfTestError(f"negative control survived: {name}")


def expect_exact_failure(
    name: str,
    operation: Callable[[], object],
    expected: str,
    *,
    exception_type: type[BaseException] = checker.CustodyError,
) -> dict[str, object]:
    try:
        operation()
    except exception_type as error:
        observed = str(error)
        require(
            observed == expected,
            f"{name} failed for wrong exact reason: expected {expected!r}, "
            f"found {observed!r}",
        )
        return {"name": name, "rejected": True, "exact_reason": expected}
    raise SelfTestError(f"negative control survived: {name}")


def expect_any_failure(
    name: str,
    operation: Callable[[], object],
    *,
    exception_type: type[BaseException] = checker.CustodyError,
) -> dict[str, object]:
    try:
        operation()
    except exception_type as error:
        return {"name": name, "rejected": True, "reason": str(error)}
    raise SelfTestError(f"negative control survived: {name}")


def require_policy(candidate: dict[str, object]) -> None:
    checker.validate_metadata(candidate, LEGACY_V4_AUTHORITY)
    checker.require(
        checker.metadata_policy_sha256(candidate)
        == checker.EXPECTED_METADATA_POLICY_SHA256,
        "metadata policy projection SHA-256 drifted",
    )


def mutated_policy(path: tuple[object, ...], replacement: object) -> dict[str, object]:
    candidate = copy.deepcopy(METADATA)
    cursor: object = candidate
    for component in path[:-1]:
        if isinstance(component, int):
            require(isinstance(cursor, list), "internal mutation list route drifted")
            cursor = cursor[component]
        else:
            require(isinstance(cursor, dict), "internal mutation object route drifted")
            cursor = cursor[component]
    final = path[-1]
    if isinstance(final, int):
        require(isinstance(cursor, list), "internal mutation final list route drifted")
        cursor[final] = replacement
    else:
        require(
            isinstance(cursor, dict), "internal mutation final object route drifted"
        )
        cursor[final] = replacement
    return candidate


OBSERVATION_DYNAMIC_IDENTITY_PATHS: Final = (
    ("capture", "repository_raw_result", "bytes"),
    ("capture", "repository_raw_result", "sha256"),
    ("capture", "external_owner_mutable_custody", "result", "bytes"),
    ("capture", "external_owner_mutable_custody", "result", "sha256"),
    (
        "decisive_result_projection",
        "complete_inventory_tree_leaves_probes_authority",
        "bytes",
    ),
    (
        "decisive_result_projection",
        "complete_inventory_tree_leaves_probes_authority",
        "sha256",
    ),
)


def set_object_path(
    candidate: dict[str, object], path: tuple[object, ...], replacement: object
) -> None:
    cursor: object = candidate
    for component in path[:-1]:
        if isinstance(component, int):
            require(isinstance(cursor, list), "internal object-path list drifted")
            cursor = cursor[component]
        else:
            require(isinstance(cursor, dict), "internal object-path object drifted")
            require(component in cursor, "internal object-path component is absent")
            cursor = cursor[component]
    final = path[-1]
    if isinstance(final, int):
        require(isinstance(cursor, list), "internal object-path final list drifted")
        cursor[final] = replacement
    else:
        require(isinstance(cursor, dict), "internal object-path final object drifted")
        require(final in cursor, "internal object-path final component is absent")
        cursor[final] = replacement


def observation_receipt_policy_projection(
    receipt: dict[str, object],
) -> dict[str, object]:
    projected = copy.deepcopy(receipt)
    for path in OBSERVATION_DYNAMIC_IDENTITY_PATHS:
        set_object_path(projected, path, None)
    return projected


def observation_receipt_policy_sha256(receipt: dict[str, object]) -> str:
    return hashlib.sha256(
        checker.canonical_json_bytes(observation_receipt_policy_projection(receipt))
    ).hexdigest()


def receipt_for_observation_bytes(raw_source: bytes) -> dict[str, object]:
    receipt = copy.deepcopy(OBSERVATION_RECEIPT)
    byte_count = len(raw_source)
    digest = hashlib.sha256(raw_source).hexdigest()
    for path in OBSERVATION_DYNAMIC_IDENTITY_PATHS:
        set_object_path(
            receipt,
            path,
            byte_count if path[-1] == "bytes" else digest,
        )
    return receipt


def validate_observation_custody(
    raw_source: bytes, receipt: dict[str, object]
) -> dict[str, object]:
    checker.require(
        observation_receipt_policy_sha256(receipt)
        == EXPECTED_OBSERVATION_RECEIPT_POLICY_SHA256,
        "observation receipt policy projection drifted",
    )
    raw_sha256 = hashlib.sha256(raw_source).hexdigest()
    raw_bytes = len(raw_source)
    for path in OBSERVATION_DYNAMIC_IDENTITY_PATHS:
        cursor: object = receipt
        for component in path:
            checker.require(
                isinstance(cursor, dict),
                "observation receipt raw identity route drifted",
            )
            cursor = cursor[component]
        expected: object = raw_bytes if path[-1] == "bytes" else raw_sha256
        checker.require_exact_typed_value(
            cursor, expected, "observation receipt raw identity"
        )

    raw = checker.parse_json_object(raw_source, "Darwin observation raw result")
    checker.exact_keys(
        raw,
        {
            "archive",
            "authentication_boundary",
            "candidate_receipt",
            "canonical_tree_manifest",
            "executable_leaves",
            "execution_route",
            "host",
            "live_probes",
            "nested_kernel_regression",
            "platform_key",
            "qualification_state_before_run",
            "release_identity",
            "safe_preflight",
            "schema",
            "source_binding",
            "status",
        },
        "Darwin observation root",
    )
    checker.require(
        raw_source == checker.canonical_json_bytes(raw) + b"\n",
        "Darwin observation raw result is not canonical one-line JSON",
    )
    checker.require_exact_typed_value(
        raw.get("schema"),
        "pid-rs/lean-toolchain-release-custody-check/v4",
        "observation schema",
    )
    checker.require_exact_typed_value(
        raw.get("status"),
        "observation_only_unqualified",
        "observation status",
    )
    checker.require_exact_typed_value(
        raw.get("platform_key"), "darwin-aarch64", "observation platform"
    )
    checker.require_exact_typed_value(
        raw.get("qualification_state_before_run"),
        "hosted_pending",
        "observation prior qualification state",
    )
    decisive = receipt["decisive_result_projection"]
    checker.require(isinstance(decisive, dict), "decisive receipt projection drifted")
    for key, raw_key in (
        ("raw_schema", "schema"),
        ("status", "status"),
        ("platform_key", "platform_key"),
        ("qualification_state_before_run", "qualification_state_before_run"),
    ):
        checker.require_exact_typed_value(
            decisive[key], raw[raw_key], f"decisive receipt field {key}"
        )

    source_binding = checker.exact_keys(
        raw.get("source_binding"),
        {
            "acyclic_policy",
            "checker_bytes",
            "checker_sha256",
            "historical_nontransferable_receipt_binding",
            "metadata_bytes",
            "metadata_policy_projection_sha256",
            "metadata_sha256",
            "nested_checker_binding",
        },
        "observation source binding",
    )
    subject_files = receipt["source_subject"]
    checker.require(isinstance(subject_files, dict), "receipt source subject drifted")
    subject_files = subject_files["files"]
    checker.require(isinstance(subject_files, dict), "receipt source files drifted")
    outer = subject_files["outer_checker"]
    metadata_file = subject_files["metadata"]
    nested = subject_files["nested_checker"]
    checker.require(
        isinstance(outer, dict)
        and isinstance(metadata_file, dict)
        and isinstance(nested, dict),
        "receipt source-file identities drifted",
    )
    checker.require_exact_typed_value(
        source_binding["checker_bytes"], outer["bytes"], "source checker bytes"
    )
    checker.require_exact_typed_value(
        source_binding["checker_sha256"],
        outer["sha256"],
        "source checker digest",
    )
    checker.require_exact_typed_value(
        source_binding["metadata_bytes"],
        metadata_file["bytes"],
        "source metadata bytes",
    )
    checker.require_exact_typed_value(
        source_binding["metadata_sha256"],
        metadata_file["sha256"],
        "source metadata digest",
    )
    checker.require_exact_typed_value(
        source_binding["metadata_policy_projection_sha256"],
        metadata_file["policy_projection_sha256"],
        "source metadata projection digest",
    )
    nested_binding = checker.exact_keys(
        source_binding["nested_checker_binding"],
        {"bytes", "hard_link_count", "mode", "path", "sha256", "symbolic_link"},
        "nested source binding",
    )
    checker.require_exact_typed_value(
        nested_binding["bytes"], nested["bytes"], "nested checker bytes"
    )
    checker.require_exact_typed_value(
        nested_binding["sha256"], nested["sha256"], "nested checker digest"
    )
    metadata_nested = LEGACY_V4_CONSTANTS["nested_checker_binding"]
    checker.require(
        isinstance(metadata_nested, dict), "metadata nested binding drifted"
    )
    for observed_key, metadata_key in (
        ("path", "path"),
        ("mode", "mode"),
        ("symbolic_link", "symbolic_link"),
    ):
        checker.require_exact_typed_value(
            nested_binding[observed_key],
            metadata_nested[metadata_key],
            f"nested checker observation {observed_key}",
        )
    checker.require_exact_typed_value(
        nested_binding["hard_link_count"],
        1,
        "nested checker observation hard-link count",
    )
    checker.require_exact_typed_value(
        source_binding["acyclic_policy"],
        LEGACY_V4_CONSTANTS["acyclic_policy"],
        "source acyclic policy",
    )
    historical_binding = checker.exact_keys(
        source_binding["historical_nontransferable_receipt_binding"],
        {"bytes", "hard_link_count", "mode", "path", "sha256", "symbolic_link"},
        "historical receipt observation binding",
    )
    historical_source = LEGACY_V4_CONSTANTS["historical_receipt_binding"]
    checker.require(isinstance(historical_source, dict), "historical source drifted")
    for observed_key, metadata_key in (
        ("path", "path"),
        ("bytes", "bytes"),
        ("mode", "mode"),
        ("sha256", "sha256"),
        ("symbolic_link", "symbolic_link"),
    ):
        checker.require_exact_typed_value(
            historical_binding[observed_key],
            historical_source[metadata_key],
            f"historical receipt observation {observed_key}",
        )
    checker.require_exact_typed_value(
        historical_binding["hard_link_count"],
        1,
        "historical receipt observation hard-link count",
    )
    checker.require_exact_typed_value(
        raw.get("release_identity"),
        LEGACY_V4_CONSTANTS["release_identity"],
        "release identity",
    )

    darwin_asset = {
        "archive": {
            "root": LEGACY_V4_CONSTANTS["archive_root"],
            "sha256": LEGACY_V4_CONSTANTS["archive"]["sha256_before"],
            "size": LEGACY_V4_CONSTANTS["archive"]["size"],
        },
        "github_asset": LEGACY_V4_CONSTANTS["github_asset"],
        "host": {"machines": ["arm64", "aarch64"], "system": "Darwin"},
    }
    archive = checker.exact_keys(
        raw.get("archive"),
        {
            "advertised_github_asset",
            "extraction_decompressed_stream_bytes",
            "path",
            "preflight_decompressed_stream_bytes",
            "sha256_after",
            "sha256_before",
            "size",
        },
        "observation archive",
    )
    checker.require_exact_typed_value(
        archive["advertised_github_asset"],
        darwin_asset["github_asset"],
        "advertised Darwin asset",
    )
    checker.require_exact_typed_value(
        archive["size"], darwin_asset["archive"]["size"], "archive size"
    )
    advertised_sha256 = darwin_asset["archive"]["sha256"]
    checker.require_exact_typed_value(
        archive["sha256_before"], advertised_sha256, "archive digest before"
    )
    checker.require_exact_typed_value(
        archive["sha256_after"], advertised_sha256, "archive digest after"
    )
    checker.require(
        type(archive["preflight_decompressed_stream_bytes"]) is int
        and type(archive["extraction_decompressed_stream_bytes"]) is int
        and archive["preflight_decompressed_stream_bytes"] > 0
        and archive["preflight_decompressed_stream_bytes"]
        == archive["extraction_decompressed_stream_bytes"]
        <= LEGACY_V4_CONSTANTS["limits"]["decompressed_stream_bytes_max"],
        "observation decompressed stream lengths differ or exceed the bound",
    )
    decisive_archive = decisive["archive"]
    checker.require(isinstance(decisive_archive, dict), "decisive archive drifted")
    checker.require_exact_typed_value(
        decisive_archive["size"], archive["size"], "decisive archive size"
    )
    checker.require_exact_typed_value(
        decisive_archive["advertised_and_pre_post_sha256"],
        advertised_sha256,
        "decisive archive digest",
    )
    for key in (
        "preflight_decompressed_stream_bytes",
        "extraction_decompressed_stream_bytes",
    ):
        checker.require_exact_typed_value(
            decisive_archive[key], archive[key], f"decisive archive {key}"
        )
    capture = receipt["capture"]
    checker.require(isinstance(capture, dict), "receipt capture drifted")
    capture_archive = capture["archive_path"]
    argv = capture["literal_argv"]
    checker.require(
        isinstance(capture_archive, dict)
        and isinstance(argv, list)
        and len(argv) == 10,
        "receipt archive launch route drifted",
    )
    checker.require_exact_typed_value(
        archive["path"], capture_archive["path"], "archive capture path"
    )
    checker.require_exact_typed_value(archive["path"], argv[8], "archive argv path")

    preflight = checker.exact_keys(
        raw.get("safe_preflight"),
        {
            "inventory",
            "links_devices_fifos_sockets_rejected",
            "normalized_unique_paths",
            "only_directories_and_regular_files",
            "parent_topology_complete",
            "portable_casefold_unique_paths",
            "resource_limits",
            "single_expected_root",
        },
        "observation safe preflight",
    )
    candidate = checker.exact_keys(
        raw.get("candidate_receipt"),
        {
            "inventory",
            "leaves",
            "probes",
            "promotion_status",
            "required_next_step",
            "tree_manifest",
        },
        "observation candidate receipt",
    )
    for key in (
        "links_devices_fifos_sockets_rejected",
        "normalized_unique_paths",
        "only_directories_and_regular_files",
        "parent_topology_complete",
        "portable_casefold_unique_paths",
    ):
        checker.require_exact_typed_value(
            preflight[key], True, f"observation safe-preflight field {key}"
        )
    checker.require_exact_typed_value(
        preflight["resource_limits"],
        LEGACY_V4_CONSTANTS["limits"],
        "observation resource limits",
    )
    checker.require_exact_typed_value(
        preflight["single_expected_root"],
        darwin_asset["archive"]["root"],
        "observation archive root",
    )
    inventory = checker.exact_keys(
        preflight["inventory"],
        {
            "directories",
            "max_depth",
            "max_file_bytes",
            "max_path_bytes",
            "members",
            "regular_file_bytes",
            "regular_files",
        },
        "observation inventory",
    )
    checker.require_exact_typed_value(
        inventory, candidate["inventory"], "candidate inventory copy"
    )
    for key in (
        "members",
        "directories",
        "regular_files",
        "regular_file_bytes",
        "max_file_bytes",
        "max_path_bytes",
        "max_depth",
    ):
        checker.require(
            type(inventory[key]) is int and inventory[key] > 0,
            f"observation inventory {key} is not a positive integer",
        )
    checker.require(
        inventory["members"] == inventory["directories"] + inventory["regular_files"],
        "observation inventory member arithmetic drifted",
    )
    checker.require(
        inventory["regular_file_bytes"] >= inventory["max_file_bytes"],
        "observation inventory byte maxima are contradictory",
    )
    checker.require(
        inventory["regular_file_bytes"]
        <= archive["extraction_decompressed_stream_bytes"],
        "observation regular-file bytes exceed the decompressed stream",
    )
    ceiling_keys = {
        "members": "members_max",
        "directories": "directories_max",
        "regular_files": "regular_files_max",
        "regular_file_bytes": "regular_file_bytes_max",
        "max_file_bytes": "file_bytes_max",
        "max_path_bytes": "path_bytes_max",
        "max_depth": "path_depth_max",
    }
    for observed_key, limit_key in ceiling_keys.items():
        checker.require(
            inventory[observed_key] <= LEGACY_V4_CONSTANTS["limits"][limit_key],
            f"observation inventory {observed_key} exceeds its resource ceiling",
        )

    tree_manifest = raw.get("canonical_tree_manifest")
    leaves = raw.get("executable_leaves")
    probes = raw.get("live_probes")
    checker.require_exact_typed_value(
        tree_manifest, candidate["tree_manifest"], "candidate tree-manifest copy"
    )
    checker.require_exact_typed_value(
        leaves, candidate["leaves"], "candidate executable-leaf copy"
    )
    checker.require_exact_typed_value(
        probes, candidate["probes"], "candidate live-probe copy"
    )
    tree_manifest = checker.exact_keys(
        tree_manifest,
        {"algorithm", "format", "pre_post_equal", "sha256"},
        "observation tree manifest",
    )
    checker.require(
        tree_manifest["algorithm"] == "sha256"
        and tree_manifest["format"] == checker.MANIFEST_FORMAT,
        "observation tree-manifest contract drifted",
    )
    checker.exact_hex(tree_manifest["sha256"], 64, "observation tree-manifest SHA-256")
    checker.require_exact_typed_value(
        tree_manifest["pre_post_equal"], True, "tree pre/post equality"
    )
    leaves = checker.exact_keys(
        leaves, {"lake", "lean", "leanchecker"}, "observation executable leaves"
    )
    leaf_total = 0
    archive_root = preflight["single_expected_root"]
    checker.require(isinstance(archive_root, str), "archive root type drifted")
    for role, leaf_value in leaves.items():
        leaf = checker.validate_leaf_shape(
            leaf_value, f"observation {role} executable leaf"
        )
        checker.require_exact_typed_value(
            leaf["path"], f"bin/{role}", f"observation {role} leaf path"
        )
        checker.require(
            leaf["size"] <= inventory["max_file_bytes"],
            f"observation {role} leaf exceeds the maximum file size",
        )
        full_path = f"{archive_root}/{leaf['path']}"
        checker.require(
            len(full_path.encode("utf-8")) <= inventory["max_path_bytes"]
            and len(full_path.split("/")) <= inventory["max_depth"],
            f"observation {role} leaf exceeds path inventory bounds",
        )
        leaf_total += leaf["size"]
    checker.require(
        inventory["regular_files"] >= len(leaves)
        and leaf_total <= inventory["regular_file_bytes"],
        "observation executable leaves contradict the archive inventory",
    )
    probes = checker.exact_keys(
        probes,
        {
            "build",
            "commit",
            "lake_stdout",
            "lean_platform",
            "lean_stdout",
            "leanchecker_absent_module_exit",
            "leanchecker_absent_module_stderr",
            "version",
        },
        "observation live probes",
    )
    lean_stdout = probes["lean_stdout"]
    lake_stdout = probes["lake_stdout"]
    absent_stderr = probes["leanchecker_absent_module_stderr"]
    checker.require(
        isinstance(lean_stdout, str)
        and isinstance(lake_stdout, str)
        and isinstance(absent_stderr, str),
        "observation live-probe stream types drifted",
    )
    lean_identity = checker.parse_lean_version(
        checker.ProcessResult(0, lean_stdout.encode("utf-8"), b"")
    )
    for key in ("version", "commit", "build"):
        checker.require_exact_typed_value(
            probes[key], getattr(lean_identity, key), f"Lean {key} consistency"
        )
    checker.require_exact_typed_value(
        probes["lean_platform"], lean_identity.platform, "Lean platform consistency"
    )
    checker.require_exact_typed_value(
        lean_identity.platform,
        "arm64-apple-darwin24.6.0",
        "Darwin arm64 Lean platform",
    )
    checker.validate_lake_version(
        checker.ProcessResult(0, lake_stdout.encode("utf-8"), b"")
    )
    checker.require_exact_typed_value(
        probes["leanchecker_absent_module_exit"],
        1,
        "LeanChecker absent-module exit type/value",
    )
    checker.validate_leanchecker_probe(
        checker.ProcessResult(
            probes["leanchecker_absent_module_exit"],
            b"",
            absent_stderr.encode("utf-8"),
        )
    )

    nested_result = checker.exact_keys(
        raw.get("nested_kernel_regression"),
        {"reason", "same_extraction_transaction", "status"},
        "nested observation",
    )
    checker.require_exact_typed_value(
        nested_result["status"],
        "not_run_unqualified_asset",
        "nested observation status",
    )
    checker.require_exact_typed_value(
        nested_result["same_extraction_transaction"],
        False,
        "nested same-extraction status",
    )
    checker.require_exact_typed_value(
        nested_result["reason"],
        "hosted-pending derived executable pins cannot qualify the direct regression "
        "route in the observation run",
        "nested observation reason",
    )
    checker.require_exact_typed_value(
        candidate["promotion_status"],
        "not_qualified_same_run",
        "candidate promotion status",
    )
    checker.require_exact_typed_value(
        candidate["required_next_step"],
        LEGACY_V4_CONSTANTS["required_next_step"],
        "candidate required next step",
    )
    decisive_nested = decisive["nested_kernel_regression"]
    checker.require(
        isinstance(decisive_nested, dict), "decisive nested projection drifted"
    )
    checker.require_exact_typed_value(
        decisive_nested["status"],
        nested_result["status"],
        "decisive nested status",
    )
    checker.require_exact_typed_value(
        decisive_nested["same_extraction_transaction"],
        nested_result["same_extraction_transaction"],
        "decisive nested transaction status",
    )
    checker.require_exact_typed_value(
        decisive["candidate_promotion_status"],
        candidate["promotion_status"],
        "decisive candidate promotion status",
    )
    host = checker.exact_keys(
        raw.get("host"), {"machine", "system"}, "observation host"
    )
    checker.require(
        host["system"] == darwin_asset["host"]["system"]
        and host["machine"] in darwin_asset["host"]["machines"],
        "observation host is inconsistent with Darwin arm64 metadata",
    )
    checker.require_exact_typed_value(
        raw.get("authentication_boundary"),
        LEGACY_V4_CONSTANTS["authentication_boundary"],
        "observation authentication boundary",
    )
    execution_route = checker.exact_keys(
        raw.get("execution_route"),
        {
            "absolute_extracted_leaf_launch",
            "ambient_umask_independent_private_mode_enforcement",
            "child_path_selects_exact_leaves_pre_and_post",
            "descendant_group_or_session_changes_continuously_observed",
            "elan_invoked",
            "environment_keys",
            "isolated_process_group_absence_checked",
            "isolated_process_group_cleanup_after_every_child_outcome",
            "isolated_process_group_cleanup_signal_policy",
            "lean_sysroot_present",
            "non_child_descendants_reaped_by_this_checker",
            "private_directory_modes_after_creation",
            "process_group_cleanup_bounds_milliseconds",
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log",
            "process_group_observation_atomic",
            "process_group_reuse_excluded",
            "zstd_canonical_path",
            "zstd_launch_path",
            "zstd_sha256",
        },
        "observation execution route",
    )
    for key in (
        "absolute_extracted_leaf_launch",
        "ambient_umask_independent_private_mode_enforcement",
        "child_path_selects_exact_leaves_pre_and_post",
        "isolated_process_group_absence_checked",
        "isolated_process_group_cleanup_after_every_child_outcome",
    ):
        checker.require_exact_typed_value(
            execution_route[key], True, f"execution-route field {key}"
        )
    for key in (
        "descendant_group_or_session_changes_continuously_observed",
        "non_child_descendants_reaped_by_this_checker",
        "process_group_observation_atomic",
        "process_group_reuse_excluded",
    ):
        checker.require_exact_typed_value(
            execution_route[key], False, f"execution-route limitation {key}"
        )
    checker.require_exact_typed_value(
        execution_route["elan_invoked"], False, "execution-route Elan boundary"
    )
    checker.require_exact_typed_value(
        execution_route["lean_sysroot_present"],
        False,
        "execution-route sysroot boundary",
    )
    checker.require_exact_typed_value(
        execution_route[
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log"
        ],
        True,
        "execution-route signal-log boundary",
    )
    checker.require_exact_typed_value(
        execution_route["environment_keys"],
        ["HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"],
        "execution-route environment keys",
    )
    checker.require_exact_typed_value(
        execution_route["isolated_process_group_cleanup_signal_policy"],
        ["TERM", "KILL"],
        "execution-route signal policy",
    )
    checker.require_exact_typed_value(
        execution_route["private_directory_modes_after_creation"],
        {
            "archive_directories_before_final_archive_mode": "0700",
            "child_home": "0700",
            "child_tmp": "0700",
            "extraction_destination": "0700",
            "temporary_root": "0700",
        },
        "execution-route private directory modes",
    )
    checker.require_exact_typed_value(
        execution_route["process_group_cleanup_bounds_milliseconds"],
        {
            "absence_poll_interval": LEGACY_V4_CONSTANTS["limits"][
                "process_group_poll_interval_milliseconds"
            ],
            "direct_child_reap_timeout": LEGACY_V4_CONSTANTS["limits"][
                "direct_child_reap_timeout_milliseconds"
            ],
            "kill_grace": LEGACY_V4_CONSTANTS["limits"][
                "process_group_kill_grace_milliseconds"
            ],
            "term_grace": LEGACY_V4_CONSTANTS["limits"][
                "process_group_term_grace_milliseconds"
            ],
        },
        "execution-route process-group bounds",
    )
    checker.exact_hex(
        execution_route["zstd_sha256"], 64, "execution-route zstd SHA-256"
    )
    checker.require_exact_typed_value(
        execution_route["zstd_launch_path"],
        "/opt/homebrew/bin/zstd",
        "execution-route zstd launch path",
    )
    checker.require_exact_typed_value(
        execution_route["zstd_canonical_path"],
        "/opt/homebrew/Cellar/zstd/1.5.7_1/bin/zstd",
        "execution-route zstd canonical path",
    )
    checker.require_exact_typed_value(
        execution_route["zstd_sha256"],
        "aff8169fb421bb925fb16c44a7e0143fa2c7a941dc45cce76b15062a2ce54917",
        "execution-route zstd digest",
    )
    parsed_authority = checker.parse_legacy_v4_authority(
        raw_source,
        checker.canonical_json_bytes(receipt) + b"\n",
        enforce_published_seals=False,
    )
    checker.require_exact_typed_value(
        parsed_authority.inventory,
        inventory,
        "legacy parser inventory authority",
    )
    return raw


def mutated_observation(
    path: tuple[object, ...], replacement: object
) -> tuple[bytes, dict[str, object]]:
    return mutated_observation_paths(((path, replacement),))


def mutated_observation_paths(
    changes: tuple[tuple[tuple[object, ...], object], ...],
) -> tuple[bytes, dict[str, object]]:
    candidate = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "Darwin observation mutation baseline"
    )
    for path, replacement in changes:
        set_object_path(candidate, path, replacement)
    raw_source = checker.canonical_json_bytes(candidate) + b"\n"
    return raw_source, receipt_for_observation_bytes(raw_source)


def observation_custody_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    require(
        OBSERVATION_RECEIPT_SOURCE
        == checker.canonical_json_bytes(OBSERVATION_RECEIPT) + b"\n",
        "Darwin observation receipt is not canonical one-line JSON",
    )
    validate_observation_custody(OBSERVATION_RAW_SOURCE, OBSERVATION_RECEIPT)
    positives = [
        {
            "name": "darwin_observation_custody_exact_baseline",
            "accepted": True,
            "qualification_credit": "none",
        }
    ]
    cases: list[tuple[str, tuple[object, ...], object, str]] = [
        ("observation_status", ("status",), "passed", "observation status"),
        (
            "observation_platform",
            ("platform_key",),
            "linux-x86_64",
            "observation platform",
        ),
        (
            "observation_prior_qualification",
            ("qualification_state_before_run",),
            "qualified",
            "prior qualification state",
        ),
        (
            "observation_source_checker_bytes",
            ("source_binding", "checker_bytes"),
            141465,
            "source checker bytes",
        ),
        (
            "observation_source_checker_digest",
            ("source_binding", "checker_sha256"),
            "0" * 64,
            "source checker digest",
        ),
        (
            "observation_source_metadata_digest",
            ("source_binding", "metadata_sha256"),
            "0" * 64,
            "source metadata digest",
        ),
        (
            "observation_source_metadata_projection",
            ("source_binding", "metadata_policy_projection_sha256"),
            "0" * 64,
            "source metadata projection digest",
        ),
        (
            "observation_source_nested_digest",
            ("source_binding", "nested_checker_binding", "sha256"),
            "0" * 64,
            "nested checker digest",
        ),
        (
            "observation_release_identity",
            ("release_identity", "release", "tag_commit"),
            "0" * 40,
            "release identity",
        ),
        (
            "observation_archive_after_digest",
            ("archive", "sha256_after"),
            "0" * 64,
            "archive digest after",
        ),
        (
            "observation_archive_stream_length",
            ("archive", "extraction_decompressed_stream_bytes"),
            2802083841,
            "stream lengths differ",
        ),
        (
            "observation_candidate_inventory_copy",
            ("candidate_receipt", "inventory", "members"),
            15279,
            "candidate inventory copy",
        ),
        (
            "observation_candidate_tree_copy",
            ("candidate_receipt", "tree_manifest", "sha256"),
            "0" * 64,
            "candidate tree-manifest copy",
        ),
        (
            "observation_candidate_leaf_copy",
            ("candidate_receipt", "leaves", "lean", "sha256"),
            "0" * 64,
            "candidate executable-leaf copy",
        ),
        (
            "observation_candidate_probe_copy",
            ("candidate_receipt", "probes", "version"),
            "4.32.1",
            "candidate live-probe copy",
        ),
        (
            "observation_nested_status",
            ("nested_kernel_regression", "status"),
            "passed",
            "nested observation status",
        ),
        (
            "observation_nested_same_transaction",
            ("nested_kernel_regression", "same_extraction_transaction"),
            True,
            "nested same-extraction status",
        ),
        (
            "observation_promotion_status",
            ("candidate_receipt", "promotion_status"),
            "qualified_same_run",
            "candidate promotion status",
        ),
        (
            "observation_host_machine",
            ("host", "machine"),
            "x86_64",
            "observation host is inconsistent",
        ),
        (
            "observation_authentication_status",
            ("authentication_boundary", "status"),
            "authenticated",
            "authentication boundary",
        ),
        (
            "observation_process_cleanup_claim",
            (
                "execution_route",
                "isolated_process_group_cleanup_after_every_child_outcome",
            ),
            False,
            "execution-route field",
        ),
        (
            "observation_atomicity_overclaim",
            ("execution_route", "process_group_observation_atomic"),
            True,
            "execution-route limitation",
        ),
    ]
    negatives = [
        expect_failure(
            name,
            lambda path=path, replacement=replacement: validate_observation_custody(
                *mutated_observation(path, replacement)
            ),
            expected,
        )
        for name, path, replacement, expected in cases
    ]

    probe_cases = (
        (
            "observation_lean_stdout",
            "lean_stdout",
            "nonsense\n",
            "Lean version probe rejected",
        ),
        (
            "observation_lake_stdout",
            "lake_stdout",
            "nonsense\n",
            "Lake version probe rejected",
        ),
        (
            "observation_absent_exit",
            "leanchecker_absent_module_exit",
            0,
            "absent-module exit type/value",
        ),
        (
            "observation_absent_diagnostic",
            "leanchecker_absent_module_stderr",
            "",
            "LeanChecker absent-module probe rejected",
        ),
    )
    for name, key, replacement, expected in probe_cases:
        probe_candidate = checker.parse_json_object(
            OBSERVATION_RAW_SOURCE, f"Darwin observation {name} mutation"
        )
        set_object_path(probe_candidate, ("live_probes", key), replacement)
        set_object_path(
            probe_candidate, ("candidate_receipt", "probes", key), replacement
        )
        probe_source = checker.canonical_json_bytes(probe_candidate) + b"\n"
        negatives.append(
            expect_failure(
                name,
                lambda probe_source=probe_source: validate_observation_custody(
                    probe_source, receipt_for_observation_bytes(probe_source)
                ),
                expected,
            )
        )

    coordinated_cases = (
        (
            "observation_archive_stream_nonpositive",
            (
                (("archive", "preflight_decompressed_stream_bytes"), 0),
                (("archive", "extraction_decompressed_stream_bytes"), 0),
            ),
            "stream lengths differ or exceed",
        ),
        (
            "observation_archive_path",
            ((("archive", "path"), "/private/tmp/substituted.tar.zst"),),
            "archive capture path",
        ),
        (
            "observation_safe_preflight_flag",
            ((("safe_preflight", "normalized_unique_paths"), False),),
            "safe-preflight field normalized_unique_paths",
        ),
        (
            "observation_inventory_ceiling",
            (
                (("safe_preflight", "inventory", "regular_files"), 19_400),
                (("safe_preflight", "inventory", "members"), 20_007),
                (("candidate_receipt", "inventory", "regular_files"), 19_400),
                (("candidate_receipt", "inventory", "members"), 20_007),
            ),
            "inventory members exceeds its resource ceiling",
        ),
        (
            "observation_tree_algorithm",
            (
                (("canonical_tree_manifest", "algorithm"), "sha512"),
                (("candidate_receipt", "tree_manifest", "algorithm"), "sha512"),
            ),
            "tree-manifest contract drifted",
        ),
        (
            "observation_tree_pre_post_false",
            (
                (("canonical_tree_manifest", "pre_post_equal"), False),
                (("candidate_receipt", "tree_manifest", "pre_post_equal"), False),
            ),
            "tree pre/post equality",
        ),
        (
            "observation_leaf_mode",
            (
                (("executable_leaves", "lean", "mode"), "0644"),
                (("candidate_receipt", "leaves", "lean", "mode"), "0644"),
            ),
            "mode must be 0755",
        ),
        (
            "observation_leaf_role_path",
            (
                (("executable_leaves", "lean", "path"), "bin/lake"),
                (("candidate_receipt", "leaves", "lean", "path"), "bin/lake"),
            ),
            "observation lean leaf path",
        ),
        (
            "observation_leaf_digest",
            (
                (("executable_leaves", "lean", "sha256"), "0" * 63),
                (
                    ("candidate_receipt", "leaves", "lean", "sha256"),
                    "0" * 63,
                ),
            ),
            "SHA-256 is malformed",
        ),
        (
            "observation_leaf_inventory_size",
            (
                (("executable_leaves", "lean", "size"), 209_341_521),
                (
                    ("candidate_receipt", "leaves", "lean", "size"),
                    209_341_521,
                ),
            ),
            "leaf exceeds the maximum file size",
        ),
        (
            "observation_matched_wrong_lean_identity",
            (
                (("live_probes", "version"), "4.32.1"),
                (("candidate_receipt", "probes", "version"), "4.32.1"),
                (
                    ("live_probes", "lean_stdout"),
                    "Lean (version 4.32.1, arm64-apple-darwin24.6.0, commit "
                    "f3b06c705e6c85f5314019d5d3baab0fec5b580c, Release)\n",
                ),
                (
                    ("candidate_receipt", "probes", "lean_stdout"),
                    "Lean (version 4.32.1, arm64-apple-darwin24.6.0, commit "
                    "f3b06c705e6c85f5314019d5d3baab0fec5b580c, Release)\n",
                ),
            ),
            "Lean version probe rejected",
        ),
        (
            "observation_authentication_statement",
            ((("authentication_boundary", "statements", 0), "x"),),
            "observation authentication boundary",
        ),
        (
            "observation_source_acyclic_policy",
            ((("source_binding", "acyclic_policy"), "x"),),
            "source acyclic policy",
        ),
        (
            "observation_environment_keys",
            ((("execution_route", "environment_keys"), ["HOME"]),),
            "execution-route environment keys",
        ),
        (
            "observation_candidate_required_next_step",
            ((("candidate_receipt", "required_next_step"), ""),),
            "candidate required next step",
        ),
        (
            "observation_nested_reason",
            ((("nested_kernel_regression", "reason"), ""),),
            "nested observation reason",
        ),
        (
            "observation_absent_exit_boolean",
            (
                (("live_probes", "leanchecker_absent_module_exit"), True),
                (
                    (
                        "candidate_receipt",
                        "probes",
                        "leanchecker_absent_module_exit",
                    ),
                    True,
                ),
            ),
            "absent-module exit type/value",
        ),
        (
            "observation_regular_bytes_above_stream",
            (
                (("safe_preflight", "inventory", "regular_file_bytes"), 2_802_083_841),
                (
                    ("candidate_receipt", "inventory", "regular_file_bytes"),
                    2_802_083_841,
                ),
            ),
            "regular-file bytes exceed the decompressed stream",
        ),
        (
            "observation_zstd_launch_path",
            ((("execution_route", "zstd_launch_path"), False),),
            "zstd launch path",
        ),
        (
            "observation_nested_source_path",
            ((("source_binding", "nested_checker_binding", "path"), "other.py"),),
            "nested checker observation path",
        ),
        (
            "observation_historical_source_path",
            (
                (
                    (
                        "source_binding",
                        "historical_nontransferable_receipt_binding",
                        "path",
                    ),
                    "other.json",
                ),
            ),
            "historical receipt observation path",
        ),
    )
    for name, changes, expected in coordinated_cases:
        negatives.append(
            expect_failure(
                name,
                lambda changes=changes: validate_observation_custody(
                    *mutated_observation_paths(changes)
                ),
                expected,
            )
        )

    extra_root = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "Darwin observation extra-root mutation"
    )
    extra_root["unexpected"] = None
    extra_root_source = checker.canonical_json_bytes(extra_root) + b"\n"
    negatives.append(
        expect_failure(
            "observation_extra_root_key",
            lambda: validate_observation_custody(
                extra_root_source, receipt_for_observation_bytes(extra_root_source)
            ),
            "Darwin observation root keys drifted",
        )
    )

    arithmetic = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "Darwin observation arithmetic mutation"
    )
    set_object_path(arithmetic, ("safe_preflight", "inventory", "members"), 15279)
    set_object_path(arithmetic, ("candidate_receipt", "inventory", "members"), 15279)
    arithmetic_source = checker.canonical_json_bytes(arithmetic) + b"\n"
    negatives.append(
        expect_failure(
            "observation_inventory_arithmetic",
            lambda: validate_observation_custody(
                arithmetic_source, receipt_for_observation_bytes(arithmetic_source)
            ),
            "member arithmetic",
        )
    )
    maxima = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "Darwin observation maxima mutation"
    )
    for root in ("safe_preflight", "candidate_receipt"):
        set_object_path(maxima, (root, "inventory", "regular_file_bytes"), 1)
    maxima_source = checker.canonical_json_bytes(maxima) + b"\n"
    negatives.append(
        expect_failure(
            "observation_inventory_maximum",
            lambda: validate_observation_custody(
                maxima_source, receipt_for_observation_bytes(maxima_source)
            ),
            "byte maxima are contradictory",
        )
    )
    noncanonical_source = (
        json.dumps(
            checker.parse_json_object(
                OBSERVATION_RAW_SOURCE, "Darwin observation noncanonical mutation"
            ),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
    )
    negatives.append(
        expect_failure(
            "observation_noncanonical_raw_json",
            lambda: validate_observation_custody(
                noncanonical_source, receipt_for_observation_bytes(noncanonical_source)
            ),
            "not canonical one-line JSON",
        )
    )
    malformed_source = OBSERVATION_RAW_SOURCE.replace(
        b'"status":"observation_only_unqualified"',
        b'"status":"observation_only_unqualified","status":"passed"',
        1,
    )
    negatives.append(
        expect_failure(
            "observation_duplicate_raw_key",
            lambda: validate_observation_custody(
                malformed_source, receipt_for_observation_bytes(malformed_source)
            ),
            "duplicate JSON object key",
        )
    )

    receipt_cases: list[tuple[str, tuple[object, ...], object]] = [
        (
            "observation_receipt_promotion_disposition",
            ("scope", "promotion_disposition"),
            "go",
        ),
        (
            "observation_receipt_blocker_removed",
            ("promotion_review", "remaining_blockers"),
            OBSERVATION_RECEIPT["promotion_review"]["remaining_blockers"][:-1],
        ),
        (
            "observation_receipt_future_commit",
            ("acyclic_boundary", "containing_commit"),
            "0" * 40,
        ),
        (
            "observation_receipt_self_hash",
            ("acyclic_boundary", "receipt_self_sha256"),
            "0" * 64,
        ),
        (
            "observation_receipt_authentication_overclaim",
            ("nonclaims", "publisher_or_provider_authentication"),
            "authenticated",
        ),
        (
            "observation_receipt_readme_digest",
            (
                "capture",
                "external_owner_mutable_custody",
                "readme",
                "sha256",
            ),
            "0" * 64,
        ),
        (
            "observation_receipt_stderr_digest",
            (
                "capture",
                "external_owner_mutable_custody",
                "stderr",
                "sha256",
            ),
            "0" * 64,
        ),
    ]
    for name, path, replacement in receipt_cases:
        receipt = copy.deepcopy(OBSERVATION_RECEIPT)
        set_object_path(receipt, path, replacement)
        negatives.append(
            expect_failure(
                name,
                lambda receipt=receipt: validate_observation_custody(
                    OBSERVATION_RAW_SOURCE, receipt
                ),
                "receipt policy projection",
            )
        )
    return negatives, positives


def legacy_v4_independence_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    forbidden = {"METADATA", "ASSETS", "LIMITS"}
    code_names = set(validate_observation_custody.__code__.co_names)
    require(
        code_names.isdisjoint(forbidden),
        f"legacy-v4 validator code names depend on mutable metadata: {sorted(code_names & forbidden)}",
    )
    source_tree = ast.parse(SELF_PATH.read_bytes(), filename=os.fspath(SELF_PATH))
    validator_nodes = [
        node
        for node in source_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "validate_observation_custody"
    ]
    require(len(validator_nodes) == 1, "legacy-v4 validator AST anchor drifted")
    ast_names = {
        node.id for node in ast.walk(validator_nodes[0]) if isinstance(node, ast.Name)
    }
    require(
        ast_names.isdisjoint(forbidden),
        f"legacy-v4 validator AST depends on mutable metadata: {sorted(ast_names & forbidden)}",
    )
    production_code_names = set(checker.parse_legacy_v4_authority.__code__.co_names)
    require(
        production_code_names.isdisjoint(forbidden),
        "production legacy-v4 authority parser code names depend on mutable "
        f"metadata: {sorted(production_code_names & forbidden)}",
    )
    checker_tree = ast.parse(CHECKER_SOURCE, filename=os.fspath(CHECKER_PATH))
    production_nodes = [
        node
        for node in checker_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "parse_legacy_v4_authority"
    ]
    require(
        len(production_nodes) == 1,
        "production legacy-v4 authority parser AST anchor drifted",
    )
    production_ast_names = {
        node.id for node in ast.walk(production_nodes[0]) if isinstance(node, ast.Name)
    }
    require(
        production_ast_names.isdisjoint(forbidden),
        "production legacy-v4 authority parser AST depends on mutable metadata: "
        f"{sorted(production_ast_names & forbidden)}",
    )
    saved = {name: globals()[name] for name in forbidden}
    checker_saved = {
        name: checker.__dict__.get(name, _MISSING_CHECKER_GLOBAL) for name in forbidden
    }
    try:
        globals()["METADATA"] = object()
        globals()["ASSETS"] = object()
        globals()["LIMITS"] = object()
        for name in forbidden:
            checker.__dict__[name] = object()
        validated = validate_observation_custody(
            OBSERVATION_RAW_SOURCE, copy.deepcopy(OBSERVATION_RECEIPT)
        )
        parsed = checker.parse_legacy_v4_authority(
            OBSERVATION_RAW_SOURCE,
            OBSERVATION_RECEIPT_SOURCE,
            enforce_published_seals=True,
        )
    finally:
        globals().update(saved)
        for name, value in checker_saved.items():
            if value is _MISSING_CHECKER_GLOBAL:
                checker.__dict__.pop(name, None)
            else:
                checker.__dict__[name] = value
    require(
        validated["schema"] == checker.LEGACY_RESULT_SCHEMA,
        "legacy-v4 poison-independence baseline drifted",
    )
    require(
        parsed == LEGACY_V4_AUTHORITY,
        "production legacy-v4 poison-independence authority drifted",
    )
    positives = [
        {
            "name": "legacy_v4_validator_ast_and_co_names_independent_of_mutable_metadata",
            "accepted": True,
        },
        {
            "name": "legacy_v4_production_parser_ast_and_co_names_independent_of_mutable_metadata",
            "accepted": True,
        },
        {
            "name": "legacy_v4_validator_poisoned_current_metadata_independence",
            "accepted": True,
        },
        {
            "name": "legacy_v4_production_parser_poisoned_current_metadata_independence",
            "accepted": True,
        },
    ]

    matched_arithmetic = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "legacy matched arithmetic mutation"
    )
    matched_arithmetic["safe_preflight"]["inventory"]["members"] += 1
    matched_arithmetic["candidate_receipt"]["inventory"]["members"] += 1
    matched_arithmetic_source = checker.canonical_json_bytes(matched_arithmetic) + b"\n"
    matched_arithmetic_receipt = receipt_for_observation_bytes(
        matched_arithmetic_source
    )
    negatives = [
        expect_failure(
            "legacy_v4_matched_wrong_members_arithmetic",
            lambda: validate_observation_custody(
                matched_arithmetic_source, matched_arithmetic_receipt
            ),
            "member arithmetic",
        )
    ]

    matched_leaf = checker.parse_json_object(
        OBSERVATION_RAW_SOURCE, "legacy matched leaf mutation"
    )
    replacement_sha = "0" * 64
    matched_leaf["executable_leaves"]["lean"]["sha256"] = replacement_sha
    matched_leaf["candidate_receipt"]["leaves"]["lean"]["sha256"] = replacement_sha
    matched_leaf_source = checker.canonical_json_bytes(matched_leaf) + b"\n"
    matched_leaf_receipt = receipt_for_observation_bytes(matched_leaf_source)
    negatives.append(
        expect_failure(
            "legacy_v4_matched_wrong_leaf_rejected_by_published_seal",
            lambda: checker.parse_legacy_v4_authority(
                matched_leaf_source,
                checker.canonical_json_bytes(matched_leaf_receipt) + b"\n",
                enforce_published_seals=True,
            ),
            "published legacy-v4 raw evidence identity drifted",
        )
    )
    return negatives, positives


def promoted_metadata_from_observation() -> dict[str, object]:
    candidate = copy.deepcopy(METADATA)
    checker.validate_metadata(candidate, LEGACY_V4_AUTHORITY)
    return candidate


def closed_promotion_contradiction_controls() -> list[dict[str, object]]:
    baseline = promoted_metadata_from_observation()
    checker.validate_metadata(baseline, LEGACY_V4_AUTHORITY)
    controls: list[dict[str, object]] = []

    def reject(name: str, candidate: dict[str, object], expected: str) -> None:
        controls.append(
            expect_failure(
                name,
                lambda candidate=candidate: checker.validate_metadata(
                    candidate, LEGACY_V4_AUTHORITY
                ),
                expected,
            )
        )

    cases: list[tuple[str, tuple[object, ...], object, str]] = [
        (
            "qualified_members_arithmetic_unconstrained",
            ("assets", 0, "custody_lifecycle", "inventory", "members"),
            15_279,
            "member arithmetic",
        ),
        (
            "qualified_zero_inventory_unconstrained",
            ("assets", 0, "custody_lifecycle", "inventory", "members"),
            0,
            "positive integers",
        ),
        (
            "qualified_inventory_ceilings_unconstrained",
            ("assets", 0, "custody_lifecycle", "inventory", "max_path_bytes"),
            LIMITS["path_bytes_max"] + 1,
            "exceeds its resource ceiling",
        ),
        (
            "qualified_regular_file_bytes_below_max_file_unconstrained",
            (
                "assets",
                0,
                "custody_lifecycle",
                "inventory",
                "regular_file_bytes",
            ),
            1,
            "byte relations",
        ),
        (
            "qualified_leaf_above_max_file_unconstrained",
            ("assets", 0, "custody_lifecycle", "leaves", "lean", "size"),
            209_341_521,
            "exceeds max_file_bytes",
        ),
        (
            "qualified_lean_platform_empty_unconstrained",
            ("assets", 0, "custody_lifecycle", "probes", "lean_platform"),
            "",
            "Lean stdout/scalar/platform coupling drifted",
        ),
        (
            "qualified_lean_stdout_consistency_unconstrained",
            ("assets", 0, "custody_lifecycle", "probes", "lean_stdout"),
            "nonsense",
            "Lean version probe rejected",
        ),
        (
            "qualified_lake_stdout_consistency_unconstrained",
            ("assets", 0, "custody_lifecycle", "probes", "lake_stdout"),
            "nonsense",
            "Lake version probe rejected",
        ),
        (
            "qualified_absent_module_exit_unconstrained",
            (
                "assets",
                0,
                "custody_lifecycle",
                "probes",
                "leanchecker_absent_module_exit",
            ),
            0,
            "integer 1",
        ),
        (
            "qualified_absent_module_diagnostic_empty_unconstrained",
            (
                "assets",
                0,
                "custody_lifecycle",
                "probes",
                "leanchecker_absent_module_stderr",
            ),
            "",
            "LeanChecker absent-module probe rejected",
        ),
        (
            "ready_state_stale_candidate_route_unconstrained",
            ("assets", 0, "custody_lifecycle", "required_next_step"),
            "observation_then_separate_reviewed_pin_promotion_then_fresh_strict_replay",
            "strict-replay lifecycle",
        ),
        (
            "provider_timestamp_grammar_weak",
            ("assets", 0, "github_asset", "created_at"),
            "Z",
            "provider timestamps drifted",
        ),
        (
            "authentication_statement_semantics_weak",
            ("authentication_boundary", "statements", 0),
            "x",
            "exact semantics drifted",
        ),
        (
            "historical_nontransferability_reason_weak",
            ("historical_nontransferable_observations", 0, "reason_nontransferable"),
            "cannot transfer",
            "nontransferability reason drifted",
        ),
        (
            "checker_policy_prose_weak",
            ("checker_binding", "policy"),
            "Acyclic seal: cannot authenticate itself",
            "source-binding boundary drifted",
        ),
    ]
    for name, path, replacement, expected in cases:
        candidate = copy.deepcopy(baseline)
        set_object_path(candidate, path, replacement)
        reject(name, candidate, expected)

    leaf_sum = copy.deepcopy(baseline)
    set_object_path(
        leaf_sum,
        ("assets", 0, "custody_lifecycle", "inventory", "max_file_bytes"),
        100,
    )
    set_object_path(
        leaf_sum,
        ("assets", 0, "custody_lifecycle", "inventory", "regular_file_bytes"),
        200,
    )
    for role in ("lean", "lake", "leanchecker"):
        set_object_path(
            leaf_sum,
            ("assets", 0, "custody_lifecycle", "leaves", role, "size"),
            80,
        )
    reject(
        "qualified_leaf_sum_above_regular_bytes_unconstrained",
        leaf_sum,
        "executable leaves contradict inventory",
    )

    pending_empty = copy.deepcopy(baseline)
    set_object_path(
        pending_empty,
        ("assets", 1, "custody_lifecycle", "pending_reason"),
        "",
    )
    reject(
        "pending_reason_type_and_content_weak_empty",
        pending_empty,
        "pending lifecycle route drifted",
    )
    pending_boolean = copy.deepcopy(baseline)
    set_object_path(
        pending_boolean,
        ("assets", 1, "custody_lifecycle", "pending_reason"),
        False,
    )
    reject(
        "pending_reason_type_and_content_weak",
        pending_boolean,
        "pending lifecycle route drifted",
    )

    review = OBSERVATION_RECEIPT["promotion_review"]
    require(isinstance(review, dict), "promotion review receipt drifted")
    accepted = review["accepted_contradictory_mutations"]
    require(isinstance(accepted, list), "accepted-mutation receipt drifted")
    accepted_names: list[str] = []
    for item in accepted:
        require(isinstance(item, dict), "accepted-mutation item drifted")
        name = item["id"]
        require(isinstance(name, str), "accepted-mutation identifier drifted")
        accepted_names.append(name)
    contradiction_names = {
        str(item["name"])
        for item in controls
        if str(item["name"]) != "pending_reason_type_and_content_weak_empty"
    }
    require(
        len(contradiction_names) == 17 and contradiction_names == set(accepted_names),
        "closed promotion contradictions differ from the typed receipt inventory",
    )
    return controls


def _scalar_object_paths(
    value: object, prefix: tuple[object, ...]
) -> list[tuple[object, ...]]:
    if isinstance(value, dict):
        paths: list[tuple[object, ...]] = []
        for key in sorted(value):
            paths.extend(_scalar_object_paths(value[key], (*prefix, key)))
        return paths
    require(
        not isinstance(value, list),
        f"single-field registry encountered an unexpanded list at {prefix!r}",
    )
    return [prefix]


def _wrong_scalar(value: object) -> object:
    if value is None:
        return "unexpected_non_null"
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if isinstance(value, str):
        return value + "-mutated"
    raise SelfTestError(f"unsupported scalar mutation type: {type(value).__name__}")


def promoted_single_field_controls() -> list[dict[str, object]]:
    darwin_base = ("assets", 0, "custody_lifecycle")
    linux_base = ("assets", 1, "custody_lifecycle")
    darwin_lifecycle = METADATA["assets"][0]["custody_lifecycle"]
    linux_lifecycle = METADATA["assets"][1]["custody_lifecycle"]
    require(
        isinstance(darwin_lifecycle, dict) and isinstance(linux_lifecycle, dict),
        "single-field lifecycle baseline drifted",
    )
    categories: dict[str, list[tuple[object, ...]]] = {
        "inventory": [
            (*darwin_base, "inventory", key)
            for key in sorted(darwin_lifecycle["inventory"])
        ],
        "leaves": [
            (*darwin_base, "leaves", role, key)
            for role in ("lake", "lean", "leanchecker")
            for key in ("mode", "path", "sha256", "size")
        ],
        "tree": [
            (*darwin_base, "tree_manifest", key)
            for key in ("algorithm", "format", "sha256")
        ],
        "probes": [
            (*darwin_base, "probes", key) for key in sorted(darwin_lifecycle["probes"])
        ],
        "reviewed_source": _scalar_object_paths(
            darwin_lifecycle["reviewed_pin_source"],
            (*darwin_base, "reviewed_pin_source"),
        ),
        "credit_boundary": [
            ("credit_boundary", key) for key in sorted(METADATA["credit_boundary"])
        ],
        "provider_timestamps": [
            ("assets", 0, "github_asset", "created_at"),
            ("assets", 0, "github_asset", "updated_at"),
            ("assets", 1, "github_asset", "created_at"),
            ("assets", 1, "github_asset", "updated_at"),
            ("subject", "release", "created_at"),
            ("subject", "release", "published_at"),
        ],
        "authentication_boundary": [
            ("authentication_boundary", "status"),
            *[("authentication_boundary", "statements", index) for index in range(5)],
        ],
        "darwin_lifecycle": [
            (*darwin_base, key)
            for key in (
                "archive_custody_credit",
                "pending_reason",
                "permitted_route",
                "required_next_step",
                "state",
                "static_qualification_credit",
                "static_schema_credit",
            )
        ],
        "linux_lifecycle_and_nullness": [
            (*linux_base, key)
            for key in (
                "archive_custody_credit",
                "inventory",
                "leaves",
                "pending_reason",
                "permitted_route",
                "probes",
                "required_next_step",
                "reviewed_pin_source",
                "state",
                "static_qualification_credit",
                "static_schema_credit",
                "tree_manifest",
            )
        ],
    }
    require(len(categories["inventory"]) == 7, "inventory registry arity drifted")
    require(len(categories["leaves"]) == 12, "leaf registry arity drifted")
    require(len(categories["tree"]) == 3, "tree registry arity drifted")
    require(len(categories["probes"]) == 8, "probe registry arity drifted")
    require(
        len(categories["reviewed_source"]) == 35,
        "reviewed-source registry arity drifted",
    )
    require(
        len(categories["credit_boundary"]) == 16,
        "credit-boundary registry arity drifted",
    )
    require(
        len(categories["provider_timestamps"]) == 6,
        "provider-timestamp registry arity drifted",
    )
    require(
        len(categories["authentication_boundary"]) == 6,
        "authentication-boundary registry arity drifted",
    )
    controls: list[dict[str, object]] = []
    observed_paths: set[tuple[object, ...]] = set()
    for category, paths in categories.items():
        for path in paths:
            require(
                path not in observed_paths, f"duplicate single-field path: {path!r}"
            )
            observed_paths.add(path)
            candidate = copy.deepcopy(METADATA)
            cursor: object = candidate
            for component in path[:-1]:
                cursor = cursor[component]  # type: ignore[index]
            original = cursor[path[-1]]  # type: ignore[index]
            set_object_path(candidate, path, _wrong_scalar(original))
            path_name = "__".join(str(component) for component in path)
            controls.append(
                expect_any_failure(
                    f"promoted_single_field_{category}_{path_name}",
                    lambda candidate=candidate: checker.validate_metadata(
                        candidate, LEGACY_V4_AUTHORITY
                    ),
                )
            )
    return controls


def _authority_matching_candidate(
    candidate: dict[str, object], *, raw_sha256: str | None = None
) -> object:
    lifecycle = candidate["assets"][0]["custody_lifecycle"]
    return checker.LegacyV4Authority(
        inventory=copy.deepcopy(lifecycle["inventory"]),
        leaves=copy.deepcopy(lifecycle["leaves"]),
        probes=copy.deepcopy(lifecycle["probes"]),
        tree_manifest=copy.deepcopy(lifecycle["tree_manifest"]),
        decompressed_stream_bytes=LEGACY_V4_AUTHORITY.decompressed_stream_bytes,
        raw_sha256=(
            LEGACY_V4_AUTHORITY.raw_sha256 if raw_sha256 is None else raw_sha256
        ),
        receipt_sha256=LEGACY_V4_AUTHORITY.receipt_sha256,
    )


def promoted_matched_wrong_controls() -> list[dict[str, object]]:
    cases: list[tuple[str, dict[str, object], object, str]] = []

    arithmetic = copy.deepcopy(METADATA)
    arithmetic["assets"][0]["custody_lifecycle"]["inventory"]["members"] += 1
    cases.append(
        (
            "promoted_matched_wrong_inventory_arithmetic",
            arithmetic,
            _authority_matching_candidate(arithmetic),
            "member arithmetic",
        )
    )

    leaf_sum = copy.deepcopy(METADATA)
    inventory = leaf_sum["assets"][0]["custody_lifecycle"]["inventory"]
    inventory["max_file_bytes"] = 100
    inventory["regular_file_bytes"] = 200
    for role in ("lake", "lean", "leanchecker"):
        leaf_sum["assets"][0]["custody_lifecycle"]["leaves"][role]["size"] = 80
    cases.append(
        (
            "promoted_matched_wrong_leaf_sum_inventory",
            leaf_sum,
            _authority_matching_candidate(leaf_sum),
            "executable leaves contradict inventory",
        )
    )

    lean_identity = copy.deepcopy(METADATA)
    probes = lean_identity["assets"][0]["custody_lifecycle"]["probes"]
    probes["version"] = "4.32.3"
    probes["lean_stdout"] = probes["lean_stdout"].replace("4.32.2", "4.32.3", 1)
    cases.append(
        (
            "promoted_matched_wrong_lean_scalar_and_stdout",
            lean_identity,
            _authority_matching_candidate(lean_identity),
            "Lean version pin drifted",
        )
    )

    lake_identity = copy.deepcopy(METADATA)
    lake_probes = lake_identity["assets"][0]["custody_lifecycle"]["probes"]
    lake_probes["lake_stdout"] = (
        "Lake version 9.9.9-src+f3b06c7 (Lean version 4.32.2)\n"
    )
    cases.append(
        (
            "promoted_matched_wrong_arbitrary_lake_numeric_version",
            lake_identity,
            _authority_matching_candidate(lake_identity),
            "Lake version probe rejected",
        )
    )

    absent_exit = copy.deepcopy(METADATA)
    absent_exit["assets"][0]["custody_lifecycle"]["probes"][
        "leanchecker_absent_module_exit"
    ] = True
    cases.append(
        (
            "promoted_matched_wrong_boolean_absent_exit",
            absent_exit,
            _authority_matching_candidate(absent_exit),
            "integer 1",
        )
    )

    lifecycle = copy.deepcopy(METADATA)
    route = lifecycle["assets"][0]["custody_lifecycle"]
    route["state"] = "qualified"
    route["permitted_route"] = "observation_only"
    route["required_next_step"] = "same_run_promotion"
    route["pending_reason"] = "coordinated stale state"
    route["static_qualification_credit"] = "qualified"
    cases.append(
        (
            "promoted_matched_wrong_lifecycle_route_credit_and_nullness",
            lifecycle,
            _authority_matching_candidate(lifecycle),
            "static credit boundary drifted",
        )
    )

    historical_tree_execution_claim = copy.deepcopy(METADATA)
    historical_tree_execution_claim["assets"][0]["custody_lifecycle"]["tree_manifest"][
        "pre_post_equal"
    ] = True
    cases.append(
        (
            "promoted_static_tree_rejects_historical_pre_post_execution_claim",
            historical_tree_execution_claim,
            _authority_matching_candidate(historical_tree_execution_claim),
            "tree manifest keys drifted",
        )
    )

    tree = copy.deepcopy(METADATA)
    tree["assets"][0]["custody_lifecycle"]["tree_manifest"]["sha256"] = "0" * 64
    cases.append(
        (
            "promoted_matched_wrong_tree_all_copies",
            tree,
            _authority_matching_candidate(tree, raw_sha256="0" * 64),
            "source disagrees with frozen legacy authority",
        )
    )

    leaf = copy.deepcopy(METADATA)
    leaf["assets"][0]["custody_lifecycle"]["leaves"]["lean"]["sha256"] = "0" * 64
    cases.append(
        (
            "promoted_matched_wrong_leaf_all_copies",
            leaf,
            _authority_matching_candidate(leaf, raw_sha256="0" * 64),
            "source disagrees with frozen legacy authority",
        )
    )

    controls = [
        expect_failure(
            name,
            lambda candidate=candidate, authority=authority: checker.validate_metadata(
                candidate, authority
            ),
            expected,
        )
        for name, candidate, authority, expected in cases
    ]
    require(
        len({str(control["name"]) for control in controls}) == len(controls),
        "matched-wrong control names are not unique",
    )
    return controls


def metadata_controls() -> list[dict[str, object]]:
    (
        source_snapshot,
        metadata_snapshot,
        nested_checker_snapshot,
        historical_receipt_snapshot,
        legacy_raw_snapshot,
        legacy_receipt_snapshot,
        loaded,
        assets,
    ) = checker.load_policy()
    require(
        source_snapshot.sha256 == EXPECTED_CHECKER_SHA256,
        "live source-binding baseline drifted",
    )
    require(
        metadata_snapshot.sha256 == EXPECTED_METADATA_SHA256,
        "live metadata baseline drifted",
    )
    require(
        nested_checker_snapshot.sha256
        == METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
        "live nested-checker binding baseline drifted",
    )
    require(
        historical_receipt_snapshot.sha256
        == METADATA["historical_nontransferable_observations"][0]["source_receipt"][
            "sha256"
        ],
        "live historical-receipt binding baseline drifted",
    )
    require(
        legacy_raw_snapshot.sha256 == EXPECTED_OBSERVATION_RAW_SHA256
        and legacy_receipt_snapshot.sha256 == EXPECTED_OBSERVATION_RECEIPT_SHA256,
        "live legacy-v4 evidence binding baseline drifted",
    )
    require(
        loaded == METADATA and set(assets) == {"darwin-aarch64", "linux-x86_64"},
        "live metadata semantic baseline drifted",
    )
    controls: list[dict[str, object]] = []
    controls.append(
        expect_failure(
            "json_duplicate_root_key",
            lambda: checker.parse_json_object(b'{"a":1,"a":2}\n', "duplicate"),
            "duplicate JSON object key",
        )
    )
    controls.append(
        expect_failure(
            "json_duplicate_nested_key",
            lambda: checker.parse_json_object(b'{"a":{"b":1,"b":2}}\n', "duplicate"),
            "duplicate JSON object key",
        )
    )
    controls.append(
        expect_failure(
            "json_invalid_utf8",
            lambda: checker.parse_json_object(b'{"a":"\xff"}\n', "invalid"),
            "not strict duplicate-free",
        )
    )
    controls.append(
        expect_failure(
            "json_carriage_return",
            lambda: checker.parse_json_object(b'{"a":1}\r\n', "CR"),
            "carriage return",
        )
    )
    controls.append(
        expect_failure(
            "json_nonobject_root",
            lambda: checker.parse_json_object(b"[]\n", "array"),
            "root must be an object",
        )
    )
    for name, token in (
        ("json_nonfinite_nan", b"NaN"),
        ("json_nonfinite_positive_infinity", b"Infinity"),
        ("json_nonfinite_negative_infinity", b"-Infinity"),
    ):
        controls.append(
            expect_failure(
                name,
                lambda token=token: checker.parse_json_object(
                    b'{"value":' + token + b"}\n", "nonfinite"
                ),
                "non-finite JSON constant is forbidden",
            )
        )
    for name, token in (
        ("json_float_token", b"1.0"),
        ("json_float_positive_overflow", b"1e9999"),
        ("json_float_negative_overflow", b"-1e9999"),
    ):
        controls.append(
            expect_failure(
                name,
                lambda token=token: checker.parse_json_object(
                    b'{"value":' + token + b"}\n", "float"
                ),
                "JSON floating-point number is forbidden",
            )
        )
    noncanonical = b" " + METADATA_SOURCE
    parsed_noncanonical = checker.parse_json_object(noncanonical, "noncanonical")
    controls.append(
        expect_failure(
            "metadata_noncanonical_transport",
            lambda: checker.require(
                noncanonical == checker.canonical_metadata_bytes(parsed_noncanonical),
                "metadata is not canonical",
            ),
            "not canonical",
        )
    )

    mutations = (
        ("schema", ("schema",), "pid-rs/wrong", "schema drifted"),
        ("limit", ("limits", "members_max"), 20_001, "resource-limit policy drifted"),
        (
            "nested_output_ceiling",
            ("limits", "child_output_bytes_max"),
            16_384,
            "resource-limit policy drifted",
        ),
        (
            "nested_non_replay_lean_child_bound",
            ("limits", "nested_kernel_non_replay_lean_child_timeout_seconds"),
            119,
            "resource-limit policy drifted",
        ),
        (
            "nested_non_replay_lean_child_count",
            ("limits", "nested_kernel_non_replay_lean_child_count"),
            5,
            "resource-limit policy drifted",
        ),
        (
            "nested_identity_child_bound",
            ("limits", "nested_kernel_identity_child_timeout_seconds"),
            59,
            "resource-limit policy drifted",
        ),
        (
            "nested_identity_child_count",
            ("limits", "nested_kernel_identity_child_count"),
            3,
            "resource-limit policy drifted",
        ),
        (
            "nested_orchestration_headroom",
            ("limits", "nested_kernel_orchestration_headroom_seconds"),
            239,
            "resource-limit policy drifted",
        ),
        (
            "nested_non_replay_allocation",
            ("limits", "nested_kernel_non_replay_margin_seconds"),
            1_199,
            "resource-limit policy drifted",
        ),
        (
            "nested_required_outer_bound",
            ("limits", "nested_kernel_required_outer_timeout_seconds"),
            3_899,
            "resource-limit policy drifted",
        ),
        (
            "nested_selected_outer_bound",
            ("limits", "nested_kernel_regression_timeout_seconds"),
            4_199,
            "resource-limit policy drifted",
        ),
        (
            "process_group_term_grace_bound",
            ("limits", "process_group_term_grace_milliseconds"),
            499,
            "resource-limit policy drifted",
        ),
        (
            "process_group_kill_grace_bound",
            ("limits", "process_group_kill_grace_milliseconds"),
            1_999,
            "resource-limit policy drifted",
        ),
        (
            "process_group_poll_interval_bound",
            ("limits", "process_group_poll_interval_milliseconds"),
            9,
            "resource-limit policy drifted",
        ),
        (
            "direct_child_reap_bound",
            ("limits", "direct_child_reap_timeout_milliseconds"),
            1_999,
            "resource-limit policy drifted",
        ),
        (
            "provider_observation_date",
            ("provider_observation_provenance", "observed_utc_date"),
            "2026-08-06",
            "provider observation provenance drifted",
        ),
        (
            "provider_observation_authentication",
            ("provider_observation_provenance", "authentication"),
            "authenticated",
            "provider observation provenance drifted",
        ),
        (
            "provider_observation_raw_response_retention",
            ("provider_observation_provenance", "raw_provider_response_retained"),
            True,
            "provider observation provenance drifted",
        ),
        (
            "provider_observation_compare_route",
            (
                "provider_observation_provenance",
                "routes",
                "compare_pull_request_result_to_tag",
            ),
            "https://example.invalid/compare",
            "provider observation provenance drifted",
        ),
        (
            "release_id",
            ("subject", "release", "id"),
            361_230_721,
            "release/tag identity drifted",
        ),
        (
            "release_draft_boolean_integer_collapse",
            ("subject", "release", "draft"),
            0,
            "release/tag identity drifted",
        ),
        (
            "release_prerelease_boolean_integer_collapse",
            ("subject", "release", "prerelease"),
            0,
            "release/tag identity drifted",
        ),
        (
            "release_tag",
            ("subject", "release", "tag"),
            "v4.32.1",
            "release/tag identity drifted",
        ),
        (
            "target_commitish",
            ("subject", "release", "target_commitish"),
            "main",
            "release/tag identity drifted",
        ),
        (
            "tag_commit",
            ("subject", "release", "tag_commit"),
            "0" * 40,
            "release/tag identity drifted",
        ),
        (
            "tag_parent",
            ("subject", "release", "tag_commit_parent"),
            "0" * 40,
            "release/tag identity drifted",
        ),
        (
            "tag_signature",
            ("subject", "release", "tag_commit_signature"),
            "verified",
            "release/tag identity drifted",
        ),
        ("fix_commit", ("subject", "fix", "commit"), "0" * 40, "fix identity drifted"),
        (
            "fix_parent",
            ("subject", "fix", "commit_parent"),
            "0" * 40,
            "fix identity drifted",
        ),
        ("fix_issue", ("subject", "fix", "issue"), 14_575, "fix identity drifted"),
        (
            "fix_subject_sha",
            ("subject", "fix", "commit_subject_sha256"),
            "0" * 64,
            "fix identity drifted",
        ),
        (
            "fix_release_branch_role",
            ("subject", "fix", "release_branch_role"),
            "pull_request_merge",
            "fix identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_commit",
            ("subject", "provider_recorded_pull_request_result", "commit"),
            "0" * 40,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_merge_base",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "merge_base_with_tag_commit",
            ),
            "0" * 40,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_relation",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "relation_to_tag_commit",
            ),
            "ancestor",
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_authentication",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "provider_metadata_authentication",
            ),
            "authenticated",
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_sole_parent",
            ("subject", "provider_recorded_pull_request_result", "sole_parent"),
            "0" * 40,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_parent_count_boolean_integer_collapse",
            ("subject", "provider_recorded_pull_request_result", "parent_count"),
            True,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_tree",
            ("subject", "provider_recorded_pull_request_result", "commit_tree"),
            "0" * 40,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_subject_sha",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "commit_subject_sha256",
            ),
            "0" * 64,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_verification_boolean_integer_collapse",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "provider_verification_verified",
            ),
            1,
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_history_shape",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "history_shape",
            ),
            "two_parent_merge_commit",
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "provider_recorded_pull_request_result_provider_field",
            (
                "subject",
                "provider_recorded_pull_request_result",
                "provider_field",
            ),
            "commit.sha",
            "provider-recorded pull-request result divergence identity drifted",
        ),
        (
            "authentication_status",
            ("authentication_boundary", "status"),
            "authenticated",
            "must remain none",
        ),
        (
            "authentication_statement",
            ("authentication_boundary", "statements", 0),
            "strong authentication",
            "authentication boundary exact semantics drifted",
        ),
        (
            "checker_path",
            ("checker_binding", "checker_path"),
            "scripts/other.py",
            "binding path drifted",
        ),
        (
            "projection_omits",
            ("checker_binding", "projection_omits"),
            [],
            "omission set drifted",
        ),
        (
            "nested_checker_path",
            ("checker_binding", "nested_checker_binding", "path"),
            "scripts/other.py",
            "nested checker binding path drifted",
        ),
        (
            "nested_checker_bytes",
            ("checker_binding", "nested_checker_binding", "bytes"),
            METADATA["checker_binding"]["nested_checker_binding"]["bytes"] + 1,
            "nested checker binding byte length drifted",
        ),
        (
            "nested_checker_sha",
            ("checker_binding", "nested_checker_binding", "sha256"),
            "0" * 64,
            "nested checker binding SHA-256 drifted",
        ),
        (
            "nested_checker_mode",
            ("checker_binding", "nested_checker_binding", "mode"),
            "0600",
            "mode must be 0644",
        ),
        (
            "nested_checker_link",
            ("checker_binding", "nested_checker_binding", "single_hard_link"),
            False,
            "exactly one hard link",
        ),
        (
            "nested_checker_symlink",
            ("checker_binding", "nested_checker_binding", "symbolic_link"),
            True,
            "reject symbolic links",
        ),
        (
            "historical_transfer",
            (
                "historical_nontransferable_observations",
                0,
                "transfer_to_current_packet",
            ),
            True,
            "classification drifted",
        ),
        (
            "historical_receipt_path",
            ("historical_nontransferable_observations", 0, "source_receipt", "path"),
            "audit/evidence/other.json",
            "source receipt identity drifted",
        ),
        (
            "historical_receipt_bytes",
            ("historical_nontransferable_observations", 0, "source_receipt", "bytes"),
            144_127,
            "source receipt identity drifted",
        ),
        (
            "historical_receipt_sha",
            ("historical_nontransferable_observations", 0, "source_receipt", "sha256"),
            "0" * 64,
            "source receipt identity drifted",
        ),
        (
            "historical_receipt_mode",
            ("historical_nontransferable_observations", 0, "source_receipt", "mode"),
            "0600",
            "source receipt identity drifted",
        ),
        (
            "historical_receipt_link",
            (
                "historical_nontransferable_observations",
                0,
                "source_receipt",
                "single_hard_link",
            ),
            False,
            "source receipt identity drifted",
        ),
        (
            "historical_receipt_symlink",
            (
                "historical_nontransferable_observations",
                0,
                "source_receipt",
                "symbolic_link",
            ),
            True,
            "source receipt identity drifted",
        ),
        ("darwin_asset_id", ("assets", 0, "github_asset", "id"), 1, "asset id drifted"),
        (
            "darwin_asset_size",
            ("assets", 0, "archive", "size"),
            550_165_783,
            "archive size drifted",
        ),
        (
            "darwin_asset_sha",
            ("assets", 0, "archive", "sha256"),
            "0" * 64,
            "archive SHA-256 drifted",
        ),
        (
            "darwin_advertised_digest",
            ("assets", 0, "github_asset", "digest"),
            "sha256:" + "0" * 64,
            "GitHub digest",
        ),
        (
            "darwin_root",
            ("assets", 0, "archive", "root"),
            "lean-4.32.2-other",
            "archive root drifted",
        ),
        (
            "darwin_reviewed_pending_reason",
            ("assets", 0, "custody_lifecycle", "pending_reason"),
            "stale pending reason",
            "strict-replay lifecycle drifted",
        ),
        (
            "darwin_reviewed_inventory_shape",
            ("assets", 0, "custody_lifecycle", "inventory"),
            {},
            "keys drifted",
        ),
        (
            "darwin_reviewed_leaves_shape",
            ("assets", 0, "custody_lifecycle", "leaves"),
            {},
            "keys drifted",
        ),
        (
            "darwin_reviewed_probes_shape",
            ("assets", 0, "custody_lifecycle", "probes"),
            {},
            "keys drifted",
        ),
        (
            "darwin_reviewed_tree_shape",
            ("assets", 0, "custody_lifecycle", "tree_manifest"),
            {},
            "keys drifted",
        ),
        (
            "linux_asset_size",
            ("assets", 1, "github_asset", "size"),
            1,
            "asset size disagrees",
        ),
        (
            "linux_pending_reason",
            ("assets", 1, "custody_lifecycle", "pending_reason"),
            None,
            "pending lifecycle route drifted",
        ),
        (
            "linux_unreviewed_inventory",
            ("assets", 1, "custody_lifecycle", "inventory"),
            {},
            "must not contain reviewed derived pins",
        ),
        (
            "asset_order",
            ("assets", 0, "key"),
            "linux-x86_64",
            "expected asset selection drifted",
        ),
    )
    for name, path, replacement, expected in mutations:
        controls.append(
            expect_failure(
                "metadata_" + name,
                lambda path=path, replacement=replacement: require_policy(
                    mutated_policy(path, replacement)
                ),
                expected,
            )
        )

    source_mutation = copy.deepcopy(METADATA)
    source_mutation["checker_binding"]["checker_sha256"] = "0" * 64
    controls.append(
        expect_failure(
            "checker_source_binding_sha",
            lambda: checker.require(
                EXPECTED_CHECKER_SHA256
                == source_mutation["checker_binding"]["checker_sha256"],
                "checker source SHA-256 binding drifted",
            ),
            "binding drifted",
        )
    )
    source_size = copy.deepcopy(METADATA)
    source_size["checker_binding"]["checker_bytes"] = 1
    controls.append(
        expect_failure(
            "checker_source_binding_size",
            lambda: checker.require(
                len(CHECKER_SOURCE) == source_size["checker_binding"]["checker_bytes"],
                "checker source byte-length binding drifted",
            ),
            "binding drifted",
        )
    )
    return controls


def literal_dict_key_controls() -> list[dict[str, object]]:
    def duplicate_keys(source: bytes) -> list[str]:
        tree = ast.parse(source, filename="<literal-dict-key-audit>")
        duplicates: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            seen: set[str] = set()
            for key in node.keys:
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                if key.value in seen:
                    duplicates.append(key.value)
                seen.add(key.value)
        return duplicates

    require(
        duplicate_keys(CHECKER_SOURCE) == [],
        "custody checker contains a duplicate literal dictionary key",
    )
    return [
        expect_failure(
            "duplicate_literal_dictionary_key",
            lambda: checker.require(
                duplicate_keys(b"packet = {'route': 1, 'route': 2}\n") == [],
                "custody checker contains a duplicate literal dictionary key",
            ),
            "duplicate literal dictionary key",
        )
    ]


def tar_info(
    name: str, kind: bytes, *, size: int = 0, mode: int = 0o644, linkname: str = ""
) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = size
    info.mode = mode
    info.linkname = linkname
    return info


def synthetic_members() -> list[tuple[tarfile.TarInfo, bytes | None]]:
    root = ASSETS["darwin-aarch64"]["archive"]["root"]
    return [
        (tar_info(root, tarfile.DIRTYPE, mode=0o755), None),
        (tar_info(f"{root}/bin", tarfile.DIRTYPE, mode=0o755), None),
        (tar_info(f"{root}/bin/lean", tarfile.REGTYPE, size=4, mode=0o755), b"lean"),
        (tar_info(f"{root}/bin/lake", tarfile.REGTYPE, size=4, mode=0o755), b"lake"),
        (
            tar_info(f"{root}/bin/leanchecker", tarfile.REGTYPE, size=7, mode=0o755),
            b"checker",
        ),
        (
            tar_info(f"{root}/LICENSE", tarfile.REGTYPE, size=8, mode=0o644),
            b"license\n",
        ),
    ]


def make_tar(members: list[tuple[tarfile.TarInfo, bytes | None]]) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for info, payload in members:
            archive.addfile(info, None if payload is None else io.BytesIO(payload))
    return stream.getvalue()


def synthetic_baseline() -> tuple[
    bytes, list[object], dict[str, int], list[object], str
]:
    raw = make_tar(synthetic_members())
    records, inventory = checker.preflight_tar_stream(
        io.BytesIO(raw), ASSETS["darwin-aarch64"], LIMITS
    )
    require(
        inventory
        == {
            "directories": 2,
            "max_depth": 3,
            "max_file_bytes": 8,
            "max_path_bytes": 42,
            "members": 6,
            "regular_file_bytes": 23,
            "regular_files": 4,
        },
        f"synthetic inventory drifted: {inventory}",
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-custody-selftest-"
    ) as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        extracted = checker.extract_tar_stream(
            io.BytesIO(raw), destination, ASSETS["darwin-aarch64"], LIMITS, records
        )
        expected = checker.entries_from_records(records, extracted)
        scanned = checker.scan_extracted_tree(destination, LIMITS)
        checker.require_same_tree(expected, scanned, "in synthetic baseline")
        leaves = checker.leaf_facts(
            scanned, ASSETS["darwin-aarch64"]["archive"]["root"]
        )
        require(
            set(leaves) == {"lean", "lake", "leanchecker"},
            "synthetic leaf inventory drifted",
        )
        manifest = checker.tree_manifest_sha256(scanned)
    return raw, records, inventory, scanned, manifest


(
    SYNTHETIC_TAR,
    SYNTHETIC_RECORDS,
    SYNTHETIC_INVENTORY,
    SYNTHETIC_TREE,
    SYNTHETIC_MANIFEST,
) = synthetic_baseline()


def member_controls() -> list[dict[str, object]]:
    root = ASSETS["darwin-aarch64"]["archive"]["root"]
    cases = (
        ("absolute_path", tar_info(f"/{root}/x", tarfile.REGTYPE, size=1), "absolute"),
        (
            "parent_traversal",
            tar_info(f"{root}/../x", tarfile.REGTYPE, size=1),
            "traversing",
        ),
        (
            "dot_component",
            tar_info(f"{root}/./x", tarfile.REGTYPE, size=1),
            "non-normal",
        ),
        (
            "empty_component",
            tar_info(f"{root}//x", tarfile.REGTYPE, size=1),
            "non-normal",
        ),
        (
            "backslash",
            tar_info(f"{root}\\x", tarfile.REGTYPE, size=1),
            "forbidden separator",
        ),
        (
            "drive_marker",
            tar_info(f"{root}/C:x", tarfile.REGTYPE, size=1),
            "drive marker",
        ),
        ("non_ascii", tar_info(f"{root}/café", tarfile.REGTYPE, size=1), "not ASCII"),
        (
            "unsupported_character",
            tar_info(f"{root}/x y", tarfile.REGTYPE, size=1),
            "unsupported component",
        ),
        (
            "unexpected_root",
            tar_info("other/x", tarfile.REGTYPE, size=1),
            "unexpected archive root",
        ),
        (
            "symlink",
            tar_info(f"{root}/sym", tarfile.SYMTYPE, linkname=""),
            "links are forbidden",
        ),
        (
            "hardlink",
            tar_info(f"{root}/hard", tarfile.LNKTYPE, linkname=""),
            "links are forbidden",
        ),
        ("fifo", tar_info(f"{root}/fifo", tarfile.FIFOTYPE), "device/FIFO"),
        ("character_device", tar_info(f"{root}/char", tarfile.CHRTYPE), "device/FIFO"),
        ("block_device", tar_info(f"{root}/block", tarfile.BLKTYPE), "device/FIFO"),
        ("socket_type", tar_info(f"{root}/socket", b"s"), "unsupported"),
        (
            "file_bad_mode",
            tar_info(f"{root}/mode", tarfile.REGTYPE, size=1, mode=0o666),
            "neither 0644 nor 0755",
        ),
        (
            "directory_bad_mode",
            tar_info(f"{root}/dir", tarfile.DIRTYPE, mode=0o777),
            "mode is not 0755",
        ),
        (
            "directory_payload",
            tar_info(f"{root}/dir", tarfile.DIRTYPE, size=1, mode=0o755),
            "nonzero payload",
        ),
        (
            "link_target_on_file",
            tar_info(f"{root}/file", tarfile.REGTYPE, size=1, linkname="target"),
            "unexpected link target",
        ),
    )
    controls = [
        expect_failure(
            "tar_" + name,
            lambda info=info: checker.member_record(info, root, LIMITS),
            expected,
        )
        for name, info, expected in cases
    ]
    too_long = tar_info(root + "/" + "a" * 300, tarfile.REGTYPE, size=1)
    controls.append(
        expect_failure(
            "tar_path_byte_ceiling",
            lambda: checker.member_record(too_long, root, LIMITS),
            "path exceeds",
        )
    )
    too_deep = tar_info(
        root + "/" + "/".join("a" for _ in range(20)), tarfile.REGTYPE, size=1
    )
    controls.append(
        expect_failure(
            "tar_path_depth_ceiling",
            lambda: checker.member_record(too_deep, root, LIMITS),
            "depth ceiling",
        )
    )
    too_large = tar_info(
        f"{root}/large", tarfile.REGTYPE, size=int(LIMITS["file_bytes_max"]) + 1
    )
    controls.append(
        expect_failure(
            "tar_file_byte_ceiling",
            lambda: checker.member_record(too_large, root, LIMITS),
            "file exceeds",
        )
    )
    pax = tar_info(f"{root}/pax", tarfile.REGTYPE, size=1)
    pax.pax_headers = {"path": pax.name}
    controls.append(
        expect_failure(
            "tar_pax_metadata",
            lambda: checker.member_record(pax, root, LIMITS),
            "PAX metadata",
        )
    )
    sparse = tar_info(f"{root}/sparse", tarfile.REGTYPE, size=1)
    sparse.sparse = [(0, 1)]
    controls.append(
        expect_failure(
            "tar_sparse_extents",
            lambda: checker.member_record(sparse, root, LIMITS),
            "sparse extents",
        )
    )
    return controls


def inventory_controls() -> list[dict[str, object]]:
    root = ASSETS["darwin-aarch64"]["archive"]["root"]
    directory = checker.MemberRecord(root, "directory", "0755", 0)
    bin_dir = checker.MemberRecord(f"{root}/bin", "directory", "0755", 0)
    leaf = checker.MemberRecord(f"{root}/bin/lean", "file", "0755", 4)
    controls = [
        expect_failure(
            "inventory_empty",
            lambda: checker.inventory_from_records([], LIMITS),
            "no members",
        ),
        expect_failure(
            "inventory_duplicate_exact",
            lambda: checker.inventory_from_records(
                [directory, bin_dir, leaf, leaf], LIMITS
            ),
            "duplicate normalized",
        ),
        expect_failure(
            "inventory_casefold_collision",
            lambda: checker.inventory_from_records(
                [
                    directory,
                    bin_dir,
                    leaf,
                    checker.MemberRecord(f"{root}/bin/Lean", "file", "0755", 4),
                ],
                LIMITS,
            ),
            "case-folding",
        ),
        expect_failure(
            "inventory_missing_parent",
            lambda: checker.inventory_from_records([directory, leaf], LIMITS),
            "parent is absent",
        ),
        expect_failure(
            "inventory_file_as_parent",
            lambda: checker.inventory_from_records(
                [
                    directory,
                    checker.MemberRecord(f"{root}/bin", "file", "0644", 1),
                    leaf,
                ],
                LIMITS,
            ),
            "file is used as a parent",
        ),
        expect_failure(
            "inventory_root_not_directory",
            lambda: checker.inventory_from_records(
                [checker.MemberRecord(root, "file", "0644", 1)], LIMITS
            ),
            "first tar member",
        ),
        expect_failure(
            "inventory_multiple_roots",
            lambda: checker.inventory_from_records(
                [directory, checker.MemberRecord("other", "directory", "0755", 0)],
                LIMITS,
            ),
            "multiple roots",
        ),
    ]
    limited = dict(LIMITS)
    limited["members_max"] = 2
    controls.append(
        expect_failure(
            "inventory_member_ceiling",
            lambda: checker.inventory_from_records([directory, bin_dir, leaf], limited),
            "member count",
        )
    )
    limited = dict(LIMITS)
    limited["directories_max"] = 1
    controls.append(
        expect_failure(
            "inventory_directory_ceiling",
            lambda: checker.inventory_from_records([directory, bin_dir, leaf], limited),
            "directory count",
        )
    )
    limited = dict(LIMITS)
    limited["regular_files_max"] = 0
    controls.append(
        expect_failure(
            "inventory_file_count_ceiling",
            lambda: checker.inventory_from_records([directory, bin_dir, leaf], limited),
            "regular-file count",
        )
    )
    limited = dict(LIMITS)
    limited["regular_file_bytes_max"] = 3
    controls.append(
        expect_failure(
            "inventory_total_bytes_ceiling",
            lambda: checker.inventory_from_records([directory, bin_dir, leaf], limited),
            "regular-file bytes",
        )
    )
    return controls


def extraction_controls() -> list[dict[str, object]]:
    asset = ASSETS["darwin-aarch64"]
    controls: list[dict[str, object]] = []
    changed_members = synthetic_members()
    changed_members[2] = (
        tar_info(changed_members[2][0].name, tarfile.REGTYPE, size=5, mode=0o755),
        b"lean!",
    )
    changed_tar = make_tar(changed_members)
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-extract-sequence-"
    ) as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        controls.append(
            expect_failure(
                "extraction_member_changed_after_preflight",
                lambda: checker.extract_tar_stream(
                    io.BytesIO(changed_tar),
                    destination,
                    asset,
                    LIMITS,
                    SYNTHETIC_RECORDS,
                ),
                "changed between preflight",
            )
        )
    missing_tar = make_tar(synthetic_members()[:-1])
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-extract-missing-"
    ) as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        controls.append(
            expect_failure(
                "extraction_member_lost_after_preflight",
                lambda: checker.extract_tar_stream(
                    io.BytesIO(missing_tar),
                    destination,
                    asset,
                    LIMITS,
                    SYNTHETIC_RECORDS,
                ),
                "lost a preflighted",
            )
        )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-extract-nonempty-"
    ) as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        (destination / "occupied").write_bytes(b"x")
        controls.append(
            expect_failure(
                "extraction_nonempty_destination",
                lambda: checker.extract_tar_stream(
                    io.BytesIO(SYNTHETIC_TAR),
                    destination,
                    asset,
                    LIMITS,
                    SYNTHETIC_RECORDS,
                ),
                "not empty",
            )
        )
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-tree-mutation-") as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        checker.extract_tar_stream(
            io.BytesIO(SYNTHETIC_TAR), destination, asset, LIMITS, SYNTHETIC_RECORDS
        )
        root = destination / asset["archive"]["root"]
        target = root / "LICENSE"
        target.write_bytes(b"mutated\n")
        changed = checker.scan_extracted_tree(destination, LIMITS)
        controls.append(
            expect_failure(
                "tree_content_mutation",
                lambda: checker.require_same_tree(
                    SYNTHETIC_TREE, changed, "after content mutation"
                ),
                "tree changed",
            )
        )
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-tree-symlink-") as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        checker.extract_tar_stream(
            io.BytesIO(SYNTHETIC_TAR), destination, asset, LIMITS, SYNTHETIC_RECORDS
        )
        root = destination / asset["archive"]["root"]
        (root / "symlink").symlink_to(root / "LICENSE")
        controls.append(
            expect_failure(
                "tree_symbolic_link",
                lambda: checker.scan_extracted_tree(destination, LIMITS),
                "link or special",
            )
        )
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-tree-mode-") as temporary:
        destination = Path(temporary) / "tree"
        os.mkdir(destination, 0o700)
        checker.extract_tar_stream(
            io.BytesIO(SYNTHETIC_TAR), destination, asset, LIMITS, SYNTHETIC_RECORDS
        )
        root = destination / asset["archive"]["root"]
        (root / "LICENSE").chmod(0o600)
        controls.append(
            expect_failure(
                "tree_mode_mutation",
                lambda: checker.scan_extracted_tree(destination, LIMITS),
                "mode drifted",
            )
        )
    malformed_entry = checker.TreeEntry("x", "file", "0644", None, None)
    controls.append(
        expect_failure(
            "manifest_incomplete_file_row",
            lambda: checker.tree_manifest_sha256([malformed_entry]),
            "file row is incomplete",
        )
    )
    reversed_tree = list(reversed(SYNTHETIC_TREE))
    controls.append(
        expect_failure(
            "manifest_unsorted_paths",
            lambda: checker.tree_manifest_sha256(reversed_tree),
            "not strictly byte-sorted",
        )
    )
    missing_leaf_tree = [
        entry for entry in SYNTHETIC_TREE if not entry.path.endswith("/bin/leanchecker")
    ]
    controls.append(
        expect_failure(
            "manifest_missing_leanchecker_leaf",
            lambda: checker.leaf_facts(missing_leaf_tree, asset["archive"]["root"]),
            "leaf is absent",
        )
    )
    return controls


def version_controls() -> list[dict[str, object]]:
    darwin = b"Lean (version 4.32.2, arm64-apple-darwin24.6.0, commit f3b06c705e6c85f5314019d5d3baab0fec5b580c, Release)\n"
    linux = b"Lean (version 4.32.2, x86_64-unknown-linux-gnu, commit f3b06c705e6c85f5314019d5d3baab0fec5b580c, Release)\n"
    require(
        checker.parse_lean_version(checker.ProcessResult(0, darwin, b"")).platform
        == "arm64-apple-darwin24.6.0",
        "Darwin version positive drifted",
    )
    require(
        checker.parse_lean_version(checker.ProcessResult(0, linux, b"")).platform
        == "x86_64-unknown-linux-gnu",
        "Linux version positive drifted",
    )
    lean_cases = (
        ("lean_nonzero", checker.ProcessResult(1, darwin, b""), "exited 1"),
        (
            "lean_stderr",
            checker.ProcessResult(0, darwin, b"warning\n"),
            "emitted stderr",
        ),
        (
            "lean_wrong_version",
            checker.ProcessResult(0, darwin.replace(b"4.32.2", b"4.32.1", 1), b""),
            "not 4.32.2",
        ),
        (
            "lean_wrong_commit",
            checker.ProcessResult(0, darwin.replace(b"f3b06c", b"03b06c", 1), b""),
            "wrong source commit",
        ),
        (
            "lean_debug",
            checker.ProcessResult(0, darwin.replace(b"Release", b"Debug"), b""),
            "Release build",
        ),
        (
            "lean_missing_newline",
            checker.ProcessResult(0, darwin[:-1], b""),
            "unexpected Lean version",
        ),
        (
            "lean_extra_line",
            checker.ProcessResult(0, darwin + b"extra\n", b""),
            "unexpected Lean version",
        ),
        (
            "lean_crlf",
            checker.ProcessResult(0, darwin[:-1] + b"\r\n", b""),
            "carriage return",
        ),
        (
            "lean_short_platform",
            checker.ProcessResult(
                0, darwin.replace(b"arm64-apple-darwin24.6.0", b"darwin"), b""
            ),
            "unexpected Lean version",
        ),
        (
            "lean_long_secret_stdout",
            checker.ProcessResult(0, b"lean_stdout_secret_" + b"x" * 2_000, b""),
            "digest-only rejection",
        ),
    )
    controls = [
        expect_exact_failure(
            name,
            lambda result=result: checker.parse_lean_version(result),
            checker.process_result_rejection_diagnostic("Lean version probe", result),
        )
        for name, result, _expected in lean_cases
    ]
    lake = b"Lake version 5.0.0-src+f3b06c7 (Lean version 4.32.2)\n"
    checker.validate_lake_version(checker.ProcessResult(0, lake, b""))
    lake_cases = (
        ("lake_nonzero", checker.ProcessResult(1, lake, b""), "exited 1"),
        ("lake_stderr", checker.ProcessResult(0, lake, b"warning\n"), "emitted stderr"),
        (
            "lake_wrong_commit",
            checker.ProcessResult(0, lake.replace(b"f3b06c7", b"03b06c7"), b""),
            "wrong exact version/source-commit abbreviation",
        ),
        (
            "lake_wrong_lean",
            checker.ProcessResult(0, lake.replace(b"4.32.2", b"4.32.1"), b""),
            "wrong Lean version",
        ),
        (
            "lake_extra_line",
            checker.ProcessResult(0, lake + b"extra\n", b""),
            "unexpected Lake version",
        ),
        (
            "lake_crlf",
            checker.ProcessResult(0, lake[:-1] + b"\r\n", b""),
            "carriage return",
        ),
        (
            "lake_long_secret_stdout",
            checker.ProcessResult(0, b"lake_stdout_secret_" + b"y" * 2_000, b""),
            "digest-only rejection",
        ),
    )
    controls.extend(
        expect_exact_failure(
            name,
            lambda result=result: checker.validate_lake_version(result),
            checker.process_result_rejection_diagnostic("Lake version probe", result),
        )
        for name, result, _expected in lake_cases
    )
    checker_stderr = b"uncaught exception: Could not find any oleans for: pid_rs_toolchain_custody_absent_module.olean\n"
    valid_checker = checker.ProcessResult(1, b"", checker_stderr)
    checker.validate_leanchecker_probe(valid_checker)
    checker_cases = (
        ("leanchecker_zero", checker.ProcessResult(0, b"", checker_stderr), "exited 0"),
        (
            "leanchecker_stdout",
            checker.ProcessResult(1, b"extra\n", checker_stderr),
            "emitted stdout",
        ),
        (
            "leanchecker_wrong_diagnostic",
            checker.ProcessResult(1, b"", b"not found\n"),
            "diagnostic drifted",
        ),
        (
            "leanchecker_long_secret_stderr",
            checker.ProcessResult(1, b"", b"leanchecker_stderr_secret_" + b"z" * 2_000),
            "digest-only rejection",
        ),
    )
    controls.extend(
        expect_exact_failure(
            name,
            lambda result=result: checker.validate_leanchecker_probe(result),
            checker.process_result_rejection_diagnostic(
                "LeanChecker absent-module probe", result
            ),
        )
        for name, result, _expected in checker_cases
    )
    return controls


def version_independent_ast_projection(value: object) -> object:
    """Project semantic AST fields while omitting only empty version-added metadata."""

    if isinstance(value, ast.AST):
        fields: list[list[object]] = []
        for field in sorted(value._fields):
            observed = getattr(value, field)
            if observed is None or observed == [] or observed == ():
                continue
            fields.append([field, version_independent_ast_projection(observed)])
        return {"fields": fields, "node": type(value).__name__}
    if isinstance(value, list):
        return [version_independent_ast_projection(item) for item in value]
    if isinstance(value, tuple):
        return {"tuple": [version_independent_ast_projection(item) for item in value]}
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if value is Ellipsis:
        return {"ellipsis": True}
    if value is None or type(value) in {bool, float, int, str}:
        return value
    raise SelfTestError(
        "production qualify AST projection encountered an unsupported value"
    )


def validate_production_qualify_executable_wiring(
    source: bytes,
) -> dict[str, object]:
    """Prove the exact producer/use/order graph in the real qualify function."""

    failure = "production qualify executable custody wiring drifted"
    try:
        tree = ast.parse(source, filename="<production-qualify-wiring>")
    except (SyntaxError, UnicodeError) as error:
        raise SelfTestError(failure) from error
    candidates = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "qualify"
    ]
    require(len(candidates) == 1, failure)
    qualify_node = candidates[0]
    main_candidates = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "main"
    ]
    require(len(main_candidates) == 1, failure)
    main_node = main_candidates[0]
    parents = {
        child: parent
        for parent in ast.walk(qualify_node)
        for child in ast.iter_child_nodes(parent)
    }
    with_candidates = [
        node
        for node in ast.walk(qualify_node)
        if isinstance(node, ast.With)
        and len(node.items) == 1
        and isinstance(node.items[0].context_expr, ast.Call)
        and isinstance(node.items[0].context_expr.func, ast.Attribute)
        and isinstance(node.items[0].context_expr.func.value, ast.Name)
        and node.items[0].context_expr.func.value.id == "tempfile"
        and node.items[0].context_expr.func.attr == "TemporaryDirectory"
    ]
    require(len(with_candidates) == 1, failure)
    custody_with = with_candidates[0]
    require(parents.get(custody_with) is qualify_node, failure)

    def call_name(call: ast.Call) -> str | None:
        return call.func.id if isinstance(call.func, ast.Name) else None

    def name(argument: ast.expr) -> str | None:
        return argument.id if isinstance(argument, ast.Name) else None

    def text(argument: ast.expr) -> str | None:
        return (
            argument.value
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            else None
        )

    critical_callees = {
        "leaf_facts",
        "probe_toolchain",
        "require",
        "require_executable_snapshot_sets_equal",
        "require_executable_snapshots_match_tree_leaves",
        "require_same_tree",
        "run_nested_kernel_regression",
        "scan_extracted_tree",
        "snapshot_tool_executables",
        "tree_manifest_sha256",
    }
    route_critical_names = critical_callees | {"main", "qualify"}

    def module_scope_nodes() -> list[ast.AST]:
        """Walk executable module scope without entering function or class bodies."""

        pending: list[ast.AST] = list(reversed(tree.body))
        observed: list[ast.AST] = []
        while pending:
            node = pending.pop()
            observed.append(node)
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                continue
            pending.extend(reversed(list(ast.iter_child_nodes(node))))
        return observed

    module_nodes = module_scope_nodes()
    module_function_counts = {
        critical: sum(
            1
            for node in module_nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == critical
        )
        for critical in route_critical_names
    }
    require(
        module_function_counts == {critical: 1 for critical in route_critical_names},
        failure,
    )
    module_other_bindings: set[str] = {
        node.id
        for node in module_nodes
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    module_other_bindings.update(
        node.name for node in module_nodes if isinstance(node, ast.ClassDef)
    )
    module_other_bindings.update(
        node.asname if node.asname is not None else node.name.split(".", 1)[0]
        for node in module_nodes
        if isinstance(node, ast.alias)
    )
    module_other_bindings.update(
        node.name
        for node in module_nodes
        if isinstance(node, ast.ExceptHandler) and node.name is not None
    )
    module_other_bindings.update(
        name
        for node in module_nodes
        if isinstance(node, (ast.Global, ast.Nonlocal))
        for name in node.names
    )
    for node in module_nodes:
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
            module_other_bindings.add(node.name)
        if isinstance(node, ast.MatchMapping) and node.rest is not None:
            module_other_bindings.add(node.rest)
    require(module_other_bindings.isdisjoint(route_critical_names), failure)
    module_dynamic_calls = {
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "globals",
        "locals",
        "setattr",
        "vars",
    }
    require(
        not any(
            (
                isinstance(node, (ast.Attribute, ast.Subscript))
                and isinstance(node.ctx, (ast.Store, ast.Del))
            )
            or (
                isinstance(node, ast.Call)
                and (
                    (
                        isinstance(node.func, ast.Name)
                        and node.func.id in module_dynamic_calls
                    )
                    or isinstance(node.func, ast.Subscript)
                )
            )
            or isinstance(node, ast.NamedExpr)
            for node in module_nodes
        ),
        failure,
    )
    main_bound_names = {
        node.id
        for node in ast.walk(main_node)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    main_bound_names.update(
        name
        for node in ast.walk(main_node)
        if isinstance(node, (ast.Global, ast.Nonlocal))
        for name in node.names
    )
    main_bound_names.update(
        node.arg for node in ast.walk(main_node) if isinstance(node, ast.arg)
    )
    main_bound_names.update(
        node.asname if node.asname is not None else node.name.split(".", 1)[0]
        for node in ast.walk(main_node)
        if isinstance(node, ast.alias)
    )
    require(main_bound_names.isdisjoint(route_critical_names), failure)
    main_dynamic_calls = {
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "globals",
        "locals",
        "setattr",
        "vars",
    }
    require(
        len(main_node.body) == 1
        and isinstance(main_node.body[0], ast.Try)
        and not any(
            (
                isinstance(node, (ast.Attribute, ast.Subscript))
                and isinstance(node.ctx, (ast.Store, ast.Del))
            )
            or (
                isinstance(node, ast.Call)
                and (
                    (
                        isinstance(node.func, ast.Name)
                        and node.func.id in main_dynamic_calls
                    )
                    or isinstance(node.func, ast.Subscript)
                )
            )
            or isinstance(node, ast.NamedExpr)
            for node in ast.walk(main_node)
        ),
        failure,
    )
    main_try = main_node.body[0]
    main_parents = {
        child: parent
        for parent in ast.walk(main_node)
        for child in ast.iter_child_nodes(parent)
    }
    qualify_calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "qualify"
    ]
    require(len(qualify_calls) == 1, failure)
    main_qualify_call = qualify_calls[0]
    main_result_assignment = main_parents.get(main_qualify_call)
    require(
        isinstance(main_result_assignment, ast.Assign)
        and main_result_assignment.value is main_qualify_call
        and len(main_result_assignment.targets) == 1
        and isinstance(main_result_assignment.targets[0], ast.Name)
        and main_result_assignment.targets[0].id == "result"
        and main_parents.get(main_result_assignment) is main_try
        and main_result_assignment in main_try.body
        and len(main_qualify_call.args) == 11
        and not main_qualify_call.keywords
        and isinstance(main_qualify_call.args[0], ast.Subscript)
        and isinstance(main_qualify_call.args[0].value, ast.Name)
        and main_qualify_call.args[0].value.id == "assets"
        and isinstance(main_qualify_call.args[2], ast.Attribute)
        and isinstance(main_qualify_call.args[2].value, ast.Name)
        and main_qualify_call.args[2].value.id == "args"
        and main_qualify_call.args[2].attr == "zstd"
        and isinstance(main_qualify_call.args[3], ast.Attribute)
        and isinstance(main_qualify_call.args[3].value, ast.Name)
        and main_qualify_call.args[3].value.id == "args"
        and main_qualify_call.args[3].attr == "observation_only"
        and tuple(
            argument.id if isinstance(argument, ast.Name) else None
            for argument in main_qualify_call.args[4:]
        )
        == (
            "source_snapshot",
            "metadata_snapshot",
            "nested_checker_snapshot",
            "historical_receipt_snapshot",
            "legacy_raw_snapshot",
            "legacy_receipt_snapshot",
            "metadata",
        ),
        failure,
    )
    bound_names = {
        node.id
        for node in ast.walk(qualify_node)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    bound_names.update(
        node.name
        for node in ast.walk(qualify_node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node is not qualify_node
    )
    bound_names.update(
        name
        for node in ast.walk(qualify_node)
        if isinstance(node, (ast.Global, ast.Nonlocal))
        for name in node.names
    )
    bound_names.update(
        node.arg for node in ast.walk(qualify_node) if isinstance(node, ast.arg)
    )
    bound_names.update(
        node.asname if node.asname is not None else node.name.split(".", 1)[0]
        for node in ast.walk(qualify_node)
        if isinstance(node, ast.alias)
    )
    bound_names.update(
        node.name
        for node in ast.walk(qualify_node)
        if isinstance(node, ast.ExceptHandler) and node.name is not None
    )
    require(bound_names.isdisjoint(critical_callees), failure)
    dynamic_namespace_calls = {
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "globals",
        "locals",
        "setattr",
        "vars",
    }
    require(
        not any(
            (
                isinstance(node, (ast.Attribute, ast.Subscript))
                and isinstance(node.ctx, (ast.Store, ast.Del))
            )
            or (
                isinstance(node, ast.Call)
                and (
                    (
                        isinstance(node.func, ast.Name)
                        and node.func.id in dynamic_namespace_calls
                    )
                    or isinstance(node.func, ast.Subscript)
                )
            )
            or isinstance(node, ast.NamedExpr)
            for node in ast.walk(qualify_node)
        ),
        failure,
    )
    tracked_mutable_values = {
        "final_snapshots",
        "leaves",
        "nested_kernel_regression",
        "post_nested_snapshots",
        "pre_nested_snapshots",
        "probe_snapshots",
        "probes",
        "scanned_after",
        "scanned_before",
    }
    require(
        not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in tracked_mutable_values
            for node in ast.walk(qualify_node)
        )
        and not any(
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Name)
            and node.value.id in tracked_mutable_values
            and any(
                isinstance(target, ast.Name) and target.id != node.value.id
                for target in node.targets
            )
            for node in ast.walk(qualify_node)
        ),
        failure,
    )
    store_counts = {
        tracked: sum(
            1
            for node in ast.walk(qualify_node)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == tracked
        )
        for tracked in (
            "final_snapshots",
            "destination",
            "expected_archive",
            "key",
            "leaves",
            "lifecycle",
            "manifest",
            "nested_kernel_regression",
            "post_nested_snapshots",
            "pre_nested_snapshots",
            "probe_snapshots",
            "probes",
            "scanned_after",
            "scanned_before",
            "state",
            "strict_replay",
            "tool_root",
            "result",
        )
    }
    require(
        store_counts
        == {
            "final_snapshots": 1,
            "destination": 1,
            "expected_archive": 1,
            "key": 1,
            "leaves": 1,
            "lifecycle": 1,
            "manifest": 1,
            "nested_kernel_regression": 2,
            "post_nested_snapshots": 1,
            "pre_nested_snapshots": 1,
            "probe_snapshots": 1,
            "probes": 1,
            "scanned_after": 1,
            "scanned_before": 1,
            "state": 1,
            "strict_replay": 1,
            "tool_root": 1,
            "result": 3,
        },
        failure,
    )
    require(
        len([node for node in ast.walk(qualify_node) if isinstance(node, ast.Return)])
        == 1
        and isinstance(qualify_node.body[-1], ast.Return)
        and not any(
            isinstance(
                node,
                (
                    ast.AsyncFor,
                    ast.Await,
                    ast.Break,
                    ast.Continue,
                    ast.For,
                    ast.Raise,
                    ast.Try,
                    ast.While,
                    ast.Yield,
                    ast.YieldFrom,
                ),
            )
            for node in ast.walk(qualify_node)
        ),
        failure,
    )
    strict_replay_assignments = [
        node
        for node in qualify_node.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "strict_replay"
    ]
    require(len(strict_replay_assignments) == 1, failure)
    strict_replay_value = strict_replay_assignments[0].value
    require(
        isinstance(strict_replay_value, ast.Compare)
        and name(strict_replay_value.left) == "state"
        and len(strict_replay_value.ops) == 1
        and isinstance(strict_replay_value.ops[0], ast.Eq)
        and len(strict_replay_value.comparators) == 1
        and text(strict_replay_value.comparators[0])
        == "reviewed_pins_strict_replay_required",
        failure,
    )

    def assignment_targets(call: ast.Call) -> tuple[str, ...] | None:
        parent = parents.get(call)
        if not isinstance(parent, ast.Assign) or parent.value is not call:
            return None
        if len(parent.targets) != 1:
            return None
        target = parent.targets[0]
        if isinstance(target, ast.Name):
            return (target.id,)
        if isinstance(target, ast.Tuple) and all(
            isinstance(item, ast.Name) for item in target.elts
        ):
            return tuple(item.id for item in target.elts if isinstance(item, ast.Name))
        return None

    def assignment_node(call: ast.Call) -> ast.Assign | None:
        parent = parents.get(call)
        return (
            parent if isinstance(parent, ast.Assign) and parent.value is call else None
        )

    def require_direct_with(call: ast.Call) -> None:
        statement = parents.get(call)
        require(
            isinstance(statement, (ast.Assign, ast.Expr))
            and (
                (isinstance(statement, ast.Assign) and statement.value is call)
                or (isinstance(statement, ast.Expr) and statement.value is call)
            )
            and parents.get(statement) is custody_with
            and statement in custody_with.body,
            failure,
        )

    def direct_assignment(container: ast.AST, target: str) -> ast.Assign:
        body = getattr(container, "body", None)
        require(isinstance(body, list), failure)
        assignments = [
            statement
            for statement in body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == target
        ]
        require(len(assignments) == 1, failure)
        return assignments[0]

    def is_subscript(expression: ast.expr, base: str, key: str) -> bool:
        return (
            isinstance(expression, ast.Subscript)
            and name(expression.value) == base
            and text(expression.slice) == key
        )

    key_assignment = direct_assignment(qualify_node, "key")
    lifecycle_assignment = direct_assignment(qualify_node, "lifecycle")
    state_assignment = direct_assignment(qualify_node, "state")
    expected_archive_assignment = direct_assignment(qualify_node, "expected_archive")
    require(
        is_subscript(key_assignment.value, "asset", "key")
        and is_subscript(lifecycle_assignment.value, "asset", "custody_lifecycle")
        and is_subscript(state_assignment.value, "lifecycle", "state")
        and is_subscript(expected_archive_assignment.value, "asset", "archive"),
        failure,
    )
    destination_assignment = direct_assignment(custody_with, "destination")
    tool_root_assignment = direct_assignment(custody_with, "tool_root")
    scanned_before_assignment = direct_assignment(custody_with, "scanned_before")
    manifest_assignment = direct_assignment(custody_with, "manifest")
    leaves_assignment = direct_assignment(custody_with, "leaves")
    require(
        isinstance(destination_assignment.value, ast.BinOp)
        and isinstance(destination_assignment.value.op, ast.Div)
        and name(destination_assignment.value.left) == "private_root"
        and text(destination_assignment.value.right) == "tree"
        and isinstance(tool_root_assignment.value, ast.BinOp)
        and isinstance(tool_root_assignment.value.op, ast.Div)
        and name(tool_root_assignment.value.left) == "destination"
        and is_subscript(tool_root_assignment.value.right, "expected_archive", "root")
        and isinstance(scanned_before_assignment.value, ast.Call)
        and call_name(scanned_before_assignment.value) == "scan_extracted_tree"
        and tuple(name(argument) for argument in scanned_before_assignment.value.args)
        == ("destination", "limits")
        and not scanned_before_assignment.value.keywords
        and isinstance(manifest_assignment.value, ast.Call)
        and call_name(manifest_assignment.value) == "tree_manifest_sha256"
        and len(manifest_assignment.value.args) == 1
        and name(manifest_assignment.value.args[0]) == "scanned_before"
        and not manifest_assignment.value.keywords
        and isinstance(leaves_assignment.value, ast.Call)
        and call_name(leaves_assignment.value) == "leaf_facts"
        and len(leaves_assignment.value.args) == 2
        and name(leaves_assignment.value.args[0]) == "scanned_before"
        and is_subscript(leaves_assignment.value.args[1], "expected_archive", "root")
        and not leaves_assignment.value.keywords,
        failure,
    )

    result_assignment = direct_assignment(qualify_node, "result")
    require(isinstance(result_assignment.value, ast.Dict), failure)

    def dict_value(mapping: ast.Dict, key: str) -> ast.expr | None:
        for candidate_key, candidate_value in zip(
            mapping.keys, mapping.values, strict=True
        ):
            if text(candidate_key) == key:
                return candidate_value
        return None

    require(
        name(dict_value(result_assignment.value, "nested_kernel_regression"))
        == "nested_kernel_regression",
        failure,
    )
    final_guard = qualify_node.body[-2]
    require(
        isinstance(final_guard, ast.If)
        and isinstance(final_guard.test, ast.Compare)
        and name(final_guard.test.left) == "state"
        and len(final_guard.test.ops) == 1
        and isinstance(final_guard.test.ops[0], ast.Eq)
        and len(final_guard.test.comparators) == 1
        and text(final_guard.test.comparators[0]) == "hosted_pending"
        and len(final_guard.body) == 1
        and len(final_guard.orelse) == 1
        and isinstance(qualify_node.body[-1], ast.Return)
        and name(qualify_node.body[-1].value) == "result",
        failure,
    )

    def expanded_result_receipt_key(statement: ast.stmt, key: str) -> bool:
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "result"
            and isinstance(statement.value, ast.Dict)
            and len(statement.value.keys) == 2
            and statement.value.keys[0] is None
            and name(statement.value.values[0]) == "result"
            and text(statement.value.keys[1]) == key
            and isinstance(statement.value.values[1], ast.Dict)
        ):
            return False
        receipt = statement.value.values[1]
        expected_keys = (
            {
                "inventory",
                "leaves",
                "probes",
                "promotion_status",
                "required_next_step",
                "tree_manifest",
            }
            if key == "candidate_receipt"
            else {
                "execution_outcome",
                "immutable_publication_state",
                "nested_same_extraction_transaction",
                "required_next_step",
                "reviewed_pins_equal_fresh_strict_replay",
                "same_run_metadata_promotion_allowed",
                "strict_archive_custody_credit",
                "tree_pre_post_equal",
            }
        )
        return {
            text(candidate) for candidate in receipt.keys if candidate is not None
        } == expected_keys

    require(
        expanded_result_receipt_key(final_guard.body[0], "candidate_receipt")
        and expanded_result_receipt_key(final_guard.orelse[0], "strict_replay_receipt"),
        failure,
    )

    events: list[str] = []
    calls = sorted(
        (node for node in ast.walk(qualify_node) if isinstance(node, ast.Call)),
        key=lambda node: (node.lineno, node.col_offset),
    )
    snapshot_contracts = {
        "immediate pre-nested executable snapshot": (
            "pre_nested_snapshots",
            "produce_pre",
        ),
        "immediate post-nested executable snapshot": (
            "post_nested_snapshots",
            "produce_post",
        ),
        "post-final-tree-scan executable snapshot": (
            "final_snapshots",
            "produce_final",
        ),
    }
    equality_contracts = {
        "probe-to-immediate-pre-nested executable custody": (
            "probe_snapshots",
            "pre_nested_snapshots",
            "equal_probe_pre",
        ),
        "immediate pre/post-nested executable custody": (
            "pre_nested_snapshots",
            "post_nested_snapshots",
            "equal_pre_post",
        ),
        "post-nested-to-final-tree-scan executable custody": (
            "post_nested_snapshots",
            "final_snapshots",
            "equal_post_final",
        ),
    }
    leaf_contracts = {
        "pre-nested executable-to-reviewed-tree binding": (
            "pre_nested_snapshots",
            "leaf_pre",
        ),
        "post-nested executable-to-reviewed-tree binding": (
            "post_nested_snapshots",
            "leaf_post",
        ),
        "post-final-tree-scan executable-to-reviewed-tree binding": (
            "final_snapshots",
            "leaf_final",
        ),
    }
    for call in calls:
        function = call_name(call)
        if function == "probe_toolchain":
            require_direct_with(call)
            require(
                assignment_targets(call) == ("probes", "probe_snapshots")
                and tuple(name(argument) for argument in call.args)
                == ("tool_root", "private_root", "limits")
                and not call.keywords,
                failure,
            )
            events.append("produce_probe")
        elif function == "snapshot_tool_executables" and len(call.args) == 2:
            contract = snapshot_contracts.get(text(call.args[1]))
            if contract is not None:
                require_direct_with(call)
                target, event = contract
                require(
                    name(call.args[0]) == "tool_root"
                    and assignment_targets(call) == (target,)
                    and not call.keywords,
                    failure,
                )
                events.append(event)
        elif (
            function == "require_executable_snapshot_sets_equal" and len(call.args) == 3
        ):
            contract = equality_contracts.get(text(call.args[2]))
            if contract is not None:
                require_direct_with(call)
                left, right, event = contract
                require(
                    (name(call.args[0]), name(call.args[1])) == (left, right)
                    and not call.keywords,
                    failure,
                )
                events.append(event)
        elif (
            function == "require_executable_snapshots_match_tree_leaves"
            and len(call.args) == 4
        ):
            contract = leaf_contracts.get(text(call.args[3]))
            if contract is not None:
                require_direct_with(call)
                snapshots, event = contract
                require(
                    tuple(name(argument) for argument in call.args[:3])
                    == ("tool_root", snapshots, "leaves")
                    and not call.keywords,
                    failure,
                )
                events.append(event)
        elif function == "run_nested_kernel_regression":
            nested_assignment = assignment_node(call)
            strict_branch = parents.get(nested_assignment)
            require(
                nested_assignment is not None
                and isinstance(strict_branch, ast.If)
                and parents.get(strict_branch) is custody_with
                and strict_branch in custody_with.body
                and len(strict_branch.body) == 2
                and strict_branch.body[1] is nested_assignment
                and len(strict_branch.orelse) == 1,
                failure,
            )
            strict_test = strict_branch.test
            require(
                isinstance(strict_test, ast.Compare)
                and name(strict_test.left) == "state"
                and len(strict_test.ops) == 1
                and isinstance(strict_test.ops[0], ast.Eq)
                and len(strict_test.comparators) == 1
                and text(strict_test.comparators[0])
                == "reviewed_pins_strict_replay_required",
                failure,
            )
            probe_requirement = strict_branch.body[0]
            require(
                isinstance(probe_requirement, ast.Expr)
                and isinstance(probe_requirement.value, ast.Call)
                and call_name(probe_requirement.value) == "require"
                and len(probe_requirement.value.args) == 2
                and text(probe_requirement.value.args[1])
                == "toolchain version/platform/diagnostic probes differ from reviewed pins",
                failure,
            )
            probe_condition = probe_requirement.value.args[0]
            require(
                isinstance(probe_condition, ast.Compare)
                and name(probe_condition.left) == "probes"
                and len(probe_condition.ops) == 1
                and isinstance(probe_condition.ops[0], ast.Eq)
                and len(probe_condition.comparators) == 1
                and isinstance(probe_condition.comparators[0], ast.Subscript)
                and name(probe_condition.comparators[0].value) == "lifecycle"
                and text(probe_condition.comparators[0].slice) == "probes",
                failure,
            )
            else_assignment = strict_branch.orelse[0]
            try:
                else_value = (
                    ast.literal_eval(else_assignment.value)
                    if isinstance(else_assignment, ast.Assign)
                    else None
                )
            except (TypeError, ValueError):
                else_value = None
            require(
                isinstance(else_assignment, ast.Assign)
                and len(else_assignment.targets) == 1
                and isinstance(else_assignment.targets[0], ast.Name)
                and else_assignment.targets[0].id == "nested_kernel_regression"
                and else_value
                == {
                    "status": "not_run_pending_asset",
                    "same_extraction_transaction": False,
                    "reason": (
                        "hosted-pending derived executable pins cannot execute "
                        "the strict regression route in an observation run"
                    ),
                },
                failure,
            )
            require(
                assignment_targets(call) == ("nested_kernel_regression",)
                and tuple(name(argument) for argument in call.args)
                == (
                    "tool_root",
                    "private_root",
                    "limits",
                    "key",
                    "nested_checker_snapshot",
                    "metadata",
                    "probes",
                    "pre_nested_snapshots",
                )
                and not call.keywords,
                failure,
            )
            events.append("nested_receives_pre")
        elif function == "scan_extracted_tree" and assignment_targets(call) == (
            "scanned_after",
        ):
            require_direct_with(call)
            require(
                tuple(name(argument) for argument in call.args)
                == ("destination", "limits")
                and not call.keywords,
                failure,
            )
            events.append("produce_scan_after")
        elif (
            function == "require_same_tree"
            and len(call.args) == 3
            and text(call.args[2]) == "across executable probes"
        ):
            require_direct_with(call)
            require(
                (name(call.args[0]), name(call.args[1]))
                == ("scanned_before", "scanned_after")
                and not call.keywords,
                failure,
            )
            events.append("equal_tree_before_after")
        elif (
            function == "require"
            and len(call.args) == 2
            and text(call.args[1])
            == "canonical tree manifest changed across executable probes"
        ):
            require_direct_with(call)
            condition = call.args[0]
            require(
                isinstance(condition, ast.Compare)
                and len(condition.ops) == 1
                and isinstance(condition.ops[0], ast.Eq)
                and len(condition.comparators) == 1
                and name(condition.comparators[0]) == "manifest"
                and isinstance(condition.left, ast.Call)
                and call_name(condition.left) == "tree_manifest_sha256"
                and len(condition.left.args) == 1
                and name(condition.left.args[0]) == "scanned_after"
                and not condition.left.keywords
                and not call.keywords,
                failure,
            )
            events.append("equal_manifest_after")
    expected_events = [
        "produce_probe",
        "produce_pre",
        "equal_probe_pre",
        "leaf_pre",
        "nested_receives_pre",
        "produce_post",
        "equal_pre_post",
        "leaf_post",
        "produce_scan_after",
        "equal_tree_before_after",
        "equal_manifest_after",
        "produce_final",
        "equal_post_final",
        "leaf_final",
    ]
    require(events == expected_events, failure)
    normalized_ast = json.dumps(
        {
            "main": version_independent_ast_projection(main_node),
            "qualify": version_independent_ast_projection(qualify_node),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    require(
        hashlib.sha256(normalized_ast).hexdigest()
        == EXPECTED_PRODUCTION_ROUTE_AST_SHA256,
        "production custody route normalized AST closure drifted",
    )
    normalized_module_ast = json.dumps(
        version_independent_ast_projection(tree),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    require(
        hashlib.sha256(normalized_module_ast).hexdigest()
        == EXPECTED_CHECKER_MODULE_AST_SHA256,
        "production checker normalized module AST closure drifted",
    )
    return {
        "name": "production_qualify_exact_executable_custody_def_use_order_graph",
        "accepted": True,
        "exact_events": events,
        "normalized_module_ast_sha256": EXPECTED_CHECKER_MODULE_AST_SHA256,
        "normalized_ast_sha256": EXPECTED_PRODUCTION_ROUTE_AST_SHA256,
        "closure_scope": "defense_in_depth_not_formal_proof_or_authentication",
        "coordinated_reseal_resistance": "requires_external_review_of_exact_source",
        "real_archive_access": "none",
    }


def production_qualify_wiring_controls() -> tuple[
    list[dict[str, object]], dict[str, object]
]:
    """Kill one-at-a-time source mutants without invoking checker hash gates."""

    positive = validate_production_qualify_executable_wiring(CHECKER_SOURCE)
    source = CHECKER_SOURCE.decode("utf-8")

    def mutation(old: str, new: str) -> bytes:
        require(old != new and source.count(old) == 1, "wiring mutant anchor drifted")
        mutated = source.replace(old, new, 1)
        require(mutated != source, "wiring mutant was not independently changed")
        return mutated.encode("utf-8")

    base_cases = (
        (
            "qualify_wiring_delete_probe_producer",
            "probes, probe_snapshots = probe_toolchain(",
            "probes, probe_snapshots = bypassed_probe_toolchain(",
            "deletion",
        ),
        (
            "qualify_wiring_delete_pre_snapshot_producer",
            'pre_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate pre-nested executable snapshot"',
            'pre_nested_snapshots = bypassed_snapshot_tool_executables(\n            tool_root, "immediate pre-nested executable snapshot"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_probe_pre_equality",
            'require_executable_snapshot_sets_equal(\n            probe_snapshots,\n            pre_nested_snapshots,\n            "probe-to-immediate-pre-nested executable custody"',
            'bypassed_executable_snapshot_sets_equal(\n            probe_snapshots,\n            pre_nested_snapshots,\n            "probe-to-immediate-pre-nested executable custody"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_pre_leaf_binding",
            'require_executable_snapshots_match_tree_leaves(\n            tool_root,\n            pre_nested_snapshots,\n            leaves,\n            "pre-nested executable-to-reviewed-tree binding"',
            'bypassed_executable_snapshots_match_tree_leaves(\n            tool_root,\n            pre_nested_snapshots,\n            leaves,\n            "pre-nested executable-to-reviewed-tree binding"',
            "deletion",
        ),
        (
            "qualify_wiring_nested_argument_substituted_probe",
            "                probes,\n                pre_nested_snapshots,\n            )",
            "                probes,\n                probe_snapshots,\n            )",
            "substitution",
        ),
        (
            "qualify_wiring_delete_nested_execution",
            "nested_kernel_regression = run_nested_kernel_regression(",
            "nested_kernel_regression = bypassed_nested_kernel_regression(",
            "deletion",
        ),
        (
            "qualify_wiring_delete_post_snapshot_producer",
            'post_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            'post_nested_snapshots = bypassed_snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_pre_post_equality",
            'require_executable_snapshot_sets_equal(\n            pre_nested_snapshots,\n            post_nested_snapshots,\n            "immediate pre/post-nested executable custody"',
            'bypassed_executable_snapshot_sets_equal(\n            pre_nested_snapshots,\n            post_nested_snapshots,\n            "immediate pre/post-nested executable custody"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_post_leaf_binding",
            'require_executable_snapshots_match_tree_leaves(\n            tool_root,\n            post_nested_snapshots,\n            leaves,\n            "post-nested executable-to-reviewed-tree binding"',
            'bypassed_executable_snapshots_match_tree_leaves(\n            tool_root,\n            post_nested_snapshots,\n            leaves,\n            "post-nested executable-to-reviewed-tree binding"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_post_tree_scan",
            "scanned_after = scan_extracted_tree(destination, limits)",
            "scanned_after = bypassed_scan_extracted_tree(destination, limits)",
            "deletion",
        ),
        (
            "qualify_wiring_delete_tree_equality",
            'require_same_tree(scanned_before, scanned_after, "across executable probes")',
            'bypassed_same_tree(scanned_before, scanned_after, "across executable probes")',
            "deletion",
        ),
        (
            "qualify_wiring_manifest_uses_pre_scan",
            "tree_manifest_sha256(scanned_after) == manifest",
            "tree_manifest_sha256(scanned_before) == manifest",
            "substitution",
        ),
        (
            "qualify_wiring_delete_post_scan_manifest_equality",
            """        require(
            tree_manifest_sha256(scanned_after) == manifest,
            "canonical tree manifest changed across executable probes",
        )""",
            """        bypassed_require(
            tree_manifest_sha256(scanned_after) == manifest,
            "canonical tree manifest changed across executable probes",
        )""",
            "deletion",
        ),
        (
            "qualify_wiring_delete_final_snapshot_producer",
            'final_snapshots = snapshot_tool_executables(\n            tool_root, "post-final-tree-scan executable snapshot"',
            'final_snapshots = bypassed_snapshot_tool_executables(\n            tool_root, "post-final-tree-scan executable snapshot"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_post_final_equality",
            'require_executable_snapshot_sets_equal(\n            post_nested_snapshots,\n            final_snapshots,\n            "post-nested-to-final-tree-scan executable custody"',
            'bypassed_executable_snapshot_sets_equal(\n            post_nested_snapshots,\n            final_snapshots,\n            "post-nested-to-final-tree-scan executable custody"',
            "deletion",
        ),
        (
            "qualify_wiring_delete_final_leaf_binding",
            'require_executable_snapshots_match_tree_leaves(\n            tool_root,\n            final_snapshots,\n            leaves,\n            "post-final-tree-scan executable-to-reviewed-tree binding"',
            'bypassed_executable_snapshots_match_tree_leaves(\n            tool_root,\n            final_snapshots,\n            leaves,\n            "post-final-tree-scan executable-to-reviewed-tree binding"',
            "deletion",
        ),
        (
            "qualify_wiring_probe_pre_equality_reversed",
            '            probe_snapshots,\n            pre_nested_snapshots,\n            "probe-to-immediate-pre-nested executable custody"',
            '            pre_nested_snapshots,\n            probe_snapshots,\n            "probe-to-immediate-pre-nested executable custody"',
            "substitution",
        ),
        (
            "qualify_wiring_pre_leaf_uses_probe_snapshot",
            '            pre_nested_snapshots,\n            leaves,\n            "pre-nested executable-to-reviewed-tree binding"',
            '            probe_snapshots,\n            leaves,\n            "pre-nested executable-to-reviewed-tree binding"',
            "substitution",
        ),
        (
            "qualify_wiring_pre_post_equality_reversed",
            '            pre_nested_snapshots,\n            post_nested_snapshots,\n            "immediate pre/post-nested executable custody"',
            '            post_nested_snapshots,\n            pre_nested_snapshots,\n            "immediate pre/post-nested executable custody"',
            "substitution",
        ),
        (
            "qualify_wiring_post_leaf_uses_pre_snapshot",
            '            post_nested_snapshots,\n            leaves,\n            "post-nested executable-to-reviewed-tree binding"',
            '            pre_nested_snapshots,\n            leaves,\n            "post-nested executable-to-reviewed-tree binding"',
            "substitution",
        ),
        (
            "qualify_wiring_tree_equality_reversed",
            'require_same_tree(scanned_before, scanned_after, "across executable probes")',
            'require_same_tree(scanned_after, scanned_before, "across executable probes")',
            "substitution",
        ),
        (
            "qualify_wiring_post_final_equality_reversed",
            '            post_nested_snapshots,\n            final_snapshots,\n            "post-nested-to-final-tree-scan executable custody"',
            '            final_snapshots,\n            post_nested_snapshots,\n            "post-nested-to-final-tree-scan executable custody"',
            "substitution",
        ),
        (
            "qualify_wiring_final_leaf_uses_post_snapshot",
            '            final_snapshots,\n            leaves,\n            "post-final-tree-scan executable-to-reviewed-tree binding"',
            '            post_nested_snapshots,\n            leaves,\n            "post-final-tree-scan executable-to-reviewed-tree binding"',
            "substitution",
        ),
        (
            "qualify_wiring_pre_equality_leaf_order_swapped",
            """        require_executable_snapshot_sets_equal(
            probe_snapshots,
            pre_nested_snapshots,
            "probe-to-immediate-pre-nested executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            pre_nested_snapshots,
            leaves,
            "pre-nested executable-to-reviewed-tree binding",
        )""",
            """        require_executable_snapshots_match_tree_leaves(
            tool_root,
            pre_nested_snapshots,
            leaves,
            "pre-nested executable-to-reviewed-tree binding",
        )
        require_executable_snapshot_sets_equal(
            probe_snapshots,
            pre_nested_snapshots,
            "probe-to-immediate-pre-nested executable custody",
        )""",
            "reorder",
        ),
        (
            "qualify_wiring_post_equality_leaf_order_swapped",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,
            "immediate pre/post-nested executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            post_nested_snapshots,
            leaves,
            "post-nested executable-to-reviewed-tree binding",
        )""",
            """        require_executable_snapshots_match_tree_leaves(
            tool_root,
            post_nested_snapshots,
            leaves,
            "post-nested executable-to-reviewed-tree binding",
        )
        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,
            "immediate pre/post-nested executable custody",
        )""",
            "reorder",
        ),
        (
            "qualify_wiring_final_equality_leaf_order_swapped",
            """        require_executable_snapshot_sets_equal(
            post_nested_snapshots,
            final_snapshots,
            "post-nested-to-final-tree-scan executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            final_snapshots,
            leaves,
            "post-final-tree-scan executable-to-reviewed-tree binding",
        )""",
            """        require_executable_snapshots_match_tree_leaves(
            tool_root,
            final_snapshots,
            leaves,
            "post-final-tree-scan executable-to-reviewed-tree binding",
        )
        require_executable_snapshot_sets_equal(
            post_nested_snapshots,
            final_snapshots,
            "post-nested-to-final-tree-scan executable custody",
        )""",
            "reorder",
        ),
    )
    control_flow_cases = (
        (
            "qualify_wiring_strict_guard_forced_false",
            '        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            '        if False and state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            "control_flow",
        ),
        (
            "qualify_wiring_strict_guard_negated",
            '        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            '        if state != "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            "control_flow",
        ),
        (
            "qualify_wiring_else_result_target_substituted",
            '        else:\n            nested_kernel_regression = {\n                "status": "not_run_pending_asset",',
            '        else:\n            bypassed_nested_kernel_regression = {\n                "status": "not_run_pending_asset",',
            "control_flow",
        ),
        (
            "qualify_wiring_else_result_semantics_substituted",
            '        else:\n            nested_kernel_regression = {\n                "status": "not_run_pending_asset",',
            '        else:\n            nested_kernel_regression = {\n                "status": "forged_executed",',
            "control_flow",
        ),
        (
            "qualify_wiring_final_strict_replay_guard_negated",
            '    strict_replay = state == "reviewed_pins_strict_replay_required"',
            '    strict_replay = state != "reviewed_pins_strict_replay_required"',
            "control_flow",
        ),
        (
            "qualify_wiring_final_hosted_pending_guard_forced_false",
            '    if state == "hosted_pending":\n        result = {',
            "    if False:\n        result = {",
            "control_flow",
        ),
        (
            "qualify_wiring_early_return_before_strict_branch",
            '        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            '        if state == "reviewed_pins_strict_replay_required":\n            return {}\n        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            "control_flow",
        ),
        (
            "qualify_wiring_pre_post_equality_wrapped_in_dead_branch",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,
            "immediate pre/post-nested executable custody",
        )""",
            """        if False:
            require_executable_snapshot_sets_equal(
                pre_nested_snapshots,
                post_nested_snapshots,
                "immediate pre/post-nested executable custody",
            )""",
            "control_flow",
        ),
        (
            "qualify_wiring_pre_post_equality_wrapped_in_swallowing_try",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,
            "immediate pre/post-nested executable custody",
        )""",
            """        try:
            require_executable_snapshot_sets_equal(
                pre_nested_snapshots,
                post_nested_snapshots,
                "immediate pre/post-nested executable custody",
            )
        except Exception:
            pass""",
            "control_flow",
        ),
    )
    rebind_cases = (
        (
            "qualify_wiring_probe_snapshot_rebound",
            '        pre_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate pre-nested executable snapshot"',
            '        probe_snapshots = {}\n        pre_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate pre-nested executable snapshot"',
            "rebind",
        ),
        (
            "qualify_wiring_pre_snapshot_rebound_to_probe",
            """        require_executable_snapshot_sets_equal(
            probe_snapshots,""",
            """        pre_nested_snapshots = probe_snapshots
        require_executable_snapshot_sets_equal(
            probe_snapshots,""",
            "rebind",
        ),
        (
            "qualify_wiring_post_snapshot_rebound_to_pre",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            """        post_nested_snapshots = pre_nested_snapshots
        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            "rebind",
        ),
        (
            "qualify_wiring_final_snapshot_rebound_to_post",
            """        require_executable_snapshot_sets_equal(
            post_nested_snapshots,
            final_snapshots,""",
            """        final_snapshots = post_nested_snapshots
        require_executable_snapshot_sets_equal(
            post_nested_snapshots,
            final_snapshots,""",
            "rebind",
        ),
        (
            "qualify_wiring_scanned_after_rebound_to_before",
            '        require_same_tree(scanned_before, scanned_after, "across executable probes")',
            '        scanned_after = scanned_before\n        require_same_tree(scanned_before, scanned_after, "across executable probes")',
            "rebind",
        ),
        (
            "qualify_wiring_manifest_rebound_after_scan",
            """        require(
            tree_manifest_sha256(scanned_after) == manifest,""",
            """        manifest = tree_manifest_sha256(scanned_after)
        require(
            tree_manifest_sha256(scanned_after) == manifest,""",
            "rebind",
        ),
        (
            "qualify_wiring_tool_root_rebound_before_probe",
            "        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)",
            "        tool_root = destination\n        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)",
            "rebind",
        ),
        (
            "qualify_wiring_leaves_rebound_before_probe",
            "        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)",
            "        leaves = {}\n        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)",
            "rebind",
        ),
        (
            "qualify_wiring_probes_rebound_before_strict_branch",
            '        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            '        probes = lifecycle["probes"]\n        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            "rebind",
        ),
        (
            "qualify_wiring_nested_result_rebound_after_branch",
            '        post_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            '        nested_kernel_regression = {"status": "forged"}\n        post_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            "rebind",
        ),
        (
            "qualify_wiring_state_rebound_after_nested_branch",
            '        post_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            '        state = "hosted_pending"\n        post_nested_snapshots = snapshot_tool_executables(\n            tool_root, "immediate post-nested executable snapshot"',
            "rebind",
        ),
        (
            "qualify_wiring_pre_snapshot_mutated_in_place",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            """        pre_nested_snapshots.clear()
        pre_nested_snapshots.update(post_nested_snapshots)
        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            "in_place_mutation",
        ),
        (
            "qualify_wiring_post_snapshot_leaf_mutated_in_place",
            """        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            """        post_nested_snapshots["lean"] = pre_nested_snapshots["lean"]
        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,""",
            "in_place_mutation",
        ),
        (
            "qualify_wiring_reviewed_probes_mutated_in_place",
            '        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            '        lifecycle["probes"] = probes\n        if state == "reviewed_pins_strict_replay_required":\n            require(\n                probes == lifecycle["probes"],',
            "in_place_mutation",
        ),
        (
            "qualify_wiring_scanned_before_rebound_after_post_scan",
            '        require_same_tree(scanned_before, scanned_after, "across executable probes")',
            '        scanned_before = scanned_after\n        require_same_tree(scanned_before, scanned_after, "across executable probes")',
            "rebind",
        ),
        (
            "qualify_wiring_scanned_before_producer_substituted",
            "scanned_before = scan_extracted_tree(destination, limits)",
            "scanned_before = []",
            "producer_substitution",
        ),
        (
            "qualify_wiring_manifest_producer_substituted",
            "manifest = tree_manifest_sha256(scanned_before)",
            'manifest = "0" * 64',
            "producer_substitution",
        ),
        (
            "qualify_wiring_leaves_producer_substituted",
            'leaves = leaf_facts(scanned_before, expected_archive["root"])',
            'leaves = lifecycle["leaves"]',
            "producer_substitution",
        ),
        (
            "qualify_wiring_tool_root_producer_substituted",
            'tool_root = destination / expected_archive["root"]',
            "tool_root = destination",
            "producer_substitution",
        ),
        (
            "qualify_wiring_nested_result_output_substituted",
            '"nested_kernel_regression": nested_kernel_regression,',
            '"nested_kernel_regression": {"status": "forged"},',
            "producer_substitution",
        ),
    )
    shadow_anchor = "        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)"
    shadow_cases = tuple(
        (
            f"qualify_wiring_local_shadow_{callee}",
            shadow_anchor,
            f"        {callee} = lambda *_args: None\n" + shadow_anchor,
            "callee_shadow",
        )
        for callee in (
            "leaf_facts",
            "probe_toolchain",
            "require",
            "require_executable_snapshot_sets_equal",
            "require_executable_snapshots_match_tree_leaves",
            "require_same_tree",
            "run_nested_kernel_regression",
            "scan_extracted_tree",
            "snapshot_tool_executables",
            "tree_manifest_sha256",
        )
    ) + (
        (
            "main_route_direct_global_equality_shadow",
            "        result = qualify(",
            "        global require_executable_snapshot_sets_equal\n"
            "        require_executable_snapshot_sets_equal = lambda *_args: None\n"
            "        result = qualify(",
            "main_route_shadow",
        ),
        (
            "main_route_indirect_globals_equality_shadow",
            "        result = qualify(",
            '        globals()["require_executable_snapshot_sets_equal"] = lambda *_args: None\n'
            "        result = qualify(",
            "main_route_shadow",
        ),
        (
            "main_route_local_qualify_shadow",
            "        result = qualify(",
            "        qualify = lambda *_args: {}\n        result = qualify(",
            "main_route_shadow",
        ),
        (
            "qualify_wiring_indirect_globals_shadow",
            shadow_anchor,
            '        globals()["require_executable_snapshot_sets_equal"] = lambda *_args: None\n'
            + shadow_anchor,
            "callee_shadow",
        ),
        (
            "qualify_wiring_global_shadow_declaration",
            '    key = asset["key"]\n    lifecycle = asset["custody_lifecycle"]',
            '    global require_executable_snapshot_sets_equal\n    key = asset["key"]\n    lifecycle = asset["custody_lifecycle"]',
            "callee_shadow",
        ),
        (
            "module_route_direct_equality_shadow",
            "def main(argv: list[str] | None = None) -> int:",
            "require_executable_snapshot_sets_equal = lambda *_args: None\n\n"
            "def main(argv: list[str] | None = None) -> int:",
            "module_route_shadow",
        ),
        (
            "module_route_indirect_globals_equality_shadow",
            "def main(argv: list[str] | None = None) -> int:",
            'globals()["require_executable_snapshot_sets_equal"] = lambda *_args: None\n\n'
            "def main(argv: list[str] | None = None) -> int:",
            "module_route_shadow",
        ),
        (
            "module_route_delete_equality_helper",
            "def main(argv: list[str] | None = None) -> int:",
            "del require_executable_snapshot_sets_equal\n\n"
            "def main(argv: list[str] | None = None) -> int:",
            "module_route_shadow",
        ),
        (
            "module_route_import_alias_equality_shadow",
            "def main(argv: list[str] | None = None) -> int:",
            "from builtins import len as require_executable_snapshot_sets_equal\n\n"
            "def main(argv: list[str] | None = None) -> int:",
            "module_route_shadow",
        ),
    )
    cases = base_cases + control_flow_cases + rebind_cases + shadow_cases
    controls: list[dict[str, object]] = []
    for name, old, new, mutation_class in cases:
        control = expect_failure(
            name,
            lambda old=old, new=new: validate_production_qualify_executable_wiring(
                mutation(old, new)
            ),
            "production qualify executable custody wiring drifted",
            exception_type=SelfTestError,
        )
        control["source_mutation_class"] = mutation_class
        control["checker_hash_or_load_gate_used"] = False
        controls.append(control)
    controls.append(
        expect_failure(
            "custody_route_normalized_ast_closure_extra_statement",
            lambda: validate_production_qualify_executable_wiring(
                mutation(
                    '    strict_replay = state == "reviewed_pins_strict_replay_required"',
                    '    pass\n    strict_replay = state == "reviewed_pins_strict_replay_required"',
                )
            ),
            "production custody route normalized AST closure drifted",
            exception_type=SelfTestError,
        )
    )
    controls.append(
        expect_failure(
            "checker_module_normalized_ast_closure_extra_statement",
            lambda: validate_production_qualify_executable_wiring(
                mutation(
                    "def main(argv: list[str] | None = None) -> int:",
                    "pass\n\ndef main(argv: list[str] | None = None) -> int:",
                )
            ),
            "production checker normalized module AST closure drifted",
            exception_type=SelfTestError,
        )
    )
    return controls, positive


def nested_kernel_regression_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    nested_source = exact_source(
        checker.KERNEL_REGRESSION_CHECKER_PATH,
        METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
        "nested checker boundary authority",
    )
    nested_tree = ast.parse(
        nested_source, filename=os.fspath(checker.KERNEL_REGRESSION_CHECKER_PATH)
    )
    boundary_candidates = [
        node.value
        for node in ast.walk(nested_tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("This is exact-source regression evidence")
    ]
    require(
        len(boundary_candidates) == 1,
        "nested checker exact boundary literal inventory drifted",
    )
    production_boundary = boundary_candidates[0]
    require(
        hashlib.sha256(production_boundary.encode("utf-8")).hexdigest()
        == checker.EXPECTED_NESTED_BOUNDARY_SHA256,
        "nested checker exact boundary digest drifted",
    )
    tool_root = Path(
        "/private/tmp/pid-rs-lean-toolchain-custody-self-test/"
        "lean-4.32.2-darwin_aarch64"
    )

    def executable_evidence(role: str, marker: str, size: int) -> dict[str, object]:
        path = tool_root / "bin" / role
        return {
            "launch_path": os.fspath(path),
            "canonical_path": os.fspath(path),
            "bytes": size,
            "sha256": marker * 64,
            "identity": {
                "device": 1,
                "inode": size,
                "mode": stat.S_IFREG | 0o755,
                "permissions": "0o755",
                "links": 1,
                "size": size,
                "modified_ns": 1,
                "changed_ns": 1,
            },
        }

    def expected_mismatch_diagnostic(
        role: str,
        observed: dict[str, object],
        expected: dict[str, object],
        paths: list[str],
    ) -> str:
        return (
            f"{role} disagrees with the outer live executable snapshot at fields: "
            + json.dumps(
                paths,
                sort_keys=False,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "; observed_evidence_sha256="
            + hashlib.sha256(checker.canonical_json_bytes(observed)).hexdigest()
            + "; expected_evidence_sha256="
            + hashlib.sha256(checker.canonical_json_bytes(expected)).hexdigest()
        )

    def expect_structural_evidence_failure(
        name: str,
        observed: object,
        expected: dict[str, object],
        role: str,
        *,
        forbidden: tuple[str, ...] = (),
    ) -> dict[str, object]:
        try:
            checker.validate_nested_executable_evidence(
                observed,
                tool_root / "bin/lean",
                expected,
                role,
            )
        except checker.CustodyError as error:
            diagnostic = str(error)
            encoded = diagnostic.encode("ascii", errors="strict")
            require(
                type(error) is checker.CustodyError
                and diagnostic
                in {
                    f"{role} schema shape drifted",
                    "nested executable evidence role drifted",
                }
                and len(encoded) <= checker.MISMATCH_DIAGNOSTIC_BYTES_MAX,
                f"{name} did not use the fixed structural diagnostic",
            )
            require(
                all(token not in diagnostic for token in forbidden),
                f"{name} disclosed an observed field name or value",
            )
            return {
                "name": name,
                "rejected": True,
                "diagnostic_bytes_max": checker.MISMATCH_DIAGNOSTIC_BYTES_MAX,
                "generic_structural_diagnostic": True,
                "canonical_evidence_digests_reported": False,
                "raw_observed_names_or_values_reported": False,
            }
        raise SelfTestError(f"negative control survived: {name}")

    lean_evidence = executable_evidence("lean", "1", 1_024)
    lake_evidence = executable_evidence("lake", "2", 768)
    leanchecker_evidence = executable_evidence("leanchecker", "3", 896)
    expected_executable_evidence = {
        "lean": lean_evidence,
        "lake": lake_evidence,
        "leanchecker": leanchecker_evidence,
    }
    helper_identity = checker.FileIdentity(
        device=1,
        inode=2,
        mode=stat.S_IFREG | 0o755,
        links=1,
        size=4,
        modified_ns=3,
        changed_ns=4,
    )
    helper_snapshot = checker.ExecutableSnapshot(
        launch_path=tool_root / "bin" / "helper",
        launch_identity=helper_identity,
        launch_target=None,
        canonical_path=tool_root / "bin" / "helper",
        canonical_identity=helper_identity,
        data=b"lean",
        sha256=hashlib.sha256(b"lean").hexdigest(),
    )
    helper_evidence = checker.nested_executable_evidence_from_outer(helper_snapshot)
    require(
        helper_evidence["bytes"] == 4
        and helper_evidence["sha256"] == hashlib.sha256(b"lean").hexdigest()
        and helper_evidence["identity"]["permissions"] == "0o755",
        "outer executable-snapshot evidence projection drifted",
    )
    valid: dict[str, object] = {
        "schema": checker.KERNEL_REGRESSION_RESULT_SCHEMA,
        "status": "regression_checks_passed",
        "scope_boundary": copy.deepcopy(checker.EXPECTED_NESTED_SCOPE_BOUNDARY),
        "checker_source_sha256": METADATA["checker_binding"]["nested_checker_binding"][
            "sha256"
        ],
        "active_scientific_project_inputs_consumed": [],
        "active_scientific_project_toolchain_migration_claimed": False,
        "lean": {
            "version": "4.32.2",
            "platform": "aarch64-apple-darwin",
            "commit": "f3b06c705e6c85f5314019d5d3baab0fec5b580c",
            "build": "Release",
            "toolchain": "leanprover/lean4:v4.32.2",
            "post_execution_identity_equal": True,
        },
        "lake": {
            "version": "5.0.0-src+f3b06c7",
            "lean_version": "4.32.2",
            "post_execution_identity_equal": True,
        },
        "trust_zero_semantics": {
            "argument": "--trust=0",
            "help_meaning": (
                "do_not_trust_any_macro_and_type_check_all_imported_modules"
            ),
            "no_macros_trusted": True,
            "all_imported_modules_typechecked": True,
            "selected_lean_implementation_and_runtime_remain_trusted": True,
            "zero_tcb": False,
        },
        "leanchecker_fresh_semantics": {
            "argument": "--fresh",
            "external_verifier": False,
            "fresh_replay_rechecks_source_elaboration_or_guarded_commands": False,
            "full_fixture_bad_declaration_source_present": True,
            "full_fixture_bad_thmdecl_reached_or_attempted": False,
            "full_fixture_post_failure_unknown_bad_reference_guard": True,
            "guard_msgs_rerun": False,
            "initial_environment": "mkEmptyEnvironment",
            "independent_kernel_implementation": False,
            "ordinary_olean_count": 3,
            "ordinary_olean_files_in_mode_0700_private_temporary_tree": True,
            "complete_declaration_inventory_claimed": False,
            "selected_emitted_olean_name_probe_only": True,
            "residual_axiom_shaped_E_present_in_each_selected_target_olean": True,
            "rejected_constructor_E_mk_absent_in_each_selected_target_olean": True,
            "unreached_bad_declaration_absent_in_full_selected_target_olean": True,
            "minimum_fixture_bad_source_reference_probe_or_absence_claimed": False,
            "replayed_content": "imported_and_defined_constants",
            "same_executable_leaf_as_source_elaboration": False,
            "same_process_as_source_elaboration": False,
            "selected_release_implementation_and_runtime_remain_trusted": True,
            "source_reelaboration": False,
        },
        "execution_route": {
            "direct_toolchain_root": os.fspath(tool_root),
            "ambient_home_logname_user_retained": False,
            "reviewed_pin_platform_key": "darwin-aarch64",
            "metadata_lifecycle_state": "reviewed_pins_strict_replay_required",
            "toolchain_metadata_sha256": EXPECTED_METADATA_SHA256,
            "toolchain_metadata_policy_projection_sha256": (
                checker.EXPECTED_METADATA_POLICY_SHA256
            ),
            "nested_checker_self_binding_equal": True,
            "archive_derivation_claimed_by_this_checker": False,
            "required_archive_derivation_route": (
                "nested_same-transaction_execution_by_"
                "lean-toolchain-release-custody-check/v5"
            ),
            "elan_invoked": False,
            "direct_lean_pre_execution": lean_evidence,
            "direct_lean_post_execution": lean_evidence,
            "direct_lake_pre_execution": lake_evidence,
            "direct_lake_post_execution": lake_evidence,
            "direct_leanchecker_pre_execution": leanchecker_evidence,
            "direct_leanchecker_post_execution": leanchecker_evidence,
            "absolute_launch_and_source_paths": True,
            "source_compile_arguments": [
                "--trust=0",
                "-o",
                "<absolute-private-olean>",
                "<absolute-private-query>",
            ],
            "unguarded_source_arguments": ["--trust=0", "<absolute-query>"],
            "leanchecker_fresh_environment_replay_arguments": [
                "--fresh",
                "<private-module>",
            ],
            "leanchecker_fresh_environment_replay_timeout_seconds": 900,
            "direct_tool_leaves_bound": ["lean", "lake", "leanchecker"],
            "direct_tool_leaf_bytes_equal_before_and_after": True,
            "version_commit_build_platform_equal_before_and_after": True,
            "immediate_pre_post_source_and_tool_endpoint_checks": True,
            "shared_outer_process_group": True,
            "inner_children_start_new_sessions": False,
            "isolated_child_group_cleanup_after_every_outcome": False,
            "isolated_child_group_cleanup_signal_policy": ["TERM", "KILL"],
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log": True,
            "process_group_cleanup_bounds_milliseconds": {
                "term_grace": 500,
                "kill_grace": 2000,
                "absence_poll_interval": 10,
                "direct_child_reap_timeout": 2000,
            },
            "isolated_child_group_absence_checked": False,
            "non_child_descendants_reaped_by_this_checker": False,
            "process_group_observation_atomic": False,
            "process_group_reuse_excluded": False,
            "descendant_group_or_session_changes_continuously_observed": False,
            "shared_group_signal_from_nested_checker": False,
            "shared_group_cleanup_owned_by_outer_supervisor": True,
            "private_temporary_directory_pre_post_identity_equal": True,
            "private_temporary_directory_modes": {
                "temporary_root": "0700",
                "query_root": "0700",
                "olean_root": "0700",
            },
            "private_lean_path_only_for_leanchecker_fresh_environment_replay": True,
            "per_child_private_home_and_tmp": True,
            "per_child_private_environment_directory_modes": {
                "temporary_root": "0700",
                "home": "0700",
                "tmp": "0700",
            },
            "version_output_is_identity_evidence_not_authenticity": True,
            "fixed_child_path": os.defpath,
            "leanchecker_fresh_environment_child_path_prefix": os.fspath(
                tool_root / "bin"
            ),
            "child_environment_removed_prefixes": (
                checker.EXPECTED_NESTED_ENVIRONMENT_PREFIXES_TO_REMOVE
            ),
            "child_environment_removed_keys": (
                checker.EXPECTED_NESTED_ENVIRONMENT_KEYS_TO_REMOVE
            ),
        },
        "origin_sha256": checker.EXPECTED_KERNEL_REGRESSION_ORIGIN_SHA256,
        "fixtures": [
            {
                "name": "issue_14576.lean",
                "sha256": (
                    "0aaec9548df29266061467e37026935391a05bf6142fd027915f40c687a889e2"
                ),
                "bytes": 2460,
                "trust": 0,
                "guarded_invalid_projection": True,
                "eof_canary_observed": True,
                "module": "Issue14576Full",
                "derived_query_bytes": 2584,
                "derived_query_sha256": (
                    "f9ecdb91eb99b11e358d2c3cff32059ca14f7fd65a0bfd9bc7f88abf1fdaf841"
                ),
                "olean_bytes": 1024,
                "olean_sha256": "a" * 64,
                "target_olean_inventory_probe": {
                    "claim_scope": "selected_names_in_this_emitted_olean_only",
                    "complete_declaration_inventory_claimed": False,
                    "bracketing_lookup_controls": {
                        "present": "PidRsTargetOleanLookupPositive",
                        "absent": "PidRsTargetOleanLookupNegative",
                    },
                    "selected_declarations": [
                        {
                            "symbol": "E",
                            "status": "present",
                            "rendering": "axiom E : sorry",
                            "source_role": (
                                "residual_axiom_shaped_declaration_from_failed_"
                                "inductive_route"
                            ),
                        },
                        {
                            "symbol": "E.mk",
                            "status": "absent",
                            "rendering": "Unknown constant `E.mk`",
                            "source_role": "rejected_constructor_attempt",
                        },
                        {
                            "declaration_source_present": True,
                            "post_failure_unknown_identifier_reference_guard": True,
                            "symbol": "bad",
                            "status": "absent",
                            "rendering": "Unknown constant `bad`",
                            "source_role": "unreached_downstream_declaration",
                            "thmdecl_reached_or_attempted": False,
                        },
                    ],
                    "source_bytes": 621,
                    "source_sha256": (
                        "9e62ee47c67457f21ad6cdab44c69fec42b0a7a7b9ad347416294b69edf4f033"
                    ),
                    "exit_code": 0,
                    "eof_canary_observed": True,
                    "target_olean_imported": True,
                },
                "leanchecker_fresh_environment_replayed": True,
            },
            {
                "name": "issue_14576_min.lean",
                "sha256": (
                    "77769c1ce88649f56bf1fc8a0ae89fafdef25eae17b744fc7f28cb7b9519cbb5"
                ),
                "bytes": 804,
                "trust": 0,
                "guarded_invalid_projection": True,
                "eof_canary_observed": True,
                "module": "Issue14576Min",
                "derived_query_bytes": 932,
                "derived_query_sha256": (
                    "83abd16bdd236ae9f4fdcfa0d975ddcd0dc4f24681f5eba3f31ad6c95302a927"
                ),
                "olean_bytes": 768,
                "olean_sha256": "b" * 64,
                "target_olean_inventory_probe": {
                    "claim_scope": "selected_names_in_this_emitted_olean_only",
                    "complete_declaration_inventory_claimed": False,
                    "bracketing_lookup_controls": {
                        "present": "PidRsTargetOleanLookupPositive",
                        "absent": "PidRsTargetOleanLookupNegative",
                    },
                    "selected_declarations": [
                        {
                            "symbol": "E",
                            "status": "present",
                            "rendering": "axiom E : sorry",
                            "source_role": (
                                "residual_axiom_shaped_declaration_from_failed_"
                                "inductive_route"
                            ),
                        },
                        {
                            "symbol": "E.mk",
                            "status": "absent",
                            "rendering": "Unknown constant `E.mk`",
                            "source_role": "rejected_constructor_attempt",
                        },
                    ],
                    "source_bytes": 560,
                    "source_sha256": (
                        "7804185ed6b01627e02cfdd5b03ac36a19cd0d4f4411373dd64f97d972b8f47a"
                    ),
                    "exit_code": 0,
                    "eof_canary_observed": True,
                    "target_olean_imported": True,
                },
                "leanchecker_fresh_environment_replayed": True,
            },
        ],
        "trust_zero_olean_compilations": 3,
        "leanchecker_fresh_environment_replays": 3,
        "leanchecker_fresh_environment_replayed_modules": [
            "Issue14576Full",
            "Issue14576Min",
            "Issue14576MinBenign",
        ],
        "leanchecker_fresh_environment_replay_measurements": [
            {
                "module": "Issue14576Full",
                "duration_monotonic_ns": 1,
                "timeout_seconds": 900,
            },
            {
                "module": "Issue14576Min",
                "duration_monotonic_ns": 2,
                "timeout_seconds": 900,
            },
            {
                "module": "Issue14576MinBenign",
                "duration_monotonic_ns": 3,
                "timeout_seconds": 900,
            },
        ],
        "leanchecker_fresh_environment_replay_total_monotonic_ns": 6,
        "leanchecker_fresh_environment_replay_max_monotonic_ns": 3,
        "nested_timing_contract": {
            "inner_per_replay_timeout_seconds": 900,
            "replay_count": 3,
            "non_replay_lean_child_timeout_seconds": 120,
            "non_replay_lean_child_count": 6,
            "identity_child_timeout_seconds": 60,
            "identity_child_count": 4,
            "orchestration_headroom_seconds": 240,
            "declared_non_replay_margin_seconds": 1200,
            "required_outer_timeout_seconds": 3900,
            "derivation": (
                "inner_per_replay_timeout_seconds*replay_count+"
                "non_replay_lean_child_timeout_seconds*non_replay_lean_child_count+"
                "identity_child_timeout_seconds*identity_child_count+"
                "orchestration_headroom_seconds"
            ),
            "environmental_premise": (
                "Wall duration depends on host load, scheduler behavior, dynamic loading, "
                "filesystem state, and hardware; the finite limits fail closed and are not "
                "performance guarantees."
            ),
        },
        "benign_near_neighbor": {
            "source_fixture": "issue_14576_min.lean",
            "source_fixture_sha256": (
                "77769c1ce88649f56bf1fc8a0ae89fafdef25eae17b744fc7f28cb7b9519cbb5"
            ),
            "transformation": (
                "replace_malformed_nested_C_projection_with_valid_W_projection_and_remove_"
                "only_the_expected_message_scaffolding"
            ),
            "transformed_source_sha256": (
                "f8b55af8ef253edd4f37dab119104caad470a6a1c787759797cbf8b402f34782"
            ),
            "exit_code": 0,
            "trust": 0,
            "eof_canary_observed": True,
            "module": "Issue14576MinBenign",
            "derived_query_bytes": 716,
            "derived_query_sha256": (
                "f9985480723b5c0f8e944490b524a5681d994916190dec1a02d7d190bc3ee0c0"
            ),
            "olean_bytes": 640,
            "olean_sha256": "c" * 64,
            "leanchecker_fresh_environment_replayed": True,
        },
        "unguarded_negative_control": {
            "source_fixture": "issue_14576.lean",
            "source_fixture_sha256": (
                "0aaec9548df29266061467e37026935391a05bf6142fd027915f40c687a889e2"
            ),
            "transformation": (
                "replace_exactly_one_reviewed_invalid_projection_message_guard_"
                "scaffolding_with_unguarded_mkbug"
            ),
            "transformed_source_sha256": (
                "79c675b9023e315c30c52eccb5713aa326fa3d7b8dbd05ac32d107dd7410e90f"
            ),
            "transformed_source_bytes": 2397,
            "exit_code": 1,
            "diagnostic": "(kernel) invalid projection\\n  w.1",
            "diagnostic_stream": "stdout",
            "diagnostic_source_line": 58,
            "diagnostic_source_column": 0,
            "diagnostic_path": "exact_absolute_private_query_path",
            "stdout_shape": (
                "<exact-absolute-private-query>:58:0: error: (kernel) invalid projection\\n"
                "  w.1\\n<exact-eof-canary>\\n"
            ),
            "stderr": "empty",
            "trust": 0,
            "eof_canary_observed": True,
            "derived_query_bytes": 2466,
            "derived_query_sha256": (
                "569d521a544b86f0ae70c19aa59f9b71ee036aeb8fb919e3f347e9050fb276c5"
            ),
        },
        "boundary": production_boundary,
    }
    checker.validate_nested_kernel_regression_result(
        valid,
        tool_root,
        "darwin-aarch64",
        checker.NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
        EXPECTED_METADATA_SHA256,
        METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
        "aarch64-apple-darwin",
        expected_executable_evidence,
    )

    def mutated(*path: str | int, value: object) -> dict[str, object]:
        candidate = json.loads(json.dumps(valid))
        cursor: object = candidate
        for key in path[:-1]:
            if isinstance(key, int):
                require(
                    isinstance(cursor, list), f"mutation path is not a list: {path}"
                )
                cursor = cursor[key]
            else:
                require(
                    isinstance(cursor, dict),
                    f"mutation path is not an object: {path}",
                )
                cursor = cursor[key]
        leaf = path[-1]
        if isinstance(leaf, int):
            require(isinstance(cursor, list), f"mutation leaf is not a list: {path}")
            cursor[leaf] = value
        else:
            require(
                isinstance(cursor, dict),
                f"mutation leaf is not an object: {path}",
            )
            cursor[leaf] = value
        return candidate

    cases = (
        (
            "nested_regression_schema",
            mutated("schema", value="pid-rs/lean-kernel-14576-check/v4"),
            "schema or status drifted",
        ),
        (
            "nested_regression_status",
            mutated("status", value="failed"),
            "schema or status drifted",
        ),
        (
            "nested_regression_extra_top_level_field",
            mutated("unexpected", value=True),
            "result keys drifted",
        ),
        (
            "nested_regression_missing_lean_identity",
            mutated("lean", value=None),
            "Lean identity must be an object",
        ),
        (
            "nested_regression_lean_version",
            mutated("lean", "version", value="4.32.1"),
            "Lean identity drifted",
        ),
        (
            "nested_regression_lean_platform",
            mutated("lean", "platform", value="x86_64-unknown-linux-gnu"),
            "Lean identity drifted",
        ),
        (
            "nested_regression_lean_post_identity_false",
            mutated("lean", "post_execution_identity_equal", value=False),
            "Lean identity drifted",
        ),
        (
            "nested_regression_lake_version",
            mutated("lake", "version", value="5.0.0-src+0000000"),
            "Lake identity drifted",
        ),
        (
            "nested_regression_missing_route",
            mutated("execution_route", value=None),
            "execution route must be an object",
        ),
        (
            "nested_regression_wrong_toolchain_root",
            mutated(
                "execution_route",
                "direct_toolchain_root",
                value=os.fspath(tool_root.parent / "substituted"),
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_wrong_platform",
            mutated(
                "execution_route",
                "reviewed_pin_platform_key",
                value="linux-x86_64",
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_wrong_metadata_lifecycle_state",
            mutated(
                "execution_route",
                "metadata_lifecycle_state",
                value="hosted_pending",
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_self_claimed_archive_derivation",
            mutated(
                "execution_route",
                "archive_derivation_claimed_by_this_checker",
                value=True,
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_metadata_identity_substitution",
            mutated(
                "execution_route",
                "toolchain_metadata_sha256",
                value="0" * 64,
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_self_binding_false",
            mutated(
                "execution_route",
                "nested_checker_self_binding_equal",
                value=False,
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_metadata_policy_identity_substitution",
            mutated(
                "execution_route",
                "toolchain_metadata_policy_projection_sha256",
                value="0" * 64,
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_required_archive_route",
            mutated(
                "execution_route",
                "required_archive_derivation_route",
                value="standalone",
            ),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_elan_invoked",
            mutated("execution_route", "elan_invoked", value=True),
            "direct-toolchain route drifted",
        ),
        (
            "nested_regression_source_compile_arguments",
            mutated(
                "execution_route",
                "source_compile_arguments",
                value=["--trust=1"],
            ),
            "command route drifted",
        ),
        (
            "nested_regression_tool_leaf_inventory",
            mutated(
                "execution_route",
                "direct_tool_leaves_bound",
                value=["lean", "lake"],
            ),
            "tool endpoint claims drifted",
        ),
        (
            "nested_regression_shared_group_not_selected",
            mutated("execution_route", "shared_outer_process_group", value=False),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_inner_child_new_session",
            mutated("execution_route", "inner_children_start_new_sessions", value=True),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_nested_group_signal_claim",
            mutated(
                "execution_route",
                "shared_group_signal_from_nested_checker",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_outer_group_cleanup_owner_false",
            mutated(
                "execution_route",
                "shared_group_cleanup_owned_by_outer_supervisor",
                value=False,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_isolated_cleanup_claim_in_shared_mode",
            mutated(
                "execution_route",
                "isolated_child_group_cleanup_after_every_outcome",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_isolated_cleanup_signal_drift",
            mutated(
                "execution_route",
                "isolated_child_group_cleanup_signal_policy",
                value=["KILL"],
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_cleanup_policy_delivery_log_claim",
            mutated(
                "execution_route",
                "process_group_cleanup_signal_policy_is_escalation_not_delivery_log",
                value=False,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_nonchild_reaping_claim",
            mutated(
                "execution_route",
                "non_child_descendants_reaped_by_this_checker",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_atomic_group_observation_claim",
            mutated(
                "execution_route",
                "process_group_observation_atomic",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_process_group_reuse_excluded_claim",
            mutated(
                "execution_route",
                "process_group_reuse_excluded",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_descendant_group_change_monitoring_claim",
            mutated(
                "execution_route",
                "descendant_group_or_session_changes_continuously_observed",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_process_group_cleanup_term_bound",
            mutated(
                "execution_route",
                "process_group_cleanup_bounds_milliseconds",
                "term_grace",
                value=499,
            ),
            "process-group cleanup bounds",
        ),
        (
            "nested_regression_isolated_absence_claim_in_shared_mode",
            mutated(
                "execution_route",
                "isolated_child_group_absence_checked",
                value=True,
            ),
            "descendant cleanup route drifted",
        ),
        (
            "nested_regression_environment_prefixes",
            mutated(
                "execution_route",
                "child_environment_removed_prefixes",
                value=[],
            ),
            "environment route drifted",
        ),
        (
            "nested_regression_ambient_home_retention_claim",
            mutated(
                "execution_route",
                "ambient_home_logname_user_retained",
                value=True,
            ),
            "environment route drifted",
        ),
        (
            "nested_regression_per_child_private_home_false",
            mutated(
                "execution_route",
                "per_child_private_home_and_tmp",
                value=False,
            ),
            "environment route drifted",
        ),
        (
            "nested_regression_per_child_private_tmp_mode",
            mutated(
                "execution_route",
                "per_child_private_environment_directory_modes",
                "tmp",
                value="0755",
            ),
            "per-child private environment modes",
        ),
        (
            "nested_regression_lean_pre_snapshot_sha",
            mutated(
                "execution_route",
                "direct_lean_pre_execution",
                "sha256",
                value="0" * 64,
            ),
            "disagrees with the outer live executable snapshot",
        ),
        (
            "nested_regression_private_directory_identity_false",
            mutated(
                "execution_route",
                "private_temporary_directory_pre_post_identity_equal",
                value=False,
            ),
            "private-directory custody drifted",
        ),
        (
            "nested_regression_private_olean_directory_mode",
            mutated(
                "execution_route",
                "private_temporary_directory_modes",
                "olean_root",
                value="0755",
            ),
            "private-directory modes",
        ),
        (
            "nested_regression_private_directory_mode_extra_key",
            mutated(
                "execution_route",
                "private_temporary_directory_modes",
                "unexpected",
                value="0700",
            ),
            "private-directory modes",
        ),
        (
            "nested_regression_checker_source_substitution",
            mutated("checker_source_sha256", value="0" * 64),
            "checker-source identity drifted",
        ),
        (
            "nested_regression_active_project_input_injection",
            mutated(
                "active_scientific_project_inputs_consumed",
                value=["audit/formal/lean/lean-toolchain"],
            ),
            "active-project decoupling drifted",
        ),
        (
            "nested_regression_active_project_migration_claim",
            mutated(
                "active_scientific_project_toolchain_migration_claimed",
                value=True,
            ),
            "active-project decoupling drifted",
        ),
        (
            "nested_regression_missing_trust_zero_semantics",
            mutated("trust_zero_semantics", value=None),
            "trust-zero semantics",
        ),
        (
            "nested_regression_extra_trust_zero_semantics_field",
            mutated("trust_zero_semantics", "unexpected", value=True),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_argument",
            mutated("trust_zero_semantics", "argument", value="--trust=1"),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_help_meaning",
            mutated(
                "trust_zero_semantics",
                "help_meaning",
                value="trust_every_macro",
            ),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_macros_trusted",
            mutated("trust_zero_semantics", "no_macros_trusted", value=False),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_imports_unchecked",
            mutated(
                "trust_zero_semantics",
                "all_imported_modules_typechecked",
                value=False,
            ),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_runtime_untrusted",
            mutated(
                "trust_zero_semantics",
                "selected_lean_implementation_and_runtime_remain_trusted",
                value=False,
            ),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_tcb_claim",
            mutated("trust_zero_semantics", "zero_tcb", value=True),
            "trust-zero semantics",
        ),
        (
            "nested_regression_trust_zero_boolean_integer_collapse",
            mutated("trust_zero_semantics", "zero_tcb", value=0),
            "trust-zero semantics",
        ),
        (
            "nested_regression_missing_leanchecker_fresh_semantics",
            mutated("leanchecker_fresh_semantics", value=None),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_extra_leanchecker_fresh_semantics_field",
            mutated("leanchecker_fresh_semantics", "unexpected", value=True),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_fresh_argument",
            mutated("leanchecker_fresh_semantics", "argument", value="--default"),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_external_verifier_claim",
            mutated("leanchecker_fresh_semantics", "external_verifier", value=True),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_boolean_integer_collapse",
            mutated("leanchecker_fresh_semantics", "external_verifier", value=0),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_guard_rerun_claim",
            mutated("leanchecker_fresh_semantics", "guard_msgs_rerun", value=True),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_rechecks_source_or_guarded_commands_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "fresh_replay_rechecks_source_elaboration_or_guarded_commands",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_full_bad_source_presence_false",
            mutated(
                "leanchecker_fresh_semantics",
                "full_fixture_bad_declaration_source_present",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_full_bad_thmdecl_reached_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "full_fixture_bad_thmdecl_reached_or_attempted",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_full_bad_later_reference_guard_false",
            mutated(
                "leanchecker_fresh_semantics",
                "full_fixture_post_failure_unknown_bad_reference_guard",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_initial_environment",
            mutated(
                "leanchecker_fresh_semantics",
                "initial_environment",
                value="ambient_environment",
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_ordinary_olean_count",
            mutated("leanchecker_fresh_semantics", "ordinary_olean_count", value=2),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_private_tree_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "ordinary_olean_files_in_mode_0700_private_temporary_tree",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_complete_inventory_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "complete_declaration_inventory_claimed",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_selected_probe_scope_false",
            mutated(
                "leanchecker_fresh_semantics",
                "selected_emitted_olean_name_probe_only",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_residual_axiom_shaped_E_false",
            mutated(
                "leanchecker_fresh_semantics",
                "residual_axiom_shaped_E_present_in_each_selected_target_olean",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_E_mk_absence_false",
            mutated(
                "leanchecker_fresh_semantics",
                "rejected_constructor_E_mk_absent_in_each_selected_target_olean",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_unreached_full_bad_absence_false",
            mutated(
                "leanchecker_fresh_semantics",
                "unreached_bad_declaration_absent_in_full_selected_target_olean",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_minimum_bad_source_reference_probe_or_absence_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "minimum_fixture_bad_source_reference_probe_or_absence_claimed",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_replayed_content",
            mutated(
                "leanchecker_fresh_semantics",
                "replayed_content",
                value="source_text",
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_independent_kernel_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "independent_kernel_implementation",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_same_executable_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "same_executable_leaf_as_source_elaboration",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_same_process_claim",
            mutated(
                "leanchecker_fresh_semantics",
                "same_process_as_source_elaboration",
                value=True,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_release_trust_erased",
            mutated(
                "leanchecker_fresh_semantics",
                "selected_release_implementation_and_runtime_remain_trusted",
                value=False,
            ),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_leanchecker_source_reelaboration_claim",
            mutated("leanchecker_fresh_semantics", "source_reelaboration", value=True),
            "LeanChecker-fresh semantics",
        ),
        (
            "nested_regression_origin_identity",
            mutated("origin_sha256", value="0" * 64),
            "origin identity drifted",
        ),
        (
            "nested_regression_missing_fixture_inventory",
            mutated("fixtures", value=None),
            "fixture inventory drifted",
        ),
        (
            "nested_regression_fixture_order",
            mutated("fixtures", value=list(reversed(valid["fixtures"]))),
            "field 'bytes' drifted",
        ),
        (
            "nested_regression_fixture_extra_field",
            mutated("fixtures", 0, "unexpected", value=True),
            "fixture issue_14576.lean keys drifted",
        ),
        (
            "nested_regression_fixture_source_sha",
            mutated("fixtures", 0, "sha256", value="0" * 64),
            "field 'sha256' drifted",
        ),
        (
            "nested_regression_fixture_trust_boolean_integer_collapse",
            mutated("fixtures", 0, "trust", value=False),
            "trust level drifted",
        ),
        (
            "nested_regression_fixture_guard_false",
            mutated("fixtures", 0, "guarded_invalid_projection", value=False),
            "field 'guarded_invalid_projection' drifted",
        ),
        (
            "nested_regression_fixture_eof_false",
            mutated("fixtures", 1, "eof_canary_observed", value=False),
            "field 'eof_canary_observed' drifted",
        ),
        (
            "nested_regression_fixture_query_sha",
            mutated("fixtures", 1, "derived_query_sha256", value="0" * 64),
            "field 'derived_query_sha256' drifted",
        ),
        (
            "nested_regression_fixture_olean_zero_bytes",
            mutated("fixtures", 0, "olean_bytes", value=0),
            "olean bytes must be a positive integer",
        ),
        (
            "nested_regression_fixture_olean_malformed_sha",
            mutated("fixtures", 1, "olean_sha256", value="not-a-sha"),
            "olean SHA-256 is malformed",
        ),
        (
            "nested_regression_fixture_selected_probe_missing",
            mutated("fixtures", 0, "target_olean_inventory_probe", value=None),
            "selected declaration probe must be an object",
        ),
        (
            "nested_regression_fixture_selected_probe_scope",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "claim_scope",
                value="complete_inventory",
            ),
            "selected declaration probe field 'claim_scope' type/value drifted",
        ),
        (
            "nested_regression_fixture_complete_inventory_claim",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "complete_declaration_inventory_claimed",
                value=True,
            ),
            "selected declaration probe field 'complete_declaration_inventory_claimed' type/value drifted",
        ),
        (
            "nested_regression_fixture_lookup_positive_control",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "bracketing_lookup_controls",
                "present",
                value="E",
            ),
            "selected declaration probe field 'bracketing_lookup_controls'",
        ),
        (
            "nested_regression_fixture_lookup_negative_control",
            mutated(
                "fixtures",
                1,
                "target_olean_inventory_probe",
                "bracketing_lookup_controls",
                "absent",
                value="bad",
            ),
            "selected declaration probe field 'bracketing_lookup_controls'",
        ),
        (
            "nested_regression_fixture_residual_E_status",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                0,
                "status",
                value="absent",
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_residual_E_source_role",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                0,
                "source_role",
                value="accepted_inductive_declaration",
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_rejected_E_mk_status",
            mutated(
                "fixtures",
                1,
                "target_olean_inventory_probe",
                "selected_declarations",
                1,
                "status",
                value="present",
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_full_bad_evidence_removed",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                value=valid["fixtures"][0]["target_olean_inventory_probe"][
                    "selected_declarations"
                ][:2],
            ),
            "selected declaration probe field 'selected_declarations' length drifted",
        ),
        (
            "nested_regression_fixture_full_bad_source_presence_false",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                2,
                "declaration_source_present",
                value=False,
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_full_bad_thmdecl_reached_claim",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                2,
                "thmdecl_reached_or_attempted",
                value=True,
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_full_bad_later_guard_false",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                2,
                "post_failure_unknown_identifier_reference_guard",
                value=False,
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_full_bad_source_role",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "selected_declarations",
                2,
                "source_role",
                value="rejected_theorem_attempt",
            ),
            "selected declaration probe field 'selected_declarations'",
        ),
        (
            "nested_regression_fixture_minimum_bad_evidence_injected",
            mutated(
                "fixtures",
                1,
                "target_olean_inventory_probe",
                "selected_declarations",
                value=[
                    *valid["fixtures"][1]["target_olean_inventory_probe"][
                        "selected_declarations"
                    ],
                    {
                        "declaration_source_present": True,
                        "post_failure_unknown_identifier_reference_guard": True,
                        "symbol": "bad",
                        "status": "absent",
                        "rendering": "Unknown constant `bad`",
                        "source_role": "unreached_downstream_declaration",
                        "thmdecl_reached_or_attempted": False,
                    },
                ],
            ),
            "selected declaration probe field 'selected_declarations' length drifted",
        ),
        (
            "nested_regression_fixture_selected_probe_source_sha",
            mutated(
                "fixtures",
                1,
                "target_olean_inventory_probe",
                "source_sha256",
                value="0" * 64,
            ),
            "selected declaration probe field 'source_sha256' type/value drifted",
        ),
        (
            "nested_regression_fixture_selected_probe_exit",
            mutated(
                "fixtures",
                0,
                "target_olean_inventory_probe",
                "exit_code",
                value=1,
            ),
            "selected declaration probe field 'exit_code' type/value drifted",
        ),
        (
            "nested_regression_fixture_selected_probe_import_false",
            mutated(
                "fixtures",
                1,
                "target_olean_inventory_probe",
                "target_olean_imported",
                value=False,
            ),
            "selected declaration probe field 'target_olean_imported' type/value drifted",
        ),
        (
            "nested_regression_fixture_fresh_replay_false",
            mutated(
                "fixtures",
                0,
                "leanchecker_fresh_environment_replayed",
                value=False,
            ),
            "field 'leanchecker_fresh_environment_replayed' drifted",
        ),
        (
            "nested_regression_trust_zero_compilation_count",
            mutated("trust_zero_olean_compilations", value=2),
            "trust-zero compilation count drifted",
        ),
        (
            "nested_regression_trust_zero_compilation_boolean_integer_collapse",
            mutated("trust_zero_olean_compilations", value=True),
            "trust-zero compilation count drifted",
        ),
        (
            "nested_regression_benign_transformed_source_sha",
            mutated(
                "benign_near_neighbor", "transformed_source_sha256", value="0" * 64
            ),
            "benign near-neighbor field 'transformed_source_sha256' drifted",
        ),
        (
            "nested_regression_benign_exit",
            mutated("benign_near_neighbor", "exit_code", value=1),
            "benign near-neighbor field 'exit_code' drifted",
        ),
        (
            "nested_regression_benign_trust_boolean_integer_collapse",
            mutated("benign_near_neighbor", "trust", value=False),
            "benign near-neighbor field 'trust' drifted",
        ),
        (
            "nested_regression_benign_eof_false",
            mutated("benign_near_neighbor", "eof_canary_observed", value=False),
            "benign near-neighbor field 'eof_canary_observed' drifted",
        ),
        (
            "nested_regression_benign_olean_zero_bytes",
            mutated("benign_near_neighbor", "olean_bytes", value=0),
            "benign olean bytes must be a positive integer",
        ),
        (
            "nested_regression_benign_fresh_replay_false",
            mutated(
                "benign_near_neighbor",
                "leanchecker_fresh_environment_replayed",
                value=False,
            ),
            "benign near-neighbor field 'leanchecker_fresh_environment_replayed' drifted",
        ),
        (
            "nested_regression_unguarded_source_sha",
            mutated(
                "unguarded_negative_control",
                "transformed_source_sha256",
                value="0" * 64,
            ),
            "unguarded negative control field 'transformed_source_sha256' type/value drifted",
        ),
        (
            "nested_regression_unguarded_exit",
            mutated("unguarded_negative_control", "exit_code", value=0),
            "unguarded negative control field 'exit_code' type/value drifted",
        ),
        (
            "nested_regression_unguarded_diagnostic",
            mutated("unguarded_negative_control", "diagnostic", value="unknown error"),
            "unguarded negative control field 'diagnostic' type/value drifted",
        ),
        (
            "nested_regression_unguarded_eof_false",
            mutated("unguarded_negative_control", "eof_canary_observed", value=False),
            "unguarded negative control field 'eof_canary_observed' type/value drifted",
        ),
        (
            "nested_regression_unguarded_trust_boolean_integer_collapse",
            mutated("unguarded_negative_control", "trust", value=False),
            "unguarded negative control field 'trust' type/value drifted",
        ),
        (
            "nested_regression_unguarded_query_sha",
            mutated(
                "unguarded_negative_control", "derived_query_sha256", value="0" * 64
            ),
            "unguarded negative control field 'derived_query_sha256' type/value drifted",
        ),
        (
            "nested_regression_replay_count",
            mutated("leanchecker_fresh_environment_replays", value=2),
            "replay inventory drifted",
        ),
        (
            "nested_regression_replay_module_order",
            mutated(
                "leanchecker_fresh_environment_replayed_modules",
                value=[
                    "Issue14576Min",
                    "Issue14576Full",
                    "Issue14576MinBenign",
                ],
            ),
            "replay inventory drifted",
        ),
        (
            "nested_regression_replay_measurement_inventory",
            mutated("leanchecker_fresh_environment_replay_measurements", value=[]),
            "replay measurement inventory drifted",
        ),
        (
            "nested_regression_replay_measurement_module",
            mutated(
                "leanchecker_fresh_environment_replay_measurements",
                0,
                "module",
                value="Issue14576Min",
            ),
            "measurement Issue14576Full identity/bound drifted",
        ),
        (
            "nested_regression_replay_measurement_timeout",
            mutated(
                "leanchecker_fresh_environment_replay_measurements",
                1,
                "timeout_seconds",
                value=899,
            ),
            "measurement Issue14576Min identity/bound drifted",
        ),
        (
            "nested_regression_replay_measurement_duration_negative",
            mutated(
                "leanchecker_fresh_environment_replay_measurements",
                2,
                "duration_monotonic_ns",
                value=-1,
            ),
            "measurement Issue14576MinBenign duration drifted",
        ),
        (
            "nested_regression_replay_measurement_boolean_integer_collapse",
            mutated(
                "leanchecker_fresh_environment_replay_measurements",
                0,
                "duration_monotonic_ns",
                value=False,
            ),
            "measurement Issue14576Full duration drifted",
        ),
        (
            "nested_regression_replay_measurement_total",
            mutated("leanchecker_fresh_environment_replay_total_monotonic_ns", value=7),
            "replay measurement aggregate drifted",
        ),
        (
            "nested_regression_replay_measurement_maximum",
            mutated("leanchecker_fresh_environment_replay_max_monotonic_ns", value=2),
            "replay measurement aggregate drifted",
        ),
        (
            "nested_regression_timing_inner_bound",
            mutated(
                "nested_timing_contract",
                "inner_per_replay_timeout_seconds",
                value=899,
            ),
            "timing inner bound drifted",
        ),
        (
            "nested_regression_timing_replay_count",
            mutated("nested_timing_contract", "replay_count", value=2),
            "timing replay count drifted",
        ),
        (
            "nested_regression_timing_non_replay_lean_child_bound",
            mutated(
                "nested_timing_contract",
                "non_replay_lean_child_timeout_seconds",
                value=119,
            ),
            "timing non-replay Lean-child bound drifted",
        ),
        (
            "nested_regression_timing_non_replay_lean_child_count",
            mutated(
                "nested_timing_contract",
                "non_replay_lean_child_count",
                value=5,
            ),
            "timing non-replay Lean-child count drifted",
        ),
        (
            "nested_regression_timing_identity_child_bound",
            mutated(
                "nested_timing_contract",
                "identity_child_timeout_seconds",
                value=59,
            ),
            "timing identity-child bound drifted",
        ),
        (
            "nested_regression_timing_identity_child_count",
            mutated("nested_timing_contract", "identity_child_count", value=3),
            "timing identity-child count drifted",
        ),
        (
            "nested_regression_timing_orchestration_headroom",
            mutated(
                "nested_timing_contract",
                "orchestration_headroom_seconds",
                value=239,
            ),
            "timing orchestration headroom drifted",
        ),
        (
            "nested_regression_timing_non_replay_allocation",
            mutated(
                "nested_timing_contract",
                "declared_non_replay_margin_seconds",
                value=1199,
            ),
            "timing non-replay allocation drifted or is contradictory",
        ),
        (
            "nested_regression_timing_required_outer",
            mutated(
                "nested_timing_contract",
                "required_outer_timeout_seconds",
                value=3899,
            ),
            "timing required outer bound drifted or is contradictory",
        ),
        (
            "nested_regression_timing_derivation",
            mutated("nested_timing_contract", "derivation", value="arbitrary"),
            "timing derivation drifted",
        ),
        (
            "nested_regression_timing_environmental_premise",
            mutated(
                "nested_timing_contract", "environmental_premise", value="guaranteed"
            ),
            "timing environmental premise drifted",
        ),
        (
            "nested_regression_timing_extra_field",
            mutated("nested_timing_contract", "unexpected", value=True),
            "timing contract keys drifted",
        ),
        (
            "nested_regression_nonclaim_boundary",
            mutated("boundary", value=production_boundary + " appended overclaim"),
            "nonclaim boundary drifted",
        ),
    )

    def canonical_nested_stdout(candidate: dict[str, object]) -> bytes:
        return checker.canonical_json_bytes(candidate) + b"\n"

    def validate_through_production_wrapper(
        stdout: bytes, stderr: bytes = b""
    ) -> dict[str, object]:
        return checker.parse_and_validate_nested_kernel_regression_output(
            checker.ProcessResult(0, stdout, stderr),
            tool_root,
            "darwin-aarch64",
            checker.NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
            EXPECTED_METADATA_SHA256,
            METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
            "aarch64-apple-darwin",
            expected_executable_evidence,
        )

    def expect_production_wrapper_redaction(
        name: str,
        stdout: bytes,
        forbidden: tuple[str, ...],
        *,
        stderr: bytes = b"",
    ) -> dict[str, object]:
        result = checker.ProcessResult(0, stdout, stderr)
        expected = checker.nested_zero_exit_result_digest_diagnostic(result)
        try:
            validate_through_production_wrapper(stdout, stderr)
        except checker.CustodyError as error:
            diagnostic = str(error)
            try:
                encoded = diagnostic.encode("ascii", errors="strict")
            except UnicodeError as unicode_error:
                raise SelfTestError(
                    f"{name} emitted a non-ASCII boundary diagnostic"
                ) from unicode_error
            require(
                type(error) is checker.CustodyError
                and diagnostic == expected
                and len(encoded) <= checker.MISMATCH_DIAGNOSTIC_BYTES_MAX
                and all(0x20 <= byte <= 0x7E for byte in encoded),
                f"{name} did not collapse to the exact one-line generic diagnostic",
            )
            cli_line = checker.cli_failure_line(error)
            cli_bytes = cli_line.encode("ascii", errors="strict")
            require(
                cli_line.startswith(checker.CLI_FAILURE_PREFIX)
                and cli_line.endswith("\n")
                and cli_line.count("\n") == 1
                and "\r" not in cli_line
                and len(cli_bytes) <= checker.CLI_FAILURE_STDERR_BYTES_MAX
                and all(0x20 <= byte <= 0x7E for byte in cli_bytes[:-1])
                and cli_bytes[-1:] == b"\n",
                f"{name} exceeded or injected the complete production CLI stderr line",
            )
            require(
                all(token not in diagnostic for token in forbidden),
                f"{name} disclosed a child-controlled name, token, or value",
            )
            return {
                "name": name,
                "rejected": True,
                "production_zero_exit_wrapper": True,
                "diagnostic_bytes": len(encoded),
                "complete_cli_stderr_bytes": len(cli_bytes),
                "stdout_bytes_reported": len(stdout),
                "stdout_sha256_reported": hashlib.sha256(stdout).hexdigest(),
                "stderr_bytes_reported": len(stderr),
                "stderr_sha256_reported": hashlib.sha256(stderr).hexdigest(),
                "raw_child_material_reported": False,
            }
        raise SelfTestError(f"negative control survived: {name}")

    def expect_production_wrapper_typed_leaf(
        name: str,
        candidate: dict[str, object],
        expected_diagnostic: str,
        forbidden: tuple[str, ...] = (),
    ) -> dict[str, object]:
        stdout = canonical_nested_stdout(candidate)
        try:
            validate_through_production_wrapper(stdout)
        except checker.NestedExecutableEvidenceMismatch as error:
            diagnostic = str(error)
            encoded = diagnostic.encode("ascii", errors="strict")
            require(
                diagnostic == expected_diagnostic
                and checker.nested_executable_mismatch_is_boundary_safe(diagnostic)
                and len(encoded) <= checker.MISMATCH_DIAGNOSTIC_BYTES_MAX
                and all(0x20 <= byte <= 0x7E for byte in encoded),
                f"{name} did not preserve the exact safe typed leaf diagnostic",
            )
            cli_line = checker.cli_failure_line(error)
            cli_bytes = cli_line.encode("ascii", errors="strict")
            require(
                cli_line.startswith(checker.CLI_FAILURE_PREFIX)
                and cli_line.endswith("\n")
                and cli_line.count("\n") == 1
                and "\r" not in cli_line
                and len(cli_bytes) <= checker.CLI_FAILURE_STDERR_BYTES_MAX
                and all(0x20 <= byte <= 0x7E for byte in cli_bytes[:-1])
                and cli_bytes[-1:] == b"\n",
                f"{name} exceeded or injected the complete production CLI stderr line",
            )
            require(
                all(token not in diagnostic for token in forbidden),
                f"{name} disclosed an unbounded child-controlled name or value",
            )
            return {
                "name": name,
                "rejected": True,
                "production_zero_exit_wrapper": True,
                "typed_safe_leaf_diagnostic": True,
                "diagnostic_bytes": len(encoded),
                "complete_cli_stderr_bytes": len(cli_bytes),
            }
        except checker.CustodyError as error:
            raise SelfTestError(
                f"{name} was incorrectly collapsed to the generic diagnostic: {error}"
            ) from error
        raise SelfTestError(f"negative control survived: {name}")

    controls = [
        expect_failure(
            name,
            lambda candidate=candidate: (
                checker.validate_nested_kernel_regression_result(
                    candidate,
                    tool_root,
                    "darwin-aarch64",
                    checker.NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
                    EXPECTED_METADATA_SHA256,
                    METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
                    "aarch64-apple-darwin",
                    expected_executable_evidence,
                )
            ),
            reason,
        )
        for name, candidate, reason in cases
    ]

    valid_stdout = canonical_nested_stdout(valid)
    require(
        validate_through_production_wrapper(valid_stdout) == valid,
        "production zero-exit nested-result wrapper rejected its exact baseline",
    )

    duplicate_key = "duplicate_secret_" + "d" * (2_000 - len("duplicate_secret_"))
    duplicate_key_json = json.dumps(duplicate_key, ensure_ascii=True).encode("ascii")
    duplicate_stdout = (
        b"{" + duplicate_key_json + b":0," + duplicate_key_json + b":1}\n"
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_duplicate_2000_byte_key",
            duplicate_stdout,
            (duplicate_key,),
        )
    )
    long_float = "1." + "2" * 2_000
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_2002_byte_float_token",
            ('{"float_secret":' + long_float + "}\n").encode("ascii"),
            ("float_secret", long_float),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_nonfinite_token",
            b'{"nonfinite_secret":NaN}\n',
            ("nonfinite_secret", "NaN"),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_malformed_json",
            b'{"malformed_secret":]}\n',
            ("malformed_secret",),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_invalid_utf8",
            b'{"unicode_secret":"\xff"}\n',
            ("unicode_secret",),
        )
    )
    for framing_name, framing_stdout in (
        ("empty_stdout", b""),
        ("multiple_lines", b"{}\n{}\n"),
        ("crlf", b"{}\r\n"),
        ("wrong_root", b"[]\n"),
        ("trailing_data", b"{}\ntrailing_secret"),
    ):
        controls.append(
            expect_production_wrapper_redaction(
                f"nested_production_wrapper_{framing_name}",
                framing_stdout,
                ("trailing_secret",),
            )
        )
    excessive_nesting = (
        b'{"nesting_secret":' + b"[" * 1_100 + b"0" + b"]" * 1_100 + b"}\n"
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_excessive_nesting",
            excessive_nesting,
            ("nesting_secret",),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_utf8_bom",
            b"\xef\xbb\xbf" + valid_stdout,
            ("regression_checks_passed",),
        )
    )
    long_integer = "7" * 2_000
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_2000_digit_integer",
            ('{"long_integer_secret":' + long_integer + "}\n").encode("ascii"),
            ("long_integer_secret", long_integer),
        )
    )
    digit_limit_integer = "8" * 5_000
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_integer_digit_limit_value_error",
            ('{"digit_limit_secret":' + digit_limit_integer + "}\n").encode("ascii"),
            ("digit_limit_secret", digit_limit_integer, "Exceeds the limit"),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_noncanonical_json",
            b" " + valid_stdout,
            ("regression_checks_passed",),
        )
    )
    alternate_escape = valid_stdout.replace(
        b'"regression_checks_passed"',
        b'"\\u0072egression_checks_passed"',
        1,
    )
    require(
        alternate_escape != valid_stdout,
        "alternate-escape nested-result fixture was not distinct",
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_noncanonical_alternate_escape",
            alternate_escape,
            ("regression_checks_passed",),
        )
    )
    valid_schema_json = json.dumps(
        checker.KERNEL_REGRESSION_RESULT_SCHEMA,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    duplicate_valid_root = b'{"schema":' + valid_schema_json + b"," + valid_stdout[1:]
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_duplicate_valid_root_key",
            duplicate_valid_root,
            ("schema",),
        )
    )
    duplicate_valid_route = valid_stdout.replace(
        b'"execution_route":{',
        b'"execution_route":{"elan_invoked":false,',
        1,
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_duplicate_valid_route_key",
            duplicate_valid_route,
            ("elan_invoked",),
        )
    )
    duplicate_valid_evidence = valid_stdout.replace(
        b'"direct_lean_pre_execution":{',
        b'"direct_lean_pre_execution":{"bytes":1024,',
        1,
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_duplicate_valid_evidence_key",
            duplicate_valid_evidence,
            ("direct_lean_pre_execution",),
        )
    )
    root_long_key = "root_secret_" + "r" * (2_000 - len("root_secret_"))
    root_long_extra = copy.deepcopy(valid)
    root_long_extra[root_long_key] = "root_secret_value"
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_root_2000_byte_extra_key",
            canonical_nested_stdout(root_long_extra),
            (root_long_key, "root_secret_value"),
        )
    )
    route_long_key = "route_secret_" + "t" * (2_000 - len("route_secret_"))
    route_long_extra = copy.deepcopy(valid)
    route_long_extra["execution_route"][route_long_key] = "route_secret_value"
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_route_2000_byte_extra_key",
            canonical_nested_stdout(route_long_extra),
            (route_long_key, "route_secret_value"),
        )
    )
    hostile_root_keys = (
        ("newline", "root_newline_secret\nsecond_line"),
        ("escape", "root_escape_secret\x1b[31m"),
        ("bidi", "root_bidi_secret\u202eforged"),
        (
            "delimiter",
            "root_delimiter_secret; stdout_sha256="
            + "a" * 64
            + "; observed_evidence_sha256="
            + "b" * 64,
        ),
    )
    for hostile_name, hostile_key in hostile_root_keys:
        hostile_root = copy.deepcopy(valid)
        hostile_root[hostile_key] = f"{hostile_name}_secret_value"
        controls.append(
            expect_production_wrapper_redaction(
                f"nested_production_wrapper_root_{hostile_name}_key",
                canonical_nested_stdout(hostile_root),
                (hostile_key, f"{hostile_name}_secret_value"),
            )
        )
    bool_int = copy.deepcopy(valid)
    bool_int["trust_zero_olean_compilations"] = True
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_bool_for_integer_type",
            canonical_nested_stdout(bool_int),
            ("True",),
        )
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_zero_exit_secret_stderr",
            valid_stdout,
            ("validator_secret_stderr",),
            stderr=b"validator_secret_stderr\n",
        )
    )

    for exception_stage, attribute in (
        ("parse", "parse_json_object"),
        ("canonical", "canonical_json_bytes"),
        ("root", "validate_nested_kernel_regression_result"),
        ("route", "validate_nested_execution_route"),
        ("evidence", "validate_nested_executable_evidence"),
        ("late", "validate_nested_replay_measurements"),
    ):
        original_validator = getattr(checker, attribute)
        secret = f"unexpected_{exception_stage}_validator_secret"

        def unexpected_validator(
            *_args: object, secret: str = secret, **_kwargs: object
        ) -> None:
            raise RuntimeError(secret + "\nforged traceback")

        setattr(checker, attribute, unexpected_validator)
        try:
            controls.append(
                expect_production_wrapper_redaction(
                    f"nested_production_wrapper_unexpected_{exception_stage}_exception",
                    valid_stdout,
                    (secret, "forged traceback"),
                )
            )
        finally:
            setattr(checker, attribute, original_validator)

    wrapper_modified_leaf = copy.deepcopy(valid)
    wrapper_modified_evidence = copy.deepcopy(lean_evidence)
    wrapper_modified_evidence["identity"]["modified_ns"] = 2
    wrapper_modified_leaf["execution_route"]["direct_lean_pre_execution"] = (
        wrapper_modified_evidence
    )
    controls.append(
        expect_production_wrapper_typed_leaf(
            "nested_production_wrapper_typed_leaf_mismatch",
            wrapper_modified_leaf,
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean pre-execution evidence",
                wrapper_modified_evidence,
                lean_evidence,
                ["/identity/modified_ns"],
            ),
        )
    )
    wrapper_overflow_key = "leaf_overflow_secret_" + "o" * (
        2_000 - len("leaf_overflow_secret_")
    )
    wrapper_overflow_evidence = copy.deepcopy(lean_evidence)
    wrapper_overflow_evidence[wrapper_overflow_key] = "leaf_overflow_secret_value"
    wrapper_overflow = copy.deepcopy(valid)
    wrapper_overflow["execution_route"]["direct_lean_pre_execution"] = (
        wrapper_overflow_evidence
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_structural_leaf_2000_byte_extra",
            canonical_nested_stdout(wrapper_overflow),
            (wrapper_overflow_key, "leaf_overflow_secret_value"),
        )
    )
    injection_key = (
        'leaf_newline\n_escape\x1b_quote"_slash\\_comma,_semicolon;_bidi\u202e_'
        "observed_evidence_sha256=fake"
    )
    injection_evidence = copy.deepcopy(lean_evidence)
    injection_evidence[injection_key] = "leaf_injection_secret_value"
    injection_candidate = copy.deepcopy(valid)
    injection_candidate["execution_route"]["direct_lean_pre_execution"] = (
        injection_evidence
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_structural_leaf_injection_redacted",
            canonical_nested_stdout(injection_candidate),
            (injection_key, "leaf_injection_secret_value"),
        )
    )
    for extra_count in (16, 17):
        count_evidence = copy.deepcopy(lean_evidence)
        count_keys = tuple(f"count_{index:02d}" for index in range(extra_count))
        count_evidence.update(
            {
                key: f"count_secret_value_{index:02d}"
                for index, key in enumerate(count_keys)
            }
        )
        count_candidate = copy.deepcopy(valid)
        count_candidate["execution_route"]["direct_lean_pre_execution"] = count_evidence
        controls.append(
            expect_production_wrapper_redaction(
                f"nested_production_wrapper_structural_leaf_{extra_count}_extra_fields",
                canonical_nested_stdout(count_candidate),
                tuple(count_keys)
                + tuple(
                    f"count_secret_value_{index:02d}" for index in range(extra_count)
                ),
            )
        )
    for key_bytes in (128, 2_000):
        threshold_key = "p" * key_bytes
        threshold_evidence = copy.deepcopy(lean_evidence)
        threshold_evidence[threshold_key] = "path_threshold_secret_value"
        threshold_candidate = copy.deepcopy(valid)
        threshold_candidate["execution_route"]["direct_lean_pre_execution"] = (
            threshold_evidence
        )
        controls.append(
            expect_production_wrapper_redaction(
                f"nested_production_wrapper_structural_leaf_{key_bytes}_byte_key",
                canonical_nested_stdout(threshold_candidate),
                (threshold_key, "path_threshold_secret_value"),
            )
        )
    missing_leaf_evidence = copy.deepcopy(lean_evidence)
    del missing_leaf_evidence["identity"]["device"]
    missing_leaf_candidate = copy.deepcopy(valid)
    missing_leaf_candidate["execution_route"]["direct_lean_pre_execution"] = (
        missing_leaf_evidence
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_structural_leaf_missing_known_field",
            canonical_nested_stdout(missing_leaf_candidate),
            ("device",),
        )
    )
    wrong_type_leaf_evidence = copy.deepcopy(lean_evidence)
    wrong_type_leaf_evidence["identity"]["device"] = "leaf_type_secret_value"
    wrong_type_leaf_candidate = copy.deepcopy(valid)
    wrong_type_leaf_candidate["execution_route"]["direct_lean_pre_execution"] = (
        wrong_type_leaf_evidence
    )
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_structural_leaf_wrong_type",
            canonical_nested_stdout(wrong_type_leaf_candidate),
            ("leaf_type_secret_value",),
        )
    )
    all_known_leaf_values = copy.deepcopy(lean_evidence)
    all_known_leaf_values["bytes"] += 1
    all_known_leaf_values["canonical_path"] += ".changed"
    all_known_leaf_values["launch_path"] += ".changed"
    all_known_leaf_values["sha256"] = "f" * 64
    for identity_key in (
        "changed_ns",
        "device",
        "inode",
        "links",
        "mode",
        "modified_ns",
        "size",
    ):
        all_known_leaf_values["identity"][identity_key] += 1
    all_known_leaf_values["identity"]["permissions"] = "0o700"
    all_known_candidate = copy.deepcopy(valid)
    all_known_candidate["execution_route"]["direct_lean_pre_execution"] = (
        all_known_leaf_values
    )
    all_known_paths = sorted(checker.NESTED_EXECUTABLE_EVIDENCE_VALUE_POINTERS)
    require(len(all_known_paths) == 12, "typed evidence pointer allowlist drifted")
    controls.append(
        expect_production_wrapper_typed_leaf(
            "nested_production_wrapper_typed_all_12_known_leaf_values",
            all_known_candidate,
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean pre-execution evidence",
                all_known_leaf_values,
                lean_evidence,
                all_known_paths,
            ),
        )
    )
    late_semantic = copy.deepcopy(valid)
    late_semantic["boundary"] = "late_semantic_secret"
    controls.append(
        expect_production_wrapper_redaction(
            "nested_production_wrapper_late_semantic_failure",
            canonical_nested_stdout(late_semantic),
            ("late_semantic_secret",),
        )
    )
    require(
        checker.nested_executable_mismatch_is_boundary_safe(
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean pre-execution evidence",
                wrapper_modified_evidence,
                lean_evidence,
                ["/identity/modified_ns"],
            )
        )
        and not checker.nested_executable_mismatch_is_boundary_safe(
            expected_mismatch_diagnostic(
                "nested Lean kernel direct forged pre-execution evidence",
                wrapper_modified_evidence,
                lean_evidence,
                ["/identity/modified_ns"],
            )
        )
        and not checker.nested_executable_mismatch_is_boundary_safe(
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean forged-execution evidence",
                wrapper_modified_evidence,
                lean_evidence,
                ["/identity/modified_ns"],
            )
        ),
        "typed leaf boundary recognizer accepted a forged role or phase",
    )
    safe_leaf_diagnostic = expected_mismatch_diagnostic(
        "nested Lean kernel direct lean pre-execution evidence",
        wrapper_modified_evidence,
        lean_evidence,
        ["/identity/modified_ns"],
    )
    detail_prefix, detail_and_digests = safe_leaf_diagnostic.split(" at fields: ", 1)
    _safe_detail, digest_suffix = detail_and_digests.split(
        "; observed_evidence_sha256=", 1
    )

    def forged_leaf_detail(detail: str) -> str:
        return (
            detail_prefix
            + " at fields: "
            + detail
            + "; observed_evidence_sha256="
            + digest_suffix
        )

    forged_leaf_details = (
        '["not-a-json-pointer"]',
        '["/SECRET_FORGED_LABEL"]',
        '["/identity"]',
        '["/z","/a"]',
        '["/ok"]\nforged_label',
        checker.MISMATCH_OVERFLOW_MARKER,
        json.dumps(["/" + "x" * 128], separators=(",", ":")),
        json.dumps(
            [f"/field_{index:02d}" for index in range(17)],
            separators=(",", ":"),
        ),
    )
    require(
        all(
            not checker.nested_executable_mismatch_is_boundary_safe(
                forged_leaf_detail(detail)
            )
            for detail in forged_leaf_details
        ),
        "typed leaf boundary recognizer accepted a malformed field inventory",
    )
    modified_ns_nested = copy.deepcopy(lean_evidence)
    modified_ns_nested["identity"]["modified_ns"] = 2
    controls.append(
        expect_exact_failure(
            "nested_regression_lean_post_snapshot_drift",
            lambda: checker.validate_nested_executable_evidence(
                modified_ns_nested,
                tool_root / "bin/lean",
                lean_evidence,
                "nested Lean kernel direct lean post-execution evidence",
            ),
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean post-execution evidence",
                modified_ns_nested,
                lean_evidence,
                ["/identity/modified_ns"],
            ),
        )
    )
    evidence_role = "nested Lean kernel direct lean pre-execution evidence"
    too_many_observed_fields = copy.deepcopy(lean_evidence)
    extra_names = tuple(f"observed_secret_extra_{index:02d}" for index in range(17))
    too_many_observed_fields.update(
        {
            name: f"observed_secret_value_{index:02d}"
            for index, name in enumerate(extra_names)
        }
    )
    controls.append(
        expect_structural_evidence_failure(
            "nested_regression_observed_mismatch_field_count_bound",
            too_many_observed_fields,
            lean_evidence,
            evidence_role,
            forbidden=extra_names
            + tuple(too_many_observed_fields[name] for name in extra_names),
        )
    )
    for key_bytes in (129, 2_000):
        oversized_name = f"observed_{key_bytes}_byte_secret_" + "x" * (
            key_bytes - len(f"observed_{key_bytes}_byte_secret_")
        )
        require(
            len(oversized_name.encode("utf-8")) == key_bytes,
            "oversized observed field-name fixture drifted",
        )
        oversized_observed = copy.deepcopy(lean_evidence)
        oversized_observed[oversized_name] = "observed_oversized_secret_value"
        controls.append(
            expect_structural_evidence_failure(
                f"nested_regression_observed_mismatch_field_name_{key_bytes}_byte_bound",
                oversized_observed,
                lean_evidence,
                evidence_role,
                forbidden=(oversized_name, "observed_oversized_secret_value"),
            )
        )
    path_type_observed = copy.deepcopy(lean_evidence)
    path_type_observed["launch_path"] = "observed_secret_launch_value"
    path_type_observed["identity"]["device"] = "observed_secret_device_value"
    controls.append(
        expect_structural_evidence_failure(
            "nested_regression_observed_path_and_type_mismatch",
            path_type_observed,
            lean_evidence,
            evidence_role,
            forbidden=(
                "observed_secret_launch_value",
                "observed_secret_device_value",
            ),
        )
    )
    combined_name_observed = copy.deepcopy(lean_evidence)
    combined_names = tuple(
        f"observed_combined_secret_{index:02d}_" + "q" * 88 for index in range(8)
    )
    require(
        all(
            len(name.encode("utf-8")) <= checker.MISMATCH_FIELD_PATH_BYTES_MAX - 1
            for name in combined_names
        ),
        "combined observed field-name fixture exceeded the per-path bound",
    )
    combined_name_observed.update(
        {name: "observed_combined_secret_value" for name in combined_names}
    )
    controls.append(
        expect_structural_evidence_failure(
            "nested_regression_observed_combined_field_names_message_bound",
            combined_name_observed,
            lean_evidence,
            evidence_role,
            forbidden=combined_names + ("observed_combined_secret_value",),
        )
    )
    oversized_role = "role_secret_" + "r" * 900
    controls.append(
        expect_structural_evidence_failure(
            "nested_regression_mismatch_diagnostic_role_byte_bound",
            modified_ns_nested,
            lean_evidence,
            oversized_role,
            forbidden=(oversized_role,),
        )
    )
    lexical_outer_expected = copy.deepcopy(lean_evidence)
    lexical_outer_expected["launch_path"] = (
        "/var/folders/pid-rs-lexical-alias/lean-4.32.2-darwin_aarch64/bin/lean"
    )
    require(
        checker.differing_json_field_paths(lean_evidence, lexical_outer_expected)
        == ["/launch_path"],
        "source-reproduced Q1 counterexample was not exclusive to /launch_path",
    )
    controls.append(
        expect_exact_failure(
            "nested_regression_exact_q1_launch_path_counterexample",
            lambda: checker.validate_nested_executable_evidence(
                lean_evidence,
                tool_root / "bin/lean",
                lexical_outer_expected,
                "nested Lean kernel direct lean pre-execution evidence",
            ),
            expected_mismatch_diagnostic(
                "nested Lean kernel direct lean pre-execution evidence",
                lean_evidence,
                lexical_outer_expected,
                ["/launch_path"],
            ),
        )
    )
    aliased_outer_evidence = copy.deepcopy(expected_executable_evidence)
    aliased_outer_evidence["lean"]["launch_path"] = (
        "/var/folders/pid-rs-lexical-alias/lean-4.32.2-darwin_aarch64/bin/lean"
    )
    controls.append(
        expect_failure(
            "nested_regression_outer_lexical_launch_path_alias",
            lambda: checker.validate_nested_kernel_regression_result(
                valid,
                tool_root,
                "darwin-aarch64",
                checker.NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
                EXPECTED_METADATA_SHA256,
                METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
                "aarch64-apple-darwin",
                aliased_outer_evidence,
            ),
            'outer live executable snapshot at fields: ["/launch_path"]',
        )
    )
    aliased_helper_snapshot = checker.ExecutableSnapshot(
        launch_path=Path("/var/folders/pid-rs-lexical-alias/bin/helper"),
        launch_identity=helper_identity,
        launch_target=None,
        canonical_path=Path("/private/var/folders/pid-rs-lexical-alias/bin/helper"),
        canonical_identity=helper_identity,
        data=b"lean",
        sha256=hashlib.sha256(b"lean").hexdigest(),
    )
    controls.append(
        expect_failure(
            "outer_executable_evidence_rejects_lexical_launch_path_alias",
            lambda: checker.nested_executable_evidence_from_outer(
                aliased_helper_snapshot
            ),
            "launch path is not canonical",
        )
    )
    for key in sorted(checker.EXPECTED_NESTED_SCOPE_BOUNDARY):
        controls.append(
            expect_failure(
                f"nested_regression_scope_boundary_{key}",
                lambda key=key: checker.validate_nested_kernel_regression_result(
                    mutated(
                        "scope_boundary",
                        key,
                        value=_wrong_scalar(
                            checker.EXPECTED_NESTED_SCOPE_BOUNDARY[key]
                        ),
                    ),
                    tool_root,
                    "darwin-aarch64",
                    checker.NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
                    EXPECTED_METADATA_SHA256,
                    METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
                    "aarch64-apple-darwin",
                    expected_executable_evidence,
                ),
                "scope boundary",
            )
        )
    controls.append(
        expect_failure(
            "nested_regression_selected_outer_bound",
            lambda: checker.validate_nested_kernel_regression_result(
                valid,
                tool_root,
                "darwin-aarch64",
                3899,
                EXPECTED_METADATA_SHA256,
                METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
                "aarch64-apple-darwin",
                expected_executable_evidence,
            ),
            "selected outer bound drifted or is contradictory",
        )
    )
    python = Path(sys.executable)
    nested_checker = ROOT / "scripts/check-lean-kernel-14576.py"
    valid_command = checker.nested_kernel_regression_command(
        python, nested_checker, tool_root
    )
    checker.validate_nested_kernel_regression_command(
        valid_command, python, nested_checker, tool_root
    )
    controls.append(
        expect_failure(
            "nested_regression_command_missing_shared_group_flag",
            lambda: checker.validate_nested_kernel_regression_command(
                valid_command[:-1], python, nested_checker, tool_root
            ),
            "command route drifted",
        )
    )
    substituted = list(valid_command)
    substituted[-2] = os.fspath(tool_root.parent / "substituted")
    controls.append(
        expect_failure(
            "nested_regression_command_toolchain_substitution",
            lambda: checker.validate_nested_kernel_regression_command(
                substituted, python, nested_checker, tool_root
            ),
            "command route drifted",
        )
    )
    positive_controls: list[dict[str, object]] = []
    secret_failure = checker.ProcessResult(
        7,
        b"sensitive synthetic stdout",
        b"sensitive synthetic stderr",
    )
    failure_diagnostic = checker.failed_process_digest_diagnostic(
        secret_failure, "nested Lean kernel regression checker"
    )
    expected_failure_diagnostic = (
        "nested Lean kernel regression checker failed with exit 7; "
        "stdout_bytes=26; stdout_sha256="
        + hashlib.sha256(secret_failure.stdout).hexdigest()
        + "; stderr_bytes=26; stderr_sha256="
        + hashlib.sha256(secret_failure.stderr).hexdigest()
    )
    require(
        failure_diagnostic == expected_failure_diagnostic
        and "sensitive" not in failure_diagnostic,
        "nested nonzero process diagnostic leaked stream bytes or lost digest custody",
    )
    positive_controls.append(
        {
            "name": "nested_nonzero_process_reports_only_stream_counts_and_digests",
            "accepted": True,
            "raw_stream_values_disclosed": False,
            "asset_qualification_credit": "none",
        }
    )
    bounded_field_paths = checker.differing_json_field_paths(
        {
            "unexpected": 0,
            "present": True,
            "identity": {"modified_ns": 2},
        },
        {
            "identity": {"modified_ns": 1},
            "missing": 0,
            "present": 1,
        },
    )
    require(
        bounded_field_paths
        == [
            "/identity/modified_ns",
            "/missing",
            "/present",
            "/unexpected",
        ],
        "bounded field-name diagnostics lost recursive, key, order, or type closure",
    )
    require(
        checker.differing_json_field_paths({"a/b~c": 1}, {"a/b~c": 2}) == ["/a~1b~0c"],
        "field-name diagnostics lost RFC 6901 key escaping",
    )
    positive_controls.append(
        {
            "name": "helper_only_field_path_inventory_preserves_recursive_key_and_type_closure",
            "accepted": True,
            "production_typed_passthrough": False,
            "reported_paths": bounded_field_paths,
            "reported_values": False,
        }
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-nested-wrapper-selftest-"
    ) as temporary:
        container = Path(temporary).resolve(strict=True)
        real_parent = container / "real-parent"
        alias_parent = container / "alias-parent"
        real_parent.mkdir()
        alias_parent.symlink_to(real_parent, target_is_directory=True)
        lexical_private_root = alias_parent / "private-root"
        lexical_private_root.mkdir(mode=0o700)
        require(
            Path(os.path.abspath(os.fspath(lexical_private_root)))
            != lexical_private_root.resolve(strict=True),
            "synthetic parent-alias route was not lexically distinct",
        )
        private_root = checker.canonicalize_existing_directory(
            lexical_private_root, "synthetic aliased private root"
        )
        require(
            private_root == real_parent / "private-root",
            "synthetic parent alias did not normalize to the exact real directory",
        )
        require(
            checker.identity_from_stat(lexical_private_root.lstat())
            == checker.identity_from_stat(private_root.lstat())
            and stat.S_IMODE(private_root.lstat().st_mode) == 0o700,
            "synthetic parent alias did not retain exact endpoint identity and mode",
        )
        controls.append(
            expect_failure(
                "final_component_directory_symlink_rejected_during_canonicalization",
                lambda: checker.canonicalize_existing_directory(
                    alias_parent, "synthetic final-component symlink"
                ),
                "is not a direct directory",
            )
        )
        controls.append(
            expect_failure(
                "noncanonical_existing_directory_rejected_before_nested_execution",
                lambda: checker.require_canonical_existing_directory(
                    lexical_private_root, "synthetic aliased private root"
                ),
                "path is not canonical",
            )
        )
        positive_controls.append(
            {
                "name": "lexical_parent_alias_normalized_before_executable_snapshots",
                "accepted": True,
                "lexical_and_canonical_paths_distinct_before_normalization": True,
                "asset_qualification_credit": "none",
            }
        )
        live_tool_root = private_root / "lean-4.32.2-darwin_aarch64"
        live_bin = live_tool_root / "bin"
        live_bin.mkdir(parents=True)
        for role in ("lean", "lake", "leanchecker"):
            leaf = live_bin / role
            leaf.write_text(f"synthetic {role}\n", encoding="ascii")
            leaf.chmod(0o755)
        (private_root / "home").mkdir()
        (private_root / "tmp").mkdir()
        live_snapshots = {
            role: checker.snapshot_executable(live_bin / role, f"synthetic {role}")
            for role in ("lean", "lake", "leanchecker")
        }
        fresh_pre_nested_snapshots = checker.snapshot_tool_executables(
            live_tool_root, "synthetic immediate pre-nested snapshot"
        )
        checker.require_executable_snapshot_sets_equal(
            live_snapshots,
            fresh_pre_nested_snapshots,
            "synthetic probe-to-pre-nested custody",
        )
        fresh_post_nested_snapshots = checker.snapshot_tool_executables(
            live_tool_root, "synthetic immediate post-nested snapshot"
        )
        checker.require_executable_snapshot_sets_equal(
            fresh_pre_nested_snapshots,
            fresh_post_nested_snapshots,
            "synthetic pre/post-nested custody",
        )
        baseline_lean_snapshot = fresh_post_nested_snapshots["lean"]
        baseline_lean_identity = baseline_lean_snapshot.canonical_identity
        identity_drift_cases = (
            (
                "device",
                replace(
                    baseline_lean_identity, device=baseline_lean_identity.device + 1
                ),
            ),
            (
                "inode",
                replace(baseline_lean_identity, inode=baseline_lean_identity.inode + 1),
            ),
            (
                "changed_ns",
                replace(
                    baseline_lean_identity,
                    changed_ns=baseline_lean_identity.changed_ns + 1,
                ),
            ),
            (
                "modified_ns",
                replace(
                    baseline_lean_identity,
                    modified_ns=baseline_lean_identity.modified_ns + 1,
                ),
            ),
        )
        for field, drifted_identity in identity_drift_cases:
            drifted_post_snapshots = dict(fresh_post_nested_snapshots)
            drifted_post_snapshots["lean"] = replace(
                baseline_lean_snapshot,
                launch_identity=drifted_identity,
                canonical_identity=drifted_identity,
            )
            controls.append(
                expect_failure(
                    f"fresh_pre_post_nested_full_snapshot_{field}_drift",
                    lambda drifted_post_snapshots=drifted_post_snapshots: (
                        checker.require_executable_snapshot_sets_equal(
                            fresh_pre_nested_snapshots,
                            drifted_post_snapshots,
                            "synthetic pre/post-nested custody",
                        )
                    ),
                    "lean full snapshot changed",
                )
            )
        coherent_drifted_data = (
            bytes([baseline_lean_snapshot.data[0] ^ 1])
            + baseline_lean_snapshot.data[1:]
        )
        require(
            len(coherent_drifted_data) == len(baseline_lean_snapshot.data)
            and coherent_drifted_data != baseline_lean_snapshot.data,
            "coherent executable data-drift fixture changed size or not content",
        )
        coherent_drifted_post_snapshots = dict(fresh_post_nested_snapshots)
        coherent_drifted_post_snapshots["lean"] = replace(
            baseline_lean_snapshot,
            data=coherent_drifted_data,
            sha256=hashlib.sha256(coherent_drifted_data).hexdigest(),
        )
        controls.append(
            expect_failure(
                "fresh_pre_post_nested_full_snapshot_coherent_data_sha256_drift",
                lambda: checker.require_executable_snapshot_sets_equal(
                    fresh_pre_nested_snapshots,
                    coherent_drifted_post_snapshots,
                    "synthetic pre/post-nested custody",
                ),
                "lean full snapshot changed",
            )
        )
        positive_controls.append(
            {
                "name": "fresh_outer_snapshots_retained_and_full_compared_immediately_pre_and_post_nested",
                "accepted": True,
                "snapshot_fields": [
                    "launch_path",
                    "launch_identity",
                    "launch_target",
                    "canonical_path",
                    "canonical_identity",
                    "data",
                    "sha256",
                ],
                "asset_qualification_credit": "none",
            }
        )
        live_leaves = {
            role: {
                "mode": "0755",
                "path": f"bin/{role}",
                "sha256": snapshot.sha256,
                "size": len(snapshot.data),
            }
            for role, snapshot in live_snapshots.items()
        }
        checker.require_executable_snapshots_match_tree_leaves(
            live_tool_root,
            live_snapshots,
            live_leaves,
            "synthetic pre-nested reviewed-tree binding",
        )
        for name, leaf_key, value, reason in (
            (
                "pre_nested_tree_leaf_path_substitution",
                "path",
                "bin/lake",
                "live path differs from tree leaf",
            ),
            (
                "pre_nested_tree_leaf_size_substitution",
                "size",
                len(live_snapshots["lean"].data) + 1,
                "live size/SHA-256 differs from tree leaf",
            ),
            (
                "pre_nested_tree_leaf_sha256_substitution",
                "sha256",
                "0" * 64,
                "live size/SHA-256 differs from tree leaf",
            ),
            (
                "pre_nested_tree_leaf_mode_substitution",
                "mode",
                "0644",
                "mode must be 0755",
            ),
        ):
            mutated_leaves = copy.deepcopy(live_leaves)
            mutated_leaves["lean"][leaf_key] = value
            controls.append(
                expect_failure(
                    name,
                    lambda mutated_leaves=mutated_leaves: (
                        checker.require_executable_snapshots_match_tree_leaves(
                            live_tool_root,
                            live_snapshots,
                            mutated_leaves,
                            "synthetic pre-nested reviewed-tree binding",
                        )
                    ),
                    reason,
                )
            )
        two_link_identity = replace(
            live_snapshots["lean"].canonical_identity,
            links=2,
        )
        two_link_snapshots = dict(live_snapshots)
        two_link_snapshots["lean"] = replace(
            live_snapshots["lean"],
            launch_identity=two_link_identity,
            canonical_identity=two_link_identity,
        )
        controls.append(
            expect_failure(
                "pre_nested_tree_leaf_link_count_substitution",
                lambda: checker.require_executable_snapshots_match_tree_leaves(
                    live_tool_root,
                    two_link_snapshots,
                    live_leaves,
                    "synthetic pre-nested reviewed-tree binding",
                ),
                "live mode/link identity differs from tree leaf",
            )
        )
        positive_controls.append(
            {
                "name": "outer_live_snapshots_bound_to_independently_scanned_tree_leaves_before_nested_execution",
                "accepted": True,
                "bound_fields": ["path", "size", "sha256", "mode", "links"],
                "asset_qualification_credit": "none",
            }
        )

        child_measurement_source = """\
import hashlib
import json
import os
import pathlib
import stat
import sys

result = {}
for role, raw_path in zip(('lean', 'lake', 'leanchecker'), sys.argv[1:], strict=True):
    path = pathlib.Path(raw_path)
    launch = path.lstat()
    canonical = path.resolve(strict=True)
    before = canonical.lstat()
    data = canonical.read_bytes()
    after = canonical.lstat()
    fields = lambda item: (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )
    if fields(launch) != fields(before) or fields(before) != fields(after) or not stat.S_ISREG(before.st_mode):
        raise SystemExit(91)
    result[role] = {
        'bytes': len(data),
        'canonical_path': os.fspath(canonical),
        'identity': {
            'changed_ns': before.st_ctime_ns,
            'device': before.st_dev,
            'inode': before.st_ino,
            'links': before.st_nlink,
            'mode': before.st_mode,
            'modified_ns': before.st_mtime_ns,
            'permissions': oct(stat.S_IMODE(before.st_mode)),
            'size': before.st_size,
        },
        'launch_path': os.fspath(path),
        'sha256': hashlib.sha256(data).hexdigest(),
    }
sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\\n')
"""

        def independently_measure_child_leaves(
            phase: str,
        ) -> dict[str, object]:
            child_measurement = checker.run_bounded_process(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    child_measurement_source,
                    *(
                        os.fspath(live_bin / role)
                        for role in ("lean", "lake", "leanchecker")
                    ),
                ],
                private_root,
                {"LANG": "C", "LC_ALL": "C", "PATH": os.defpath},
                LIMITS,
            )
            require(
                child_measurement.returncode == 0
                and child_measurement.stderr == b""
                and child_measurement.stdout.endswith(b"\n")
                and child_measurement.stdout.count(b"\n") == 1,
                f"independent child {phase} leaf measurement process failed",
            )
            child_evidence = checker.parse_json_object(
                child_measurement.stdout,
                f"independent child {phase} leaf evidence",
            )
            require(
                child_measurement.stdout
                == checker.canonical_json_bytes(child_evidence) + b"\n",
                f"independent child {phase} leaf evidence was not canonical JSON",
            )
            checker.exact_keys(
                child_evidence,
                {"lean", "lake", "leanchecker"},
                f"independent child {phase} leaf evidence",
            )
            return child_evidence

        child_pre_evidence = independently_measure_child_leaves("pre")
        child_post_evidence = independently_measure_child_leaves("post")
        require(
            child_post_evidence == child_pre_evidence,
            "independently measured child pre/post leaf evidence drifted",
        )
        for role, snapshot in live_snapshots.items():
            expected = checker.nested_executable_evidence_from_outer(snapshot)
            for phase, evidence in (
                ("pre", child_pre_evidence),
                ("post", child_post_evidence),
            ):
                checker.validate_nested_executable_evidence(
                    evidence[role],
                    live_bin / role,
                    expected,
                    f"nested Lean kernel direct {role} {phase}-execution evidence",
                )
        positive_controls.append(
            {
                "name": "independent_isolated_children_derive_equal_pre_post_leaf_evidence_without_outer_json_injection",
                "accepted": True,
                "child_flags": ["-I", "-S", "-B"],
                "asset_qualification_credit": "none",
            }
        )
        live_valid = copy.deepcopy(valid)
        live_valid["lean"]["platform"] = "aarch64-apple-darwin"
        live_route = live_valid["execution_route"]
        live_route["direct_toolchain_root"] = os.fspath(live_tool_root)
        live_route["leanchecker_fresh_environment_child_path_prefix"] = os.fspath(
            live_bin
        )
        for role, snapshot in live_snapshots.items():
            evidence = checker.nested_executable_evidence_from_outer(snapshot)
            live_route[f"direct_{role}_pre_execution"] = evidence
            live_route[f"direct_{role}_post_execution"] = evidence

        nested_checker_baseline = checker.snapshot_bound_nested_checker(METADATA)
        original_command_builder = checker.nested_kernel_regression_command
        original_command_validator = checker.validate_nested_kernel_regression_command

        def run_wrapper_case(
            case_name: str,
            returncode: int,
            payload: str,
            expected_failure: tuple[str, str] | None = None,
            stderr_payload: str = "",
        ) -> dict[str, object] | None:
            ready = private_root / f"nested-{case_name}.ready"
            marker = private_root / f"nested-{case_name}.survived"
            base = early_exit_descendant_command(ready, marker, returncode)
            leader = base[5]
            emitting_leader = leader.replace(
                "raise SystemExit(int(sys.argv[3]))",
                "sys.stdout.write(sys.argv[5] + '\\n');"
                "sys.stderr.write(sys.argv[6]);"
                "raise SystemExit(int(sys.argv[3]))",
            )
            injected_command = [
                *base[:5],
                emitting_leader,
                *base[6:],
                payload,
                stderr_payload,
            ]
            calls = {"builder": 0, "validator": 0}

            def injected_builder(
                python: Path, checker_source: Path, direct_root: Path
            ) -> list[str]:
                require(
                    python == Path(sys.executable)
                    and checker_source == nested_checker_baseline.path
                    and direct_root == live_tool_root,
                    "synthetic nested-wrapper command seam inputs drifted",
                )
                calls["builder"] += 1
                return list(injected_command)

            def injected_validator(
                command: list[str],
                python: Path,
                checker_source: Path,
                direct_root: Path,
            ) -> None:
                require(
                    command == injected_command
                    and python == Path(sys.executable)
                    and checker_source == nested_checker_baseline.path
                    and direct_root == live_tool_root,
                    "synthetic nested-wrapper command validation seam drifted",
                )
                calls["validator"] += 1

            checker.nested_kernel_regression_command = injected_builder
            checker.validate_nested_kernel_regression_command = injected_validator
            try:

                def operation() -> dict[str, object]:
                    return checker.run_nested_kernel_regression(
                        live_tool_root,
                        private_root,
                        LIMITS,
                        "darwin-aarch64",
                        nested_checker_baseline,
                        METADATA,
                        {"lean_platform": "aarch64-apple-darwin"},
                        live_snapshots,
                    )

                if expected_failure is None:
                    observed = operation()
                    require(
                        observed["status"] == "executed_same_transaction_checks_passed"
                        and observed[
                            "outer_supervisor_group_cleanup_after_nested_outcome"
                        ]
                        is True,
                        "synthetic nested-wrapper positive result drifted",
                    )
                else:
                    failure_name, reason = expected_failure
                    failure_control = expect_exact_failure(
                        failure_name,
                        operation,
                        reason,
                    )
                    require(
                        failure_control.pop("exact_reason") == reason,
                        "nested-wrapper exact failure record drifted",
                    )
                    failure_control["exact_reason_verified"] = True
                    failure_control["diagnostic_values_retained_in_output"] = False
                    controls.append(failure_control)
                    observed = None
            finally:
                checker.nested_kernel_regression_command = original_command_builder
                checker.validate_nested_kernel_regression_command = (
                    original_command_validator
                )
            require(
                calls == {"builder": 1, "validator": 1},
                "synthetic nested-wrapper command seam was not traversed exactly once",
            )
            require_delayed_descendant_absent(
                marker,
                f"run_nested_kernel_regression {case_name} return code {returncode}",
            )
            return observed

        canonical_payload = json.dumps(
            live_valid,
            sort_keys=True,
            separators=(",", ":"),
        )
        run_wrapper_case("canonical-zero", 0, canonical_payload)
        positive_controls.append(
            {
                "name": "nested_wrapper_injected_output_wiring_and_zero_exit_cleanup",
                "accepted": True,
                "route": "real_run_nested_kernel_regression_with_injected_command",
                "child_execution_credit": "synthetic_only",
                "asset_qualification_credit": "none",
            }
        )
        run_wrapper_case(
            "nonzero",
            7,
            "nonzero_child_stdout_secret",
            (
                "nested_wrapper_early_leader_nonzero_exit_cleanup",
                checker.failed_process_digest_diagnostic(
                    checker.ProcessResult(
                        7,
                        b"nonzero_child_stdout_secret\n",
                        b"nonzero_child_stderr_secret\n",
                    ),
                    "nested Lean kernel regression checker",
                ),
            ),
            "nonzero_child_stderr_secret\n",
        )
        reversed_top_level = {
            key: live_valid[key] for key in reversed(tuple(live_valid))
        }
        noncanonical_order = json.dumps(
            reversed_top_level,
            sort_keys=False,
            separators=(",", ":"),
        )
        require(
            noncanonical_order != canonical_payload,
            "nested-wrapper key-order mutation was not distinct",
        )
        run_wrapper_case(
            "noncanonical-order",
            0,
            noncanonical_order,
            (
                "nested_wrapper_noncanonical_key_order",
                checker.nested_zero_exit_result_digest_diagnostic(
                    checker.ProcessResult(
                        0,
                        noncanonical_order.encode("ascii") + b"\n",
                        b"",
                    )
                ),
            ),
        )
        noncanonical_whitespace = json.dumps(live_valid, sort_keys=True)
        require(
            noncanonical_whitespace != canonical_payload,
            "nested-wrapper whitespace mutation was not distinct",
        )
        run_wrapper_case(
            "noncanonical-whitespace",
            0,
            noncanonical_whitespace,
            (
                "nested_wrapper_noncanonical_whitespace",
                checker.nested_zero_exit_result_digest_diagnostic(
                    checker.ProcessResult(
                        0,
                        noncanonical_whitespace.encode("ascii") + b"\n",
                        b"",
                    )
                ),
            ),
        )
        negative_zero = canonical_payload.replace('"trust":0', '"trust":-0', 1)
        require(
            negative_zero != canonical_payload,
            "nested-wrapper negative-zero mutation was not distinct",
        )
        run_wrapper_case(
            "negative-zero",
            0,
            negative_zero,
            (
                "nested_wrapper_negative_zero_spelling",
                checker.nested_zero_exit_result_digest_diagnostic(
                    checker.ProcessResult(
                        0,
                        negative_zero.encode("ascii") + b"\n",
                        b"",
                    )
                ),
            ),
        )
    return controls, positive_controls


def environment_controls() -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-env-") as temporary:
        root = Path(temporary) / "toolchain"
        bin_dir = root / "bin"
        bin_dir.mkdir(parents=True)
        for role in ("lean", "lake", "leanchecker"):
            leaf = bin_dir / role
            leaf.write_bytes(b"executable\n")
            leaf.chmod(0o755)
        home = Path(temporary) / "home"
        tmp = Path(temporary) / "tmp"
        home.mkdir()
        tmp.mkdir()
        environment = checker.build_child_environment(root, home, tmp)
        for name, mutation, expected in (
            (
                "environment_lean_sysroot",
                {**environment, "LEAN_SYSROOT": "/evil"},
                "whitelist drifted",
            ),
            (
                "environment_elan_toolchain",
                {**environment, "ELAN_TOOLCHAIN": "evil"},
                "whitelist drifted",
            ),
            (
                "environment_pythonpath",
                {**environment, "PYTHONPATH": "/evil"},
                "whitelist drifted",
            ),
            (
                "environment_missing_home",
                {key: value for key, value in environment.items() if key != "HOME"},
                "whitelist drifted",
            ),
            (
                "environment_path_precedence",
                {**environment, "PATH": "/usr/bin:" + os.fspath(bin_dir) + ":/bin"},
                "PATH precedence",
            ),
            (
                "environment_locale",
                {**environment, "LANG": "en_US.UTF-8"},
                "locale is not fixed",
            ),
        ):
            controls.append(
                expect_failure(
                    name,
                    lambda mutation=mutation: checker.validate_child_environment(
                        mutation, root
                    ),
                    expected,
                )
            )
        substituted = Path(temporary) / "substituted"
        substituted.mkdir()
        for role in ("lean", "lake", "leanchecker"):
            leaf = substituted / role
            leaf.write_bytes(b"substitution\n")
            leaf.chmod(0o755)
        mutated = dict(environment)
        mutated["PATH"] = os.fspath(substituted) + ":/usr/bin:/bin"
        controls.append(
            expect_failure(
                "environment_path_executable_substitution",
                lambda: checker.validate_child_environment(mutated, root),
                "PATH precedence drifted",
            )
        )
    return controls


def early_exit_descendant_command(
    ready: Path, marker: Path, returncode: int
) -> list[str]:
    descendant = """\
import pathlib
import sys
import time

pathlib.Path(sys.argv[1]).write_text(str(__import__('os').getpid()), encoding='ascii')
time.sleep(0.6)
pathlib.Path(sys.argv[2]).write_text('survived', encoding='ascii')
time.sleep(60)
"""
    leader = """\
import pathlib
import subprocess
import sys
import time

ready = pathlib.Path(sys.argv[1])
subprocess.Popen(
    [sys.executable, '-I', '-S', '-B', '-c', sys.argv[4], sys.argv[1], sys.argv[2]],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    close_fds=True,
)
deadline = time.monotonic() + 5
while not ready.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not ready.exists():
    raise SystemExit(99)
raise SystemExit(int(sys.argv[3]))
"""
    return [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-c",
        leader,
        os.fspath(ready),
        os.fspath(marker),
        str(returncode),
        descendant,
    ]


def require_delayed_descendant_absent(marker: Path, role: str) -> None:
    time.sleep(0.75)
    require(not marker.exists(), f"{role} delayed descendant survived group cleanup")


def process_controls() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    environment = {"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"}
    result = checker.run_bounded_process(
        ["/bin/sh", "-c", "printf ok"], Path("/"), environment, LIMITS
    )
    require(
        result == checker.ProcessResult(0, b"ok", b""),
        "bounded-process positive drifted",
    )
    overridden = checker.run_bounded_process(
        ["/bin/sh", "-c", "printf ok"],
        Path("/"),
        environment,
        LIMITS,
        timeout_seconds=1,
    )
    require(
        overridden == checker.ProcessResult(0, b"ok", b""),
        "bounded-process timeout override positive drifted",
    )
    positive_controls = [
        {
            "name": "bounded_process_zero_exit_baseline",
            "accepted": True,
            "route": "real_run_bounded_process",
        },
        {
            "name": "bounded_process_timeout_override_baseline",
            "accepted": True,
            "route": "real_run_bounded_process",
        },
    ]
    controls = [
        expect_failure(
            "process_relative_executable",
            lambda: checker.run_bounded_process(
                ["sh", "-c", "true"], Path("/"), environment, LIMITS
            ),
            "not absolute",
        ),
        expect_failure(
            "process_nonpositive_timeout_override",
            lambda: checker.run_bounded_process(
                ["/bin/sh", "-c", "true"],
                Path("/"),
                environment,
                LIMITS,
                timeout_seconds=0,
            ),
            "timeout must be positive",
        ),
    ]
    small = dict(LIMITS)
    small["child_output_bytes_max"] = 4
    controls.append(
        expect_failure(
            "process_stdout_ceiling",
            lambda: checker.run_bounded_process(
                ["/bin/sh", "-c", "printf 12345"], Path("/"), environment, small
            ),
            "stdout exceeds",
        )
    )
    controls.append(
        expect_failure(
            "process_stderr_ceiling",
            lambda: checker.run_bounded_process(
                ["/bin/sh", "-c", "printf 12345 >&2"], Path("/"), environment, small
            ),
            "stderr exceeds",
        )
    )
    fast_timeout = dict(LIMITS)
    fast_timeout["process_timeout_seconds"] = 1
    controls.append(
        expect_failure(
            "process_timeout",
            lambda: checker.run_bounded_process(
                ["/bin/sh", "-c", "while :; do :; done"],
                Path("/"),
                environment,
                fast_timeout,
            ),
            "exceeded 1 seconds",
        )
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-process-group-selftest-"
    ) as temporary:
        root = Path(temporary)
        for returncode in (0, 7):
            ready = root / f"bounded-{returncode}.ready"
            marker = root / f"bounded-{returncode}.survived"
            observed = checker.run_bounded_process(
                early_exit_descendant_command(ready, marker, returncode),
                Path("/"),
                environment,
                LIMITS,
            )
            require(
                observed.returncode == returncode,
                f"early-exit descendant baseline return code {returncode} drifted",
            )
            require_delayed_descendant_absent(
                marker, f"run_bounded_process return code {returncode}"
            )
            positive_controls.append(
                {
                    "name": f"bounded_process_early_leader_exit_{returncode}_cleanup",
                    "accepted": True,
                    "route": "real_run_bounded_process",
                }
            )

        ready = root / "exception.ready"
        marker = root / "exception.survived"
        command = early_exit_descendant_command(ready, marker, 0)
        original_popen = checker.subprocess.Popen

        class WaitExceptionProxy:
            def __init__(self, process: subprocess.Popen[bytes]) -> None:
                self._process = process
                self._raised = False

            @property
            def pid(self) -> int:
                return self._process.pid

            @property
            def returncode(self) -> int | None:
                return self._process.returncode

            def poll(self) -> int | None:
                return self._process.poll()

            def wait(self, timeout: float | None = None) -> int:
                if not self._raised:
                    deadline = time.monotonic() + 5
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self._raised = True
                    raise RuntimeError("synthetic wait failure")
                return self._process.wait(timeout=timeout)

        def raising_popen(*args: object, **kwargs: object) -> WaitExceptionProxy:
            return WaitExceptionProxy(original_popen(*args, **kwargs))

        checker.subprocess.Popen = raising_popen
        try:
            controls.append(
                expect_failure(
                    "process_unexpected_wait_exception_cleans_group",
                    lambda: checker.run_bounded_process(
                        command, Path("/"), environment, LIMITS
                    ),
                    "synthetic wait failure",
                    exception_type=RuntimeError,
                )
            )
        finally:
            checker.subprocess.Popen = original_popen
        require_delayed_descendant_absent(marker, "unexpected wait exception")

    return controls, positive_controls


def private_directory_umask_controls() -> list[dict[str, object]]:
    """Exercise the real creation/extraction helpers under hostile ambient umasks."""

    positives: list[dict[str, object]] = []
    for mask in (0o000, 0o777):
        temporary_context: tempfile.TemporaryDirectory[str] | None = None
        previous = os.umask(mask)
        try:
            temporary_context = tempfile.TemporaryDirectory(
                prefix=f"pid-rs-lean-private-umask-{mask:03o}-"
            )
            private_root = Path(temporary_context.name)
            checker.enforce_private_directory_mode(
                private_root, "self-test private temporary root"
            )
            home = private_root / "home"
            temporary = private_root / "tmp"
            destination = private_root / "tree"
            checker.create_private_directory(home, "self-test private HOME")
            checker.create_private_directory(temporary, "self-test private TMPDIR")
            checker.create_private_directory(
                destination, "self-test private extraction destination"
            )
            extracted = checker.extract_tar_stream(
                io.BytesIO(SYNTHETIC_TAR),
                destination,
                ASSETS["darwin-aarch64"],
                LIMITS,
                SYNTHETIC_RECORDS,
            )
            require(
                all(
                    stat.S_IMODE(path.lstat().st_mode) == 0o700
                    and not path.is_symlink()
                    for path in (private_root, home, temporary, destination)
                ),
                f"private directory 0700 enforcement drifted under umask {mask:03o}",
            )
            scanned = checker.scan_extracted_tree(destination, LIMITS)
            checker.require_same_tree(
                checker.entries_from_records(SYNTHETIC_RECORDS, extracted),
                scanned,
                f"hostile-umask extraction {mask:03o}",
            )
            require(
                checker.tree_manifest_sha256(scanned) == SYNTHETIC_MANIFEST_SHA256,
                f"hostile-umask manifest drifted under umask {mask:03o}",
            )
        finally:
            os.umask(previous)
            if temporary_context is not None:
                temporary_context.cleanup()
        positives.append(
            {
                "name": f"private_directory_and_extraction_umask_{mask:03o}",
                "accepted": True,
                "route": (
                    "real_private_root_home_tmp_destination_and_extraction_helpers"
                ),
            }
        )
    return positives


def write_synthetic_zstd_with_descendant(
    path: Path,
    ready: Path,
    marker: Path,
    returncode: int,
    stderr_bytes: bytes = b"",
) -> None:
    descendant = """\
import pathlib
import sys
import time

pathlib.Path(sys.argv[1]).write_text(str(__import__('os').getpid()), encoding='ascii')
time.sleep(0.6)
pathlib.Path(sys.argv[2]).write_text('survived', encoding='ascii')
time.sleep(60)
"""
    payload = f"""#!{sys.executable}
import pathlib
import subprocess
import sys
import time

ready = pathlib.Path({os.fspath(ready)!r})
subprocess.Popen(
    [sys.executable, '-I', '-S', '-B', '-c', {descendant!r},
     {os.fspath(ready)!r}, {os.fspath(marker)!r}],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    close_fds=True,
)
deadline = time.monotonic() + 5
while not ready.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not ready.exists():
    raise SystemExit(99)
sys.stdout.buffer.write(b'synthetic-zstd-stream')
sys.stderr.buffer.write({stderr_bytes!r})
raise SystemExit({returncode})
"""
    path.write_text(payload, encoding="utf-8")
    path.chmod(0o755)


def zstd_process_group_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    negatives: list[dict[str, object]] = []
    positives: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-zstd-group-selftest-"
    ) as temporary:
        root = Path(temporary)
        archive = root / "synthetic.tar.zst"
        archive.write_bytes(b"ignored")
        for returncode in (0, 7):
            ready = root / f"zstd-{returncode}.ready"
            marker = root / f"zstd-{returncode}.survived"
            executable = root / f"zstd-{returncode}"
            write_synthetic_zstd_with_descendant(executable, ready, marker, returncode)
            zstd = checker.snapshot_executable(executable, "synthetic zstd")
            if returncode == 0:
                value, consumed = checker.consume_zstd_archive(
                    archive,
                    zstd,
                    LIMITS,
                    lambda stream: stream.read(),
                )
                require(
                    value == b"synthetic-zstd-stream"
                    and consumed == len(b"synthetic-zstd-stream"),
                    "synthetic zstd success baseline drifted",
                )
                positives.append(
                    {
                        "name": "zstd_early_leader_zero_exit_cleanup",
                        "accepted": True,
                        "route": "real_consume_zstd_archive",
                    }
                )
            else:
                negatives.append(
                    expect_exact_failure(
                        "zstd_early_leader_nonzero_exit_cleanup",
                        lambda archive=archive, zstd=zstd: checker.consume_zstd_archive(
                            archive,
                            zstd,
                            LIMITS,
                            lambda stream: stream.read(),
                        ),
                        checker.fixed_process_stream_rejection_diagnostic(
                            "zstd decoder",
                            7,
                            len(b"synthetic-zstd-stream"),
                            hashlib.sha256(b"synthetic-zstd-stream").hexdigest(),
                            b"",
                        ),
                    )
                )
            require_delayed_descendant_absent(
                marker, f"consume_zstd_archive return code {returncode}"
            )

        ready = root / "zstd-stderr.ready"
        marker = root / "zstd-stderr.survived"
        executable = root / "zstd-stderr"
        secret_stderr = b"zstd_stderr_secret_" + b"s" * 2_000
        write_synthetic_zstd_with_descendant(
            executable, ready, marker, 0, secret_stderr
        )
        zstd = checker.snapshot_executable(executable, "synthetic zstd stderr")
        negatives.append(
            expect_exact_failure(
                "zstd_zero_exit_long_secret_stderr_digest_only",
                lambda: checker.consume_zstd_archive(
                    archive,
                    zstd,
                    LIMITS,
                    lambda stream: stream.read(),
                ),
                checker.fixed_process_stream_rejection_diagnostic(
                    "zstd decoder",
                    0,
                    len(b"synthetic-zstd-stream"),
                    hashlib.sha256(b"synthetic-zstd-stream").hexdigest(),
                    secret_stderr,
                ),
            )
        )
        require_delayed_descendant_absent(marker, "zstd long stderr")

        ready = root / "zstd-consumer-error.ready"
        marker = root / "zstd-consumer-error.survived"
        executable = root / "zstd-consumer-error"
        write_synthetic_zstd_with_descendant(executable, ready, marker, 0)
        zstd = checker.snapshot_executable(executable, "synthetic zstd")

        def fail_consumer(_stream: object) -> bytes:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            raise checker.CustodyError("synthetic zstd consumer failure")

        negatives.append(
            expect_failure(
                "zstd_consumer_exception_cleans_group",
                lambda: checker.consume_zstd_archive(
                    archive, zstd, LIMITS, fail_consumer
                ),
                "synthetic zstd consumer failure",
            )
        )
        require_delayed_descendant_absent(marker, "zstd consumer exception")
    return negatives, positives


def file_custody_controls() -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-file-custody-") as temporary:
        root = Path(temporary)
        archive = root / "archive.tar.zst"
        archive.write_bytes(b"archive\n")
        observed = checker.external_file_digest(archive, "synthetic archive")
        archive.write_bytes(b"mutated\n")
        replay = checker.external_file_digest(archive, "synthetic archive")
        controls.append(
            expect_failure(
                "archive_pre_post_mutation",
                lambda: checker.require_external_unchanged(
                    observed, replay, "synthetic archive"
                ),
                "identity changed",
            )
        )
        target = root / "target"
        target.write_bytes(b"target\n")
        symlink = root / "symlink"
        symlink.symlink_to(target)
        controls.append(
            expect_failure(
                "archive_symbolic_link",
                lambda: checker.external_file_digest(symlink, "symlink archive"),
                "not a regular file",
            )
        )
        hardlink = root / "hardlink"
        os.link(target, hardlink)
        controls.append(
            expect_failure(
                "archive_multiply_linked",
                lambda: checker.external_file_digest(target, "hardlinked archive"),
                "exactly one hard link",
            )
        )
        executable = root / "executable"
        executable.write_bytes(b"first\n")
        executable.chmod(0o755)
        executable_snapshot = checker.snapshot_executable(
            executable, "synthetic executable"
        )
        executable.write_bytes(b"second\n")
        controls.append(
            expect_failure(
                "executable_pre_post_mutation",
                lambda: checker.require_executable_unchanged(
                    executable_snapshot, "synthetic executable"
                ),
                "changed",
            )
        )
        executable_target = root / "executable-target"
        executable_target.write_bytes(b"target\n")
        executable_target.chmod(0o755)
        executable_link = root / "executable-link"
        executable_link.symlink_to(executable_target)
        link_snapshot = checker.snapshot_executable(
            executable_link, "linked executable"
        )
        controls.append(
            expect_failure(
                "extracted_executable_symlink_detection",
                lambda: checker.require(
                    link_snapshot.launch_target is None,
                    "extracted executable leaf is a symbolic link",
                ),
                "symbolic link",
            )
        )

        repo = root / "repo"
        scripts = repo / "scripts"
        scripts.mkdir(parents=True)
        regular = scripts / "source.py"
        regular.write_bytes(b"source\n")
        regular.chmod(0o644)
        original_root = checker.ROOT
        checker.ROOT = repo
        try:
            alternate = scripts / "alternate-source.py"
            alternate.write_bytes(b"source\n")
            alternate.chmod(0o644)
            original_open = checker.os.open

            def substituted_open(path: object, flags: int, *args: object) -> int:
                selected = alternate if Path(path) == regular else path
                return original_open(selected, flags, *args)

            checker.os.open = substituted_open
            try:
                controls.append(
                    expect_failure(
                        "repo_source_descriptor_substitution",
                        lambda: checker.snapshot_repo_file(
                            regular, "descriptor-substituted source"
                        ),
                        "identity changed during descriptor-bound double read",
                    )
                )
            finally:
                checker.os.open = original_open
            source_snapshot = checker.snapshot_repo_file(regular, "synthetic source")
            regular.write_bytes(b"changed\n")
            controls.append(
                expect_failure(
                    "repo_source_pre_post_mutation",
                    lambda: checker.require_repo_snapshot_unchanged(
                        source_snapshot, "synthetic source"
                    ),
                    "changed across",
                )
            )
            linked_source = scripts / "linked.py"
            linked_source.symlink_to(regular)
            controls.append(
                expect_failure(
                    "repo_source_symbolic_link",
                    lambda: checker.snapshot_repo_file(linked_source, "linked source"),
                    "not a regular file",
                )
            )
        finally:
            checker.ROOT = original_root
    return controls


def nested_checker_source_binding_controls() -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-nested-checker-binding-"
    ) as temporary:
        repo = Path(temporary) / "repo"
        scripts = repo / "scripts"
        scripts.mkdir(parents=True)
        source = scripts / "check-lean-kernel-14576.py"
        reviewed = (ROOT / "scripts/check-lean-kernel-14576.py").read_bytes()
        source.write_bytes(reviewed)
        source.chmod(0o644)
        binding: dict[str, object] = {
            "bytes": len(reviewed),
            "mode": "0644",
            "path": "scripts/check-lean-kernel-14576.py",
            "sha256": hashlib.sha256(reviewed).hexdigest(),
            "single_hard_link": True,
            "symbolic_link": False,
        }
        metadata = {"checker_binding": {"nested_checker_binding": binding}}
        original_root = checker.ROOT
        checker.ROOT = repo
        try:
            baseline = checker.snapshot_bound_nested_checker(metadata)
            checker.require_nested_checker_binding(baseline, binding)

            alternate = scripts / "alternate.py"
            alternate.write_bytes(reviewed)
            alternate.chmod(0o644)
            alternate_snapshot = checker.snapshot_repo_file(
                alternate, "alternate nested checker"
            )
            controls.append(
                expect_failure(
                    "nested_checker_runtime_path_substitution",
                    lambda: checker.require_nested_checker_binding(
                        alternate_snapshot, binding
                    ),
                    "repository path differs",
                )
            )

            source.write_bytes(reviewed + b"x")
            controls.append(
                expect_failure(
                    "nested_checker_runtime_size_substitution",
                    lambda: checker.snapshot_bound_nested_checker(metadata),
                    "byte-length binding drifted",
                )
            )
            source.write_bytes(b"R" + reviewed[1:])
            controls.append(
                expect_failure(
                    "nested_checker_runtime_sha_substitution",
                    lambda: checker.snapshot_bound_nested_checker(metadata),
                    "SHA-256 binding drifted",
                )
            )
            source.write_bytes(reviewed)

            source.chmod(0o600)
            controls.append(
                expect_failure(
                    "nested_checker_runtime_mode_substitution",
                    lambda: checker.snapshot_bound_nested_checker(metadata),
                    "permissions must be 0644",
                )
            )
            source.chmod(0o644)

            hardlink = scripts / "nested-hardlink.py"
            os.link(source, hardlink)
            controls.append(
                expect_failure(
                    "nested_checker_runtime_hardlink_substitution",
                    lambda: checker.snapshot_bound_nested_checker(metadata),
                    "exactly one hard link",
                )
            )
            hardlink.unlink()

            target = scripts / "nested-target.py"
            target.write_bytes(reviewed)
            target.chmod(0o644)
            source.unlink()
            source.symlink_to(target)
            controls.append(
                expect_failure(
                    "nested_checker_runtime_symlink_substitution",
                    lambda: checker.snapshot_bound_nested_checker(metadata),
                    "not a regular file",
                )
            )
        finally:
            checker.ROOT = original_root
    return controls


def historical_receipt_semantic_controls() -> list[dict[str, object]]:
    observation = METADATA["historical_nontransferable_observations"][0]
    receipt_path = ROOT / observation["source_receipt"]["path"]
    payload = checker.parse_json_object(
        receipt_path.read_bytes(), "historical semantic-control receipt"
    )
    checker.validate_historical_receipt_semantics(payload, observation)

    missing_pointer = copy.deepcopy(payload)
    del missing_pointer["lean_darwin_archive_observation"]
    wrong_outcome = copy.deepcopy(payload)
    wrong_outcome["lean_darwin_archive_observation"]["lean_milestone_credit"] = "none"
    wrong_nested_identity = copy.deepcopy(payload)
    wrong_nested_identity["lean_darwin_archive_observation"][
        "qualification_source_binding"
    ]["nested_checker_sha256"] = "0" * 64
    return [
        expect_failure(
            "historical_receipt_missing_json_pointer",
            lambda: checker.validate_historical_receipt_semantics(
                missing_pointer, observation
            ),
            "JSON pointer is absent",
        ),
        expect_failure(
            "historical_receipt_outcome_substitution",
            lambda: checker.validate_historical_receipt_semantics(
                wrong_outcome, observation
            ),
            "outcome drifted",
        ),
        expect_failure(
            "historical_receipt_nested_identity_substitution",
            lambda: checker.validate_historical_receipt_semantics(
                wrong_nested_identity, observation
            ),
            "prior_nested_checker identity drifted",
        ),
    ]


def validate_q1_failure_evidence(
    payload: dict[str, object], stdout_source: bytes, stderr_source: bytes
) -> None:
    root = checker.exact_keys(
        payload,
        {
            "archive_observation",
            "capture_boundary",
            "credit_boundary",
            "execution",
            "failure",
            "nonclaims",
            "p_binding",
            "schema",
            "status",
            "worktree_custody",
        },
        "Q1 retained failure evidence",
    )
    checker.require_exact_typed_value(
        root["schema"],
        "pid-rs/lean-toolchain-strict-replay-failure/v1",
        "Q1 retained failure schema",
    )
    checker.require_exact_typed_value(
        root["status"],
        "retained_negative_zero_credit",
        "Q1 retained failure status",
    )

    archive_identity = {
        "device": 16_777_231,
        "direct_regular_file": True,
        "gid": 0,
        "inode": 795_962_933,
        "mode": "0400",
        "sha256": ("ea99ead969901b9fe4c7e7bf350b812a0249e9a5cea20474a737c0cc64746bc0"),
        "single_hard_link": True,
        "size": 550_165_784,
        "symbolic_link": False,
        "uid": 501,
    }
    checker.validate_exact_typed_object(
        root["archive_observation"],
        {
            "archive_path": (
                "/private/tmp/pid-rs-lean4322-darwin.orHE2a/"
                "lean-4.32.2-darwin_aarch64.tar.zst"
            ),
            "archive_path_nonportable": True,
            "checker_archive_postcheck_reached": False,
            "exact_mtime_scalar_retained": False,
            "external_postcheck": archive_identity,
            "external_precheck": archive_identity,
            "failure_auditor_archive_access": "none",
            "pre_post_identity_equal": True,
            "pre_post_timestamps_equal": True,
            "q1_checker_archive_access": (
                "opened_preflighted_and_extracted_before_failure"
            ),
            "qualification_credit": "none",
        },
        "Q1 archive observation",
    )

    expected_stderr = (
        "Lean toolchain custody check failed: nested Lean kernel direct lean "
        "pre-execution evidence disagrees with the outer live executable snapshot\n"
    )
    checker.validate_exact_typed_object(
        root["execution"],
        {
            "argv": [
                "/opt/homebrew/bin/python3",
                "-I",
                "-S",
                "-B",
                "scripts/check-lean-toolchain-custody.py",
                "--platform",
                "darwin-aarch64",
                "--archive",
                (
                    "/private/tmp/pid-rs-lean4322-darwin.orHE2a/"
                    "lean-4.32.2-darwin_aarch64.tar.zst"
                ),
                "--zstd",
                "/opt/homebrew/bin/zstd",
            ],
            "cwd": "/private/tmp/pid-rs-lean4322-q.Wwpn0p/worktree",
            "cwd_nonportable": True,
            "external_timeout_seconds": None,
            "observation_only": False,
            "python_flags": ["-I", "-S", "-B"],
            "return_utc_observed_approximate_untrusted": "2026-08-08T02:51:48Z",
            "started_utc_observed_untrusted": "2026-08-08T02:48:05Z",
            "tee_used": False,
            "time_authentication": "none",
            "umask": "0077",
        },
        "Q1 execution route",
    )

    stdout_leaf = {
        "bytes": 0,
        "git_blob_sha1": "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        "path": (
            "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-"
            "q1-2026-08-08.stdout"
        ),
        "retained_repository_mode": "0644",
        "sha256": EXPECTED_Q1_STDOUT_SHA256,
        "single_hard_link": True,
        "source_capture_mode": "0600",
        "source_mtime_local_untrusted": "2026-08-08T04:48:05+02:00",
        "symbolic_link": False,
    }
    stderr_leaf = {
        "bytes": 141,
        "git_blob_sha1": "531cffe1c92a77eb1170614a7e8e742b66013e8e",
        "path": (
            "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-"
            "q1-2026-08-08.stderr"
        ),
        "retained_repository_mode": "0644",
        "sha256": EXPECTED_Q1_STDERR_SHA256,
        "single_hard_link": True,
        "source_capture_mode": "0600",
        "source_mtime_local_untrusted": "2026-08-08T04:51:48+02:00",
        "symbolic_link": False,
    }
    checker.validate_exact_typed_object(
        root["capture_boundary"],
        {
            "authentication": ("none_owner_mutable_ephemeral_capture_copied_exactly"),
            "copied_to_repository_exact_bytes": True,
            "source_capture_directory": (
                "/private/tmp/pid-rs-lean4322-q.Wwpn0p/capture"
            ),
            "source_capture_directory_nonportable": True,
            "source_capture_owner_mutable": True,
            "stderr": stderr_leaf,
            "stdout": stdout_leaf,
            "time_authentication": "none",
        },
        "Q1 capture boundary",
    )
    require(
        stdout_source == b""
        and stderr_source == expected_stderr.encode("ascii")
        and hashlib.sha256(stdout_source).hexdigest() == stdout_leaf["sha256"]
        and hashlib.sha256(stderr_source).hexdigest() == stderr_leaf["sha256"],
        "Q1 raw stdout/stderr bytes drifted",
    )
    for leaf, source, role in (
        (stdout_leaf, stdout_source, "Q1 stdout"),
        (stderr_leaf, stderr_source, "Q1 stderr"),
    ):
        git_header = f"blob {len(source)}\0".encode("ascii")
        require(
            hashlib.sha1(git_header + source).hexdigest() == leaf["git_blob_sha1"],
            f"{role} Git blob identity drifted",
        )

    checker.validate_exact_typed_object(
        root["credit_boundary"],
        {
            "active_scientific_lean_project": "none",
            "archive_custody": "none",
            "kernel_soundness": "none",
            "nested_regression_qualification": "none",
            "publication_qualification": "none",
            "release_authorization": "none",
            "theorem_truth": "none",
        },
        "Q1 credit boundary",
    )
    checker.validate_exact_typed_object(
        root["failure"],
        {
            "actual_mismatch_field_paths_known": False,
            "canonical_result_emitted": False,
            "exclusive_actual_mismatch_claimed": False,
            "first_rejected_evidence_role": "lean_pre_execution",
            "inference_basis": (
                "exact_P_source_control_flow_plus_exact_production_stderr_not_a_"
                "retained_nested_result"
            ),
            "mismatch_inference": (
                "source_level_reproduction_explains_the_failure_without_proving_"
                "exclusive_actual_fields"
            ),
            "nested_result_retained": False,
            "observed_process_return_code": 1,
            "production_diagnostic_disclosed_field_paths": [],
            "separate_exit_status_artifact_retained": False,
            "source_counterexample_exclusive_mismatch": True,
            "source_reproduced_counterexample_field_paths": ["/launch_path"],
            "stages": {
                "archive_direct_file_precheck": "reached_passed",
                "archive_extraction": "reached_passed",
                "archive_zstd_preflight": "reached_passed",
                "canonical_outer_result_emission": "not_reached",
                "nested_checker_execution_and_canonical_result_parse": (
                    "reached_passed_inferred_from_exact_source_control_flow"
                ),
                "outer_live_tool_probes": "reached_passed",
                "outer_validate_nested_lake_evidence": "not_reached",
                "outer_validate_nested_lean_post_execution_evidence": "not_reached",
                "outer_validate_nested_lean_pre_execution_evidence": "reached_failed",
                "outer_validate_nested_leanchecker_evidence": "not_reached",
                "post_probe_extracted_tree_scan": "not_reached",
                "pre_probe_extracted_tree_scan": "reached_passed",
                "release_archive_postcheck": "not_reached",
                "repository_source_postchecks": "not_reached",
            },
            "stderr_line": expected_stderr,
            "stdout_empty": True,
        },
        "Q1 failure semantics",
    )
    checker.validate_exact_typed_object(
        root["nonclaims"],
        {
            "active_scientific_project_toolchain_migration": False,
            "actual_mismatch_field_identity": False,
            "archive_authenticity": False,
            "archive_custody": False,
            "external_checker_independence": False,
            "kernel_soundness": False,
            "pdf_or_document_claim_transfer": False,
            "pid_or_population_claim_transfer": False,
            "provider_authentication": False,
            "release_authorization": False,
            "reproducible_build": False,
            "rust_or_binary64_claim_transfer": False,
            "same_run_qualification": False,
            "source_to_binary_provenance": False,
            "theorem_truth": False,
        },
        "Q1 nonclaims",
    )
    checker.validate_exact_typed_object(
        root["p_binding"],
        {
            "commit": "0e13bb77a63f013cf8ec60824ed2613c669bb0b5",
            "metadata": {
                "bytes": 17_195,
                "path": "audit/formal/lean/toolchain-release-v4.32.2.json",
                "policy_projection_sha256": (
                    "5f72b60bd7bda8172ef2b2be0f4807eb082fcc88c9690b9c26c98ae83216b292"
                ),
                "sha256": (
                    "c2bfb532a809402dc280f5c54d9db0b89e8fe94ec4db97ab123f613a841de481"
                ),
            },
            "nested_checker": {
                "bytes": 118_682,
                "path": "scripts/check-lean-kernel-14576.py",
                "sha256": (
                    "9e6881e90c42475607aef3ceb42161ad6a32b971471029d063703043c7e337b4"
                ),
            },
            "outer_checker": {
                "bytes": 168_523,
                "path": "scripts/check-lean-toolchain-custody.py",
                "sha256": (
                    "6dbbc63eb4116063015eabdc448057738e02bf985a7fef8222cd1be14e5adb84"
                ),
            },
            "parent": "711d2dbd81b7135147cfe41d4ed9678abfc9c244",
            "promotion_receipt": {
                "bytes": 30_071,
                "path": (
                    "audit/evidence/lean-4.32.2-darwin-aarch64-reviewed-pins-"
                    "promotion-2026-08-07.receipt.json"
                ),
                "sha256": (
                    "bfa40273b4f857ebc0a09a2cd87b0f37b5b4a3260e5d518e1c922cfc5196b821"
                ),
            },
            "tree": "774aad8233149703e9060dd66a230f4dde189701",
        },
        "Q1 exact P binding",
    )
    checker.validate_exact_typed_object(
        root["worktree_custody"],
        {
            "detached_head": True,
            "head_after": "0e13bb77a63f013cf8ec60824ed2613c669bb0b5",
            "head_before": "0e13bb77a63f013cf8ec60824ed2613c669bb0b5",
            "linked_index": {
                "bytes": 74_212,
                "sha256": (
                    "e01220bcf952e4c1c3272a642e58946fdfada581c544781eab2182ad5df8f6fe"
                ),
            },
            "primary_dirty_worktree_touched": False,
            "status_after_bytes": 0,
            "status_before_bytes": 0,
            "status_clean_after": True,
            "status_clean_before": True,
            "tree_after": "774aad8233149703e9060dd66a230f4dde189701",
            "tree_before": "774aad8233149703e9060dd66a230f4dde189701",
        },
        "Q1 worktree custody",
    )


def q1_failure_evidence_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    failure_source = exact_source(
        Q1_FAILURE_PATH, EXPECTED_Q1_FAILURE_SHA256, "Q1 failure evidence"
    )
    stderr_source = exact_source(
        Q1_STDERR_PATH, EXPECTED_Q1_STDERR_SHA256, "Q1 raw stderr"
    )
    stdout_source = exact_source(
        Q1_STDOUT_PATH, EXPECTED_Q1_STDOUT_SHA256, "Q1 raw stdout"
    )
    payload = checker.parse_json_object(failure_source, "Q1 failure evidence")
    require(
        failure_source == checker.canonical_json_bytes(payload) + b"\n",
        "Q1 failure evidence is not canonical one-line JSON",
    )
    validate_q1_failure_evidence(payload, stdout_source, stderr_source)

    def mutated(*path: object, value: object) -> dict[str, object]:
        candidate = copy.deepcopy(payload)
        cursor: object = candidate
        for component in path[:-1]:
            require(isinstance(cursor, dict), "Q1 mutation path is not an object")
            cursor = cursor[component]
        require(isinstance(cursor, dict), "Q1 mutation leaf is not an object")
        cursor[path[-1]] = value
        return candidate

    cases = (
        ("q1_schema", mutated("schema", value="wrong"), "schema"),
        ("q1_status", mutated("status", value="passed"), "status"),
        (
            "q1_extra_root_key",
            mutated("unexpected", value=True),
            "keys drifted",
        ),
        (
            "q1_stderr_digest",
            mutated("capture_boundary", "stderr", "sha256", value="0" * 64),
            "capture boundary",
        ),
        (
            "q1_capture_authentication_overclaim",
            mutated("capture_boundary", "authentication", value="authenticated"),
            "capture boundary",
        ),
        (
            "q1_stream_time_authentication_overclaim",
            mutated("capture_boundary", "time_authentication", value="trusted"),
            "capture boundary",
        ),
        (
            "q1_runner_isolation_flag_removed",
            mutated("execution", "python_flags", value=["-I", "-S"]),
            "execution route",
        ),
        (
            "q1_runner_argv_substitution",
            mutated("execution", "argv", value=[]),
            "execution route",
        ),
        (
            "q1_runner_observation_only_invented",
            mutated("execution", "observation_only", value=True),
            "execution route",
        ),
        (
            "q1_runner_tee_invented",
            mutated("execution", "tee_used", value=True),
            "execution route",
        ),
        (
            "q1_runner_external_timeout_invented",
            mutated("execution", "external_timeout_seconds", value=4_000),
            "execution route",
        ),
        (
            "q1_runner_umask_substitution",
            mutated("execution", "umask", value="0022"),
            "execution route",
        ),
        (
            "q1_known_mismatch_path",
            mutated(
                "failure",
                "source_reproduced_counterexample_field_paths",
                value=["/identity/modified_ns"],
            ),
            "failure semantics",
        ),
        (
            "q1_actual_mismatch_fields_falsely_known",
            mutated("failure", "actual_mismatch_field_paths_known", value=True),
            "failure semantics",
        ),
        (
            "q1_production_diagnostic_field_disclosure_invented",
            mutated(
                "failure",
                "production_diagnostic_disclosed_field_paths",
                value=["/launch_path"],
            ),
            "failure semantics",
        ),
        (
            "q1_exclusive_mismatch_overclaim",
            mutated("failure", "exclusive_actual_mismatch_claimed", value=True),
            "failure semantics",
        ),
        (
            "q1_source_counterexample_exclusivity_removed",
            mutated("failure", "source_counterexample_exclusive_mismatch", value=False),
            "failure semantics",
        ),
        (
            "q1_archive_access_erased",
            mutated("archive_observation", "q1_checker_archive_access", value="none"),
            "archive observation",
        ),
        (
            "q1_archive_hash_substitution",
            mutated(
                "archive_observation",
                "external_precheck",
                "sha256",
                value="0" * 64,
            ),
            "archive observation",
        ),
        (
            "q1_archive_mtime_scalar_invented",
            mutated("archive_observation", "exact_mtime_scalar_retained", value=True),
            "archive observation",
        ),
        (
            "q1_archive_credit_overclaim",
            mutated("credit_boundary", "archive_custody", value="qualified"),
            "credit boundary",
        ),
        (
            "q1_postcheck_overclaim",
            mutated(
                "failure",
                "stages",
                "release_archive_postcheck",
                value="reached_passed",
            ),
            "failure semantics",
        ),
        (
            "q1_result_emission_overclaim",
            mutated("failure", "canonical_result_emitted", value=True),
            "failure semantics",
        ),
        (
            "q1_exit_status_boolean_substitution",
            mutated("failure", "observed_process_return_code", value=True),
            "failure semantics",
        ),
        (
            "q1_separate_exit_artifact_invented",
            mutated("failure", "separate_exit_status_artifact_retained", value=True),
            "failure semantics",
        ),
        (
            "q1_p_checker_binding_substitution",
            mutated("p_binding", "outer_checker", "sha256", value="0" * 64),
            "exact P binding",
        ),
        (
            "q1_policy_projection_substitution",
            mutated(
                "p_binding", "metadata", "policy_projection_sha256", value="0" * 64
            ),
            "exact P binding",
        ),
        (
            "q1_nonclaim_overclaim",
            mutated("nonclaims", "kernel_soundness", value=True),
            "nonclaims",
        ),
        (
            "q1_worktree_dirty_substitution",
            mutated("worktree_custody", "status_after_bytes", value=1),
            "worktree custody",
        ),
        (
            "q1_linked_index_substitution",
            mutated("worktree_custody", "linked_index", "sha256", value="0" * 64),
            "worktree custody",
        ),
    )
    controls = [
        expect_failure(
            name,
            lambda candidate=candidate: validate_q1_failure_evidence(
                candidate, stdout_source, stderr_source
            ),
            reason,
        )
        for name, candidate, reason in cases
    ]
    coordinated_stdout = b"invented stdout\n"
    coordinated_payload = copy.deepcopy(payload)
    coordinated_stdout_leaf = coordinated_payload["capture_boundary"]["stdout"]
    coordinated_stdout_leaf["bytes"] = len(coordinated_stdout)
    coordinated_stdout_leaf["sha256"] = hashlib.sha256(coordinated_stdout).hexdigest()
    coordinated_stdout_leaf["git_blob_sha1"] = hashlib.sha1(
        f"blob {len(coordinated_stdout)}\0".encode("ascii") + coordinated_stdout
    ).hexdigest()
    controls.append(
        expect_failure(
            "q1_coordinated_stdout_raw_and_binding_reseal",
            lambda: validate_q1_failure_evidence(
                coordinated_payload,
                coordinated_stdout,
                stderr_source,
            ),
            "capture boundary",
        )
    )
    require(
        exact_source(
            Q1_FAILURE_PATH,
            EXPECTED_Q1_FAILURE_SHA256,
            "post-control Q1 failure evidence",
        )
        == failure_source
        and exact_source(
            Q1_STDERR_PATH, EXPECTED_Q1_STDERR_SHA256, "post-control Q1 raw stderr"
        )
        == stderr_source
        and exact_source(
            Q1_STDOUT_PATH, EXPECTED_Q1_STDOUT_SHA256, "post-control Q1 raw stdout"
        )
        == stdout_source,
        "Q1 retained evidence changed across controls",
    )
    positives = [
        {
            "name": "q1_failure_raw_and_typed_evidence_bound_zero_credit",
            "accepted": True,
            "archive_access_by_self_test": "none",
            "qualification_credit": "none",
        }
    ]
    return controls, positives


def host_and_state_controls() -> list[dict[str, object]]:
    controls = [
        expect_failure(
            "linux_pending_strict_rejected",
            lambda: checker.qualify(
                ASSETS["linux-x86_64"],
                Path("/absent"),
                None,
                False,
                None,
                None,
                None,
                None,
                None,
                None,
                METADATA,
            ),
            "hosted_pending",
        ),
        expect_failure(
            "darwin_reviewed_pins_observation_only_rejected",
            lambda: checker.qualify(
                ASSETS["darwin-aarch64"],
                Path("/absent"),
                None,
                True,
                None,
                None,
                None,
                None,
                None,
                None,
                METADATA,
            ),
            "reviewed pins permit strict replay only",
        ),
    ]
    original_system = checker.platform.system
    original_machine = checker.platform.machine
    try:
        checker.platform.system = lambda: "Darwin"
        checker.platform.machine = lambda: "arm64"
        controls.append(
            expect_failure(
                "darwin_strict_replay_reaches_archive_preflight",
                lambda: checker.qualify(
                    ASSETS["darwin-aarch64"],
                    Path("/absent"),
                    None,
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    METADATA,
                ),
                "cannot lstat Lean release archive",
            )
        )
        checker.platform.system = lambda: "Plan9"
        checker.platform.machine = lambda: "arm64"
        controls.append(
            expect_failure(
                "host_wrong_system",
                lambda: checker.validate_host(ASSETS["darwin-aarch64"]),
                "requires host system",
            )
        )
        checker.platform.system = lambda: "Darwin"
        checker.platform.machine = lambda: "x86_64"
        controls.append(
            expect_failure(
                "host_wrong_machine",
                lambda: checker.validate_host(ASSETS["darwin-aarch64"]),
                "requires host machine",
            )
        )
    finally:
        checker.platform.system = original_system
        checker.platform.machine = original_machine
    return controls


def invocation_controls() -> list[dict[str, object]]:
    cases = (
        (
            "invocation_no_isolation",
            [sys.executable, os.fspath(CHECKER_PATH), "--help"],
        ),
        (
            "invocation_missing_S",
            [sys.executable, "-I", "-B", os.fspath(CHECKER_PATH), "--help"],
        ),
        (
            "invocation_missing_I",
            [sys.executable, "-S", "-B", os.fspath(CHECKER_PATH), "--help"],
        ),
        (
            "invocation_missing_B",
            [sys.executable, "-I", "-S", os.fspath(CHECKER_PATH), "--help"],
        ),
    )
    controls: list[dict[str, object]] = []
    for name, command in cases:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        expected = b"ERROR: check-lean-toolchain-custody.py requires Python -I -S -B\n"
        require(
            result.returncode == 2
            and result.stdout == b""
            and result.stderr == expected,
            f"{name} did not fail at the exact bootstrap guard",
        )
        controls.append(
            {
                "name": name,
                "rejected": True,
                "reason_contains": "requires Python -I -S -B",
            }
        )
    positive = subprocess.run(
        [sys.executable, "-I", "-S", "-B", os.fspath(CHECKER_PATH), "--help"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    require(
        positive.returncode == 0
        and b"--observation-only" in positive.stdout
        and positive.stderr == b"",
        "fully isolated help baseline drifted",
    )
    pending = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            os.fspath(CHECKER_PATH),
            "--platform",
            "linux-x86_64",
            "--archive",
            "/private/tmp/absent.tar.zst",
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    require(
        pending.returncode == 1
        and pending.stdout == b""
        and b"hosted_pending" in pending.stderr,
        "strict hosted-pending CLI route did not fail closed",
    )
    controls.append(
        {
            "name": "invocation_strict_hosted_pending",
            "rejected": True,
            "reason_contains": "hosted_pending",
        }
    )
    darwin_observation_only = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            os.fspath(CHECKER_PATH),
            "--platform",
            "darwin-aarch64",
            "--archive",
            "/private/tmp/absent.tar.zst",
            "--observation-only",
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    require(
        darwin_observation_only.returncode == 1
        and darwin_observation_only.stdout == b""
        and b"reviewed pins permit strict replay only"
        in darwin_observation_only.stderr,
        "Darwin observation-only route did not fail closed",
    )
    controls.append(
        {
            "name": "invocation_darwin_observation_only_rejected",
            "rejected": True,
            "reason_contains": "reviewed pins permit strict replay only",
        }
    )
    return controls


def bootstrap_runtime_contract_controls() -> list[dict[str, object]]:
    valid_flags = types.SimpleNamespace(
        isolated=1,
        safe_path=True,
        no_site=1,
        ignore_environment=1,
        dont_write_bytecode=1,
    )
    require(
        checker._bootstrap_runtime_supported((3, 11), valid_flags),
        "valid Python bootstrap runtime was rejected",
    )
    cases = (
        ("bootstrap_python_minimum", (3, 10), valid_flags),
        (
            "bootstrap_missing_safe_path_attribute",
            (3, 11),
            types.SimpleNamespace(
                isolated=1,
                no_site=1,
                ignore_environment=1,
                dont_write_bytecode=1,
            ),
        ),
        (
            "bootstrap_no_bytecode_state_false",
            (3, 11),
            types.SimpleNamespace(
                isolated=1,
                safe_path=True,
                no_site=1,
                ignore_environment=1,
                dont_write_bytecode=0,
            ),
        ),
    )
    return [
        expect_failure(
            name,
            lambda version=version, flags=flags: checker.require(
                checker._bootstrap_runtime_supported(version, flags),
                "unsupported Python bootstrap runtime",
            ),
            "unsupported Python bootstrap runtime",
        )
        for name, version, flags in cases
    ]


def main() -> int:
    try:
        initial_self_source = SELF_PATH.read_bytes()
        self_test_source_sha256 = hashlib.sha256(initial_self_source).hexdigest()
        require(
            exact_source(SELF_PATH, self_test_source_sha256, "custody self-test")
            == initial_self_source,
            "custody self-test exact-source baseline drifted",
        )
        require(
            SYNTHETIC_MANIFEST == SYNTHETIC_MANIFEST_SHA256,
            f"synthetic manifest pin drifted: {SYNTHETIC_MANIFEST}",
        )
        nested_negatives, nested_positives = nested_kernel_regression_controls()
        wiring_negatives, wiring_positive = production_qualify_wiring_controls()
        observation_negatives, observation_positives = observation_custody_controls()
        legacy_negatives, legacy_positives = legacy_v4_independence_controls()
        closed_contradictions = closed_promotion_contradiction_controls()
        promoted_single_fields = promoted_single_field_controls()
        promoted_matched_wrong = promoted_matched_wrong_controls()
        process_negatives, process_positives = process_controls()
        zstd_negatives, zstd_positives = zstd_process_group_controls()
        private_umask_positives = private_directory_umask_controls()
        q1_negatives, q1_positives = q1_failure_evidence_controls()
        categories = {
            "metadata_and_source": [
                *metadata_controls(),
                *literal_dict_key_controls(),
            ],
            "tar_members": member_controls(),
            "tar_inventory": inventory_controls(),
            "extraction_and_manifest": extraction_controls(),
            "versions_and_diagnostics": version_controls(),
            "nested_kernel_regression": nested_negatives,
            "production_qualify_wiring": wiring_negatives,
            "environment_substitution": environment_controls(),
            "process_bounds": process_negatives,
            "zstd_process_groups": zstd_negatives,
            "file_custody": file_custody_controls(),
            "nested_checker_source_binding": nested_checker_source_binding_controls(),
            "historical_receipt_semantics": historical_receipt_semantic_controls(),
            "q1_retained_failure_evidence": q1_negatives,
            "darwin_observation_custody": observation_negatives,
            "frozen_legacy_v4_authority": legacy_negatives,
            "closed_promotion_contradictions": closed_contradictions,
            "promoted_single_field_semantics": promoted_single_fields,
            "promoted_matched_wrong_semantics": promoted_matched_wrong,
            "host_and_lifecycle_state": host_and_state_controls(),
            "isolated_invocation": [
                *invocation_controls(),
                *bootstrap_runtime_contract_controls(),
            ],
        }
        positive_controls = [
            *nested_positives,
            wiring_positive,
            *observation_positives,
            *legacy_positives,
            *process_positives,
            *zstd_positives,
            *private_umask_positives,
            *q1_positives,
        ]
        counts = {name: len(items) for name, items in categories.items()}
        expected_counts = {
            "metadata_and_source": 89,
            "tar_members": 24,
            "tar_inventory": 11,
            "extraction_and_manifest": 9,
            "versions_and_diagnostics": 21,
            "nested_kernel_regression": 232,
            "production_qualify_wiring": 76,
            "environment_substitution": 7,
            "process_bounds": 6,
            "zstd_process_groups": 3,
            "file_custody": 8,
            "nested_checker_source_binding": 6,
            "historical_receipt_semantics": 3,
            "q1_retained_failure_evidence": 31,
            "darwin_observation_custody": 59,
            "frozen_legacy_v4_authority": 2,
            "closed_promotion_contradictions": 18,
            "promoted_single_field_semantics": 112,
            "promoted_matched_wrong_semantics": 9,
            "host_and_lifecycle_state": 5,
            "isolated_invocation": 9,
        }
        require(
            counts == expected_counts,
            f"negative-control category counts drifted: {counts}",
        )
        flat = [control for items in categories.values() for control in items]
        names = [str(control["name"]) for control in flat]
        require(len(names) == 740, f"negative-control total drifted: {len(names)}")
        require(len(set(names)) == len(names), "negative-control names are not unique")
        positive_names = [str(control["name"]) for control in positive_controls]
        require(
            len(set(positive_names)) == len(positive_names),
            "positive-control names are not unique",
        )
        require(
            len(positive_names) == 21,
            f"positive-control total drifted: {len(positive_names)}",
        )
        require(
            set(names).isdisjoint(positive_names),
            "positive- and negative-control names are not disjoint",
        )
        require(
            exact_source(
                CHECKER_PATH, EXPECTED_CHECKER_SHA256, "post-control custody checker"
            )
            == CHECKER_SOURCE,
            "custody checker exact source changed across self-test",
        )
        require(
            exact_source(
                METADATA_PATH, EXPECTED_METADATA_SHA256, "post-control custody metadata"
            )
            == METADATA_SOURCE,
            "custody metadata exact source changed across self-test",
        )
        require(
            exact_source(
                OBSERVATION_RAW_PATH,
                EXPECTED_OBSERVATION_RAW_SHA256,
                "post-control Darwin observation raw result",
            )
            == OBSERVATION_RAW_SOURCE,
            "Darwin observation raw result changed across self-test",
        )
        require(
            exact_source(
                OBSERVATION_RECEIPT_PATH,
                EXPECTED_OBSERVATION_RECEIPT_SHA256,
                "post-control Darwin observation receipt",
            )
            == OBSERVATION_RECEIPT_SOURCE,
            "Darwin observation receipt changed across self-test",
        )
        nested_checker_path = (
            ROOT / METADATA["checker_binding"]["nested_checker_binding"]["path"]
        )
        exact_source(
            nested_checker_path,
            METADATA["checker_binding"]["nested_checker_binding"]["sha256"],
            "post-control nested kernel checker",
        )
        require(
            exact_source(
                SELF_PATH, self_test_source_sha256, "post-control custody self-test"
            )
            == initial_self_source,
            "custody self-test exact source changed across execution",
        )
        evidence = {
            "schema": "pid-rs/lean-toolchain-release-custody-self-test/v5",
            "status": "passed",
            "checker_source_sha256": EXPECTED_CHECKER_SHA256,
            "metadata_sha256": EXPECTED_METADATA_SHA256,
            "self_test_source_sha256": self_test_source_sha256,
            "metadata_policy_projection_sha256": checker.EXPECTED_METADATA_POLICY_SHA256,
            "synthetic_tree_manifest_sha256": SYNTHETIC_MANIFEST_SHA256,
            "negative_controls_rejected": len(flat),
            "category_counts": counts,
            "negative_controls": categories,
            "positive_controls_accepted": len(positive_controls),
            "positive_controls": positive_controls,
            "accepted_contradictions_now_rejected": 17,
            "accepted_contradiction_ids": sorted(
                str(item["name"])
                for item in closed_contradictions
                if str(item["name"]) != "pending_reason_type_and_content_weak_empty"
            ),
            "boundary": (
                "These bounded controls exercise duplicate-free canonical JSON, exact release "
                "and asset metadata, and the acyclic two-checker seal. Synthetic tar fixtures "
                "exercise parser, archive-topology, resource-preflight, extraction, tree-mutation, "
                "and file-custody paths; the suite also exercises three exact executable-leaf "
                "shapes, typed Darwin/Linux probe grammars, and the total nested v6 "
                "same-transaction result. No control opens or extracts an actual Lean 4.32.2 "
                "release archive, and no synthetic fixture earns release-archive custody or real "
                "nested-regression credit. The frozen legacy-v4 authority is proven by AST and "
                "bytecode-name inspection to avoid METADATA, ASSETS, and LIMITS, then revalidated "
                "while those globals are poisoned; coordinated raw/receipt and reviewed-pin "
                "mutations cannot hide intrinsic contradictions behind equality or digest checks. "
                "Every one of the 17 receipt-listed accepted contradictions now rejects, as do the "
                "additional empty pending-reason case, all registered scalar fields, matched-wrong "
                "copies, and any attempt to transfer the historical tree pre/post execution "
                "observation into static v3 metadata. Static v3 credit remains internal consistency "
                "only. Q1 did open, preflight, and extract the actual Darwin archive and reached "
                "outer validation of nested Lean pre-execution evidence, then failed closed with "
                "zero qualification credit. Its production diagnostic disclosed no mismatching "
                "field. Exact-P source reproduction isolates a lexical-versus-canonical temporary-"
                "parent launch path as a sufficient exclusive one-field counterexample, not as "
                "proof of Q1's exclusive actual mismatch. This P2 suite exercises canonical-root "
                "repair, fresh pre/post outer snapshots, reviewed-tree leaf prebinding, and the "
                "outer strict-replay process-output boundary. At that boundary, nonzero nested "
                "outcomes and zero-exit malformed, noncanonical, or structural/semantic results "
                "collapse to fixed diagnostics with independent stdout/stderr byte counts and "
                "SHA-256 digests; the complete emitted CLI stderr, including prefix and LF, is "
                "one-line ASCII no larger than 1,024 bytes. Direct-executable evidence must first "
                "match the exact recursive expected key/type/container shape. Only a mismatch at "
                "one or more of the exact 12 known value leaves may retain a canonical ASCII JSON-"
                "pointer array plus canonical observed/expected evidence SHA-256 digests; unknown, "
                "missing, wrong-type, malformed, container, overflow-marker, and mixed forged "
                "inventories take the generic route. Direct outer "
                "zstd, Lean-version, Lake-version, and LeanChecker probe rejections likewise retain "
                "only a fixed stage and stream counts/digests. Production-direction hostile names, "
                "tokens, values, controls, and unexpected exceptions, table-driven full device/"
                "inode/time/content-plus-digest drift, and an independently measuring child exercise "
                "that scope. A semantic production-route validator rejects 74 registered deletion, "
                "reorder, dead-branch, producer, rebind, in-place mutation, local/main/module shadow, "
                "and disposition mutants without checker hash/import rejection. Two additional "
                "controls separately exercise version-neutral normalized-AST projections of the "
                "qualify/main route and complete checker module as defense in depth against "
                "unrecognized same-module drift. This bounded mutation evidence and source closure "
                "is not mutation completeness, a formal implementation proof, or authentication; "
                "coordinated checker/self-test resealing requires exact-source external review. "
                "This is not "
                "a global diagnostic guarantee: standalone nested-checker "
                "diagnostics and tar-parser/member diagnostics are excluded. The production tar "
                "route is reached only after the archive size and SHA-256 equal the reviewed exact "
                "pin. This P2 suite does not rerun the release archive. Linux remains observation-only "
                "hosted_pending. P2 must first be published and close its hosted gates; a new clean "
                "Q2 strict replay from exact published P2 must then freshly establish archive "
                "custody, tree pre/post equality, and real nested v6 execution in one extraction "
                "transaction and be published immutably before scoped result credit exists. The "
                "checks do not authenticate GitHub, Lean, Python, zstd, the OS, loader, "
                "hardware, source-to-binary provenance, provide an independent kernel or nanoda "
                "result, migrate the active Lean project, prove kernel soundness or theorem truth, "
                "authorize a release, validate a PDF, or transfer anything to Rust, binary64, PID "
                "estimators, data, or population claims."
            ),
        }
        print(
            json.dumps(
                evidence,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
        return 0
    except (
        SelfTestError,
        checker.CustodyError,
        IndexError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Lean toolchain custody self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
