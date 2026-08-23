#!/usr/bin/env python3
"""Fail-closed semantic checker for the append-only composite-v12 lifecycle."""

from __future__ import annotations

import sys


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-m1a-composite-v12.py requires Python 3.11+ "
        "-I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import types
from typing import Any


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
REPOSITORY = "sepahead/pid-rs"
C9_COMMIT = "337fe9b7f7cf30a8f00138310ce0398d9e95b9c5"
C11_COMMIT = "91d954160a7e717ae46b6088175ae52e92570127"
C11_TREE = "97841c6eda10573ddc3537c9e3b2ca41a93a3fa1"
C11_MESSAGE = "Repair KSG M1a composite v11 contract\n"
R11_MESSAGE = "Record KSG M1a composite v11 receipt\n"
C12_MESSAGE = "Repair KSG M1a composite v12 contract\n"
R12_MESSAGE = "Record KSG M1a composite v12 receipt\n"
V11_RELATIVE = "scripts/check-ksg-m1a-composite-v11.py"
V11_PATH = ROOT / V11_RELATIVE
V11_SHA256 = "96aedfa1b4cf251d054203e32f8fb1dc425e6dcfdcbce60dfe89ce3ff8e1c9f8"
V11_SIZE_BYTES = 147_682
POLICY_PATH = "audit/evidence/ksg-rev4-m1a-composite-v12-path-policy-v1.json"
BOUNDARY_PATH = "audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md"
FAILURE_PATH = (
    "audit/evidence/ksg-rev4-m1a-composite-v11-local-closure-failure-"
    "v12-2026-08-23.json"
)
FAILURE_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-v11-failure-v12.schema.json"
HOSTED_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v12.schema.json"
LOCAL_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v12.schema.json"
RECEIPT_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-receipt-v12.schema.json"
HOSTED_TOOL = "scripts/capture-ksg-m1a-composite-v12.py"
LOCAL_TOOL = "scripts/capture-ksg-m1a-composite-v12-local-closure.py"
CHECKER = "scripts/check-ksg-m1a-composite-v12.py"
SELF_TEST = "scripts/check-ksg-m1a-composite-v12-self-test.py"
WORKFLOW = ".github/workflows/ksg-m1a-composite-v12.yml"
RETIRED_V11_WORKFLOW = ".github/workflows/ksg-m1a-composite-v11.yml"
CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
CURRENT_SOURCE_SELF_TEST = "scripts/check-current-source-state-v1-self-test.py"
CURRENT_SOURCE_MANIFEST = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_SCHEMA = "audit/schemas/current-source-state-v1.schema.json"
LEAN_CHECKER = "scripts/check-lean-toolchain-freeze.py"
LEAN_SELF_TEST = "scripts/check-lean-toolchain-freeze-self-test.py"
LEAN_R14_RECEIPT = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-19-r14.json"
)
LEAN_R14_PROJECTION_SHA256 = (
    "33f4ac70c5920f39c486203c3da4e78e532adb4f2f19b83fd919172f23711332"
)
LEAN_R14_HISTORY_FILE_LIMIT = 4 * 1024 * 1024
LEAN_R14_HISTORY_AGGREGATE_LIMIT = 32 * 1024 * 1024
LOCAL_EVIDENCE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v12-2026-08-23.json"
)
SUCCESSOR_CAPTURE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v12-2026-08-23.json"
)
RECEIPT = "audit/evidence/ksg-rev4-m1a-composite-receipt-v12-2026-08-23.json"
R11_EVIDENCE_PATHS = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v11-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v11-2026-08-23.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v11-2026-08-23.json",
)
R12_EVIDENCE_PATHS = (LOCAL_EVIDENCE, SUCCESSOR_CAPTURE, RECEIPT)
ORDINARY_LIMIT = 2 * 1024 * 1024
AGGREGATE_LIMIT = 16 * 1024 * 1024
VERSION_LIMIT = 64 * 1024
GIT_METADATA_LIMIT = 2 * 1024 * 1024
RECORD_LIMIT = 32 * 1024 * 1024
CAPTURE_BODY_LIMIT = 22 * 1024 * 1024
OID_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class BootstrapError(RuntimeError):
    """The exact frozen v11 checker primitive could not be loaded."""


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v11(path: Path = V11_PATH) -> bytes:
    before = path.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V11_SIZE_BYTES,
        "frozen v11 checker primitive metadata changed",
    )
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        bootstrap_require(
            (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
                opened.st_nlink,
                opened.st_size,
            )
            == (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_nlink,
                before.st_size,
            ),
            "opened frozen v11 checker primitive identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "short frozen v11 checker primitive read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(
            os.read(descriptor, 1) == b"", "frozen v11 checker primitive grew"
        )
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
        bootstrap_require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "frozen v11 checker primitive changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V11_SHA256,
        "frozen v11 checker primitive digest changed",
    )
    return raw


