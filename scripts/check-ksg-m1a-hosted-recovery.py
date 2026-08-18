#!/usr/bin/env python3
"""Fail closed on the bounded KSG M1a hosted-recovery lifecycle.

The scientific implementation remains cb3f58f0.  The failed public custody
correction remains 7473e62a.  This checker accepts only one unsigned sole-child
recovery of that correction, preserves both predecessor histories, and grants
no local or scientific credit.
"""

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
        "ERROR: check-ksg-m1a-hosted-recovery.py requires Python 3.11+ "
        "-I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
import ast
from dataclasses import dataclass
import datetime
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
from typing import Any, Callable


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER_RELATIVE = "scripts/check-ksg-m1a-hosted-recovery.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-hosted-recovery-self-test.py"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json"
BOUNDARY_RELATIVE = "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md"
NEGATIVE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json"
)
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json"
R6_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json"
R7_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json"
R8_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-14-r8.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
LEAN_CHECKER = "scripts/check-lean-toolchain-freeze.py"
LEAN_SELF_TEST = "scripts/check-lean-toolchain-freeze-self-test.py"
CERT_CHECKER = "scripts/check-certified-sxpid2-claim.py"
CERT_SELF_TEST = "scripts/check-certified-sxpid2-claim-self-test.py"
ACTIVE_PACKET = "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
FINAL_MATRIX = "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md"
FINAL_DECISION = "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md"
FUTURE_RECEIPT = "audit/evidence/ksg-rev4-m1a-composite-receipt-v3-2026-08-13.json"
OLD_RETAINED_INDEX = "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin"
RECOVERY_RETAINED_INDEX = "audit/evidence/ksg-rev4-m1a-hosted-recovery-sealed-index.bin"

IMPLEMENTATION = "cb3f58f0b190454cb3f1090de8798261ec78f194"
IMPLEMENTATION_TREE = "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0"
IMPLEMENTATION_PARENT = "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9"
CORRECTION = "7473e62acef6077c2c1147e09d5d1297f2a2874b"
CORRECTION_TREE = "d0b2613e678a89318550c1797ba9cc59a4ec9478"
CORRECTION_ENTRY_COUNT = 724
CORRECTION_TREE_PROJECTION_SIZE_BYTES = 173_969
CORRECTION_TREE_PROJECTION_SHA256 = (
    "d6b6ea6f43bba0f240269fe16ba4a40ae87663f1185e6201c8a0d300b605f7fa"
)
PROTECTED_COUNT = 83
PROTECTED_SHA256 = "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843"
CORRECTION_INDEX_SHA256 = (
    "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc"
)
CORRECTION_INDEX_SIZE_BYTES = 87_963
CORRECTION_INDEX_BLOB = "79f0eaf13969008a8a31c2e47f3fbb06ba2055c6"
R6_SHA256 = "f14e7a33c01909055cc868fc955e6b2520ae15ebf0d598730911ec57a7f4c5ea"
R7_SHA256 = "3dd2df7d7064bac93cf4806cdeac28d9ecc747444689162a4636029228822abb"
RETIRED_RECOVERY_CHECKPOINT = "37473f8fa9470fcec0bd419ec3df18ea4a6d805b"
RETIRED_RECOVERY_TREE = "66f33f467f2bc661795599fa53ef81681ecd8406"
RETIRED_RECOVERY_INDEX_SHA256 = (
    "fb892aeaac2091e1d4c6b619a4ce0053771d8aeb0ee147105017613a3b46a56d"
)
RETIRED_RECOVERY_INDEX_SIZE_BYTES = 88_875
RETIRED_RECOVERY_ENTRY_COUNT = 731

POST_COMMIT_NONIMPLICATIONS = (
    "This post-commit identity artifact is not authentication, authenticity, "
    "attestation, provenance, or proof of repository origin.",
    "It does not establish line review, human review, independent review, "
    "institutional review, or review completion.",
    "It does not establish scientific validity, estimator validity, formal "
    "correctness, source-to-formal correspondence, implementation refinement, "
    "numerical correctness, or application validity.",
    "Commit, tree, blob, and SHA-256 identifiers bind exact bytes under named "
    "algorithms; they do not confer trust or authenticity.",
    "Generation is bounded execution evidence for one committed state, not a "
    "CI-pass, release, tag, or fact about any other commit.",
    "Repeated endpoint checks are not an atomic history against concurrent "
    "filesystem or repository mutation.",
    "Repository-ignored products and Git object-store internals are outside this "
    "committed-tree identity projection.",
    "Emission uses standard output and validation uses standard input; this artifact "
    "does not bind storage location, filesystem identity, durability, or upload custody.",
)

EXPECTED_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"
EXPECTED_TIMEZONE = "+0200"
CORRECTION_MESSAGE = (
    "Correct KSG M1a hosted custody wiring\n\n"
    f"Sealed-index-SHA256: {CORRECTION_INDEX_SHA256}\n"
    f"Sealed-index-Size: {CORRECTION_INDEX_SIZE_BYTES}\n"
)
RECOVERY_MESSAGE_TEMPLATE = (
    "Repair KSG M1a hosted recovery wiring\n\n"
    "Sealed-index-SHA256: <lowercase-sha256>\n"
    "Sealed-index-Size: <canonical-decimal-bytes>\n"
)

# Deterministic non-evidentiary identity used only by the isolated receipt
# self-test vector.  Production receipt validation derives the real identity
# from Git objects and retained index bytes and never consults these values.
SELF_TEST_VECTOR_RECOVERY_COMMIT = "3" * 40
SELF_TEST_VECTOR_RECOVERY_TREE = "4" * 40
SELF_TEST_VECTOR_RECOVERY_INDEX_SHA256 = (
    "458ec452a2b34fb5c5c66d4007a0368f208b1e63f679d022f36e1fc52c36e901"
)
SELF_TEST_VECTOR_RECOVERY_INDEX_BLOB = "c97e69f95b0b807a4322fb6fb7274a33ed5cfa20"
SELF_TEST_VECTOR_RECOVERY_INDEX_SIZE_BYTES = 90_000
SELF_TEST_VECTOR_RECOVERY_ENTRY_COUNT = 732

# FREEZE_PLACEHOLDER: every value below is replaced prospectively only after
# the named authored bytes have stopped moving.  A frozen policy rejects any
# surviving placeholder.
EXPECTED_FROZEN_POLICY_SHA256 = (
    "3bb78b296e9a1898ee72a2ae88988c1a73bbb81c3247054a500935f3690a4916"
)
EXPECTED_FROZEN_POLICY_SIZE_BYTES = 11_820
EXPECTED_FROZEN_BOUNDARY_SHA256 = (
    "3f0d5facb1c65b269c4e8633699773c2ef12d92ecdebfd9d85c9da7347f94ca4"
)
EXPECTED_FROZEN_BOUNDARY_SIZE_BYTES = 9_601
EXPECTED_FROZEN_SELF_TEST_SHA256 = (
    "0ebd801ce758203ce12111ccec8802bc9a6c68ad80033105abc59f6e60d05787"
)
EXPECTED_FROZEN_SELF_TEST_SIZE_BYTES = 142_954
EXPECTED_FROZEN_SCHEMA_SHA256 = (
    "345296eca6d944fbc40d1133b862a7ff047a6083123b023e1533a2f22cf4a2c5"
)
EXPECTED_FROZEN_SCHEMA_SIZE_BYTES = 114_567
EXPECTED_FROZEN_NEGATIVE_SHA256 = (
    "d9ec2ef753ee8f8f4f3d1d3bcc11aab791b4c127445088f250e7a53d71d896f5"
)
EXPECTED_FROZEN_NEGATIVE_SIZE_BYTES = 161_415
EXPECTED_FROZEN_CERT_CHECKER_SHA256 = (
    "c119b3d239627f4d052d9ecf6fc7c47536ba2cd31dba91e867ad9d7e485fee67"
)
EXPECTED_FROZEN_CERT_CHECKER_SIZE_BYTES = 82_193
EXPECTED_FROZEN_CERT_SELF_TEST_SHA256 = (
    "ae2289b6e3ac461d6f0161009e13384e903d527ea52026b15d9d2ea8c32d435c"
)
EXPECTED_FROZEN_CERT_SELF_TEST_SIZE_BYTES = 114_214
EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256 = (
    "d66cca263179116cbccae0eb5c48641d0554b5733b8bff5f6713c0565ff86a65"
)
EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES = 99_100
EXPECTED_FROZEN_LEAN_SELF_TEST_SHA256 = (
    "89fd8d07ee437b8639074266ed4613b695309126df30d54461a6ce7c221b914c"
)
EXPECTED_FROZEN_LEAN_SELF_TEST_SIZE_BYTES = 111_382
EXPECTED_FROZEN_LEAN_GENERATOR_SHA256 = (
    "4ab8d4305174302fa01afc8851acb4ca2bf718f6329a1bfd217d9ff0a9709f2c"
)
EXPECTED_FROZEN_LEAN_GENERATOR_SIZE_BYTES = 52_054
EXPECTED_POLICY_SEMANTIC_PROJECTION_SHA256 = (
    "ebdda2dbb0efde9bc461ac6c7bccc88c76f035c52a53195b987215cfdbb703b2"
)
EXPECTED_FROZEN_WORKFLOW_SHA256 = (
    "61283264499a7b6069a4e5e9563c72541ab101b69379f3ace75a12cd4bf4b175"
)
EXPECTED_FROZEN_WORKFLOW_SIZE_BYTES = 68_913
EXPECTED_FROZEN_JUST_SHA256 = (
    "8cb030aaa01b1230c7d490c1bc399be8875c7285f4c39d6ca46eff624bfd4591"
)
EXPECTED_FROZEN_JUST_SIZE_BYTES = 24_451
EXPECTED_FROZEN_SCRIPTS_README_SHA256 = (
    "32d63a3e34e1263d1fd6e49fedff9a35d6717df34dc2edf7aca062db41963f2a"
)
EXPECTED_FROZEN_SCRIPTS_README_SIZE_BYTES = 128_696

# FREEZE_PLACEHOLDER: exact raw child stdout is captured only after all four
# prospective children are final.  These are one-way pins; phase receipts may
# copy them but may not define or reseal them.
EXPECTED_CHILD_STDOUT: dict[str, tuple[int, str]] = {
    CERT_CHECKER: (
        93,
        "09dacad5bd95e7f0fbab262c8f15997fe7bee00c4fe14f32c7dd975a700bcea5",
    ),
    CERT_SELF_TEST: (
        58,
        "46fdca8535622ac6a78e6c86c3293da3be6a60dac7dadb73f7dc9e60252889bf",
    ),
    LEAN_CHECKER: (
        326,
        "0b285433f78d7996c1e214cb5cfccf8177b91f98f7439ad508532dece4cd6f51",
    ),
    LEAN_SELF_TEST: (
        162,
        "f2b2279a1b8f8ea114b31be743195c4b9867af99432c6e03cda70a2b159ab85d",
    ),
}

HISTORICAL_CORRECTION_ARTIFACTS = {
    "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md": (
        8_814,
        "591bccc8e770b9b51ab34ce8cce9d2ac54973c50185141e1a598fd90260dcc16",
    ),
    "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json": (
        11_910,
        "8797335e0f23240f6f018c4403caff1a6c209f9c110ffeaa91fb47503bf331ed",
    ),
    "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json": (
        484_959,
        "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5",
    ),
    R6_RELATIVE: (126_143, R6_SHA256),
    CURRENT_SOURCE_RELATIVE: (
        174_120,
        "c66c51282faabd6746838714e07862e722f3da6a2ca77d78cd093167d5f50c24",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json": (
        57_331,
        "797e7c5a0dc7122aff6c16319749c3a18683ebbe21e94dd039cdc5b7a330d42c",
    ),
    "scripts/check-ksg-m1a-custody-correction.py": (
        244_228,
        "e504fb1617fc93abd096ced451d82c74745011edb4a3b4673bd2dd8c4cea3147",
    ),
    "scripts/check-ksg-m1a-custody-correction-self-test.py": (
        119_142,
        "a466461b9eecd4afd3f839aa8137a6fc6b4de13e1aa6e18dc81b0862c6f0fdcb",
    ),
}

PROTECTED_EXTRA_PATHS = frozenset(
    {
        ACTIVE_PACKET,
        "crates/pid-core/src/kdtree.rs",
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/src/nn.rs",
        "scripts/check-ksg-harmonic-revision.py",
        "scripts/check-ksg-harmonic-revision-self-test.py",
        "scripts/check-ksg-m1a-phase.py",
        "scripts/check-ksg-m1a-phase-self-test.py",
        "audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md",
        "audit/evidence/ksg-rev4-m1a-path-policy-v1.json",
        "audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json",
    }
)

REQUIRED_POLICY_ROWS = {
    ".github/workflows/ci.yml": ("M", "hosted_recovery_wiring"),
    "AGENTS.md": ("M", "lean_r8_pointer_consequence"),
    "CHANGELOG.md": ("M", "mandatory_release_record"),
    "audit/evidence/completion-active-resume.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    CURRENT_SOURCE_RELATIVE: ("M", "self_excluding_source_state"),
    NEGATIVE_RELATIVE: ("A", "retained_failed_correction_hosted_negative"),
    BOUNDARY_RELATIVE: ("A", "hosted_recovery_authority"),
    POLICY_RELATIVE: ("A", "hosted_recovery_authority"),
    R7_RELATIVE: ("A", "lean_r7_preserved_execution_custody"),
    R8_RELATIVE: ("A", "lean_r8_execution_custody"),
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md": (
        "M",
        "durable_program_coordination",
    ),
    "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    SCHEMA_RELATIVE: ("A", "hosted_recovery_authority"),
    "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md": (
        "M",
        "lean_r8_pointer_consequence",
    ),
    "justfile": ("M", "hosted_recovery_wiring"),
    "scripts/README.md": ("M", "hosted_recovery_docs_and_lean_r8_pointer"),
    CERT_SELF_TEST: ("M", "certified_container_rebind"),
    CERT_CHECKER: ("M", "certified_container_rebind"),
    SELF_TEST_RELATIVE: ("A", "hosted_recovery_verifier"),
    CHECKER_RELATIVE: ("A", "hosted_recovery_verifier"),
    LEAN_SELF_TEST: ("M", "lean_r8_custody"),
    LEAN_CHECKER: ("M", "lean_r8_custody"),
    "scripts/generate-lean-4.33-replay.py": ("M", "lean_r8_custody"),
}

EXPECTED_REVIEW_CLASSES = {
    "certified_container_rebind",
    "durable_program_coordination",
    "hosted_recovery_authority",
    "hosted_recovery_docs_and_lean_r8_pointer",
    "hosted_recovery_verifier",
    "hosted_recovery_wiring",
    "lean_r7_preserved_execution_custody",
    "lean_r8_custody",
    "lean_r8_execution_custody",
    "lean_r8_pointer_consequence",
    "mandatory_release_record",
    "retained_failed_correction_hosted_negative",
    "self_excluding_source_state",
}

RECEIPT_ROOT_KEYS = {
    "claim",
    "correction_local_phase_custody",
    "custody_correction",
    "evidence_class",
    "hosted_observations",
    "hosted_recovery",
    "implementation_anchor",
    "milestone",
    "negative_evidence_semantics",
    "nonimplications",
    "recovery_local_phase_custody",
    "remote_observations",
    "repository",
    "revision4_integration",
    "schema",
    "schema_revision",
}
PHASE_CUSTODY_KEYS = {
    "alternate_index",
    "boundary",
    "checker",
    "policy",
    "postcommit_outputs",
    "precommit_outputs",
    "self_test",
}
RECOVERY_PHASE_KEYS = {
    "candidate",
    "certified_sxpid_recovery",
    "child_output_sha256",
    "credit",
    "current_source_manifest_sha256",
    "disposition",
    "failed_correction_anchor",
    "implementation_anchor",
    "lean_r8",
    "lifecycle",
    "mode",
    "negative_evidence",
    "policy_sha256",
    "preclosure",
    "repository_state",
    "runtime_mode",
    "schema",
    "static_artifact_sha256",
}
CORRECTION_PHASE_KEYS = {
    "candidate",
    "certified_sxpid_correction",
    "child_output_sha256",
    "credit",
    "current_source_manifest_sha256",
    "disposition",
    "implementation_anchor",
    "lean_r6",
    "lifecycle",
    "mode",
    "negative_evidence",
    "policy_sha256",
    "preclosure",
    "repository_state",
    "runtime_mode",
    "schema",
    "static_artifact_sha256",
}

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTITY = re.compile(
    rb"(?P<name>[^\n<>]+) <(?P<email>[^\n<>\s]+)> "
    rb"(?P<epoch>[1-9][0-9]*) (?P<timezone>[+-][0-9]{4})"
)
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_GIT_BYTES = 96 * 1024 * 1024
MAX_INDEX_BYTES = 64 * 1024 * 1024
MAX_INTERPRETER_BYTES = 128 * 1024 * 1024
SELF_TEST_SCHEMA = "pid-rs/ksg-rev4-m1a-hosted-recovery-self-test-vector/v1"
RECEIPT_SCHEMA = "pid-rs/ksg-rev4-m1a-composite-receipt/v3"
NEGATIVE_EVIDENCE_SEMANTICS = (
    "CI run 31686107959 attempt 1 on cb3f58f0b190454cb3f1090de8798261ec78f194 is terminal failed zero-credit evidence and remains failed after every later correction or recovery observation.",
    "CodeQL run 31686106737 attempt 1 succeeded on cb3f58f0b190454cb3f1090de8798261ec78f194, but that success neither changes the separate failed CI run nor establishes all-green status for the implementation head.",
    "CI run 31724449805 attempt 1 on 7473e62acef6077c2c1147e09d5d1297f2a2874b is terminal failed zero-credit evidence and remains failed after every later recovery observation.",
    "CodeQL run 31724449083 attempt 1 succeeded on 7473e62acef6077c2c1147e09d5d1297f2a2874b, but that success neither changes the separate failed CI run nor establishes all-green status for the correction head.",
    "All-green hosted status applies only to separately observed successful CI and CodeQL attempt-1 runs whose head SHA and tree both equal the distinct recovery subject.",
    "A later hosted success cannot erase, relabel, retry, supersede, or transfer success credit to either earlier failed CI observation.",
    "The implementation, correction, and recovery heads are distinct lifecycle subjects; no run, job, analysis, alert, artifact, or conclusion transfers across them.",
    "Provider identifiers, captures, logs, timestamps, digests, artifacts, and alert rosters are unauthenticated observations, not trusted time, authorship, transparency, provenance, or causation.",
)
COMPOSITE_NONIMPLICATIONS = (
    "This composite receipt is bounded lifecycle custody for an exact M1a implementation, its failed direct-child custody correction, and one fast-forward hosted recovery; it is not scientific, formal, estimator, PID, calibration, support, application, package, release, or identity evidence.",
    "The two failed CI runs remain failed zero-credit observations; later recovery success cannot erase, relabel, retry, or transfer success to either failed head.",
    "Same-head CodeQL success does not make a separate CI run green, and no result transfers across distinct heads.",
    "Provider identifiers, logs, timestamps, digests, artifacts, and alert rosters are unauthenticated observations, not trusted time, authorship, transparency, provenance, or causation.",
    "The unchanged 83-path projection proves only byte equality for its named paths, not scientific correctness or origin.",
    "The r8 replay is current execution custody only for its named Lean project; r6 and r7 are byte-preserved prior evidence, not current runner custody, and none transfers any theorem to Rust, binary64, KSG M1c, or any PID construction.",
    "The receipt and both retained indexes are absent from all three subject trees; the receipt does not hash or attest its own bytes or containing descendant commit.",
    "Revision 4 remains integration_no_go with thirteen open gates and no final evidence matrix or decision.",
)
CORRECTION_NEGATIVE_SEMANTICS = (
    "CI run 31724449805 attempt 1 on 7473e62a is terminal failed zero-credit evidence and remains failed after any later recovery success.",
    "The CI run has two distinct failed jobs; neither failure may be omitted, merged, relabeled, or transferred to the other diagnostic.",
    "CodeQL run 31724449083 attempt 1 succeeded on 7473e62a, but that success neither makes the separate CI run green nor establishes all-green hosted status for the correction head.",
    "The exact fixed-authority SelfTestError, the exact certified-protocol accepted-vector failure, and repository/workflow bytes are separately observed facts; this record does not authenticate the provider or claim causation.",
    "The second terminal log does not expose an internal exception class; no reviewer-derived local reproduction or inferred cause is promoted into this provider-observation record.",
    "All-green hosted status may describe only separately observed successful CI and CodeQL runs on the exact distinct recovery head.",
)
CORRECTION_NEGATIVE_NONIMPLICATIONS = (
    "This retained record is unauthenticated provider observation of one failed CI run and one successful CodeQL run on 7473e62a; it grants no lifecycle or scientific credit.",
    "The two failed diagnostics record an exact fixed-authority read failure and an exact accepted-vector protocol failure; they do not authenticate the provider response or establish broader causation.",
    "No unexposed inner exception class, Python-minor-version mechanism, AST-digest mechanism, or remediation sufficiency follows from the second outer diagnostic.",
    "CodeQL success does not make CI green, establish all-green hosted status, or transfer success to a later recovery head.",
    "Run, job, analysis, alert, artifact, commit, tree, blob, and SHA-256 identifiers do not establish authorship, trusted time, transparency-log inclusion, or repository provenance.",
)
CURRENT_CAPTURE_FORMAT = "canonical-compact-sorted-key-ascii-json-plus-lf/v1"
EXPECTED_CORRECTION_CAPTURE_BINDINGS = {
    "ci_artifact_inventory": (
        646,
        "93d10101fe1dbe0ac6fc2e36d5a74331070de3411fb3338b2575db5a720fcf41",
    ),
    "ci_job_step_roster": (
        78_769,
        "a7638cdefea287f9f8fc15de465cf7de501e74809f884006ec0651e7ff91e6bf",
    ),
    "ci_run_summary": (
        473,
        "782c8fdcb081558f485d00ac1caacc0e5639b9961ceceae2357d4614b1aad853",
    ),
    "codeql_alert_state": (
        2_247,
        "51ab4929b4e5162befb56f3ac66e3b9d4b247a8060aa609748f5098263ef58bf",
    ),
    "codeql_job_analysis_roster": (
        5_557,
        "719e122875495887c7db5cebcd9c281cf132092591f79db484e15ff5e0c83933",
    ),
    "codeql_run_summary": (
        428,
        "1e540c29b8e765bed32f0df27e8265b317e53fa1c99508f2e914131cd4d81ced",
    ),
}
FIXED_GIT_CONFIG = (
    "core.attributesFile=/dev/null",
    "core.fsmonitor=false",
    "core.hooksPath=/dev/null",
    "core.ignoreCase=false",
    "core.untrackedCache=false",
    "diff.external=",
)


class RecoveryError(RuntimeError):
    """A fail-closed recovery predicate did not hold."""


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
        raise RecoveryError(message)


def canonical_json(value: Any, *, pretty: bool) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise RecoveryError("value is not canonical JSON data") from error
    return (rendered + "\n").encode("ascii")


