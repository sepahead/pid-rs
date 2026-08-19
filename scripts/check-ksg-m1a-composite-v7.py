#!/usr/bin/env python3
"""Validate the append-only composite-v7 successor contract.

C7 preserves published C6 exactly, records two distinct bounded defect classes why
R6 is permanently unissued, and permits R7 only after a fresh C7 replay, one
bounded local record, and three fresh attempt-1 hosted successes.  This is an
operational evidence contract, not a scientific or authenticity claim.
"""

from __future__ import annotations

import argparse
import ast
import base64
from collections import defaultdict
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
from typing import Any, Callable


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v7.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"
V6_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v6.py"
V6_CHECKER_PATH = ROOT / V6_CHECKER_RELATIVE
V6_CHECKER_SHA256 = "6708de55bd0ffd938d1a567630b64d2a6d577cccd09b2285abe00ccf31cba494"
V6_CHECKER_SIZE_BYTES = 124_520

C6_COMMIT = "0c3afa0ab5b264370072a18d24655df35b90574c"
C6_TREE = "ad28fd5ec3eed76fca1315b24c2e047fb5e6cff4"
C6_PARENT = "be862b155d710573ec95356fc1cbe9a96a2b83b9"
C6_MESSAGE = "Repair KSG M1a composite v6 contract\n"
C6_IDENTITY = (
    b"author Sepehr Mahmoudian <sepmhn@gmail.com> 1787057941 +0200",
    b"committer Sepehr Mahmoudian <sepmhn@gmail.com> 1787057941 +0200",
)
C7_MESSAGE = "Repair KSG M1a composite v7 contract\n"
R7_MESSAGE = "Record KSG M1a composite v7 receipt\n"
FORBIDDEN_MESSAGES = frozenset(
    {
        "Record KSG M1a composite v4 receipt\n",
        "Record KSG M1a composite v5 receipt\n",
        "Record KSG M1a composite v6 receipt\n",
    }
)
FORBIDDEN_EVIDENCE_PATHS = (
    "audit/evidence/ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json",
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v6-2026-08-18.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v5-2026-08-18.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v6-2026-08-18.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v5-2026-08-18.json",
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v6-2026-08-18.json",
)

# Terminal C6 attempt-1 CI roster: 45 jobs, 44 success and the sole failure
# named below.  The committed predecessor capture binds the complete raw roster.
C6_CI_RUN = 32_139_920_717
C6_CI_FAILED_JOB = 95_719_898_423
C6_REPOSITORY_ID = 1_271_708_111
C6_CI_CREATED_AT = "2026-08-18T13:00:40Z"
C6_CI_UPDATED_AT = "2026-08-18T14:48:10Z"
C6_CODEQL_RUN = 32_139_921_184
C6_CONTRACT_RUN = 32_139_920_743
C6_CONTRACT_FAILED_JOB = 95_719_898_016
C6_MISSING_RG_DIAGNOSTIC = "composite publication PDF v6 adjudication: missing command: rg"

CI_RELATIVE = ".github/workflows/ci.yml"
CI_SHA256 = "cc046f60af6880a046272bf768151e3824aa0a9e22d03a6fe5a5f6bd433b19b7"
CI_SIZE_BYTES = 69_067
V6_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v6.yml"
RETIRED_V6_WORKFLOW_SHA256 = "0717fa37b2b40e5325ed2e436fd3d4f9a83475a136c7d0f41e3cfa0316d13c16"
RETIRED_V6_WORKFLOW_SIZE_BYTES = 1_585
V7_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v7.yml"
V7_WORKFLOW_SHA256 = "b6c8fb9a9ada3fc78fa909cf69f52fc823b15e285e17047498e6a981ac8724ce"
V7_WORKFLOW_SIZE_BYTES = 6_760
JUSTFILE_RELATIVE = "justfile"
JUSTFILE_SHA256 = "9397e036e5eafcdd9d0662002fff4ff0486856a474c3d04ff4db3c94b4b90116"
JUSTFILE_SIZE_BYTES = 36_074
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v7-path-policy-v1.json"
BOUNDARY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v7.py"
CAPTURE_TOOL_SHA256 = "2139176d51809853e98c558ec792eff61f0631ed027d04cc1a9d6d8f8ac1f06c"
CAPTURE_TOOL_SIZE_BYTES = 21_883
CAPTURE_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v7.schema.json"
LOCAL_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v7-local-closure.py"
LOCAL_TOOL_SHA256 = "5268322d756e546f29ed9d2ded58264800808570be286adfba562f7decb284c1"
LOCAL_TOOL_SIZE_BYTES = 35_401
LOCAL_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v7.schema.json"
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v7.schema.json"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v7.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v7-self-test.py"
COUNTEREXAMPLE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-v6-local-closure-"
    "counterexample-v7-2026-08-18.json"
)
COUNTEREXAMPLE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-counterexample-v7.schema.json"
)
COUNTEREXAMPLE_SHA256 = "cabcd565f25e11d14c4082532ea7efe1987eb0d700c115a8fbf36937486eede2"
COUNTEREXAMPLE_SIZE_BYTES = 9_103
COUNTEREXAMPLE_SCHEMA_SHA256 = "d06f0437cd5eddce35a88be9eccd5653ddc36b29b361ff924c33578d15a4de7b"
COUNTEREXAMPLE_SCHEMA_SIZE_BYTES = 21_621
PREDECESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-"
    "hosted-capture-v7-2026-08-18.json"
)
PREDECESSOR_CAPTURE_SHA256 = "e9a1d574cb4127263d8aaec3e291e78836b849f9b402af8a0daa5eb37cc70104"
PREDECESSOR_CAPTURE_SIZE_BYTES = 1_819_338
PREDECESSOR_NORMALIZED_SHA256 = "bc81849000b3967b9f3a226629e39cfe754fc2cf951294a94fc319a41ac0f9e8"
SUCCESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v7-2026-08-18.json"
)
LOCAL_RECORD_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v7-2026-08-18.json"
)
RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v7-2026-08-18.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
R11_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r11.json"
)
R12_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r12.json"
)
R11_SHA256 = "2d72cd2a170d06fff824ec69f0cb4b722739bdfb64782d553313d35cedeec83e"
R11_SIZE_BYTES = 139_124
LEAN_CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
LEAN_SELF_TEST_RELATIVE = "scripts/check-lean-toolchain-freeze-self-test.py"
LEAN_CUSTODY_PATHS = (LEAN_SELF_TEST_RELATIVE, LEAN_CHECKER_RELATIVE)

PUBLICATION_PATHS = (
    "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-visual-receipt-2026-08-18.md",
    "audit/formal/latex/ksg-m1a-composite-v7-boundary.tex",
    "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.svg",
    "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf",
    "output/pdf/ksg-m1a-composite-v7-boundary.pdf",
    "output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv",
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh",
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh",
)
PUBLICATION_FIELDS = {
    "boundary_markdown": BOUNDARY_RELATIVE,
    "boundary_pdf": "output/pdf/ksg-m1a-composite-v7-boundary.pdf",
    "figure_pdf": "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf",
    "figure_svg": "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.svg",
    "latex_source": "audit/formal/latex/ksg-m1a-composite-v7-boundary.tex",
    "pdf_gate": "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh",
    "pdf_gate_self_test": "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh",
    "rendering_receipt": "output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv",
    "visual_receipt": "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-visual-receipt-2026-08-18.md",
}
RECEIPT_NONIMPLICATIONS = [
    "The C6 hosted failures and static local contradiction have zero qualification credit and cannot issue R6.",
    "The two C6 defect classes are distinct bounded operational findings, not independent replications or scientific findings.",
    "Apt-installed ripgrep is package-name and route bound here, not byte-pinned or hermetically supplied.",
    "Successful C7 runs establish only reached operational gates; they do not prove unreached commands, cross-platform independence, or absence of other defects.",
    "Provider responses, Git identities, local executable observations, and timestamps do not authenticate themselves or establish trusted time.",
    "This receipt does not establish PID, KSG, theorem, numerical-result, security, privacy, accessibility, or application validity.",
]
CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Two retrieval repetitions are correlated provider observations, not independent replications.",
    "The predecessor phase records C6's failed hosted attempt and cannot issue R6 or qualify C7.",
    "The C6 missing-rg diagnostic is dependency-closure evidence, not evidence of defective PDF content.",
    "The separate C6 local-recorder contradiction is source-and-byte evidence, not a detailed runtime trace.",
    "A successful successor phase is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]
V6_CAPTURE_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v6.py",
    "sha256": "8089cce79cd9ff14e9eda1b46c51a746b508b026f2cbf5a83cb295e7860d7efa",
    "size_bytes": 41_770,
}
V6_LOCAL_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v6-local-closure.py",
    "sha256": "5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a",
    "size_bytes": 57_021,
}
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
ROLE_KIND = {
    role: kind
    for prefix in ("predecessor", "successor")
    for kind in ("ci", "codeql", "contract")
    for role in (f"{prefix}_{kind}",)
}
EXPECTED_RUN_CONCLUSION = {
    "predecessor_ci": "failure",
    "predecessor_codeql": "success",
    "predecessor_contract": "failure",
    "successor_ci": "success",
    "successor_codeql": "success",
    "successor_contract": "success",
}
PREDECESSOR_REQUIRED_FAILED_JOB_IDS = {
    "predecessor_ci": {C6_CI_FAILED_JOB},
    "predecessor_codeql": set(),
    "predecessor_contract": {C6_CONTRACT_FAILED_JOB},
}
PREDECESSOR_REQUIRED_FAILURE_IDENTITIES = {
    "predecessor_ci": {
        C6_CI_FAILED_JOB: (
            "Formal LaTeX / PDF inventory and cross-toolchain structure",
            (
                (
                    11,
                    "Rebuild papers and check cross-toolchain text, geometry, fonts, and workflow renders",
                ),
            ),
        )
    },
    "predecessor_codeql": {},
    "predecessor_contract": {
        C6_CONTRACT_FAILED_JOB: (
            "Validate the composite-v6 correction contract",
            (
                (
                    9,
                    "Validate immutable predecessor PDF portability and the bounded successor publication",
                ),
            ),
        )
    },
}
PREDECESSOR_REQUIRED_LOG_BINDINGS = {
    "predecessor_ci": {
        C6_CI_FAILED_JOB: (
            "166e1d703f81c080adecc7a6bc3f366bf66b11708b3c31b3ea1cd121fcd94460",
            128_761,
        )
    },
    "predecessor_codeql": {},
    "predecessor_contract": {
        C6_CONTRACT_FAILED_JOB: (
            "b1665fe7c8573a1df1e47ea78cbe39c804a960ec1f8aabcc79c23be574ec0960",
            57_487,
        )
    },
}
C6_CI_PRIOR_PDF_GATE_MARKERS = (
    b"OK: certified SxPID2 assurance PDF is warning-free and cross-toolchain structurally equivalent (fe8a8af0ddec4904922c3073f45bc7503d7e1b00d34d168b083463d638392142)",
    b"OK: dependency-colored SxPID PDF is lint-clean, semantically complete, font-complete, warning-free, and cross-toolchain structurally equivalent (4579c676c569916e26c2d60307c020e936da8ef9153cff328b3ab7782c451ad1)",
    b"OK: ecosystem compatibility audit PDF is warning-free and cross-toolchain structurally equivalent (8d79e4ce11b525c6e3da4216f740200cb133408a7727be739681cb2bbb9960d8)",
    b"OK: exact log-product SxPID2 PDF is warning-free and cross-toolchain structurally equivalent (8560773507b3c889cd9c3ff7962f76947473c13c58b4a137d9b66a9725e8d0c4)",
    b"OK: finite-alphabet convergence PDF is lint-clean, semantically complete, font-complete, warning-free, and cross-toolchain structurally equivalent (f8847a51f4b7f82bdf8ec150418c0fa7c7e25f232a6c117d11758d6754419e3e)",
    b"OK: formal-tool adoption PDF is warning-free and cross-toolchain structurally equivalent (d07a243f9b14b27cd83aed6355c89c027053244fce86006e06a13510ca098b97)",
    b"OK: foundational SxPID audit PDF, exact witnesses, and Lean firewall are warning-free and reproducible (6975e6dfed5dd72cced9c82b2a3980481ca6b1125cf8175dd2990bbb58e2ee8e)",
)
POLICY_NONIMPLICATIONS = [
    "This path policy describes the exact C7 and conditional R7 topology; it does not itself authorize, authenticate, qualify, or issue either commit or evidence.",
    "The two C6 defects are bounded operational defects; neither is a PID, estimator, theorem, numerical-result, security, accessibility, or application result.",
    "The missing-rg diagnostic is a dependency-closure observation and does not establish defective PDF content.",
    "The C6 local-recorder contradiction follows from exact source and blob sizes; it does not invent a detailed runtime trace.",
    "C6 hosted observations and r11 do not transfer qualification or replay credit to C7.",
    "Git and SHA-256 identities bind named bytes and topology only; they do not establish authorship, authenticity, provider completeness, trusted time, independent reproduction, or durability.",
]
R7_POLICY_ROWS = [
    {
        "mode": "100644",
        "path": CURRENT_SOURCE_RELATIVE,
        "role": "self_excluding_source_state",
        "status": "M",
    },
    {
        "mode": "100644",
        "path": LOCAL_RECORD_RELATIVE,
        "role": "durable_local_l7_closure",
        "status": "A",
    },
    {
        "mode": "100644",
        "path": RECEIPT_RELATIVE,
        "role": "derived_v7_receipt",
        "status": "A",
    },
    {
        "mode": "100644",
        "path": SUCCESSOR_CAPTURE_RELATIVE,
        "role": "fresh_successor_hosted_capture",
        "status": "A",
    },
]
# The final C7 path inventory is frozen before the one-shot r12 replay.  The
# C7 tree remains derived from the eventual commit, so no tree identity enters
# these source bytes.
FROZEN_C7_POLICY_ROWS: tuple[tuple[str, str, str, str], ...] = (
    (CI_RELATIVE, "M", "100644", "repository_ci_dependency_repair"),
    (V6_WORKFLOW_RELATIVE, "M", "100644", "retired_v6_no_credit_workflow"),
    (V7_WORKFLOW_RELATIVE, "A", "100644", "dedicated_v7_hosted_gate"),
    ("AGENTS.md", "M", "100644", "operational_and_scientific_object_guide"),
    ("CHANGELOG.md", "M", "100644", "append_only_change_record"),
    ("audit/evidence/completion-active-resume.md", "M", "100644", "current_replay_pointer"),
    (CURRENT_SOURCE_RELATIVE, "M", "100644", "self_excluding_source_state"),
    (PREDECESSOR_CAPTURE_RELATIVE, "A", "100644", "predecessor_failure_hosted_capture"),
    (COUNTEREXAMPLE_RELATIVE, "A", "100644", "c6_local_bound_counterexample"),
    (BOUNDARY_RELATIVE, "A", "100644", "operational_boundary_record"),
    (
        "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-visual-receipt-2026-08-18.md",
        "A",
        "100644",
        "operational_boundary_visual_receipt",
    ),
    (POLICY_RELATIVE, "A", "100644", "c7_r7_path_policy"),
    (R12_RELATIVE, "A", "100644", "current_lean_replay_receipt"),
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
        "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf",
        "A",
        "100644",
        "operational_boundary_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.svg",
        "A",
        "100644",
        "operational_boundary_vector_source",
    ),
    (
        "audit/formal/latex/ksg-m1a-composite-v7-boundary.tex",
        "A",
        "100644",
        "operational_boundary_latex_source",
    ),
    (CAPTURE_SCHEMA_RELATIVE, "A", "100644", "dual_phase_hosted_capture_schema"),
    (
        COUNTEREXAMPLE_SCHEMA_RELATIVE,
        "A",
        "100644",
        "c6_local_bound_counterexample_schema",
    ),
    (LOCAL_SCHEMA_RELATIVE, "A", "100644", "local_l7_closure_schema"),
    (RECEIPT_SCHEMA_RELATIVE, "A", "100644", "dual_capture_typed_receipt_schema"),
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
    (
        "output/pdf/ksg-m1a-composite-v7-boundary.pdf",
        "A",
        "100644",
        "operational_boundary_publication_pdf",
    ),
    (
        "output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv",
        "A",
        "100644",
        "operational_boundary_rendering_receipt",
    ),
    ("scripts/README.md", "M", "100644", "script_process_guide"),
    (LOCAL_TOOL_RELATIVE, "A", "100644", "bounded_local_l7_closure_capture_tool"),
    (CAPTURE_TOOL_RELATIVE, "A", "100644", "bounded_dual_phase_hosted_capture_tool"),
    (
        "scripts/check-certified-sxpid2-claim-self-test.py",
        "M",
        "100644",
        "certified_sxpid2_claim_hostile_suite",
    ),
    (
        "scripts/check-certified-sxpid2-claim.py",
        "M",
        "100644",
        "certified_sxpid2_claim_gate",
    ),
    (
        "scripts/check-formal-pdf-set.sh",
        "M",
        "100755",
        "formal_pdf_inventory_and_versioned_adjudication_gate",
    ),
    ("scripts/check-formal-pdf-style.py", "M", "100755", "formal_pdf_style_gate"),
    (
        "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh",
        "A",
        "100755",
        "operational_boundary_pdf_gate_self_test",
    ),
    (
        "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh",
        "A",
        "100755",
        "operational_boundary_pdf_gate",
    ),
    (SELF_TEST_RELATIVE, "A", "100644", "composite_v7_hostile_suite"),
    (CHECKER_RELATIVE, "A", "100644", "composite_v7_semantic_gate"),
    (
        "scripts/check-lean-toolchain-freeze-self-test.py",
        "M",
        "100644",
        "lean_replay_hostile_suite",
    ),
    ("scripts/check-lean-toolchain-freeze.py", "M", "100644", "lean_replay_gate"),
    ("scripts/generate-lean-4.33-replay.py", "M", "100644", "lean_replay_generator"),
)
# One reviewed acyclic cut.  This remains the unique zero expression until all
# non-cut C7 and Lean bytes settle and H_L is computed from the three-cut-
# normalized Lean checker source.
EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "27174d31a76b25af9473c0d3e6bc0bd5095cf786c51848b7931bc28eaccb74ab"
# Final acyclic source/artifact bindings are populated after their reviewed bytes
# settle.  Self-referential C7 current-source/r12/tree fields are derived instead.
FROZEN_C7_PATH_BINDINGS: dict[str, tuple[str, int, str]] = {
    ".github/workflows/ci.yml": (
        "cc046f60af6880a046272bf768151e3824aa0a9e22d03a6fe5a5f6bd433b19b7",
        69_067,
        "100644",
    ),
    ".github/workflows/ksg-m1a-composite-v6.yml": (
        "0717fa37b2b40e5325ed2e436fd3d4f9a83475a136c7d0f41e3cfa0316d13c16",
        1_585,
        "100644",
    ),
    ".github/workflows/ksg-m1a-composite-v7.yml": (
        "b6c8fb9a9ada3fc78fa909cf69f52fc823b15e285e17047498e6a981ac8724ce",
        6_760,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-hosted-capture-v7-2026-08-18.json": (
        "e9a1d574cb4127263d8aaec3e291e78836b849f9b402af8a0daa5eb37cc70104",
        1_819_338,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-v6-local-closure-counterexample-v7-2026-08-18.json": (
        "cabcd565f25e11d14c4082532ea7efe1987eb0d700c115a8fbf36937486eede2",
        9_103,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md": (
        "c666f0ffff37d45eb1d78830d2fcc766a6fdb63d327afee1ed6dec6c69ba7642",
        9_466,
        "100644",
    ),
    "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-visual-receipt-2026-08-18.md": (
        "0ec8104d6f71dac55025c09e59dab3665ca50204b71a05aab9db1a98ac5b5afe",
        3_513,
        "100644",
    ),
    "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf": (
        "545a1e278038fa0bc82809dbf1bf5407fba6ca0fe032839b69477a1064e96482",
        73_959,
        "100644",
    ),
    "audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.svg": (
        "bf5b4a2bacbf6f7e34a354dafa27610fcdd80ca7ab6e6ee81d6b07261ab64a28",
        10_983,
        "100644",
    ),
    "audit/formal/latex/ksg-m1a-composite-v7-boundary.tex": (
        "8bb1461d5fc5e7fd883d040b0865a47276e060696176b0c1b4ae8e9c797e5b8b",
        16_188,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v7.schema.json": (
        "401dae966fe4e61ab81a660af9aef56992b44271c3bdf9198349a4fe2d45a103",
        8_965,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-counterexample-v7.schema.json": (
        "d06f0437cd5eddce35a88be9eccd5653ddc36b29b361ff924c33578d15a4de7b",
        21_621,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v7.schema.json": (
        "7da6e51680f3aef6d41cc24196eea6ec4f11385f02a62762cec7e6617f7dd99b",
        9_947,
        "100644",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v7.schema.json": (
        "a4f2f991864322e727549d527180e4937528d4f2f94408031cddb82ac9819c44",
        12_533,
        "100644",
    ),
    "justfile": (
        "9397e036e5eafcdd9d0662002fff4ff0486856a474c3d04ff4db3c94b4b90116",
        36_074,
        "100644",
    ),
    "output/pdf/ksg-m1a-composite-v7-boundary.pdf": (
        "2b05eb2e9d1e694d2f2f04b2bed3acf9b7f1c2eb1ac6672c48757ef9d067d33f",
        1_049_198,
        "100644",
    ),
    "output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv": (
        "f7be03f0cd1c89e046225b7743e0334f189c3216ead4d74ab309cf0243b9816e",
        1_275,
        "100644",
    ),
    "scripts/capture-ksg-m1a-composite-v7-local-closure.py": (
        "5268322d756e546f29ed9d2ded58264800808570be286adfba562f7decb284c1",
        35_401,
        "100644",
    ),
    "scripts/capture-ksg-m1a-composite-v7.py": (
        "2139176d51809853e98c558ec792eff61f0631ed027d04cc1a9d6d8f8ac1f06c",
        21_883,
        "100644",
    ),
    "scripts/check-formal-pdf-set.sh": (
        "95e6843d2c0346bda5d5c793cd07ca08f6a562544719a4041738f1f536eed76c",
        3_433,
        "100755",
    ),
    "scripts/check-formal-pdf-style.py": (
        "6a8290e88efe5728de70be97f2d2ac8520e8e5ba348faa5798d1c218bdb72d9e",
        9_018,
        "100755",
    ),
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh": (
        "a88b769182dd0f28078354ce170a8c69881eabbe8213d82b1c2951267fdbdcb2",
        23_137,
        "100755",
    ),
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh": (
        "cb38f112bf25b807c6688742f22dcc253eef7235f14830e8220b83603c7c2526",
        111_043,
        "100755",
    ),
    "scripts/check-ksg-m1a-composite-v7-self-test.py": (
        "da29201919922914e138b766a8c7e911d1227c6b21785d0efd41c46a5559bb63",
        58_800,
        "100644",
    ),
}
RESERVED_REPLAY_PATHS = [R12_RELATIVE]

