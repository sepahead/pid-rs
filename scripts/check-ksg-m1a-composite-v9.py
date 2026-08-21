#!/usr/bin/env python3
"""Validate the retained-surface composite-v9 successor and conditional R9 cut.

C9 preserves published C8 and its scientific publication family, retires the
failed v8 hosted route, and repairs exactly five stale operational bindings.
The hosted marker exposes the first binding. Read-only sequential digest-repin
analysis identified the complete mismatch set; source reconstruction guards
that set without claiming unique counterfactual necessity or order. R9 requires a fresh exact-C9
L9 record, r14/current-source custody, and three fresh attempt-1 hosted
successes. This is operational evidence, not scientific validation.
"""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
from typing import Any, Final


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v9.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"

V8_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v8.py"
V8_CHECKER_PATH = ROOT / V8_CHECKER_RELATIVE
V8_CHECKER_SHA256 = "ed0404c2e3cd2c3f2bd9f8fa177649c26ca87f620280e2e6e4f5ac49c551d1df"
V8_CHECKER_SIZE_BYTES = 124_760
V8_SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v8-self-test.py"
V8_SELF_TEST_SHA256 = "483713bf21d615953f8eb759afa9f80e859de0c6436d8903736e383b8b69ed1a"
V8_SELF_TEST_SIZE_BYTES = 28_968

C8_COMMIT = "7c80d48db415279fc4d744eadb1515797606912b"
C8_TREE = "ba01abdd86a542b359df75e9058fccf28cfc5a3d"
C8_PARENT = "23b69abafb4bfdaab4b2321eb6cee7be7e1cd32e"
C8_MESSAGE = "Repair KSG M1a composite v8 contract\n"
C8_IDENTITY = (
    b"author Sepehr Mahmoudian <sepmhn@gmail.com> 1787162521 +0200",
    b"committer Sepehr Mahmoudian <sepmhn@gmail.com> 1787162521 +0200",
)
C9_MESSAGE = "Repair KSG M1a composite v9 contract\n"
R9_MESSAGE = "Record KSG M1a composite v9 receipt\n"

C8_CI_RUN = 32_286_213_706
C8_CI_CONCLUSION = "failure"
C8_CODEQL_RUN = 32_286_212_997
C8_CONTRACT_RUN = 32_286_213_774
C8_CONTRACT_FAILED_JOB = 96_176_246_257
C8_CI_FAILED_JOB = 96_176_246_476
C8_REPOSITORY_ID = 1_271_708_111
C8_CONTRACT_RAW_LOG_SHA256 = (
    "63be55db45dbf212881ede76b8c4ae70cd4bad28de0c49bd4b12d0b70a515d0e"
)
C8_CONTRACT_RAW_LOG_SIZE_BYTES = 59_731
C8_CI_RAW_LOG_SHA256 = (
    "0c475bce091b1f2ae414b6325ec0b46caae5f375ee5b4e87bd989688915d6fc4"
)
C8_CI_RAW_LOG_SIZE_BYTES = 136_873
GOOD_UPLOAD_PIN = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
BAD_UPLOAD_PIN = GOOD_UPLOAD_PIN[:-1]
CERTIFIED_FAILURE_MARKER = b"certified SxPID2 claim check failed: release-audit just dependency line exact digest changed"
C8_STALE_BINDINGS = [
    "execution-container:.github/workflows/ci.yml",
    "execution-container:justfile",
    "release-audit-line:justfile",
    "reviewed-documentation:scripts/README.md",
    "support-gate:scripts/check-formal-pdf-set.sh",
]

CI_RELATIVE = ".github/workflows/ci.yml"
RETIRED_V8_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v8.yml"
V9_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v9.yml"
BAD_V8_WORKFLOW_SHA256 = (
    "581669b6373963f011238b68cc511b05e4c04d810009816ffbc363c6fff4cc8a"
)
BAD_V8_WORKFLOW_SIZE_BYTES = 10_061

# Final whole-file workflow bindings after all semantics settled.
CI_SHA256 = "9a70c744b57ccf5ca222fc9e8d0cd3f159276db8927f454a647d5d2be4bcd219"
CI_SIZE_BYTES = 69_842
RETIRED_V8_WORKFLOW_SHA256 = (
    "4c934572fa831a78dd9622dc6e6f00cc8281a93f1f557424b393b0c3be1c651b"
)
RETIRED_V8_WORKFLOW_SIZE_BYTES = 2_711
V9_WORKFLOW_SHA256 = "cf727766595d841e552011926e2a509bcec66c29248536f02504c32c87453130"
V9_WORKFLOW_SIZE_BYTES = 10_084

ACTION_PIN_CHECKER_RELATIVE = "scripts/check-github-action-pins.py"
ACTION_PIN_SELF_TEST_RELATIVE = "scripts/check-github-action-pins-self-test.py"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v9.py"
LOCAL_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v9-local-closure.py"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v9.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v9-self-test.py"
JUSTFILE_RELATIVE = "justfile"
BOUNDARY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v9-boundary-2026-08-19.md"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v9-path-policy-v1.json"
CAPTURE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v9.schema.json"
)
LOCAL_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v9.schema.json"
)
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v9.schema.json"
FORMAL_PDF_SET_RELATIVE = "scripts/check-formal-pdf-set.sh"
WORKFLOW_PDF_GATE_RELATIVE = "scripts/check-mathematical-workflow-pdf.sh"
WORKFLOW_PDF_SELF_TEST_RELATIVE = "scripts/check-mathematical-workflow-pdf-self-test.sh"
WORKFLOW_PDF_SOURCE_RELATIVE = (
    "audit/formal/latex/mathematical-problem-solving-workflow.tex"
)
WORKFLOW_PDF_RELATIVE = "output/pdf/mathematical-problem-solving-workflow.pdf"
PREDECESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-"
    "hosted-capture-v9-2026-08-19.json"
)
SUCCESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v9-2026-08-19.json"
)
LOCAL_RECORD_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v9-2026-08-19.json"
)
RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v9-2026-08-19.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
R13_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-19-r13.json"
)
R14_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-19-r14.json"
)
R13_SHA256 = "373a5ef518f096628c070e2a107ff78f4ef872695dbc1bf37ac13308853eea12"
R13_SIZE_BYTES = 144_286
C9_NARRATIVE_PATHS = (
    "AGENTS.md",
    "CHANGELOG.md",
    BOUNDARY_RELATIVE,
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
    "scripts/README.md",
)
C9_L8_NARRATIVE_BOUNDARY = (
    b"No L8 record is installed; no operator-invocation history is claimed."
)
LEAN_CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
LEAN_SELF_TEST_RELATIVE = "scripts/check-lean-toolchain-freeze-self-test.py"
LEAN_CUSTODY_PATHS = (LEAN_SELF_TEST_RELATIVE, LEAN_CHECKER_RELATIVE)
# Finalized only after every non-cut r14 input, including the v9 self-test, is
# frozen. This deliberately excludes the three Lean cut literals.
EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "e5de3fde1a10e9180daa0e23367080a2e61a5d03f65956de6c7a65d7fe501ad6"
WORKFLOW_PDF_SHA256 = "6abf5af2ab7fb5cf0b40c37977dc38156d4bdf251b6f2948815c472fc77f1288"
WORKFLOW_PDF_SIZE_BYTES = 824_560
WORKFLOW_PDF_SOURCE_SHA256 = (
    "deb0cf82f4ddaa2ecfeb858d1130df12d9a3831feaf9f3215fa176c8a2f9aae1"
)
WORKFLOW_PDF_SOURCE_SIZE_BYTES = 262_345
PREDECESSOR_WORKFLOW_PDF_GATE_SHA256 = (
    "c1d9a2d7201a0175550d3d71b3a3762c2bb68472cb0f826637ad5c8e52e1b7f8"
)
PREDECESSOR_WORKFLOW_PDF_GATE_SIZE_BYTES = 245_965
PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SHA256 = (
    "a800c3ee9f9cc0f442c898b3265ac61157a56ff8d70430a083dabecbabafe2b3"
)
PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SIZE_BYTES = 276_971

CAPTURE_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v8.py",
    "sha256": "79ffbe59dc57ed99d2b4032aa71cac300448d0978a42a52fcf7b40b08236ae6f",
    "size_bytes": 24_111,
}
LOCAL_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v8-local-closure.py",
    "sha256": "b9b0a41cb2027d1cba464040843656bc2486e317f8cf1d3079cb58b02f7c6ba7",
    "size_bytes": 40_584,
}

CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Two retrieval repetitions are correlated provider observations, not independent replications.",
    "The predecessor phase records one retained operational-binding defect reached by two C8 hosted routes and cannot issue R8 or qualify C9.",
    "The C8 dedicated contract reached its retained certified-SxPID2 check and failed closed before PDF, static-contract, or artifact-upload steps.",
    "The C8 repository CI certified-SxPID2 job reached the same fail-closed marker; every other terminal job outcome remains separately roster-bound.",
    "Same-generation repository-CI and dedicated-workflow executions in either phase are correlated GitHub observations, not independent replications.",
    "The satisfiable retained local recorder and the absent, unissued L8 path have zero C9 or R9 credit; no operator-invocation history is claimed.",
    "A successful successor phase is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]
RECEIPT_NONIMPLICATIONS = [
    "The one C8 retained-surface defect observed through two hosted routes and the absent L8 record have zero qualification credit and cannot issue R8.",
    "Successful C9 runs establish only reached operational gates; they do not prove unreached commands, independent replication, or absence of other defects.",
    "Provider responses, Git identities, local executable observations, and timestamps do not authenticate themselves or establish trusted time.",
    "The five repaired digests bind reviewed operational containers and slices; they do not by themselves establish semantics, authenticity, or runtime behaviour.",
    "The exact C8 publication family is retained; C9 adds no mathematical or scientific publication.",
    "The unchanged workflow PDF/source and portability gate do not establish identical layout, mathematical correctness, accessibility, renderer independence, or cross-toolchain PDF byte identity.",
    "This receipt does not establish PID, KSG, theorem, numerical-result, security, privacy, accessibility, or application validity.",
]
POLICY_NONIMPLICATIONS = [
    "This policy describes an exact C9 and conditional R9 topology; it does not itself authorize, authenticate, qualify, or issue a commit or receipt.",
    "The C8 marker identifies one stale operational-binding defect reached in repository CI and the dedicated v8 workflow; it is not a PID, estimator, theorem, numerical-result, security, accessibility, or application finding.",
    "The first fail-closed marker is not the complete mismatch inventory: read-only sequential digest-repin analysis identified five changed bindings, and source reconstruction guards that exact set; neither establishes a unique counterfactual necessity set or ordering.",
    "The absent L8 record grants no C9 or R9 credit and does not claim any operator-invocation history for the retained recorder.",
    "C8 hosted observations and retained r13 do not transfer qualification or replay credit to C9.",
    "Git and SHA-256 identities bind named bytes and topology only; they do not establish authorship, provider completeness, trusted time, independent reproduction, semantic correctness, or durability.",
    "The C9 repair changes no theorem statement, mathematical-claim semantic content, estimator result, numerical result, scientific publication byte, or PDF byte; claim-packet edits are replay-custody pointer prose only.",
]

PHASE_ROLES = {
    "predecessor_failure": (
        "predecessor_ci",
        "predecessor_codeql",
        "predecessor_contract",
    ),
    "successor_qualification": (
        "successor_ci",
        "successor_codeql",
        "successor_contract",
    ),
}
PREDECESSOR_RUNS = {
    "predecessor_ci": C8_CI_RUN,
    "predecessor_codeql": C8_CODEQL_RUN,
    "predecessor_contract": C8_CONTRACT_RUN,
}
EXPECTED_CONCLUSIONS = {
    "predecessor_ci": C8_CI_CONCLUSION,
    "predecessor_codeql": "success",
    "predecessor_contract": "failure",
    "successor_ci": "success",
    "successor_codeql": "success",
    "successor_contract": "success",
}

LOCAL_AUTHORITY_ROLES = {
    ACTION_PIN_CHECKER_RELATIVE: "github_action_pin_semantic_gate",
    ACTION_PIN_SELF_TEST_RELATIVE: "github_action_pin_hostile_suite",
    JUSTFILE_RELATIVE: "local_command_wiring",
    LOCAL_SCHEMA_RELATIVE: "local_l9_closure_schema",
    LOCAL_TOOL_RELATIVE: "bounded_local_l9_closure_capture_tool",
    SELF_TEST_RELATIVE: "composite_v9_hostile_suite",
    CHECKER_RELATIVE: "composite_v9_semantic_gate",
    FORMAL_PDF_SET_RELATIVE: "formal_pdf_aggregate_gate",
    "scripts/README.md": "workflow_pdf_process_boundary",
    WORKFLOW_PDF_GATE_RELATIVE: "workflow_pdf_portability_gate",
    WORKFLOW_PDF_SELF_TEST_RELATIVE: "workflow_pdf_portability_hostile_suite",
    V8_SELF_TEST_RELATIVE: "retained_v8_hostile_suite_authority",
    V8_CHECKER_RELATIVE: "retained_v8_semantic_gate_authority",
}
LOCAL_AUTHORITY_MODES = {
    path: (
        "100755"
        if path
        in {
            FORMAL_PDF_SET_RELATIVE,
            WORKFLOW_PDF_GATE_RELATIVE,
            WORKFLOW_PDF_SELF_TEST_RELATIVE,
        }
        else "100644"
    )
    for path in LOCAL_AUTHORITY_ROLES
}
LOCAL_LIMITS = {
    "authority_stream_bytes": 2 * 1024 * 1024,
    "command_stream_bytes": 8 * 1024 * 1024,
    "executable_bytes": 256 * 1024 * 1024,
    "record_bytes": 32 * 1024 * 1024,
    "version_stream_bytes": 64 * 1024,
}

PUBLICATION_FIELDS: dict[str, str] = {}  # rebound after immutable-v8 load
UPLOAD_ROUTE: Final = b"actions/upload-artifact@"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_FILE_BYTES = 8 * 1024 * 1024


class BootstrapError(RuntimeError):
    """The exact immutable-v8 checker could not be loaded."""


def bootstrap_require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapError(message)


def read_bound_v8() -> bytes:
    before = V8_CHECKER_PATH.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not V8_CHECKER_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V8_CHECKER_SIZE_BYTES,
        "immutable v8 checker metadata changed",
    )
    descriptor = os.open(V8_CHECKER_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
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
            "immutable v8 checker opened identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "immutable v8 checker short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(os.read(descriptor, 1) == b"", "immutable v8 checker grew")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = V8_CHECKER_PATH.lstat()
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
            "immutable v8 checker changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V8_CHECKER_SHA256,
        "immutable v8 checker digest changed",
    )
    return raw


