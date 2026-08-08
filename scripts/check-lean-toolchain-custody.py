#!/usr/bin/env python3
"""Qualify exact Lean 4.32.2 release archives under a fail-closed custody policy.

This checker never downloads an asset.  It consumes one caller-supplied archive,
matches it to exact reviewed repository metadata, preflights the complete tar
topology before writing, extracts regular files without following links, hashes a
canonical tree twice, and launches only the three exact extracted executable
leaves under a minimal environment.

The checker/metadata seal is deliberately acyclic.  The checker embeds a digest
of canonical metadata with the four finalized checker size/digest fields
omitted; after both checkers are finalized, their byte lengths and SHA-256
digests are written into those omitted fields.  Runtime verifies both.  A
coordinated source+metadata reseal is still possible and needs Git review or an
external receipt; mutable repository bytes cannot authenticate themselves.
"""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys


def _bootstrap_runtime_supported(version_info: object, flags: object) -> bool:
    version = tuple(version_info)[:2]
    return version >= (3, 11) and (
        getattr(flags, "isolated", 0) == 1
        and getattr(flags, "safe_path", False) is True
        and getattr(flags, "no_site", 0) == 1
        and getattr(flags, "ignore_environment", 0) == 1
        and getattr(flags, "dont_write_bytecode", 0) == 1
    )