IMMUTABLE_C6_AUTHORITIES = {
    R11_RELATIVE: (R11_SHA256, R11_SIZE_BYTES),
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v6.schema.json": (
        "5d075f383729818a7e15f321058dc973416492c3fabbc152f8b6e584ec001df6",
        14_163,
    ),
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json": (
        "4ab719785b6f89ce63d1061813a31e17289fa94cf4300aab00946de2c045f3fd",
        13_620,
    ),
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v6.schema.json": (
        "65504b10c0fff4e2f287a0271364553d89cf6a6dfef7c6418ab8780e7e28f00f",
        20_482,
    ),
    "scripts/capture-ksg-m1a-composite-v6.py": (
        "8089cce79cd9ff14e9eda1b46c51a746b508b026f2cbf5a83cb295e7860d7efa",
        41_770,
    ),
    "scripts/capture-ksg-m1a-composite-v6-local-closure.py": (
        "5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a",
        57_021,
    ),
    V6_CHECKER_RELATIVE: (V6_CHECKER_SHA256, V6_CHECKER_SIZE_BYTES),
    "scripts/check-ksg-m1a-composite-v6-self-test.py": (
        "3430e7c0e083fd444de4649d432051a9fa54659d974b6d4384337857d79b7265",
        69_573,
    ),
    "scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh": (
        "087d3fa3ac9467d63423fc2a246216cfcd61e176ceceae3eb9dff7428b141b35",
        95_273,
    ),
    "scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh": (
        "c2a42bebb2f33f2e3e1d34ddce1abc0b8c2c554524e4ea7881c13ff489bc6625",
        17_071,
    ),
    "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh": (
        "d4f6416ef9aee5f158e9ab5b5f7909d75e45ccc9e49d77405e92fa0db59431af",
        39_346,
    ),
    "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh": (
        "170d596cd2f179a984d59a652660e1d283508af4c7b6673c444a8061f38574e5",
        3_851,
    ),
}
IMMUTABLE_C6_EXECUTABLES = frozenset(
    {
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh",
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh",
        "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh",
        "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh",
    }
)

C6_RECEIPT_AUTHORITY_ROLES = {
    CI_RELATIVE: "published_c6_ci_workflow",
    R11_RELATIVE: "finalized_c6_era_predecessor_replay",
    V6_WORKFLOW_RELATIVE: "published_c6_v6_workflow",
    V6_CHECKER_RELATIVE: "immutable_v6_checker_primitives",
    "scripts/check-ksg-m1a-composite-v6-self-test.py": "immutable_v6_hostile_suite",
    "scripts/capture-ksg-m1a-composite-v6.py": "immutable_v6_hosted_capture_primitives",
    "scripts/capture-ksg-m1a-composite-v6-local-closure.py": "immutable_v6_local_capture_primitives",
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v6.schema.json": "immutable_v6_hosted_capture_schema",
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json": "immutable_v6_local_capture_schema",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v6.schema.json": "immutable_v6_receipt_schema",
}

R12_REQUIRED_OPERATIONAL_PATHS = (
    CI_RELATIVE,
    V6_WORKFLOW_RELATIVE,
    V7_WORKFLOW_RELATIVE,
    JUSTFILE_RELATIVE,
    CAPTURE_TOOL_RELATIVE,
    CAPTURE_SCHEMA_RELATIVE,
    LOCAL_TOOL_RELATIVE,
    LOCAL_SCHEMA_RELATIVE,
    RECEIPT_SCHEMA_RELATIVE,
    CHECKER_RELATIVE,
    SELF_TEST_RELATIVE,
    POLICY_RELATIVE,
    "scripts/check-formal-pdf-set.sh",
    "scripts/check-formal-pdf-style.py",
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh",
    "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh",
    "scripts/generate-lean-4.33-replay.py",
    "scripts/check-current-source-state-v1.py",
    "scripts/check-current-source-state-v1-self-test.py",
)

C6_LOCAL_AUTHORITIES = (
    (
        "audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json",
        "local_l6_closure_schema",
        "4ab719785b6f89ce63d1061813a31e17289fa94cf4300aab00946de2c045f3fd",
        13_620,
    ),
    (
        JUSTFILE_RELATIVE,
        "local_command_wiring",
        "7654a4ea10c71dced82ce492717a55568f91fbe9d09471aa3e306d830907873c",
        32_358,
    ),
    (
        "scripts/capture-ksg-m1a-composite-v6-local-closure.py",
        "bounded_local_l6_closure_capture_tool",
        "5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a",
        57_021,
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-self-test.py",
        "composite_v6_hostile_suite",
        "3430e7c0e083fd444de4649d432051a9fa54659d974b6d4384337857d79b7265",
        69_573,
    ),
    (
        V6_CHECKER_RELATIVE,
        "composite_v6_semantic_gate",
        V6_CHECKER_SHA256,
        V6_CHECKER_SIZE_BYTES,
    ),
)

COUNTEREXAMPLE_ANCHORS = (
    ("identity_and_bounds", 49, 64, 733, "3752fb310e0eb758ee4f994ee56d6e1ac26644b42e159d5152e2c51d62e3bda7"),
    ("authority_roles", 136, 142, 285, "7b417702cb0274e6f4740b7495b6776a7300ee1888645b2a3067484981488af2"),
    ("local_regular_file_bound", 190, 203, 564, "c9cb0e38b4926b98be6cd39af69d08f7943cff2a4a483ad6f7af48d8d36e45fe"),
    ("stream_overflow_guard", 442, 448, 339, "6a65cb6283ac87333d1e602ce8d7f5a31af283c1c8ababdd9ab50b8a2bb3b12d"),
    ("committed_read_call_chain", 459, 487, 801, "17e07e69d7a0ca8242c50f704a6749f0d564c778ec1b73e40b7767281787bb05"),
    ("authority_descriptor_route", 757, 773, 662, "470826af1cef617e1e4f0545be38e3460e1a6a50529b49a36429fa26f66401fb"),
    ("capture_execution_order", 1456, 1465, 478, "7906370b0d74dcceb939ff9ccc8b33a10659897d39b1f2713312ede1f5e4ab2f"),
)
COUNTEREXAMPLE_NONIMPLICATIONS = [
    "This static counterexample is not an invocation record and does not claim a runtime, host, environment, operator, wall-clock time, monotonic interval, authentication event, or first-attempt chronology.",
    "It does not claim that any C6 local closure command, checker, self-test, formal proof, PDF gate, or hosted workflow was reached by a local invocation.",
    "It diagnoses only the immutable C6 local recorder's committed-authority transport bound; it does not establish a defect in the bound authority files, KSG, PID, formal proofs, PDFs, or scientific results.",
    "It does not authenticate Git objects, an operating-system execution, toolchain bytes, or an off-host observation; the stated object identities are repository content bindings.",
    "It does not authorize mutation of C6 bytes or history, retroactive issuance of a C6 local record, or transfer of evidence between revisions.",
    "It does not establish that a C7 successor repair, local record, hosted run, receipt, or publication passes; each requires separate evidence.",
]
LOCAL_AUTHORITY_ROLES = {
    JUSTFILE_RELATIVE: "local_command_wiring",
    LOCAL_SCHEMA_RELATIVE: "local_l7_closure_schema",
    LOCAL_TOOL_RELATIVE: "bounded_local_l7_closure_capture_tool",
    SELF_TEST_RELATIVE: "composite_v7_hostile_suite",
    CHECKER_RELATIVE: "composite_v7_semantic_gate",
    "scripts/check-ksg-m1a-composite-v6-self-test.py": "retained_v6_oversize_hostile_suite_authority",
    V6_CHECKER_RELATIVE: "retained_v6_oversize_semantic_gate_authority",
}
LOCAL_TOOL_SPECS = {
    "bash": ("--version",),
    "chktex": ("--version",),
    "fc-match": ("--version",),
    "git": ("--version",),
    "just": ("--version",),
    "lacheck": ("--version",),
    "latexmk": ("--version",),
    "lualatex": ("--version",),
    "pdfinfo": ("-v",),
    "pdffonts": ("-v",),
    "pdftocairo": ("-v",),
    "pdftotext": ("-v",),
    "python3": ("--version",),
    "rg": ("--version",),
    "rsvg-convert": ("--version",),
    "xmllint": ("--version",),
}
LOCAL_LIMITS = {
    "authority_stream_bytes": 2_097_152,
    "command_stream_bytes": 8_388_608,
    "executable_bytes": 268_435_456,
    "record_bytes": 33_554_432,
    "version_stream_bytes": 65_536,
}
LOCAL_NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C7 checkout and is neither independent replication nor first-attempt authority.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, builtins, libraries, TeX helpers, or transitive processes.",
    "The separate authority-stream bound fixes one exact C6 contradiction; it is not a generic executable-closure or hermeticity theorem.",
    "The redacted environment-route digest is an opaque correlated fingerprint, not a publicly recomputable path authority.",
    "HOME is absent; isolated XDG and TeX roots do not prove absence of every passwd-derived fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove every descendant was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove output contains no sensitive information.",
    "Ordinary Git status plus selected metadata checks exclude ignored products and uninspected Git metadata, so this is not hermetic closure.",
    "A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
]

# This editing-scope guard is distinct from the already frozen final C7 delta.
# It remains available only for the bounded pre-commit assembly sequence; the
# eventual C7 tree identity is derived from the commit rather than embedded.
DRAFT_ALLOWED_PATHS = frozenset(
    {
        CI_RELATIVE,
        V6_WORKFLOW_RELATIVE,
        V7_WORKFLOW_RELATIVE,
        "AGENTS.md",
        "CHANGELOG.md",
        "audit/evidence/completion-active-resume.md",
        "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
        "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
        "audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/evidence-matrix.md",
        "claims/SX-COUNT-ATOM-BRIDGE-001/revision-index.md",
        JUSTFILE_RELATIVE,
        CURRENT_SOURCE_RELATIVE,
        "scripts/README.md",
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-certified-sxpid2-claim-self-test.py",
        "scripts/check-formal-pdf-set.sh",
        "scripts/check-formal-pdf-style.py",
        "scripts/check-lean-toolchain-freeze.py",
        "scripts/check-lean-toolchain-freeze-self-test.py",
        "scripts/generate-lean-4.33-replay.py",
        BOUNDARY_RELATIVE,
        POLICY_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_TOOL_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
        COUNTEREXAMPLE_RELATIVE,
        COUNTEREXAMPLE_SCHEMA_RELATIVE,
        PREDECESSOR_CAPTURE_RELATIVE,
        R12_RELATIVE,
        *PUBLICATION_PATHS,
    }
)

REQUIRED_CORE_DRAFT_PATHS = frozenset(
    {
        CI_RELATIVE,
        V6_WORKFLOW_RELATIVE,
        V7_WORKFLOW_RELATIVE,
        JUSTFILE_RELATIVE,
        BOUNDARY_RELATIVE,
        POLICY_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_TOOL_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
        COUNTEREXAMPLE_RELATIVE,
        COUNTEREXAMPLE_SCHEMA_RELATIVE,
    }
)