def load_bound_v8(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_immutable_composite_v8_primitives_for_v9")
    module.__file__ = os.fspath(V8_CHECKER_PATH)
    module.__package__ = ""
    sys.modules[module.__name__] = module
    code = compile(
        raw,
        os.fspath(V8_CHECKER_PATH),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


try:
    V8_RAW = read_bound_v8()
    V8 = load_bound_v8(V8_RAW)
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected immutable-v8 checker load failure", file=sys.stderr)
    raise SystemExit(2) from None


ContractError = V8.ContractError
require = V8.require
sha256 = V8.sha256
canonical_json = V8.canonical_json
parse_json = V8.parse_json
parse_commit = V8.parse_commit
parse_tree = V8.parse_tree
tree_blob = V8.tree_blob
changed_entries = V8.changed_entries
project_digest = V8.project_digest
exact_keys = V8.exact_keys
validate_schema_instance = V8.validate_schema_instance
PUBLICATION_FIELDS = dict(V8.PUBLICATION_FIELDS)


EXPECTED_C9_ROWS: tuple[tuple[str, str, str, str], ...] = tuple(
    sorted(
        (
            (
                RETIRED_V8_WORKFLOW_RELATIVE,
                "M",
                "100644",
                "retired_v8_no_credit_workflow",
            ),
            (V9_WORKFLOW_RELATIVE, "A", "100644", "dedicated_v9_hosted_gate"),
            ("AGENTS.md", "M", "100644", "operational_and_scientific_object_guide"),
            ("CHANGELOG.md", "M", "100644", "append_only_change_record"),
            (
                "audit/evidence/completion-active-resume.md",
                "M",
                "100644",
                "current_replay_pointer",
            ),
            (CURRENT_SOURCE_RELATIVE, "M", "100644", "self_excluding_source_state"),
            (
                PREDECESSOR_CAPTURE_RELATIVE,
                "A",
                "100644",
                "predecessor_failure_hosted_capture",
            ),
            (BOUNDARY_RELATIVE, "A", "100644", "operational_boundary_record"),
            (POLICY_RELATIVE, "A", "100644", "c9_r9_path_policy"),
            (R14_RELATIVE, "A", "100644", "current_lean_replay_receipt"),
            (
                "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
                "M",
                "100644",
                "durable_active_plan",
            ),
            (
                "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
                "M",
                "100644",
                "lean_replay_process_record",
            ),
            (
                "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md",
                "M",
                "100644",
                "current_replay_scientific_pointer",
            ),
            (
                CAPTURE_SCHEMA_RELATIVE,
                "A",
                "100644",
                "dual_phase_hosted_capture_schema",
            ),
            (LOCAL_SCHEMA_RELATIVE, "A", "100644", "local_l9_closure_schema"),
            (
                RECEIPT_SCHEMA_RELATIVE,
                "A",
                "100644",
                "dual_capture_typed_receipt_schema",
            ),
            (
                "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
                "M",
                "100644",
                "current_replay_claim_pointer",
            ),
            (
                "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md",
                "M",
                "100644",
                "current_replay_decision_pointer",
            ),
            (
                "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md",
                "M",
                "100644",
                "current_replay_evidence_pointer",
            ),
            (
                "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md",
                "M",
                "100644",
                "current_replay_revision_pointer",
            ),
            (JUSTFILE_RELATIVE, "M", "100644", "local_command_wiring"),
            ("scripts/README.md", "M", "100644", "script_process_guide"),
            (
                LOCAL_TOOL_RELATIVE,
                "A",
                "100644",
                "bounded_local_l9_closure_capture_tool",
            ),
            (
                CAPTURE_TOOL_RELATIVE,
                "A",
                "100644",
                "bounded_dual_phase_hosted_capture_tool",
            ),
            (
                "scripts/check-certified-sxpid2-claim.py",
                "M",
                "100644",
                "retained_operational_binding_repin",
            ),
            (
                "scripts/check-certified-sxpid2-claim-self-test.py",
                "M",
                "100644",
                "retained_operational_binding_hostile_suite",
            ),
            (SELF_TEST_RELATIVE, "A", "100644", "composite_v9_hostile_suite"),
            (CHECKER_RELATIVE, "A", "100644", "composite_v9_semantic_gate"),
            (
                "scripts/check-lean-toolchain-freeze-self-test.py",
                "M",
                "100644",
                "lean_replay_hostile_suite",
            ),
            (
                "scripts/check-lean-toolchain-freeze.py",
                "M",
                "100644",
                "lean_replay_gate",
            ),
            (
                "scripts/generate-lean-4.33-replay.py",
                "M",
                "100644",
                "lean_replay_generator",
            ),
        )
    )
)
R9_ROWS = (
    (CURRENT_SOURCE_RELATIVE, "M", "100644", "self_excluding_source_state"),
    (LOCAL_RECORD_RELATIVE, "A", "100644", "durable_local_l9_closure"),
    (RECEIPT_RELATIVE, "A", "100644", "derived_v9_receipt"),
    (SUCCESSOR_CAPTURE_RELATIVE, "A", "100644", "fresh_successor_hosted_capture"),
)

# Closed acyclic binding set. Values are finalized only after every non-cut
# source byte and the authorized predecessor capture settle.
FROZEN_C9_PATH_BINDINGS: dict[str, tuple[str, int, str]] = {
    ".github/workflows/ksg-m1a-composite-v8.yml": (
        "4c934572fa831a78dd9622dc6e6f00cc8281a93f1f557424b393b0c3be1c651b",
        2711,
        "100644",
    ),
    ".github/workflows/ksg-m1a-composite-v9.yml": (
        "cf727766595d841e552011926e2a509bcec66c29248536f02504c32c87453130",
        10084,
        "100644",
    ),
    "AGENTS.md": (
        "13017d7d6f5bd114be746bcba812141eb2215f1addfe5b8d437e418b7d09091c",
        61959,
        "100644",
    ),
    "CHANGELOG.md": (
        "77740c3723f4394aaf03942e46138fb6f51aa0c20cad5a4560522f16484ccf22",
        200620,
        "100644",
    ),
    "audit/evidence/completion-active-resume.md": (
        "2667c63d38600e985b040c53f22d343617cc8ef9851e0c59d3ba1a2e38ff02a6",
        2886,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-hosted-capture-v9-2026-08-19.json": (
        "41deaa02193103e7611a1676f751bcbeddf9024cabacb47950802a3d73c1878f",
        1849506,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-v9-boundary-2026-08-19.md": (
        "13d51c61677e7e3ddd885f40147455a4750c1464c5c876f3b4fa550ebc69911a",
        8525,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-v9-path-policy-v1.json": (
        "d66eb04184cfcdb3e6f9800a451ae1c002c12ad927f043e7c7ff1f63059c8ff5",
        11436,
        "100644",
    ),
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md": (
        "ca57d4b1855187a57140a0203ed8e5440e5a71568cbdc1bc3cbe3844627be888",
        44108,
        "100644",
    ),
    "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md": (
        "e23a76eaa3754e984c6a909b3de1a549a427e148a66e4df7214ebd944d737097",
        17620,
        "100644",
    ),
    "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md": (
        "6dea29695ff558808efcd43fb1553fd332ca549d24919320814fd7edb9441098",
        16840,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v9.schema.json": (
        "25ba4b03f3c6b50a21b8377ef9baf060aa0c4e2abeb9f7f13994b1816c823502",
        8965,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v9.schema.json": (
        "9a627b0dcecd0b2381ee7288b793fb2cd0aeb5e7118315da641e40e8e0948fbf",
        9947,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v9.schema.json": (
        "a22b5db858f68533bde5d9bc22636fafaaa174a444b331eddab2e9bc70afc60d",
        15961,
        "100644",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md": (
        "55e7d19f4ff73292b257b5042d89dfd634ac238aa521ca873c8fe509f01e76a0",
        8067,
        "100644",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md": (
        "dd50059f74381311472c15ec462fb3b83fe870588a554e309a4f628e48e79770",
        4941,
        "100644",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md": (
        "2b47658470a6b17fc2473abf0bdee07c682d212c991df19869d2d5b43b839602",
        5429,
        "100644",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md": (
        "8f5860156c7c68a246f01e2666cd6a520424bba548f6829dda917a24b6ad974d",
        3182,
        "100644",
    ),
    "justfile": (
        "74fb7bfd4500d8b121666a738a412fbdb409e7acf673b156645d215453ab310f",
        45574,
        "100644",
    ),
    "scripts/README.md": (
        "daedd86d0307984df8885849528ddfdd2d096a7b9d2799e308358ad4af59b33a",
        152884,
        "100644",
    ),
    "scripts/capture-ksg-m1a-composite-v9-local-closure.py": (
        "12ea05d1ec644f9b66e33820db3b6de98adeaea405239b0efa681d288321b6f2",
        41859,
        "100644",
    ),
    "scripts/capture-ksg-m1a-composite-v9.py": (
        "71009d35c015ff07a584aa9520966ea75a5cfdf38f818ca668bafa687a48eade",
        25054,
        "100644",
    ),
    "scripts/check-certified-sxpid2-claim-self-test.py": (
        "2b3481e1ff735ddc2055a4979606a16c5032f54fc4cfd4717d227f68b9e9fb82",
        119743,
        "100644",
    ),
    "scripts/check-certified-sxpid2-claim.py": (
        "ded0df95ecc9758548b0cec12aa5bf091dc36d3e027ecc12280a0086cd50a9c0",
        82193,
        "100644",
    ),
}

FORBIDDEN_EVIDENCE_PATHS = tuple(V8.FORBIDDEN_EVIDENCE_PATHS) + (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v8-2026-08-19.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v8-2026-08-19.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v8-2026-08-19.json",
)
FORBIDDEN_MESSAGES = frozenset(V8.FORBIDDEN_MESSAGES) | {
    "Record KSG M1a composite v8 receipt\n"
}


def read_file(
    relative: str, maximum: int = MAX_FILE_BYTES, mode: int | None = None
) -> bytes:
    path = ROOT / relative
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and 0 < before.st_size <= maximum,
        f"required bounded regular file changed: {relative}",
    )
    if mode is not None:
        require(
            stat.S_IMODE(before.st_mode) == mode,
            f"required file mode changed: {relative}",
        )
    raw = path.read_bytes()
    after = path.lstat()
    require(
        len(raw) == before.st_size
        and tuple(
            getattr(before, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        )
        == tuple(
            getattr(after, key)
            for key in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ),
        f"required file changed while read: {relative}",
    )
    return raw


def descriptor(entries: dict[str, Any], path: str) -> dict[str, Any]:
    raw = tree_blob(entries, path)
    return {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}


def authority(entries: dict[str, Any], path: str, role: str) -> dict[str, Any]:
    return {**descriptor(entries, path), "role": role}


def validate_c8_anchor() -> tuple[dict[str, Any], dict[str, Any]]:
    commit = parse_commit(C8_COMMIT)
    require(
        commit.tree == C8_TREE
        and commit.parent == C8_PARENT
        and commit.message == C8_MESSAGE
        and (commit.author, commit.committer) == C8_IDENTITY,
        "published C8 exact commit envelope changed",
    )
    _c6_entries, c7_entries = V8.validate_c7_anchor()
    c8_entries = parse_tree(C8_TREE)
    require(
        changed_entries(c7_entries, c8_entries)
        == tuple(
            (path, status, mode) for path, status, mode, _role in V8.EXPECTED_C8_ROWS
        ),
        "published C8 exact delta changed",
    )
    V8.validate_c8_sources(c7_entries, c8_entries, C8_COMMIT, C8_TREE)
    require(
        len(tree_blob(c8_entries, RETIRED_V8_WORKFLOW_RELATIVE))
        == BAD_V8_WORKFLOW_SIZE_BYTES
        and sha256(tree_blob(c8_entries, RETIRED_V8_WORKFLOW_RELATIVE))
        == BAD_V8_WORKFLOW_SHA256,
        "published C8 failed workflow bytes changed",
    )
    return c7_entries, c8_entries


def validate_raw_upload_occurrences(
    raw: bytes, label: str, expected_count: int
) -> None:
    folded = raw.lower()
    expected = GOOD_UPLOAD_PIN.encode("ascii")
    offsets: list[int] = []
    cursor = 0
    while (offset := folded.find(UPLOAD_ROUTE, cursor)) >= 0:
        offsets.append(offset)
        start = offset + len(UPLOAD_ROUTE)
        require(
            raw[start : start + 40] == expected,
            f"{label} contains a non-reviewed raw upload-action occurrence",
        )
        following = raw[start + 40 : start + 41]
        require(
            following == b"" or following in b" \t\r\n\"',}]",
            f"{label} contains a non-delimited raw upload-action pin",
        )
        cursor = start + 40
    require(
        len(offsets) == expected_count,
        f"{label} raw upload-action occurrence count changed",
    )


def exact_bytes(raw: bytes, digest: str, size: int, label: str) -> None:
    require(
        size > 0 and digest != "0" * 64 and len(raw) == size and sha256(raw) == digest,
        f"{label} exact bytes changed or remain unfrozen",
    )


def validate_workflow_bytes(ci_raw: bytes, retired_raw: bytes, v9_raw: bytes) -> None:
    exact_bytes(ci_raw, CI_SHA256, CI_SIZE_BYTES, "whole CI workflow")
    exact_bytes(
        retired_raw,
        RETIRED_V8_WORKFLOW_SHA256,
        RETIRED_V8_WORKFLOW_SIZE_BYTES,
        "whole retired-v8 workflow",
    )
    exact_bytes(v9_raw, V9_WORKFLOW_SHA256, V9_WORKFLOW_SIZE_BYTES, "whole v9 workflow")
    validate_raw_upload_occurrences(ci_raw, "CI workflow", 3)
    validate_raw_upload_occurrences(retired_raw, "retired-v8 workflow", 0)
    validate_raw_upload_occurrences(v9_raw, "v9 workflow", 1)
    canonical = (
        b"uses: actions/upload-artifact@"
        + GOOD_UPLOAD_PIN.encode("ascii")
        + b" # v7.0.1"
    )
    require(
        ci_raw.count(canonical) == 3, "CI canonical upload-action line count changed"
    )
    require(
        v9_raw.count(canonical) == 1, "v9 canonical upload-action line count changed"
    )
    require(
        b"uses: actions/upload-artifact@" not in retired_raw.lower(),
        "retired v8 retained a live upload action",
    )
    require(
        retired_raw.count(C8_COMMIT.encode("ascii")) == 1
        and retired_raw.count(str(C8_CONTRACT_RUN).encode("ascii")) == 1
        and retired_raw.count(str(C8_CONTRACT_FAILED_JOB).encode("ascii")) == 1
        and retired_raw.count(str(C8_CI_RUN).encode("ascii")) == 1
        and retired_raw.count(str(C8_CI_FAILED_JOB).encode("ascii")) == 1
        and retired_raw.count(C8_CONTRACT_RAW_LOG_SHA256.encode("ascii")) == 1
        and retired_raw.count(C8_CI_RAW_LOG_SHA256.encode("ascii")) == 1
        and b"44 successful jobs and sole failed job" in retired_raw
        and CERTIFIED_FAILURE_MARKER in retired_raw
        and b"later PDF, static-contract, and artifact-upload steps were skipped"
        in retired_raw
        and b"identified five changed bindings" in retired_raw
        and b"source reconstruction guards that exact set" in retired_raw
        and b"without establishing unique counterfactual necessity or order"
        in retired_raw
        and b"no L8 record is installed" in retired_raw
        and b"R8 is permanently unissued" in retired_raw
        and b"exit 1\n" in retired_raw,
        "retired-v8 refusal identity changed",
    )
    refusal = b"      - name: Refuse retries and non-main qualification events\n"
    pins = (
        b"      - name: Validate every external action pin and the truncation hostile\n"
    )
    static = (
        b"      - name: Validate static v9 contract in normal and optimized modes\n"
    )
    upload = b"      - name: Upload the exact v9 static result\n"
    stage_pdf = b"      - name: Stage the reviewed Ubuntu luaotfload tool beneath setup-python\n"
    retained_pdf = b"      - name: Recheck the unchanged v6 and v7 publications\n"
    workflow_pdf = b"      - name: Validate the unchanged C8 mathematical-workflow PDF portability gate\n"
    require(
        all(
            v9_raw.count(marker) == 1
            for marker in (
                refusal,
                pins,
                stage_pdf,
                retained_pdf,
                workflow_pdf,
                static,
                upload,
            )
        )
        and v9_raw.index(refusal)
        < v9_raw.index(pins)
        < v9_raw.index(stage_pdf)
        < v9_raw.index(retained_pdf)
        < v9_raw.index(workflow_pdf)
        < v9_raw.index(static)
        < v9_raw.index(upload),
        "v9 attempt refusal, pin/PDF/static gate, or upload order changed",
    )
    for literal in (
        b'formal_tool_path="$pythonLocation/bin/luaotfload-tool"',
        b'luaotfload_source="$(/usr/bin/readlink -f /usr/bin/luaotfload-tool)"',
        b'/usr/bin/install -m 0755 "$luaotfload_source" "$formal_tool_stage"',
        b'/usr/bin/ln -T -- "$formal_tool_stage" "$formal_tool_path"',
        b'workflow_path="$pythonLocation/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin"',
        b"bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh",
        b"bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
    ):
        require(
            v9_raw.count(literal) == 1, f"v9 workflow-PDF route changed: {literal!r}"
        )
    for command in (
        b"python3 -I -S -B scripts/check-github-action-pins.py",
        b"python3 -O -I -S -B scripts/check-github-action-pins.py",
        b"python3 -I -S -B scripts/check-github-action-pins-self-test.py",
        b"python3 -O -I -S -B scripts/check-github-action-pins-self-test.py",
    ):
        require(
            v9_raw.count(command) == 1, "v9 workflow action-pin command roster changed"
        )
        require(
            ci_raw.count(command) == 1, "ordinary CI action-pin command roster changed"
        )
    ci_pin_step = (
        b"      - name: Enforce exact GitHub Action pins and mutation closure\n"
    )
    require(
        ci_raw.count(ci_pin_step) == 1
        and ci_raw.index(ci_pin_step)
        < ci_raw.index(b"      - name: Replay the frozen arithmetic corpus"),
        "ordinary CI action-pin guard order changed",
    )
    require(
        ci_raw.count(
            b"bash --noprofile --norc scripts/check-formal-pdf-set.sh --cross-toolchain"
        )
        == 1
        and ci_raw.index(b'formal_tool_path="$pythonLocation/bin/luaotfload-tool"')
        < ci_raw.index(
            b"bash --noprofile --norc scripts/check-formal-pdf-set.sh --cross-toolchain"
        ),
        "ordinary CI workflow-PDF cross-toolchain route changed",
    )


def recipe_block(raw: bytes, recipe: bytes) -> bytes:
    marker = recipe + b":\n"
    require(raw.count(marker) == 1, f"Just recipe changed: {recipe.decode()}")
    start = raw.index(marker)
    match = re.search(
        rb"(?m)^[a-zA-Z0-9_-]+(?: [^:\n]+)?:\n", raw[start + len(marker) :]
    )
    end = len(raw) if match is None else start + len(marker) + match.start()
    return raw[start:end]


def validate_justfile_bytes(raw: bytes) -> None:
    block = recipe_block(raw, b"ksg-composite-v9")
    required_in_order = (
        b"    command -v rg >/dev/null\n",
        b"    rg --version >/dev/null\n",
        b"    python3 -I -S -B scripts/check-github-action-pins.py",
        b"    python3 -O -I -S -B scripts/check-github-action-pins.py",
        b"    python3 -I -S -B scripts/check-github-action-pins-self-test.py",
        b"    python3 -O -I -S -B scripts/check-github-action-pins-self-test.py",
        b"    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
        b"    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
        b"    python3 -I -S -B scripts/capture-ksg-m1a-composite-v9-local-closure.py --self-test",
        b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact\n",
        b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact\n",
        b"scripts/check-mathematical-workflow-pdf-self-test.sh\n",
        b"scripts/check-mathematical-workflow-pdf.sh --exact\n",
        b"    python3 -I -S -B scripts/check-lean-toolchain-freeze.py\n",
        b"    python3 -I -S -B scripts/check-current-source-state-v1.py\n",
        b"    python3 -I -S -B scripts/capture-ksg-m1a-composite-v9.py --self-test",
        b"    python3 -I -S -B scripts/check-ksg-m1a-composite-v9.py --validate-static",
        b"    python3 -I -S -B scripts/check-ksg-m1a-composite-v9-self-test.py",
    )
    offsets: list[int] = []
    for command in required_in_order:
        require(
            block.count(command) == 1,
            f"v9 Just command missing or duplicated: {command!r}",
        )
        offsets.append(block.index(command))
    require(offsets == sorted(offsets), "v9 Just command order changed")
    require(
        raw.count(b"release-audit:") == 1
        and b" ksg-composite-v9 "
        in raw[raw.index(b"release-audit:") : raw.index(b"release-audit:") + 700]
        and b" ksg-composite-v8 "
        not in raw[raw.index(b"release-audit:") : raw.index(b"release-audit:") + 700],
        "release-audit does not select composite-v9 exactly",
    )


def policy_rows(value: Any, label: str) -> tuple[tuple[str, str, str, str], ...]:
    require(type(value) is list and value != [], f"{label} is not a nonempty array")
    rows: list[tuple[str, str, str, str]] = []
    for index, item in enumerate(value):
        row = exact_keys(item, {"mode", "path", "role", "status"}, f"{label}[{index}]")
        require(
            type(row["path"]) is str
            and V8.V7.V6._v5._v4.validate_relative_path(
                row["path"], f"{label}[{index}] path"
            )
            and row["mode"] in {"100644", "100755"}
            and row["status"] in {"A", "M"}
            and type(row["role"]) is str
            and re.fullmatch(r"[a-z0-9_]+", row["role"]) is not None,
            f"{label}[{index}] changed",
        )
        rows.append((row["path"], row["status"], row["mode"], row["role"]))
    require(rows == sorted(set(rows)), f"{label} is not path-sorted unique")
    require(len({row[0] for row in rows}) == len(rows), f"{label} repeats a path")
    return tuple(rows)


def validate_policy_value(value: Any) -> None:
    root = exact_keys(
        value,
        {
            "base",
            "c8_disposition",
            "c9",
            "diagnosis",
            "nonimplications",
            "publication",
            "r9",
            "replay",
            "repository",
            "schema",
            "schema_revision",
        },
        "composite-v9 path policy",
    )
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-composite-v9-path-policy/v1"
        and root["schema_revision"] == 1
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY,
        "v9 policy identity changed",
    )
    require(
        root["base"]
        == {
            "commit": C8_COMMIT,
            "message": C8_MESSAGE,
            "parent": C8_PARENT,
            "r4_status": "permanently_unissued",
            "r5_status": "permanently_unissued",
            "r6_status": "permanently_unissued",
            "r7_status": "permanently_unissued",
            "r8_status": "permanently_unissued",
            "tree": C8_TREE,
        },
        "v9 policy predecessor changed",
    )
    require(
        root["diagnosis"]
        == {
            "analysis": "read_only_sequential_digest_repin",
            "binding_difference_set": C8_STALE_BINDINGS,
            "evidence_scope": "exact_changed_binding_set_not_unique_counterfactual_necessity_or_order",
            "observed_first_marker": CERTIFIED_FAILURE_MARKER.decode("ascii"),
            "source_guard": "anchor_candidate_assignment_difference_set",
        },
        "v9 policy five-binding diagnosis boundary changed",
    )
    disposition = root["c8_disposition"]
    require(
        type(disposition) is dict
        and set(disposition)
        == {
            "codeql_attempt_1",
            "dedicated_attempt_1",
            "local_recorder",
            "repository_ci_attempt_1",
        }
        and disposition.get("codeql_attempt_1")
        == {"conclusion": "success", "run": C8_CODEQL_RUN}
        and disposition.get("repository_ci_attempt_1")
        == {
            "conclusion": "failure",
            "failed_step": {
                "name": "Run python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                "number": 22,
            },
            "job": C8_CI_FAILED_JOB,
            "raw_log_sha256": C8_CI_RAW_LOG_SHA256,
            "raw_log_size_bytes": C8_CI_RAW_LOG_SIZE_BYTES,
            "retained_artifacts": [
                "coverage-lcov",
                f"post-commit-source-state-v2-{C8_COMMIT}",
                "workspace-sbom",
            ],
            "roster": {"failure": 1, "success": 44, "total": 45},
            "run": C8_CI_RUN,
            "failed_surface": "certified_sxpid2_retained_operational_bindings",
        }
        and disposition.get("local_recorder")
        == {
            "credit": "zero",
            "l8_record": "absent_unissued",
            "recorder": "satisfiable_retained_no_installed_record",
        },
        "v9 policy C8 disposition changed or remains unresolved",
    )
    defect = disposition.get("dedicated_attempt_1")
    require(
        defect
        == {
            "conclusion": "failure",
            "failed_step": {
                "name": "Recheck retained C7 operational surfaces",
                "number": 10,
            },
            "job": C8_CONTRACT_FAILED_JOB,
            "later_static_and_upload_steps": "skipped",
            "raw_log_sha256": C8_CONTRACT_RAW_LOG_SHA256,
            "raw_log_size_bytes": C8_CONTRACT_RAW_LOG_SIZE_BYTES,
            "run": C8_CONTRACT_RUN,
        },
        "v9 policy dedicated C8 defect changed",
    )
    c9 = root["c9"]
    require(
        type(c9) is dict
        and set(c9)
        == {
            "commit_message",
            "delta",
            "delta_state",
            "parent",
            "tree",
            "tree_derivation",
        }
        and c9["commit_message"] == C9_MESSAGE
        and c9["parent"] == C8_COMMIT
        and c9["tree"] is None
        and c9["tree_derivation"]
        == "derive_from_the_exact_unsigned_direct_child_commit"
        and c9["delta_state"] == "final_exact"
        and policy_rows(c9["delta"], "C9 policy delta") == EXPECTED_C9_ROWS,
        "v9 policy C9 topology changed",
    )
    r9 = root["r9"]
    require(
        type(r9) is dict
        and set(r9) == {"commit_message", "delta", "evidence_state", "parent"}
        and r9["commit_message"] == R9_MESSAGE
        and r9["parent"] == "derive_exact_c9_commit"
        and r9["evidence_state"] == "conditional_absent_at_c9"
        and policy_rows(r9["delta"], "R9 policy delta") == R9_ROWS,
        "v9 policy conditional R9 topology changed",
    )
    require(
        root["publication"]
        == {
            "c9_new_pdf": "none",
            "retained_family": "exact_composite_v8_publication_unchanged",
            "workflow_pdf": {
                "committed_pdf": "unchanged",
                "source": "unchanged",
                "portability_gate": "unchanged",
            },
        }
        and root["replay"]
        == {
            "current": R14_RELATIVE,
            "predicate": "fresh_post_c8_r14_and_current_source_match_c9",
            "retained_prior": {
                "path": R13_RELATIVE,
                "sha256": R13_SHA256,
                "size_bytes": R13_SIZE_BYTES,
            },
        },
        "v9 publication or replay policy changed",
    )
    require(
        root["nonimplications"] == POLICY_NONIMPLICATIONS,
        "v9 policy nonimplication boundary changed",
    )