def load_bound_v11(raw: bytes) -> types.ModuleType:
    module_name = "pid_rs_check_ksg_m1a_composite_v11_frozen"
    bootstrap_require(
        module_name not in sys.modules, "frozen v11 module name is occupied"
    )
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(V11_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V11_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


try:
    V11_RAW = read_bound_v11()
    V11 = load_bound_v11(V11_RAW)
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print(
        "ERROR: unexpected frozen-v11 checker primitive load failure", file=sys.stderr
    )
    raise SystemExit(2) from None


ContractError = V11.ContractError
require = V11.require
refuse = V11.refuse
ExpectedAuthority = V11.ExpectedAuthority
ordinary = V11.ordinary
TreeEntry = V11.TreeEntry
CommitEnvelope = V11.CommitEnvelope

EXPECTED_AUTHORITIES = tuple(
    sorted(
        (
            ordinary(".github/workflows/ci.yml", "repository_ci_authority"),
            ordinary(RETIRED_V11_WORKFLOW, "retired_v11_manual_refusal"),
            ordinary(WORKFLOW, "dedicated_v12_workflow_authority"),
            ordinary(".gitleaks.toml", "narrow_secret_scan_policy_authority"),
            ordinary("crates/pid-core/build_support.rs", "rust_1_98_parser_repair"),
            ordinary("justfile", "local_command_wiring"),
            ordinary(BOUNDARY_PATH, "v12_semantic_boundary"),
            ordinary(POLICY_PATH, "v12_path_policy"),
            ExpectedAuthority(
                FAILURE_PATH,
                "consumed_l11_failure_diagnostic",
                "100644",
                0o644,
                "ordinary_2mib",
                False,
            ),
            ordinary(FAILURE_SCHEMA, "consumed_l11_failure_schema"),
            ordinary(HOSTED_SCHEMA, "v12_hosted_capture_schema"),
            ordinary(LOCAL_SCHEMA, "local_l12_closure_schema"),
            ordinary(RECEIPT_SCHEMA, "v12_receipt_schema"),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v8.py", "frozen_v8_hosted_transport"
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v8-local-closure.py",
                "frozen_v8_local_transport",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v11.py",
                "frozen_v11_hosted_transport",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v11-local-closure.py",
                "frozen_v11_local_transport",
            ),
            ordinary(V11_RELATIVE, "frozen_v11_checker_primitives"),
            ordinary(
                "scripts/check-ksg-m1a-composite-v11-self-test.py",
                "frozen_v11_checker_hostile_suite",
            ),
            ordinary(HOSTED_TOOL, "bounded_hosted_v12_capture_tool"),
            ordinary(LOCAL_TOOL, "bounded_local_l12_capture_tool"),
            ordinary(CHECKER, "composite_v12_semantic_gate"),
            ordinary(SELF_TEST, "composite_v12_hostile_suite"),
            ordinary(
                "scripts/normalize-actions-checkout-git-info-exclude.py",
                "git_info_exclude_normalizer",
            ),
            ordinary(
                "scripts/normalize-actions-checkout-git-info-exclude-self-test.py",
                "git_info_exclude_hostile_suite",
            ),
            ordinary(
                "scripts/check-certified-sxpid2-claim.py", "certified_sxpid_claim_gate"
            ),
            ordinary(
                "scripts/check-certified-sxpid2-claim-self-test.py",
                "certified_sxpid_claim_hostile_suite",
            ),
            ordinary(LEAN_CHECKER, "current_c12_lean_freeze_gate"),
            ordinary(LEAN_SELF_TEST, "current_c12_lean_freeze_hostile_suite"),
            ordinary(LEAN_R14_RECEIPT, "preserved_lean_r14_receipt"),
            ordinary(
                CURRENT_SOURCE_CHECKER, "current_source_semantic_gate", executable=True
            ),
            ordinary(
                CURRENT_SOURCE_MANIFEST,
                "fresh_current_source_generation_17_manifest",
            ),
            ordinary(CURRENT_SOURCE_SCHEMA, "current_source_manifest_schema"),
            ordinary(
                CURRENT_SOURCE_SELF_TEST,
                "current_source_hostile_suite",
                executable=True,
            ),
        ),
        key=lambda item: item.path,
    )
)
EXPECTED_BY_PATH = {item.path: item for item in EXPECTED_AUTHORITIES}
LIMITS = {"ordinary_2mib": ORDINARY_LIMIT}
EXPECTED_C12_DELTA = tuple(
    sorted(
        (
            (".github/workflows/ksg-m1a-composite-v11.yml", "M", "100644"),
            (WORKFLOW, "A", "100644"),
            ("CHANGELOG.md", "M", "100644"),
            ("justfile", "M", "100644"),
            ("scripts/check-certified-sxpid2-claim.py", "M", "100644"),
            ("scripts/check-certified-sxpid2-claim-self-test.py", "M", "100644"),
            (LEAN_CHECKER, "M", "100644"),
            (LEAN_SELF_TEST, "M", "100644"),
            (CURRENT_SOURCE_MANIFEST, "M", "100644"),
            (BOUNDARY_PATH, "A", "100644"),
            (POLICY_PATH, "A", "100644"),
            (FAILURE_PATH, "A", "100644"),
            (FAILURE_SCHEMA, "A", "100644"),
            (HOSTED_SCHEMA, "A", "100644"),
            (LOCAL_SCHEMA, "A", "100644"),
            (RECEIPT_SCHEMA, "A", "100644"),
            (HOSTED_TOOL, "A", "100644"),
            (LOCAL_TOOL, "A", "100644"),
            (CHECKER, "A", "100644"),
            (SELF_TEST, "A", "100644"),
        )
    )
)
EXPECTED_R12_DELTA = tuple(
    sorted(
        (
            (CURRENT_SOURCE_MANIFEST, "M", "100644"),
            (LOCAL_EVIDENCE, "A", "100644"),
            (SUCCESSOR_CAPTURE, "A", "100644"),
            (RECEIPT, "A", "100644"),
        )
    )
)
LOCAL_LIMITS = {
    "authority_aggregate_bytes": AGGREGATE_LIMIT,
    "command_stream_bytes": 8 * 1024 * 1024,
    "executable_bytes": 256 * 1024 * 1024,
    "ordinary_authority_bytes": ORDINARY_LIMIT,
    "record_bytes": RECORD_LIMIT,
    "version_stream_bytes": VERSION_LIMIT,
}
LOCAL_V8 = {
    "path": "scripts/capture-ksg-m1a-composite-v8-local-closure.py",
    "sha256": "b9b0a41cb2027d1cba464040843656bc2486e317f8cf1d3079cb58b02f7c6ba7",
    "size_bytes": 40_584,
}
LOCAL_V11 = {
    "path": "scripts/capture-ksg-m1a-composite-v11-local-closure.py",
    "sha256": "e86afacbcc089d19d7e6b5e1e3415cfe2f1a6455f2645095d5bccf54016ceb6d",
    "size_bytes": 53_843,
}
HOSTED_V8 = {
    "path": "scripts/capture-ksg-m1a-composite-v8.py",
    "sha256": "79ffbe59dc57ed99d2b4032aa71cac300448d0978a42a52fcf7b40b08236ae6f",
    "size_bytes": 24_111,
}
HOSTED_V11 = {
    "path": "scripts/capture-ksg-m1a-composite-v11.py",
    "sha256": "2602fc868b92621e1109658845779d70fc870d6522222128c427ba5cfea7b191",
    "size_bytes": 25_607,
}
STATIC_SOURCE_SHA256 = {
    BOUNDARY_PATH: "86a7e12ead9d0ccd454bbe1a933042392f606f22946dbb88d148c15b075fa022",
    POLICY_PATH: "1c316334c2f16f3089b108c98c9c7a2295b8ebf163ff717f184e2e3c26baef07",
    FAILURE_SCHEMA: "284170a439c9f145cf7a39f471f8e160c06c1051062fe660c659675d5a9e53df",
    HOSTED_SCHEMA: "68105ab85232db25df0ea41ffa6e3e36e57b7b80c9e6b6653f50459709382055",
    LOCAL_SCHEMA: "40ee3152c3d97df3477a9ffbb8d694ae1588366944c377fa3f1e9334d3174bda",
    RECEIPT_SCHEMA: "c00bcde8cea4427fd9218e5586d14b2707c9f88c3e74e9c46135a282af5cc171",
    WORKFLOW: "f6e58072ba2fdd3a7346b638fec4f671b8d256bd8ffbde469f295c331f945bab",
    RETIRED_V11_WORKFLOW: "dd2a03a8c3b2744db2a31e26344b551930e88096b91222493eb52d3d799e40d2",
    LEAN_CHECKER: "b35bc9f2ce173bee70fda01c31ded6a2a84ffabfcf2633b9c789451339a66dcf",
    LEAN_SELF_TEST: "bf7dbdc1f4f05406d36aa84a6a0bd2e98bf5748a3550f7aa26f017dc1664623b",
    LEAN_R14_RECEIPT: "a6a37dea6e22fb948273c045a4ec4f2b7b355d5a99ff1e7fa9b411bb73086805",
}
LOCAL_NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C12 checkout and is neither independent replication nor hosted first-attempt authority.",
    "The consumed failed L11, false Q11, and permanently unissued R11 grant no L12 or C12 qualification credit.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, builtins, libraries, TeX helpers, or transitive processes.",
    "Every authority is capped at 2 MiB and the complete roster at 16 MiB; a nearby path or role receives no larger implicit class.",
    "The redacted environment-route digest is an opaque correlated fingerprint, not a publicly recomputable path authority.",
    "HOME is absent; isolated XDG and TeX roots do not prove absence of every passwd-derived fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove every descendant was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove output contains no sensitive information.",
    "Ordinary Git status plus selected metadata checks exclude ignored products and uninspected Git metadata, so this is not hermetic closure.",
    "A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
]
HOSTED_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Two retrieval repetitions are correlated provider observations, not independent replications.",
    "The consumed failed L11, false Q11, and permanently unissued R11 grant no C12 qualification credit.",
    "Repository-CI, CodeQL, and dedicated-v12 are separate correlated provider observations; no common cause is inferred.",
    "A successful capture is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "The capture binds the wrapper and frozen transport bytes, but cannot prove which bytes the operating system executed or exclude interference.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]
RECEIPT_NONIMPLICATIONS = [
    "Q12 is an operational conjunction for one exact C12 identity, not PID, KSG, theorem, numerical, security, privacy, accessibility, or application validation.",
    "L12 records one bounded local execution and cannot prove hermeticity, operator uniqueness, or absence of an undisclosed parallel launch.",
    "GitHub response bytes, repeated retrievals, timestamps, digests, and unsigned Git objects do not authenticate themselves or establish trusted time.",
    "CodeQL analysis and alert endpoints are repository-level current-state observations rather than run-foreign-keyed historical facts.",
    "C11, consumed failed L11, false Q11, and permanently unissued R11 grant no evidence or qualification credit to C12 or R12.",
]


def validate_authority_specification() -> None:
    paths = [item.path for item in EXPECTED_AUTHORITIES]
    roles = [item.role for item in EXPECTED_AUTHORITIES]
    require(
        len(EXPECTED_AUTHORITIES) == 34
        and paths == sorted(paths)
        and len(paths) == len(set(paths))
        and len(roles) == len(set(roles))
        and all(item.limit_class == "ordinary_2mib" for item in EXPECTED_AUTHORITIES),
        "v12 authority paths, roles, or resource classes changed",
    )
    require(
        EXPECTED_BY_PATH[CURRENT_SOURCE_CHECKER].git_mode == "100755"
        and EXPECTED_BY_PATH[CURRENT_SOURCE_SELF_TEST].git_mode == "100755",
        "current-source executable mode contract changed",
    )


def validate_live_authorities(head: str, *, strict: bool) -> dict[str, Any]:
    validate_authority_specification()
    root_fd, root_identity = V11.open_canonical_root(ROOT)
    aggregate = 0
    pending: list[str] = []
    states: dict[str, int] = {}
    try:
        for authority in EXPECTED_AUTHORITIES:
            try:
                raw = V11.stable_read(root_fd, authority)
            except FileNotFoundError:
                require(
                    not strict and not authority.authoring_required,
                    f"required v12 authority absent: {authority.path}",
                )
                pending.append(authority.path)
                states["pending_evidence_absent"] = (
                    states.get("pending_evidence_absent", 0) + 1
                )
                continue
            aggregate += len(raw)
            require(
                aggregate <= AGGREGATE_LIMIT, "v12 authority aggregate exceeds 16 MiB"
            )
            live_oid = V11.git_oid("blob", raw)
            entry = V11.tree_entry(head, authority.path)
            state = "prospective_not_in_head"
            if entry is not None:
                mode, oid = entry
                committed = V11.verify_object("blob", oid, ORDINARY_LIMIT)
                state = (
                    "bound_to_head"
                    if mode == authority.git_mode
                    and oid == live_oid
                    and committed == raw
                    else "worktree_differs_from_head"
                )
            require(
                not strict or state == "bound_to_head",
                f"unbound v12 authority: {authority.path}",
            )
            states[state] = states.get(state, 0) + 1
    finally:
        V11.recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)
    require(pending in ([], [FAILURE_PATH]), "unexpected pending v12 authority")
    return {
        "aggregate_bytes": aggregate,
        "pending": pending,
        "states": dict(sorted(states.items())),
    }


def is_ancestor_in_envelopes(
    ancestor: str, descendant: str, envelopes: dict[str, CommitEnvelope]
) -> bool:
    frontier = [descendant]
    visited: set[str] = set()
    while frontier:
        current = frontier.pop()
        if current == ancestor:
            return True
        if current in visited:
            continue
        visited.add(current)
        envelope = envelopes.get(current)
        if envelope is not None:
            frontier.extend(envelope.parents)
    return False