if _bootstrap_sys.version_info < (3, 11):
    print(
        "ERROR: check-lean-toolchain-custody.py requires Python >= 3.11",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
if not _bootstrap_runtime_supported(_bootstrap_sys.version_info, _bootstrap_sys.flags):
    print(
        "ERROR: check-lean-toolchain-custody.py requires Python -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import unicodedata
from typing import BinaryIO, Callable, Final, Iterator, TypeVar


SCRIPT_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT_PATH.parent.parent
METADATA_PATH = ROOT / "audit/formal/lean/toolchain-release-v4.32.2.json"
KERNEL_REGRESSION_CHECKER_PATH = ROOT / "scripts/check-lean-kernel-14576.py"
LEGACY_OBSERVATION_RAW_PATH = (
    ROOT / "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.raw.json"
)
LEGACY_OBSERVATION_RECEIPT_PATH = (
    ROOT
    / "audit/evidence/lean-4.32.2-darwin-aarch64-observation-2026-08-07.receipt.json"
)

METADATA_SCHEMA: Final = "pid-rs/lean-toolchain-release-custody-metadata/v3"
RESULT_SCHEMA: Final = "pid-rs/lean-toolchain-release-custody-check/v5"
KERNEL_REGRESSION_RESULT_SCHEMA: Final = "pid-rs/lean-kernel-14576-check/v6"
LEGACY_RESULT_SCHEMA: Final = "pid-rs/lean-toolchain-release-custody-check/v4"
LEGACY_RECEIPT_SCHEMA: Final = "pid-rs/lean-toolchain-darwin-observation-custody/v1"
MANIFEST_FORMAT: Final = "pid-rs/lean-toolchain-extracted-tree-manifest/v1"
MANIFEST_HEADER: Final = (MANIFEST_FORMAT + "\n").encode("ascii")
EXPECTED_METADATA_POLICY_SHA256: Final = (
    "5f72b60bd7bda8172ef2b2be0f4807eb082fcc88c9690b9c26c98ae83216b292"
)
EXPECTED_VERSION: Final = "4.32.2"
EXPECTED_LAKE_VERSION: Final = "5.0.0-src+f3b06c7"
EXPECTED_DARWIN_PLATFORM: Final = "arm64-apple-darwin24.6.0"
EXPECTED_COMMIT: Final = "f3b06c705e6c85f5314019d5d3baab0fec5b580c"
EXPECTED_FIX_COMMIT: Final = "8be817b3f6310f62f220861b0c92dbabb951115d"
EXPECTED_FIX_PARENT: Final = "f054605aea4b840552cca2e725580bffd1e1b704"
EXPECTED_PULL_REQUEST_RESULT_COMMIT: Final = "a39eab69e1eee9ad38f4efe507907b1026a77808"
EXPECTED_PULL_REQUEST_RELEASE_MERGE_BASE: Final = (
    "4792cd22887c8b529a351f6563b693426ff2a8f8"
)
EXPECTED_NESTED_CHECKER_BYTES: Final = 118_682
EXPECTED_NESTED_CHECKER_SHA256: Final = (
    "9e6881e90c42475607aef3ceb42161ad6a32b971471029d063703043c7e337b4"
)
EXPECTED_LEGACY_OBSERVATION_RAW_BYTES: Final = 12_027
EXPECTED_LEGACY_OBSERVATION_RAW_SHA256: Final = (
    "374bc2eb53881cae4c7b989944dff3daff0fc02c2340ce39bd920a4ddb08723a"
)
EXPECTED_LEGACY_OBSERVATION_RECEIPT_BYTES: Final = 11_383
EXPECTED_LEGACY_OBSERVATION_RECEIPT_SHA256: Final = (
    "4720cb4b6d0be274d52f36e2a16d63dcf6542ed47520b9370b956cc1d7d2a903"
)
EXPECTED_AUTHENTICATION_BOUNDARY_SHA256: Final = (
    "08acdaeb348118d3d6a2b4a0384ce8a285ad3a8ea59aa88bca2cc0855a4104dd"
)
EXPECTED_CREDIT_BOUNDARY_SHA256: Final = (
    "67309b2b6e4685e157e5c4aa9f9cc833854bfa378e02becb74ee5a3992efd123"
)
EXPECTED_REVIEWED_PIN_SOURCE_SHA256: Final = (
    "5d5b1c744a8af8e141ca74ca18e1718ba1f868b129232c6551c4687cdc4d8bfd"
)
EXPECTED_CHECKER_POLICY: Final = (
    "Acyclic seal: canonical metadata v3 with exactly the outer and nested checker "
    "byte-length/SHA-256 fields omitted is hashed into both checker sources; the "
    "finalized checker sources are then hashed into those omitted metadata fields. "
    "Runtime verifies the exact outer and nested bindings separately. The static tree "
    "pin contains only its algorithm, format, and digest; historical "
    "pre/post execution equality is not transferred and must be freshly established "
    "by strict replay. Reviewed pins "
    "grant only internal static-schema credit and enable a later strict replay; they "
    "grant no archive custody or same-run qualification. Coordinated resealing remains "
    "possible and requires Git/review/external custody; no mutable repository can "
    "authenticate itself."
)
EXPECTED_HISTORICAL_NONTRANSFERABILITY_REASON: Final = (
    "The current custody checker, nested checker, and metadata are byte-distinct. "
    "Archive equality alone cannot transfer extraction, process, source-binding, or "
    "regression execution claims to changed verifier bytes."
)
EXPECTED_NESTED_SCOPE_BOUNDARY: Final = {
    "active_scientific_lean_project": "none",
    "archive_custody": "none_by_nested_checker",
    "downstream_authorization": "none",
    "kernel_soundness": "none",
    "nanoda_or_external_checker": "none",
    "pdf_transfer": "none",
    "pid_estimator_population_transfer": "none",
    "publisher_provider_authentication": "none",
    "real_nested_regression": "checks_passed_unpublished_nested_result",
    "release_authorization": "none",
    "reproducible_build": "none",
    "rust_binary64_transfer": "none",
    "same_run_qualification": "forbidden",
    "source_to_binary_provenance": "none",
    "static_schema_validation": "metadata_projection_and_self_binding_checked",
    "theorem_truth": "none",
}
EXPECTED_NESTED_BOUNDARY_SHA256: Final = (
    "9dd6c748aa455e862e72064c01d28ecd2e81af271be352904584fe00f17e76ce"
)
ABSENT_MODULE: Final = "pid_rs_toolchain_custody_absent_module.olean"
NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS: Final = 900
NESTED_KERNEL_REPLAY_COUNT: Final = 3
NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS: Final = 120
NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT: Final = 6
NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS: Final = 60
NESTED_KERNEL_IDENTITY_CHILD_COUNT: Final = 4
NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS: Final = 240
NESTED_KERNEL_NON_REPLAY_MARGIN_SECONDS: Final = (
    NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS
    * NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT
    + NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS * NESTED_KERNEL_IDENTITY_CHILD_COUNT
    + NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS
)
NESTED_KERNEL_REQUIRED_OUTER_TIMEOUT_SECONDS: Final = (
    NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS * NESTED_KERNEL_REPLAY_COUNT
    + NESTED_KERNEL_NON_REPLAY_MARGIN_SECONDS
)
NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS: Final = 4_200
MISMATCH_FIELD_PATHS_MAX: Final = 16
MISMATCH_FIELD_PATH_BYTES_MAX: Final = 128
CLI_FAILURE_PREFIX: Final = "Lean toolchain custody check failed: "
CLI_FAILURE_STDERR_BYTES_MAX: Final = 1_024
# The child-boundary payload budget reserves the exact production CLI prefix and LF.
# This makes the complete emitted stderr line, rather than only the inner message,
# the object bounded by CLI_FAILURE_STDERR_BYTES_MAX.
MISMATCH_DIAGNOSTIC_BYTES_MAX: Final = (
    CLI_FAILURE_STDERR_BYTES_MAX - len(CLI_FAILURE_PREFIX.encode("ascii")) - len(b"\n")
)
MISMATCH_OVERFLOW_MARKER: Final = "<mismatch-details-omitted-bounds-exceeded>"
NESTED_EXECUTABLE_EVIDENCE_VALUE_POINTERS: Final = frozenset(
    {
        "/bytes",
        "/canonical_path",
        "/identity/changed_ns",
        "/identity/device",
        "/identity/inode",
        "/identity/links",
        "/identity/mode",
        "/identity/modified_ns",
        "/identity/permissions",
        "/identity/size",
        "/launch_path",
        "/sha256",
    }
)
NESTED_EXECUTABLE_EVIDENCE_ROLES: Final = frozenset(
    f"nested Lean kernel direct {executable} {phase}-execution evidence"
    for executable in ("lean", "lake", "leanchecker")
    for phase in ("pre", "post")
)
PROCESS_GROUP_TERM_GRACE_MILLISECONDS: Final = 500
PROCESS_GROUP_KILL_GRACE_MILLISECONDS: Final = 2_000
PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS: Final = 10
DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS: Final = 2_000
PROCESS_GROUP_TERM_GRACE_SECONDS: Final = PROCESS_GROUP_TERM_GRACE_MILLISECONDS / 1_000
PROCESS_GROUP_KILL_GRACE_SECONDS: Final = PROCESS_GROUP_KILL_GRACE_MILLISECONDS / 1_000
PROCESS_GROUP_POLL_INTERVAL_SECONDS: Final = (
    PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS / 1_000
)
DIRECT_CHILD_REAP_TIMEOUT_SECONDS: Final = (
    DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS / 1_000
)
EXPECTED_TRUST_ZERO_SEMANTICS: Final = {
    "argument": "--trust=0",
    "help_meaning": "do_not_trust_any_macro_and_type_check_all_imported_modules",
    "no_macros_trusted": True,
    "all_imported_modules_typechecked": True,
    "selected_lean_implementation_and_runtime_remain_trusted": True,
    "zero_tcb": False,
}
EXPECTED_LEANCHECKER_FRESH_SEMANTICS: Final = {
    "argument": "--fresh",
    "complete_declaration_inventory_claimed": False,
    "external_verifier": False,
    "fresh_replay_rechecks_source_elaboration_or_guarded_commands": False,
    "full_fixture_bad_declaration_source_present": True,
    "full_fixture_bad_thmdecl_reached_or_attempted": False,
    "full_fixture_post_failure_unknown_bad_reference_guard": True,
    "guard_msgs_rerun": False,
    "initial_environment": "mkEmptyEnvironment",
    "independent_kernel_implementation": False,
    "minimum_fixture_bad_source_reference_probe_or_absence_claimed": False,
    "ordinary_olean_count": 3,
    "ordinary_olean_files_in_mode_0700_private_temporary_tree": True,
    "rejected_constructor_E_mk_absent_in_each_selected_target_olean": True,
    "unreached_bad_declaration_absent_in_full_selected_target_olean": True,
    "replayed_content": "imported_and_defined_constants",
    "same_executable_leaf_as_source_elaboration": False,
    "same_process_as_source_elaboration": False,
    "selected_emitted_olean_name_probe_only": True,
    "selected_release_implementation_and_runtime_remain_trusted": True,
    "source_reelaboration": False,
    "residual_axiom_shaped_E_present_in_each_selected_target_olean": True,
}
EXPECTED_KERNEL_REGRESSION_ORIGIN_SHA256: Final = (
    "fd725d7ba4b08071f40ac6acaca62ecad09aefa11aa3c78cb94d2873cc5ddde1"
)
EXPECTED_KERNEL_REGRESSION_FIXTURES: Final = (
    {
        "name": "issue_14576.lean",
        "sha256": "0aaec9548df29266061467e37026935391a05bf6142fd027915f40c687a889e2",
        "bytes": 2_460,
        "module": "Issue14576Full",
        "derived_query_bytes": 2_584,
        "derived_query_sha256": (
            "f9ecdb91eb99b11e358d2c3cff32059ca14f7fd65a0bfd9bc7f88abf1fdaf841"
        ),
        "inventory_probe_source_bytes": 621,
        "inventory_probe_source_sha256": (
            "9e62ee47c67457f21ad6cdab44c69fec42b0a7a7b9ad347416294b69edf4f033"
        ),
    },
    {
        "name": "issue_14576_min.lean",
        "sha256": "77769c1ce88649f56bf1fc8a0ae89fafdef25eae17b744fc7f28cb7b9519cbb5",
        "bytes": 804,
        "module": "Issue14576Min",
        "derived_query_bytes": 932,
        "derived_query_sha256": (
            "83abd16bdd236ae9f4fdcfa0d975ddcd0dc4f24681f5eba3f31ad6c95302a927"
        ),
        "inventory_probe_source_bytes": 560,
        "inventory_probe_source_sha256": (
            "7804185ed6b01627e02cfdd5b03ac36a19cd0d4f4411373dd64f97d972b8f47a"
        ),
    },
)
EXPECTED_BENIGN_TRANSFORMED_SOURCE_SHA256: Final = (
    "f8b55af8ef253edd4f37dab119104caad470a6a1c787759797cbf8b402f34782"
)
EXPECTED_BENIGN_QUERY_SHA256: Final = (
    "f9985480723b5c0f8e944490b524a5681d994916190dec1a02d7d190bc3ee0c0"
)
EXPECTED_UNGUARDED_TRANSFORMED_SOURCE_SHA256: Final = (
    "79c675b9023e315c30c52eccb5713aa326fa3d7b8dbd05ac32d107dd7410e90f"
)
EXPECTED_UNGUARDED_QUERY_SHA256: Final = (
    "569d521a544b86f0ae70c19aa59f9b71ee036aeb8fb919e3f347e9050fb276c5"
)
EXPECTED_NESTED_ENVIRONMENT_PREFIXES_TO_REMOVE: Final = [
    "PYTHON",
    "LEAN",
    "LAKE",
    "ELAN",
    "LD_",
    "DYLD_",
    "GIT_",
]
EXPECTED_NESTED_ENVIRONMENT_KEYS_TO_REMOVE: Final = sorted(
    [
        "AR",
        "AS",
        "CARGO_BUILD_RUSTC",
        "CARGO_ENCODED_RUSTFLAGS",
        "CC",
        "CFLAGS",
        "CPATH",
        "CPPFLAGS",
        "CPLUS_INCLUDE_PATH",
        "CXX",
        "CXXFLAGS",
        "C_INCLUDE_PATH",
        "DEVELOPER_DIR",
        "GCONV_PATH",
        "GLIBC_TUNABLES",
        "LDFLAGS",
        "LD",
        "LIBPATH",
        "LIBRARY_PATH",
        "MACOSX_DEPLOYMENT_TARGET",
        "NM",
        "OBJCOPY",
        "OBJDUMP",
        "OBJC_INCLUDE_PATH",
        "RANLIB",
        "RUSTC",
        "RUSTDOCFLAGS",
        "RUSTFLAGS",
        "RUSTUP_TOOLCHAIN",
        "SDKROOT",
        "SHLIB_PATH",
        "STRIP",
    ]
)
ALLOWED_COMPONENT = re.compile(r"[A-Za-z0-9._+\-]+\Z")
LEAN_VERSION_LINE = re.compile(
    rb"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    rb"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), commit "
    rb"(?P<commit>[0-9a-f]{40}), (?P<build>[A-Za-z][A-Za-z0-9_.+\-]*)\)\n\Z"
)
LAKE_VERSION_LINE = re.compile(
    rb"Lake version (?P<lake>[0-9]+\.[0-9]+\.[0-9]+-src\+[0-9a-f]{7}) "
    rb"\(Lean version (?P<lean>[0-9]+\.[0-9]+\.[0-9]+)\)\n\Z"
)

EXPECTED_LIMITS: Final = {
    "archive_bytes_max": 600_000_000,
    "child_output_bytes_max": 65_536,
    "decompressed_stream_bytes_max": 3_200_000_000,
    "directories_max": 1_000,
    "direct_child_reap_timeout_milliseconds": 2_000,
    "file_bytes_max": 250_000_000,
    "members_max": 20_000,
    "nested_kernel_inner_replay_timeout_seconds": 900,
    "nested_kernel_non_replay_lean_child_timeout_seconds": 120,
    "nested_kernel_non_replay_lean_child_count": 6,
    "nested_kernel_identity_child_timeout_seconds": 60,
    "nested_kernel_identity_child_count": 4,
    "nested_kernel_orchestration_headroom_seconds": 240,
    "nested_kernel_non_replay_margin_seconds": 1_200,
    "nested_kernel_regression_timeout_seconds": 4_200,
    "nested_kernel_replay_count": 3,
    "nested_kernel_required_outer_timeout_seconds": 3_900,
    "path_bytes_max": 256,
    "path_depth_max": 16,
    "process_group_kill_grace_milliseconds": 2_000,
    "process_group_poll_interval_milliseconds": 10,
    "process_group_term_grace_milliseconds": 500,
    "process_timeout_seconds": 30,
    "regular_file_bytes_max": 3_500_000_000,
    "regular_files_max": 19_000,
    "stream_timeout_seconds": 300,
}

EXPECTED_PROVIDER_OBSERVATION_PROVENANCE: Final = {
    "authentication": "none",
    "classification": "manually_transcribed_github_provider_observations",
    "observed_utc_date": "2026-08-07",
    "raw_provider_response_retained": False,
    "routes": {
        "compare_pull_request_result_to_tag": (
            "https://api.github.com/repos/leanprover/lean4/compare/"
            "a39eab69e1eee9ad38f4efe507907b1026a77808..."
            "f3b06c705e6c85f5314019d5d3baab0fec5b580c"
        ),
        "fix_commit": (
            "https://api.github.com/repos/leanprover/lean4/commits/"
            "8be817b3f6310f62f220861b0c92dbabb951115d"
        ),
        "pull_request": "https://api.github.com/repos/leanprover/lean4/pulls/14577",
        "pull_request_result_commit": (
            "https://api.github.com/repos/leanprover/lean4/commits/"
            "a39eab69e1eee9ad38f4efe507907b1026a77808"
        ),
        "release": (
            "https://api.github.com/repos/leanprover/lean4/releases/tags/v4.32.2"
        ),
        "tag_commit": (
            "https://api.github.com/repos/leanprover/lean4/commits/"
            "f3b06c705e6c85f5314019d5d3baab0fec5b580c"
        ),
    },
}

EXPECTED_ASSET_IDENTITIES: Final = {
    "darwin-aarch64": {
        "created_at": "2026-07-28T16:33:33Z",
        "name": "lean-4.32.2-darwin_aarch64.tar.zst",
        "root": "lean-4.32.2-darwin_aarch64",
        "size": 550_165_784,
        "sha256": "ea99ead969901b9fe4c7e7bf350b812a0249e9a5cea20474a737c0cc64746bc0",
        "id": 492_935_890,
        "system": "Darwin",
        "machines": ["arm64", "aarch64"],
        "updated_at": "2026-07-28T16:34:17Z",
    },
    "linux-x86_64": {
        "created_at": "2026-07-28T16:33:33Z",
        "name": "lean-4.32.2-linux.tar.zst",
        "root": "lean-4.32.2-linux",
        "size": 563_991_635,
        "sha256": "5f2069e6f5db73780f374ccb49ce8ea649aa20a0cebf0116816744c999ce72aa",
        "id": 492_935_897,
        "system": "Linux",
        "machines": ["x86_64", "amd64"],
        "updated_at": "2026-07-28T16:34:23Z",
    },
}

T = TypeVar("T")


class CustodyError(RuntimeError):
    """The source, policy, archive, extraction, or live identity check failed."""


class NestedExecutableEvidenceMismatch(CustodyError):
    """A typed, bounded direct-executable mismatch safe across the child boundary."""


@dataclass(frozen=True)
class FileIdentity:
    device: int
    inode: int
    mode: int
    links: int
    size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class StableSnapshot:
    path: Path
    data: bytes
    sha256: str
    identity: FileIdentity
    parent_identities: tuple[tuple[Path, FileIdentity], ...]


@dataclass(frozen=True)
class ExternalDigestSnapshot:
    path: Path
    sha256: str
    identity: FileIdentity


@dataclass(frozen=True)
class ExecutableSnapshot:
    launch_path: Path
    launch_identity: FileIdentity
    launch_target: str | None
    canonical_path: Path
    canonical_identity: FileIdentity
    data: bytes
    sha256: str


@dataclass(frozen=True)
class MemberRecord:
    path: str
    kind: str
    mode: str
    size: int


@dataclass(frozen=True)
class TreeEntry:
    path: str
    kind: str
    mode: str
    size: int | None
    sha256: str | None

    def canonical_row(self) -> dict[str, object]:
        if self.kind == "directory":
            return {"mode": self.mode, "path": self.path, "type": "directory"}
        require(
            self.size is not None and self.sha256 is not None, "file row is incomplete"
        )
        return {
            "mode": self.mode,
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
            "type": "file",
        }


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class LeanIdentity:
    version: str
    platform: str
    commit: str
    build: str


@dataclass(frozen=True)
class LegacyV4Authority:
    """Reviewed values extracted only from the frozen published v4 evidence pair."""

    inventory: dict[str, object]
    leaves: dict[str, object]
    probes: dict[str, object]
    tree_manifest: dict[str, object]
    decompressed_stream_bytes: int
    raw_sha256: str
    receipt_sha256: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CustodyError(message)


def require_bounded_cli_failure_payload(diagnostic: str, role: str) -> None:
    """Bound the complete production stderr line, including prefix and final LF."""

    try:
        payload = diagnostic.encode("ascii", errors="strict")
    except UnicodeError as error:
        raise CustodyError(f"{role} is not ASCII") from error
    complete = CLI_FAILURE_PREFIX.encode("ascii") + payload + b"\n"
    require(
        payload
        and len(payload) <= MISMATCH_DIAGNOSTIC_BYTES_MAX
        and all(0x20 <= byte <= 0x7E for byte in payload)
        and len(complete) <= CLI_FAILURE_STDERR_BYTES_MAX
        and complete.count(b"\n") == 1
        and b"\r" not in complete,
        f"{role} exceeded its complete CLI stderr boundary",
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise CustodyError(f"value is not canonical JSON: {error}") from error
    return rendered.encode("ascii")


def canonical_metadata_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise CustodyError(f"metadata is not canonical JSON: {error}") from error
    return (rendered + "\n").encode("ascii")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CustodyError("duplicate JSON object key is forbidden")
        result[key] = value
    return result


def reject_nonfinite_json_constant(token: str) -> object:
    """Reject Python's non-standard NaN/Infinity JSON extensions."""

    del token
    raise CustodyError("non-finite JSON constant is forbidden")


def reject_json_float(token: str) -> object:
    """Reject every JSON float token; custody schemas contain integers only."""

    del token
    raise CustodyError("JSON floating-point number is forbidden")


def parse_json_object(data: bytes, role: str) -> dict[str, object]:
    require(b"\r" not in data, f"{role} contains a carriage return")
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_json_constant,
            parse_float=reject_json_float,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CustodyError(f"{role} is not strict duplicate-free UTF-8 JSON") from error
    require(isinstance(value, dict), f"{role} root must be an object")
    return value


def exact_keys(value: object, expected: set[str], role: str) -> dict[str, object]:
    require(isinstance(value, dict), f"{role} must be an object")
    observed = set(value)
    require(observed == expected, f"{role} keys drifted")
    return value


def validate_exact_typed_object(
    value: object, expected: dict[str, object], role: str
) -> dict[str, object]:
    observed = exact_keys(value, set(expected), role)
    for key, expected_value in expected.items():
        require_exact_typed_value(
            observed[key], expected_value, f"{role} field {key!r}"
        )
    return observed


def require_exact_typed_value(observed: object, expected: object, role: str) -> None:
    """Recursively reject JSON bool/int and all other type/value collapses."""

    require(type(observed) is type(expected), f"{role} type/value drifted")
    if isinstance(expected, dict):
        require(isinstance(observed, dict), f"{role} must be an object")
        require(set(observed) == set(expected), f"{role} keys drifted")
        for key, expected_value in expected.items():
            require_exact_typed_value(observed[key], expected_value, f"{role}.{key}")
        return
    if isinstance(expected, list):
        require(isinstance(observed, list), f"{role} must be an array")
        require(len(observed) == len(expected), f"{role} length drifted")
        for index, expected_value in enumerate(expected):
            require_exact_typed_value(
                observed[index], expected_value, f"{role}[{index}]"
            )
        return
    require(observed == expected, f"{role} type/value drifted")


def require_exact_typed_shape(observed: object, expected: object, role: str) -> None:
    """Require the trusted recursive key/type/shape without comparing leaf values.

    The error text deliberately identifies only the fixed validator role.  It never
    renders an observed key, type, index, or value selected by the nested child.
    """

    require(type(observed) is type(expected), f"{role} schema shape drifted")
    if isinstance(expected, dict):
        require(isinstance(observed, dict), f"{role} schema shape drifted")
        require(set(observed) == set(expected), f"{role} schema shape drifted")
        for key, expected_value in expected.items():
            require_exact_typed_shape(observed[key], expected_value, role)
        return
    if isinstance(expected, list):
        require(isinstance(observed, list), f"{role} schema shape drifted")
        require(len(observed) == len(expected), f"{role} schema shape drifted")
        for observed_value, expected_value in zip(observed, expected, strict=True):
            require_exact_typed_shape(observed_value, expected_value, role)


def differing_json_field_paths(
    observed: object, expected: object, prefix: str = ""
) -> list[str]:
    """Return deterministic JSON-pointer names without reporting field values."""

    current = prefix or "/"
    if type(observed) is not type(expected):
        return [current]
    if isinstance(expected, dict):
        require(isinstance(observed, dict), "field-difference input must be an object")
        paths: list[str] = []
        for key in sorted(set(observed) | set(expected)):
            escaped = key.replace("~", "~0").replace("/", "~1")
            child = f"{prefix}/{escaped}"
            if key not in observed or key not in expected:
                paths.append(child)
            else:
                paths.extend(
                    differing_json_field_paths(observed[key], expected[key], child)
                )
        return paths
    if isinstance(expected, list):
        require(isinstance(observed, list), "field-difference input must be an array")
        paths = []
        for index in range(max(len(observed), len(expected))):
            child = f"{prefix}/{index}"
            if index >= len(observed) or index >= len(expected):
                paths.append(child)
            else:
                paths.extend(
                    differing_json_field_paths(observed[index], expected[index], child)
                )
        return paths
    return [] if observed == expected else [current]


def bounded_differing_json_field_paths(
    observed: object, expected: object
) -> tuple[list[str], bool]:
    """Return bounded deterministic JSON-pointer names, or only an overflow bit.

    The observed value can come from the nested child.  Once any pointer-count or
    pointer-byte bound would be exceeded, no pointer names are returned.  This
    prevents a child-selected key from crossing the diagnostic boundary through
    a structural-validation error.
    """

    paths: list[str] = []
    overflow = False

    def append_path(path: str) -> None:
        nonlocal overflow
        if overflow:
            return
        if (
            not path
            or len(path.encode("utf-8")) > MISMATCH_FIELD_PATH_BYTES_MAX
            or len(paths) >= MISMATCH_FIELD_PATHS_MAX
        ):
            paths.clear()
            overflow = True
            return
        paths.append(path)

    def visit(observed_value: object, expected_value: object, prefix: str) -> None:
        nonlocal overflow
        if overflow:
            return
        current = prefix or "/"
        if type(observed_value) is not type(expected_value):
            append_path(current)
            return
        if isinstance(expected_value, dict):
            require(
                isinstance(observed_value, dict),
                "bounded field-difference input must be an object",
            )
            keys = set(observed_value) | set(expected_value)
            if not all(isinstance(key, str) for key in keys):
                paths.clear()
                overflow = True
                return
            for key in sorted(keys):
                escaped = key.replace("~", "~0").replace("/", "~1")
                child = f"{prefix}/{escaped}"
                if key not in observed_value or key not in expected_value:
                    append_path(child)
                else:
                    visit(observed_value[key], expected_value[key], child)
                if overflow:
                    return
            return
        if isinstance(expected_value, list):
            require(
                isinstance(observed_value, list),
                "bounded field-difference input must be an array",
            )
            for index in range(max(len(observed_value), len(expected_value))):
                child = f"{prefix}/{index}"
                if index >= len(observed_value) or index >= len(expected_value):
                    append_path(child)
                else:
                    visit(observed_value[index], expected_value[index], child)
                if overflow:
                    return
            return
        if observed_value != expected_value:
            append_path(current)

    visit(observed, expected, "")
    require(
        overflow or paths == sorted(set(paths)),
        "bounded mismatch reporter produced nondeterministic field paths",
    )
    return paths, overflow


def nested_evidence_mismatch_diagnostic(
    observed: object, expected: object, role: str
) -> str | None:
    """Build a digest-bearing report only for fixed-schema leaf-value mismatch."""

    require(
        role in NESTED_EXECUTABLE_EVIDENCE_ROLES,
        "nested executable evidence role drifted",
    )
    # This predicate must precede both digest construction and pointer discovery.
    # Missing/extra keys, wrong types, and wrong container shapes therefore take
    # only the generic result-stream-digest route at the outer trust boundary.
    require_exact_typed_shape(observed, expected, role)
    observed_digest = sha256_bytes(canonical_json_bytes(observed))
    expected_digest = sha256_bytes(canonical_json_bytes(expected))
    paths, overflow = bounded_differing_json_field_paths(observed, expected)
    if not paths and not overflow:
        return None
    require(
        not overflow and set(paths).issubset(NESTED_EXECUTABLE_EVIDENCE_VALUE_POINTERS),
        f"{role} typed mismatch pointer inventory drifted",
    )

    def render(label: str, detail: str) -> str:
        return (
            f"{label} disagrees with the outer live executable snapshot at fields: "
            f"{detail}; observed_evidence_sha256={observed_digest}; "
            f"expected_evidence_sha256={expected_digest}"
        )

    detail = json.dumps(
        paths,
        sort_keys=False,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    diagnostic = render(role, detail)
    require_bounded_cli_failure_payload(diagnostic, "fixed mismatch diagnostic")
    return diagnostic


def exact_hex(value: object, length: int, role: str) -> str:
    require(isinstance(value, str), f"{role} must be a string")
    require(
        re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None,
        f"{role} is malformed",
    )
    return value


def identity_from_stat(observed: os.stat_result) -> FileIdentity:
    return FileIdentity(
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=observed.st_mode,
        links=observed.st_nlink,
        size=observed.st_size,
        modified_ns=observed.st_mtime_ns,
        changed_ns=observed.st_ctime_ns,
    )


def directory_identity_from_stat(observed: os.stat_result) -> FileIdentity:
    """Bind a directory object without unrelated child-entry metadata."""

    require(stat.S_ISDIR(observed.st_mode), "repository parent is not a directory")
    return FileIdentity(
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=observed.st_mode,
        links=0,
        size=0,
        modified_ns=0,
        changed_ns=0,
    )


def enforce_private_directory_mode(path: Path, role: str) -> FileIdentity:
    """Set and verify mode 0700 after creation, independent of ambient umask."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    try:
        before = absolute.lstat()
        require(
            stat.S_ISDIR(before.st_mode) and not stat.S_ISLNK(before.st_mode),
            f"{role} is not a direct directory: {absolute}",
        )
        absolute.chmod(0o700)
        after = absolute.lstat()
    except OSError as error:
        raise CustodyError(
            f"cannot enforce {role} mode 0700: {absolute}: {error}"
        ) from error
    require(
        stat.S_ISDIR(after.st_mode) and not stat.S_ISLNK(after.st_mode),
        f"{role} changed away from a direct directory: {absolute}",
    )
    require(
        (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino),
        f"{role} identity changed while enforcing mode 0700: {absolute}",
    )
    require(
        stat.S_IMODE(after.st_mode) == 0o700,
        f"{role} mode is not 0700 after enforcement: {absolute}",
    )
    return directory_identity_from_stat(after)


def create_private_directory(path: Path, role: str) -> FileIdentity:
    """Create one direct private directory and enforce its intended mode."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    try:
        os.mkdir(absolute, 0o700)
    except OSError as error:
        raise CustodyError(f"cannot create {role}: {absolute}: {error}") from error
    return enforce_private_directory_mode(absolute, role)


def canonicalize_existing_directory(path: Path, role: str) -> Path:
    """Resolve only parent aliases while retaining the exact directory object."""

    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        before = lexical.lstat()
        canonical = lexical.resolve(strict=True)
        after = canonical.lstat()
    except OSError as error:
        raise CustodyError(f"cannot canonicalize {role}: {lexical}: {error}") from error
    require(
        stat.S_ISDIR(before.st_mode) and not lexical.is_symlink(),
        f"{role} is not a direct directory: {lexical}",
    )
    require(
        stat.S_ISDIR(after.st_mode) and not canonical.is_symlink(),
        f"{role} canonical route is not a direct directory: {canonical}",
    )
    require(
        identity_from_stat(before) == identity_from_stat(after),
        f"{role} endpoint identity changed across canonicalization",
    )
    require(
        canonical == canonical.resolve(strict=True),
        f"{role} canonical route is not stable",
    )
    return canonical


def require_canonical_existing_directory(path: Path, role: str) -> Path:
    """Require callers to have normalized an existing directory already."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    canonical = canonicalize_existing_directory(absolute, role)
    require(absolute == canonical, f"{role} path is not canonical")
    return absolute


def lstat_regular(path: Path, role: str, *, one_link: bool = True) -> FileIdentity:
    try:
        observed = path.lstat()
    except OSError as error:
        raise CustodyError(f"cannot lstat {role} {path}: {error}") from error
    require(stat.S_ISREG(observed.st_mode), f"{role} is not a regular file: {path}")
    require(not path.is_symlink(), f"{role} is a symbolic link: {path}")
    if one_link:
        require(
            observed.st_nlink == 1, f"{role} must have exactly one hard link: {path}"
        )
    return identity_from_stat(observed)


def require_repo_lexical_parents(
    path: Path, role: str
) -> tuple[tuple[Path, FileIdentity], ...]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    root = Path(os.path.abspath(os.fspath(ROOT)))
    try:
        relative = absolute.relative_to(root)
    except ValueError as error:
        raise CustodyError(
            f"repository input escapes the lexical root: {path}"
        ) from error
    identities: list[tuple[Path, FileIdentity]] = []
    cursor = root
    for component in (None, *relative.parts[:-1]):
        if component is not None:
            cursor /= component
        try:
            observed = cursor.lstat()
        except OSError as error:
            raise CustodyError(
                f"cannot lstat {role} repository parent {cursor}: {error}"
            ) from error
        require(
            stat.S_ISDIR(observed.st_mode),
            f"repository parent is not a directory: {cursor}",
        )
        require(
            not cursor.is_symlink(), f"repository parent is a symbolic link: {cursor}"
        )
        identities.append((cursor, directory_identity_from_stat(observed)))
    return tuple(identities)


def read_descriptor_bytes(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        block = os.read(descriptor, 1024 * 1024)
        if not block:
            return b"".join(chunks)
        chunks.append(block)


def snapshot_repo_file(path: Path, role: str) -> StableSnapshot:
    absolute = Path(os.path.abspath(os.fspath(path)))
    parents_before = require_repo_lexical_parents(absolute, role)
    before = lstat_regular(absolute, role)
    require(stat.S_IMODE(before.mode) == 0o644, f"{role} permissions must be 0644")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise CustodyError(f"cannot open {role} {absolute}: {error}") from error
    try:
        descriptor_before = identity_from_stat(os.fstat(descriptor))
        first = read_descriptor_bytes(descriptor)
        middle = identity_from_stat(os.fstat(descriptor))
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = read_descriptor_bytes(descriptor)
        descriptor_after = identity_from_stat(os.fstat(descriptor))
    except OSError as error:
        raise CustodyError(f"cannot read {role} {absolute}: {error}") from error
    finally:
        os.close(descriptor)
    after = lstat_regular(absolute, role)
    parents_after = require_repo_lexical_parents(absolute, role)
    require(
        before == descriptor_before == middle == descriptor_after == after,
        f"{role} identity changed during descriptor-bound double read",
    )
    require(first == second, f"{role} bytes changed during double read")
    require(len(first) == before.size, f"{role} size disagrees with its metadata")
    require(
        parents_after == parents_before,
        f"{role} parent identity changed during descriptor-bound double read",
    )
    return StableSnapshot(
        absolute,
        first,
        sha256_bytes(first),
        before,
        parents_before,
    )


def require_repo_snapshot_unchanged(original: StableSnapshot, role: str) -> None:
    replay = snapshot_repo_file(original.path, role)
    require(
        replay.identity == original.identity,
        f"{role} identity changed across qualification",
    )
    require(replay.data == original.data, f"{role} bytes changed across qualification")
    require(
        replay.parent_identities == original.parent_identities,
        f"{role} parent identity changed across qualification",
    )


def require_nested_checker_binding(
    observed: StableSnapshot, binding: dict[str, object]
) -> None:
    expected_path = ROOT / str(binding["path"])
    require(
        observed.path == expected_path,
        "nested checker repository path differs from its exact binding",
    )
    require(
        observed.identity.size == binding["bytes"],
        "nested checker byte-length binding drifted",
    )
    require(
        observed.sha256 == binding["sha256"],
        "nested checker SHA-256 binding drifted",
    )
    require(
        stat.S_IMODE(observed.identity.mode) == int(str(binding["mode"]), 8),
        "nested checker mode binding drifted",
    )
    require(
        observed.identity.links == 1 and binding["single_hard_link"] is True,
        "nested checker link-count binding drifted",
    )
    require(
        not observed.path.is_symlink() and binding["symbolic_link"] is False,
        "nested checker symbolic-link binding drifted",
    )


def snapshot_bound_nested_checker(metadata: dict[str, object]) -> StableSnapshot:
    checker_binding = metadata["checker_binding"]
    require(isinstance(checker_binding, dict), "toolchain checker binding is absent")
    nested_binding = checker_binding["nested_checker_binding"]
    require(isinstance(nested_binding, dict), "nested checker binding is absent")
    validate_nested_checker_binding(nested_binding)
    path = ROOT / str(nested_binding["path"])
    observed = snapshot_repo_file(path, "nested Lean kernel regression checker")
    require_nested_checker_binding(observed, nested_binding)
    return observed


def validate_historical_receipt_semantics(
    payload: dict[str, object], observation: dict[str, object]
) -> None:
    historical_result = payload.get("lean_darwin_archive_observation")
    require(
        isinstance(historical_result, dict),
        "historical Darwin source receipt JSON pointer is absent",
    )
    require(
        historical_result.get("lean_milestone_credit") == observation["prior_outcome"],
        "historical Darwin source receipt outcome drifted",
    )
    source_binding = historical_result.get("qualification_source_binding")
    require(
        isinstance(source_binding, dict),
        "historical Darwin qualification source binding is absent",
    )
    expected_historical_bindings = {
        "prior_custody_checker": ("checker_bytes", "checker_sha256"),
        "prior_metadata": ("metadata_bytes", "metadata_sha256"),
        "prior_nested_checker": ("nested_checker_bytes", "nested_checker_sha256"),
    }
    for role, (bytes_key, sha_key) in expected_historical_bindings.items():
        expected = observation[role]
        require(isinstance(expected, dict), f"historical {role} binding is malformed")
        require(
            source_binding.get(bytes_key) == expected["bytes"]
            and source_binding.get(sha_key) == expected["sha256"],
            f"historical Darwin source receipt {role} identity drifted",
        )


def snapshot_bound_historical_receipt(metadata: dict[str, object]) -> StableSnapshot:
    observations = metadata["historical_nontransferable_observations"]
    require(
        isinstance(observations, list) and len(observations) == 1,
        "historical nontransferable observation inventory drifted",
    )
    observation = observations[0]
    require(isinstance(observation, dict), "historical Darwin observation is malformed")
    receipt = observation["source_receipt"]
    require(isinstance(receipt, dict), "historical source receipt binding is malformed")
    path = ROOT / str(receipt["path"])
    observed = snapshot_repo_file(path, "historical Darwin source receipt")
    require(
        observed.path == path,
        "historical Darwin source receipt path differs from its exact binding",
    )
    require(
        observed.identity.size == receipt["bytes"],
        "historical Darwin source receipt byte-length binding drifted",
    )
    require(
        observed.sha256 == receipt["sha256"],
        "historical Darwin source receipt SHA-256 binding drifted",
    )
    require(
        stat.S_IMODE(observed.identity.mode) == int(str(receipt["mode"]), 8),
        "historical Darwin source receipt mode binding drifted",
    )
    require(
        observed.identity.links == 1 and receipt["single_hard_link"] is True,
        "historical Darwin source receipt link-count binding drifted",
    )
    require(
        not observed.path.is_symlink() and receipt["symbolic_link"] is False,
        "historical Darwin source receipt symbolic-link binding drifted",
    )
    payload = parse_json_object(observed.data, "historical Darwin source receipt")
    validate_historical_receipt_semantics(payload, observation)
    return observed


def repo_source_binding_evidence(snapshot: StableSnapshot) -> dict[str, object]:
    return {
        "bytes": snapshot.identity.size,
        "hard_link_count": snapshot.identity.links,
        "mode": f"{stat.S_IMODE(snapshot.identity.mode):04o}",
        "path": os.fspath(snapshot.path.relative_to(ROOT)),
        "sha256": snapshot.sha256,
        "symbolic_link": False,
    }


def metadata_policy_projection(metadata: dict[str, object]) -> dict[str, object]:
    binding = exact_keys(
        metadata.get("checker_binding"),
        {
            "checker_bytes",
            "checker_path",
            "checker_sha256",
            "nested_checker_binding",
            "policy",
            "projection_omits",
        },
        "checker binding",
    )
    nested = exact_keys(
        binding["nested_checker_binding"],
        {"bytes", "mode", "path", "sha256", "single_hard_link", "symbolic_link"},
        "nested checker binding",
    )
    projected_nested = {
        key: value for key, value in nested.items() if key not in {"bytes", "sha256"}
    }
    projected_binding = {
        key: value
        for key, value in binding.items()
        if key not in {"checker_bytes", "checker_sha256", "nested_checker_binding"}
    }
    projected_binding["nested_checker_binding"] = projected_nested
    projection = dict(metadata)
    projection["checker_binding"] = projected_binding
    return projection


def metadata_policy_sha256(metadata: dict[str, object]) -> str:
    return sha256_bytes(canonical_json_bytes(metadata_policy_projection(metadata)))


def _legacy_receipt_raw_identity(
    receipt: dict[str, object], route: tuple[str, ...], role: str
) -> object:
    cursor: object = receipt
    for component in route:
        require(isinstance(cursor, dict), f"{role} route drifted")
        require(component in cursor, f"{role} route component is absent")
        cursor = cursor[component]
    return cursor


def parse_legacy_v4_authority(
    raw_source: bytes,
    receipt_source: bytes,
    *,
    enforce_published_seals: bool,
) -> LegacyV4Authority:
    """Parse v4 observation evidence without consulting mutable v3 metadata.

    The unsealed mode exists only so the mutation suite can coordinate the raw
    byte identity duplicated by the receipt and exercise intrinsic v4
    semantics. Production uses the sealed wrapper below.
    """

    raw_sha256 = sha256_bytes(raw_source)
    receipt_sha256 = sha256_bytes(receipt_source)
    if enforce_published_seals:
        require(
            len(raw_source) == EXPECTED_LEGACY_OBSERVATION_RAW_BYTES
            and raw_sha256 == EXPECTED_LEGACY_OBSERVATION_RAW_SHA256,
            "published legacy-v4 raw evidence identity drifted",
        )
        require(
            len(receipt_source) == EXPECTED_LEGACY_OBSERVATION_RECEIPT_BYTES
            and receipt_sha256 == EXPECTED_LEGACY_OBSERVATION_RECEIPT_SHA256,
            "published legacy-v4 receipt evidence identity drifted",
        )
    raw = parse_json_object(raw_source, "legacy-v4 Darwin observation")
    receipt = parse_json_object(receipt_source, "legacy-v4 Darwin receipt")
    require(
        raw_source == canonical_json_bytes(raw) + b"\n",
        "legacy-v4 Darwin observation is not canonical one-line JSON",
    )
    require(
        receipt_source == canonical_json_bytes(receipt) + b"\n",
        "legacy-v4 Darwin receipt is not canonical one-line JSON",
    )
    exact_keys(
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
        "legacy-v4 Darwin observation",
    )
    exact_keys(
        receipt,
        {
            "acyclic_boundary",
            "capture",
            "decisive_result_projection",
            "nonclaims",
            "promotion_review",
            "schema",
            "schema_revision",
            "scope",
            "source_subject",
        },
        "legacy-v4 Darwin receipt",
    )
    require(
        raw["schema"] == LEGACY_RESULT_SCHEMA
        and raw["status"] == "observation_only_unqualified"
        and raw["platform_key"] == "darwin-aarch64"
        and raw["qualification_state_before_run"] == "hosted_pending",
        "legacy-v4 lifecycle identity drifted",
    )
    require(
        receipt["schema"] == LEGACY_RECEIPT_SCHEMA
        and type(receipt["schema_revision"]) is int
        and receipt["schema_revision"] == 1,
        "legacy-v4 receipt schema drifted",
    )
    for route in (
        ("capture", "repository_raw_result"),
        ("capture", "external_owner_mutable_custody", "result"),
        (
            "decisive_result_projection",
            "complete_inventory_tree_leaves_probes_authority",
        ),
    ):
        identity = _legacy_receipt_raw_identity(receipt, route, "legacy raw identity")
        require(isinstance(identity, dict), "legacy raw identity must be an object")
        require(
            type(identity.get("bytes")) is int
            and identity["bytes"] == len(raw_source)
            and identity.get("sha256") == raw_sha256,
            "legacy receipt raw byte identity drifted",
        )
    decisive = exact_keys(
        receipt["decisive_result_projection"],
        {
            "archive",
            "candidate_promotion_status",
            "complete_inventory_tree_leaves_probes_authority",
            "nested_kernel_regression",
            "platform_key",
            "qualification_state_before_run",
            "raw_schema",
            "release_identity_cross_check",
            "status",
        },
        "legacy decisive projection",
    )
    require(
        decisive["raw_schema"] == raw["schema"]
        and decisive["status"] == raw["status"]
        and decisive["platform_key"] == raw["platform_key"]
        and decisive["qualification_state_before_run"]
        == raw["qualification_state_before_run"],
        "legacy decisive lifecycle projection drifted",
    )
    archive = exact_keys(
        raw["archive"],
        {
            "advertised_github_asset",
            "extraction_decompressed_stream_bytes",
            "path",
            "preflight_decompressed_stream_bytes",
            "sha256_after",
            "sha256_before",
            "size",
        },
        "legacy archive",
    )
    expected_asset = EXPECTED_ASSET_IDENTITIES["darwin-aarch64"]
    require(
        type(archive["size"]) is int
        and archive["size"] == expected_asset["size"]
        and archive["sha256_before"] == expected_asset["sha256"]
        and archive["sha256_after"] == expected_asset["sha256"],
        "legacy archive advertised identity drifted",
    )
    require(
        type(archive["preflight_decompressed_stream_bytes"]) is int
        and archive["preflight_decompressed_stream_bytes"] > 0
        and archive["preflight_decompressed_stream_bytes"]
        == archive["extraction_decompressed_stream_bytes"]
        <= EXPECTED_LIMITS["decompressed_stream_bytes_max"],
        "legacy decompressed stream lengths differ or exceed the bound",
    )
    preflight = exact_keys(
        raw["safe_preflight"],
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
        "legacy safe preflight",
    )
    require(
        preflight["resource_limits"] == EXPECTED_LIMITS
        and preflight["single_expected_root"] == expected_asset["root"]
        and all(
            preflight[key] is True
            for key in (
                "links_devices_fifos_sockets_rejected",
                "normalized_unique_paths",
                "only_directories_and_regular_files",
                "parent_topology_complete",
                "portable_casefold_unique_paths",
            )
        ),
        "legacy preflight policy drifted",
    )
    candidate = exact_keys(
        raw["candidate_receipt"],
        {
            "inventory",
            "leaves",
            "probes",
            "promotion_status",
            "required_next_step",
            "tree_manifest",
        },
        "legacy candidate receipt",
    )
    inventory = validate_inventory_shape(preflight["inventory"], "legacy inventory")
    require(
        inventory == candidate["inventory"]
        and all(type(value) is int and value > 0 for value in inventory.values()),
        "legacy candidate inventory copy or positivity drifted",
    )
    require(
        inventory["members"] == inventory["directories"] + inventory["regular_files"],
        "legacy inventory member arithmetic drifted",
    )
    require(
        inventory["regular_file_bytes"] >= inventory["max_file_bytes"]
        and inventory["regular_file_bytes"]
        <= archive["extraction_decompressed_stream_bytes"],
        "legacy inventory byte maxima are contradictory",
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
        require(
            inventory[observed_key] <= EXPECTED_LIMITS[limit_key],
            f"legacy inventory {observed_key} exceeds its resource ceiling",
        )
    tree = exact_keys(
        raw["canonical_tree_manifest"],
        {"algorithm", "format", "pre_post_equal", "sha256"},
        "legacy tree manifest",
    )
    require(
        tree == candidate["tree_manifest"], "legacy candidate manifest copy drifted"
    )
    require(
        tree["algorithm"] == "sha256"
        and tree["format"] == MANIFEST_FORMAT
        and tree["pre_post_equal"] is True,
        "legacy tree-manifest contract drifted",
    )
    exact_hex(tree["sha256"], 64, "legacy tree-manifest SHA-256")
    leaves = exact_keys(
        raw["executable_leaves"],
        {"lake", "lean", "leanchecker"},
        "legacy executable leaves",
    )
    require(leaves == candidate["leaves"], "legacy candidate leaf copy drifted")
    leaf_total = 0
    for role, value in leaves.items():
        leaf = validate_leaf_shape(value, f"legacy {role} leaf")
        require(leaf["path"] == f"bin/{role}", f"legacy {role} path drifted")
        require(
            leaf["size"] <= inventory["max_file_bytes"],
            f"legacy {role} leaf exceeds maximum file bytes",
        )
        full_path = f"{expected_asset['root']}/{leaf['path']}"
        require(
            len(full_path.encode("utf-8")) <= inventory["max_path_bytes"]
            and len(full_path.split("/")) <= inventory["max_depth"],
            f"legacy {role} path exceeds inventory bounds",
        )
        leaf_total += int(leaf["size"])
    require(
        inventory["regular_files"] >= len(leaves)
        and leaf_total <= inventory["regular_file_bytes"],
        "legacy executable leaves contradict inventory",
    )
    probes = exact_keys(
        raw["live_probes"],
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
        "legacy live probes",
    )
    require(probes == candidate["probes"], "legacy candidate probe copy drifted")
    identity = parse_lean_version(
        ProcessResult(0, str(probes["lean_stdout"]).encode("ascii"), b"")
    )
    require(
        probes["version"] == identity.version
        and probes["commit"] == identity.commit
        and probes["build"] == identity.build
        and probes["lean_platform"] == identity.platform
        and identity.platform == EXPECTED_DARWIN_PLATFORM,
        "legacy Lean probe scalar/stdout coupling drifted",
    )
    validate_lake_version(
        ProcessResult(0, str(probes["lake_stdout"]).encode("ascii"), b"")
    )
    require(
        type(probes["leanchecker_absent_module_exit"]) is int,
        "legacy absent-module exit must be an integer",
    )
    validate_leanchecker_probe(
        ProcessResult(
            int(probes["leanchecker_absent_module_exit"]),
            b"",
            str(probes["leanchecker_absent_module_stderr"]).encode("ascii"),
        )
    )
    nested = exact_keys(
        raw["nested_kernel_regression"],
        {"reason", "same_extraction_transaction", "status"},
        "legacy nested result",
    )
    require(
        nested
        == {
            "reason": (
                "hosted-pending derived executable pins cannot qualify the direct "
                "regression route in the observation run"
            ),
            "same_extraction_transaction": False,
            "status": "not_run_unqualified_asset",
        }
        and candidate["promotion_status"] == "not_qualified_same_run",
        "legacy no-same-run lifecycle drifted",
    )
    host = exact_keys(raw["host"], {"machine", "system"}, "legacy host")
    require(
        host["system"] == "Darwin" and host["machine"] in {"arm64", "aarch64"},
        "legacy Darwin host identity drifted",
    )
    require(
        sha256_bytes(canonical_json_bytes(raw["authentication_boundary"]))
        == EXPECTED_AUTHENTICATION_BOUNDARY_SHA256,
        "legacy authentication boundary drifted",
    )
    return LegacyV4Authority(
        inventory=dict(inventory),
        leaves=dict(leaves),
        probes=dict(probes),
        tree_manifest=dict(tree),
        decompressed_stream_bytes=int(archive["extraction_decompressed_stream_bytes"]),
        raw_sha256=raw_sha256,
        receipt_sha256=receipt_sha256,
    )


def load_frozen_legacy_v4_authority(
    raw_snapshot: StableSnapshot, receipt_snapshot: StableSnapshot
) -> LegacyV4Authority:
    require(
        raw_snapshot.path == LEGACY_OBSERVATION_RAW_PATH
        and receipt_snapshot.path == LEGACY_OBSERVATION_RECEIPT_PATH,
        "published legacy-v4 evidence paths drifted",
    )
    return parse_legacy_v4_authority(
        raw_snapshot.data,
        receipt_snapshot.data,
        enforce_published_seals=True,
    )


def validate_subject(metadata: dict[str, object]) -> None:
    subject = exact_keys(
        metadata.get("subject"),
        {"repository", "release", "fix", "provider_recorded_pull_request_result"},
        "subject",
    )
    require(
        subject["repository"] == "https://github.com/leanprover/lean4",
        "repository identity drifted",
    )
    expected_release = {
        "created_at": "2026-07-28T14:26:42Z",
        "draft": False,
        "id": 361_230_720,
        "name": "v4.32.2",
        "prerelease": False,
        "published_at": "2026-07-28T16:34:35Z",
        "tag": "v4.32.2",
        "tag_commit": EXPECTED_COMMIT,
        "tag_commit_parent": EXPECTED_FIX_COMMIT,
        "tag_commit_signature": "unsigned",
        "tag_commit_tree": "5df28f43fb70e35300783fa33f97dadaabd1f5e2",
        "tag_object_type": "commit",
        "target_commitish": "master",
        "url": "https://github.com/leanprover/lean4/releases/tag/v4.32.2",
    }
    release = validate_exact_typed_object(
        subject["release"], expected_release, "release/tag identity drifted"
    )
    expected_fix = {
        "commit": EXPECTED_FIX_COMMIT,
        "commit_parent": EXPECTED_FIX_PARENT,
        "commit_signature": "unsigned",
        "commit_subject": "fix: missing check at kernel inductive declaration (#14577)",
        "commit_subject_bytes": 59,
        "commit_subject_sha256": (
            "b59fc317313e4f24ea32a3ca6cea97c81257436e6393f96f2674048d6af89aa5"
        ),
        "commit_tree": "ddf459e027f32e994e9a7781b1c4b28f90b0203e",
        "issue": 14_576,
        "issue_url": "https://github.com/leanprover/lean4/issues/14576",
        "pull_request": 14_577,
        "pull_request_url": "https://github.com/leanprover/lean4/pull/14577",
        "release_branch_role": "fix_backport",
    }
    fix = validate_exact_typed_object(
        subject["fix"], expected_fix, "fix identity drifted"
    )
    require(
        type(fix["commit_subject_bytes"]) is int
        and fix["commit_subject_bytes"]
        == len(str(fix["commit_subject"]).encode("utf-8"))
        and fix["commit_subject_sha256"]
        == sha256_bytes(str(fix["commit_subject"]).encode("utf-8")),
        "issue-14576 fix subject byte identity drifted",
    )
    expected_pull_request_result = {
        "commit": EXPECTED_PULL_REQUEST_RESULT_COMMIT,
        "commit_subject": "fix: missing check at kernel inductive declaration (#14577)",
        "commit_subject_bytes": 59,
        "commit_subject_sha256": (
            "b59fc317313e4f24ea32a3ca6cea97c81257436e6393f96f2674048d6af89aa5"
        ),
        "commit_tree": "c789d5c648cc81bae0a4cdeaefe4ae451cc65320",
        "history_shape": "one_parent_not_two_parent_merge_commit",
        "merge_base_with_tag_commit": EXPECTED_PULL_REQUEST_RELEASE_MERGE_BASE,
        "parent_count": 1,
        "provider_field": "merge_commit_sha",
        "provider_metadata_authentication": "none",
        "provider_verification_reason": "valid",
        "provider_verification_verified": True,
        "relation_to_tag_commit": "divergent",
        "sole_parent": "b1722adad3d00ad4443a08709b1efb93a78b477c",
    }
    pull_request_result = validate_exact_typed_object(
        subject["provider_recorded_pull_request_result"],
        expected_pull_request_result,
        "provider-recorded pull-request result divergence identity drifted",
    )
    require(
        type(pull_request_result["parent_count"]) is int
        and pull_request_result["parent_count"] == 1
        and pull_request_result["history_shape"]
        == "one_parent_not_two_parent_merge_commit"
        and pull_request_result["provider_field"] == "merge_commit_sha"
        and type(pull_request_result["provider_verification_verified"]) is bool
        and pull_request_result["provider_verification_verified"] is True
        and type(pull_request_result["commit_subject_bytes"]) is int
        and pull_request_result["commit_subject_bytes"]
        == len(str(pull_request_result["commit_subject"]).encode("utf-8"))
        and pull_request_result["commit_subject_sha256"]
        == sha256_bytes(str(pull_request_result["commit_subject"]).encode("utf-8")),
        "provider-recorded pull-request result typed subject/history/verification identity drifted",
    )
    require(
        release["tag_commit_parent"] == fix["commit"],
        "release tag is not the exact direct child of the fix",
    )
    require(
        pull_request_result["commit"]
        not in {
            release["tag_commit"],
            release["tag_commit_parent"],
            fix["commit_parent"],
            pull_request_result["merge_base_with_tag_commit"],
        },
        "pull-request result divergence observation collapsed distinct commits",
    )
    require(
        pull_request_result["commit_tree"] != fix["commit_tree"]
        and pull_request_result["commit_subject_sha256"]
        == fix["commit_subject_sha256"],
        "divergent pull-request/backport tree and shared-subject relation drifted",
    )


def validate_inventory_shape(value: object, role: str) -> dict[str, object]:
    inventory = exact_keys(
        value,
        {
            "directories",
            "max_depth",
            "max_file_bytes",
            "max_path_bytes",
            "members",
            "regular_file_bytes",
            "regular_files",
        },
        role,
    )
    for key, item in inventory.items():
        require(
            type(item) is int and item >= 0,
            f"{role}.{key} must be a nonnegative integer",
        )
    return inventory


def validate_leaf_shape(value: object, role: str) -> dict[str, object]:
    leaf = exact_keys(value, {"mode", "path", "sha256", "size"}, role)
    require(leaf["mode"] == "0755", f"{role} mode must be 0755")
    require(
        isinstance(leaf["path"], str)
        and leaf["path"] in {"bin/lean", "bin/lake", "bin/leanchecker"},
        f"{role} path drifted",
    )
    exact_hex(leaf["sha256"], 64, f"{role} SHA-256")
    require(
        type(leaf["size"]) is int and leaf["size"] > 0, f"{role} size must be positive"
    )
    return leaf


def validate_nested_checker_binding(value: object) -> dict[str, object]:
    binding = exact_keys(
        value,
        {
            "bytes",
            "mode",
            "path",
            "sha256",
            "single_hard_link",
            "symbolic_link",
        },
        "nested checker binding",
    )
    require(
        binding["path"] == "scripts/check-lean-kernel-14576.py",
        "nested checker binding path drifted",
    )
    require(
        type(binding["bytes"]) is int
        and binding["bytes"] == EXPECTED_NESTED_CHECKER_BYTES,
        "nested checker binding byte length drifted",
    )
    require(
        binding["sha256"] == EXPECTED_NESTED_CHECKER_SHA256,
        "nested checker binding SHA-256 drifted",
    )
    require(binding["mode"] == "0644", "nested checker binding mode must be 0644")
    require(
        binding["single_hard_link"] is True,
        "nested checker binding must require exactly one hard link",
    )
    require(
        binding["symbolic_link"] is False,
        "nested checker binding must reject symbolic links",
    )
    return binding


def validate_historical_nontransferable_observations(value: object) -> None:
    require(
        isinstance(value, list) and len(value) == 1,
        "historical nontransferable observation inventory drifted",
    )
    observation = exact_keys(
        value[0],
        {
            "classification",
            "current_packet_qualification_credit",
            "platform_key",
            "prior_custody_checker",
            "prior_metadata",
            "prior_nested_checker",
            "prior_outcome",
            "reason_nontransferable",
            "source_receipt",
            "transfer_to_current_packet",
        },
        "historical Darwin observation",
    )
    require(
        observation["classification"]
        == "historical_nontransferable_changed_packet_bytes"
        and observation["current_packet_qualification_credit"] == "none"
        and observation["platform_key"] == "darwin-aarch64"
        and observation["transfer_to_current_packet"] is False,
        "historical Darwin observation classification drifted",
    )
    require(
        observation["prior_outcome"]
        == "historical_darwin_toolchain_qualification_and_issue_14576_same_kernel_regression_only",
        "historical Darwin outcome boundary drifted",
    )
    require(
        observation["reason_nontransferable"]
        == EXPECTED_HISTORICAL_NONTRANSFERABILITY_REASON,
        "historical Darwin nontransferability reason drifted",
    )
    expected_sources = {
        "prior_custody_checker": (
            68_575,
            "cdb7e5e611dd0973b1342e24fd9e955cb303c30cad4ba7d418d75306e7990c60",
        ),
        "prior_metadata": (
            8_458,
            "9e501109e3f728f2f9d0c65c1c91884b411ae9597dfab21295c69179f64de731",
        ),
        "prior_nested_checker": (
            68_990,
            "f3bd7cfa08db1343ffbd875f05887e9dac66b89a910f061a70929e051f0d5967",
        ),
    }
    for role, (expected_bytes, expected_sha256) in expected_sources.items():
        validate_exact_typed_object(
            observation[role],
            {"bytes": expected_bytes, "sha256": expected_sha256},
            f"historical {role} identity drifted",
        )
    validate_exact_typed_object(
        observation["source_receipt"],
        {
            "bytes": 144_128,
            "json_pointer": "/lean_darwin_archive_observation",
            "mode": "0644",
            "path": (
                "audit/evidence/c3-post-correction-publication-custody-2026-08-06.json"
            ),
            "sha256": (
                "6820d85dad4bada7ec2c52923a7f1c6d1b389c4d705f0dcb26277886b3595f43"
            ),
            "single_hard_link": True,
            "symbolic_link": False,
        },
        "historical source receipt identity drifted",
    )


def validate_reviewed_pin_source(
    value: object, authority: LegacyV4Authority
) -> dict[str, object]:
    source = exact_keys(
        value,
        {
            "classification",
            "observed_lifecycle",
            "publication_authentication",
            "published_observation",
            "raw_evidence",
            "raw_schema",
            "receipt_evidence",
            "receipt_schema",
            "transferred_credit",
        },
        "Darwin reviewed-pin source",
    )
    exact_keys(
        source["published_observation"],
        {
            "commit",
            "direct_parent",
            "direct_parent_parent",
            "direct_parent_tree",
            "object_format",
            "repository",
            "tree",
        },
        "published observation identity",
    )
    for role in ("raw_evidence", "receipt_evidence"):
        evidence = exact_keys(
            source[role],
            {
                "bytes",
                "git_blob_sha1",
                "git_tree_mode",
                "path",
                "runtime_mode",
                "sha256",
                "single_hard_link",
                "symbolic_link",
            },
            role.replace("_", " "),
        )
        require(
            type(evidence["bytes"]) is int
            and evidence["bytes"] > 0
            and evidence["git_tree_mode"] == "100644"
            and evidence["runtime_mode"] == "0644"
            and evidence["single_hard_link"] is True
            and evidence["symbolic_link"] is False,
            f"{role} repository/runtime shape drifted",
        )
        exact_hex(evidence["git_blob_sha1"], 40, f"{role} Git blob SHA-1")
        exact_hex(evidence["sha256"], 64, f"{role} SHA-256")
    exact_keys(
        source["observed_lifecycle"],
        {
            "lifecycle_state_before_run",
            "nested_status",
            "promotion_status",
            "same_extraction_transaction",
            "status",
        },
        "observed legacy lifecycle",
    )
    exact_keys(
        source["transferred_credit"],
        {"nested_regression", "reviewed_pin_values", "strict_archive_custody"},
        "reviewed-pin transferred credit",
    )
    require(
        sha256_bytes(canonical_json_bytes(source))
        == EXPECTED_REVIEWED_PIN_SOURCE_SHA256,
        "Darwin reviewed-pin source identity drifted",
    )
    require(
        source["raw_evidence"]["sha256"] == authority.raw_sha256
        and source["receipt_evidence"]["sha256"] == authority.receipt_sha256,
        "Darwin reviewed-pin source disagrees with frozen legacy authority",
    )
    return source


def validate_custody_lifecycle(
    value: object,
    asset_key: str,
    expected: dict[str, object],
    limits: dict[str, object],
    legacy_authority: LegacyV4Authority | None,
) -> dict[str, object]:
    lifecycle = exact_keys(
        value,
        {
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
        },
        f"{asset_key} custody lifecycle",
    )
    require(
        lifecycle["archive_custody_credit"] == "none"
        and lifecycle["static_qualification_credit"] == "none"
        and lifecycle["static_schema_credit"] == "internal_consistency_only",
        f"{asset_key} static credit boundary drifted",
    )
    if asset_key == "linux-x86_64":
        require(
            lifecycle["state"] == "hosted_pending"
            and lifecycle["permitted_route"] == "observation_only"
            and lifecycle["required_next_step"]
            == "observation_then_separate_reviewed_pin_promotion_then_fresh_strict_replay"
            and lifecycle["pending_reason"]
            == (
                "The exact GitHub-advertised archive size and SHA-256 are pinned, but "
                "no independently reviewed extracted-tree, executable-leaf, or "
                "live-version observation was available when this metadata revision "
                "was sealed."
            ),
            "Linux pending lifecycle route drifted",
        )
        require(
            lifecycle["reviewed_pin_source"] is None
            and lifecycle["inventory"] is None
            and lifecycle["leaves"] is None
            and lifecycle["probes"] is None
            and lifecycle["tree_manifest"] is None,
            "Linux pending lifecycle must not contain reviewed derived pins",
        )
        return lifecycle
    require(
        asset_key == "darwin-aarch64" and legacy_authority is not None,
        "Darwin reviewed pins require the frozen legacy-v4 authority",
    )
    require(
        lifecycle["state"] == "reviewed_pins_strict_replay_required"
        and lifecycle["permitted_route"] == "strict_replay_only"
        and lifecycle["required_next_step"]
        == "fresh_strict_replay_from_exact_published_packet"
        and lifecycle["pending_reason"] is None,
        "Darwin reviewed-pin strict-replay lifecycle drifted",
    )
    inventory = validate_inventory_shape(
        lifecycle["inventory"], f"{asset_key} inventory"
    )
    require(
        all(type(item) is int and item > 0 for item in inventory.values()),
        f"{asset_key} inventory values must be positive integers",
    )
    require(
        inventory["members"] == inventory["directories"] + inventory["regular_files"],
        f"{asset_key} inventory member arithmetic drifted",
    )
    require(
        inventory["regular_file_bytes"] >= inventory["max_file_bytes"]
        and inventory["regular_file_bytes"]
        <= legacy_authority.decompressed_stream_bytes,
        f"{asset_key} inventory byte relations are contradictory",
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
        require(
            inventory[observed_key] <= limits[limit_key],
            f"{asset_key} inventory {observed_key} exceeds its resource ceiling",
        )
    leaves = exact_keys(
        lifecycle["leaves"], {"lean", "lake", "leanchecker"}, f"{asset_key} leaves"
    )
    leaf_total = 0
    leaf_paths: set[str] = set()
    for role, leaf in leaves.items():
        observed = validate_leaf_shape(leaf, f"{asset_key} {role} leaf")
        require(
            observed["path"] == f"bin/{role}", f"{asset_key} {role} leaf route drifted"
        )
        require(
            observed["path"] not in leaf_paths,
            f"{asset_key} executable leaf paths are not distinct",
        )
        leaf_paths.add(str(observed["path"]))
        require(
            observed["size"] <= inventory["max_file_bytes"],
            f"{asset_key} {role} leaf exceeds max_file_bytes",
        )
        full_path = f"{expected['root']}/{observed['path']}"
        require(
            len(full_path.encode("utf-8")) <= inventory["max_path_bytes"]
            and len(full_path.split("/")) <= inventory["max_depth"],
            f"{asset_key} {role} leaf exceeds inventory path bounds",
        )
        leaf_total += int(observed["size"])
    require(
        inventory["regular_files"] >= len(leaves)
        and leaf_total <= inventory["regular_file_bytes"],
        f"{asset_key} executable leaves contradict inventory",
    )
    tree = exact_keys(
        lifecycle["tree_manifest"],
        {"algorithm", "format", "sha256"},
        f"{asset_key} tree manifest",
    )
    require(
        tree["algorithm"] == "sha256" and tree["format"] == MANIFEST_FORMAT,
        f"{asset_key} tree-manifest contract drifted",
    )
    exact_hex(tree["sha256"], 64, f"{asset_key} tree-manifest SHA-256")
    probes = exact_keys(
        lifecycle["probes"],
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
        f"{asset_key} probes",
    )
    require(
        probes["version"] == EXPECTED_VERSION, f"{asset_key} Lean version pin drifted"
    )
    require(probes["commit"] == EXPECTED_COMMIT, f"{asset_key} Lean commit pin drifted")
    require(probes["build"] == "Release", f"{asset_key} Lean build pin drifted")
    require(
        type(probes["leanchecker_absent_module_exit"]) is int
        and probes["leanchecker_absent_module_exit"] == 1,
        f"{asset_key} leanchecker exit pin must be integer 1",
    )
    for key in (
        "lake_stdout",
        "lean_platform",
        "lean_stdout",
        "leanchecker_absent_module_stderr",
    ):
        require(
            isinstance(probes[key], str), f"{asset_key} probe {key} must be a string"
        )
    identity = parse_lean_version(
        ProcessResult(0, str(probes["lean_stdout"]).encode("ascii"), b"")
    )
    require(
        identity.version == probes["version"]
        and identity.commit == probes["commit"]
        and identity.build == probes["build"]
        and identity.platform == probes["lean_platform"]
        and identity.platform == EXPECTED_DARWIN_PLATFORM,
        f"{asset_key} Lean stdout/scalar/platform coupling drifted",
    )
    validate_lake_version(
        ProcessResult(0, str(probes["lake_stdout"]).encode("ascii"), b"")
    )
    validate_leanchecker_probe(
        ProcessResult(
            int(probes["leanchecker_absent_module_exit"]),
            b"",
            str(probes["leanchecker_absent_module_stderr"]).encode("ascii"),
        )
    )
    validate_reviewed_pin_source(lifecycle["reviewed_pin_source"], legacy_authority)
    legacy_tree_pin = {
        key: legacy_authority.tree_manifest[key]
        for key in ("algorithm", "format", "sha256")
    }
    require(
        inventory == legacy_authority.inventory
        and leaves == legacy_authority.leaves
        and tree == legacy_tree_pin
        and probes == legacy_authority.probes,
        "Darwin reviewed pins differ from the published observation",
    )
    return lifecycle


def validate_asset(
    value: object,
    expected: dict[str, object],
    limits: dict[str, object],
    legacy_authority: LegacyV4Authority | None,
) -> dict[str, object]:
    asset = exact_keys(
        value,
        {"archive", "custody_lifecycle", "github_asset", "host", "key"},
        "asset",
    )
    key = asset["key"]
    require(
        isinstance(key, str) and key in EXPECTED_ASSET_IDENTITIES,
        "asset key is unsupported",
    )
    require(
        expected == EXPECTED_ASSET_IDENTITIES[key],
        f"internal expected asset selection drifted: {key}",
    )
    archive = exact_keys(
        asset["archive"], {"format", "root", "sha256", "size"}, f"{key} archive"
    )
    require(archive["format"] == "tar.zst", f"{key} archive format drifted")
    require(archive["root"] == expected["root"], f"{key} archive root drifted")
    require(
        archive["size"] == expected["size"], f"{key} advertised archive size drifted"
    )
    require(
        archive["sha256"] == expected["sha256"],
        f"{key} advertised archive SHA-256 drifted",
    )
    github = exact_keys(
        asset["github_asset"],
        {
            "browser_download_url",
            "content_type",
            "created_at",
            "digest",
            "id",
            "name",
            "size",
            "state",
            "updated_at",
        },
        f"{key} GitHub asset",
    )
    require(github["id"] == expected["id"], f"{key} GitHub asset id drifted")
    require(github["name"] == expected["name"], f"{key} GitHub asset name drifted")
    require(
        github["size"] == expected["size"],
        f"{key} GitHub asset size disagrees with archive pin",
    )
    require(
        github["digest"] == f"sha256:{expected['sha256']}",
        f"{key} GitHub digest disagrees with archive pin",
    )
    require(
        github["content_type"] == "application/octet-stream"
        and github["state"] == "uploaded",
        f"{key} GitHub asset publication state drifted",
    )
    expected_url = f"https://github.com/leanprover/lean4/releases/download/v4.32.2/{expected['name']}"
    require(
        github["browser_download_url"] == expected_url, f"{key} download URL drifted"
    )
    require(
        github["created_at"] == expected["created_at"]
        and github["updated_at"] == expected["updated_at"],
        f"{key} provider timestamps drifted",
    )
    host = exact_keys(asset["host"], {"machines", "system"}, f"{key} host")
    require(
        host == {"system": expected["system"], "machines": expected["machines"]},
        f"{key} host identity drifted",
    )
    validate_custody_lifecycle(
        asset["custody_lifecycle"], key, expected, limits, legacy_authority
    )
    return asset


def validate_metadata(
    metadata: dict[str, object],
    legacy_authority: LegacyV4Authority | None = None,
) -> dict[str, dict[str, object]]:
    exact_keys(
        metadata,
        {
            "assets",
            "authentication_boundary",
            "checker_binding",
            "credit_boundary",
            "historical_nontransferable_observations",
            "limits",
            "provider_observation_provenance",
            "schema",
            "subject",
        },
        "metadata",
    )
    require(metadata["schema"] == METADATA_SCHEMA, "metadata schema drifted")
    limits = validate_exact_typed_object(
        metadata["limits"], EXPECTED_LIMITS, "resource-limit policy drifted"
    )
    require(
        limits["nested_kernel_inner_replay_timeout_seconds"]
        == NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS
        and limits["nested_kernel_replay_count"] == NESTED_KERNEL_REPLAY_COUNT
        and limits["nested_kernel_non_replay_lean_child_timeout_seconds"]
        == NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS
        and limits["nested_kernel_non_replay_lean_child_count"]
        == NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT
        and limits["nested_kernel_identity_child_timeout_seconds"]
        == NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS
        and limits["nested_kernel_identity_child_count"]
        == NESTED_KERNEL_IDENTITY_CHILD_COUNT
        and limits["nested_kernel_orchestration_headroom_seconds"]
        == NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS
        and limits["nested_kernel_non_replay_margin_seconds"]
        == NESTED_KERNEL_NON_REPLAY_MARGIN_SECONDS
        and limits["nested_kernel_required_outer_timeout_seconds"]
        == NESTED_KERNEL_REQUIRED_OUTER_TIMEOUT_SECONDS
        and limits["nested_kernel_regression_timeout_seconds"]
        == NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS
        and limits["process_group_term_grace_milliseconds"]
        == PROCESS_GROUP_TERM_GRACE_MILLISECONDS
        and limits["process_group_kill_grace_milliseconds"]
        == PROCESS_GROUP_KILL_GRACE_MILLISECONDS
        and limits["process_group_poll_interval_milliseconds"]
        == PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS
        and limits["direct_child_reap_timeout_milliseconds"]
        == DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS
        and NESTED_KERNEL_REQUIRED_OUTER_TIMEOUT_SECONDS
        == NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS * NESTED_KERNEL_REPLAY_COUNT
        + NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS
        * NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT
        + NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS
        * NESTED_KERNEL_IDENTITY_CHILD_COUNT
        + NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS
        and NESTED_KERNEL_NON_REPLAY_MARGIN_SECONDS
        == NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS
        * NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT
        + NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS
        * NESTED_KERNEL_IDENTITY_CHILD_COUNT
        + NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS
        and NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS
        >= NESTED_KERNEL_REQUIRED_OUTER_TIMEOUT_SECONDS,
        "nested kernel timing policy is contradictory",
    )
    validate_subject(metadata)
    validate_exact_typed_object(
        metadata["provider_observation_provenance"],
        EXPECTED_PROVIDER_OBSERVATION_PROVENANCE,
        "provider observation provenance drifted",
    )
    boundary = exact_keys(
        metadata["authentication_boundary"],
        {"status", "statements"},
        "authentication boundary",
    )
    require(boundary["status"] == "none", "authentication boundary must remain none")
    statements = boundary["statements"]
    require(
        isinstance(statements, list)
        and len(statements) == 5
        and all(isinstance(item, str) and item for item in statements),
        "authentication/nonclaim inventory drifted",
    )
    require(
        sha256_bytes(canonical_json_bytes(boundary))
        == EXPECTED_AUTHENTICATION_BOUNDARY_SHA256,
        "authentication boundary exact semantics drifted",
    )
    credit_boundary = exact_keys(
        metadata["credit_boundary"],
        {
            "active_scientific_lean_project",
            "archive_custody",
            "downstream_authorization",
            "kernel_soundness",
            "nanoda_or_external_checker",
            "pdf_transfer",
            "pid_estimator_population_transfer",
            "publisher_provider_authentication",
            "real_nested_regression",
            "release_authorization",
            "reproducible_build",
            "rust_binary64_transfer",
            "same_run_qualification",
            "source_to_binary_provenance",
            "static_schema_validation",
            "theorem_truth",
        },
        "metadata credit boundary",
    )
    require(
        sha256_bytes(canonical_json_bytes(credit_boundary))
        == EXPECTED_CREDIT_BOUNDARY_SHA256,
        "metadata credit boundary exact semantics drifted",
    )
    validate_historical_nontransferable_observations(
        metadata["historical_nontransferable_observations"]
    )
    binding = exact_keys(
        metadata["checker_binding"],
        {
            "checker_bytes",
            "checker_path",
            "checker_sha256",
            "nested_checker_binding",
            "policy",
            "projection_omits",
        },
        "checker binding",
    )
    require(
        binding["checker_path"] == "scripts/check-lean-toolchain-custody.py",
        "checker binding path drifted",
    )
    require(
        binding["projection_omits"]
        == [
            "checker_binding.checker_bytes",
            "checker_binding.checker_sha256",
            "checker_binding.nested_checker_binding.bytes",
            "checker_binding.nested_checker_binding.sha256",
        ],
        "acyclic projection omission set drifted",
    )
    require(
        type(binding["checker_bytes"]) is int and binding["checker_bytes"] > 0,
        "checker byte-length binding is absent",
    )
    exact_hex(binding["checker_sha256"], 64, "checker source SHA-256")
    validate_nested_checker_binding(binding["nested_checker_binding"])
    require(
        binding["policy"] == EXPECTED_CHECKER_POLICY,
        "acyclic source-binding boundary drifted",
    )
    assets_value = metadata["assets"]
    require(
        isinstance(assets_value, list) and len(assets_value) == 2,
        "asset inventory must contain exactly Darwin and Linux",
    )
    assets: dict[str, dict[str, object]] = {}
    expected_order = ["darwin-aarch64", "linux-x86_64"]
    for index, item in enumerate(assets_value):
        expected = EXPECTED_ASSET_IDENTITIES[expected_order[index]]
        asset = validate_asset(item, expected, limits, legacy_authority)
        key = asset["key"]
        require(key == expected_order[index], "asset order drifted")
        require(key not in assets, f"duplicate asset key: {key}")
        assets[key] = asset
    return assets


def load_policy() -> tuple[
    StableSnapshot,
    StableSnapshot,
    StableSnapshot,
    StableSnapshot,
    StableSnapshot,
    StableSnapshot,
    dict[str, object],
    dict[str, dict[str, object]],
]:
    metadata_snapshot = snapshot_repo_file(METADATA_PATH, "toolchain release metadata")
    metadata = parse_json_object(metadata_snapshot.data, "toolchain release metadata")
    require(
        metadata_snapshot.data == canonical_metadata_bytes(metadata),
        "toolchain release metadata is not canonical sorted JSON",
    )
    legacy_raw_snapshot = snapshot_repo_file(
        LEGACY_OBSERVATION_RAW_PATH, "published legacy-v4 observation raw evidence"
    )
    legacy_receipt_snapshot = snapshot_repo_file(
        LEGACY_OBSERVATION_RECEIPT_PATH,
        "published legacy-v4 observation receipt evidence",
    )
    legacy_authority = load_frozen_legacy_v4_authority(
        legacy_raw_snapshot, legacy_receipt_snapshot
    )
    assets = validate_metadata(metadata, legacy_authority)
    policy_digest = metadata_policy_sha256(metadata)
    require(
        policy_digest == EXPECTED_METADATA_POLICY_SHA256,
        "metadata policy projection SHA-256 drifted",
    )
    source_snapshot = snapshot_repo_file(
        SCRIPT_PATH, "toolchain custody checker source"
    )
    binding = metadata["checker_binding"]
    require(
        source_snapshot.identity.size == binding["checker_bytes"],
        "checker source byte-length binding drifted",
    )
    require(
        source_snapshot.sha256 == binding["checker_sha256"],
        "checker source SHA-256 binding drifted",
    )
    nested_checker_snapshot = snapshot_bound_nested_checker(metadata)
    historical_receipt_snapshot = snapshot_bound_historical_receipt(metadata)
    return (
        source_snapshot,
        metadata_snapshot,
        nested_checker_snapshot,
        historical_receipt_snapshot,
        legacy_raw_snapshot,
        legacy_receipt_snapshot,
        metadata,
        assets,
    )


def external_file_digest(path: Path, role: str) -> ExternalDigestSnapshot:
    require(path.is_absolute(), f"{role} path must be absolute")
    absolute = Path(os.path.abspath(os.fspath(path)))
    before = lstat_regular(absolute, role)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(absolute, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = identity_from_stat(os.fstat(stream.fileno()))
            require(opened == before, f"{role} pathname changed before open")
            digest = hashlib.sha256()
            total = 0
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                total += len(block)
        after = lstat_regular(absolute, role)
    except OSError as error:
        raise CustodyError(f"cannot hash {role} {absolute}: {error}") from error
    require(before == after, f"{role} identity changed during hash")
    require(total == before.size, f"{role} size changed during hash")
    return ExternalDigestSnapshot(absolute, digest.hexdigest(), before)


def require_external_unchanged(
    before: ExternalDigestSnapshot, after: ExternalDigestSnapshot, role: str
) -> None:
    require(after.path == before.path, f"{role} path changed")
    require(
        after.identity == before.identity,
        f"{role} identity changed across qualification",
    )
    require(
        after.sha256 == before.sha256, f"{role} SHA-256 changed across qualification"
    )


def snapshot_executable(path: Path, role: str) -> ExecutableSnapshot:
    require(path.is_absolute(), f"{role} launch path must be absolute")
    launch_path = Path(os.path.abspath(os.fspath(path)))
    try:
        launch_stat = launch_path.lstat()
        require(
            stat.S_ISREG(launch_stat.st_mode) or stat.S_ISLNK(launch_stat.st_mode),
            f"{role} launch route is neither a file nor symlink",
        )
        launch_target = (
            os.readlink(launch_path) if stat.S_ISLNK(launch_stat.st_mode) else None
        )
        canonical = launch_path.resolve(strict=True)
        before = lstat_regular(canonical, f"{role} canonical leaf")
        require(before.mode & 0o111 != 0, f"{role} canonical leaf is not executable")
        first = canonical.read_bytes()
        middle = lstat_regular(canonical, f"{role} canonical leaf")
        second = canonical.read_bytes()
        after = lstat_regular(canonical, f"{role} canonical leaf")
    except OSError as error:
        raise CustodyError(f"cannot snapshot {role} executable: {error}") from error
    require(
        before == middle == after,
        f"{role} executable identity changed during double read",
    )
    require(
        first == second and len(first) == before.size,
        f"{role} executable bytes changed during double read",
    )
    return ExecutableSnapshot(
        launch_path=launch_path,
        launch_identity=identity_from_stat(launch_stat),
        launch_target=launch_target,
        canonical_path=canonical,
        canonical_identity=before,
        data=first,
        sha256=sha256_bytes(first),
    )


def require_executable_unchanged(before: ExecutableSnapshot, role: str) -> None:
    after = snapshot_executable(before.launch_path, role)
    require(
        after.launch_identity == before.launch_identity
        and after.launch_target == before.launch_target,
        f"{role} launch route changed",
    )
    require(
        after.canonical_path == before.canonical_path, f"{role} canonical path changed"
    )
    require(
        after.canonical_identity == before.canonical_identity
        and after.data == before.data,
        f"{role} canonical leaf changed",
    )


def select_zstd(explicit: Path | None) -> Path:
    if explicit is not None:
        require(explicit.is_absolute(), "--zstd must be an absolute path")
        return Path(os.path.abspath(os.fspath(explicit)))
    candidates = (
        Path("/usr/bin/zstd"),
        Path("/opt/homebrew/bin/zstd"),
        Path("/usr/local/bin/zstd"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise CustodyError(
        "no zstd decoder found at an enumerated absolute route; pass --zstd"
    )


class BoundedReader(io.RawIOBase):
    def __init__(self, source: BinaryIO, limit: int):
        self.source = source
        self.limit = limit
        self.count = 0
        self.digest = hashlib.sha256()

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        block = self.source.read(size)
        self.count += len(block)
        self.digest.update(block)
        require(
            self.count <= self.limit,
            "decompressed archive stream exceeds its byte ceiling",
        )
        return block

    @property
    def sha256(self) -> str:
        return self.digest.hexdigest()

    def readinto(self, target: bytearray | memoryview) -> int:
        block = self.read(len(target))
        length = len(block)
        target[:length] = block
        return length

    def drain(self) -> None:
        while self.read(1024 * 1024):
            pass


@contextmanager
def stream_deadline(seconds: int) -> Iterator[None]:
    require(
        os.name == "posix" and hasattr(signal, "setitimer"),
        "archive streaming requires POSIX interval-timer custody",
    )
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def expired(_signum: int, _frame: object) -> None:
        raise CustodyError(f"archive stream exceeded {seconds} seconds")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def process_group_exists(process_group: int) -> bool:
    """Probe one captured non-self POSIX group without signalling its members."""

    require(os.name == "posix", "process-group existence probes require POSIX")
    require(
        type(process_group) is int and process_group > 1,
        "captured process-group number is invalid",
    )
    require(
        process_group != os.getpgrp(),
        "refusing to inspect the custody checker's own process group as a child group",
    )
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # EPERM still means the captured PGID has at least one member.  Poll it as
        # present and accept only bounded disappearance, including short-lived
        # exited orphan/zombie groups on supported POSIX hosts.
        return True
    return True


def wait_for_process_group_absence(
    process_group: int,
    seconds: float,
    direct_child: subprocess.Popen[bytes] | None = None,
) -> bool:
    """Boundedly observe group absence; non-child descendants cannot be reaped here."""

    require(seconds >= 0.0, "process-group absence bound is negative")
    deadline = time.monotonic() + seconds
    if direct_child is not None:
        direct_child.poll()
    while process_group_exists(process_group):
        if direct_child is not None:
            direct_child.poll()
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            return False
        time.sleep(min(PROCESS_GROUP_POLL_INTERVAL_SECONDS, remaining))
    return True


def cleanup_isolated_process_group(process: subprocess.Popen[bytes]) -> None:
    """TERM/KILL the captured non-self group after every isolated child outcome.

    The direct child starts a new session, so its PID is the initial PGID before
    ``exec``.  Retaining that number addresses same-group descendants even after
    the leader exits.  The probe/signal sequence is not atomic; PGID reuse and
    descendants that change process group or session remain explicit limits.
    """

    require(os.name == "posix", "isolated process-group cleanup requires POSIX")
    process_group = process.pid
    require(
        process_group != os.getpgrp(),
        "refusing to signal the custody checker's own process group",
    )
    for selected_signal, grace in (
        (signal.SIGTERM, PROCESS_GROUP_TERM_GRACE_SECONDS),
        (signal.SIGKILL, PROCESS_GROUP_KILL_GRACE_SECONDS),
    ):
        if not process_group_exists(process_group):
            break
        try:
            os.killpg(process_group, selected_signal)
        except ProcessLookupError:
            break
        except PermissionError as error:
            if wait_for_process_group_absence(process_group, grace, process):
                break
            if selected_signal == signal.SIGKILL:
                raise CustodyError(
                    "captured child process group remained permission-denied after "
                    "bounded TERM/KILL cleanup"
                ) from error
            continue
        if wait_for_process_group_absence(process_group, grace, process):
            break
    process.poll()
    require(
        not process_group_exists(process_group),
        "captured child process group remained after bounded TERM/KILL cleanup",
    )
    try:
        process.wait(timeout=DIRECT_CHILD_REAP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise CustodyError(
            "isolated direct child was not reaped after bounded group cleanup"
        ) from error


def consume_zstd_archive(
    archive: Path,
    zstd: ExecutableSnapshot,
    limits: dict[str, object],
    consumer: Callable[[BinaryIO], T],
) -> tuple[T, int]:
    command = [os.fspath(zstd.launch_path), "-q", "-d", "-c", "--", os.fspath(archive)]
    environment = {"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"}
    with tempfile.TemporaryFile() as errors:
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=errors,
                env=environment,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as error:
            raise CustodyError(f"zstd decoder could not start: {error}") from error
        require(process.stdout is not None, "zstd stdout pipe was not created")
        reader = BoundedReader(
            process.stdout, int(limits["decompressed_stream_bytes_max"])
        )
        try:
            with stream_deadline(int(limits["stream_timeout_seconds"])):
                result = consumer(reader)
                reader.drain()
            process.stdout.close()
            returncode = process.wait(timeout=10)
        except BaseException as operation_error:
            try:
                process.stdout.close()
            except OSError:
                pass
            try:
                cleanup_isolated_process_group(process)
            except BaseException as cleanup_error:
                raise cleanup_error from operation_error
            raise
        cleanup_isolated_process_group(process)
        errors.flush()
        error_size = errors.tell()
        require(
            error_size <= int(limits["child_output_bytes_max"]),
            "zstd stderr exceeds its byte ceiling",
        )
        errors.seek(0)
        stderr = errors.read()
    if returncode != 0 or stderr != b"":
        raise CustodyError(
            fixed_process_stream_rejection_diagnostic(
                "zstd decoder",
                returncode,
                reader.count,
                reader.sha256,
                stderr,
            )
        )
    return result, reader.count


def normalize_member_name(name: str, root: str, limits: dict[str, object]) -> str:
    require(isinstance(name, str), "tar member name is not text")
    require(
        name != "" and not name.startswith("/"),
        f"tar member path is empty or absolute: {name!r}",
    )
    require(
        "\\" not in name and "\x00" not in name and ":" not in name,
        f"tar member path has a forbidden separator or drive marker: {name!r}",
    )
    require(
        unicodedata.normalize("NFC", name) == name,
        f"tar member path is not NFC-normalized: {name!r}",
    )
    try:
        encoded = name.encode("ascii", errors="strict")
    except UnicodeError as error:
        raise CustodyError(f"tar member path is not ASCII: {name!r}") from error
    require(
        len(encoded) <= int(limits["path_bytes_max"]),
        f"tar member path exceeds its byte ceiling: {name!r}",
    )
    components = name.split("/")
    require(
        len(components) <= int(limits["path_depth_max"]),
        f"tar member path exceeds its depth ceiling: {name!r}",
    )
    require(
        all(component not in {"", ".", ".."} for component in components),
        f"tar member path is non-normal or traversing: {name!r}",
    )
    require(
        all(
            ALLOWED_COMPONENT.fullmatch(component) is not None
            for component in components
        ),
        f"tar member path contains an unsupported component: {name!r}",
    )
    require(
        components[0] == root, f"tar member has an unexpected archive root: {name!r}"
    )
    normalized = "/".join(components)
    require(
        normalized == name, f"tar member path normalization changed bytes: {name!r}"
    )
    return normalized


def member_record(
    member: tarfile.TarInfo, root: str, limits: dict[str, object]
) -> MemberRecord:
    path = normalize_member_name(member.name, root, limits)
    require(not member.pax_headers, f"tar member uses unsupported PAX metadata: {path}")
    require(not member.sparse, f"tar member uses unsupported sparse extents: {path}")
    require(member.linkname == "", f"tar member has an unexpected link target: {path}")
    mode = stat.S_IMODE(member.mode)
    if member.isdir():
        require(member.size == 0, f"tar directory has a nonzero payload: {path}")
        require(mode == 0o755, f"tar directory mode is not 0755: {path}")
        return MemberRecord(path, "directory", "0755", 0)
    if member.isreg():
        require(member.size >= 0, f"tar file has a negative size: {path}")
        require(
            member.size <= int(limits["file_bytes_max"]),
            f"tar file exceeds its byte ceiling: {path}",
        )
        require(
            mode in {0o644, 0o755}, f"tar file mode is neither 0644 nor 0755: {path}"
        )
        return MemberRecord(path, "file", f"{mode:04o}", member.size)
    if member.issym() or member.islnk():
        raise CustodyError(f"tar links are forbidden: {path}")
    if member.ischr() or member.isblk() or member.isfifo():
        raise CustodyError(f"tar device/FIFO member is forbidden: {path}")
    raise CustodyError(
        f"tar member type is unsupported (including sockets): {path}; type={member.type!r}"
    )


def inventory_from_records(
    records: list[MemberRecord], limits: dict[str, object]
) -> dict[str, int]:
    require(records, "tar archive has no members")
    require(
        len(records) <= int(limits["members_max"]),
        "tar member count exceeds its ceiling",
    )
    paths: dict[str, MemberRecord] = {}
    portable_paths: set[str] = set()
    for record in records:
        require(
            record.path not in paths, f"duplicate normalized tar member: {record.path}"
        )
        portable = unicodedata.normalize("NFC", record.path).casefold()
        require(
            portable not in portable_paths,
            f"case-folding tar path collision: {record.path}",
        )
        paths[record.path] = record
        portable_paths.add(portable)
    root = records[0].path.split("/")[0]
    require(
        records[0] == MemberRecord(root, "directory", "0755", 0),
        "first tar member is not the exact root directory",
    )
    require(
        set(path.split("/")[0] for path in paths) == {root},
        "tar archive has multiple roots",
    )
    for path, record in paths.items():
        components = path.split("/")
        for depth in range(1, len(components)):
            parent = "/".join(components[:depth])
            require(parent in paths, f"tar member parent is absent: {path}")
            require(
                paths[parent].kind == "directory",
                f"tar file is used as a parent: {path}",
            )
        if record.kind == "directory":
            require(record.size == 0, f"directory record retained a payload: {path}")
    directories = sum(record.kind == "directory" for record in records)
    regular_files = sum(record.kind == "file" for record in records)
    regular_bytes = sum(record.size for record in records if record.kind == "file")
    max_file = max(
        (record.size for record in records if record.kind == "file"), default=0
    )
    max_path = max(len(record.path.encode("ascii")) for record in records)
    max_depth = max(len(record.path.split("/")) for record in records)
    require(
        directories <= int(limits["directories_max"]),
        "tar directory count exceeds its ceiling",
    )
    require(
        regular_files <= int(limits["regular_files_max"]),
        "tar regular-file count exceeds its ceiling",
    )
    require(
        regular_bytes <= int(limits["regular_file_bytes_max"]),
        "tar regular-file bytes exceed their ceiling",
    )
    return {
        "directories": directories,
        "max_depth": max_depth,
        "max_file_bytes": max_file,
        "max_path_bytes": max_path,
        "members": len(records),
        "regular_file_bytes": regular_bytes,
        "regular_files": regular_files,
    }


def preflight_tar_stream(
    stream: BinaryIO, asset: dict[str, object], limits: dict[str, object]
) -> tuple[list[MemberRecord], dict[str, int]]:
    archive = asset["archive"]
    root = archive["root"]
    require(isinstance(root, str), "archive root metadata is malformed")
    records: list[MemberRecord] = []
    try:
        with tarfile.open(fileobj=stream, mode="r|") as payload:
            for member in payload:
                records.append(member_record(member, root, limits))
                require(
                    len(records) <= int(limits["members_max"]),
                    "tar member count exceeds its ceiling",
                )
    except (tarfile.TarError, EOFError) as error:
        raise CustodyError(
            f"tar preflight could not parse the complete archive: {error}"
        ) from error
    return records, inventory_from_records(records, limits)


def target_for(destination: Path, normalized_path: str) -> Path:
    return destination.joinpath(*normalized_path.split("/"))


def extract_tar_stream(
    stream: BinaryIO,
    destination: Path,
    asset: dict[str, object],
    limits: dict[str, object],
    expected_records: list[MemberRecord],
) -> list[TreeEntry]:
    require(destination.is_absolute(), "extraction destination must be absolute")
    try:
        destination_stat = destination.lstat()
        initial_entries = list(destination.iterdir())
    except OSError as error:
        raise CustodyError(f"cannot inspect extraction destination: {error}") from error
    require(
        stat.S_ISDIR(destination_stat.st_mode) and not destination.is_symlink(),
        "extraction destination is not a real directory",
    )
    require(
        stat.S_IMODE(destination_stat.st_mode) == 0o700,
        "extraction destination mode must be 0700",
    )
    require(not initial_entries, "extraction destination is not empty")
    directories = sorted(
        (record for record in expected_records if record.kind == "directory"),
        key=lambda record: (len(record.path.split("/")), record.path.encode("ascii")),
    )
    for record in directories:
        target = target_for(destination, record.path)
        create_private_directory(
            target, f"preflighted extraction directory {record.path}"
        )

    extracted: list[TreeEntry] = []
    root = asset["archive"]["root"]
    index = 0
    try:
        with tarfile.open(fileobj=stream, mode="r|") as payload:
            for member in payload:
                require(
                    index < len(expected_records),
                    "extraction stream gained an unexpected tar member",
                )
                observed = member_record(member, root, limits)
                expected = expected_records[index]
                require(
                    observed == expected,
                    f"tar member changed between preflight and extraction at index {index}",
                )
                index += 1
                if observed.kind == "directory":
                    extracted.append(
                        TreeEntry(observed.path, "directory", observed.mode, None, None)
                    )
                    continue
                target = target_for(destination, observed.path)
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                try:
                    descriptor = os.open(target, flags, int(observed.mode, 8))
                    source = payload.extractfile(member)
                    require(
                        source is not None,
                        f"tar file payload is absent: {observed.path}",
                    )
                    digest = hashlib.sha256()
                    total = 0
                    with os.fdopen(descriptor, "wb") as output:
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            output.write(block)
                            digest.update(block)
                            total += len(block)
                            require(
                                total <= observed.size,
                                f"tar file exceeded its declared size: {observed.path}",
                            )
                        output.flush()
                        os.fchmod(output.fileno(), int(observed.mode, 8))
                except OSError as error:
                    raise CustodyError(
                        f"cannot extract regular file {observed.path}: {error}"
                    ) from error
                require(
                    total == observed.size, f"tar file was truncated: {observed.path}"
                )
                extracted.append(
                    TreeEntry(
                        observed.path, "file", observed.mode, total, digest.hexdigest()
                    )
                )
    except (tarfile.TarError, EOFError) as error:
        raise CustodyError(
            f"tar extraction could not parse the complete archive: {error}"
        ) from error
    require(
        index == len(expected_records),
        "extraction stream lost a preflighted tar member",
    )
    for record in sorted(
        directories, key=lambda item: len(item.path.split("/")), reverse=True
    ):
        try:
            os.chmod(
                target_for(destination, record.path),
                int(record.mode, 8),
                follow_symlinks=False,
            )
        except OSError as error:
            raise CustodyError(
                f"cannot finalize directory mode {record.path}: {error}"
            ) from error
    return extracted


def hash_tree_file(path: Path, role: str) -> tuple[int, str, FileIdentity]:
    before = lstat_regular(path, role)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = identity_from_stat(os.fstat(stream.fileno()))
            require(opened == before, f"{role} path changed before open")
            digest = hashlib.sha256()
            total = 0
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                total += len(block)
        after = lstat_regular(path, role)
    except OSError as error:
        raise CustodyError(f"cannot hash {role}: {error}") from error
    require(before == after and total == before.size, f"{role} changed during hash")
    return total, digest.hexdigest(), before


def scan_extracted_tree(
    destination: Path, limits: dict[str, object]
) -> list[TreeEntry]:
    entries: list[TreeEntry] = []

    def visit(directory: Path) -> None:
        try:
            children = list(os.scandir(directory))
        except OSError as error:
            raise CustodyError(
                f"cannot enumerate extracted directory {directory}: {error}"
            ) from error
        for child in children:
            path = Path(child.path)
            relative = path.relative_to(destination).as_posix()
            normalize_member_name(relative, relative.split("/")[0], limits)
            try:
                observed = child.stat(follow_symlinks=False)
            except OSError as error:
                raise CustodyError(
                    f"cannot lstat extracted entry {relative}: {error}"
                ) from error
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISDIR(observed.st_mode):
                require(mode == 0o755, f"extracted directory mode drifted: {relative}")
                entries.append(TreeEntry(relative, "directory", "0755", None, None))
                visit(path)
            elif stat.S_ISREG(observed.st_mode):
                require(
                    observed.st_nlink == 1,
                    f"extracted file has multiple hard links: {relative}",
                )
                require(
                    mode in {0o644, 0o755}, f"extracted file mode drifted: {relative}"
                )
                size, digest, stable = hash_tree_file(
                    path, f"extracted file {relative}"
                )
                require(
                    stable == identity_from_stat(observed),
                    f"extracted file changed after directory enumeration: {relative}",
                )
                entries.append(TreeEntry(relative, "file", f"{mode:04o}", size, digest))
            else:
                raise CustodyError(
                    f"extracted tree contains a link or special node: {relative}"
                )

    visit(destination)
    entries.sort(key=lambda entry: entry.path.encode("ascii"))
    require(
        len(entries) <= int(limits["members_max"]),
        "extracted tree entry count exceeds its ceiling",
    )
    return entries


def tree_manifest_sha256(entries: list[TreeEntry]) -> str:
    digest = hashlib.sha256()
    digest.update(MANIFEST_HEADER)
    previous: bytes | None = None
    for entry in entries:
        encoded_path = entry.path.encode("ascii")
        require(
            previous is None or encoded_path > previous,
            "tree manifest paths are not strictly byte-sorted",
        )
        previous = encoded_path
        digest.update(canonical_json_bytes(entry.canonical_row()) + b"\n")
    return digest.hexdigest()


def entries_from_records(
    records: list[MemberRecord], extracted: list[TreeEntry]
) -> list[TreeEntry]:
    require(
        len(records) == len(extracted), "extracted entry count disagrees with preflight"
    )
    by_path: dict[str, TreeEntry] = {}
    for record, entry in zip(records, extracted, strict=True):
        require(
            record.path == entry.path
            and record.kind == entry.kind
            and record.mode == entry.mode,
            f"extracted entry identity disagrees with preflight: {record.path}",
        )
        if record.kind == "file":
            require(
                entry.size == record.size and entry.sha256 is not None,
                f"extracted file digest record is incomplete: {record.path}",
            )
        by_path[entry.path] = entry
    return sorted(by_path.values(), key=lambda entry: entry.path.encode("ascii"))


def require_same_tree(
    first: list[TreeEntry], second: list[TreeEntry], role: str
) -> None:
    require(first == second, f"extracted tree changed {role}")


def leaf_facts(entries: list[TreeEntry], root: str) -> dict[str, dict[str, object]]:
    by_path = {entry.path: entry for entry in entries}
    result: dict[str, dict[str, object]] = {}
    for role in ("lean", "lake", "leanchecker"):
        relative = f"bin/{role}"
        full = f"{root}/{relative}"
        require(full in by_path, f"required executable leaf is absent: {full}")
        entry = by_path[full]
        require(
            entry.kind == "file"
            and entry.mode == "0755"
            and entry.size is not None
            and entry.sha256 is not None,
            f"required executable leaf is malformed: {full}",
        )
        result[role] = {
            "mode": entry.mode,
            "path": relative,
            "sha256": entry.sha256,
            "size": entry.size,
        }
    return result


def build_child_environment(
    tool_root: Path, home: Path, temporary: Path
) -> dict[str, str]:
    environment = {
        "HOME": os.fspath(home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.fspath(tool_root / "bin")
        + os.pathsep
        + "/usr/bin"
        + os.pathsep
        + "/bin",
        "TMPDIR": os.fspath(temporary),
    }
    validate_child_environment(environment, tool_root)
    return environment


def resolve_from_path(name: str, path_value: str) -> Path | None:
    for directory in path_value.split(os.pathsep):
        candidate = Path(directory) / name
        try:
            observed = candidate.lstat()
        except OSError:
            continue
        if (
            stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode)
        ) and os.access(candidate, os.X_OK):
            return Path(os.path.abspath(os.fspath(candidate)))
    return None


def validate_child_environment(environment: dict[str, str], tool_root: Path) -> None:
    require(
        set(environment) == {"HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"},
        "child environment whitelist drifted",
    )
    require(
        environment["LANG"] == "C" and environment["LC_ALL"] == "C",
        "child locale is not fixed",
    )
    forbidden = [
        key
        for key in environment
        if key == "LEAN_SYSROOT"
        or key.startswith(("LEAN_", "LAKE_", "ELAN_", "LD_", "DYLD_", "PYTHON"))
    ]
    require(
        not forbidden,
        f"Lean/Elan/loader/Python substitution environment remains: {forbidden}",
    )
    expected_first = os.fspath(tool_root / "bin")
    require(
        environment["PATH"].split(os.pathsep) == [expected_first, "/usr/bin", "/bin"],
        "child PATH precedence drifted",
    )
    for role in ("lean", "lake", "leanchecker"):
        selected = resolve_from_path(role, environment["PATH"])
        require(
            selected == tool_root / "bin" / role,
            f"child PATH selects a substituted {role} executable",
        )


def run_bounded_process(
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    limits: dict[str, object],
    *,
    timeout_seconds: int | None = None,
) -> ProcessResult:
    require(
        command and Path(command[0]).is_absolute(),
        "child executable route is not absolute",
    )
    timeout = (
        int(limits["process_timeout_seconds"])
        if timeout_seconds is None
        else timeout_seconds
    )
    require(timeout > 0, "toolchain child timeout must be positive")
    ceiling = int(limits["child_output_bytes_max"])
    with (
        tempfile.TemporaryFile() as stdout_file,
        tempfile.TemporaryFile() as stderr_file,
    ):
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as error:
            raise CustodyError(f"toolchain child could not start: {error}") from error
        timed_out: subprocess.TimeoutExpired | None = None
        try:
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as error:
                timed_out = error
                returncode = (
                    process.returncode if process.returncode is not None else -1
                )
        except BaseException as operation_error:
            try:
                cleanup_isolated_process_group(process)
            except BaseException as cleanup_error:
                raise cleanup_error from operation_error
            raise
        cleanup_isolated_process_group(process)
        if timed_out is not None:
            raise CustodyError(
                f"toolchain child exceeded {timeout} seconds"
            ) from timed_out
        stdout_file.flush()
        stderr_file.flush()
        stdout_size = stdout_file.tell()
        stderr_size = stderr_file.tell()
        require(
            stdout_size <= ceiling, "toolchain child stdout exceeds its byte ceiling"
        )
        require(
            stderr_size <= ceiling, "toolchain child stderr exceeds its byte ceiling"
        )
        stdout_file.seek(0)
        stderr_file.seek(0)
        return ProcessResult(returncode, stdout_file.read(), stderr_file.read())


def fixed_process_stream_rejection_diagnostic(
    stage: str,
    exit_status: int,
    stdout_bytes: int,
    stdout_sha256: str,
    stderr: bytes,
) -> str:
    """Render a fixed, ASCII, digest-only diagnostic for bounded process streams."""

    require(
        stage
        in {
            "zstd decoder",
            "Lean version probe",
            "Lake version probe",
            "LeanChecker absent-module probe",
        },
        "process rejection stage is not fixed",
    )
    diagnostic = (
        f"{stage} rejected; exit_status={exit_status}; "
        f"stdout_bytes={stdout_bytes}; stdout_sha256={stdout_sha256}; "
        f"stderr_bytes={len(stderr)}; stderr_sha256={sha256_bytes(stderr)}"
    )
    require_bounded_cli_failure_payload(
        diagnostic, "fixed process rejection diagnostic"
    )
    return diagnostic


def process_result_rejection_diagnostic(stage: str, result: ProcessResult) -> str:
    return fixed_process_stream_rejection_diagnostic(
        stage,
        result.returncode,
        len(result.stdout),
        sha256_bytes(result.stdout),
        result.stderr,
    )


def parse_lean_version(result: ProcessResult) -> LeanIdentity:
    generic_diagnostic = process_result_rejection_diagnostic(
        "Lean version probe", result
    )
    try:
        require(result.returncode == 0, "Lean version probe exited nonzero")
        require(result.stderr == b"", "Lean version probe emitted stderr")
        require(
            b"\r" not in result.stdout,
            "Lean version probe emitted a carriage return",
        )
        match = LEAN_VERSION_LINE.fullmatch(result.stdout)
        require(match is not None, "unexpected Lean version output")
        identity = LeanIdentity(
            version=match.group("version").decode("ascii"),
            platform=match.group("platform").decode("ascii"),
            commit=match.group("commit").decode("ascii"),
            build=match.group("build").decode("ascii"),
        )
        require(identity.version == EXPECTED_VERSION, "Lean version is not 4.32.2")
        require(
            identity.commit == EXPECTED_COMMIT,
            "Lean version reports the wrong source commit",
        )
        require(
            identity.build == "Release",
            "Lean version does not report a Release build",
        )
    except Exception:
        raise CustodyError(generic_diagnostic) from None
    return identity


def validate_lake_version(result: ProcessResult) -> None:
    generic_diagnostic = process_result_rejection_diagnostic(
        "Lake version probe", result
    )
    try:
        require(result.returncode == 0, "Lake version probe exited nonzero")
        require(result.stderr == b"", "Lake version probe emitted stderr")
        require(
            b"\r" not in result.stdout,
            "Lake version probe emitted a carriage return",
        )
        match = LAKE_VERSION_LINE.fullmatch(result.stdout)
        require(match is not None, "unexpected Lake version output")
        require(
            match.group("lean").decode("ascii") == EXPECTED_VERSION,
            "Lake reports the wrong Lean version",
        )
        require(
            match.group("lake").decode("ascii") == EXPECTED_LAKE_VERSION,
            "Lake reports the wrong exact version/source-commit abbreviation",
        )
    except Exception:
        raise CustodyError(generic_diagnostic) from None


def validate_leanchecker_probe(result: ProcessResult) -> None:
    expected = (
        f"uncaught exception: Could not find any oleans for: {ABSENT_MODULE}\n".encode(
            "ascii"
        )
    )
    generic_diagnostic = process_result_rejection_diagnostic(
        "LeanChecker absent-module probe", result
    )
    try:
        require(
            result.returncode == 1,
            "LeanChecker absent-module probe exited unexpectedly",
        )
        require(
            result.stdout == b"",
            "LeanChecker absent-module probe emitted stdout",
        )
        require(
            result.stderr == expected,
            "LeanChecker absent-module diagnostic drifted",
        )
    except Exception:
        raise CustodyError(generic_diagnostic) from None


def positive_int(value: object, role: str) -> int:
    require(type(value) is int and value > 0, f"{role} must be a positive integer")
    return value


def nested_executable_evidence_from_outer(
    snapshot: ExecutableSnapshot,
) -> dict[str, object]:
    require(
        snapshot.launch_target is None,
        "outer extracted executable launch route is a symbolic link",
    )
    require(
        snapshot.launch_path == snapshot.canonical_path,
        "outer extracted executable launch path is not canonical",
    )
    identity = snapshot.canonical_identity
    return {
        "launch_path": os.fspath(snapshot.launch_path),
        "canonical_path": os.fspath(snapshot.canonical_path),
        "bytes": len(snapshot.data),
        "sha256": snapshot.sha256,
        "identity": {
            "device": identity.device,
            "inode": identity.inode,
            "mode": identity.mode,
            "permissions": oct(stat.S_IMODE(identity.mode)),
            "links": identity.links,
            "size": identity.size,
            "modified_ns": identity.modified_ns,
            "changed_ns": identity.changed_ns,
        },
    }


def require_executable_snapshots_match_tree_leaves(
    tool_root: Path,
    snapshots: dict[str, ExecutableSnapshot],
    leaves: dict[str, object],
    role: str,
) -> None:
    """Bind live executable snapshots to the independently scanned tree leaves."""

    direct_root = require_canonical_existing_directory(tool_root, f"{role} root")
    exact_keys(snapshots, {"lean", "lake", "leanchecker"}, f"{role} snapshots")
    exact_keys(leaves, {"lean", "lake", "leanchecker"}, f"{role} leaves")
    for executable_role in ("lean", "lake", "leanchecker"):
        leaf = validate_leaf_shape(
            leaves[executable_role], f"{role} {executable_role} tree leaf"
        )
        expected_path = direct_root.joinpath(*str(leaf["path"]).split("/"))
        snapshot = snapshots[executable_role]
        identity = snapshot.canonical_identity
        require(
            snapshot.launch_target is None
            and snapshot.launch_path == expected_path
            and snapshot.canonical_path == expected_path,
            f"{role} {executable_role} live path differs from tree leaf",
        )
        require(
            snapshot.launch_identity == identity
            and stat.S_ISREG(identity.mode)
            and stat.S_IMODE(identity.mode) == int(str(leaf["mode"]), 8)
            and identity.links == 1,
            f"{role} {executable_role} live mode/link identity differs from tree leaf",
        )
        require(
            identity.size == leaf["size"]
            and len(snapshot.data) == leaf["size"]
            and snapshot.sha256 == leaf["sha256"]
            and sha256_bytes(snapshot.data) == leaf["sha256"],
            f"{role} {executable_role} live size/SHA-256 differs from tree leaf",
        )


def snapshot_tool_executables(
    tool_root: Path, role: str
) -> dict[str, ExecutableSnapshot]:
    direct_root = require_canonical_existing_directory(tool_root, f"{role} root")
    return {
        executable_role: snapshot_executable(
            direct_root / "bin" / executable_role,
            f"{role} {executable_role}",
        )
        for executable_role in ("lean", "lake", "leanchecker")
    }


def require_executable_snapshot_sets_equal(
    before: dict[str, ExecutableSnapshot],
    after: dict[str, ExecutableSnapshot],
    role: str,
) -> None:
    exact_keys(before, {"lean", "lake", "leanchecker"}, f"{role} before")
    exact_keys(after, {"lean", "lake", "leanchecker"}, f"{role} after")
    for executable_role in ("lean", "lake", "leanchecker"):
        require(
            after[executable_role] == before[executable_role],
            f"{role} {executable_role} full snapshot changed",
        )


def validate_nested_fixture_result(value: object, expected: dict[str, object]) -> None:
    fixture = exact_keys(
        value,
        {
            "bytes",
            "derived_query_bytes",
            "derived_query_sha256",
            "eof_canary_observed",
            "guarded_invalid_projection",
            "leanchecker_fresh_environment_replayed",
            "module",
            "name",
            "olean_bytes",
            "olean_sha256",
            "sha256",
            "target_olean_inventory_probe",
            "trust",
        },
        f"nested Lean kernel fixture {expected['name']}",
    )
    for key in (
        "bytes",
        "derived_query_bytes",
        "derived_query_sha256",
        "module",
        "name",
        "sha256",
    ):
        expected_value = expected[key]
        require(
            type(fixture[key]) is type(expected_value)
            and fixture[key] == expected_value,
            f"nested Lean kernel fixture {expected['name']} field {key!r} drifted",
        )
    require(
        type(fixture["trust"]) is int and fixture["trust"] == 0,
        f"nested Lean kernel fixture {expected['name']} trust level drifted",
    )
    for key in (
        "eof_canary_observed",
        "guarded_invalid_projection",
        "leanchecker_fresh_environment_replayed",
    ):
        require(
            fixture[key] is True,
            f"nested Lean kernel fixture {expected['name']} field {key!r} drifted",
        )
    positive_int(
        fixture["olean_bytes"],
        f"nested Lean kernel fixture {expected['name']} olean bytes",
    )
    exact_hex(
        fixture["olean_sha256"],
        64,
        f"nested Lean kernel fixture {expected['name']} olean SHA-256",
    )
    probe = exact_keys(
        fixture["target_olean_inventory_probe"],
        {
            "claim_scope",
            "complete_declaration_inventory_claimed",
            "eof_canary_observed",
            "exit_code",
            "bracketing_lookup_controls",
            "selected_declarations",
            "source_bytes",
            "source_sha256",
            "target_olean_imported",
        },
        f"nested Lean kernel fixture {expected['name']} selected declaration probe",
    )
    selected_declarations = [
        {
            "rendering": "axiom E : sorry",
            "source_role": (
                "residual_axiom_shaped_declaration_from_failed_inductive_route"
            ),
            "status": "present",
            "symbol": "E",
        },
        {
            "rendering": "Unknown constant `E.mk`",
            "source_role": "rejected_constructor_attempt",
            "status": "absent",
            "symbol": "E.mk",
        },
    ]
    if expected["name"] == "issue_14576.lean":
        selected_declarations.append(
            {
                "declaration_source_present": True,
                "post_failure_unknown_identifier_reference_guard": True,
                "rendering": "Unknown constant `bad`",
                "source_role": "unreached_downstream_declaration",
                "status": "absent",
                "symbol": "bad",
                "thmdecl_reached_or_attempted": False,
            }
        )
    expected_probe = {
        "claim_scope": "selected_names_in_this_emitted_olean_only",
        "complete_declaration_inventory_claimed": False,
        "eof_canary_observed": True,
        "exit_code": 0,
        "bracketing_lookup_controls": {
            "absent": "PidRsTargetOleanLookupNegative",
            "present": "PidRsTargetOleanLookupPositive",
        },
        "selected_declarations": selected_declarations,
        "source_bytes": expected["inventory_probe_source_bytes"],
        "source_sha256": expected["inventory_probe_source_sha256"],
        "target_olean_imported": True,
    }
    validate_exact_typed_object(
        probe,
        expected_probe,
        f"nested Lean kernel fixture {expected['name']} selected declaration probe",
    )


def validate_nested_benign_result(value: object) -> None:
    benign = exact_keys(
        value,
        {
            "derived_query_bytes",
            "derived_query_sha256",
            "eof_canary_observed",
            "exit_code",
            "leanchecker_fresh_environment_replayed",
            "module",
            "olean_bytes",
            "olean_sha256",
            "source_fixture",
            "source_fixture_sha256",
            "transformation",
            "transformed_source_sha256",
            "trust",
        },
        "nested Lean kernel benign near-neighbor",
    )
    expected = {
        "derived_query_bytes": 716,
        "derived_query_sha256": EXPECTED_BENIGN_QUERY_SHA256,
        "eof_canary_observed": True,
        "exit_code": 0,
        "leanchecker_fresh_environment_replayed": True,
        "module": "Issue14576MinBenign",
        "source_fixture": "issue_14576_min.lean",
        "source_fixture_sha256": EXPECTED_KERNEL_REGRESSION_FIXTURES[1]["sha256"],
        "transformation": (
            "replace_malformed_nested_C_projection_with_valid_W_projection_and_remove_"
            "only_the_expected_message_scaffolding"
        ),
        "transformed_source_sha256": EXPECTED_BENIGN_TRANSFORMED_SOURCE_SHA256,
        "trust": 0,
    }
    for key, expected_value in expected.items():
        require(
            type(benign[key]) is type(expected_value) and benign[key] == expected_value,
            f"nested Lean kernel benign near-neighbor field {key!r} drifted",
        )
    positive_int(benign["olean_bytes"], "nested Lean kernel benign olean bytes")
    exact_hex(benign["olean_sha256"], 64, "nested Lean kernel benign olean SHA-256")


def validate_nested_unguarded_result(value: object) -> None:
    unguarded = exact_keys(
        value,
        {
            "derived_query_bytes",
            "derived_query_sha256",
            "diagnostic",
            "diagnostic_path",
            "diagnostic_source_column",
            "diagnostic_source_line",
            "diagnostic_stream",
            "eof_canary_observed",
            "exit_code",
            "source_fixture",
            "source_fixture_sha256",
            "stderr",
            "stdout_shape",
            "transformation",
            "transformed_source_bytes",
            "transformed_source_sha256",
            "trust",
        },
        "nested Lean kernel unguarded negative control",
    )
    expected = {
        "derived_query_bytes": 2_466,
        "derived_query_sha256": EXPECTED_UNGUARDED_QUERY_SHA256,
        "diagnostic": "(kernel) invalid projection\\n  w.1",
        "diagnostic_path": "exact_absolute_private_query_path",
        "diagnostic_source_column": 0,
        "diagnostic_source_line": 58,
        "diagnostic_stream": "stdout",
        "eof_canary_observed": True,
        "exit_code": 1,
        "source_fixture": "issue_14576.lean",
        "source_fixture_sha256": EXPECTED_KERNEL_REGRESSION_FIXTURES[0]["sha256"],
        "stderr": "empty",
        "stdout_shape": (
            "<exact-absolute-private-query>:58:0: error: (kernel) invalid projection\\n"
            "  w.1\\n<exact-eof-canary>\\n"
        ),
        "transformation": (
            "replace_exactly_one_reviewed_invalid_projection_message_guard_scaffolding_"
            "with_unguarded_mkbug"
        ),
        "transformed_source_bytes": 2_397,
        "transformed_source_sha256": EXPECTED_UNGUARDED_TRANSFORMED_SOURCE_SHA256,
        "trust": 0,
    }
    validate_exact_typed_object(
        unguarded, expected, "nested Lean kernel unguarded negative control"
    )


def validate_nested_replay_measurements(nested: dict[str, object]) -> None:
    measurements = nested.get("leanchecker_fresh_environment_replay_measurements")
    require(
        isinstance(measurements, list)
        and len(measurements) == NESTED_KERNEL_REPLAY_COUNT,
        "nested Lean kernel replay measurement inventory drifted",
    )
    expected_modules = ["Issue14576Full", "Issue14576Min", "Issue14576MinBenign"]
    durations: list[int] = []
    for measurement, module in zip(measurements, expected_modules, strict=True):
        item = exact_keys(
            measurement,
            {"duration_monotonic_ns", "module", "timeout_seconds"},
            f"nested Lean kernel replay measurement {module}",
        )
        require(
            item["module"] == module
            and type(item["timeout_seconds"]) is int
            and item["timeout_seconds"] == NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS,
            f"nested Lean kernel replay measurement {module} identity/bound drifted",
        )
        duration = item["duration_monotonic_ns"]
        require(
            type(duration) is int and duration >= 0,
            f"nested Lean kernel replay measurement {module} duration drifted",
        )
        durations.append(duration)
    total = nested.get("leanchecker_fresh_environment_replay_total_monotonic_ns")
    maximum = nested.get("leanchecker_fresh_environment_replay_max_monotonic_ns")
    require(
        type(total) is int
        and total == sum(durations)
        and type(maximum) is int
        and maximum == max(durations),
        "nested Lean kernel replay measurement aggregate drifted",
    )


def validate_nested_executable_evidence(
    value: object,
    expected_path: Path,
    expected_evidence: dict[str, object],
    role: str,
) -> dict[str, object]:
    mismatch_diagnostic = nested_evidence_mismatch_diagnostic(
        value, expected_evidence, role
    )
    if mismatch_diagnostic is not None:
        raise NestedExecutableEvidenceMismatch(mismatch_diagnostic)

    # Structural checks intentionally follow the value-free fixed-schema predicate
    # and typed leaf-value comparison.  At this point every observed key, type, and
    # value equals outer live evidence, so no validator can disclose child material.
    evidence = exact_keys(
        value,
        {"bytes", "canonical_path", "identity", "launch_path", "sha256"},
        role,
    )
    expected_text = os.fspath(expected_path)
    require(
        evidence["launch_path"] == expected_text
        and evidence["canonical_path"] == expected_text,
        f"{role} launch/canonical path drifted",
    )
    size = positive_int(evidence["bytes"], f"{role} bytes")
    observed_sha256 = exact_hex(evidence["sha256"], 64, f"{role} SHA-256")
    require(observed_sha256 == evidence["sha256"], f"{role} SHA-256 drifted")
    identity = exact_keys(
        evidence["identity"],
        {
            "changed_ns",
            "device",
            "inode",
            "links",
            "mode",
            "modified_ns",
            "permissions",
            "size",
        },
        f"{role} identity",
    )
    for key in ("changed_ns", "device", "inode", "mode", "modified_ns"):
        require(
            type(identity[key]) is int and identity[key] >= 0,
            f"{role} identity field {key!r} drifted",
        )
    require(
        type(identity["links"]) is int
        and identity["links"] == 1
        and type(identity["size"]) is int
        and identity["size"] == size
        and identity["permissions"] == "0o755"
        and stat.S_ISREG(int(identity["mode"]))
        and int(identity["mode"]) & 0o111 != 0,
        f"{role} identity size/link/mode drifted",
    )
    return evidence


def validate_nested_execution_route(
    value: object,
    tool_root: Path,
    platform_key: str,
    expected_metadata_sha256: str,
    expected_executable_evidence: dict[str, dict[str, object]],
) -> None:
    route = exact_keys(
        value,
        {
            "absolute_launch_and_source_paths",
            "ambient_home_logname_user_retained",
            "archive_derivation_claimed_by_this_checker",
            "child_environment_removed_keys",
            "child_environment_removed_prefixes",
            "direct_lake_post_execution",
            "direct_lake_pre_execution",
            "direct_lean_post_execution",
            "direct_lean_pre_execution",
            "direct_leanchecker_post_execution",
            "direct_leanchecker_pre_execution",
            "direct_tool_leaf_bytes_equal_before_and_after",
            "direct_tool_leaves_bound",
            "direct_toolchain_root",
            "descendant_group_or_session_changes_continuously_observed",
            "elan_invoked",
            "fixed_child_path",
            "immediate_pre_post_source_and_tool_endpoint_checks",
            "inner_children_start_new_sessions",
            "isolated_child_group_absence_checked",
            "isolated_child_group_cleanup_after_every_outcome",
            "isolated_child_group_cleanup_signal_policy",
            "leanchecker_fresh_environment_child_path_prefix",
            "leanchecker_fresh_environment_replay_arguments",
            "leanchecker_fresh_environment_replay_timeout_seconds",
            "metadata_lifecycle_state",
            "nested_checker_self_binding_equal",
            "non_child_descendants_reaped_by_this_checker",
            "per_child_private_environment_directory_modes",
            "per_child_private_home_and_tmp",
            "private_lean_path_only_for_leanchecker_fresh_environment_replay",
            "private_temporary_directory_modes",
            "private_temporary_directory_pre_post_identity_equal",
            "process_group_cleanup_bounds_milliseconds",
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log",
            "process_group_observation_atomic",
            "process_group_reuse_excluded",
            "reviewed_pin_platform_key",
            "required_archive_derivation_route",
            "shared_outer_process_group",
            "shared_group_cleanup_owned_by_outer_supervisor",
            "shared_group_signal_from_nested_checker",
            "source_compile_arguments",
            "toolchain_metadata_policy_projection_sha256",
            "toolchain_metadata_sha256",
            "unguarded_source_arguments",
            "version_commit_build_platform_equal_before_and_after",
            "version_output_is_identity_evidence_not_authenticity",
        },
        "nested Lean kernel regression execution route",
    )
    require(
        route["direct_toolchain_root"] == os.fspath(tool_root)
        and route["reviewed_pin_platform_key"] == platform_key
        and route["metadata_lifecycle_state"] == "reviewed_pins_strict_replay_required"
        and route["toolchain_metadata_sha256"] == expected_metadata_sha256
        and route["toolchain_metadata_policy_projection_sha256"]
        == EXPECTED_METADATA_POLICY_SHA256
        and route["nested_checker_self_binding_equal"] is True
        and route["archive_derivation_claimed_by_this_checker"] is False
        and route["required_archive_derivation_route"]
        == "nested_same-transaction_execution_by_"
        "lean-toolchain-release-custody-check/v5"
        and route["elan_invoked"] is False,
        "nested Lean kernel regression direct-toolchain route drifted",
    )
    require(
        route["absolute_launch_and_source_paths"] is True
        and route["source_compile_arguments"]
        == ["--trust=0", "-o", "<absolute-private-olean>", "<absolute-private-query>"]
        and route["unguarded_source_arguments"] == ["--trust=0", "<absolute-query>"]
        and route["leanchecker_fresh_environment_replay_arguments"]
        == ["--fresh", "<private-module>"]
        and type(route["leanchecker_fresh_environment_replay_timeout_seconds"]) is int
        and route["leanchecker_fresh_environment_replay_timeout_seconds"]
        == NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS,
        "nested Lean kernel regression command route drifted",
    )
    require(
        route["direct_tool_leaves_bound"] == ["lean", "lake", "leanchecker"]
        and route["direct_tool_leaf_bytes_equal_before_and_after"] is True
        and route["version_commit_build_platform_equal_before_and_after"] is True
        and route["immediate_pre_post_source_and_tool_endpoint_checks"] is True,
        "nested Lean kernel regression tool endpoint claims drifted",
    )
    require(
        route["shared_outer_process_group"] is True
        and route["inner_children_start_new_sessions"] is False
        and route["isolated_child_group_cleanup_after_every_outcome"] is False
        and route["isolated_child_group_cleanup_signal_policy"] == ["TERM", "KILL"]
        and route["process_group_cleanup_signal_policy_is_escalation_not_delivery_log"]
        is True
        and route["isolated_child_group_absence_checked"] is False
        and route["non_child_descendants_reaped_by_this_checker"] is False
        and route["process_group_observation_atomic"] is False
        and route["process_group_reuse_excluded"] is False
        and route["descendant_group_or_session_changes_continuously_observed"] is False
        and route["shared_group_signal_from_nested_checker"] is False
        and route["shared_group_cleanup_owned_by_outer_supervisor"] is True,
        "nested Lean kernel regression descendant cleanup route drifted",
    )
    validate_exact_typed_object(
        route["process_group_cleanup_bounds_milliseconds"],
        {
            "absence_poll_interval": PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS,
            "direct_child_reap_timeout": DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS,
            "kill_grace": PROCESS_GROUP_KILL_GRACE_MILLISECONDS,
            "term_grace": PROCESS_GROUP_TERM_GRACE_MILLISECONDS,
        },
        "nested Lean kernel regression process-group cleanup bounds",
    )
    require(
        route["private_temporary_directory_pre_post_identity_equal"] is True,
        "nested Lean kernel regression private-directory custody drifted",
    )
    validate_exact_typed_object(
        route["private_temporary_directory_modes"],
        {
            "temporary_root": "0700",
            "query_root": "0700",
            "olean_root": "0700",
        },
        "nested Lean kernel regression private-directory modes",
    )
    validate_exact_typed_object(
        route["per_child_private_environment_directory_modes"],
        {"temporary_root": "0700", "home": "0700", "tmp": "0700"},
        "nested Lean kernel regression per-child private environment modes",
    )
    require(
        route["private_lean_path_only_for_leanchecker_fresh_environment_replay"] is True
        and route["ambient_home_logname_user_retained"] is False
        and route["per_child_private_home_and_tmp"] is True
        and route["version_output_is_identity_evidence_not_authenticity"] is True
        and route["fixed_child_path"] == os.defpath
        and route["leanchecker_fresh_environment_child_path_prefix"]
        == os.fspath(tool_root / "bin")
        and route["child_environment_removed_prefixes"]
        == EXPECTED_NESTED_ENVIRONMENT_PREFIXES_TO_REMOVE
        and route["child_environment_removed_keys"]
        == EXPECTED_NESTED_ENVIRONMENT_KEYS_TO_REMOVE,
        "nested Lean kernel regression environment route drifted",
    )
    for role in ("lean", "lake", "leanchecker"):
        expected_path = tool_root / "bin" / role
        expected_evidence = expected_executable_evidence[role]
        before = validate_nested_executable_evidence(
            route[f"direct_{role}_pre_execution"],
            expected_path,
            expected_evidence,
            f"nested Lean kernel direct {role} pre-execution evidence",
        )
        after = validate_nested_executable_evidence(
            route[f"direct_{role}_post_execution"],
            expected_path,
            expected_evidence,
            f"nested Lean kernel direct {role} post-execution evidence",
        )
        require(
            after == before,
            f"nested Lean kernel direct {role} pre/post evidence drifted",
        )


def probe_toolchain(
    tool_root: Path, private_root: Path, limits: dict[str, object]
) -> tuple[dict[str, object], dict[str, ExecutableSnapshot]]:
    tool_root = require_canonical_existing_directory(
        tool_root, "extracted toolchain root before probes"
    )
    home = private_root / "home"
    temporary = private_root / "tmp"
    create_private_directory(home, "private child HOME")
    create_private_directory(temporary, "private child TMPDIR")
    environment = build_child_environment(tool_root, home, temporary)
    snapshots: dict[str, ExecutableSnapshot] = {}
    for role in ("lean", "lake", "leanchecker"):
        path = tool_root / "bin" / role
        snapshot = snapshot_executable(path, f"extracted {role}")
        require(
            snapshot.launch_target is None, f"extracted {role} leaf is a symbolic link"
        )
        snapshots[role] = snapshot
    lean_result = run_bounded_process(
        [os.fspath(tool_root / "bin/lean"), "--version"], tool_root, environment, limits
    )
    identity = parse_lean_version(lean_result)
    lake_result = run_bounded_process(
        [os.fspath(tool_root / "bin/lake"), "--version"], tool_root, environment, limits
    )
    validate_lake_version(lake_result)
    checker_result = run_bounded_process(
        [os.fspath(tool_root / "bin/leanchecker"), ABSENT_MODULE],
        tool_root,
        environment,
        limits,
    )
    validate_leanchecker_probe(checker_result)
    validate_child_environment(environment, tool_root)
    for role, snapshot in snapshots.items():
        require_executable_unchanged(snapshot, f"extracted {role}")
        selected = resolve_from_path(role, environment["PATH"])
        require(
            selected == snapshot.launch_path, f"child PATH selection changed for {role}"
        )
    probes = {
        "build": identity.build,
        "commit": identity.commit,
        "lake_stdout": lake_result.stdout.decode("ascii"),
        "lean_platform": identity.platform,
        "lean_stdout": lean_result.stdout.decode("ascii"),
        "leanchecker_absent_module_exit": checker_result.returncode,
        "leanchecker_absent_module_stderr": checker_result.stderr.decode("ascii"),
        "version": identity.version,
    }
    return probes, snapshots


def validate_nested_kernel_regression_result(
    nested: dict[str, object],
    tool_root: Path,
    platform_key: str,
    outer_timeout_seconds: int,
    expected_metadata_sha256: str,
    expected_checker_sha256: str,
    expected_lean_platform: str,
    expected_executable_evidence: dict[str, dict[str, object]],
) -> None:
    exact_keys(
        nested,
        {
            "active_scientific_project_inputs_consumed",
            "active_scientific_project_toolchain_migration_claimed",
            "benign_near_neighbor",
            "boundary",
            "checker_source_sha256",
            "execution_route",
            "fixtures",
            "lake",
            "lean",
            "leanchecker_fresh_environment_replay_max_monotonic_ns",
            "leanchecker_fresh_environment_replay_measurements",
            "leanchecker_fresh_environment_replay_total_monotonic_ns",
            "leanchecker_fresh_environment_replayed_modules",
            "leanchecker_fresh_environment_replays",
            "leanchecker_fresh_semantics",
            "nested_timing_contract",
            "origin_sha256",
            "schema",
            "scope_boundary",
            "status",
            "trust_zero_olean_compilations",
            "trust_zero_semantics",
            "unguarded_negative_control",
        },
        "nested Lean kernel regression result",
    )
    require(
        nested.get("schema") == KERNEL_REGRESSION_RESULT_SCHEMA
        and nested.get("status") == "regression_checks_passed",
        "nested Lean kernel regression result schema or status drifted",
    )
    validate_exact_typed_object(
        nested.get("scope_boundary"),
        EXPECTED_NESTED_SCOPE_BOUNDARY,
        "nested Lean kernel regression scope boundary",
    )
    lean = exact_keys(
        nested.get("lean"),
        {
            "build",
            "commit",
            "platform",
            "post_execution_identity_equal",
            "toolchain",
            "version",
        },
        "nested Lean kernel regression Lean identity",
    )
    require(
        lean["version"] == EXPECTED_VERSION
        and lean["commit"] == EXPECTED_COMMIT
        and lean["build"] == "Release"
        and lean["toolchain"] == "leanprover/lean4:v4.32.2"
        and lean["post_execution_identity_equal"] is True
        and lean["platform"] == expected_lean_platform,
        "nested Lean kernel regression Lean identity drifted",
    )
    lake = exact_keys(
        nested.get("lake"),
        {"lean_version", "post_execution_identity_equal", "version"},
        "nested Lean kernel regression Lake identity",
    )
    require(
        lake["version"] == "5.0.0-src+f3b06c7"
        and lake["lean_version"] == EXPECTED_VERSION
        and lake["post_execution_identity_equal"] is True,
        "nested Lean kernel regression Lake identity drifted",
    )
    validate_nested_execution_route(
        nested.get("execution_route"),
        tool_root,
        platform_key,
        expected_metadata_sha256,
        expected_executable_evidence,
    )
    require(
        nested.get("checker_source_sha256") == expected_checker_sha256,
        "nested Lean kernel regression checker-source identity drifted",
    )
    require(
        nested.get("active_scientific_project_inputs_consumed") == []
        and nested.get("active_scientific_project_toolchain_migration_claimed")
        is False,
        "nested Lean kernel regression active-project decoupling drifted",
    )
    validate_exact_typed_object(
        nested.get("trust_zero_semantics"),
        EXPECTED_TRUST_ZERO_SEMANTICS,
        "nested Lean kernel regression trust-zero semantics",
    )
    validate_exact_typed_object(
        nested.get("leanchecker_fresh_semantics"),
        EXPECTED_LEANCHECKER_FRESH_SEMANTICS,
        "nested Lean kernel regression LeanChecker-fresh semantics",
    )
    require(
        nested.get("origin_sha256") == EXPECTED_KERNEL_REGRESSION_ORIGIN_SHA256,
        "nested Lean kernel regression origin identity drifted",
    )
    fixtures = nested.get("fixtures")
    require(
        isinstance(fixtures, list)
        and len(fixtures) == len(EXPECTED_KERNEL_REGRESSION_FIXTURES),
        "nested Lean kernel regression fixture inventory drifted",
    )
    for fixture, expected_fixture in zip(
        fixtures, EXPECTED_KERNEL_REGRESSION_FIXTURES, strict=True
    ):
        validate_nested_fixture_result(fixture, expected_fixture)
    require(
        type(nested.get("trust_zero_olean_compilations")) is int
        and nested.get("trust_zero_olean_compilations") == 3,
        "nested Lean kernel regression trust-zero compilation count drifted",
    )
    validate_nested_benign_result(nested.get("benign_near_neighbor"))
    validate_nested_unguarded_result(nested.get("unguarded_negative_control"))
    require(
        type(nested.get("leanchecker_fresh_environment_replays")) is int
        and nested.get("leanchecker_fresh_environment_replays")
        == NESTED_KERNEL_REPLAY_COUNT
        and nested.get("leanchecker_fresh_environment_replayed_modules")
        == ["Issue14576Full", "Issue14576Min", "Issue14576MinBenign"],
        "nested Lean kernel regression replay inventory drifted",
    )
    validate_nested_replay_measurements(nested)
    timing = exact_keys(
        nested.get("nested_timing_contract"),
        {
            "declared_non_replay_margin_seconds",
            "derivation",
            "environmental_premise",
            "identity_child_count",
            "identity_child_timeout_seconds",
            "inner_per_replay_timeout_seconds",
            "non_replay_lean_child_count",
            "non_replay_lean_child_timeout_seconds",
            "orchestration_headroom_seconds",
            "replay_count",
            "required_outer_timeout_seconds",
        },
        "nested Lean kernel timing contract",
    )
    inner = timing.get("inner_per_replay_timeout_seconds")
    count = timing.get("replay_count")
    lean_timeout = timing.get("non_replay_lean_child_timeout_seconds")
    lean_count = timing.get("non_replay_lean_child_count")
    identity_timeout = timing.get("identity_child_timeout_seconds")
    identity_count = timing.get("identity_child_count")
    headroom = timing.get("orchestration_headroom_seconds")
    margin = timing.get("declared_non_replay_margin_seconds")
    required_outer = timing.get("required_outer_timeout_seconds")
    require(
        type(inner) is int and inner == NESTED_KERNEL_INNER_REPLAY_TIMEOUT_SECONDS,
        "nested Lean kernel timing inner bound drifted",
    )
    require(
        type(count) is int and count == NESTED_KERNEL_REPLAY_COUNT,
        "nested Lean kernel timing replay count drifted",
    )
    require(
        type(lean_timeout) is int
        and lean_timeout == NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS,
        "nested Lean kernel timing non-replay Lean-child bound drifted",
    )
    require(
        type(lean_count) is int
        and lean_count == NESTED_KERNEL_NON_REPLAY_LEAN_CHILD_COUNT,
        "nested Lean kernel timing non-replay Lean-child count drifted",
    )
    require(
        type(identity_timeout) is int
        and identity_timeout == NESTED_KERNEL_IDENTITY_CHILD_TIMEOUT_SECONDS,
        "nested Lean kernel timing identity-child bound drifted",
    )
    require(
        type(identity_count) is int
        and identity_count == NESTED_KERNEL_IDENTITY_CHILD_COUNT,
        "nested Lean kernel timing identity-child count drifted",
    )
    require(
        type(headroom) is int
        and headroom == NESTED_KERNEL_ORCHESTRATION_HEADROOM_SECONDS,
        "nested Lean kernel timing orchestration headroom drifted",
    )
    require(
        type(margin) is int
        and margin
        == lean_timeout * lean_count + identity_timeout * identity_count + headroom
        and margin == NESTED_KERNEL_NON_REPLAY_MARGIN_SECONDS,
        "nested Lean kernel timing non-replay allocation drifted or is contradictory",
    )
    require(
        type(required_outer) is int
        and required_outer == inner * count + margin
        and required_outer == NESTED_KERNEL_REQUIRED_OUTER_TIMEOUT_SECONDS,
        "nested Lean kernel timing required outer bound drifted or is contradictory",
    )
    require(
        timing.get("derivation") == "inner_per_replay_timeout_seconds*replay_count+"
        "non_replay_lean_child_timeout_seconds*non_replay_lean_child_count+"
        "identity_child_timeout_seconds*identity_child_count+"
        "orchestration_headroom_seconds",
        "nested Lean kernel timing derivation drifted",
    )
    premise = timing.get("environmental_premise")
    require(
        isinstance(premise, str)
        and "host load" in premise
        and "not performance guarantees" in premise,
        "nested Lean kernel timing environmental premise drifted",
    )
    require(
        type(outer_timeout_seconds) is int
        and outer_timeout_seconds == NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS
        and outer_timeout_seconds >= required_outer,
        "nested Lean kernel selected outer bound drifted or is contradictory",
    )
    boundary = nested.get("boundary")
    require(
        isinstance(boundary, str)
        and len(boundary.encode("utf-8")) < 16_384
        and sha256_bytes(boundary.encode("utf-8")) == EXPECTED_NESTED_BOUNDARY_SHA256,
        "nested Lean kernel regression nonclaim boundary drifted",
    )


def nested_kernel_regression_command(
    python: Path, checker_source: Path, direct_root: Path
) -> list[str]:
    return [
        os.fspath(python),
        "-I",
        "-S",
        "-B",
        os.fspath(checker_source),
        "--toolchain-root",
        os.fspath(direct_root),
        "--shared-outer-process-group",
    ]


def validate_nested_kernel_regression_command(
    command: list[str], python: Path, checker_source: Path, direct_root: Path
) -> None:
    require(
        command
        == nested_kernel_regression_command(python, checker_source, direct_root),
        "nested Lean kernel regression command route drifted",
    )


def failed_process_digest_diagnostic(result: ProcessResult, role: str) -> str:
    require(
        role == "nested Lean kernel regression checker",
        "failed-process diagnostic role is not fixed",
    )
    require(result.returncode != 0, f"{role} failure diagnostic requires nonzero exit")
    diagnostic = (
        f"{role} failed with exit {result.returncode}; "
        f"stdout_bytes={len(result.stdout)}; "
        f"stdout_sha256={sha256_bytes(result.stdout)}; "
        f"stderr_bytes={len(result.stderr)}; "
        f"stderr_sha256={sha256_bytes(result.stderr)}"
    )
    require_bounded_cli_failure_payload(diagnostic, "fixed failed-process diagnostic")
    return diagnostic


def nested_zero_exit_result_digest_diagnostic(result: ProcessResult) -> str:
    """Return the sole generic diagnostic allowed across the zero-exit child boundary."""

    diagnostic = (
        "nested Lean kernel regression result rejected; "
        f"stdout_bytes={len(result.stdout)}; "
        f"stdout_sha256={sha256_bytes(result.stdout)}; "
        f"stderr_bytes={len(result.stderr)}; "
        f"stderr_sha256={sha256_bytes(result.stderr)}"
    )
    require_bounded_cli_failure_payload(diagnostic, "fixed nested result diagnostic")
    return diagnostic


def nested_executable_mismatch_is_boundary_safe(diagnostic: str) -> bool:
    """Recognize the exact typed leaf diagnostic that may bypass generic redaction."""

    try:
        encoded = diagnostic.encode("ascii", errors="strict")
    except UnicodeError:
        return False
    if (
        len(encoded) > MISMATCH_DIAGNOSTIC_BYTES_MAX
        or len(CLI_FAILURE_PREFIX.encode("ascii")) + len(encoded) + len(b"\n")
        > CLI_FAILURE_STDERR_BYTES_MAX
        or not encoded
        or any(byte < 0x20 or byte > 0x7E for byte in encoded)
    ):
        return False
    roles = "(?:lean|lake|leanchecker)"
    phases = "(?:pre|post)"
    match = re.fullmatch(
        rf"nested Lean kernel direct {roles} {phases}-execution evidence "
        rf"disagrees with the outer live executable snapshot at fields: (?P<detail>.*); "
        rf"observed_evidence_sha256=(?P<observed>[0-9a-f]{{64}}); "
        rf"expected_evidence_sha256=(?P<expected>[0-9a-f]{{64}})",
        diagnostic,
    )
    if match is None:
        return False
    detail = match.group("detail")
    try:
        paths = json.loads(
            detail,
            parse_constant=reject_nonfinite_json_constant,
            parse_float=reject_json_float,
        )
    except (CustodyError, json.JSONDecodeError, TypeError, ValueError):
        return False
    return (
        isinstance(paths, list)
        and 0 < len(paths) <= MISMATCH_FIELD_PATHS_MAX
        and all(
            isinstance(path, str)
            and path in NESTED_EXECUTABLE_EVIDENCE_VALUE_POINTERS
            and 0 < len(path.encode("utf-8")) <= MISMATCH_FIELD_PATH_BYTES_MAX
            for path in paths
        )
        and paths == sorted(set(paths))
        and detail
        == json.dumps(
            paths,
            sort_keys=False,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def parse_and_validate_nested_kernel_regression_output(
    result: ProcessResult,
    tool_root: Path,
    platform_key: str,
    outer_timeout_seconds: int,
    expected_metadata_sha256: str,
    expected_checker_sha256: str,
    expected_lean_platform: str,
    expected_executable_evidence: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Close the complete zero-exit nested-child output trust boundary."""

    generic_diagnostic = nested_zero_exit_result_digest_diagnostic(result)
    try:
        require(result.returncode == 0, "nested result wrapper requires zero exit")
        require(
            result.stderr == b"",
            "nested Lean kernel regression checker emitted stderr",
        )
        require(
            b"\r" not in result.stdout
            and result.stdout.endswith(b"\n")
            and result.stdout.count(b"\n") == 1,
            "nested Lean kernel regression checker did not emit one canonical JSON line",
        )
        nested = parse_json_object(
            result.stdout,
            "nested Lean kernel regression result",
        )
        require(
            result.stdout == canonical_json_bytes(nested) + b"\n",
            "nested Lean kernel regression result did not emit canonical JSON bytes",
        )
        validate_nested_kernel_regression_result(
            nested,
            tool_root,
            platform_key,
            outer_timeout_seconds,
            expected_metadata_sha256,
            expected_checker_sha256,
            expected_lean_platform,
            expected_executable_evidence,
        )
    except NestedExecutableEvidenceMismatch as error:
        if nested_executable_mismatch_is_boundary_safe(str(error)):
            raise
        raise CustodyError(generic_diagnostic) from None
    except Exception:
        raise CustodyError(generic_diagnostic) from None
    return nested


def run_nested_kernel_regression(
    tool_root: Path,
    private_root: Path,
    limits: dict[str, object],
    platform_key: str,
    nested_checker_baseline: StableSnapshot,
    metadata: dict[str, object],
    probes: dict[str, object],
    executable_snapshots: dict[str, ExecutableSnapshot],
) -> dict[str, object]:
    """Run the exact regression checker against this still-live extracted tree."""

    direct_root = require_canonical_existing_directory(
        tool_root, "extracted toolchain root before nested regression"
    )
    require(
        direct_root.name == tool_root.name,
        "canonical extracted toolchain root basename drifted",
    )
    require(
        nested_checker_baseline.path == KERNEL_REGRESSION_CHECKER_PATH,
        "nested checker baseline path drifted",
    )
    require_repo_snapshot_unchanged(
        nested_checker_baseline,
        "nested Lean kernel regression checker",
    )
    checker_source = snapshot_bound_nested_checker(metadata)
    require(
        checker_source.identity == nested_checker_baseline.identity
        and checker_source.data == nested_checker_baseline.data,
        "nested Lean kernel regression checker changed before execution",
    )
    python = snapshot_executable(
        Path(sys.executable),
        "nested regression Python interpreter",
    )
    environment = build_child_environment(
        direct_root,
        private_root / "home",
        private_root / "tmp",
    )
    command = nested_kernel_regression_command(
        python.launch_path, checker_source.path, direct_root
    )
    validate_nested_kernel_regression_command(
        command, python.launch_path, checker_source.path, direct_root
    )
    result = run_bounded_process(
        command,
        ROOT,
        environment,
        limits,
        timeout_seconds=NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise CustodyError(
            failed_process_digest_diagnostic(
                result, "nested Lean kernel regression checker"
            )
        )
    nested = parse_and_validate_nested_kernel_regression_output(
        result,
        direct_root,
        platform_key,
        NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
        sha256_bytes(canonical_metadata_bytes(metadata)),
        checker_source.sha256,
        str(probes["lean_platform"]),
        {
            role: nested_executable_evidence_from_outer(snapshot)
            for role, snapshot in executable_snapshots.items()
        },
    )
    require_repo_snapshot_unchanged(
        checker_source,
        "nested Lean kernel regression checker",
    )
    require_executable_unchanged(
        python,
        "nested regression Python interpreter",
    )
    return {
        "status": "executed_same_transaction_checks_passed",
        "same_extraction_transaction": True,
        "outer_supervisor_group_cleanup_after_nested_outcome": True,
        "checker_binding": repo_source_binding_evidence(checker_source),
        "python_launch_path": os.fspath(python.launch_path),
        "python_canonical_path": os.fspath(python.canonical_path),
        "python_sha256": python.sha256,
        "command_arguments": [
            "-I",
            "-S",
            "-B",
            "scripts/check-lean-kernel-14576.py",
            "--toolchain-root",
            "<same-live-extracted-toolchain-root>",
            "--shared-outer-process-group",
        ],
        "timeout_seconds": NESTED_KERNEL_REGRESSION_TIMEOUT_SECONDS,
        "result": nested,
    }


def validate_host(asset: dict[str, object]) -> dict[str, str]:
    observed = {"system": platform.system(), "machine": platform.machine().lower()}
    host = asset["host"]
    require(
        observed["system"] == host["system"],
        f"asset requires host system {host['system']}, found {observed['system']}",
    )
    allowed = [str(item).lower() for item in host["machines"]]
    require(
        observed["machine"] in allowed,
        f"asset requires host machine in {allowed}, found {observed['machine']}",
    )
    return observed


def qualify(
    asset: dict[str, object],
    archive_path: Path,
    zstd_path: Path | None,
    observation_only: bool,
    source_snapshot: StableSnapshot,
    metadata_snapshot: StableSnapshot,
    nested_checker_snapshot: StableSnapshot,
    historical_receipt_snapshot: StableSnapshot,
    legacy_raw_snapshot: StableSnapshot,
    legacy_receipt_snapshot: StableSnapshot,
    metadata: dict[str, object],
) -> dict[str, object]:
    key = asset["key"]
    lifecycle = asset["custody_lifecycle"]
    state = lifecycle["state"]
    if state == "hosted_pending":
        require(
            observation_only,
            f"{key} derived pins are hosted_pending; strict replay is forbidden",
        )
    else:
        require(
            state == "reviewed_pins_strict_replay_required" and not observation_only,
            f"{key} reviewed pins permit strict replay only",
        )
    host = validate_host(asset)
    limits = metadata["limits"]
    archive_before = external_file_digest(archive_path, "Lean release archive")
    expected_archive = asset["archive"]
    require(
        archive_before.identity.size <= int(limits["archive_bytes_max"]),
        "release archive exceeds the policy byte ceiling",
    )
    require(
        archive_before.identity.size == expected_archive["size"],
        "release archive size differs from GitHub-advertised metadata",
    )
    require(
        archive_before.sha256 == expected_archive["sha256"],
        "release archive SHA-256 differs from GitHub-advertised metadata",
    )
    zstd = snapshot_executable(select_zstd(zstd_path), "zstd decoder")

    preflight_result, preflight_stream_bytes = consume_zstd_archive(
        archive_before.path,
        zstd,
        limits,
        lambda stream: preflight_tar_stream(stream, asset, limits),
    )
    records, inventory = preflight_result
    if state == "reviewed_pins_strict_replay_required":
        require(
            inventory == lifecycle["inventory"],
            "archive inventory differs from the reviewed exact pin",
        )

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-toolchain-custody-"
    ) as temporary_name:
        private_root = canonicalize_existing_directory(
            Path(temporary_name), "private extraction temporary root"
        )
        enforce_private_directory_mode(
            private_root, "private extraction temporary root"
        )
        destination = private_root / "tree"
        create_private_directory(destination, "private extraction destination")
        extracted, extraction_stream_bytes = consume_zstd_archive(
            archive_before.path,
            zstd,
            limits,
            lambda stream: extract_tar_stream(
                stream, destination, asset, limits, records
            ),
        )
        expected_entries = entries_from_records(records, extracted)
        scanned_before = scan_extracted_tree(destination, limits)
        require_same_tree(
            expected_entries,
            scanned_before,
            "between extraction and independent tree scan",
        )
        manifest = tree_manifest_sha256(scanned_before)
        leaves = leaf_facts(scanned_before, expected_archive["root"])
        if state == "reviewed_pins_strict_replay_required":
            require(
                manifest == lifecycle["tree_manifest"]["sha256"],
                "canonical extracted-tree manifest SHA-256 differs from the reviewed pin",
            )
            require(
                leaves == lifecycle["leaves"],
                "executable leaf identities differ from the reviewed pins",
            )
        tool_root = destination / expected_archive["root"]
        probes, probe_snapshots = probe_toolchain(tool_root, private_root, limits)
        pre_nested_snapshots = snapshot_tool_executables(
            tool_root, "immediate pre-nested executable snapshot"
        )
        require_executable_snapshot_sets_equal(
            probe_snapshots,
            pre_nested_snapshots,
            "probe-to-immediate-pre-nested executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            pre_nested_snapshots,
            leaves,
            "pre-nested executable-to-reviewed-tree binding",
        )
        if state == "reviewed_pins_strict_replay_required":
            require(
                probes == lifecycle["probes"],
                "toolchain version/platform/diagnostic probes differ from reviewed pins",
            )
            nested_kernel_regression = run_nested_kernel_regression(
                tool_root,
                private_root,
                limits,
                key,
                nested_checker_snapshot,
                metadata,
                probes,
                pre_nested_snapshots,
            )
        else:
            nested_kernel_regression = {
                "status": "not_run_pending_asset",
                "same_extraction_transaction": False,
                "reason": (
                    "hosted-pending derived executable pins cannot execute "
                    "the strict regression route in an observation run"
                ),
            }
        post_nested_snapshots = snapshot_tool_executables(
            tool_root, "immediate post-nested executable snapshot"
        )
        require_executable_snapshot_sets_equal(
            pre_nested_snapshots,
            post_nested_snapshots,
            "immediate pre/post-nested executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            post_nested_snapshots,
            leaves,
            "post-nested executable-to-reviewed-tree binding",
        )
        scanned_after = scan_extracted_tree(destination, limits)
        require_same_tree(scanned_before, scanned_after, "across executable probes")
        require(
            tree_manifest_sha256(scanned_after) == manifest,
            "canonical tree manifest changed across executable probes",
        )
        final_snapshots = snapshot_tool_executables(
            tool_root, "post-final-tree-scan executable snapshot"
        )
        require_executable_snapshot_sets_equal(
            post_nested_snapshots,
            final_snapshots,
            "post-nested-to-final-tree-scan executable custody",
        )
        require_executable_snapshots_match_tree_leaves(
            tool_root,
            final_snapshots,
            leaves,
            "post-final-tree-scan executable-to-reviewed-tree binding",
        )

    require_executable_unchanged(zstd, "zstd decoder")
    archive_after = external_file_digest(archive_before.path, "Lean release archive")
    require_external_unchanged(archive_before, archive_after, "Lean release archive")
    require_repo_snapshot_unchanged(source_snapshot, "toolchain custody checker source")
    require_repo_snapshot_unchanged(metadata_snapshot, "toolchain release metadata")
    require_repo_snapshot_unchanged(
        nested_checker_snapshot,
        "nested Lean kernel regression checker",
    )
    require_repo_snapshot_unchanged(
        historical_receipt_snapshot,
        "historical Darwin source receipt",
    )
    require_repo_snapshot_unchanged(
        legacy_raw_snapshot,
        "published legacy-v4 observation raw evidence",
    )
    require_repo_snapshot_unchanged(
        legacy_receipt_snapshot,
        "published legacy-v4 observation receipt evidence",
    )

    strict_replay = state == "reviewed_pins_strict_replay_required"
    status = (
        "strict_replay_checks_passed_publication_pending"
        if strict_replay
        else "observation_only_unqualified"
    )
    credit_boundary = {
        **metadata["credit_boundary"],
        "static_schema_validation": "validated_against_exact_bound_packet",
        "archive_custody": (
            "none_until_exact_result_is_immutably_published"
            if strict_replay
            else "none"
        ),
        "real_nested_regression": (
            "executed_same_transaction_checks_passed_unpublished_result"
            if strict_replay
            else "not_run_pending_asset"
        ),
    }
    result = {
        "schema": RESULT_SCHEMA,
        "result_kind": "strict_replay" if strict_replay else "observation_only",
        "status": status,
        "platform_key": key,
        "lifecycle_state_before_run": state,
        "host": host,
        "source_binding": {
            "checker_bytes": source_snapshot.identity.size,
            "checker_sha256": source_snapshot.sha256,
            "metadata_bytes": metadata_snapshot.identity.size,
            "metadata_sha256": metadata_snapshot.sha256,
            "metadata_policy_projection_sha256": EXPECTED_METADATA_POLICY_SHA256,
            "nested_checker_binding": repo_source_binding_evidence(
                nested_checker_snapshot
            ),
            "historical_nontransferable_receipt_binding": (
                repo_source_binding_evidence(historical_receipt_snapshot)
            ),
            "acyclic_policy": metadata["checker_binding"]["policy"],
            "published_observation_binding": (
                lifecycle["reviewed_pin_source"] if strict_replay else None
            ),
        },
        "release_identity": metadata["subject"],
        "archive": {
            "path": os.fspath(archive_before.path),
            "size": archive_before.identity.size,
            "sha256_before": archive_before.sha256,
            "sha256_after": archive_after.sha256,
            "advertised_github_asset": asset["github_asset"],
            "preflight_decompressed_stream_bytes": preflight_stream_bytes,
            "extraction_decompressed_stream_bytes": extraction_stream_bytes,
        },
        "safe_preflight": {
            "inventory": inventory,
            "single_expected_root": expected_archive["root"],
            "normalized_unique_paths": True,
            "portable_casefold_unique_paths": True,
            "only_directories_and_regular_files": True,
            "links_devices_fifos_sockets_rejected": True,
            "parent_topology_complete": True,
            "resource_limits": limits,
        },
        "canonical_tree_manifest": {
            "algorithm": "sha256",
            "format": MANIFEST_FORMAT,
            "sha256": manifest,
            "pre_post_equal": True,
        },
        "executable_leaves": leaves,
        "live_probes": probes,
        "execution_route": {
            "absolute_extracted_leaf_launch": True,
            "child_path_selects_exact_leaves_pre_and_post": True,
            "isolated_process_group_cleanup_after_every_child_outcome": True,
            "isolated_process_group_cleanup_signal_policy": ["TERM", "KILL"],
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log": True,
            "process_group_cleanup_bounds_milliseconds": {
                "term_grace": PROCESS_GROUP_TERM_GRACE_MILLISECONDS,
                "kill_grace": PROCESS_GROUP_KILL_GRACE_MILLISECONDS,
                "absence_poll_interval": PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS,
                "direct_child_reap_timeout": DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS,
            },
            "isolated_process_group_absence_checked": True,
            "non_child_descendants_reaped_by_this_checker": False,
            "process_group_observation_atomic": False,
            "process_group_reuse_excluded": False,
            "descendant_group_or_session_changes_continuously_observed": False,
            "elan_invoked": False,
            "lean_sysroot_present": False,
            "environment_keys": ["HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"],
            "ambient_umask_independent_private_mode_enforcement": True,
            "private_directory_modes_after_creation": {
                "temporary_root": "0700",
                "extraction_destination": "0700",
                "child_home": "0700",
                "child_tmp": "0700",
                "archive_directories_before_final_archive_mode": "0700",
            },
            "zstd_launch_path": os.fspath(zstd.launch_path),
            "zstd_canonical_path": os.fspath(zstd.canonical_path),
            "zstd_sha256": zstd.sha256,
        },
        "nested_kernel_regression": nested_kernel_regression,
        "authentication_boundary": metadata["authentication_boundary"],
        "credit_boundary": credit_boundary,
    }
    if state == "hosted_pending":
        result = {
            **result,
            "candidate_receipt": {
                "promotion_status": "not_qualified_same_run",
                "inventory": inventory,
                "tree_manifest": result["canonical_tree_manifest"],
                "leaves": leaves,
                "probes": probes,
                "required_next_step": lifecycle["required_next_step"],
            },
        }
    else:
        result = {
            **result,
            "strict_replay_receipt": {
                "execution_outcome": "all_strict_checks_passed",
                "immutable_publication_state": "not_yet_published",
                "nested_same_extraction_transaction": True,
                "required_next_step": (
                    "publish_result_bytes_without_changing_bound_packet"
                ),
                "reviewed_pins_equal_fresh_strict_replay": True,
                "same_run_metadata_promotion_allowed": False,
                "strict_archive_custody_credit": (
                    "none_until_exact_result_is_immutably_published"
                ),
                "tree_pre_post_equal": True,
            },
        }
    return result


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform", required=True, choices=tuple(EXPECTED_ASSET_IDENTITIES)
    )
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument(
        "--zstd",
        type=Path,
        help="absolute zstd executable; otherwise enumerated system paths are tried",
    )
    parser.add_argument(
        "--observation-only",
        action="store_true",
        help="emit a non-qualifying candidate receipt only for a hosted_pending platform",
    )
    return parser.parse_args(argv)


def cli_failure_line(error: BaseException) -> str:
    """Return the exact line written by the production CLI failure route."""

    return f"{CLI_FAILURE_PREFIX}{error}\n"


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_arguments(sys.argv[1:] if argv is None else argv)
        require(args.archive.is_absolute(), "--archive must be an absolute path")
        (
            source_snapshot,
            metadata_snapshot,
            nested_checker_snapshot,
            historical_receipt_snapshot,
            legacy_raw_snapshot,
            legacy_receipt_snapshot,
            metadata,
            assets,
        ) = load_policy()
        result = qualify(
            assets[args.platform],
            Path(os.path.abspath(os.fspath(args.archive))),
            args.zstd,
            args.observation_only,
            source_snapshot,
            metadata_snapshot,
            nested_checker_snapshot,
            historical_receipt_snapshot,
            legacy_raw_snapshot,
            legacy_receipt_snapshot,
            metadata,
        )
        print(
            json.dumps(
                result,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
        return 0
    except (CustodyError, OSError, UnicodeError, ValueError, tarfile.TarError) as error:
        sys.stderr.write(cli_failure_line(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