def validate_schema_bytes(raw: bytes, relative: str) -> dict[str, Any]:
    schema = parse_json(raw, f"v9 schema {relative}")
    require(
        type(schema) is dict
        and schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        and schema.get("$id")
        == f"https://github.com/sepahead/pid-rs/blob/main/{relative}",
        f"v9 closed schema identity changed: {relative}",
    )
    if relative == CAPTURE_SCHEMA_RELATIVE:
        defs = schema.get("$defs")
        require(
            type(defs) is dict
            and set(schema) == {"$defs", "$id", "$schema", "oneOf"}
            and defs.get("predecessorDocument", {})
            .get("properties", {})
            .get("schema_revision")
            == {"const": 9}
            and defs.get("successorDocument", {})
            .get("properties", {})
            .get("schema_revision")
            == {"const": 9}
            and defs.get("predecessorDocument", {}).get("type") == "object"
            and defs.get("predecessorDocument", {}).get("additionalProperties") is False
            and defs.get("successorDocument", {}).get("type") == "object"
            and defs.get("successorDocument", {}).get("additionalProperties") is False
            and defs.get("predecessorDocument", {}).get("required")
            == sorted(defs.get("predecessorDocument", {}).get("properties", {}))
            and defs.get("successorDocument", {}).get("required")
            == sorted(defs.get("successorDocument", {}).get("properties", {}))
            and schema.get("oneOf")
            == [
                {"$ref": "#/$defs/predecessorDocument"},
                {"$ref": "#/$defs/successorDocument"},
            ],
            "v9 hosted schema revision or phase union changed",
        )
    elif relative == LOCAL_SCHEMA_RELATIVE:
        limits = schema.get("properties", {}).get("limits")
        require(
            set(schema)
            == {
                "$defs",
                "$id",
                "$schema",
                "additionalProperties",
                "properties",
                "required",
                "type",
            }
            and schema.get("type") == "object"
            and schema.get("additionalProperties") is False
            and schema.get("required") == sorted(schema.get("properties", {}))
            and schema.get("properties", {}).get("schema_revision") == {"const": 4}
            and schema.get("properties", {}).get("schema")
            == {"const": "pid-rs/ksg-rev4-m1a-composite-local-closure/v4"},
            "L9 local schema revision changed",
        )
        require(
            type(limits) is dict
            and limits.get("type") == "object"
            and limits.get("additionalProperties") is False
            and limits.get("required") == sorted(LOCAL_LIMITS)
            and limits.get("properties")
            == {key: {"const": value} for key, value in LOCAL_LIMITS.items()},
            "L9 local schema resource limits differ from the recorder/checker bounds",
        )
    else:
        require(
            relative == RECEIPT_SCHEMA_RELATIVE
            and set(schema)
            == {
                "$defs",
                "$id",
                "$schema",
                "additionalProperties",
                "properties",
                "required",
                "type",
            }
            and schema.get("type") == "object"
            and schema.get("additionalProperties") is False
            and schema.get("required") == sorted(schema.get("properties", {}))
            and schema.get("properties", {}).get("schema_revision") == {"const": 9}
            and schema.get("properties", {}).get("schema")
            == {"const": "pid-rs/ksg-rev4-m1a-composite-receipt/v9"},
            "v9 receipt schema revision changed",
        )
        defects = schema["properties"].get("defects")
        prefixes = defects.get("prefixItems") if type(defects) is dict else None
        require(
            type(defects) is dict
            and set(defects) == {"items", "maxItems", "minItems", "prefixItems", "type"}
            and defects["type"] == "array"
            and defects["items"] is False
            and defects["minItems"] == defects["maxItems"] == 1
            and type(prefixes) is list
            and len(prefixes) == 1
            and all(
                type(item) is dict
                and item.get("type") == "object"
                and item.get("additionalProperties") is False
                and item.get("required") == sorted(item.get("properties", {}))
                for item in prefixes
            )
            and prefixes[0]["properties"].get("id")
            == {"const": "c8_certified_sxpid2_retained_binding_staleness"}
            and prefixes[0]["properties"].get("observed_marker")
            == {"const": CERTIFIED_FAILURE_MARKER.decode("ascii")}
            and prefixes[0]["properties"].get("scope")
            == {
                "const": [
                    "hosted_repository_ci_step_22",
                    "hosted_dedicated_v8_step_10",
                ]
            }
            and prefixes[0]["properties"].get("stale_binding_count") == {"const": 5}
            and prefixes[0]["properties"].get("stale_bindings")
            == {"const": C8_STALE_BINDINGS},
            "v9 receipt exact one-defect schema changed",
        )
        encoded = canonical_json(schema, pretty=True)
        require(
            b"missing_rg" not in encoded
            and b"contradiction" not in encoded
            and b"unattempted" not in encoded
            and b"current_r13" not in encoded
            and b"retained_r11" not in encoded
            and b"c8_certified_sxpid2_retained_binding_staleness" in encoded
            and b'"defects"' in encoded
            and b'"defect"' not in encoded
            and b"current_r14" in encoded
            and b"retained_r13" in encoded,
            "v9 receipt schema retained a false predecessor or replay model",
        )
    return schema


def frozen_c9_required_paths() -> set[str]:
    cut_paths = {
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
        CURRENT_SOURCE_RELATIVE,
        R14_RELATIVE,
        "scripts/check-lean-toolchain-freeze-self-test.py",
        "scripts/check-lean-toolchain-freeze.py",
        "scripts/generate-lean-4.33-replay.py",
    }
    return {
        path
        for path, _status, _mode, _role in EXPECTED_C9_ROWS
        if path not in cut_paths
    }