def introduction_commits(
    path: str,
    envelopes: dict[str, CommitEnvelope],
    selected: dict[str, dict[str, TreeEntry]],
) -> list[str]:
    introductions: list[str] = []
    for oid, envelope in envelopes.items():
        if path not in selected[oid]:
            continue
        if not envelope.parents or all(
            path not in selected[parent] for parent in envelope.parents
        ):
            introductions.append(oid)
    return introductions


def analyze_lifecycle_projection(
    head: str,
    envelopes: dict[str, CommitEnvelope],
    selected: dict[str, dict[str, TreeEntry]],
) -> dict[str, Any]:
    require(
        head in envelopes
        and C11_COMMIT in envelopes
        and set(envelopes) == set(selected)
        and all(
            parent in selected
            for envelope in envelopes.values()
            for parent in envelope.parents
        ),
        "reachable lifecycle projection is incomplete",
    )
    c11 = envelopes[C11_COMMIT]
    require(
        c11.tree == C11_TREE
        and c11.parents == (C9_COMMIT,)
        and c11.message == C11_MESSAGE
        and not c11.signed,
        "fixed C11 envelope changed",
    )
    require(
        is_ancestor_in_envelopes(C11_COMMIT, head, envelopes),
        "C11 is not an ancestor of HEAD",
    )
    c12_candidates = [
        oid
        for oid, envelope in envelopes.items()
        if envelope.parents == (C11_COMMIT,) and envelope.message == C12_MESSAGE
    ]
    c12 = V11.unique_lifecycle_identity(c12_candidates, "C12")
    require(not envelopes[c12].signed, "C12 is signed")

    for oid, envelope in envelopes.items():
        if envelope.message == C11_MESSAGE:
            require(oid == C11_COMMIT, "C11 lifecycle message was reused")
        if envelope.message == R11_MESSAGE:
            refuse("R11 lifecycle message is reachable after failed L11")
        if envelope.message == C12_MESSAGE:
            require(oid == c12, "C12 lifecycle message was reused")
        require(
            all(path not in selected[oid] for path in R11_EVIDENCE_PATHS),
            "R11 evidence is reachable after failed L11",
        )
    require(
        introduction_commits(FAILURE_PATH, envelopes, selected) == [c12],
        "C11 failure diagnostic was not introduced exactly by C12",
    )

    r12_candidates = [
        oid
        for oid, envelope in envelopes.items()
        if envelope.parents == (c12,) and envelope.message == R12_MESSAGE
    ]
    introductions = {
        path: introduction_commits(path, envelopes, selected)
        for path in R12_EVIDENCE_PATHS
    }
    if not any(introductions.values()) and not r12_candidates:
        require(head == c12, "receipt-absent lifecycle is not exact C12")
        for envelope in envelopes.values():
            require(
                envelope.message != R12_MESSAGE,
                "R12 message is reused without evidence",
            )
        return {"c12": c12, "phase": "candidate", "r12": None}

    r12 = V11.unique_lifecycle_identity(r12_candidates, "R12")
    require(not envelopes[r12].signed, "R12 is signed")
    require(
        all(values == [r12] for values in introductions.values()),
        "R12 evidence introduction is absent, split, reused, or ambiguous",
    )
    require(
        is_ancestor_in_envelopes(r12, head, envelopes), "R12 is not an ancestor of HEAD"
    )
    for oid, envelope in envelopes.items():
        if envelope.message == R12_MESSAGE:
            require(oid == r12, "R12 lifecycle message was reused")
        if is_ancestor_in_envelopes(r12, oid, envelopes):
            for path in R12_EVIDENCE_PATHS:
                require(
                    selected[oid].get(path) == selected[r12].get(path),
                    f"R12 evidence bytes or mode changed in descendant: {path}",
                )
    return {
        "c12": c12,
        "phase": "receipt" if head == r12 else "preservation",
        "r12": r12,
    }


def locate_lifecycle(head: str) -> dict[str, Any]:
    V11.verify_ancestor(C11_COMMIT, head)
    commits = V11.reachable_commits(head)
    require(C11_COMMIT in commits, "fixed C11 is absent from reachable history")
    envelopes = {oid: V11.commit_envelope(oid) for oid in commits}
    projection_paths = (*R11_EVIDENCE_PATHS, *R12_EVIDENCE_PATHS, FAILURE_PATH)
    selected = {
        oid: V11.selected_tree_entries(oid, projection_paths) for oid in commits
    }
    result = analyze_lifecycle_projection(head, envelopes, selected)
    c12 = result["c12"]
    c11_entries = V11.recursive_tree_entries(C11_COMMIT)
    c12_entries = V11.recursive_tree_entries(c12)
    require(
        V11.changed_rows(c11_entries, c12_entries) == EXPECTED_C12_DELTA,
        "C11-to-C12 delta differs from the exact twenty-row cut",
    )
    result["c12_tree"] = envelopes[c12].tree
    r12 = result["r12"]
    if r12 is not None:
        r12_entries = V11.recursive_tree_entries(r12)
        require(
            V11.changed_rows(c12_entries, r12_entries) == EXPECTED_R12_DELTA,
            "C12-to-R12 delta differs from the exact four-row receipt cut",
        )
        result["r12_tree"] = envelopes[r12].tree
    else:
        result["r12_tree"] = None
    return result


FAILURE_NONIMPLICATIONS = [
    "The first observed release-line mismatch does not imply that either latent whole-file mismatch was reached by L11.",
    "The later source diagnosis is not a reconstruction of a local closure record; the v11 recorder emitted no L11 record on failure.",
    "A diagnostic replay of just ksg-composite-v11 cannot become L11 or reverse the one-shot consumption rule.",
    "The mismatch does not imply a PID, KSG, theorem, estimator, numerical, security, privacy, accessibility, or application defect.",
    "The repaired bindings and their finite hostile suites do not prove absence of every semantic bypass or execution interference.",
]
EXPECTED_FAILURE_SURFACES = [
    {
        "classification": "latent_not_reached",
        "expected_sha256": "9a70c744b57ccf5ca222fc9e8d0cd3f159276db8927f454a647d5d2be4bcd219",
        "observed_sha256": "17b252ff25e881b4f1d01af13f88572c54ed6b221e4b5157fcacc7aae7efafc5",
        "surface": "ci_full_file",
    },
    {
        "classification": "unchanged_positive_control",
        "expected_sha256": "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda",
        "observed_sha256": "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda",
        "surface": "certified_ci_job",
    },
    {
        "classification": "unchanged_positive_control",
        "expected_sha256": "fbd80548b0c62cb46f646e77e5f1df37d439299e71faec9bd05656839f660ae7",
        "observed_sha256": "fbd80548b0c62cb46f646e77e5f1df37d439299e71faec9bd05656839f660ae7",
        "surface": "certified_just_recipe",
    },
    {
        "classification": "latent_not_reached",
        "expected_sha256": "93399171cfbb743dba93c7be1ec85e446a33193e41ada3977d198b0e4ecc6437",
        "observed_sha256": "ec035caae045135ffdc73da3d06ead1bf8815ad4dfc9f9a82893d91c82e7353a",
        "surface": "just_full_file",
    },
    {
        "classification": "first_observed_blocker",
        "expected_sha256": "8ec3a9d007658116e7c400a09a05a3f58f085db39b8fc2ca5e865b4dd3c98ea6",
        "observed_sha256": "3b5707c46f519d34af265340f4ccc707a12ada38ff64d29d648cff4da4fb107c",
        "surface": "release_audit_line",
    },
]


def validate_failure_diagnostic(value: Any) -> None:
    root = V11.exact_keys(
        value,
        {
            "credit",
            "diagnosis",
            "first_observed_failure",
            "nonimplications",
            "repository",
            "schema",
            "schema_revision",
            "subject",
        },
        "C11 consumed-L11 failure diagnostic",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"]
        == "pid-rs/ksg-rev4-m1a-composite-v11-local-closure-failure/v12"
        and root["schema_revision"] == 12
        and root["credit"]
        == {
            "c12_qualification": "none",
            "l11": "consumed_failed",
            "q11": False,
            "r11": "permanently_unissued",
        }
        and root["subject"]
        == {
            "c11_commit": C11_COMMIT,
            "c11_message": C11_MESSAGE,
            "c11_parent": C9_COMMIT,
            "c11_tree": C11_TREE,
        }
        and root["first_observed_failure"]
        == {
            "command": ["just", "ksg-composite-v11"],
            "error": "certified SxPID2 claim check failed: release-audit just dependency line exact digest changed",
            "exit_code": 1,
            "phase": "local_L11_command",
            "production_launch_consumed": True,
            "record_emitted": False,
        }
        and root["diagnosis"]
        == {"complete": True, "surfaces": EXPECTED_FAILURE_SURFACES}
        and root["nonimplications"] == FAILURE_NONIMPLICATIONS,
        "C11 consumed-L11 failure diagnostic changed",
    )