MAX_FILE_BYTES = 8 * 1024 * 1024
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class BootstrapError(RuntimeError):
    pass


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v6() -> bytes:
    before = V6_CHECKER_PATH.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not V6_CHECKER_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V6_CHECKER_SIZE_BYTES,
        "immutable v6 checker metadata changed",
    )
    descriptor = os.open(V6_CHECKER_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        bootstrap_require(
            (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink, opened.st_size)
            == (before.st_dev, before.st_ino, before.st_mode, before.st_nlink, before.st_size),
            "immutable v6 checker opened identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "immutable v6 checker short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(os.read(descriptor, 1) == b"", "immutable v6 checker grew")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = V6_CHECKER_PATH.lstat()
    for field in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns"):
        bootstrap_require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "immutable v6 checker changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(hashlib.sha256(raw).hexdigest() == V6_CHECKER_SHA256, "immutable v6 checker digest changed")
    return raw


def load_bound_v6(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_immutable_composite_v6_primitives_for_v7")
    module.__file__ = os.fspath(V6_CHECKER_PATH)
    module.__package__ = ""
    sys.modules[module.__name__] = module
    code = compile(raw, os.fspath(V6_CHECKER_PATH), "exec", dont_inherit=True, optimize=sys.flags.optimize)
    exec(code, module.__dict__)
    return module


try:
    V6_RAW = read_bound_v6()
    V6 = load_bound_v6(V6_RAW)
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected immutable-v6 checker load failure", file=sys.stderr)
    raise SystemExit(2) from None


ContractError = V6.ContractError
require = V6.require
canonical_json = V6.canonical_json
parse_json = V6.parse_json
validate_schema_instance = V6.validate_schema_instance
sha256 = V6.sha256
git = V6.git
parse_commit = V6.parse_commit
parse_tree = V6.parse_tree
tree_blob = V6.tree_blob
changed_entries = V6.changed_entries
exact_keys = V6.exact_keys
exact_int = V6.exact_int
project_digest = V6.project_digest
single_json_response = V6.single_json_response
paged_json_response = V6.paged_json_response
normalized_artifacts = V6.normalized_artifacts_v5
normalized_analyses = V6.normalized_analyses_v5
normalized_alerts = V6.normalized_alerts_v5
validate_postcommit_artifact = V6.validate_postcommit_artifact
member_bytes = V6.member_bytes
parse_utc_timestamp = V6.parse_utc_timestamp
CaptureRows = V6.CaptureRows

C6_RECEIPT_AUTHORITY_ROLES.update(
    {
        path: f"published_c6_{role}"
        for path, _mode, role in V6.PROCESS_ARTIFACTS
    }
)


def read_file(relative: str, maximum: int = MAX_FILE_BYTES, mode: int | None = None) -> bytes:
    path = ROOT / relative
    metadata = path.lstat()
    require(
        stat.S_ISREG(metadata.st_mode)
        and not path.is_symlink()
        and metadata.st_nlink == 1
        and 0 < metadata.st_size <= maximum,
        f"required bounded regular file changed: {relative}",
    )
    if mode is not None:
        require(stat.S_IMODE(metadata.st_mode) == mode, f"required file mode changed: {relative}")
    raw = path.read_bytes()
    after = path.lstat()
    require(
        len(raw) == metadata.st_size
        and (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_nlink, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)
        == (after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
        f"required file changed while read: {relative}",
    )
    return raw


def exact_file(relative: str, expected_sha256: str, expected_size: int) -> bytes:
    raw = read_file(relative)
    require(
        len(raw) == expected_size and sha256(raw) == expected_sha256,
        f"exact file binding changed: {relative}",
    )
    return raw


def c6_anchor() -> tuple[Any, dict[str, Any]]:
    commit = parse_commit(C6_COMMIT)
    require(
        commit.tree == C6_TREE
        and commit.parent == C6_PARENT
        and commit.message == C6_MESSAGE
        and (commit.author, commit.committer) == C6_IDENTITY,
        "published C6 exact commit envelope changed",
    )
    entries = parse_tree(C6_TREE)
    for relative, (digest, size) in IMMUTABLE_C6_AUTHORITIES.items():
        raw = tree_blob(entries, relative)
        expected_mode = "100755" if relative in IMMUTABLE_C6_EXECUTABLES else "100644"
        require(
            entries[relative].mode == expected_mode and len(raw) == size and sha256(raw) == digest,
            f"published C6 immutable authority changed: {relative}",
        )
    return commit, entries


def step_block(raw: bytes, name: bytes) -> bytes:
    marker = b"      - name: " + name + b"\n"
    require(raw.count(marker) == 1, f"workflow step identity changed: {name.decode('utf-8')}")
    start = raw.index(marker)
    candidates = [
        position
        for prefix in (b"      - name: ", b"      - uses: ")
        if (position := raw.find(prefix, start + len(marker))) >= 0
    ]
    end = min(candidates) if candidates else len(raw)
    return raw[start:end]


RG_PROBE = (
    b"          /usr/bin/test -x /usr/bin/rg\n"
    b"          test \"$(command -v rg)\" = \"/usr/bin/rg\"\n"
    b"          /usr/bin/rg --version >/dev/null\n"
)

JUST_V7_PUBLICATION_PENDING = (
    b"    # C7_PUBLICATION_LANE_PENDING: the v7 PDF gate and hostile suite are inserted here\n"
    b"    # only after their separately owned, complete publication family is reviewed.\n"
)
JUST_V7_PUBLICATION_FINAL = (
    b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact\n"
    b"    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact\n"
)
JUST_V7_RECIPE_DRAFT = b"""ksg-composite-v7:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v7.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    command -v rg >/dev/null
    rg --version >/dev/null
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > "$result_root/local.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > "$result_root/local.optimized.json"
    cmp "$result_root/local.json" "$result_root/local.optimized.json"
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    # C7_PUBLICATION_LANE_PENDING: the v7 PDF gate and hostile suite are inserted here
    # only after their separately owned, complete publication family is reviewed.
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v7.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v7.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v7.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v7-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v7-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"
"""
JUST_V7_RECIPE_FINAL = JUST_V7_RECIPE_DRAFT.replace(
    JUST_V7_PUBLICATION_PENDING, JUST_V7_PUBLICATION_FINAL
)


def validate_rg_dependency(workflow_raw: bytes, lane: str) -> None:
    require(b"\r" not in workflow_raw, f"{lane} workflow line endings changed")
    if lane == "ci":
        install_name = b"Install the runner TeX toolchain"
        probe_specs = (
            (
                b"Rebuild papers and check cross-toolchain text, geometry, fonts, and workflow renders",
                (b"bash --noprofile --norc scripts/check-formal-pdf-set.sh --cross-toolchain",),
            ),
        )
    else:
        require(lane == "v7", "unknown ripgrep dependency lane")
        install_name = b"Install the complete reviewed PDF command set"
        probe_specs = (
            (b"Recheck retained C6 operational surfaces", ()),
            (
                b"Recheck the unchanged v6 publications after dependency closure",
                (
                    b"scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --cross-toolchain",
                    b"scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --cross-toolchain",
                    b"scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --cross-toolchain",
                    b"scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --cross-toolchain",
                ),
            ),
            (
                b"Validate the composite-v7 publication family and hostile suite",
                (
                    b"scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --cross-toolchain",
                    b"scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --cross-toolchain",
                ),
            ),
        )
    install = step_block(workflow_raw, install_name)
    require(
        install.count(b"            ripgrep \\\n") == 1
        and all(
            b"ripgrep" not in line.lstrip()[1:]
            for line in install.splitlines()
            if line.lstrip().startswith(b"#")
        ),
        f"{lane} ripgrep package dependency is absent, moved, or commented",
    )
    for probe_name, required_after in probe_specs:
        block = step_block(workflow_raw, probe_name)
        require(block.count(RG_PROBE) == 1, f"{lane} exact /usr/bin/rg runtime probe changed")
        probe_end = block.index(RG_PROBE) + len(RG_PROBE)
        for command in required_after:
            require(
                workflow_raw.count(command) == 1
                and block.count(command) == 1
                and block.index(command) >= probe_end,
                f"{lane} required PDF gate is absent, moved, duplicated, or bypasses the /usr/bin/rg probe",
            )
    require(
        b"/usr/bin/test -x /usr/bin/rg" in workflow_raw
        and b'test "$(command -v rg)" = "/usr/bin/rg"' in workflow_raw
        and b"/usr/bin/rg --version" in workflow_raw,
        f"{lane} causal ripgrep executable binding changed",
    )


def certified_job_digest(workflow_raw: bytes) -> str:
    lines = workflow_raw.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line == b"  certified-sxpid-reference:\n"]
    require(len(starts) == 1, "certified-sxpid-reference CI job is not unique")
    start = starts[0]
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if re.fullmatch(rb"  [A-Za-z0-9_-]+:\n", lines[index]) is not None
        ),
        len(lines),
    )
    return sha256(b"".join(lines[start:end]))


def validate_workflows(ci_raw: bytes, v7_raw: bytes, retired_v6_raw: bytes) -> None:
    require(
        len(ci_raw) == CI_SIZE_BYTES
        and sha256(ci_raw) == CI_SHA256
        and len(retired_v6_raw) == RETIRED_V6_WORKFLOW_SIZE_BYTES
        and sha256(retired_v6_raw) == RETIRED_V6_WORKFLOW_SHA256
        and len(v7_raw) == V7_WORKFLOW_SIZE_BYTES
        and sha256(v7_raw) == V7_WORKFLOW_SHA256,
        "C7 CI, retired-v6, or successor-v7 workflow exact bytes changed",
    )
    validate_rg_dependency(ci_raw, "ci")
    validate_rg_dependency(v7_raw, "v7")
    require(
        certified_job_digest(ci_raw)
        == "6c173cbf90fe27bbd43342f37ebe0378db76a1e4e8e22a92aa4d5416f9789bda",
        "certified-sxpid-reference CI job-section digest changed",
    )
    require(
        retired_v6_raw.count(b"workflow_dispatch:") == 1
        and b"  push:" not in retired_v6_raw
        and b"R6 is permanently unissued" in retired_v6_raw
        and b"missing command: rg" in retired_v6_raw
        and b"65536" in retired_v6_raw
        and b"exit 1" in retired_v6_raw,
        "retired v6 workflow no-credit disposition changed",
    )
    required_v6_gate_lines = (
        b"scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --cross-toolchain",
        b"scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --cross-toolchain",
        b"scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --cross-toolchain",
        b"scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --cross-toolchain",
    )
    require(
        all(v7_raw.count(line) == 1 for line in required_v6_gate_lines),
        "v7 workflow changed a retained v6 shell-gate invocation",
    )
    retained_publication = step_block(
        v7_raw, b"Recheck the unchanged v6 publications after dependency closure"
    )
    v7_publication = step_block(
        v7_raw, b"Validate the composite-v7 publication family and hostile suite"
    )
    replay = step_block(v7_raw, b"Validate fresh replay and current-source custody")
    static = step_block(v7_raw, b"Validate static v7 contract in normal and optimized modes")
    require(
        v7_raw.index(retained_publication)
        < v7_raw.index(v7_publication)
        < v7_raw.index(replay)
        < v7_raw.index(static),
        "v7 publication/replay/static workflow step order changed",
    )
    require(
        v7_raw.count(b"C7_PUBLICATION_LANE_PENDING") == 0,
        "v7 workflow publication lane remains unresolved",
    )


def just_recipe(raw: bytes, name: bytes) -> bytes:
    require(b"\r" not in raw, "justfile line endings changed")
    lines = raw.splitlines(keepends=True)
    header = name + b":\n"
    starts = [index for index, line in enumerate(lines) if line == header]
    require(len(starts) == 1, f"just recipe identity changed: {name.decode('ascii')}")
    start = starts[0]
    ends = [index for index in range(start + 1, len(lines)) if lines[index] == b"\n"]
    require(ends != [], f"just recipe terminator changed: {name.decode('ascii')}")
    return b"".join(lines[start : ends[0]])


def validate_justfile_values(raw: bytes, require_publication: bool) -> None:
    require(
        len(raw) == JUSTFILE_SIZE_BYTES and sha256(raw) == JUSTFILE_SHA256,
        "C7 justfile exact bytes changed",
    )
    recipe = just_recipe(raw, b"ksg-composite-v7")
    allowed = {JUST_V7_RECIPE_FINAL} if require_publication else {
        JUST_V7_RECIPE_DRAFT,
        JUST_V7_RECIPE_FINAL,
    }
    require(recipe in allowed, "local composite-v7 recipe commands or order changed")
    require(
        recipe.count(b"capture-ksg-m1a-composite-v7-local-closure.py") == 2
        and b"capture-ksg-m1a-composite-v7-local-closure.py --output" not in recipe,
        "local composite-v7 recipe recursively invokes real local capture mode",
    )
    release_lines = [line for line in raw.splitlines() if line.startswith(b"release-audit:")]
    require(
        len(release_lines) == 1
        and b" ksg-composite-v7 " in release_lines[0]
        and b"ksg-composite-v6" not in release_lines[0],
        "release audit does not select the local composite-v7 command exclusively",
    )


def assigned_expression(module: ast.Module, name: str) -> ast.expr:
    matches = [
        node.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    ]
    require(len(matches) == 1, f"local recorder assignment changed: {name}")
    return matches[0]


def assigned_integer(module: ast.Module, name: str) -> int:
    expression = assigned_expression(module, name)

    def evaluate(expression: ast.expr) -> int:
        if isinstance(expression, ast.Constant) and type(expression.value) is int:
            return int(expression.value)
        require(
            isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Mult),
            f"local recorder bound expression changed: {name}",
        )
        return evaluate(expression.left) * evaluate(expression.right)

    return evaluate(expression)


def function_node(module: ast.Module, name: str) -> ast.FunctionDef:
    matches = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(matches) == 1, f"local recorder function changed: {name}")
    return matches[0]


def calls_name(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == name
    ]


def validate_local_repair_source(raw: bytes) -> None:
    require(
        len(raw) == LOCAL_TOOL_SIZE_BYTES and sha256(raw) == LOCAL_TOOL_SHA256,
        "v7 local-recorder exact source bytes changed",
    )
    validate_local_repair_semantics(raw)


def validate_local_repair_semantics(raw: bytes) -> None:
    require(raw.count(b"MAX_AUTHORITY_STREAM_BYTES = 2 * 1024 * 1024\n") == 1, "dedicated authority bound literal changed")
    require(
        len(re.findall(rb"(?<![0-9])2 \* 1024 \* 1024", raw)) == 1,
        "authority bound literal escaped its dedicated definition",
    )
    module = ast.parse(raw, filename=LOCAL_TOOL_RELATIVE)
    observed_limits = {
        "authority_stream_bytes": assigned_integer(module, "MAX_AUTHORITY_STREAM_BYTES"),
        "command_stream_bytes": assigned_integer(module, "MAX_COMMAND_STREAM_BYTES"),
        "executable_bytes": assigned_integer(module, "MAX_EXECUTABLE_BYTES"),
        "record_bytes": assigned_integer(module, "MAX_RECORD_BYTES"),
        "version_stream_bytes": assigned_integer(module, "MAX_VERSION_STREAM_BYTES"),
    }
    require(
        observed_limits == LOCAL_LIMITS
        and assigned_integer(module, "COMMAND_TIMEOUT_SECONDS") == 14_400,
        "v7 local recorder retained limits or timeout changed",
    )
    require(
        ast.literal_eval(assigned_expression(module, "COMMAND_ARGV"))
        == ("just", "ksg-composite-v7")
        and ast.literal_eval(assigned_expression(module, "NONIMPLICATIONS"))
        == LOCAL_NONIMPLICATIONS,
        "v7 local fixed command or nonimplications changed",
    )
    expected_literal_assignments = {
        "REPOSITORY": REPOSITORY,
        "C6_COMMIT": C6_COMMIT,
        "C7_MESSAGE": C7_MESSAGE,
        "V6_RELATIVE": V6_LOCAL_PRIMITIVE["path"],
        "V6_SHA256": V6_LOCAL_PRIMITIVE["sha256"],
        "V6_SIZE_BYTES": V6_LOCAL_PRIMITIVE["size_bytes"],
        "SCRIPT_RELATIVE": LOCAL_TOOL_RELATIVE,
        "SCHEMA_RELATIVE": LOCAL_SCHEMA_RELATIVE,
        "CHECKER_RELATIVE": CHECKER_RELATIVE,
        "SELF_TEST_RELATIVE": SELF_TEST_RELATIVE,
        "JUSTFILE_RELATIVE": JUSTFILE_RELATIVE,
        "V6_CHECKER_RELATIVE": V6_CHECKER_RELATIVE,
        "V6_SELF_TEST_RELATIVE": "scripts/check-ksg-m1a-composite-v6-self-test.py",
    }
    require(
        all(
            ast.literal_eval(assigned_expression(module, name)) == expected
            for name, expected in expected_literal_assignments.items()
        ),
        "v7 local subject, primitive, or authority-path literal changed",
    )
    path_names = {
        "JUSTFILE_RELATIVE": JUSTFILE_RELATIVE,
        "SCHEMA_RELATIVE": LOCAL_SCHEMA_RELATIVE,
        "SCRIPT_RELATIVE": LOCAL_TOOL_RELATIVE,
        "SELF_TEST_RELATIVE": SELF_TEST_RELATIVE,
        "CHECKER_RELATIVE": CHECKER_RELATIVE,
        "V6_SELF_TEST_RELATIVE": "scripts/check-ksg-m1a-composite-v6-self-test.py",
        "V6_CHECKER_RELATIVE": V6_CHECKER_RELATIVE,
    }
    authority_expression = assigned_expression(module, "AUTHORITY_ROLES")
    require(isinstance(authority_expression, ast.Dict), "local authority roster changed shape")
    observed_authorities: dict[str, str] = {}
    for key_node, value_node in zip(authority_expression.keys, authority_expression.values):
        require(
            isinstance(key_node, ast.Name)
            and key_node.id in path_names
            and isinstance(value_node, ast.Constant)
            and type(value_node.value) is str,
            "local authority roster contains a nonliteral route",
        )
        observed_authorities[path_names[key_node.id]] = value_node.value
    require(observed_authorities == LOCAL_AUTHORITY_ROLES, "local authority roster changed")

    limits_expression = assigned_expression(module, "LIMITS")
    require(isinstance(limits_expression, ast.Dict), "local LIMITS projection changed shape")
    limit_symbols = {
        "MAX_AUTHORITY_STREAM_BYTES": LOCAL_LIMITS["authority_stream_bytes"],
        "MAX_COMMAND_STREAM_BYTES": LOCAL_LIMITS["command_stream_bytes"],
        "MAX_EXECUTABLE_BYTES": LOCAL_LIMITS["executable_bytes"],
        "MAX_RECORD_BYTES": LOCAL_LIMITS["record_bytes"],
        "MAX_VERSION_STREAM_BYTES": LOCAL_LIMITS["version_stream_bytes"],
    }
    observed_projection: dict[str, int] = {}
    for key_node, value_node in zip(limits_expression.keys, limits_expression.values):
        require(
            isinstance(key_node, ast.Constant)
            and type(key_node.value) is str
            and isinstance(value_node, ast.Name)
            and value_node.id in limit_symbols,
            "local LIMITS projection contains a nonliteral route",
        )
        observed_projection[key_node.value] = limit_symbols[value_node.id]
    require(observed_projection == LOCAL_LIMITS, "local LIMITS projection changed")

    top_level_v6_writes: dict[str, ast.expr] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "V6":
            require(target.attr not in top_level_v6_writes, "duplicate immutable-v6 rebind")
            top_level_v6_writes[target.attr] = node.value
    require(
        set(top_level_v6_writes) == {"C5_COMMIT", "C6_MESSAGE", "TOOL_SPECS"}
        and isinstance(top_level_v6_writes["C5_COMMIT"], ast.Name)
        and top_level_v6_writes["C5_COMMIT"].id == "C6_COMMIT"
        and isinstance(top_level_v6_writes["C6_MESSAGE"], ast.Name)
        and top_level_v6_writes["C6_MESSAGE"].id == "C7_MESSAGE",
        "local immutable-v6 subject rebindings changed",
    )
    tool_rebind = top_level_v6_writes["TOOL_SPECS"]
    require(
        isinstance(tool_rebind, ast.BinOp)
        and isinstance(tool_rebind.op, ast.BitOr)
        and isinstance(tool_rebind.left, ast.Call)
        and isinstance(tool_rebind.left.func, ast.Name)
        and tool_rebind.left.func.id == "dict"
        and len(tool_rebind.left.args) == 1
        and isinstance(tool_rebind.left.args[0], ast.Attribute)
        and isinstance(tool_rebind.left.args[0].value, ast.Name)
        and tool_rebind.left.args[0].value.id == "V6"
        and tool_rebind.left.args[0].attr == "TOOL_SPECS"
        and ast.literal_eval(tool_rebind.right) == {"rg": ("--version",)},
        "local reviewed-executable extension changed",
    )
    retained_v6_tools = dict(V6.LOCAL_TOOL_SPECS)
    # V6's local recorder owns the exact tuple-valued predecessor roster.
    retained_v6_tools = {
        name: tuple(arguments[1:]) if arguments and arguments[0] == name else tuple(arguments)
        for name, arguments in retained_v6_tools.items()
    }
    require(
        (retained_v6_tools | {"rg": ("--version",)}) == LOCAL_TOOL_SPECS,
        "immutable-v6 reviewed-executable roster no longer yields the exact v7 roster",
    )
    all_v6_write_names = {
        target.attr
        for node in ast.walk(module)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "V6"
    }
    require(
        all_v6_write_names <= {"C5_COMMIT", "C6_MESSAGE", "TOOL_SPECS", "ROOT", "run_bounded"},
        "v7 local repair adds an unreviewed immutable-v6 module mutation",
    )
    require(
        raw.count(b'"schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v2"') == 1
        and raw.count(b'value["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v2"') == 1
        and raw.count(b'"schema_revision": 2') == 1
        and raw.count(b'value["schema_revision"] == 2') == 1,
        "v7 local schema identity or revision changed",
    )
    capture_function = function_node(module, "capture_under_fixed_umask")
    v6_calls = [
        item
        for item in ast.walk(capture_function)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Attribute)
        and isinstance(item.func.value, ast.Name)
        and item.func.value.id == "V6"
    ]
    call_names = [item.func.attr for item in v6_calls]
    require(
        call_names.count("reject_ambient_secrets") == 1
        and call_names.count("reject_sensitive_output") == 2
        and call_names.count("run_bounded") == 1,
        "v7 local secret/output/process control points changed",
    )
    command_calls = [item for item in v6_calls if item.func.attr == "run_bounded"]
    require(
        len(command_calls[0].args) == 6
        and isinstance(command_calls[0].args[4], ast.Name)
        and command_calls[0].args[4].id == "COMMAND_TIMEOUT_SECONDS"
        and isinstance(command_calls[0].args[5], ast.Name)
        and command_calls[0].args[5].id == "MAX_COMMAND_STREAM_BYTES",
        "v7 local command runner no longer uses the exact command timeout/stream class",
    )
    require(
        raw.count(b'require(not timed_out and code == 0, "local closure command did not complete successfully")') == 1,
        "v7 local command success/timeout gate changed",
    )
    authority_reader = function_node(module, "git_authority_output")
    calls = calls_name(authority_reader, "run_internal")
    require(
        len(calls) == 1
        and any(isinstance(argument, ast.Name) and argument.id == "MAX_AUTHORITY_STREAM_BYTES" for argument in calls[0].args),
        "dedicated Git authority reader lost its authority-only bound",
    )
    descriptors = function_node(module, "authority_descriptors")
    require(
        len(calls_name(descriptors, "git_authority_output")) == 1
        and len(calls_name(descriptors, "descriptor")) == 1,
        "authority descriptor route changed",
    )
    require(
        b"V6.git_output(" in raw and b"generic v6 Git output accepted a 65,537-byte authority" in raw,
        "generic-v6 oversize negative control is absent",
    )