def validate_source_bindings(entries: dict[str, Any]) -> None:
    required = frozen_c9_required_paths()
    require(
        set(FROZEN_C9_PATH_BINDINGS) == required,
        "v9 acyclic exact binding inventory remains unfrozen",
    )
    for path, (digest, size, mode) in FROZEN_C9_PATH_BINDINGS.items():
        raw = tree_blob(entries, path)
        require(
            entries[path].mode == mode and len(raw) == size and sha256(raw) == digest,
            f"frozen C9 path bytes changed: {path}",
        )


def validate_c9_narrative_boundaries(documents: dict[str, bytes]) -> None:
    require(
        set(documents) == set(C9_NARRATIVE_PATHS),
        "C9 narrative boundary path set changed",
    )
    for path in C9_NARRATIVE_PATHS:
        normalized = re.sub(rb"\s+", b" ", documents[path])
        require(
            C9_L8_NARRATIVE_BOUNDARY in normalized
            and b"No L8 record was run" not in normalized
            and b"No L8 capture was launched" not in normalized
            and b"operator-invocation history is established" not in normalized,
            f"L8 narrative asserts unsupported operator history: {path}",
        )
        require(
            b"failed c8 publication family" not in normalized.lower(),
            f"C9 narrative conflates publication with hosted failure: {path}",
        )


def validate_capture_root(
    raw: bytes,
    phase: str,
    c9_entries: dict[str, Any],
    c9: str,
    c9_tree: str,
    schema: dict[str, Any],
) -> tuple[dict[str, Any], Any]:
    require(
        0 < len(raw) <= V8.V7.V6.MAX_JSON_BYTES,
        f"{phase} capture size is outside the bound",
    )
    value = parse_json(raw, f"composite-v9 {phase} hosted capture")
    validate_schema_instance(value, schema, f"composite-v9 {phase} hosted capture")
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v8_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        f"composite-v9 {phase} capture",
    )
    expected_subject = {"predecessor_commit": C8_COMMIT, "predecessor_tree": C8_TREE}
    if phase == "successor_qualification":
        expected_subject.update({"successor_commit": c9, "successor_tree": c9_tree})
    require(
        phase in PHASE_ROLES
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v9"
        and root["schema_revision"] == 9
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["phase"] == phase
        and root["subject"] == expected_subject
        and root["capture_tool"] == descriptor(c9_entries, CAPTURE_TOOL_RELATIVE)
        and root["immutable_v8_primitives"] == CAPTURE_PRIMITIVE
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS,
        f"composite-v9 {phase} capture identity changed",
    )
    runs = exact_keys(
        root["runs"], set(PHASE_ROLES[phase]), f"composite-v9 {phase} run map"
    )
    require(
        all(type(item) is int and item > 0 for item in runs.values())
        and len(set(runs.values())) == 3
        and (phase != "predecessor_failure" or runs == PREDECESSOR_RUNS),
        f"composite-v9 {phase} run identifiers changed or overlap",
    )
    retry_keys: list[tuple[str, int, int, str, int]] = []
    require(type(root["retry_events"]) is list, "capture retry events are not an array")
    for item in root["retry_events"]:
        event = exact_keys(
            item,
            {
                "attempt",
                "category",
                "logical_request",
                "page",
                "path",
                "repetition",
                "response_sha256",
                "response_size_bytes",
            },
            "capture retry event",
        )
        require(
            type(event["attempt"]) is int
            and event["attempt"] in {1, 2}
            and type(event["repetition"]) is int
            and event["repetition"] in {1, 2}
            and event["category"]
            in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(event["logical_request"]) is str
            and event["logical_request"]
            and type(event["page"]) is int
            and event["page"] >= 0
            and type(event["path"]) is str
            and event["path"].startswith(f"/repos/{REPOSITORY}/")
            and type(event["response_sha256"]) is str
            and SHA256_RE.fullmatch(event["response_sha256"]) is not None
            and type(event["response_size_bytes"]) is int
            and 0 <= event["response_size_bytes"] <= V8.V7.V6.MAX_JSON_BYTES,
            "capture retry event changed or exceeds its bound",
        )
        retry_keys.append(
            (
                event["logical_request"],
                event["repetition"],
                event["page"],
                event["path"],
                event["attempt"],
            )
        )
    require(
        retry_keys == sorted(set(retry_keys)),
        "capture retry events are not sorted unique",
    )
    captures = root["captures"]
    require(
        type(captures) is list and 0 < len(captures) <= V8.V7.V6.MAX_CAPTURE_ROWS,
        "capture response count is outside the bound",
    )
    decoded = [
        V8.V7.V6.decode_capture_row(item, f"capture response {index}")
        for index, item in enumerate(captures)
    ]
    require(
        sum(len(body) for _row, body in decoded) <= V8.V7.V6.MAX_CAPTURE_BODY_BYTES,
        "capture bodies exceed the checker budget",
    )
    keys = [
        (row["logical_request"], row["repetition"], row["page"], row["path"])
        for row, _body in decoded
    ]
    require(keys == sorted(set(keys)), "capture responses are not sorted unique")
    capture_keys = set(keys)
    retry_groups: dict[tuple[str, int, int, str], list[int]] = defaultdict(list)
    for logical, repetition, page, path, attempt in retry_keys:
        key = (logical, repetition, page, path)
        require(key in capture_keys, "retry event has no successful request row")
        retry_groups[key].append(attempt)
    require(
        all(
            values == list(range(1, len(values) + 1)) and len(values) <= 2
            for values in retry_groups.values()
        ),
        "retry attempts are not consecutive and bounded",
    )
    grouped: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]] = defaultdict(
        list
    )
    for row, body in decoded:
        grouped[(row["logical_request"], row["repetition"])].append((row, body))
    return root, V8.V7.CaptureRows(dict(grouped))


def normalize_run(value: Any, role: str, run_id: int, head: str) -> dict[str, Any]:
    require(type(value) is dict, f"{role} run response is not an object")
    repository = value.get("repository")
    head_repository = value.get("head_repository")
    result = {
        "conclusion": value.get("conclusion"),
        "event": value.get("event"),
        "head_branch": value.get("head_branch"),
        "head_sha": value.get("head_sha"),
        "name": value.get("name"),
        "path": value.get("path"),
        "repository_id": repository.get("id") if type(repository) is dict else None,
        "run_attempt": value.get("run_attempt"),
        "run_id": value.get("id"),
        "status": value.get("status"),
        "workflow_id": value.get("workflow_id"),
    }
    expected = EXPECTED_CONCLUSIONS[role]
    require(
        expected in {"failure", "success"},
        "terminal C8 CI conclusion remains unresolved",
    )
    require(
        result["run_id"] == run_id
        and type(result["run_id"]) is int
        and result["head_sha"] == head
        and result["head_branch"] == "main"
        and result["run_attempt"] == 1
        and type(result["run_attempt"]) is int
        and result["status"] == "completed"
        and result["conclusion"] == expected
        and type(result["workflow_id"]) is int
        and result["workflow_id"] > 0
        and type(repository) is dict
        and repository.get("full_name") == REPOSITORY
        and type(head_repository) is dict
        and head_repository.get("full_name") == REPOSITORY
        and result["repository_id"] == C8_REPOSITORY_ID
        and head_repository.get("id") == C8_REPOSITORY_ID,
        f"{role} run identity or disposition changed",
    )
    routes = {
        "predecessor_ci": ("CI", CI_RELATIVE, "push"),
        "predecessor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
        ),
        "predecessor_contract": (
            "KSG M1a composite v8",
            RETIRED_V8_WORKFLOW_RELATIVE,
            "push",
        ),
        "successor_ci": ("CI", CI_RELATIVE, "push"),
        "successor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
        ),
        "successor_contract": ("KSG M1a composite v9", V9_WORKFLOW_RELATIVE, "push"),
    }
    require(
        (result["name"], result["path"], result["event"]) == routes[role],
        f"{role} exact workflow route changed",
    )
    return result


def normalize_jobs(
    values: list[Any], role: str, run_id: int, head: str
) -> tuple[list[dict[str, Any]], set[int]]:
    jobs: list[dict[str, Any]] = []
    for value in values:
        require(type(value) is dict, f"{role} job is not an object")
        job_id = V8.V7.exact_int(value.get("id"), f"{role} job id", 1)
        conclusion = value.get("conclusion")
        require(
            value.get("status") == "completed"
            and conclusion in {"success", "failure", "skipped", "cancelled"}
            and value.get("run_id") == run_id
            and value.get("run_attempt") == 1
            and value.get("head_sha") == head
            and type(value.get("name")) is str
            and value.get("name"),
            f"{role} job identity changed",
        )
        started, completed = V8.V7.V6.normalized_job_timestamps(value, conclusion, role)
        steps_raw = value.get("steps")
        require(
            type(steps_raw) is list and steps_raw != [], f"{role} job steps are absent"
        )
        steps: list[dict[str, Any]] = []
        for step in steps_raw:
            require(type(step) is dict, f"{role} step is not an object")
            item = {
                "conclusion": step.get("conclusion"),
                "name": step.get("name"),
                "number": step.get("number"),
                "status": step.get("status"),
            }
            require(
                item["status"] == "completed"
                and item["conclusion"] in {"success", "failure", "skipped", "cancelled"}
                and type(item["name"]) is str
                and item["name"]
                and type(item["number"]) is int
                and item["number"] > 0,
                f"{role} step identity changed",
            )
            steps.append(item)
        steps.sort(key=lambda item: item["number"])
        require(
            len(steps) == len({item["number"] for item in steps}),
            f"{role} step numbers overlap",
        )
        if conclusion == "failure":
            require(
                any(item["conclusion"] == "failure" for item in steps),
                f"{role} failed job has no failed step",
            )
        elif conclusion == "success":
            require(
                all(item["conclusion"] in {"success", "skipped"} for item in steps),
                f"{role} success job has adverse step",
            )
        jobs.append(
            {
                "completed_at": completed,
                "conclusion": conclusion,
                "job_id": job_id,
                "name": value["name"],
                "started_at": started,
                "status": "completed",
                "steps": steps,
            }
        )
    jobs.sort(key=lambda item: item["job_id"])
    require(
        len(jobs) == len({item["job_id"] for item in jobs}), f"{role} job IDs overlap"
    )
    failed = {item["job_id"] for item in jobs if item["conclusion"] == "failure"}
    kind = role.removeprefix("predecessor_").removeprefix("successor_")
    expected_count = 45 if kind == "ci" else 4 if kind == "codeql" else 1
    require(len(jobs) == expected_count, f"{role} job count changed")
    if EXPECTED_CONCLUSIONS[role] == "success":
        require(
            failed == set() and all(item["conclusion"] == "success" for item in jobs),
            f"{role} has adverse jobs",
        )
    else:
        expected_failed = {
            "predecessor_ci": {C8_CI_FAILED_JOB},
            "predecessor_contract": {C8_CONTRACT_FAILED_JOB},
        }
        require(
            role in expected_failed and failed == expected_failed[role],
            "predecessor failure partition changed",
        )
    names = tuple(sorted(item["name"] for item in jobs))
    if kind == "ci":
        require(
            names == V8.V7.V6._v5._v4.EXPECTED_CI_JOB_NAMES, f"{role} CI roster changed"
        )
        if role == "predecessor_ci":
            failed_job = next(
                item for item in jobs if item["job_id"] == C8_CI_FAILED_JOB
            )
            require(
                failed_job["name"] == "Exact-count directed-rounding SxPID2 reference"
                and [
                    (item["number"], item["name"])
                    for item in failed_job["steps"]
                    if item["conclusion"] == "failure"
                ]
                == [
                    (
                        22,
                        "Run python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
                    )
                ]
                and sum(item["conclusion"] == "success" for item in jobs) == 44,
                "predecessor CI sole certified-SxPID2 failure identity changed",
            )
    elif kind == "codeql":
        require(
            names
            == tuple(
                sorted(
                    f"Analyze ({language})"
                    for language in V8.V7.V6._v5._v4.LANGUAGE_ORDER
                )
            ),
            f"{role} CodeQL roster changed",
        )
    else:
        expected_name = (
            "Validate the composite-v8 bounded correction contract"
            if role == "predecessor_contract"
            else "Validate the composite-v9 bounded correction contract"
        )
        require(names == (expected_name,), f"{role} contract job name changed")
        if role == "predecessor_contract":
            require(
                jobs[0]["job_id"] == C8_CONTRACT_FAILED_JOB
                and [
                    (item["number"], item["name"])
                    for item in jobs[0]["steps"]
                    if item["conclusion"] == "failure"
                ]
                == [(10, "Recheck retained C7 operational surfaces")],
                "predecessor contract retained-surface failure identity changed",
            )
        else:
            required_steps = {
                "Normalize only the reviewed inert checkout residue",
                "Refuse retries and non-main qualification events",
                "Validate every external action pin and the truncation hostile",
                "Stage the reviewed Ubuntu luaotfload tool beneath setup-python",
                "Recheck retained C8 gates under the five C9 binding repairs",
                "Recheck the unchanged v6 and v7 publications",
                "Validate the unchanged C8 mathematical-workflow PDF portability gate",
                "Validate fresh replay and current-source custody",
                "Validate static v9 contract in normal and optimized modes",
                "Upload the exact v9 static result",
            }
            by_name = {item["name"]: item for item in jobs[0]["steps"]}
            require(
                required_steps <= set(by_name)
                and all(
                    by_name[name]["conclusion"] == "success" for name in required_steps
                ),
                "successor contract required step roster changed",
            )
    return jobs, failed


def validate_predecessor_log(rows: Any, role: str, failed: set[int]) -> None:
    expected_jobs = {
        "predecessor_ci": {C8_CI_FAILED_JOB},
        "predecessor_contract": {C8_CONTRACT_FAILED_JOB},
    }
    require(
        role in expected_jobs and failed == expected_jobs[role],
        "predecessor failed-log identity changed",
    )
    job_id = next(iter(expected_jobs[role]))
    observations: list[tuple[str, int]] = []
    for repetition in (1, 2):
        values = rows.take(
            f"{role}_failed_job_{job_id}_log",
            repetition,
        )
        require(
            len(values) == 1
            and values[0][0]["page"] == 0
            and values[0][0]["path"]
            == f"/repos/{REPOSITORY}/actions/jobs/{job_id}/logs"
            and values[0][0]["response_kind"] == "log",
            "predecessor exact raw job-log route changed",
        )
        raw = values[0][1]
        validate_predecessor_log_bytes(raw, role)
        observations.append((sha256(raw), len(raw)))
    require(
        observations[0] == observations[1], "repeated predecessor raw job logs differ"
    )


def validate_predecessor_log_bytes(raw: bytes, role: str) -> None:
    if role == "predecessor_contract":
        require(
            len(raw) == C8_CONTRACT_RAW_LOG_SIZE_BYTES
            and sha256(raw) == C8_CONTRACT_RAW_LOG_SHA256
            and raw.count(CERTIFIED_FAILURE_MARKER) == 1,
            "exact C8 dedicated retained-surface failure log changed",
        )
    else:
        require(
            role == "predecessor_ci"
            and len(raw) == C8_CI_RAW_LOG_SIZE_BYTES
            and sha256(raw) == C8_CI_RAW_LOG_SHA256
            and raw.count(CERTIFIED_FAILURE_MARKER) == 1,
            "exact C8 repository-CI retained-surface failure log changed",
        )


def validate_contract_artifact(
    artifacts: list[dict[str, Any]], archives: dict[int, bytes], c9: str, c9_tree: str
) -> None:
    require(len(artifacts) == 1, "successor contract artifact count changed")
    item = artifacts[0]
    require(
        item["name"] == f"ksg-m1a-composite-v9-static-{c9}",
        "successor contract artifact name changed",
    )
    member_path = "ksg-m1a-composite-v9-static.json"
    require(
        item["members"]
        == [member for member in item["members"] if member["path"] == member_path]
        and len(item["members"]) == 1,
        "successor contract artifact members changed",
    )
    raw = V8.V7.member_bytes(
        archives[item["artifact_id"]], member_path, "successor contract artifact"
    )
    value = parse_json(raw, "successor contract static result", canonical=False)
    require(
        raw == canonical_json(value, pretty=False)
        and value
        == {
            "c8_commit": C8_COMMIT,
            "c9_commit": c9,
            "head": c9,
            "r9_commit": None,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v9-static-validation/v1",
            "tree": c9_tree,
        },
        "successor contract static result changed",
    )