def validate_policy(value: Any) -> None:
    root = V11.exact_keys(
        value,
        {
            "authority_contract",
            "c11",
            "c12",
            "l12",
            "nonimplications",
            "qualification",
            "r12",
            "current_source_generation",
            "repository",
            "schema",
            "schema_revision",
            "state",
        },
        "v12 policy",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-v12-path-policy/v1"
        and root["schema_revision"] == 1
        and root["state"] == "candidate_authoring_no_evidence"
        and root["c11"]
        == {
            "commit": C11_COMMIT,
            "failure_record": FAILURE_PATH,
            "l11": "consumed_failed",
            "q11": False,
            "r11": "permanently_unissued",
            "tree": C11_TREE,
        }
        and root["c12"]["parent"] == C11_COMMIT
        and root["c12"]["message"] == C12_MESSAGE
        and root["qualification"]["formula"]
        == "Q12 = L12 AND CI12_attempt1 AND CodeQL12_attempt1 AND Dedicated12_attempt1"
        and root["qualification"]["attempt"] == 1
        and root["qualification"]["status"] == "not_run"
        and root["l12"]["status"] == "not_produced"
        and root["l12"]["preflight_consumes_attempt"] is False
        and root["r12"]["message"] == R12_MESSAGE
        and root["r12"]["status"] == "unissued"
        and root["current_source_generation"]
        == {
            "fresh_after_exact_c12_bytes_settle": True,
            "generation_slot": 17,
            "namespace": (
                "current_source_generation_slot_distinct_from_composite_r12_"
                "receipt_lean_r14_replay_and_current_source_schema_revision"
            ),
            "precondition": (
                "c11_failure_diagnostic_reviewed_and_added_before_manifest_generation"
            ),
            "prior_manifest_reuse": False,
            "status": "generated_fresh",
        },
        "v12 policy identity or staging changed",
    )
    authority = root["authority_contract"]
    require(
        authority["default_limit_bytes"] == ORDINARY_LIMIT
        and authority["aggregate_limit_bytes"] == AGGREGATE_LIMIT
        and authority["special_limits"] == []
        and authority["single_structure"] == "AuthoritySpec"
        and "pass_not_atomic" in authority["concurrency_boundary"]
        and "checksum_bound_module_execution" in authority["frozen_v11_reuse"],
        "v12 authority policy changed",
    )


def validate_schema(value: Any, path: str) -> None:
    root = V11.exact_keys(
        value,
        set(value) if type(value) is dict else set(),
        f"v12 schema {path}",
    )
    require(
        root.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        f"v12 schema dialect changed: {path}",
    )
    if path == FAILURE_SCHEMA:
        require(
            root.get("additionalProperties") is False
            and root["properties"]["schema"]["const"]
            == "pid-rs/ksg-rev4-m1a-composite-v11-local-closure-failure/v12"
            and root["properties"]["schema_revision"] == {"const": 12},
            "failure schema critical contract changed",
        )
    elif path == HOSTED_SCHEMA:
        successor = root["$defs"]["successorDocument"]
        require(
            root.get("$ref") == "#/$defs/successorDocument"
            and successor["additionalProperties"] is False
            and successor["properties"]["schema_revision"] == {"const": 12}
            and "immutable_v11_primitives" in successor["required"],
            "hosted schema critical contract changed",
        )
    elif path == LOCAL_SCHEMA:
        properties = root["properties"]
        require(
            root.get("additionalProperties") is False
            and properties["authorities"]["minItems"] == len(EXPECTED_AUTHORITIES)
            and properties["authorities"]["maxItems"] == len(EXPECTED_AUTHORITIES)
            and properties["limits"] == {"const": LOCAL_LIMITS}
            and properties["schema_revision"] == {"const": 12}
            and properties["subject"]["properties"]["c11_parent"]
            == {"const": C11_COMMIT},
            "local schema critical contract changed",
        )
    elif path == RECEIPT_SCHEMA:
        properties = root["properties"]
        require(
            root.get("additionalProperties") is False
            and properties["schema_revision"] == {"const": 12}
            and properties["subject"]["properties"]["parent"] == {"const": C11_COMMIT}
            and properties["qualification"]["properties"]["attempt"] == {"const": 1},
            "receipt schema critical contract changed",
        )
    else:
        refuse(f"unknown v12 schema: {path}")


def validate_workflows_and_wiring(active: str, retired: str, just: str) -> None:
    require(
        "push:" in active
        and "workflow_dispatch:" in active
        and "KSG M1a composite v12" in active
        and "capture-ksg-m1a-composite-v12.py --self-test" in active
        and "capture-ksg-m1a-composite-v12-local-closure.py --self-test" in active
        and "capture-ksg-m1a-composite-v12-local-closure.py --preflight-live" in active
        and "check-ksg-m1a-composite-v12-self-test.py" in active
        and "check-ksg-m1a-composite-v12.py --workflow" in active
        and "GITHUB_RUN_ATTEMPT" in active
        and 'test "${GITHUB_EVENT_NAME}" = "push"' in active
        and "continue-on-error" not in active
        and "[skip ci]" not in active,
        "active v12 workflow semantics changed",
    )
    require(
        "workflow_dispatch:" in retired
        and "push:" not in retired
        and "exit 1" in retired
        and "C11 is permanently consumed" in retired,
        "retired v11 workflow regained a qualification route",
    )
    require(
        "ksg-composite-v11:" in just
        and "C11 L11 attempt is permanently consumed; refusing replay" in just
        and "ksg-composite-v12:" in just
        and "check-ksg-m1a-composite-v12.py --auto" in just
        and re.search(r"^release-audit:.*\bksg-composite-v12\b", just, re.MULTILINE)
        is not None
        and not re.search(
            r"^release-audit:.*\bksg-composite-v11\b", just, re.MULTILINE
        ),
        "v12 Just lifecycle wiring changed",
    )


def validate_static_source_digest(path: str, raw: bytes) -> None:
    require(
        path in STATIC_SOURCE_SHA256
        and hashlib.sha256(raw).hexdigest() == STATIC_SOURCE_SHA256[path],
        f"v12 reviewed static source digest changed: {path}",
    )


def validate_lean_r14_history(
    receipt_raw: bytes,
    current_checker_raw: bytes,
    current_self_test_raw: bytes,
) -> None:
    receipt = V11.parse_json(
        receipt_raw, "preserved Lean r14 receipt", maximum=ORDINARY_LIMIT
    )
    require(
        receipt_raw == V11.pretty_json(receipt),
        "preserved Lean r14 receipt is not canonical pretty JSON",
    )
    require(type(receipt) is dict, "preserved Lean r14 receipt is not an object")
    operational = receipt.get("operational_wiring_sha256")
    final_custody = receipt.get("custody_gate_sha256")
    replay_custody = receipt.get("replay_custody_gate_sha256")
    custody_paths = (LEAN_SELF_TEST, LEAN_CHECKER)
    require(
        type(operational) is dict
        and len(operational) == 158
        and list(operational) == sorted(operational)
        and type(final_custody) is dict
        and tuple(final_custody) == custody_paths
        and type(replay_custody) is dict
        and tuple(replay_custody) == custody_paths,
        "preserved Lean r14 operational/custody inventories changed",
    )

    historical_total = 0
    for path, digest in operational.items():
        require(
            type(path) is str
            and path
            and not path.startswith("/")
            and all(component not in {"", ".", ".."} for component in path.split("/"))
            and type(digest) is str
            and SHA256_RE.fullmatch(digest) is not None,
            "preserved Lean r14 operational entry is malformed",
        )
        raw = V11.tree_blob(C9_COMMIT, path, LEAN_R14_HISTORY_FILE_LIMIT)
        historical_total += len(raw)
        require(
            hashlib.sha256(raw).hexdigest() == digest,
            f"preserved Lean r14 operational digest differs from exact C9: {path}",
        )

    c9_self_test = V11.tree_blob(C9_COMMIT, LEAN_SELF_TEST, LEAN_R14_HISTORY_FILE_LIMIT)
    c9_checker = V11.tree_blob(C9_COMMIT, LEAN_CHECKER, LEAN_R14_HISTORY_FILE_LIMIT)
    historical_total += len(c9_self_test) + len(c9_checker)
    require(
        hashlib.sha256(c9_self_test).hexdigest()
        == final_custody[LEAN_SELF_TEST]
        == replay_custody[LEAN_SELF_TEST]
        and hashlib.sha256(c9_checker).hexdigest() == final_custody[LEAN_CHECKER],
        "preserved Lean r14 final custody differs from exact C9 bytes",
    )
    final_projection = (
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "'
        + LEAN_R14_PROJECTION_SHA256.encode("ascii")
        + b'"'
    )
    placeholder_projection = b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    require(
        c9_checker.count(final_projection) == 1
        and placeholder_projection not in c9_checker,
        "exact-C9 Lean r14 projection literal is not uniquely reconstructable",
    )
    require(
        hashlib.sha256(
            c9_checker.replace(final_projection, placeholder_projection, 1)
        ).hexdigest()
        == replay_custody[LEAN_CHECKER],
        "preserved Lean r14 replay custody differs from exact C9 pre-pin bytes",
    )
    require(
        historical_total <= LEAN_R14_HISTORY_AGGREGATE_LIMIT,
        "preserved Lean r14 C9-byte verification exceeded its aggregate bound",
    )
    require(
        hashlib.sha256(current_checker_raw).hexdigest() != final_custody[LEAN_CHECKER]
        and hashlib.sha256(current_self_test_raw).hexdigest()
        != final_custody[LEAN_SELF_TEST]
        and b"PRESERVED_R14_OPERATIONAL_WIRING_HASHES" in current_checker_raw
        and b"EXPECTED_OPERATIONAL_WIRING_HASHES" in current_checker_raw,
        "current-C12 Lean gate was conflated with preserved r14 custody",
    )