def validate_capture_source(raw: bytes) -> None:
    require(
        len(raw) == CAPTURE_TOOL_SIZE_BYTES and sha256(raw) == CAPTURE_TOOL_SHA256,
        "v7 hosted-capture exact source bytes changed",
    )
    validate_capture_source_semantics(raw)


def validate_capture_source_semantics(raw: bytes) -> None:
    module = ast.parse(raw, filename=CAPTURE_TOOL_RELATIVE)
    expected_literals = {
        "REPOSITORY": REPOSITORY,
        "C6_COMMIT": C6_COMMIT,
        "C6_TREE": C6_TREE,
        "SCRIPT_RELATIVE": CAPTURE_TOOL_RELATIVE,
        "V6_RELATIVE": V6_CAPTURE_PRIMITIVE["path"],
        "V6_SHA256": V6_CAPTURE_PRIMITIVE["sha256"],
        "V6_SIZE_BYTES": V6_CAPTURE_PRIMITIVE["size_bytes"],
    }
    require(
        all(
            ast.literal_eval(assigned_expression(module, name)) == expected
            for name, expected in expected_literals.items()
        )
        and ast.literal_eval(assigned_expression(module, "NONIMPLICATIONS"))
        == CAPTURE_NONIMPLICATIONS,
        "v7 hosted-capture fixed identity or nonimplications changed",
    )
    expected_forbidden_tls = (
        "CURL_CA_BUNDLE",
        "OPENSSL_CONF",
        "PYTHONHTTPSVERIFY",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SSLKEYLOGFILE",
    )
    require(
        ast.literal_eval(assigned_expression(module, "FORBIDDEN_TLS_ENVIRONMENT"))
        == expected_forbidden_tls,
        "v7 hosted-capture forbidden TLS/key-log environment changed",
    )
    conclusions = ast.literal_eval(assigned_expression(module, "PREDECESSOR_CONCLUSIONS"))
    require(
        conclusions
        == {
            "predecessor_ci": "failure",
            "predecessor_codeql": "success",
            "predecessor_contract": "failure",
        },
        "v7 hosted-capture predecessor truth values changed",
    )
    predecessor_ci_run = ast.literal_eval(assigned_expression(module, "C6_CI_RUN"))
    require(predecessor_ci_run == C6_CI_RUN, "v7 hosted-capture predecessor CI run literal changed")
    run_expression = assigned_expression(module, "PREDECESSOR_RUNS")
    require(isinstance(run_expression, ast.Dict), "v7 predecessor run map changed shape")
    observed_runs: dict[str, int] = {}
    for key_node, value_node in zip(run_expression.keys, run_expression.values):
        require(isinstance(key_node, ast.Constant) and type(key_node.value) is str, "v7 predecessor run key changed")
        value = (
            predecessor_ci_run
            if isinstance(value_node, ast.Name) and value_node.id == "C6_CI_RUN"
            else ast.literal_eval(value_node)
        )
        observed_runs[key_node.value] = value
    require(
        observed_runs
        == {
            "predecessor_ci": C6_CI_RUN,
            "predecessor_codeql": C6_CODEQL_RUN,
            "predecessor_contract": C6_CONTRACT_RUN,
        },
        "v7 hosted-capture predecessor run map changed",
    )
    function_hashes = {
        "workflow_identity": "2f0197545c52b775dedaea9387db03e81d5a1bd37f8ee03ec5192e9965a6c5c6",
        "expected_successor_artifact_names": "53f4b4434798b79158cdc02def05196f449300cab3611cedbb252bbd65c94bac",
    }
    for name, expected in function_hashes.items():
        node = function_node(module, name)
        projected = ast.dump(node, annotate_fields=True, include_attributes=False).encode("utf-8")
        require(sha256(projected) == expected, f"v7 hosted-capture {name} route changed")
    top_level_writes: dict[str, ast.expr] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "V6":
            require(target.attr not in top_level_writes, "duplicate hosted immutable-v6 rebind")
            top_level_writes[target.attr] = node.value
    require(
        set(top_level_writes) == {"workflow_identity", "expected_successor_artifact_names"}
        and all(
            isinstance(top_level_writes[name], ast.Name)
            and top_level_writes[name].id == name
            for name in top_level_writes
        ),
        "v7 hosted capture adds or changes an immutable-v6 transport rebind",
    )
    all_writes = {
        target.attr
        for node in ast.walk(module)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "V6"
    }
    require(all_writes == set(top_level_writes), "v7 hosted capture mutates another immutable-v6 global")
    require(
        raw.count(b'"schema": "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v7"') == 1
        and raw.count(b'"schema_revision": 7') == 1,
        "v7 hosted-capture schema identity changed",
    )
    require(
        raw.count(b"for repetition in (1, 2):") == 1
        and raw.count(b"len(captures) <= V6.MAX_CAPTURE_ROWS") == 1
        and raw.count(b'sum(row["body_size_bytes"] for row in captures) <= V6.MAX_CAPTURE_BODY_BYTES') == 1
        and raw.count(b"len(rendered) <= V6.MAX_CAPTURE_BYTES") == 1,
        "v7 hosted-capture repetition or retained row/body/document bounds changed",
    )


def validate_counterexample(c6_entries: dict[str, Any]) -> dict[str, Any]:
    schema_raw = exact_file(
        COUNTEREXAMPLE_SCHEMA_RELATIVE,
        COUNTEREXAMPLE_SCHEMA_SHA256,
        COUNTEREXAMPLE_SCHEMA_SIZE_BYTES,
    )
    evidence_raw = exact_file(COUNTEREXAMPLE_RELATIVE, COUNTEREXAMPLE_SHA256, COUNTEREXAMPLE_SIZE_BYTES)
    return validate_counterexample_pair_bytes(schema_raw, evidence_raw, c6_entries)


def validate_counterexample_pair_bytes(
    schema_raw: bytes, evidence_raw: bytes, c6_entries: dict[str, Any]
) -> dict[str, Any]:
    """Validate the one exact full-Draft pair without pretending to evaluate it generically."""
    require(
        len(schema_raw) == COUNTEREXAMPLE_SCHEMA_SIZE_BYTES
        and sha256(schema_raw) == COUNTEREXAMPLE_SCHEMA_SHA256,
        "exact counterexample schema bytes changed",
    )
    require(
        len(evidence_raw) == COUNTEREXAMPLE_SIZE_BYTES
        and sha256(evidence_raw) == COUNTEREXAMPLE_SHA256,
        "exact counterexample evidence bytes changed",
    )
    schema = parse_json(schema_raw, "C6 local-closure counterexample schema")
    evidence = parse_json(evidence_raw, "C6 local-closure counterexample")
    require(
        type(schema) is dict
        and set(schema) == {
            "$defs",
            "$id",
            "$schema",
            "additionalProperties",
            "properties",
            "required",
            "type",
        }
        and schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        and schema["$id"]
        == f"https://github.com/sepahead/pid-rs/blob/main/{COUNTEREXAMPLE_SCHEMA_RELATIVE}"
        and schema["additionalProperties"] is False,
        "exact counterexample schema root changed",
    )
    validate_counterexample_value(evidence, c6_entries)
    return evidence


def validate_counterexample_value(evidence: dict[str, Any], c6_entries: dict[str, Any]) -> None:
    require(
        type(evidence) is dict
        and set(evidence)
        == {
            "authorities",
            "bounds",
            "conclusion",
            "counterexamples",
            "derivation",
            "nonimplications",
            "rederivation",
            "repository",
            "route",
            "schema",
            "source_anchors",
            "subject",
        }
        and evidence["schema"]
        == "pid-rs/ksg-rev4-m1a-composite-v6-local-closure-counterexample-v7/v1"
        and evidence["repository"] == REPOSITORY,
        "counterexample root identity changed",
    )
    c6_commit = parse_commit(C6_COMMIT)
    require(
        evidence["subject"]
        == {
            "commit_message": c6_commit.message,
            "commit_object_sha1": c6_commit.oid,
            "object_format": "sha1",
            "parent_commit_sha1": c6_commit.parent,
            "source_basis": "immutable_commit_tree",
            "tree_object_sha1": c6_commit.tree,
        },
        "counterexample exact C6 subject changed",
    )
    expected_authorities = []
    for path, role, digest, size in C6_LOCAL_AUTHORITIES:
        raw = tree_blob(c6_entries, path)
        expected_authorities.append(
            {
                "blob_sha1": c6_entries[path].oid,
                "mode": c6_entries[path].mode,
                "path": path,
                "role": role,
                "sha256": digest,
                "size_bytes": size,
            }
        )
        require(len(raw) == size and sha256(raw) == digest, f"counterexample authority drift: {path}")
    require(evidence["authorities"] == expected_authorities, "counterexample authority rederivation changed")
    source_path = "scripts/capture-ksg-m1a-composite-v6-local-closure.py"
    source = tree_blob(c6_entries, source_path)
    lines = source.splitlines(keepends=True)
    expected_anchors: list[dict[str, Any]] = []
    for anchor_id, line_start, line_end, size, digest in COUNTEREXAMPLE_ANCHORS:
        raw = b"".join(lines[line_start - 1 : line_end])
        require(
            len(raw) == size and sha256(raw) == digest,
            f"counterexample source anchor changed: {anchor_id}",
        )
        expected_anchors.append(
            {
                "id": anchor_id,
                "line_end": line_end,
                "line_start": line_start,
                "path": source_path,
                "sha256": digest,
                "size_bytes": size,
            }
        )
    require(evidence["source_anchors"] == expected_anchors, "counterexample source-anchor tuple changed")

    stream_bound = 65_536
    local_bound = 2_097_152
    require(
        evidence["bounds"]
        == {
            "committed_internal_stream_bound_bytes": stream_bound,
            "committed_internal_stream_bound_expression": "64 * 1024",
            "largest_complete_stdout_accepted_bytes": stream_bound,
            "local_authority_bound_bytes": local_bound,
            "local_authority_bound_expression": "2 * 1024 * 1024",
            "overflow_predicate": "len(destination) > maximum_stream_bytes",
            "stream_bound_symbol": "MAX_VERSION_STREAM_BYTES",
        },
        "counterexample exact bound model changed",
    )
    require(
        evidence["route"]
        == {
            "authority_iteration": "sorted(AUTHORITY_ROLES.items())",
            "call_chain": ["authority_descriptors", "git_output", "internal_command", "run_bounded"],
            "capture_execution_order": [
                "toolchain_observation",
                "repository_snapshot",
                "authority_descriptors",
                "run_bounded(COMMAND_ARGV, ...)",
            ],
            "committed_blob_read": 'git_output(git_path, environment, "show", f"{head}:{relative}")',
            "committed_blob_transport": "git show stdout",
            "equality_guard": 'require(raw == committed, "local authority differs from the C6 tree")',
            "internal_command_bound_argument": "MAX_VERSION_STREAM_BYTES",
            "local_blob_read": "read_regular(ROOT / relative, 2 * 1024 * 1024, 0o644)",
            "stream_accumulation": "destination.extend(chunk)",
        },
        "counterexample committed source route changed",
    )
    require(
        evidence["rederivation"]
        == {
            "content_command_template": ["git", "show", f"{C6_COMMIT}:<PATH>"],
            "size_command_template": ["git", "cat-file", "-s", f"{C6_COMMIT}:<PATH>"],
            "source_anchor_definition": "inclusive one-based LF-terminated line slices of the exact C6 capture-tool blob",
        },
        "counterexample rederivation recipe changed",
    )

    oversized = [item for item in expected_authorities if item["size_bytes"] > stream_bound]
    expected_counterexamples = [
        {
            "committed_blob_sha1": item["blob_sha1"],
            "committed_stdout_size_bytes": item["size_bytes"],
            "complete_stdout_accepted_by_run_bounded": False,
            "exact_equality_return_possible": False,
            "excess_over_stream_bound_bytes": item["size_bytes"] - stream_bound,
            "path": item["path"],
            "required_by_authority_roles": True,
            "sha256": item["sha256"],
            "size_within_local_authority_bound": item["size_bytes"] <= local_bound,
        }
        for item in oversized
    ]
    require(
        evidence["counterexamples"] == expected_counterexamples,
        "counterexample rows do not rederive from the exact authority inventory",
    )
    authority_paths = [item["path"] for item in expected_authorities]
    first_oversized = authority_paths.index(oversized[0]["path"])
    require(
        evidence["derivation"]
        == {
            "all_authorities_required": True,
            "authority_count": len(expected_authorities),
            "authority_order": authority_paths,
            "complete_authority_binding_precedes_local_command": True,
            "exact_local_committed_equality_required": True,
            "first_oversized_authority_index_zero_based": first_oversized,
            "oversized_required_authority_count": len(oversized),
            "proof_rule": "for each required authority, local_size <= local_authority_bound and committed_stdout_size > committed_internal_stream_bound implies run_bounded cannot return the complete committed bytes required by raw == committed",
            "result": "contradiction",
        },
        "counterexample derivation and authority order changed",
    )
    require(
        evidence["conclusion"]
        == {
            "complete_authority_list_constructible": False,
            "exact_authority_equality_satisfiable": False,
            "first_blocking_path": oversized[0]["path"],
            "immutable_c6_local_record_issuable": False,
            "reason": "required_committed_blob_exceeds_internal_stdout_bound",
            "result": "static_contract_contradiction",
            "scope": "immutable_c6_local_recorder",
        }
        and evidence["nonimplications"] == COUNTEREXAMPLE_NONIMPLICATIONS,
        "counterexample conclusion or bounded nonimplications changed",
    )


def validate_schema_file(relative: str, expected_id_suffix: str) -> dict[str, Any]:
    raw = read_file(relative)
    schema = parse_json(raw, relative)
    validate_schema_value(schema, relative, expected_id_suffix)
    return schema


def validate_schema_value(schema: dict[str, Any], relative: str, expected_id_suffix: str) -> None:
    validate_schema_instance({}, schema, relative, definition_only=True)
    root_closed = (
        schema.get("oneOf")
        == [
            {"$ref": "#/$defs/predecessorDocument"},
            {"$ref": "#/$defs/successorDocument"},
        ]
        if relative == CAPTURE_SCHEMA_RELATIVE
        else schema.get("additionalProperties") is False
    )
    require(
        type(schema) is dict
        and schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        and type(schema.get("$id")) is str
        and schema["$id"]
        == f"https://github.com/sepahead/pid-rs/blob/main/{expected_id_suffix}"
        and root_closed,
        f"closed schema root changed: {relative}",
    )


def tree_descriptor(entries: dict[str, Any], path: str) -> dict[str, Any]:
    raw = tree_blob(entries, path)
    return {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}


