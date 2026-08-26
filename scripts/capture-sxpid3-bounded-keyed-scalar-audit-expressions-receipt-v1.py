#!/usr/bin/env python3
"""Create the fixed no-clobber bounded SxPID3 audit-expression receipt.

This command is intentionally usable only at the reviewed source commit S.  It binds the exact
source package and ten execution inputs, runs six lanes in normal and optimized CPython, checks the
closed finite findings, and exclusively creates one untracked receipt.  A later receipt-only commit
E is required before the receipt becomes preserved evidence.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Final

if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.no_site == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: capture requires CPython 3.11+ started with -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
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
COMMAND_TIMEOUT_SECONDS: Final[int] = 7_200
TOOL_TIMEOUT_SECONDS: Final[int] = 60
STDOUT_CAP_BYTES: Final[int] = 4 * 1024 * 1024
STDERR_CAP_BYTES: Final[int] = 1024 * 1024
TOOL_OUTPUT_CAP_BYTES: Final[int] = 32 * 1024 * 1024
MINIMUM_GIT_VERSION: Final[tuple[int, int, int]] = (2, 41, 0)

SOURCE_DELTA: Final[dict[str, tuple[str, str]]] = {
    ".github/workflows/sxpid3-bounded-keyed-scalar-audit-expressions.yml": (
        "A",
        "100644",
    ),
    "CHANGELOG.md": ("M", "100644"),
    SCHEMA_RELATIVE: ("A", "100644"),
    GENERATOR_RELATIVE: ("A", "100755"),
    (
        "scripts/capture-sxpid3-bounded-keyed-scalar-audit-expressions-"
        "receipt-v1-self-test.py"
    ): ("A", "100755"),
    (
        "scripts/check-sxpid3-bounded-keyed-scalar-audit-expressions-"
        "receipt-v1.py"
    ): ("A", "100755"),
    (
        "scripts/check-sxpid3-bounded-keyed-scalar-audit-expressions-"
        "receipt-v1-self-test.py"
    ): ("A", "100755"),
}

INPUT_ROLES: Final[dict[str, str]] = {
    SCHEMA_RELATIVE: "closed_receipt_schema",
    GENERATOR_RELATIVE: "no_clobber_receipt_generator",
    "crates/pid-core/src/discrete_pid.rs": "three_source_antichain_and_mobius_source",
    "crates/pid-core/src/sxpid.rs": "fixed_three_source_lexical_route_source",
    "scripts/check-sxpid3-all108-independent.py": "independent_exact_lane",
    (
        "scripts/check-sxpid3-all108-independent-self-test.py"
    ): "independent_exact_lane_self_test",
    "scripts/check-sxpid3-bounded-full-coordinates.py": "primary_exact_lane",
    (
        "scripts/check-sxpid3-bounded-full-coordinates-self-test.py"
    ): "primary_exact_lane_self_test",
    "scripts/check-sxpid3-p5-rust-source-route.py": "lexical_rust_route_lane",
    (
        "scripts/check-sxpid3-p5-rust-source-route-self-test.py"
    ): "lexical_rust_route_lane_self_test",
}

P1_PATHS: Final[tuple[str, ...]] = (
    ".github/workflows/sxpid3-informative-invariance.yml",
    "audit/formal/lean-sxpid3-informative-invariance/AGENTS.md",
    (
        "audit/formal/lean-sxpid3-informative-invariance/"
        "PidSxPid3InformativeInvariance.lean"
    ),
    "crates/pid-core/tests/sxpid_informative_invariance.rs",
    "justfile.sxpid3-informative-invariance",
    "scripts/check-lean-sxpid3-informative-invariance-parity.py",
    "scripts/check-lean-sxpid3-informative-invariance-self-test.py",
    "scripts/check-lean-sxpid3-informative-invariance.py",
    "scripts/check-sxpid3-informative-invariance-self-test.py",
    "scripts/check-sxpid3-informative-invariance.py",
)

COMMAND_ROSTER: Final[tuple[tuple[str, str, str, int], ...]] = (
    (
        "primary_checker",
        "scripts/check-sxpid3-bounded-full-coordinates.py",
        "69e0844fccff4b28b34bcc9f9f8b8edc04a73a14fbfcced1fdd2edd27da6498f",
        12_237,
    ),
    (
        "primary_self_test",
        "scripts/check-sxpid3-bounded-full-coordinates-self-test.py",
        "971aaca8d31230b775f69d0f5f1e91e5f9ef9579dc853cff1b6d1c845dfa7e10",
        1_106,
    ),
    (
        "independent_checker",
        "scripts/check-sxpid3-all108-independent.py",
        "63e1470075f7fca88e9a8d82d52cdfcb56d389b4b3c7ac4d5ccba5071d6c2212",
        16_808,
    ),
    (
        "independent_self_test",
        "scripts/check-sxpid3-all108-independent-self-test.py",
        "1ee40d697aebd1b6d01ad5781ab46ad7a5265a50f1918cff67cda5e08775d8ae",
        2_788,
    ),
    (
        "rust_source_route_checker",
        "scripts/check-sxpid3-p5-rust-source-route.py",
        "a8cdab4307bf3bc46b03ad6487282a5ab4f0768959d1370f008860de978f22d0",
        11_054,
    ),
    (
        "rust_source_route_self_test",
        "scripts/check-sxpid3-p5-rust-source-route-self-test.py",
        "67ad8be5b31bb93a0c64df8a6a3cf91a8a0a669d82b73d8556b98060a93f0487",
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


class ReceiptError(RuntimeError):
    """A bounded source, process, schema, or no-clobber obligation failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptError(message)


class SchemaDefinitionError(ReceiptError):
    """The checked-in closed schema uses malformed or unsupported semantics."""


class InstanceValidationError(ReceiptError):
    """A receipt does not satisfy the supported closed schema."""


class FinalizedDescriptorReleaseError(ReceiptError):
    """Verified finalized bytes remain, but one or more descriptor closes failed."""


SCHEMA_ANNOTATIONS: Final[set[str]] = {
    "$id",
    "$schema",
    "$defs",
    "description",
    "title",
}
SCHEMA_ASSERTIONS: Final[set[str]] = {
    "$ref",
    "additionalProperties",
    "const",
    "enum",
    "items",
    "maxItems",
    "minimum",
    "minItems",
    "minLength",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "type",
    "uniqueItems",
}
SCHEMA_TYPES: Final[set[str]] = {
    "array",
    "boolean",
    "integer",
    "null",
    "object",
    "string",
}


def json_token(value: Any, error_type: type[ReceiptError]) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise error_type("value is not finite JSON data") from error


def schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "array": isinstance(value, list),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "object": isinstance(value, dict),
        "string": isinstance(value, str),
    }.get(expected, False)