def validate_source_surfaces(root_fd: int) -> dict[str, bytes]:
    raws: dict[str, bytes] = {}
    for path in (
        BOUNDARY_PATH,
        POLICY_PATH,
        FAILURE_SCHEMA,
        HOSTED_SCHEMA,
        LOCAL_SCHEMA,
        RECEIPT_SCHEMA,
        WORKFLOW,
        RETIRED_V11_WORKFLOW,
        LEAN_CHECKER,
        LEAN_SELF_TEST,
        LEAN_R14_RECEIPT,
        "justfile",
    ):
        raws[path] = V11.stable_read(root_fd, EXPECTED_BY_PATH[path])
        if path in STATIC_SOURCE_SHA256:
            validate_static_source_digest(path, raws[path])
    policy = V11.parse_json(raws[POLICY_PATH], "v12 policy")
    require(
        raws[POLICY_PATH] == V11.pretty_json(policy), "v12 policy is not canonical JSON"
    )
    validate_policy(policy)
    for path in (FAILURE_SCHEMA, HOSTED_SCHEMA, LOCAL_SCHEMA, RECEIPT_SCHEMA):
        value = V11.parse_json(raws[path], path)
        require(
            raws[path] == V11.pretty_json(value),
            f"schema is not canonical JSON: {path}",
        )
        validate_schema(value, path)
    validate_workflows_and_wiring(
        raws[WORKFLOW].decode("utf-8", errors="strict"),
        raws[RETIRED_V11_WORKFLOW].decode("utf-8", errors="strict"),
        raws["justfile"].decode("utf-8", errors="strict"),
    )
    validate_lean_r14_history(
        raws[LEAN_R14_RECEIPT], raws[LEAN_CHECKER], raws[LEAN_SELF_TEST]
    )
    for path in (
        HOSTED_TOOL,
        LOCAL_TOOL,
        CHECKER,
        SELF_TEST,
        LEAN_CHECKER,
        LEAN_SELF_TEST,
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-certified-sxpid2-claim-self-test.py",
    ):
        raw = V11.stable_read(root_fd, EXPECTED_BY_PATH[path])
        V11.validate_no_duplicate_literal_dict_keys(raw, path)
    return raws