def validate_capture_root_v7(
    capture_raw: bytes,
    phase: str,
    c7_entries: dict[str, Any],
    c7: str,
    c7_tree: str,
    capture_schema: dict[str, Any],
    capture_tool_binding: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Any]:
    require(
        0 < len(capture_raw) <= V6.MAX_JSON_BYTES,
        f"composite-v7 {phase} hosted capture size is outside the bound",
    )
    value = parse_json(capture_raw, f"composite-v7 {phase} hosted capture")
    validate_schema_instance(value, capture_schema, f"composite-v7 {phase} hosted capture")
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v6_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        f"composite-v7 {phase} capture",
    )
    expected_subject = {"predecessor_commit": C6_COMMIT, "predecessor_tree": C6_TREE}
    if phase == "successor_qualification":
        expected_subject.update({"successor_commit": c7, "successor_tree": c7_tree})
    require(
        phase in PHASE_ROLES
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v7"
        and root["schema_revision"] == 7
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["phase"] == phase
        and root["subject"] == expected_subject
        and root["capture_tool"]
        == (
            tree_descriptor(c7_entries, CAPTURE_TOOL_RELATIVE)
            if capture_tool_binding is None
            else capture_tool_binding
        )
        and root["immutable_v6_primitives"] == V6_CAPTURE_PRIMITIVE
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS,
        f"composite-v7 {phase} capture identity or phase coupling changed",
    )
    runs = exact_keys(root["runs"], set(PHASE_ROLES[phase]), f"composite-v7 {phase} run map")
    expected_predecessor = {
        "predecessor_ci": C6_CI_RUN,
        "predecessor_codeql": C6_CODEQL_RUN,
        "predecessor_contract": C6_CONTRACT_RUN,
    }
    require(
        all(type(item) is int and item > 0 for item in runs.values())
        and len(set(runs.values())) == 3
        and (phase != "predecessor_failure" or runs == expected_predecessor),
        f"composite-v7 {phase} run identifiers changed or overlap",
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
            and event["category"] in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(event["logical_request"]) is str
            and event["logical_request"]
            and type(event["page"]) is int
            and event["page"] >= 0
            and type(event["path"]) is str
            and event["path"].startswith(f"/repos/{REPOSITORY}/")
            and type(event["response_sha256"]) is str
            and SHA256_RE.fullmatch(event["response_sha256"]) is not None
            and type(event["response_size_bytes"]) is int
            and 0 <= event["response_size_bytes"] <= V6.MAX_JSON_BYTES,
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
    require(retry_keys == sorted(set(retry_keys)), "capture retry events are not sorted unique")
    captures = root["captures"]
    require(
        type(captures) is list and 0 < len(captures) <= V6.MAX_CAPTURE_ROWS,
        "capture response count is outside the bound",
    )
    decoded = [V6.decode_capture_row(item, f"capture response {index}") for index, item in enumerate(captures)]
    require(
        sum(len(raw) for _row, raw in decoded) <= V6.MAX_CAPTURE_BODY_BYTES,
        "retained provider bodies exceed the checker budget",
    )
    keys = [
        (row["logical_request"], row["repetition"], row["page"], row["path"])
        for row, _raw in decoded
    ]
    require(keys == sorted(set(keys)), "capture responses are not sorted unique")
    capture_keys = set(keys)
    retry_groups: dict[tuple[str, int, int, str], list[int]] = defaultdict(list)
    for logical, repetition, page, path, attempt in retry_keys:
        key = (logical, repetition, page, path)
        require(key in capture_keys, "retry event has no successful request row")
        retry_groups[key].append(attempt)
    require(
        all(attempts == list(range(1, len(attempts) + 1)) and len(attempts) <= 2 for attempts in retry_groups.values()),
        "retry attempts are not consecutive and bounded",
    )
    grouped: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]] = defaultdict(list)
    for row, raw in decoded:
        grouped[(row["logical_request"], row["repetition"])].append((row, raw))
    return root, CaptureRows(dict(grouped))


def normalized_run_v7(value: Any, role: str, run_id: int, head: str) -> dict[str, Any]:
    require(type(value) is dict, f"{role} run response is not an object")
    repository = value.get("repository")
    head_repository = value.get("head_repository")
    result = {
        "conclusion": value.get("conclusion"),
        "created_at": value.get("created_at"),
        "event": value.get("event"),
        "head_branch": value.get("head_branch"),
        "head_sha": value.get("head_sha"),
        "name": value.get("name"),
        "path": value.get("path"),
        "repository_id": repository.get("id") if type(repository) is dict else None,
        "run_attempt": value.get("run_attempt"),
        "run_id": value.get("id"),
        "run_started_at": value.get("run_started_at"),
        "status": value.get("status"),
        "updated_at": value.get("updated_at"),
        "workflow_id": value.get("workflow_id"),
    }
    require(
        result["run_id"] == run_id
        and type(result["run_id"]) is int
        and result["head_sha"] == head
        and result["head_branch"] == "main"
        and result["run_attempt"] == 1
        and type(result["run_attempt"]) is int
        and result["status"] == "completed"
        and result["conclusion"] == EXPECTED_RUN_CONCLUSION[role]
        and type(result["workflow_id"]) is int
        and result["workflow_id"] > 0
        and type(repository) is dict
        and repository.get("full_name") == REPOSITORY
        and type(head_repository) is dict
        and head_repository.get("full_name") == REPOSITORY
        and type(result["repository_id"]) is int
        and result["repository_id"] == C6_REPOSITORY_ID
        and head_repository.get("id") == result["repository_id"],
        f"{role} run identity or disposition changed",
    )
    expected_routes = {
        "ci": (297_369_773, "CI", CI_RELATIVE, "push"),
        "codeql": (310_582_096, "Push on main", "dynamic/github-code-scanning/codeql", "dynamic"),
        "predecessor_contract": (None, "KSG M1a composite v6", V6_WORKFLOW_RELATIVE, "push"),
        "successor_contract": (None, "KSG M1a composite v7", V7_WORKFLOW_RELATIVE, "push"),
    }
    route_key = ROLE_KIND[role] if ROLE_KIND[role] != "contract" else role
    workflow_id, name, path, event = expected_routes[route_key]
    require(
        (workflow_id is None or result["workflow_id"] == workflow_id)
        and (result["name"], result["path"], result["event"]) == (name, path, event),
        f"{role} exact workflow route changed",
    )
    if role == "predecessor_ci":
        validate_c6_ci_terminal_run_v7(result)
    return result


def validate_c6_ci_terminal_run_v7(value: dict[str, Any]) -> None:
    require(
        value.get("repository_id") == C6_REPOSITORY_ID
        and value.get("created_at") == C6_CI_CREATED_AT
        and value.get("run_started_at") == C6_CI_CREATED_AT
        and value.get("updated_at") == C6_CI_UPDATED_AT,
        "predecessor CI terminal time or repository identity changed",
    )


def validate_predecessor_job_dispositions_v7(
    jobs: list[dict[str, Any]], role: str, failed: set[int]
) -> None:
    require(
        failed == PREDECESSOR_REQUIRED_FAILED_JOB_IDS[role],
        f"{role} failed-job identity changed",
    )
    require(
        all(
            item["conclusion"]
            == ("failure" if item["job_id"] in failed else "success")
            for item in jobs
        ),
        f"{role} contains an unbound non-success job disposition",
    )


def validate_required_failure_identity_v7(
    role: str, job_id: int, job: dict[str, Any]
) -> None:
    job_name, failed_steps = PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[role][job_id]
    require(
        job["name"] == job_name
        and tuple(
            sorted(
                (item["number"], item["name"])
                for item in job["steps"]
                if item["conclusion"] == "failure"
            )
        )
        == failed_steps,
        f"{role} required failure identity changed for job {job_id}",
    )


def normalized_jobs_v7(
    values: list[Any], role: str, run_id: int, head: str
) -> tuple[list[dict[str, Any]], set[int]]:
    jobs: list[dict[str, Any]] = []
    for value in values:
        require(type(value) is dict, f"{role} job is not an object")
        job_id = exact_int(value.get("id"), f"{role} job id", 1)
        conclusion = value.get("conclusion")
        require(
            value.get("status") == "completed"
            and conclusion in {"success", "failure", "skipped", "cancelled"}
            and value.get("run_id") == run_id
            and type(value.get("run_id")) is int
            and value.get("run_attempt") == 1
            and type(value.get("run_attempt")) is int
            and value.get("head_sha") == head
            and type(value.get("name")) is str
            and value.get("name"),
            f"{role} job identity or disposition changed",
        )
        started_raw, completed_raw = V6.normalized_job_timestamps(value, conclusion, role)
        steps_raw = value.get("steps")
        require(
            type(steps_raw) is list and (steps_raw != [] or conclusion in {"skipped", "cancelled"}),
            f"{role} job steps are absent",
        )
        steps: list[dict[str, Any]] = []
        for step in steps_raw:
            require(type(step) is dict, f"{role} step is not an object")
            normalized = {
                "conclusion": step.get("conclusion"),
                "name": step.get("name"),
                "number": step.get("number"),
                "status": step.get("status"),
            }
            require(
                normalized["status"] == "completed"
                and normalized["conclusion"] in {"success", "failure", "skipped", "cancelled"}
                and type(normalized["name"]) is str
                and normalized["name"]
                and type(normalized["number"]) is int
                and normalized["number"] > 0,
                f"{role} step identity or disposition changed",
            )
            steps.append(normalized)
        steps.sort(key=lambda item: item["number"])
        require(len(steps) == len({item["number"] for item in steps}), f"{role} step numbers overlap")
        if conclusion == "failure":
            require(any(item["conclusion"] == "failure" for item in steps), f"{role} failed job has no failed step")
        elif conclusion == "success":
            require(all(item["conclusion"] in {"success", "skipped"} for item in steps), f"{role} successful job contains an adverse step")
        jobs.append(
            {
                "completed_at": completed_raw,
                "conclusion": conclusion,
                "job_id": job_id,
                "name": value["name"],
                "started_at": started_raw,
                "status": "completed",
                "steps": steps,
            }
        )
    jobs.sort(key=lambda item: item["job_id"])
    require(len(jobs) == len({item["job_id"] for item in jobs}), f"{role} job IDs overlap")
    failed = {item["job_id"] for item in jobs if item["conclusion"] == "failure"}
    expected_count = 45 if ROLE_KIND[role] == "ci" else 4 if ROLE_KIND[role] == "codeql" else 1
    require(len(jobs) == expected_count, f"{role} job count changed")
    if role.startswith("successor_") or role == "predecessor_codeql":
        require(all(item["conclusion"] == "success" for item in jobs), f"{role} has an adverse job")
    else:
        validate_predecessor_job_dispositions_v7(jobs, role, failed)
        by_id = {item["job_id"]: item for item in jobs}
        for failed_id in PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[role]:
            job = by_id.get(failed_id)
            require(job is not None, f"{role} required failure job {failed_id} is absent")
            validate_required_failure_identity_v7(role, failed_id, job)
    names = tuple(sorted(item["name"] for item in jobs))
    if ROLE_KIND[role] == "ci":
        require(names == V6._v5._v4.EXPECTED_CI_JOB_NAMES, f"{role} CI job roster changed")
    elif ROLE_KIND[role] == "codeql":
        require(
            names == tuple(sorted(f"Analyze ({language})" for language in V6._v5._v4.LANGUAGE_ORDER)),
            f"{role} CodeQL job roster changed",
        )
    else:
        expected_name = (
            "Validate the composite-v6 correction contract"
            if role == "predecessor_contract"
            else "Validate the composite-v7 bounded correction contract"
        )
        require(names == (expected_name,), f"{role} contract job name changed")
        step_names = [item["name"] for item in jobs[0]["steps"]]
        required_steps = (
            {
                "Validate immutable predecessor PDF portability and the bounded successor publication",
                "Validate fresh replay and current-source custody",
                "Validate static v6 contract in normal and optimized modes",
                "Upload the exact v6 static result",
            }
            if role == "predecessor_contract"
            else {
                "Normalize only the reviewed inert checkout residue",
                "Refuse retries and non-main qualification events",
                "Install the hash-pinned PDF verifier dependency",
                "Install the complete reviewed PDF command set",
                "Recheck retained C6 operational surfaces",
                "Recheck the unchanged v6 publications after dependency closure",
                "Validate the composite-v7 publication family and hostile suite",
                "Validate fresh replay and current-source custody",
                "Validate static v7 contract in normal and optimized modes",
                "Upload the exact v7 static result",
            }
        )
        require(all(step_names.count(name) == 1 for name in required_steps), f"{role} contract step roster changed")
        if role == "predecessor_contract":
            require(
                [item["name"] for item in jobs[0]["steps"] if item["conclusion"] == "failure"]
                == ["Validate immutable predecessor PDF portability and the bounded successor publication"],
                "predecessor contract failure-step identity changed",
            )
        else:
            require(
                all(next(item for item in jobs[0]["steps"] if item["name"] == name)["conclusion"] == "success" for name in required_steps),
                "successor contract bounded-repair step did not succeed",
            )
    return jobs, failed


def validate_failed_job_logs_v7(
    rows: Any, role: str, failed_ids: set[int]
) -> None:
    repetitions: list[list[tuple[int, str, int]]] = []
    for repetition in (1, 2):
        observed: list[tuple[int, str, int]] = []
        for job_id in sorted(failed_ids):
            captures = rows.take(f"{role}_failed_job_{job_id}_log", repetition)
            require(
                len(captures) == 1
                and captures[0][0]["page"] == 0
                and captures[0][0]["path"] == f"/repos/{REPOSITORY}/actions/jobs/{job_id}/logs"
                and captures[0][0]["response_kind"] == "log",
                f"{role} failed-job log capture changed",
            )
            raw = captures[0][1]
            validate_required_failed_log_binding_v7(
                role, job_id, sha256(raw), len(raw)
            )
            require(
                C6_MISSING_RG_DIAGNOSTIC.encode("ascii") in raw,
                f"{role} missing-rg diagnostic is absent from failed job {job_id}",
            )
            if role == "predecessor_ci":
                validate_c6_ci_prior_pdf_markers_v7(raw)
            observed.append((job_id, sha256(raw), len(raw)))
        repetitions.append(observed)
    require(repetitions[0] == repetitions[1], f"{role} repeated failed-job logs differ")


def validate_required_failed_log_binding_v7(
    role: str, job_id: int, digest: str, size: int
) -> None:
    require(
        PREDECESSOR_REQUIRED_LOG_BINDINGS.get(role, {}).get(job_id)
        == (digest, size),
        f"{role} failed-job log bytes changed for job {job_id}",
    )


def validate_c6_ci_prior_pdf_markers_v7(raw: bytes) -> None:
    diagnostic = C6_MISSING_RG_DIAGNOSTIC.encode("ascii")
    require(
        raw.count(diagnostic) == 1
        and all(raw.count(marker) == 1 for marker in C6_CI_PRIOR_PDF_GATE_MARKERS),
        "predecessor CI seven prior PDF-gate markers changed",
    )
    offsets = [raw.index(marker) for marker in C6_CI_PRIOR_PDF_GATE_MARKERS]
    require(
        offsets == sorted(offsets) and offsets[-1] < raw.index(diagnostic),
        "predecessor CI prior PDF gates did not precede the missing-rg diagnostic",
    )


def validate_contract_artifact_v7(
    artifacts: list[dict[str, Any]], archives: dict[int, bytes], c7: str, c7_tree: str
) -> None:
    require(len(artifacts) == 1, "successor contract artifact count changed")
    artifact = artifacts[0]
    require(
        artifact["name"] == f"ksg-m1a-composite-v7-static-{c7}",
        "successor contract artifact name changed",
    )
    member_path = "ksg-m1a-composite-v7-static.json"
    matches = [item for item in artifact["members"] if item["path"] == member_path]
    require(len(matches) == 1 and artifact["members"] == matches, "successor contract artifact members changed")
    raw = member_bytes(archives[artifact["artifact_id"]], member_path, "successor contract artifact")
    value = parse_json(raw, "successor contract static result", canonical=False)
    require(
        raw == canonical_json(value, pretty=False)
        and value
        == {
            "c6_commit": C6_COMMIT,
            "c7_commit": c7,
            "head": c7,
            "r7_commit": None,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v7-static-validation/v1",
            "tree": c7_tree,
        },
        "successor contract static result changed",
    )


