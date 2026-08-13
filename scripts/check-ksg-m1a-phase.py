#!/usr/bin/env python3
"""Fail closed on the KSG revision-4 M1a Git and receipt boundary.

This checker has two creditable lifecycle modes.  Precommit mode compares the
bbdf-anchored worktree overlay with an externally sealed alternate-index byte
stream supplied as regular-file descriptor 0, its reconstructed tree, and a
detached checkpoint.  Postcommit mode requires that same checkpoint to be the
clean direct-child HEAD.  While the reviewed policy inventory is provisional,
only an explicitly requested no-credit diagnostic can succeed.

The checker does not establish authenticity, scientific validity, general
neighbor-search correctness, estimator validity, or PID validity.
"""

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
        "ERROR: check-ksg-m1a-phase.py requires Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any


PYTHON_CHILD_PREFIX = (
    (sys.executable, "-O", "-I", "-S", "-B")
    if sys.flags.optimize == 1
    else (sys.executable, "-I", "-S", "-B")
)
SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-path-policy-v1.json"
BOUNDARY_RELATIVE = "audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md"
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-phase-self-test.py"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-phase.py"
CURRENT_SOURCE_MANIFEST = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
ACTIVE_PACKET = "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
FINAL_MATRIX = "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md"
FINAL_DECISION = "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md"
FUTURE_RECEIPT = "audit/evidence/ksg-rev4-m1a-implementation-receipt-2026-08-13.json"
ANCHOR = "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9"
ANCHOR_TREE = "b54a8bad05ab7b115f8016fd3c993a5aea74162c"
ANCHOR_ENTRY_COUNT = 711
ANCHOR_LISTING_SHA256 = (
    "663213b86a17a44e1f988c720fed13e74b9f6a4006d9d4b80ce72764e730d455"
)
EXPECTED_RECEIPT_SCHEMA_SHA256 = (
    "b477f8c4c3cb2066c0eb9c09a98cb9fbbc3ba330951aed440d2011fcace4d672"
)
# Freeze protocol: change this literal together with the policy state, boundary
# marker/state line, and reviewed policy digest. The self-test exercises both
# structural states but requires the live artifacts to match this one.
EXPECTED_LIVE_POLICY_STATE = "frozen"
# Freeze protocol: after the final policy inventory is reviewed, replace this
# zero placeholder with the exact frozen policy SHA-256. A frozen policy cannot
# receive credit while this placeholder remains.
EXPECTED_FROZEN_POLICY_SHA256 = "7f4944ae0d4f9578c08a16f5bd5ba251e30339f574e11fa75840857a3710942e"
EXPECTED_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"
EXPECTED_TIMEZONE = "+0200"
EXPECTED_MESSAGE = "Harden KSG integer-harmonic runtime correspondence\n"
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
EXPECTED_FORBIDDEN_CONTEXTS = (
    "PID2 represented-sum or atom-availability changes",
    "Williams-Beer I_min changes",
    "categorical MGW shared-exclusions or fitted-quantized changes",
    "PID3 lattice or incomplete-PID changes",
    "general nextafter or neighbor-backend parity presented as KSG M1a evidence",
    "unrelated PDF or formal-method changes",
    "combined software-identity or release-family advancement",
    "immutable evidence-matrix-v4.md or decision-v4.md creation",
)
EXPECTED_REVIEW_CLASSES = {
    "durable_program_coordination": (
        "Refresh durable status for already observed bbdf/hosted/Lean-r4 custody "
        "and record bounded current KSG M1a next actions without granting "
        "scientific, estimator, PID, or integration authority."
    ),
    "ksg_preclosure_authority": (
        "Update only revision-4 preclosure facts and retain integration_no_go, all "
        "13 open integration gates, absent final matrix/decision, and estimator/PID "
        "nontransfer."
    ),
    "ksg_preclosure_verifier": (
        "Bind preclosure runtime markers and the explicitly red lifecycle; reserve "
        "the M1a receipt contract to the versioned phase schema without granting "
        "M1c authority."
    ),
    "ksg_runtime_boundary": (
        "Harden strict-radius, shell-count, backend, and fixed-witness "
        "correspondence without claiming general neighbor correctness or "
        "statistical validity."
    ),
    "lean_r5_custody": (
        "Create append-preserving Lean 4.33 replay custody after all other bytes "
        "freeze; do not alter theorem statements or transfer Lean credit to Rust."
    ),
    "lean_r5_execution_custody": (
        "Add a new no-clobber current-project replay receipt while preserving every "
        "prior replay byte."
    ),
    "lean_r5_pointer_consequence": (
        "Point the existing current-replay surfaces to r5 and retain prior receipts "
        "as historical evidence without changing their scientific scope."
    ),
    "mandatory_release_record": (
        "Record the bounded engineering work under Unreleased without calling it a "
        "release, theorem, validation, or estimator result."
    ),
    "phase_authority": (
        "Define the acyclic M1a path, receipt, and nonclaim boundary; the two "
        "verifier scripts retain the documented self-reference cut."
    ),
    "phase_hosted_wiring": (
        "Run normal and optimized M1a policy/self-test checks plus the exact "
        "postcommit tree/checkpoint mode in hosted CI without weakening existing "
        "KSG, Lean, source-state, or repository gates."
    ),
    "phase_verifier_self_cut": (
        "Validate exact paths, Git objects, commit envelope, externally sealed "
        "alternate-index bytes, tree/checkpoint, and lifecycle; external custody "
        "rather than an internal digest anchors these scripts."
    ),
    "self_excluding_source_state": (
        "Regenerate last from the settled candidate; its self-exclusion avoids a "
        "manifest digest cycle."
    ),
}
REQUIRED_POLICY_PATHS = frozenset(
    {
        "AGENTS.md",
        "CHANGELOG.md",
        CURRENT_SOURCE_MANIFEST,
        "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
        BOUNDARY_RELATIVE,
        POLICY_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        "crates/pid-core/src/kdtree.rs",
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/src/nn.rs",
        "scripts/check-ksg-harmonic-revision-self-test.py",
        "scripts/check-ksg-harmonic-revision.py",
        SELF_TEST_RELATIVE,
        CHECKER_RELATIVE,
    }
)
REQUIRED_ADDED_PATHS = frozenset(
    {
        BOUNDARY_RELATIVE,
        POLICY_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        SELF_TEST_RELATIVE,
        CHECKER_RELATIVE,
    }
)
FORBIDDEN_POLICY_PATHS = frozenset({FINAL_MATRIX, FINAL_DECISION, FUTURE_RECEIPT})
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTITY = re.compile(
    rb"(?P<name>[^\n<>]+) <(?P<email>[^\n<>\s]+)> "
    rb"(?P<epoch>[1-9][0-9]*) (?P<timezone>[+-][0-9]{4})"
)
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_INDEX_BYTES = 64 * 1024 * 1024
SELF_TEST_VECTOR_SCHEMA = "pid-rs/ksg-rev4-m1a-self-test-vector/v1"
SELF_TEST_VALIDATORS = frozenset(
    {
        "boundary_state",
        "checkpoint",
        "credit",
        "delta",
        "lifecycle_metadata",
        "lifecycle_observation",
        "manifest_replay",
        "policy",
        "preclosure",
        "receipt_schema",
        "runtime_mode",
        "strict_json",
    }
)