def validate_local_snapshot(value: Any, c12: str, c12_tree: str, label: str) -> Any:
    snapshot = V11.exact_keys(
        value,
        {
            "alternates",
            "common_dir",
            "config_overlays",
            "git_dir",
            "grafts",
            "head",
            "http_alternates",
            "info_attributes_rules",
            "info_exclude_rules",
            "message",
            "object_format",
            "observed_at",
            "parent",
            "replacement_refs",
            "shallow",
            "status",
            "tree",
            "worktree_root",
        },
        f"{label} L12 repository snapshot",
    )
    require(
        snapshot["alternates"] == "absent"
        and snapshot["common_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["config_overlays"] == "absent"
        and snapshot["git_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["grafts"] == "absent"
        and snapshot["head"] == c12
        and snapshot["http_alternates"] == "absent"
        and snapshot["info_attributes_rules"] == "absent"
        and snapshot["info_exclude_rules"] == "absent"
        and snapshot["message"] == C12_MESSAGE
        and snapshot["object_format"] == "sha1"
        and snapshot["parent"] == C11_COMMIT
        and snapshot["replacement_refs"] == []
        and snapshot["shallow"] == "absent"
        and snapshot["tree"] == c12_tree
        and snapshot["worktree_root"] == "<REPOSITORY_ROOT>"
        and V11.decode_binding(snapshot["status"], f"{label} Git status", 0) == b"",
        f"{label} L12 repository snapshot identity changed",
    )
    return V11.parse_utc_timestamp(snapshot["observed_at"], f"{label} observation")


def validate_local_evidence(raw: bytes, c12: str, c12_tree: str) -> dict[str, Any]:
    value = V11.parse_json(raw, "L12 local closure", maximum=RECORD_LIMIT)
    require(
        raw == V11.pretty_json(value), "L12 local closure is not canonical pretty JSON"
    )
    root = V11.exact_keys(
        value,
        {
            "authorities",
            "immutable_v8_primitives",
            "immutable_v11_primitives",
            "invocation",
            "limits",
            "nonimplications",
            "platform",
            "repository",
            "repository_state",
            "reviewed_executables",
            "schema",
            "schema_revision",
            "subject",
        },
        "L12 local closure",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v12"
        and root["schema_revision"] == 12
        and root["limits"] == LOCAL_LIMITS
        and root["immutable_v8_primitives"] == LOCAL_V8
        and root["immutable_v11_primitives"] == LOCAL_V11
        and root["nonimplications"] == LOCAL_NONIMPLICATIONS,
        "L12 root identity changed",
    )
    require(
        root["subject"]
        == {
            "c11_parent": C11_COMMIT,
            "c12_commit": c12,
            "c12_message": C12_MESSAGE,
            "c12_tree": c12_tree,
        },
        "L12 subject differs from exact C12",
    )

    authorities = root["authorities"]
    require(
        type(authorities) is list
        and len(authorities) == len(EXPECTED_AUTHORITIES)
        and [item.get("path") for item in authorities]
        == [authority.path for authority in EXPECTED_AUTHORITIES],
        "L12 authority roster changed",
    )
    c12_entries = V11.recursive_tree_entries(c12)
    aggregate = 0
    for item, expected in zip(authorities, EXPECTED_AUTHORITIES, strict=True):
        authority = V11.exact_keys(
            item,
            {
                "binding_state",
                "git_blob_oid",
                "git_mode",
                "limit_class",
                "live_blob_oid",
                "live_mode",
                "path",
                "role",
                "sha256",
                "size_bytes",
            },
            f"L12 authority {expected.path}",
        )
        entry = c12_entries.get(expected.path)
        require(
            entry is not None
            and entry.kind == "blob"
            and entry.mode == expected.git_mode,
            f"C12 authority tree entry changed: {expected.path}",
        )
        blob = V11.verify_object("blob", entry.oid, ORDINARY_LIMIT)
        require(
            authority["binding_state"] == "bound_to_head"
            and authority["git_blob_oid"] == entry.oid
            and authority["live_blob_oid"] == entry.oid
            and authority["git_mode"] == expected.git_mode
            and authority["live_mode"] == f"{expected.live_mode:04o}"
            and authority["limit_class"] == "ordinary_2mib"
            and authority["path"] == expected.path
            and authority["role"] == expected.role
            and authority["sha256"] == hashlib.sha256(blob).hexdigest()
            and authority["size_bytes"] == len(blob),
            f"L12 authority binding changed: {expected.path}",
        )
        aggregate += len(blob)
    require(aggregate <= AGGREGATE_LIMIT, "L12 authority aggregate exceeds 16 MiB")

    state = V11.exact_keys(root["repository_state"], {"after", "before"}, "L12 state")
    before = validate_local_snapshot(state["before"], c12, c12_tree, "before")
    after = validate_local_snapshot(state["after"], c12, c12_tree, "after")
    require(
        {key: item for key, item in state["before"].items() if key != "observed_at"}
        == {key: item for key, item in state["after"].items() if key != "observed_at"},
        "L12 repository endpoints differ",
    )

    invocation = V11.exact_keys(
        root["invocation"],
        {
            "argv",
            "cwd",
            "elapsed_monotonic_ns",
            "environment",
            "environment_routes_sha256",
            "exit_code",
            "finished_at",
            "monotonic_finish_ns",
            "monotonic_start_ns",
            "signal",
            "started_at",
            "stderr",
            "stdout",
            "timeout_seconds",
            "timed_out",
            "umask",
        },
        "L12 invocation",
    )
    stdout = V11.decode_binding(invocation["stdout"], "L12 stdout", 8 * 1024 * 1024)
    stderr = V11.decode_binding(invocation["stderr"], "L12 stderr", 8 * 1024 * 1024)
    started = V11.parse_utc_timestamp(invocation["started_at"], "L12 start")
    finished = V11.parse_utc_timestamp(invocation["finished_at"], "L12 finish")
    require(
        invocation["argv"] == ["just", "ksg-composite-v12"]
        and invocation["cwd"] == "<REPOSITORY_ROOT>"
        and invocation["environment"] == V11.LOCAL_ENVIRONMENT
        and type(invocation["environment_routes_sha256"]) is str
        and SHA256_RE.fullmatch(invocation["environment_routes_sha256"]) is not None
        and invocation["exit_code"] == 0
        and invocation["signal"] is None
        and invocation["timeout_seconds"] == 14_400
        and invocation["timed_out"] is False
        and invocation["umask"] == "0077"
        and invocation["monotonic_start_ns"] == 0
        and type(invocation["monotonic_finish_ns"]) is int
        and invocation["monotonic_finish_ns"] > 0
        and invocation["elapsed_monotonic_ns"] == invocation["monotonic_finish_ns"]
        and stdout + stderr != b""
        and before <= started <= finished <= after,
        "L12 invocation or ordering changed",
    )

    platform_value = V11.exact_keys(
        root["platform"],
        {
            "architecture",
            "gil_enabled",
            "operating_system",
            "operating_system_release",
            "python_implementation",
            "python_version",
        },
        "L12 platform",
    )
    require(
        platform_value["operating_system"] == "Darwin"
        and platform_value["architecture"] in {"arm64", "aarch64"}
        and type(platform_value["operating_system_release"]) is str
        and bool(platform_value["operating_system_release"])
        and platform_value["python_implementation"] == "CPython"
        and platform_value["python_version"] == "3.14.6"
        and platform_value["gil_enabled"] is True,
        "L12 reviewed platform changed",
    )
    records = root["reviewed_executables"]
    require(
        type(records) is list
        and [record.get("name") for record in records]
        == sorted(V11.LOCAL_TOOL_VERSIONS),
        "L12 reviewed executable roster changed",
    )
    for record in records:
        name = record["name"]
        V11.exact_keys(
            record,
            {
                "executable_sha256",
                "executable_size_bytes",
                "name",
                "route",
                "version_argv",
                "version_exit_code",
                "version_stderr",
                "version_stdout",
            },
            f"L12 executable {name}",
        )
        version_stdout = V11.decode_binding(
            record["version_stdout"], f"{name} version stdout", VERSION_LIMIT
        )
        version_stderr = V11.decode_binding(
            record["version_stderr"], f"{name} version stderr", VERSION_LIMIT
        )
        require(
            type(record["executable_sha256"]) is str
            and SHA256_RE.fullmatch(record["executable_sha256"]) is not None
            and type(record["executable_size_bytes"]) is int
            and 0 < record["executable_size_bytes"] <= 256 * 1024 * 1024
            and type(record["route"]) is str
            and re.fullmatch(
                rf"<(?:SYSTEM|USR_LOCAL|HOMEBREW|TEXLIVE)_BIN>/{re.escape(name)}",
                record["route"],
            )
            is not None
            and record["version_argv"] == V11.LOCAL_TOOL_VERSIONS[name]
            and record["version_exit_code"] == 0
            and version_stdout + version_stderr != b"",
            f"L12 executable binding changed: {name}",
        )
    return {
        "authority_count": len(authorities),
        "command_exit_code": 0,
        "platform": "Darwin-arm64-CPython-3.14.6-GIL",
        "reviewed_executables": len(records),
    }


def validate_successor_capture(
    raw: bytes, hosted_tool_raw: bytes, c12: str, c12_tree: str
) -> dict[str, Any]:
    value = V11.parse_hosted_canonical_json(raw, "C12 successor capture", RECORD_LIMIT)
    root = V11.exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v8_primitives",
            "immutable_v11_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        "C12 successor capture",
    )
    runs = root["runs"]
    require(
        root["capture_tool"] == V11.descriptor(hosted_tool_raw, HOSTED_TOOL)
        and root["immutable_v8_primitives"] == HOSTED_V8
        and root["immutable_v11_primitives"] == HOSTED_V11
        and root["nonimplications"] == HOSTED_NONIMPLICATIONS
        and root["phase"] == "successor_qualification"
        and root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v12"
        and root["schema_revision"] == 12
        and root["subject"]
        == {
            "predecessor_commit": C11_COMMIT,
            "predecessor_tree": C11_TREE,
            "successor_commit": c12,
            "successor_tree": c12_tree,
        }
        and type(runs) is dict
        and set(runs) == {"successor_ci", "successor_codeql", "successor_contract"}
        and all(type(run_id) is int and run_id > 0 for run_id in runs.values())
        and len(set(runs.values())) == 3,
        "C12 successor capture identity changed",
    )
    decoded, retry_count = V11.decode_capture_document(root, "C12 successor capture")
    expected_routes = {
        "successor_ci": ("CI", ".github/workflows/ci.yml", "push", 45),
        "successor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
            4,
        ),
        "successor_contract": (
            "KSG M1a composite v12",
            WORKFLOW,
            "push",
            1,
        ),
    }
    expected_artifacts = {
        "successor_ci": {
            "coverage-lcov",
            f"post-commit-source-state-v2-{c12}",
            "workspace-sbom",
        },
        "successor_codeql": set(),
        "successor_contract": {f"ksg-m1a-composite-v12-static-{c12}"},
    }
    repository_ids: set[int] = set()
    identifier_domains: dict[str, set[int]] = {
        "run": set(),
        "job": set(),
        "artifact": set(),
    }
    allowed_logicals: set[str] = set()
    codeql_job_names: set[str] = set()
    for role in sorted(runs):
        run_id = runs[role]
        require(run_id not in identifier_domains["run"], "successor run IDs overlap")
        identifier_domains["run"].add(run_id)
        run_logical = f"{role}_run"
        allowed_logicals.add(run_logical)
        run_rows = V11.paired_capture_bodies(decoded, run_logical)
        require(
            len(run_rows) == 1
            and run_rows[0][0]["page"] == 0
            and run_rows[0][0]["path"] == f"/repos/{REPOSITORY}/actions/runs/{run_id}"
            and run_rows[0][0]["response_kind"] == "json",
            f"{role} run route changed",
        )
        run = V11.parse_json(run_rows[0][1], f"{role} run")
        repository = run.get("repository") if type(run) is dict else None
        head_repository = run.get("head_repository") if type(run) is dict else None
        name, path, event, expected_jobs = expected_routes[role]
        require(
            type(run) is dict
            and run.get("id") == run_id
            and run.get("head_sha") == c12
            and run.get("head_branch") == "main"
            and run.get("run_attempt") == 1
            and type(run.get("run_attempt")) is int
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and (run.get("name"), run.get("path"), run.get("event"))
            == (name, path, event)
            and type(repository) is dict
            and repository.get("full_name") == REPOSITORY
            and type(repository.get("id")) is int
            and repository.get("id") > 0
            and type(head_repository) is dict
            and head_repository.get("full_name") == REPOSITORY
            and head_repository.get("id") == repository.get("id"),
            f"{role} attempt-1 terminal success identity changed",
        )
        repository_id = repository["id"]
        repository_ids.add(repository_id)

        jobs_logical = f"{role}_jobs"
        allowed_logicals.add(jobs_logical)
        jobs = V11.paged_object_array(
            decoded,
            jobs_logical,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs?per_page=100&page=",
            "jobs",
        )
        require(len(jobs) == expected_jobs, f"{role} job count changed")
        for job in jobs:
            job_id = job.get("id")
            steps = job.get("steps")
            require(
                type(job_id) is int
                and job_id > 0
                and job_id not in identifier_domains["job"]
                and job.get("run_id") == run_id
                and job.get("run_attempt") == 1
                and job.get("head_sha") == c12
                and job.get("status") == "completed"
                and job.get("conclusion") == "success"
                and type(steps) is list
                and bool(steps)
                and all(
                    type(step) is dict
                    and step.get("status") == "completed"
                    and step.get("conclusion") in {"success", "skipped"}
                    for step in steps
                ),
                f"{role} contains an adverse or foreign job",
            )
            identifier_domains["job"].add(job_id)
            if role == "successor_codeql":
                require(type(job.get("name")) is str, "CodeQL job name changed")
                codeql_job_names.add(job["name"])

        artifacts_logical = f"{role}_artifacts"
        allowed_logicals.add(artifacts_logical)
        artifacts = V11.paged_object_array(
            decoded,
            artifacts_logical,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100&page=",
            "artifacts",
        )
        observed_names: set[str] = set()
        for artifact in artifacts:
            artifact_id = artifact.get("id")
            artifact_name = artifact.get("name")
            workflow_run = artifact.get("workflow_run")
            require(
                type(artifact_id) is int
                and artifact_id > 0
                and artifact_id not in identifier_domains["artifact"]
                and type(artifact_name) is str
                and artifact_name not in observed_names
                and artifact.get("expired") is False
                and type(artifact.get("size_in_bytes")) is int
                and artifact.get("size_in_bytes") > 0
                and type(workflow_run) is dict
                and workflow_run.get("id") == run_id
                and workflow_run.get("head_sha") == c12
                and workflow_run.get("head_branch") == "main"
                and workflow_run.get("repository_id") == repository_id
                and workflow_run.get("head_repository_id") == repository_id,
                f"{role} artifact join changed",
            )
            identifier_domains["artifact"].add(artifact_id)
            observed_names.add(artifact_name)
            logical = f"{role}_artifact_{artifact_id}"
            allowed_logicals.add(logical)
            payloads = V11.paired_capture_bodies(decoded, logical)
            require(
                len(payloads) == 1
                and payloads[0][0]["page"] == 0
                and payloads[0][0]["path"]
                == f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
                and payloads[0][0]["response_kind"] == "zip",
                f"{role} artifact payload route changed",
            )
            members = V11.validate_zip_payload(
                payloads[0][1], f"{role} artifact {artifact_id}"
            )
            if role == "successor_contract":
                require(
                    set(members) == {"ksg-m1a-composite-v12-static.json"},
                    "dedicated-v12 static artifact members changed",
                )
                static_raw = members["ksg-m1a-composite-v12-static.json"]
                static_value = V11.parse_json(static_raw, "dedicated-v12 static result")
                require(
                    static_raw == V11.compact_json(static_value)
                    and type(static_value) is dict
                    and static_value.get("result") == "pass"
                    and static_value.get("head") == c12
                    and static_value.get("tree") == c12_tree
                    and static_value.get("lifecycle_phase") == "candidate",
                    "dedicated-v12 static result changed",
                )
        require(
            observed_names == expected_artifacts[role],
            f"{role} artifact names changed",
        )

    analysis_ids: set[int] = set()
    analyses_logical = "successor_codeql_analyses"
    allowed_logicals.add(analyses_logical)
    analyses = V11.paged_json_array(
        decoded,
        analyses_logical,
        f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain&per_page=100&page=",
    )
    exact_head_analyses = [
        analysis
        for analysis in analyses
        if analysis.get("commit_sha") == c12
        and analysis.get("ref") == "refs/heads/main"
    ]
    languages = ("actions", "javascript-typescript", "python", "rust")
    observed_languages: set[str] = set()
    for analysis in exact_head_analyses:
        identifier = analysis.get("id")
        category = analysis.get("category")
        matches = [
            language for language in languages if category == f"/language:{language}"
        ]
        require(
            type(identifier) is int
            and identifier > 0
            and identifier not in analysis_ids
            and len(matches) == 1
            and matches[0] not in observed_languages
            and f"Analyze ({matches[0]})" in codeql_job_names
            and type(analysis.get("results_count")) is int
            and analysis.get("results_count") >= 0
            and type(analysis.get("rules_count")) is int
            and analysis.get("rules_count") > 0
            and analysis.get("error") in {"", None}
            and analysis.get("warning") in {"", None},
            "CodeQL exact-head analysis identity or language/job join changed",
        )
        analysis_ids.add(identifier)
        observed_languages.add(matches[0])
    require(
        len(exact_head_analyses) == 4
        and observed_languages == set(languages)
        and codeql_job_names == {f"Analyze ({language})" for language in languages},
        "CodeQL exact-C12 analysis/job roster changed",
    )
    alert_numbers: set[int] = set()
    for state in ("dismissed", "fixed", "open"):
        logical = f"successor_codeql_alerts_{state}"
        allowed_logicals.add(logical)
        alerts = V11.paged_json_array(
            decoded,
            logical,
            f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}&per_page=100&page=",
        )
        for alert in alerts:
            number = alert.get("number")
            require(
                alert.get("state") == state
                and type(number) is int
                and number > 0
                and number not in alert_numbers,
                f"CodeQL {state} alert partition changed or overlaps",
            )
            alert_numbers.add(number)
    require(len(repository_ids) == 1, "successor runs disagree on repository identity")
    require(
        {row["logical_request"] for row, _body in decoded} == allowed_logicals,
        "successor capture contains an unaccounted logical request",
    )
    return {
        "capture_rows": len(decoded),
        "codeql_analysis_count": len(analysis_ids),
        "repository_id_consistent": True,
        "retry_events": retry_count,
        "run_ids": dict(sorted(runs.items())),
    }