def derive_role_observation_v7(
    rows: Any,
    role: str,
    run_id: int,
    head: str,
    entries: dict[str, Any],
    tree: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    repeated: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[int, bytes], Any, Any]] = []
    failed_sets: list[set[int]] = []
    for repetition in (1, 2):
        run = normalized_run_v7(
            single_json_response(
                rows,
                f"{role}_run",
                repetition,
                f"/repos/{REPOSITORY}/actions/runs/{run_id}",
            ),
            role,
            run_id,
            head,
        )
        jobs, failed = normalized_jobs_v7(
            paged_json_response(
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
        artifact_values = paged_json_response(
            rows,
            f"{role}_artifacts",
            repetition,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts",
            "artifacts",
        )
        artifacts, archives = normalized_artifacts(
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
            analyses = normalized_analyses(
                paged_json_response(
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
                state: paged_json_response(
                    rows,
                    f"{role}_alerts_{state}",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}",
                    None,
                )
                for state in ("dismissed", "fixed", "open")
            }
            alerts = normalized_alerts(alert_values, role)
        repeated.append((run, jobs, artifacts, archives, analyses, alerts))
        failed_sets.append(failed)
    first, second = repeated
    require(
        canonical_json((first[0], first[1], first[2], first[4], first[5]), pretty=False)
        == canonical_json((second[0], second[1], second[2], second[4], second[5]), pretty=False),
        f"{role} repeated normalized observations differ",
    )
    run, jobs, artifacts, archives, _analyses, _alerts = first
    require(failed_sets[0] == failed_sets[1], f"{role} repeated failed-job identities differ")
    if role in {"predecessor_codeql", "predecessor_contract", "successor_codeql"}:
        require(artifacts == [], f"{role} unexpectedly published artifacts")
    elif role == "successor_ci":
        validate_postcommit_artifact(artifacts, archives, entries, head, tree, role)
    elif role == "successor_contract":
        validate_contract_artifact_v7(artifacts, archives, head, tree)
    if role.startswith("predecessor_"):
        validate_failed_job_logs_v7(rows, role, failed_sets[0])
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
            if _analyses is None
            else [item["analysis_id"] for item in _analyses],
            "artifact_ids": [item["artifact_id"] for item in artifacts],
            "job_ids": [item["job_id"] for item in jobs],
            "repository_id": run["repository_id"],
            "run_id": run["run_id"],
        },
    )


def validate_identifier_domains_v7(domains: list[dict[str, Any]]) -> None:
    require(domains != [], "hosted identifier-domain projection is empty")
    repository_ids = [item["repository_id"] for item in domains]
    require(
        len(set(repository_ids)) == 1,
        "hosted repository identifier join changed",
    )
    for field, label in (
        ("run_id", "run"),
        ("job_ids", "job"),
        ("artifact_ids", "artifact"),
        ("analysis_ids", "CodeQL analysis"),
    ):
        identifiers = (
            [item[field] for item in domains]
            if field == "run_id"
            else [identifier for item in domains for identifier in item[field]]
        )
        require(
            len(identifiers) == len(set(identifiers)),
            f"hosted {label} identifier domains overlap",
        )


def derive_phase_with_domains_v7(
    capture_raw: bytes,
    phase: str,
    c7_entries: dict[str, Any],
    c7: str,
    c7_tree: str,
    capture_schema: dict[str, Any],
    capture_tool_binding: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    capture, rows = validate_capture_root_v7(
        capture_raw,
        phase,
        c7_entries,
        c7,
        c7_tree,
        capture_schema,
        capture_tool_binding,
    )
    head = C6_COMMIT if phase == "predecessor_failure" else c7
    tree = C6_TREE if phase == "predecessor_failure" else c7_tree
    entries = parse_tree(tree)
    derived = [
        derive_role_observation_v7(
            rows, role, capture["runs"][role], head, entries, tree
        )
        for role in PHASE_ROLES[phase]
    ]
    rows.finish()
    roles = [item[0] for item in derived]
    domains = [item[1] for item in derived]
    result = {
        "capture_sha256": sha256(capture_raw),
        "normalized_sha256": project_digest(roles),
        "phase": phase,
        "roles": roles,
    }
    validate_identifier_domains_v7(domains)
    return result, domains


def derive_phase_v7(
    capture_raw: bytes,
    phase: str,
    c7_entries: dict[str, Any],
    c7: str,
    c7_tree: str,
    capture_schema: dict[str, Any],
    capture_tool_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result, _domains = derive_phase_with_domains_v7(
        capture_raw,
        phase,
        c7_entries,
        c7,
        c7_tree,
        capture_schema,
        capture_tool_binding,
    )
    return result


def decode_local_public_binding_v7(value: Any, label: str, maximum: int) -> bytes:
    raw = V6.decode_local_binding(value, label, maximum)
    V6.reject_local_sensitive_bytes(raw, label)
    return raw


def load_local_record_validator(raw: bytes) -> types.ModuleType:
    require(
        len(raw) == LOCAL_TOOL_SIZE_BYTES and sha256(raw) == LOCAL_TOOL_SHA256,
        "v7 local-recorder validator source changed",
    )
    module = types.ModuleType("pid_rs_exact_composite_v7_local_record_validator")
    module.__file__ = os.fspath(ROOT / LOCAL_TOOL_RELATIVE)
    module.__package__ = ""
    try:
        code = compile(raw, module.__file__, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        exec(code, module.__dict__)
    except (OSError, SyntaxError, RuntimeError) as error:
        raise ContractError(f"cannot load exact v7 local-record validator: {error}") from None
    return module


def derive_local_qualification_v7(
    local_raw: bytes,
    c7_entries: dict[str, Any],
    c7: str,
    c7_tree: str,
    local_schema: dict[str, Any],
) -> dict[str, Any]:
    require(0 < len(local_raw) <= LOCAL_LIMITS["record_bytes"], "local record size is outside the bound")
    value = parse_json(local_raw, "composite-v7 local closure")
    validate_schema_instance(value, local_schema, "composite-v7 local closure")
    validator_raw = tree_blob(c7_entries, LOCAL_TOOL_RELATIVE)
    validator = load_local_record_validator(validator_raw)
    try:
        validator.validate_record_value(value)
    except Exception as error:
        raise ContractError(f"composite-v7 local closure semantic validation failed: {error}") from None
    require(
        value["subject"]
        == {
            "c6_parent": C6_COMMIT,
            "c7_commit": c7,
            "c7_message": C7_MESSAGE,
            "c7_tree": c7_tree,
        }
        and value["limits"] == LOCAL_LIMITS
        and value["nonimplications"] == LOCAL_NONIMPLICATIONS
        and value["immutable_v6_primitives"] == V6_LOCAL_PRIMITIVE,
        "composite-v7 local subject, limits, or primitive identity changed",
    )
    expected_authorities = []
    for path, role in sorted(LOCAL_AUTHORITY_ROLES.items()):
        raw = tree_blob(c7_entries, path)
        require(
            c7_entries[path].mode == "100644" and 0 < len(raw) <= LOCAL_LIMITS["authority_stream_bytes"],
            f"composite-v7 local authority mode or bound changed: {path}",
        )
        expected_authorities.append(
            {"path": path, "role": role, "sha256": sha256(raw), "size_bytes": len(raw)}
        )
    require(value["authorities"] == expected_authorities, "local record authorities differ from exact C7")
    invocation = value["invocation"]
    reviewed = value["reviewed_executables"]
    command_stdout = decode_local_public_binding_v7(
        invocation["stdout"], "composite-v7 local command stdout", LOCAL_LIMITS["command_stream_bytes"]
    )
    command_stderr = decode_local_public_binding_v7(
        invocation["stderr"], "composite-v7 local command stderr", LOCAL_LIMITS["command_stream_bytes"]
    )
    require(command_stdout + command_stderr != b"", "composite-v7 local command retained no output")
    for item in reviewed:
        version_stdout = decode_local_public_binding_v7(
            item["version_stdout"],
            f"composite-v7 local {item['name']} version stdout",
            LOCAL_LIMITS["version_stream_bytes"],
        )
        version_stderr = decode_local_public_binding_v7(
            item["version_stderr"],
            f"composite-v7 local {item['name']} version stderr",
            LOCAL_LIMITS["version_stream_bytes"],
        )
        require(
            version_stdout + version_stderr != b"",
            f"composite-v7 local {item['name']} version output is empty",
        )
    require(
        [item["name"] for item in reviewed] == sorted(LOCAL_TOOL_SPECS)
        and all(item["version_argv"] == [item["name"], *LOCAL_TOOL_SPECS[item["name"]]] for item in reviewed),
        "local reviewed-executable exact roster changed",
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
            "sha256": sha256(local_raw),
            "size_bytes": len(local_raw),
        },
        "reviewed_executables_sha256": project_digest(reviewed),
        "subject": {"c7_commit": c7, "c7_tree": c7_tree},
    }


def policy_rows_v7(value: Any, label: str) -> tuple[tuple[str, str, str, str], ...]:
    require(type(value) is list and value != [], f"{label} is not a nonempty array")
    rows: list[tuple[str, str, str, str]] = []
    for index, item in enumerate(value):
        row = exact_keys(item, {"mode", "path", "role", "status"}, f"{label}[{index}]")
        path = row["path"]
        require(
            type(path) is str
            and V6._v5._v4.validate_relative_path(path, f"{label}[{index}] path")
            and row["mode"] in {"100644", "100755"}
            and row["status"] in {"A", "M"}
            and type(row["role"]) is str
            and re.fullmatch(r"[a-z0-9_]+", row["role"]) is not None,
            f"{label}[{index}] changed",
        )
        rows.append((path, row["status"], row["mode"], row["role"]))
    require(rows == sorted(set(rows)), f"{label} is not path-sorted unique")
    require(
        len({path for path, _status, _mode, _role in rows}) == len(rows),
        f"{label} repeats a path",
    )
    return tuple(rows)


def authority_descriptor_v7(
    entries: dict[str, Any], path: str, role: str
) -> dict[str, Any]:
    return {**tree_descriptor(entries, path), "role": role}


def contract_authorities_v7(
    c6_entries: dict[str, Any],
    c7_entries: dict[str, Any],
    c7_policy_rows: tuple[tuple[str, str, str, str], ...],
) -> list[dict[str, Any]]:
    values = [
        authority_descriptor_v7(c6_entries, path, role)
        for path, role in C6_RECEIPT_AUTHORITY_ROLES.items()
    ]
    values.extend(
        authority_descriptor_v7(c7_entries, path, role)
        for path, _status, _mode, role in c7_policy_rows
    )
    values.sort(key=lambda item: (item["path"], item["role"]))
    require(
        len(values) == len({(item["path"], item["role"]) for item in values}),
        "composite-v7 contract authority roles overlap",
    )
    return values


def lean_replay_projection_sha256_v7(receipt: dict[str, Any]) -> str:
    """Reproduce the r12 projection without importing the mutable Lean checker."""

    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    require(type(custody) is dict, "r12 custody-gate inventory is malformed")
    require(
        tuple(custody) == LEAN_CUSTODY_PATHS,
        "r12 custody-gate exact path set drifted",
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
        raise ContractError(f"cannot project r12 replay receipt: {error}") from None
    return sha256(raw)


def lean_r12_source_cuts_v7(raw: bytes) -> tuple[str, str, str, bytes]:
    """Extract and normalize exactly the three final Lean/r12 checksum cuts."""

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
            "composite-v7 checker scalar",
            re.compile(
                r'^EXPECTED_COMPOSITE_V7_CHECKER_OPERATIONAL_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            re.compile(
                r"^EXPECTED_COMPOSITE_V7_CHECKER_OPERATIONAL_SHA256 = .+$",
                re.MULTILINE,
            ),
            'EXPECTED_COMPOSITE_V7_CHECKER_OPERATIONAL_SHA256 = "0" * 64',
        ),
        (
            "composite-v7 operational-map row",
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v7\.py": "([0-9a-f]{64})",$',
                re.MULTILINE,
            ),
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v7\.py": .+$',
                re.MULTILINE,
            ),
            '    "scripts/check-ksg-m1a-composite-v7.py": "0" * 64,',
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


def normalized_lean_checker_cut_v7(raw: bytes) -> str:
    """Extract the one final normalized-Lean binding from v7 checker bytes."""

    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"composite-v7 checker is not UTF-8: {error}") from None
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


def validate_lean_r12_checksum_cut_v7(
    v7_checker_raw: bytes, lean_checker_raw: bytes
) -> str:
    """Bind final v7 bytes to the exactly three-cut-normalized Lean source."""

    checker_digest = sha256(v7_checker_raw)
    projection, scalar_cut, operational_cut, normalized = lean_r12_source_cuts_v7(
        lean_checker_raw
    )
    require(
        scalar_cut == checker_digest and operational_cut == checker_digest,
        "Lean composite-v7 checker cuts do not bind the exact v7 checker bytes",
    )
    require(
        normalized_lean_checker_cut_v7(v7_checker_raw) == sha256(normalized),
        "normalized Lean checker authority changed",
    )
    return projection


def validate_lean_r12_receipt_cuts_v7(
    v7_checker_raw: bytes,
    lean_checker_raw: bytes,
    lean_self_test_raw: bytes,
    r11: dict[str, Any],
    r12: dict[str, Any],
    projection: str,
) -> None:
    """Join the r12 projection and custody-only exact-set semantics."""

    operational = r12.get("operational_wiring_sha256")
    scientific = r12.get("checker_sha256")
    require(
        type(operational) is dict
        and operational.get(CHECKER_RELATIVE) == sha256(v7_checker_raw),
        "Lean r12 operational map does not bind the v7 checker bytes",
    )
    require(
        type(scientific) is dict and scientific == r11.get("checker_sha256"),
        "Lean r12 scientific checker inventory changed from r11",
    )
    require(
        lean_replay_projection_sha256_v7(r12) == projection,
        "Lean r12 projection cut changed",
    )
    final_custody = r12.get("custody_gate_sha256")
    replay_custody = r12.get("replay_custody_gate_sha256")
    require(
        type(final_custody) is dict
        and type(replay_custody) is dict
        and tuple(final_custody) == LEAN_CUSTODY_PATHS
        and tuple(replay_custody) == LEAN_CUSTODY_PATHS,
        "Lean r12 custody inventories are not the exact reviewed path set",
    )
    custody_paths = set(LEAN_CUSTODY_PATHS)
    require(
        custody_paths.isdisjoint(operational)
        and custody_paths.isdisjoint(scientific),
        "Lean r12 custody paths entered an ordinary digest inventory",
    )
    require(
        final_custody[LEAN_CHECKER_RELATIVE] == sha256(lean_checker_raw)
        and final_custody[LEAN_SELF_TEST_RELATIVE] == sha256(lean_self_test_raw)
        and replay_custody[LEAN_SELF_TEST_RELATIVE]
        == final_custody[LEAN_SELF_TEST_RELATIVE],
        "Lean r12 final or replay-time custody changed",
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
        "Lean r12 projection line is not exactly reconstructable",
    )
    replay_checker_raw = lean_checker_raw.replace(
        final_projection_line, placeholder_projection_line, 1
    )
    require(
        replay_custody[LEAN_CHECKER_RELATIVE] == sha256(replay_checker_raw),
        "Lean r12 replay-time checker custody changed",
    )


def validate_fresh_replay_v7(
    c6_entries: dict[str, Any], c7_entries: dict[str, Any]
) -> dict[str, Any]:
    V6.validate_replay_pair(c6_entries)
    require(
        c7_entries.get(R11_RELATIVE) == c6_entries.get(R11_RELATIVE),
        "C7 changed finalized C6-era r11 replay bytes",
    )
    r12_raw = tree_blob(c7_entries, R12_RELATIVE)
    r12 = parse_json(r12_raw, "fresh composite-v7 r12 replay", canonical=False)
    require(
        r12_raw == canonical_json(r12, pretty=True)
        and r12.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and r12.get("status") == "passed"
        and sha256(r12_raw) != R11_SHA256,
        "fresh r12 replay identity, canonical form, or disposition changed",
    )
    prior_hashes = r12.get("prior_replay_preservation_sha256")
    prior_schemas = r12.get("prior_replay_schema")
    require(
        type(prior_hashes) is dict
        and type(prior_schemas) is dict
        and prior_hashes.get(R11_RELATIVE) == R11_SHA256
        and prior_schemas.get(R11_RELATIVE) == "pid-rs/lean-current-project-replay/v2",
        "fresh r12 does not preserve exact finalized r11 predecessor replay",
    )
    r11_raw = tree_blob(c6_entries, R11_RELATIVE)
    r11 = parse_json(r11_raw, "finalized C6-era r11 replay", canonical=False)
    operational = r12.get("operational_wiring_sha256")
    require(type(operational) is dict, "fresh r12 operational wiring map is malformed")
    for path in R12_REQUIRED_OPERATIONAL_PATHS:
        raw = tree_blob(c7_entries, path)
        require(
            operational.get(path) == sha256(raw),
            f"fresh r12 does not bind exact C7 operational wiring: {path}",
        )
    v7_checker_raw = tree_blob(c7_entries, CHECKER_RELATIVE)
    lean_checker_raw = tree_blob(c7_entries, LEAN_CHECKER_RELATIVE)
    lean_self_test_raw = tree_blob(c7_entries, LEAN_SELF_TEST_RELATIVE)
    projection = validate_lean_r12_checksum_cut_v7(
        v7_checker_raw, lean_checker_raw
    )
    validate_lean_r12_receipt_cuts_v7(
        v7_checker_raw,
        lean_checker_raw,
        lean_self_test_raw,
        r11,
        r12,
        projection,
    )
    V6._v5._v4.validate_current_source(c7_entries, "C7")
    return {
        "current_r12": tree_descriptor(c7_entries, R12_RELATIVE),
        "current_source": tree_descriptor(c7_entries, CURRENT_SOURCE_RELATIVE),
        "predicate": "fresh_post_c6_r12_and_current_source_match_c7",
        "retained_r11": tree_descriptor(c7_entries, R11_RELATIVE),
    }


def publication_binding_v7(c7_entries: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "validated"}
    executable_paths = {
        "scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh",
        "scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh",
    }
    for field, path in PUBLICATION_FIELDS.items():
        expected_mode = "100755" if path in executable_paths else "100644"
        require(
            path in c7_entries and c7_entries[path].mode == expected_mode,
            f"C7 publication path is absent or wrong mode: {path}",
        )
        result[field] = tree_descriptor(c7_entries, path)
    return result


def derive_receipt_v7(
    predecessor_raw: bytes,
    local_raw: bytes,
    successor_raw: bytes,
    c6_entries: dict[str, Any],
    c7_entries: dict[str, Any],
    c7: str,
    c7_tree: str,
    capture_schema: dict[str, Any],
    local_schema: dict[str, Any],
    c7_policy_rows: tuple[tuple[str, str, str, str], ...],
) -> dict[str, Any]:
    require(
        predecessor_raw == tree_blob(c7_entries, PREDECESSOR_CAPTURE_RELATIVE),
        "receipt predecessor input differs from the exact C7 capture blob",
    )
    predecessor, predecessor_domains = derive_phase_with_domains_v7(
        predecessor_raw,
        "predecessor_failure",
        c7_entries,
        c7,
        c7_tree,
        capture_schema,
    )
    successor, successor_domains = derive_phase_with_domains_v7(
        successor_raw,
        "successor_qualification",
        c7_entries,
        c7,
        c7_tree,
        capture_schema,
    )
    validate_identifier_domains_v7([*predecessor_domains, *successor_domains])
    local_qualification = derive_local_qualification_v7(
        local_raw, c7_entries, c7, c7_tree, local_schema
    )
    value = {
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
        "contract_authorities": contract_authorities_v7(
            c6_entries, c7_entries, c7_policy_rows
        ),
        "defects": [
            {
                "evidence": [tree_descriptor(c7_entries, PREDECESSOR_CAPTURE_RELATIVE)],
                "id": "c6_hosted_missing_rg",
                "scope": "hosted_dependency_closure",
                "status": "failed_zero_credit",
            },
            {
                "evidence": [tree_descriptor(c7_entries, COUNTEREXAMPLE_RELATIVE)],
                "id": "c6_local_authority_bound_contradiction",
                "scope": "immutable_local_recorder",
                "status": "impossible_zero_credit",
            },
        ],
        "local_qualification": local_qualification,
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "observations": [predecessor, successor],
        "publication": publication_binding_v7(c7_entries),
        "replay": validate_fresh_replay_v7(c6_entries, c7_entries),
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v7",
        "schema_revision": 7,
        "subject": {
            "c6_commit": C6_COMMIT,
            "c6_tree": C6_TREE,
            "c7_commit": c7,
            "c7_tree": c7_tree,
        },
        "verdict": {
            "c6_hosted_qualification": "failed_zero_credit",
            "c6_local_qualification": "impossible_zero_credit",
            "c6_publication": "published_unchanged",
            "c7_bounded_repair": "pass",
            "c7_hosted_observation": "pass",
            "c7_local_qualification": "pass",
            "r4_receipt_issued": False,
            "r5_receipt_issued": False,
            "r6_receipt_issued": False,
            "r7_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
    }
    validate_receipt_semantics(value)
    return value


def validate_receipt_semantics(value: dict[str, Any]) -> None:
    require(
        value.get("schema") == "pid-rs/ksg-rev4-m1a-composite-receipt/v7"
        and value.get("schema_revision") == 7
        and value.get("repository") == REPOSITORY
        and value.get("nonimplications") == RECEIPT_NONIMPLICATIONS,
        "v7 receipt root semantics changed",
    )
    subject = value["subject"]
    require(
        subject["c6_commit"] == C6_COMMIT
        and subject["c6_tree"] == C6_TREE
        and SHA1_RE.fullmatch(subject["c7_commit"]) is not None
        and SHA1_RE.fullmatch(subject["c7_tree"]) is not None,
        "v7 receipt subject changed",
    )
    require(
        [(item["phase"], item["path"]) for item in value["capture_bindings"]]
        == [
            ("predecessor_failure", PREDECESSOR_CAPTURE_RELATIVE),
            ("successor_qualification", SUCCESSOR_CAPTURE_RELATIVE),
        ],
        "v7 receipt capture-binding order changed",
    )
    require(
        value["local_qualification"]["record_binding"]["path"] == LOCAL_RECORD_RELATIVE
        and value["local_qualification"]["subject"]
        == {"c7_commit": subject["c7_commit"], "c7_tree": subject["c7_tree"]},
        "v7 receipt local qualification changed",
    )
    defects = value["defects"]
    require(
        [(item["id"], item["scope"], item["status"]) for item in defects]
        == [
            ("c6_hosted_missing_rg", "hosted_dependency_closure", "failed_zero_credit"),
            (
                "c6_local_authority_bound_contradiction",
                "immutable_local_recorder",
                "impossible_zero_credit",
            ),
        ]
        and [[binding["path"] for binding in item["evidence"]] for item in defects]
        == [[PREDECESSOR_CAPTURE_RELATIVE], [COUNTEREXAMPLE_RELATIVE]],
        "v7 receipt two-defect mapping changed",
    )
    observations = value["observations"]
    predecessor_roles = observations[0]["roles"]
    successor_roles = observations[1]["roles"]
    require(
        [item["phase"] for item in observations]
        == ["predecessor_failure", "successor_qualification"]
        and [[role["role"] for role in item["roles"]] for item in observations]
        == [
            ["predecessor_ci", "predecessor_codeql", "predecessor_contract"],
            ["successor_ci", "successor_codeql", "successor_contract"],
        ],
        "v7 receipt observation phase/role order changed",
    )
    require(
        [item["conclusion"] for item in predecessor_roles]
        == ["failure", "success", "failure"]
        and all(item["conclusion"] == "success" for item in successor_roles)
        and all(
            (item["failed_job_ids"] != []) == (item["conclusion"] == "failure")
            for item in (*predecessor_roles, *successor_roles)
        )
        and [item["workflow_path"] for item in predecessor_roles]
        == [CI_RELATIVE, "dynamic/github-code-scanning/codeql", V6_WORKFLOW_RELATIVE]
        and [item["workflow_path"] for item in successor_roles]
        == [CI_RELATIVE, "dynamic/github-code-scanning/codeql", V7_WORKFLOW_RELATIVE]
        and predecessor_roles[1]["run_id"] == C6_CODEQL_RUN
        and predecessor_roles[2]["run_id"] == C6_CONTRACT_RUN
        and predecessor_roles[0]["failed_job_ids"] == [C6_CI_FAILED_JOB]
        and predecessor_roles[2]["failed_job_ids"] == [C6_CONTRACT_FAILED_JOB]
        and predecessor_roles[0]["run_id"] == C6_CI_RUN
        and len(
            {
                item["run_id"]
                for item in (*predecessor_roles, *successor_roles)
            }
        )
        == 6,
        "v7 receipt hosted qualification truth values or identifier joins changed",
    )
    replay = value["replay"]
    require(
        replay["retained_r11"]["path"] == R11_RELATIVE
        and replay["current_r12"]["path"] == R12_RELATIVE
        and replay["current_source"]["path"] == CURRENT_SOURCE_RELATIVE
        and replay["predicate"] == "fresh_post_c6_r12_and_current_source_match_c7",
        "v7 receipt fresh replay binding changed",
    )
    publication = value["publication"]
    require(
        publication["status"] == "validated"
        and all(publication[field]["path"] == path for field, path in PUBLICATION_FIELDS.items()),
        "v7 receipt publication binding changed",
    )
    require(
        value["verdict"]
        == {
            "c6_hosted_qualification": "failed_zero_credit",
            "c6_local_qualification": "impossible_zero_credit",
            "c6_publication": "published_unchanged",
            "c7_bounded_repair": "pass",
            "c7_hosted_observation": "pass",
            "c7_local_qualification": "pass",
            "r4_receipt_issued": False,
            "r5_receipt_issued": False,
            "r6_receipt_issued": False,
            "r7_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
        "v7 receipt verdict changed",
    )
    authorities = value["contract_authorities"]
    require(
        authorities == sorted(authorities, key=lambda item: (item["path"], item["role"]))
        and len({(item["path"], item["role"]) for item in authorities}) == len(authorities),
        "v7 receipt authority ordering changed",
    )


def worktree_changes() -> dict[str, str]:
    raw = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    result: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if record == b"":
            continue
        require(len(record) >= 4 and record[2:3] == b" ", "unsupported worktree status record")
        status_text = record[:2].decode("ascii")
        require(status_text in {" M", "M ", "A ", "??"}, "draft contains a rename, delete, conflict, or unsupported status")
        try:
            path = record[3:].decode("utf-8")
        except UnicodeDecodeError:
            raise ContractError("draft worktree path is not UTF-8") from None
        require(path not in result, f"duplicate draft worktree path: {path}")
        result[path] = status_text
    return result


def validate_policy_draft() -> dict[str, Any]:
    policy = parse_json(read_file(POLICY_RELATIVE), "composite-v7 draft path policy")
    validate_policy_value(policy)
    return policy


def validate_policy_value(
    policy: dict[str, Any],
) -> tuple[tuple[str, str, str, str], ...] | None:
    expected_local = {
        "authority_stream_cap_bytes": 65_536,
        "first_oversize_authority": "scripts/check-ksg-m1a-composite-v6-self-test.py",
        "machine_counterexample": {
            "path": COUNTEREXAMPLE_RELATIVE,
            "schema_path": COUNTEREXAMPLE_SCHEMA_RELATIVE,
            "schema_sha256": COUNTEREXAMPLE_SCHEMA_SHA256,
            "schema_size_bytes": COUNTEREXAMPLE_SCHEMA_SIZE_BYTES,
            "sha256": COUNTEREXAMPLE_SHA256,
            "size_bytes": COUNTEREXAMPLE_SIZE_BYTES,
        },
        "machine_counterexample_state": "present_exact_bound",
        "oversize_authorities": [
            {
                "path": C6_LOCAL_AUTHORITIES[3][0],
                "sha256": C6_LOCAL_AUTHORITIES[3][2],
                "size_bytes": C6_LOCAL_AUTHORITIES[3][3],
            },
            {
                "path": C6_LOCAL_AUTHORITIES[4][0],
                "sha256": C6_LOCAL_AUTHORITIES[4][2],
                "size_bytes": C6_LOCAL_AUTHORITIES[4][3],
            },
        ],
        "status": "unsatisfiable_exact_byte_equality_under_internal_stream_cap",
    }
    ci_job_name, ci_failed_steps = PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[
        "predecessor_ci"
    ][C6_CI_FAILED_JOB]
    require(len(ci_failed_steps) == 1, "predecessor CI failed-step identity changed")
    ci_step_number, ci_step_name = ci_failed_steps[0]
    expected_ci = {
        "attempt": 1,
        "branch": "main",
        "conclusion": "failure",
        "event": "push",
        "diagnostic": C6_MISSING_RG_DIAGNOSTIC,
        "failed_job": C6_CI_FAILED_JOB,
        "failed_job_name": ci_job_name,
        "failed_step": {
            "name": ci_step_name,
            "number": ci_step_number,
        },
        "job_count": 45,
        "repository_id": C6_REPOSITORY_ID,
        "run": C6_CI_RUN,
        "status": "completed",
        "successful_jobs": 44,
        "terminal_at": C6_CI_UPDATED_AT,
        "workflow_sha256": "61283264499a7b6069a4e5e9563c72541ab101b69379f3ace75a12cd4bf4b175",
        "workflow_size_bytes": 68_913,
    }
    expected_predecessor_capture = {
        "normalized_sha256": PREDECESSOR_NORMALIZED_SHA256,
        "path": PREDECESSOR_CAPTURE_RELATIVE,
        "response_rows": 36,
        "retry_events": 0,
        "sha256": PREDECESSOR_CAPTURE_SHA256,
        "size_bytes": PREDECESSOR_CAPTURE_SIZE_BYTES,
        "state": "present_exact_bound",
    }
    require(
        type(policy) is dict
        and set(policy)
        == {
            "base",
            "c6_disposition",
            "c7",
            "nonimplications",
            "r7",
            "repository",
            "reserved_absent_paths",
            "schema",
            "schema_revision",
        }
        and policy["schema"] == "pid-rs/ksg-m1a-composite-v7-path-policy"
        and policy["schema_revision"] == 1
        and policy["repository"] == REPOSITORY
        and policy["base"]
        == {
            "commit": C6_COMMIT,
            "message": C6_MESSAGE,
            "parent": C6_PARENT,
            "r4_status": "permanently_unissued",
            "r5_status": "permanently_unissued",
            "r6_status": "permanently_unissued",
            "tree": C6_TREE,
        }
        and policy["r7"]
        == {
            "delta": R7_POLICY_ROWS,
            "direct_parent_role": "c7_bounded_operational_repair",
            "message": R7_MESSAGE,
        }
        and policy["nonimplications"] == POLICY_NONIMPLICATIONS,
        "draft path-policy identity or unresolved state changed",
    )
    c7 = exact_keys(
        policy["c7"],
        {"delta", "delta_state", "direct_parent", "message", "tree", "tree_state"},
        "composite-v7 policy C7",
    )
    require(
        c7["direct_parent"] == C6_COMMIT and c7["message"] == C7_MESSAGE,
        "composite-v7 policy C7 parent or message changed",
    )
    if c7["delta_state"] == "unresolved_until_publication_and_r12":
        require(
            c7["delta"] is None
            and c7["tree"] is None
            and c7["tree_state"] == "unresolved_until_c7_commit",
            "draft C7 policy placeholders changed",
        )
        c7_rows = None
    else:
        require(
            c7["delta_state"] == "frozen_exact_rows"
            and c7["tree"] is None
            and c7["tree_state"] == "derived_from_c7_commit_not_embedded"
            and FROZEN_C7_POLICY_ROWS != (),
            "final C7 policy state or checker row freeze is absent",
        )
        c7_rows = policy_rows_v7(c7["delta"], "composite-v7 policy C7 delta")
        require(c7_rows == FROZEN_C7_POLICY_ROWS, "final C7 policy rows changed")
    reserved = policy.get("reserved_absent_paths", {})
    expected_reserved = {
        "legacy_receipts": list(FORBIDDEN_EVIDENCE_PATHS),
        "publication": sorted(PUBLICATION_PATHS) if c7_rows is None else [],
        "replay_and_hosted": RESERVED_REPLAY_PATHS if c7_rows is None else [],
    }
    require(reserved == expected_reserved, "C7 permanent/reserved absence inventory changed")
    hosted = policy["c6_disposition"]
    require(
        set(hosted)
        == {
            "codeql_attempt_1",
            "dedicated_attempt_1",
            "local_recorder",
            "predecessor_capture",
            "repository_ci_attempt_1",
        }
        and hosted["codeql_attempt_1"] == {"conclusion": "success", "run": C6_CODEQL_RUN}
        and hosted["dedicated_attempt_1"]
        == {
            "conclusion": "failure",
            "diagnostic": C6_MISSING_RG_DIAGNOSTIC,
            "job": C6_CONTRACT_FAILED_JOB,
            "run": C6_CONTRACT_RUN,
            "workflow_sha256": "41d5c0f2000c26f35b0a703890dfcf86a9da91bb00b51b65e0570cfb0df39791",
            "workflow_size_bytes": 6_696,
        }
        and hosted["local_recorder"] == expected_local
        and hosted["predecessor_capture"] == expected_predecessor_capture
        and hosted["repository_ci_attempt_1"] == expected_ci,
        "draft C6 hosted disposition changed",
    )
    return c7_rows


def validate_allowed_draft_paths_v7(
    paths: set[str], allowed_paths: frozenset[str] = DRAFT_ALLOWED_PATHS
) -> None:
    """Apply the independently hostile-tested C7 editing-scope subset guard."""

    require(
        paths <= allowed_paths,
        "draft contains a path outside the approved C7 scope",
    )


def validate_draft() -> dict[str, Any]:
    _commit, c6_entries = c6_anchor()
    changes = worktree_changes()
    validate_allowed_draft_paths_v7(set(changes))
    require(REQUIRED_CORE_DRAFT_PATHS <= set(changes), "draft core path inventory is incomplete")
    exact_file(V6_CHECKER_RELATIVE, V6_CHECKER_SHA256, V6_CHECKER_SIZE_BYTES)
    exact_file(R11_RELATIVE, R11_SHA256, R11_SIZE_BYTES)
    counterexample = validate_counterexample(c6_entries)
    capture_schema = validate_schema_file(CAPTURE_SCHEMA_RELATIVE, CAPTURE_SCHEMA_RELATIVE)
    validate_schema_file(LOCAL_SCHEMA_RELATIVE, LOCAL_SCHEMA_RELATIVE)
    validate_schema_file(RECEIPT_SCHEMA_RELATIVE, RECEIPT_SCHEMA_RELATIVE)
    ci_raw = read_file(CI_RELATIVE)
    v7_raw = read_file(V7_WORKFLOW_RELATIVE)
    retired_v6_raw = read_file(V6_WORKFLOW_RELATIVE)
    validate_workflows(ci_raw, v7_raw, retired_v6_raw)
    validate_local_repair_source(read_file(LOCAL_TOOL_RELATIVE))
    capture_tool_raw = read_file(CAPTURE_TOOL_RELATIVE)
    validate_capture_source(capture_tool_raw)
    predecessor_raw = read_file(
        PREDECESSOR_CAPTURE_RELATIVE, V6.MAX_JSON_BYTES, mode=0o644
    )
    require(
        len(predecessor_raw) == PREDECESSOR_CAPTURE_SIZE_BYTES
        and sha256(predecessor_raw) == PREDECESSOR_CAPTURE_SHA256,
        "installed predecessor capture exact bytes changed",
    )
    predecessor_observation = derive_phase_v7(
        predecessor_raw,
        "predecessor_failure",
        {},
        C6_COMMIT,
        C6_TREE,
        capture_schema,
        {
            "path": CAPTURE_TOOL_RELATIVE,
            "sha256": CAPTURE_TOOL_SHA256,
            "size_bytes": CAPTURE_TOOL_SIZE_BYTES,
        },
    )
    require(
        predecessor_observation["capture_sha256"] == PREDECESSOR_CAPTURE_SHA256
        and predecessor_observation["normalized_sha256"]
        == PREDECESSOR_NORMALIZED_SHA256,
        "installed predecessor capture normalized projection changed",
    )
    validate_justfile_values(read_file(JUSTFILE_RELATIVE), require_publication=False)
    policy = validate_policy_draft()
    require(
        all(
            not (ROOT / path).exists() and not (ROOT / path).is_symlink()
            for path in (R12_RELATIVE,)
        ),
        "r12 appeared before the fresh-replay freeze",
    )
    require(
        all(not (ROOT / path).exists() and not (ROOT / path).is_symlink() for path in FORBIDDEN_EVIDENCE_PATHS),
        "a permanently forbidden R4/R5/R6 evidence path appeared",
    )
    return {
        "c6_commit": C6_COMMIT,
        "counterexample_canonical_projection_sha256": sha256(
            canonical_json(counterexample, pretty=False)
        ),
        "counterexample_schema_sha256": COUNTEREXAMPLE_SCHEMA_SHA256,
        "counterexample_sha256": COUNTEREXAMPLE_SHA256,
        "draft_changed_paths": sorted(changes),
        "policy_state": policy["c7"]["delta_state"],
        "predecessor_capture_sha256": PREDECESSOR_CAPTURE_SHA256,
        "predecessor_normalized_sha256": PREDECESSOR_NORMALIZED_SHA256,
        "publication_paths_present": sum((ROOT / path).is_file() for path in PUBLICATION_PATHS),
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v7-draft-validation/v1",
        "terminal_c6_ci_bound": True,
    }


def schemas_from_c7_tree(
    c7_entries: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for path in (CAPTURE_SCHEMA_RELATIVE, LOCAL_SCHEMA_RELATIVE, RECEIPT_SCHEMA_RELATIVE):
        require(c7_entries.get(path) is not None and c7_entries[path].mode == "100644", f"C7 schema mode changed: {path}")
        raw = tree_blob(c7_entries, path)
        schema = parse_json(raw, f"C7 schema {path}")
        validate_schema_value(schema, path, path)
        values.append(schema)
    return values[0], values[1], values[2]


def validate_frozen_c7_path_bindings(c7_entries: dict[str, Any]) -> None:
    required = {
        CI_RELATIVE,
        V6_WORKFLOW_RELATIVE,
        V7_WORKFLOW_RELATIVE,
        JUSTFILE_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        LOCAL_TOOL_RELATIVE,
        LOCAL_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_RELATIVE,
        SELF_TEST_RELATIVE,
        COUNTEREXAMPLE_RELATIVE,
        COUNTEREXAMPLE_SCHEMA_RELATIVE,
        PREDECESSOR_CAPTURE_RELATIVE,
        "scripts/check-formal-pdf-set.sh",
        "scripts/check-formal-pdf-style.py",
        *PUBLICATION_FIELDS.values(),
    }
    require(
        set(FROZEN_C7_PATH_BINDINGS) == required,
        "final acyclic C7 exact path-binding inventory is not frozen",
    )
    for path, (digest, size, mode) in FROZEN_C7_PATH_BINDINGS.items():
        raw = tree_blob(c7_entries, path)
        require(
            SHA256_RE.fullmatch(digest) is not None
            and type(size) is int
            and size > 0
            and mode in {"100644", "100755"}
            and c7_entries[path].mode == mode
            and len(raw) == size
            and sha256(raw) == digest,
            f"frozen C7 exact path bytes changed: {path}",
        )


def ancestry_commits_v7(start: str, head: str) -> list[str]:
    if start == head:
        return [start]
    raw = git("rev-list", "--reverse", "--ancestry-path", f"{start}..{head}")
    try:
        descendants = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"C7 descendant history is not ASCII: {error}") from None
    require(descendants != [] and descendants[-1] == head, "HEAD is not on the C7 ancestry path")
    return [start, *descendants]


def new_reachable_commits_v7(start: str, head: str) -> list[str]:
    raw = git("rev-list", "--reverse", f"{start}..{head}")
    try:
        commits = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"new C7 reachable history is not ASCII: {error}") from None
    require(all(SHA1_RE.fullmatch(item) is not None for item in commits), "new C7 history contains malformed commit IDs")
    return [start, *commits]


def all_reachable_commits_v7(head: str) -> list[str]:
    raw = git("rev-list", "--reverse", head)
    try:
        commits = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"reachable history is not ASCII: {error}") from None
    require(
        commits != []
        and commits[-1] == head
        and all(SHA1_RE.fullmatch(item) is not None for item in commits),
        "reachable history contains malformed commit IDs",
    )
    return commits


def descendant_message_v7(oid: str) -> str:
    raw = V6._v5._v4.exact_object(oid, "commit", maximum=1024 * 1024)
    _headers, separator, message_raw = raw.partition(b"\n\n")
    require(separator == b"\n\n", f"descendant commit message envelope changed at {oid[:12]}")
    try:
        return message_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"descendant commit message is not UTF-8 at {oid[:12]}: {error}") from None