class PhaseError(RuntimeError):
    """A bounded M1a phase requirement failed."""


@dataclass(frozen=True)
class Entry:
    mode: str
    oid: str


@dataclass(frozen=True)
class PolicyEntry:
    path: str
    status: str
    review_class: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseError(message)


def canonical_json(value: Any, *, pretty: bool) -> bytes:
    try:
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
    except (TypeError, ValueError) as error:
        raise PhaseError(f"cannot canonicalize JSON: {error}") from error
    return (rendered + "\n").encode("utf-8")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise PhaseError(f"duplicate JSON key is forbidden: {key!r}")
        value[key] = item
    return value


def reject_constant(value: str) -> Any:
    raise PhaseError(f"non-finite JSON constant is forbidden: {value}")


def parse_json_bytes(raw: bytes, label: str, *, require_canonical: bool) -> Any:
    require(0 < len(raw) <= MAX_JSON_BYTES, f"{label} exceeds the JSON byte bound")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PhaseError(f"{label} is not strict UTF-8 JSON: {error}") from error
    if require_canonical:
        require(
            raw == canonical_json(value, pretty=True), f"{label} is not canonical JSON"
        )
    return value


def read_regular(relative: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    path = ROOT / relative
    try:
        before = path.lstat()
    except OSError as error:
        raise PhaseError(f"cannot stat {relative}: {error}") from error
    require(stat.S_ISREG(before.st_mode), f"path is not a regular file: {relative}")
    require(before.st_nlink == 1, f"path is hard-linked: {relative}")
    require(0 <= before.st_size <= maximum, f"path exceeds byte bound: {relative}")
    try:
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise PhaseError(f"cannot read {relative}: {error}") from error

    def identity(item: os.stat_result) -> tuple[int, ...]:
        return (
            item.st_dev,
            item.st_ino,
            item.st_mode,
            item.st_nlink,
            item.st_size,
            item.st_mtime_ns,
            item.st_ctime_ns,
        )

    require(identity(before) == identity(after), f"path changed while read: {relative}")
    require(len(raw) == before.st_size, f"short read: {relative}")
    return raw


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
    }