def expected_receipt(
    local_raw: bytes, successor_raw: bytes, c12: str, c12_tree: str
) -> dict[str, Any]:
    return {
        "bindings": {
            "hosted_capture": V11.descriptor(successor_raw, SUCCESSOR_CAPTURE),
            "local_closure": V11.descriptor(local_raw, LOCAL_EVIDENCE),
        },
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "qualification": {
            "attempt": 1,
            "formula": "Q12 = L12 AND CI12_attempt1 AND CodeQL12_attempt1 AND Dedicated12_attempt1",
            "terms": {
                "CI12_attempt1": True,
                "CodeQL12_attempt1": True,
                "Dedicated12_attempt1": True,
                "L12": True,
            },
            "value": True,
        },
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v12",
        "schema_revision": 12,
        "subject": {
            "commit": c12,
            "message": C12_MESSAGE,
            "parent": C11_COMMIT,
            "tree": c12_tree,
        },
    }


def derive_receipt_from_descriptors(local_fd: int, successor_fd: int) -> dict[str, Any]:
    require(local_fd != successor_fd, "L12 and successor descriptor numbers alias")
    metadata_before = V11.complete_git_metadata_snapshot()
    V11.validate_git_metadata()
    head = (
        V11.git("rev-parse", "--verify", "HEAD")
        .decode("ascii", errors="strict")
        .strip()
    )
    require(OID_RE.fullmatch(head) is not None, "receipt-derivation HEAD is malformed")
    status_before = V11.git(
        "status", "--porcelain=v1", "--untracked-files=all", maximum=GIT_METADATA_LIMIT
    )
    topology = locate_lifecycle(head)
    require(
        topology["phase"] == "candidate"
        and topology["r12"] is None
        and head == topology["c12"]
        and status_before == b"",
        "receipt derivation requires the clean exact receipt-absent C12",
    )
    local_raw, local_identity = V11.bounded_input_fd(
        local_fd, "L12 input", RECORD_LIMIT
    )
    successor_raw, successor_identity = V11.bounded_input_fd(
        successor_fd, "C12 successor input", RECORD_LIMIT
    )
    require(
        local_identity != successor_identity,
        "L12 and successor inputs are one file",
    )
    c12 = topology["c12"]
    c12_tree = topology["c12_tree"]
    validate_local_evidence(local_raw, c12, c12_tree)
    validate_successor_capture(
        successor_raw,
        V11.tree_blob(c12, HOSTED_TOOL, ORDINARY_LIMIT),
        c12,
        c12_tree,
    )
    result = expected_receipt(local_raw, successor_raw, c12, c12_tree)
    schema = V11.parse_json(
        V11.tree_blob(c12, RECEIPT_SCHEMA, ORDINARY_LIMIT), RECEIPT_SCHEMA
    )
    validate_schema(schema, RECEIPT_SCHEMA)
    require(
        0 < len(V11.pretty_json(result)) <= RECORD_LIMIT,
        "derived R12 receipt exceeds its output bound",
    )
    final_head = (
        V11.git("rev-parse", "--verify", "HEAD")
        .decode("ascii", errors="strict")
        .strip()
    )
    status_after = V11.git(
        "status", "--porcelain=v1", "--untracked-files=all", maximum=GIT_METADATA_LIMIT
    )
    metadata_after = V11.complete_git_metadata_snapshot()
    V11.validate_complete_probe_endpoints(
        head,
        status_before,
        metadata_before,
        final_head,
        status_after,
        metadata_after,
    )
    return result


def validate_r12_evidence(topology: dict[str, Any]) -> dict[str, Any]:
    r12 = topology["r12"]
    require(type(r12) is str and OID_RE.fullmatch(r12) is not None, "R12 is absent")
    c12 = topology["c12"]
    c12_tree = topology["c12_tree"]
    local_raw = V11.tree_blob(r12, LOCAL_EVIDENCE, RECORD_LIMIT)
    successor_raw = V11.tree_blob(r12, SUCCESSOR_CAPTURE, RECORD_LIMIT)
    receipt_raw = V11.tree_blob(r12, RECEIPT, RECORD_LIMIT)
    hosted_tool_raw = V11.tree_blob(c12, HOSTED_TOOL, ORDINARY_LIMIT)
    local_result = validate_local_evidence(local_raw, c12, c12_tree)
    hosted_result = validate_successor_capture(
        successor_raw, hosted_tool_raw, c12, c12_tree
    )
    receipt_value = V11.parse_json(receipt_raw, "R12 receipt", maximum=RECORD_LIMIT)
    require(
        receipt_raw == V11.pretty_json(receipt_value),
        "R12 receipt is not canonical pretty JSON",
    )
    require(
        receipt_value == expected_receipt(local_raw, successor_raw, c12, c12_tree),
        "R12 receipt differs from canonical derivation",
    )
    return {
        "hosted": hosted_result,
        "local": local_result,
        "qualification": True,
        "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
    }