def resolve_schema_pointer(root: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise SchemaDefinitionError("only local JSON Schema references are supported")
    value: Any = root
    for raw in reference[2:].split("/"):
        if re.search(r"~(?:[^01]|$)", raw) is not None:
            raise SchemaDefinitionError("JSON Schema reference has a malformed escape")
        component = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or component not in value:
            raise SchemaDefinitionError("JSON Schema reference is unresolved")
        value = value[component]
    return value


def validate_schema_definition(schema: Any) -> None:
    if not isinstance(schema, dict):
        raise SchemaDefinitionError("schema root is not an object")
    active: set[int] = set()
    complete: set[int] = set()

    def visit(rule: Any) -> None:
        if not isinstance(rule, dict):
            raise SchemaDefinitionError("schema node is not an object")
        identity = id(rule)
        if identity in complete:
            return
        if identity in active:
            raise SchemaDefinitionError("recursive JSON Schema references are unsupported")
        active.add(identity)
        try:
            unknown = set(rule) - SCHEMA_ANNOTATIONS - SCHEMA_ASSERTIONS
            if unknown:
                raise SchemaDefinitionError(
                    f"unsupported JSON Schema keyword(s): {', '.join(sorted(unknown))}"
                )
            definitions = rule.get("$defs")
            if definitions is not None:
                if not isinstance(definitions, dict) or any(
                    not isinstance(key, str) for key in definitions
                ):
                    raise SchemaDefinitionError("schema $defs is malformed")
                for child in definitions.values():
                    visit(child)
            if "$ref" in rule:
                reference = rule["$ref"]
                if not isinstance(reference, str):
                    raise SchemaDefinitionError("schema $ref is not a string")
                if set(rule) - SCHEMA_ANNOTATIONS - {"$ref"}:
                    raise SchemaDefinitionError("assertion siblings beside $ref are unsupported")
                visit(resolve_schema_pointer(schema, reference))
            if "type" in rule:
                declared = rule["type"]
                accepted = [declared] if isinstance(declared, str) else declared
                if (
                    not isinstance(accepted, list)
                    or not accepted
                    or any(not isinstance(item, str) for item in accepted)
                    or len(accepted) != len(set(accepted))
                    or any(item not in SCHEMA_TYPES for item in accepted)
                ):
                    raise SchemaDefinitionError("schema type declaration is malformed")
            for keyword in ("minItems", "maxItems", "minLength"):
                if keyword in rule and (
                    not isinstance(rule[keyword], int)
                    or isinstance(rule[keyword], bool)
                    or rule[keyword] < 0
                ):
                    raise SchemaDefinitionError(f"schema {keyword} is malformed")
            if rule.get("minItems", 0) > rule.get("maxItems", sys.maxsize):
                raise SchemaDefinitionError("schema minItems exceeds maxItems")
            if "minimum" in rule and (
                not isinstance(rule["minimum"], int)
                or isinstance(rule["minimum"], bool)
            ):
                raise SchemaDefinitionError("schema minimum is malformed")
            if "pattern" in rule:
                try:
                    re.compile(rule["pattern"])
                except (TypeError, re.error) as error:
                    raise SchemaDefinitionError("schema pattern is malformed") from error
            if "enum" in rule:
                choices = rule["enum"]
                if not isinstance(choices, list) or not choices:
                    raise SchemaDefinitionError("schema enum is malformed")
                tokens = [json_token(choice, SchemaDefinitionError) for choice in choices]
                if len(tokens) != len(set(tokens)):
                    raise SchemaDefinitionError("schema enum is not unique")
            if "const" in rule:
                json_token(rule["const"], SchemaDefinitionError)
            required = rule.get("required")
            if required is not None and (
                not isinstance(required, list)
                or any(not isinstance(item, str) for item in required)
                or len(required) != len(set(required))
            ):
                raise SchemaDefinitionError("schema required list is malformed")
            properties = rule.get("properties")
            if properties is not None:
                if not isinstance(properties, dict) or any(
                    not isinstance(key, str) for key in properties
                ):
                    raise SchemaDefinitionError("schema properties object is malformed")
                for child in properties.values():
                    visit(child)
            additional = rule.get("additionalProperties")
            if additional is not None and not isinstance(additional, (bool, dict)):
                raise SchemaDefinitionError("schema additionalProperties is malformed")
            if isinstance(additional, dict):
                visit(additional)
            items = rule.get("items")
            if items is not None:
                visit(items)
            variants = rule.get("oneOf")
            if variants is not None:
                if not isinstance(variants, list) or not variants:
                    raise SchemaDefinitionError("schema oneOf is malformed")
                for child in variants:
                    visit(child)
            if "uniqueItems" in rule and not isinstance(rule["uniqueItems"], bool):
                raise SchemaDefinitionError("schema uniqueItems is malformed")
            declared_type = rule.get("type")
            declared_types = (
                [declared_type]
                if isinstance(declared_type, str)
                else declared_type or []
            )
            if "object" in declared_types:
                if (
                    not isinstance(properties, dict)
                    or additional is not False
                    or not isinstance(required, list)
                    or set(required) != set(properties)
                ):
                    raise SchemaDefinitionError(
                        "object schemas must be closed and require every declared property"
                    )
            if "array" in declared_types and items is None:
                raise SchemaDefinitionError("array schemas must declare items")
        finally:
            active.remove(identity)
        complete.add(identity)

    visit(schema)


def validate_schema(instance: Any, schema: Any, *, name: str = "instance") -> None:
    validate_schema_definition(schema)
    if not isinstance(schema, dict):
        raise SchemaDefinitionError("schema root is not an object")

    def visit(value: Any, rule: dict[str, Any], path: str) -> None:
        if "$ref" in rule:
            visit(value, resolve_schema_pointer(schema, rule["$ref"]), path)
            return
        if "oneOf" in rule:
            matches = 0
            for variant in rule["oneOf"]:
                try:
                    visit(value, variant, path)
                except InstanceValidationError:
                    continue
                matches += 1
            if matches != 1:
                raise InstanceValidationError(f"{path}: oneOf match count is {matches}")
        if "type" in rule:
            declared = rule["type"]
            accepted = [declared] if isinstance(declared, str) else declared
            if not any(schema_type_matches(value, expected) for expected in accepted):
                raise InstanceValidationError(f"{path}: type differs")
        if "const" in rule and json_token(value, InstanceValidationError) != json_token(
            rule["const"], SchemaDefinitionError
        ):
            raise InstanceValidationError(f"{path}: const differs")
        if "enum" in rule:
            token = json_token(value, InstanceValidationError)
            if token not in {
                json_token(choice, SchemaDefinitionError) for choice in rule["enum"]
            }:
                raise InstanceValidationError(f"{path}: value is outside enum")
        if (
            "minimum" in rule
            and schema_type_matches(value, "number")
            and value < rule["minimum"]
        ):
            raise InstanceValidationError(f"{path}: value is below minimum")
        if isinstance(value, dict):
            missing = set(rule.get("required", [])) - set(value)
            if missing:
                raise InstanceValidationError(f"{path}: required keys are absent")
            properties = rule.get("properties", {})
            for key, child in value.items():
                if key in properties:
                    visit(child, properties[key], f"{path}.{key}")
                elif rule.get("additionalProperties") is False:
                    raise InstanceValidationError(f"{path}: additional property {key}")
                elif isinstance(rule.get("additionalProperties"), dict):
                    visit(child, rule["additionalProperties"], f"{path}.{key}")
        if isinstance(value, list):
            if len(value) < rule.get("minItems", 0):
                raise InstanceValidationError(f"{path}: fewer than minItems")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                raise InstanceValidationError(f"{path}: more than maxItems")
            if rule.get("uniqueItems") is True:
                tokens = [json_token(item, InstanceValidationError) for item in value]
                if len(tokens) != len(set(tokens)):
                    raise InstanceValidationError(f"{path}: duplicate array item")
            if "items" in rule:
                for index, child in enumerate(value):
                    visit(child, rule["items"], f"{path}[{index}]")
        if isinstance(value, str):
            if len(value) < rule.get("minLength", 0):
                raise InstanceValidationError(f"{path}: string is too short")
            if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
                raise InstanceValidationError(f"{path}: string pattern differs")

    visit(instance, schema, name)


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
                raise ReceiptError(f"duplicate JSON key in {label}: {key}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> Any:
        raise ReceiptError(f"non-finite JSON constant in {label}: {token}")

    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReceiptError(f"invalid JSON from {label}") from error


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


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


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    grace_deadline = time.monotonic() + 1.0
    while time.monotonic() < grace_deadline:
        if process_group_state(process.pid) == "absent":
            break
        time.sleep(0.02)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    if process.poll() is None:
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired as error:
            raise ReceiptError("process-group leader survived SIGKILL") from error
    if process_group_state(process.pid) != "absent":
        raise ReceiptError("process-group absence could not be established after cleanup")


def process_group_state(process_group_id: int) -> str:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "unknown_permission"
    return "present"


def read_process_pipe(descriptor: int, size: int) -> bytes:
    """A narrow seam for hostile pipe-read cleanup tests."""

    return os.read(descriptor, size)


def run_capped(
    argv: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    stdout_cap: int,
    stderr_cap: int,
    stdin_bytes: bytes | None = None,
    environment: dict[str, str] | None = None,
) -> tuple[int, bytes, bytes, bool]:
    """Run one new-session process while bounding time and retained pipe bytes."""

    require(
        stdin_bytes is None or len(stdin_bytes) <= TOOL_OUTPUT_CAP_BYTES,
        "child stdin exceeded its explicit byte cap",
    )
    process: subprocess.Popen[bytes] | None = None
    selector: selectors.BaseSelector | None = None
    stdin_stream: Any = None
    stdout_stream: Any = None
    stderr_stream: Any = None
    buffers: dict[int, bytearray] = {}
    caps: dict[int, int] = {}
    stdout_fd = -1
    stderr_fd = -1
    try:
        if stdin_bytes is not None:
            stdin_stream = tempfile.TemporaryFile(mode="w+b")
            written = stdin_stream.write(stdin_bytes)
            require(written == len(stdin_bytes), "short child-stdin staging write")
            stdin_stream.flush()
            stdin_stream.seek(0)
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=clean_environment() if environment is None else environment,
            stdin=stdin_stream if stdin_stream is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            close_fds=True,
            start_new_session=True,
        )
        stdout_stream = process.stdout
        stderr_stream = process.stderr
        require(
            stdout_stream is not None and stderr_stream is not None,
            "pipe setup failed",
        )
        selector = selectors.DefaultSelector()
        for stream, cap in ((stdout_stream, stdout_cap), (stderr_stream, stderr_cap)):
            descriptor = stream.fileno()
            os.set_blocking(descriptor, False)
            selector.register(descriptor, selectors.EVENT_READ)
            buffers[descriptor] = bytearray()
            caps[descriptor] = cap
        stdout_fd = stdout_stream.fileno()
        stderr_fd = stderr_stream.fileno()
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        while selector.get_map():
            if process.poll() is not None and process_group_state(process.pid) != "absent":
                terminate_process_group(process)
                raise ReceiptError(
                    "residual process-group member survived parent exit"
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                terminate_process_group(process)
                break
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                events = [
                    (key, selectors.EVENT_READ) for key in selector.get_map().values()
                ]
            for key, _mask in events:
                descriptor = key.fd
                try:
                    chunk = read_process_pipe(descriptor, 65_536)
                except BlockingIOError:
                    continue
                if chunk == b"":
                    selector.unregister(descriptor)
                    continue
                if len(buffers[descriptor]) + len(chunk) > caps[descriptor]:
                    terminate_process_group(process)
                    raise ReceiptError("child output exceeded its explicit byte cap")
                buffers[descriptor].extend(chunk)
        if timed_out:
            return process.returncode or -1, bytes(buffers[stdout_fd]), bytes(
                buffers[stderr_fd]
            ), True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            terminate_process_group(process)
            return process.returncode or -1, bytes(buffers[stdout_fd]), bytes(
                buffers[stderr_fd]
            ), True
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            terminate_process_group(process)
            return process.returncode or -1, bytes(buffers[stdout_fd]), bytes(
                buffers[stderr_fd]
            ), True
        if process_group_state(process.pid) != "absent":
            terminate_process_group(process)
            raise ReceiptError("residual process-group member survived nominal child exit")
        return returncode, bytes(buffers[stdout_fd]), bytes(buffers[stderr_fd]), False
    finally:
        active_error = sys.exc_info()[1]
        cleanup_error: BaseException | None = None
        if process is not None:
            try:
                state = process_group_state(process.pid)
                if process.poll() is None or state != "absent":
                    terminate_process_group(process)
            except BaseException as error:
                cleanup_error = error
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                cleanup_error = cleanup_error or error
        for stream in (stdout_stream, stderr_stream, stdin_stream):
            if stream is not None:
                try:
                    stream.close()
                except BaseException as error:
                    cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            if active_error is not None:
                active_error.add_note(f"process cleanup also failed: {cleanup_error}")
            else:
                raise cleanup_error


def git_executable() -> Path:
    found = shutil.which("git", path=clean_environment()["PATH"])
    require(found is not None, "git executable is absent")
    return Path(found).resolve()


def bootstrap_head_oid() -> str:
    """Resolve HEAD without an attribute-sensitive Git operation."""

    status, stdout, stderr, timed_out = run_capped(
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
        stderr_cap=STDERR_CAP_BYTES,
        environment=clean_environment(attribute_source=None),
    )
    require(
        status == 0
        and not timed_out
        and stderr == b""
        and re.fullmatch(rb"[0-9a-f]{40}\n", stdout) is not None,
        "exact HEAD bootstrap failed closed",
    )
    return stdout[:-1].decode("ascii")


def git_result(
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
    status, stdout, stderr, timed_out = run_capped(
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
        stderr_cap=STDERR_CAP_BYTES,
        stdin_bytes=stdin_bytes,
        environment=clean_environment(attribute_source=exact_attribute_source),
    )
    require(not timed_out, "git command timed out")
    return status, stdout, stderr


def git_bytes(
    arguments: list[str],
    *,
    stdin_bytes: bytes | None = None,
    attribute_source: str | None = None,
    pin_attributes: bool = True,
) -> bytes:
    status, stdout, stderr = git_result(
        arguments,
        stdin_bytes=stdin_bytes,
        attribute_source=attribute_source,
        pin_attributes=pin_attributes,
    )
    require(
        status == 0 and stderr == b"",
        f"git command failed closed: {' '.join(arguments[:2])}",
    )
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
    """Reject any tracked-path clean-filter route before invoking Git status."""

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
            raw_directory = Path(
                git_bytes(
                    ["rev-parse", selector], attribute_source=head_oid
                )[:-1].decode("ascii", errors="strict")
            )
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
            require(
                attribute != b"filter",
                f"a requested path declares the filter attribute in {label}",
            )

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
    index_rows = git_bytes(
        ["ls-files", "-v", "-z"], attribute_source=head_oid
    )
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
    require(
        stage_paths == index_paths,
        "tracked stage and index path rosters differ",
    )


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


def require_status(observed: bytes, expected: bytes, label: str) -> None:
    require(observed == expected, f"unexpected repository status at {label}")


def safe_read_regular(path: Path, *, mode: int, cap: int) -> bytes:
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == mode
        and 0 < before.st_size <= cap,
        f"regular-file metadata rejected: {path.name}",
    )
    flags = os.O_RDONLY | os.O_CLOEXEC
    require(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW is unavailable")
    flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
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
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
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
    require(
        raw_path.decode("utf-8", errors="strict") == relative and object_type == "blob",
        "ls-tree path or type drifted",
    )
    blob = git_bytes(["cat-file", "blob", oid])
    return mode, oid, blob


def parse_name_status(raw: bytes) -> list[tuple[str, str]]:
    require(raw.endswith(b"\0"), "diff-tree output lacks NUL framing")
    tokens = raw[:-1].split(b"\0") if raw else []
    require(len(tokens) % 2 == 0, "diff-tree status/path framing drifted")
    result: list[tuple[str, str]] = []
    for index in range(0, len(tokens), 2):
        result.append(
            (
                tokens[index].decode("ascii", errors="strict"),
                tokens[index + 1].decode("utf-8", errors="strict"),
            )
        )
    return result


def canonical_repository() -> None:
    exact_head = bootstrap_head_oid()
    require_supported_git_version(exact_head)
    top = Path(git_line(["rev-parse", "--show-toplevel"])).resolve()
    require(top == ROOT, "capture is not running at the canonical repository root")
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
        require(
            stat.S_ISDIR(metadata.st_mode) and not directory.is_symlink(),
            "canonical Git metadata directory is not a real directory",
        )
        require(
            not os.path.lexists(directory / "info" / "grafts"),
            "Git graft state is unsupported",
        )
        require(
            not os.path.lexists(directory / "info" / "sparse-checkout"),
            "Git sparse-checkout state is unsupported",
        )
        require(
            not os.path.lexists(directory / "info" / "attributes"),
            "Git info/attributes state is unsupported",
        )
    objects = common / "objects"
    for index, directory in enumerate((objects, objects / "info", objects / "pack")):
        if index > 0 and not os.path.lexists(directory):
            continue
        metadata = directory.lstat()
        require(
            stat.S_ISDIR(metadata.st_mode) and not directory.is_symlink(),
            "Git object storage directories must be real local directories",
        )
    for relative in (
        "objects/info/alternates",
        "objects/info/http-alternates",
    ):
        require(
            not os.path.lexists(common / relative),
            "Git object alternates are unsupported",
        )
    require(
        not any((common / "objects" / "pack").glob("*.promisor")),
        "promisor object packs are unsupported",
    )
    config_keys = git_bytes(
        ["config", "--no-includes", "--null", "--name-only", "--list"]
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
            key not in {
                "extensions.partialclone",
                "core.sparsecheckout",
                "core.sparsecheckoutcone",
            }
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
    require(
        git_line(["rev-parse", "--is-shallow-repository"]) == "false",
        "shallow Git history is unsupported",
    )
    require(git_line(["rev-parse", f"{BASE_COMMIT}^{{tree}}"] ) == BASE_TREE, "base tree drifted")
    require_status_attribute_closure(exact_head)
    require(
        bootstrap_head_oid() == exact_head,
        "HEAD changed across canonical repository validation",
    )


def source_package(source_commit: str, *, require_live: bool) -> dict[str, Any]:
    parent_line = git_line(["rev-list", "--parents", "-n", "1", source_commit]).split()
    require(parent_line == [source_commit, BASE_COMMIT], "source commit is not the required direct child")
    source_tree = git_line(["rev-parse", f"{source_commit}^{{tree}}"])
    observed_delta = parse_name_status(
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
    expected_delta = sorted((status, path) for path, (status, _mode) in SOURCE_DELTA.items())
    require(sorted(observed_delta) == expected_delta, "source commit delta roster drifted")
    entries: list[dict[str, Any]] = []
    for relative in sorted(SOURCE_DELTA):
        expected_status, expected_mode = SOURCE_DELTA[relative]
        base_entry = ls_tree_entry(BASE_COMMIT, relative)
        source_entry = ls_tree_entry(source_commit, relative)
        require(source_entry is not None, f"source package path is absent: {relative}")
        source_mode, source_oid, source_blob = source_entry
        require(source_mode == expected_mode, f"source package mode drifted: {relative}")
        if expected_status == "A":
            require(base_entry is None, f"added source path already existed: {relative}")
            base_mode: str | None = None
        else:
            require(base_entry is not None, f"modified source path lacked a base blob: {relative}")
            base_mode = base_entry[0]
            require(base_mode == expected_mode and base_entry[1] != source_oid, "modified source path did not change exactly")
        if require_live:
            live_mode = 0o755 if source_mode == "100755" else 0o644
            live_blob = safe_read_regular(ROOT / relative, mode=live_mode, cap=32 * 1024 * 1024)
            require(live_blob == source_blob, f"live source package bytes drifted: {relative}")
        entries.append(
            {
                "path": relative,
                "status": expected_status,
                "base_mode": base_mode,
                "source_mode": source_mode,
                "source_blob_oid": source_oid,
                "source_sha256": sha256_bytes(source_blob),
                "source_bytes": len(source_blob),
            }
        )
    require(
        git_bytes(["ls-tree", "-z", source_commit, "--", RECEIPT_RELATIVE]) == b"",
        "receipt unexpectedly exists in the source commit",
    )
    return {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "sole_parent": BASE_COMMIT,
        "base_tree": BASE_TREE,
        "direct_child_of_required_base": True,
        "source_delta": entries,
        "receipt_path": RECEIPT_RELATIVE,
        "receipt_absent_from_source_commit": True,
    }


def execution_input(relative: str, role: str, source_commit: str) -> dict[str, Any]:
    entry = ls_tree_entry(source_commit, relative)
    require(entry is not None, f"execution input is absent: {relative}")
    git_mode, oid, blob = entry
    require(git_mode in {"100644", "100755"}, f"execution input mode rejected: {relative}")
    live_mode = 0o755 if git_mode == "100755" else 0o644
    live = safe_read_regular(ROOT / relative, mode=live_mode, cap=32 * 1024 * 1024)
    require(live == blob, f"execution input differs from source blob: {relative}")
    return {
        "path": relative,
        "role": role,
        "source_blob_oid": oid,
        "git_mode": git_mode,
        "live_mode": f"0{live_mode:o}",
        "byte_count": len(blob),
        "sha256": sha256_bytes(blob),
        "source_blob_matches_live_file": True,
    }


def execution_inputs(source_commit: str) -> list[dict[str, Any]]:
    return [
        execution_input(relative, INPUT_ROLES[relative], source_commit)
        for relative in sorted(INPUT_ROLES)
    ]


def p1_binding(source_commit: str) -> dict[str, Any]:
    require(
        git_line(["rev-list", "--parents", "-n", "1", BASE_COMMIT]).split()
        == [BASE_COMMIT, P1_COMMIT],
        "P1 is not the sole raw parent of the P5 core base commit",
    )
    status, stdout, stderr = git_result(["merge-base", "--is-ancestor", P1_COMMIT, source_commit])
    require(status == 0 and stdout == b"" and stderr == b"", "P1 baseline is not an ancestor")
    require(git_line(["rev-parse", f"{P1_COMMIT}^{{tree}}"] ) == P1_TREE, "P1 baseline tree drifted")
    paths: list[dict[str, Any]] = []
    for relative in P1_PATHS:
        baseline = ls_tree_entry(P1_COMMIT, relative)
        source = ls_tree_entry(source_commit, relative)
        require(baseline is not None and source is not None, f"P1 path is absent: {relative}")
        require(baseline == source, f"P1 path changed after its baseline: {relative}")
        mode, oid, blob = baseline
        paths.append(
            {
                "path": relative,
                "baseline_blob_oid": oid,
                "source_blob_oid": source[1],
                "git_mode": mode,
                "byte_count": len(blob),
                "sha256": sha256_bytes(blob),
                "unchanged_at_source": True,
            }
        )
    return {
        "baseline_commit": P1_COMMIT,
        "baseline_tree": P1_TREE,
        "adjacent_child_commit": BASE_COMMIT,
        "adjacent_child_has_p1_as_sole_parent": True,
        "baseline_is_ancestor_of_source": True,
        "path_count": len(paths),
        "paths": paths,
        "consumed": False,
        "replayed": False,
        "fresh_execution_credit": "none",
        "semantic_transfer": "none",
        "relationship": "adjacent_separate_lane_provenance_only",
    }


def tool_binding(path: Path, public_name: str, version: str) -> dict[str, Any]:
    resolved = path.resolve()
    raw = safe_read_regular(
        resolved,
        mode=stat.S_IMODE(resolved.stat().st_mode),
        cap=256 * 1024 * 1024,
    )
    return {
        "public_name": public_name,
        "version": version,
        "executable_sha256": sha256_bytes(raw),
        "executable_bytes": len(raw),
    }


def host_boundary() -> dict[str, Any]:
    git_version = git_line(["--version"])
    python_version = (
        f"CPython {sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )
    return {
        "python": tool_binding(Path(sys.executable), "$PYTHON", python_version),
        "git": tool_binding(git_executable(), "$GIT", git_version),
        "required_python_flags": ["-I", "-S", "-B"],
        "python_optimize": 0,
        "observation_class": "bounded_local_execution_environment_observation_not_attestation",
    }


def run_lane(
    base_id: str,
    relative: str,
    expected_stdout_sha256: str,
    expected_stdout_bytes: int,
    mode: str,
    input_by_path: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    require(mode in {"normal", "optimized"}, "unknown Python execution mode")
    actual_argv = [os.fspath(Path(sys.executable).resolve())]
    public_argv = ["$PYTHON"]
    if mode == "optimized":
        actual_argv.append("-O")
        public_argv.append("-O")
    actual_argv.extend(["-I", "-S", "-B", os.fspath(ROOT / relative)])
    public_argv.extend(["-I", "-S", "-B", f"$REPOSITORY/{relative}"])
    status, stdout, stderr, timed_out = run_capped(
        actual_argv,
        cwd=ROOT,
        timeout_seconds=COMMAND_TIMEOUT_SECONDS,
        stdout_cap=STDOUT_CAP_BYTES,
        stderr_cap=STDERR_CAP_BYTES,
    )
    require(not timed_out, f"{base_id} timed out")
    require(status == 0, f"{base_id} returned a nonzero status")
    require(stderr == b"", f"{base_id} emitted stderr")
    require(stdout != b"", f"{base_id} emitted empty stdout")
    require(
        len(stdout) == expected_stdout_bytes
        and sha256_bytes(stdout) == expected_stdout_sha256,
        f"{base_id} stdout byte-count or digest pin drifted",
    )
    payload = strict_json(stdout, base_id)
    require(isinstance(payload, dict), f"{base_id} stdout root is not an object")
    stdout_format = payload.get("format", payload.get("schema"))
    require(isinstance(stdout_format, str) and stdout_format, f"{base_id} lacks a format token")
    input_binding = input_by_path[relative]
    command = {
        "id": f"{base_id}_{mode}",
        "entrypoint": relative,
        "mode": mode,
        "argv": public_argv,
        "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
        "stdout_cap_bytes": STDOUT_CAP_BYTES,
        "stderr_cap_bytes": STDERR_CAP_BYTES,
        "exit_status": status,
        "timed_out": False,
        "stdout_bytes": len(stdout),
        "stdout_sha256": sha256_bytes(stdout),
        "stdout_format": stdout_format,
        "stderr_bytes": 0,
        "stderr_sha256": EMPTY_SHA256,
        "entrypoint_source_sha256": input_binding["sha256"],
    }
    return command, payload, stdout


def require_no_common_session_escape_primitives(
    input_by_path: dict[str, dict[str, Any]], source_commit: str
) -> None:
    forbidden = (b"setsid", b"start_new_session", b"daemon", b"os.fork", b"fork(")
    for _base_id, relative, _stdout_sha256, _stdout_bytes in COMMAND_ROSTER:
        entry = ls_tree_entry(source_commit, relative)
        require(entry is not None, "entrypoint disappeared during escape audit")
        require(
            sha256_bytes(entry[2]) == input_by_path[relative]["sha256"]
            and all(token not in entry[2] for token in forbidden),
            f"common session-escape primitive found in entrypoint: {relative}",
        )


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


def verify_payloads(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    primary = payloads["primary_checker"]
    primary_self = payloads["primary_self_test"]
    independent = payloads["independent_checker"]
    independent_self = payloads["independent_self_test"]
    rust_route = payloads["rust_source_route_checker"]
    rust_self = payloads["rust_source_route_self_test"]
    require(primary.get("gate") == "GO", "primary lane did not pass")
    require(primary_self.get("gate") == "GO", "primary self-test did not pass")
    require(independent.get("status") == "GO", "independent lane did not pass")
    require(independent_self.get("status") == "GO", "independent self-test did not pass")
    require(rust_route.get("gate") == "GO", "lexical Rust route did not pass")
    require(rust_self.get("gate") == "GO", "lexical Rust self-test did not pass")
    require(
        primary_self.get("baseline_stdout_sha256") == COMMAND_ROSTER[0][2]
        and primary_self.get("process_mutation_count") == 36
        and primary_self.get("normal_optimized_parity") is True,
        "primary self-test summary drifted",
    )
    require(
        independent_self.get("full_run_stdout_sha256") == COMMAND_ROSTER[2][2]
        and independent_self.get("mutation_count") == 27
        and independent_self.get("full_run_normal_optimized_byte_identical") is True,
        "independent self-test summary drifted",
    )
    require(
        rust_self.get("baseline_stdout_sha256") == COMMAND_ROSTER[4][2]
        and rust_self.get("mutation_count") == 54
        and rust_self.get("fail_closed_normal_and_optimized") is True,
        "lexical Rust self-test summary drifted",
    )
    bounded = primary.get("bounded_exhaustive_scope")
    require(isinstance(bounded, dict), "primary bounded scope is absent")
    scope = independent.get("scope")
    require(isinstance(scope, dict), "independent bounded scope is absent")
    findings = expected_findings()
    domain = findings["domain"]
    require(
        bounded.get("binary_labeled_count_tables") == domain["labeled_binary_tables"]
        and bounded.get("tables_by_total") == domain["tables_by_total"]
        and bounded.get("primitive_rational_laws") == domain["primitive_rational_laws"]
        and bounded.get("nonprimitive_rescaled_count_vectors") == domain["nonprimitive_rescaled_count_vectors"]
        and bounded.get("full_support_16_cell_laws") == 0
        and bounded.get("maximum_positive_cells") == 5
        and bounded.get("averaged_keyed_scalar_audit_expression_product_verdicts") == domain["expression_evaluations"]
        and bounded.get("strictly_positive_exact_product_checks") == domain["strictly_positive_exact_products"]
        and bounded.get("pointwise_audit_expressions_evaluated") == 0,
        "primary finite-domain summary drifted",
    )
    require(
        scope.get("labeled_count_tables") == domain["labeled_binary_tables"]
        and scope.get("keyed_scalar_audit_expressions_per_table") == 108
        and scope.get("audit_expression_evaluations") == domain["expression_evaluations"],
        "independent finite-domain summary drifted",
    )
    primary_signs = bounded.get("bounded_sign_counts_by_audit_expression_block")
    require(primary_signs == SIGN_CENSUS, "primary sign census drifted")
    require(
        independent.get("bounded_sign_counts_by_audit_expression_block") == SIGN_CENSUS,
        "independent sign census drifted",
    )
    digests = findings["digests"]
    independent_digests = independent.get("digests")
    require(isinstance(independent_digests, dict), "independent digests are absent")
    require(
        bounded.get("neutral_cross_route_audit_expression_stream_sha256")
        == digests["route_neutral_v2_expression_stream_sha256"]
        == independent_digests.get("table_bound_all_expression_result_sha256"),
        "route-neutral v2 digest drifted",
    )
    require(
        bounded.get("route_native_result_stream_sha256") == digests["primary_route_native_stream_sha256"]
        and independent_digests.get("route_native_v1_result_sha256") == digests["independent_route_native_stream_sha256"]
        and bounded.get("corpus_stream_sha256") == digests["primary_corpus_stream_sha256"]
        and independent_digests.get("corpus_sha256") == digests["independent_corpus_stream_sha256"],
        "route-native or corpus digest drifted",
    )
    registry = primary.get("audit_expression_registry")
    require(
        isinstance(registry, dict)
        and registry.get("keyed_scalar_audit_expression_count") == 108
        and registry.get("sha256") == digests["primary_audit_registry_sha256"]
        and independent_digests.get("audit_expression_registry_sha256")
        == digests["independent_audit_registry_sha256"],
        "audit-expression registry drifted",
    )
    serialization = primary.get("serialization")
    require(
        isinstance(serialization, dict)
        and serialization.get("neutral_framing_unit_sha256")
        == digests["primary_neutral_v2_framing_unit_sha256"]
        and independent_digests.get("table_bound_framing_probe_sha256")
        == digests["independent_table_bound_framing_probe_sha256"],
        "route-specific framing pin drifted",
    )
    rust_context = rust_route.get("audit_expression_context")
    require(
        isinstance(rust_context, dict)
        and rust_context.get("expression_count") == 108
        and rust_context.get("numeric_rust_expressions_compared") == 0
        and len(rust_route.get("anchors", {})) == 21
        and rust_route.get("route_manifest_sha256")
        == digests["lexical_rust_route_manifest_sha256"]
        and rust_route.get("boundaries") == ROUTE_BOUNDARIES
        and rust_self.get("route_manifest_sha256")
        == digests["lexical_rust_route_manifest_sha256"],
        "lexical Rust route boundary drifted",
    )
    return findings


def reverify(
    expected_source: dict[str, Any],
    expected_inputs: list[dict[str, Any]],
    expected_p1: dict[str, Any],
    expected_host: dict[str, Any],
    expected_status: bytes,
) -> None:
    canonical_repository()
    source_commit = expected_source["source_commit"]
    require(git_line(["rev-parse", "HEAD"]) == source_commit, "HEAD changed during capture")
    require(
        git_line(["rev-parse", "HEAD^{tree}"]) == expected_source["source_tree"],
        "source tree changed during capture",
    )
    require_status(status_bytes(), expected_status, "bounded revalidation entry")
    require(source_package(source_commit, require_live=True) == expected_source, "source package changed")
    require(execution_inputs(source_commit) == expected_inputs, "execution inputs changed")
    require(p1_binding(source_commit) == expected_p1, "P1 adjacent lane changed")
    require(host_boundary() == expected_host, "host executable bytes or versions changed")
    canonical_repository()
    require(git_line(["rev-parse", "HEAD"]) == source_commit, "HEAD changed during capture")
    require(
        git_line(["rev-parse", "HEAD^{tree}"]) == expected_source["source_tree"],
        "source tree changed during capture",
    )
    require_status(status_bytes(), expected_status, "bounded revalidation exit")


def open_receipt_parent(path: Path) -> dict[str, Any]:
    require(
        hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"),
        "required no-follow directory-descriptor primitives are unavailable",
    )
    parent_before = path.parent.lstat()
    require(
        stat.S_ISDIR(parent_before.st_mode) and not path.parent.is_symlink(),
        "receipt parent is not a real directory",
    )
    leaf = path.name
    require(
        leaf not in {"", ".", ".."}
        and "/" not in leaf
        and os.sep not in leaf
        and path.parent / leaf == path,
        "receipt leaf name is invalid",
    )
    parent_fd = os.open(
        path.parent,
        os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        opened = os.fstat(parent_fd)
        require(
            (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink)
            == (
                parent_before.st_dev,
                parent_before.st_ino,
                parent_before.st_mode,
                parent_before.st_nlink,
            ),
            "receipt parent identity changed while opened",
        )
    except BaseException:
        os.close(parent_fd)
        raise
    return {
        "parent_fd": parent_fd,
        "parent_identity": (opened.st_dev, opened.st_ino, opened.st_mode),
        "parent_path": path.parent,
        "leaf": leaf,
        "file_identity": None,
        "file_fd": None,
    }


def require_receipt_parent_identity(custody: dict[str, Any]) -> None:
    opened = os.fstat(custody["parent_fd"])
    observed = custody["parent_path"].lstat()
    expected = custody["parent_identity"]
    require(
        (opened.st_dev, opened.st_ino, opened.st_mode) == expected
        and (observed.st_dev, observed.st_ino, observed.st_mode) == expected
        and stat.S_ISDIR(observed.st_mode)
        and not custody["parent_path"].is_symlink(),
        "receipt parent directory identity changed",
    )


def close_receipt_custody(custody: dict[str, Any]) -> None:
    file_descriptor = custody.get("file_fd")
    if isinstance(file_descriptor, int) and file_descriptor >= 0:
        os.close(file_descriptor)
        custody["file_fd"] = -1
    parent_descriptor = custody.get("parent_fd")
    if isinstance(parent_descriptor, int) and parent_descriptor >= 0:
        os.close(parent_descriptor)
        custody["parent_fd"] = -1


def release_finalized_receipt_custody(custody: dict[str, Any]) -> None:
    """Attempt each final close once; never tombstone after verified final bytes."""

    errors: list[BaseException] = []
    file_descriptor = custody.get("file_fd")
    custody["file_fd"] = -1
    if isinstance(file_descriptor, int) and file_descriptor >= 0:
        try:
            os.close(file_descriptor)
        except BaseException as error:
            errors.append(error)
    parent_descriptor = custody.get("parent_fd")
    custody["parent_fd"] = -1
    if isinstance(parent_descriptor, int) and parent_descriptor >= 0:
        try:
            os.close(parent_descriptor)
        except BaseException as error:
            errors.append(error)
    if errors:
        raise FinalizedDescriptorReleaseError(
            "verified finalized receipt bytes were retained but descriptor release failed; "
            "do not rerun capture, validate the retained file prospectively"
        ) from errors[0]


FAILED_RECEIPT_TOMBSTONE: Final[bytes] = b"INVALIDATED SXPID3 RECEIPT: WRITE OR POSTWRITE FAILURE\n"
PENDING_RECEIPT_TOMBSTONE: Final[bytes] = b"PENDING SXPID3 RECEIPT: PREFINALIZATION CHECKS INCOMPLETE\n"


def invalidate_failed_receipt(custody: dict[str, Any]) -> None:
    """Invalidate only the exact still-open inode; never compare-and-unlink a path."""

    descriptor = custody.get("file_fd")
    try:
        if isinstance(descriptor, int) and descriptor >= 0:
            opened = os.fstat(descriptor)
            require(
                (opened.st_dev, opened.st_ino) == custody.get("file_identity")
                and stat.S_ISREG(opened.st_mode),
                "retained receipt descriptor identity changed",
            )
            os.ftruncate(descriptor, 0)
            os.fchmod(descriptor, 0o600)
            secured = os.fstat(descriptor)
            require(
                (secured.st_dev, secured.st_ino) == custody.get("file_identity")
                and stat.S_ISREG(secured.st_mode)
                and stat.S_IMODE(secured.st_mode) == 0o600,
                "failed-receipt tombstone mode or identity drifted",
            )
            os.lseek(descriptor, 0, os.SEEK_SET)
            offset = 0
            while offset < len(FAILED_RECEIPT_TOMBSTONE):
                written = os.write(descriptor, FAILED_RECEIPT_TOMBSTONE[offset:])
                require(written > 0, "short failed-receipt tombstone write")
                offset += written
            os.fsync(descriptor)
            after = os.fstat(descriptor)
            require(
                (after.st_dev, after.st_ino) == custody.get("file_identity")
                and stat.S_ISREG(after.st_mode)
                and stat.S_IMODE(after.st_mode) == 0o600
                and after.st_nlink == secured.st_nlink
                and after.st_size == len(FAILED_RECEIPT_TOMBSTONE),
                "failed-receipt tombstone postwrite custody drifted",
            )
            os.lseek(descriptor, 0, os.SEEK_SET)
            chunks: list[bytes] = []
            remaining = len(FAILED_RECEIPT_TOMBSTONE)
            while remaining:
                chunk = os.read(descriptor, remaining)
                require(chunk != b"", "short failed-receipt tombstone reread")
                chunks.append(chunk)
                remaining -= len(chunk)
            require(
                os.read(descriptor, 1) == b""
                and b"".join(chunks) == FAILED_RECEIPT_TOMBSTONE,
                "failed-receipt tombstone exact-byte reread drifted",
            )
            reread = os.fstat(descriptor)
            require(
                (reread.st_dev, reread.st_ino, reread.st_mode, reread.st_nlink, reread.st_size)
                == (after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size),
                "failed-receipt tombstone changed during exact reread",
            )
        os.fsync(custody["parent_fd"])
    finally:
        close_receipt_custody(custody)


def rewrite_retained_receipt(custody: dict[str, Any], encoded: bytes) -> None:
    descriptor = custody.get("file_fd")
    require(isinstance(descriptor, int) and descriptor >= 0, "receipt descriptor is closed")
    opened = os.fstat(descriptor)
    require(
        (opened.st_dev, opened.st_ino) == custody.get("file_identity")
        and stat.S_ISREG(opened.st_mode)
        and opened.st_nlink == 1,
        "retained receipt descriptor metadata drifted",
    )
    os.ftruncate(descriptor, 0)
    os.lseek(descriptor, 0, os.SEEK_SET)
    offset = 0
    while offset < len(encoded):
        written = os.write(descriptor, encoded[offset:])
        require(written > 0, "short retained-receipt write")
        offset += written
    os.fsync(descriptor)
    after = os.fstat(descriptor)
    require(
        (after.st_dev, after.st_ino) == custody["file_identity"]
        and stat.S_ISREG(after.st_mode)
        and after.st_nlink == 1
        and stat.S_IMODE(after.st_mode) == 0o600
        and after.st_size == len(encoded),
        "retained receipt metadata changed during rewrite",
    )


def create_pending_receipt_exclusive(path: Path) -> dict[str, Any]:
    custody = open_receipt_parent(path)
    try:
        descriptor = os.open(
            custody["leaf"],
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=custody["parent_fd"],
        )
        custody["file_fd"] = descriptor
        opened = os.fstat(descriptor)
        custody["file_identity"] = (opened.st_dev, opened.st_ino)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, "created receipt metadata rejected")
        os.fchmod(descriptor, 0o600)
        secured = os.fstat(descriptor)
        require(
            (secured.st_dev, secured.st_ino) == custody["file_identity"]
            and stat.S_ISREG(secured.st_mode)
            and secured.st_nlink == 1
            and stat.S_IMODE(secured.st_mode) == 0o600,
            "created receipt mode did not stabilize at 0600",
        )
        rewrite_retained_receipt(custody, PENDING_RECEIPT_TOMBSTONE)
        os.fsync(custody["parent_fd"])
        require_receipt_parent_identity(custody)
    except BaseException:
        invalidate_failed_receipt(custody)
        raise
    require(custody["file_identity"] is not None, "receipt creation identity was not retained")
    return custody


def read_receipt_through_custody(
    custody: dict[str, Any], *, cap: int = 32 * 1024 * 1024
) -> bytes:
    require_receipt_parent_identity(custody)
    before = os.stat(
        custody["leaf"],
        dir_fd=custody["parent_fd"],
        follow_symlinks=False,
    )
    require(
        (before.st_dev, before.st_ino) == custody["file_identity"]
        and stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o600
        and 0 < before.st_size <= cap,
        "created receipt leaf metadata drifted",
    )
    descriptor = custody["file_fd"]
    require(isinstance(descriptor, int) and descriptor >= 0, "receipt descriptor is closed")
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
    require(
        all(getattr(opened, field) == getattr(before, field) for field in metadata_fields),
        "created receipt identity changed while retained",
    )
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = opened.st_size
    while remaining:
        chunk = os.read(descriptor, min(remaining, 1024 * 1024))
        require(chunk != b"", "short created-receipt read")
        chunks.append(chunk)
        remaining -= len(chunk)
    require(os.read(descriptor, 1) == b"", "created receipt grew while read")
    after_fd = os.fstat(descriptor)
    after = os.stat(
        custody["leaf"],
        dir_fd=custody["parent_fd"],
        follow_symlinks=False,
    )
    require(
        all(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field)
            for field in metadata_fields
        ),
        "created receipt changed during descriptor-relative read",
    )
    require_receipt_parent_identity(custody)
    raw = b"".join(chunks)
    require(len(raw) == opened.st_size, "created-receipt read length drifted")
    return raw


def require_receipt_leaf_identity(
    custody: dict[str, Any], *, expected_size: int
) -> None:
    """Check the retained descriptor and leaf path immediately before success-close."""

    require_receipt_parent_identity(custody)
    descriptor = custody.get("file_fd")
    require(isinstance(descriptor, int) and descriptor >= 0, "receipt descriptor is closed")
    opened = os.fstat(descriptor)
    observed = os.stat(
        custody["leaf"],
        dir_fd=custody["parent_fd"],
        follow_symlinks=False,
    )
    metadata_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    require(
        all(
            getattr(opened, field) == getattr(observed, field)
            for field in metadata_fields
        )
        and (opened.st_dev, opened.st_ino) == custody.get("file_identity")
        and stat.S_ISREG(opened.st_mode)
        and opened.st_nlink == 1
        and stat.S_IMODE(opened.st_mode) == 0o600
        and opened.st_size == expected_size,
        "final receipt leaf identity or metadata drifted",
    )


def build_and_write_receipt() -> tuple[str, str]:
    require(sys.flags.optimize == 0, "capture rejects optimized Python")
    canonical_repository()
    require_status(status_bytes(), b"", "initial source cut")
    require(
        not os.path.lexists(RECEIPT_PATH),
        "receipt path already exists before source selection",
    )
    source_commit = git_line(["rev-parse", "HEAD"])
    source = source_package(source_commit, require_live=True)
    inputs = execution_inputs(source_commit)
    adjacent = p1_binding(source_commit)
    host = host_boundary()
    input_by_path = {item["path"]: item for item in inputs}
    require_no_common_session_escape_primitives(input_by_path, source_commit)
    commands: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    paired_stdout: dict[str, dict[str, bytes]] = {}
    for base_id, relative, expected_hash, expected_bytes in COMMAND_ROSTER:
        paired_stdout[base_id] = {}
        for mode in ("normal", "optimized"):
            reverify(source, inputs, adjacent, host, b"")
            command, payload, stdout = run_lane(
                base_id,
                relative,
                expected_hash,
                expected_bytes,
                mode,
                input_by_path,
            )
            commands.append(command)
            reverify(source, inputs, adjacent, host, b"")
            paired_stdout[base_id][mode] = stdout
            if mode == "normal":
                payloads[base_id] = payload
        require(
            paired_stdout[base_id]["normal"] == paired_stdout[base_id]["optimized"],
            f"{base_id} normal and optimized stdout differ",
        )
    findings = verify_payloads(payloads)
    receipt = {
        "schema": "pid-rs/sxpid3-bounded-keyed-scalar-audit-expressions-receipt/v1",
        "schema_revision": 1,
        "result_id": RESULT_ID,
        "captured_at_utc": utc_now(),
        "source_package": source,
        "execution_inputs": inputs,
        "commands": commands,
        "findings": findings,
        "p1_adjacent_lane": adjacent,
        "validation": {
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
        },
        "nonclaims": NONCLAIMS,
        "host_boundary": host,
    }
    schema_raw = input_by_path[SCHEMA_RELATIVE]
    schema_blob = ls_tree_entry(source_commit, SCHEMA_RELATIVE)
    require(schema_blob is not None and sha256_bytes(schema_blob[2]) == schema_raw["sha256"], "schema binding drifted")
    schema = strict_json(schema_blob[2], "receipt schema")
    validate_schema(receipt, schema, name="prospective receipt")
    encoded = canonical_json(receipt)
    reverify(source, inputs, adjacent, host, b"")
    # This is deliberately the final clean-state observation before the pending leaf exists.
    require_status(status_bytes(), b"", "immediately before receipt write")
    created_custody = create_pending_receipt_exclusive(RECEIPT_PATH)
    try:
        expected_post_status = b"?? " + RECEIPT_RELATIVE.encode("utf-8") + b"\0"
        require_status(status_bytes(), expected_post_status, "after pending placeholder create")
        pending = read_receipt_through_custody(created_custody)
        require(
            pending == PENDING_RECEIPT_TOMBSTONE,
            "pending placeholder differs from the schema-invalid marker",
        )
        try:
            strict_json(pending, "pending placeholder")
        except ReceiptError:
            pass
        else:
            raise ReceiptError("pending placeholder unexpectedly parses as JSON")
        reverify(source, inputs, adjacent, host, expected_post_status)
        require_status(status_bytes(), expected_post_status, "immediately before finalization")
        rewrite_retained_receipt(created_custody, encoded)
        reread = read_receipt_through_custody(created_custody)
        require(reread == encoded, "final receipt reread differs from canonical bytes")
        reverify(source, inputs, adjacent, host, expected_post_status)
        require_status(status_bytes(), expected_post_status, "final runtime custody check")
        final_reread = read_receipt_through_custody(created_custody)
        require(
            final_reread == encoded,
            "final post-reverification receipt bytes differ from canonical bytes",
        )
        require_receipt_leaf_identity(created_custody, expected_size=len(encoded))
        os.fsync(created_custody["parent_fd"])
        require_receipt_parent_identity(created_custody)
    except BaseException:
        invalidate_failed_receipt(created_custody)
        raise
    release_finalized_receipt_custody(created_custody)
    return source_commit, sha256_bytes(encoded)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        required=True,
        help="exclusively create the one fixed receipt path",
    )
    return parser.parse_args()


def main() -> int:
    parse_arguments()
    try:
        source_commit, receipt_sha256 = build_and_write_receipt()
        sys.stdout.buffer.write(
            canonical_json(
                {
                    "committed_transition": (
                        "after prospective validation and snapshot, chmod this exact receipt "
                        "0644 before the receipt-only E commit and committed validation"
                    ),
                    "prospective_live_mode": "0600",
                    "required_committed_live_mode": "0644",
                    "receipt_path": RECEIPT_RELATIVE,
                    "receipt_sha256": receipt_sha256,
                    "source_commit": source_commit,
                    "status": "WROTE",
                }
            )
        )
        return 0
    except FinalizedDescriptorReleaseError as error:
        detail = str(error).replace(os.fspath(ROOT), "$REPOSITORY")
        print(
            "ERROR: capture retained verified finalized bytes after descriptor-release "
            f"failure: {detail}",
            file=sys.stderr,
        )
        return 1
    except (OSError, ReceiptError, ValueError) as error:
        detail = str(error).replace(os.fspath(ROOT), "$REPOSITORY")
        print(f"ERROR: capture failed closed: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