def validate_forbidden_state_v7(
    present_paths: set[str], message: str, oid: str, c7: str, r7: str | None
) -> None:
    require(
        present_paths.isdisjoint(FORBIDDEN_EVIDENCE_PATHS),
        f"forbidden R4/R5/R6 evidence path appeared at {oid[:12]}",
    )
    require(message not in FORBIDDEN_MESSAGES, "forbidden R4/R5/R6 receipt message appeared")
    require(message != C7_MESSAGE or oid == c7, "C7 message appeared outside the exact C7 commit")
    require(message != R7_MESSAGE or (r7 is not None and oid == r7), "R7 message appeared outside the exact R7 commit")


def validate_forbidden_history_v7(head: str, c7: str, r7: str | None) -> None:
    pathspecs = tuple(f":(literal){path}" for path in FORBIDDEN_EVIDENCE_PATHS)
    for oid in all_reachable_commits_v7(head):
        forbidden_rows = git("ls-tree", "-z", "--name-only", oid, "--", *pathspecs)
        try:
            present_paths = {
                item.decode("utf-8") for item in forbidden_rows.split(b"\0") if item
            }
        except UnicodeDecodeError as error:
            raise ContractError(f"forbidden-path history output is not UTF-8: {error}") from None
        message = descendant_message_v7(oid)
        validate_forbidden_state_v7(present_paths, message, oid, c7, r7)