def derive_role(
    rows: Any,
    role: str,
    run_id: int,
    head: str,
    entries: dict[str, Any],
    tree: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    repeated: list[
        tuple[
            dict[str, Any],
            list[dict[str, Any]],
            list[dict[str, Any]],
            dict[int, bytes],
            Any,
            Any,
        ]
    ] = []
    failed_sets: list[set[int]] = []
    for repetition in (1, 2):
        run = normalize_run(
            V8.V7.single_json_response(
                rows,
                f"{role}_run",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}",
            ),
            role,
            run_id,
            head,
        )
        jobs, failed = normalize_jobs(
            V8.V7.paged_json_response(
                rows,
                f"{role}_jobs",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs",
                "jobs",
            ),
            role,
            run_id,
            head,
        )
        artifact_values = V8.V7.paged_json_response(
            rows,
            f"{role}_artifacts",
            repetition,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts",
            "artifacts",
        )
        artifacts, archives = V8.V7.normalized_artifacts(
            artifact_values,
            rows,
            role,
            run_id,
            run["repository_id"],
            head,
            repetition,
        )
        analyses: Any = None
        alerts: Any = None
        if role == "successor_codeql":
            analyses = V8.V7.normalized_analyses(
                V8.V7.paged_json_response(
                    rows,
                    f"{role}_analyses",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
                    None,
                ),
                jobs,
                head,
                role,
            )
            alert_values = {
                state: V8.V7.paged_json_response(
                    rows,
                    f"{role}_alerts_{state}",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}",
                    None,
                )
                for state in ("dismissed", "fixed", "open")
            }
            alerts = V8.V7.normalized_alerts(alert_values, role)
        repeated.append((run, jobs, artifacts, archives, analyses, alerts))
        failed_sets.append(failed)
    first, second = repeated
    require(
        canonical_json((first[0], first[1], first[2], first[4], first[5]), pretty=False)
        == canonical_json(
            (second[0], second[1], second[2], second[4], second[5]), pretty=False
        ),
        f"{role} repeated normalized observations differ",
    )
    run, jobs, artifacts, archives, analyses, _alerts = first
    require(
        failed_sets[0] == failed_sets[1],
        f"{role} repeated failed-job identities differ",
    )
    expected_names = {
        "predecessor_ci": {
            "coverage-lcov",
            f"post-commit-source-state-v2-{C8_COMMIT}",
            "workspace-sbom",
        },
        "predecessor_codeql": set(),
        "predecessor_contract": set(),
        "successor_ci": {
            "coverage-lcov",
            f"post-commit-source-state-v2-{head}",
            "workspace-sbom",
        },
        "successor_codeql": set(),
        "successor_contract": {f"ksg-m1a-composite-v9-static-{head}"},
    }
    require(
        {item["name"] for item in artifacts} == expected_names[role],
        f"{role} artifact names changed",
    )
    if role in {"predecessor_ci", "successor_ci"}:
        V8.V7.validate_postcommit_artifact(
            artifacts, archives, entries, head, tree, role
        )
    elif role == "successor_contract":
        validate_contract_artifact(artifacts, archives, head, tree)
    if role in {"predecessor_ci", "predecessor_contract"}:
        validate_predecessor_log(rows, role, failed_sets[0])
    return (
        {
            "artifact_names": sorted(item["name"] for item in artifacts),
            "conclusion": run["conclusion"],
            "failed_job_ids": sorted(failed_sets[0]),
            "job_count": len(jobs),
            "jobs_sha256": project_digest(jobs),
            "role": role,
            "run_id": run["run_id"],
            "workflow_path": run["path"],
        },
        {
            "analysis_ids": []
            if analyses is None
            else [item["analysis_id"] for item in analyses],
            "artifact_ids": [item["artifact_id"] for item in artifacts],
            "job_ids": [item["job_id"] for item in jobs],
            "repository_id": run["repository_id"],
            "run_id": run["run_id"],
        },
    )


def validate_identifier_domains(domains: list[dict[str, Any]]) -> None:
    require(
        domains != [] and len({item["repository_id"] for item in domains}) == 1,
        "hosted repository ID join changed",
    )
    for field, label in (
        ("run_id", "run"),
        ("job_ids", "job"),
        ("artifact_ids", "artifact"),
        ("analysis_ids", "CodeQL analysis"),
    ):
        values = (
            [item[field] for item in domains]
            if field == "run_id"
            else [identifier for item in domains for identifier in item[field]]
        )
        require(
            len(values) == len(set(values)),
            f"hosted {label} identifier domains overlap",
        )


def derive_phase(
    raw: bytes,
    phase: str,
    c9_entries: dict[str, Any],
    c9: str,
    c9_tree: str,
    schema: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    capture, rows = validate_capture_root(raw, phase, c9_entries, c9, c9_tree, schema)
    head = C8_COMMIT if phase == "predecessor_failure" else c9
    tree = C8_TREE if phase == "predecessor_failure" else c9_tree
    entries = parse_tree(tree)
    derived = [
        derive_role(rows, role, capture["runs"][role], head, entries, tree)
        for role in PHASE_ROLES[phase]
    ]
    rows.finish()
    roles = [item[0] for item in derived]
    domains = [item[1] for item in derived]
    validate_identifier_domains(domains)
    return (
        {
            "capture_sha256": sha256(raw),
            "normalized_sha256": project_digest(roles),
            "phase": phase,
            "roles": roles,
        },
        domains,
    )


def load_local_validator(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_exact_composite_v9_local_record_validator")
    module.__file__ = os.fspath(ROOT / LOCAL_TOOL_RELATIVE)
    module.__package__ = ""
    try:
        code = compile(
            raw, module.__file__, "exec", dont_inherit=True, optimize=sys.flags.optimize
        )
        exec(code, module.__dict__)
    except (OSError, RuntimeError, SyntaxError) as error:
        raise ContractError(f"cannot load exact v9 local validator: {error}") from None
    return module


def decode_local_binding(value: Any, label: str, maximum: int) -> bytes:
    raw = V8.V7.V6.decode_local_binding(value, label, maximum)
    V8.V7.V6.reject_local_sensitive_bytes(raw, label)
    return raw


def derive_local(
    raw: bytes,
    c9_entries: dict[str, Any],
    c9: str,
    c9_tree: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    require(
        0 < len(raw) <= LOCAL_LIMITS["record_bytes"],
        "L9 record size is outside the bound",
    )
    value = parse_json(raw, "composite-v9 L9 closure")
    validate_schema_instance(value, schema, "composite-v9 L9 closure")
    validator_raw = tree_blob(c9_entries, LOCAL_TOOL_RELATIVE)
    validator = load_local_validator(validator_raw)
    try:
        validator.validate_record_value(value)
    except Exception as error:
        raise ContractError(
            f"composite-v9 L9 semantic validation failed: {error}"
        ) from None
    require(
        value["subject"]
        == {
            "c8_parent": C8_COMMIT,
            "c9_commit": c9,
            "c9_message": C9_MESSAGE,
            "c9_tree": c9_tree,
        }
        and value["limits"] == LOCAL_LIMITS
        and value["immutable_v8_primitives"] == LOCAL_PRIMITIVE,
        "L9 subject, limits, or primitive identity changed",
    )
    expected_authorities: list[dict[str, Any]] = []
    for path, role in sorted(LOCAL_AUTHORITY_ROLES.items()):
        authority_raw = tree_blob(c9_entries, path)
        require(
            c9_entries[path].mode == LOCAL_AUTHORITY_MODES[path]
            and 0 < len(authority_raw) <= LOCAL_LIMITS["authority_stream_bytes"],
            f"L9 named authority mode or size changed: {path}",
        )
        expected_authorities.append(
            {
                "path": path,
                "role": role,
                "sha256": sha256(authority_raw),
                "size_bytes": len(authority_raw),
            }
        )
    require(
        value["authorities"] == expected_authorities,
        "L9 authorities differ from exact C9",
    )
    invocation = value["invocation"]
    stdout = decode_local_binding(
        invocation["stdout"], "L9 command stdout", LOCAL_LIMITS["command_stream_bytes"]
    )
    stderr = decode_local_binding(
        invocation["stderr"], "L9 command stderr", LOCAL_LIMITS["command_stream_bytes"]
    )
    require(stdout + stderr != b"", "L9 command retained no output")
    reviewed = value["reviewed_executables"]
    for item in reviewed:
        version_stdout = decode_local_binding(
            item["version_stdout"],
            f"L9 {item['name']} version stdout",
            LOCAL_LIMITS["version_stream_bytes"],
        )
        version_stderr = decode_local_binding(
            item["version_stderr"],
            f"L9 {item['name']} version stderr",
            LOCAL_LIMITS["version_stream_bytes"],
        )
        require(
            version_stdout + version_stderr != b"",
            f"L9 {item['name']} version output is empty",
        )
    require(
        [item["name"] for item in reviewed] == sorted(V8.V7.LOCAL_TOOL_SPECS)
        and all(
            item["version_argv"]
            == [item["name"], *V8.V7.LOCAL_TOOL_SPECS[item["name"]]]
            for item in reviewed
        ),
        "L9 reviewed executable roster changed",
    )
    return {
        "authorities_sha256": project_digest(expected_authorities),
        "command": {
            "argv": invocation["argv"],
            "elapsed_monotonic_ns": invocation["elapsed_monotonic_ns"],
            "exit_code": invocation["exit_code"],
            "stderr_sha256": invocation["stderr"]["sha256"],
            "stderr_size_bytes": invocation["stderr"]["size_bytes"],
            "stdout_sha256": invocation["stdout"]["sha256"],
            "stdout_size_bytes": invocation["stdout"]["size_bytes"],
            "timed_out": invocation["timed_out"],
        },
        "platform": {
            "architecture": value["platform"]["architecture"],
            "operating_system": value["platform"]["operating_system"],
            "python_implementation": value["platform"]["python_implementation"],
        },
        "record_binding": {
            "path": LOCAL_RECORD_RELATIVE,
            "sha256": sha256(raw),
            "size_bytes": len(raw),
        },
        "reviewed_executables_sha256": project_digest(reviewed),
        "subject": {"c9_commit": c9, "c9_tree": c9_tree},
    }


def lean_replay_projection_sha256(receipt: dict[str, Any]) -> str:
    """Reproduce the r14 projection without importing the mutable Lean checker."""

    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    require(type(custody) is dict, "r14 custody-gate inventory is malformed")
    require(
        tuple(custody) == LEAN_CUSTODY_PATHS, "r14 custody-gate exact path set drifted"
    )
    projected["custody_gate_sha256"] = {
        LEAN_SELF_TEST_RELATIVE: custody[LEAN_SELF_TEST_RELATIVE]
    }
    try:
        raw = json.dumps(
            projected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError) as error:
        raise ContractError(f"cannot project r14 replay receipt: {error}") from None
    return sha256(raw)


def lean_r14_source_cuts(raw: bytes) -> tuple[str, str, str, bytes]:
    """Extract and normalize exactly the three final Lean/r14 checksum cuts."""

    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"Lean checker source is not UTF-8: {error}") from None
    patterns = (
        (
            "replay projection",
            re.compile(
                r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            re.compile(
                r"^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = .+$", re.MULTILINE
            ),
            'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
        ),
        (
            "composite-v9 checker scalar",
            re.compile(
                r'^EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            re.compile(
                r"^EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = .+$", re.MULTILINE
            ),
            'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "0" * 64',
        ),
        (
            "composite-v9 operational-map row",
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v9\.py": "([0-9a-f]{64})",$',
                re.MULTILINE,
            ),
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v9\.py": .+$',
                re.MULTILINE,
            ),
            '    "scripts/check-ksg-m1a-composite-v9.py": "0" * 64,',
        ),
    )
    values: list[str] = []
    normalized = source
    for label, pattern, assignment_pattern, replacement in patterns:
        matches = list(pattern.finditer(normalized))
        require(
            len(matches) == 1 and len(assignment_pattern.findall(normalized)) == 1,
            f"Lean {label} cut is not unique and final",
        )
        value = matches[0].group(1)
        require(value != "0" * 64, f"Lean {label} cut remains a placeholder")
        values.append(value)
        normalized = pattern.sub(replacement, normalized, count=1)
    return values[0], values[1], values[2], normalized.encode("utf-8")


def normalized_lean_checker_cut(raw: bytes) -> str:
    """Extract the one final normalized-Lean binding from v9 checker bytes."""

    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"composite-v9 checker is not UTF-8: {error}") from None
    pattern = re.compile(
        r'^EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "([0-9a-f]{64})"$',
        re.MULTILINE,
    )
    assignment_pattern = re.compile(
        r"^EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = .+$", re.MULTILINE
    )
    matches = list(pattern.finditer(source))
    require(
        len(matches) == 1 and len(assignment_pattern.findall(source)) == 1,
        "normalized Lean checker cut is not a unique final literal",
    )
    value = matches[0].group(1)
    require(value != "0" * 64, "normalized Lean checker cut remains a placeholder")
    return value


def validate_lean_r14_checksum_cut(
    v9_checker_raw: bytes, lean_checker_raw: bytes
) -> str:
    """Bind final v9 bytes to the exactly three-cut-normalized Lean source."""

    checker_digest = sha256(v9_checker_raw)
    projection, scalar_cut, operational_cut, normalized = lean_r14_source_cuts(
        lean_checker_raw
    )
    require(
        scalar_cut == checker_digest and operational_cut == checker_digest,
        "Lean composite-v9 checker cuts do not bind the exact v9 checker bytes",
    )
    require(
        normalized_lean_checker_cut(v9_checker_raw) == sha256(normalized),
        "normalized Lean checker authority changed",
    )
    return projection


def validate_lean_r14_receipt_cuts(
    v9_checker_raw: bytes,
    lean_checker_raw: bytes,
    lean_self_test_raw: bytes,
    r13: dict[str, Any],
    r14: dict[str, Any],
    projection: str,
) -> None:
    """Join the r14 projection and custody-only exact-set semantics."""

    operational = r14.get("operational_wiring_sha256")
    scientific = r14.get("checker_sha256")
    require(
        type(operational) is dict
        and operational.get(CHECKER_RELATIVE) == sha256(v9_checker_raw),
        "Lean r14 operational map does not bind the v9 checker bytes",
    )
    require(
        type(scientific) is dict and scientific == r13.get("checker_sha256"),
        "Lean r14 scientific checker inventory changed from r13",
    )
    require(
        lean_replay_projection_sha256(r14) == projection,
        "Lean r14 projection cut changed",
    )
    final_custody = r14.get("custody_gate_sha256")
    replay_custody = r14.get("replay_custody_gate_sha256")
    require(
        type(final_custody) is dict
        and type(replay_custody) is dict
        and tuple(final_custody) == LEAN_CUSTODY_PATHS
        and tuple(replay_custody) == LEAN_CUSTODY_PATHS,
        "Lean r14 custody inventories are not the exact reviewed path set",
    )
    custody_paths = set(LEAN_CUSTODY_PATHS)
    require(
        custody_paths.isdisjoint(operational) and custody_paths.isdisjoint(scientific),
        "Lean r14 custody paths entered an ordinary digest inventory",
    )
    require(
        final_custody[LEAN_CHECKER_RELATIVE] == sha256(lean_checker_raw)
        and final_custody[LEAN_SELF_TEST_RELATIVE] == sha256(lean_self_test_raw)
        and replay_custody[LEAN_SELF_TEST_RELATIVE]
        == final_custody[LEAN_SELF_TEST_RELATIVE],
        "Lean r14 final or replay-time custody changed",
    )
    final_projection_line = (
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + projection + '"'
    ).encode("ascii")
    placeholder_projection_line = (
        b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    )
    require(
        lean_checker_raw.count(final_projection_line) == 1
        and placeholder_projection_line not in lean_checker_raw,
        "Lean r14 projection line is not exactly reconstructable",
    )
    replay_checker_raw = lean_checker_raw.replace(
        final_projection_line, placeholder_projection_line, 1
    )
    require(
        replay_custody[LEAN_CHECKER_RELATIVE] == sha256(replay_checker_raw),
        "Lean r14 replay-time checker custody changed",
    )