def check(mode: str) -> dict[str, Any]:
    require(
        mode in {"authoring", "auto", "candidate", "workflow"},
        "unknown v12 checker mode",
    )
    outer_metadata_before = V11.complete_git_metadata_snapshot()
    metadata = V11.validate_git_metadata()
    head = (
        V11.git("rev-parse", "--verify", "HEAD")
        .decode("ascii", errors="strict")
        .strip()
    )
    require(OID_RE.fullmatch(head) is not None, "HEAD identity changed")
    status_before = V11.git(
        "status", "--porcelain=v1", "--untracked-files=all", maximum=GIT_METADATA_LIMIT
    )
    tree, commit_raw = V11.verify_head_objects(head)
    parsed_tree, parents, message, signed = V11.parse_commit_envelope(commit_raw)
    require(parsed_tree == tree, "HEAD commit/tree binding changed")
    selected_mode = mode
    if mode == "auto":
        selected_mode = "authoring" if head == C11_COMMIT else "candidate"
    topology: dict[str, Any] | None = None
    strict = selected_mode != "authoring"
    if selected_mode == "authoring":
        require(
            head == C11_COMMIT
            and tree == C11_TREE
            and parents == (C9_COMMIT,)
            and message == C11_MESSAGE
            and not signed,
            "authoring base is not exact unsigned C11",
        )
        lifecycle_phase = "authoring"
    else:
        require(status_before == b"" and not signed, "workflow HEAD is dirty or signed")
        topology = locate_lifecycle(head)
        lifecycle_phase = topology["phase"]
        if selected_mode == "candidate":
            require(
                lifecycle_phase == "candidate"
                and parents == (C11_COMMIT,)
                and message == C12_MESSAGE
                and head == topology["c12"]
                and tree == topology["c12_tree"],
                "candidate mode requires exact clean unsigned C12",
            )

    roster = validate_live_authorities(head, strict=strict)
    root_fd, root_identity = V11.open_canonical_root(ROOT)
    failure_result: dict[str, Any] | None = None
    try:
        validate_source_surfaces(root_fd)
        frozen_raw = V11.stable_read(root_fd, EXPECTED_BY_PATH[V11_RELATIVE])
        require(
            frozen_raw == V11_RAW
            and hashlib.sha256(frozen_raw).hexdigest() == V11_SHA256,
            "frozen v11 checker source differs inside complete probe",
        )
        try:
            failure_raw = V11.stable_read(root_fd, EXPECTED_BY_PATH[FAILURE_PATH])
        except FileNotFoundError:
            require(
                not strict, "committed C12 lacks the consumed-L11 failure diagnostic"
            )
        else:
            failure_value = V11.parse_json(
                failure_raw, "C11 consumed-L11 failure diagnostic"
            )
            require(
                failure_raw == V11.pretty_json(failure_value),
                "C11 failure diagnostic is not canonical pretty JSON",
            )
            validate_failure_diagnostic(failure_value)
            failure_result = {
                "l11": "consumed_failed",
                "q11": False,
                "r11": "permanently_unissued",
                "surface_count": len(EXPECTED_FAILURE_SURFACES),
            }
        for path in R11_EVIDENCE_PATHS:
            V11.require_descriptor_absent(root_fd, path, "forbidden R11 evidence")
            require(
                V11.tree_entry(head, path) is None,
                f"forbidden R11 evidence is committed: {path}",
            )
    finally:
        V11.recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)

    evidence_result = None
    if topology is not None and topology["r12"] is not None:
        evidence_result = validate_r12_evidence(topology)
    final_v11 = read_bound_v11()
    require(final_v11 == V11_RAW, "frozen v11 checker changed across complete probe")
    final_head = (
        V11.git("rev-parse", "--verify", "HEAD")
        .decode("ascii", errors="strict")
        .strip()
    )
    status_after = V11.git(
        "status", "--porcelain=v1", "--untracked-files=all", maximum=GIT_METADATA_LIMIT
    )
    outer_metadata_after = V11.complete_git_metadata_snapshot()
    V11.validate_complete_probe_endpoints(
        head,
        status_before,
        outer_metadata_before,
        final_head,
        status_after,
        outer_metadata_after,
    )
    return {
        "authority_aggregate_bytes": roster["aggregate_bytes"],
        "authority_count": len(EXPECTED_AUTHORITIES),
        "authority_states": roster["states"],
        "c11_failure": failure_result,
        "frozen_v11_checker": {
            "sha256": V11_SHA256,
            "size_bytes": V11_SIZE_BYTES,
        },
        "git_commit_and_tree_objects_verified": True,
        "git_metadata_isolation": metadata,
        "head": head,
        "lifecycle_phase": lifecycle_phase,
        "mode": selected_mode,
        "pending_authorities": roster["pending"],
        "r12_commit": None if topology is None else topology["r12"],
        "r12_evidence": evidence_result,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-check/v1",
        "tree": tree,
    }


def projection_fixture() -> tuple[
    str, str, dict[str, CommitEnvelope], dict[str, dict[str, TreeEntry]]
]:
    c12 = "c" * 40
    r12 = "d" * 40
    envelopes = {
        C9_COMMIT: CommitEnvelope(C9_COMMIT, "1" * 40, (), "historical\n", False),
        C11_COMMIT: CommitEnvelope(
            C11_COMMIT, C11_TREE, (C9_COMMIT,), C11_MESSAGE, False
        ),
        c12: CommitEnvelope(c12, "2" * 40, (C11_COMMIT,), C12_MESSAGE, False),
        r12: CommitEnvelope(r12, "3" * 40, (c12,), R12_MESSAGE, False),
    }
    selected = {oid: {} for oid in envelopes}
    failure_entry = TreeEntry("100644", "blob", "4" * 40)
    selected[c12][FAILURE_PATH] = failure_entry
    selected[r12][FAILURE_PATH] = failure_entry
    for index, path in enumerate(R12_EVIDENCE_PATHS, start=5):
        selected[r12][path] = TreeEntry("100644", "blob", str(index) * 40)
    return c12, r12, envelopes, selected


def offline_self_test() -> dict[str, Any]:
    validate_authority_specification()
    v11_result = V11.offline_self_test()
    require(v11_result.get("result") == "pass", "frozen v11 checker self-test failed")
    c12, r12, envelopes, selected = projection_fixture()
    candidate_envelopes = {key: value for key, value in envelopes.items() if key != r12}
    candidate_selected = {key: value for key, value in selected.items() if key != r12}
    candidate = analyze_lifecycle_projection(
        c12, candidate_envelopes, candidate_selected
    )
    receipt = analyze_lifecycle_projection(r12, envelopes, selected)
    require(
        candidate == {"c12": c12, "phase": "candidate", "r12": None}
        and receipt == {"c12": c12, "phase": "receipt", "r12": r12},
        "v12 lifecycle positive controls changed",
    )
    rejected = 0

    def expect_projection_failure(
        mutant_envelopes: dict[str, CommitEnvelope],
        mutant_selected: dict[str, dict[str, TreeEntry]],
        mutant_head: str,
    ) -> None:
        nonlocal rejected
        try:
            analyze_lifecycle_projection(mutant_head, mutant_envelopes, mutant_selected)
        except ContractError:
            rejected += 1
        else:
            raise ContractError("v12 lifecycle mutation unexpectedly passed")

    side = "e" * 40
    for message_text, evidence_path in (
        (R11_MESSAGE, None),
        (C12_MESSAGE, None),
        ("side\n", R11_EVIDENCE_PATHS[0]),
        ("side\n", FAILURE_PATH),
    ):
        mutant_envelopes = dict(candidate_envelopes)
        mutant_envelopes[side] = CommitEnvelope(
            side, "6" * 40, (C9_COMMIT,), message_text, False
        )
        mutant_selected = {
            key: dict(value) for key, value in candidate_selected.items()
        }
        mutant_selected[side] = {}
        if evidence_path is not None:
            mutant_selected[side][evidence_path] = TreeEntry("100644", "blob", "7" * 40)
        expect_projection_failure(mutant_envelopes, mutant_selected, c12)

    split_selected = {key: dict(value) for key, value in selected.items()}
    split_selected[r12].pop(R12_EVIDENCE_PATHS[0])
    expect_projection_failure(envelopes, split_selected, r12)

    reused_envelopes = dict(envelopes)
    reused_envelopes[side] = CommitEnvelope(
        side, "6" * 40, (C9_COMMIT,), R12_MESSAGE, False
    )
    reused_selected = {key: dict(value) for key, value in selected.items()}
    reused_selected[side] = {}
    expect_projection_failure(reused_envelopes, reused_selected, r12)

    descendant = "f" * 40
    descendant_envelopes = dict(envelopes)
    descendant_envelopes[descendant] = CommitEnvelope(
        descendant, "8" * 40, (r12,), "descendant\n", False
    )
    descendant_selected = {key: dict(value) for key, value in selected.items()}
    descendant_selected[descendant] = dict(selected[r12])
    descendant_selected[descendant][R12_EVIDENCE_PATHS[0]] = TreeEntry(
        "100644", "blob", "9" * 40
    )
    expect_projection_failure(descendant_envelopes, descendant_selected, descendant)

    require(rejected == 7, "v12 lifecycle hostile count changed")
    return {
        "frozen_v11_checker_offline_self_test": "pass",
        "lifecycle_positive_controls": 2,
        "lifecycle_projection_hostiles_rejected": rejected,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-offline-self-test/v1",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, allow_abbrev=False, add_help=False
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--authoring", action="store_true")
    modes.add_argument("--auto", action="store_true")
    modes.add_argument("--candidate", action="store_true")
    modes.add_argument("--workflow", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--derive-receipt", action="store_true")
    parser.add_argument("--local-fd", type=int)
    parser.add_argument("--successor-fd", type=int)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.derive_receipt:
            require(
                type(arguments.local_fd) is int and type(arguments.successor_fd) is int,
                "receipt derivation requires two descriptors",
            )
            result = derive_receipt_from_descriptors(
                arguments.local_fd, arguments.successor_fd
            )
        else:
            require(
                arguments.local_fd is None and arguments.successor_fd is None,
                "path-free checker mode received evidence descriptors",
            )
            if arguments.self_test:
                result = offline_self_test()
            else:
                mode = next(
                    name
                    for name in ("authoring", "auto", "candidate", "workflow")
                    if getattr(arguments, name)
                )
                result = check(mode)
        sys.stdout.buffer.write(V11.pretty_json(result))
        return 0
    except (
        BootstrapError,
        ContractError,
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: unexpected bounded v12 checker failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