def duplicate_rejector(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> Any:
    raise RecoveryError(f"non-finite JSON constant: {value}")


def parse_json(raw: bytes, label: str, *, canonical: bool = True) -> Any:
    require(len(raw) <= MAX_JSON_BYTES, f"{label} exceeds JSON bound")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=duplicate_rejector,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        raise RecoveryError(f"{label} is not strict JSON") from error
    reject_float_and_bool_alias(value, label)
    require_scalar_field_types(value, label)
    if canonical:
        require(raw == canonical_json(value, pretty=True), f"{label} not canonical")
    return value


def reject_float_and_bool_alias(value: Any, label: str) -> None:
    if isinstance(value, float):
        raise RecoveryError(f"{label} contains a float")
    if isinstance(value, list):
        for item in value:
            reject_float_and_bool_alias(item, label)
    elif isinstance(value, dict):
        for item in value.values():
            reject_float_and_bool_alias(item, label)


INTEGER_JSON_FIELDS = {
    "alert_number",
    "analysis_id",
    "archive_size_bytes",
    "artifact_id",
    "attempt",
    "ci_attempt",
    "ci_run_id",
    "codeql_run_id",
    "codeql_attempt",
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
INTEGER_JSON_LIST_FIELDS = {
    "baseline_alert_numbers",
    "dismissed_alert_numbers",
    "fixed_alert_numbers",
    "new_alert_numbers",
    "observed_alert_numbers",
    "open_alert_numbers",
}
BOOLEAN_JSON_FIELDS = {
    "author_and_committer_headers_identical",
    "credit_permitted",
    "deletions_permitted",
    "decision_v4_absent_at_recovery",
    "evidence_matrix_v4_absent_at_recovery",
    "all_green_applies_only_to_recovery_head",
    "all_jobs_successful",
    "authentication_claimed",
    "candidate_equals_anchor",
    "causation_claimed",
    "commit_message_trailer_matches",
    "correction_heads_equal",
    "distinct_from_correction",
    "distinct_from_implementation_anchor",
    "expired",
    "failed_correction_ci_must_remain_failed",
    "failed_correction_codeql_must_remain_separate",
    "final_decision_absent",
    "final_evidence_matrix_absent",
    "future_composite_receipt_absent",
    "future_retained_indexes_absent",
    "implementation_heads_equal",
    "current_manifest_checker_passed",
    "head_tree_matches_index",
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
    "precommit_descriptor_observation_authenticated",
    "post_commit_checker_is_tracked_head_blob",
    "post_commit_schema_is_tracked_head_blob",
    "reconstructs_tree_twice",
    "recovery_heads_equal",
    "recovery_subject_must_not_contain_receipt",
    "recovery_subject_must_not_contain_retained_indexes",
    "remains_implementation_after_recovery",
    "repetitions_equal",
    "repeated_endpoint_observations_match",
    "retained_negative_evidence",
    "runner_authenticity_claimed",
    "scientific_authority_unchanged",
    "single_link",
    "self_excluding_projection_matches_head_tree",
    "signature_headers_permitted",
    "three_subject_heads_distinct",
    "trusted_time_claimed",
    "truncated",
    "tracked_worktree_matches_head",
    "unsigned",
    "workflow_fetch_depth_zero",
}


def require_scalar_field_types(value: Any, label: str) -> None:
    pending: list[tuple[Any, str | None, str]] = [(value, None, label)]
    while pending:
        item, field, path = pending.pop()
        if field in INTEGER_JSON_FIELDS:
            require(type(item) is int, f"{path} is not an exact JSON integer")
        if field in INTEGER_JSON_LIST_FIELDS:
            require(
                type(item) is list and all(type(child) is int for child in item),
                f"{path} is not a flat exact JSON integer list",
            )
        if field in BOOLEAN_JSON_FIELDS:
            require(type(item) is bool, f"{path} is not an exact JSON boolean")
        if isinstance(item, dict):
            pending.extend((child, key, f"{path}.{key}") for key, child in item.items())
        elif isinstance(item, list):
            pending.extend(
                (child, None, f"{path}[{index}]") for index, child in enumerate(item)
            )


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == keys, f"{label} key set changed")
    return value


def exact_int(value: Any, label: str, minimum: int = 0) -> int:
    require(
        type(value) is int and value >= minimum, f"{label} is not a bounded integer"
    )
    return value


def exact_bool(value: Any, label: str) -> bool:
    require(type(value) is bool, f"{label} is not a boolean")
    return value


def validate_phase_jobs_count(value: Any, label: str) -> int:
    return exact_int(value, label, 1)


def validate_api_jobs_container(value: Any, label: str) -> list[dict[str, Any]]:
    require(
        type(value) is list and all(isinstance(row, dict) for row in value),
        f"{label} is not an API job-object list",
    )
    return value


def validate_named_api_jobs_projection(value: Any, label: str) -> None:
    require(type(value) is list, f"{label} capture inventory is not a list")
    matches = [
        row
        for row in value
        if isinstance(row, dict)
        and row.get("endpoint_class") == "codeql_job_analysis_roster"
    ]
    require(len(matches) == 1, f"{label} jobs capture is not unique")
    projection = exact_keys(
        matches[0].get("projection"), {"analyses", "jobs"}, f"{label} projection"
    )
    validate_api_jobs_container(projection["jobs"], f"{label} projection jobs")


def require_named_field_paths(
    value: Any,
    field: str,
    expected: set[tuple[str | int, ...]],
    label: str,
) -> None:
    observed: set[tuple[str | int, ...]] = set()
    pending: list[tuple[Any, tuple[str | int, ...]]] = [(value, ())]
    while pending:
        item, path = pending.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = (*path, key)
                if key == field:
                    observed.add(child_path)
                pending.append((child, child_path))
        elif isinstance(item, list):
            pending.extend((child, (*path, index)) for index, child in enumerate(item))
    require(observed == expected, f"{label} {field} path inventory changed")


LEAN_V2_PACKAGE_NAMES = {
    "Cli",
    "LeanSearchClient",
    "Qq",
    "aesop",
    "batteries",
    "importGraph",
    "mathlib",
    "plausible",
    "proofwidgets",
}
LEAN_V2_ROOT_KEYS = {
    "active_claim_authority_sha256",
    "active_configuration",
    "active_resume_sha256",
    "checker_sha256",
    "command_records",
    "compatibility_scope",
    "current_evidence_sha256",
    "custody_gate_sha256",
    "dependency_checkout_preflight",
    "derived_instance_evidence_sha256",
    "environment_policy",
    "execution_environment",
    "execution_window",
    "historical_preservation_sha256",
    "lake_identity",
    "lake_version_line",
    "lake_version_stderr",
    "lean_identity",
    "lean_version_line",
    "lean_version_stderr",
    "official_archive",
    "official_archive_observation",
    "operational_wiring_sha256",
    "package_pins",
    "prior_replay_preservation_sha256",
    "prior_replay_schema",
    "provider_observations",
    "python_optimization_parity",
    "replay_custody_gate_sha256",
    "schema",
    "scope_boundary",
    "source_sha256",
    "status",
    "verification",
}
CURRENT_SOURCE_ROOT_KEYS = {
    "binding",
    "critical_artifacts",
    "generated_by",
    "generated_pdfs",
    "historical_release",
    "nonimplications",
    "repository",
    "review_inventory",
    "schema",
    "schema_revision",
    "source_projection",
    "subprojections",
}
HOSTED_NEGATIVE_ROOT_KEYS = {
    "capture_boundary",
    "ci_failure",
    "codeql_success",
    "negative_semantics",
    "nonimplications",
    "repository",
    "schema",
    "schema_revision",
    "subject",
}


def validate_lean_v2_scalar_contract(value: Any, label: str) -> None:
    root = exact_keys(value, LEAN_V2_ROOT_KEYS, label)
    require_named_field_paths(
        root,
        "revision",
        {("package_pins", name, "revision") for name in LEAN_V2_PACKAGE_NAMES},
        label,
    )
    require_named_field_paths(root, "schema_revision", set(), label)
    require(
        root["schema"] == "pid-rs/lean-current-project-replay/v2",
        f"{label} schema changed",
    )
    packages = exact_keys(
        root["package_pins"], LEAN_V2_PACKAGE_NAMES, f"{label} package pins"
    )
    for name, raw in packages.items():
        package = exact_keys(
            raw,
            {"inherited", "input_revision", "revision", "url"},
            f"{label} package {name}",
        )
        exact_bool(package["inherited"], f"{label} package {name} inherited")
        require(
            isinstance(package["input_revision"], str)
            and bool(package["input_revision"])
            and isinstance(package["url"], str)
            and bool(package["url"]),
            f"{label} package {name} text identity changed",
        )
        sha1(package["revision"], f"{label} package {name} revision")


def validate_active_packet_revision_contract(value: Any, label: str) -> None:
    root = exact_keys(
        value,
        {
            "active_revision",
            "claim_id",
            "facts",
            "historical_hashes",
            "open_integration_gates",
            "packet_files",
            "packet_stage",
            "revision_history",
            "schema",
            "schema_revision",
            "status",
        },
        label,
    )
    require_named_field_paths(
        root,
        "revision",
        {("revision_history", index, "revision") for index in range(4)},
        label,
    )
    require_named_field_paths(root, "schema_revision", {("schema_revision",)}, label)
    exact_int(root["schema_revision"], f"{label} schema revision", 1)
    require(root["schema_revision"] == 1, f"{label} schema revision changed")
    exact_int(root["active_revision"], f"{label} active revision", 1)
    require(root["active_revision"] == 4, f"{label} active revision changed")
    history = root["revision_history"]
    require(
        isinstance(history, list) and len(history) == 4,
        f"{label} revision history changed",
    )
    for index, raw in enumerate(history, start=1):
        row = exact_keys(
            raw, {"active", "revision", "status"}, f"{label} revision {index}"
        )
        exact_bool(row["active"], f"{label} revision {index} active")
        exact_int(row["revision"], f"{label} revision {index} number", 1)
        require(
            row["revision"] == index,
            f"{label} revision {index} number changed",
        )
        require(
            row["active"] is (index == root["active_revision"]),
            f"{label} revision {index} active marker changed",
        )


def validate_current_source_revision_contract(value: Any, label: str) -> None:
    root = exact_keys(value, CURRENT_SOURCE_ROOT_KEYS, label)
    require_named_field_paths(root, "revision", set(), label)
    require_named_field_paths(root, "schema_revision", {("schema_revision",)}, label)
    exact_int(root["schema_revision"], f"{label} schema revision", 1)
    require(root["schema_revision"] == 1, f"{label} schema revision changed")


def validate_implementation_negative_revision_contract(value: Any, label: str) -> None:
    root = exact_keys(value, HOSTED_NEGATIVE_ROOT_KEYS, label)
    require_named_field_paths(root, "revision", set(), label)
    require_named_field_paths(root, "schema_revision", {("schema_revision",)}, label)
    exact_int(root["schema_revision"], f"{label} schema revision", 1)
    require(root["schema_revision"] == 1, f"{label} schema revision changed")
    codeql = root["codeql_success"]
    boundary = root["capture_boundary"]
    require(
        isinstance(codeql, dict) and isinstance(boundary, dict),
        f"{label} hosted capture objects changed",
    )
    validate_named_api_jobs_projection(
        codeql.get("api_captures"), f"{label} CodeQL API"
    )
    validate_named_api_jobs_projection(
        boundary.get("api_responses"), f"{label} capture-boundary API"
    )


def sha1(value: Any, label: str) -> str:
    require(
        isinstance(value, str) and HEX40.fullmatch(value) is not None,
        f"{label} malformed",
    )
    return value


def sha256(value: Any, label: str) -> str:
    require(
        isinstance(value, str) and HEX64.fullmatch(value) is not None,
        f"{label} malformed",
    )
    return value


def validate_path(value: str) -> None:
    require(isinstance(value, str) and value and "\0" not in value, "path malformed")
    pure = PurePosixPath(value)
    require(
        not pure.is_absolute()
        and value == pure.as_posix()
        and all(part not in {"", ".", ".."} for part in pure.parts),
        f"unsafe repository path: {value!r}",
    )


def stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def validate_regular_snapshot(
    before: tuple[int, ...],
    path_before: tuple[int, ...],
    after: tuple[int, ...],
    path_after: tuple[int, ...],
    *,
    allow_empty: bool,
    maximum: int,
    required_mode: int | None,
    label: str,
) -> None:
    require(
        len(before) == len(path_before) == len(after) == len(path_after) == 7
        and all(
            type(item) is int
            for snapshot in (before, path_before, after, path_after)
            for item in snapshot
        ),
        f"malformed file snapshot: {label}",
    )
    mode, nlink, size = before[2], before[3], before[4]
    require(
        stat.S_ISREG(mode)
        and nlink == 1
        and (allow_empty or size > 0)
        and 0 <= size <= maximum
        and (required_mode is None or stat.S_IMODE(mode) == required_mode)
        and before == path_before == after == path_after,
        f"unsafe or unstable file: {label}",
    )


def read_regular(
    relative: str,
    *,
    maximum: int = MAX_FILE_BYTES,
    allow_empty: bool = False,
    required_mode: int | None = None,
) -> bytes:
    validate_path(relative)
    path = ROOT / relative
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        path_before = path.lstat()
        before_identity = stat_identity(before)
        path_before_identity = stat_identity(path_before)
        validate_regular_snapshot(
            before_identity,
            path_before_identity,
            before_identity,
            path_before_identity,
            allow_empty=allow_empty,
            maximum=maximum,
            required_mode=required_mode,
            label=relative,
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(bool(chunk), f"short read: {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"file grew: {relative}")
        after = os.fstat(descriptor)
        path_after = path.lstat()
    finally:
        os.close(descriptor)
    validate_regular_snapshot(
        before_identity,
        path_before_identity,
        stat_identity(after),
        stat_identity(path_after),
        allow_empty=allow_empty,
        maximum=maximum,
        required_mode=required_mode,
        label=relative,
    )
    return b"".join(chunks)


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


def git(
    *arguments: str,
    check: bool = True,
    extra_environment: dict[str, str] | None = None,
) -> bytes | tuple[int, bytes]:
    executable = Path("/usr/bin/git")
    executable_before = executable.lstat()
    require(
        stat.S_ISREG(executable_before.st_mode)
        and executable.resolve(strict=True) == executable,
        "fixed Git executable is not a canonical regular file",
    )
    command = [os.fspath(executable), "--no-optional-locks"]
    for item in FIXED_GIT_CONFIG:
        command.extend(("-c", item))
    command.extend(arguments)
    environment = safe_environment()
    if extra_environment:
        require(
            set(extra_environment) <= {"GIT_INDEX_FILE"},
            "unapproved Git environment override",
        )
        environment.update(extra_environment)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    require(
        len(completed.stdout) <= MAX_GIT_BYTES
        and len(completed.stderr) <= 4 * 1024 * 1024,
        "Git output exceeded bound",
    )
    executable_after = executable.lstat()
    require(
        (
            executable_before.st_dev,
            executable_before.st_ino,
            executable_before.st_mode,
            executable_before.st_size,
            executable_before.st_mtime_ns,
        )
        == (
            executable_after.st_dev,
            executable_after.st_ino,
            executable_after.st_mode,
            executable_after.st_size,
            executable_after.st_mtime_ns,
        ),
        "fixed Git executable changed during invocation",
    )
    if not check:
        return completed.returncode, completed.stdout
    require(
        completed.returncode == 0,
        "Git command failed: "
        + " ".join(arguments)
        + ": "
        + completed.stderr.decode("utf-8", errors="replace").strip(),
    )
    require(not completed.stderr, "Git emitted unexpected stderr")
    return completed.stdout


def git_text(*arguments: str, extra_environment: dict[str, str] | None = None) -> str:
    raw = git(*arguments, extra_environment=extra_environment)
    require(isinstance(raw, bytes), "internal Git result type changed")
    return raw.decode("utf-8", errors="strict").rstrip("\n")


def object_digest(kind: str, raw: bytes) -> str:
    return hashlib.sha1(  # noqa: S324 -- repository object format is SHA-1.
        f"{kind} {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def exact_object(oid: str, kind: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    sha1(oid, f"{kind} object id")
    actual_type = git_text("cat-file", "-t", oid)
    require(actual_type == kind, f"object {oid} is not {kind}")
    raw = git("cat-file", kind, oid)
    require(
        isinstance(raw, bytes) and len(raw) <= maximum, f"{kind} object exceeds bound"
    )
    require(object_digest(kind, raw) == oid, f"{kind} object bytes disagree with id")
    return raw


def parse_raw_tree(raw: bytes, label: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    offset = 0
    prior: bytes | None = None
    while offset < len(raw):
        space = raw.find(b" ", offset)
        nul = raw.find(b"\0", space + 1)
        require(
            space > offset and nul > space and nul + 21 <= len(raw),
            f"{label} malformed",
        )
        mode_raw = raw[offset:space]
        name_raw = raw[space + 1 : nul]
        oid = raw[nul + 1 : nul + 21].hex()
        require(
            mode_raw in {b"40000", b"100644", b"100755"}, f"{label} mode unsupported"
        )
        require(
            name_raw not in {b"", b".", b".."}
            and b"/" not in name_raw
            and b"\0" not in name_raw,
            f"{label} name unsafe",
        )
        name_raw.decode("utf-8", errors="strict")
        sort_key = name_raw + (b"/" if mode_raw == b"40000" else b"")
        require(prior is None or prior < sort_key, f"{label} entries not canonical")
        prior = sort_key
        rows.append((mode_raw.decode("ascii"), name_raw.decode("utf-8"), oid))
        offset = nul + 21
    require(offset == len(raw), f"{label} trailing bytes")
    return rows


def walk_raw_tree_objects(
    root: str, load_tree: Callable[[str], bytes]
) -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    seen_trees: set[str] = set()

    def walk(tree_oid: str, prefix: str) -> int:
        sha1(tree_oid, "tree object id")
        require(tree_oid not in seen_trees, "tree object is recursively repeated")
        seen_trees.add(tree_oid)
        raw = load_tree(tree_oid)
        require(
            isinstance(raw, bytes) and len(raw) <= MAX_GIT_BYTES,
            "tree loader result invalid",
        )
        leaf_count = 0
        for mode, name, oid in parse_raw_tree(raw, f"tree {tree_oid}"):
            path = f"{prefix}/{name}" if prefix else name
            validate_path(path)
            if mode == "40000":
                nested_count = walk(oid, path)
                require(nested_count > 0, f"empty nested tree is forbidden: {path}")
                leaf_count += nested_count
            else:
                require(path not in entries, "duplicate tree path")
                entries[path] = Entry(mode, oid)
                leaf_count += 1
        return leaf_count

    require(walk(root, "") > 0, "root tree is empty")
    return dict(sorted(entries.items()))


def parse_tree(root: str) -> dict[str, Entry]:
    ordered = walk_raw_tree_objects(
        root, lambda oid: exact_object(oid, "tree", maximum=MAX_GIT_BYTES)
    )
    for entry in ordered.values():
        exact_object(entry.oid, "blob")
    raw_listing = git("ls-tree", "-rz", "-r", "--full-tree", root)
    require(isinstance(raw_listing, bytes), "tree listing result type changed")
    require(
        not raw_listing or raw_listing.endswith(b"\0"),
        "tree listing lacks NUL termination",
    )
    listed: dict[str, Entry] = {}
    for record in raw_listing[:-1].split(b"\0") if raw_listing else []:
        prefix, separator, path_raw = record.partition(b"\t")
        fields = prefix.split(b" ")
        require(
            separator == b"\t" and len(fields) == 3 and fields[1] == b"blob",
            "recursive Git tree listing is malformed/non-blob",
        )
        path = path_raw.decode("utf-8", errors="strict")
        validate_path(path)
        require(path not in listed, "recursive Git tree listing has duplicate path")
        listed[path] = Entry(fields[0].decode("ascii"), fields[2].decode("ascii"))
    require(
        list(listed) == sorted(listed) and listed == ordered,
        "recursive raw-tree walk disagrees with sorted Git listing",
    )
    return ordered


def tree_blob(entries: dict[str, Entry], path: str) -> bytes:
    entry = entries.get(path)
    require(
        entry is not None and entry.mode in {"100644", "100755"},
        f"tree path absent: {path}",
    )
    return exact_object(entry.oid, "blob")


def tree_projection(
    entries: dict[str, Entry], paths: tuple[str, ...] | None = None
) -> bytes:
    selected = tuple(entries) if paths is None else paths
    rows: list[dict[str, Any]] = []
    for path in selected:
        entry = entries.get(path)
        require(entry is not None, f"projection path absent: {path}")
        raw = exact_object(entry.oid, "blob")
        rows.append(
            {
                "git_blob_oid_sha1": entry.oid,
                "git_mode": entry.mode,
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            }
        )
    return canonical_json(rows, pretty=False)


def protected_paths(entries: dict[str, Entry]) -> tuple[str, ...]:
    packet = parse_json(
        tree_blob(entries, ACTIVE_PACKET), "active packet", canonical=False
    )
    validate_active_packet_revision_contract(packet, "active packet")
    files = packet.get("packet_files") if isinstance(packet, dict) else None
    require(
        isinstance(files, dict) and len(files) == 72, "active packet inventory changed"
    )
    paths = tuple(sorted(set(files) | set(PROTECTED_EXTRA_PATHS)))
    require(len(paths) == PROTECTED_COUNT, "protected path count changed")
    return paths


def protected_projection(entries: dict[str, Entry]) -> tuple[bytes, str]:
    raw = tree_projection(entries, protected_paths(entries))
    return raw, hashlib.sha256(raw).hexdigest()


def parse_identity(raw: bytes, label: bytes) -> tuple[bytes, dict[str, str]]:
    prefix, separator, value = raw.partition(b" ")
    require(prefix == label and separator == b" ", "commit identity label changed")
    match = IDENTITY.fullmatch(value)
    require(match is not None, "commit identity malformed")
    name = match.group("name").decode("utf-8", errors="strict")
    email = match.group("email").decode("ascii")
    timezone = match.group("timezone").decode("ascii")
    require(
        (name, email, timezone) == (EXPECTED_NAME, EXPECTED_EMAIL, EXPECTED_TIMEZONE),
        "commit human identity/timezone changed",
    )
    return value, {"email": email, "name": name}


def parse_commit_bytes(
    raw: bytes,
    *,
    expected_tree: str,
    expected_parent: str,
    recovery: bool,
) -> dict[str, Any]:
    require(b"\r" not in raw and b"\0" not in raw, "commit contains CR/NUL")
    header, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", "commit message separator absent")
    lines = header.split(b"\n")
    require(len(lines) == 4, "commit is not unsigned sole-parent form")
    require(
        lines[0] == f"tree {expected_tree}".encode("ascii")
        and lines[1] == f"parent {expected_parent}".encode("ascii"),
        "commit tree/parent changed",
    )
    author_raw, author = parse_identity(lines[2], b"author")
    committer_raw, committer = parse_identity(lines[3], b"committer")
    require(author_raw == committer_raw, "author and committer headers differ")
    message_text = message.decode("utf-8", errors="strict")
    if recovery:
        match = re.fullmatch(
            r"Repair KSG M1a hosted recovery wiring\n\n"
            r"Sealed-index-SHA256: ([0-9a-f]{64})\n"
            r"Sealed-index-Size: ([1-9][0-9]{0,7})\n",
            message_text,
        )
        require(match is not None, "recovery message/trailer grammar changed")
        size_text = match.group(2)
        size = int(size_text, 10)
        require(
            str(size) == size_text and size <= MAX_INDEX_BYTES,
            "recovery index size noncanonical",
        )
        index_sha = match.group(1)
    else:
        require(
            message_text == CORRECTION_MESSAGE, "historical correction message changed"
        )
        index_sha = CORRECTION_INDEX_SHA256
        size = CORRECTION_INDEX_SIZE_BYTES
    return {
        "author": author,
        "committer": committer,
        "message": message_text,
        "sealed_index_sha256": index_sha,
        "sealed_index_size_bytes": size,
    }


def parse_commit(
    commit: str, *, tree: str, parent: str, recovery: bool
) -> dict[str, Any]:
    return parse_commit_bytes(
        exact_object(commit, "commit"),
        expected_tree=tree,
        expected_parent=parent,
        recovery=recovery,
    )


def validate_historical_chain() -> tuple[
    dict[str, Entry], dict[str, Entry], dict[str, Any]
]:
    # The implementation has a different message; its exact object digest plus the
    # separately checked unsigned header/tree/parent form binds that predecessor.
    validate_implementation_commit_headers()
    implementation_raw = exact_object(IMPLEMENTATION, "commit")
    require(
        hashlib.sha256(implementation_raw).hexdigest()
        == "d08cb80a6582942e4c30682194988fb93f09165b4b8df37c8eb362e4be5d6826",
        "implementation commit object bytes changed",
    )
    correction_raw = exact_object(CORRECTION, "commit")
    require(
        hashlib.sha256(correction_raw).hexdigest()
        == "b12b693a350263a6556885c131a00ba24d9848c739dfc671e09c3a8fe824ca54",
        "correction commit object bytes changed",
    )
    correction_envelope = parse_commit_bytes(
        correction_raw,
        expected_tree=CORRECTION_TREE,
        expected_parent=IMPLEMENTATION,
        recovery=False,
    )
    implementation = parse_tree(IMPLEMENTATION_TREE)
    correction = parse_tree(CORRECTION_TREE)
    require(len(correction) == CORRECTION_ENTRY_COUNT, "correction entry count changed")
    full = tree_projection(correction)
    require(
        len(full) == CORRECTION_TREE_PROJECTION_SIZE_BYTES
        and hashlib.sha256(full).hexdigest() == CORRECTION_TREE_PROJECTION_SHA256,
        "correction full-tree projection changed",
    )
    left, left_sha = protected_projection(implementation)
    right, right_sha = protected_projection(correction)
    require(
        left == right and left_sha == right_sha == PROTECTED_SHA256,
        "protected 83-path projection changed across historical subjects",
    )
    for path, (size, digest) in HISTORICAL_CORRECTION_ARTIFACTS.items():
        raw = tree_blob(correction, path)
        require(
            len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
            f"historical correction authority changed: {path}",
        )
    return implementation, correction, correction_envelope


def validate_implementation_commit_headers() -> None:
    raw = exact_object(IMPLEMENTATION, "commit")
    header, separator, _ = raw.partition(b"\n\n")
    require(separator == b"\n\n", "implementation commit malformed")
    lines = header.split(b"\n")
    require(
        len(lines) == 4
        and lines[0] == f"tree {IMPLEMENTATION_TREE}".encode("ascii")
        and lines[1] == f"parent {IMPLEMENTATION_PARENT}".encode("ascii"),
        "implementation tree/parent/signature form changed",
    )
    author, _ = parse_identity(lines[2], b"author")
    committer, _ = parse_identity(lines[3], b"committer")
    require(author == committer, "implementation author/committer changed")


def validate_policy(value: Any, *, verify_anchor: bool) -> tuple[PolicyEntry, ...]:
    root = exact_keys(
        value,
        {
            "authority",
            "commit_envelope",
            "deletions_permitted",
            "entries",
            "failed_correction_anchor",
            "forbidden_contexts",
            "implementation_anchor",
            "receipt_contract",
            "review_classes",
            "schema",
            "schema_revision",
        },
        "recovery policy",
    )
    require_named_field_paths(root, "revision", set(), "recovery policy")
    require_named_field_paths(
        root, "schema_revision", {("schema_revision",)}, "recovery policy"
    )
    exact_int(root["schema_revision"], "recovery policy schema revision", 1)
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-hosted-recovery-path-policy"
        and root["schema_revision"] == 1
        and root["deletions_permitted"] is False,
        "policy identity/deletion boundary changed",
    )
    authority = exact_keys(
        root["authority"],
        {
            "credit_permitted",
            "freeze_instruction",
            "inventory_status",
            "lifecycle_validation_permitted",
            "mechanical_resealing_permitted",
            "provisional_disposition",
            "scope",
        },
        "policy authority",
    )
    state = authority["inventory_status"]
    require(state in {"provisional", "frozen"}, "policy state invalid")
    require(
        authority["credit_permitted"] is False
        and authority["mechanical_resealing_permitted"] is False
        and authority["lifecycle_validation_permitted"] is (state == "frozen")
        and authority["provisional_disposition"] == "local_hosted_pending_no_credit",
        "policy authority overcredits or mismatches lifecycle state",
    )
    envelope = exact_keys(
        root["commit_envelope"],
        {
            "author",
            "author_and_committer_headers_identical",
            "committer",
            "message_template",
            "parent_count",
            "signature_headers_permitted",
            "timezone",
        },
        "policy commit envelope",
    )
    human = {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
    require(
        envelope
        == {
            "author": human,
            "author_and_committer_headers_identical": True,
            "committer": human,
            "message_template": RECOVERY_MESSAGE_TEMPLATE,
            "parent_count": 1,
            "signature_headers_permitted": False,
            "timezone": EXPECTED_TIMEZONE,
        },
        "policy recovery envelope changed",
    )
    rows: list[PolicyEntry] = []
    require(isinstance(root["entries"], list), "policy entries not a list")
    for raw in root["entries"]:
        item = exact_keys(raw, {"path", "review_class", "status"}, "policy entry")
        validate_path(item["path"])
        require(item["status"] in {"A", "M"}, "policy status invalid")
        rows.append(PolicyEntry(item["path"], item["status"], item["review_class"]))
    require(
        len(rows) == 27
        and sum(row.status == "M" for row in rows) == 19
        and sum(row.status == "A" for row in rows) == 8
        and tuple(row.path for row in rows) == tuple(sorted(REQUIRED_POLICY_ROWS))
        and {row.path: (row.status, row.review_class) for row in rows}
        == REQUIRED_POLICY_ROWS,
        "policy 27-path reviewed inventory changed",
    )
    reviews = root["review_classes"]
    require(
        isinstance(reviews, dict)
        and set(reviews) == EXPECTED_REVIEW_CLASSES
        and all(isinstance(item, str) and item for item in reviews.values()),
        "policy review-class authority changed",
    )
    failed = root["failed_correction_anchor"]
    implementation = root["implementation_anchor"]
    require(
        isinstance(failed, dict)
        and failed.get("commit") == CORRECTION
        and failed.get("direct_parent") == IMPLEMENTATION
        and failed.get("tree") == CORRECTION_TREE
        and failed.get("sealed_index")
        == {
            "entry_count": CORRECTION_ENTRY_COUNT,
            "sha256": CORRECTION_INDEX_SHA256,
            "size_bytes": CORRECTION_INDEX_SIZE_BYTES,
        }
        and isinstance(implementation, dict)
        and implementation.get("commit") == IMPLEMENTATION
        and implementation.get("direct_parent") == IMPLEMENTATION_PARENT
        and implementation.get("tree") == IMPLEMENTATION_TREE
        and implementation.get("protected_projection", {}).get("entry_count")
        == PROTECTED_COUNT
        and implementation.get("protected_projection", {}).get("sha256")
        == PROTECTED_SHA256,
        "policy predecessor anchors changed",
    )
    receipt = root["receipt_contract"]
    require(
        isinstance(receipt, dict)
        and receipt.get("receipt_path") == FUTURE_RECEIPT
        and receipt.get("receipt_schema") == RECEIPT_SCHEMA
        and receipt.get("retained_correction_index_path") == OLD_RETAINED_INDEX
        and receipt.get("retained_recovery_index_path") == RECOVERY_RETAINED_INDEX
        and all(
            receipt.get(key) is True
            for key in (
                "failed_correction_ci_must_remain_failed",
                "failed_correction_codeql_must_remain_separate",
                "later_descendant_required",
                "recovery_subject_must_not_contain_receipt",
                "recovery_subject_must_not_contain_retained_indexes",
            )
        ),
        "policy receipt contract changed",
    )
    require(
        isinstance(root["forbidden_contexts"], list)
        and len(root["forbidden_contexts"]) == 7
        and all(isinstance(item, str) and item for item in root["forbidden_contexts"]),
        "policy forbidden contexts changed",
    )
    semantic_projection = {key: item for key, item in root.items() if key != "entries"}
    semantic_authority = dict(authority)
    semantic_authority["inventory_status"] = "<POLICY-STATE>"
    semantic_authority["lifecycle_validation_permitted"] = "<POLICY-STATE>"
    semantic_projection["authority"] = semantic_authority
    require(
        hashlib.sha256(canonical_json(semantic_projection, pretty=False)).hexdigest()
        == EXPECTED_POLICY_SEMANTIC_PROJECTION_SHA256,
        "policy non-entry semantic authority changed/resealed",
    )
    if verify_anchor:
        validate_implementation_commit_headers()
    return tuple(rows)


def load_policy() -> tuple[dict[str, Any], bytes, tuple[PolicyEntry, ...]]:
    raw = read_regular(POLICY_RELATIVE)
    value = parse_json(raw, "recovery policy")
    rows = validate_policy(value, verify_anchor=True)
    state = value["authority"]["inventory_status"]
    if state == "frozen":
        require(
            HEX64.fullmatch(EXPECTED_FROZEN_POLICY_SHA256) is not None
            and len(raw) == EXPECTED_FROZEN_POLICY_SIZE_BYTES
            and hashlib.sha256(raw).hexdigest() == EXPECTED_FROZEN_POLICY_SHA256,
            "frozen policy digest placeholder/mismatch",
        )
    return value, raw, rows


def validate_freeze_inventory(
    state: str,
    *,
    source: bytes | None = None,
    digest_pins: tuple[str, ...] | None = None,
    size_pins: tuple[int, ...] | None = None,
) -> None:
    require(state in {"provisional", "frozen"}, "freeze inventory state changed")
    if state == "provisional":
        return
    if source is None:
        source = read_regular(CHECKER_RELATIVE)
    if digest_pins is None:
        digest_pins = (
            EXPECTED_FROZEN_POLICY_SHA256,
            EXPECTED_FROZEN_BOUNDARY_SHA256,
            EXPECTED_FROZEN_SELF_TEST_SHA256,
            EXPECTED_FROZEN_SCHEMA_SHA256,
            EXPECTED_FROZEN_NEGATIVE_SHA256,
            EXPECTED_FROZEN_CERT_CHECKER_SHA256,
            EXPECTED_FROZEN_CERT_SELF_TEST_SHA256,
            EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256,
            EXPECTED_FROZEN_LEAN_SELF_TEST_SHA256,
            EXPECTED_FROZEN_LEAN_GENERATOR_SHA256,
            EXPECTED_FROZEN_WORKFLOW_SHA256,
            EXPECTED_FROZEN_JUST_SHA256,
            EXPECTED_FROZEN_SCRIPTS_README_SHA256,
            *(digest for _size, digest in EXPECTED_CHILD_STDOUT.values()),
        )
    if size_pins is None:
        size_pins = (
            EXPECTED_FROZEN_POLICY_SIZE_BYTES,
            EXPECTED_FROZEN_BOUNDARY_SIZE_BYTES,
            EXPECTED_FROZEN_SELF_TEST_SIZE_BYTES,
            EXPECTED_FROZEN_SCHEMA_SIZE_BYTES,
            EXPECTED_FROZEN_NEGATIVE_SIZE_BYTES,
            EXPECTED_FROZEN_CERT_CHECKER_SIZE_BYTES,
            EXPECTED_FROZEN_CERT_SELF_TEST_SIZE_BYTES,
            EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES,
            EXPECTED_FROZEN_LEAN_SELF_TEST_SIZE_BYTES,
            EXPECTED_FROZEN_LEAN_GENERATOR_SIZE_BYTES,
            EXPECTED_FROZEN_WORKFLOW_SIZE_BYTES,
            EXPECTED_FROZEN_JUST_SIZE_BYTES,
            EXPECTED_FROZEN_SCRIPTS_README_SIZE_BYTES,
            *(size for size, _digest in EXPECTED_CHILD_STDOUT.values()),
        )
    require(
        (b"__" + b"FREEZE_") not in source
        and bool(digest_pins)
        and all(
            isinstance(digest, str) and HEX64.fullmatch(digest) is not None
            for digest in digest_pins
        )
        and bool(size_pins)
        and all(type(size) is int and size > 0 for size in size_pins),
        "frozen checker retains a placeholder or malformed reviewed pin",
    )


def validate_boundary(raw: bytes, state: str) -> None:
    text = raw.decode("utf-8", errors="strict")
    marker = f"<!-- ksg-m1a-hosted-recovery-policy-state: {state} -->"
    require(text.count(marker) == 1, "boundary policy-state marker changed")
    state_text = (
        "provisional inventory; exact lifecycle validation disabled; hosted pending; no credit"
        if state == "provisional"
        else "frozen reviewed inventory; exact local lifecycle validation enabled; hosted pending; no credit"
    )
    require(state_text in text, "boundary human policy state changed")
    for token in (
        IMPLEMENTATION,
        CORRECTION,
        CORRECTION_TREE,
        "31724449805",
        "31724449083",
        "fetch-depth: 0",
        "27-path",
        "19 modifications and 8 additions",
        "descriptor 0",
        "integration_no_go",
        FUTURE_RECEIPT,
        OLD_RETAINED_INDEX,
        RECOVERY_RETAINED_INDEX,
    ):
        require(token in text, f"boundary token disappeared: {token}")
    if state == "frozen":
        require(
            len(raw) == EXPECTED_FROZEN_BOUNDARY_SIZE_BYTES
            and hashlib.sha256(raw).hexdigest() == EXPECTED_FROZEN_BOUNDARY_SHA256,
            "frozen boundary exact bytes changed",
        )


def validate_static_artifacts(state: str) -> dict[str, str]:
    boundary = read_regular(BOUNDARY_RELATIVE)
    validate_boundary(boundary, state)
    result = {BOUNDARY_RELATIVE: hashlib.sha256(boundary).hexdigest()}
    if state == "frozen":
        for path, expected_size, expected_digest in (
            (
                SELF_TEST_RELATIVE,
                EXPECTED_FROZEN_SELF_TEST_SIZE_BYTES,
                EXPECTED_FROZEN_SELF_TEST_SHA256,
            ),
            (
                SCHEMA_RELATIVE,
                EXPECTED_FROZEN_SCHEMA_SIZE_BYTES,
                EXPECTED_FROZEN_SCHEMA_SHA256,
            ),
            (
                NEGATIVE_RELATIVE,
                EXPECTED_FROZEN_NEGATIVE_SIZE_BYTES,
                EXPECTED_FROZEN_NEGATIVE_SHA256,
            ),
        ):
            raw = read_regular(path)
            require(
                HEX64.fullmatch(expected_digest) is not None
                and (expected_size < 0 or len(raw) == expected_size)
                and hashlib.sha256(raw).hexdigest() == expected_digest,
                f"frozen static artifact changed: {path}",
            )
            result[path] = hashlib.sha256(raw).hexdigest()
    return result


def changed_entries(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    for path in sorted(set(anchor) | set(candidate)):
        left = anchor.get(path)
        right = candidate.get(path)
        if left == right:
            continue
        status = "D" if right is None else "A" if left is None else "M"
        mode = "000000" if right is None else right.mode
        rows.append((path, status, mode))
    return tuple(rows)


def validate_delta(
    rows: tuple[PolicyEntry, ...],
    correction: dict[str, Entry],
    candidate: dict[str, Entry],
) -> tuple[tuple[str, str, str], ...]:
    observed = changed_entries(correction, candidate)
    expected = tuple((row.path, row.status, "100644") for row in rows)
    require(observed == expected, "recovery candidate delta differs from exact policy")
    require(len(candidate) == 732, "recovery candidate entry count changed")
    for path in (
        FUTURE_RECEIPT,
        OLD_RETAINED_INDEX,
        RECOVERY_RETAINED_INDEX,
        FINAL_MATRIX,
        FINAL_DECISION,
    ):
        require(
            path not in candidate, f"recovery subject contains future authority: {path}"
        )
    return observed


def reject_retired_attempt(
    checkpoint: str,
    tree: str,
    index_sha256: str,
    index_size_bytes: int,
    entry_count: int,
) -> None:
    require(
        checkpoint != RETIRED_RECOVERY_CHECKPOINT
        and tree != RETIRED_RECOVERY_TREE
        and (index_sha256, index_size_bytes, entry_count)
        != (
            RETIRED_RECOVERY_INDEX_SHA256,
            RETIRED_RECOVERY_INDEX_SIZE_BYTES,
            RETIRED_RECOVERY_ENTRY_COUNT,
        ),
        "retired failed local recovery attempt was reused or relabeled",
    )


def assignment_span(source: str, tree: ast.Module, name: str) -> tuple[str, Any]:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    require(len(matches) == 1, f"certified assignment changed: {name}")
    node = matches[0]
    require(
        node.lineno is not None
        and node.end_lineno is not None
        and node.col_offset == 0
        and node.end_col_offset is not None,
        f"certified assignment span unavailable: {name}",
    )
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    start = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    try:
        value = ast.literal_eval(node.value)
    except (ValueError, SyntaxError) as error:
        raise RecoveryError(f"certified assignment not literal: {name}") from error
    return source[start:end], value


def node_text(source: str, node: ast.AST, label: str) -> str:
    require(
        hasattr(node, "lineno")
        and hasattr(node, "end_lineno")
        and node.lineno is not None  # type: ignore[attr-defined]
        and node.end_lineno is not None  # type: ignore[attr-defined]
        and node.col_offset is not None  # type: ignore[attr-defined]
        and node.end_col_offset is not None,  # type: ignore[attr-defined]
        f"{label} source span unavailable",
    )
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    start = starts[node.lineno - 1] + node.col_offset  # type: ignore[attr-defined]
    end = starts[node.end_lineno - 1] + node.end_col_offset  # type: ignore[attr-defined]
    return source[start:end]


def mapping_value_node(tree: ast.Module, assignment: str, key: str) -> ast.AST:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == assignment
        and isinstance(node.value, ast.Dict)
    ]
    require(len(matches) == 1, f"mapping assignment changed: {assignment}")
    mapping = matches[0].value
    values = [
        value
        for raw_key, value in zip(mapping.keys, mapping.values, strict=True)
        if isinstance(raw_key, ast.Constant) and raw_key.value == key
    ]
    require(len(values) == 1, f"mapping key changed: {assignment}[{key!r}]")
    return values[0]


CERT_REBINDS = (
    "EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256",
    "EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256",
    "EXPECTED_EXECUTION_CONTAINER_SHA256",
    "EXPECTED_REVIEWED_DOCUMENTATION_SHA256",
)
CERT_SELF_TEST_REBINDS = (
    "EXPECTED_CI_JOB_DIGEST",
    "EXPECTED_JUST_RECIPE_DIGEST",
)
CERT_PRIVATE_BLOCK_BEGIN = b"# BEGIN KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
CERT_PRIVATE_BLOCK_END = b"# END KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
CERT_BOOTSTRAP_BLOCK_BEGIN = b"# BEGIN KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
CERT_BOOTSTRAP_BLOCK_END = b"# END KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
CERT_EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE = 2776
CERT_EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA = (
    "e843b76db3f67b3bb331be12b346423a10e748edaf119c920d06b71318de95e8"
)
CERT_EXPECTED_CHECKER_BOOTSTRAP_SIZE = 668
CERT_EXPECTED_CHECKER_BOOTSTRAP_SHA = (
    "1129a9c3987603fbf16507edc8adebc54a69f7a9acf68494a099247bf41a6106"
)
CERT_EXPECTED_PRIVATE_BLOCK_SIZE = 9085
CERT_EXPECTED_PRIVATE_BLOCK_SHA = (
    "cab243329941efab04a038b67690ec912c30d8c4b59b7bc7f0d705601b55f6de"
)


def normalize_certified_source(raw: bytes) -> tuple[str, dict[str, Any]]:
    source = raw.decode("utf-8", errors="strict")
    tree = ast.parse(source, filename="<certified-checker>")
    values: dict[str, Any] = {}
    normalized = source
    for name in CERT_REBINDS:
        span, value = assignment_span(source, tree, name)
        values[name] = value
        require(
            normalized.count(span) == 1, f"certified assignment text ambiguous: {name}"
        )
        normalized = normalized.replace(span, f"{name} = <RECOVERY-REBIND>", 1)
    return normalized, values


def normalize_literal_assignments(
    raw: bytes, names: tuple[str, ...], label: str
) -> tuple[str, dict[str, Any]]:
    source = raw.decode("utf-8", errors="strict")
    tree = ast.parse(source, filename=f"<{label}>")
    normalized = source
    values: dict[str, Any] = {}
    for name in names:
        segment, value = assignment_span(source, tree, name)
        require(normalized.count(segment) == 1, f"{label} assignment ambiguous: {name}")
        normalized = normalized.replace(segment, f"{name} = <RECOVERY-REBIND>", 1)
        values[name] = value
    return normalized, values


def exact_marked_block(raw: bytes, begin: bytes, end: bytes, label: str) -> bytes:
    require(
        raw.count(begin) == raw.count(end) == 1, f"{label} marker inventory changed"
    )
    start = raw.index(begin)
    finish = raw.index(end, start) + len(end)
    require(
        start >= 2
        and raw[start - 2 : start] == b"\n\n"
        and raw[finish : finish + 1] == b"\n",
        f"{label} blank-line/marker boundary changed",
    )
    return raw[start:finish]


def literal_assignment_value(raw: bytes, name: str, label: str) -> Any:
    source = raw.decode("utf-8", errors="strict")
    tree = ast.parse(source, filename=f"<{label}>")
    _segment, value = assignment_span(source, tree, name)
    return value


def validate_version_stable_cert_protocol(
    correction_checker: bytes,
    candidate_checker: bytes,
    correction_selftest: bytes,
    candidate_selftest: bytes,
) -> None:
    normalized_anchor_checker, _anchor_checker_values = normalize_certified_source(
        correction_checker
    )
    normalized_candidate_checker, _candidate_checker_values = (
        normalize_certified_source(candidate_checker)
    )
    require(
        normalized_anchor_checker == normalized_candidate_checker,
        "certified checker differs beyond the four reviewed literal rebinds",
    )
    candidate_bootstrap = exact_marked_block(
        candidate_checker,
        CERT_BOOTSTRAP_BLOCK_BEGIN,
        CERT_BOOTSTRAP_BLOCK_END,
        "certified checker bootstrap block",
    )
    # The retained convention hashes the marked content through the byte before
    # the end marker.  This raw-byte predicate is CPython-minor-independent.
    reviewed_bootstrap = candidate_bootstrap[: -len(CERT_BOOTSTRAP_BLOCK_END)]
    require(
        len(reviewed_bootstrap) == CERT_EXPECTED_CHECKER_BOOTSTRAP_SIZE
        and hashlib.sha256(reviewed_bootstrap).hexdigest()
        == CERT_EXPECTED_CHECKER_BOOTSTRAP_SHA,
        "certified checker bootstrap exact bytes changed",
    )
    exact_marked_block(
        candidate_checker,
        CERT_PRIVATE_BLOCK_BEGIN,
        CERT_PRIVATE_BLOCK_END,
        "certified private-vector block",
    )
    candidate_private = exact_marked_block(
        candidate_checker,
        CERT_PRIVATE_BLOCK_BEGIN,
        CERT_PRIVATE_BLOCK_END,
        "certified private-vector block",
    )[: -len(CERT_PRIVATE_BLOCK_END)]
    correction_bootstrap = exact_marked_block(
        correction_checker,
        CERT_BOOTSTRAP_BLOCK_BEGIN,
        CERT_BOOTSTRAP_BLOCK_END,
        "7473 certified checker bootstrap block",
    )
    correction_private = exact_marked_block(
        correction_checker,
        CERT_PRIVATE_BLOCK_BEGIN,
        CERT_PRIVATE_BLOCK_END,
        "7473 certified private-vector block",
    )
    require(
        correction_bootstrap == candidate_bootstrap
        and correction_private[: -len(CERT_PRIVATE_BLOCK_END)] == candidate_private
        and len(candidate_private) == CERT_EXPECTED_PRIVATE_BLOCK_SIZE
        and hashlib.sha256(candidate_private).hexdigest()
        == CERT_EXPECTED_PRIVATE_BLOCK_SHA,
        "certified marked protocol blocks changed from 7473 authority",
    )
    normalized_anchor, anchor_values = normalize_literal_assignments(
        correction_selftest, CERT_SELF_TEST_REBINDS, "7473 certified self-test"
    )
    normalized_candidate, candidate_values = normalize_literal_assignments(
        candidate_selftest, CERT_SELF_TEST_REBINDS, "recovery certified self-test"
    )
    require(
        normalized_anchor == normalized_candidate
        and candidate_values["EXPECTED_CI_JOB_DIGEST"]
        != anchor_values["EXPECTED_CI_JOB_DIGEST"]
        and candidate_values["EXPECTED_JUST_RECIPE_DIGEST"]
        == anchor_values["EXPECTED_JUST_RECIPE_DIGEST"],
        "certified self-test differs beyond the one CI job digest rebind",
    )
    stdin_bootstrap = literal_assignment_value(
        candidate_selftest, "CHECKER_STDIN_BOOTSTRAP", "certified self-test"
    )
    require(
        isinstance(stdin_bootstrap, str)
        and len(stdin_bootstrap.encode("utf-8"))
        == CERT_EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE
        and hashlib.sha256(stdin_bootstrap.encode("utf-8")).hexdigest()
        == CERT_EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA
        and "exec(compile(_source" in stdin_bootstrap
        and "os.dup2(_input.fileno(), 0)" in stdin_bootstrap,
        "certified private exact-source launcher bytes changed",
    )
    # Parse all reviewed pieces with this exact runtime.  We deliberately do
    # not store ast.dump/marshal bytes: those are CPython-minor-version data.
    for source, parse_label in (
        (candidate_selftest.decode("utf-8", errors="strict"), "certified self-test"),
        (reviewed_bootstrap.decode("utf-8", errors="strict"), "certified bootstrap"),
        (
            candidate_private.decode("utf-8", errors="strict"),
            "certified private vector",
        ),
        (stdin_bootstrap, "certified source launcher"),
    ):
        ast.parse(source, filename=f"<{parse_label}>")


def extract_container(raw: bytes, start_line: str, next_pattern: str) -> bytes:
    text = raw.decode("utf-8", errors="strict")
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line == start_line]
    require(len(starts) == 1, f"container start not unique: {start_line.strip()}")
    start = starts[0]
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if re.fullmatch(next_pattern, lines[index]) is not None
        ),
        len(lines),
    )
    return "".join(lines[start:end]).encode("utf-8")


def validate_workflow_fetch_depth(anchor_raw: bytes, candidate_raw: bytes) -> str:
    anchor_job = extract_container(
        anchor_raw, "  certified-sxpid-reference:\n", r"  [A-Za-z0-9_-]+:\n"
    )
    candidate_job = extract_container(
        candidate_raw, "  certified-sxpid-reference:\n", r"  [A-Za-z0-9_-]+:\n"
    )
    addition = b"          fetch-depth: 0\n"
    require(
        candidate_job.count(addition) == 1,
        "certified checkout lacks unique fetch-depth zero",
    )
    require(
        anchor_job.count(addition) == 0,
        "historical job unexpectedly contains recovery line",
    )
    require(
        candidate_job.replace(addition, b"", 1) == anchor_job,
        "certified job changed beyond fetch-depth zero",
    )
    require(
        candidate_job.count(b"persist-credentials: false\n") == 1
        and candidate_job.index(addition)
        < candidate_job.index(b"persist-credentials: false\n"),
        "certified checkout credential/history ordering changed",
    )
    return hashlib.sha256(candidate_job).hexdigest()


def just_recipe(raw: bytes) -> bytes:
    return extract_container(raw, "certified-sxpid:\n", r"[^ \t\r\n].*\n")


def marker_block(raw: bytes, begin: bytes, end: bytes, label: str) -> bytes:
    require(raw.count(begin) == 1 and raw.count(end) == 1, f"{label} markers changed")
    start = raw.index(begin)
    finish = raw.index(end, start) + len(end)
    require(start < finish, f"{label} marker order changed")
    return raw[start:finish]


def validate_recovery_wiring(workflow: bytes, just: bytes, readme: bytes) -> None:
    workflow_text = workflow.decode("utf-8", errors="strict")
    require(
        re.search(r"(?m)^defaults:\s*$", workflow_text) is None,
        "global workflow defaults are forbidden",
    )
    workflow_block = marker_block(
        workflow,
        b"      # BEGIN KSG_M1A_HOSTED_RECOVERY_WORKFLOW_V1\n",
        b"      # END KSG_M1A_HOSTED_RECOVERY_WORKFLOW_V1\n",
        "hosted-recovery workflow",
    )
    require(
        workflow_block.count(
            b"      - name: Verify the KSG M1a hosted-recovery lifecycle\n"
        )
        == 1
        and workflow_block.count(b"        run: |\n") == 1
        and re.search(
            rb"(?m)^\s{6,10}(?:if|shell|continue-on-error|working-directory):",
            workflow_block,
        )
        is None,
        "hosted-recovery workflow job/step guard or relocation changed",
    )
    ksg_job = extract_container(
        workflow, "  ksg-harmonic-assurance:\n", r"  [A-Za-z0-9_-]+:\n"
    )
    require(workflow_block in ksg_job, "hosted-recovery step left KSG assurance job")
    workflow_commands = (
        b"python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \\\n",
        b"python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \\\n",
        b"python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
        b"python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
    )
    require(
        workflow_block.count(workflow_commands[0]) == 4
        and workflow_block.count(workflow_commands[1]) == 4
        and workflow_block.count(workflow_commands[2]) == 1
        and workflow_block.count(workflow_commands[3]) == 1
        and workflow_block.count(b"--mode candidate-commit \\\n") == 2
        and workflow_block.count(b"--mode postcommit \\\n") == 2
        and workflow_block.count(
            b'--validate-composite-receipt < "$composite_receipt"\n'
        )
        == 2,
        "hosted-recovery workflow command projection changed",
    )
    composite_start = b'          if [[ -f "$composite_receipt" ]]\n'
    require(
        workflow_block.count(composite_start) == 1,
        "composite receipt applicability block changed",
    )
    composite_block = workflow_block[workflow_block.index(composite_start) :]
    for token in (
        b'            receipt_recovery="$(\n',
        b"              python3 -I -S -B - \"$composite_receipt\" <<'PY'\n",
        b"              value = json.loads(raw, object_pairs_hook=unique)\n",
        b'            if [[ "$GITHUB_EVENT_NAME" == "push" ]] \\\n',
        b'              && [[ "$GITHUB_REF" == "refs/heads/main" ]] \\\n',
        b'              && [[ "$head" == "$GITHUB_SHA" ]] \\\n',
        b'              && [[ "$parent_count" == "1" ]] \\\n',
        b'              && [[ "$direct_parent" == "$receipt_recovery" ]]\n',
        b"              if git symbolic-ref -q HEAD >/dev/null\n",
        b"composite receipt is retained outside its exact direct-child push; sole-child validation is not applicable and no credit is granted",
    ):
        require(
            composite_block.count(token) == 1,
            "composite receipt exact-topology guard changed",
        )
    require(
        b"git switch" not in composite_block
        and b"git branch" not in composite_block
        and composite_block.count(
            b'--validate-composite-receipt < "$composite_receipt"\n'
        )
        == 2,
        "composite receipt detached-checkout lifecycle changed",
    )

    just_text = just.decode("utf-8", errors="strict")
    require(
        just_text.count("ksg-revision:\n") == 1
        and "set shell" not in just_text.lower()
        and "shell :=" not in just_text.lower(),
        "Just recovery recipe/shell authority duplicated or relocated",
    )
    recipe = extract_container(just, "ksg-revision:\n", r"[^ \t\r\n].*\n")
    just_block = marker_block(
        recipe,
        b"    # BEGIN KSG_M1A_HOSTED_RECOVERY_JUST_V1\n",
        b"    # END KSG_M1A_HOSTED_RECOVERY_JUST_V1\n",
        "hosted-recovery Just",
    )
    exact_just_commands = (
        b"    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py --validate-policy-only --allow-provisional-diagnostic\n",
        b"    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py --validate-policy-only --allow-provisional-diagnostic\n",
        b"    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
        b"    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py\n",
    )
    require(
        all(just_block.count(command) == 1 for command in exact_just_commands)
        and b"set shell" not in just_block.lower()
        and b"shell :=" not in just_block.lower(),
        "hosted-recovery Just command/shell projection changed",
    )

    readme_text = readme.decode("utf-8", errors="strict")
    begin = "<!-- BEGIN KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n"
    end = "<!-- END KSG_M1A_HOSTED_RECOVERY_README_V1 -->\n"
    readme_block = marker_block(
        readme, begin.encode(), end.encode(), "hosted-recovery README"
    )
    prefix = readme_text[: readme_text.index(begin)]
    require(
        prefix.count("```") % 2 == 0,
        "hosted-recovery README marker is inside an outer fence",
    )
    for token in (
        "## KSG M1a hosted-recovery verifier",
        "fetch-depth: 0",
        "--allow-provisional-diagnostic",
        "--mode precommit",
        "--mode candidate-commit",
        "--mode postcommit",
        "cb3f58f0...",
        CORRECTION,
        "integration_no_go",
    ):
        require(
            token.encode() in readme_block,
            f"hosted-recovery README token absent: {token}",
        )

    # Prose is line-wrapped for publication.  Collapse ASCII whitespace only:
    # accepting Unicode lookalike whitespace here would make the certified
    # semantic projection broader than the Markdown source readers inspect.
    normalized_readme = re.sub(rb"[\t\n\v\f\r ]+", b" ", readme_block).strip()
    for truth in (
        b"C4 was published as `da253576a5f76e99633fff4de5cf1118f967b90d`, "
        b"but its attempt-1 hosted qualification failed; R4 is therefore permanently "
        b"unissued.",
        b"The append-only correction is documented in "
        b"`audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md`",
        b"C5 is the unsigned direct child of published C4",
        b"The predecessor-failure capture belongs to C5.",
        b"Only a fresh attempt-1 all-success C5 qualification can permit R5",
        b"The receipt binds both captures.",
        b"C4's attempt-1 qualification failed, R4 is permanently unissued, and the two "
        b"reserved v4 evidence paths must remain absent.",
        b"Do not run the v4 live capture, derive an R4 receipt, reinterpret a rerun as "
        b"attempt 1, or seed evidence from its synthetic fixture.",
        b"Composite-v5 uses separately versioned predecessor/successor captures and a "
        b"separately typed R5 receipt; those artifacts preserve the failed observation "
        b"without reviving or renaming R4.",
    ):
        require(
            truth in normalized_readme,
            f"hosted-recovery README current C4/C5 truth absent: {truth.decode()}",
        )

    lowered = normalized_readme.lower()
    for contradiction in (
        b"shallow checkout is sufficient",
        b"fetch-depth: 0 is unnecessary",
        b"grants scientific credit",
        b"validate on every later descendant",
        b"integration_go",
        b"r4 may be issued",
        b"r4 can be revived",
        b"run the v4 live capture now",
        b"derive and publish an r4 receipt",
        b"rename r5 as r4",
        b"reuse the v4 capture for composite-v5",
        b"one shared v5 capture is sufficient",
    ):
        require(
            contradiction not in lowered, "hosted-recovery README contradicts authority"
        )


def validate_certified_rebind(
    correction: dict[str, Entry], candidate: dict[str, Entry]
) -> dict[str, str]:
    anchor_checker = tree_blob(correction, CERT_CHECKER)
    candidate_checker = tree_blob(candidate, CERT_CHECKER)
    anchor_normalized, anchor_values = normalize_certified_source(anchor_checker)
    candidate_normalized, values = normalize_certified_source(candidate_checker)
    require(
        anchor_normalized == candidate_normalized,
        "certified checker changed beyond four rebind assignments",
    )
    workflow = tree_blob(candidate, ".github/workflows/ci.yml")
    just = tree_blob(candidate, "justfile")
    readme = tree_blob(candidate, "scripts/README.md")
    validate_recovery_wiring(workflow, just, readme)
    for path, raw, expected_size, expected_digest in (
        (
            ".github/workflows/ci.yml",
            workflow,
            EXPECTED_FROZEN_WORKFLOW_SIZE_BYTES,
            EXPECTED_FROZEN_WORKFLOW_SHA256,
        ),
        (
            "justfile",
            just,
            EXPECTED_FROZEN_JUST_SIZE_BYTES,
            EXPECTED_FROZEN_JUST_SHA256,
        ),
        (
            "scripts/README.md",
            readme,
            EXPECTED_FROZEN_SCRIPTS_README_SIZE_BYTES,
            EXPECTED_FROZEN_SCRIPTS_README_SHA256,
        ),
    ):
        require(
            expected_size == len(raw)
            and HEX64.fullmatch(expected_digest) is not None
            and hashlib.sha256(raw).hexdigest() == expected_digest,
            f"frozen recovery wiring bytes changed: {path}",
        )
    workflow_job_sha = validate_workflow_fetch_depth(
        tree_blob(correction, ".github/workflows/ci.yml"), workflow
    )
    recipe_sha = hashlib.sha256(just_recipe(just)).hexdigest()
    execution = values["EXPECTED_EXECUTION_CONTAINER_SHA256"]
    documentation = values["EXPECTED_REVIEWED_DOCUMENTATION_SHA256"]
    require(
        values["EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256"] == workflow_job_sha
        and values["EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256"] == recipe_sha
        and execution
        == {
            ".github/workflows/ci.yml": hashlib.sha256(workflow).hexdigest(),
            "justfile": hashlib.sha256(just).hexdigest(),
        }
        and isinstance(documentation, dict)
        and documentation.get("scripts/README.md") == hashlib.sha256(readme).hexdigest()
        and documentation.get("audit/tools/certified-sxpid/README.md")
        == anchor_values["EXPECTED_REVIEWED_DOCUMENTATION_SHA256"].get(
            "audit/tools/certified-sxpid/README.md"
        ),
        "certified four-container digest rebind is not exact",
    )
    require(
        len(candidate_checker) == EXPECTED_FROZEN_CERT_CHECKER_SIZE_BYTES
        and hashlib.sha256(candidate_checker).hexdigest()
        == EXPECTED_FROZEN_CERT_CHECKER_SHA256,
        "frozen certified checker bytes changed",
    )
    selftest = tree_blob(candidate, CERT_SELF_TEST)
    correction_selftest = tree_blob(correction, CERT_SELF_TEST)
    validate_version_stable_cert_protocol(
        anchor_checker, candidate_checker, correction_selftest, selftest
    )
    selftest_text = selftest.decode("utf-8", errors="strict")
    for token in (
        IMPLEMENTATION,
        "cannot read the fixed cb3f certified-checker authority",
        "git",
        "show",
        "CHECKER_STDIN_BOOTSTRAP",
    ):
        require(
            token in selftest_text,
            f"certified self-test history/source token absent: {token}",
        )
    require(
        len(selftest) == EXPECTED_FROZEN_CERT_SELF_TEST_SIZE_BYTES
        and hashlib.sha256(selftest).hexdigest()
        == EXPECTED_FROZEN_CERT_SELF_TEST_SHA256,
        "frozen certified self-test bytes changed",
    )
    return {
        "certified_checker": hashlib.sha256(candidate_checker).hexdigest(),
        "certified_self_test": hashlib.sha256(selftest).hexdigest(),
        "just_recipe": recipe_sha,
        "workflow_job": workflow_job_sha,
    }


def compact_projection(value: Any) -> bytes:
    return canonical_json(value, pretty=False)


def validate_projection_binding(
    value: Any,
    projected: Any,
    encoding: str,
    label: str,
    *,
    entry_count: int | None = None,
) -> str:
    keys = (
        {"encoding", "sha256", "size_bytes"}
        if entry_count is None
        else {
            "encoding",
            "entry_count",
            "sha256",
        }
    )
    item = exact_keys(value, keys, label)
    raw = compact_projection(projected)
    require(
        item["encoding"] == encoding
        and item["sha256"] == hashlib.sha256(raw).hexdigest()
        and (entry_count is not None or item["size_bytes"] == len(raw))
        and (entry_count is None or item["entry_count"] == entry_count),
        f"{label} does not bind the exact projection",
    )
    return item["sha256"]


def validate_api_capture(
    value: Any,
    endpoint: str,
    projected: Any,
    label: str,
    *,
    fixed_correction: bool = True,
) -> None:
    item = exact_keys(
        value,
        {
            "endpoint_class",
            "format",
            "pagination_complete",
            "repetitions_equal",
            "sha256",
            "size_bytes",
        },
        label,
    )
    raw = compact_projection(projected)
    expected = EXPECTED_CORRECTION_CAPTURE_BINDINGS.get(endpoint)
    require(
        item["endpoint_class"] == endpoint
        and item["format"] == CURRENT_CAPTURE_FORMAT
        and item["pagination_complete"] is True
        and item["repetitions_equal"] is True
        and item["size_bytes"] == len(raw)
        and item["sha256"] == hashlib.sha256(raw).hexdigest()
        and (
            not fixed_correction
            or (
                expected is not None
                and item["size_bytes"] == expected[0]
                and item["sha256"] == expected[1]
            )
        ),
        f"{label} capture projection changed",
    )


def validate_hosted_jobs(
    value: Any,
    label: str,
    expected_count: int,
    *,
    require_success: bool = False,
) -> list[dict[str, Any]]:
    require(
        isinstance(value, list) and len(value) == expected_count,
        f"{label} job count changed",
    )
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        row = exact_keys(
            raw,
            {
                "completed_at",
                "conclusion",
                "job_id",
                "name",
                "started_at",
                "status",
                "steps",
            },
            f"{label} job {index}",
        )
        exact_int(row["job_id"], f"{label} job id", 1)
        require(
            row["status"] == "completed"
            and row["conclusion"] in {"cancelled", "failure", "skipped", "success"}
            and isinstance(row["name"], str)
            and row["name"]
            and isinstance(row["started_at"], str)
            and isinstance(row["completed_at"], str),
            f"{label} job lifecycle changed",
        )
        started = parse_rfc3339_utc(row["started_at"], f"{label} job started_at")
        completed = parse_rfc3339_utc(row["completed_at"], f"{label} job completed_at")
        require(started <= completed, f"{label} job interval is reversed")
        steps = row["steps"]
        require(isinstance(steps, list) and steps, f"{label} job steps absent")
        prior = 0
        for step_raw in steps:
            step = exact_keys(
                step_raw, {"conclusion", "name", "number", "status"}, f"{label} step"
            )
            number = exact_int(step["number"], f"{label} step number", 1)
            require(
                number > prior
                and step["status"] == "completed"
                and step["conclusion"] in {"cancelled", "failure", "skipped", "success"}
                and isinstance(step["name"], str)
                and step["name"],
                f"{label} step roster is not exact/sorted",
            )
            prior = number
        if require_success:
            require(
                row["conclusion"] == "success"
                and all(step["conclusion"] in {"skipped", "success"} for step in steps),
                f"{label} successful job contains a non-success step",
            )
        rows.append(row)
    require(
        [row["job_id"] for row in rows] == sorted({row["job_id"] for row in rows}),
        f"{label} jobs are not job-id-sorted unique",
    )
    return rows


def parse_rfc3339_utc(value: Any, label: str) -> datetime.datetime:
    require(
        isinstance(value, str)
        and re.fullmatch(
            r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?Z",
            value,
        )
        is not None,
        f"{label} is not strict UTC RFC3339",
    )
    try:
        parsed = datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise RecoveryError(f"{label} calendar date is invalid") from error
    require(parsed.tzinfo == datetime.timezone.utc, f"{label} timezone changed")
    return parsed


def ci_summary_projection(ci: dict[str, Any]) -> dict[str, Any]:
    keys = {
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
    }
    return {key: ci[key] for key in keys}


def codeql_summary_projection(codeql: dict[str, Any]) -> dict[str, Any]:
    keys = {
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
    }
    return {key: codeql[key] for key in keys}


def validate_alert_state(value: Any) -> dict[str, Any]:
    keys = {
        "baseline_alert_numbers",
        "dismissed",
        "dismissed_alert_numbers",
        "fixed",
        "fixed_alert_numbers",
        "maximum_alert_number",
        "minimum_alert_number",
        "new_alert_numbers",
        "observed_alert_numbers",
        "observed_new_alerts",
        "open",
        "open_alert_numbers",
        "total",
    }
    state = exact_keys(value, keys, "CodeQL alert state")
    for key in (
        "baseline_alert_numbers",
        "dismissed_alert_numbers",
        "fixed_alert_numbers",
        "new_alert_numbers",
        "observed_alert_numbers",
        "open_alert_numbers",
    ):
        numbers = state[key]
        require(
            isinstance(numbers, list)
            and all(type(number) is int and number > 0 for number in numbers)
            and numbers == sorted(set(numbers)),
            f"CodeQL alert list changed: {key}",
        )
    require(
        state["new_alert_numbers"] == []
        and state["observed_new_alerts"] == 0
        and state["observed_alert_numbers"] == state["baseline_alert_numbers"]
        and state["open"] == len(state["open_alert_numbers"])
        and state["dismissed"] == len(state["dismissed_alert_numbers"])
        and state["fixed"] == len(state["fixed_alert_numbers"])
        and state["total"] == len(state["observed_alert_numbers"])
        and set(state["open_alert_numbers"])
        | set(state["dismissed_alert_numbers"])
        | set(state["fixed_alert_numbers"])
        == set(state["observed_alert_numbers"]),
        "CodeQL alert-state counts/sets changed",
    )
    alert_partitions = (
        set(state["open_alert_numbers"]),
        set(state["dismissed_alert_numbers"]),
        set(state["fixed_alert_numbers"]),
    )
    require(
        all(
            not left & right
            for index, left in enumerate(alert_partitions)
            for right in alert_partitions[index + 1 :]
        ),
        "CodeQL alert categories overlap",
    )
    observed = state["observed_alert_numbers"]
    exact_int(state["minimum_alert_number"], "CodeQL minimum alert number", 1)
    exact_int(state["maximum_alert_number"], "CodeQL maximum alert number", 1)
    require(
        state["minimum_alert_number"] == min(observed)
        and state["maximum_alert_number"] == max(observed),
        "CodeQL alert bounds changed",
    )
    return state


def validate_codeql_analyses(
    value: Any, jobs: list[dict[str, Any]], *, head: str = CORRECTION
) -> list[dict[str, Any]]:
    require(
        isinstance(value, list) and len(value) == 4, "CodeQL analysis count changed"
    )
    keys = {
        "analysis_id",
        "category",
        "commit_sha",
        "conclusion",
        "error",
        "job_id",
        "language",
        "no_new_alerts_observed",
        "ref",
        "results_count",
        "rules_count",
        "status",
        "warning",
    }
    analyses: list[dict[str, Any]] = []
    for raw in value:
        row = exact_keys(raw, keys, "CodeQL analysis")
        require(
            row["language"] in {"actions", "javascript-typescript", "python", "rust"}
            and row["commit_sha"] == head
            and row["ref"] == "refs/heads/main"
            and row["status"] == "completed"
            and row["conclusion"] == "success"
            and row["no_new_alerts_observed"] is True
            and row["error"] == row["warning"] == "",
            "CodeQL analysis lifecycle/head changed",
        )
        exact_int(row["job_id"], "CodeQL analysis job id", 1)
        exact_int(row["analysis_id"], "CodeQL analysis id", 1)
        exact_int(row["results_count"], "CodeQL result count")
        exact_int(row["rules_count"], "CodeQL rules count", 1)
        analyses.append(row)
    job_names_by_id = {row["job_id"]: row["name"] for row in jobs}
    require(
        [row["language"] for row in analyses]
        == ["actions", "javascript-typescript", "python", "rust"]
        and [row["analysis_id"] for row in analyses]
        == sorted({row["analysis_id"] for row in analyses})
        and {row["job_id"] for row in analyses} == {row["job_id"] for row in jobs},
        "CodeQL analysis language/job projection changed",
    )
    require(
        all(
            row["category"] == f"/language:{row['language']}"
            and job_names_by_id[row["job_id"]] == f"Analyze ({row['language']})"
            for row in analyses
        ),
        "CodeQL analysis language/category/job identity changed",
    )
    return analyses


def validate_negative(value: Any) -> dict[str, Any]:
    root = exact_keys(value, HOSTED_NEGATIVE_ROOT_KEYS, "correction hosted negative")
    require_named_field_paths(root, "revision", set(), "correction hosted negative")
    require_named_field_paths(
        root,
        "schema_revision",
        {("schema_revision",)},
        "correction hosted negative",
    )
    exact_int(root["schema_revision"], "correction negative schema revision", 1)
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-custody-correction-ci-failure/v1"
        and root["schema_revision"] == 1
        and root["repository"] == "sepahead/pid-rs"
        and root["subject"]
        == {
            "correction_commit": CORRECTION,
            "direct_parent": IMPLEMENTATION,
            "implementation_commit": IMPLEMENTATION,
            "tree": CORRECTION_TREE,
        },
        "correction negative identity changed",
    )
    require(
        root["negative_semantics"] == list(CORRECTION_NEGATIVE_SEMANTICS)
        and root["nonimplications"] == list(CORRECTION_NEGATIVE_NONIMPLICATIONS),
        "correction negative semantics/nonimplications changed",
    )
    ci = exact_keys(
        root["ci_failure"],
        {
            "all_jobs_successful",
            "api_captures",
            "artifact_contents_projection",
            "artifact_inventory",
            "artifact_inventory_projection",
            "attempt",
            "conclusion",
            "failed_diagnostics",
            "failed_job_count",
            "head_sha",
            "head_tree",
            "job_roster",
            "job_roster_projection",
            "jobs_successful",
            "jobs_total",
            "pagination_complete",
            "postcommit_source_state_v2",
            "ref",
            "repository",
            "retained_negative_evidence",
            "run_id",
            "runner_authenticity_claimed",
            "source_event",
            "status",
            "success_credit",
            "workflow",
            "workflow_path",
        },
        "correction CI failure",
    )
    codeql = exact_keys(
        root["codeql_success"],
        {
            "alert_state",
            "all_jobs_successful",
            "analysis_roster",
            "analysis_roster_projection",
            "api_captures",
            "attempt",
            "conclusion",
            "head_sha",
            "head_tree",
            "job_roster",
            "job_roster_projection",
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
        },
        "correction CodeQL success",
    )
    jobs_total = exact_int(ci["jobs_total"], "failed CI total", 1)
    jobs_successful = exact_int(ci["jobs_successful"], "failed CI successes")
    failed_jobs = exact_int(ci["failed_job_count"], "failed CI failed count", 1)
    require(
        ci["run_id"] == 31724449805
        and ci["attempt"] == 1
        and ci["head_sha"] == CORRECTION
        and ci["head_tree"] == CORRECTION_TREE
        and ci["ref"] == "refs/heads/main"
        and ci["repository"] == "sepahead/pid-rs"
        and ci["source_event"] == "push"
        and ci["workflow"] == "CI"
        and ci["workflow_path"] == ".github/workflows/ci.yml"
        and ci["status"] == "completed"
        and ci["conclusion"] == "failure"
        and ci["all_jobs_successful"] is False
        and ci["pagination_complete"] is True
        and ci["runner_authenticity_claimed"] is False
        and ci["retained_negative_evidence"] is True
        and ci["success_credit"] == "none"
        and (jobs_total, jobs_successful, failed_jobs) == (45, 43, 2)
        and jobs_successful + failed_jobs == jobs_total,
        "terminal correction CI observation changed",
    )
    roster = validate_hosted_jobs(ci["job_roster"], "CI", 45)
    failed_rows = [row for row in roster if row["conclusion"] == "failure"]
    require(
        [(row["job_id"], row["name"]) for row in failed_rows]
        == [
            (94529230276, "Exact-count directed-rounding SxPID2 reference"),
            (94529230323, "KSG integer-harmonic arithmetic and phase isolation"),
        ],
        "failed CI job identities changed",
    )
    validate_projection_binding(
        ci["job_roster_projection"],
        roster,
        "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "CI job roster projection",
        entry_count=45,
    )
    inventory = ci["artifact_inventory"]
    require(
        isinstance(inventory, list) and len(inventory) == 3,
        "artifact inventory count changed",
    )
    for row in inventory:
        exact_keys(
            row,
            {
                "artifact_id",
                "created_at",
                "expired",
                "expires_at",
                "name",
                "size_in_bytes",
                "updated_at",
            },
            "artifact inventory row",
        )
        require(row["expired"] is False, "retained artifact unexpectedly expired")
    require(
        [row["artifact_id"] for row in inventory]
        == [9190701644, 9190731526, 9190753799]
        and [row["name"] for row in inventory]
        == [
            "workspace-sbom",
            f"post-commit-source-state-v2-{CORRECTION}",
            "coverage-lcov",
        ],
        "artifact inventory identities changed",
    )
    validate_projection_binding(
        ci["artifact_inventory_projection"],
        inventory,
        "canonical compact sorted-key ASCII JSON plus LF over artifact-id-sorted rows",
        "artifact inventory projection",
    )

    boundary = exact_keys(
        root["capture_boundary"],
        {
            "api_responses",
            "artifact_contents",
            "authentication_claimed",
            "causation_claimed",
            "failed_log_captures",
            "provider",
            "trusted_time_claimed",
        },
        "negative capture boundary",
    )
    require(
        boundary["provider"] == "github_actions"
        and boundary["authentication_claimed"] is False
        and boundary["causation_claimed"] is False
        and boundary["trusted_time_claimed"] is False,
        "negative capture boundary weakened",
    )
    contents = boundary["artifact_contents"]
    require(
        isinstance(contents, list) and len(contents) == 3,
        "artifact contents count changed",
    )
    for row in contents:
        exact_keys(
            row,
            {
                "archive_sha256",
                "archive_size_bytes",
                "artifact_id",
                "members",
                "name",
                "repetitions_equal",
            },
            "artifact content row",
        )
        sha256(row["archive_sha256"], "artifact archive digest")
        exact_int(row["archive_size_bytes"], "artifact archive size", 1)
        require(
            row["repetitions_equal"] is True
            and isinstance(row["members"], list)
            and row["members"],
            "artifact content capture changed",
        )
        for member in row["members"]:
            exact_keys(member, {"path", "sha256", "size_bytes"}, "artifact member")
            validate_path(member["path"])
            sha256(member["sha256"], "artifact member digest")
            exact_int(member["size_bytes"], "artifact member size", 1)
        require(
            [member["path"] for member in row["members"]]
            == sorted({member["path"] for member in row["members"]}),
            "artifact members not path-sorted unique",
        )
    require(
        [row["artifact_id"] for row in contents] == [9190701644, 9190731526, 9190753799]
        and [
            (
                row["artifact_id"],
                row["name"],
                row["archive_size_bytes"],
                row["archive_sha256"],
            )
            for row in contents
        ]
        == [
            (
                9190701644,
                "workspace-sbom",
                22405,
                "d88a652a5174484e6b7238fd47c1a6a3b69ea0297e3fc4d8b3b9c5f03b74bf06",
            ),
            (
                9190731526,
                f"post-commit-source-state-v2-{CORRECTION}",
                1448,
                "3d093b4cb2bc545ec7a6d8588dd003d83ccb7d1e2f614aea815b9317ae1e6649",
            ),
            (
                9190753799,
                "coverage-lcov",
                259874,
                "830a8e7e648d9fad06061e4e779741fa62998d7ec5f4577703f26bc8a3054e31",
            ),
        ],
        "artifact archive identities changed",
    )
    validate_projection_binding(
        ci["artifact_contents_projection"],
        contents,
        "canonical compact sorted-key ASCII JSON plus LF over artifact-id-sorted archives with path-sorted member rows",
        "artifact contents projection",
    )
    postcommit = exact_keys(
        ci["postcommit_source_state_v2"],
        {
            "artifact_id",
            "content_sha256",
            "content_size_bytes",
            "name",
            "sha256",
            "size_bytes",
        },
        "postcommit source-state artifact",
    )
    require(
        postcommit
        == {
            "artifact_id": 9190731526,
            "content_sha256": "384e01a0b3ab723b197b048b600aa3e7fd6a2b52c7802078fee2ad0230304ca4",
            "content_size_bytes": 2809,
            "name": f"post-commit-source-state-v2-{CORRECTION}",
            "sha256": "3d093b4cb2bc545ec7a6d8588dd003d83ccb7d1e2f614aea815b9317ae1e6649",
            "size_bytes": 1448,
        }
        and contents[1]["members"]
        == [
            {
                "path": "pid-rs-post-commit-source-state-v2.json",
                "sha256": postcommit["content_sha256"],
                "size_bytes": postcommit["content_size_bytes"],
            }
        ],
        "postcommit source-state artifact/content cross-binding changed",
    )

    diagnostics = ci["failed_diagnostics"]
    require(
        isinstance(diagnostics, list) and len(diagnostics) == 2,
        "failed diagnostic count changed",
    )
    expected_diagnostics = (
        (
            94529230276,
            "Exact-count directed-rounding SxPID2 reference",
            24,
            "Run python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
            "SelfTestError",
            "cannot read the fixed cb3f certified-checker authority",
            "a58955e29a2a8cde17e348be972de5399a2f3b1a4d19bff57b3c45e93838331d",
            130747,
        ),
        (
            94529230323,
            "KSG integer-harmonic arithmetic and phase isolation",
            10,
            "Verify the KSG M1a hosted-custody correction lifecycle",
            "not_observed_in_terminal_log",
            "KSG M1a custody-correction self-test failed: accepted vector failed: certified_protocol: b''",
            "8af0b59d7960791b7162f7d4faa2c8a6084474ef5d816804dfd430514a886c8d",
            112382,
        ),
    )
    for diagnostic, expected in zip(diagnostics, expected_diagnostics, strict=True):
        item = exact_keys(
            diagnostic,
            {
                "exception_class",
                "exception_message",
                "job_id",
                "job_name",
                "raw_log",
                "step_name",
                "step_number",
                "traceback_projection",
            },
            "failed diagnostic",
        )
        raw_log = exact_keys(
            item["raw_log"],
            {"repetitions_equal", "sha256", "size_bytes", "truncated"},
            "failed diagnostic raw log",
        )
        trace = exact_keys(
            item["traceback_projection"],
            {"encoding", "sha256", "size_bytes", "text"},
            "failed diagnostic traceback",
        )
        require(
            (
                item["job_id"],
                item["job_name"],
                item["step_number"],
                item["step_name"],
                item["exception_class"],
                item["exception_message"],
                raw_log["sha256"],
                raw_log["size_bytes"],
            )
            == expected
            and raw_log["repetitions_equal"] is True
            and raw_log["truncated"] is False
            and isinstance(trace["encoding"], str)
            and isinstance(trace["text"], str)
            and trace["text"].endswith("\n")
            and trace["sha256"]
            == hashlib.sha256(trace["text"].encode("utf-8")).hexdigest()
            and trace["size_bytes"] == len(trace["text"].encode("utf-8")),
            "failed diagnostic identity/projection changed",
        )
        failure = next(row for row in failed_rows if row["job_id"] == item["job_id"])
        failed_steps = [
            step for step in failure["steps"] if step["conclusion"] == "failure"
        ]
        require(
            len(failed_steps) == 1
            and (failed_steps[0]["number"], failed_steps[0]["name"])
            == (item["step_number"], item["step_name"]),
            "failed diagnostic does not bind exact roster step",
        )

    log_captures = boundary["failed_log_captures"]
    require(
        isinstance(log_captures, list) and len(log_captures) == 2,
        "failed log capture count changed",
    )
    for diagnostic, capture in zip(diagnostics, log_captures, strict=True):
        row = exact_keys(
            capture,
            {
                "capture_command",
                "diagnostic_projection",
                "format",
                "job_id",
                "repetitions_equal",
                "sha256",
                "size_bytes",
            },
            "failed log capture",
        )
        projection = exact_keys(
            row["diagnostic_projection"],
            {"diagnostic_line", "encoding", "sha256", "size_bytes"},
            "failed log diagnostic projection",
        )
        raw = projection["diagnostic_line"].encode("utf-8")
        require(
            row["job_id"] == diagnostic["job_id"]
            and row["capture_command"]
            == f"gh api repos/sepahead/pid-rs/actions/jobs/{row['job_id']}/logs"
            and row["format"] == "github-actions-job-log-raw-response-bytes/v1"
            and row["repetitions_equal"] is True
            and row["sha256"] == diagnostic["raw_log"]["sha256"]
            and row["size_bytes"] == diagnostic["raw_log"]["size_bytes"]
            and projection["sha256"] == hashlib.sha256(raw).hexdigest()
            and projection["size_bytes"] == len(raw)
            and isinstance(projection["encoding"], str),
            "failed log capture/diagnostic cross-binding changed",
        )

    ci_capture_projections = {
        "ci_artifact_inventory": inventory,
        "ci_job_step_roster": roster,
        "ci_run_summary": ci_summary_projection(ci),
    }
    require(
        [item.get("endpoint_class") for item in ci["api_captures"]]
        == sorted(ci_capture_projections),
        "CI capture endpoint inventory changed",
    )
    for capture, endpoint in zip(
        ci["api_captures"], sorted(ci_capture_projections), strict=True
    ):
        validate_api_capture(
            capture, endpoint, ci_capture_projections[endpoint], "CI API"
        )

    require(
        codeql["run_id"] == 31724449083
        and codeql["attempt"] == 1
        and codeql["head_sha"] == CORRECTION
        and codeql["head_tree"] == CORRECTION_TREE
        and codeql["repository"] == "sepahead/pid-rs"
        and codeql["ref"] == "refs/heads/main"
        and codeql["source_event"] == "dynamic"
        and codeql["workflow"] == "CodeQL"
        and codeql["status"] == "completed"
        and codeql["conclusion"] == "success"
        and codeql["all_jobs_successful"] is True
        and codeql["jobs_total"] == codeql["jobs_successful"] == 4
        and codeql["new_alerts"] == 0
        and codeql["pagination_complete"] is True
        and codeql["runner_authenticity_claimed"] is False,
        "correction CodeQL observation changed",
    )
    codeql_jobs = validate_hosted_jobs(
        codeql["job_roster"], "CodeQL", 4, require_success=True
    )
    require(
        all(row["conclusion"] == "success" for row in codeql_jobs),
        "CodeQL job not successful",
    )
    validate_projection_binding(
        codeql["job_roster_projection"],
        codeql_jobs,
        "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "CodeQL job projection",
        entry_count=4,
    )
    analyses = validate_codeql_analyses(codeql["analysis_roster"], codeql_jobs)
    validate_projection_binding(
        codeql["analysis_roster_projection"],
        analyses,
        "canonical compact sorted-key ASCII JSON plus LF over analysis-id-sorted rows",
        "CodeQL analysis projection",
        entry_count=4,
    )
    alerts = validate_alert_state(codeql["alert_state"])
    codeql_capture_projections = {
        "codeql_alert_state": alerts,
        "codeql_job_analysis_roster": {"analyses": analyses, "jobs": codeql_jobs},
        "codeql_run_summary": codeql_summary_projection(codeql),
    }
    require(
        [item.get("endpoint_class") for item in codeql["api_captures"]]
        == sorted(codeql_capture_projections),
        "CodeQL capture endpoint inventory changed",
    )
    for capture, endpoint in zip(
        codeql["api_captures"], sorted(codeql_capture_projections), strict=True
    ):
        validate_api_capture(
            capture, endpoint, codeql_capture_projections[endpoint], "CodeQL API"
        )
    all_captures = ci["api_captures"] + codeql["api_captures"]
    require(
        boundary["api_responses"]
        == sorted(all_captures, key=lambda row: row["endpoint_class"]),
        "boundary API responses do not byte-deep equal CI/CodeQL captures",
    )
    return {
        "ci_run_id": 31724449805,
        "codeql_run_id": 31724449083,
        "failed_jobs": failed_jobs,
        "jobs": jobs_total,
    }


def validate_legacy_hosted_artifact(
    value: Any, head: str, label: str
) -> dict[str, Any]:
    item = exact_keys(
        value,
        {
            "artifact_id",
            "content_sha256",
            "content_size_bytes",
            "name",
            "sha256",
            "size_bytes",
        },
        label,
    )
    exact_int(item["artifact_id"], f"{label} id", 1)
    exact_int(item["content_size_bytes"], f"{label} content size", 1)
    exact_int(item["size_bytes"], f"{label} archive size", 1)
    sha256(item["content_sha256"], f"{label} content digest")
    sha256(item["sha256"], f"{label} archive digest")
    require(
        item["name"] == f"post-commit-source-state-v2-{head}",
        f"{label} head/name changed",
    )
    return item


def validate_postcommit_source_state_content(
    value: Any,
    head: str,
    tree: str,
    *,
    expected_manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes]:
    content = exact_keys(
        value,
        {
            "binding",
            "checks",
            "determinism",
            "evidence_class",
            "generated_by",
            "nonimplications",
            "repository",
            "schema",
            "schema_revision",
        },
        "recovery postcommit source-state content",
    )
    binding = exact_keys(
        content["binding"],
        {"commit_oid", "git_object_format", "manifest", "tree_oid"},
        "recovery postcommit binding",
    )
    manifest = exact_keys(
        binding["manifest"],
        {
            "blob_oid",
            "path",
            "schema",
            "schema_revision",
            "sha256",
            "size_bytes",
            "source_projection_entries_sha256",
            "source_projection_entry_count",
        },
        "recovery postcommit manifest binding",
    )
    require_named_field_paths(
        content, "revision", set(), "recovery postcommit source-state content"
    )
    require_named_field_paths(
        content,
        "schema_revision",
        {("schema_revision",), ("binding", "manifest", "schema_revision")},
        "recovery postcommit source-state content",
    )
    sha1(manifest["blob_oid"], "recovery postcommit manifest blob")
    sha256(manifest["sha256"], "recovery postcommit manifest digest")
    sha256(
        manifest["source_projection_entries_sha256"],
        "recovery postcommit source projection digest",
    )
    exact_int(manifest["size_bytes"], "recovery postcommit manifest size", 1)
    exact_int(manifest["schema_revision"], "recovery postcommit manifest revision", 1)
    exact_int(
        manifest["source_projection_entry_count"],
        "recovery postcommit source projection count",
        1,
    )
    exact_int(content["schema_revision"], "recovery postcommit schema revision", 1)
    checks = exact_keys(
        content["checks"],
        {
            "current_manifest_checker_passed",
            "head_tree_matches_index",
            "manifest_is_tracked_head_blob",
            "post_commit_checker_is_tracked_head_blob",
            "post_commit_schema_is_tracked_head_blob",
            "repeated_endpoint_observations_match",
            "repository_visible_untracked_paths",
            "self_excluding_projection_matches_head_tree",
            "tracked_worktree_matches_head",
        },
        "recovery postcommit checks",
    )
    require(
        binding["commit_oid"] == head
        and binding["git_object_format"] == "sha1"
        and binding["tree_oid"] == tree
        and manifest["path"] == CURRENT_SOURCE_RELATIVE
        and manifest["schema"] == "pid-rs/current-source-state"
        and manifest["schema_revision"] == 1
        and checks
        == {
            "current_manifest_checker_passed": True,
            "head_tree_matches_index": True,
            "manifest_is_tracked_head_blob": True,
            "post_commit_checker_is_tracked_head_blob": True,
            "post_commit_schema_is_tracked_head_blob": True,
            "repeated_endpoint_observations_match": True,
            "repository_visible_untracked_paths": [],
            "self_excluding_projection_matches_head_tree": True,
            "tracked_worktree_matches_head": True,
        }
        and content["determinism"]
        == {
            "artifact_transport": "canonical_json_stdout_or_stdin_only",
            "commit_cycle": "none; the committed manifest excludes itself and this artifact is generated only after commit",
            "generated_at": "omitted_for_determinism",
            "storage_custody": "caller_owned_not_bound_by_this_artifact",
        }
        and content["evidence_class"] == "post_commit_identity_evidence_only"
        and content["generated_by"] == "scripts/check-post-commit-source-state-v2.py"
        and content["nonimplications"] == list(POST_COMMIT_NONIMPLICATIONS)
        and content["repository"] == "sepahead/pid-rs"
        and content["schema"] == "pid-rs/post-commit-source-state"
        and content["schema_revision"] == 2,
        "recovery postcommit content constants/checks changed",
    )
    if expected_manifest is not None:
        require(
            manifest == expected_manifest,
            "recovery postcommit content does not bind the recovery tree manifest",
        )
    return content, canonical_json(content, pretty=True)


def recovery_current_manifest_descriptor(entries: dict[str, Entry]) -> dict[str, Any]:
    manifest_entry = entries.get(CURRENT_SOURCE_RELATIVE)
    require(manifest_entry is not None, "recovery current-source manifest is absent")
    raw = tree_blob(entries, CURRENT_SOURCE_RELATIVE)
    manifest = parse_json(raw, "recovery current-source manifest")
    exact_keys(manifest, CURRENT_SOURCE_ROOT_KEYS, "recovery current-source manifest")
    binding = exact_keys(
        manifest["binding"],
        {
            "commit_binding",
            "excluded_paths",
            "generated_at",
            "projection_algorithm",
            "scope_kind",
        },
        "recovery current-source binding",
    )
    projection = exact_keys(
        manifest["source_projection"],
        {"entries", "entries_sha256", "entry_count"},
        "recovery current-source projection",
    )
    validate_current_source_revision_contract(manifest, "recovery current-source")
    expected_rows: list[dict[str, Any]] = []
    for path, entry in entries.items():
        if path == CURRENT_SOURCE_RELATIVE:
            continue
        blob = tree_blob(entries, path)
        expected_rows.append(
            {
                "git_mode": entry.mode,
                "path": path,
                "sha256": hashlib.sha256(blob).hexdigest(),
                "size_bytes": len(blob),
            }
        )
    compact_rows = canonical_json(expected_rows, pretty=False)[:-1]
    require(
        binding["commit_binding"]
        == "not_self_asserted; resolve the manifest blob's containing commit from Git"
        and binding["excluded_paths"] == [CURRENT_SOURCE_RELATIVE]
        and binding["generated_at"] == "omitted_for_determinism"
        and binding["scope_kind"] == "self_excluding_worktree_source_projection"
        and isinstance(binding["projection_algorithm"], str)
        and bool(binding["projection_algorithm"])
        and manifest["generated_by"] == CURRENT_SOURCE_CHECKER
        and manifest["repository"] == "sepahead/pid-rs"
        and manifest["schema"] == "pid-rs/current-source-state"
        and manifest["schema_revision"] == 1
        and projection["entries"] == expected_rows
        and projection["entry_count"] == len(expected_rows)
        and projection["entries_sha256"] == hashlib.sha256(compact_rows).hexdigest(),
        "recovery current-source manifest does not project the recovery tree",
    )
    return {
        "blob_oid": manifest_entry.oid,
        "path": CURRENT_SOURCE_RELATIVE,
        "schema": "pid-rs/current-source-state",
        "schema_revision": 1,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "source_projection_entries_sha256": projection["entries_sha256"],
        "source_projection_entry_count": projection["entry_count"],
    }


def validate_recovery_ci_success(value: Any, head: str, tree: str) -> dict[str, Any]:
    ci = exact_keys(
        value,
        {
            "all_jobs_successful",
            "api_captures",
            "attempt",
            "conclusion",
            "failed_diagnostic",
            "failed_job_count",
            "head_sha",
            "head_tree",
            "job_roster",
            "job_roster_projection",
            "jobs_successful",
            "jobs_total",
            "pagination_complete",
            "postcommit_source_state_v2",
            "postcommit_source_state_v2_content",
            "ref",
            "repository",
            "retained_negative_evidence",
            "run_id",
            "runner_authenticity_claimed",
            "source_event",
            "status",
            "success_credit",
            "workflow",
            "workflow_path",
        },
        "recovery CI success",
    )
    require(
        ci["all_jobs_successful"] is True
        and exact_int(ci["attempt"], "recovery CI attempt", 1) == 1
        and ci["conclusion"] == "success"
        and ci["failed_diagnostic"] is None
        and ci["failed_job_count"] == 0
        and ci["head_sha"] == head
        and ci["head_tree"] == tree
        and ci["jobs_successful"] == ci["jobs_total"] == 45
        and ci["pagination_complete"] is True
        and ci["ref"] == "refs/heads/main"
        and ci["repository"] == "sepahead/pid-rs"
        and ci["retained_negative_evidence"] is False
        and exact_int(ci["run_id"], "recovery CI run id", 1)
        not in {31686107959, 31724449805}
        and ci["runner_authenticity_claimed"] is False
        and ci["source_event"] == "push"
        and ci["status"] == "completed"
        and ci["success_credit"] == "hosted_success_observation_only"
        and ci["workflow"] == "CI"
        and ci["workflow_path"] == ".github/workflows/ci.yml",
        "recovery CI identity/lifecycle changed",
    )
    jobs = validate_hosted_jobs(
        ci["job_roster"], "recovery CI", 45, require_success=True
    )
    require(
        all(row["conclusion"] == "success" for row in jobs),
        "recovery CI has a non-success job",
    )
    validate_projection_binding(
        ci["job_roster_projection"],
        jobs,
        "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "recovery CI job projection",
        entry_count=45,
    )
    artifact = validate_legacy_hosted_artifact(
        ci["postcommit_source_state_v2"], head, "recovery CI postcommit artifact"
    )
    content, content_raw = validate_postcommit_source_state_content(
        ci["postcommit_source_state_v2_content"], head, tree
    )
    require(
        artifact["content_sha256"] == hashlib.sha256(content_raw).hexdigest()
        and artifact["content_size_bytes"] == len(content_raw),
        "recovery CI legacy descriptor does not bind the canonical content bytes",
    )
    captures = ci["api_captures"]
    require(
        isinstance(captures, list)
        and len(captures) == 3
        and all(isinstance(item, dict) for item in captures)
        and [item.get("endpoint_class") for item in captures]
        == [
            "ci_job_step_roster",
            "ci_run_summary",
            "postcommit_source_state_v2_content",
        ],
        "recovery CI capture inventory/order changed",
    )
    validate_api_capture(
        captures[0],
        "ci_job_step_roster",
        jobs,
        "recovery CI API",
        fixed_correction=False,
    )
    validate_api_capture(
        captures[1],
        "ci_run_summary",
        ci_summary_projection(ci),
        "recovery CI API",
        fixed_correction=False,
    )
    validate_api_capture(
        captures[2],
        "postcommit_source_state_v2_content",
        content,
        "recovery CI API",
        fixed_correction=False,
    )
    return {"artifact": artifact, "content": content, "jobs": jobs}


def validate_recovery_codeql_success(
    value: Any,
    head: str,
    tree: str,
    *,
    baseline_alert_numbers: list[int],
) -> dict[str, Any]:
    codeql = exact_keys(
        value,
        {
            "alert_state",
            "all_jobs_successful",
            "analysis_roster",
            "analysis_roster_projection",
            "api_captures",
            "attempt",
            "conclusion",
            "head_sha",
            "head_tree",
            "job_roster",
            "job_roster_projection",
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
        },
        "recovery CodeQL success",
    )
    require(
        codeql["all_jobs_successful"] is True
        and exact_int(codeql["attempt"], "recovery CodeQL attempt", 1) == 1
        and codeql["conclusion"] == "success"
        and codeql["head_sha"] == head
        and codeql["head_tree"] == tree
        and codeql["jobs_successful"] == codeql["jobs_total"] == 4
        and codeql["new_alerts"] == 0
        and codeql["pagination_complete"] is True
        and codeql["ref"] == "refs/heads/main"
        and codeql["repository"] == "sepahead/pid-rs"
        and exact_int(codeql["run_id"], "recovery CodeQL run id", 1)
        not in {31686106737, 31724449083}
        and codeql["runner_authenticity_claimed"] is False
        and codeql["source_event"] == "dynamic"
        and codeql["status"] == "completed"
        and codeql["workflow"] == "CodeQL",
        "recovery CodeQL identity/lifecycle changed",
    )
    jobs = validate_hosted_jobs(
        codeql["job_roster"], "recovery CodeQL", 4, require_success=True
    )
    require(
        all(row["conclusion"] == "success" for row in jobs),
        "recovery CodeQL job not successful",
    )
    validate_projection_binding(
        codeql["job_roster_projection"],
        jobs,
        "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps",
        "recovery CodeQL job projection",
        entry_count=4,
    )
    analyses = validate_codeql_analyses(codeql["analysis_roster"], jobs, head=head)
    validate_projection_binding(
        codeql["analysis_roster_projection"],
        analyses,
        "canonical compact sorted-key ASCII JSON plus LF over analysis-id-sorted rows",
        "recovery CodeQL analysis projection",
        entry_count=4,
    )
    alerts = validate_alert_state(codeql["alert_state"])
    require(
        alerts["baseline_alert_numbers"] == baseline_alert_numbers
        and alerts["observed_new_alerts"]
        == codeql["new_alerts"]
        == len(alerts["new_alert_numbers"]),
        "recovery CodeQL alert baseline/new-count changed",
    )
    projections = {
        "codeql_alert_state": alerts,
        "codeql_job_analysis_roster": {"analyses": analyses, "jobs": jobs},
        "codeql_run_summary": codeql_summary_projection(codeql),
    }
    captures = codeql["api_captures"]
    require(
        isinstance(captures, list)
        and len(captures) == 3
        and all(isinstance(item, dict) for item in captures)
        and [item.get("endpoint_class") for item in captures] == sorted(projections),
        "recovery CodeQL capture inventory/order changed",
    )
    for capture, endpoint in zip(captures, sorted(projections), strict=True):
        validate_api_capture(
            capture,
            endpoint,
            projections[endpoint],
            "recovery CodeQL API",
            fixed_correction=False,
        )
    return {"analyses": analyses, "alerts": alerts, "jobs": jobs}


def validate_replay(candidate: dict[str, Entry]) -> dict[str, str]:
    r6 = tree_blob(candidate, R6_RELATIVE)
    require(
        len(r6) == 126_143 and hashlib.sha256(r6).hexdigest() == R6_SHA256, "r6 changed"
    )
    r7 = tree_blob(candidate, R7_RELATIVE)
    require(
        len(r7) == 127_246 and hashlib.sha256(r7).hexdigest() == R7_SHA256,
        "r7 changed",
    )
    r8 = tree_blob(candidate, R8_RELATIVE)
    value = parse_json(r8, "Lean r8 replay")
    exact_keys(value, LEAN_V2_ROOT_KEYS, "Lean r8 replay")
    require(
        isinstance(value, dict)
        and value.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and value.get("status") == "passed",
        "Lean r8 replay identity/status changed",
    )
    validate_lean_v2_scalar_contract(value, "Lean r8 replay")
    prior = value.get("prior_replay_preservation_sha256")
    require(
        isinstance(prior, dict)
        and prior.get(R6_RELATIVE) == R6_SHA256
        and prior.get(R7_RELATIVE) == R7_SHA256,
        "Lean r8 does not preserve exact r6/r7",
    )
    operational = value.get("operational_wiring_sha256")
    lean_checker_raw = tree_blob(candidate, LEAN_CHECKER)
    lean_selftest_raw = tree_blob(candidate, LEAN_SELF_TEST)
    lean_generator_path = "scripts/generate-lean-4.33-replay.py"
    lean_generator_raw = tree_blob(candidate, lean_generator_path)
    lean_source = lean_checker_raw.decode("utf-8", errors="strict")
    lean_tree = ast.parse(lean_source, filename=f"<{LEAN_CHECKER}>")
    final_line = assignment_span(
        lean_source,
        lean_tree,
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256",
    )[0]
    require(
        lean_source.count(final_line) == 1,
        "Lean replay-projection assignment text is ambiguous",
    )
    replay_lean = lean_source.replace(
        final_line,
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
        1,
    ).encode("utf-8")
    operational_cut_node = mapping_value_node(
        lean_tree, "EXPECTED_OPERATIONAL_WIRING_HASHES", CHECKER_RELATIVE
    )
    operational_cut_text = node_text(
        lean_source, operational_cut_node, "Lean recovery-checker operational cut"
    )
    require(
        lean_source.count(operational_cut_text) == 1,
        "Lean recovery-checker operational cut text is absent/ambiguous",
    )
    normalized_lean_text = replay_lean.decode("utf-8").replace(
        operational_cut_text, "PENDING_OPERATIONAL_SHA256", 1
    )
    normalized_lean = normalized_lean_text.encode("utf-8")
    require(
        len(normalized_lean) == EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES
        and HEX64.fullmatch(EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256) is not None
        and hashlib.sha256(normalized_lean).hexdigest()
        == EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256,
        "normalized Lean r8 checker cut changed",
    )
    _operational_segment, expected_operational = assignment_span(
        lean_source, lean_tree, "EXPECTED_OPERATIONAL_WIRING_HASHES"
    )
    _prior_segment, expected_prior = assignment_span(
        lean_source, lean_tree, "PRESERVED_PRIOR_REPLAY_HASHES"
    )
    _prior_schema_segment, expected_prior_schemas = assignment_span(
        lean_source, lean_tree, "PRESERVED_PRIOR_REPLAY_SCHEMAS"
    )
    require(
        operational == expected_operational
        and prior == expected_prior
        and value["prior_replay_schema"] == expected_prior_schemas,
        "Lean r8 operational/prior authority differs from normalized checker",
    )
    forbidden_operational = {LEAN_CHECKER, LEAN_SELF_TEST, R8_RELATIVE}
    require(
        not (set(operational) & forbidden_operational)
        and not (set(operational) & set(prior))
        and R7_RELATIVE not in operational
        and CHECKER_RELATIVE in operational
        and SELF_TEST_RELATIVE in operational
        and lean_generator_path in operational,
        "Lean r8 operational inventory overlaps prior evidence, contains a cycle, or omits required paths",
    )
    for path, expected_digest in operational.items():
        validate_path(path)
        require(
            path in candidate
            and expected_digest
            == hashlib.sha256(tree_blob(candidate, path)).hexdigest(),
            f"Lean r8 full operational map digest mismatch: {path}",
        )
    for path, raw, size, digest_pin in (
        (
            LEAN_SELF_TEST,
            lean_selftest_raw,
            EXPECTED_FROZEN_LEAN_SELF_TEST_SIZE_BYTES,
            EXPECTED_FROZEN_LEAN_SELF_TEST_SHA256,
        ),
        (
            lean_generator_path,
            lean_generator_raw,
            EXPECTED_FROZEN_LEAN_GENERATOR_SIZE_BYTES,
            EXPECTED_FROZEN_LEAN_GENERATOR_SHA256,
        ),
    ):
        require(
            len(raw) == size
            and HEX64.fullmatch(digest_pin) is not None
            and hashlib.sha256(raw).hexdigest() == digest_pin,
            f"frozen Lean r8 authority changed: {path}",
        )
    required = {
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
        POLICY_RELATIVE,
        BOUNDARY_RELATIVE,
        NEGATIVE_RELATIVE,
        SCHEMA_RELATIVE,
        lean_generator_path,
    }
    require(
        isinstance(operational, dict) and required <= set(operational),
        "Lean r8 recovery map incomplete",
    )
    for path in required:
        require(
            operational[path] == hashlib.sha256(tree_blob(candidate, path)).hexdigest(),
            f"Lean r8 operational digest mismatch: {path}",
        )
    sha256(operational[CHECKER_RELATIVE], "Lean r8 recovery-checker cut")
    custody = value.get("custody_gate_sha256")
    replay_custody = value.get("replay_custody_gate_sha256")
    require(
        isinstance(custody, dict)
        and isinstance(replay_custody, dict)
        and tuple(custody) == tuple(replay_custody) == (LEAN_SELF_TEST, LEAN_CHECKER)
        and custody[LEAN_SELF_TEST] == hashlib.sha256(lean_selftest_raw).hexdigest()
        and custody[LEAN_CHECKER] == hashlib.sha256(lean_checker_raw).hexdigest()
        and replay_custody[LEAN_SELF_TEST] == custody[LEAN_SELF_TEST]
        and replay_custody[LEAN_CHECKER] == hashlib.sha256(replay_lean).hexdigest(),
        "Lean r8 final/replay two-cut custody changed",
    )
    digest = hashlib.sha256(r8).hexdigest()
    projected_receipt = dict(value)
    projected_receipt["custody_gate_sha256"] = {LEAN_SELF_TEST: custody[LEAN_SELF_TEST]}
    projection = hashlib.sha256(
        json.dumps(
            projected_receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _projection_segment, lean_projection_literal = assignment_span(
        lean_source,
        lean_tree,
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256",
    )
    require(
        lean_projection_literal == projection
        and operational[CHECKER_RELATIVE]
        == hashlib.sha256(tree_blob(candidate, CHECKER_RELATIVE)).hexdigest(),
        "Lean r8 operational checker/projection cut equations changed",
    )
    return {
        "prior_r6_sha256": R6_SHA256,
        "prior_r7_sha256": R7_SHA256,
        "receipt_sha256": digest,
        "replay_projection_sha256": projection,
    }


def fixed_temp_root() -> Path:
    root = Path("/tmp").resolve(strict=True)
    state = root.lstat()
    require(
        root.is_absolute()
        and stat.S_ISDIR(state.st_mode)
        and state.st_uid == 0
        and bool(state.st_mode & stat.S_ISVTX),
        "fixed temporary root custody changed",
    )
    return root


def read_absolute_regular(path: Path, maximum: int) -> tuple[bytes, tuple[int, ...]]:
    before_path = path.lstat()
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum,
            "absolute file invalid",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(bool(chunk), "absolute file short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "absolute file grew")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    require(
        stat_identity(before_path)
        == stat_identity(before)
        == stat_identity(after)
        == stat_identity(path.lstat()),
        "absolute file identity changed",
    )
    return b"".join(chunks), stat_identity(after)


PYTHON_SOURCE_BOOTSTRAP = """import hashlib
import sys
if not (sys.version_info >= (3, 11) and sys.flags.isolated == 1 and sys.flags.safe_path and sys.flags.no_site == 1 and sys.flags.ignore_environment == 1 and sys.dont_write_bytecode and sys.flags.optimize in {0, 1}):
    raise SystemExit("isolated source bootstrap runtime mismatch")
logical_path, expected_sha, expected_size = sys.argv[1], sys.argv[2], int(sys.argv[3], 10)
arguments = sys.argv[4:]
if expected_size < 1 or expected_size > 33554432:
    raise SystemExit("isolated source bootstrap size out of range")
source = sys.stdin.buffer.read(expected_size + 1)
if len(source) != expected_size or hashlib.sha256(source).hexdigest() != expected_sha:
    raise SystemExit("isolated source bootstrap bytes disagree")
sys.stdin = open("/dev/null", "r", encoding="utf-8")
sys.argv = [logical_path, *arguments]
namespace = {"__name__": "__main__", "__file__": logical_path, "__package__": None, "__spec__": None, "__cached__": None}
exec(compile(source, logical_path, "exec", dont_inherit=True), namespace, namespace)
"""


def run_candidate_python(
    candidate: dict[str, Entry], relative: str, arguments: tuple[str, ...], timeout: int
) -> subprocess.CompletedProcess[bytes]:
    require(
        relative
        in {
            CERT_CHECKER,
            CERT_SELF_TEST,
            LEAN_CHECKER,
            LEAN_SELF_TEST,
            CURRENT_SOURCE_CHECKER,
        },
        "unapproved child",
    )
    source = tree_blob(candidate, relative)
    require(
        hashlib.sha256(read_regular(relative)).digest()
        == hashlib.sha256(source).digest(),
        "child worktree/tree bytes differ",
    )
    resolved = Path(sys.executable).resolve(strict=True)
    interpreter, original_state = read_absolute_regular(resolved, MAX_INTERPRETER_BYTES)
    prefix = ("-O", "-I", "-S", "-B") if sys.flags.optimize == 1 else ("-I", "-S", "-B")
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-recovery-python-", dir=fixed_temp_root()
    ) as temporary:
        directory = Path(temporary)
        os.chmod(directory, 0o700)
        executable = directory / "python3"
        descriptor = os.open(
            executable,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o500,
        )
        try:
            view = memoryview(interpreter)
            while view:
                count = os.write(descriptor, view)
                require(count > 0, "private interpreter short write")
                view = view[count:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        private_raw, private_state = read_absolute_regular(
            executable, MAX_INTERPRETER_BYTES
        )
        require(
            private_raw == interpreter
            and stat.S_IMODE(executable.stat().st_mode) == 0o500,
            "private interpreter custody changed",
        )
        directory_state = directory.lstat()
        completed = subprocess.run(
            [
                os.fspath(executable),
                *prefix,
                "-c",
                PYTHON_SOURCE_BOOTSTRAP,
                os.fspath(ROOT / relative),
                hashlib.sha256(source).hexdigest(),
                str(len(source)),
                *arguments,
            ],
            cwd=ROOT,
            env=safe_environment(),
            input=source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        final_private, final_state = read_absolute_regular(
            executable, MAX_INTERPRETER_BYTES
        )
        require(
            final_private == private_raw
            and final_state == private_state
            and stat_identity(directory.lstat()) == stat_identity(directory_state),
            "private interpreter/directory changed",
        )
    final_original, final_original_state = read_absolute_regular(
        resolved, MAX_INTERPRETER_BYTES
    )
    require(
        final_original == interpreter and final_original_state == original_state,
        "source interpreter changed",
    )
    require(
        len(completed.stdout) <= MAX_GIT_BYTES
        and len(completed.stderr) <= MAX_GIT_BYTES,
        "child output exceeded bound",
    )
    return completed


def validate_children(candidate: dict[str, Entry]) -> tuple[dict[str, str], str]:
    outputs: dict[str, str] = {}
    for path, timeout in (
        (CERT_CHECKER, 300),
        (CERT_SELF_TEST, 900),
        (LEAN_CHECKER, 300),
        (LEAN_SELF_TEST, 900),
    ):
        completed = run_candidate_python(candidate, path, (), timeout)
        require(
            completed.returncode == 0 and completed.stderr == b"" and completed.stdout,
            f"child failed: {path}",
        )
        expected_size, expected_digest = EXPECTED_CHILD_STDOUT[path]
        observed_digest = hashlib.sha256(completed.stdout).hexdigest()
        require(
            expected_size > 0
            and len(completed.stdout) == expected_size
            and HEX64.fullmatch(expected_digest) is not None
            and observed_digest == expected_digest,
            f"frozen child stdout changed: {path}",
        )
        outputs[path] = observed_digest
    current = run_candidate_python(candidate, CURRENT_SOURCE_CHECKER, ("--emit",), 240)
    require(
        current.returncode == 0 and current.stderr == b"",
        "current-source generator failed",
    )
    manifest = tree_blob(candidate, CURRENT_SOURCE_RELATIVE)
    require(
        current.stdout == manifest,
        "current-source manifest does not equal bounded generator output",
    )
    digest = hashlib.sha256(manifest).hexdigest()
    return outputs, digest


def parse_index_listing(raw: bytes) -> dict[str, Entry]:
    require(not raw or raw.endswith(b"\0"), "index listing lacks NUL terminator")
    result: dict[str, Entry] = {}
    for record in raw[:-1].split(b"\0") if raw else []:
        prefix, tab, path_raw = record.partition(b"\t")
        fields = prefix.split(b" ")
        require(
            tab == b"\t" and len(fields) == 3 and fields[2] == b"0",
            "index record malformed",
        )
        mode, oid = fields[0].decode("ascii"), fields[1].decode("ascii")
        path = path_raw.decode("utf-8", errors="strict")
        validate_path(path)
        require(
            mode in {"100644", "100755"}
            and HEX40.fullmatch(oid) is not None
            and path not in result,
            "index entry invalid",
        )
        result[path] = Entry(mode, oid)
    require(list(result) == sorted(result), "index listing unsorted")
    return result


def write_private(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600
    )
    try:
        view = memoryview(raw)
        while view:
            count = os.write(descriptor, view)
            require(count > 0, "private file short write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_sealed_fd0() -> tuple[bytes, os.stat_result]:
    before = os.fstat(0)
    require(
        stat.S_ISREG(before.st_mode)
        and stat.S_IMODE(before.st_mode) == 0o400
        and before.st_nlink == 1
        and 0 < before.st_size <= MAX_INDEX_BYTES,
        "fd0 sealed index mode/link/size changed",
    )
    flags = fcntl.fcntl(0, fcntl.F_GETFL)
    require(
        flags & os.O_ACCMODE == os.O_RDONLY and os.lseek(0, 0, os.SEEK_CUR) == 0,
        "fd0 is not read-only at offset zero",
    )
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
        chunk = os.read(0, min(remaining, 1024 * 1024))
        require(bool(chunk), "fd0 short read")
        chunks.append(chunk)
        remaining -= len(chunk)
    require(os.read(0, 1) == b"", "fd0 grew")
    after = os.fstat(0)
    require(stat_identity(before) == stat_identity(after), "fd0 changed during read")
    return b"".join(chunks), before


def validate_sealed_index(
    raw: bytes,
    expected_sha: str,
    expected_count: int,
    tree: str,
    entries: dict[str, Entry],
) -> dict[str, Any]:
    require(
        hashlib.sha256(raw).hexdigest() == expected_sha, "sealed index digest mismatch"
    )
    results: list[tuple[str, dict[str, Entry]]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-recovery-index-", dir=fixed_temp_root()
    ) as temporary:
        for suffix in ("a", "b"):
            path = Path(temporary) / f"index-{suffix}"
            write_private(path, raw)
            environment = {"GIT_INDEX_FILE": os.fspath(path)}
            reconstructed = git_text("write-tree", extra_environment=environment)
            listing = git("ls-files", "--stage", "-z", extra_environment=environment)
            require(isinstance(listing, bytes), "index listing type changed")
            results.append((reconstructed, parse_index_listing(listing)))
    require(
        results[0] == results[1]
        and all(
            item_tree == tree and listed == entries and len(listed) == expected_count
            for item_tree, listed in results
        ),
        "sealed index does not reconstruct exact tree twice",
    )
    return {
        "entry_count": expected_count,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "retained_index_artifact": {
            "git_blob_oid_sha1": object_digest("blob", raw),
            "path": RECOVERY_RETAINED_INDEX,
            "sha256": expected_sha,
            "size_bytes": len(raw),
        },
        "sha256": expected_sha,
        "single_link": True,
        "size_bytes": len(raw),
    }


def repository_context() -> tuple[str, str]:
    require(
        SCRIPT == ROOT / CHECKER_RELATIVE and not SCRIPT.is_symlink(),
        "checker path is not canonical",
    )
    require(
        git_text("rev-parse", "--show-object-format") == "sha1",
        "repository object format changed",
    )
    require(
        Path(git_text("rev-parse", "--show-toplevel")).resolve(strict=True)
        == ROOT.resolve(strict=True),
        "repository root changed",
    )
    config_raw = git("config", "--local", "--name-only", "--null", "--list")
    require(isinstance(config_raw, bytes), "local config result type changed")
    require(
        not config_raw or config_raw.endswith(b"\0"),
        "local Git config key list lacks NUL termination",
    )
    config_keys = tuple(
        item.decode("utf-8", errors="strict").lower()
        for item in (config_raw[:-1].split(b"\0") if config_raw else ())
    )
    require(
        all(config_keys) and len(config_keys) == len(set(config_keys)),
        "local Git config keys are empty or duplicated",
    )
    require(
        git_text("rev-parse", "--is-shallow-repository") == "false",
        "shallow repository cannot establish exact ancestry custody",
    )
    require(
        all(
            key != "extensions.partialclone"
            and key != "core.excludesfile"
            and not (key.startswith("remote.") and key.endswith(".promisor"))
            and key != "include.path"
            and not (key.startswith("includeif.") and key.endswith(".path"))
            for key in config_keys
        ),
        "partial-clone/promisor/included local configuration is forbidden",
    )
    require(
        not git_text("for-each-ref", "--format=%(refname)", "refs/replace"),
        "replacement refs present",
    )
    git_dir = Path(git_text("rev-parse", "--absolute-git-dir"))
    require(not (git_dir / "info/grafts").exists(), "graft file present")
    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    require(
        HEX40.fullmatch(head) is not None and HEX40.fullmatch(tree) is not None,
        "HEAD/tree identity malformed",
    )
    return head, tree


def git_predicate(*arguments: str) -> bool:
    result = git(*arguments, check=False)
    require(isinstance(result, tuple) and result[0] in {0, 1}, "Git predicate error")
    return result[0] == 0


def decode_z(raw: bytes) -> tuple[str, ...]:
    require(not raw or raw.endswith(b"\0"), "path list lacks NUL")
    paths = (
        tuple(
            item.decode("utf-8", errors="strict")
            for item in raw[:-1].split(b"\0")
            if item
        )
        if raw
        else ()
    )
    for path in paths:
        validate_path(path)
    require(paths == tuple(sorted(set(paths))), "path list is not sorted unique")
    return paths


def lifecycle_branch() -> tuple[str | None, tuple[str, ...]]:
    result = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    require(
        isinstance(result, tuple) and result[0] in {0, 1},
        "symbolic-ref predicate failed",
    )
    branch = (
        result[1].decode("utf-8", errors="strict").rstrip("\n")
        if result[0] == 0
        else None
    )
    active: list[str] = []
    for name in (
        "MERGE_HEAD",
        "AUTO_MERGE",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "REBASE_HEAD",
        "BISECT_LOG",
        "rebase-apply",
        "rebase-merge",
        "sequencer",
    ):
        path = Path(git_text("rev-parse", "--git-path", name))
        if not path.is_absolute():
            path = ROOT / path
        if os.path.lexists(path):
            active.append(name)
    return branch, tuple(active)


def compare_worktree(candidate: dict[str, Entry]) -> None:
    for path, entry in candidate.items():
        expected_mode = 0o755 if entry.mode == "100755" else 0o644
        raw = read_regular(
            path,
            allow_empty=True,
            required_mode=expected_mode,
        )
        require(
            object_digest("blob", raw) == entry.oid,
            f"worktree bytes/mode differ from candidate: {path}",
        )


def validate_receipt_worktree_state(descendant: dict[str, Entry]) -> None:
    branch, active = lifecycle_branch()
    untracked = git("ls-files", "--others", "--exclude-per-directory=.gitignore", "-z")
    require(isinstance(untracked, bytes), "receipt untracked observation changed type")
    require(
        branch is None
        and not active
        and git_predicate("diff", "--cached", "--quiet", "HEAD", "--")
        and git_predicate("diff", "--quiet", "HEAD", "--")
        and not decode_z(untracked),
        "receipt descendant must be a clean detached checkout with no active operation",
    )
    compare_worktree(descendant)


def validate_lifecycle(
    mode: str,
    checkpoint: str,
    rows: tuple[PolicyEntry, ...],
    candidate: dict[str, Entry],
) -> str:
    head, head_tree = repository_context()
    branch, active = lifecycle_branch()
    require(not active, "active Git operation present")
    if mode == "precommit":
        require(
            branch == "main" and head == CORRECTION and head_tree == CORRECTION_TREE,
            "precommit is not attached correction HEAD",
        )
        require(
            git_predicate("diff", "--cached", "--quiet", CORRECTION, "--"),
            "primary index differs from correction",
        )
        modified_raw = git("diff", "--name-only", "-z", CORRECTION, "--")
        added_raw = git(
            "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"
        )
        require(
            isinstance(modified_raw, bytes) and isinstance(added_raw, bytes),
            "path observation type changed",
        )
        require(
            decode_z(modified_raw)
            == tuple(row.path for row in rows if row.status == "M")
            and decode_z(added_raw)
            == tuple(row.path for row in rows if row.status == "A"),
            "precommit worktree overlay differs from policy",
        )
        result = "failed_correction_plus_exact_recovery_overlay"
    else:
        require(
            head == checkpoint
            and head_tree == git_text("rev-parse", f"{checkpoint}^{{tree}}"),
            "committed HEAD differs from checkpoint",
        )
        require(
            (mode == "candidate-commit" and branch is None)
            or (mode == "postcommit" and branch == "main"),
            "candidate/postcommit attachment differs from mode",
        )
        require(
            git_predicate("diff", "--cached", "--quiet", "HEAD", "--")
            and git_predicate("diff", "--quiet", "HEAD", "--"),
            "committed tracked state dirty",
        )
        untracked = git(
            "ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"
        )
        require(
            isinstance(untracked, bytes) and not decode_z(untracked),
            "committed state has untracked paths",
        )
        result = (
            "clean_detached_sole_child_recovery_no_credit"
            if mode == "candidate-commit"
            else "clean_main_sole_child_recovery_no_credit"
        )
    compare_worktree(candidate)
    return result


def artifact_descriptor(value: Any, path: str, label: str) -> None:
    item = exact_keys(
        value, {"git_blob_oid_sha1", "path", "sha256", "size_bytes"}, label
    )
    require(item["path"] == path, f"{label} path changed")
    sha1(item["git_blob_oid_sha1"], f"{label} blob")
    sha256(item["sha256"], f"{label} digest")
    size = exact_int(item["size_bytes"], f"{label} size", 1)
    require(size <= MAX_FILE_BYTES, f"{label} size exceeds artifact bound")


def artifact_descriptor_exact(
    value: Any, path: str, raw: bytes, entry: Entry, label: str
) -> None:
    artifact_descriptor(value, path, label)
    require(
        value
        == {
            "git_blob_oid_sha1": entry.oid,
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        },
        f"{label} does not bind exact Git blob bytes",
    )


def validate_protected_receipt_projection(value: Any, label: str) -> None:
    item = exact_keys(
        value,
        {"candidate_equals_anchor", "entry_count", "format", "sha256"},
        label,
    )
    require(
        item
        == {
            "candidate_equals_anchor": True,
            "entry_count": PROTECTED_COUNT,
            "format": "canonical compact sorted-key ASCII JSON plus LF over sorted {path,git_mode,git_blob_oid_sha1,sha256,size_bytes} rows",
            "sha256": PROTECTED_SHA256,
        },
        f"{label} changed",
    )


def validate_subject_sealed_index(
    value: Any,
    *,
    path: str,
    raw: bytes,
    entry: Entry,
    expected_count: int,
    expected_tree: str,
    expected_entries: dict[str, Entry],
    label: str,
) -> dict[str, Any]:
    item = exact_keys(
        value,
        {
            "commit_message_trailer_matches",
            "entry_count",
            "git_blob_oid_sha1",
            "path",
            "path_or_residency_claimed",
            "precommit_descriptor_observation_authenticated",
            "reconstructs_tree_twice",
            "sha256",
            "size_bytes",
        },
        label,
    )
    digest = hashlib.sha256(raw).hexdigest()
    require(
        item["path"] == path
        and item["git_blob_oid_sha1"] == entry.oid == object_digest("blob", raw)
        and item["sha256"] == digest
        and item["size_bytes"] == len(raw)
        and item["entry_count"] == expected_count
        and item["commit_message_trailer_matches"] is True
        and item["reconstructs_tree_twice"] is True
        and item["precommit_descriptor_observation_authenticated"] is False
        and item["path_or_residency_claimed"] is False,
        f"{label} descriptor changed",
    )
    validate_sealed_index(raw, digest, expected_count, expected_tree, expected_entries)
    return item


def validate_phase_group(value: Any, recovery: bool, expected_mode: str) -> None:
    group = exact_keys(
        value,
        {"normal", "optimized", "pair_normalized_equal"},
        "phase output group",
    )
    require(group["pair_normalized_equal"] is True, "phase pair marker changed")
    observed_outputs: list[bytes] = []
    for label, optimize in (("normal", 0), ("optimized", 1)):
        wrapper = exact_keys(group[label], {"output", "sha256"}, "phase output wrapper")
        output = wrapper["output"]
        exact_keys(
            output,
            RECOVERY_PHASE_KEYS if recovery else CORRECTION_PHASE_KEYS,
            "phase output",
        )
        require_named_field_paths(output, "revision", set(), "phase output")
        require_named_field_paths(output, "schema_revision", set(), "phase output")
        negative_evidence = output.get("negative_evidence")
        require(
            isinstance(negative_evidence, dict),
            "phase negative-evidence summary is not an object",
        )
        validate_phase_jobs_count(
            negative_evidence.get("jobs"), "phase negative-evidence jobs"
        )
        require(
            output["runtime_mode"] == optimize and output["mode"] == expected_mode,
            "phase runtime mode/outer role changed",
        )
        raw = canonical_json(output, pretty=False)
        require(
            wrapper["sha256"] == hashlib.sha256(raw).hexdigest(),
            "phase wrapper digest changed",
        )
        if not recovery:
            expected = {
                ("normal", "precommit"): (
                    6_227,
                    "b747b5017e74caa74692c872d911d4f58613e2a8dda836ec3bdc5bdd7624f4f2",
                ),
                ("optimized", "precommit"): (
                    6_227,
                    "a698f7b9ff33cad1d47e97188f1f6234d2213591f8103c0a80310bab4e7220ba",
                ),
                ("normal", "postcommit"): (
                    5_638,
                    "9691c4fbef777fec4d708eb2a400027bf3b7ba3dbc36e26f2f165ba251d0314f",
                ),
                ("optimized", "postcommit"): (
                    5_638,
                    "84923c556f22359e269bbd7bfc067a67e811bb312cf9731eedf778c4860c2b6a",
                ),
            }
            phase = output.get("mode")
            require(
                phase in {"precommit", "postcommit"}
                and (len(raw), wrapper["sha256"]) == expected[(label, phase)],
                "historical correction phase bytes/hash changed",
            )
        normalized = dict(output)
        normalized["runtime_mode"] = "<NORMALIZED-RUNTIME-MODE>"
        observed_outputs.append(canonical_json(normalized, pretty=False))
    require(
        observed_outputs[0] == observed_outputs[1],
        "phase outputs differ beyond runtime mode",
    )


def phase_output_pair(group: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    return group["normal"]["output"], group["optimized"]["output"]


def validate_recovery_phase_semantics(
    custody: dict[str, Any], expected: dict[str, Any]
) -> None:
    alternate = custody["alternate_index"]
    replay = exact_keys(
        expected["replay"],
        {
            "prior_r6_sha256",
            "prior_r7_sha256",
            "receipt_sha256",
            "replay_projection_sha256",
        },
        "recovery phase Lean r8 expectation",
    )
    require(
        replay["prior_r6_sha256"] == R6_SHA256
        and replay["prior_r7_sha256"] == R7_SHA256
        and HEX64.fullmatch(replay["receipt_sha256"]) is not None
        and HEX64.fullmatch(replay["replay_projection_sha256"]) is not None,
        "recovery phase Lean r8 expectation changed",
    )
    expected_delta = [
        {"mode": mode, "path": path, "status": status}
        for path, status, mode in expected["delta"]
    ]
    for phase_name, expected_mode, expected_lifecycle, expected_alternate in (
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
        group = custody[phase_name]
        for runtime_name, runtime_mode in (("normal", 0), ("optimized", 1)):
            output = group[runtime_name]["output"]
            require(
                output["mode"] == expected_mode
                and output["runtime_mode"] == runtime_mode
                and output["lifecycle"] == expected_lifecycle
                and output["credit"] == "none_local_custody_match_hosted_pending"
                and output["disposition"] == "local_hosted_pending_no_credit"
                and output["schema"]
                == "pid-rs/ksg-rev4-m1a-hosted-recovery-phase-validation/v1"
                and output["policy_sha256"] == expected["policy_sha256"]
                and output["current_source_manifest_sha256"]
                == expected["current_source"]
                and output["child_output_sha256"] == expected["children"]
                and output["static_artifact_sha256"] == expected["static"]
                and output["lean_r8"] == replay
                and output["negative_evidence"]
                == {
                    "sha256": expected["negative_sha256"],
                    **expected["negative_summary"],
                }
                and output["implementation_anchor"] == expected["implementation_anchor"]
                and output["failed_correction_anchor"]
                == expected["failed_correction_anchor"]
                and output["certified_sxpid_recovery"] == expected["certified"]
                and output["candidate"]
                == {
                    "alternate_index_custody": expected_alternate,
                    "checkpoint_commit": expected["checkpoint"],
                    "commit_envelope": expected["envelope"],
                    "delta": expected_delta,
                    "tree": expected["tree"],
                }
                and output["preclosure"]
                == {
                    "final_decision_absent": True,
                    "final_evidence_matrix_absent": True,
                    "future_composite_receipt_absent": True,
                    "future_retained_indexes_absent": True,
                    "open_gate_count": 13,
                    "status": "integration_no_go",
                }
                and output["repository_state"]
                == {"active_git_operations": [], "branch": "main"},
                f"recovery {phase_name}/{runtime_name} output is coordinated-resealed",
            )
    pre_normal, _ = phase_output_pair(custody["precommit_outputs"])
    post_normal, _ = phase_output_pair(custody["postcommit_outputs"])
    normalized_pre = dict(pre_normal)
    normalized_post = dict(post_normal)
    for normalized in (normalized_pre, normalized_post):
        normalized["mode"] = "<PHASE>"
        normalized["lifecycle"] = "<LIFECYCLE>"
        candidate = dict(normalized["candidate"])
        candidate["alternate_index_custody"] = "<ALTERNATE>"
        normalized["candidate"] = candidate
    require(
        normalized_pre == normalized_post,
        "recovery pre/post outputs differ beyond phase/lifecycle/alternate",
    )


def receipt_recovery_phase_expectations(
    receipt: dict[str, Any],
    *,
    negative_summary: dict[str, Any],
    policy_rows: tuple[PolicyEntry, ...],
) -> dict[str, Any]:
    recovery = receipt["hosted_recovery"]
    recovery_sealed = recovery["sealed_index"]
    synthetic = receipt["revision4_integration"]
    exact_keys(
        synthetic,
        {
            "decision_v4_absent_at_recovery",
            "evidence_matrix_v4_absent_at_recovery",
            "open_gate_count",
            "status",
        },
        "receipt revision4 integration phase authority",
    )
    # Vector mode deliberately uses fixed, checker-owned synthetic facts for
    # future candidate artifacts.  None is copied from a phase output, and no
    # not-yet-committed A-path is read from the current worktree.
    certified = {
        "four_container_digest_literals": {
            "certified_checker": "1" * 64,
            "certified_self_test": "2" * 64,
            "just_recipe": "3" * 64,
            "workflow_job": "4" * 64,
        },
        "scientific_authority_unchanged": True,
        "self_test_sha256": "2" * 64,
        "workflow_fetch_depth_zero": True,
    }
    children = {
        CERT_SELF_TEST: "5" * 64,
        CERT_CHECKER: "6" * 64,
        LEAN_SELF_TEST: "7" * 64,
        LEAN_CHECKER: "8" * 64,
    }
    current_source = "f" * 64
    static = {
        NEGATIVE_RELATIVE: "9" * 64,
        BOUNDARY_RELATIVE: "a" * 64,
        SCHEMA_RELATIVE: "b" * 64,
        SELF_TEST_RELATIVE: "c" * 64,
    }
    implementation_anchor = {
        "commit": IMPLEMENTATION,
        "direct_parent": IMPLEMENTATION_PARENT,
        "protected_projection": {
            "candidate_equals_anchor": True,
            "entry_count": PROTECTED_COUNT,
            "sha256": PROTECTED_SHA256,
        },
        "tree": IMPLEMENTATION_TREE,
    }
    failed_correction_anchor = {
        "commit": CORRECTION,
        "direct_parent": IMPLEMENTATION,
        "full_tree_projection": {
            "entry_count": CORRECTION_ENTRY_COUNT,
            "sha256": CORRECTION_TREE_PROJECTION_SHA256,
            "size_bytes": CORRECTION_TREE_PROJECTION_SIZE_BYTES,
        },
        "protected_projection": {
            "candidate_equals_anchor": True,
            "entry_count": PROTECTED_COUNT,
            "sha256": PROTECTED_SHA256,
        },
        "sealed_index": {
            "entry_count": CORRECTION_ENTRY_COUNT,
            "git_blob_oid_sha1": CORRECTION_INDEX_BLOB,
            "sha256": CORRECTION_INDEX_SHA256,
            "size_bytes": CORRECTION_INDEX_SIZE_BYTES,
        },
        "tree": CORRECTION_TREE,
    }
    envelope = {
        "author": recovery["author"],
        "committer": recovery["committer"],
        "message": recovery["commit_message"],
        "sealed_index_sha256": recovery_sealed["sha256"],
        "sealed_index_size_bytes": recovery_sealed["size_bytes"],
    }
    delta = tuple((row.path, row.status, "100644") for row in policy_rows)
    replay = {
        "prior_r6_sha256": R6_SHA256,
        "prior_r7_sha256": R7_SHA256,
        "receipt_sha256": "d" * 64,
        "replay_projection_sha256": "e" * 64,
    }
    return {
        "certified": certified,
        "checkpoint": recovery["commit"],
        "children": children,
        "current_source": current_source,
        "delta": delta,
        "envelope": envelope,
        "failed_correction_anchor": failed_correction_anchor,
        "implementation_anchor": implementation_anchor,
        "negative_sha256": EXPECTED_FROZEN_NEGATIVE_SHA256,
        "negative_summary": negative_summary,
        "policy_sha256": "0" * 64,
        "replay": replay,
        "static": static,
        "tree": recovery["tree"],
    }


def validate_phase_custody(
    value: Any,
    *,
    recovery: bool,
    expected_recovery: dict[str, Any] | None = None,
    subject_entries: dict[str, Entry] | None = None,
    retained_index: tuple[bytes, Entry] | None = None,
) -> None:
    custody = exact_keys(value, PHASE_CUSTODY_KEYS, "phase custody")
    paths = (
        (POLICY_RELATIVE, BOUNDARY_RELATIVE, CHECKER_RELATIVE, SELF_TEST_RELATIVE)
        if recovery
        else (
            "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json",
            "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md",
            "scripts/check-ksg-m1a-custody-correction.py",
            "scripts/check-ksg-m1a-custody-correction-self-test.py",
        )
    )
    for key, path in zip(
        ("policy", "boundary", "checker", "self_test"), paths, strict=True
    ):
        if subject_entries is None:
            artifact_descriptor(custody[key], path, f"{key} artifact")
        else:
            artifact_descriptor_exact(
                custody[key],
                path,
                tree_blob(subject_entries, path),
                subject_entries[path],
                f"{key} artifact",
            )
    alternate = custody["alternate_index"]
    required_alternate = {
        "entry_count",
        "input_descriptor_read_only",
        "input_transport",
        "mode_octal",
        "path_or_residency_claimed",
        "precommit_descriptor_observation_authenticated",
        "retained_index_artifact",
        "sha256",
        "single_link",
        "size_bytes",
    }
    exact_keys(alternate, required_alternate, "phase alternate index")
    retained_path = RECOVERY_RETAINED_INDEX if recovery else OLD_RETAINED_INDEX
    retained = alternate["retained_index_artifact"]
    artifact_descriptor(retained, retained_path, "phase retained index")
    require(
        alternate["input_descriptor_read_only"] is True
        and alternate["input_transport"] == "standard_input_regular_file_descriptor"
        and alternate["mode_octal"] == "0400"
        and alternate["path_or_residency_claimed"] is False
        and alternate["precommit_descriptor_observation_authenticated"] is False
        and alternate["single_link"] is True
        and retained["sha256"] == alternate["sha256"]
        and retained["size_bytes"] == alternate["size_bytes"],
        "phase alternate-index custody changed",
    )
    if not recovery:
        require(
            alternate["entry_count"] == CORRECTION_ENTRY_COUNT
            and alternate["sha256"] == CORRECTION_INDEX_SHA256
            and alternate["size_bytes"] == CORRECTION_INDEX_SIZE_BYTES
            and retained["git_blob_oid_sha1"] == CORRECTION_INDEX_BLOB,
            "historical correction alternate index changed",
        )
    if retained_index is not None:
        retained_raw, retained_entry = retained_index
        artifact_descriptor_exact(
            retained,
            retained_path,
            retained_raw,
            retained_entry,
            "phase retained index",
        )
        require(
            alternate["entry_count"]
            == (
                len(subject_entries)
                if recovery and subject_entries is not None
                else CORRECTION_ENTRY_COUNT
            ),
            "phase retained index entry count differs from subject tree",
        )
    validate_phase_group(custody["precommit_outputs"], recovery, "precommit")
    validate_phase_group(custody["postcommit_outputs"], recovery, "postcommit")
    if recovery:
        require(
            expected_recovery is not None, "recovery phase semantic expectations absent"
        )
        validate_recovery_phase_semantics(custody, expected_recovery)


def installed_negative_authorities() -> tuple[
    bytes, dict[str, Any], str, bytes, dict[str, Any]
]:
    implementation_path = (
        "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
    )
    correction_raw = read_regular(NEGATIVE_RELATIVE)
    implementation_raw = read_regular(implementation_path)
    require(
        len(correction_raw) == EXPECTED_FROZEN_NEGATIVE_SIZE_BYTES
        and hashlib.sha256(correction_raw).hexdigest()
        == EXPECTED_FROZEN_NEGATIVE_SHA256
        and len(implementation_raw) == 484_959
        and hashlib.sha256(implementation_raw).hexdigest()
        == "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5",
        "installed negative authority bytes changed/resealed",
    )
    correction = parse_json(correction_raw, "installed correction negative authority")
    implementation = parse_json(
        implementation_raw, "installed implementation negative authority"
    )
    validate_negative(correction)
    validate_implementation_negative_revision_contract(
        implementation, "installed implementation negative"
    )
    require(
        isinstance(correction, dict)
        and isinstance(correction.get("ci_failure"), dict)
        and isinstance(correction.get("codeql_success"), dict)
        and isinstance(implementation.get("ci_failure"), dict)
        and isinstance(implementation.get("codeql_success"), dict),
        "installed negative authority hosted subobjects changed",
    )
    return (
        correction_raw,
        correction,
        implementation_path,
        implementation_raw,
        implementation,
    )


def validate_receipt_subject_authorities(
    receipt: dict[str, Any],
    *,
    correction_raw: bytes,
    recovery_commit: str,
    recovery_tree: str,
    implementation_raw: bytes,
) -> None:
    correction = receipt["custody_correction"]
    recovery = receipt["hosted_recovery"]
    correction_sealed = exact_keys(
        correction["sealed_index"],
        {
            "commit_message_trailer_matches",
            "entry_count",
            "git_blob_oid_sha1",
            "path",
            "path_or_residency_claimed",
            "precommit_descriptor_observation_authenticated",
            "reconstructs_tree_twice",
            "sha256",
            "size_bytes",
        },
        "receipt correction sealed index",
    )
    recovery_sealed = exact_keys(
        recovery["sealed_index"],
        set(correction_sealed),
        "receipt recovery sealed index",
    )
    require(
        correction_sealed
        == {
            "commit_message_trailer_matches": True,
            "entry_count": CORRECTION_ENTRY_COUNT,
            "git_blob_oid_sha1": CORRECTION_INDEX_BLOB,
            "path": OLD_RETAINED_INDEX,
            "path_or_residency_claimed": False,
            "precommit_descriptor_observation_authenticated": False,
            "reconstructs_tree_twice": True,
            "sha256": CORRECTION_INDEX_SHA256,
            "size_bytes": CORRECTION_INDEX_SIZE_BYTES,
        },
        "receipt correction sealed index authority changed",
    )
    require(
        correction_sealed["path_or_residency_claimed"] is False
        and correction_sealed["precommit_descriptor_observation_authenticated"]
        is False,
        "receipt correction sealed index boolean authority changed",
    )
    recovery_custody = exact_keys(
        receipt["recovery_local_phase_custody"],
        PHASE_CUSTODY_KEYS,
        "receipt recovery phase custody",
    )
    policy_value = parse_json(
        read_regular(POLICY_RELATIVE), "installed recovery path policy authority"
    )
    policy_rows = validate_policy(policy_value, verify_anchor=False)
    expected_recovery_count = CORRECTION_ENTRY_COUNT + sum(
        row.status == "A" for row in policy_rows
    )
    recovery_alternate = exact_keys(
        recovery_custody["alternate_index"],
        {
            "entry_count",
            "input_descriptor_read_only",
            "input_transport",
            "mode_octal",
            "path_or_residency_claimed",
            "precommit_descriptor_observation_authenticated",
            "retained_index_artifact",
            "sha256",
            "single_link",
            "size_bytes",
        },
        "receipt recovery alternate index",
    )
    retained = exact_keys(
        recovery_alternate["retained_index_artifact"],
        {"git_blob_oid_sha1", "path", "sha256", "size_bytes"},
        "receipt recovery retained index",
    )
    require(
        recovery_sealed
        == {
            "commit_message_trailer_matches": True,
            "entry_count": expected_recovery_count,
            "git_blob_oid_sha1": retained["git_blob_oid_sha1"],
            "path": RECOVERY_RETAINED_INDEX,
            "path_or_residency_claimed": False,
            "precommit_descriptor_observation_authenticated": False,
            "reconstructs_tree_twice": True,
            "sha256": recovery_alternate["sha256"],
            "size_bytes": recovery_alternate["size_bytes"],
        }
        and retained
        == {
            "git_blob_oid_sha1": recovery_sealed["git_blob_oid_sha1"],
            "path": RECOVERY_RETAINED_INDEX,
            "sha256": recovery_sealed["sha256"],
            "size_bytes": recovery_sealed["size_bytes"],
        }
        and recovery_alternate["entry_count"] == recovery_sealed["entry_count"]
        and recovery_alternate["sha256"] == recovery_sealed["sha256"]
        and recovery_alternate["size_bytes"] == recovery_sealed["size_bytes"]
        and recovery_alternate["input_descriptor_read_only"] is True
        and recovery_alternate["input_transport"]
        == "standard_input_regular_file_descriptor"
        and recovery_alternate["mode_octal"] == "0400"
        and recovery_alternate["path_or_residency_claimed"] is False
        and recovery_alternate["precommit_descriptor_observation_authenticated"]
        is False
        and recovery_alternate["single_link"] is True,
        "receipt recovery sealed/alternate index authority changed",
    )
    require(
        recovery_sealed["path_or_residency_claimed"] is False
        and recovery_sealed["precommit_descriptor_observation_authenticated"] is False,
        "receipt recovery sealed index boolean authority changed",
    )
    require(
        recovery_sealed["sha256"] != CORRECTION_INDEX_SHA256
        and recovery_sealed["git_blob_oid_sha1"] != CORRECTION_INDEX_BLOB,
        "receipt recovery sealed index aliases correction authority",
    )
    expected_recovery_message = (
        "Repair KSG M1a hosted recovery wiring\n\n"
        f"Sealed-index-SHA256: {recovery_sealed['sha256']}\n"
        f"Sealed-index-Size: {recovery_sealed['size_bytes']}\n"
    )
    require(
        correction["commit_message"] == CORRECTION_MESSAGE
        and recovery["commit_message"] == expected_recovery_message
        and recovery["commit"] == recovery_commit
        and recovery["tree"] == recovery_tree,
        "receipt subject commit-message sealed-index binding changed",
    )
    for phase_name, expected_alternate in (
        ("precommit_outputs", recovery_alternate),
        ("postcommit_outputs", None),
    ):
        group = exact_keys(
            recovery_custody[phase_name],
            {"normal", "optimized", "pair_normalized_equal"},
            f"receipt recovery {phase_name}",
        )
        require(
            group["pair_normalized_equal"] is True,
            f"receipt recovery {phase_name} pair marker changed",
        )
        for runtime_name in ("normal", "optimized"):
            wrapper = exact_keys(
                group[runtime_name],
                {"output", "sha256"},
                f"receipt recovery {phase_name}/{runtime_name}",
            )
            output = exact_keys(
                wrapper["output"],
                RECOVERY_PHASE_KEYS,
                f"receipt recovery {phase_name}/{runtime_name} output",
            )
            candidate = exact_keys(
                output["candidate"],
                {
                    "alternate_index_custody",
                    "checkpoint_commit",
                    "commit_envelope",
                    "delta",
                    "tree",
                },
                f"receipt recovery {phase_name}/{runtime_name} candidate",
            )
            envelope = exact_keys(
                candidate["commit_envelope"],
                {
                    "author",
                    "committer",
                    "message",
                    "sealed_index_sha256",
                    "sealed_index_size_bytes",
                },
                f"receipt recovery {phase_name}/{runtime_name} envelope",
            )
            candidate_alternate = candidate["alternate_index_custody"]
            if expected_alternate is None:
                require(
                    candidate_alternate is None,
                    f"receipt recovery {phase_name}/{runtime_name} alternate changed",
                )
            else:
                candidate_alternate = exact_keys(
                    candidate_alternate,
                    {
                        "entry_count",
                        "input_descriptor_read_only",
                        "input_transport",
                        "mode_octal",
                        "path_or_residency_claimed",
                        "precommit_descriptor_observation_authenticated",
                        "retained_index_artifact",
                        "sha256",
                        "single_link",
                        "size_bytes",
                    },
                    f"receipt recovery {phase_name}/{runtime_name} alternate",
                )
                require(
                    candidate_alternate["path_or_residency_claimed"] is False
                    and candidate_alternate[
                        "precommit_descriptor_observation_authenticated"
                    ]
                    is False,
                    f"receipt recovery {phase_name}/{runtime_name} alternate booleans changed",
                )
            require(
                candidate["checkpoint_commit"] == recovery_commit
                and candidate["tree"] == recovery_tree
                and candidate_alternate == expected_alternate
                and envelope
                == {
                    "author": recovery["author"],
                    "committer": recovery["committer"],
                    "message": recovery["commit_message"],
                    "sealed_index_sha256": recovery_sealed["sha256"],
                    "sealed_index_size_bytes": recovery_sealed["size_bytes"],
                },
                f"receipt recovery {phase_name}/{runtime_name} subject join changed",
            )
    hosted = receipt["hosted_observations"]
    for field, path, raw in (
        ("correction_negative_evidence_artifact", NEGATIVE_RELATIVE, correction_raw),
        (
            "implementation_negative_evidence_artifact",
            "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json",
            implementation_raw,
        ),
    ):
        require(
            hosted[field]
            == {
                "git_blob_oid_sha1": object_digest("blob", raw),
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            },
            f"receipt {field} authority changed",
        )
    for key, path in (
        ("boundary", BOUNDARY_RELATIVE),
        ("checker", CHECKER_RELATIVE),
        ("policy", POLICY_RELATIVE),
        ("self_test", SELF_TEST_RELATIVE),
    ):
        raw = read_regular(path)
        require(
            recovery_custody[key]
            == {
                "git_blob_oid_sha1": object_digest("blob", raw),
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            },
            f"receipt recovery custody {key} authority changed",
        )


def validate_receipt_structure(
    value: Any,
    *,
    descendant: dict[str, Entry] | None = None,
    self_test_vector: bool = False,
) -> dict[str, Any]:
    receipt = exact_keys(value, RECEIPT_ROOT_KEYS, "composite-v3 receipt")
    require_named_field_paths(
        receipt, "revision", {("claim", "revision")}, "composite-v3 receipt"
    )
    require_named_field_paths(
        receipt,
        "schema_revision",
        {
            ("schema_revision",),
            (
                "hosted_observations",
                "recovery_ci_success",
                "postcommit_source_state_v2_content",
                "schema_revision",
            ),
            (
                "hosted_observations",
                "recovery_ci_success",
                "postcommit_source_state_v2_content",
                "binding",
                "manifest",
                "schema_revision",
            ),
        },
        "composite-v3 receipt",
    )
    exact_int(receipt["schema_revision"], "composite-v3 schema revision", 1)
    claim = exact_keys(receipt["claim"], {"id", "revision"}, "composite-v3 claim")
    exact_int(claim["revision"], "composite-v3 claim revision", 1)
    require(
        receipt["schema"] == RECEIPT_SCHEMA
        and receipt["schema_revision"] == 3
        and receipt["repository"] == "sepahead/pid-rs",
        "composite-v3 identity changed",
    )
    require(
        receipt["evidence_class"]
        == "m1a_three_subject_hosted_recovery_custody_not_scientific_evidence"
        and claim == {"id": "KSG-INTEGER-HARMONIC-001", "revision": 4}
        and receipt["milestone"]
        == {
            "gate_id": "G1",
            "implementation_phase": "M1a",
            "integration_status": "integration_no_go",
            "status": "implementation_failed_correction_and_hosted_recovery_observed",
        }
        and receipt["revision4_integration"]
        == {
            "decision_v4_absent_at_recovery": True,
            "evidence_matrix_v4_absent_at_recovery": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        }
        and receipt["negative_evidence_semantics"] == list(NEGATIVE_EVIDENCE_SEMANTICS)
        and receipt["nonimplications"] == list(COMPOSITE_NONIMPLICATIONS),
        "composite-v3 exact evidence/nonclaim boundary changed",
    )
    implementation = exact_keys(
        receipt["implementation_anchor"],
        {
            "commit",
            "direct_parent",
            "protected_projection",
            "remains_implementation_after_recovery",
            "tree",
        },
        "receipt implementation subject",
    )
    correction = exact_keys(
        receipt["custody_correction"],
        {
            "author",
            "commit",
            "commit_message",
            "committer",
            "direct_parent",
            "distinct_from_implementation_anchor",
            "implementation_identity_after_correction",
            "object_format",
            "one_parent",
            "sealed_index",
            "tree",
            "unsigned",
        },
        "receipt correction subject",
    )
    recovery = exact_keys(
        receipt["hosted_recovery"],
        {
            "author",
            "commit",
            "commit_message",
            "committer",
            "direct_parent",
            "distinct_from_correction",
            "implementation_identity_after_recovery",
            "object_format",
            "one_parent",
            "sealed_index",
            "tree",
            "unsigned",
        },
        "receipt recovery subject",
    )
    require(
        implementation["commit"] == IMPLEMENTATION
        and implementation["tree"] == IMPLEMENTATION_TREE
        and implementation["direct_parent"] == IMPLEMENTATION_PARENT
        and implementation["remains_implementation_after_recovery"] is True,
        "receipt implementation identity changed",
    )
    validate_protected_receipt_projection(
        implementation["protected_projection"], "implementation protected projection"
    )
    require(
        correction["commit"] == CORRECTION
        and correction["tree"] == CORRECTION_TREE
        and correction["direct_parent"] == IMPLEMENTATION
        and correction["implementation_identity_after_correction"] == IMPLEMENTATION
        and correction["distinct_from_implementation_anchor"] is True
        and correction["object_format"] == "sha1"
        and correction["one_parent"] is True
        and correction["unsigned"] is True
        and correction["author"]
        == correction["committer"]
        == {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
        and correction["commit_message"] == CORRECTION_MESSAGE,
        "receipt correction identity changed",
    )
    recovery_commit = sha1(recovery["commit"], "receipt recovery commit")
    recovery_tree = sha1(recovery["tree"], "receipt recovery tree")
    if self_test_vector:
        require(
            recovery_commit == SELF_TEST_VECTOR_RECOVERY_COMMIT
            and recovery_tree == SELF_TEST_VECTOR_RECOVERY_TREE
            and recovery["sealed_index"]
            == {
                "commit_message_trailer_matches": True,
                "entry_count": SELF_TEST_VECTOR_RECOVERY_ENTRY_COUNT,
                "git_blob_oid_sha1": SELF_TEST_VECTOR_RECOVERY_INDEX_BLOB,
                "path": RECOVERY_RETAINED_INDEX,
                "path_or_residency_claimed": False,
                "precommit_descriptor_observation_authenticated": False,
                "reconstructs_tree_twice": True,
                "sha256": SELF_TEST_VECTOR_RECOVERY_INDEX_SHA256,
                "size_bytes": SELF_TEST_VECTOR_RECOVERY_INDEX_SIZE_BYTES,
            }
            and recovery["commit_message"]
            == (
                "Repair KSG M1a hosted recovery wiring\n\n"
                "Sealed-index-SHA256: "
                f"{SELF_TEST_VECTOR_RECOVERY_INDEX_SHA256}\n"
                "Sealed-index-Size: "
                f"{SELF_TEST_VECTOR_RECOVERY_INDEX_SIZE_BYTES}\n"
            ),
            "receipt self-test synthetic recovery identity/seal changed",
        )
    require(
        recovery_commit not in {IMPLEMENTATION, CORRECTION}
        and recovery["direct_parent"] == CORRECTION
        and recovery["implementation_identity_after_recovery"] == IMPLEMENTATION
        and recovery["distinct_from_correction"] is True
        and recovery["object_format"] == "sha1"
        and recovery["one_parent"] is True
        and recovery["unsigned"] is True
        and recovery["author"]
        == recovery["committer"]
        == {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME},
        "receipt recovery identity changed",
    )
    hosted = exact_keys(
        receipt["hosted_observations"],
        {
            "all_green_applies_only_to_recovery_head",
            "correction_ci_failure",
            "correction_codeql_success",
            "correction_heads_equal",
            "correction_negative_evidence_artifact",
            "implementation_ci_failure",
            "implementation_codeql_success",
            "implementation_heads_equal",
            "implementation_negative_evidence_artifact",
            "recovery_ci_success",
            "recovery_codeql_success",
            "recovery_heads_equal",
            "three_subject_heads_distinct",
        },
        "receipt hosted observations",
    )
    (
        installed_correction_raw,
        installed_correction,
        installed_implementation_path,
        installed_implementation_raw,
        installed_implementation,
    ) = installed_negative_authorities()
    validate_receipt_subject_authorities(
        receipt,
        correction_raw=installed_correction_raw,
        recovery_commit=recovery_commit,
        recovery_tree=recovery_tree,
        implementation_raw=installed_implementation_raw,
    )
    require(
        isinstance(hosted["recovery_ci_success"], dict)
        and isinstance(hosted["recovery_codeql_success"], dict),
        "receipt recovery hosted observation objects changed type",
    )
    for field, authority, authority_field in (
        ("correction_ci_failure", installed_correction, "ci_failure"),
        ("correction_codeql_success", installed_correction, "codeql_success"),
        ("implementation_ci_failure", installed_implementation, "ci_failure"),
        (
            "implementation_codeql_success",
            installed_implementation,
            "codeql_success",
        ),
    ):
        require(
            canonical_json(hosted[field], pretty=False)
            == canonical_json(authority[authority_field], pretty=False),
            f"receipt {field} does not byte-deep equal installed negative authority",
        )
    require(
        hosted.get("implementation_heads_equal") is True
        and hosted.get("correction_heads_equal") is True
        and hosted.get("recovery_heads_equal") is True
        and hosted.get("all_green_applies_only_to_recovery_head") is True
        and hosted.get("three_subject_heads_distinct") is True,
        "receipt cross-head boundary changed",
    )
    require(
        hosted.get("implementation_ci_failure", {}).get("head_sha") == IMPLEMENTATION
        and hosted.get("implementation_ci_failure", {}).get("conclusion") == "failure"
        and hosted.get("correction_ci_failure", {}).get("head_sha") == CORRECTION
        and hosted.get("correction_ci_failure", {}).get("run_id") == 31724449805
        and hosted.get("correction_ci_failure", {}).get("conclusion") == "failure"
        and hosted.get("recovery_ci_success", {}).get("head_sha") == recovery_commit
        and hosted.get("recovery_ci_success", {}).get("conclusion") == "success"
        and hosted.get("recovery_codeql_success", {}).get("head_sha") == recovery_commit
        and hosted.get("recovery_codeql_success", {}).get("conclusion") == "success",
        "receipt hosted observations conflate heads/conclusions",
    )
    remote = receipt["remote_observations"]
    require(
        isinstance(remote, dict)
        and set(remote)
        == {
            "branch",
            "correction_commit",
            "implementation_commit",
            "observed_at",
            "observed_remote_head",
            "recovery_commit",
        }
        and remote.get("branch") == "main"
        and remote.get("implementation_commit") == IMPLEMENTATION
        and remote.get("correction_commit") == CORRECTION
        and remote.get("recovery_commit") == recovery_commit
        and remote.get("observed_remote_head") == recovery_commit,
        "receipt remote chain changed",
    )
    observed_remote_time = parse_rfc3339_utc(
        remote["observed_at"], "receipt remote observed_at"
    )
    recovery_ci = validate_recovery_ci_success(
        hosted["recovery_ci_success"], recovery_commit, recovery_tree
    )
    recovery_codeql = validate_recovery_codeql_success(
        hosted["recovery_codeql_success"],
        recovery_commit,
        recovery_tree,
        baseline_alert_numbers=hosted["correction_codeql_success"]["alert_state"][
            "observed_alert_numbers"
        ],
    )
    implementation_ci_names = sorted(
        row["name"] for row in hosted["implementation_ci_failure"]["job_roster"]
    )
    correction_ci_names = sorted(
        row["name"] for row in hosted["correction_ci_failure"]["job_roster"]
    )
    recovery_ci_names = sorted(row["name"] for row in recovery_ci["jobs"])
    implementation_codeql_names = sorted(
        row["name"] for row in hosted["implementation_codeql_success"]["job_roster"]
    )
    correction_codeql_names = sorted(
        row["name"] for row in hosted["correction_codeql_success"]["job_roster"]
    )
    recovery_codeql_names = sorted(row["name"] for row in recovery_codeql["jobs"])
    require(
        implementation_ci_names == correction_ci_names == recovery_ci_names
        and implementation_codeql_names
        == correction_codeql_names
        == recovery_codeql_names
        and sorted(
            (row["language"], row["category"])
            for row in hosted["correction_codeql_success"]["analysis_roster"]
        )
        == sorted(
            (row["language"], row["category"]) for row in recovery_codeql["analyses"]
        ),
        "receipt recovery hosted job/analysis semantic roster changed",
    )
    run_ids = (
        hosted["implementation_ci_failure"]["run_id"],
        hosted["implementation_codeql_success"]["run_id"],
        hosted["correction_ci_failure"]["run_id"],
        hosted["correction_codeql_success"]["run_id"],
        hosted["recovery_ci_success"]["run_id"],
        hosted["recovery_codeql_success"]["run_id"],
    )
    job_id_inventories = tuple(
        {row["job_id"] for row in hosted[key]["job_roster"]}
        for key in (
            "implementation_ci_failure",
            "implementation_codeql_success",
            "correction_ci_failure",
            "correction_codeql_success",
            "recovery_ci_success",
            "recovery_codeql_success",
        )
    )
    require(
        run_ids[:4] == (31686107959, 31686106737, 31724449805, 31724449083)
        and len(set(run_ids)) == len(run_ids) == 6
        and all(
            not left & right
            for index, left in enumerate(job_id_inventories)
            for right in job_id_inventories[index + 1 :]
        ),
        "receipt run/job identities overlap or transfer across subjects",
    )
    analysis_id_inventories = tuple(
        {row["analysis_id"] for row in hosted[key]["analysis_roster"]}
        for key in (
            "implementation_codeql_success",
            "correction_codeql_success",
            "recovery_codeql_success",
        )
    )
    artifact_id_inventories = (
        {
            hosted["implementation_ci_failure"]["postcommit_source_state_v2"][
                "artifact_id"
            ]
        },
        {
            hosted["correction_ci_failure"]["postcommit_source_state_v2"][
                "artifact_id"
            ],
            *(
                row["artifact_id"]
                for row in hosted["correction_ci_failure"]["artifact_inventory"]
            ),
        },
        {hosted["recovery_ci_success"]["postcommit_source_state_v2"]["artifact_id"]},
    )
    require(
        all(
            not left & right
            for inventories in (analysis_id_inventories, artifact_id_inventories)
            for index, left in enumerate(inventories)
            for right in inventories[index + 1 :]
        ),
        "receipt reuses hosted analysis/artifact identifiers across subjects",
    )
    require(
        all(
            parse_rfc3339_utc(row["completed_at"], "recovery hosted job completion")
            <= observed_remote_time
            for row in (*recovery_ci["jobs"], *recovery_codeql["jobs"])
        ),
        "remote observation predates recovery hosted completion",
    )
    correction_entries_for_phase = (
        parse_tree(CORRECTION_TREE) if descendant is not None else None
    )
    correction_retained_for_phase = (
        (
            tree_blob(descendant, OLD_RETAINED_INDEX),
            descendant[OLD_RETAINED_INDEX],
        )
        if descendant is not None and OLD_RETAINED_INDEX in descendant
        else None
    )
    validate_phase_custody(
        receipt["correction_local_phase_custody"],
        recovery=False,
        subject_entries=correction_entries_for_phase,
        retained_index=correction_retained_for_phase,
    )
    policy_value_for_phase = parse_json(
        read_regular(POLICY_RELATIVE), "installed recovery path policy phase authority"
    )
    policy_rows_for_phase = validate_policy(policy_value_for_phase, verify_anchor=False)
    vector_phase_expectations = (
        receipt_recovery_phase_expectations(
            receipt,
            negative_summary=validate_negative(installed_correction),
            policy_rows=policy_rows_for_phase,
        )
        if self_test_vector
        else None
    )
    if descendant is not None:
        correction_negative_raw = tree_blob(descendant, NEGATIVE_RELATIVE)
        correction_negative = installed_correction
        implementation_negative_path = installed_implementation_path
        implementation_negative_raw = tree_blob(
            descendant, implementation_negative_path
        )
        require(
            correction_negative_raw == installed_correction_raw
            and implementation_negative_raw == installed_implementation_raw,
            "retained negative artifacts differ from installed authorities",
        )
        for field, path, raw in (
            (
                "correction_negative_evidence_artifact",
                NEGATIVE_RELATIVE,
                correction_negative_raw,
            ),
            (
                "implementation_negative_evidence_artifact",
                implementation_negative_path,
                implementation_negative_raw,
            ),
        ):
            entry = descendant[path]
            artifact_descriptor_exact(hosted[field], path, raw, entry, field)
        recovery_entries = parse_tree(recovery_tree)
        correction_entries = parse_tree(CORRECTION_TREE)
        expected_postcommit_manifest = recovery_current_manifest_descriptor(
            recovery_entries
        )
        validate_postcommit_source_state_content(
            recovery_ci["content"],
            recovery_commit,
            recovery_tree,
            expected_manifest=expected_postcommit_manifest,
        )
        policy_raw = tree_blob(recovery_entries, POLICY_RELATIVE)
        policy_value = parse_json(policy_raw, "recovery subject policy")
        rows = validate_policy(policy_value, verify_anchor=False)
        require(
            policy_value["authority"]["inventory_status"] == "frozen"
            and policy_value["authority"]["lifecycle_validation_permitted"] is True,
            "receipt recovery-subject policy is not frozen/enabled",
        )
        delta = validate_delta(rows, correction_entries, recovery_entries)
        envelope = parse_commit(
            recovery_commit, tree=recovery_tree, parent=CORRECTION, recovery=True
        )
        cert = validate_certified_rebind(correction_entries, recovery_entries)
        replay = validate_replay(recovery_entries)
        current_source = hashlib.sha256(
            tree_blob(recovery_entries, CURRENT_SOURCE_RELATIVE)
        ).hexdigest()
        static = {
            BOUNDARY_RELATIVE: hashlib.sha256(
                tree_blob(recovery_entries, BOUNDARY_RELATIVE)
            ).hexdigest(),
            SELF_TEST_RELATIVE: hashlib.sha256(
                tree_blob(recovery_entries, SELF_TEST_RELATIVE)
            ).hexdigest(),
            SCHEMA_RELATIVE: hashlib.sha256(
                tree_blob(recovery_entries, SCHEMA_RELATIVE)
            ).hexdigest(),
            NEGATIVE_RELATIVE: EXPECTED_FROZEN_NEGATIVE_SHA256,
        }
        children = {
            path: digest for path, (_size, digest) in EXPECTED_CHILD_STDOUT.items()
        }
        implementation_anchor = {
            "commit": IMPLEMENTATION,
            "direct_parent": IMPLEMENTATION_PARENT,
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": PROTECTED_COUNT,
                "sha256": PROTECTED_SHA256,
            },
            "tree": IMPLEMENTATION_TREE,
        }
        failed_correction_anchor = {
            "commit": CORRECTION,
            "direct_parent": IMPLEMENTATION,
            "full_tree_projection": {
                "entry_count": CORRECTION_ENTRY_COUNT,
                "sha256": CORRECTION_TREE_PROJECTION_SHA256,
                "size_bytes": CORRECTION_TREE_PROJECTION_SIZE_BYTES,
            },
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": PROTECTED_COUNT,
                "sha256": PROTECTED_SHA256,
            },
            "sealed_index": {
                "entry_count": CORRECTION_ENTRY_COUNT,
                "git_blob_oid_sha1": CORRECTION_INDEX_BLOB,
                "sha256": CORRECTION_INDEX_SHA256,
                "size_bytes": CORRECTION_INDEX_SIZE_BYTES,
            },
            "tree": CORRECTION_TREE,
        }
        certified = {
            "four_container_digest_literals": cert,
            "scientific_authority_unchanged": True,
            "self_test_sha256": cert["certified_self_test"],
            "workflow_fetch_depth_zero": True,
        }
        validate_phase_custody(
            receipt["recovery_local_phase_custody"],
            recovery=True,
            expected_recovery={
                "certified": certified,
                "checkpoint": recovery_commit,
                "children": children,
                "current_source": current_source,
                "delta": delta,
                "envelope": envelope,
                "failed_correction_anchor": failed_correction_anchor,
                "implementation_anchor": implementation_anchor,
                "negative_sha256": EXPECTED_FROZEN_NEGATIVE_SHA256,
                "negative_summary": validate_negative(correction_negative),
                "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
                "replay": replay,
                "static": static,
                "tree": recovery_tree,
            },
            subject_entries=recovery_entries,
            retained_index=(
                tree_blob(descendant, RECOVERY_RETAINED_INDEX),
                descendant[RECOVERY_RETAINED_INDEX],
            ),
        )
    elif self_test_vector:
        require(
            vector_phase_expectations is not None,
            "receipt self-test phase expectations absent",
        )
        validate_phase_custody(
            receipt["recovery_local_phase_custody"],
            recovery=True,
            expected_recovery=vector_phase_expectations,
        )
    else:
        validate_phase_group(
            receipt["recovery_local_phase_custody"]["precommit_outputs"],
            True,
            "precommit",
        )
        validate_phase_group(
            receipt["recovery_local_phase_custody"]["postcommit_outputs"],
            True,
            "postcommit",
        )
    return {"recovery_commit": recovery_commit, "recovery_tree": recovery_tree}


def verify_receipt_descendant(raw: bytes, summary: dict[str, Any]) -> None:
    head, head_tree = repository_context()
    require(
        head not in {IMPLEMENTATION, CORRECTION, summary["recovery_commit"]},
        "receipt is not in strict descendant",
    )
    require(
        git_predicate("merge-base", "--is-ancestor", summary["recovery_commit"], head),
        "receipt HEAD not descendant of recovery",
    )
    require(
        git_predicate("merge-base", "--is-ancestor", IMPLEMENTATION, CORRECTION)
        and git_predicate(
            "merge-base", "--is-ancestor", CORRECTION, summary["recovery_commit"]
        ),
        "receipt three-subject ancestry changed",
    )
    implementation_entries = parse_tree(IMPLEMENTATION_TREE)
    correction_entries = parse_tree(CORRECTION_TREE)
    recovery_commit_envelope = parse_commit(
        summary["recovery_commit"],
        tree=summary["recovery_tree"],
        parent=CORRECTION,
        recovery=True,
    )
    correction_commit_envelope = parse_commit(
        CORRECTION, tree=CORRECTION_TREE, parent=IMPLEMENTATION, recovery=False
    )
    require(
        summary["recovery_tree"]
        == git_text("rev-parse", f"{summary['recovery_commit']}^{{tree}}")
        and correction_commit_envelope["message"] == CORRECTION_MESSAGE
        and recovery_commit_envelope["message"].startswith(
            "Repair KSG M1a hosted recovery wiring\n\n"
        ),
        "receipt recovery/correction commit envelopes changed",
    )
    recovery_entries = parse_tree(summary["recovery_tree"])
    implementation_protected_raw, implementation_protected_sha = protected_projection(
        implementation_entries
    )
    correction_protected_raw, correction_protected_sha = protected_projection(
        correction_entries
    )
    recovery_protected_raw, recovery_protected_sha = protected_projection(
        recovery_entries
    )
    require(
        implementation_protected_raw
        == correction_protected_raw
        == recovery_protected_raw
        and implementation_protected_sha
        == correction_protected_sha
        == recovery_protected_sha
        == PROTECTED_SHA256
        and all(
            path not in implementation_entries
            and path not in correction_entries
            and path not in recovery_entries
            for path in (FUTURE_RECEIPT, OLD_RETAINED_INDEX, RECOVERY_RETAINED_INDEX)
        ),
        "subject protected projection changed or future authority appears in subject",
    )
    descendant_commit_raw = exact_object(head, "commit")
    descendant_header, separator, _descendant_message = descendant_commit_raw.partition(
        b"\n\n"
    )
    descendant_lines = descendant_header.split(b"\n")
    require(
        separator == b"\n\n"
        and len(descendant_lines) == 4
        and descendant_lines[0] == f"tree {head_tree}".encode("ascii")
        and descendant_lines[1]
        == f"parent {summary['recovery_commit']}".encode("ascii")
        and descendant_lines[2].startswith(b"author ")
        and descendant_lines[3].startswith(b"committer "),
        "receipt descendant is not an unsigned sole child of recovery",
    )
    descendant = parse_tree(head_tree)
    validate_receipt_worktree_state(descendant)
    require(
        changed_entries(recovery_entries, descendant)
        == (
            (FUTURE_RECEIPT, "A", "100644"),
            (OLD_RETAINED_INDEX, "A", "100644"),
            (RECOVERY_RETAINED_INDEX, "A", "100644"),
        ),
        "receipt descendant delta is not exactly three additions",
    )
    entry = descendant.get(FUTURE_RECEIPT)
    require(
        entry is not None and tree_blob(descendant, FUTURE_RECEIPT) == raw,
        "stdin receipt differs from descendant blob",
    )
    receipt = parse_json(raw, "composite-v3 receipt")
    validate_receipt_structure(receipt, descendant=descendant)
    correction_index_raw: bytes | None = None
    recovery_index_raw: bytes | None = None
    for path, expected_sha, expected_size, expected_blob in (
        (
            OLD_RETAINED_INDEX,
            CORRECTION_INDEX_SHA256,
            CORRECTION_INDEX_SIZE_BYTES,
            CORRECTION_INDEX_BLOB,
        ),
        (RECOVERY_RETAINED_INDEX, None, None, None),
    ):
        item = descendant.get(path)
        require(
            item is not None and item.mode == "100644", f"retained index absent: {path}"
        )
        index_raw = tree_blob(descendant, path)
        if expected_sha is not None:
            require(
                hashlib.sha256(index_raw).hexdigest() == expected_sha
                and len(index_raw) == expected_size
                and item.oid == expected_blob,
                "old retained index bytes changed",
            )
            correction_index_raw = index_raw
        else:
            recovery_index_raw = index_raw
    require(
        correction_index_raw is not None and recovery_index_raw is not None,
        "retained index bytes absent",
    )
    correction_subject = receipt["custody_correction"]
    recovery_subject = receipt["hosted_recovery"]
    validate_subject_sealed_index(
        correction_subject["sealed_index"],
        path=OLD_RETAINED_INDEX,
        raw=correction_index_raw,
        entry=descendant[OLD_RETAINED_INDEX],
        expected_count=CORRECTION_ENTRY_COUNT,
        expected_tree=CORRECTION_TREE,
        expected_entries=correction_entries,
        label="receipt correction sealed index",
    )
    validate_subject_sealed_index(
        recovery_subject["sealed_index"],
        path=RECOVERY_RETAINED_INDEX,
        raw=recovery_index_raw,
        entry=descendant[RECOVERY_RETAINED_INDEX],
        expected_count=len(recovery_entries),
        expected_tree=summary["recovery_tree"],
        expected_entries=recovery_entries,
        label="receipt recovery sealed index",
    )
    require(
        correction_subject["sealed_index"]["sha256"]
        == correction_commit_envelope["sealed_index_sha256"]
        and correction_subject["sealed_index"]["size_bytes"]
        == correction_commit_envelope["sealed_index_size_bytes"]
        and recovery_subject["sealed_index"]["sha256"]
        == recovery_commit_envelope["sealed_index_sha256"]
        and recovery_subject["sealed_index"]["size_bytes"]
        == recovery_commit_envelope["sealed_index_size_bytes"]
        and correction_subject["commit_message"]
        == correction_commit_envelope["message"]
        and recovery_subject["commit_message"] == recovery_commit_envelope["message"],
        "receipt subject messages/trailers do not bind retained indexes",
    )
    final_head, final_tree = repository_context()
    require(
        (final_head, final_tree) == (head, head_tree),
        "repository head/tree changed during receipt validation",
    )


def validate_self_test_vector(value: Any) -> None:
    root = exact_keys(value, {"payload", "schema", "validator"}, "self-test vector")
    require(
        root["schema"] == SELF_TEST_SCHEMA and isinstance(root["validator"], str),
        "self-test vector identity changed",
    )
    validator, payload = root["validator"], root["payload"]
    if validator == "policy":
        validate_policy(payload, verify_anchor=False)
    elif validator == "commit":
        item = exact_keys(payload, {"raw_hex", "tree"}, "commit vector")
        parse_commit_bytes(
            bytes.fromhex(item["raw_hex"]),
            expected_tree=sha1(item["tree"], "vector tree"),
            expected_parent=CORRECTION,
            recovery=True,
        )
    elif validator == "delta":
        item = exact_keys(payload, {"observed"}, "delta vector")
        observed = tuple(
            (row["path"], row["status"], row["mode"]) for row in item["observed"]
        )
        expected = tuple(
            (path, status, "100644")
            for path, (status, _) in REQUIRED_POLICY_ROWS.items()
        )
        require(observed == expected, "synthetic recovery delta changed")
    elif validator == "protected":
        item = exact_keys(payload, {"count", "sha256"}, "protected vector")
        require(
            item == {"count": PROTECTED_COUNT, "sha256": PROTECTED_SHA256},
            "protected vector changed",
        )
    elif validator == "history":
        item = exact_keys(
            payload,
            {"correction", "implementation", "parent", "tree"},
            "history vector",
        )
        require(
            item
            == {
                "correction": CORRECTION,
                "implementation": IMPLEMENTATION,
                "parent": IMPLEMENTATION,
                "tree": CORRECTION_TREE,
            },
            "history vector changed",
        )
    elif validator == "negative":
        validate_negative(payload)
    elif validator == "replay":
        item = exact_keys(
            payload,
            {"prior_r6_sha256", "prior_r7_sha256", "schema", "status"},
            "replay vector",
        )
        require(
            item
            == {
                "prior_r6_sha256": R6_SHA256,
                "prior_r7_sha256": R7_SHA256,
                "schema": "pid-rs/lean-current-project-replay/v2",
                "status": "passed",
            },
            "replay vector changed",
        )
    elif validator == "lean_v2":
        validate_lean_v2_scalar_contract(payload, "Lean-v2 vector")
    elif validator == "active_packet":
        validate_active_packet_revision_contract(payload, "active-packet vector")
    elif validator == "current_source":
        validate_current_source_revision_contract(payload, "current-source vector")
        require(
            payload.get("schema") == "pid-rs/current-source-state",
            "current-source vector schema changed",
        )
    elif validator == "implementation_negative":
        validate_implementation_negative_revision_contract(
            payload, "implementation-negative vector"
        )
        require(
            payload.get("schema") == "pid-rs/ksg-rev4-public-ci-failure/v1",
            "implementation-negative vector schema changed",
        )
    elif validator == "retired_attempt":
        item = exact_keys(
            payload,
            {"checkpoint", "entry_count", "index_sha256", "index_size", "tree"},
            "retired-attempt vector",
        )
        reject_retired_attempt(
            sha1(item["checkpoint"], "retired-attempt checkpoint"),
            sha1(item["tree"], "retired-attempt tree"),
            sha256(item["index_sha256"], "retired-attempt index digest"),
            exact_int(item["index_size"], "retired-attempt index size", 1),
            exact_int(item["entry_count"], "retired-attempt entry count", 1),
        )
    elif validator == "worktree_leaf":
        item = exact_keys(
            payload,
            {"mode", "oid", "path", "role"},
            "worktree-leaf vector",
        )
        validate_path(item["path"])
        mode = item["mode"]
        require(mode in {"100644", "100755"}, "worktree-leaf mode changed")
        oid = sha1(item["oid"], "worktree-leaf oid")
        if item["role"] == "candidate":
            compare_worktree({item["path"]: Entry(mode=mode, oid=oid)})
        elif item["role"] == "authority":
            require(
                object_digest("blob", read_regular(item["path"])) == oid,
                "authority leaf differs from expected blob",
            )
        else:
            raise RecoveryError("worktree-leaf role changed")
    elif validator == "regular_snapshot":
        item = exact_keys(
            payload,
            {
                "after",
                "allow_empty",
                "before",
                "maximum",
                "path_after",
                "path_before",
                "required_mode",
            },
            "regular-snapshot vector",
        )
        required_mode = item["required_mode"]
        require(
            required_mode is None or required_mode in {0o644, 0o755},
            "regular-snapshot mode changed",
        )
        snapshots: dict[str, tuple[int, ...]] = {}
        for key in ("before", "path_before", "after", "path_after"):
            raw_snapshot = item[key]
            require(
                isinstance(raw_snapshot, list)
                and len(raw_snapshot) == 7
                and all(type(value) is int for value in raw_snapshot),
                "regular-snapshot identity malformed",
            )
            snapshots[key] = tuple(raw_snapshot)
        validate_regular_snapshot(
            snapshots["before"],
            snapshots["path_before"],
            snapshots["after"],
            snapshots["path_after"],
            allow_empty=exact_bool(item["allow_empty"], "regular-snapshot allow-empty"),
            maximum=exact_int(item["maximum"], "regular-snapshot maximum", 0),
            required_mode=required_mode,
            label="self-test snapshot",
        )
    elif validator == "workflow":
        item = exact_keys(payload, {"anchor", "candidate"}, "workflow vector")
        validate_workflow_fetch_depth(
            item["anchor"].encode(), item["candidate"].encode()
        )
    elif validator == "wiring":
        item = exact_keys(
            payload, {"just", "readme", "workflow"}, "recovery wiring vector"
        )
        require(
            all(isinstance(item[key], str) for key in item),
            "recovery wiring vector values changed type",
        )
        validate_recovery_wiring(
            item["workflow"].encode(), item["just"].encode(), item["readme"].encode()
        )
    elif validator == "receipt":
        validate_receipt_structure(payload, self_test_vector=True)
    elif validator == "recovery_phase":
        item = exact_keys(payload, {"custody", "expected"}, "recovery phase vector")
        validate_phase_custody(
            item["custody"],
            recovery=True,
            expected_recovery=exact_keys(
                item["expected"],
                {
                    "certified",
                    "checkpoint",
                    "children",
                    "current_source",
                    "delta",
                    "envelope",
                    "failed_correction_anchor",
                    "implementation_anchor",
                    "negative_sha256",
                    "negative_summary",
                    "policy_sha256",
                    "replay",
                    "static",
                    "tree",
                },
                "recovery phase expectations",
            ),
        )
    elif validator == "cert_protocol":
        item = exact_keys(
            payload,
            {
                "candidate_checker_hex",
                "candidate_selftest_hex",
                "correction_checker_hex",
                "correction_selftest_hex",
            },
            "certified protocol vector",
        )
        decoded: dict[str, bytes] = {}
        for key, raw_hex in item.items():
            require(
                isinstance(raw_hex, str) and len(raw_hex) <= 2 * MAX_FILE_BYTES,
                "certified protocol vector frame changed",
            )
            try:
                decoded[key] = bytes.fromhex(raw_hex)
            except ValueError as error:
                raise RecoveryError(
                    "certified protocol vector hex malformed"
                ) from error
        validate_version_stable_cert_protocol(
            decoded["correction_checker_hex"],
            decoded["candidate_checker_hex"],
            decoded["correction_selftest_hex"],
            decoded["candidate_selftest_hex"],
        )
    elif validator == "freeze_inventory":
        item = exact_keys(
            payload,
            {"digests", "sizes", "source_hex", "state"},
            "freeze inventory vector",
        )
        require(
            isinstance(item["digests"], list)
            and isinstance(item["sizes"], list)
            and isinstance(item["source_hex"], str),
            "freeze inventory vector values changed",
        )
        try:
            frozen_source = bytes.fromhex(item["source_hex"])
        except ValueError as error:
            raise RecoveryError("freeze inventory vector source malformed") from error
        validate_freeze_inventory(
            item["state"],
            source=frozen_source,
            digest_pins=tuple(item["digests"]),
            size_pins=tuple(item["sizes"]),
        )
    elif validator == "postcommit_content":
        item = exact_keys(
            payload,
            {"content", "expected_manifest", "head", "tree"},
            "postcommit content vector",
        )
        validate_postcommit_source_state_content(
            item["content"],
            sha1(item["head"], "postcommit content vector head"),
            sha1(item["tree"], "postcommit content vector tree"),
            expected_manifest=exact_keys(
                item["expected_manifest"],
                {
                    "blob_oid",
                    "path",
                    "schema",
                    "schema_revision",
                    "sha256",
                    "size_bytes",
                    "source_projection_entries_sha256",
                    "source_projection_entry_count",
                },
                "postcommit content expected manifest",
            ),
        )
    elif validator == "scalar_types":
        reviewed_fields = (
            BOOLEAN_JSON_FIELDS | INTEGER_JSON_FIELDS | INTEGER_JSON_LIST_FIELDS
        )
        exact_keys(payload, reviewed_fields, "scalar-type inventory vector")
        require_scalar_field_types(payload, "scalar-type inventory vector")
    elif validator == "jobs":
        item = exact_keys(payload, {"api_jobs", "phase_jobs"}, "jobs-path vector")
        validate_api_jobs_container(item["api_jobs"], "jobs-path API jobs")
        validate_phase_jobs_count(item["phase_jobs"], "jobs-path phase jobs")
    elif validator == "source_transport":
        item = exact_keys(
            payload,
            {"bootstrap_sha256", "contains_compile_exec", "isolated_flags"},
            "source transport vector",
        )
        require(
            item["bootstrap_sha256"]
            == hashlib.sha256(PYTHON_SOURCE_BOOTSTRAP.encode()).hexdigest()
            and item["contains_compile_exec"] is True
            and item["isolated_flags"] == ["-I", "-S", "-B"],
            "source transport vector changed",
        )
    elif validator == "raw_tree":
        item = exact_keys(payload, {"expected", "objects", "root"}, "raw-tree vector")
        objects = item["objects"]
        require(
            isinstance(objects, dict) and 0 < len(objects) <= 16,
            "raw-tree object map invalid",
        )
        decoded: dict[str, bytes] = {}
        for oid, raw_hex in objects.items():
            sha1(oid, "raw-tree vector object id")
            require(
                isinstance(raw_hex, str), "raw-tree vector bytes are not hexadecimal"
            )
            try:
                raw = bytes.fromhex(raw_hex)
            except ValueError as error:
                raise RecoveryError("raw-tree vector bytes are malformed") from error
            require(
                object_digest("tree", raw) == oid, "raw-tree vector object id disagrees"
            )
            decoded[oid] = raw
        walked = walk_raw_tree_objects(
            sha1(item["root"], "raw-tree vector root"),
            lambda oid: (
                decoded.get(oid)  # type: ignore[return-value]
                if oid in decoded
                else (_ for _ in ()).throw(RecoveryError("raw-tree object absent"))
            ),
        )
        expected = exact_keys(
            item["expected"], set(item["expected"]), "raw-tree expected"
        )
        require(
            expected
            == {
                path: {"mode": entry.mode, "oid": entry.oid}
                for path, entry in walked.items()
            },
            "raw-tree vector flattened result changed",
        )
    else:
        raise RecoveryError("unsupported self-test validator")


def emit(value: Any) -> None:
    sys.stdout.buffer.write(canonical_json(value, pretty=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--mode", choices=("candidate-commit", "precommit", "postcommit")
    )
    parser.add_argument("--expected-candidate-tree")
    parser.add_argument("--checkpoint-commit")
    parser.add_argument("--alternate-index-sha256")
    parser.add_argument("--alternate-index-entry-count", type=int)
    parser.add_argument("--allow-provisional-diagnostic", action="store_true")
    parser.add_argument("--validate-policy-only", action="store_true")
    parser.add_argument("--validate-composite-receipt", action="store_true")
    parser.add_argument("--self-test-vectors", action="store_true")
    return parser.parse_args()


def run_vector(arguments: argparse.Namespace) -> int:
    require(
        arguments.mode is None
        and arguments.expected_candidate_tree is None
        and arguments.checkpoint_commit is None
        and arguments.alternate_index_sha256 is None
        and arguments.alternate_index_entry_count is None
        and not arguments.allow_provisional_diagnostic
        and not arguments.validate_policy_only
        and not arguments.validate_composite_receipt,
        "self-test vector arguments conflict",
    )
    try:
        validate_self_test_vector(
            parse_json(sys.stdin.buffer.read(MAX_JSON_BYTES + 1), "self-test vector")
        )
    except (RecoveryError, ValueError):
        emit({"result": "fail"})
        return 0
    emit({"result": "pass"})
    return 0


def run_receipt(arguments: argparse.Namespace) -> int:
    require(
        arguments.mode is None
        and arguments.expected_candidate_tree is None
        and arguments.checkpoint_commit is None
        and arguments.alternate_index_sha256 is None
        and arguments.alternate_index_entry_count is None
        and not arguments.allow_provisional_diagnostic
        and not arguments.validate_policy_only,
        "receipt arguments conflict",
    )
    policy, _policy_raw, _rows = load_policy()
    state = policy["authority"]["inventory_status"]
    require(state == "frozen", "receipt validation requires frozen recovery policy")
    validate_freeze_inventory(state)
    validate_static_artifacts(state)
    entry_repository = repository_context()
    entry_branch = lifecycle_branch()
    entry_checker = read_regular(CHECKER_RELATIVE)
    entry_head_entries = parse_tree(entry_repository[1])
    require(
        CHECKER_RELATIVE in entry_head_entries
        and tree_blob(entry_head_entries, CHECKER_RELATIVE) == entry_checker,
        "executing recovery checker differs from tracked receipt-descendant blob",
    )
    raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    value = parse_json(raw, "composite-v3 receipt")
    summary = validate_receipt_structure(value)
    verify_receipt_descendant(raw, summary)
    require(
        repository_context() == entry_repository
        and lifecycle_branch() == entry_branch
        and read_regular(CHECKER_RELATIVE) == entry_checker,
        "repository/config/worktree/checker source changed during receipt validation",
    )
    emit(
        {
            "credit": "none_typed_descendant_receipt_validation_only",
            "disposition": "local_hosted_pending_no_credit",
            "schema": "pid-rs/ksg-rev4-m1a-composite-receipt-v3-validation/v1",
            "summary": summary,
            "validated_receipt_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    return 0


def main() -> int:
    arguments = parse_args()
    if arguments.self_test_vectors:
        return run_vector(arguments)
    if arguments.validate_composite_receipt:
        return run_receipt(arguments)
    policy, policy_raw, rows = load_policy()
    state = policy["authority"]["inventory_status"]
    validate_freeze_inventory(state)
    static = validate_static_artifacts(state)
    implementation, correction, correction_envelope = validate_historical_chain()
    if arguments.validate_policy_only:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None,
            "policy-only arguments conflict",
        )
        require(
            state in {"provisional", "frozen"},
            "wrong provisional/frozen policy disposition",
        )
        emit(
            {
                "correction_commit": CORRECTION,
                "credit": "none_policy_inventory_provisional"
                if state == "provisional"
                else "none_policy_frozen_lifecycle_validation_only",
                "disposition": "local_hosted_pending_no_credit",
                "entry_count": len(rows),
                "implementation_commit": IMPLEMENTATION,
                "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
                "protected_projection": {
                    "entry_count": PROTECTED_COUNT,
                    "sha256": PROTECTED_SHA256,
                },
                "schema": "pid-rs/ksg-rev4-m1a-hosted-recovery-policy-validation/v1",
                "static_artifact_sha256": static,
            }
        )
        return 0
    require(
        state == "frozen" and not arguments.allow_provisional_diagnostic,
        "lifecycle validation requires frozen policy",
    )
    require(
        arguments.mode is not None
        and arguments.expected_candidate_tree is not None
        and arguments.checkpoint_commit is not None,
        "lifecycle mode/tree/checkpoint required",
    )
    candidate_tree = sha1(arguments.expected_candidate_tree, "candidate tree")
    checkpoint = sha1(arguments.checkpoint_commit, "checkpoint")
    candidate = parse_tree(candidate_tree)
    delta = validate_delta(rows, correction, candidate)
    candidate_protected, candidate_protected_sha = protected_projection(candidate)
    implementation_protected, _ = protected_projection(implementation)
    require(
        candidate_protected == implementation_protected
        and candidate_protected_sha == PROTECTED_SHA256,
        "candidate protected projection changed",
    )
    envelope = parse_commit(
        checkpoint, tree=candidate_tree, parent=CORRECTION, recovery=True
    )
    reject_retired_attempt(
        checkpoint,
        candidate_tree,
        envelope["sealed_index_sha256"],
        envelope["sealed_index_size_bytes"],
        len(candidate),
    )
    alternate: dict[str, Any] | None = None
    if arguments.mode == "precommit":
        require(
            arguments.alternate_index_sha256 is not None
            and arguments.alternate_index_entry_count is not None,
            "precommit sealed-index args missing",
        )
        raw, metadata = read_sealed_fd0()
        expected_sha = sha256(
            arguments.alternate_index_sha256, "alternate index digest"
        )
        count = exact_int(
            arguments.alternate_index_entry_count, "alternate index count", 1
        )
        alternate = validate_sealed_index(
            raw, expected_sha, count, candidate_tree, candidate
        )
        require(
            metadata.st_size == len(raw) == envelope["sealed_index_size_bytes"]
            and expected_sha == envelope["sealed_index_sha256"],
            "checkpoint trailer differs from fd0",
        )
    else:
        require(
            arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None,
            "committed lifecycle forbids index args",
        )
    lifecycle = validate_lifecycle(arguments.mode, checkpoint, rows, candidate)
    stable_repository = repository_context()
    stable_branch_state = lifecycle_branch()
    stable_checker_source = read_regular(CHECKER_RELATIVE)
    cert = validate_certified_rebind(correction, candidate)
    negative_raw = tree_blob(candidate, NEGATIVE_RELATIVE)
    require(
        len(negative_raw) == EXPECTED_FROZEN_NEGATIVE_SIZE_BYTES
        and hashlib.sha256(negative_raw).hexdigest() == EXPECTED_FROZEN_NEGATIVE_SHA256,
        "frozen correction negative bytes changed",
    )
    negative = validate_negative(parse_json(negative_raw, "correction negative"))
    replay = validate_replay(candidate)
    children, current_source = validate_children(candidate)
    require(
        repository_context() == stable_repository
        and lifecycle_branch() == stable_branch_state
        and read_regular(CHECKER_RELATIVE) == stable_checker_source
        and validate_lifecycle(arguments.mode, checkpoint, rows, candidate)
        == lifecycle,
        "repository/worktree/source snapshot changed across child execution",
    )
    emit(
        {
            "candidate": {
                "alternate_index_custody": alternate,
                "checkpoint_commit": checkpoint,
                "commit_envelope": envelope,
                "delta": [
                    {"mode": mode, "path": path, "status": status}
                    for path, status, mode in delta
                ],
                "tree": candidate_tree,
            },
            "certified_sxpid_recovery": {
                "four_container_digest_literals": cert,
                "scientific_authority_unchanged": True,
                "self_test_sha256": cert["certified_self_test"],
                "workflow_fetch_depth_zero": True,
            },
            "child_output_sha256": children,
            "credit": "none_local_custody_match_hosted_pending",
            "current_source_manifest_sha256": current_source,
            "disposition": "local_hosted_pending_no_credit",
            "failed_correction_anchor": {
                "commit": CORRECTION,
                "direct_parent": IMPLEMENTATION,
                "full_tree_projection": {
                    "entry_count": CORRECTION_ENTRY_COUNT,
                    "sha256": CORRECTION_TREE_PROJECTION_SHA256,
                    "size_bytes": CORRECTION_TREE_PROJECTION_SIZE_BYTES,
                },
                "protected_projection": {
                    "candidate_equals_anchor": True,
                    "entry_count": PROTECTED_COUNT,
                    "sha256": PROTECTED_SHA256,
                },
                "sealed_index": {
                    "entry_count": CORRECTION_ENTRY_COUNT,
                    "git_blob_oid_sha1": CORRECTION_INDEX_BLOB,
                    "sha256": CORRECTION_INDEX_SHA256,
                    "size_bytes": CORRECTION_INDEX_SIZE_BYTES,
                },
                "tree": CORRECTION_TREE,
            },
            "implementation_anchor": {
                "commit": IMPLEMENTATION,
                "direct_parent": IMPLEMENTATION_PARENT,
                "protected_projection": {
                    "candidate_equals_anchor": True,
                    "entry_count": PROTECTED_COUNT,
                    "sha256": PROTECTED_SHA256,
                },
                "tree": IMPLEMENTATION_TREE,
            },
            "lean_r8": replay,
            "lifecycle": lifecycle,
            "mode": arguments.mode,
            "negative_evidence": {
                "sha256": hashlib.sha256(negative_raw).hexdigest(),
                **negative,
            },
            "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
            "preclosure": {
                "final_decision_absent": True,
                "final_evidence_matrix_absent": True,
                "future_composite_receipt_absent": True,
                "future_retained_indexes_absent": True,
                "open_gate_count": 13,
                "status": "integration_no_go",
            },
            "repository_state": {
                "active_git_operations": [],
                "branch": lifecycle_branch()[0],
            },
            "runtime_mode": sys.flags.optimize,
            "schema": "pid-rs/ksg-rev4-m1a-hosted-recovery-phase-validation/v1",
            "static_artifact_sha256": static,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecoveryError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(f"KSG M1a hosted-recovery check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