def validate_fresh_replay(
    c8_entries: dict[str, Any], c9_entries: dict[str, Any]
) -> None:
    r13_raw = tree_blob(c8_entries, R13_RELATIVE)
    require(
        len(r13_raw) == R13_SIZE_BYTES and sha256(r13_raw) == R13_SHA256,
        "retained r13 exact bytes changed",
    )
    r13 = parse_json(r13_raw, "retained r13")
    r14_raw = tree_blob(c9_entries, R14_RELATIVE)
    r14 = parse_json(r14_raw, "current r14", canonical=False)
    require(
        r14_raw == canonical_json(r14, pretty=True)
        and r14.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and r14.get("status") == "passed"
        and r14.get("source_sha256") == r13.get("source_sha256")
        and r14.get("active_configuration") == r13.get("active_configuration")
        and r14.get("prior_replay_preservation_sha256", {}).get(R13_RELATIVE)
        == R13_SHA256
        and r14.get("prior_replay_schema", {}).get(R13_RELATIVE)
        == "pid-rs/lean-current-project-replay/v2",
        "r14 is not a fresh theorem-preserving successor of retained r13",
    )
    operational = r14.get("operational_wiring_sha256")
    require(type(operational) is dict, "r14 operational wiring is absent")
    non_operational_paths = {
        CURRENT_SOURCE_RELATIVE,
        R14_RELATIVE,
        "audit/evidence/completion-active-resume.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md",
        LEAN_CHECKER_RELATIVE,
        LEAN_SELF_TEST_RELATIVE,
    }
    operational_c9_paths = tuple(
        path
        for path, _status, _mode, _role in EXPECTED_C9_ROWS
        if path not in non_operational_paths
    )
    require(
        len(operational_c9_paths) == 22,
        "r14 C9 operational-source inventory changed",
    )
    for path in operational_c9_paths:
        require(
            operational.get(path) == sha256(tree_blob(c9_entries, path)),
            f"r14 does not bind exact C9 operational source: {path}",
        )
    active_claims = r14.get("active_claim_authority_sha256")
    require(type(active_claims) is dict, "r14 active-claim authority is absent")
    for path in (
        "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md",
    ):
        require(
            active_claims.get(path) == sha256(tree_blob(c9_entries, path)),
            f"r14 does not bind exact C9 active-claim pointer: {path}",
        )
    active_resume = r14.get("active_resume_sha256")
    require(
        type(active_resume) is dict
        and active_resume.get("audit/evidence/completion-active-resume.md")
        == sha256(tree_blob(c9_entries, "audit/evidence/completion-active-resume.md")),
        "r14 does not bind exact C9 active-resume pointer",
    )
    v9_checker_raw = tree_blob(c9_entries, CHECKER_RELATIVE)
    lean_checker_raw = tree_blob(c9_entries, LEAN_CHECKER_RELATIVE)
    lean_self_test_raw = tree_blob(c9_entries, LEAN_SELF_TEST_RELATIVE)
    projection = validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)
    validate_lean_r14_receipt_cuts(
        v9_checker_raw,
        lean_checker_raw,
        lean_self_test_raw,
        r13,
        r14,
        projection,
    )
    V8.V7.V6._v5._v4.validate_current_source(c9_entries, "C9")


def publication_binding(
    c8_entries: dict[str, Any], c9_entries: dict[str, Any]
) -> dict[str, Any]:
    values = {
        field: descriptor(c8_entries, path)
        for field, path in PUBLICATION_FIELDS.items()
    }
    for path in PUBLICATION_FIELDS.values():
        require(
            c9_entries.get(path) == c8_entries.get(path),
            f"C9 changed retained C8 publication: {path}",
        )
    require(
        c9_entries.get(WORKFLOW_PDF_RELATIVE) == c8_entries.get(WORKFLOW_PDF_RELATIVE)
        and c9_entries.get(WORKFLOW_PDF_SOURCE_RELATIVE)
        == c8_entries.get(WORKFLOW_PDF_SOURCE_RELATIVE)
        and c9_entries.get(WORKFLOW_PDF_GATE_RELATIVE)
        == c8_entries.get(WORKFLOW_PDF_GATE_RELATIVE)
        and c9_entries.get(WORKFLOW_PDF_SELF_TEST_RELATIVE)
        == c8_entries.get(WORKFLOW_PDF_SELF_TEST_RELATIVE),
        "C9 changed the retained workflow PDF, source, gate, or hostile suite",
    )
    pdf = descriptor(c8_entries, WORKFLOW_PDF_RELATIVE)
    source = descriptor(c8_entries, WORKFLOW_PDF_SOURCE_RELATIVE)
    retained_gate = descriptor(c8_entries, WORKFLOW_PDF_GATE_RELATIVE)
    retained_self_test = descriptor(c8_entries, WORKFLOW_PDF_SELF_TEST_RELATIVE)
    require(
        (pdf["sha256"], pdf["size_bytes"])
        == (WORKFLOW_PDF_SHA256, WORKFLOW_PDF_SIZE_BYTES)
        and (source["sha256"], source["size_bytes"])
        == (WORKFLOW_PDF_SOURCE_SHA256, WORKFLOW_PDF_SOURCE_SIZE_BYTES)
        and (retained_gate["sha256"], retained_gate["size_bytes"])
        == (
            PREDECESSOR_WORKFLOW_PDF_GATE_SHA256,
            PREDECESSOR_WORKFLOW_PDF_GATE_SIZE_BYTES,
        )
        and (retained_self_test["sha256"], retained_self_test["size_bytes"])
        == (
            PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SHA256,
            PREDECESSOR_WORKFLOW_PDF_SELF_TEST_SIZE_BYTES,
        ),
        "retained C8 workflow PDF/source/gate authority changed",
    )
    values["retained_c8_workflow_pdf_gate"] = retained_gate
    values["retained_c8_workflow_pdf_self_test"] = retained_self_test
    return {
        "authorities": values,
        "c9_new_pdf": False,
        "status": "retained_exact_c8_family",
        "workflow_pdf": {
            "committed_pdf": pdf,
            "portability_gate": descriptor(c9_entries, WORKFLOW_PDF_GATE_RELATIVE),
            "source": source,
            "status": "unchanged_pdf_source_and_gate",
        },
    }


def contract_authorities(
    c8_entries: dict[str, Any], c9_entries: dict[str, Any]
) -> list[dict[str, Any]]:
    values = [
        authority(c9_entries, path, role)
        for path, _status, _mode, role in EXPECTED_C9_ROWS
        if path != CURRENT_SOURCE_RELATIVE
    ]
    values.extend(
        authority(c8_entries, path, f"retained_c8_{field}")
        for field, path in PUBLICATION_FIELDS.items()
    )
    values.extend(
        (
            authority(
                c8_entries, WORKFLOW_PDF_RELATIVE, "retained_workflow_pdf_baseline"
            ),
            authority(
                c8_entries, WORKFLOW_PDF_SOURCE_RELATIVE, "retained_workflow_pdf_source"
            ),
            authority(
                c8_entries, WORKFLOW_PDF_GATE_RELATIVE, "retained_workflow_pdf_gate"
            ),
            authority(
                c8_entries,
                WORKFLOW_PDF_SELF_TEST_RELATIVE,
                "retained_workflow_pdf_hostile_suite",
            ),
        )
    )
    values.sort(key=lambda item: (item["path"], item["role"]))
    require(
        len(values) == len({(item["path"], item["role"]) for item in values}),
        "v9 contract authority roles overlap",
    )
    return values


def derive_receipt(
    predecessor_raw: bytes,
    local_raw: bytes,
    successor_raw: bytes,
    c8_entries: dict[str, Any],
    c9_entries: dict[str, Any],
    c9: str,
    c9_tree: str,
    schemas: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> dict[str, Any]:
    predecessor, predecessor_domains = derive_phase(
        predecessor_raw, "predecessor_failure", c9_entries, c9, c9_tree, schemas[0]
    )
    successor, successor_domains = derive_phase(
        successor_raw, "successor_qualification", c9_entries, c9, c9_tree, schemas[0]
    )
    validate_identifier_domains([*predecessor_domains, *successor_domains])
    local = derive_local(local_raw, c9_entries, c9, c9_tree, schemas[1])
    result = {
        "capture_bindings": [
            {
                "path": PREDECESSOR_CAPTURE_RELATIVE,
                "phase": "predecessor_failure",
                "sha256": sha256(predecessor_raw),
                "size_bytes": len(predecessor_raw),
            },
            {
                "path": SUCCESSOR_CAPTURE_RELATIVE,
                "phase": "successor_qualification",
                "sha256": sha256(successor_raw),
                "size_bytes": len(successor_raw),
            },
        ],
        "contract_authorities": contract_authorities(c8_entries, c9_entries),
        "defects": [
            {
                "evidence": [
                    {
                        "capture": {
                            "path": PREDECESSOR_CAPTURE_RELATIVE,
                            "sha256": sha256(predecessor_raw),
                            "size_bytes": len(predecessor_raw),
                        },
                        "job": C8_CI_FAILED_JOB,
                        "raw_log_sha256": C8_CI_RAW_LOG_SHA256,
                        "raw_log_size_bytes": C8_CI_RAW_LOG_SIZE_BYTES,
                        "route": "repository_ci",
                        "run": C8_CI_RUN,
                    },
                    {
                        "capture": {
                            "path": PREDECESSOR_CAPTURE_RELATIVE,
                            "sha256": sha256(predecessor_raw),
                            "size_bytes": len(predecessor_raw),
                        },
                        "job": C8_CONTRACT_FAILED_JOB,
                        "raw_log_sha256": C8_CONTRACT_RAW_LOG_SHA256,
                        "raw_log_size_bytes": C8_CONTRACT_RAW_LOG_SIZE_BYTES,
                        "route": "dedicated_v8",
                        "run": C8_CONTRACT_RUN,
                    },
                ],
                "id": "c8_certified_sxpid2_retained_binding_staleness",
                "observed_marker": CERTIFIED_FAILURE_MARKER.decode("ascii"),
                "scope": [
                    "hosted_repository_ci_step_22",
                    "hosted_dedicated_v8_step_10",
                ],
                "stale_binding_count": 5,
                "stale_bindings": C8_STALE_BINDINGS,
                "status": "failed_zero_credit",
            },
        ],
        "local_qualification": local,
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "observations": [predecessor, successor],
        "predecessor_local": {
            "credit": "zero",
            "l8_record": "absent_unissued",
            "r8_receipt_issued": False,
            "recorder": "satisfiable_retained_no_installed_record",
        },
        "publication": publication_binding(c8_entries, c9_entries),
        "replay": {
            "current_r14": descriptor(c9_entries, R14_RELATIVE),
            "current_source": descriptor(c9_entries, CURRENT_SOURCE_RELATIVE),
            "predicate": "fresh_post_c8_r14_and_current_source_match_c9",
            "retained_r13": descriptor(c8_entries, R13_RELATIVE),
        },
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v9",
        "schema_revision": 9,
        "subject": {
            "c8_commit": C8_COMMIT,
            "c8_tree": C8_TREE,
            "c9_commit": c9,
            "c9_tree": c9_tree,
        },
        "verdict": {
            "c8_hosted_qualification": "failed_zero_credit",
            "c8_local_qualification": "absent_zero_credit",
            "c8_publication": "published_unchanged",
            "c9_bounded_repair": "pass",
            "c9_hosted_observation": "pass",
            "c9_local_qualification": "pass",
            "r4_receipt_issued": False,
            "r5_receipt_issued": False,
            "r6_receipt_issued": False,
            "r7_receipt_issued": False,
            "r8_receipt_issued": False,
            "r9_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
    }
    validate_schema_instance(result, schemas[2], "derived composite-v9 receipt")
    return result


def commit_message(oid: str) -> str:
    raw = V8.V7.V6._v5._v4.exact_object(oid, "commit", maximum=1024 * 1024)
    _headers, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", f"commit message envelope changed at {oid[:12]}")
    try:
        return message.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(
            f"commit message is not UTF-8 at {oid[:12]}: {error}"
        ) from None


def validate_forbidden_history(head: str, c9: str, r9: str | None) -> None:
    raw = V8.V7.git("rev-list", "--reverse", f"{C8_COMMIT}..{head}")
    try:
        descendants = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"C9 reachable history is not ASCII: {error}") from None
    commits = [C8_COMMIT, *descendants]
    require(commits[-1] == head, "HEAD is outside the C8 successor history")
    pathspecs = tuple(f":(literal){path}" for path in FORBIDDEN_EVIDENCE_PATHS)
    for oid in commits:
        rows = V8.V7.git("ls-tree", "-z", "--name-only", oid, "--", *pathspecs)
        require(rows == b"", f"forbidden R4-R8 evidence path appears at {oid[:12]}")
        message = commit_message(oid)
        require(
            message not in FORBIDDEN_MESSAGES,
            f"forbidden R4-R8 message appears at {oid[:12]}",
        )
        require(
            message != C9_MESSAGE or oid == c9, "C9 message appears outside exact C9"
        )
        require(
            message != R9_MESSAGE or (r9 is not None and oid == r9),
            "R9 message appears outside exact R9",
        )


def schemas_from_tree(
    entries: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for path in (
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
    ):
        require(
            entries.get(path) is not None and entries[path].mode == "100644",
            f"C9 schema mode changed: {path}",
        )
        values.append(validate_schema_bytes(tree_blob(entries, path), path))
    return values[0], values[1], values[2]


def ast_dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def ast_shape(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def parse_source_ast(raw: bytes, label: str) -> ast.Module:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"{label} is not UTF-8: {error}") from None
    try:
        return ast.parse(text, filename=label, mode="exec", type_comments=True)
    except SyntaxError as error:
        raise ContractError(f"{label} is not valid Python: {error}") from None


def exact_top_level_assignment(
    module: ast.Module, target_name: str, expected_expression: str, label: str
) -> None:
    matches: list[ast.AST] = []
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if ast_dotted_name(target) == target_name:
                    matches.append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and ast_dotted_name(statement.target) == target_name
        ):
            matches.append(
                statement.value if statement.value is not None else statement
            )
    expected = ast.parse(expected_expression, mode="eval").body
    require(
        len(matches) == 1 and ast_shape(matches[0]) == ast_shape(expected),
        f"{label} exact top-level assignment changed: {target_name}",
    )


def top_level_assignment_targets(module: ast.Module, prefix: str) -> list[str]:
    result: list[str] = []
    for statement in module.body:
        targets: list[ast.AST] = []
        if isinstance(statement, ast.Assign):
            targets.extend(statement.targets)
        elif isinstance(statement, ast.AnnAssign):
            targets.append(statement.target)
        elif isinstance(statement, ast.AugAssign):
            targets.append(statement.target)
        for target in targets:
            name = ast_dotted_name(target)
            if name is not None and name.startswith(prefix):
                result.append(name)
    return result


def exact_function(module: ast.Module, name: str, label: str) -> ast.FunctionDef:
    matches = [
        statement
        for statement in module.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name == name
    ]
    require(
        len(matches) == 1 and isinstance(matches[0], ast.FunctionDef),
        f"{label} function shape changed: {name}",
    )
    return matches[0]


def direct_call_name(statement: ast.stmt) -> str | None:
    value: ast.AST | None = None
    if isinstance(statement, ast.Expr):
        value = statement.value
    elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
        value = statement.value
    if isinstance(value, ast.Call):
        return ast_dotted_name(value.func)
    return None


def ast_call_counts(node: ast.AST, names: set[str]) -> dict[str, int]:
    counts = {name: 0 for name in names}
    for candidate in ast.walk(node):
        if isinstance(candidate, ast.Call):
            name = ast_dotted_name(candidate.func)
            if name in counts:
                counts[name] += 1
    return counts


def validate_hosted_capture_ast(raw: bytes) -> None:
    module = parse_source_ast(raw, "v9 hosted capture")
    exact_top_level_assignment(
        module,
        "V8.V7.V6.workflow_identity",
        "workflow_identity",
        "v9 hosted capture",
    )
    exact_top_level_assignment(
        module,
        "V8.V7.V6.expected_successor_artifact_names",
        "expected_successor_artifact_names",
        "v9 hosted capture",
    )
    require(
        top_level_assignment_targets(module, "V8.V7.V6.")
        == ["V8.V7.V6.workflow_identity", "V8.V7.V6.expected_successor_artifact_names"],
        "v9 hosted capture gained an unreviewed nested primitive rebind",
    )
    main = exact_function(module, "main", "v9 hosted capture")
    repetition_loops = [
        node
        for node in ast.walk(main)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "repetition"
        and ast_shape(node.iter) == ast_shape(ast.parse("(1, 2)", mode="eval").body)
    ]
    require(len(repetition_loops) == 1, "v9 hosted capture repetition loop changed")
    role_loops = [
        statement
        for statement in repetition_loops[0].body
        if isinstance(statement, ast.For)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "role"
        and ast_shape(statement.iter)
        == ast_shape(ast.parse("sorted(runs)", mode="eval").body)
    ]
    require(len(role_loops) == 1, "v9 hosted capture role loop changed")
    role_loop = role_loops[0]
    run_assignments = [
        statement
        for statement in role_loop.body
        if isinstance(statement, ast.Assign)
        and direct_call_name(statement) == "V8.V7.V6.capture_run"
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Tuple)
        and [ast_dotted_name(item) for item in statement.targets[0].elts]
        == ["artifacts", "failed_job_ids", "repository_id"]
    ]
    require(
        len(run_assignments) == 1,
        "v9 hosted capture operational run assignment changed",
    )
    require(
        sum(
            direct_call_name(statement) == "V8.V7.V6.capture_artifacts"
            for statement in role_loop.body
        )
        == 1,
        "v9 hosted capture operational artifact call changed",
    )
    phase_if = [
        statement
        for statement in role_loop.body
        if isinstance(statement, ast.If)
        and ast_shape(statement.test)
        == ast_shape(
            ast.parse('arguments.phase == "predecessor_failure"', mode="eval").body
        )
    ]
    codeql_if = [
        statement
        for statement in role_loop.body
        if isinstance(statement, ast.If)
        and ast_shape(statement.test)
        == ast_shape(ast.parse('role == "successor_codeql"', mode="eval").body)
    ]
    require(
        len(phase_if) == 1
        and sum(
            direct_call_name(statement) == "V8.V7.V6.capture_failed_logs"
            for statement in phase_if[0].body
        )
        == 1
        and len(codeql_if) == 1
        and sum(
            direct_call_name(statement) == "V8.V7.V6.capture_codeql"
            for statement in codeql_if[0].body
        )
        == 1,
        "v9 hosted capture conditional log or CodeQL route changed",
    )
    names = {
        "V8.V7.V6.capture_run",
        "V8.V7.V6.capture_artifacts",
        "V8.V7.V6.capture_failed_logs",
        "V8.V7.V6.capture_codeql",
    }
    require(
        ast_call_counts(main, names) == {name: 1 for name in names},
        "v9 hosted capture main-loop nested primitive call roster changed",
    )