def git(
    *arguments: str,
    check: bool = True,
    extra_environment: dict[str, str] | None = None,
) -> bytes:
    executable = Path("/usr/bin/git")
    try:
        before = executable.lstat()
    except OSError as error:
        raise PhaseError(f"cannot inspect fixed Git executable: {error}") from error
    require(
        stat.S_ISREG(before.st_mode) and executable.resolve(strict=True) == executable,
        "fixed Git executable is not a canonical regular file",
    )
    command = [
        os.fspath(executable),
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "diff.external=",
        "-C",
        os.fspath(ROOT),
        *arguments,
    ]
    environment = safe_environment()
    if extra_environment is not None:
        require(
            set(extra_environment) <= {"GIT_INDEX_FILE"},
            "unsupported Git environment override",
        )
        environment.update(extra_environment)
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
        raise PhaseError(f"Git invocation failed: {error}") from error
    require(
        len(completed.stdout) <= MAX_GIT_OUTPUT_BYTES
        and len(completed.stderr) <= MAX_GIT_OUTPUT_BYTES,
        "Git output exceeds byte bound",
    )
    try:
        after = executable.lstat()
    except OSError as error:
        raise PhaseError(f"cannot recheck fixed Git executable: {error}") from error
    require(
        (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        ),
        "fixed Git executable changed during invocation",
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PhaseError(
            f"Git command failed ({completed.returncode}): {arguments!r}: {detail}"
        )
    if not check:
        return bytes([completed.returncode]) + completed.stdout
    return completed.stdout


def git_text(*arguments: str, extra_environment: dict[str, str] | None = None) -> str:
    try:
        return (
            git(*arguments, extra_environment=extra_environment)
            .decode("utf-8", errors="strict")
            .rstrip("\n")
        )
    except UnicodeDecodeError as error:
        raise PhaseError(f"Git returned non-UTF-8 text for {arguments!r}") from error


def validate_path(path: str) -> None:
    pure = PurePosixPath(path)
    require(
        bool(path)
        and not path.startswith("/")
        and ".." not in pure.parts
        and pure.as_posix() == path
        and "\x00" not in path
        and "\n" not in path
        and "\r" not in path,
        f"unsafe or noncanonical repository path: {path!r}",
    )


def parse_tree(tree: str) -> tuple[dict[str, Entry], bytes]:
    require(HEX40.fullmatch(tree) is not None, "tree is not a lowercase SHA-1 id")
    raw = git("ls-tree", "-rz", "-r", "--full-tree", tree)
    records = raw[:-1].split(b"\0") if raw else []
    require(not raw or raw.endswith(b"\0"), "Git tree listing lacks NUL termination")
    entries: dict[str, Entry] = {}
    for record in records:
        prefix, separator, path_raw = record.partition(b"\t")
        require(separator == b"\t", "malformed Git tree entry")
        fields = prefix.split(b" ")
        require(len(fields) == 3, "malformed Git tree entry prefix")
        mode_raw, kind, oid_raw = fields
        require(kind == b"blob", "tree contains a non-blob leaf")
        try:
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
            path = path_raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise PhaseError("tree contains a non-UTF-8 field") from error
        require(mode in {"100644", "100755"}, f"unsupported tree mode: {mode}")
        require(HEX40.fullmatch(oid) is not None, "tree blob id is malformed")
        validate_path(path)
        require(path not in entries, f"duplicate tree path: {path}")
        entries[path] = Entry(mode, oid)
    require(list(entries) == sorted(entries), "tree listing is not sorted")
    return entries, raw


def blob_oid(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 -- Git SHA-1 object identity.


def changed_entries(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> tuple[tuple[str, str, str], ...]:
    changed: list[tuple[str, str, str]] = []
    for path in sorted(set(anchor) | set(candidate)):
        old = anchor.get(path)
        new = candidate.get(path)
        if old == new:
            continue
        if old is None and new is not None:
            changed.append((path, "A", new.mode))
        elif old is not None and new is None:
            changed.append((path, "D", old.mode))
        elif new is not None:
            changed.append((path, "M", new.mode))
    return tuple(changed)


def validate_policy_data(value: Any, *, verify_anchor: bool) -> tuple[PolicyEntry, ...]:
    require(isinstance(value, dict), "policy root must be an object")
    expected_keys = {
        "anchor",
        "authority",
        "commit_envelope",
        "deletions_permitted",
        "entries",
        "forbidden_contexts",
        "receipt_contract",
        "review_classes",
        "schema",
        "schema_revision",
    }
    require(set(value) == expected_keys, "policy top-level shape changed")
    require(
        value.get("schema") == "pid-rs/ksg-rev4-m1a-path-policy"
        and type(value.get("schema_revision")) is int
        and value["schema_revision"] == 1,
        "policy schema identity changed",
    )
    anchor = value.get("anchor")
    require(
        anchor
        == {
            "commit": ANCHOR,
            "tree": ANCHOR_TREE,
            "tree_entry_count": ANCHOR_ENTRY_COUNT,
            "tree_listing_sha256": ANCHOR_LISTING_SHA256,
        },
        "policy anchor changed",
    )
    authority = value.get("authority")
    require(isinstance(authority, dict), "policy authority is malformed")
    require(
        set(authority)
        == {
            "authoritative_when_inventory_frozen",
            "credit_permitted",
            "freeze_instruction",
            "inventory_status",
            "mechanical_resealing_permitted",
            "scope",
        },
        "policy authority shape changed",
    )
    status = authority.get("inventory_status")
    credit = authority.get("credit_permitted")
    require(
        status in {"provisional_anticipated_paths_not_frozen", "frozen"}
        and type(credit) is bool,
        "policy inventory state is malformed",
    )
    require(
        (status == "frozen") == credit,
        "policy credit must be true exactly when the inventory is frozen",
    )
    require(
        authority.get("authoritative_when_inventory_frozen") is True
        and authority.get("mechanical_resealing_permitted") is False,
        "policy authority weakened",
    )
    require(
        authority.get("scope")
        == "KSG revision-4 M1a runtime correspondence, preclosure custody, mandatory changelog, and direct Lean-r5/current-source consequences only",
        "policy authority scope changed",
    )
    require(
        authority.get("freeze_instruction")
        == "After every discretionary or authored candidate writer stops, and before the prescribed append-only r5 receipt and self-excluding current-source manifest generators run, replace inventory_status with frozen, set credit_permitted true, review the exact sorted entry inventory, and rerun the hostile suite. Construct the external tree and checkpoint only after both prescribed generators finish. Do not mechanically accept an observed delta.",
        "policy freeze instruction changed",
    )
    require(value.get("deletions_permitted") is False, "policy permits deletions")
    envelope = value.get("commit_envelope")
    expected_identity = {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
    require(
        envelope
        == {
            "author": expected_identity,
            "author_and_committer_headers_identical": True,
            "committer": expected_identity,
            "message": EXPECTED_MESSAGE,
            "parent_count": 1,
            "signature_headers_permitted": False,
            "timezone": EXPECTED_TIMEZONE,
        },
        "policy commit envelope changed",
    )
    review_classes = value.get("review_classes")
    require(
        review_classes == EXPECTED_REVIEW_CLASSES,
        "policy review-class semantics changed",
    )
    rows = value.get("entries")
    require(isinstance(rows, list) and rows, "policy entries must be a nonempty array")
    parsed: list[PolicyEntry] = []
    for index, row in enumerate(rows):
        require(
            isinstance(row, dict) and set(row) == {"path", "review_class", "status"},
            f"policy entry {index} shape changed",
        )
        path = row.get("path")
        row_status = row.get("status")
        review_class = row.get("review_class")
        require(isinstance(path, str), f"policy entry {index} path is not text")
        validate_path(path)
        require(row_status in {"A", "M"}, f"policy entry {path} status is invalid")
        require(
            isinstance(review_class, str) and review_class in review_classes,
            f"policy entry {path} review class is invalid",
        )
        parsed.append(PolicyEntry(path, row_status, review_class))
    require(
        [item.path for item in parsed] == sorted(item.path for item in parsed)
        and len({item.path for item in parsed}) == len(parsed),
        "policy entries are not sorted and duplicate-free",
    )
    paths = {item.path for item in parsed}
    require(REQUIRED_POLICY_PATHS <= paths, "policy omits a required M1a path")
    require(not (paths & FORBIDDEN_POLICY_PATHS), "policy includes an M1c-only path")
    status_by_path = {item.path: item.status for item in parsed}
    require(
        all(status_by_path[path] == "A" for path in REQUIRED_ADDED_PATHS),
        "new lifecycle paths are not classified as additions",
    )
    receipt = value.get("receipt_contract")
    require(
        receipt
        == {
            "final_descendant_receipt_path": FUTURE_RECEIPT,
            "final_descendant_receipt_schema": (
                "pid-rs/ksg-rev4-m1a-implementation-receipt/v1"
            ),
            "m1a_subject_must_not_contain_receipt": True,
            "m1c_must_bind_receipt_path_and_sha256": True,
        },
        "policy receipt contract changed",
    )
    forbidden = value.get("forbidden_contexts")
    require(
        forbidden == list(EXPECTED_FORBIDDEN_CONTEXTS),
        "policy forbidden-context inventory changed",
    )
    if verify_anchor:
        anchor_entries, listing = parse_tree(ANCHOR_TREE)
        require(
            len(anchor_entries) == ANCHOR_ENTRY_COUNT
            and hashlib.sha256(listing).hexdigest() == ANCHOR_LISTING_SHA256,
            "anchor tree inventory changed",
        )
        require(
            git_text("rev-parse", f"{ANCHOR}^{{tree}}") == ANCHOR_TREE,
            "anchor commit/tree relation changed",
        )
        for item in parsed:
            if item.status == "M":
                require(
                    item.path in anchor_entries,
                    f"modified path absent from anchor: {item.path}",
                )
            else:
                require(
                    item.path not in anchor_entries,
                    f"added path exists in anchor: {item.path}",
                )
    return tuple(parsed)


def load_policy(
    *, verify_anchor: bool
) -> tuple[dict[str, Any], bytes, tuple[PolicyEntry, ...]]:
    raw = read_regular(POLICY_RELATIVE)
    value = parse_json_bytes(raw, "M1a path policy", require_canonical=True)
    entries = validate_policy_data(value, verify_anchor=verify_anchor)
    observed_digest = hashlib.sha256(raw).hexdigest()
    inventory_status = value["authority"]["inventory_status"]
    require(
        inventory_status == EXPECTED_LIVE_POLICY_STATE,
        "live policy state differs from the reviewed checker state",
    )
    if inventory_status == "frozen":
        require(
            HEX64.fullmatch(EXPECTED_FROZEN_POLICY_SHA256) is not None
            and EXPECTED_FROZEN_POLICY_SHA256 != "0" * 64
            and observed_digest == EXPECTED_FROZEN_POLICY_SHA256,
            "frozen policy is not bound by the reviewed checker digest",
        )
    else:
        require(
            EXPECTED_FROZEN_POLICY_SHA256 == "0" * 64,
            "provisional policy unexpectedly carries a frozen-policy digest",
        )
    return value, raw, entries


def validate_receipt_schema_data(value: Any) -> None:
    require(isinstance(value, dict), "M1a receipt schema root is not an object")
    require(
        hashlib.sha256(canonical_json(value, pretty=True)).hexdigest()
        == EXPECTED_RECEIPT_SCHEMA_SHA256,
        "M1a receipt schema bytes differ from the reviewed contract",
    )
    require(
        value.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        and value.get("$id")
        == "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json"
        and value.get("type") == "object"
        and value.get("additionalProperties") is False,
        "M1a receipt schema envelope changed",
    )
    required = value.get("required")
    expected = [
        "schema",
        "schema_revision",
        "repository",
        "claim",
        "milestone",
        "subject",
        "phase_custody",
        "remote_observation",
        "hosted_validation",
        "acyclic_boundary",
        "evidence_class",
        "nonimplications",
    ]
    require(
        required == expected, "M1a receipt schema top-level required fields changed"
    )
    properties = value.get("properties")
    require(
        isinstance(properties, dict) and set(properties) == set(expected),
        "M1a receipt schema property set changed",
    )
    require(
        properties["schema"].get("const")
        == "pid-rs/ksg-rev4-m1a-implementation-receipt/v1"
        and properties["schema_revision"].get("const") == 1
        and properties["evidence_class"].get("const")
        == "m1a_lifecycle_custody_not_scientific_evidence",
        "M1a receipt schema identity changed",
    )
    milestone = properties["milestone"]["properties"]
    require(
        milestone["gate_id"].get("const") == "G1"
        and milestone["phase"].get("const") == "M1a"
        and milestone["status"].get("const")
        == "implementation_anchor_observed_integration_no_go",
        "M1a receipt milestone changed",
    )
    nonimplications = properties["nonimplications"].get("const")
    require(
        isinstance(nonimplications, list) and len(nonimplications) == 5,
        "M1a receipt nonimplications changed",
    )


def validate_boundary_state_data(boundary: str, inventory_status: str) -> None:
    normalized_boundary = " ".join(boundary.split())
    for marker in (
        "General `nextafter`-adjacent and boundary-shell brute/kd-tree parity remains a separate P2 backlog item.",
        "Revision 4 remains `integration_no_go` throughout M1a.",
        "The phase checker and its self-test cannot hash themselves without a cycle.",
        "The M1a receipt is distinct from whatever gate-specific evidence contracts a future M1c checker ultimately defines.",
    ):
        require(
            marker in normalized_boundary,
            f"M1a boundary marker disappeared: {marker}",
        )
    state_markers = {
        state: f"<!-- ksg-m1a-policy-state: {state} -->"
        for state in ("provisional_anticipated_paths_not_frozen", "frozen")
    }
    state_lines = {
        "provisional_anticipated_paths_not_frozen": (
            "- Current policy state: **provisional inventory; no M1a credit**"
        ),
        "frozen": (
            "- Current policy state: **frozen reviewed inventory; M1a credit "
            "eligible only with external custody**"
        ),
    }
    require(inventory_status in state_lines, "M1a boundary policy state is unsupported")
    for state in state_lines:
        expected_count = 1 if state == inventory_status else 0
        require(
            boundary.count(state_markers[state]) == expected_count,
            "M1a boundary and policy machine states differ",
        )
        require(
            boundary.count(state_lines[state]) == expected_count,
            "M1a boundary and policy human-readable states differ",
        )


def validate_static_artifacts(inventory_status: str) -> dict[str, str]:
    schema_raw = read_regular(RECEIPT_SCHEMA_RELATIVE)
    schema = parse_json_bytes(schema_raw, "M1a receipt schema", require_canonical=True)
    validate_receipt_schema_data(schema)
    boundary = read_regular(BOUNDARY_RELATIVE).decode("utf-8", errors="strict")
    validate_boundary_state_data(boundary, inventory_status)
    return {
        BOUNDARY_RELATIVE: hashlib.sha256(boundary.encode("utf-8")).hexdigest(),
        RECEIPT_SCHEMA_RELATIVE: hashlib.sha256(schema_raw).hexdigest(),
        CHECKER_RELATIVE: hashlib.sha256(read_regular(CHECKER_RELATIVE)).hexdigest(),
        SELF_TEST_RELATIVE: hashlib.sha256(
            read_regular(SELF_TEST_RELATIVE)
        ).hexdigest(),
    }


def validate_repository_context() -> tuple[str, str]:
    require(SCRIPT == ROOT / CHECKER_RELATIVE, "checker path is not canonical")
    require(not (ROOT / CHECKER_RELATIVE).is_symlink(), "checker path is a symlink")
    require(
        git_text("rev-parse", "--show-object-format") == "sha1",
        "repository object format is not SHA-1",
    )
    reported = Path(git_text("rev-parse", "--show-toplevel")).resolve(strict=True)
    require(
        reported == ROOT.resolve(strict=True),
        "checker is not at the canonical worktree root",
    )
    require(
        not git_text("for-each-ref", "--format=%(refname)", "refs/replace"),
        "replacement refs are present",
    )
    git_dir = Path(git_text("rev-parse", "--absolute-git-dir"))
    require(not (git_dir / "info/grafts").exists(), "Git graft file is present")
    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    require(
        HEX40.fullmatch(head) is not None and HEX40.fullmatch(tree) is not None,
        "HEAD identity is malformed",
    )
    return head, tree


def exact_object(oid: str, kind: str) -> bytes:
    require(HEX40.fullmatch(oid) is not None, f"{kind} id is malformed")
    require(git_text("cat-file", "-t", oid) == kind, f"object is not a {kind}: {oid}")
    raw = git("cat-file", kind, oid)
    require(len(raw) <= MAX_FILE_BYTES, f"{kind} object exceeds byte bound")
    header = f"{kind} {len(raw)}\0".encode("ascii")
    observed = hashlib.sha1(header + raw).hexdigest()  # noqa: S324 -- Git SHA-1 identity.
    require(observed == oid, f"{kind} object bytes do not match id")
    return raw


def parse_checkpoint_bytes(raw: bytes, expected_tree: str) -> dict[str, Any]:
    """Validate exact unsigned commit content; exposed for the hostile suite."""

    require(b"\r" not in raw and b"\0" not in raw, "checkpoint contains CR or NUL")
    header, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", "checkpoint lacks message separator")
    lines = header.split(b"\n")
    require(len(lines) == 4, "checkpoint is not exact unsigned single-parent form")
    require(
        lines[0] == f"tree {expected_tree}".encode("ascii")
        and lines[1] == f"parent {ANCHOR}".encode("ascii"),
        "checkpoint tree or parent changed",
    )
    require(message == EXPECTED_MESSAGE.encode("utf-8"), "checkpoint message changed")
    identities: list[dict[str, Any]] = []
    values: list[bytes] = []
    for label, line in ((b"author", lines[2]), (b"committer", lines[3])):
        prefix, space, value = line.partition(b" ")
        require(
            space == b" " and prefix == label,
            f"checkpoint {label.decode()} header changed",
        )
        match = IDENTITY.fullmatch(value)
        require(match is not None, f"checkpoint {label.decode()} identity is malformed")
        name = match.group("name").decode("utf-8", errors="strict")
        email = match.group("email").decode("ascii", errors="strict")
        timezone = match.group("timezone").decode("ascii", errors="strict")
        require(
            name == EXPECTED_NAME
            and email == EXPECTED_EMAIL
            and timezone == EXPECTED_TIMEZONE,
            f"checkpoint {label.decode()} identity changed",
        )
        values.append(value)
        identities.append({"email": email, "name": name})
    require(values[0] == values[1], "checkpoint author and committer headers differ")
    return {
        "author": identities[0],
        "committer": identities[1],
        "message": EXPECTED_MESSAGE,
    }


def parse_checkpoint(commit: str, expected_tree: str) -> dict[str, Any]:
    raw = exact_object(commit, "commit")
    return parse_checkpoint_bytes(raw, expected_tree)


def validate_delta(
    policy_entries: tuple[PolicyEntry, ...],
    anchor: dict[str, Entry],
    candidate: dict[str, Entry],
) -> tuple[tuple[str, str, str], ...]:
    observed = changed_entries(anchor, candidate)
    expected = tuple((item.path, item.status, "100644") for item in policy_entries)
    require(observed == expected, "candidate tree delta differs from exact policy")
    require(
        FINAL_MATRIX not in candidate and FINAL_DECISION not in candidate,
        "candidate contains final M1c authority",
    )
    require(
        FUTURE_RECEIPT not in candidate, "candidate contains its future M1a receipt"
    )
    return observed


def decode_z_paths(raw: bytes, label: str) -> tuple[str, ...]:
    require(not raw or raw.endswith(b"\0"), f"{label} lacks NUL termination")
    values = raw[:-1].split(b"\0") if raw else []
    try:
        paths = tuple(item.decode("utf-8", errors="strict") for item in values)
    except UnicodeDecodeError as error:
        raise PhaseError(f"{label} contains a non-UTF-8 path") from error
    for path in paths:
        validate_path(path)
    require(len(paths) == len(set(paths)), f"{label} contains duplicates")
    return paths


def parse_index_entries(raw: bytes) -> dict[str, Entry]:
    require(not raw or raw.endswith(b"\0"), "alternate-index listing lacks NUL")
    records = raw[:-1].split(b"\0") if raw else []
    entries: dict[str, Entry] = {}
    for record in records:
        prefix, separator, path_raw = record.partition(b"\t")
        require(separator == b"\t", "malformed alternate-index entry")
        fields = prefix.split(b" ")
        require(len(fields) == 3, "malformed alternate-index entry prefix")
        mode_raw, oid_raw, stage_raw = fields
        require(stage_raw == b"0", "alternate index contains a non-zero stage")
        try:
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
            path = path_raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise PhaseError("alternate index contains a non-UTF-8 field") from error
        require(mode in {"100644", "100755"}, "alternate index has unsupported mode")
        require(HEX40.fullmatch(oid) is not None, "alternate-index oid is malformed")
        validate_path(path)
        require(path not in entries, f"duplicate alternate-index path: {path}")
        entries[path] = Entry(mode, oid)
    require(list(entries) == sorted(entries), "alternate-index listing is not sorted")
    return entries


def read_sealed_alternate_index(descriptor: int) -> tuple[bytes, os.stat_result]:
    require(
        type(descriptor) is int and descriptor >= 0,
        "alternate-index descriptor is invalid",
    )
    try:
        before = os.fstat(descriptor)
        offset = os.lseek(descriptor, 0, os.SEEK_CUR)
        descriptor_flags = fcntl.fcntl(descriptor, fcntl.F_GETFL)
    except OSError as error:
        raise PhaseError(f"cannot inspect alternate index: {error}") from error
    require(offset == 0, "alternate-index descriptor is not positioned at byte zero")
    require(
        descriptor_flags & os.O_ACCMODE == os.O_RDONLY,
        "alternate-index descriptor is not read-only",
    )
    require(stat.S_ISREG(before.st_mode), "alternate index is not a regular file")
    require(stat.S_IMODE(before.st_mode) == 0o400, "alternate index mode is not 0400")
    require(before.st_nlink == 1, "alternate index is not single-link")
    require(0 < before.st_size <= MAX_INDEX_BYTES, "alternate index exceeds byte bound")
    try:
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(bool(chunk), "alternate index ended early")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(not os.read(descriptor, 1), "alternate index grew while read")
        after = os.fstat(descriptor)
    except OSError as error:
        raise PhaseError(f"cannot read alternate index: {error}") from error
    require(
        (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        == (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ),
        "alternate index changed while read",
    )
    raw = b"".join(chunks)
    require(len(raw) == before.st_size, "alternate-index read length changed")
    return raw, before


def write_private_copy(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "short write while copying alternate index")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_alternate_index(
    descriptor: int,
    expected_sha256: str,
    expected_entry_count: int,
    candidate_tree: str,
    candidate: dict[str, Entry],
) -> dict[str, Any]:
    require(
        HEX64.fullmatch(expected_sha256) is not None,
        "alternate-index SHA-256 is malformed",
    )
    require(
        type(expected_entry_count) is int and expected_entry_count > 0,
        "alternate-index entry count is invalid",
    )
    raw, metadata = read_sealed_alternate_index(descriptor)
    digest = hashlib.sha256(raw).hexdigest()
    require(
        digest == expected_sha256,
        "alternate-index SHA-256 differs from external record",
    )
    observed: list[tuple[str, dict[str, Entry]]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-ksg-m1a-index-") as directory:
        for suffix in ("a", "b"):
            copy_path = Path(directory) / f"index-{suffix}"
            write_private_copy(copy_path, raw)
            environment = {"GIT_INDEX_FILE": os.fspath(copy_path)}
            tree = git_text("write-tree", extra_environment=environment)
            listing = git("ls-files", "--stage", "-z", extra_environment=environment)
            observed.append((tree, parse_index_entries(listing)))
    for tree, entries in observed:
        require(tree == candidate_tree, "alternate index reconstructs a different tree")
        require(
            entries == candidate, "alternate-index entries differ from candidate tree"
        )
        require(
            len(entries) == expected_entry_count,
            "alternate-index entry count differs from external record",
        )
    require(
        observed[0] == observed[1], "repeated alternate-index reconstruction differed"
    )
    return {
        "entry_count": expected_entry_count,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "sha256": digest,
        "single_link": True,
        "size_bytes": metadata.st_size,
    }


def compare_candidate_to_worktree(candidate: dict[str, Entry]) -> None:
    for path, entry in candidate.items():
        raw = read_regular(path)
        mode = "100755" if (ROOT / path).stat().st_mode & stat.S_IXUSR else "100644"
        require(
            mode == entry.mode, f"worktree mode differs from candidate tree: {path}"
        )
        require(
            blob_oid(raw) == entry.oid,
            f"worktree bytes differ from candidate tree: {path}",
        )


def require_git_quiet(*arguments: str, label: str) -> None:
    result = git(*arguments, check=False)
    returncode = result[0]
    require(returncode == 0, label)


def git_quiet(*arguments: str) -> bool:
    return git(*arguments, check=False)[0] == 0


def validate_lifecycle_metadata(
    branch: str | None, active_operations: tuple[str, ...]
) -> None:
    require(
        branch == "main",
        "creditable lifecycle validation requires symbolic branch main",
    )
    require(
        not active_operations,
        "repository has an active Git operation: " + ", ".join(active_operations),
    )


def observe_lifecycle_metadata() -> tuple[str | None, tuple[str, ...]]:
    branch_result = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch_result[0] == 0:
        try:
            branch = branch_result[1:].decode("utf-8", errors="strict").rstrip("\n")
        except UnicodeDecodeError as error:
            raise PhaseError("symbolic branch name is not UTF-8") from error
    else:
        branch = None
    operation_paths = (
        "MERGE_HEAD",
        "AUTO_MERGE",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "REBASE_HEAD",
        "BISECT_LOG",
        "rebase-apply",
        "rebase-merge",
        "sequencer",
    )
    active: list[str] = []
    for relative in operation_paths:
        path_text = git_text("rev-parse", "--git-path", relative)
        path = Path(path_text)
        if not path.is_absolute():
            path = ROOT / path
        if os.path.lexists(path):
            active.append(relative)
    return branch, tuple(active)


def validate_lifecycle_observation(
    *,
    mode: str,
    head: str,
    checkpoint: str,
    index_clean: bool,
    tracked_clean: bool,
    modified: tuple[str, ...],
    untracked: tuple[str, ...],
    expected_modified: tuple[str, ...],
    expected_added: tuple[str, ...],
) -> str:
    if mode == "precommit":
        require(head == ANCHOR, "precommit HEAD is not the exact bbdf anchor")
        require(index_clean, "primary index differs from bbdf")
        require(
            tuple(sorted(modified)) == expected_modified,
            "tracked worktree paths differ from policy",
        )
        require(
            tuple(sorted(untracked)) == expected_added,
            "untracked worktree paths differ from policy",
        )
        return "anchor_plus_exact_worktree_overlay"
    require(mode == "postcommit", "unsupported lifecycle mode")
    require(head == checkpoint, "postcommit HEAD differs from detached checkpoint")
    require(index_clean, "postcommit index differs from HEAD")
    require(tracked_clean, "postcommit tracked worktree differs from HEAD")
    require(not modified, "postcommit tracked delta is nonempty")
    require(
        not untracked, "postcommit worktree contains repository-visible untracked paths"
    )
    return "clean_committed_direct_child"


def validate_worktree_lifecycle(
    mode: str,
    head: str,
    checkpoint: str,
    policy_entries: tuple[PolicyEntry, ...],
    candidate: dict[str, Entry],
) -> str:
    expected_modified = tuple(
        item.path for item in policy_entries if item.status == "M"
    )
    expected_added = tuple(item.path for item in policy_entries if item.status == "A")
    if mode == "precommit":
        modified = decode_z_paths(
            git("diff", "--name-only", "-z", ANCHOR, "--"), "tracked worktree delta"
        )
        untracked = decode_z_paths(
            git("ls-files", "--others", "--exclude-standard", "-z"), "untracked paths"
        )
        lifecycle = validate_lifecycle_observation(
            mode=mode,
            head=head,
            checkpoint=checkpoint,
            index_clean=git_quiet("diff", "--cached", "--quiet", ANCHOR, "--"),
            tracked_clean=False,
            modified=modified,
            untracked=untracked,
            expected_modified=expected_modified,
            expected_added=expected_added,
        )
        compare_candidate_to_worktree(candidate)
        return lifecycle
    require(mode == "postcommit", "unsupported lifecycle mode")
    modified = decode_z_paths(
        git("diff", "--name-only", "-z", "HEAD", "--"),
        "postcommit tracked paths",
    )
    untracked = decode_z_paths(
        git("ls-files", "--others", "--exclude-standard", "-z"),
        "postcommit untracked paths",
    )
    lifecycle = validate_lifecycle_observation(
        mode=mode,
        head=head,
        checkpoint=checkpoint,
        index_clean=git_quiet("diff", "--cached", "--quiet", "HEAD", "--"),
        tracked_clean=git_quiet("diff", "--quiet", "HEAD", "--"),
        modified=modified,
        untracked=untracked,
        expected_modified=expected_modified,
        expected_added=expected_added,
    )
    compare_candidate_to_worktree(candidate)
    return lifecycle


def candidate_blob(candidate: dict[str, Entry], path: str) -> bytes:
    entry = candidate.get(path)
    require(entry is not None, f"candidate path is absent: {path}")
    raw = exact_object(entry.oid, "blob")
    return raw


def validate_preclosure(candidate: dict[str, Entry]) -> None:
    packet_raw = candidate_blob(candidate, ACTIVE_PACKET)
    packet = parse_json_bytes(
        packet_raw, "candidate active KSG packet", require_canonical=True
    )
    validate_preclosure_data(packet)


def validate_preclosure_data(packet: Any) -> None:
    require(isinstance(packet, dict), "candidate active KSG packet is malformed")
    require(
        packet.get("active_revision") == 4
        and packet.get("claim_id") == "KSG-INTEGER-HARMONIC-001"
        and packet.get("status") == "integration_no_go"
        and packet.get("packet_stage")
        == "preclosure_core_manifest_must_be_regenerated_at_m1c"
        and tuple(packet.get("open_integration_gates", ())) == EXPECTED_PACKET_GATES,
        "candidate active packet advanced beyond M1a preclosure",
    )


def validate_manifest_replay(
    *, actual: bytes, emitted: bytes, returncode: int, stderr: bytes
) -> str:
    require(
        returncode == 0,
        "current-source manifest emitter failed: "
        + stderr.decode("utf-8", errors="replace").strip(),
    )
    require(actual == emitted, "current-source manifest is stale for candidate bytes")
    return hashlib.sha256(actual).hexdigest()


def validate_current_source_manifest() -> str:
    checker = ROOT / CURRENT_SOURCE_CHECKER
    require(
        checker.is_file() and not checker.is_symlink(),
        "current-source checker path is invalid",
    )
    command = [
        *PYTHON_CHILD_PREFIX,
        os.fspath(checker),
        "--emit",
    ]
    environment = safe_environment()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PhaseError(f"current-source manifest replay failed: {error}") from error
    actual = read_regular(CURRENT_SOURCE_MANIFEST, maximum=8 * 1024 * 1024)
    return validate_manifest_replay(
        actual=actual,
        emitted=completed.stdout,
        returncode=completed.returncode,
        stderr=completed.stderr,
    )


def validate_credit_request(inventory_status: str, allow_provisional: bool) -> bool:
    provisional = inventory_status != "frozen"
    if provisional:
        require(allow_provisional, "provisional policy cannot grant M1a credit")
    else:
        require(
            not allow_provisional,
            "frozen policy cannot use provisional diagnostic mode",
        )
    return provisional


def observed_worktree_delta(anchor: dict[str, Entry]) -> list[dict[str, str]]:
    modified = decode_z_paths(
        git("diff", "--name-only", "-z", ANCHOR, "--"), "observed modified paths"
    )
    added = decode_z_paths(
        git("ls-files", "--others", "--exclude-standard", "-z"), "observed added paths"
    )
    rows = [{"path": path, "status": "M"} for path in modified]
    rows.extend({"path": path, "status": "A"} for path in added)
    rows.sort(key=lambda item: item["path"])
    require(
        len(rows) == len({item["path"] for item in rows}), "observed delta overlaps"
    )
    for row in rows:
        if row["status"] == "M":
            require(
                row["path"] in anchor,
                f"observed modified path is absent from anchor: {row['path']}",
            )
    return rows


def exact_mapping(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    """Return an exact-key mapping for the bounded CLI self-test protocol."""

    require(isinstance(value, dict) and set(value) == keys, f"{label} shape changed")
    return value


def text_tuple(value: Any, label: str) -> tuple[str, ...]:
    require(
        isinstance(value, list) and all(isinstance(item, str) for item in value),
        f"{label} must be an array of text",
    )
    return tuple(value)


def self_test_entry_map(value: Any, label: str) -> dict[str, Entry]:
    require(isinstance(value, dict), f"{label} must be an object")
    parsed: dict[str, Entry] = {}
    for path, raw_entry in value.items():
        require(isinstance(path, str), f"{label} path is not text")
        validate_path(path)
        entry = exact_mapping(raw_entry, {"mode", "oid"}, f"{label} entry")
        mode = entry["mode"]
        oid = entry["oid"]
        require(
            isinstance(mode, str) and isinstance(oid, str),
            f"{label} entry fields are not text",
        )
        parsed[path] = Entry(mode, oid)
    return parsed


def self_test_policy_entries(value: Any) -> tuple[PolicyEntry, ...]:
    require(isinstance(value, list), "self-test policy entries must be an array")
    parsed: list[PolicyEntry] = []
    for raw_entry in value:
        entry = exact_mapping(
            raw_entry,
            {"path", "review_class", "status"},
            "self-test policy entry",
        )
        path = entry["path"]
        status = entry["status"]
        review_class = entry["review_class"]
        require(
            isinstance(path, str)
            and isinstance(status, str)
            and isinstance(review_class, str),
            "self-test policy entry fields are not text",
        )
        validate_path(path)
        parsed.append(PolicyEntry(path, status, review_class))
    return tuple(parsed)


def validate_self_test_vector_envelope(request: Any) -> dict[str, Any]:
    require(isinstance(request, dict), "self-test vector envelope is not an object")
    envelope = exact_mapping(
        request,
        {"arguments", "schema", "validator"},
        "self-test vector envelope",
    )
    require(
        envelope["schema"] == SELF_TEST_VECTOR_SCHEMA,
        "self-test vector schema changed",
    )
    require(
        envelope["validator"] in SELF_TEST_VALIDATORS,
        "self-test validator name is unsupported",
    )
    require(
        isinstance(envelope["arguments"], dict), "self-test arguments are malformed"
    )
    return envelope


def dispatch_self_test_vector(envelope: dict[str, Any]) -> None:
    """Run one pure validator without importing or executing repository bytes."""

    validator = envelope["validator"]
    arguments = envelope["arguments"]

    if validator == "policy":
        values = exact_mapping(arguments, {"value"}, "policy vector")
        validate_policy_data(values["value"], verify_anchor=False)
    elif validator == "receipt_schema":
        values = exact_mapping(arguments, {"value"}, "receipt-schema vector")
        validate_receipt_schema_data(values["value"])
    elif validator == "boundary_state":
        values = exact_mapping(
            arguments,
            {"boundary", "inventory_status"},
            "boundary-state vector",
        )
        require(
            isinstance(values["boundary"], str)
            and isinstance(values["inventory_status"], str),
            "boundary-state vector fields are not text",
        )
        validate_boundary_state_data(values["boundary"], values["inventory_status"])
    elif validator == "checkpoint":
        values = exact_mapping(arguments, {"expected_tree", "raw"}, "checkpoint vector")
        require(
            isinstance(values["expected_tree"], str) and isinstance(values["raw"], str),
            "checkpoint vector fields are not text",
        )
        parse_checkpoint_bytes(values["raw"].encode("utf-8"), values["expected_tree"])
    elif validator == "lifecycle_observation":
        values = exact_mapping(
            arguments,
            {
                "checkpoint",
                "expected_added",
                "expected_modified",
                "head",
                "index_clean",
                "mode",
                "modified",
                "tracked_clean",
                "untracked",
            },
            "lifecycle-observation vector",
        )
        require(
            all(isinstance(values[key], str) for key in ("checkpoint", "head", "mode"))
            and all(
                type(values[key]) is bool for key in ("index_clean", "tracked_clean")
            ),
            "lifecycle-observation scalar fields are malformed",
        )
        validate_lifecycle_observation(
            mode=values["mode"],
            head=values["head"],
            checkpoint=values["checkpoint"],
            index_clean=values["index_clean"],
            tracked_clean=values["tracked_clean"],
            modified=text_tuple(values["modified"], "modified paths"),
            untracked=text_tuple(values["untracked"], "untracked paths"),
            expected_modified=text_tuple(
                values["expected_modified"], "expected modified paths"
            ),
            expected_added=text_tuple(values["expected_added"], "expected added paths"),
        )
    elif validator == "lifecycle_metadata":
        values = exact_mapping(
            arguments,
            {"active_operations", "branch"},
            "lifecycle-metadata vector",
        )
        require(
            values["branch"] is None or isinstance(values["branch"], str),
            "lifecycle branch is malformed",
        )
        validate_lifecycle_metadata(
            values["branch"],
            text_tuple(values["active_operations"], "active Git operations"),
        )
    elif validator == "delta":
        values = exact_mapping(
            arguments,
            {"anchor", "candidate", "policy_entries"},
            "delta vector",
        )
        validate_delta(
            self_test_policy_entries(values["policy_entries"]),
            self_test_entry_map(values["anchor"], "anchor entries"),
            self_test_entry_map(values["candidate"], "candidate entries"),
        )
    elif validator == "preclosure":
        values = exact_mapping(arguments, {"packet"}, "preclosure vector")
        validate_preclosure_data(values["packet"])
    elif validator == "manifest_replay":
        values = exact_mapping(
            arguments,
            {"actual", "emitted", "returncode", "stderr"},
            "manifest-replay vector",
        )
        require(
            all(isinstance(values[key], str) for key in ("actual", "emitted", "stderr"))
            and type(values["returncode"]) is int,
            "manifest-replay vector fields are malformed",
        )
        validate_manifest_replay(
            actual=values["actual"].encode("utf-8"),
            emitted=values["emitted"].encode("utf-8"),
            returncode=values["returncode"],
            stderr=values["stderr"].encode("utf-8"),
        )
    elif validator == "credit":
        values = exact_mapping(
            arguments,
            {"allow_provisional", "inventory_status"},
            "credit vector",
        )
        require(
            isinstance(values["inventory_status"], str)
            and type(values["allow_provisional"]) is bool,
            "credit vector fields are malformed",
        )
        validate_credit_request(values["inventory_status"], values["allow_provisional"])
    elif validator == "strict_json":
        values = exact_mapping(
            arguments, {"raw", "require_canonical"}, "strict-JSON vector"
        )
        require(
            isinstance(values["raw"], str)
            and type(values["require_canonical"]) is bool,
            "strict-JSON vector fields are malformed",
        )
        parse_json_bytes(
            values["raw"].encode("utf-8"),
            "self-test JSON value",
            require_canonical=values["require_canonical"],
        )
    elif validator == "runtime_mode":
        values = exact_mapping(arguments, {"optimize"}, "runtime-mode vector")
        require(
            type(values["optimize"]) is int and values["optimize"] in {0, 1},
            "runtime-mode optimization value is malformed",
        )
        require(
            sys.flags.optimize == values["optimize"],
            "checker child optimization differs from its parent",
        )
    else:  # pragma: no cover -- envelope validation exhausts the fixed dispatch.
        raise PhaseError("self-test validator dispatch is inconsistent")


def emit_self_test_result(passed: bool) -> int:
    emit({"result": "pass" if passed else "fail"})
    return 0 if passed else 1


def run_self_test_vector_mode(arguments: argparse.Namespace) -> int:
    try:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None
            and not arguments.allow_provisional_diagnostic
            and not arguments.validate_policy_only
            and not arguments.emit_observed_delta
            and not arguments.self_test_sealed_index,
            "self-test vector mode cannot accompany other arguments",
        )
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        require(len(raw) <= MAX_JSON_BYTES, "self-test vector exceeds byte bound")
        request = parse_json_bytes(raw, "self-test vector", require_canonical=True)
        envelope = validate_self_test_vector_envelope(request)
    except PhaseError as error:
        print(f"KSG M1a self-test vector protocol failed: {error}", file=sys.stderr)
        return 2
    try:
        dispatch_self_test_vector(envelope)
    except PhaseError:
        return emit_self_test_result(False)
    return emit_self_test_result(True)


def run_self_test_sealed_index_mode(arguments: argparse.Namespace) -> int:
    try:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is not None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is not None
            and arguments.alternate_index_entry_count is not None
            and not arguments.allow_provisional_diagnostic
            and not arguments.validate_policy_only
            and not arguments.emit_observed_delta
            and not arguments.self_test_vectors,
            "sealed-index self-test mode has an invalid argument set",
        )
    except PhaseError as error:
        print(f"KSG M1a sealed-index test protocol failed: {error}", file=sys.stderr)
        return 2
    try:
        anchor_entries, _listing = parse_tree(ANCHOR_TREE)
        validate_alternate_index(
            0,
            arguments.alternate_index_sha256,
            arguments.alternate_index_entry_count,
            arguments.expected_candidate_tree,
            anchor_entries,
        )
    except PhaseError:
        return emit_self_test_result(False)
    return emit_self_test_result(True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--mode", choices=("precommit", "postcommit"))
    parser.add_argument("--expected-candidate-tree")
    parser.add_argument("--checkpoint-commit")
    parser.add_argument("--alternate-index-sha256")
    parser.add_argument("--alternate-index-entry-count", type=int)
    parser.add_argument("--allow-provisional-diagnostic", action="store_true")
    parser.add_argument("--validate-policy-only", action="store_true")
    parser.add_argument("--emit-observed-delta", action="store_true")
    parser.add_argument(
        "--self-test-vectors",
        action="store_true",
        help="run one fixed no-credit pure-validator vector from standard input",
    )
    parser.add_argument(
        "--self-test-sealed-index",
        action="store_true",
        help="run the fixed no-credit sealed-index validator on descriptor 0",
    )
    return parser.parse_args()


def emit(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json(value, pretty=False))
    sys.stdout.buffer.flush()


def main() -> int:
    arguments = parse_args()
    if arguments.self_test_vectors:
        return run_self_test_vector_mode(arguments)
    if arguments.self_test_sealed_index:
        return run_self_test_sealed_index_mode(arguments)
    policy, policy_raw, policy_entries = load_policy(verify_anchor=True)
    head, head_tree = validate_repository_context()
    anchor, listing = parse_tree(ANCHOR_TREE)
    require(
        len(anchor) == ANCHOR_ENTRY_COUNT
        and hashlib.sha256(listing).hexdigest() == ANCHOR_LISTING_SHA256,
        "anchor inventory changed",
    )
    if arguments.emit_observed_delta:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None
            and not arguments.allow_provisional_diagnostic
            and not arguments.validate_policy_only,
            "observed-delta mode cannot accompany validation arguments",
        )
        emit(
            {
                "anchor_commit": ANCHOR,
                "credit": "none_mechanical_observation_requires_human_review",
                "entries": observed_worktree_delta(anchor),
                "schema": "pid-rs/ksg-rev4-m1a-observed-delta-diagnostic/v1",
            }
        )
        return 0
    authority = policy["authority"]
    provisional = authority["inventory_status"] != "frozen"
    static_hashes = validate_static_artifacts(authority["inventory_status"])
    if arguments.validate_policy_only:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None
            and not arguments.allow_provisional_diagnostic,
            "policy-only mode cannot accompany lifecycle arguments",
        )
        emit(
            {
                "anchor_commit": ANCHOR,
                "credit": "none_policy_inventory_provisional"
                if provisional
                else "policy_frozen_not_lifecycle_credit",
                "entry_count": len(policy_entries),
                "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
                "schema": "pid-rs/ksg-rev4-m1a-policy-validation/v1",
                "static_artifact_sha256": static_hashes,
            }
        )
        return 0
    require(
        arguments.mode is not None
        and arguments.expected_candidate_tree is not None
        and arguments.checkpoint_commit is not None,
        "lifecycle validation requires mode, external tree, and detached checkpoint",
    )
    alternate_values = (
        arguments.alternate_index_sha256,
        arguments.alternate_index_entry_count,
    )
    if arguments.mode == "precommit":
        require(
            all(value is not None for value in alternate_values),
            "precommit validation requires the sealed alternate index on standard input, SHA-256, and entry count",
        )
    else:
        require(
            all(value is None for value in alternate_values),
            "postcommit validation forbids alternate-index arguments",
        )
    provisional = validate_credit_request(
        authority["inventory_status"], arguments.allow_provisional_diagnostic
    )
    candidate_tree = arguments.expected_candidate_tree
    checkpoint = arguments.checkpoint_commit
    require(
        HEX40.fullmatch(candidate_tree) is not None, "candidate tree id is malformed"
    )
    require(HEX40.fullmatch(checkpoint) is not None, "checkpoint id is malformed")
    candidate, _candidate_listing = parse_tree(candidate_tree)
    delta = validate_delta(policy_entries, anchor, candidate)
    envelope = parse_checkpoint(checkpoint, candidate_tree)
    require(
        git_text("rev-parse", f"{checkpoint}^{{tree}}") == candidate_tree,
        "checkpoint tree relation changed",
    )
    branch, active_operations = observe_lifecycle_metadata()
    validate_lifecycle_metadata(branch, active_operations)
    alternate_index_custody: dict[str, Any] | None = None
    if arguments.mode == "precommit":
        require(
            arguments.alternate_index_sha256 is not None
            and arguments.alternate_index_entry_count is not None,
            "precommit alternate-index arguments disappeared after validation",
        )
        alternate_index_custody = validate_alternate_index(
            0,
            arguments.alternate_index_sha256,
            arguments.alternate_index_entry_count,
            candidate_tree,
            candidate,
        )
    lifecycle = validate_worktree_lifecycle(
        arguments.mode, head, checkpoint, policy_entries, candidate
    )
    require(
        (arguments.mode == "precommit" and head_tree == ANCHOR_TREE)
        or (arguments.mode == "postcommit" and head_tree == candidate_tree),
        "HEAD tree is inconsistent with lifecycle mode",
    )
    validate_preclosure(candidate)
    manifest_sha256 = validate_current_source_manifest()
    emit(
        {
            "anchor": {"commit": ANCHOR, "tree": ANCHOR_TREE},
            "candidate": {
                "alternate_index_custody": alternate_index_custody,
                "checkpoint_commit": checkpoint,
                "commit_envelope": envelope,
                "delta": [
                    {"mode": mode, "path": path, "status": status}
                    for path, status, mode in delta
                ],
                "tree": candidate_tree,
            },
            "credit": "none_policy_inventory_provisional"
            if provisional
            else "external_tree_checkpoint_match",
            "current_source_manifest_sha256": manifest_sha256,
            "lifecycle": lifecycle,
            "repository_state": {
                "active_git_operations": [],
                "branch": "main",
                "ignored_paths_outside_source_projection_not_checked": True,
            },
            "mode": arguments.mode,
            "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
            "preclosure": {
                "final_decision_absent": True,
                "final_evidence_matrix_absent": True,
                "future_receipt_absent": True,
                "open_gate_count": 13,
                "status": "integration_no_go",
            },
            "schema": "pid-rs/ksg-rev4-m1a-phase-validation/v1",
            "static_artifact_sha256": static_hashes,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PhaseError as error:
        print(f"KSG M1a phase check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
