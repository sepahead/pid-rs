#!/usr/bin/env python3
"""Fail closed on the KSG revision-4 M1a custody correction.

The implementation remains the exact cb3f58f0 commit.  This checker validates
only a direct-child lifecycle/custody correction, retains the implementation
head's failed hosted run as zero-credit evidence, and preserves the protected
83-path implementation projection.  A local pass is always hosted-pending.
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
        "ERROR: check-ksg-m1a-custody-correction.py requires Python 3.11+ "
        "-I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
import ast
import csv
import datetime
from dataclasses import dataclass
import fcntl
import hashlib
import io
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
PYTHON_STDIN_BOOTSTRAP = """import hashlib
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
    raise SystemExit("isolated stdin source bootstrap runtime mismatch")
if len(sys.argv) < 4:
    raise SystemExit("isolated stdin source bootstrap arguments missing")
logical_path = sys.argv[1]
expected_sha256 = sys.argv[2]
try:
    expected_size = int(sys.argv[3], 10)
except ValueError:
    raise SystemExit("isolated stdin source bootstrap size malformed") from None
arguments = sys.argv[4:]
if expected_size < 1 or expected_size > 33554432:
    raise SystemExit("isolated stdin source bootstrap size out of range")
source = sys.stdin.buffer.read(expected_size + 1)
if len(source) != expected_size or hashlib.sha256(source).hexdigest() != expected_sha256:
    raise SystemExit("isolated stdin source bootstrap bytes disagree")