def validate_local_capture_ast(raw: bytes) -> None:
    module = parse_source_ast(raw, "v9 local capture")
    for name, expression in (
        ("MAX_VERSION_STREAM_BYTES", "64 * 1024"),
        ("MAX_AUTHORITY_STREAM_BYTES", "2 * 1024 * 1024"),
        ("MAX_COMMAND_STREAM_BYTES", "8 * 1024 * 1024"),
        ("MAX_RECORD_BYTES", "32 * 1024 * 1024"),
        ("MAX_EXECUTABLE_BYTES", "256 * 1024 * 1024"),
    ):
        exact_top_level_assignment(module, name, expression, "v9 local capture")
    exact_top_level_assignment(
        module,
        "LIMITS",
        """{
            "authority_stream_bytes": MAX_AUTHORITY_STREAM_BYTES,
            "command_stream_bytes": MAX_COMMAND_STREAM_BYTES,
            "executable_bytes": MAX_EXECUTABLE_BYTES,
            "record_bytes": MAX_RECORD_BYTES,
            "version_stream_bytes": MAX_VERSION_STREAM_BYTES,
        }""",
        "v9 local capture",
    )
    exact_top_level_assignment(
        module, "PRIMITIVES", "V8.PRIMITIVES", "v9 local capture"
    )
    exact_top_level_assignment(
        module, "PRIMITIVES.C5_COMMIT", "C8_COMMIT", "v9 local capture"
    )
    exact_top_level_assignment(
        module, "PRIMITIVES.C6_MESSAGE", "C9_MESSAGE", "v9 local capture"
    )
    exact_top_level_assignment(
        module,
        "PRIMITIVES.TOOL_SPECS",
        'dict(PRIMITIVES.TOOL_SPECS) | {"rg": ("--version",)}',
        "v9 local capture",
    )
    require(
        top_level_assignment_targets(module, "PRIMITIVES.")
        == ["PRIMITIVES.C5_COMMIT", "PRIMITIVES.C6_MESSAGE", "PRIMITIVES.TOOL_SPECS"],
        "v9 local capture gained an unreviewed top-level primitive rebind",
    )
    authority = exact_function(module, "authority_descriptors", "v9 local capture")
    require(
        ast_call_counts(authority, {"PRIMITIVES.read_regular"})
        == {"PRIMITIVES.read_regular": 1},
        "v9 local capture authority read route changed",
    )
    capture = exact_function(module, "capture_under_fixed_umask", "v9 local capture")
    expected_counts = {
        "PRIMITIVES.reject_ambient_secrets": 1,
        "PRIMITIVES.create_output": 1,
        "PRIMITIVES.fixed_path_directories": 1,
        "PRIMITIVES.minimal_environment": 1,
        "PRIMITIVES.toolchain_observation": 1,
        "PRIMITIVES.repository_snapshot": 2,
        "PRIMITIVES.run_bounded": 1,
        "PRIMITIVES.reject_sensitive_output": 2,
        "PRIMITIVES.validate_output_descriptor": 2,
    }
    require(
        ast_call_counts(capture, set(expected_counts)) == expected_counts,
        "v9 local capture operational primitive call roster changed",
    )
    main = exact_function(module, "main", "v9 local capture")
    require(
        ast_call_counts(main, {"PRIMITIVES.under_fixed_umask"})
        == {"PRIMITIVES.under_fixed_umask": 1},
        "v9 local capture fixed-umask entry route changed",
    )


def validate_capture_source_routes(hosted_raw: bytes, local_raw: bytes) -> None:
    validate_hosted_capture_ast(hosted_raw)
    validate_local_capture_ast(local_raw)


def validate_certified_rebind_difference_guard_source(raw: bytes) -> None:
    require(
        C8_STALE_BINDINGS == sorted(set(C8_STALE_BINDINGS)),
        "C8 five-binding mismatch inventory is not sorted unique",
    )
    module = parse_source_ast(raw, "certified-SxPID2 rebind-difference self-test")
    safe_environment = exact_function(
        module,
        "safe_environment",
        "certified-SxPID2 rebind-difference self-test",
    )
    expected_safe_environment = ast.parse(
        '''def safe_environment() -> dict[str, str]:
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
                "TMPDIR": "/tmp",
            }
        '''
    ).body[0]
    require(
        ast_shape(safe_environment) == ast_shape(expected_safe_environment),
        "certified-SxPID2 isolated Git environment changed",
    )
    expression = (
        "frozenset({" + ", ".join(repr(item) for item in C8_STALE_BINDINGS) + "})"
    )
    exact_top_level_assignment(
        module,
        "EXPECTED_C8_FAILURE_BINDING_DIFFERENCES",
        expression,
        "certified-SxPID2 rebind-difference self-test",
    )
    reconstruction = exact_function(
        module,
        "validate_checker_source_reconstruction",
        "certified-SxPID2 rebind-difference self-test",
    )
    expected_assignment = ast.parse(
        """binding_differences = {
            *(
                f"execution-container:{path}"
                for path in EXECUTION_CONTAINER_PATHS
                if candidate_execution[path] != anchor_execution[path]
            ),
            *(
                f"reviewed-documentation:{path}"
                for path in REVIEWED_DOCUMENTATION_PATHS
                if candidate_documentation[path] != anchor_documentation[path]
            ),
            *(
                f"support-gate:{path}"
                for path in SUPPORT_GATE_PATHS
                if candidate_support[path] != anchor_support[path]
            ),
            *(
                ("release-audit-line:justfile",)
                if candidate_release_digest != anchor_release_digest
                else ()
            ),
        }"""
    ).body[0]
    expected_require = ast.parse(
        """require(
            binding_differences == EXPECTED_C8_FAILURE_BINDING_DIFFERENCES,
            "C8 failure five-binding difference set changed",
        )"""
    ).body[0]
    assignment_indices = [
        index
        for index, statement in enumerate(reconstruction.body)
        if ast_shape(statement) == ast_shape(expected_assignment)
    ]
    require_indices = [
        index
        for index, statement in enumerate(reconstruction.body)
        if ast_shape(statement) == ast_shape(expected_require)
    ]
    require(
        len(assignment_indices) == len(require_indices) == 1
        and assignment_indices[0] < require_indices[0],
        "certified-SxPID2 anchor/candidate binding-difference route changed",
    )


def validate_fresh_replay_source_routes(raw: bytes) -> None:
    module = parse_source_ast(raw, "v9 composite checker")
    fresh = exact_function(module, "validate_fresh_replay", "v9 composite checker")
    expected_non_operational = ast.parse(
        """{
            CURRENT_SOURCE_RELATIVE,
            R14_RELATIVE,
            \"audit/evidence/completion-active-resume.md\",
            \"claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md\",
            \"claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md\",
            \"claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md\",
            \"claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md\",
            LEAN_CHECKER_RELATIVE,
            LEAN_SELF_TEST_RELATIVE,
        }""",
        mode="eval",
    ).body
    expected_operational = ast.parse(
        """tuple(
            path
            for path, _status, _mode, _role in EXPECTED_C9_ROWS
            if path not in non_operational_paths
        )""",
        mode="eval",
    ).body
    assignments: dict[str, list[ast.AST]] = defaultdict(list)
    for statement in fresh.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            name = ast_dotted_name(statement.targets[0])
            if name in {"non_operational_paths", "operational_c9_paths"}:
                assignments[name].append(statement.value)
    require(
        len(assignments["non_operational_paths"]) == 1
        and ast_shape(assignments["non_operational_paths"][0])
        == ast_shape(expected_non_operational)
        and len(assignments["operational_c9_paths"]) == 1
        and ast_shape(assignments["operational_c9_paths"][0])
        == ast_shape(expected_operational),
        "v9 r14 operational-source partition changed",
    )
    expected_operational_loop = ast.parse(
        """for path in operational_c9_paths:
            require(
                operational.get(path) == sha256(tree_blob(c9_entries, path)),
                f\"r14 does not bind exact C9 operational source: {path}\",
            )"""
    ).body[0]
    require(
        sum(
            ast_shape(statement) == ast_shape(expected_operational_loop)
            for statement in fresh.body
        )
        == 1,
        "v9 r14 operational-source comparison loop changed",
    )
    checksum_statement = ast.parse(
        "projection = validate_lean_r14_checksum_cut(v9_checker_raw, lean_checker_raw)"
    ).body[0]
    receipt_statement = ast.parse(
        """validate_lean_r14_receipt_cuts(
            v9_checker_raw,
            lean_checker_raw,
            lean_self_test_raw,
            r13,
            r14,
            projection,
        )"""
    ).body[0]
    current_source_statement = ast.parse(
        'V8.V7.V6._v5._v4.validate_current_source(c9_entries, "C9")'
    ).body[0]
    expected_sequence = (
        ast_shape(checksum_statement),
        ast_shape(receipt_statement),
        ast_shape(current_source_statement),
    )
    indices: list[int] = []
    for expected in expected_sequence:
        matches = [
            index
            for index, statement in enumerate(fresh.body)
            if ast_shape(statement) == expected
        ]
        require(
            len(matches) == 1,
            "v9 r14 checksum, receipt, or current-source route changed",
        )
        indices.append(matches[0])
    require(indices == sorted(indices), "v9 r14 route order changed")

    source_validator = exact_function(
        module, "validate_c9_sources", "v9 composite checker"
    )
    route_statement = ast.parse(
        "validate_fresh_replay_source_routes(tree_blob(c9_entries, CHECKER_RELATIVE))"
    ).body[0]
    fresh_statement = ast.parse("validate_fresh_replay(c8_entries, c9_entries)").body[0]
    route_matches = [
        index
        for index, statement in enumerate(source_validator.body)
        if ast_shape(statement) == ast_shape(route_statement)
    ]
    fresh_matches = [
        index
        for index, statement in enumerate(source_validator.body)
        if ast_shape(statement) == ast_shape(fresh_statement)
    ]
    require(
        len(route_matches) == len(fresh_matches) == 1
        and route_matches[0] < fresh_matches[0],
        "v9 r14 source-custody call route changed",
    )