def validate_retention_history_v7(
    head: str,
    c7: str,
    r7: str | None,
    c6_entries: dict[str, Any],
    c7_entries: dict[str, Any],
    c7_policy_rows: tuple[tuple[str, str, str, str], ...],
) -> None:
    c6_retained_paths = set(IMMUTABLE_C6_AUTHORITIES) | {
        path for path, _mode, _role in V6.PROCESS_ARTIFACTS
    }
    r7_entries = None if r7 is None else parse_tree(parse_commit(r7).tree)
    r7_added_paths = {
        row["path"] for row in R7_POLICY_ROWS if row["status"] == "A"
    }
    for oid in new_reachable_commits_v7(C6_COMMIT, head):
        tree = C6_TREE if oid == C6_COMMIT else V6.parse_descendant_tree(oid)
        entries = parse_tree(tree)
        c7_reachable = V6.git_predicate("merge-base", "--is-ancestor", c7, oid)
        r7_reachable = r7 is not None and V6.git_predicate(
            "merge-base", "--is-ancestor", r7, oid
        )
        for path in c6_retained_paths:
            require(
                entries.get(path) == c6_entries.get(path),
                f"HEAD-reachable history changed retained C6 bytes at {oid[:12]}: {path}",
            )
        if not c7_reachable:
            validate_pre_c7_reachable_state_v7(oid, tree, entries, c6_entries)
            continue
        for path, _status, _mode, _role in c7_policy_rows:
            if path != CURRENT_SOURCE_RELATIVE:
                require(
                    entries.get(path) == c7_entries.get(path),
                    f"HEAD-reachable history changed retained C7 authority at {oid[:12]}: {path}",
                )
        V6._v5._v4.validate_current_source(entries, f"C7-reachable commit {oid[:12]}")
        if not r7_reachable:
            require(
                all(path not in entries for path in r7_added_paths),
                f"R7 evidence appeared before the exact R7 commit at {oid[:12]}",
            )
            continue
        require(r7_entries is not None, "R7 retention state is internally inconsistent")
        for row in R7_POLICY_ROWS:
            if row["path"] != CURRENT_SOURCE_RELATIVE:
                require(
                    entries.get(row["path"]) == r7_entries.get(row["path"]),
                    f"HEAD-reachable history changed R7 receipt-cut authority at {oid[:12]}: {row['path']}",
                )


def validate_pre_c7_reachable_state_v7(
    oid: str,
    tree: str,
    entries: dict[str, Any],
    c6_entries: dict[str, Any],
) -> None:
    require(
        oid == C6_COMMIT and tree == C6_TREE and entries == c6_entries,
        "HEAD-reachable pre-C7 side history is not the exact published C6 commit and tree",
    )


def validate_c7_contract_sources(
    c6_entries: dict[str, Any], c7_entries: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_frozen_c7_path_bindings(c7_entries)
    validate_workflows(
        tree_blob(c7_entries, CI_RELATIVE),
        tree_blob(c7_entries, V7_WORKFLOW_RELATIVE),
        tree_blob(c7_entries, V6_WORKFLOW_RELATIVE),
    )
    validate_justfile_values(tree_blob(c7_entries, JUSTFILE_RELATIVE), require_publication=True)
    validate_capture_source(tree_blob(c7_entries, CAPTURE_TOOL_RELATIVE))
    validate_local_repair_source(tree_blob(c7_entries, LOCAL_TOOL_RELATIVE))
    validate_counterexample_pair_bytes(
        tree_blob(c7_entries, COUNTEREXAMPLE_SCHEMA_RELATIVE),
        tree_blob(c7_entries, COUNTEREXAMPLE_RELATIVE),
        c6_entries,
    )
    schemas = schemas_from_c7_tree(c7_entries)
    publication_binding_v7(c7_entries)
    validate_fresh_replay_v7(c6_entries, c7_entries)
    return schemas


def validate_exact_c7_delta_v7(
    actual: tuple[tuple[str, str, str], ...],
    policy_rows: tuple[tuple[str, str, str, str], ...],
) -> None:
    require(
        actual
        == tuple(
            (path, status, mode)
            for path, status, mode, _role in policy_rows
        ),
        "C6 to C7 delta differs from the exact frozen policy rows",
    )


def validate_topology_v7() -> dict[str, Any]:
    require(C6_CI_RUN > 0, "terminal C6 CI roster remains unresolved")
    _c6_commit, c6_entries = c6_anchor()
    head, head_tree = V6.validate_repository()
    head_entries = parse_tree(head_tree)
    receipt_present = RECEIPT_RELATIVE in head_entries
    if receipt_present:
        r7 = V6._v5._v4.commit_introducing(RECEIPT_RELATIVE)
        r7_commit = parse_commit(r7)
        require(r7_commit.message == R7_MESSAGE, "R7 exact message changed")
        c7 = r7_commit.parent
    else:
        r7 = None
        c7 = head
    c7_commit = parse_commit(c7)
    require(
        c7_commit.parent == C6_COMMIT and c7_commit.message == C7_MESSAGE,
        "C7 is not the exact unsigned direct child of published C6",
    )
    c7_tree = c7_commit.tree
    c7_entries = parse_tree(c7_tree)
    policy = parse_json(tree_blob(c7_entries, POLICY_RELATIVE), "composite-v7 final path policy")
    c7_policy_rows = validate_policy_value(policy)
    require(c7_policy_rows is not None, "C7 path rows remain in draft state")
    validate_exact_c7_delta_v7(changed_entries(c6_entries, c7_entries), c7_policy_rows)
    for path, _status, mode, _role in c7_policy_rows:
        require(c7_entries.get(path) is not None and c7_entries[path].mode == mode, f"C7 policy path is absent or wrong mode: {path}")
    require(
        PREDECESSOR_CAPTURE_RELATIVE in c7_entries
        and R12_RELATIVE in c7_entries
        and CURRENT_SOURCE_RELATIVE in c7_entries
        and all(path in c7_entries for path in PUBLICATION_FIELDS.values())
        and LOCAL_RECORD_RELATIVE not in c7_entries
        and SUCCESSOR_CAPTURE_RELATIVE not in c7_entries
        and RECEIPT_RELATIVE not in c7_entries,
        "C7 predecessor/replay/publication versus R7 phase separation changed",
    )
    c6_retained_paths = set(IMMUTABLE_C6_AUTHORITIES) | {
        path for path, _mode, _role in V6.PROCESS_ARTIFACTS
    }
    for path in c6_retained_paths:
        require(c7_entries.get(path) == c6_entries.get(path), f"C7 changed retained published C6 bytes: {path}")
    schemas = validate_c7_contract_sources(c6_entries, c7_entries)
    derive_phase_v7(
        tree_blob(c7_entries, PREDECESSOR_CAPTURE_RELATIVE),
        "predecessor_failure",
        c7_entries,
        c7,
        c7_tree,
        schemas[0],
    )
    require(
        read_file(CHECKER_RELATIVE, mode=0o644) == tree_blob(c7_entries, CHECKER_RELATIVE),
        "executing composite-v7 checker bytes differ from the C7 authority blob",
    )
    validate_forbidden_history_v7(head, c7, r7)
    if r7 is None:
        require(head == c7, "receipt-absent state is not exact C7")
    else:
        require(V6.git_predicate("merge-base", "--is-ancestor", r7, head), "R7 is not an ancestor of HEAD")
        r7_commit = parse_commit(r7)
        require(r7_commit.parent == c7 and r7_commit.message == R7_MESSAGE, "R7 is not the exact direct C7 child")
        r7_entries = parse_tree(r7_commit.tree)
        expected_r7_delta = tuple((row["path"], row["status"], row["mode"]) for row in R7_POLICY_ROWS)
        require(changed_entries(c7_entries, r7_entries) == expected_r7_delta, "C7 to R7 delta is not the exact four-row receipt cut")
        V6._v5._v4.validate_current_source(r7_entries, "R7")
    validate_retention_history_v7(
        head, c7, r7, c6_entries, c7_entries, c7_policy_rows
    )
    V6.validate_worktree(head_entries, head, head_tree)
    return {
        "c6_entries": c6_entries,
        "c7": c7,
        "c7_entries": c7_entries,
        "c7_policy_rows": c7_policy_rows,
        "c7_tree": c7_tree,
        "head": head,
        "head_entries": head_entries,
        "head_tree": head_tree,
        "r7": r7,
        "schemas": schemas,
    }


def validate_receipt_bytes_v7(receipt_raw: bytes, topology: dict[str, Any]) -> dict[str, Any]:
    require(receipt_raw == canonical_json(parse_json(receipt_raw, "composite-v7 receipt", canonical=False), pretty=True), "composite-v7 receipt is not canonical pretty JSON")
    receipt = parse_json(receipt_raw, "composite-v7 receipt", canonical=False)
    validate_schema_instance(receipt, topology["schemas"][2], "composite-v7 receipt")
    r7 = topology["r7"]
    require(r7 is not None, "receipt derivation comparison requires R7")
    r7_entries = parse_tree(parse_commit(r7).tree)
    expected = derive_receipt_v7(
        tree_blob(topology["c7_entries"], PREDECESSOR_CAPTURE_RELATIVE),
        tree_blob(r7_entries, LOCAL_RECORD_RELATIVE),
        tree_blob(r7_entries, SUCCESSOR_CAPTURE_RELATIVE),
        topology["c6_entries"],
        topology["c7_entries"],
        topology["c7"],
        topology["c7_tree"],
        topology["schemas"][0],
        topology["schemas"][1],
        topology["c7_policy_rows"],
    )
    require(receipt == expected, "composite-v7 receipt differs from exact raw-evidence derivation")
    return receipt


def static_result_v7(topology: dict[str, Any], schema: str = "pid-rs/ksg-rev4-m1a-composite-v7-static-validation/v1") -> dict[str, Any]:
    return {
        "c6_commit": C6_COMMIT,
        "c7_commit": topology["c7"],
        "head": topology["head"],
        "r7_commit": topology["r7"],
        "result": "pass",
        "schema": schema,
        "tree": topology["head_tree"],
    }


def validate_static() -> dict[str, Any]:
    topology = validate_topology_v7()
    if topology["r7"] is not None:
        r7_entries = parse_tree(parse_commit(topology["r7"]).tree)
        validate_receipt_bytes_v7(tree_blob(r7_entries, RECEIPT_RELATIVE), topology)
    return static_result_v7(topology)


def bounded_stdin_v7() -> bytes:
    raw = sys.stdin.buffer.read(LOCAL_LIMITS["record_bytes"] + 1)
    require(0 < len(raw) <= LOCAL_LIMITS["record_bytes"], "standard-input receipt size is outside the bound")
    return raw


def bounded_regular_fd_v7(fd: int, label: str, maximum: int) -> tuple[bytes, tuple[int, int]]:
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
    try:
        while remaining:
            chunk = os.read(fd, min(remaining, 1024 * 1024))
            require(chunk != b"", f"{label} descriptor ended early")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(fd, 1) == b"", f"{label} descriptor grew during read")
        after = os.fstat(fd)
    except OSError as error:
        raise ContractError(f"cannot read {label} descriptor: {error}") from None
    identity = (before.st_dev, before.st_ino)
    require_stable_fd_snapshot_v7(fd_snapshot_v7(before), fd_snapshot_v7(after), label)
    return b"".join(chunks), identity


def fd_snapshot_v7(value: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def require_stable_fd_snapshot_v7(
    before: tuple[int, int, int, int, int, int, int],
    after: tuple[int, int, int, int, int, int, int],
    label: str,
) -> None:
    require(before == after, f"{label} descriptor identity changed during read")


def require_distinct_fd_numbers_v7(local_fd: int, successor_fd: int) -> None:
    require(local_fd != successor_fd, "local and successor descriptor numbers must be distinct")


def require_distinct_fd_identities_v7(
    local_identity: tuple[int, int], successor_identity: tuple[int, int]
) -> None:
    require(
        local_identity != successor_identity,
        "local and successor inputs alias the same regular file",
    )


def derive_receipt_command_v7(local_fd: int, successor_fd: int) -> dict[str, Any]:
    require_distinct_fd_numbers_v7(local_fd, successor_fd)
    topology = validate_topology_v7()
    require(topology["r7"] is None and topology["head"] == topology["c7"], "receipt derivation requires exact receipt-absent C7")
    local_raw, local_identity = bounded_regular_fd_v7(local_fd, "local-closure input", LOCAL_LIMITS["record_bytes"])
    successor_raw, successor_identity = bounded_regular_fd_v7(successor_fd, "successor-capture input", V6.MAX_JSON_BYTES)
    require_distinct_fd_identities_v7(local_identity, successor_identity)
    value = derive_receipt_v7(
        tree_blob(topology["c7_entries"], PREDECESSOR_CAPTURE_RELATIVE),
        local_raw,
        successor_raw,
        topology["c6_entries"],
        topology["c7_entries"],
        topology["c7"],
        topology["c7_tree"],
        topology["schemas"][0],
        topology["schemas"][1],
        topology["c7_policy_rows"],
    )
    validate_schema_instance(value, topology["schemas"][2], "derived composite-v7 receipt")
    final = validate_topology_v7()
    require(
        final["r7"] is None
        and (final["head"], final["head_tree"], final["c7"], final["c7_tree"])
        == (topology["head"], topology["head_tree"], topology["c7"], topology["c7_tree"]),
        "repository state changed during receipt derivation",
    )
    return value


def validate_receipt_command_v7() -> dict[str, Any]:
    topology = validate_topology_v7()
    require(topology["r7"] is not None, "receipt validation requires R7 or a retained descendant")
    r7_entries = parse_tree(parse_commit(topology["r7"]).tree)
    receipt_raw = bounded_stdin_v7()
    require(receipt_raw == tree_blob(r7_entries, RECEIPT_RELATIVE), "receipt stdin differs from the exact R7 blob")
    validate_receipt_bytes_v7(receipt_raw, topology)
    return static_result_v7(topology, "pid-rs/ksg-rev4-m1a-composite-v7-receipt-validation/v1")


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
                arguments.local_closure_fd is not None and arguments.successor_capture_fd is not None,
                "receipt derivation requires both bounded evidence descriptors",
            )
        else:
            require(
                arguments.local_closure_fd is None and arguments.successor_capture_fd is None,
                "evidence descriptors are permitted only for receipt derivation",
            )
        if arguments.validate_draft:
            result = validate_draft()
        elif arguments.validate_static:
            result = validate_static()
        elif arguments.derive_receipt:
            result = derive_receipt_command_v7(arguments.local_closure_fd, arguments.successor_capture_fd)
        else:
            result = validate_receipt_command_v7()
        sys.stdout.buffer.write(canonical_json(result, pretty=bool(arguments.derive_receipt)))
        return 0
    except (ContractError, OSError, SyntaxError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