sys.stdin = open("/dev/null", "r", encoding="utf-8")
sys.argv = [logical_path, *arguments]
namespace = {
    "__name__": "__main__",
    "__file__": logical_path,
    "__package__": None,
    "__spec__": None,
    "__cached__": None,
}
code = compile(source, logical_path, "exec", dont_inherit=True)
exec(code, namespace, namespace)
"""
EXPECTED_PYTHON_STDIN_BOOTSTRAP_SIZE_BYTES = 1338
EXPECTED_PYTHON_STDIN_BOOTSTRAP_SHA256 = (
    "9e7820e1c8619284c4cefc795ebb49beb40f21de944b2058ef87331fa9ce473c"
)
EXPECTED_PYTHON_STDIN_BOOTSTRAP_AST_SHA256 = (
    "1d2db2894cb2e7b41b7a86dc391101be345c431048c6a6a3cea973ed56dbdab4"
)
SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER_RELATIVE = "scripts/check-ksg-m1a-custody-correction.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-custody-correction-self-test.py"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json"
BOUNDARY_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md"
)
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json"
NEGATIVE_RELATIVE = "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
R5_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json"
R6_RELATIVE = "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
CURRENT_SOURCE_SCHEMA = "audit/schemas/current-source-state-v1.schema.json"
LEAN_CHECKER = "scripts/check-lean-toolchain-freeze.py"
LEAN_SELF_TEST = "scripts/check-lean-toolchain-freeze-self-test.py"
LEAN_GENERATOR = "scripts/generate-lean-4.33-replay.py"
CERT_CHECKER = "scripts/check-certified-sxpid2-claim.py"
CERT_SELF_TEST = "scripts/check-certified-sxpid2-claim-self-test.py"
ACTIVE_PACKET = "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
FINAL_MATRIX = "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md"
FINAL_DECISION = "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md"
FUTURE_COMPOSITE_RECEIPT = (
    "audit/evidence/ksg-rev4-m1a-composite-receipt-2026-08-13.json"
)
FUTURE_RETAINED_INDEX = (
    "audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin"
)
CURRENT_SOURCE_PDF_PATHS = (
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "output/pdf/ecosystem-compatibility-audit.pdf",
    "output/pdf/exact-log-product-sxpid2-assurance.pdf",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "output/pdf/mathematical-problem-solving-workflow.pdf",
    "output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf",
    "output/pdf/two-source-sxpid-count-atom-bridge.pdf",
)
IMPLEMENTATION = "cb3f58f0b190454cb3f1090de8798261ec78f194"
IMPLEMENTATION_TREE = "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0"
IMPLEMENTATION_PARENT = "bbdfda40f0a49a2260b10eafdcb438fc61ae94e9"
PROTECTED_COUNT = 83
PROTECTED_SHA256 = "37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843"
R5_SHA256 = "872175ca504efb24752633704fe13e57802e43ae25bb3c463c4fb8c9dfd073f7"
EXPECTED_SCHEMA_SHA256 = (
    "797e7c5a0dc7122aff6c16319749c3a18683ebbe21e94dd039cdc5b7a330d42c"
)
EXPECTED_SCHEMA_TYPED_CONST_PROJECTION_COUNT = 78
EXPECTED_SCHEMA_TYPED_CONST_PROJECTION_SHA256 = (
    "4783fa9ce5560f4d1fd2efcc10161806ac5fe71fe372add5fefe4880463f005f"
)
EXPECTED_SCHEMA_BOOLEAN_CONTROL_PROJECTION_COUNT = 56
EXPECTED_SCHEMA_BOOLEAN_CONTROL_PROJECTION_SHA256 = (
    "f7935fbe2ab11427d708bc2ca89bcd3a260bfde2d6de88ad10f7b72e3664e221"
)
EXPECTED_BOUNDARY_SIZE_BYTES = 8_814
EXPECTED_BOUNDARY_SHA256 = (
    "591bccc8e770b9b51ab34ce8cce9d2ac54973c50185141e1a598fd90260dcc16"
)
EXPECTED_CORRECTION_SELFTEST_SIZE_BYTES = 119_142
EXPECTED_CORRECTION_SELFTEST_SHA256 = (
    "a466461b9eecd4afd3f839aa8137a6fc6b4de13e1aa6e18dc81b0862c6f0fdcb"
)
EXPECTED_NEGATIVE_SHA256 = (
    "f4a187516847c9826e9729c83906e1598df4657bc069c54a5527e71bdde17dc5"
)
EXPECTED_NEGATIVE_SIZE_BYTES = 484_959
EXPECTED_LEAN_ANCHOR_CHECKER_SIZE_BYTES = 94_778
EXPECTED_LEAN_ANCHOR_CHECKER_SHA256 = (
    "a7bb586857d28aecba2a9800cd03e55e6485c412fdb5232913cca3f989ff6e72"
)
EXPECTED_LEAN_ANCHOR_SELFTEST_SIZE_BYTES = 87_737
EXPECTED_LEAN_ANCHOR_SELFTEST_SHA256 = (
    "805ca781a62a95e19559deae2ebdd70a66f1bee057a59985aa6c1ae69088bf0f"
)
EXPECTED_LEAN_ANCHOR_GENERATOR_SIZE_BYTES = 50_589
EXPECTED_LEAN_ANCHOR_GENERATOR_SHA256 = (
    "1a306b79476bd526d74c4fa23401ee6daf781b36d74bc13a6fd32b161710332a"
)
EXPECTED_LEAN_SELFTEST_SIZE_BYTES = 100_715
EXPECTED_LEAN_SELFTEST_SHA256 = (
    "40f93dc5a7e820c5feebb0f3332034d35469b9cf88a04bcb2e5b10e735d39d56"
)
EXPECTED_LEAN_GENERATOR_SIZE_BYTES = 50_589
EXPECTED_LEAN_GENERATOR_SHA256 = (
    "58d52accca9ce043ec720cf66e8f4cca7f612c692f5b7ca372723a4a0c0fde0d"
)
# This pin is prospectively filled only after every non-cycle Lean checker byte
# freezes.  Its normalization cuts exactly the correction-checker map value and
# the replay-receipt projection assignment, avoiding a C<->L digest cycle.
EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES = 97_352
EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256 = (
    "39a24616db303cd0813baab726e1c465d276bac68180989ab4a8d4985c62c433"
)
LEAN_REPLAY_PROJECTION_ASSIGNMENT = "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256"
LEAN_OPERATIONAL_ASSIGNMENT = "EXPECTED_OPERATIONAL_WIRING_HASHES"
LEAN_CORRECTION_CHECKER_MAP_KEY = CHECKER_RELATIVE
LEAN_R5_RECEIPT_LEAF = (
    "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json"
)
LEAN_R6_RECEIPT_LEAF = (
    "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json"
)
EXPECTED_IMPLEMENTATION_CI_PROJECTION_SHA256 = (
    "7bfaa85a32790072a7d3eeb3a88a02e3d2f71bf2e7c5bee3f3efa6bf73993935"
)
EXPECTED_IMPLEMENTATION_CODEQL_JOB_PROJECTION_SHA256 = (
    "795ca7a2fd97e0491b0cb0f6c3f297ea9817d9ee61c85b14e38aa8fb82ea3b53"
)
EXPECTED_IMPLEMENTATION_CODEQL_ANALYSIS_PROJECTION_SHA256 = (
    "8daa926dfc35fbbbe0c2e90bffbd60ef8d8c1ae83b8f51e94c25df4b92da4e8e"
)
EXPECTED_IMPLEMENTATION_CAPTURE_SHA256 = {
    "ci_job_step_roster": EXPECTED_IMPLEMENTATION_CI_PROJECTION_SHA256,
    "ci_run_summary": "d21ab098e85af71509681cc96a2539c8bb462e595c4515604556a8e732895164",
    "codeql_alert_state": "51ab4929b4e5162befb56f3ac66e3b9d4b247a8060aa609748f5098263ef58bf",
    "codeql_job_analysis_roster": "39e58aa01eeeb0201421b8baa2b79a8c9834f0a6744dce66aca093b14829432d",
    "codeql_run_summary": "92e7294a697a387220665fd1b3ae57298c28e7f076374c5fe4f98c285e4c1ff5",
    "postcommit_source_state_v2_artifact": "837041344b20abac2d36b86dfbf3cd2ead7c59b0a1bc3fa2084791b61f6db9fc",
}
CORRECTION_WIRING_MARKERS = {
    ".github/workflows/ci.yml": (
        "# BEGIN KSG_M1A_CUSTODY_CORRECTION_WORKFLOW_V1",
        "# END KSG_M1A_CUSTODY_CORRECTION_WORKFLOW_V1",
        4286,
        "db153a4ade266a65dc9ca1cdb5b537bca64da0956b95dcc9f2034e36d2a04ff1",
    ),
    "justfile": (
        "# BEGIN KSG_M1A_CUSTODY_CORRECTION_JUST_V1",
        "# END KSG_M1A_CUSTODY_CORRECTION_JUST_V1",
        419,
        "929780bec2c8a28d8684aaa9b2f9cab7dcb321400e8792ce0bbdab598c1376d1",
    ),
    "scripts/README.md": (
        "<!-- BEGIN KSG_M1A_CUSTODY_CORRECTION_README_V1 -->",
        "<!-- END KSG_M1A_CUSTODY_CORRECTION_README_V1 -->",
        5718,
        "9b5e64701185b317b90758fb08e99e45369e751a4a517e176407cccfe71f1c20",
    ),
}
EXPECTED_CORRECTION_WIRING_FULL_FILES = {
    ".github/workflows/ci.yml": (
        66_490,
        "be1ce389b90b613defc86d1aafd6a17fce641f187eb83b55b43b0f537dd9deb6",
    ),
    "justfile": (
        24_407,
        "dfd5e270e8c7f84b5e9887bf9556384280d3d9ca933403d65170d5980a972212",
    ),
    "scripts/README.md": (
        121_247,
        "87a27ec193bf29a2e769c2dba143a86a9d4d56c37051376c1b85d0abb493f2ca",
    ),
}
EXPECTED_WORKFLOW_JOB_SIZE_BYTES = 16_298
EXPECTED_WORKFLOW_JOB_SHA256 = (
    "59ab80ab98cf203e8e15b731f795d076cb780f42b87fc7dff90c9d15464f8732"
)
EXPECTED_JUST_RECIPE_SIZE_BYTES = 2_053
EXPECTED_JUST_RECIPE_SHA256 = (
    "ea2973eaf9b5268187aaa0ad32c40aaccb402893b5f4b2d57a045efdf9ab8ab1"
)
EXPECTED_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"
EXPECTED_TIMEZONE = "+0200"
EXPECTED_MESSAGE_TEMPLATE = (
    "Correct KSG M1a hosted custody wiring\n\n"
    "Sealed-index-SHA256: <lowercase-sha256>\n"
    "Sealed-index-Size: <canonical-decimal-bytes>\n"
)
EXPECTED_LIVE_POLICY_STATE = "frozen"
# Freeze protocol: replace this zero placeholder with the reviewed frozen policy
# digest at the same time as the policy and boundary state markers are frozen.
EXPECTED_FROZEN_POLICY_SHA256 = (
    "8797335e0f23240f6f018c4403caff1a6c209f9c110ffeaa91fb47503bf331ed"
)
EXPECTED_REBIND_PATHS = (
    ".github/workflows/ci.yml",
    "justfile",
    "scripts/README.md",
)
EXPECTED_CERT_REVIEWED_DOC_PATHS = (
    "audit/tools/certified-sxpid/README.md",
    "scripts/README.md",
)
EXPECTED_CERT_BOOTSTRAP_AST_SHA256 = (
    "049be32c1dcbfdb0d402408e3bb52c57c9891ab731e4a002c91b0d2e4f3012c0"
)
EXPECTED_CERT_BOOTSTRAP_SHA256 = (
    "1129a9c3987603fbf16507edc8adebc54a69f7a9acf68494a099247bf41a6106"
)
EXPECTED_CERT_BOOTSTRAP_SIZE_BYTES = 668
CERT_BOOTSTRAP_BEGIN = "# BEGIN KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
CERT_BOOTSTRAP_END = "# END KSG_M1A_CUSTODY_CHECKER_BOOTSTRAP_V1"
EXPECTED_CERT_GATE_COMMANDS = (
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "python3 scripts/check-lean-exact-log-product.py",
    "python3 -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py",
    "python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
    "python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py",
)
EXPECTED_CERT_NARROW_REBINDS = {
    "EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256": (
        "c2032b35d8ca3de8f00273ef76b577650a602e43c5d6190eb062d975e84f0c3c",
        "5b34fa8061b525efdddd813aea936300718d56d3e8402fe2796a63cc70cae5c9",
    ),
    "EXPECTED_JUST_CERTIFIED_SXPID_RECIPE_SHA256": (
        "d706ca9cdb493933cc35701677a5fcb50c7650c71aa617e6caa644f04c7a5747",
        "fbd80548b0c62cb46f646e77e5f1df37d439299e71faec9bd05656839f660ae7",
    ),
}
EXPECTED_CERT_RELEASE_LINE_SHA256 = (
    "ffae544532b91adfbbc3067fcf08a67ed692d63dcff4c807a623a4c2895fb4b1"
)
EXPECTED_CERT_PRIVATE_PROTOCOL_AST_SHA256 = (
    "ff86f5f4aeb19afbe0827be1895de38701ce6e2ddbab61c85f4c45568e6ba911"
)
EXPECTED_CERT_PRIVATE_PROTOCOL_SHA256 = (
    "cab243329941efab04a038b67690ec912c30d8c4b59b7bc7f0d705601b55f6de"
)
EXPECTED_CERT_PRIVATE_PROTOCOL_SIZE_BYTES = 9085
EXPECTED_CERT_SELFTEST_SIZE_BYTES = 114_214
EXPECTED_CERT_SELFTEST_SHA256 = (
    "bb27185f13f373fe3d4d0f2d3eb94255c3ba522d91520f368cd1fbaa39950324"
)
EXPECTED_CERT_SELFTEST_LAUNCHER_SIZE_BYTES = 2776
EXPECTED_CERT_SELFTEST_LAUNCHER_SHA256 = (
    "e843b76db3f67b3bb331be12b346423a10e748edaf119c920d06b71318de95e8"
)
EXPECTED_CHILD_STDOUT = {
    CERT_CHECKER: (
        b"OK: certified SxPID2 claim revisions 1-3, schemas, evidence, "
        b"catalog, and gates are coherent\n"
    ),
    CERT_SELF_TEST: (b"OK: 121 certified-SxPID2 revision mutations were rejected\n"),
    LEAN_CHECKER: (
        b"OK: Lean 4.33.0 remains frozen to the exact release/commit, "
        b"nine-package closure, 11 source files, 3 Fintype-derivation command "
        b"scopes plus 4 proof-term scopes, current replay evidence, six "
        b"derived-instance printed-skeleton comparisons, and 19 byte-preserved "
        b"historical 4.32 artifacts, plus 6 byte-preserved prior 4.33 replay\n"
    ),
    LEAN_SELF_TEST: (
        b"OK: Lean 4.33 freeze self-test rejected all 101 policy, replay, "
        b"source-scope, pin, historical, derived-evidence, canonical-JSON, "
        b"symlink, and hard-link mutations\n"
    ),
}
EXPECTED_CHILD_STDOUT_SHA256 = {
    path: hashlib.sha256(raw).hexdigest() for path, raw in EXPECTED_CHILD_STDOUT.items()
}
EXPECTED_CERT_PRIVATE_FUNCTIONS = (
    "canonical_json_bytes",
    "parse_canonical_json_bytes",
    "exact_mapping",
    "snapshot_data",
    "decode_self_test_json_value",
    "snapshot_from_delta",
    "snapshot_without_unfrozen_container_pins",
    "emit_self_test_result",
    "emit_self_test_failure",
    "require_private_runtime_mode",
    "run_self_test_vector_mode",
    "parse_args",
)
CERT_PRIVATE_BEGIN = "# BEGIN KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
CERT_PRIVATE_END = "# END KSG_M1A_CUSTODY_PRIVATE_TEST_VECTOR_V1"
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
    ".github/workflows/ci.yml": ("M", "hosted_correction_wiring"),
    "AGENTS.md": ("M", "lean_r6_pointer_consequence"),
    "CHANGELOG.md": ("M", "mandatory_release_record"),
    "audit/evidence/completion-active-resume.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    CURRENT_SOURCE_RELATIVE: ("M", "self_excluding_source_state"),
    BOUNDARY_RELATIVE: ("A", "correction_authority"),
    POLICY_RELATIVE: ("A", "correction_authority"),
    NEGATIVE_RELATIVE: ("A", "retained_hosted_negative"),
    R6_RELATIVE: ("A", "lean_r6_execution_custody"),
    "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md": (
        "M",
        "durable_program_coordination",
    ),
    "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    SCHEMA_RELATIVE: ("A", "correction_authority"),
    "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md": (
        "M",
        "lean_r6_pointer_consequence",
    ),
    "justfile": ("M", "hosted_correction_wiring"),
    "scripts/README.md": ("M", "correction_docs_and_lean_r6_pointer"),
    CERT_SELF_TEST: ("M", "certified_sxpid_cli_selftest_custody"),
    CERT_CHECKER: ("M", "certified_sxpid_rebind_and_cli_protocol_custody"),
    SELF_TEST_RELATIVE: ("A", "correction_verifier_self_cut"),
    CHECKER_RELATIVE: ("A", "correction_verifier_self_cut"),
    LEAN_SELF_TEST: (
        "M",
        "lean_r6_custody",
    ),
    LEAN_CHECKER: ("M", "lean_r6_custody"),
    LEAN_GENERATOR: ("M", "lean_r6_custody"),
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTITY = re.compile(
    rb"(?P<name>[^\n<>]+) <(?P<email>[^\n<>\s]+)> "
    rb"(?P<epoch>[1-9][0-9]*) (?P<timezone>[+-][0-9]{4})"
)
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_INDEX_BYTES = 64 * 1024 * 1024
MAX_INTERPRETER_BYTES = 128 * 1024 * 1024
FIXED_TEMP_ROOT_LINK = Path("/tmp")
FIXED_GIT_CONFIG = (
    "core.attributesFile=/dev/null",
    "core.fsmonitor=false",
    "core.hooksPath=/dev/null",
    "core.ignoreCase=false",
    "core.untrackedCache=false",
    "diff.external=",
)
SELF_TEST_VECTOR_SCHEMA = "pid-rs/ksg-rev4-m1a-custody-correction-self-test-vector/v1"
COMPOSITE_RECEIPT_SCHEMA = "pid-rs/ksg-rev4-m1a-composite-receipt/v2"
JOB_PROJECTION_ENCODING = "canonical compact sorted-key ASCII JSON plus LF over job-id-sorted rows with number-sorted steps"
ANALYSIS_PROJECTION_ENCODING = (
    "canonical compact sorted-key ASCII JSON plus LF over language-sorted analysis rows"
)
EXPECTED_CI_JOB_NAMES = tuple(
    sorted(
        (
            "All features / macos-latest",
            "All features / windows-latest",
            "Core all-features",
            "Core experimental-all",
            "Core experimental-continuous",
            "Core experimental-heuristics",
            "Core experimental-hierarchy",
            "Core experimental-hyperbolic",
            "Core experimental-pipelines",
            "Core no-default-features",
            "Core parallel",
            "Core research-mixed-dimension-pid3",
            "Coverage threshold",
            "Deterministic property and identity suites",
            "Exact-count SxPID2 reference / MSRV 1.89",
            "Exact-count directed-rounding SxPID2 reference",
            "Examples + exp0 + run-log replay",
            "Fixed fuzz corpus smoke",
            "Formal LaTeX / PDF inventory and cross-toolchain structure",
            "Formal proof cores, frozen Lean 4.33.0 replay, and historical packet custody",
            "KSG integer-harmonic arithmetic and phase isolation",
            "MSRV 1.89 / all-features",
            "MSRV 1.89 / default",
            "MSRV 1.89 / no-default-features",
            "Miri / pure safe-Rust boundaries",
            "Package + semver + unused dependencies",
            "Python 3.11 / NumPy 1.26.4 / macos-latest",
            "Python 3.11 / NumPy 1.26.4 / ubuntu-latest",
            "Python 3.11 / NumPy 1.26.4 / windows-latest",
            "Python 3.12 / NumPy 1.26.4 / ubuntu-latest",
            "Python 3.13 / NumPy 2.5.1 / ubuntu-latest",
            "Python 3.14 / NumPy 2.5.1 / macos-latest",
            "Python 3.14 / NumPy 2.5.1 / ubuntu-latest",
            "Python 3.14 / NumPy 2.5.1 / windows-latest",
            "Python experimental namespace smoke",
            "Release scope and scientific evidence coherence",
            "Release-mode numerical fixtures",
            "Rustdoc + docs.rs configuration",
            "Rustfmt + Clippy",
            "Secret scan (full history)",
            "Supply chain without advisory exceptions",
            "Workspace CycloneDX SBOM",
            "Workspace default / macos-latest",
            "Workspace default / ubuntu-latest",
            "Workspace default / windows-latest",
        )
    )
)
EXPECTED_IMPLEMENTATION_CI_JOB_IDENTITIES = (
    (94402437657, "Formal LaTeX / PDF inventory and cross-toolchain structure"),
    (94402437669, "Workspace default / ubuntu-latest"),
    (94402437670, "Coverage threshold"),
    (94402437689, "KSG integer-harmonic arithmetic and phase isolation"),
    (94402437700, "Rustdoc + docs.rs configuration"),
    (94402437706, "Release-mode numerical fixtures"),
    (94402437721, "Exact-count SxPID2 reference / MSRV 1.89"),
    (94402437738, "Supply chain without advisory exceptions"),
    (94402437742, "Workspace default / windows-latest"),
    (
        94402437753,
        "Formal proof cores, frozen Lean 4.33.0 replay, and historical packet custody",
    ),
    (94402437784, "Exact-count directed-rounding SxPID2 reference"),
    (94402437787, "Workspace default / macos-latest"),
    (94402437804, "Core experimental-hyperbolic"),
    (94402437838, "MSRV 1.89 / no-default-features"),
    (94402437844, "MSRV 1.89 / default"),
    (94402437851, "Examples + exp0 + run-log replay"),
    (94402437869, "Python 3.11 / NumPy 1.26.4 / macos-latest"),
    (94402437883, "Core no-default-features"),
    (94402437884, "Rustfmt + Clippy"),
    (94402437886, "Workspace CycloneDX SBOM"),
    (94402437895, "Python 3.14 / NumPy 2.5.1 / ubuntu-latest"),
    (94402437896, "Core experimental-pipelines"),
    (94402437903, "Deterministic property and identity suites"),
    (94402437904, "All features / macos-latest"),
    (94402437906, "Core research-mixed-dimension-pid3"),
    (94402437907, "Secret scan (full history)"),
    (94402437910, "Python 3.14 / NumPy 2.5.1 / macos-latest"),
    (94402437921, "Core all-features"),
    (94402437922, "Python 3.11 / NumPy 1.26.4 / windows-latest"),
    (94402437926, "Python experimental namespace smoke"),
    (94402437929, "All features / windows-latest"),
    (94402437930, "Fixed fuzz corpus smoke"),
    (94402437939, "Python 3.11 / NumPy 1.26.4 / ubuntu-latest"),
    (94402437946, "Core parallel"),
    (94402437949, "Python 3.13 / NumPy 2.5.1 / ubuntu-latest"),
    (94402437955, "Python 3.14 / NumPy 2.5.1 / windows-latest"),
    (94402437969, "Package + semver + unused dependencies"),
    (94402437993, "Core experimental-hierarchy"),
    (94402438014, "Miri / pure safe-Rust boundaries"),
    (94402438016, "Python 3.12 / NumPy 1.26.4 / ubuntu-latest"),
    (94402438017, "Core experimental-continuous"),
    (94402438031, "Core experimental-heuristics"),
    (94402438093, "MSRV 1.89 / all-features"),
    (94402438096, "Release scope and scientific evidence coherence"),
    (94402438150, "Core experimental-all"),
)


class CorrectionError(RuntimeError):
    """A bounded correction requirement failed."""


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
        raise CorrectionError(message)


def fixed_temp_root() -> Path:
    root = FIXED_TEMP_ROOT_LINK.resolve(strict=True)
    state = root.lstat()
    validate_temporary_root_security(
        is_directory=stat.S_ISDIR(state.st_mode),
        is_symlink=stat.S_ISLNK(state.st_mode),
        owner_uid=state.st_uid,
        sticky=bool(state.st_mode & stat.S_ISVTX),
    )
    return root


def validate_temporary_root_security(
    *, is_directory: Any, is_symlink: Any, owner_uid: Any, sticky: Any
) -> None:
    require(
        is_directory is True
        and is_symlink is False
        and type(owner_uid) is int
        and owner_uid == 0
        and sticky is True,
        "fixed temporary root is absent or lacks root-owned sticky-directory custody",
    )


def validate_fixed_git_config(value: Any) -> None:
    require(
        type(value) is list
        and all(type(assignment) is str for assignment in value)
        and tuple(value) == FIXED_GIT_CONFIG,
        "fixed Git configuration inventory changed",
    )


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
        raise CorrectionError(f"cannot canonicalize JSON: {error}") from error
    return (rendered + "\n").encode("ascii")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CorrectionError(f"duplicate JSON key is forbidden: {key!r}")
        value[key] = item
    return value


def reject_constant(value: str) -> Any:
    raise CorrectionError(f"non-finite JSON constant is forbidden: {value}")


def parse_json_bytes(raw: bytes, label: str, *, canonical: bool) -> Any:
    require(0 < len(raw) <= MAX_JSON_BYTES, f"{label} exceeds JSON byte bound")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise CorrectionError(f"{label} is not strict UTF-8 JSON: {error}") from error
    if canonical:
        require(
            raw == canonical_json(value, pretty=True), f"{label} is not canonical JSON"
        )
    return value


def stat_identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def validate_path_descriptor_identity(
    path_before: tuple[int, ...],
    descriptor_before: tuple[int, ...],
    descriptor_after: tuple[int, ...],
    path_after: tuple[int, ...],
    label: str,
) -> None:
    require(
        path_before == descriptor_before == descriptor_after == path_after,
        f"{label} path/descriptor identity changed",
    )


def read_regular(relative: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    path = ROOT / relative
    path_before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 <= before.st_size <= maximum,
            f"path lacks bounded single-link regular-file custody: {relative}",
        )
        require(
            stat_identity(path_before) == stat_identity(before),
            f"path changed while opened: {relative}",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            require(chunk, f"short descriptor read: {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"path grew while read: {relative}")
        after = os.fstat(descriptor)
        path_after = path.lstat()
        require(
            stat_identity(before) == stat_identity(after) == stat_identity(path_after),
            f"path changed while read: {relative}",
        )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


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
    before = executable.lstat()
    require(
        stat.S_ISREG(before.st_mode) and executable.resolve(strict=True) == executable,
        "fixed Git executable is not a canonical regular file",
    )
    environment = safe_environment()
    if extra_environment is not None:
        require(
            set(extra_environment) <= {"GIT_INDEX_FILE"},
            "unsupported Git environment override",
        )
        environment.update(extra_environment)
    command = [os.fspath(executable)]
    for assignment in FIXED_GIT_CONFIG:
        command.extend(("-c", assignment))
    command.extend(("-C", os.fspath(ROOT), *arguments))
    completed = subprocess.run(
        command,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    require(
        len(completed.stdout) <= MAX_GIT_OUTPUT_BYTES
        and len(completed.stderr) <= MAX_GIT_OUTPUT_BYTES,
        "Git output exceeds byte bound",
    )
    after = executable.lstat()
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
        raise CorrectionError(
            f"Git command failed ({completed.returncode}): {arguments!r}: {detail}"
        )
    if not check:
        require(0 <= completed.returncode <= 255, "Git return code is out of range")
        return bytes([completed.returncode]) + completed.stdout
    return completed.stdout


def git_text(*arguments: str, extra_environment: dict[str, str] | None = None) -> str:
    return (
        git(*arguments, extra_environment=extra_environment)
        .decode("utf-8", errors="strict")
        .rstrip("\n")
    )


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
        f"unsafe/noncanonical repository path: {path!r}",
    )


def parse_raw_tree_object(raw: bytes, label: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    offset = 0
    while offset < len(raw):
        space = raw.find(b" ", offset)
        nul = raw.find(b"\0", space + 1)
        require(space > offset and nul > space, f"malformed raw tree object: {label}")
        mode = raw[offset:space].decode("ascii", errors="strict")
        name_raw = raw[space + 1 : nul]
        require(
            b"/" not in name_raw and name_raw not in {b"", b".", b".."},
            f"unsafe tree component: {label}",
        )
        name = name_raw.decode("utf-8", errors="strict")
        oid_raw = raw[nul + 1 : nul + 21]
        require(len(oid_raw) == 20, f"truncated tree object id: {label}")
        rows.append((mode, name, oid_raw.hex()))
        offset = nul + 21
    require(offset == len(raw), f"trailing raw tree bytes: {label}")
    return rows


def walk_raw_tree_objects(tree: str, load_tree: Any) -> dict[str, Entry]:
    require(HEX40.fullmatch(tree) is not None, "tree id is malformed")
    entries: dict[str, Entry] = {}
    seen_trees: set[str] = set()

    def visit(oid: str, prefix: str) -> None:
        require(oid not in seen_trees, f"tree object is recursively repeated: {oid}")
        seen_trees.add(oid)
        raw_object = load_tree(oid)
        require(
            isinstance(raw_object, bytes) and len(raw_object) <= MAX_GIT_OUTPUT_BYTES,
            f"tree loader returned invalid bytes: {oid}",
        )
        for mode, name, child_oid in parse_raw_tree_object(raw_object, prefix or "."):
            path = f"{prefix}/{name}" if prefix else name
            validate_path(path)
            if mode == "40000":
                before = len(entries)
                visit(child_oid, path)
                require(
                    len(entries) > before,
                    f"nested tree contributes no blob leaf: {path}",
                )
                continue
            require(mode in {"100644", "100755"}, f"unsupported tree mode: {mode}")
            require(path not in entries, f"duplicate tree path: {path}")
            entries[path] = Entry(mode, child_oid)

    visit(tree, "")
    require(bool(entries), "root tree contributes no blob leaves")
    return dict(sorted(entries.items()))


def parse_tree(tree: str) -> tuple[dict[str, Entry], bytes]:
    ordered = walk_raw_tree_objects(
        tree,
        lambda oid: exact_object(oid, "tree", maximum=MAX_GIT_OUTPUT_BYTES),
    )
    raw = git("ls-tree", "-rz", "-r", "--full-tree", tree)
    require(not raw or raw.endswith(b"\0"), "tree listing lacks NUL termination")
    listed: dict[str, Entry] = {}
    for record in raw[:-1].split(b"\0") if raw else []:
        prefix, separator, path_raw = record.partition(b"\t")
        require(separator == b"\t", "malformed tree entry")
        fields = prefix.split(b" ")
        require(
            len(fields) == 3 and fields[1] == b"blob", "non-blob/malformed tree leaf"
        )
        path = path_raw.decode("utf-8", errors="strict")
        listed[path] = Entry(fields[0].decode("ascii"), fields[2].decode("ascii"))
    require(
        list(listed) == sorted(listed) and listed == ordered,
        "recursive raw-tree walk disagrees with sorted Git listing",
    )
    return ordered, raw


def exact_object(oid: str, kind: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    require(HEX40.fullmatch(oid) is not None, f"{kind} id is malformed")
    require(git_text("cat-file", "-t", oid) == kind, f"object is not {kind}: {oid}")
    raw = git("cat-file", kind, oid)
    require(len(raw) <= maximum, f"{kind} object exceeds byte bound")
    digest = hashlib.sha1(  # noqa: S324 -- Git SHA-1 object identity.
        f"{kind} {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()
    require(digest == oid, f"{kind} bytes do not match object id")
    return raw


def blob_oid(raw: bytes) -> str:
    return hashlib.sha1(  # noqa: S324 -- Git SHA-1 object identity.
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def candidate_blob(candidate: dict[str, Entry], path: str) -> bytes:
    entry = candidate.get(path)
    require(entry is not None, f"candidate path is absent: {path}")
    return exact_object(entry.oid, "blob")


def changed_entries(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> tuple[tuple[str, str, str], ...]:
    result: list[tuple[str, str, str]] = []
    for path in sorted(set(anchor) | set(candidate)):
        old = anchor.get(path)
        new = candidate.get(path)
        if old == new:
            continue
        if old is None and new is not None:
            result.append((path, "A", new.mode))
        elif new is None and old is not None:
            result.append((path, "D", old.mode))
        elif new is not None:
            result.append((path, "M", new.mode))
    return tuple(result)


def validate_policy_data(value: Any, *, verify_anchor: bool) -> tuple[PolicyEntry, ...]:
    reject_json_floats(value, "correction policy")
    reject_numeric_boolean_aliases(value, "correction policy")
    require_boolean_field_types(value, "correction policy")
    require(isinstance(value, dict), "policy root must be an object")
    require(
        set(value)
        == {
            "authority",
            "commit_envelope",
            "deletions_permitted",
            "entries",
            "forbidden_contexts",
            "implementation_anchor",
            "receipt_contract",
            "review_classes",
            "schema",
            "schema_revision",
        },
        "policy top-level shape changed",
    )
    require(
        value.get("schema") == "pid-rs/ksg-rev4-m1a-custody-correction-path-policy"
        and type(value.get("schema_revision")) is int
        and value["schema_revision"] == 1,
        "policy schema identity changed",
    )
    authority = value.get("authority")
    require(
        isinstance(authority, dict)
        and set(authority)
        == {
            "credit_permitted",
            "freeze_instruction",
            "inventory_status",
            "lifecycle_validation_permitted",
            "mechanical_resealing_permitted",
            "provisional_disposition",
            "scope",
        },
        "policy authority shape changed",
    )
    status = authority.get("inventory_status")
    credit = authority.get("credit_permitted")
    lifecycle_validation = authority.get("lifecycle_validation_permitted")
    require(
        status in {"provisional", "frozen"}
        and type(credit) is bool
        and type(lifecycle_validation) is bool,
        "policy state malformed",
    )
    require(
        credit is False, "local policy must never permit lifecycle or scientific credit"
    )
    require(
        lifecycle_validation == (status == "frozen"),
        "exact lifecycle validation is enabled exactly when policy is frozen",
    )
    require(
        authority.get("mechanical_resealing_permitted") is False
        and authority.get("provisional_disposition") == "local_hosted_pending_no_credit"
        and "Never mechanically accept" in authority.get("freeze_instruction", "")
        and "implementation bytes remain cb3f58f0" in authority.get("scope", ""),
        "policy authority semantics weakened",
    )
    freeze_instruction = authority["freeze_instruction"]
    for token in (
        "prospectively derive",
        "Patch the checker and prospective Lean maps first",
        "final authored edits",
        "no authored byte may change",
        "append-only r6 receipt/checker cycle finalization",
        "self-excluding current-source generation",
        "construct the final authored correction tree and its exact sealed index",
        "strict dynamic message trailer commits the index SHA-256",
        "before precommit validation or any ref update",
    ):
        require(token in freeze_instruction, f"freeze-order token disappeared: {token}")
    require(value.get("deletions_permitted") is False, "policy permits deletion")
    anchor = value.get("implementation_anchor")
    if isinstance(anchor, dict) and isinstance(
        anchor.get("protected_projection"), dict
    ):
        exact_integer(
            anchor["protected_projection"].get("entry_count"),
            "policy protected projection entry count",
            minimum=PROTECTED_COUNT,
            maximum=PROTECTED_COUNT,
        )
    require(
        isinstance(anchor, dict)
        and anchor.get("commit") == IMPLEMENTATION
        and anchor.get("tree") == IMPLEMENTATION_TREE
        and anchor.get("direct_parent") == IMPLEMENTATION_PARENT
        and anchor.get("protected_projection")
        == {
            "entry_count": PROTECTED_COUNT,
            "format": "canonical compact sorted-key ASCII JSON plus LF over sorted {path,git_mode,git_blob_oid_sha1,sha256,size_bytes} rows",
            "sha256": PROTECTED_SHA256,
        },
        "policy implementation anchor/projection changed",
    )
    identity = {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
    envelope = value.get("commit_envelope")
    if isinstance(envelope, dict):
        exact_integer(
            envelope.get("parent_count"),
            "policy checkpoint parent count",
            minimum=1,
            maximum=1,
        )
    require(
        envelope
        == {
            "author": identity,
            "author_and_committer_headers_identical": True,
            "committer": identity,
            "message_template": EXPECTED_MESSAGE_TEMPLATE,
            "parent_count": 1,
            "signature_headers_permitted": False,
            "timezone": EXPECTED_TIMEZONE,
        },
        "policy commit envelope changed",
    )
    review_classes = value.get("review_classes")
    require(
        isinstance(review_classes, dict)
        and set(review_classes)
        == {
            "certified_sxpid_cli_selftest_custody",
            "certified_sxpid_rebind_and_cli_protocol_custody",
            "correction_docs_and_lean_r6_pointer",
            "correction_authority",
            "correction_verifier_self_cut",
            "durable_program_coordination",
            "hosted_correction_wiring",
            "lean_r6_custody",
            "lean_r6_execution_custody",
            "lean_r6_pointer_consequence",
            "mandatory_release_record",
            "retained_hosted_negative",
            "self_excluding_source_state",
        },
        "policy review classes changed",
    )
    require(
        "exact marked isolation bootstrap"
        in review_classes["certified_sxpid_rebind_and_cli_protocol_custody"]
        and "AST-bound fixed private CLI vector protocol"
        in review_classes["certified_sxpid_rebind_and_cli_protocol_custody"]
        and "narrow certified CI-job and Just-recipe digests"
        in review_classes["certified_sxpid_rebind_and_cli_protocol_custody"]
        and "release-audit-line digest and every other pre-existing semantic definition"
        in review_classes["certified_sxpid_rebind_and_cli_protocol_custody"],
        "certified-SxPID rebind boundary weakened",
    )
    require(
        "fixed private CLI vector interface"
        in review_classes["certified_sxpid_cli_selftest_custody"]
        and "unchecked bytecode"
        in review_classes["certified_sxpid_cli_selftest_custody"],
        "certified-SxPID self-test custody boundary weakened",
    )
    require(
        "candidate-tree blob supplied on standard input"
        in review_classes["correction_verifier_self_cut"]
        and "no mutable child-source pathname reopen"
        in review_classes["correction_verifier_self_cut"],
        "correction child executed-byte custody boundary weakened",
    )
    rows = value.get("entries")
    require(isinstance(rows, list), "policy entries are not an array")
    parsed: list[PolicyEntry] = []
    for index, row in enumerate(rows):
        require(
            isinstance(row, dict) and set(row) == {"path", "review_class", "status"},
            f"policy row {index} shape changed",
        )
        path = row.get("path")
        row_status = row.get("status")
        review_class = row.get("review_class")
        require(isinstance(path, str), f"policy row {index} path is not text")
        validate_path(path)
        require(row_status in {"A", "M"}, f"policy row status invalid: {path}")
        require(review_class in review_classes, f"policy review class invalid: {path}")
        parsed.append(PolicyEntry(path, row_status, review_class))
    require(
        [row.path for row in parsed] == sorted(REQUIRED_POLICY_ROWS)
        and len(parsed) == len(REQUIRED_POLICY_ROWS),
        "policy inventory differs from coordinated anticipated inventory",
    )
    require(
        {row.path: (row.status, row.review_class) for row in parsed}
        == REQUIRED_POLICY_ROWS,
        "policy status/review-class mapping changed",
    )
    receipt = value.get("receipt_contract")
    require(
        receipt
        == {
            "composite_descendant_receipt_path": FUTURE_COMPOSITE_RECEIPT,
            "composite_descendant_receipt_schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v2",
            "correction_subject_must_not_contain_receipt": True,
            "correction_subject_must_not_contain_retained_index": True,
            "implementation_subject_must_not_contain_receipt": True,
            "implementation_subject_must_not_contain_retained_index": True,
            "later_descendant_required": True,
            "retained_index_commit_message_trailer_required": True,
            "retained_index_descendant_path": FUTURE_RETAINED_INDEX,
        },
        "policy receipt contract changed",
    )
    forbidden = value.get("forbidden_contexts")
    require(
        isinstance(forbidden, list)
        and len(forbidden) == 10
        and all(isinstance(item, str) and item for item in forbidden)
        and any("83-path" in item for item in forbidden)
        and any("31686107959" in item for item in forbidden)
        and any("evidence-matrix-v4" in item for item in forbidden),
        "policy forbidden-context boundary changed",
    )
    if verify_anchor:
        anchor_entries, _ = parse_tree(IMPLEMENTATION_TREE)
        require(
            git_text("rev-parse", f"{IMPLEMENTATION}^{{tree}}") == IMPLEMENTATION_TREE
            and git_text("rev-parse", f"{IMPLEMENTATION}^") == IMPLEMENTATION_PARENT,
            "implementation commit relation changed",
        )
        for row in parsed:
            require(
                (row.status == "M" and row.path in anchor_entries)
                or (row.status == "A" and row.path not in anchor_entries),
                f"policy classification disagrees with implementation tree: {row.path}",
            )
    return tuple(parsed)


def load_policy(
    *, verify_anchor: bool
) -> tuple[dict[str, Any], bytes, tuple[PolicyEntry, ...]]:
    raw = read_regular(POLICY_RELATIVE)
    value = parse_json_bytes(raw, "correction policy", canonical=True)
    entries = validate_policy_data(value, verify_anchor=verify_anchor)
    status = value["authority"]["inventory_status"]
    digest = hashlib.sha256(raw).hexdigest()
    require(
        status == EXPECTED_LIVE_POLICY_STATE, "live policy state differs from checker"
    )
    if status == "frozen":
        require(
            EXPECTED_FROZEN_POLICY_SHA256 != "0" * 64
            and digest == EXPECTED_FROZEN_POLICY_SHA256,
            "frozen policy digest is not reviewed/bound",
        )
    else:
        require(
            EXPECTED_FROZEN_POLICY_SHA256 == "0" * 64,
            "provisional policy carries frozen digest",
        )
    return value, raw, entries


def schema_const(value: Any, path: tuple[str, ...], expected: Any) -> None:
    current = value
    for component in path:
        if isinstance(current, dict):
            require(component in current, f"schema path missing: {'/'.join(path)}")
            current = current[component]
        elif isinstance(current, list):
            require(
                component.isascii()
                and component.isdigit()
                and int(component) < len(current),
                f"schema array path missing: {'/'.join(path)}",
            )
            current = current[int(component)]
        else:
            raise CorrectionError(f"schema path missing: {'/'.join(path)}")
    require(
        type(current) is type(expected) and current == expected,
        f"schema const changed: {'/'.join(path)}",
    )


def validate_schema_numeric_types(value: Any) -> None:
    require(isinstance(value, dict), "composite schema root is not an object")
    pending: list[tuple[Any, str]] = [(value, "")]
    integer_const_count = 0
    boolean_const_count = 0
    typed_const_projection: list[dict[str, Any]] = []
    boolean_control_projection: list[dict[str, Any]] = []
    while pending:
        node, path = pending.pop()
        if isinstance(node, dict):
            if "const" in node and type(node["const"]) is int:
                integer_const_count += 1
                require(
                    node.get("type") == "integer",
                    f"schema numeric const lacks explicit integer type: {path}",
                )
                typed_const_projection.append(
                    {"path": path, "type": node.get("type"), "value": node["const"]}
                )
            if "const" in node and type(node["const"]) is bool:
                boolean_const_count += 1
                require(
                    node.get("type") == "boolean",
                    f"schema boolean const lacks explicit boolean type: {path}",
                )
                typed_const_projection.append(
                    {"path": path, "type": node.get("type"), "value": node["const"]}
                )
            for keyword in (
                "additionalProperties",
                "unevaluatedProperties",
                "uniqueItems",
            ):
                if keyword in node:
                    require(
                        type(node[keyword]) is bool,
                        f"schema boolean control is not exact: {path}/{keyword}",
                    )
                    boolean_control_projection.append(
                        {"keyword": keyword, "path": path, "value": node[keyword]}
                    )
            if "minimum" in node and type(node["minimum"]) is int:
                require(
                    node.get("type") == "integer"
                    or (
                        isinstance(node.get("type"), list) and "integer" in node["type"]
                    ),
                    f"schema numeric minimum lacks explicit integer type: {path}",
                )
            pending.extend(
                (
                    child,
                    f"{path}/{key.replace('~', '~0').replace('/', '~1')}",
                )
                for key, child in node.items()
            )
        elif isinstance(node, list):
            pending.extend(
                (child, f"{path}/{index}") for index, child in enumerate(node)
            )
    require(
        integer_const_count == 25 and boolean_const_count == 53,
        "schema reviewed integer/boolean const inventory changed",
    )
    typed_const_projection.sort(key=lambda row: row["path"])
    boolean_control_projection.sort(key=lambda row: (row["path"], row["keyword"]))
    require(
        len(typed_const_projection) == EXPECTED_SCHEMA_TYPED_CONST_PROJECTION_COUNT
        and hashlib.sha256(
            canonical_json(typed_const_projection, pretty=False)
        ).hexdigest()
        == EXPECTED_SCHEMA_TYPED_CONST_PROJECTION_SHA256,
        "schema reviewed typed-const path/value/type projection changed",
    )
    require(
        len(boolean_control_projection)
        == EXPECTED_SCHEMA_BOOLEAN_CONTROL_PROJECTION_COUNT
        and hashlib.sha256(
            canonical_json(boolean_control_projection, pretty=False)
        ).hexdigest()
        == EXPECTED_SCHEMA_BOOLEAN_CONTROL_PROJECTION_SHA256,
        "schema reviewed boolean-control path/value projection changed",
    )


def validate_schema_data(value: Any) -> None:
    validate_schema_numeric_types(value)
    require(
        hashlib.sha256(canonical_json(value, pretty=True)).hexdigest()
        == EXPECTED_SCHEMA_SHA256,
        "composite schema differs from the exact reviewed schema bytes",
    )
    schema_const(value, ("$schema",), "https://json-schema.org/draft/2020-12/schema")
    schema_const(value, ("additionalProperties",), False)
    schema_const(
        value,
        ("properties", "schema", "const"),
        "pid-rs/ksg-rev4-m1a-composite-receipt/v2",
    )
    schema_const(value, ("properties", "schema_revision", "const"), 2)
    schema_const(
        value,
        ("properties", "implementation_anchor", "properties", "commit", "const"),
        IMPLEMENTATION,
    )
    schema_const(
        value,
        ("properties", "implementation_anchor", "properties", "tree", "const"),
        IMPLEMENTATION_TREE,
    )
    schema_const(
        value,
        ("properties", "implementation_anchor", "properties", "direct_parent", "const"),
        IMPLEMENTATION_PARENT,
    )
    schema_const(
        value,
        (
            "properties",
            "implementation_anchor",
            "properties",
            "protected_projection",
            "properties",
            "entry_count",
            "const",
        ),
        PROTECTED_COUNT,
    )
    schema_const(
        value,
        (
            "properties",
            "implementation_anchor",
            "properties",
            "protected_projection",
            "properties",
            "sha256",
            "const",
        ),
        PROTECTED_SHA256,
    )
    schema_const(
        value,
        ("properties", "custody_correction", "properties", "direct_parent", "const"),
        IMPLEMENTATION,
    )
    schema_const(
        value,
        (
            "properties",
            "custody_correction",
            "properties",
            "implementation_identity_after_correction",
            "const",
        ),
        IMPLEMENTATION,
    )
    schema_const(
        value,
        (
            "properties",
            "hosted_observations",
            "properties",
            "implementation_ci_failure",
            "properties",
            "run_id",
            "const",
        ),
        31686107959,
    )
    schema_const(
        value,
        (
            "properties",
            "hosted_observations",
            "properties",
            "implementation_ci_failure",
            "properties",
            "conclusion",
            "const",
        ),
        "failure",
    )
    schema_const(
        value,
        (
            "properties",
            "hosted_observations",
            "properties",
            "implementation_codeql_success",
            "allOf",
            "1",
            "properties",
            "run_id",
            "const",
        ),
        31686106737,
    )
    schema_const(
        value,
        ("properties", "revision4_integration", "properties", "status", "const"),
        "integration_no_go",
    )
    schema_const(
        value,
        (
            "properties",
            "revision4_integration",
            "properties",
            "open_gate_count",
            "const",
        ),
        13,
    )
    schema_const(
        value,
        (
            "properties",
            "acyclic_boundary",
            "properties",
            "implementation_tree_excludes_receipt",
            "const",
        ),
        True,
    )
    schema_const(
        value,
        (
            "properties",
            "acyclic_boundary",
            "properties",
            "correction_tree_excludes_receipt",
            "const",
        ),
        True,
    )
    required = value.get("required")
    require(
        isinstance(required, list)
        and set(required)
        == {
            "schema",
            "schema_revision",
            "repository",
            "claim",
            "milestone",
            "implementation_anchor",
            "custody_correction",
            "local_phase_custody",
            "remote_observations",
            "hosted_observations",
            "negative_evidence_semantics",
            "revision4_integration",
            "acyclic_boundary",
            "evidence_class",
            "nonimplications",
        },
        "composite schema required inventory changed",
    )


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == keys, f"{label} shape changed")
    return value


def exact_text(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value), f"{label} is not nonempty text")
    return value


def exact_integer(
    value: Any,
    label: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    require(
        type(value) is int
        and value >= minimum
        and (maximum is None or value <= maximum),
        f"{label} is not a bounded integer",
    )
    return value


def reject_json_floats(value: Any, label: str) -> None:
    """Reject JSON floating-point scalars; every numeric contract field is integral."""
    pending: list[tuple[Any, str]] = [(value, label)]
    while pending:
        item, path = pending.pop()
        require(type(item) is not float, f"{path} contains a floating-point value")
        if isinstance(item, dict):
            pending.extend((child, f"{path}.{key}") for key, child in item.items())
        elif isinstance(item, list):
            pending.extend(
                (child, f"{path}[{index}]") for index, child in enumerate(item)
            )


NUMERIC_JSON_FIELDS = {
    "alert_number",
    "analysis_id",
    "artifact_id",
    "attempt",
    "codeql_run_id",
    "completed_at_epoch",
    "content_size_bytes",
    "dismissed",
    "entry_count",
    "failed_ci_run_id",
    "failed_job_count",
    "failed_jobs",
    "fixed",
    "job_id",
    "jobs",
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
    "results_count",
    "revision",
    "rules_count",
    "run_id",
    "runtime_mode",
    "schema_revision",
    "sealed_index_size_bytes",
    "size_bytes",
    "started_at_epoch",
    "step_number",
    "total",
}
NUMERIC_JSON_LIST_FIELDS = {
    "baseline_alert_numbers",
    "dismissed_alert_numbers",
    "fixed_alert_numbers",
    "new_alert_numbers",
    "observed_alert_numbers",
    "open_alert_numbers",
}
BOOLEAN_JSON_FIELDS = {
    "all_green_applies_only_to_correction_head",
    "all_jobs_successful",
    "authentication_claimed",
    "author_and_committer_headers_identical",
    "bounded_private_cli_protocol_exact",
    "candidate_equals_anchor",
    "candidate_tree_matches_checkpoint",
    "causation_claimed",
    "checkpoint_became_correction_commit",
    "cli_only_selftest_transport",
    "correction_heads_equal",
    "correction_subject_must_not_contain_receipt",
    "correction_subject_must_not_contain_retained_index",
    "correction_tree_excludes_receipt",
    "correction_tree_excludes_retained_index",
    "credit_permitted",
    "decision_v4_absent_at_correction",
    "deletions_permitted",
    "distinct_from_implementation_anchor",
    "evidence_matrix_v4_absent_at_correction",
    "final_decision_absent",
    "final_evidence_matrix_absent",
    "future_composite_receipt_absent",
    "head_equals_correction_commit",
    "head_tree_equals_correction_tree",
    "implementation_and_correction_heads_distinct",
    "implementation_heads_equal",
    "implementation_subject_must_not_contain_receipt",
    "implementation_subject_must_not_contain_retained_index",
    "implementation_tree_excludes_receipt",
    "implementation_tree_excludes_retained_index",
    "independently_recorded_before_ref_update",
    "input_descriptor_read_only",
    "later_descendant_required",
    "lifecycle_validation_permitted",
    "mechanical_resealing_permitted",
    "no_new_alerts_observed",
    "one_parent",
    "pagination_complete",
    "pair_normalized_equal",
    "path_or_residency_claimed",
    "precommit_descriptor_observation_authenticated",
    "receipt_claims_its_own_commit",
    "receipt_hashes_itself",
    "receipt_subjects_preexist_receipt",
    "remains_implementation_after_correction",
    "repeated_observations_equal",
    "repetitions_equal",
    "retained_index_commit_message_trailer_required",
    "retained_negative_evidence",
    "runner_authenticity_claimed",
    "scientific_authority_unchanged",
    "signature_headers_permitted",
    "single_link",
    "three_container_digest_rebind_exact",
    "trusted_time_claimed",
    "truncated",
    "unsigned",
}


def reject_numeric_boolean_aliases(value: Any, label: str) -> None:
    pending: list[tuple[Any, str | None, str]] = [(value, None, label)]
    while pending:
        item, field, path = pending.pop()
        require(
            not (
                type(item) is bool
                and field is not None
                and (field in NUMERIC_JSON_FIELDS or field in NUMERIC_JSON_LIST_FIELDS)
            ),
            f"{path} uses a boolean in an integer field",
        )
        if isinstance(item, dict):
            pending.extend((child, key, f"{path}.{key}") for key, child in item.items())
        elif isinstance(item, list):
            pending.extend(
                (child, field, f"{path}[{index}]") for index, child in enumerate(item)
            )


def require_boolean_field_types(value: Any, label: str) -> None:
    pending: list[tuple[Any, str | None, str]] = [(value, None, label)]
    while pending:
        item, field, path = pending.pop()
        if field in BOOLEAN_JSON_FIELDS:
            require(type(item) is bool, f"{path} is not an exact JSON boolean")
        elif type(item) is bool:
            raise CorrectionError(f"{path} is an unreviewed JSON boolean field")
        if isinstance(item, dict):
            pending.extend((child, key, f"{path}.{key}") for key, child in item.items())
        elif isinstance(item, list):
            pending.extend(
                (child, field, f"{path}[{index}]") for index, child in enumerate(item)
            )


def parse_utc(value: Any, label: str) -> datetime.datetime:
    text = exact_text(value, label)
    require(
        re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", text)
        is not None,
        f"{label} is not exact second-resolution RFC3339 UTC",
    )
    try:
        parsed = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError as error:
        raise CorrectionError(f"{label} is not a real UTC timestamp") from error
    require(
        parsed.isoformat().replace("+00:00", "Z") == text, f"{label} is noncanonical"
    )
    return parsed


def validate_sha1(value: Any, label: str) -> str:
    require(
        isinstance(value, str) and HEX40.fullmatch(value) is not None,
        f"{label} is not SHA-1",
    )
    return value


def validate_sha256(value: Any, label: str) -> str:
    require(
        isinstance(value, str) and HEX64.fullmatch(value) is not None,
        f"{label} is not SHA-256",
    )
    return value


def validate_projection(
    projection: Any, rows: list[dict[str, Any]], encoding: str, label: str
) -> str:
    item = exact_keys(projection, {"encoding", "entry_count", "sha256"}, label)
    require(item["encoding"] == encoding, f"{label} encoding changed")
    require(item["entry_count"] == len(rows), f"{label} entry count disagrees")
    digest = hashlib.sha256(canonical_json(rows, pretty=False)).hexdigest()
    require(item["sha256"] == digest, f"{label} digest disagrees with embedded rows")
    return digest


def validate_hosted_jobs(
    value: Any, *, expected_total: int | None, require_success: bool, label: str
) -> list[dict[str, Any]]:
    require(isinstance(value, list) and value, f"{label} roster is empty/not an array")
    if expected_total is not None:
        require(len(value) == expected_total, f"{label} roster count changed")
    rows: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, raw_job in enumerate(value):
        job = exact_keys(
            raw_job,
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
        job_id = exact_integer(job["job_id"], f"{label} job id", minimum=1)
        require(job_id not in seen_ids, f"{label} duplicate job id")
        seen_ids.add(job_id)
        require(job["status"] == "completed", f"{label} job is not completed")
        job_allowed = (
            {"success"}
            if require_success
            else {"cancelled", "failure", "skipped", "success"}
        )
        step_allowed = (
            {"skipped", "success"}
            if require_success
            else {"cancelled", "failure", "skipped", "success"}
        )
        require(job["conclusion"] in job_allowed, f"{label} job conclusion invalid")
        exact_text(job["name"], f"{label} job name")
        started = parse_utc(job["started_at"], f"{label} job start")
        completed = parse_utc(job["completed_at"], f"{label} job end")
        require(started <= completed, f"{label} job time order invalid")
        require(
            isinstance(job["steps"], list) and job["steps"], f"{label} job lacks steps"
        )
        step_rows: list[dict[str, Any]] = []
        step_numbers: set[int] = set()
        for raw_step in job["steps"]:
            step = exact_keys(
                raw_step, {"conclusion", "name", "number", "status"}, f"{label} step"
            )
            number = exact_integer(step["number"], f"{label} step number", minimum=1)
            require(number not in step_numbers, f"{label} duplicate step number")
            step_numbers.add(number)
            require(
                step["status"] == "completed" and step["conclusion"] in step_allowed,
                f"{label} step lifecycle invalid",
            )
            exact_text(step["name"], f"{label} step name")
            step_rows.append(
                {
                    "conclusion": step["conclusion"],
                    "name": step["name"],
                    "number": number,
                    "status": "completed",
                }
            )
        step_rows.sort(key=lambda row: row["number"])
        rows.append(
            {
                "completed_at": job["completed_at"],
                "conclusion": job["conclusion"],
                "job_id": job_id,
                "name": job["name"],
                "started_at": job["started_at"],
                "status": "completed",
                "steps": step_rows,
            }
        )
    rows.sort(key=lambda row: row["job_id"])
    return rows


def validate_analysis_rows(value: Any, label: str, head: str) -> list[dict[str, Any]]:
    require(
        isinstance(value, list) and len(value) == 4, f"{label} must have four analyses"
    )
    rows: list[dict[str, Any]] = []
    languages: set[str] = set()
    job_ids: set[int] = set()
    analysis_ids: set[int] = set()
    for raw in value:
        row = exact_keys(
            raw,
            {
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
            },
            f"{label} analysis",
        )
        language = row["language"]
        require(
            language in {"actions", "javascript-typescript", "python", "rust"}
            and language not in languages,
            f"{label} language inventory invalid",
        )
        job_id = exact_integer(row["job_id"], f"{label} job id", minimum=1)
        analysis_id = exact_integer(
            row["analysis_id"], f"{label} analysis id", minimum=1
        )
        require(
            job_id not in job_ids and analysis_id not in analysis_ids,
            f"{label} duplicate identity",
        )
        languages.add(language)
        job_ids.add(job_id)
        analysis_ids.add(analysis_id)
        exact_integer(row["results_count"], f"{label} results count")
        exact_integer(row["rules_count"], f"{label} rules count")
        require(
            row["category"] == f"/language:{language}"
            and row["commit_sha"] == head
            and row["ref"] == "refs/heads/main"
            and row["status"] == "completed"
            and row["conclusion"] == "success"
            and row["no_new_alerts_observed"] is True
            and row["error"] == ""
            and row["warning"] == "",
            f"{label} analysis upload facts changed",
        )
        rows.append(dict(row))
    rows.sort(key=lambda row: row["language"])
    return rows


def validate_alert_state(value: Any, label: str) -> dict[str, Any]:
    state = exact_keys(
        value,
        {
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
        },
        label,
    )
    for name in ("open", "dismissed", "fixed", "total", "observed_new_alerts"):
        exact_integer(state[name], f"{label} {name}")
    rosters: dict[str, list[int]] = {}
    for name in (
        "baseline_alert_numbers",
        "dismissed_alert_numbers",
        "fixed_alert_numbers",
        "new_alert_numbers",
        "observed_alert_numbers",
        "open_alert_numbers",
    ):
        roster = state[name]
        require(
            isinstance(roster, list)
            and all(type(item) is int and item >= 1 for item in roster)
            and roster == sorted(set(roster)),
            f"{label} {name} is not a sorted unique positive-integer roster",
        )
        rosters[name] = roster
    categorized = (
        rosters["open_alert_numbers"]
        + rosters["dismissed_alert_numbers"]
        + rosters["fixed_alert_numbers"]
    )
    require(
        len(categorized) == len(set(categorized))
        and rosters["observed_alert_numbers"] == sorted(categorized)
        and rosters["new_alert_numbers"]
        == sorted(
            set(rosters["observed_alert_numbers"])
            - set(rosters["baseline_alert_numbers"])
        )
        and state["observed_new_alerts"] == len(rosters["new_alert_numbers"]) == 0
        and state["open"] == len(rosters["open_alert_numbers"])
        and state["dismissed"] == len(rosters["dismissed_alert_numbers"])
        and state["fixed"] == len(rosters["fixed_alert_numbers"])
        and state["total"] == len(rosters["observed_alert_numbers"]),
        f"{label} derived roster/count/set-difference semantics disagree",
    )
    for name in ("minimum_alert_number", "maximum_alert_number"):
        require(
            state[name] is None or (type(state[name]) is int and state[name] >= 1),
            f"{label} alert range invalid",
        )
    if state["total"] == 0:
        require(
            state["minimum_alert_number"] is None
            and state["maximum_alert_number"] is None,
            f"{label} empty range invalid",
        )
    else:
        require(
            state["minimum_alert_number"] == min(rosters["observed_alert_numbers"])
            and state["maximum_alert_number"] == max(rosters["observed_alert_numbers"]),
            f"{label} extrema disagree with observed roster",
        )
    return state


def scalar_projection(value: dict[str, Any], omitted: set[str]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in omitted}


def validate_capture_inventory(
    value: Any, expected: dict[str, Any], label: str
) -> dict[str, str]:
    require(
        isinstance(value, list) and len(value) == len(expected),
        f"{label} capture inventory count changed",
    )
    require(
        [
            item.get("endpoint_class") if isinstance(item, dict) else None
            for item in value
        ]
        == sorted(expected),
        f"{label} capture inventory is not exact/sorted",
    )
    result: dict[str, str] = {}
    for raw in value:
        capture = exact_keys(
            raw,
            {
                "endpoint_class",
                "projection",
                "repetitions_equal",
                "sha256",
                "size_bytes",
            },
            f"{label} capture",
        )
        endpoint = capture["endpoint_class"]
        require(endpoint in expected, f"{label} unexpected endpoint class")
        require(
            capture["projection"] == expected[endpoint],
            f"{label} embedded endpoint projection changed",
        )
        encoded = canonical_json(capture["projection"], pretty=False)
        digest = hashlib.sha256(encoded).hexdigest()
        require(
            capture["repetitions_equal"] is True
            and capture["sha256"] == digest
            and capture["size_bytes"] == len(encoded),
            f"{label} capture digest/size/repetition disagrees",
        )
        result[endpoint] = digest
    return result


def validate_postcommit_artifact(value: Any, head: str, label: str) -> dict[str, Any]:
    artifact = exact_keys(
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
    exact_integer(artifact["artifact_id"], f"{label} id", minimum=1)
    exact_integer(artifact["size_bytes"], f"{label} archive size", minimum=1)
    exact_integer(artifact["content_size_bytes"], f"{label} content size", minimum=1)
    validate_sha256(artifact["sha256"], f"{label} archive digest")
    validate_sha256(artifact["content_sha256"], f"{label} content digest")
    require(
        artifact["name"] == f"post-commit-source-state-v2-{head}",
        f"{label} name/head binding changed",
    )
    return artifact


CI_CAPTURE_OMISSIONS = {
    "api_captures",
    "failed_diagnostic",
    "job_roster",
    "job_roster_projection",
    "negative_evidence_sha256",
    "postcommit_source_state_v2",
}
CODEQL_CAPTURE_OMISSIONS = {
    "alert_state",
    "analysis_roster",
    "analysis_roster_projection",
    "api_captures",
    "job_roster",
    "job_roster_projection",
}


def validate_ci_observation(
    value: Any,
    *,
    head: str,
    tree: str,
    run_id: int,
    successful: bool,
    implementation: bool,
    negative_record: bool = False,
) -> dict[str, Any]:
    require(
        len(EXPECTED_CI_JOB_NAMES) == 45, "internal CI job-name inventory count changed"
    )
    common = {
        "all_jobs_successful",
        "api_captures",
        "attempt",
        "conclusion",
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
        "run_id",
        "runner_authenticity_claimed",
        "source_event",
        "status",
        "workflow",
        "workflow_path",
    }
    extra = (
        {
            "failed_diagnostic",
            "failed_job_count",
            "retained_negative_evidence",
            "success_credit",
        }
        | (set() if negative_record else {"negative_evidence_sha256"})
        if implementation
        else {"head_equals_correction_commit", "head_tree_equals_correction_tree"}
    )
    run = exact_keys(value, common | extra, "CI observation")
    exact_integer(run["attempt"], "CI attempt", minimum=1, maximum=1)
    exact_integer(run["jobs_total"], "CI total jobs", minimum=1)
    exact_integer(run["jobs_successful"], "CI successful jobs", minimum=0)
    require(
        run["workflow"] == "CI"
        and run["workflow_path"] == ".github/workflows/ci.yml"
        and run["run_id"] == run_id
        and run["attempt"] == 1
        and run["head_sha"] == head
        and run["head_tree"] == tree
        and run["repository"] == "sepahead/pid-rs"
        and run["ref"] == "refs/heads/main"
        and run["source_event"] == "push"
        and run["status"] == "completed"
        and run["conclusion"] == ("success" if successful else "failure")
        and run["all_jobs_successful"] is successful
        and run["pagination_complete"] is True
        and run["runner_authenticity_claimed"] is False,
        "CI observation identity/lifecycle changed",
    )
    rows = validate_hosted_jobs(
        run["job_roster"],
        expected_total=45,
        require_success=successful,
        label="CI",
    )
    require(
        len({row["name"] for row in rows}) == len(rows)
        and tuple(sorted(row["name"] for row in rows)) == EXPECTED_CI_JOB_NAMES,
        "CI exact workflow job-name inventory changed",
    )
    if implementation:
        exact_integer(
            run["failed_job_count"],
            "implementation CI failed-job count",
            minimum=1,
            maximum=1,
        )
        require(
            tuple((row["job_id"], row["name"]) for row in rows)
            == EXPECTED_IMPLEMENTATION_CI_JOB_IDENTITIES,
            "implementation CI exact job-id/name roster changed",
        )
    successes = sum(row["conclusion"] == "success" for row in rows)
    require(
        run["jobs_total"] == len(rows)
        and run["jobs_successful"] == successes
        and successful == (successes == len(rows)),
        "CI derived totals disagree with exact roster",
    )
    roster_projection = validate_projection(
        run["job_roster_projection"],
        rows,
        JOB_PROJECTION_ENCODING,
        "CI roster projection",
    )
    if implementation:
        require(
            roster_projection == EXPECTED_IMPLEMENTATION_CI_PROJECTION_SHA256,
            "implementation CI reviewed roster projection changed",
        )
    artifact = validate_postcommit_artifact(
        run["postcommit_source_state_v2"], head, "CI postcommit artifact"
    )
    if implementation:
        require(
            run["failed_job_count"] == 1
            and run["retained_negative_evidence"] is True
            and run["success_credit"] == "none",
            "implementation CI failure semantics changed",
        )
        if not negative_record:
            validate_sha256(run["negative_evidence_sha256"], "negative evidence digest")
        failed = [row for row in rows if row["conclusion"] == "failure"]
        require(
            len(failed) == 1, "implementation CI must retain exactly one failed job"
        )
        failed_steps = [
            step for step in failed[0]["steps"] if step["conclusion"] == "failure"
        ]
        require(
            len(failed_steps) == 1,
            "implementation CI must retain exactly one failed step",
        )
        diagnostic = exact_keys(
            run["failed_diagnostic"],
            {
                "job_id",
                "job_name",
                "log_sha256",
                "log_size_bytes",
                "step_name",
                "step_number",
                "truncated",
            },
            "failed diagnostic",
        )
        require(
            diagnostic["job_id"] == 94402437784 == failed[0]["job_id"]
            and diagnostic["job_name"]
            == "Exact-count directed-rounding SxPID2 reference"
            == failed[0]["name"]
            and diagnostic["step_number"] == 22 == failed_steps[0]["number"]
            and diagnostic["step_name"]
            == "Run python3 scripts/check-certified-sxpid2-claim.py"
            == failed_steps[0]["name"]
            and diagnostic["truncated"] is False,
            "failed diagnostic identity differs from exact failed roster row",
        )
        require(
            diagnostic["log_sha256"]
            == "610c6faba7c794bbcbde35bb37b032f010045fd8f324b33887c0739c1d7b94f2"
            and diagnostic["log_size_bytes"] == 196292,
            "failed raw log capture changed",
        )
    else:
        require(
            run["head_equals_correction_commit"] is True
            and run["head_tree_equals_correction_tree"] is True,
            "correction CI cross-head markers changed",
        )
    expected_captures = {
        "ci_job_step_roster": rows,
        "ci_run_summary": scalar_projection(run, CI_CAPTURE_OMISSIONS),
        "postcommit_source_state_v2_artifact": artifact,
    }
    validate_capture_inventory(run["api_captures"], expected_captures, "CI")
    return {"artifact": artifact, "rows": rows}


def validate_codeql_observation(
    value: Any,
    *,
    head: str,
    tree: str,
    run_id: int | None,
    implementation: bool,
) -> dict[str, Any]:
    keys = {
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
    }
    if not implementation:
        keys |= {"head_equals_correction_commit", "head_tree_equals_correction_tree"}
    run = exact_keys(value, keys, "CodeQL observation")
    exact_integer(run["run_id"], "CodeQL run id", minimum=1)
    exact_integer(run["attempt"], "CodeQL attempt", minimum=1, maximum=1)
    exact_integer(run["jobs_total"], "CodeQL total jobs", minimum=4, maximum=4)
    exact_integer(
        run["jobs_successful"], "CodeQL successful jobs", minimum=4, maximum=4
    )
    exact_integer(run["new_alerts"], "CodeQL new-alert count", maximum=0)
    require(
        (run_id is None or run["run_id"] == run_id)
        and run["workflow"] == "CodeQL"
        and run["attempt"] == 1
        and run["head_sha"] == head
        and run["head_tree"] == tree
        and run["repository"] == "sepahead/pid-rs"
        and run["ref"] == "refs/heads/main"
        and run["source_event"]
        in ({"dynamic"} if implementation else {"dynamic", "push"})
        and run["status"] == "completed"
        and run["conclusion"] == "success"
        and run["all_jobs_successful"] is True
        and run["pagination_complete"] is True
        and run["runner_authenticity_claimed"] is False
        and run["new_alerts"] == 0,
        "CodeQL observation identity/lifecycle changed",
    )
    jobs = validate_hosted_jobs(
        run["job_roster"], expected_total=4, require_success=True, label="CodeQL"
    )
    require(
        run["jobs_total"] == 4 and run["jobs_successful"] == 4, "CodeQL totals changed"
    )
    job_projection = validate_projection(
        run["job_roster_projection"],
        jobs,
        JOB_PROJECTION_ENCODING,
        "CodeQL job projection",
    )
    analyses = validate_analysis_rows(run["analysis_roster"], "CodeQL", head)
    analysis_projection = validate_projection(
        run["analysis_roster_projection"],
        analyses,
        ANALYSIS_PROJECTION_ENCODING,
        "CodeQL analysis projection",
    )
    require(
        {row["job_id"] for row in jobs} == {row["job_id"] for row in analyses},
        "CodeQL job/analysis identities disagree",
    )
    for row in analyses:
        matching = next(job for job in jobs if job["job_id"] == row["job_id"])
        require(
            matching["name"] == f"Analyze ({row['language']})",
            "CodeQL job name/language mismatch",
        )
    if implementation:
        require(
            job_projection == EXPECTED_IMPLEMENTATION_CODEQL_JOB_PROJECTION_SHA256
            and analysis_projection
            == EXPECTED_IMPLEMENTATION_CODEQL_ANALYSIS_PROJECTION_SHA256
            and [
                (
                    row["language"],
                    row["job_id"],
                    row["analysis_id"],
                    row["results_count"],
                    row["rules_count"],
                    row["error"],
                    row["warning"],
                )
                for row in analyses
            ]
            == [
                ("actions", 94402437296, 1612601534, 0, 17, "", ""),
                ("javascript-typescript", 94402437445, 1612602800, 0, 87, "", ""),
                ("python", 94402437367, 1612605633, 44, 43, "", ""),
                ("rust", 94402437298, 1612608452, 113, 25, "", ""),
            ],
            "implementation CodeQL reviewed projections/exact identities changed",
        )
    else:
        require(
            run["head_equals_correction_commit"] is True
            and run["head_tree_equals_correction_tree"] is True,
            "correction CodeQL cross-head markers changed",
        )
    alert_state = validate_alert_state(run["alert_state"], "CodeQL alert state")
    expected_captures = {
        "codeql_alert_state": alert_state,
        "codeql_job_analysis_roster": {"analyses": analyses, "jobs": jobs},
        "codeql_run_summary": scalar_projection(run, CODEQL_CAPTURE_OMISSIONS),
    }
    validate_capture_inventory(run["api_captures"], expected_captures, "CodeQL")
    return {"alert_state": alert_state, "analyses": analyses, "jobs": jobs}


NEGATIVE_SEMANTICS = [
    "CI run 31686107959 attempt 1 on cb3f58f0 is terminal failed zero-credit evidence and remains failed after any later correction success.",
    "CodeQL run 31686106737 attempt 1 succeeded on cb3f58f0, but that success neither makes the separate CI run green nor establishes all-green hosted status for the implementation head.",
    "All-green hosted status may describe only separately observed successful CI and CodeQL runs on the exact distinct correction head.",
    "No provider observation here is authentication, trusted time, causation, authorship, transparency-log evidence, or repository provenance.",
]
COMPOSITE_NONIMPLICATIONS = [
    "This composite receipt is bounded lifecycle custody for an exact M1a implementation anchor and its exact direct-child custody correction; it is not scientific, formal, estimator, PID, calibration, support, application, package, release, or identity evidence.",
    "The correction does not change the implementation identity cb3f58f0 or the protected 83-path projection and does not turn revision 4 into an integration decision.",
    "Commit, tree, blob, SHA-256, remote, run, job, and artifact identifiers bind named observations but do not establish authenticity, authorship, trusted time, transparency-log inclusion, or repository origin.",
    "The KSG runtime witnesses remain fixed-input implementation correspondence only; they do not establish general neighbor-search correctness, estimator consistency, population support, or transfer to continuous PID, categorical SxPID, I_min, PID3, wrappers, or consumers.",
    "The receipt is absent from both subject trees and cannot attest its own bytes or containing descendant commit.",
]
NEGATIVE_NONIMPLICATIONS = [
    "This retained record is unauthenticated provider observation of one failed CI run and one successful CodeQL run on cb3f58f0; it grants no lifecycle or scientific credit.",
    "The failed diagnostic records an exact observed mismatch in a stale workflow container digest; it does not authenticate the provider response or establish broader causation.",
    "CodeQL success does not make CI green, establish all-green hosted status, or transfer success to a later correction head.",
    "Run, job, analysis, alert, artifact, commit, tree, blob, and SHA-256 identifiers do not establish authorship, trusted time, transparency-log inclusion, or repository provenance.",
]
FAILED_DIAGNOSTIC_LINE = (
    "certified SxPID2 claim check failed: reviewed revision-3 execution container digest changed for "
    ".github/workflows/ci.yml: expected "
    "5a85b5c11fa537801ce35a898349c7af0f867cc3cf3a71dfbabf4a8ca96469f8, observed "
    "3f79b14c8fd9e01cf3a457288e2544d971e5f4592895a115378ded8c799f5d1d\n"
)


def validate_artifact_record(value: Any, path: str, label: str) -> dict[str, Any]:
    artifact = exact_keys(
        value, {"git_blob_oid_sha1", "path", "sha256", "size_bytes"}, label
    )
    require(artifact["path"] == path, f"{label} path changed")
    validate_sha1(artifact["git_blob_oid_sha1"], f"{label} blob id")
    validate_sha256(artifact["sha256"], f"{label} digest")
    exact_integer(
        artifact["size_bytes"],
        f"{label} size",
        minimum=1,
        maximum=(MAX_INDEX_BYTES if path == FUTURE_RETAINED_INDEX else MAX_FILE_BYTES),
    )
    return artifact


def validate_artifact_against_tree(
    artifact: dict[str, Any],
    tree: dict[str, Entry],
    label: str,
    *,
    maximum: int = MAX_FILE_BYTES,
) -> None:
    entry = tree.get(artifact["path"])
    require(
        entry is not None and entry.mode == "100644",
        f"{label} absent/non-regular in correction tree",
    )
    raw = exact_object(entry.oid, "blob", maximum=maximum)
    require(
        artifact["git_blob_oid_sha1"] == entry.oid
        and artifact["sha256"] == hashlib.sha256(raw).hexdigest()
        and artifact["size_bytes"] == len(raw),
        f"{label} descriptor disagrees with correction-tree blob",
    )


PHASE_OUTPUT_ROOT_KEYS = {
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
SELF_TEST_COMPOSITE_CORRECTION_COMMIT = "1" * 40
SELF_TEST_COMPOSITE_CORRECTION_TREE = "2" * 40
SELF_TEST_COMPOSITE_ALTERNATE_INDEX = {
    "entry_count": 109,
    "input_descriptor_read_only": True,
    "input_transport": "standard_input_regular_file_descriptor",
    "mode_octal": "0400",
    "path_or_residency_claimed": False,
    "precommit_descriptor_observation_authenticated": False,
    "retained_index_artifact": {
        "git_blob_oid_sha1": "4" * 40,
        "path": FUTURE_RETAINED_INDEX,
        "sha256": "7" * 64,
        "size_bytes": 32768,
    },
    "sha256": "7" * 64,
    "single_link": True,
    "size_bytes": 32768,
}
SELF_TEST_COMPOSITE_PHASE_FACTS = {
    "certified_sxpid_correction": {
        "cli_only_selftest_sha256": "3" * 64,
        "scientific_authority_unchanged": True,
        "three_container_digest_literals": {
            ".github/workflows/ci.yml": "8" * 64,
            "justfile": "9" * 64,
            "scripts/README.md": "a" * 64,
        },
    },
    "child_output_sha256": {
        CERT_CHECKER: "c" * 64,
        CERT_SELF_TEST: "b" * 64,
        LEAN_CHECKER: "d" * 64,
        LEAN_SELF_TEST: "e" * 64,
    },
    "current_source_manifest_sha256": "4" * 64,
    "lean_r6": {
        "schema": "pid-rs/lean-current-project-replay/v2",
        "sha256": "5" * 64,
        "status": "passed",
    },
    "policy_sha256": "6" * 64,
    "static_artifact_sha256": {
        BOUNDARY_RELATIVE: "e" * 64,
        SCHEMA_RELATIVE: "f" * 64,
        CHECKER_RELATIVE: "2" * 64,
        SELF_TEST_RELATIVE: "1" * 64,
    },
}


def validate_phase_output_shape(
    value: Any,
    *,
    phase: str,
    optimize: int,
    correction_commit: str,
    correction_tree: str,
    alternate: dict[str, Any] | None,
    expected_envelope: dict[str, Any],
) -> dict[str, Any]:
    output = exact_keys(
        value, PHASE_OUTPUT_ROOT_KEYS, f"{phase}/{optimize} phase output"
    )
    require(
        output["schema"] == "pid-rs/ksg-rev4-m1a-custody-correction-phase-validation/v1"
        and output["mode"] == phase
        and type(output["runtime_mode"]) is int
        and output["runtime_mode"] == optimize
        and output["credit"] == "none_local_custody_match_hosted_pending"
        and output["disposition"] == "local_hosted_pending_no_credit"
        and output["lifecycle"]
        == (
            "implementation_plus_exact_correction_overlay"
            if phase == "precommit"
            else "clean_main_direct_child_postcommit_no_credit"
        ),
        f"{phase}/{optimize} phase identity/disposition changed",
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
        f"{phase}/{optimize} candidate",
    )
    require(
        candidate["checkpoint_commit"] == correction_commit
        and candidate["tree"] == correction_tree
        and canonical_json(candidate["alternate_index_custody"], pretty=False)
        == canonical_json(alternate, pretty=False),
        f"{phase}/{optimize} candidate identity/alternate custody changed",
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
        f"{phase}/{optimize} envelope",
    )
    human = {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
    message_commitment = parse_correction_message(envelope["message"])
    require(
        envelope
        == {
            "author": human,
            "committer": human,
            "message": envelope["message"],
            "sealed_index_sha256": message_commitment["sha256"],
            "sealed_index_size_bytes": message_commitment["size_bytes"],
        },
        f"{phase}/{optimize} envelope changed",
    )
    require(
        canonical_json(envelope, pretty=False)
        == canonical_json(expected_envelope, pretty=False),
        f"{phase}/{optimize} envelope differs from the correction commitment",
    )
    require(
        isinstance(candidate["delta"], list),
        f"{phase}/{optimize} delta is not an array",
    )
    delta_paths: list[str] = []
    for row in candidate["delta"]:
        item = exact_keys(
            row, {"mode", "path", "status"}, f"{phase}/{optimize} delta row"
        )
        validate_path(item["path"])
        require(
            item["mode"] == "100644" and item["status"] in {"A", "M"},
            f"{phase}/{optimize} delta row changed",
        )
        delta_paths.append(item["path"])
    require(
        delta_paths == sorted(set(delta_paths)),
        f"{phase}/{optimize} delta is not sorted unique",
    )
    certified = exact_keys(
        output["certified_sxpid_correction"],
        {
            "cli_only_selftest_sha256",
            "scientific_authority_unchanged",
            "three_container_digest_literals",
        },
        f"{phase}/{optimize} certified correction",
    )
    validate_sha256(
        certified["cli_only_selftest_sha256"], f"{phase}/{optimize} certified selftest"
    )
    require(
        certified["scientific_authority_unchanged"] is True,
        f"{phase}/{optimize} scientific nonclaim changed",
    )
    digest_literals = exact_keys(
        certified["three_container_digest_literals"],
        set(EXPECTED_REBIND_PATHS),
        f"{phase}/{optimize} certified literal map",
    )
    for path, digest in digest_literals.items():
        validate_sha256(digest, f"{phase}/{optimize} certified literal {path}")
    children = exact_keys(
        output["child_output_sha256"],
        {CERT_CHECKER, CERT_SELF_TEST, LEAN_CHECKER, LEAN_SELF_TEST},
        f"{phase}/{optimize} child output map",
    )
    for path, digest in children.items():
        validate_sha256(digest, f"{phase}/{optimize} child output {path}")
    validate_sha256(
        output["current_source_manifest_sha256"],
        f"{phase}/{optimize} current-source digest",
    )
    validate_sha256(output["policy_sha256"], f"{phase}/{optimize} policy digest")
    implementation = exact_keys(
        output["implementation_anchor"],
        {"commit", "direct_parent", "protected_projection", "tree"},
        f"{phase}/{optimize} implementation anchor",
    )
    require(
        implementation
        == {
            "commit": IMPLEMENTATION,
            "direct_parent": IMPLEMENTATION_PARENT,
            "protected_projection": {
                "candidate_equals_anchor": True,
                "entry_count": PROTECTED_COUNT,
                "sha256": PROTECTED_SHA256,
            },
            "tree": IMPLEMENTATION_TREE,
        },
        f"{phase}/{optimize} implementation anchor changed",
    )
    lean = exact_keys(
        output["lean_r6"], {"schema", "sha256", "status"}, f"{phase}/{optimize} Lean r6"
    )
    require(
        lean["schema"] == "pid-rs/lean-current-project-replay/v2"
        and lean["status"] == "passed",
        f"{phase}/{optimize} Lean r6 identity changed",
    )
    validate_sha256(lean["sha256"], f"{phase}/{optimize} Lean r6 digest")
    negative = exact_keys(
        output["negative_evidence"],
        {"codeql_run_id", "failed_ci_run_id", "failed_jobs", "jobs", "sha256"},
        f"{phase}/{optimize} negative evidence",
    )
    exact_integer(
        negative["failed_jobs"],
        f"{phase}/{optimize} negative failed jobs",
        minimum=1,
        maximum=1,
    )
    exact_integer(
        negative["jobs"],
        f"{phase}/{optimize} negative job count",
        minimum=45,
        maximum=45,
    )
    require(
        negative["codeql_run_id"] == 31686106737
        and negative["failed_ci_run_id"] == 31686107959
        and negative["failed_jobs"] == 1
        and negative["jobs"] == 45,
        f"{phase}/{optimize} negative summary changed",
    )
    validate_sha256(negative["sha256"], f"{phase}/{optimize} negative digest")
    require(
        output["preclosure"]
        == {
            "final_decision_absent": True,
            "final_evidence_matrix_absent": True,
            "future_composite_receipt_absent": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        }
        and output["repository_state"]
        == {"active_git_operations": [], "branch": "main"},
        f"{phase}/{optimize} preclosure/repository state changed",
    )
    static = exact_keys(
        output["static_artifact_sha256"],
        {BOUNDARY_RELATIVE, SCHEMA_RELATIVE, CHECKER_RELATIVE, SELF_TEST_RELATIVE},
        f"{phase}/{optimize} static artifact map",
    )
    for path, digest in static.items():
        validate_sha256(digest, f"{phase}/{optimize} static artifact {path}")
    return output


def validate_phase_output_group(
    value: Any,
    *,
    phase: str,
    correction_commit: str,
    correction_tree: str,
    alternate: dict[str, Any] | None,
    expected_envelope: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    group = exact_keys(
        value, {"normal", "optimized", "pair_normalized_equal"}, f"{phase} outputs"
    )
    require(
        group["pair_normalized_equal"] is True,
        f"{phase} output pair equality marker changed",
    )
    results: dict[str, dict[str, Any]] = {}
    for label, optimize in (("normal", 0), ("optimized", 1)):
        record = exact_keys(
            group[label], {"output", "sha256"}, f"{phase} {label} output record"
        )
        output = validate_phase_output_shape(
            record["output"],
            phase=phase,
            optimize=optimize,
            correction_commit=correction_commit,
            correction_tree=correction_tree,
            alternate=alternate,
            expected_envelope=expected_envelope,
        )
        encoded = canonical_json(output, pretty=False)
        require(
            record["sha256"] == hashlib.sha256(encoded).hexdigest(),
            f"{phase} {label} output digest changed",
        )
        results[label] = output
    normalized = []
    for label in ("normal", "optimized"):
        item = dict(results[label])
        item["runtime_mode"] = "<NORMALIZED-RUNTIME-MODE>"
        normalized.append(canonical_json(item, pretty=False))
    require(
        normalized[0] == normalized[1],
        f"{phase} normal/optimized outputs differ beyond runtime mode",
    )
    return results


def validate_current_source_tree(
    manifest_value: Any, correction_entries: dict[str, Entry]
) -> None:
    exact_keys(
        manifest_value,
        {
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
        },
        "current-source manifest",
    )
    schema_raw = candidate_blob(correction_entries, CURRENT_SOURCE_SCHEMA)
    parse_json_bytes(schema_raw, "current-source schema", canonical=True)
    require(
        hashlib.sha256(schema_raw).hexdigest()
        == "1027cc3826aa6933a23dea1736b5d007b9c5bc1568f41ac87dea98e5f2924a97",
        "current-source schema raw bytes changed",
    )
    expected_rows: list[dict[str, Any]] = []
    for path, entry in correction_entries.items():
        if path == CURRENT_SOURCE_RELATIVE:
            continue
        raw = exact_object(entry.oid, "blob")
        expected_rows.append(
            {
                "git_mode": entry.mode,
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            }
        )
    mapping = {row["path"]: row for row in expected_rows}
    require(
        len(mapping) == len(expected_rows), "current-source projection duplicates paths"
    )
    compact_rows = json.dumps(
        expected_rows,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")

    critical_pairs = (
        ("assurance_registry_authority", "audit/evidence/assurance-registry.json"),
        (
            "assurance_registry_typed_view",
            "audit/evidence/assurance-registry-typed-view-v1.json",
        ),
        ("method_catalog", "method-catalog.json"),
        ("release_scope", "release-scope-1.0.json"),
        ("review_inventory", "audit/evidence/FILE_REVIEW_LEDGER.csv"),
        ("source_errata", "audit/source-errata.json"),
    )
    expected_critical: list[dict[str, Any]] = []
    for role, path in critical_pairs:
        row = mapping.get(path)
        require(row is not None, f"current-source critical path absent: {path}")
        expected_critical.append(
            {
                "path": path,
                "role": role,
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
            }
        )

    expected_pdfs: list[dict[str, Any]] = []
    for path in CURRENT_SOURCE_PDF_PATHS:
        row = mapping.get(path)
        require(row is not None, f"current-source generated PDF absent: {path}")
        expected_pdfs.append(
            {
                "path": path,
                "role": "generated_pdf_byte_identity_only",
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
            }
        )

    selectors = (
        ("claim_packets", ("claims/",)),
        ("formal_sources_and_receipts", ("audit/formal/",)),
        ("generated_pdf_set", ("output/pdf/",)),
        ("release_documents", ("README.md", "RELEASE_NOTES.md", "CHANGELOG.md")),
    )
    expected_subprojections: list[dict[str, Any]] = []
    for name, prefixes in selectors:
        selected = [
            row
            for row in expected_rows
            if any(
                row["path"] == prefix or row["path"].startswith(prefix)
                for prefix in prefixes
            )
        ]
        expected_subprojections.append(
            {
                "entries_sha256": hashlib.sha256(
                    json.dumps(
                        selected,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode("ascii")
                ).hexdigest(),
                "entry_count": len(selected),
                "name": name,
                "selectors": list(prefixes),
            }
        )

    ledger_path = "audit/evidence/FILE_REVIEW_LEDGER.csv"
    ledger_raw = candidate_blob(correction_entries, ledger_path)
    require(
        mapping[ledger_path]["sha256"] == hashlib.sha256(ledger_raw).hexdigest(),
        "current-source review ledger differs from projection",
    )
    try:
        ledger_text = ledger_raw.decode("utf-8", errors="strict")
        require(
            "\r" not in ledger_text and ledger_text.endswith("\n"),
            "review ledger line ending changed",
        )
        ledger_rows = list(csv.DictReader(io.StringIO(ledger_text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise CorrectionError(
            f"current-source review ledger malformed: {error}"
        ) from error
    require(
        bool(ledger_rows)
        and all(None not in row for row in ledger_rows)
        and {"path", "reviewer", "review_status"}.issubset(ledger_rows[0]),
        "current-source review ledger columns/rows malformed",
    )
    ledger_paths = [row.get("path", "") for row in ledger_rows]
    require(
        all(ledger_paths)
        and ledger_paths == sorted(ledger_paths)
        and len(ledger_paths) == len(set(ledger_paths)),
        "current-source review ledger paths changed",
    )
    expected_review = {
        "artifact": ledger_path,
        "evidence_scope": "historical_v0_9_0_exact_tag_tree_inventory",
        "human_reviewer_assignments": sum(
            row["reviewer"] not in {"", "UNASSIGNED"} for row in ledger_rows
        ),
        "inventoried_files": len(ledger_rows),
        "line_review_dispositions": sum(
            row["review_status"] not in {"", "INVENTORIED_NOT_REVIEWED"}
            for row in ledger_rows
        ),
        "status": "inventory_is_not_review",
        "tagged_commit_sha": "a9a275157237999c8da6ab813130d74f6113dec9",
    }
    require(
        (
            expected_review["inventoried_files"],
            expected_review["line_review_dispositions"],
            expected_review["human_reviewer_assignments"],
        )
        == (186, 0, 0),
        "current-source review ledger derived counts changed",
    )

    registry_path = "audit/evidence/assurance-registry.json"
    registry_raw = candidate_blob(correction_entries, registry_path)
    registry = parse_json_bytes(
        registry_raw, "current-source assurance registry", canonical=False
    )
    boundary = registry.get("release_boundary") if isinstance(registry, dict) else None
    require(isinstance(boundary, dict), "current-source release boundary absent")
    tag = boundary.get("tag")
    tag_object = boundary.get("tag_object_sha")
    tagged_commit = boundary.get("tagged_commit_sha")
    require(
        (tag, tag_object, tagged_commit)
        == (
            "v0.9.0",
            "dafa6cc9655eee70b4524ac92993c0dd820477e0",
            "a9a275157237999c8da6ab813130d74f6113dec9",
        )
        and git_text("rev-parse", f"refs/tags/{tag}") == tag_object
        and git_text("rev-parse", f"refs/tags/{tag}^{{commit}}") == tagged_commit
        and expected_review["tagged_commit_sha"] == tagged_commit,
        "current-source historical release/tag/review linkage changed",
    )
    expected_historical = {
        "evidence_class": "tag_release_fact",
        "review_completion_inferred": False,
        "tag": tag,
        "tag_object_sha": tag_object,
        "tagged_commit_sha": tagged_commit,
    }
    expected = {
        "binding": {
            "commit_binding": "not_self_asserted; resolve the manifest blob's containing commit from Git",
            "excluded_paths": [CURRENT_SOURCE_RELATIVE],
            "generated_at": "omitted_for_determinism",
            "projection_algorithm": (
                "canonical compact JSON of sorted repository .gitignore-aware tracked-plus-"
                "untracked entries {git_mode,path,sha256,size_bytes}; ambient global and "
                ".git/info excludes are ignored"
            ),
            "scope_kind": "self_excluding_worktree_source_projection",
        },
        "critical_artifacts": expected_critical,
        "generated_by": CURRENT_SOURCE_CHECKER,
        "generated_pdfs": expected_pdfs,
        "historical_release": expected_historical,
        "nonimplications": [
            "This deterministic consistency record is not authentication or attestation.",
            "It does not claim its own final SHA-256 or containing commit.",
            "It does not establish line review, human review, independent review, or institutional review.",
            "It does not establish source-to-formal correspondence, implementation refinement, estimator validity, or application validity.",
            "A generated PDF hash establishes byte identity only, not semantic or visual correctness.",
            "Ignored build products and Git object-store bytes are outside the source projection.",
            "The projection records repository index modes and worktree bytes; it is not an object-store integrity proof.",
        ],
        "repository": "sepahead/pid-rs",
        "review_inventory": expected_review,
        "schema": "pid-rs/current-source-state",
        "schema_revision": 1,
        "source_projection": {
            "entries": expected_rows,
            "entries_sha256": hashlib.sha256(compact_rows).hexdigest(),
            "entry_count": len(expected_rows),
        },
        "subprojections": expected_subprojections,
    }
    require(
        canonical_json(manifest_value, pretty=False)
        == canonical_json(expected, pretty=False),
        "current-source manifest does not exactly reproduce immutable correction-tree generator semantics",
    )


def validate_composite_receipt_data(
    value: Any,
    *,
    verify_git_objects: bool = True,
    receipt_raw: bytes | None = None,
    entry_repository_state: tuple[str, str] | None = None,
) -> dict[str, Any]:
    reject_json_floats(value, "composite receipt")
    reject_numeric_boolean_aliases(value, "composite receipt")
    require_boolean_field_types(value, "composite receipt")
    if verify_git_objects:
        require(
            entry_repository_state is not None,
            "composite validation lacks entry repository/security snapshot",
        )
        entry_head, entry_tree = entry_repository_state
    else:
        require(
            entry_repository_state is None,
            "semantic composite vector supplied repository authority",
        )
    receipt = exact_keys(
        value,
        {
            "acyclic_boundary",
            "claim",
            "custody_correction",
            "evidence_class",
            "hosted_observations",
            "implementation_anchor",
            "local_phase_custody",
            "milestone",
            "negative_evidence_semantics",
            "nonimplications",
            "remote_observations",
            "repository",
            "revision4_integration",
            "schema",
            "schema_revision",
        },
        "composite receipt",
    )
    require(
        receipt["schema"] == COMPOSITE_RECEIPT_SCHEMA
        and receipt["schema_revision"] == 2
        and receipt["repository"] == "sepahead/pid-rs"
        and receipt["evidence_class"]
        == "m1a_composite_lifecycle_custody_not_scientific_evidence"
        and receipt["negative_evidence_semantics"] == NEGATIVE_SEMANTICS
        and receipt["nonimplications"] == COMPOSITE_NONIMPLICATIONS,
        "composite receipt identity/nonclaim boundary changed",
    )
    require(
        receipt["claim"] == {"id": "KSG-INTEGER-HARMONIC-001", "revision": 4}
        and receipt["milestone"]
        == {
            "gate_id": "G1",
            "implementation_phase": "M1a",
            "integration_status": "integration_no_go",
            "status": "implementation_anchor_and_custody_correction_observed",
        }
        and receipt["revision4_integration"]
        == {
            "decision_v4_absent_at_correction": True,
            "evidence_matrix_v4_absent_at_correction": True,
            "open_gate_count": 13,
            "status": "integration_no_go",
        },
        "composite claim/milestone/integration boundary changed",
    )
    anchor = exact_keys(
        receipt["implementation_anchor"],
        {
            "commit",
            "direct_parent",
            "object_format",
            "protected_projection",
            "remains_implementation_after_correction",
            "tree",
        },
        "implementation anchor",
    )
    require(
        anchor["commit"] == IMPLEMENTATION
        and anchor["tree"] == IMPLEMENTATION_TREE
        and anchor["direct_parent"] == IMPLEMENTATION_PARENT
        and anchor["object_format"] == "sha1"
        and anchor["remains_implementation_after_correction"] is True
        and anchor["protected_projection"]
        == {
            "candidate_equals_anchor": True,
            "entry_count": PROTECTED_COUNT,
            "format": "canonical compact sorted-key ASCII JSON plus LF over sorted {path,git_mode,git_blob_oid_sha1,sha256,size_bytes} rows",
            "sha256": PROTECTED_SHA256,
        },
        "composite implementation anchor/projection changed",
    )
    correction = exact_keys(
        receipt["custody_correction"],
        {
            "author",
            "branch",
            "commit",
            "commit_message",
            "committer",
            "direct_parent",
            "distinct_from_implementation_anchor",
            "implementation_identity_after_correction",
            "object_format",
            "one_parent",
            "tree",
            "unsigned",
        },
        "custody correction",
    )
    correction_commit = validate_sha1(correction["commit"], "correction commit")
    correction_tree = validate_sha1(correction["tree"], "correction tree")
    human = {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME}
    require(
        correction_commit != IMPLEMENTATION
        and correction["direct_parent"] == IMPLEMENTATION
        and correction["implementation_identity_after_correction"] == IMPLEMENTATION
        and correction["distinct_from_implementation_anchor"] is True
        and correction["object_format"] == "sha1"
        and correction["branch"] == "main"
        and correction["one_parent"] is True
        and correction["unsigned"] is True
        and isinstance(correction["commit_message"], str)
        and correction["author"] == human == correction["committer"],
        "composite correction commit envelope changed",
    )
    correction_message_commitment = parse_correction_message(
        correction["commit_message"]
    )
    correction_output_envelope = {
        "author": human,
        "committer": human,
        "message": correction["commit_message"],
        "sealed_index_sha256": correction_message_commitment["sha256"],
        "sealed_index_size_bytes": correction_message_commitment["size_bytes"],
    }
    if not verify_git_objects:
        require(
            correction_commit == SELF_TEST_COMPOSITE_CORRECTION_COMMIT
            and correction_tree == SELF_TEST_COMPOSITE_CORRECTION_TREE,
            "semantic composite vector correction identity changed",
        )
    correction_entries: dict[str, Entry] | None = None
    descendant_entries: dict[str, Entry] | None = None
    retained_index_raw: bytes | None = None
    if verify_git_objects:
        checkpoint_envelope = parse_checkpoint(correction_commit, correction_tree)
        require(
            checkpoint_envelope["message"] == correction["commit_message"],
            "composite correction message differs from commit object",
        )
        correction_entries, _ = parse_tree(correction_tree)
        validate_correction_authority_artifacts(correction_entries)
        implementation_entries, _ = parse_tree(IMPLEMENTATION_TREE)
        policy_raw = candidate_blob(correction_entries, POLICY_RELATIVE)
        policy_value = parse_json_bytes(
            policy_raw, "correction-tree policy", canonical=True
        )
        policy_entries = validate_policy_data(policy_value, verify_anchor=True)
        require(
            policy_value["authority"]["inventory_status"] == "frozen"
            and policy_value["authority"]["credit_permitted"] is False
            and policy_value["authority"]["lifecycle_validation_permitted"] is True
            and EXPECTED_FROZEN_POLICY_SHA256 != "0" * 64
            and hashlib.sha256(policy_raw).hexdigest() == EXPECTED_FROZEN_POLICY_SHA256,
            "correction-tree policy is not frozen/no-credit/lifecycle-enabled",
        )
        schema_raw = candidate_blob(correction_entries, SCHEMA_RELATIVE)
        validate_schema_data(
            parse_json_bytes(
                schema_raw, "correction-tree composite schema", canonical=True
            )
        )
        require(
            hashlib.sha256(schema_raw).hexdigest() == EXPECTED_SCHEMA_SHA256,
            "correction-tree schema digest changed",
        )
        validate_boundary(
            candidate_blob(correction_entries, BOUNDARY_RELATIVE).decode(
                "utf-8", errors="strict"
            ),
            "frozen",
        )
        validate_delta(policy_entries, implementation_entries, correction_entries)
        validate_protected_projection(implementation_entries, correction_entries)
        validate_preclosure(correction_entries)
        validate_r5_preserved(implementation_entries, correction_entries)
        correction_negative_sha, correction_negative = validate_negative_candidate(
            correction_entries
        )
        validate_cert_rebind(implementation_entries, correction_entries)
        validate_cert_selftest_custody(implementation_entries, correction_entries)
        validate_r6(correction_entries, policy_entries)
        require(
            FUTURE_COMPOSITE_RECEIPT not in implementation_entries
            and FUTURE_COMPOSITE_RECEIPT not in correction_entries,
            "composite receipt is present in a subject tree",
        )
        require(
            FUTURE_RETAINED_INDEX not in implementation_entries
            and FUTURE_RETAINED_INDEX not in correction_entries,
            "retained sealed index is present in a subject tree",
        )
        head = git_text("rev-parse", "HEAD")
        require(
            head == entry_head
            and git_text("rev-parse", "HEAD^{tree}") == entry_tree
            and head != correction_commit
            and git_predicate("merge-base", "--is-ancestor", correction_commit, head),
            "current HEAD is not a strict descendant of the correction commit",
        )
        descendant_entries, _ = parse_tree(git_text("rev-parse", "HEAD^{tree}"))
        receipt_entry = descendant_entries.get(FUTURE_COMPOSITE_RECEIPT)
        retained_index_entry = descendant_entries.get(FUTURE_RETAINED_INDEX)
        require(
            receipt_raw is not None
            and receipt_entry is not None
            and receipt_entry.mode == "100644"
            and exact_object(receipt_entry.oid, "blob") == receipt_raw,
            "stdin receipt bytes do not equal the committed descendant receipt blob",
        )
        require(
            retained_index_entry is not None and retained_index_entry.mode == "100644",
            "retained sealed index is absent/non-regular in the receipt descendant",
        )
        retained_index_raw = exact_object(
            retained_index_entry.oid, "blob", maximum=MAX_INDEX_BYTES
        )
        correction_checker = correction_entries.get(CHECKER_RELATIVE)
        require(
            correction_checker is not None
            and correction_checker.mode == "100644"
            and candidate_worktree_bytes(descendant_entries, CHECKER_RELATIVE)
            == exact_object(correction_checker.oid, "blob"),
            "executed checker bytes differ from correction-tree checker",
        )
    remote = exact_keys(
        receipt["remote_observations"],
        {
            "authentication_claimed",
            "correction_commit",
            "implementation_commit",
            "ref",
            "remote",
            "repeated_observations_equal",
        },
        "remote observation",
    )
    require(
        remote
        == {
            "authentication_claimed": False,
            "correction_commit": correction_commit,
            "implementation_commit": IMPLEMENTATION,
            "ref": "refs/heads/main",
            "remote": "origin",
            "repeated_observations_equal": True,
        },
        "remote correction/head observation changed",
    )
    hosted = exact_keys(
        receipt["hosted_observations"],
        {
            "all_green_applies_only_to_correction_head",
            "correction_ci_success",
            "correction_codeql_success",
            "correction_heads_equal",
            "implementation_and_correction_heads_distinct",
            "implementation_ci_failure",
            "implementation_codeql_success",
            "implementation_heads_equal",
            "negative_evidence_artifact",
        },
        "hosted observations",
    )
    if verify_git_objects:
        require(
            hosted["implementation_ci_failure"]["negative_evidence_sha256"]
            == correction_negative_sha,
            "composite implementation CI does not bind correction-tree negative bytes",
        )
        negative_value = parse_json_bytes(
            candidate_blob(correction_entries, NEGATIVE_RELATIVE),
            "correction-tree negative evidence",
            canonical=True,
        )
        validate_negative_data(negative_value)
        normalized_composite_ci = dict(hosted["implementation_ci_failure"])
        normalized_composite_ci.pop("negative_evidence_sha256")
        require(
            normalized_composite_ci == negative_value["ci_failure"]
            and hosted["implementation_codeql_success"]
            == negative_value["codeql_success"],
            "composite implementation hosted observations differ from retained negative record",
        )
    require(
        hosted["all_green_applies_only_to_correction_head"] is True
        and hosted["correction_heads_equal"] is True
        and hosted["implementation_and_correction_heads_distinct"] is True
        and hosted["implementation_heads_equal"] is True,
        "hosted cross-head markers changed",
    )
    implementation_ci = validate_ci_observation(
        hosted["implementation_ci_failure"],
        head=IMPLEMENTATION,
        tree=IMPLEMENTATION_TREE,
        run_id=31686107959,
        successful=False,
        implementation=True,
    )
    implementation_codeql = validate_codeql_observation(
        hosted["implementation_codeql_success"],
        head=IMPLEMENTATION,
        tree=IMPLEMENTATION_TREE,
        run_id=31686106737,
        implementation=True,
    )
    correction_ci = validate_ci_observation(
        hosted["correction_ci_success"],
        head=correction_commit,
        tree=correction_tree,
        run_id=exact_integer(
            hosted["correction_ci_success"].get("run_id"),
            "correction CI run id",
            minimum=1,
        ),
        successful=True,
        implementation=False,
    )
    correction_codeql = validate_codeql_observation(
        hosted["correction_codeql_success"],
        head=correction_commit,
        tree=correction_tree,
        run_id=None,
        implementation=False,
    )
    require(
        hosted["correction_ci_success"]["run_id"]
        != hosted["correction_codeql_success"]["run_id"]
        and correction_codeql["alert_state"]["baseline_alert_numbers"]
        == implementation_codeql["alert_state"]["observed_alert_numbers"],
        "correction CI/CodeQL identity or alert baseline linkage changed",
    )
    run_ids = {
        hosted["implementation_ci_failure"]["run_id"],
        hosted["implementation_codeql_success"]["run_id"],
        hosted["correction_ci_success"]["run_id"],
        hosted["correction_codeql_success"]["run_id"],
    }
    job_ids = [
        row["job_id"]
        for group in (
            implementation_ci["rows"],
            implementation_codeql["jobs"],
            correction_ci["rows"],
            correction_codeql["jobs"],
        )
        for row in group
    ]
    analysis_ids = [
        row["analysis_id"]
        for group in (implementation_codeql["analyses"], correction_codeql["analyses"])
        for row in group
    ]
    artifact_ids = {
        implementation_ci["artifact"]["artifact_id"],
        correction_ci["artifact"]["artifact_id"],
    }
    require(
        len(run_ids) == 4
        and len(job_ids) == len(set(job_ids))
        and len(analysis_ids) == len(set(analysis_ids))
        and len(artifact_ids) == 2,
        "hosted run/job/analysis/artifact identities overlap across observations",
    )
    negative_artifact = validate_artifact_record(
        hosted["negative_evidence_artifact"],
        NEGATIVE_RELATIVE,
        "negative evidence artifact",
    )
    require(
        negative_artifact["sha256"]
        == hosted["implementation_ci_failure"]["negative_evidence_sha256"],
        "negative evidence artifact/CI digest disagree",
    )
    if correction_entries is not None:
        validate_artifact_against_tree(
            negative_artifact, correction_entries, "negative evidence artifact"
        )
    local = exact_keys(
        receipt["local_phase_custody"],
        {
            "alternate_index",
            "boundary_memo",
            "candidate_tree_matches_checkpoint",
            "certified_sxpid_correction",
            "checker",
            "checkpoint_became_correction_commit",
            "current_source_manifest",
            "detached_checkpoint_commit",
            "independently_recorded_before_ref_update",
            "lean_r5_preserved_sha256",
            "lean_r6_receipt",
            "policy",
            "postcommit_disposition",
            "postcommit_outputs",
            "precommit_disposition",
            "precommit_outputs",
            "schema",
            "self_test",
        },
        "local phase custody",
    )
    artifact_paths = {
        "boundary_memo": BOUNDARY_RELATIVE,
        "checker": CHECKER_RELATIVE,
        "current_source_manifest": CURRENT_SOURCE_RELATIVE,
        "lean_r6_receipt": R6_RELATIVE,
        "policy": POLICY_RELATIVE,
        "schema": SCHEMA_RELATIVE,
        "self_test": SELF_TEST_RELATIVE,
    }
    for name, path in artifact_paths.items():
        artifact = validate_artifact_record(local[name], path, f"local {name}")
        if correction_entries is not None:
            validate_artifact_against_tree(
                artifact, correction_entries, f"local {name}"
            )
    if correction_entries is not None:
        current_manifest_value = parse_json_bytes(
            candidate_blob(correction_entries, CURRENT_SOURCE_RELATIVE),
            "correction-tree current-source manifest",
            canonical=True,
        )
        validate_current_source_tree(current_manifest_value, correction_entries)
    require(
        local["lean_r5_preserved_sha256"] == R5_SHA256
        and local["detached_checkpoint_commit"] == correction_commit
        and local["independently_recorded_before_ref_update"] is True
        and local["candidate_tree_matches_checkpoint"] is True
        and local["checkpoint_became_correction_commit"] is True
        and local["precommit_disposition"] == "local_hosted_pending_no_credit"
        and local["postcommit_disposition"] == "local_hosted_pending_no_credit",
        "local phase identity/disposition changed",
    )
    alternate = exact_keys(
        local["alternate_index"],
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
        "alternate index",
    )
    exact_integer(
        alternate["entry_count"], "full candidate index entry count", minimum=1
    )
    exact_integer(alternate["size_bytes"], "alternate index size", minimum=1)
    validate_sha256(alternate["sha256"], "alternate index digest")
    require(
        alternate["input_descriptor_read_only"] is True
        and alternate["input_transport"] == "standard_input_regular_file_descriptor"
        and alternate["mode_octal"] == "0400"
        and alternate["path_or_residency_claimed"] is False
        and alternate["precommit_descriptor_observation_authenticated"] is False
        and alternate["single_link"] is True,
        "alternate-index fd0 custody changed",
    )
    retained_index_artifact = validate_artifact_record(
        alternate["retained_index_artifact"],
        FUTURE_RETAINED_INDEX,
        "retained sealed index artifact",
    )
    require(
        retained_index_artifact["sha256"] == alternate["sha256"]
        and retained_index_artifact["size_bytes"] == alternate["size_bytes"]
        and correction_message_commitment
        == {
            "sha256": alternate["sha256"],
            "size_bytes": alternate["size_bytes"],
        },
        "retained sealed index descriptor differs from precommit observation",
    )
    if not verify_git_objects:
        require(
            canonical_json(alternate, pretty=False)
            == canonical_json(SELF_TEST_COMPOSITE_ALTERNATE_INDEX, pretty=False),
            "semantic composite vector alternate-index facts changed",
        )
    if correction_entries is not None:
        require(
            alternate["entry_count"] == len(correction_entries),
            "alternate-index entry count differs from full correction tree",
        )
        require(
            descendant_entries is not None and retained_index_raw is not None,
            "retained sealed-index descendant state disappeared",
        )
        validate_artifact_against_tree(
            retained_index_artifact,
            descendant_entries,
            "retained sealed index artifact",
            maximum=MAX_INDEX_BYTES,
        )
        require(
            hashlib.sha256(retained_index_raw).hexdigest() == alternate["sha256"]
            and len(retained_index_raw) == alternate["size_bytes"],
            "retained sealed-index blob differs from precommit digest/size",
        )
        validate_retained_index_bytes(
            retained_index_raw,
            correction_tree=correction_tree,
            correction_entries=correction_entries,
        )
    phase_outputs = {
        "precommit": validate_phase_output_group(
            local["precommit_outputs"],
            phase="precommit",
            correction_commit=correction_commit,
            correction_tree=correction_tree,
            alternate=alternate,
            expected_envelope=correction_output_envelope,
        ),
        "postcommit": validate_phase_output_group(
            local["postcommit_outputs"],
            phase="postcommit",
            correction_commit=correction_commit,
            correction_tree=correction_tree,
            alternate=None,
            expected_envelope=correction_output_envelope,
        ),
    }
    normalized_across_phases: list[bytes] = []
    for phase in ("precommit", "postcommit"):
        for label in ("normal", "optimized"):
            item = dict(phase_outputs[phase][label])
            item["runtime_mode"] = "<NORMALIZED-RUNTIME-MODE>"
            item["mode"] = "<NORMALIZED-PHASE>"
            item["lifecycle"] = "<NORMALIZED-LIFECYCLE>"
            candidate_item = dict(item["candidate"])
            candidate_item["alternate_index_custody"] = "<NORMALIZED-ALTERNATE-INDEX>"
            item["candidate"] = candidate_item
            normalized_across_phases.append(canonical_json(item, pretty=False))
    require(
        len(set(normalized_across_phases)) == 1,
        "four phase outputs differ beyond runtime/phase/lifecycle/alternate observations",
    )
    if not verify_git_objects:
        for outputs in phase_outputs.values():
            for output in outputs.values():
                require(
                    output["candidate"]["delta"] == []
                    and output["negative_evidence"]["sha256"]
                    == EXPECTED_NEGATIVE_SHA256
                    and all(
                        canonical_json(output[name], pretty=False)
                        == canonical_json(expected, pretty=False)
                        for name, expected in SELF_TEST_COMPOSITE_PHASE_FACTS.items()
                    ),
                    "semantic composite vector checker-owned phase facts changed",
                )
    if correction_entries is not None:
        policy_raw_for_output = candidate_blob(correction_entries, POLICY_RELATIVE)
        policy_value_for_output = parse_json_bytes(
            policy_raw_for_output, "phase-output correction policy", canonical=True
        )
        policy_entries_for_output = validate_policy_data(
            policy_value_for_output, verify_anchor=True
        )
        implementation_entries_for_output, _ = parse_tree(IMPLEMENTATION_TREE)
        delta_for_output = validate_delta(
            policy_entries_for_output,
            implementation_entries_for_output,
            correction_entries,
        )
        expected_delta = [
            {"mode": mode, "path": path, "status": status}
            for path, status, mode in delta_for_output
        ]
        expected_envelope = parse_checkpoint(correction_commit, correction_tree)
        expected_cert_literals = {
            path: hashlib.sha256(candidate_blob(correction_entries, path)).hexdigest()
            for path in EXPECTED_REBIND_PATHS
        }
        expected_static = {
            path: hashlib.sha256(candidate_blob(correction_entries, path)).hexdigest()
            for path in (
                BOUNDARY_RELATIVE,
                SCHEMA_RELATIVE,
                CHECKER_RELATIVE,
                SELF_TEST_RELATIVE,
            )
        }
        expected_r6_sha = hashlib.sha256(
            candidate_blob(correction_entries, R6_RELATIVE)
        ).hexdigest()
        expected_current_sha = hashlib.sha256(
            candidate_blob(correction_entries, CURRENT_SOURCE_RELATIVE)
        ).hexdigest()
        expected_cert_selftest_sha = hashlib.sha256(
            candidate_blob(correction_entries, CERT_SELF_TEST)
        ).hexdigest()
        for outputs in phase_outputs.values():
            for output in outputs.values():
                require(
                    canonical_json(output["candidate"]["delta"], pretty=False)
                    == canonical_json(expected_delta, pretty=False)
                    and canonical_json(
                        output["candidate"]["commit_envelope"], pretty=False
                    )
                    == canonical_json(expected_envelope, pretty=False)
                    and canonical_json(
                        output["certified_sxpid_correction"][
                            "three_container_digest_literals"
                        ],
                        pretty=False,
                    )
                    == canonical_json(expected_cert_literals, pretty=False)
                    and output["certified_sxpid_correction"]["cli_only_selftest_sha256"]
                    == expected_cert_selftest_sha
                    and canonical_json(output["child_output_sha256"], pretty=False)
                    == canonical_json(EXPECTED_CHILD_STDOUT_SHA256, pretty=False)
                    and output["current_source_manifest_sha256"] == expected_current_sha
                    and output["policy_sha256"]
                    == hashlib.sha256(policy_raw_for_output).hexdigest()
                    and output["lean_r6"]["sha256"] == expected_r6_sha
                    and output["negative_evidence"]["sha256"]
                    == EXPECTED_NEGATIVE_SHA256
                    and canonical_json(output["static_artifact_sha256"], pretty=False)
                    == canonical_json(expected_static, pretty=False),
                    "phase output facts disagree with immutable correction-tree artifacts",
                )
    certified = exact_keys(
        local["certified_sxpid_correction"],
        {
            "bounded_private_cli_protocol_exact",
            "checker",
            "cli_only_selftest_transport",
            "scientific_authority_unchanged",
            "self_test",
            "three_container_digest_rebind_exact",
        },
        "certified SxPID correction",
    )
    cert_checker_artifact = validate_artifact_record(
        certified["checker"], CERT_CHECKER, "certified checker"
    )
    cert_selftest_artifact = validate_artifact_record(
        certified["self_test"], CERT_SELF_TEST, "certified self-test"
    )
    if correction_entries is not None:
        validate_artifact_against_tree(
            cert_checker_artifact, correction_entries, "certified checker"
        )
        validate_artifact_against_tree(
            cert_selftest_artifact, correction_entries, "certified self-test"
        )
    require(
        certified["bounded_private_cli_protocol_exact"] is True
        and certified["three_container_digest_rebind_exact"] is True
        and certified["cli_only_selftest_transport"] is True
        and certified["scientific_authority_unchanged"] is True,
        "certified SxPID correction boundary changed",
    )
    require(
        receipt["acyclic_boundary"]
        == {
            "correction_tree_excludes_receipt": True,
            "correction_tree_excludes_retained_index": True,
            "implementation_tree_excludes_receipt": True,
            "implementation_tree_excludes_retained_index": True,
            "later_descendant_required": True,
            "receipt_claims_its_own_commit": False,
            "receipt_hashes_itself": False,
            "receipt_subjects_preexist_receipt": True,
        },
        "composite acyclic boundary changed",
    )
    if verify_git_objects:
        final_head, final_tree = repository_context()
        require(
            final_head == entry_head == head
            and final_tree == entry_tree
            and final_tree == git_text("rev-parse", f"{head}^{{tree}}")
            and git_predicate(
                "merge-base", "--is-ancestor", correction_commit, final_head
            ),
            "descendant HEAD/security changed during composite validation",
        )
        final_entries, _ = parse_tree(git_text("rev-parse", "HEAD^{tree}"))
        final_receipt_entry = final_entries.get(FUTURE_COMPOSITE_RECEIPT)
        final_retained_index_entry = final_entries.get(FUTURE_RETAINED_INDEX)
        require(
            receipt_raw is not None
            and final_receipt_entry is not None
            and exact_object(final_receipt_entry.oid, "blob") == receipt_raw
            and retained_index_raw is not None
            and final_retained_index_entry is not None
            and exact_object(
                final_retained_index_entry.oid,
                "blob",
                maximum=MAX_INDEX_BYTES,
            )
            == retained_index_raw
            and candidate_worktree_bytes(final_entries, CHECKER_RELATIVE)
            == exact_object(correction_entries[CHECKER_RELATIVE].oid, "blob"),
            "receipt/checker descendant bindings changed during validation",
        )
    return {
        "correction_ci_jobs": len(correction_ci["rows"]),
        "correction_codeql_analyses": len(correction_codeql["analyses"]),
        "implementation_ci_jobs": len(implementation_ci["rows"]),
        "implementation_codeql_analyses": len(implementation_codeql["analyses"]),
    }


def validate_boundary(text: str, state: str) -> None:
    raw = text.encode("utf-8")
    require(
        len(raw) == EXPECTED_BOUNDARY_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == EXPECTED_BOUNDARY_SHA256,
        "boundary exact reviewed bytes changed",
    )
    marker = f"<!-- ksg-m1a-custody-correction-policy-state: {state} -->"
    state_text = (
        "provisional inventory; no correction or M1a lifecycle credit"
        if state == "provisional"
        else "frozen reviewed inventory; exact local lifecycle validation enabled; hosted pending; no credit"
    )
    require(text.count(marker) == 1, "boundary state marker changed")
    require(state_text in text, "boundary human-readable state changed")
    for token in (
        IMPLEMENTATION,
        IMPLEMENTATION_TREE,
        IMPLEMENTATION_PARENT,
        str(PROTECTED_COUNT),
        PROTECTED_SHA256,
        "31686107959",
        "31686106737",
        "local_hosted_pending_no_credit",
        "credit_permitted",
        "integration_no_go",
        "83-path",
        "fd0",
        "prospectively derived",
        "final authored edits",
        "no authored byte may change",
        "append-only r6 receipt/checker cycle finalization",
        "self-excluding current-source generation",
        "final authored correction tree",
        "final tree → sealed index → message commitment → commit",
        "before any ref update",
    ):
        require(token in text, f"boundary token disappeared: {token}")


def validate_static_artifacts(state: str) -> dict[str, str]:
    schema_raw = read_regular(SCHEMA_RELATIVE)
    validate_schema_data(
        parse_json_bytes(schema_raw, "composite schema", canonical=True)
    )
    boundary_raw = read_regular(BOUNDARY_RELATIVE)
    validate_boundary(boundary_raw.decode("utf-8", errors="strict"), state)
    selftest_raw = read_regular(SELF_TEST_RELATIVE)
    require(
        len(selftest_raw) == EXPECTED_CORRECTION_SELFTEST_SIZE_BYTES
        and hashlib.sha256(selftest_raw).hexdigest()
        == EXPECTED_CORRECTION_SELFTEST_SHA256,
        "correction self-test exact reviewed bytes changed",
    )
    return {
        BOUNDARY_RELATIVE: hashlib.sha256(boundary_raw).hexdigest(),
        SCHEMA_RELATIVE: hashlib.sha256(schema_raw).hexdigest(),
        CHECKER_RELATIVE: hashlib.sha256(read_regular(CHECKER_RELATIVE)).hexdigest(),
        SELF_TEST_RELATIVE: hashlib.sha256(selftest_raw).hexdigest(),
    }


def validate_correction_authority_artifacts(candidate: dict[str, Entry]) -> None:
    boundary_raw = candidate_blob(candidate, BOUNDARY_RELATIVE)
    selftest_raw = candidate_blob(candidate, SELF_TEST_RELATIVE)
    require(
        len(boundary_raw) == EXPECTED_BOUNDARY_SIZE_BYTES
        and hashlib.sha256(boundary_raw).hexdigest() == EXPECTED_BOUNDARY_SHA256
        and len(selftest_raw) == EXPECTED_CORRECTION_SELFTEST_SIZE_BYTES
        and hashlib.sha256(selftest_raw).hexdigest()
        == EXPECTED_CORRECTION_SELFTEST_SHA256,
        "correction boundary/self-test exact reviewed candidate bytes changed",
    )


def protected_paths(tree: dict[str, Entry]) -> tuple[str, ...]:
    packet = parse_json_bytes(
        candidate_blob(tree, ACTIVE_PACKET), "active packet", canonical=False
    )
    packet_files = packet.get("packet_files") if isinstance(packet, dict) else None
    require(
        isinstance(packet_files, dict) and len(packet_files) == 72,
        "active packet file inventory changed",
    )
    paths = set(packet_files) | set(PROTECTED_EXTRA_PATHS)
    require(len(paths) == PROTECTED_COUNT, "protected path union count changed")
    for path in paths:
        validate_path(path)
    return tuple(sorted(paths))


def protected_projection(tree: dict[str, Entry]) -> tuple[bytes, str]:
    rows: list[dict[str, Any]] = []
    for path in protected_paths(tree):
        entry = tree.get(path)
        require(entry is not None, f"protected path absent: {path}")
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
    encoded = canonical_json(rows, pretty=False)
    return encoded, hashlib.sha256(encoded).hexdigest()


def validate_protected_projection(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> dict[str, Any]:
    anchor_raw, anchor_digest = protected_projection(anchor)
    candidate_raw, candidate_digest = protected_projection(candidate)
    require(
        anchor_digest == PROTECTED_SHA256
        and candidate_digest == PROTECTED_SHA256
        and anchor_raw == candidate_raw,
        "protected 83-path implementation projection changed",
    )
    return {
        "candidate_equals_anchor": True,
        "entry_count": PROTECTED_COUNT,
        "sha256": PROTECTED_SHA256,
    }


def parse_correction_message(message: Any) -> dict[str, Any]:
    require(isinstance(message, str), "correction commit message is not text")
    match = re.fullmatch(
        r"Correct KSG M1a hosted custody wiring\n\n"
        r"Sealed-index-SHA256: ([0-9a-f]{64})\n"
        r"Sealed-index-Size: ([1-9][0-9]{0,7})\n",
        message,
    )
    require(match is not None, "correction commit message/trailer grammar changed")
    size_text = match.group(2)
    size = int(size_text, 10)
    require(
        str(size) == size_text and 0 < size <= MAX_INDEX_BYTES,
        "correction sealed-index size trailer is noncanonical/out of range",
    )
    return {"sha256": match.group(1), "size_bytes": size}


def parse_checkpoint_bytes(raw: bytes, expected_tree: str) -> dict[str, Any]:
    """Validate exact unsigned correction-commit bytes without resolving an object."""

    require(b"\r" not in raw and b"\0" not in raw, "checkpoint contains CR/NUL")
    header, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", "checkpoint lacks message separator")
    lines = header.split(b"\n")
    require(len(lines) == 4, "checkpoint is not exact unsigned single-parent form")
    require(
        lines[0] == f"tree {expected_tree}".encode("ascii")
        and lines[1] == f"parent {IMPLEMENTATION}".encode("ascii"),
        "checkpoint tree/parent changed",
    )
    message_text = message.decode("utf-8", errors="strict")
    message_commitment = parse_correction_message(message_text)
    values: list[bytes] = []
    identities: list[dict[str, str]] = []
    for label, line in ((b"author", lines[2]), (b"committer", lines[3])):
        prefix, space, value = line.partition(b" ")
        require(space == b" " and prefix == label, "checkpoint identity label changed")
        match = IDENTITY.fullmatch(value)
        require(match is not None, "checkpoint identity malformed")
        name = match.group("name").decode("utf-8", errors="strict")
        email = match.group("email").decode("ascii")
        timezone = match.group("timezone").decode("ascii")
        require(
            (name, email, timezone)
            == (EXPECTED_NAME, EXPECTED_EMAIL, EXPECTED_TIMEZONE),
            "checkpoint human identity/timezone changed",
        )
        values.append(value)
        identities.append({"email": email, "name": name})
    require(values[0] == values[1], "author/committer headers differ")
    return {
        "author": identities[0],
        "committer": identities[1],
        "message": message_text,
        "sealed_index_sha256": message_commitment["sha256"],
        "sealed_index_size_bytes": message_commitment["size_bytes"],
    }


def parse_checkpoint(commit: str, expected_tree: str) -> dict[str, Any]:
    return parse_checkpoint_bytes(exact_object(commit, "commit"), expected_tree)


def validate_delta(
    policy: tuple[PolicyEntry, ...],
    anchor: dict[str, Entry],
    candidate: dict[str, Entry],
) -> tuple[tuple[str, str, str], ...]:
    observed = changed_entries(anchor, candidate)
    expected = tuple((row.path, row.status, "100644") for row in policy)
    require(observed == expected, "candidate delta differs from exact policy")
    require(
        FINAL_MATRIX not in candidate
        and FINAL_DECISION not in candidate
        and FUTURE_COMPOSITE_RECEIPT not in candidate,
        "candidate contains future integration/receipt authority",
    )
    return observed


def decode_z_paths(raw: bytes, label: str) -> tuple[str, ...]:
    require(not raw or raw.endswith(b"\0"), f"{label} lacks NUL termination")
    result: list[str] = []
    for item in raw[:-1].split(b"\0") if raw else []:
        path = item.decode("utf-8", errors="strict")
        validate_path(path)
        result.append(path)
    require(
        result == sorted(result) and len(result) == len(set(result)),
        f"{label} not sorted/unique",
    )
    return tuple(result)


def parse_index_entries(raw: bytes) -> dict[str, Entry]:
    require(not raw or raw.endswith(b"\0"), "index listing lacks NUL")
    entries: dict[str, Entry] = {}
    for record in raw[:-1].split(b"\0") if raw else []:
        prefix, separator, path_raw = record.partition(b"\t")
        require(separator == b"\t", "malformed index record")
        fields = prefix.split(b" ")
        require(len(fields) == 3 and fields[2] == b"0", "staged/unmerged index record")
        mode = fields[0].decode("ascii")
        oid = fields[1].decode("ascii")
        path = path_raw.decode("utf-8", errors="strict")
        require(
            mode in {"100644", "100755"} and HEX40.fullmatch(oid) is not None,
            "invalid index leaf",
        )
        validate_path(path)
        require(path not in entries, "duplicate index path")
        entries[path] = Entry(mode, oid)
    require(list(entries) == sorted(entries), "index listing is not sorted")
    return entries


def read_sealed_index(descriptor: int) -> tuple[bytes, os.stat_result]:
    before = os.fstat(descriptor)
    require(stat.S_ISREG(before.st_mode), "fd0 is not a regular file")
    require(stat.S_IMODE(before.st_mode) == 0o400, "fd0 index mode is not 0400")
    require(before.st_nlink == 1, "fd0 index is not single-linked")
    require(0 < before.st_size <= MAX_INDEX_BYTES, "fd0 index size invalid")
    flags = fcntl.fcntl(descriptor, fcntl.F_GETFL)
    require(flags & os.O_ACCMODE == os.O_RDONLY, "fd0 index is not read-only")
    require(
        os.lseek(descriptor, 0, os.SEEK_CUR) == 0, "fd0 index is not positioned at zero"
    )
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
        chunk = os.read(descriptor, min(1024 * 1024, remaining))
        require(chunk, "fd0 index short read")
        chunks.append(chunk)
        remaining -= len(chunk)
    require(os.read(descriptor, 1) == b"", "fd0 index exceeds recorded size")
    after = os.fstat(descriptor)
    require(
        stat_identity(before) == stat_identity(after), "fd0 index changed while read"
    )
    return b"".join(chunks), before


def write_private_copy(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600
    )
    try:
        view = memoryview(raw)
        while view:
            count = os.write(descriptor, view)
            require(count > 0, "private index copy short write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_retained_index_bytes(
    raw: bytes,
    *,
    correction_tree: str,
    correction_entries: dict[str, Entry],
) -> None:
    entry_count = len(correction_entries)
    require(
        0 < len(raw) <= MAX_INDEX_BYTES
        and HEX40.fullmatch(correction_tree) is not None
        and type(entry_count) is int
        and entry_count > 0,
        "retained sealed-index reconstruction inputs changed",
    )
    results: list[tuple[str, dict[str, Entry], tuple[int, ...]]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-m1a-retained-index-", dir=fixed_temp_root()
    ) as directory:
        root = Path(directory)
        os.chmod(root, 0o700)
        for suffix in ("a", "b"):
            path = root / f"index-{suffix}"
            write_private_copy(path, raw)
            state = path.lstat()
            require(
                stat.S_ISREG(state.st_mode)
                and stat.S_IMODE(state.st_mode) == 0o600
                and state.st_nlink == 1
                and state.st_size == len(raw),
                "retained private index copy mode/link/size changed",
            )
            environment = {"GIT_INDEX_FILE": os.fspath(path)}
            reconstructed = git_text("write-tree", extra_environment=environment)
            listed = parse_index_entries(
                git("ls-files", "--stage", "-z", extra_environment=environment)
            )
            after = path.lstat()
            require(
                stat_identity(after) == stat_identity(state),
                "retained private index copy changed during reconstruction",
            )
            results.append((reconstructed, listed, stat_identity(state)))
    require(
        results[0][0:2] == results[1][0:2]
        and all(
            tree == correction_tree
            and len(entries) == entry_count
            and entries == correction_entries
            for tree, entries, _ in results
        ),
        "retained index does not reconstruct the correction tree/count twice",
    )


def validate_alternate_index(
    expected_sha256: str,
    expected_count: int,
    candidate_tree: str,
    candidate: dict[str, Entry],
) -> dict[str, Any]:
    require(
        HEX64.fullmatch(expected_sha256) is not None, "alternate-index digest malformed"
    )
    require(
        type(expected_count) is int and expected_count > 0,
        "alternate-index count invalid",
    )
    raw, metadata = read_sealed_index(0)
    digest = hashlib.sha256(raw).hexdigest()
    require(
        digest == expected_sha256, "alternate-index digest differs from external record"
    )
    results: list[tuple[str, dict[str, Entry]]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-m1a-correction-index-"
    ) as directory:
        for suffix in ("a", "b"):
            path = Path(directory) / f"index-{suffix}"
            write_private_copy(path, raw)
            environment = {"GIT_INDEX_FILE": os.fspath(path)}
            reconstructed = git_text("write-tree", extra_environment=environment)
            listed = parse_index_entries(
                git("ls-files", "--stage", "-z", extra_environment=environment)
            )
            results.append((reconstructed, listed))
    require(
        results[0] == results[1], "repeated alternate-index reconstruction differed"
    )
    require(
        all(
            tree == candidate_tree
            and entries == candidate
            and len(entries) == expected_count
            for tree, entries in results
        ),
        "alternate index differs from candidate tree/count",
    )
    return {
        "entry_count": expected_count,
        "input_descriptor_read_only": True,
        "input_transport": "standard_input_regular_file_descriptor",
        "mode_octal": "0400",
        "path_or_residency_claimed": False,
        "precommit_descriptor_observation_authenticated": False,
        "retained_index_artifact": {
            "git_blob_oid_sha1": blob_oid(raw),
            "path": FUTURE_RETAINED_INDEX,
            "sha256": digest,
            "size_bytes": metadata.st_size,
        },
        "sha256": digest,
        "single_link": True,
        "size_bytes": metadata.st_size,
    }


def interpret_git_predicate(returncode: int) -> bool:
    """Interpret only Git's documented predicate statuses; errors never prove absence."""

    require(returncode in {0, 1}, f"Git predicate returned error status: {returncode}")
    return returncode == 0