def validate_c9_sources(
    c8_entries: dict[str, Any], c9_entries: dict[str, Any], c9: str, c9_tree: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    policy_raw = tree_blob(c9_entries, POLICY_RELATIVE)
    require(
        policy_raw
        == canonical_json(
            parse_json(policy_raw, "C9 path policy", canonical=False), pretty=True
        ),
        "C9 path policy is not canonical pretty JSON",
    )
    validate_policy_value(parse_json(policy_raw, "C9 path policy"))
    validate_source_bindings(c9_entries)
    validate_c9_narrative_boundaries(
        {path: tree_blob(c9_entries, path) for path in C9_NARRATIVE_PATHS}
    )
    validate_workflow_bytes(
        tree_blob(c9_entries, CI_RELATIVE),
        tree_blob(c9_entries, RETIRED_V8_WORKFLOW_RELATIVE),
        tree_blob(c9_entries, V9_WORKFLOW_RELATIVE),
    )
    validate_justfile_bytes(tree_blob(c9_entries, JUSTFILE_RELATIVE))
    require(
        len(tree_blob(c9_entries, V8_CHECKER_RELATIVE)) == V8_CHECKER_SIZE_BYTES
        and sha256(tree_blob(c9_entries, V8_CHECKER_RELATIVE)) == V8_CHECKER_SHA256
        and len(tree_blob(c9_entries, V8_SELF_TEST_RELATIVE)) == V8_SELF_TEST_SIZE_BYTES
        and sha256(tree_blob(c9_entries, V8_SELF_TEST_RELATIVE)) == V8_SELF_TEST_SHA256,
        "C9 changed exact retained v8 checker authorities",
    )
    capture_source = tree_blob(c9_entries, CAPTURE_TOOL_RELATIVE)
    local_source = tree_blob(c9_entries, LOCAL_TOOL_RELATIVE)
    for label, raw in (
        ("hosted capture", capture_source),
        ("local capture", local_source),
    ):
        require(
            b"missing_rg" not in raw
            and b"counterexample" not in raw
            and b"local_authority_bound_contradiction" not in raw
            and b"No L8 capture was launched" not in raw
            and b"satisfiable_retained_unattempted" not in raw,
            f"v9 {label} retained a false C8 defect or operator-history assertion",
        )
    require(
        capture_source.count(CAPTURE_PRIMITIVE["sha256"].encode("ascii")) == 1
        and capture_source.count(b"24_111") == 1,
        "v9 hosted capture immutable transport binding changed",
    )
    require(
        local_source.count(LOCAL_PRIMITIVE["sha256"].encode("ascii")) == 1
        and b"PRIMITIVES = V8.PRIMITIVES\n" in local_source
        and local_source.count(ACTION_PIN_CHECKER_RELATIVE.encode("ascii")) == 1
        and local_source.count(ACTION_PIN_SELF_TEST_RELATIVE.encode("ascii")) == 1
        and b"named_authority_roster_hostiles_rejected" in local_source,
        "v9 local capture primitive or named pin-authority route changed",
    )
    validate_capture_source_routes(capture_source, local_source)
    validate_certified_rebind_difference_guard_source(
        tree_blob(c9_entries, "scripts/check-certified-sxpid2-claim-self-test.py")
    )
    validate_fresh_replay_source_routes(tree_blob(c9_entries, CHECKER_RELATIVE))
    schemas = schemas_from_tree(c9_entries)
    publication_binding(c8_entries, c9_entries)
    validate_fresh_replay(c8_entries, c9_entries)
    predecessor_raw = tree_blob(c9_entries, PREDECESSOR_CAPTURE_RELATIVE)
    predecessor, _domains = derive_phase(
        predecessor_raw,
        "predecessor_failure",
        c9_entries,
        c9,
        c9_tree,
        schemas[0],
    )
    require(
        [item["conclusion"] for item in predecessor["roles"]]
        == ["failure", "success", "failure"]
        and predecessor["roles"][2]["failed_job_ids"] == [C8_CONTRACT_FAILED_JOB]
        and predecessor["roles"][0]["failed_job_ids"] == [C8_CI_FAILED_JOB]
        and predecessor["roles"][1]["failed_job_ids"] == [],
        "C8 predecessor is not the exact one-defect/two-route hosted partition",
    )
    return schemas


def validate_topology() -> dict[str, Any]:
    require(
        C8_CI_CONCLUSION == "failure", "terminal C8 CI conclusion remains unresolved"
    )
    _c7_entries, c8_entries = validate_c8_anchor()
    head, head_tree = V8.V7.V6.validate_repository()
    head_entries = parse_tree(head_tree)
    require(
        V8.V7.V6.git_predicate("merge-base", "--is-ancestor", C8_COMMIT, head),
        "published C8 is not an ancestor of HEAD",
    )
    c9 = V8.V7.V6._v5._v4.commit_introducing(POLICY_RELATIVE)
    c9_commit = parse_commit(c9)
    require(
        c9_commit.parent == C8_COMMIT and c9_commit.message == C9_MESSAGE,
        "C9 is not the exact unsigned direct child of published C8",
    )
    c9_tree = c9_commit.tree
    c9_entries = parse_tree(c9_tree)
    policy = parse_json(tree_blob(c9_entries, POLICY_RELATIVE), "C9 path policy")
    validate_policy_value(policy)
    require(
        changed_entries(c8_entries, c9_entries)
        == tuple(
            (path, status, mode) for path, status, mode, _role in EXPECTED_C9_ROWS
        ),
        "C8 to C9 delta differs from exact v9 policy rows",
    )
    modified = {
        path for path, status, _mode, _role in EXPECTED_C9_ROWS if status == "M"
    }
    for path, entry in c8_entries.items():
        if path not in modified:
            require(
                c9_entries.get(path) == entry,
                f"C9 changed non-sanctioned C8 bytes: {path}",
            )
    for path, _status, mode, _role in EXPECTED_C9_ROWS:
        require(
            c9_entries.get(path) is not None and c9_entries[path].mode == mode,
            f"C9 path missing or wrong mode: {path}",
        )
    require(
        all(
            path in c9_entries
            for path in (
                PREDECESSOR_CAPTURE_RELATIVE,
                R14_RELATIVE,
                CURRENT_SOURCE_RELATIVE,
            )
        )
        and all(
            path not in c9_entries
            for path in (
                LOCAL_RECORD_RELATIVE,
                SUCCESSOR_CAPTURE_RELATIVE,
                RECEIPT_RELATIVE,
            )
        ),
        "C9 predecessor/replay versus R9 evidence phase separation changed",
    )
    schemas = validate_c9_sources(c8_entries, c9_entries, c9, c9_tree)
    receipt_present = RECEIPT_RELATIVE in head_entries
    if receipt_present:
        r9 = V8.V7.V6._v5._v4.commit_introducing(RECEIPT_RELATIVE)
        r9_commit = parse_commit(r9)
        require(
            r9_commit.parent == c9 and r9_commit.message == R9_MESSAGE and head == r9,
            "R9 is not the exact unsigned direct C9 child and current HEAD",
        )
        r9_entries = parse_tree(r9_commit.tree)
        require(
            changed_entries(c9_entries, r9_entries)
            == tuple((path, status, mode) for path, status, mode, _role in R9_ROWS),
            "C9 to R9 delta differs from exact four-row receipt cut",
        )
        V8.V7.V6._v5._v4.validate_current_source(r9_entries, "R9")
    else:
        r9 = None
        require(head == c9, "receipt-absent state is not exact C9")
    validate_forbidden_history(head, c9, r9)
    V8.V7.V6.validate_worktree(head_entries, head, head_tree)
    return {
        "c8_entries": c8_entries,
        "c9": c9,
        "c9_entries": c9_entries,
        "c9_tree": c9_tree,
        "head": head,
        "head_entries": head_entries,
        "head_tree": head_tree,
        "r9": r9,
        "schemas": schemas,
    }


def static_result(
    topology: dict[str, Any],
    schema: str = "pid-rs/ksg-rev4-m1a-composite-v9-static-validation/v1",
) -> dict[str, Any]:
    return {
        "c8_commit": C8_COMMIT,
        "c9_commit": topology["c9"],
        "head": topology["head"],
        "r9_commit": topology["r9"],
        "result": "pass",
        "schema": schema,
        "tree": topology["head_tree"],
    }


def validate_receipt_bytes(raw: bytes, topology: dict[str, Any]) -> dict[str, Any]:
    value = parse_json(raw, "composite-v9 receipt", canonical=False)
    require(
        raw == canonical_json(value, pretty=True),
        "composite-v9 receipt is not canonical pretty JSON",
    )
    validate_schema_instance(value, topology["schemas"][2], "composite-v9 receipt")
    require(topology["r9"] is not None, "receipt comparison requires R9")
    r9_entries = parse_tree(parse_commit(topology["r9"]).tree)
    expected = derive_receipt(
        tree_blob(topology["c9_entries"], PREDECESSOR_CAPTURE_RELATIVE),
        tree_blob(r9_entries, LOCAL_RECORD_RELATIVE),
        tree_blob(r9_entries, SUCCESSOR_CAPTURE_RELATIVE),
        topology["c8_entries"],
        topology["c9_entries"],
        topology["c9"],
        topology["c9_tree"],
        topology["schemas"],
    )
    require(
        value == expected, "composite-v9 receipt differs from exact evidence derivation"
    )
    return value


def validate_static() -> dict[str, Any]:
    topology = validate_topology()
    if topology["r9"] is not None:
        r9_entries = parse_tree(parse_commit(topology["r9"]).tree)
        validate_receipt_bytes(tree_blob(r9_entries, RECEIPT_RELATIVE), topology)
    return static_result(topology)


def bounded_regular_fd(
    fd: int, label: str, maximum: int
) -> tuple[bytes, tuple[int, int]]:
    require(type(fd) is int and fd >= 3, f"{label} descriptor is outside the bound")
    try:
        before = os.fstat(fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        offset = os.lseek(fd, 0, os.SEEK_CUR)
    except OSError as error:
        raise ContractError(f"cannot inspect {label} descriptor: {error}") from None
    require(
        stat.S_ISREG(before.st_mode)
        and flags & os.O_ACCMODE == os.O_RDONLY
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o600
        and 0 < before.st_size <= maximum
        and offset == 0,
        f"{label} is not one new mode-0600 bounded regular file at offset zero",
    )
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
        chunk = os.read(fd, min(remaining, 1024 * 1024))
        require(chunk != b"", f"{label} descriptor ended early")
        chunks.append(chunk)
        remaining -= len(chunk)
    require(os.read(fd, 1) == b"", f"{label} descriptor grew during read")
    after = os.fstat(fd)
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    require(
        tuple(getattr(before, field) for field in fields)
        == tuple(getattr(after, field) for field in fields),
        f"{label} descriptor changed during read",
    )
    return b"".join(chunks), (before.st_dev, before.st_ino)


def derive_receipt_command(local_fd: int, successor_fd: int) -> dict[str, Any]:
    require(
        local_fd != successor_fd, "L9 and successor descriptor numbers must be distinct"
    )
    topology = validate_topology()
    require(
        topology["r9"] is None and topology["head"] == topology["c9"],
        "receipt derivation requires exact receipt-absent C9",
    )
    local_raw, local_identity = bounded_regular_fd(
        local_fd, "L9 input", LOCAL_LIMITS["record_bytes"]
    )
    successor_raw, successor_identity = bounded_regular_fd(
        successor_fd, "successor capture input", V8.V7.V6.MAX_JSON_BYTES
    )
    require(
        local_identity != successor_identity,
        "L9 and successor inputs alias the same file",
    )
    value = derive_receipt(
        tree_blob(topology["c9_entries"], PREDECESSOR_CAPTURE_RELATIVE),
        local_raw,
        successor_raw,
        topology["c8_entries"],
        topology["c9_entries"],
        topology["c9"],
        topology["c9_tree"],
        topology["schemas"],
    )
    final = validate_topology()
    require(
        final["r9"] is None
        and (final["head"], final["head_tree"], final["c9"], final["c9_tree"])
        == (
            topology["head"],
            topology["head_tree"],
            topology["c9"],
            topology["c9_tree"],
        ),
        "repository changed during receipt derivation",
    )
    return value


def bounded_stdin() -> bytes:
    raw = sys.stdin.buffer.read(LOCAL_LIMITS["record_bytes"] + 1)
    require(
        0 < len(raw) <= LOCAL_LIMITS["record_bytes"],
        "receipt stdin size is outside the bound",
    )
    return raw


def validate_receipt_command() -> dict[str, Any]:
    topology = validate_topology()
    require(topology["r9"] is not None, "receipt validation requires exact R9")
    r9_entries = parse_tree(parse_commit(topology["r9"]).tree)
    raw = bounded_stdin()
    require(
        raw == tree_blob(r9_entries, RECEIPT_RELATIVE),
        "receipt stdin differs from exact R9 blob",
    )
    validate_receipt_bytes(raw, topology)
    return static_result(
        topology, "pid-rs/ksg-rev4-m1a-composite-v9-receipt-validation/v1"
    )


def worktree_changes() -> dict[str, str]:
    raw = V8.V7.git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    values: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if record == b"":
            continue
        require(
            len(record) >= 4 and record[2:3] == b" ", "unsupported draft status record"
        )
        status_text = record[:2].decode("ascii")
        require(
            status_text in {" M", "M ", "A ", "??"}, "draft contains unsupported status"
        )
        try:
            path = record[3:].decode("utf-8")
        except UnicodeDecodeError:
            raise ContractError("draft path is not UTF-8") from None
        require(path not in values, f"duplicate draft path: {path}")
        values[path] = status_text
    return values


def validate_draft() -> dict[str, Any]:
    _c7_entries, _c8_entries = validate_c8_anchor()
    head = V8.V7.git("rev-parse", "--verify", "HEAD").decode("ascii").strip()
    require(head == C8_COMMIT, "v9 draft is not based on exact published C8")
    changes = worktree_changes()
    allowed = {path for path, _status, _mode, _role in EXPECTED_C9_ROWS}
    require(set(changes) <= allowed, "draft contains a path outside exact C9 scope")
    required = {
        RETIRED_V8_WORKFLOW_RELATIVE,
        V9_WORKFLOW_RELATIVE,
        BOUNDARY_RELATIVE,
        POLICY_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        LOCAL_TOOL_RELATIVE,
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-certified-sxpid2-claim-self-test.py",
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
    }
    require(required <= set(changes), "v9 draft core path inventory is incomplete")
    frozen_required = frozen_c9_required_paths()
    require(
        set(FROZEN_C9_PATH_BINDINGS) == frozen_required,
        "v9 draft acyclic binding path set is not closed",
    )
    policy_modes = {
        path: mode for path, _status, mode, _role in EXPECTED_C9_ROWS
    }
    require(
        all(
            type(binding) is tuple
            and len(binding) == 3
            and type(binding[0]) is str
            and SHA256_RE.fullmatch(binding[0]) is not None
            and type(binding[1]) is int
            and binding[1] > 0
            and binding[2] == policy_modes[path]
            for path, binding in FROZEN_C9_PATH_BINDINGS.items()
        ),
        "v9 draft acyclic binding value shape changed",
    )
    policy_raw = read_file(POLICY_RELATIVE, mode=0o644)
    require(
        policy_raw
        == canonical_json(
            parse_json(policy_raw, "draft policy", canonical=False), pretty=True
        ),
        "draft policy is not canonical",
    )
    validate_policy_value(parse_json(policy_raw, "draft policy"))
    for path in (
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
    ):
        validate_schema_bytes(read_file(path, mode=0o644), path)
    ci_raw = read_file(CI_RELATIVE, mode=0o644)
    retired_raw = read_file(RETIRED_V8_WORKFLOW_RELATIVE, mode=0o644)
    v9_raw = read_file(V9_WORKFLOW_RELATIVE, mode=0o644)
    validate_raw_upload_occurrences(ci_raw, "draft CI workflow", 3)
    validate_raw_upload_occurrences(retired_raw, "draft retired-v8 workflow", 0)
    validate_raw_upload_occurrences(v9_raw, "draft v9 workflow", 1)
    validate_justfile_bytes(read_file(JUSTFILE_RELATIVE, mode=0o644))
    missing_exact_paths = sorted(allowed - set(changes))
    non_cut_binding_mismatches: list[str] = []
    for path, (digest, size, mode) in sorted(FROZEN_C9_PATH_BINDINGS.items()):
        if path not in changes:
            non_cut_binding_mismatches.append(path)
            continue
        raw = read_file(path)
        metadata = (ROOT / path).lstat()
        actual_mode = f"100{stat.S_IMODE(metadata.st_mode):03o}"
        if (sha256(raw), len(raw), actual_mode) != (digest, size, mode):
            non_cut_binding_mismatches.append(path)
    return {
        "c8_commit": C8_COMMIT,
        "closed_non_cut_binding_path_count": len(frozen_required),
        "draft_changed_paths": sorted(changes),
        "draft_scope": "source_shape_only_not_cut_or_qualification",
        "missing_exact_c9_paths": missing_exact_paths,
        "non_cut_binding_mismatches": non_cut_binding_mismatches,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v9-draft-validation/v1",
        "terminal_c8_ci_bound": C8_CI_CONCLUSION == "failure",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-draft", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument("--validate-static", action="store_true")
    modes.add_argument("--derive-receipt", action="store_true")
    modes.add_argument("--validate-receipt", action="store_true")
    parser.add_argument("--local-closure-fd", type=int)
    parser.add_argument("--successor-capture-fd", type=int)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.derive_receipt:
            require(
                arguments.local_closure_fd is not None
                and arguments.successor_capture_fd is not None,
                "receipt derivation requires both bounded evidence descriptors",
            )
        else:
            require(
                arguments.local_closure_fd is None
                and arguments.successor_capture_fd is None,
                "evidence descriptors are permitted only for receipt derivation",
            )
        if arguments.validate_draft:
            result = validate_draft()
        elif arguments.validate_static:
            result = validate_static()
        elif arguments.derive_receipt:
            result = derive_receipt_command(
                arguments.local_closure_fd, arguments.successor_capture_fd
            )
        else:
            result = validate_receipt_command()
        sys.stdout.buffer.write(
            canonical_json(result, pretty=bool(arguments.derive_receipt))
        )
        return 0
    except (ContractError, OSError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