def git_predicate(*arguments: str) -> bool:
    result = git(*arguments, check=False)
    return interpret_git_predicate(result[0])


def observe_lifecycle_metadata() -> tuple[str | None, tuple[str, ...]]:
    result = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    symbolic = interpret_git_predicate(result[0])
    branch = (
        result[1:].decode("utf-8", errors="strict").rstrip("\n") if symbolic else None
    )
    require(
        symbolic or result[1:] == b"",
        "detached-HEAD predicate emitted unexpected output",
    )
    active: list[str] = []
    for relative in (
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
        path = Path(git_text("rev-parse", "--git-path", relative))
        if not path.is_absolute():
            path = ROOT / path
        if os.path.lexists(path):
            active.append(relative)
    return branch, tuple(active)


def validate_lifecycle_metadata(
    branch: str | None, active_operations: tuple[str, ...], mode: str
) -> None:
    require(
        (mode in {"precommit", "postcommit"} and branch == "main")
        or (mode == "candidate-commit" and branch is None),
        "lifecycle branch/attachment disagrees with mode",
    )
    require(not active_operations, "repository has an active Git operation")


def compare_candidate_to_worktree(candidate: dict[str, Entry]) -> None:
    for path, entry in candidate.items():
        raw = read_regular(path)
        mode = "100755" if (ROOT / path).stat().st_mode & stat.S_IXUSR else "100644"
        require(
            mode == entry.mode and blob_oid(raw) == entry.oid,
            f"worktree differs from candidate: {path}",
        )


def validate_worktree_lifecycle(
    mode: str,
    head: str,
    checkpoint: str,
    policy: tuple[PolicyEntry, ...],
    candidate: dict[str, Entry],
) -> str:
    modified_expected = tuple(row.path for row in policy if row.status == "M")
    added_expected = tuple(row.path for row in policy if row.status == "A")
    if mode == "precommit":
        require(head == IMPLEMENTATION, "precommit HEAD is not implementation anchor")
        require(
            git_predicate("diff", "--cached", "--quiet", IMPLEMENTATION, "--"),
            "primary index differs from implementation",
        )
        modified = decode_z_paths(
            git("diff", "--name-only", "-z", IMPLEMENTATION, "--"), "modified paths"
        )
        added = decode_z_paths(
            git("ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"),
            "untracked paths",
        )
        require(
            modified == modified_expected and added == added_expected,
            "worktree overlay differs from policy",
        )
        result = "implementation_plus_exact_correction_overlay"
    else:
        require(
            mode in {"candidate-commit", "postcommit"} and head == checkpoint,
            "committed lifecycle HEAD differs from checkpoint",
        )
        require(
            git_predicate("diff", "--cached", "--quiet", "HEAD", "--")
            and git_predicate("diff", "--quiet", "HEAD", "--"),
            "postcommit tracked state is dirty",
        )
        require(
            not decode_z_paths(
                git(
                    "ls-files",
                    "--others",
                    "--exclude-per-directory=.gitignore",
                    "-z",
                ),
                "untracked paths",
            ),
            "postcommit has repository-visible untracked paths",
        )
        result = (
            "clean_detached_direct_child_candidate_no_credit"
            if mode == "candidate-commit"
            else "clean_main_direct_child_postcommit_no_credit"
        )
    compare_candidate_to_worktree(candidate)
    return result


def validate_negative_data(value: Any) -> dict[str, Any]:
    reject_json_floats(value, "negative evidence")
    reject_numeric_boolean_aliases(value, "negative evidence")
    require_boolean_field_types(value, "negative evidence")
    record = exact_keys(
        value,
        {
            "capture_boundary",
            "ci_failure",
            "codeql_success",
            "negative_semantics",
            "nonimplications",
            "repository",
            "schema",
            "schema_revision",
            "subject",
        },
        "negative-evidence root",
    )
    exact_integer(
        record["schema_revision"],
        "negative-evidence schema revision",
        minimum=1,
        maximum=1,
    )
    require(
        record["schema"] == "pid-rs/ksg-rev4-public-ci-failure/v1"
        and record["schema_revision"] == 1
        and record["repository"] == "sepahead/pid-rs"
        and record["subject"]
        == {
            "direct_parent": IMPLEMENTATION_PARENT,
            "implementation_commit": IMPLEMENTATION,
            "tree": IMPLEMENTATION_TREE,
        }
        and record["negative_semantics"] == NEGATIVE_SEMANTICS
        and record["nonimplications"] == NEGATIVE_NONIMPLICATIONS,
        "negative-evidence identity/semantics/nonclaims changed",
    )
    ci = validate_ci_observation(
        record["ci_failure"],
        head=IMPLEMENTATION,
        tree=IMPLEMENTATION_TREE,
        run_id=31686107959,
        successful=False,
        implementation=True,
        negative_record=True,
    )
    codeql = validate_codeql_observation(
        record["codeql_success"],
        head=IMPLEMENTATION,
        tree=IMPLEMENTATION_TREE,
        run_id=31686106737,
        implementation=True,
    )
    require(
        record["ci_failure"]["jobs_successful"] == 44
        and record["ci_failure"]["jobs_total"] == 45,
        "terminal implementation CI totals changed",
    )
    require(
        record["ci_failure"]["job_roster_projection"]["sha256"]
        == EXPECTED_IMPLEMENTATION_CI_PROJECTION_SHA256
        and record["codeql_success"]["job_roster_projection"]["sha256"]
        == EXPECTED_IMPLEMENTATION_CODEQL_JOB_PROJECTION_SHA256
        and record["codeql_success"]["analysis_roster_projection"]["sha256"]
        == EXPECTED_IMPLEMENTATION_CODEQL_ANALYSIS_PROJECTION_SHA256,
        "reviewed implementation hosted roster projections changed",
    )
    expected_alerts = list(range(1, 192))
    alert_state = codeql["alert_state"]
    require(
        alert_state["baseline_alert_numbers"] == expected_alerts
        and alert_state["observed_alert_numbers"] == expected_alerts
        and alert_state["open_alert_numbers"] == list(range(47, 158))
        and alert_state["dismissed_alert_numbers"] == list(range(1, 47))
        and alert_state["fixed_alert_numbers"] == list(range(158, 192))
        and alert_state["new_alert_numbers"] == []
        and (
            alert_state["open"],
            alert_state["dismissed"],
            alert_state["fixed"],
            alert_state["total"],
        )
        == (111, 46, 34, 191),
        "implementation CodeQL exact alert-state observation changed",
    )
    artifact = ci["artifact"]
    require(
        artifact["artifact_id"] == 9175591607
        and artifact["name"]
        == "post-commit-source-state-v2-cb3f58f0b190454cb3f1090de8798261ec78f194"
        and artifact["content_sha256"]
        == "71b2b1ca9d4bd82846ceff3532f449af95656039a6b0d7625d9396fabd2fd996"
        and artifact["content_size_bytes"] == 2809,
        "implementation postcommit source-state artifact identity/content changed",
    )
    boundary = exact_keys(
        record["capture_boundary"],
        {
            "api_responses",
            "authentication_claimed",
            "causation_claimed",
            "failed_log_capture",
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
        "negative capture nonclaim boundary weakened",
    )
    expected_responses = sorted(
        record["ci_failure"]["api_captures"] + record["codeql_success"]["api_captures"],
        key=lambda item: item["endpoint_class"],
    )
    require(
        boundary["api_responses"] == expected_responses,
        "top-level API capture inventory differs from embedded exact projections",
    )
    require(
        {item["endpoint_class"]: item["sha256"] for item in expected_responses}
        == EXPECTED_IMPLEMENTATION_CAPTURE_SHA256,
        "reviewed implementation API capture projection digests changed",
    )
    log = exact_keys(
        boundary["failed_log_capture"],
        {
            "capture_command",
            "diagnostic_projection",
            "format",
            "repetitions_equal",
            "sha256",
            "size_bytes",
        },
        "failed log capture",
    )
    diagnostic_projection = {
        "diagnostic_line": FAILED_DIAGNOSTIC_LINE,
        "encoding": "UTF-8 normalized diagnostic line plus LF after stripping provider prefix, timestamp, and ANSI escapes",
        "sha256": "a96a053f70a1365eb1bf37ab0ebe1b837cf95462a8ca3207768e81bcef90083d",
        "size_bytes": 271,
    }
    require(
        log
        == {
            "capture_command": "gh run view 31686107959 --repo sepahead/pid-rs --job 94402437784 --log",
            "diagnostic_projection": diagnostic_projection,
            "format": "gh-cli-job-log-stdout-bytes/v1",
            "repetitions_equal": True,
            "sha256": "610c6faba7c794bbcbde35bb37b032f010045fd8f324b33887c0739c1d7b94f2",
            "size_bytes": 196292,
        },
        "failed raw-log/diagnostic capture changed",
    )
    return {
        "codeql_run_id": 31686106737,
        "failed_ci_run_id": 31686107959,
        "failed_jobs": 1,
        "jobs": 45,
    }


def validate_negative_candidate(
    candidate: dict[str, Entry],
) -> tuple[str, dict[str, Any]]:
    raw = candidate_blob(candidate, NEGATIVE_RELATIVE)
    require(
        len(raw) == EXPECTED_NEGATIVE_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == EXPECTED_NEGATIVE_SHA256,
        "retained hosted-failure evidence exact bytes changed",
    )
    value = parse_json_bytes(raw, "retained hosted failure", canonical=True)
    return hashlib.sha256(raw).hexdigest(), validate_negative_data(value)


def validate_preclosure(candidate: dict[str, Entry]) -> None:
    packet = parse_json_bytes(
        candidate_blob(candidate, ACTIVE_PACKET),
        "candidate active packet",
        canonical=False,
    )
    require(
        isinstance(packet, dict)
        and packet.get("status") == "integration_no_go"
        and packet.get("packet_stage")
        == "preclosure_core_manifest_must_be_regenerated_at_m1c"
        and tuple(packet.get("open_integration_gates", ())) == EXPECTED_PACKET_GATES,
        "candidate active packet advanced beyond correction boundary",
    )


def validate_r5_preserved(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> None:
    require(
        anchor.get(R5_RELATIVE) == candidate.get(R5_RELATIVE), "r5 Git entry changed"
    )
    raw = candidate_blob(candidate, R5_RELATIVE)
    require(hashlib.sha256(raw).hexdigest() == R5_SHA256, "r5 bytes changed")


def ast_node_byte_span(raw: bytes, node: ast.AST) -> tuple[int, int]:
    require(
        hasattr(node, "lineno")
        and hasattr(node, "end_lineno")
        and hasattr(node, "col_offset")
        and hasattr(node, "end_col_offset"),
        "AST node lacks an exact source span",
    )
    lines = raw.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    require(
        1 <= node.lineno <= len(starts) and 1 <= node.end_lineno <= len(starts),
        "AST source span is outside the source",
    )
    start = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    require(0 <= start < end <= len(raw), "AST byte span is malformed")
    return start, end


def lean_operational_cut_node(tree: ast.Module) -> ast.AST:
    mapping = assignment(tree, LEAN_OPERATIONAL_ASSIGNMENT).value
    require(
        isinstance(mapping, ast.Dict), "Lean operational wiring is not a literal dict"
    )
    matches = [
        value
        for key, value in zip(mapping.keys, mapping.values, strict=True)
        if isinstance(key, ast.Constant)
        and key.value == LEAN_CORRECTION_CHECKER_MAP_KEY
    ]
    require(
        len(matches) == 1,
        "Lean correction-checker operational digest slot is not unique",
    )
    return matches[0]


def normalized_lean_checker(
    raw: bytes,
    *,
    require_final_literals: bool = False,
) -> tuple[bytes, ast.Module, ast.Assign, ast.AST]:
    try:
        source = raw.decode("utf-8", errors="strict")
        tree = ast.parse(source, filename=LEAN_CHECKER)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise CorrectionError(
            f"Lean checker source is not strict Python: {error}"
        ) from error
    projection_assignment = assignment(tree, LEAN_REPLAY_PROJECTION_ASSIGNMENT)
    operational_value = lean_operational_cut_node(tree)
    projection_span = ast_node_byte_span(raw, projection_assignment.value)
    operational_span = ast_node_byte_span(raw, operational_value)
    projection_segment = raw[projection_span[0] : projection_span[1]]
    operational_segment = raw[operational_span[0] : operational_span[1]]
    final_projection_literal = (
        isinstance(projection_assignment.value, ast.Constant)
        and isinstance(projection_assignment.value.value, str)
        and HEX64.fullmatch(projection_assignment.value.value) is not None
        and projection_segment
        == f'"{projection_assignment.value.value}"'.encode("ascii")
    )
    final_operational_literal = (
        isinstance(operational_value, ast.Constant)
        and isinstance(operational_value.value, str)
        and HEX64.fullmatch(operational_value.value) is not None
        and operational_segment == f'"{operational_value.value}"'.encode("ascii")
    )
    provisional_projection = projection_segment == b'"0" * 64'
    provisional_operational = operational_segment == b"PENDING_OPERATIONAL_SHA256"
    require(
        (final_projection_literal and final_operational_literal)
        if require_final_literals
        else (
            (final_projection_literal or provisional_projection)
            and (final_operational_literal or provisional_operational)
        ),
        "Lean checker cycle-cut source forms changed",
    )
    replacements = [
        (
            *projection_span,
            b'"<REPLAY-RECEIPT-PROJECTION-CUT>"',
        ),
        (
            *operational_span,
            b'"<CORRECTION-CHECKER-DIGEST-CUT>"',
        ),
    ]
    first, second = sorted((item[0], item[1]) for item in replacements)
    require(first[1] <= second[0], "Lean checker normalization spans overlap")
    normalized = raw
    for start, end, replacement in sorted(replacements, reverse=True):
        normalized = normalized[:start] + replacement + normalized[end:]
    return normalized, tree, projection_assignment, operational_value


def lean_top_level_other(tree: ast.Module) -> list[str]:
    return [
        ast.dump(node, annotate_fields=True, include_attributes=False)
        for node in tree.body
        if not isinstance(
            node,
            (ast.Assign, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        )
    ]


def validate_lean_checker_ast_delta(
    anchor_checker: bytes, candidate_checker: bytes
) -> ast.Module:
    try:
        anchor_source = anchor_checker.decode("utf-8", errors="strict")
        candidate_source = candidate_checker.decode("utf-8", errors="strict")
        anchor_tree = ast.parse(anchor_source, filename=f"{LEAN_CHECKER}:r5")
        candidate_tree = ast.parse(candidate_source, filename=f"{LEAN_CHECKER}:r6")
    except (UnicodeDecodeError, SyntaxError) as error:
        raise CorrectionError(
            f"Lean checker structural source invalid: {error}"
        ) from error
    anchor_assignments = named_assignments(anchor_tree)
    candidate_assignments = named_assignments(candidate_tree)
    added_assignments = {
        "EXPECTED_PENDING_ACTIVE_CLAIM_PATHS",
        "EXPECTED_PENDING_ACTIVE_RESUME_PATHS",
        "EXPECTED_PENDING_OPERATIONAL_PATHS",
        "EXPECTED_R6_SEQUENCE_EXPLANATION_PATHS",
        "PENDING_OPERATIONAL_SHA256",
    }
    removed_assignments = {"EXPECTED_R5_SEQUENCE_EXPLANATION_PATHS"}
    changed_assignments = {
        "EXPECTED_ACTIVE_CLAIM_HASHES",
        "EXPECTED_ACTIVE_RESUME_HASHES",
        "EXPECTED_ACTIVE_RESUME_SHA256",
        "EXPECTED_CURRENT_REPLAY_POINTER_PATHS",
        "EXPECTED_OPERATIONAL_WIRING_HASHES",
        "EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256",
        "PRESERVED_PRIOR_REPLAY_HASHES",
        "PRESERVED_PRIOR_REPLAY_SCHEMAS",
        "RECEIPT_RELATIVE",
    }
    require(
        set(candidate_assignments) - set(anchor_assignments) == added_assignments
        and set(anchor_assignments) - set(candidate_assignments) == removed_assignments,
        "Lean r5-to-r6 assignment inventory changed",
    )
    for name in set(anchor_assignments) & set(candidate_assignments):
        require(
            (name in changed_assignments)
            == (not ast_equal(anchor_assignments[name], candidate_assignments[name])),
            f"Lean r5-to-r6 assignment delta changed: {name}",
        )
    anchor_definitions = named_definitions(anchor_tree)
    candidate_definitions = named_definitions(candidate_tree)
    changed_definitions = {
        "check_active_resume_split",
        "check_current_replay_pointers",
        "check_static_without_receipt",
    }
    require(
        set(anchor_definitions) == set(candidate_definitions),
        "Lean r5-to-r6 definition inventory changed",
    )
    for name in anchor_definitions:
        require(
            (name in changed_definitions)
            == (not ast_equal(anchor_definitions[name], candidate_definitions[name])),
            f"Lean r5-to-r6 definition delta changed: {name}",
        )
    require(
        lean_top_level_other(anchor_tree) == lean_top_level_other(candidate_tree),
        "Lean r5-to-r6 top-level imports/entrypoint changed",
    )
    return candidate_tree


def validate_lean_structural_custody(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> tuple[bytes, ast.Module]:
    anchor_checker = candidate_blob(anchor, LEAN_CHECKER)
    anchor_selftest = candidate_blob(anchor, LEAN_SELF_TEST)
    anchor_generator = candidate_blob(anchor, LEAN_GENERATOR)
    require(
        len(anchor_checker) == EXPECTED_LEAN_ANCHOR_CHECKER_SIZE_BYTES
        and hashlib.sha256(anchor_checker).hexdigest()
        == EXPECTED_LEAN_ANCHOR_CHECKER_SHA256
        and len(anchor_selftest) == EXPECTED_LEAN_ANCHOR_SELFTEST_SIZE_BYTES
        and hashlib.sha256(anchor_selftest).hexdigest()
        == EXPECTED_LEAN_ANCHOR_SELFTEST_SHA256
        and len(anchor_generator) == EXPECTED_LEAN_ANCHOR_GENERATOR_SIZE_BYTES
        and hashlib.sha256(anchor_generator).hexdigest()
        == EXPECTED_LEAN_ANCHOR_GENERATOR_SHA256,
        "Lean r5 structural anchors changed",
    )
    candidate_checker = candidate_blob(candidate, LEAN_CHECKER)
    candidate_selftest = candidate_blob(candidate, LEAN_SELF_TEST)
    candidate_generator = candidate_blob(candidate, LEAN_GENERATOR)
    require(
        len(candidate_selftest) == EXPECTED_LEAN_SELFTEST_SIZE_BYTES
        and hashlib.sha256(candidate_selftest).hexdigest()
        == EXPECTED_LEAN_SELFTEST_SHA256
        and len(candidate_generator) == EXPECTED_LEAN_GENERATOR_SIZE_BYTES
        and hashlib.sha256(candidate_generator).hexdigest()
        == EXPECTED_LEAN_GENERATOR_SHA256,
        "Lean r6 self-test/generator exact reviewed bytes changed",
    )
    r5_leaf = LEAN_R5_RECEIPT_LEAF.encode("ascii")
    r6_leaf = LEAN_R6_RECEIPT_LEAF.encode("ascii")
    require(
        candidate_generator.count(r6_leaf) == 1
        and candidate_generator.count(r5_leaf) == 0
        and candidate_generator.replace(r6_leaf, r5_leaf, 1) == anchor_generator,
        "Lean r6 generator differs beyond the unique r5-to-r6 output leaf",
    )
    candidate_tree = validate_lean_checker_ast_delta(anchor_checker, candidate_checker)
    return candidate_checker, candidate_tree


def lean_replay_receipt_projection(receipt: dict[str, Any]) -> str:
    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    require(isinstance(custody, dict), "Lean r6 custody projection is malformed")
    projected["custody_gate_sha256"] = {LEAN_SELF_TEST: custody.get(LEAN_SELF_TEST)}
    try:
        encoded = json.dumps(
            projected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CorrectionError(
            f"Lean r6 projection cannot canonicalize: {error}"
        ) from error
    return hashlib.sha256(encoded).hexdigest()


def validate_lean_cycle_relations(
    candidate_checker: bytes,
    receipt: dict[str, Any],
    *,
    correction_checker_sha: str,
    selftest_sha: str,
    generator_sha: str,
) -> None:
    validate_sha256(correction_checker_sha, "Lean correction-checker relation digest")
    validate_sha256(selftest_sha, "Lean self-test relation digest")
    validate_sha256(generator_sha, "Lean generator relation digest")
    normalized, _, projection_assignment, operational_value = normalized_lean_checker(
        candidate_checker, require_final_literals=True
    )
    require(
        len(normalized) == EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES
        and hashlib.sha256(normalized).hexdigest()
        == EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256,
        "Lean checker reviewed two-slot normalized source changed",
    )
    try:
        projection_literal = ast.literal_eval(projection_assignment.value)
        operational_literal = ast.literal_eval(operational_value)
    except (TypeError, ValueError) as error:
        raise CorrectionError(
            "Lean checker cycle cuts are not final string literals"
        ) from error
    receipt_projection = lean_replay_receipt_projection(receipt)
    require(
        operational_literal == correction_checker_sha
        and projection_literal == receipt_projection
        and isinstance(projection_literal, str)
        and HEX64.fullmatch(projection_literal) is not None,
        "Lean checker cycle-cut literals disagree with correction checker/r6 projection",
    )
    custody = exact_keys(
        receipt.get("custody_gate_sha256"),
        {LEAN_SELF_TEST, LEAN_CHECKER},
        "Lean r6 final custody gate",
    )
    replay_custody = exact_keys(
        receipt.get("replay_custody_gate_sha256"),
        {LEAN_SELF_TEST, LEAN_CHECKER},
        "Lean r6 replay custody gate",
    )
    checker_sha = hashlib.sha256(candidate_checker).hexdigest()
    require(
        custody == {LEAN_SELF_TEST: selftest_sha, LEAN_CHECKER: checker_sha}
        and replay_custody.get(LEAN_SELF_TEST) == selftest_sha,
        "Lean r6 final/replay custody files changed",
    )
    final_line = (
        f'{LEAN_REPLAY_PROJECTION_ASSIGNMENT} = "{projection_literal}"'
    ).encode("ascii")
    placeholder_line = (f'{LEAN_REPLAY_PROJECTION_ASSIGNMENT} = "0" * 64').encode(
        "ascii"
    )
    require(
        candidate_checker.count(final_line) == 1
        and candidate_checker.count(placeholder_line) == 0,
        "Lean final replay-projection line is not uniquely reconstructable",
    )
    replay_checker = candidate_checker.replace(final_line, placeholder_line, 1)
    require(
        replay_custody.get(LEAN_CHECKER) == hashlib.sha256(replay_checker).hexdigest()
        and replay_custody.get(LEAN_CHECKER) != checker_sha,
        "Lean replay checker pre-pin reconstruction changed",
    )
    operational = receipt.get("operational_wiring_sha256")
    require(
        isinstance(operational, dict)
        and operational.get(CHECKER_RELATIVE) == correction_checker_sha
        and operational.get(LEAN_GENERATOR) == generator_sha,
        "Lean r6 operational correction/generator custody changed",
    )
    prior_hashes = receipt.get("prior_replay_preservation_sha256")
    prior_schemas = receipt.get("prior_replay_schema")
    require(
        isinstance(prior_hashes, dict)
        and prior_hashes.get(R5_RELATIVE) == R5_SHA256
        and isinstance(prior_schemas, dict)
        and prior_schemas.get(R5_RELATIVE) == "pid-rs/lean-current-project-replay/v2",
        "Lean r6 r5 preservation relation changed",
    )


def validate_lean_final_custody(
    candidate: dict[str, Entry], receipt: dict[str, Any]
) -> None:
    anchor, _ = parse_tree(IMPLEMENTATION_TREE)
    candidate_checker, _ = validate_lean_structural_custody(anchor, candidate)
    correction_checker_sha = hashlib.sha256(
        candidate_blob(candidate, CHECKER_RELATIVE)
    ).hexdigest()
    selftest_sha = hashlib.sha256(candidate_blob(candidate, LEAN_SELF_TEST)).hexdigest()
    validate_lean_cycle_relations(
        candidate_checker,
        receipt,
        correction_checker_sha=correction_checker_sha,
        selftest_sha=selftest_sha,
        generator_sha=hashlib.sha256(
            candidate_blob(candidate, LEAN_GENERATOR)
        ).hexdigest(),
    )


def validate_r6(
    candidate: dict[str, Entry], policy: tuple[PolicyEntry, ...]
) -> dict[str, Any]:
    raw = candidate_blob(candidate, R6_RELATIVE)
    receipt = parse_json_bytes(raw, "Lean r6 receipt", canonical=True)
    require(
        isinstance(receipt, dict)
        and receipt.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and receipt.get("status") == "passed",
        "Lean r6 receipt identity/status changed",
    )
    prior = receipt.get("prior_replay_preservation_sha256")
    require(
        isinstance(prior, dict) and prior.get(R5_RELATIVE) == R5_SHA256,
        "r6 does not preserve r5",
    )
    category_by_path = {
        "audit/evidence/completion-active-resume.md": "active_resume_sha256",
        "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md": "active_claim_authority_sha256",
        "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md": "active_claim_authority_sha256",
        "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md": "active_claim_authority_sha256",
        "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md": "active_claim_authority_sha256",
        LEAN_SELF_TEST: "custody_gate_sha256",
        LEAN_CHECKER: "custody_gate_sha256",
    }
    excluded = {R6_RELATIVE, CURRENT_SOURCE_RELATIVE}
    for row in policy:
        if row.path in excluded:
            continue
        category_name = category_by_path.get(row.path, "operational_wiring_sha256")
        category = receipt.get(category_name)
        require(
            isinstance(category, dict)
            and category.get(row.path)
            == hashlib.sha256(candidate_blob(candidate, row.path)).hexdigest(),
            f"r6 {category_name} does not bind correction path: {row.path}",
        )
    validate_lean_final_custody(candidate, receipt)
    return {
        "schema": receipt["schema"],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "status": receipt["status"],
    }


def assignment(tree: ast.Module, name: str) -> ast.Assign:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    require(len(matches) == 1, f"source assignment is not unique: {name}")
    return matches[0]


def source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    require(
        isinstance(segment, str) and segment, "cannot recover source assignment segment"
    )
    return segment


def literal_assignment(tree: ast.Module, name: str) -> Any:
    node = assignment(tree, name)
    try:
        return ast.literal_eval(node.value)
    except (ValueError, TypeError) as error:
        raise CorrectionError(f"assignment is not literal: {name}") from error


def named_definitions(tree: ast.Module) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            require(
                node.name not in result, f"duplicate top-level definition: {node.name}"
            )
            result[node.name] = node
    return result


def named_assignments(tree: ast.Module) -> dict[str, ast.Assign]:
    result: dict[str, ast.Assign] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            name = node.targets[0].id
            require(name not in result, f"duplicate top-level assignment: {name}")
            result[name] = node
    return result


def ast_equal(left: ast.AST, right: ast.AST) -> bool:
    return ast.dump(left, annotate_fields=True, include_attributes=False) == ast.dump(
        right, annotate_fields=True, include_attributes=False
    )


def certified_protocol_projection(source: str, tree: ast.Module) -> str:
    require(
        source.count(CERT_PRIVATE_BEGIN) == 1 and source.count(CERT_PRIVATE_END) == 1,
        "certified private protocol markers are not unique",
    )
    begin = source.index(CERT_PRIVATE_BEGIN)
    end = source.index(CERT_PRIVATE_END, begin)
    require(begin < end, "certified private protocol markers are reversed")
    raw_block = source[begin:end].encode("utf-8")
    block = ast.parse(
        raw_block.decode("utf-8"), filename=f"{CERT_CHECKER}:private-protocol"
    )
    value = {
        "ast": ast.dump(block, annotate_fields=True, include_attributes=False),
        "raw_sha256": hashlib.sha256(raw_block).hexdigest(),
        "raw_size_bytes": len(raw_block),
    }
    require(
        len(raw_block) == EXPECTED_CERT_PRIVATE_PROTOCOL_SIZE_BYTES
        and value["raw_sha256"] == EXPECTED_CERT_PRIVATE_PROTOCOL_SHA256,
        "certified private protocol exact marked bytes changed",
    )
    return hashlib.sha256(canonical_json(value, pretty=False)).hexdigest()


def marked_cert_projection(
    source: str,
    begin_marker: str,
    end_marker: str,
    *,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> str:
    require(
        source.count(begin_marker) == 1 and source.count(end_marker) == 1,
        f"{label} markers are not unique",
    )
    begin = source.index(begin_marker)
    end = source.index(end_marker, begin)
    require(begin < end, f"{label} markers are reversed")
    raw = source[begin:end].encode("utf-8")
    require(
        len(raw) == expected_size
        and hashlib.sha256(raw).hexdigest() == expected_sha256,
        f"{label} exact marked bytes changed",
    )
    value = {
        "ast": ast.dump(
            ast.parse(raw.decode("utf-8"), filename=f"{CERT_CHECKER}:{label}"),
            annotate_fields=True,
            include_attributes=False,
        ),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_size_bytes": len(raw),
    }
    return hashlib.sha256(canonical_json(value, pretty=False)).hexdigest()


def validate_cert_source_structure(
    anchor_source: str, candidate_source: str
) -> dict[str, str]:
    anchor_tree = ast.parse(anchor_source, filename=CERT_CHECKER)
    candidate_tree = ast.parse(candidate_source, filename=CERT_CHECKER)
    require(
        candidate_source.count(CERT_BOOTSTRAP_BEGIN) == 1
        and candidate_source.count(CERT_BOOTSTRAP_END) == 1,
        "certified bootstrap marker inventory changed",
    )
    bootstrap_begin = candidate_source.index(CERT_BOOTSTRAP_BEGIN)
    bootstrap_end = candidate_source.index(CERT_BOOTSTRAP_END, bootstrap_begin) + len(
        CERT_BOOTSTRAP_END
    )
    require(
        candidate_source[bootstrap_begin - 2 : bootstrap_begin] == "\n\n"
        and candidate_source[bootstrap_end : bootstrap_end + 2] == "\n\n",
        "certified bootstrap blank-line convention changed",
    )
    require(
        marked_cert_projection(
            candidate_source,
            CERT_BOOTSTRAP_BEGIN,
            CERT_BOOTSTRAP_END,
            expected_size=EXPECTED_CERT_BOOTSTRAP_SIZE_BYTES,
            expected_sha256=EXPECTED_CERT_BOOTSTRAP_SHA256,
            label="bootstrap",
        )
        == EXPECTED_CERT_BOOTSTRAP_AST_SHA256,
        "certified bootstrap reviewed AST projection changed",
    )
    without_bootstrap = (
        candidate_source[:bootstrap_begin] + candidate_source[bootstrap_end + 2 :]
    )
    require(
        without_bootstrap.count(CERT_PRIVATE_BEGIN) == 1
        and without_bootstrap.count(CERT_PRIVATE_END) == 1,
        "certified private marker inventory changed",
    )
    begin = without_bootstrap.index(CERT_PRIVATE_BEGIN)
    end = without_bootstrap.index(CERT_PRIVATE_END, begin) + len(CERT_PRIVATE_END)
    require(
        without_bootstrap[begin - 3 : begin] == "\n\n\n"
        and without_bootstrap[end : end + 3] == "\n\n\n",
        "certified private block blank-line convention changed",
    )
    reconstructed = without_bootstrap[:begin] + without_bootstrap[end + 3 :]
    execution_target = "EXPECTED_EXECUTION_CONTAINER_SHA256"
    documentation_target = "EXPECTED_REVIEWED_DOCUMENTATION_SHA256"
    rebind_targets = {
        execution_target,
        documentation_target,
        "GATE_COMMANDS",
        *EXPECTED_CERT_NARROW_REBINDS,
    }
    anchor_definitions = named_definitions(anchor_tree)
    candidate_definitions = named_definitions(candidate_tree)
    allowed_new = set(EXPECTED_CERT_PRIVATE_FUNCTIONS)
    require(
        set(candidate_definitions) == set(anchor_definitions) | allowed_new,
        "certified checker definition inventory changed outside private protocol",
    )
    for name, node in anchor_definitions.items():
        if name == "main":
            continue
        require(
            ast_equal(node, candidate_definitions[name]),
            f"certified semantic core changed outside private protocol: {name}",
        )
    require(
        ast_equal(anchor_definitions["main"], candidate_definitions["main"]),
        "certified production main route changed",
    )
    anchor_assignments = named_assignments(anchor_tree)
    candidate_assignments = named_assignments(candidate_tree)
    require(
        set(candidate_assignments)
        == set(anchor_assignments)
        | {"SELF_TEST_VECTOR_SCHEMA", "MAX_SELF_TEST_VECTOR_BYTES"},
        "certified checker assignment inventory changed outside private protocol",
    )
    for name, node in anchor_assignments.items():
        if name in rebind_targets:
            continue
        require(
            ast_equal(node, candidate_assignments[name]),
            f"certified checker authority assignment changed: {name}",
        )
    normalized_anchor = anchor_source
    normalized_candidate = reconstructed
    for target in (
        execution_target,
        documentation_target,
        "GATE_COMMANDS",
        *EXPECTED_CERT_NARROW_REBINDS,
    ):
        anchor_rebind_segment = source_segment(
            anchor_source, anchor_assignments[target]
        )
        candidate_rebind_segment = source_segment(
            candidate_source, candidate_assignments[target]
        )
        marker = f"<EXACT-{target}-REBIND>"
        normalized_anchor = normalized_anchor.replace(anchor_rebind_segment, marker, 1)
        normalized_candidate = normalized_candidate.replace(
            candidate_rebind_segment, marker, 1
        )
    require(
        normalized_anchor == normalized_candidate,
        "removing custody blocks and normalizing exact bounded assignments does not reconstruct cb3f checker",
    )
    require(
        literal_assignment(candidate_tree, "SELF_TEST_VECTOR_SCHEMA")
        == "pid-rs/certified-sxpid2-claim-self-test-vector/v1"
        and ast_equal(
            assignment(candidate_tree, "MAX_SELF_TEST_VECTOR_BYTES").value,
            ast.parse("8 * 1024 * 1024", mode="eval").body,
        ),
        "certified private protocol identity/resource bound changed",
    )
    require(
        certified_protocol_projection(candidate_source, candidate_tree)
        == EXPECTED_CERT_PRIVATE_PROTOCOL_AST_SHA256,
        "certified private protocol reviewed AST projection changed",
    )
    anchor_execution = literal_assignment(anchor_tree, execution_target)
    candidate_execution = literal_assignment(candidate_tree, execution_target)
    anchor_documentation = literal_assignment(anchor_tree, documentation_target)
    candidate_documentation = literal_assignment(candidate_tree, documentation_target)
    require(
        isinstance(anchor_execution, dict)
        and tuple(anchor_execution) == EXPECTED_REBIND_PATHS[:2]
        and isinstance(candidate_execution, dict)
        and tuple(candidate_execution) == EXPECTED_REBIND_PATHS[:2]
        and isinstance(anchor_documentation, dict)
        and tuple(anchor_documentation) == EXPECTED_CERT_REVIEWED_DOC_PATHS
        and isinstance(candidate_documentation, dict)
        and tuple(candidate_documentation) == EXPECTED_CERT_REVIEWED_DOC_PATHS,
        "certified checker execution/documentation rebind key inventory changed",
    )
    require(
        anchor_documentation[EXPECTED_CERT_REVIEWED_DOC_PATHS[0]]
        == candidate_documentation[EXPECTED_CERT_REVIEWED_DOC_PATHS[0]],
        "certified audit-tool README authority changed",
    )
    require(
        tuple(literal_assignment(candidate_tree, "GATE_COMMANDS"))
        == EXPECTED_CERT_GATE_COMMANDS,
        "certified GATE_COMMANDS isolated normal/optimized inventory changed",
    )
    for name, (
        anchor_expected,
        candidate_expected,
    ) in EXPECTED_CERT_NARROW_REBINDS.items():
        require(
            literal_assignment(anchor_tree, name) == anchor_expected
            and literal_assignment(candidate_tree, name) == candidate_expected,
            f"bounded narrow certified digest rebind changed: {name}",
        )
    require(
        literal_assignment(anchor_tree, "EXPECTED_JUST_RELEASE_AUDIT_LINE_SHA256")
        == EXPECTED_CERT_RELEASE_LINE_SHA256
        == literal_assignment(
            candidate_tree, "EXPECTED_JUST_RELEASE_AUDIT_LINE_SHA256"
        ),
        "certified release-audit line digest changed",
    )
    return {
        **candidate_execution,
        "scripts/README.md": candidate_documentation["scripts/README.md"],
    }


def validate_correction_wiring_sources(sources: dict[str, str]) -> dict[str, str]:
    require(
        set(sources) == set(CORRECTION_WIRING_MARKERS)
        and all(isinstance(source, str) for source in sources.values()),
        "correction wiring source vector shape changed",
    )
    for path, (full_size, full_digest) in EXPECTED_CORRECTION_WIRING_FULL_FILES.items():
        full_raw = sources[path].encode("utf-8")
        require(
            len(full_raw) == full_size
            and hashlib.sha256(full_raw).hexdigest() == full_digest,
            f"full correction wiring container changed: {path}",
        )
    observed: dict[str, str] = {}
    required_tokens = {
        ".github/workflows/ci.yml": (
            "expected_checkout_sha=\"${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}\"",
            "checked-out HEAD does not equal the event-specific exact source SHA",
            'parent_record="$(git rev-list --parents -n 1 "$head")"',
            'parent_count="$(( ${#parent_fields[@]} - 1 ))"',
            'direct_parent="${parent_fields[1]}"',
            "exact direct-child source checkout is unexpectedly attached before candidate validation",
            "--mode candidate-commit",
            '[[ "$GITHUB_EVENT_NAME" == "push" ]]',
            '[[ "$GITHUB_REF" == "refs/heads/main" ]]',
            '[[ "$head" == "$GITHUB_SHA" ]]',
            'git switch --create main "$head"',
            "--mode postcommit",
            "strict postcommit replay is not applicable and no credit is granted",
        ),
        "justfile": (
            "python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py --validate-policy-only",
            "python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py --validate-policy-only",
            "python3 -I -S -B scripts/check-ksg-m1a-custody-correction-self-test.py",
            "python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction-self-test.py",
        ),
        "scripts/README.md": (
            "--allow-provisional-diagnostic",
            "--mode precommit",
            "--mode candidate-commit",
            "--mode postcommit",
            "--validate-composite-receipt < receipt.json",
            "none_typed_descendant_receipt_validation_only",
            "local_hosted_pending_no_credit",
            "The JSON Schema alone is insufficient",
        ),
    }
    for path, (
        begin_marker,
        end_marker,
        size,
        digest,
    ) in CORRECTION_WIRING_MARKERS.items():
        source = sources[path]
        require(
            source.count(begin_marker) == 1 and source.count(end_marker) == 1,
            f"correction wiring markers changed: {path}",
        )
        begin = source.index(begin_marker)
        end = source.index(end_marker, begin) + len(end_marker)
        raw = source[begin:end].encode("utf-8")
        require(
            len(raw) == size
            and hashlib.sha256(raw).hexdigest() == digest
            and all(
                raw.decode("utf-8").count(token) >= 1 for token in required_tokens[path]
            ),
            f"correction wiring reviewed marked bytes/semantics changed: {path}",
        )
        observed[path] = digest
    workflow_block = sources[".github/workflows/ci.yml"]
    begin = workflow_block.index(
        CORRECTION_WIRING_MARKERS[".github/workflows/ci.yml"][0]
    )
    end_marker = CORRECTION_WIRING_MARKERS[".github/workflows/ci.yml"][1]
    end = workflow_block.index(end_marker, begin) + len(end_marker)
    block = workflow_block[begin:end]
    require(
        block.count("--mode candidate-commit") == 2
        and block.count("--mode postcommit") == 2
        and block.count("--validate-policy-only") == 2
        and block.count("check-ksg-m1a-custody-correction-self-test.py") == 2,
        "correction workflow normal/optimized gate inventory changed",
    )
    workflow_job_begin = workflow_block.index("  ksg-harmonic-assurance:\n")
    workflow_job_end = workflow_block.index(
        "  formal-finite-convergence:\n", workflow_job_begin
    )
    workflow_job = workflow_block[workflow_job_begin:workflow_job_end].encode("utf-8")
    require(
        len(workflow_job) == EXPECTED_WORKFLOW_JOB_SIZE_BYTES
        and hashlib.sha256(workflow_job).hexdigest() == EXPECTED_WORKFLOW_JOB_SHA256,
        "full KSG harmonic-assurance job custody changed",
    )
    just_source = sources["justfile"]
    require(
        just_source.count("\nksg-revision:\n") == 1
        and just_source.count("\nksg-integration-decision:\n") == 1
        and just_source.count("\nrelease-audit:") == 1,
        "Just correction recipe/release route inventory changed",
    )
    recipe_begin = just_source.index("ksg-revision:\n")
    recipe_end = just_source.index("ksg-integration-decision:\n", recipe_begin)
    recipe = just_source[recipe_begin:recipe_end].encode("utf-8")
    release_line = next(
        line for line in just_source.splitlines() if line.startswith("release-audit:")
    )
    require(
        len(recipe) == EXPECTED_JUST_RECIPE_SIZE_BYTES
        and hashlib.sha256(recipe).hexdigest() == EXPECTED_JUST_RECIPE_SHA256
        and " ksg-revision " in f" {release_line} ",
        "full ksg-revision recipe/release-audit dependency custody changed",
    )
    return observed


def validate_correction_wiring(candidate: dict[str, Entry]) -> dict[str, str]:
    return validate_correction_wiring_sources(
        {
            path: candidate_blob(candidate, path).decode("utf-8", errors="strict")
            for path in CORRECTION_WIRING_MARKERS
        }
    )


def validate_cert_rebind(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> dict[str, str]:
    anchor_source = candidate_blob(anchor, CERT_CHECKER).decode(
        "utf-8", errors="strict"
    )
    candidate_source = candidate_blob(candidate, CERT_CHECKER).decode(
        "utf-8", errors="strict"
    )
    candidate_values = validate_cert_source_structure(anchor_source, candidate_source)
    observed: dict[str, str] = {}
    for path in EXPECTED_REBIND_PATHS:
        digest = hashlib.sha256(candidate_blob(candidate, path)).hexdigest()
        require(
            candidate_values.get(path) == digest,
            f"certified full-file rebind is stale: {path}",
        )
        observed[path] = digest
    validate_correction_wiring(candidate)
    return observed


def validate_cert_selftest_custody(
    anchor: dict[str, Entry], candidate: dict[str, Entry]
) -> str:
    require(
        anchor.get(CERT_SELF_TEST) != candidate.get(CERT_SELF_TEST),
        "certified self-test did not change despite the dynamic-loader custody repair",
    )
    raw = candidate_blob(candidate, CERT_SELF_TEST)
    require(
        len(raw) == EXPECTED_CERT_SELFTEST_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == EXPECTED_CERT_SELFTEST_SHA256,
        "certified self-test reviewed exact source changed",
    )
    source = raw.decode("utf-8", errors="strict")
    tree = ast.parse(source, filename=CERT_SELF_TEST)
    forbidden_imports = {"importlib", "runpy", "zipimport"}
    forbidden_calls = {"__import__", "compile", "eval", "exec"}
    forbidden_attributes = {
        "SourceFileLoader",
        "SourcelessFileLoader",
        "exec_module",
        "load_module",
        "module_from_spec",
        "run_module",
        "run_path",
        "spec_from_file_location",
    }
    for node in ast.walk(tree):
        require(not isinstance(node, ast.Assert), "certified self-test contains assert")
        if isinstance(node, ast.Import):
            require(
                not {alias.name.partition(".")[0] for alias in node.names}
                & forbidden_imports,
                "certified self-test imports a dynamic loader",
            )
        elif isinstance(node, ast.ImportFrom):
            require(
                (node.module or "").partition(".")[0] not in forbidden_imports,
                "certified self-test imports a dynamic loader",
            )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                require(
                    node.func.id not in forbidden_calls,
                    "certified self-test dynamically executes source",
                )
            elif isinstance(node.func, ast.Attribute):
                require(
                    node.func.attr not in forbidden_attributes,
                    "certified self-test calls a dynamic loader",
                )
    for token in (
        "PYTHON_CHILD_PREFIX",
        '"-O", "-I", "-S", "-B"',
        '"--self-test-vectors"',
        "malicious_adjacent_cache_payload",
        "PYC_MAGIC_BY_MINOR",
        "validate_static_cli_custody",
        "allow_abbrev",
        "CHECKER_STDIN_BOOTSTRAP",
        "EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256",
        "stable_source",
        "run_checker_source",
        "invoke_checker",
        "O_NOFOLLOW",
        "os.dup2(_input.fileno(), 0)",
        'exec(compile(_source, _logical_file, "exec", dont_inherit=True), _globals)',
    ):
        require(token in source, f"certified self-test custody token missing: {token}")
    launcher = literal_assignment(tree, "CHECKER_STDIN_BOOTSTRAP")
    require(
        isinstance(launcher, str)
        and len(launcher.encode("utf-8")) == EXPECTED_CERT_SELFTEST_LAUNCHER_SIZE_BYTES
        and hashlib.sha256(launcher.encode("utf-8")).hexdigest()
        == EXPECTED_CERT_SELFTEST_LAUNCHER_SHA256
        and literal_assignment(tree, "EXPECTED_CHECKER_STDIN_BOOTSTRAP_SIZE_BYTES")
        == EXPECTED_CERT_SELFTEST_LAUNCHER_SIZE_BYTES
        and literal_assignment(tree, "EXPECTED_CHECKER_STDIN_BOOTSTRAP_SHA256")
        == EXPECTED_CERT_SELFTEST_LAUNCHER_SHA256,
        "certified self-test exact stdin launcher changed",
    )
    launcher_tree = ast.parse(
        launcher, filename=f"{CERT_SELF_TEST}:checker-stdin-launcher"
    )
    require(
        [
            tuple(alias.name for alias in node.names)
            for node in launcher_tree.body
            if isinstance(node, ast.Import)
        ]
        == [("hashlib",), ("os",), ("sys",), ("tempfile",)]
        and [
            node.name
            for node in launcher_tree.body
            if isinstance(node, ast.FunctionDef)
        ]
        == ["_fail", "_size", "_digest", "_read_exact"]
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "compile"
            for node in ast.walk(launcher_tree)
        )
        == 1
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "exec"
            for node in ast.walk(launcher_tree)
        )
        == 1,
        "certified self-test stdin launcher AST custody changed",
    )
    return hashlib.sha256(raw).hexdigest()


def candidate_worktree_bytes(
    candidate: dict[str, Entry], relative: str, *, maximum: int = MAX_FILE_BYTES
) -> bytes:
    raw = read_regular(relative, maximum=maximum)
    entry = candidate.get(relative)
    require(
        entry is not None
        and entry.mode in {"100644", "100755"}
        and blob_oid(raw) == entry.oid,
        f"child/source bytes differ from candidate tree: {relative}",
    )
    return raw


def executable_identity(path_text: str) -> tuple[tuple[int, ...], str, tuple[int, ...]]:
    path = Path(path_text)
    link_state = path.lstat()
    resolved = path.resolve(strict=True)
    target_state = resolved.lstat()
    require(
        stat.S_ISREG(target_state.st_mode), "Python interpreter target is not regular"
    )
    return stat_identity(link_state), os.fspath(resolved), stat_identity(target_state)


def read_absolute_regular(path: Path, *, maximum: int) -> tuple[bytes, tuple[int, ...]]:
    before_path = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum,
            "absolute executable snapshot is not a bounded regular file",
        )
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            require(bool(chunk), "absolute executable snapshot ended early")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "absolute executable snapshot grew")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    validate_path_descriptor_identity(
        stat_identity(before_path),
        stat_identity(before),
        stat_identity(after),
        stat_identity(path.lstat()),
        "absolute executable snapshot",
    )
    return b"".join(chunks), stat_identity(before)


def write_private_interpreter(path: Path, raw: bytes) -> tuple[int, ...]:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags, 0o500)
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            require(written > 0, "private interpreter write made no progress")
            offset += written
        os.fsync(descriptor)
        state = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    require(
        stat.S_ISREG(state.st_mode)
        and stat.S_IMODE(state.st_mode) == 0o500
        and state.st_nlink == 1
        and state.st_size == len(raw),
        "private interpreter mode/link/size custody changed",
    )
    observed, observed_state = read_absolute_regular(
        path, maximum=MAX_INTERPRETER_BYTES
    )
    require(
        observed == raw and observed_state == stat_identity(state),
        "private interpreter bytes/stat disagree after creation",
    )
    return observed_state


def validate_python_stdin_bootstrap() -> None:
    raw = PYTHON_STDIN_BOOTSTRAP.encode("utf-8")
    value = {
        "ast": ast.dump(
            ast.parse(PYTHON_STDIN_BOOTSTRAP, filename="<isolated-stdin-bootstrap>"),
            annotate_fields=True,
            include_attributes=False,
        ),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_size_bytes": len(raw),
    }
    require(
        len(raw) == EXPECTED_PYTHON_STDIN_BOOTSTRAP_SIZE_BYTES
        and value["raw_sha256"] == EXPECTED_PYTHON_STDIN_BOOTSTRAP_SHA256
        and hashlib.sha256(canonical_json(value, pretty=False)).hexdigest()
        == EXPECTED_PYTHON_STDIN_BOOTSTRAP_AST_SHA256,
        "isolated stdin source bootstrap review projection changed",
    )


def run_candidate_source_python(
    candidate: dict[str, Entry],
    relative: str,
    arguments: tuple[str, ...],
    *,
    timeout: int,
) -> tuple[subprocess.CompletedProcess[bytes], bytes]:
    require(
        relative
        in {
            LEAN_CHECKER,
            LEAN_SELF_TEST,
            CERT_CHECKER,
            CERT_SELF_TEST,
            CURRENT_SOURCE_CHECKER,
        },
        "unapproved stdin-bound child checker",
    )
    validate_python_stdin_bootstrap()
    raw = candidate_worktree_bytes(candidate, relative)
    logical_path = os.fspath(ROOT / relative)
    before_python = executable_identity(sys.executable)
    resolved_python = Path(before_python[1])
    python_raw, python_state = read_absolute_regular(
        resolved_python, maximum=MAX_INTERPRETER_BYTES
    )
    environment = safe_environment()
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"})
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-m1a-python-", dir=fixed_temp_root()
    ) as temporary:
        temporary_root = Path(temporary)
        os.chmod(temporary_root, 0o700)
        temporary_mode_state = temporary_root.lstat()
        require(
            stat.S_ISDIR(temporary_mode_state.st_mode)
            and stat.S_IMODE(temporary_mode_state.st_mode) == 0o700,
            "private interpreter directory mode changed",
        )
        private_python = temporary_root / "python3"
        private_state = write_private_interpreter(private_python, python_raw)
        temporary_state = temporary_root.lstat()
        completed = subprocess.run(
            [
                os.fspath(private_python),
                *PYTHON_CHILD_PREFIX[1:],
                "-c",
                PYTHON_STDIN_BOOTSTRAP,
                logical_path,
                hashlib.sha256(raw).hexdigest(),
                str(len(raw)),
                *arguments,
            ],
            cwd=ROOT,
            env=environment,
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        final_private_raw, final_private_state = read_absolute_regular(
            private_python, maximum=MAX_INTERPRETER_BYTES
        )
        require(
            final_private_raw == python_raw
            and final_private_state == private_state
            and stat_identity(temporary_root.lstat()) == stat_identity(temporary_state),
            "private interpreter bytes/stat/directory changed across execution",
        )
    final_python_raw, final_python_state = read_absolute_regular(
        resolved_python, maximum=MAX_INTERPRETER_BYTES
    )
    require(
        executable_identity(sys.executable) == before_python
        and final_python_raw == python_raw
        and final_python_state == python_state
        and candidate_worktree_bytes(candidate, relative) == raw,
        f"candidate child/interpreter changed across stdin-bound execution: {relative}",
    )
    return completed, raw


def run_fixed_python(
    candidate: dict[str, Entry], relative: str, *, timeout: int
) -> str:
    completed, before_raw = run_candidate_source_python(
        candidate, relative, (), timeout=timeout
    )
    require(
        len(completed.stdout) <= MAX_GIT_OUTPUT_BYTES
        and len(completed.stderr) <= MAX_GIT_OUTPUT_BYTES,
        f"child checker output exceeded bound: {relative}",
    )
    require(
        completed.returncode == 0 and completed.stderr == b"",
        f"child checker failed: {relative}: "
        + completed.stderr.decode("utf-8", errors="replace").strip(),
    )
    require(
        relative in EXPECTED_CHILD_STDOUT
        and completed.stdout == EXPECTED_CHILD_STDOUT[relative],
        f"child checker reviewed success output changed: {relative}",
    )
    require(
        candidate_worktree_bytes(candidate, relative) == before_raw,
        f"candidate child bytes changed after execution: {relative}",
    )
    digest = hashlib.sha256(completed.stdout).hexdigest()
    require(
        digest == EXPECTED_CHILD_STDOUT_SHA256[relative],
        f"child checker success-output digest changed: {relative}",
    )
    return digest


def validate_current_source(candidate: dict[str, Entry]) -> str:
    before_manifest = candidate_worktree_bytes(
        candidate, CURRENT_SOURCE_RELATIVE, maximum=8 * 1024 * 1024
    )
    completed, before_checker = run_candidate_source_python(
        candidate, CURRENT_SOURCE_CHECKER, ("--emit",), timeout=180
    )
    require(
        candidate_worktree_bytes(candidate, CURRENT_SOURCE_CHECKER) == before_checker,
        "candidate current-source checker changed across replay",
    )
    actual = candidate_worktree_bytes(
        candidate, CURRENT_SOURCE_RELATIVE, maximum=8 * 1024 * 1024
    )
    require(
        len(completed.stdout) <= MAX_GIT_OUTPUT_BYTES
        and len(completed.stderr) <= MAX_GIT_OUTPUT_BYTES
        and completed.returncode == 0
        and completed.stderr == b""
        and completed.stdout == actual,
        "current-source manifest replay failed/stale/noisy",
    )
    require(actual == before_manifest, "current-source manifest changed across replay")
    return hashlib.sha256(actual).hexdigest()


def validate_repository_security(is_shallow: str, config_keys: tuple[str, ...]) -> None:
    require(
        is_shallow == "false",
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
        "worktree root changed",
    )
    config_raw = git("config", "--local", "--name-only", "--null", "--list")
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
    validate_repository_security(
        git_text("rev-parse", "--is-shallow-repository"), config_keys
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
        "HEAD identity malformed",
    )
    return head, tree


def validate_provisional_request(state: str, allow: bool) -> bool:
    provisional = state != "frozen"
    require(
        (provisional and allow) or (not provisional and not allow),
        "provisional/frozen CLI disposition mismatch",
    )
    return provisional


def observed_delta(anchor: dict[str, Entry]) -> list[dict[str, str]]:
    modified = decode_z_paths(
        git("diff", "--name-only", "-z", IMPLEMENTATION, "--"), "observed modified"
    )
    added = decode_z_paths(
        git("ls-files", "--others", "--exclude-per-directory=.gitignore", "-z"),
        "observed added",
    )
    rows = [{"path": path, "status": "M"} for path in modified]
    rows.extend({"path": path, "status": "A"} for path in added)
    rows.sort(key=lambda item: item["path"])
    require(len(rows) == len({row["path"] for row in rows}), "observed delta overlaps")
    for row in rows:
        if row["status"] == "M":
            require(
                row["path"] in anchor,
                f"observed modified path absent from anchor: {row['path']}",
            )
    return rows


def emit(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json(value, pretty=False))
    sys.stdout.buffer.flush()


def validate_self_test_vector(request: Any) -> None:
    require(
        isinstance(request, dict)
        and set(request) == {"payload", "schema", "validator"}
        and request.get("schema") == SELF_TEST_VECTOR_SCHEMA,
        "self-test vector envelope malformed",
    )
    validator = request.get("validator")
    payload = request.get("payload")
    if validator == "policy":
        validate_policy_data(payload, verify_anchor=False)
    elif validator == "schema":
        validate_schema_data(payload)
    elif validator == "schema_numeric_types":
        validate_schema_numeric_types(payload)
    elif validator == "json_scalar_types":
        require_boolean_field_types(payload, "JSON scalar-type vector")
        reject_json_floats(payload, "JSON scalar-type vector")
        reject_numeric_boolean_aliases(payload, "JSON scalar-type vector")
    elif validator == "boundary":
        require(
            isinstance(payload, dict) and set(payload) == {"state", "text"},
            "boundary vector malformed",
        )
        validate_boundary(payload["text"], payload["state"])
    elif validator == "negative":
        validate_negative_data(payload)
    elif validator == "runtime_mode":
        values = exact_keys(
            payload, {"isolated", "no_site", "optimize"}, "runtime mode vector"
        )
        require(
            values["isolated"] is True
            and values["no_site"] is True
            and type(values["optimize"]) is int
            and values["optimize"] == sys.flags.optimize,
            "runtime mode vector changed",
        )
    elif validator == "checkpoint":
        require(
            isinstance(payload, dict)
            and set(payload) == {"raw", "tree"}
            and isinstance(payload.get("raw"), str)
            and isinstance(payload.get("tree"), str),
            "checkpoint vector malformed",
        )
        parse_checkpoint_bytes(payload["raw"].encode("utf-8"), payload["tree"])
    elif validator == "lifecycle_metadata":
        require(
            isinstance(payload, dict)
            and set(payload) == {"active_operations", "branch", "mode"}
            and (
                payload.get("branch") is None or isinstance(payload.get("branch"), str)
            )
            and isinstance(payload.get("active_operations"), list)
            and all(isinstance(item, str) for item in payload["active_operations"]),
            "lifecycle-metadata vector malformed",
        )
        validate_lifecycle_metadata(
            payload["branch"], tuple(payload["active_operations"]), payload["mode"]
        )
    elif validator == "fixed_git_config":
        validate_fixed_git_config(payload)
    elif validator == "repository_security":
        require(
            isinstance(payload, dict)
            and set(payload) == {"config_keys", "is_shallow"}
            and isinstance(payload.get("is_shallow"), str)
            and isinstance(payload.get("config_keys"), list)
            and all(isinstance(item, str) for item in payload["config_keys"]),
            "repository-security vector malformed",
        )
        validate_repository_security(
            payload["is_shallow"],
            tuple(item.lower() for item in payload["config_keys"]),
        )
    elif validator == "temporary_root_security":
        values = exact_keys(
            payload,
            {"is_directory", "is_symlink", "owner_uid", "sticky"},
            "temporary-root vector",
        )
        validate_temporary_root_security(
            is_directory=values["is_directory"],
            is_symlink=values["is_symlink"],
            owner_uid=values["owner_uid"],
            sticky=values["sticky"],
        )
    elif validator == "path_descriptor_identity":
        values = exact_keys(
            payload,
            {"descriptor_after", "descriptor_before", "path_after", "path_before"},
            "path/descriptor vector",
        )
        identities: dict[str, tuple[int, ...]] = {}
        for name, value in values.items():
            require(
                isinstance(value, list)
                and len(value) == 7
                and all(type(item) is int for item in value),
                "path/descriptor vector identity changed",
            )
            identities[name] = tuple(value)
        validate_path_descriptor_identity(
            identities["path_before"],
            identities["descriptor_before"],
            identities["descriptor_after"],
            identities["path_after"],
            "synthetic path/descriptor",
        )
    elif validator == "correction_authority_artifacts":
        values = exact_keys(
            payload,
            {"boundary", "self_test"},
            "correction-authority artifact vector",
        )
        require(
            isinstance(values["boundary"], str)
            and isinstance(values["self_test"], str),
            "correction-authority vector values are not text",
        )
        boundary_raw = values["boundary"].encode("utf-8")
        selftest_raw = values["self_test"].encode("utf-8")
        require(
            len(boundary_raw) == EXPECTED_BOUNDARY_SIZE_BYTES
            and hashlib.sha256(boundary_raw).hexdigest() == EXPECTED_BOUNDARY_SHA256
            and len(selftest_raw) == EXPECTED_CORRECTION_SELFTEST_SIZE_BYTES
            and hashlib.sha256(selftest_raw).hexdigest()
            == EXPECTED_CORRECTION_SELFTEST_SHA256,
            "correction-authority exact reviewed bytes changed",
        )
    elif validator == "git_predicate_status":
        require(
            isinstance(payload, dict)
            and set(payload) == {"returncode"}
            and type(payload.get("returncode")) is int,
            "Git-predicate vector malformed",
        )
        interpret_git_predicate(payload["returncode"])
    elif validator == "raw_tree_graph":
        require(
            isinstance(payload, dict)
            and set(payload) == {"objects", "root"}
            and isinstance(payload.get("objects"), dict)
            and isinstance(payload.get("root"), str),
            "raw-tree graph vector malformed",
        )
        objects: dict[str, bytes] = {}
        require(
            0 < len(payload["objects"]) <= 64,
            "raw-tree graph object count is out of range",
        )
        for oid, encoded in payload["objects"].items():
            require(
                isinstance(oid, str)
                and HEX40.fullmatch(oid) is not None
                and isinstance(encoded, str)
                and len(encoded) <= 2 * 1024 * 1024
                and len(encoded) % 2 == 0,
                "raw-tree graph object encoding malformed",
            )
            try:
                raw_object = bytes.fromhex(encoded)
            except ValueError as error:
                raise CorrectionError(
                    "raw-tree graph object is not lowercase hex"
                ) from error
            require(
                encoded == raw_object.hex()
                and hashlib.sha1(  # noqa: S324 -- synthetic Git tree identity.
                    f"tree {len(raw_object)}\0".encode("ascii") + raw_object
                ).hexdigest()
                == oid,
                "raw-tree graph object id/bytes disagree",
            )
            objects[oid] = raw_object

        def load_vector_tree(oid: str) -> bytes:
            require(oid in objects, "raw-tree graph references an absent tree object")
            return objects[oid]

        walk_raw_tree_objects(payload["root"], load_vector_tree)
    elif validator == "certified_protocol":
        require(
            isinstance(payload, dict)
            and set(payload) == {"anchor_source", "candidate_source"}
            and isinstance(payload.get("anchor_source"), str)
            and isinstance(payload.get("candidate_source"), str),
            "certified-protocol vector malformed",
        )
        validate_cert_source_structure(
            payload["anchor_source"], payload["candidate_source"]
        )
    elif validator == "lean_checker_structure":
        require(
            isinstance(payload, dict)
            and set(payload) == {"anchor_source", "candidate_source"}
            and isinstance(payload.get("anchor_source"), str)
            and isinstance(payload.get("candidate_source"), str),
            "Lean checker structural vector malformed",
        )
        anchor_raw = payload["anchor_source"].encode("utf-8")
        candidate_raw = payload["candidate_source"].encode("utf-8")
        require(
            len(anchor_raw) == EXPECTED_LEAN_ANCHOR_CHECKER_SIZE_BYTES
            and hashlib.sha256(anchor_raw).hexdigest()
            == EXPECTED_LEAN_ANCHOR_CHECKER_SHA256
            and 0 < len(candidate_raw) <= MAX_FILE_BYTES,
            "Lean checker structural vector anchor/size changed",
        )
        validate_lean_checker_ast_delta(anchor_raw, candidate_raw)
        normalized, _, _, _ = normalized_lean_checker(candidate_raw)
        require(
            len(normalized) == EXPECTED_LEAN_NORMALIZED_CHECKER_SIZE_BYTES
            and hashlib.sha256(normalized).hexdigest()
            == EXPECTED_LEAN_NORMALIZED_CHECKER_SHA256,
            "Lean checker reviewed normalized structural vector changed",
        )
    elif validator == "correction_wiring":
        require(
            isinstance(payload, dict)
            and set(payload) == set(CORRECTION_WIRING_MARKERS)
            and all(isinstance(source, str) for source in payload.values()),
            "correction-wiring vector malformed",
        )
        validate_correction_wiring_sources(payload)
    elif validator == "lean_cycle_relations":
        require(
            isinstance(payload, dict)
            and set(payload) == {"checker_source", "receipt"}
            and isinstance(payload.get("checker_source"), str)
            and isinstance(payload.get("receipt"), dict),
            "Lean cycle-relation vector malformed",
        )
        checker_raw = payload["checker_source"].encode("utf-8")
        require(
            0 < len(checker_raw) <= MAX_FILE_BYTES,
            "Lean cycle-relation checker source exceeds bound",
        )
        validate_lean_cycle_relations(
            checker_raw,
            payload["receipt"],
            correction_checker_sha="a" * 64,
            selftest_sha="b" * 64,
            generator_sha="c" * 64,
        )
    elif validator == "composite_receipt_semantics":
        validate_composite_receipt_data(payload, verify_git_objects=False)
    else:
        raise CorrectionError("unsupported self-test validator")


def run_self_test_vectors(arguments: argparse.Namespace) -> int:
    require(
        arguments.mode is None
        and arguments.expected_candidate_tree is None
        and arguments.checkpoint_commit is None
        and arguments.alternate_index_sha256 is None
        and arguments.alternate_index_entry_count is None
        and not arguments.allow_provisional_diagnostic
        and not arguments.validate_policy_only
        and not arguments.validate_composite_receipt
        and not arguments.emit_observed_delta
        and not arguments.self_test_sealed_index,
        "self-test vector mode cannot accompany other arguments",
    )
    try:
        validate_self_test_vector(
            parse_json_bytes(
                sys.stdin.buffer.read(MAX_JSON_BYTES + 1),
                "self-test vector",
                canonical=True,
            )
        )
    except CorrectionError:
        emit({"result": "fail"})
        return 0
    emit({"result": "pass"})
    return 0


def run_self_test_sealed(arguments: argparse.Namespace) -> int:
    require(
        arguments.mode is None
        and arguments.checkpoint_commit is None
        and arguments.expected_candidate_tree is not None
        and arguments.alternate_index_sha256 is not None
        and arguments.alternate_index_entry_count is not None
        and not arguments.allow_provisional_diagnostic
        and not arguments.validate_policy_only
        and not arguments.validate_composite_receipt
        and not arguments.emit_observed_delta
        and not arguments.self_test_vectors,
        "sealed-index self-test mode argument mismatch",
    )
    candidate, _ = parse_tree(arguments.expected_candidate_tree)
    try:
        validate_alternate_index(
            arguments.alternate_index_sha256,
            arguments.alternate_index_entry_count,
            arguments.expected_candidate_tree,
            candidate,
        )
    except CorrectionError:
        emit({"result": "fail"})
        return 0
    emit({"result": "pass"})
    return 0


def run_composite_receipt_validation(arguments: argparse.Namespace) -> int:
    require(
        arguments.mode is None
        and arguments.expected_candidate_tree is None
        and arguments.checkpoint_commit is None
        and arguments.alternate_index_sha256 is None
        and arguments.alternate_index_entry_count is None
        and not arguments.allow_provisional_diagnostic
        and not arguments.validate_policy_only
        and not arguments.emit_observed_delta
        and not arguments.self_test_vectors
        and not arguments.self_test_sealed_index,
        "composite-receipt validation cannot accompany another mode/argument",
    )
    entry_repository_state = repository_context()
    raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    summary = validate_composite_receipt_data(
        parse_json_bytes(raw, "composite receipt", canonical=True),
        receipt_raw=raw,
        entry_repository_state=entry_repository_state,
    )
    emit(
        {
            "credit": "none_typed_descendant_receipt_validation_only",
            "disposition": "local_hosted_pending_no_credit",
            "schema": "pid-rs/ksg-rev4-m1a-composite-receipt-validation/v1",
            "summary": summary,
            "validated_receipt_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    return 0


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
    parser.add_argument("--emit-observed-delta", action="store_true")
    parser.add_argument("--self-test-vectors", action="store_true")
    parser.add_argument("--self-test-sealed-index", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    if arguments.self_test_vectors:
        return run_self_test_vectors(arguments)
    if arguments.self_test_sealed_index:
        return run_self_test_sealed(arguments)
    if arguments.validate_composite_receipt:
        return run_composite_receipt_validation(arguments)
    policy, policy_raw, policy_entries = load_policy(verify_anchor=True)
    head, head_tree = repository_context()
    anchor, _ = parse_tree(IMPLEMENTATION_TREE)
    validate_protected_projection(anchor, anchor)
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
                "credit": "none_mechanical_observation_requires_human_review",
                "entries": observed_delta(anchor),
                "implementation_commit": IMPLEMENTATION,
                "schema": "pid-rs/ksg-rev4-m1a-custody-correction-observed-delta/v1",
            }
        )
        return 0
    state = policy["authority"]["inventory_status"]
    static_hashes = validate_static_artifacts(state)
    if arguments.validate_policy_only:
        require(
            arguments.mode is None
            and arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None,
            "policy-only mode cannot accompany lifecycle arguments",
        )
        provisional = validate_provisional_request(
            state, arguments.allow_provisional_diagnostic
        )
        emit(
            {
                "credit": (
                    "none_policy_inventory_provisional"
                    if provisional
                    else "none_policy_frozen_lifecycle_validation_only"
                ),
                "disposition": "local_hosted_pending_no_credit",
                "entry_count": len(policy_entries),
                "implementation_commit": IMPLEMENTATION,
                "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
                "protected_projection": {
                    "entry_count": PROTECTED_COUNT,
                    "sha256": PROTECTED_SHA256,
                },
                "schema": "pid-rs/ksg-rev4-m1a-custody-correction-policy-validation/v1",
                "static_artifact_sha256": static_hashes,
            }
        )
        return 0
    require(
        arguments.mode is not None
        and arguments.expected_candidate_tree is not None
        and arguments.checkpoint_commit is not None,
        "lifecycle validation requires mode, external tree, and checkpoint",
    )
    provisional = validate_provisional_request(
        state, arguments.allow_provisional_diagnostic
    )
    if arguments.mode == "precommit":
        require(
            arguments.alternate_index_sha256 is not None
            and arguments.alternate_index_entry_count is not None,
            "precommit requires sealed fd0 index digest/count",
        )
    else:
        require(
            arguments.alternate_index_sha256 is None
            and arguments.alternate_index_entry_count is None,
            "postcommit forbids alternate-index arguments",
        )
    candidate_tree = arguments.expected_candidate_tree
    checkpoint = arguments.checkpoint_commit
    require(
        HEX40.fullmatch(candidate_tree) is not None
        and HEX40.fullmatch(checkpoint) is not None,
        "tree/checkpoint id malformed",
    )
    candidate, _ = parse_tree(candidate_tree)
    validate_correction_authority_artifacts(candidate)
    delta = validate_delta(policy_entries, anchor, candidate)
    protected = validate_protected_projection(anchor, candidate)
    envelope = parse_checkpoint(checkpoint, candidate_tree)
    branch, active = observe_lifecycle_metadata()
    validate_lifecycle_metadata(branch, active, arguments.mode)
    alternate: dict[str, Any] | None = None
    if arguments.mode == "precommit":
        require(
            arguments.alternate_index_sha256 is not None
            and arguments.alternate_index_entry_count is not None,
            "alternate-index values disappeared",
        )
        alternate = validate_alternate_index(
            arguments.alternate_index_sha256,
            arguments.alternate_index_entry_count,
            candidate_tree,
            candidate,
        )
        require(
            envelope["sealed_index_sha256"] == alternate["sha256"]
            and envelope["sealed_index_size_bytes"] == alternate["size_bytes"],
            "precommit checkpoint sealed-index trailer differs from fd0 bytes",
        )
    lifecycle = validate_worktree_lifecycle(
        arguments.mode, head, checkpoint, policy_entries, candidate
    )
    require(
        (arguments.mode == "precommit" and head_tree == IMPLEMENTATION_TREE)
        or (
            arguments.mode in {"candidate-commit", "postcommit"}
            and head_tree == candidate_tree
        ),
        "HEAD tree disagrees with lifecycle mode",
    )
    validate_preclosure(candidate)
    validate_r5_preserved(anchor, candidate)
    negative_sha, negative_summary = validate_negative_candidate(candidate)
    cert_rebind = validate_cert_rebind(anchor, candidate)
    cert_selftest_sha = validate_cert_selftest_custody(anchor, candidate)
    r6 = validate_r6(candidate, policy_entries)
    lean_output = run_fixed_python(candidate, LEAN_CHECKER, timeout=300)
    lean_self_output = run_fixed_python(candidate, LEAN_SELF_TEST, timeout=900)
    cert_output = run_fixed_python(candidate, CERT_CHECKER, timeout=300)
    cert_self_output = run_fixed_python(candidate, CERT_SELF_TEST, timeout=600)
    current_source = validate_current_source(candidate)
    final_head, final_tree = repository_context()
    final_branch, final_active = observe_lifecycle_metadata()
    validate_lifecycle_metadata(final_branch, final_active, arguments.mode)
    require(
        final_head == head and final_tree == head_tree,
        "HEAD/tree changed while child validation ran",
    )
    validate_worktree_lifecycle(
        arguments.mode, final_head, checkpoint, policy_entries, candidate
    )
    compare_candidate_to_worktree(candidate)
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
            "certified_sxpid_correction": {
                "cli_only_selftest_sha256": cert_selftest_sha,
                "scientific_authority_unchanged": True,
                "three_container_digest_literals": cert_rebind,
            },
            "child_output_sha256": {
                CERT_CHECKER: cert_output,
                CERT_SELF_TEST: cert_self_output,
                LEAN_CHECKER: lean_output,
                LEAN_SELF_TEST: lean_self_output,
            },
            "credit": "none_policy_inventory_provisional"
            if provisional
            else "none_local_custody_match_hosted_pending",
            "current_source_manifest_sha256": current_source,
            "disposition": "local_hosted_pending_no_credit",
            "implementation_anchor": {
                "commit": IMPLEMENTATION,
                "direct_parent": IMPLEMENTATION_PARENT,
                "protected_projection": protected,
                "tree": IMPLEMENTATION_TREE,
            },
            "lean_r6": r6,
            "lifecycle": lifecycle,
            "mode": arguments.mode,
            "negative_evidence": {"sha256": negative_sha, **negative_summary},
            "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
            "preclosure": {
                "final_decision_absent": True,
                "final_evidence_matrix_absent": True,
                "future_composite_receipt_absent": True,
                "open_gate_count": 13,
                "status": "integration_no_go",
            },
            "repository_state": {"active_git_operations": [], "branch": branch},
            "runtime_mode": sys.flags.optimize,
            "schema": "pid-rs/ksg-rev4-m1a-custody-correction-phase-validation/v1",
            "static_artifact_sha256": static_hashes,
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        CorrectionError,
        OSError,
        UnicodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"KSG M1a custody-correction check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
