#!/usr/bin/env python3
"""Validate the append-only KSG M1a composite-v6 correction contract.

The contract preserves the published C5 commit and records its failed hosted
qualification attempt without granting that attempt qualification credit.  It
then permits one exact C6 bounded repair and one exact R6 hosted receipt.  This
is operational evidence only: no PID, estimator, mathematical, security, or
application-validity conclusion is derived here.
"""

from __future__ import annotations

import argparse
import base64
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
from typing import Any


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v6.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"

C5_COMMIT = "be862b155d710573ec95356fc1cbe9a96a2b83b9"
C5_TREE = "37ae61554284a2fabb460d3a20a731b6ade5f8f4"
C5_PARENT = "da253576a5f76e99633fff4de5cf1118f967b90d"
C5_MESSAGE = "Repair KSG M1a composite v5 contract\n"
C5_IDENTITY = (
    b"author Sepehr Mahmoudian <sepmhn@gmail.com> 1787034072 +0200",
    b"committer Sepehr Mahmoudian <sepmhn@gmail.com> 1787034072 +0200",
)
C6_MESSAGE = "Repair KSG M1a composite v6 contract\n"
R6_MESSAGE = "Record KSG M1a composite v6 receipt\n"
FORBIDDEN_R5_MESSAGE = "Record KSG M1a composite v5 receipt\n"
FORBIDDEN_R4_MESSAGE = "Record KSG M1a composite v4 receipt\n"

CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v6.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v6-self-test.py"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v6.py"
CAPTURE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v6.schema.json"
)
LOCAL_CLOSURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v6-local-closure.py"
LOCAL_CLOSURE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json"
)
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v6.schema.json"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v6-path-policy-v1.json"
PREDECESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-"
    "hosted-capture-v6-2026-08-18.json"
)
SUCCESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v6-2026-08-18.json"
)
LOCAL_CLOSURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v6-2026-08-18.json"
)
RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v6-2026-08-18.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
LEAN_R10_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r10.json"
)
LEAN_R11_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r11.json"
)
LEAN_CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
JUSTFILE_RELATIVE = "justfile"
V5_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v5.yml"
V6_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v6.yml"
CURRENT_HOSTED_RECOVERY_SELF_TEST_RELATIVE = (
    "scripts/check-ksg-m1a-hosted-recovery-self-test.py"
)
CURRENT_HOSTED_RECOVERY_CHECKER_RELATIVE = "scripts/check-ksg-m1a-hosted-recovery.py"
PROCESS_ARTIFACTS = (
    (
        "audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md",
        "100644",
        "operational_boundary_record",
    ),
    (
        "audit/evidence/ksg-rev4-m1a-composite-v6-boundary-visual-receipt-2026-08-18.md",
        "100644",
        "operational_boundary_visual_receipt",
    ),
    (
        "audit/formal/latex/ksg-m1a-composite-v6-boundary.tex",
        "100644",
        "operational_boundary_latex_source",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.svg",
        "100644",
        "operational_boundary_vector_source",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf",
        "100644",
        "operational_boundary_vector_derivative",
    ),
    (
        "output/pdf/ksg-m1a-composite-v6-boundary.pdf",
        "100644",
        "operational_boundary_publication_pdf",
    ),
    (
        "output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv",
        "100644",
        "operational_boundary_rendering_receipt",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh",
        "100755",
        "operational_boundary_pdf_gate",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh",
        "100755",
        "operational_boundary_pdf_gate_self_test",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh",
        "100755",
        "immutable_predecessor_pdf_portability_gate",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh",
        "100755",
        "immutable_predecessor_pdf_portability_hostile_suite",
    ),
)

FORBIDDEN_R5_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v5-2026-08-18.json"
)
FORBIDDEN_R5_RECEIPT_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v5-2026-08-18.json"
)
FORBIDDEN_R5_PATHS = (FORBIDDEN_R5_CAPTURE_RELATIVE, FORBIDDEN_R5_RECEIPT_RELATIVE)
FORBIDDEN_R4_PATHS = (
    "audit/evidence/ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json",
    "audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json",
)
FORBIDDEN_R4_R5_EVIDENCE_PATHS = tuple(
    sorted((*FORBIDDEN_R4_PATHS, *FORBIDDEN_R5_PATHS))
)

V5_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v5.py"
V5_CHECKER_SHA256 = "b510e3e1a9831a41f6904fd9fd259c227c426b11436ead11789a04ad474a8c30"
V5_CHECKER_SIZE_BYTES = 92627
# Finalize this literal only after every non-cut Lean byte, including this
# checker's self-test digest, is frozen.  The r11 generator rejects the zero cut.
EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "9c7796d67aab837955ac43111f1dda4d9ededdc7d835384f8fc30e2b2cd4cf91"
V5_CAPTURE_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v5.py",
    "sha256": "a0e955c9645c852276a3750ee24c49c8feb029d748a73909461d4f71777b3a11",
    "size_bytes": 41566,
}
V5_WORKFLOW_SHA256 = "7f41177c175d785c92512beb23cfd860c5cf94f12dd2a4aa0d4f414963c86593"
V5_WORKFLOW_SIZE_BYTES = 5811
LEAN_R10_SHA256 = "ee8990136f16eda164b97cd6769ddc9cd3ef6446e5d84577d3517d4272df956f"
LEAN_R10_SIZE_BYTES = 135997

# These two byte identities are frozen with the C6 commit.  They intentionally
# bind the retired live v5 trigger and the replacement v6 trigger separately.
RETIRED_V5_WORKFLOW_SHA256 = (
    "7668120a4d4f67db90ae3af0aed048a8ccdf1ae27eb7c96732dfa33852cd14ed"
)
RETIRED_V5_WORKFLOW_SIZE_BYTES = 993
V6_WORKFLOW_SHA256 = "41d5c0f2000c26f35b0a703890dfcf86a9da91bb00b51b65e0570cfb0df39791"
V6_WORKFLOW_SIZE_BYTES = 6696
CURRENT_HOSTED_RECOVERY_SELF_TEST_SHA256 = (
    "0ebd801ce758203ce12111ccec8802bc9a6c68ad80033105abc59f6e60d05787"
)
CURRENT_HOSTED_RECOVERY_SELF_TEST_SIZE_BYTES = 142954
CURRENT_HOSTED_RECOVERY_CHECKER_SHA256 = (
    "7bbbe8d32e4f6ad631f9c2d5074f4a06e7872492945404ad26fd2195664592ee"
)
CURRENT_HOSTED_RECOVERY_CHECKER_SIZE_BYTES = 248343
V6_PDF_PREREQUISITE_BLOCKS = (
    r"""      - name: Install the hash-pinned PDF verifier dependency
        run: |
          python -m pip install \
            --disable-pip-version-check \
            --no-cache-dir \
            --no-deps \
            --require-hashes \
            --requirement audit/formal/requirements-pdf.txt
""".encode("ascii"),
    r"""      - name: Install the runner PDF toolchain
        run: |
          sudo apt-get update
          sudo apt-get install --yes --no-install-recommends \
            chktex \
            fontconfig \
            latexmk \
            lacheck \
            librsvg2-bin \
            libxml2-utils \
            lmodern \
            poppler-utils \
            texlive-fonts-extra \
            texlive-fonts-recommended \
            texlive-latex-extra \
            texlive-luatex \
            texlive-plain-generic
""".encode("ascii"),
)
V6_PUBLICATION_STEP_MARKER = b"      - name: Validate immutable predecessor PDF portability and the bounded successor publication\n"
V6_ATTEMPT_1_REFUSAL_BLOCK = (
    b"      - name: Refuse retries and non-main qualification events\n"
    b"        run: |\n"
    b"          set -euo pipefail\n"
    b'          test "${GITHUB_EVENT_NAME}" = "push"\n'
    b'          test "${GITHUB_REF}" = "refs/heads/main"\n'
    b'          test "${GITHUB_RUN_ATTEMPT}" = "1"\n'
)
V6_PORTABILITY_BLOCK = (
    b"          scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --cross-toolchain\n"
    b"          scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --cross-toolchain\n"
)
V6_BOUNDARY_BLOCK = (
    b"          scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --cross-toolchain\n"
    b"          scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --cross-toolchain\n"
)
LOCAL_L6_EXACT_PDF_BLOCK = (
    b"    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact\n"
    b"    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact\n"
    b"    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact\n"
    b"    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact\n"
)
LOCAL_L6_CAPTURE_SELF_TEST_BLOCK = (
    b"    python3 -I -S -B "
    b"scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test "
    b'> "$result_root/local-closure-self-test.json"\n'
    b"    python3 -O -I -S -B "
    b"scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test "
    b'> "$result_root/local-closure-self-test.optimized.json"\n'
    b'    cmp "$result_root/local-closure-self-test.json" '
    b'"$result_root/local-closure-self-test.optimized.json"\n'
)
HOSTED_L6_CAPTURE_SELF_TEST_BLOCK = (
    b"          python3 -I -S -B "
    b"scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test "
    b'> "${RUNNER_TEMP}/local-closure-self-test.json"\n'
    b"          python3 -O -I -S -B "
    b"scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test "
    b'> "${RUNNER_TEMP}/local-closure-self-test.optimized.json"\n'
    b"          cmp --silent "
    b'"${RUNNER_TEMP}/local-closure-self-test.json" '
    b'"${RUNNER_TEMP}/local-closure-self-test.optimized.json"\n'
)
V6_CURRENT_HOSTED_RECOVERY_SELF_TEST_BLOCK = (
    b"          python3 -I -S -B "
    b"scripts/check-ksg-m1a-hosted-recovery-self-test.py\n"
    b"          python3 -O -I -S -B "
    b"scripts/check-ksg-m1a-hosted-recovery-self-test.py\n"
)
V6_STALE_V3_SEMANTIC_TOKENS = (
    b"scripts/check-ksg-m1a-composite-v3.py",
    b"scripts/check-ksg-m1a-composite-v3-self-test.py",
    b"audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json",
    b"audit/evidence/ksg-rev4-m1a-composite-receipt-v3-2026-08-13.json",
    b"--validate-composite-receipt",
)
CAPTURE_SCHEMA_SHA256 = (
    "5d075f383729818a7e15f321058dc973416492c3fabbc152f8b6e584ec001df6"
)
CAPTURE_SCHEMA_SIZE_BYTES = 14163
LOCAL_CLOSURE_TOOL_SHA256 = (
    "5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a"
)
LOCAL_CLOSURE_TOOL_SIZE_BYTES = 57021
LOCAL_CLOSURE_SCHEMA_SHA256 = (
    "4ab719785b6f89ce63d1061813a31e17289fa94cf4300aab00946de2c045f3fd"
)
LOCAL_CLOSURE_SCHEMA_SIZE_BYTES = 13620
RECEIPT_SCHEMA_SHA256 = (
    "65504b10c0fff4e2f287a0271364553d89cf6a6dfef7c6418ab8780e7e28f00f"
)
RECEIPT_SCHEMA_SIZE_BYTES = 20482

CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "The two retrieval repetitions are correlated observations of provider state, not independent replications.",
    "The predecessor failure phase records C5's terminal hosted failure; it grants no hosted-success, R5-receipt, mathematical, estimator, or application-validation credit.",
    "A successful successor run is not mathematical, estimator, security, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to the workflow run or its historical execution window.",
    "Failed-job log bytes record provider output but do not by themselves establish a unique defect cause, generic portability defect, or remediation.",
    "Capture time, network completeness, provider response order, and trusted provider time are not claimed.",
    "The capture makes no claim about any PID functional, objective, estimator, or downstream use.",
]
GIT_CLEAN_NONHERMETIC_NONCLAIM = (
    "The clean endpoints use ordinary Git status plus selected metadata checks; "
    "rejecting core.excludesFile removes one ignore-routing overlay, but "
    "repository-ignored products and uninspected Git metadata remain outside the "
    "observation and may remain side inputs, so this is not a hermetic closure."
)
RECEIPT_NONIMPLICATIONS = [
    "C5 is a published commit, but its hosted qualification attempt failed and receives zero qualification, R5-receipt, mathematical, estimator, or application-validation credit.",
    "R5 is permanently unissued; the v6 repair does not create, reconstruct, rename, or backdate a v5 receipt.",
    "C6 repairs one named Cartesian report/figure association-rule failure surface, manifested in the immutable v4/v5 PDF gate lanes; it does not rewrite C5 history; R6 records fresh attempt-1 hosted success, and neither proves a unique root cause or only possible remedy.",
    "The two retrieval repetitions are correlated provider observations, not independent replications or a transparency log.",
    "CodeQL analysis and alert observations are repository-level current-state snapshots, not run-historical foreign-key evidence.",
    "Captured provider bytes and identifiers do not authenticate themselves or establish trusted provider time.",
    "Failed-job log bytes preserve observed output but do not by themselves prove a unique defect cause or that the successor repair is the only possible remedy.",
    "The durable local closure is an unsigned, unauthenticated, correlated operator-side observation; it is neither independent reproduction nor a first-attempt authority.",
    "Local wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "The local reviewed-executable roster is a bounded named subset, not a complete transitive executable inventory; its hashes and version output do not prove which bytes the operating system executed.",
    "The redacted local environment-route digest is an opaque capture-time fingerprint; HOME remains absent and isolated XDG/TeX roots do not prove that every passwd-derived fallback was excluded.",
    "The local secret/private-path and pipe-drain checks reject named hazards but do not prove absence of every sensitive value, identify every descendant, or prove descendant termination.",
    GIT_CLEAN_NONHERMETIC_NONCLAIM,
    "A passing checker, workflow, capture, or receipt is not mathematical proof, estimator validation, security certification, scientific review, or application approval.",
    "No result transfers among KSG mutual information, categorical or continuous shared exclusions, I_min, PID2, PID3, quantized or mixed-support routes, resampling procedures, or downstream objectives.",
    "Git and SHA-256 identities bind named bytes and topology only; they do not establish authorship, authenticity, independent reproduction, or indefinite storage durability.",
]

LOCAL_CLOSURE_NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C6 checkout and is neither an independent replication nor a first-attempt authority.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude unobserved interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, shell builtins, libraries, TeX helpers, or transitive processes.",
    "The redacted environment-route digest is an opaque correlated capture-time fingerprint, not a publicly recomputable path authority.",
    "HOME is absent from the constructed environment; isolated XDG and TeX roots reduce but do not prove the absence of every passwd-derived user-path fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove that every descendant process was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove that output contains no sensitive information.",
    GIT_CLEAN_NONHERMETIC_NONCLAIM,
    "A local closure pass is operational evidence only; it is not PID, KSG, mathematical, scientific, security, application, PDF/UA, renderer-independence, or cross-platform reproducibility evidence.",
]

PREDECESSOR_RUNS = {
    "predecessor_ci": 32107469096,
    "predecessor_codeql": 32107469060,
    "predecessor_contract": 32107469077,
}
PREDECESSOR_REQUIRED_FAILED_JOB_IDS = {
    "predecessor_ci": {95619717365},
    "predecessor_codeql": set(),
    "predecessor_contract": {95619716898},
}
PREDECESSOR_REQUIRED_FAILURE_IDENTITIES = {
    "predecessor_ci": {
        95619717365: (
            "Formal LaTeX / PDF inventory and cross-toolchain structure",
            (
                "Rebuild papers and check cross-toolchain text, geometry, fonts, and workflow renders",
            ),
        ),
    },
    "predecessor_codeql": {},
    "predecessor_contract": {
        95619716898: (
            "Validate the composite-v5 correction contract",
            ("Validate the bounded successor publication",),
        )
    },
}
PREDECESSOR_REQUIRED_LOG_MARKERS = {
    95619716898: (
        "composite-v5 boundary PDF check: PDF structure embedded Form content differs from standalone figure",
    ),
    95619717365: (
        "composite-v4 process PDF check: PDF object structure changed: embedded custody Form content differs from the standalone figure",
    ),
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

# Centralized exact, path-sorted C6 inventory independently reconciled with the
# stored policy.  The 43-row, 21-M/22-A topology is part of the contract.
C6_POLICY_ROWS: tuple[tuple[str, str, str, str], ...] = (
    (
        ".github/workflows/ksg-m1a-composite-v5.yml",
        "M",
        "100644",
        "retired_v5_no_credit_workflow",
    ),
    (
        ".github/workflows/ksg-m1a-composite-v6.yml",
        "A",
        "100644",
        "dedicated_v6_hosted_gate",
    ),
    (
        "AGENTS.md",
        "M",
        "100644",
        "operational_and_scientific_object_guide",
    ),
    ("CHANGELOG.md", "M", "100644", "append_only_change_record"),
    (
        "audit/evidence/completion-active-resume.md",
        "M",
        "100644",
        "current_replay_pointer",
    ),
    (
        CURRENT_SOURCE_RELATIVE,
        "M",
        "100644",
        "self_excluding_source_state",
    ),
    (
        PREDECESSOR_CAPTURE_RELATIVE,
        "A",
        "100644",
        "predecessor_failure_hosted_capture",
    ),
    (
        "audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md",
        "A",
        "100644",
        "operational_boundary_record",
    ),
    (
        "audit/evidence/ksg-rev4-m1a-composite-v6-boundary-visual-receipt-2026-08-18.md",
        "A",
        "100644",
        "operational_boundary_visual_receipt",
    ),
    (POLICY_RELATIVE, "A", "100644", "c6_r6_path_policy"),
    (LEAN_R11_RELATIVE, "A", "100644", "current_lean_replay_receipt"),
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
        "audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf",
        "A",
        "100644",
        "operational_boundary_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.svg",
        "A",
        "100644",
        "operational_boundary_vector_source",
    ),
    (
        "audit/formal/latex/ksg-m1a-composite-v6-boundary.tex",
        "A",
        "100644",
        "operational_boundary_latex_source",
    ),
    (
        CAPTURE_SCHEMA_RELATIVE,
        "A",
        "100644",
        "dual_phase_hosted_capture_schema",
    ),
    (
        LOCAL_CLOSURE_SCHEMA_RELATIVE,
        "A",
        "100644",
        "local_l6_closure_schema",
    ),
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
    ("justfile", "M", "100644", "local_command_wiring"),
    (
        "output/pdf/ksg-m1a-composite-v6-boundary.pdf",
        "A",
        "100644",
        "operational_boundary_publication_pdf",
    ),
    (
        "output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv",
        "A",
        "100644",
        "operational_boundary_rendering_receipt",
    ),
    ("scripts/README.md", "M", "100644", "script_process_guide"),
    (
        LOCAL_CLOSURE_TOOL_RELATIVE,
        "A",
        "100644",
        "bounded_local_l6_closure_capture_tool",
    ),
    (
        CAPTURE_TOOL_RELATIVE,
        "A",
        "100644",
        "bounded_dual_phase_hosted_capture_tool",
    ),
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
    (
        "scripts/check-formal-pdf-style.py",
        "M",
        "100755",
        "formal_pdf_style_gate",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh",
        "A",
        "100755",
        "operational_boundary_pdf_gate_self_test",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh",
        "A",
        "100755",
        "operational_boundary_pdf_gate",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh",
        "A",
        "100755",
        "immutable_predecessor_pdf_portability_hostile_suite",
    ),
    (
        "scripts/check-ksg-m1a-composite-v6-pdf-portability.sh",
        "A",
        "100755",
        "immutable_predecessor_pdf_portability_gate",
    ),
    (
        SELF_TEST_RELATIVE,
        "A",
        "100644",
        "composite_v6_hostile_suite",
    ),
    (CHECKER_RELATIVE, "A", "100644", "composite_v6_semantic_gate"),
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
R6_POLICY_ROWS = (
    (
        CURRENT_SOURCE_RELATIVE,
        "M",
        "100644",
        "self_excluding_source_state",
    ),
    (LOCAL_CLOSURE_RELATIVE, "A", "100644", "durable_local_l6_closure"),
    (RECEIPT_RELATIVE, "A", "100644", "derived_v6_receipt"),
    (
        SUCCESSOR_CAPTURE_RELATIVE,
        "A",
        "100644",
        "fresh_successor_hosted_capture",
    ),
)
POLICY_NONIMPLICATIONS: list[str] = [
    "This policy describes an exact C6 and conditional R6 path topology; it is not "
    "prior authorization to create either commit or any evidence artifact.",
    "Path, mode, role, status, Git topology, message, hash, or checker conformance "
    "does not authenticate bytes, authorship, provider observations, or trusted time.",
    "C5 was published, but its hosted qualification attempt failed; the "
    "predecessor-failure capture is zero-credit failure evidence and cannot issue or "
    "substitute for R5.",
    "R5 is permanently unissued; neither C6 nor R6 creates, reconstructs, renames, "
    "backdates, or revives it.",
    "R6 requires fresh local qualification of the exact C6 commit and fresh "
    "attempt-1, exact-C6, all-success repository CI, CodeQL, and dedicated-v6 hosted "
    "qualification; partial success, retries, or predecessor observations cannot "
    "transfer.",
    "The R6 local-closure record must be produced outside the repository from a "
    "clean exact C6 checkout, then installed byte-for-byte; its fixed command, "
    "clean endpoint observations, selected tool identities, and bounded output are "
    "unauthenticated correlated operational evidence, not a first-attempt or "
    "complete-executable-closure authority.",
    "The local record's redacted environment routes, timestamps, process "
    "observations, and secret scan do not prove hermetic execution, trusted time, "
    "atomicity, descendant termination, absence of passwd-derived fallback, or "
    "absence of every sensitive value.",
    GIT_CLEAN_NONHERMETIC_NONCLAIM,
    "C6 repairs one named Cartesian report/figure association-rule failure surface "
    "manifested in the immutable v4/v5 PDF gate lanes; reproduced residues and stale "
    "digests do not establish a unique cause or that C6 is the only possible remedy.",
    "Operational publications, process documentation, workflow results, captures, "
    "and receipts are not scientific authorities and establish no PID definition, "
    "mathematical proof, estimator validity, security certification, release, or "
    "application approval.",
    "No evidence transfers among KSG mutual information, categorical or continuous "
    "shared exclusions, I_min, PID2, PID3, quantized or mixed-support routes, "
    "resampling procedures, or downstream objectives.",
    "Repeated provider retrievals, checker agreement, and same-renderer comparisons "
    "do not establish independence or reproducibility.",
    "Git and SHA-256 identities bind named bytes and topology only; they do not "
    "establish authorship, authenticity, independent reproduction, or indefinite "
    "storage durability.",
]

MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BODY_BYTES = 22 * 1024 * 1024
MAX_CAPTURE_ROWS = 4096
MAX_LOCAL_STREAM_BYTES = 8 * 1024 * 1024
MAX_LOCAL_VERSION_STREAM_BYTES = 64 * 1024
MAX_LOCAL_EXECUTABLE_BYTES = 256 * 1024 * 1024
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
LOCAL_SECRET_OUTPUT_PATTERNS = (
    re.compile(rb"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(rb"(?i)github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"(?i)gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"(?i)(?:password|passwd|secret|credential|api[_-]?key)\s*[=:]\s*\S+"),
    re.compile(rb"/(?:Users|home)/[^/\x00\r\n ]+/"),
    re.compile(rb"/private/tmp/"),
)
LOCAL_NORMALIZED_ENVIRONMENT = {
    "GIT_CONFIG_GLOBAL": "<NULL_DEVICE>",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "<SANITIZED_TOOL_PATH>",
    "PYTHONDONTWRITEBYTECODE": "1",
    "TEXMFCACHE": "<PRIVATE_TEMP_TEXMF_CACHE>",
    "TEXMFCONFIG": "<PRIVATE_TEMP_TEXMF_CONFIG>",
    "TEXMFHOME": "<PRIVATE_TEMP_TEXMF_HOME>",
    "TEXMFVAR": "<PRIVATE_TEMP_TEXMF_VAR>",
    "TMPDIR": "<PRIVATE_TEMP_ROOT>",
    "TZ": "UTC",
    "XDG_CACHE_HOME": "<PRIVATE_TEMP_XDG_CACHE>",
    "XDG_CONFIG_HOME": "<PRIVATE_TEMP_XDG_CONFIG>",
    "XDG_DATA_HOME": "<PRIVATE_TEMP_XDG_DATA>",
}
LOCAL_TOOL_SPECS = {
    "bash": ["bash", "--version"],
    "chktex": ["chktex", "--version"],
    "fc-match": ["fc-match", "--version"],
    "git": ["git", "--version"],
    "just": ["just", "--version"],
    "lacheck": ["lacheck", "--version"],
    "latexmk": ["latexmk", "--version"],
    "lualatex": ["lualatex", "--version"],
    "pdfinfo": ["pdfinfo", "-v"],
    "pdffonts": ["pdffonts", "-v"],
    "pdftocairo": ["pdftocairo", "-v"],
    "pdftotext": ["pdftotext", "-v"],
    "python3": ["python3", "--version"],
    "rsvg-convert": ["rsvg-convert", "--version"],
    "xmllint": ["xmllint", "--version"],
}
LOCAL_AUTHORITY_ROLES = {
    JUSTFILE_RELATIVE: "local_command_wiring",
    LOCAL_CLOSURE_SCHEMA_RELATIVE: "local_l6_closure_schema",
    LOCAL_CLOSURE_TOOL_RELATIVE: "bounded_local_l6_closure_capture_tool",
    SELF_TEST_RELATIVE: "composite_v6_hostile_suite",
    CHECKER_RELATIVE: "composite_v6_semantic_gate",
}


def _bootstrap_v5_primitives() -> Any:
    path = ROOT / V5_CHECKER_RELATIVE
    try:
        before = path.lstat()
        if not (
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o644
            and before.st_size == V5_CHECKER_SIZE_BYTES
        ):
            raise OSError("unsafe immutable v5 primitive metadata")
        file_descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            opened = os.fstat(file_descriptor)
            if (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
                opened.st_size,
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            ) != (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ):
                raise OSError("immutable v5 primitive identity changed before read")
            raw = b""
            while len(raw) < opened.st_size:
                chunk = os.read(file_descriptor, opened.st_size - len(raw))
                if chunk == b"":
                    raise OSError("short immutable v5 primitive read")
                raw += chunk
            if os.read(file_descriptor, 1) != b"":
                raise OSError("immutable v5 primitive grew during read")
            closed = os.fstat(file_descriptor)
            if (
                closed.st_dev,
                closed.st_ino,
                closed.st_mode,
                closed.st_size,
                closed.st_mtime_ns,
                closed.st_ctime_ns,
            ) != (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
                opened.st_size,
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            ):
                raise OSError("immutable v5 primitive identity changed during read")
        finally:
            os.close(file_descriptor)
    except OSError as error:
        print(f"ERROR: cannot read immutable v5 primitives: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    if not (
        SCRIPT == ROOT / CHECKER_RELATIVE
        and len(raw) == V5_CHECKER_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == V5_CHECKER_SHA256
    ):
        print("ERROR: immutable v5 primitive bytes changed", file=sys.stderr)
        raise SystemExit(2)
    module_name = "_pid_rs_immutable_composite_v5"
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(
            raw,
            os.fspath(path),
            "exec",
            dont_inherit=True,
            optimize=sys.flags.optimize,
        )
        exec(code, module.__dict__)
    except Exception as error:
        print(f"ERROR: cannot load immutable v5 primitives: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    return module


_v5 = _bootstrap_v5_primitives()
ContractError = _v5.ContractError
require = _v5.require
exact_int = _v5.exact_int
exact_keys = _v5.exact_keys
canonical_json = _v5.canonical_json
parse_json = _v5.parse_json
validate_schema_instance = _v5.validate_schema_instance
sha256 = _v5.sha256
parse_tree = _v5.parse_tree
parse_commit = _v5.parse_commit
parse_descendant_tree = _v5.parse_descendant_tree
changed_entries = _v5.changed_entries
tree_blob = _v5.tree_blob
validate_repository = _v5.validate_repository
validate_worktree = _v5.validate_worktree
read_repository_file = _v5.read_repository_file
git = _v5.git
git_text = _v5.git_text
git_predicate = _v5.git_predicate
descriptor_v5 = _v5.descriptor
project_digest = _v5.project_digest
single_json_response = _v5.single_json_response
paged_json_response = _v5.paged_json_response
normalized_artifacts_v5 = _v5.normalized_artifacts_v4
validate_postcommit_artifact = _v5.validate_postcommit_artifact
normalized_analyses_v5 = _v5.normalized_analyses_v4
normalized_alerts_v5 = _v5.normalized_alerts_v4
member_bytes = _v5.member_bytes
parse_utc_timestamp = _v5.parse_utc_timestamp


def descriptor(entries: dict[str, Any], path: str) -> dict[str, Any]:
    raw = tree_blob(entries, path)
    return {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}


def authority_descriptor(
    entries: dict[str, Any], path: str, role: str
) -> dict[str, Any]:
    value = descriptor(entries, path)
    value["role"] = role
    return value


def require_exact_bytes(
    entries: dict[str, Any], path: str, digest: str, size: int, label: str
) -> bytes:
    require(
        SHA256_RE.fullmatch(digest) is not None and size > 0, f"{label} is not frozen"
    )
    raw = tree_blob(entries, path)
    require(len(raw) == size and sha256(raw) == digest, f"{label} exact bytes changed")
    return raw


def _closed_schema(
    raw: bytes,
    label: str,
    expected_id: str,
    expected_required: list[str],
    expected_digest: str,
    expected_size: int,
) -> dict[str, Any]:
    require(
        SHA256_RE.fullmatch(expected_digest) is not None and expected_size > 0,
        f"{label} byte identity is not frozen",
    )
    value = parse_json(raw, f"{label} schema")
    _v5._v4.validate_contract_schema_definition(
        value,
        label,
        expected_id=expected_id,
        expected_required=expected_required,
        expected_sha256=expected_digest,
        expected_size_bytes=expected_size,
        raw=raw,
    )
    return value


def _policy_rows(value: Any, label: str) -> tuple[tuple[str, str, str, str], ...]:
    require(type(value) is list and value, f"{label} is not a nonempty array")
    rows: list[tuple[str, str, str, str]] = []
    for index, item in enumerate(value):
        row = exact_keys(item, {"mode", "path", "role", "status"}, f"{label}[{index}]")
        path = row["path"]
        require(
            type(path) is str
            and _v5._v4.validate_relative_path(path, f"{label}[{index}] path")
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


def validate_policy_value(value: Any) -> tuple[tuple[str, str, str], ...]:
    root = exact_keys(
        value,
        {
            "base",
            "c6",
            "nonimplications",
            "r6",
            "repository",
            "schema",
            "schema_revision",
        },
        "composite-v6 path policy",
    )
    base = exact_keys(
        root["base"],
        {"commit", "r4_status", "r5_status", "reserved_absent_paths", "tree"},
        "composite-v6 policy base",
    )
    c6 = exact_keys(
        root["c6"], {"delta", "direct_parent_role", "message"}, "composite-v6 policy C6"
    )
    r6 = exact_keys(
        root["r6"], {"delta", "direct_parent_role", "message"}, "composite-v6 policy R6"
    )
    require(
        root["schema"] == "pid-rs/ksg-m1a-composite-v6-path-policy"
        and root["schema_revision"] == 1
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and base
        == {
            "commit": C5_COMMIT,
            "r4_status": "permanently_unissued",
            "r5_status": "permanently_unissued",
            "reserved_absent_paths": list(FORBIDDEN_R4_R5_EVIDENCE_PATHS),
            "tree": C5_TREE,
        }
        and c6["direct_parent_role"] == "published_c5_contract"
        and c6["message"] == C6_MESSAGE
        and r6["direct_parent_role"] == "c6_contract_repair"
        and r6["message"] == R6_MESSAGE
        and root["nonimplications"] == POLICY_NONIMPLICATIONS,
        "composite-v6 policy identity or nonimplication boundary changed",
    )
    c6_rows = _policy_rows(c6["delta"], "composite-v6 policy C6 delta")
    r6_rows = _policy_rows(r6["delta"], "composite-v6 policy R6 delta")
    require(
        len(C6_POLICY_ROWS) == 43
        and sum(row[1] == "M" for row in C6_POLICY_ROWS) == 21
        and sum(row[1] == "A" for row in C6_POLICY_ROWS) == 22,
        "C6 policy status inventory changed",
    )
    require(C6_POLICY_ROWS and c6_rows == C6_POLICY_ROWS, "C6 policy rows changed")
    require(
        len(R6_POLICY_ROWS) == 4 and r6_rows == R6_POLICY_ROWS,
        "R6 policy rows changed",
    )
    return tuple((path, status, mode) for path, status, mode, _role in c6_rows)


def validate_policy(entries: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    return validate_policy_value(
        parse_json(tree_blob(entries, POLICY_RELATIVE), "composite-v6 path policy")
    )


def validate_replay_values(r10_raw: bytes, r11: Any) -> None:
    require(type(r11) is dict, "Lean r11 current replay is not an object")
    prior_hashes = r11.get("prior_replay_preservation_sha256")
    prior_schemas = r11.get("prior_replay_schema")
    require(
        r11.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and r11.get("status") == "passed"
        and type(prior_hashes) is dict
        and type(prior_schemas) is dict
        and prior_hashes.get(LEAN_R10_RELATIVE) == sha256(r10_raw)
        and prior_schemas.get(LEAN_R10_RELATIVE)
        == "pid-rs/lean-current-project-replay/v2",
        "Lean r11 does not classify exact r10 bytes as prior replay evidence",
    )


def lean_replay_projection_sha256(receipt: dict[str, Any]) -> str:
    """Reproduce the r11 projection without importing the mutable Lean checker."""

    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    require(type(custody) is dict, "r11 custody-gate inventory is malformed")
    self_test_path = "scripts/check-lean-toolchain-freeze-self-test.py"
    require(self_test_path in custody, "r11 self-test custody is absent")
    projected["custody_gate_sha256"] = {self_test_path: custody[self_test_path]}
    try:
        raw = json.dumps(
            projected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError) as error:
        raise ContractError(f"cannot project r11 replay receipt: {error}") from None
    return sha256(raw)


def lean_r11_source_cuts(raw: bytes) -> tuple[str, str, str, bytes]:
    """Extract and normalize exactly the three final Lean/r11 checksum cuts."""

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
            "composite-v6 checker scalar",
            re.compile(
                r'^EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            re.compile(
                r"^EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = .+$",
                re.MULTILINE,
            ),
            'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "0" * 64',
        ),
        (
            "composite-v6 operational-map row",
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v6\.py": "([0-9a-f]{64})",$',
                re.MULTILINE,
            ),
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v6\.py": .+$', re.MULTILINE
            ),
            '    "scripts/check-ksg-m1a-composite-v6.py": "0" * 64,',
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
    """Extract the one final normalized-Lean binding from v6 checker bytes."""

    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"composite-v6 checker is not UTF-8: {error}") from None
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


def validate_lean_r11_checksum_cut(
    v6_checker_raw: bytes, lean_checker_raw: bytes
) -> str:
    """Bind final v6 bytes to the exactly three-cut-normalized Lean source."""

    checker_digest = sha256(v6_checker_raw)
    _projection, scalar_cut, operational_cut, normalized = lean_r11_source_cuts(
        lean_checker_raw
    )
    require(
        scalar_cut == checker_digest and operational_cut == checker_digest,
        "Lean composite-v6 checker cuts do not bind the exact v6 checker bytes",
    )
    require(
        normalized_lean_checker_cut(v6_checker_raw) == sha256(normalized),
        "normalized Lean checker authority changed",
    )
    return _projection


def validate_lean_r11_receipt_cuts(
    v6_checker_raw: bytes,
    lean_checker_raw: bytes,
    r11: dict[str, Any],
    projection: str,
) -> None:
    """Join the final projection and replay/final checker custody to r11."""

    operational = r11.get("operational_wiring_sha256")
    require(
        type(operational) is dict
        and operational.get(CHECKER_RELATIVE) == sha256(v6_checker_raw),
        "Lean r11 operational map does not bind the v6 checker bytes",
    )
    require(
        lean_replay_projection_sha256(r11) == projection,
        "Lean r11 projection cut changed",
    )
    final_custody = r11.get("custody_gate_sha256")
    replay_custody = r11.get("replay_custody_gate_sha256")
    require(
        type(final_custody) is dict
        and type(replay_custody) is dict
        and final_custody.get(LEAN_CHECKER_RELATIVE) == sha256(lean_checker_raw),
        "Lean r11 final checker custody changed",
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
        "Lean r11 projection line is not exactly reconstructable",
    )
    replay_checker_raw = lean_checker_raw.replace(
        final_projection_line, placeholder_projection_line, 1
    )
    require(
        replay_custody.get(LEAN_CHECKER_RELATIVE) == sha256(replay_checker_raw),
        "Lean r11 replay-time checker custody changed",
    )


def validate_replay_pair(c6_entries: dict[str, Any]) -> None:
    r10_raw = require_exact_bytes(
        c6_entries,
        LEAN_R10_RELATIVE,
        LEAN_R10_SHA256,
        LEAN_R10_SIZE_BYTES,
        "Lean r10 prior replay",
    )
    r11 = parse_json(
        tree_blob(c6_entries, LEAN_R11_RELATIVE),
        "Lean r11 current replay",
        canonical=False,
    )
    validate_replay_values(r10_raw, r11)
    v6_checker_raw = tree_blob(c6_entries, CHECKER_RELATIVE)
    lean_checker_raw = tree_blob(c6_entries, LEAN_CHECKER_RELATIVE)
    projection = validate_lean_r11_checksum_cut(v6_checker_raw, lean_checker_raw)
    validate_lean_r11_receipt_cuts(v6_checker_raw, lean_checker_raw, r11, projection)


def validate_exact_delta(
    actual: tuple[tuple[str, str, str], ...],
    expected: tuple[tuple[str, str, str], ...],
    label: str,
) -> None:
    require(actual == expected, f"{label} delta is not exact")


def validate_v6_workflow_prerequisites(raw: bytes) -> None:
    require(b"\r" not in raw, "successor workflow line endings changed")
    offsets: list[int] = []
    for index, block in enumerate(V6_PDF_PREREQUISITE_BLOCKS, start=1):
        require(
            raw.count(block) == 1,
            f"successor workflow PDF prerequisite block {index} changed",
        )
        offsets.append(raw.index(block))
    require(
        raw.count(V6_CURRENT_HOSTED_RECOVERY_SELF_TEST_BLOCK) == 1,
        "successor workflow current hosted-recovery self-test pair changed",
    )
    require(
        raw.count(HOSTED_L6_CAPTURE_SELF_TEST_BLOCK) == 1,
        "successor workflow local-closure capture self-test pair changed",
    )
    require(
        raw.count(V6_ATTEMPT_1_REFUSAL_BLOCK) == 1,
        "successor workflow attempt-1 refusal changed",
    )
    require(
        raw.count(V6_PORTABILITY_BLOCK) == 1,
        "successor workflow immutable-predecessor portability pair changed",
    )
    require(
        raw.count(V6_BOUNDARY_BLOCK) == 1,
        "successor workflow v6 boundary-publication pair changed",
    )
    hosted_recovery_offset = raw.index(V6_CURRENT_HOSTED_RECOVERY_SELF_TEST_BLOCK)
    local_capture_offset = raw.index(HOSTED_L6_CAPTURE_SELF_TEST_BLOCK)
    require(
        raw.count(V6_PUBLICATION_STEP_MARKER) == 1
        and offsets[0]
        < offsets[1]
        < hosted_recovery_offset
        < local_capture_offset
        < raw.index(V6_PUBLICATION_STEP_MARKER)
        < raw.index(V6_PORTABILITY_BLOCK)
        < raw.index(V6_BOUNDARY_BLOCK),
        "successor workflow prerequisites are not ordered before validation",
    )
    require(
        b"composite-v6-pdf-portability.sh --exact" not in raw
        and b"composite-v6-boundary-pdf.sh --exact" not in raw,
        "hosted D6 workflow improperly requests a maintainer exact-PDF lane",
    )
    require(
        raw.count(b"capture-ksg-m1a-composite-v6-local-closure.py") == 2
        and b"capture-ksg-m1a-composite-v6-local-closure.py --output" not in raw,
        "hosted workflow invokes the real local-closure capture mode",
    )
    require(
        all(token not in raw for token in V6_STALE_V3_SEMANTIC_TOKENS),
        "successor workflow contains a stale composite-v3 semantic token",
    )


def validate_frozen_workflow_values(retired_v5_raw: bytes, v6_raw: bytes) -> None:
    require(
        len(retired_v5_raw) == RETIRED_V5_WORKFLOW_SIZE_BYTES
        and sha256(retired_v5_raw) == RETIRED_V5_WORKFLOW_SHA256,
        "retired live v5 workflow byte identity changed",
    )
    require(
        len(v6_raw) == V6_WORKFLOW_SIZE_BYTES and sha256(v6_raw) == V6_WORKFLOW_SHA256,
        "successor live v6 workflow byte identity changed",
    )


def validate_frozen_local_closure_tool(raw: bytes) -> None:
    require(
        len(raw) == LOCAL_CLOSURE_TOOL_SIZE_BYTES
        and sha256(raw) == LOCAL_CLOSURE_TOOL_SHA256,
        "local-closure capture tool byte identity changed",
    )


def validate_local_l6_values(raw: bytes) -> None:
    require(b"\r" not in raw, "local L6 command line endings changed")
    require(
        raw.count(b"\nksg-composite-v6:\n") == 1,
        "local L6 recipe identity changed",
    )
    require(
        raw.count(LOCAL_L6_CAPTURE_SELF_TEST_BLOCK) == 1,
        "local L6 local-closure capture self-test pair changed",
    )
    require(
        raw.count(LOCAL_L6_EXACT_PDF_BLOCK) == 1,
        "local L6 exact PDF main/self-test lanes changed",
    )
    capture_offset = raw.index(LOCAL_L6_CAPTURE_SELF_TEST_BLOCK)
    exact_offset = raw.index(LOCAL_L6_EXACT_PDF_BLOCK)
    static_marker = (
        b"    python3 -I -S -B scripts/check-ksg-m1a-composite-v6.py "
        b'--validate-static > "$result_root/static.json"\n'
    )
    require(
        raw.count(static_marker) == 1
        and capture_offset < exact_offset < raw.index(static_marker),
        "local L6 capture/PDF lanes are not ordered before static validation",
    )
    require(
        raw.count(b"capture-ksg-m1a-composite-v6-local-closure.py") == 2
        and b"capture-ksg-m1a-composite-v6-local-closure.py --output" not in raw,
        "local L6 recipe recursively invokes real local-closure capture mode",
    )
    release_lines = [
        line for line in raw.splitlines() if line.startswith(b"release-audit:")
    ]
    require(
        len(release_lines) == 1
        and b" ksg-composite-v6 " in release_lines[0]
        and b"ksg-composite-v5" not in release_lines[0],
        "release audit does not select the local L6 command exclusively",
    )


def validate_current_hosted_recovery_values(
    self_test_raw: bytes, checker_raw: bytes
) -> None:
    require(
        len(self_test_raw) == CURRENT_HOSTED_RECOVERY_SELF_TEST_SIZE_BYTES
        and sha256(self_test_raw) == CURRENT_HOSTED_RECOVERY_SELF_TEST_SHA256,
        "current hosted-recovery hostile-suite byte identity changed",
    )
    require(
        len(checker_raw) == CURRENT_HOSTED_RECOVERY_CHECKER_SIZE_BYTES
        and sha256(checker_raw) == CURRENT_HOSTED_RECOVERY_CHECKER_SHA256,
        "current hosted-recovery gate byte identity changed",
    )


def validate_schema_authorities(
    c6_entries: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    capture_raw = require_exact_bytes(
        c6_entries,
        CAPTURE_SCHEMA_RELATIVE,
        CAPTURE_SCHEMA_SHA256,
        CAPTURE_SCHEMA_SIZE_BYTES,
        "composite-v6 capture schema",
    )
    receipt_raw = require_exact_bytes(
        c6_entries,
        RECEIPT_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_SHA256,
        RECEIPT_SCHEMA_SIZE_BYTES,
        "composite-v6 receipt schema",
    )
    capture_schema = parse_json(capture_raw, "composite-v6 hosted-capture schema")
    validate_schema_instance(
        {}, capture_schema, "composite-v6 hosted-capture", definition_only=True
    )
    require(
        type(capture_schema) is dict
        and capture_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
        and capture_schema.get("$id")
        == "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v6.schema.json"
        and capture_schema.get("oneOf")
        == [
            {"$ref": "#/$defs/predecessorDocument"},
            {"$ref": "#/$defs/successorDocument"},
        ],
        "composite-v6 hosted-capture schema identity changed",
    )
    local_schema = _closed_schema(
        require_exact_bytes(
            c6_entries,
            LOCAL_CLOSURE_SCHEMA_RELATIVE,
            LOCAL_CLOSURE_SCHEMA_SHA256,
            LOCAL_CLOSURE_SCHEMA_SIZE_BYTES,
            "composite-v6 local-closure schema",
        ),
        "composite-v6 local closure",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json",
        [
            "authorities",
            "invocation",
            "nonimplications",
            "platform",
            "repository",
            "repository_state",
            "reviewed_executables",
            "schema",
            "schema_revision",
            "subject",
        ],
        LOCAL_CLOSURE_SCHEMA_SHA256,
        LOCAL_CLOSURE_SCHEMA_SIZE_BYTES,
    )
    receipt_schema = _closed_schema(
        receipt_raw,
        "composite-v6 receipt",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-receipt-v6.schema.json",
        [
            "capture_bindings",
            "contract_authorities",
            "local_qualification",
            "nonimplications",
            "observations",
            "repository",
            "schema",
            "schema_revision",
            "subject",
            "verdict",
        ],
        RECEIPT_SCHEMA_SHA256,
        RECEIPT_SCHEMA_SIZE_BYTES,
    )
    return capture_schema, local_schema, receipt_schema


def decode_local_binding(value: Any, label: str, maximum: int) -> bytes:
    binding = exact_keys(
        value, {"body_base64", "sha256", "size_bytes"}, f"{label} binding"
    )
    require(
        type(binding["body_base64"]) is str
        and type(binding["sha256"]) is str
        and SHA256_RE.fullmatch(binding["sha256"]) is not None
        and type(binding["size_bytes"]) is int
        and 0 <= binding["size_bytes"] <= maximum,
        f"{label} binding scalars changed",
    )
    try:
        raw = base64.b64decode(binding["body_base64"], validate=True)
    except (ValueError, base64.binascii.Error):
        raise ContractError(f"{label} is not canonical base64") from None
    require(
        base64.b64encode(raw).decode("ascii") == binding["body_base64"]
        and len(raw) == binding["size_bytes"]
        and sha256(raw) == binding["sha256"],
        f"{label} byte binding changed",
    )
    return raw


def parse_local_timestamp(value: Any, label: str) -> datetime:
    require(
        type(value) is str and UTC_TIMESTAMP_RE.fullmatch(value) is not None,
        f"{label} is not exact microsecond UTC-Z time",
    )
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        raise ContractError(f"{label} is not a valid UTC timestamp") from None
    require(
        parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") == value,
        f"{label} is not canonical UTC time",
    )
    return parsed


def reject_local_sensitive_bytes(raw: bytes, label: str) -> None:
    require(
        all(pattern.search(raw) is None for pattern in LOCAL_SECRET_OUTPUT_PATTERNS),
        f"{label} contains a forbidden credential or private-path pattern",
    )


def validate_local_snapshot(
    value: Any, c6: str, c6_tree: str, label: str
) -> tuple[datetime, dict[str, Any]]:
    snapshot = exact_keys(
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
        f"local closure {label} snapshot",
    )
    require(
        snapshot["alternates"] == "absent"
        and snapshot["common_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["config_overlays"] == "absent"
        and snapshot["git_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["grafts"] == "absent"
        and snapshot["head"] == c6
        and snapshot["http_alternates"] == "absent"
        and snapshot["info_attributes_rules"] == "absent"
        and snapshot["info_exclude_rules"] == "absent"
        and snapshot["message"] == C6_MESSAGE
        and snapshot["object_format"] == "sha1"
        and snapshot["parent"] == C5_COMMIT
        and snapshot["replacement_refs"] == []
        and snapshot["shallow"] == "absent"
        and snapshot["tree"] == c6_tree
        and snapshot["worktree_root"] == "<REPOSITORY_ROOT>",
        f"local closure {label} repository envelope changed",
    )
    status_raw = decode_local_binding(
        snapshot["status"], f"local closure {label} status", 0
    )
    require(status_raw == b"", f"local closure {label} worktree was not clean")
    return parse_local_timestamp(
        snapshot["observed_at"], f"local closure {label} observation"
    ), snapshot


def validate_local_reviewed_executables(value: Any) -> list[dict[str, Any]]:
    require(
        type(value) is list and len(value) == len(LOCAL_TOOL_SPECS),
        "local closure reviewed-executable roster changed",
    )
    records: list[dict[str, Any]] = []
    names: list[str] = []
    for index, item in enumerate(value):
        record = exact_keys(
            item,
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
            f"local closure reviewed executable {index}",
        )
        name = record["name"]
        require(
            type(name) is str
            and name in LOCAL_TOOL_SPECS
            and type(record["executable_sha256"]) is str
            and SHA256_RE.fullmatch(record["executable_sha256"]) is not None
            and type(record["executable_size_bytes"]) is int
            and 0 < record["executable_size_bytes"] <= MAX_LOCAL_EXECUTABLE_BYTES
            and type(record["route"]) is str
            and re.fullmatch(
                rf"<(?:SYSTEM|USR_LOCAL|HOMEBREW|TEXLIVE)_BIN>/{re.escape(name)}",
                record["route"],
            )
            is not None
            and record["version_argv"] == LOCAL_TOOL_SPECS[name]
            and record["version_exit_code"] == 0
            and type(record["version_exit_code"]) is int,
            f"local closure reviewed executable {index} changed",
        )
        stdout = decode_local_binding(
            record["version_stdout"],
            f"local closure {name} version stdout",
            MAX_LOCAL_VERSION_STREAM_BYTES,
        )
        stderr = decode_local_binding(
            record["version_stderr"],
            f"local closure {name} version stderr",
            MAX_LOCAL_VERSION_STREAM_BYTES,
        )
        require(stdout + stderr != b"", f"local closure {name} version output is empty")
        reject_local_sensitive_bytes(stdout, f"local closure {name} version stdout")
        reject_local_sensitive_bytes(stderr, f"local closure {name} version stderr")
        names.append(name)
        records.append(record)
    require(
        names == sorted(LOCAL_TOOL_SPECS),
        "local closure reviewed executables are missing, extra, or reordered",
    )
    return records


def validate_local_closure_record(
    local_raw: bytes,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    local_schema: dict[str, Any],
) -> dict[str, Any]:
    require(
        0 < len(local_raw) <= MAX_JSON_BYTES,
        "local closure record size is outside the bound",
    )
    local = parse_json(local_raw, "composite-v6 local closure")
    validate_schema_instance(local, local_schema, "composite-v6 local closure")
    root = exact_keys(
        local,
        {
            "authorities",
            "invocation",
            "nonimplications",
            "platform",
            "repository",
            "repository_state",
            "reviewed_executables",
            "schema",
            "schema_revision",
            "subject",
        },
        "composite-v6 local closure",
    )
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v1"
        and root["schema_revision"] == 1
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["nonimplications"] == LOCAL_CLOSURE_NONIMPLICATIONS,
        "local closure root identity or nonclaim boundary changed",
    )
    subject = exact_keys(
        root["subject"],
        {"c5_parent", "c6_commit", "c6_message", "c6_tree"},
        "local closure subject",
    )
    require(
        subject
        == {
            "c5_parent": C5_COMMIT,
            "c6_commit": c6,
            "c6_message": C6_MESSAGE,
            "c6_tree": c6_tree,
        },
        "local closure does not bind exact C6",
    )
    expected_authorities = sorted(
        (
            authority_descriptor(c6_entries, path, role)
            for path, role in LOCAL_AUTHORITY_ROLES.items()
        ),
        key=lambda item: item["path"],
    )
    require(
        root["authorities"] == expected_authorities,
        "local closure authority preimages differ from exact C6",
    )
    state = exact_keys(
        root["repository_state"], {"after", "before"}, "local repository state"
    )
    before_time, before = validate_local_snapshot(
        state["before"], c6, c6_tree, "before"
    )
    after_time, after = validate_local_snapshot(state["after"], c6, c6_tree, "after")
    require(
        {key: before[key] for key in before if key != "observed_at"}
        == {key: after[key] for key in after if key != "observed_at"},
        "local closure endpoint repository observations disagree",
    )
    invocation = exact_keys(
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
            "timed_out",
            "timeout_seconds",
            "umask",
        },
        "local closure invocation",
    )
    require(
        invocation["argv"] == ["just", "ksg-composite-v6"]
        and invocation["cwd"] == "<REPOSITORY_ROOT>"
        and invocation["environment"] == LOCAL_NORMALIZED_ENVIRONMENT
        and type(invocation["environment_routes_sha256"]) is str
        and SHA256_RE.fullmatch(invocation["environment_routes_sha256"]) is not None
        and invocation["exit_code"] == 0
        and type(invocation["exit_code"]) is int
        and invocation["signal"] is None
        and invocation["timed_out"] is False
        and invocation["timeout_seconds"] == 14400
        and type(invocation["timeout_seconds"]) is int
        and invocation["umask"] == "0077"
        and invocation["monotonic_start_ns"] == 0
        and type(invocation["monotonic_start_ns"]) is int
        and type(invocation["monotonic_finish_ns"]) is int
        and invocation["monotonic_finish_ns"] > 0
        and type(invocation["elapsed_monotonic_ns"]) is int
        and invocation["elapsed_monotonic_ns"] == invocation["monotonic_finish_ns"],
        "local closure fixed command or execution result changed",
    )
    stdout = decode_local_binding(
        invocation["stdout"], "local closure command stdout", MAX_LOCAL_STREAM_BYTES
    )
    stderr = decode_local_binding(
        invocation["stderr"], "local closure command stderr", MAX_LOCAL_STREAM_BYTES
    )
    require(stdout + stderr != b"", "local closure command retained no output")
    reject_local_sensitive_bytes(stdout, "local closure command stdout")
    reject_local_sensitive_bytes(stderr, "local closure command stderr")
    started = parse_local_timestamp(invocation["started_at"], "local closure start")
    finished = parse_local_timestamp(invocation["finished_at"], "local closure finish")
    require(
        before_time <= started <= finished <= after_time,
        "local closure wall-clock observations are reordered",
    )
    platform_value = exact_keys(
        root["platform"],
        {
            "architecture",
            "operating_system",
            "operating_system_release",
            "python_implementation",
            "python_version",
        },
        "local closure platform",
    )
    require(
        platform_value["architecture"] in {"arm64", "aarch64"}
        and platform_value["operating_system"] == "Darwin"
        and type(platform_value["operating_system_release"]) is str
        and re.fullmatch(
            r"[0-9A-Za-z._+-]{1,128}", platform_value["operating_system_release"]
        )
        is not None
        and platform_value["python_implementation"] == "CPython"
        and type(platform_value["python_version"]) is str
        and re.fullmatch(
            r"3\.(?:1[1-9]|[2-9][0-9])\.[0-9]+", platform_value["python_version"]
        )
        is not None,
        "local closure platform contract changed",
    )
    executables = validate_local_reviewed_executables(root["reviewed_executables"])
    return {
        "authorities_sha256": sha256(
            canonical_json(expected_authorities, pretty=False)
        ),
        "command": {
            "argv": invocation["argv"],
            "elapsed_monotonic_ns": invocation["elapsed_monotonic_ns"],
            "environment_routes_sha256": invocation["environment_routes_sha256"],
            "exit_code": invocation["exit_code"],
            "finished_at": invocation["finished_at"],
            "started_at": invocation["started_at"],
            "stderr_sha256": invocation["stderr"]["sha256"],
            "stderr_size_bytes": invocation["stderr"]["size_bytes"],
            "stdout_sha256": invocation["stdout"]["sha256"],
            "stdout_size_bytes": invocation["stdout"]["size_bytes"],
            "timed_out": invocation["timed_out"],
            "umask": invocation["umask"],
        },
        "platform": platform_value,
        "repository_state": {
            "after_observed_at": after["observed_at"],
            "after_status_sha256": after["status"]["sha256"],
            "after_status_size_bytes": after["status"]["size_bytes"],
            "before_observed_at": before["observed_at"],
            "before_status_sha256": before["status"]["sha256"],
            "before_status_size_bytes": before["status"]["size_bytes"],
            "c6_commit": c6,
            "c6_tree": c6_tree,
            "http_alternates": before["http_alternates"],
            "info_attributes_rules": before["info_attributes_rules"],
            "info_exclude_rules": before["info_exclude_rules"],
        },
        "reviewed_executables_sha256": sha256(
            canonical_json(executables, pretty=False)
        ),
        "schema": "pid-rs/ksg-rev4-m1a-composite-local-qualification-observation/v1",
    }


def decode_capture_row(row: Any, label: str) -> tuple[dict[str, Any], bytes]:
    value = exact_keys(
        row,
        {
            "body_base64",
            "body_sha256",
            "body_size_bytes",
            "logical_request",
            "media_type",
            "page",
            "path",
            "redirect",
            "repetition",
            "response_kind",
            "status_code",
        },
        label,
    )
    kind = value["response_kind"]
    media = {
        "json": {"application/json", "application/octet-stream"},
        "zip": {"application/zip", "application/octet-stream"},
        "log": {"text/plain", "application/octet-stream"},
    }
    require(
        type(value["body_base64"]) is str
        and type(value["body_sha256"]) is str
        and SHA256_RE.fullmatch(value["body_sha256"]) is not None
        and type(value["logical_request"]) is str
        and type(value["path"]) is str
        and value["path"].startswith(f"/repos/{REPOSITORY}/")
        and value["repetition"] in {1, 2}
        and type(value["repetition"]) is int
        and type(value["page"]) is int
        and value["page"] >= 0
        and value["status_code"] == 200
        and type(value["status_code"]) is int
        and kind in media
        and value["media_type"] in media[kind],
        f"{label} scalar contract changed",
    )
    redirect = value["redirect"]
    if kind == "json":
        require(redirect is None, f"{label} JSON response unexpectedly redirected")
    elif redirect is not None:
        redirection = exact_keys(
            redirect,
            {"status_code", "target_host", "target_url_sha256"},
            f"{label} redirect",
        )
        require(
            redirection["status_code"] in {301, 302, 303, 307, 308}
            and type(redirection["status_code"]) is int
            and type(redirection["target_host"]) is str
            and re.fullmatch(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
                r"(?:blob\.core\.windows\.net|githubusercontent\.com)",
                redirection["target_host"],
            )
            is not None
            and type(redirection["target_url_sha256"]) is str
            and SHA256_RE.fullmatch(redirection["target_url_sha256"]) is not None,
            f"{label} redirect contract changed",
        )
    size = exact_int(value["body_size_bytes"], f"{label} body size")
    require(size <= MAX_JSON_BYTES, f"{label} body exceeds bound")
    try:
        raw = base64.b64decode(value["body_base64"], validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ContractError(f"{label} body is not canonical base64: {error}") from None
    require(
        base64.b64encode(raw).decode("ascii") == value["body_base64"]
        and len(raw) == size
        and sha256(raw) == value["body_sha256"],
        f"{label} body binding changed",
    )
    if kind == "json":
        parse_json(raw, label, canonical=False)
    elif kind == "zip":
        require(raw.startswith(b"PK"), f"{label} is not a ZIP archive")
        logical_match = re.fullmatch(
            r"(?:predecessor|successor)_(?:ci|codeql|contract)_artifact_([0-9]+)",
            value["logical_request"],
        )
        path_match = re.fullmatch(
            rf"/repos/{re.escape(REPOSITORY)}/actions/artifacts/([0-9]+)/zip",
            value["path"],
        )
        require(
            logical_match is not None
            and path_match is not None
            and logical_match.group(1) == path_match.group(1),
            f"{label} artifact logical/path identity changed",
        )
    else:
        require(raw != b"", f"{label} failed-job log is empty")
        logical_match = re.fullmatch(
            r"predecessor_(?:ci|codeql|contract)_failed_job_([0-9]+)_log",
            value["logical_request"],
        )
        path_match = re.fullmatch(
            rf"/repos/{re.escape(REPOSITORY)}/actions/jobs/([0-9]+)/logs",
            value["path"],
        )
        require(
            logical_match is not None
            and path_match is not None
            and logical_match.group(1) == path_match.group(1),
            f"{label} failed-job logical/path identity changed",
        )
    return value, raw


@dataclass
class CaptureRows:
    groups: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]]

    def take(self, logical: str, repetition: int) -> list[tuple[dict[str, Any], bytes]]:
        key = (logical, repetition)
        require(
            key in self.groups,
            f"capture request is absent: {logical} repetition {repetition}",
        )
        return self.groups.pop(key)

    def finish(self) -> None:
        require(
            not self.groups, f"unexpected capture request groups: {sorted(self.groups)}"
        )


def validate_capture_root(
    capture_raw: bytes,
    phase: str,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    capture_schema: dict[str, Any],
) -> tuple[dict[str, Any], CaptureRows]:
    value = parse_json(capture_raw, f"composite-v6 {phase} hosted capture")
    validate_schema_instance(
        value, capture_schema, f"composite-v6 {phase} hosted capture"
    )
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v5_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        f"composite-v6 {phase} capture",
    )
    expected_subject = {
        "predecessor_commit": C5_COMMIT,
        "predecessor_tree": C5_TREE,
    }
    if phase == "successor_qualification":
        expected_subject.update({"successor_commit": c6, "successor_tree": c6_tree})
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v6"
        and root["schema_revision"] == 6
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["phase"] == phase
        and root["subject"] == expected_subject
        and root["capture_tool"] == descriptor(c6_entries, CAPTURE_TOOL_RELATIVE)
        and root["immutable_v5_primitives"] == V5_CAPTURE_PRIMITIVE
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS,
        f"composite-v6 {phase} capture identity changed",
    )
    roles = PHASE_ROLES[phase]
    runs = exact_keys(root["runs"], set(roles), f"composite-v6 {phase} run map")
    require(
        all(type(item) is int and item > 0 for item in runs.values())
        and len(set(runs.values())) == 3
        and (phase != "predecessor_failure" or runs == PREDECESSOR_RUNS),
        f"composite-v6 {phase} run identifiers changed or overlap",
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
            event["attempt"] in {1, 2}
            and type(event["attempt"]) is int
            and event["repetition"] in {1, 2}
            and type(event["repetition"]) is int
            and event["category"]
            in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(event["logical_request"]) is str
            and type(event["page"]) is int
            and event["page"] >= 0
            and type(event["path"]) is str
            and event["path"].startswith(f"/repos/{REPOSITORY}/")
            and type(event["response_sha256"]) is str
            and SHA256_RE.fullmatch(event["response_sha256"]) is not None
            and type(event["response_size_bytes"]) is int
            and 0 <= event["response_size_bytes"] <= MAX_JSON_BYTES,
            "capture retry event changed",
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
        type(captures) is list and 0 < len(captures) <= MAX_CAPTURE_ROWS,
        "capture response count is outside the bound",
    )
    decoded = [
        decode_capture_row(item, f"capture response {index}")
        for index, item in enumerate(captures)
    ]
    require(
        sum(len(raw) for _row, raw in decoded) <= MAX_CAPTURE_BODY_BYTES,
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
        all(
            attempts == list(range(1, len(attempts) + 1))
            for attempts in retry_groups.values()
        ),
        "retry attempts are not consecutive and bounded",
    )
    grouped: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]] = defaultdict(
        list
    )
    for row, raw in decoded:
        grouped[(row["logical_request"], row["repetition"])].append((row, raw))
    return root, CaptureRows(dict(grouped))


def normalized_run(value: Any, role: str, run_id: int, head: str) -> dict[str, Any]:
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
        and result["repository_id"] > 0
        and head_repository.get("id") == result["repository_id"]
        and all(
            type(result[key]) is str and result[key]
            for key in ("event", "name", "path")
        ),
        f"{role} run identity or disposition changed",
    )
    kind = ROLE_KIND[role]
    if kind == "ci":
        require(
            result["workflow_id"] == 297369773
            and result["name"] == "CI"
            and result["path"] == ".github/workflows/ci.yml"
            and result["event"] == "push",
            f"{role} CI workflow identity changed",
        )
    elif kind == "codeql":
        require(
            result["workflow_id"] == 310582096
            and result["name"] == "Push on main"
            and result["path"] == "dynamic/github-code-scanning/codeql"
            and result["event"] == "dynamic",
            f"{role} CodeQL workflow identity changed",
        )
    else:
        version = "v5" if role.startswith("predecessor_") else "v6"
        require(
            result["name"] == f"KSG M1a composite {version}"
            and result["path"] == f".github/workflows/ksg-m1a-composite-{version}.yml"
            and result["event"] == "push",
            f"{role} contract workflow identity changed",
        )
    return result


def validate_predecessor_failed_set(role: str, failed: set[int]) -> None:
    required_failed = PREDECESSOR_REQUIRED_FAILED_JOB_IDS[role]
    require(
        failed == required_failed,
        f"{role} lost a required failed-job identity",
    )


def validate_predecessor_failure_identities(
    role: str, jobs: list[dict[str, Any]], failed: set[int]
) -> None:
    validate_predecessor_failed_set(role, failed)
    by_id = {item["job_id"]: item for item in jobs}
    expected = PREDECESSOR_REQUIRED_FAILURE_IDENTITIES[role]
    require(set(expected) <= set(by_id), f"{role} required failed jobs are absent")
    for job_id, (job_name, failed_steps) in expected.items():
        job = by_id[job_id]
        observed_steps = tuple(
            sorted(
                item["name"] for item in job["steps"] if item["conclusion"] == "failure"
            )
        )
        require(
            job["conclusion"] == "failure"
            and job["name"] == job_name
            and observed_steps == failed_steps,
            f"{role} required failure identity changed for job {job_id}",
        )


def normalized_job_timestamps(
    value: dict[str, Any], conclusion: Any, role: str
) -> tuple[str | None, str | None]:
    require(
        "started_at" in value and "completed_at" in value,
        f"{role} job timestamp fields are absent",
    )
    started_raw = value["started_at"]
    completed_raw = value["completed_at"]
    if started_raw is None or completed_raw is None:
        require(
            started_raw is None and completed_raw is None and conclusion == "skipped",
            f"{role} job has an unsupported missing timestamp",
        )
    else:
        require(
            type(started_raw) is str and type(completed_raw) is str,
            f"{role} job timestamps have the wrong type",
        )
        started = parse_utc_timestamp(started_raw, f"{role} job start")
        completed = parse_utc_timestamp(completed_raw, f"{role} job completion")
        require(started <= completed, f"{role} job timestamps are reversed")
    return started_raw, completed_raw


def normalized_jobs(
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
        started_raw, completed_raw = normalized_job_timestamps(value, conclusion, role)
        steps_raw = value.get("steps")
        require(
            type(steps_raw) is list
            and (steps_raw != [] or conclusion in {"skipped", "cancelled"}),
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
                and normalized["conclusion"]
                in {"success", "failure", "skipped", "cancelled"}
                and type(normalized["name"]) is str
                and normalized["name"]
                and type(normalized["number"]) is int
                and normalized["number"] > 0,
                f"{role} step identity or disposition changed",
            )
            steps.append(normalized)
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
                f"{role} successful job contains an adverse step",
            )
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
    require(
        len(jobs) == len({item["job_id"] for item in jobs}), f"{role} job IDs overlap"
    )
    failed = {item["job_id"] for item in jobs if item["conclusion"] == "failure"}
    expected_count = (
        45 if ROLE_KIND[role] == "ci" else 4 if ROLE_KIND[role] == "codeql" else 1
    )
    require(len(jobs) == expected_count, f"{role} job count changed")
    if role.startswith("successor_") or role == "predecessor_codeql":
        require(
            all(item["conclusion"] == "success" for item in jobs),
            f"{role} has an adverse job",
        )
    else:
        validate_predecessor_failure_identities(role, jobs, failed)
    names = tuple(sorted(item["name"] for item in jobs))
    if ROLE_KIND[role] == "ci":
        require(names == _v5._v4.EXPECTED_CI_JOB_NAMES, f"{role} CI job roster changed")
    elif ROLE_KIND[role] == "codeql":
        require(
            names
            == tuple(
                sorted(f"Analyze ({language})" for language in _v5._v4.LANGUAGE_ORDER)
            ),
            f"{role} CodeQL job roster changed",
        )
    else:
        expected = (
            "Validate the composite-v5 correction contract"
            if role.startswith("predecessor_")
            else "Validate the composite-v6 correction contract"
        )
        require(names == (expected,), f"{role} contract job name changed")
        step_names = [item["name"] for item in jobs[0]["steps"]]
        if role == "predecessor_contract":
            required_steps = {
                "Validate the bounded successor publication",
                "Validate fresh replay and current-source custody",
                "Validate static v5 contract in normal and optimized modes",
                "Upload the exact v5 static result",
            }
            require(
                all(step_names.count(name) == 1 for name in required_steps)
                and [
                    item["name"]
                    for item in jobs[0]["steps"]
                    if item["conclusion"] == "failure"
                ]
                == ["Validate the bounded successor publication"],
                "predecessor contract failure-step identity changed",
            )
        else:
            required_steps = {
                "Install the hash-pinned PDF verifier dependency",
                "Install the runner PDF toolchain",
                "Normalize only the reviewed inert checkout residue",
                "Refuse retries and non-main qualification events",
                "Recheck retained C5 operational surfaces",
                "Validate immutable predecessor PDF portability and the bounded successor publication",
                "Validate fresh replay and current-source custody",
                "Validate static v6 contract in normal and optimized modes",
                "Upload the exact v6 static result",
            }
            require(
                all(step_names.count(name) == 1 for name in required_steps)
                and all(
                    next(item for item in jobs[0]["steps"] if item["name"] == name)[
                        "conclusion"
                    ]
                    == "success"
                    for name in required_steps
                ),
                "successor contract bounded-repair step roster changed",
            )
    return jobs, failed


def failed_job_logs(
    rows: CaptureRows,
    role: str,
    failed_ids: set[int],
    jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {item["job_id"]: item for item in jobs}
    require(
        set(by_id) >= failed_ids,
        f"{role} failed-job metadata is absent from the normalized roster",
    )
    repetitions: list[list[dict[str, Any]]] = []
    for repetition in (1, 2):
        values: list[dict[str, Any]] = []
        for job_id in sorted(failed_ids):
            logical = f"{role}_failed_job_{job_id}_log"
            captures = rows.take(logical, repetition)
            require(
                len(captures) == 1
                and captures[0][0]["page"] == 0
                and captures[0][0]["path"]
                == f"/repos/{REPOSITORY}/actions/jobs/{job_id}/logs"
                and captures[0][0]["response_kind"] == "log",
                f"{role} failed-job log capture changed",
            )
            raw = captures[0][1]
            job = by_id[job_id]
            failed_steps = sorted(
                item["name"] for item in job["steps"] if item["conclusion"] == "failure"
            )
            require(
                failed_steps and len(failed_steps) == len(set(failed_steps)),
                f"{role} failed-step names are absent or duplicated",
            )
            observed_markers = observed_failure_markers(job_id, raw, role)
            values.append(
                {
                    "failed_steps": failed_steps,
                    "job_id": job_id,
                    "job_name": job["name"],
                    "observed_markers": observed_markers,
                    "sha256": sha256(raw),
                    "size_bytes": len(raw),
                }
            )
        repetitions.append(values)
    require(repetitions[0] == repetitions[1], f"{role} repeated failed-job logs differ")
    return repetitions[0]


def observed_failure_markers(job_id: int, raw: bytes, role: str) -> list[str]:
    markers = PREDECESSOR_REQUIRED_LOG_MARKERS.get(job_id, ())
    require(
        all(marker.encode("ascii") in raw for marker in markers),
        f"{role} required failed-job log marker changed for job {job_id}",
    )
    return list(markers)


def validate_contract_artifact(
    artifacts: list[dict[str, Any]], archives: dict[int, bytes], c6: str, c6_tree: str
) -> None:
    require(len(artifacts) == 1, "successor contract artifact count changed")
    artifact = artifacts[0]
    require(
        artifact["name"] == f"ksg-m1a-composite-v6-static-{c6}",
        "successor contract artifact name changed",
    )
    path = "ksg-m1a-composite-v6-static.json"
    matches = [item for item in artifact["members"] if item["path"] == path]
    require(
        len(matches) == 1 and artifact["members"] == matches,
        "successor contract artifact members changed",
    )
    raw = member_bytes(
        archives[artifact["artifact_id"]], path, "successor contract artifact"
    )
    value = parse_json(raw, "successor contract static result", canonical=False)
    require(
        raw == canonical_json(value, pretty=False)
        and value
        == {
            "c5_commit": C5_COMMIT,
            "c6_commit": c6,
            "head": c6,
            "r6_commit": None,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v6-static-validation/v1",
            "tree": c6_tree,
        },
        "successor contract static result changed",
    )


def receipt_artifacts(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "archive_sha256": item["archive_sha256"],
            "archive_size_bytes": item["archive_size_bytes"],
            "artifact_id": item["artifact_id"],
            "members_sha256": project_digest(item["members"]),
            "name": item["name"],
        }
        for item in artifacts
    ]


def derive_role_observation(
    rows: CaptureRows,
    role: str,
    run_id: int,
    head: str,
    entries: dict[str, Any],
    tree: str,
) -> dict[str, Any]:
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
        run = normalized_run(
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
        jobs, failed = normalized_jobs(
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
        artifacts, archives = normalized_artifacts_v5(
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
            analysis_values = paged_json_response(
                rows,
                f"{role}_analyses",
                repetition,
                f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
                None,
            )
            analyses = normalized_analyses_v5(analysis_values, jobs, head, role)
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
            alerts = normalized_alerts_v5(alert_values, role)
        repeated.append((run, jobs, artifacts, archives, analyses, alerts))
        failed_sets.append(failed)
    first = repeated[0]
    second = repeated[1]
    require(
        canonical_json((first[0], first[1], first[2], first[4], first[5]), pretty=False)
        == canonical_json(
            (second[0], second[1], second[2], second[4], second[5]), pretty=False
        ),
        f"{role} repeated normalized observations differ",
    )
    run, jobs, artifacts, archives, analyses, alerts = first
    if role == "predecessor_codeql" or role == "predecessor_contract":
        require(artifacts == [], f"{role} unexpectedly published artifacts")
    if role == "successor_codeql":
        require(artifacts == [], "successor CodeQL unexpectedly published artifacts")
    elif role == "successor_ci":
        validate_postcommit_artifact(artifacts, archives, entries, head, tree, role)
    elif role == "successor_contract":
        validate_contract_artifact(artifacts, archives, head, tree)
    logs = (
        failed_job_logs(rows, role, failed_sets[0], jobs)
        if role.startswith("predecessor_")
        else []
    )
    require(
        failed_sets[0] == failed_sets[1],
        f"{role} repeated failed-job identities differ",
    )
    compact_artifacts = receipt_artifacts(artifacts)
    return {
        "artifacts": compact_artifacts,
        "artifacts_sha256": project_digest(artifacts),
        "codeql_alerts_sha256": None if alerts is None else project_digest(alerts),
        "codeql_analysis_ids": (
            [] if analyses is None else [item["analysis_id"] for item in analyses]
        ),
        "codeql_analyses_sha256": None
        if analyses is None
        else project_digest(analyses),
        "failed_job_logs": logs,
        "failed_job_logs_sha256": project_digest(logs),
        "job_count": len(jobs),
        "job_ids": [item["job_id"] for item in jobs],
        "jobs_sha256": project_digest(jobs),
        "kind": ROLE_KIND[role],
        "role": role,
        "run": run,
    }


def validate_identifier_domains(phases: list[dict[str, Any]], label: str) -> None:
    roles = [item for phase in phases for item in phase["roles"]]
    repository_ids = [item["run"]["repository_id"] for item in roles]
    require(
        len(set(repository_ids)) == 1,
        f"{label} repository identifier join changed",
    )
    run_ids = [item["run"]["run_id"] for item in roles]
    require(
        len(run_ids) == len(set(run_ids)),
        f"{label} hosted run identifier domains overlap",
    )
    for field, resource in (
        ("job_ids", "job"),
        ("codeql_analysis_ids", "CodeQL analysis"),
    ):
        identifiers = [identifier for item in roles for identifier in item[field]]
        require(
            len(identifiers) == len(set(identifiers)),
            f"{label} {resource} identifier domains overlap",
        )
    artifact_ids = [
        artifact["artifact_id"] for item in roles for artifact in item["artifacts"]
    ]
    require(
        len(artifact_ids) == len(set(artifact_ids)),
        f"{label} artifact identifier domains overlap",
    )


def derive_phase(
    capture_raw: bytes,
    phase: str,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    capture_schema: dict[str, Any],
) -> dict[str, Any]:
    capture, rows = validate_capture_root(
        capture_raw, phase, c6_entries, c6, c6_tree, capture_schema
    )
    head = C5_COMMIT if phase == "predecessor_failure" else c6
    tree = C5_TREE if phase == "predecessor_failure" else c6_tree
    entries = parse_tree(tree)
    roles = [
        derive_role_observation(rows, role, capture["runs"][role], head, entries, tree)
        for role in PHASE_ROLES[phase]
    ]
    rows.finish()
    repository_ids = [item["run"]["repository_id"] for item in roles]
    require(len(set(repository_ids)) == 1, f"{phase} repository identities disagree")
    result = {"capture_sha256": sha256(capture_raw), "phase": phase, "roles": roles}
    validate_identifier_domains([result], phase)
    return result


def contract_authorities(
    c5_entries: dict[str, Any], c6_entries: dict[str, Any]
) -> list[dict[str, Any]]:
    values = [
        authority_descriptor(
            c5_entries, V5_CHECKER_RELATIVE, "immutable_v5_checker_primitives"
        ),
        authority_descriptor(
            c5_entries, V5_CAPTURE_PRIMITIVE["path"], "immutable_v5_capture_primitives"
        ),
        authority_descriptor(c5_entries, V5_WORKFLOW_RELATIVE, "published_c5_workflow"),
        authority_descriptor(c6_entries, V5_WORKFLOW_RELATIVE, "retired_v5_workflow"),
        authority_descriptor(c6_entries, V6_WORKFLOW_RELATIVE, "successor_v6_workflow"),
        authority_descriptor(c6_entries, CHECKER_RELATIVE, "v6_checker"),
        authority_descriptor(c6_entries, SELF_TEST_RELATIVE, "v6_checker_self_test"),
        authority_descriptor(
            c6_entries,
            CURRENT_HOSTED_RECOVERY_SELF_TEST_RELATIVE,
            "current_hosted_recovery_hostile_suite",
        ),
        authority_descriptor(
            c6_entries,
            CURRENT_HOSTED_RECOVERY_CHECKER_RELATIVE,
            "current_hosted_recovery_gate",
        ),
        authority_descriptor(c6_entries, CAPTURE_TOOL_RELATIVE, "v6_capture_tool"),
        authority_descriptor(c6_entries, CAPTURE_SCHEMA_RELATIVE, "v6_capture_schema"),
        authority_descriptor(
            c6_entries,
            LOCAL_CLOSURE_TOOL_RELATIVE,
            "v6_local_closure_capture_tool",
        ),
        authority_descriptor(
            c6_entries, LOCAL_CLOSURE_SCHEMA_RELATIVE, "v6_local_closure_schema"
        ),
        authority_descriptor(c6_entries, RECEIPT_SCHEMA_RELATIVE, "v6_receipt_schema"),
        authority_descriptor(c6_entries, POLICY_RELATIVE, "v6_path_policy"),
        authority_descriptor(c6_entries, JUSTFILE_RELATIVE, "local_command_wiring"),
        authority_descriptor(
            c6_entries, CURRENT_SOURCE_RELATIVE, "c6_current_source_state"
        ),
        authority_descriptor(c6_entries, LEAN_R10_RELATIVE, "prior_r10_lean_replay"),
        authority_descriptor(c6_entries, LEAN_R11_RELATIVE, "current_r11_lean_replay"),
    ]
    values.extend(
        authority_descriptor(c6_entries, path, role)
        for path, _mode, role in PROCESS_ARTIFACTS
    )
    return sorted(values, key=lambda item: (item["path"], item["role"]))


def derive_local_qualification(
    local_raw: bytes,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    local_schema: dict[str, Any],
) -> dict[str, Any]:
    return {
        "observation": validate_local_closure_record(
            local_raw, c6_entries, c6, c6_tree, local_schema
        ),
        "record_binding": {
            "path": LOCAL_CLOSURE_RELATIVE,
            "sha256": sha256(local_raw),
            "size_bytes": len(local_raw),
        },
    }


def derive_receipt(
    predecessor_raw: bytes,
    local_raw: bytes,
    successor_raw: bytes,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    capture_schema: dict[str, Any],
    local_schema: dict[str, Any],
) -> dict[str, Any]:
    predecessor = derive_phase(
        predecessor_raw,
        "predecessor_failure",
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
    )
    successor = derive_phase(
        successor_raw,
        "successor_qualification",
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
    )
    local_qualification = derive_local_qualification(
        local_raw, c6_entries, c6, c6_tree, local_schema
    )
    validate_identifier_domains([predecessor, successor], "predecessor/successor")
    c5_entries = parse_tree(C5_TREE)
    return {
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
        "contract_authorities": contract_authorities(c5_entries, c6_entries),
        "local_qualification": local_qualification,
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "observations": [predecessor, successor],
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v6",
        "schema_revision": 6,
        "subject": {
            "c5_commit": C5_COMMIT,
            "c5_tree": C5_TREE,
            "c6_commit": c6,
            "c6_tree": c6_tree,
        },
        "verdict": {
            "c5_hosted_qualification": "failed_zero_credit",
            "c5_publication": "published",
            "c6_bounded_repair": "pass",
            "c6_hosted_observation": "pass",
            "c6_local_qualification": "pass",
            "r5_receipt_issued": False,
            "r6_receipt_issued": True,
            "scientific_validation": "not_adjudicated",
        },
    }


def _ancestry_commits(start: str, head: str) -> list[str]:
    if start == head:
        return [start]
    raw = git("rev-list", "--reverse", "--ancestry-path", f"{start}..{head}")
    try:
        descendants = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"descendant history is not ASCII: {error}") from None
    require(
        descendants and descendants[-1] == head,
        "HEAD is not on the required ancestry path",
    )
    return [start, *descendants]


def _new_reachable_commits(start: str, head: str) -> list[str]:
    raw = git("rev-list", "--reverse", f"{start}..{head}")
    try:
        commits = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ContractError(f"new reachable history is not ASCII: {error}") from None
    require(
        all(SHA1_RE.fullmatch(item) is not None for item in commits),
        "new reachable history contains a malformed commit identity",
    )
    return [start, *commits]


def _validate_no_r4_r5_history(c6: str, head: str) -> None:
    for oid in _new_reachable_commits(C5_COMMIT, head):
        tree = C5_TREE if oid == C5_COMMIT else parse_descendant_tree(oid)
        entries = parse_tree(tree)
        raw_commit = _v5._v4.exact_object(oid, "commit", maximum=1024 * 1024)
        _headers, separator, message_raw = raw_commit.partition(b"\n\n")
        require(separator == b"\n\n", f"commit message envelope changed at {oid[:12]}")
        try:
            message = message_raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ContractError(
                f"descendant commit message is not UTF-8 at {oid[:12]}: {error}"
            ) from None
        validate_no_r4_r5_tree_message(entries, message, oid)
    require(
        git_predicate("merge-base", "--is-ancestor", c6, head),
        "C6 is not an ancestor of HEAD",
    )


def validate_no_r4_r5_tree_message(
    entries: dict[str, Any], message: str, oid: str
) -> None:
    require(
        all(path not in entries for path in FORBIDDEN_R4_R5_EVIDENCE_PATHS),
        f"forbidden R4/R5 path appeared in history at {oid[:12]}",
    )
    require(
        message not in {FORBIDDEN_R4_MESSAGE, FORBIDDEN_R5_MESSAGE},
        "forbidden R4/R5 commit message appeared in history",
    )


def validate_topology(head: str, head_tree: str) -> tuple[str, str, str | None]:
    c5 = parse_commit(C5_COMMIT)
    require(
        c5.tree == C5_TREE
        and c5.parent == C5_PARENT
        and c5.message == C5_MESSAGE
        and (c5.author, c5.committer) == C5_IDENTITY,
        "published C5 exact commit envelope changed",
    )
    c5_entries = parse_tree(C5_TREE)
    require_exact_bytes(
        c5_entries,
        V5_CHECKER_RELATIVE,
        V5_CHECKER_SHA256,
        V5_CHECKER_SIZE_BYTES,
        "immutable v5 checker primitives",
    )
    require_exact_bytes(
        c5_entries,
        V5_CAPTURE_PRIMITIVE["path"],
        V5_CAPTURE_PRIMITIVE["sha256"],
        V5_CAPTURE_PRIMITIVE["size_bytes"],
        "immutable v5 capture primitives",
    )
    require_exact_bytes(
        c5_entries,
        V5_WORKFLOW_RELATIVE,
        V5_WORKFLOW_SHA256,
        V5_WORKFLOW_SIZE_BYTES,
        "published C5 workflow",
    )
    require(
        all(path not in c5_entries for path in FORBIDDEN_R4_R5_EVIDENCE_PATHS),
        "published C5 contains forbidden R4/R5 evidence",
    )
    head_entries = parse_tree(head_tree)
    receipt_present = RECEIPT_RELATIVE in head_entries
    if receipt_present:
        r6 = _v5._v4.commit_introducing(RECEIPT_RELATIVE)
        r6_commit = parse_commit(r6)
        require(r6_commit.message == R6_MESSAGE, "R6 exact message changed")
        c6 = r6_commit.parent
    else:
        r6 = None
        c6 = head
    c6_commit = parse_commit(c6)
    require(
        c6_commit.parent == C5_COMMIT and c6_commit.message == C6_MESSAGE,
        "C6 is not the exact unsigned direct child of published C5",
    )
    c6_entries = parse_tree(c6_commit.tree)
    policy_delta = validate_policy(c6_entries)
    validate_exact_delta(
        changed_entries(c5_entries, c6_entries), policy_delta, "C6 path-policy"
    )
    require(
        PREDECESSOR_CAPTURE_RELATIVE in c6_entries
        and LOCAL_CLOSURE_RELATIVE not in c6_entries
        and SUCCESSOR_CAPTURE_RELATIVE not in c6_entries
        and RECEIPT_RELATIVE not in c6_entries,
        "C6 predecessor/local/successor evidence phase separation changed",
    )
    require_exact_bytes(
        c6_entries,
        V5_CHECKER_RELATIVE,
        V5_CHECKER_SHA256,
        V5_CHECKER_SIZE_BYTES,
        "C6-retained immutable v5 checker primitives",
    )
    require_exact_bytes(
        c6_entries,
        V5_CAPTURE_PRIMITIVE["path"],
        V5_CAPTURE_PRIMITIVE["sha256"],
        V5_CAPTURE_PRIMITIVE["size_bytes"],
        "C6-retained immutable v5 capture primitives",
    )
    validate_replay_pair(c6_entries)
    _v5._v4.validate_current_source(c6_entries, "C6")
    retired_v5_workflow_raw = require_exact_bytes(
        c6_entries,
        V5_WORKFLOW_RELATIVE,
        RETIRED_V5_WORKFLOW_SHA256,
        RETIRED_V5_WORKFLOW_SIZE_BYTES,
        "retired live v5 workflow",
    )
    v6_workflow_raw = require_exact_bytes(
        c6_entries,
        V6_WORKFLOW_RELATIVE,
        V6_WORKFLOW_SHA256,
        V6_WORKFLOW_SIZE_BYTES,
        "successor live v6 workflow",
    )
    validate_frozen_workflow_values(retired_v5_workflow_raw, v6_workflow_raw)
    validate_v6_workflow_prerequisites(v6_workflow_raw)
    validate_local_l6_values(tree_blob(c6_entries, JUSTFILE_RELATIVE))
    current_hosted_recovery_self_test_raw = require_exact_bytes(
        c6_entries,
        CURRENT_HOSTED_RECOVERY_SELF_TEST_RELATIVE,
        CURRENT_HOSTED_RECOVERY_SELF_TEST_SHA256,
        CURRENT_HOSTED_RECOVERY_SELF_TEST_SIZE_BYTES,
        "current hosted-recovery hostile suite",
    )
    current_hosted_recovery_checker_raw = require_exact_bytes(
        c6_entries,
        CURRENT_HOSTED_RECOVERY_CHECKER_RELATIVE,
        CURRENT_HOSTED_RECOVERY_CHECKER_SHA256,
        CURRENT_HOSTED_RECOVERY_CHECKER_SIZE_BYTES,
        "current hosted-recovery gate",
    )
    validate_current_hosted_recovery_values(
        current_hosted_recovery_self_test_raw, current_hosted_recovery_checker_raw
    )
    validate_frozen_local_closure_tool(
        require_exact_bytes(
            c6_entries,
            LOCAL_CLOSURE_TOOL_RELATIVE,
            LOCAL_CLOSURE_TOOL_SHA256,
            LOCAL_CLOSURE_TOOL_SIZE_BYTES,
            "local-closure capture tool",
        )
    )
    authority_modes = {
        V5_CHECKER_RELATIVE: "100644",
        V5_CAPTURE_PRIMITIVE["path"]: "100644",
        CHECKER_RELATIVE: "100644",
        SELF_TEST_RELATIVE: "100644",
        CAPTURE_TOOL_RELATIVE: "100644",
        CAPTURE_SCHEMA_RELATIVE: "100644",
        LOCAL_CLOSURE_TOOL_RELATIVE: "100644",
        LOCAL_CLOSURE_SCHEMA_RELATIVE: "100644",
        RECEIPT_SCHEMA_RELATIVE: "100644",
        POLICY_RELATIVE: "100644",
        JUSTFILE_RELATIVE: "100644",
        PREDECESSOR_CAPTURE_RELATIVE: "100644",
        CURRENT_SOURCE_RELATIVE: "100644",
        LEAN_R10_RELATIVE: "100644",
        LEAN_R11_RELATIVE: "100644",
        V5_WORKFLOW_RELATIVE: "100644",
        V6_WORKFLOW_RELATIVE: "100644",
        CURRENT_HOSTED_RECOVERY_SELF_TEST_RELATIVE: "100644",
        CURRENT_HOSTED_RECOVERY_CHECKER_RELATIVE: "100644",
        **{path: mode for path, mode, _role in PROCESS_ARTIFACTS},
    }
    for path, mode in authority_modes.items():
        require(
            path in c6_entries and c6_entries[path].mode == mode,
            f"C6 authority absent or wrong mode: {path}",
        )
    require(
        read_repository_file(
            CHECKER_RELATIVE, maximum=_v5._v4.MAX_BLOB_BYTES, mode=0o644
        )
        == tree_blob(c6_entries, CHECKER_RELATIVE),
        "executing v6 checker bytes differ from the C6 authority blob",
    )
    _validate_no_r4_r5_history(c6, head)
    if r6 is None:
        require(head == c6, "receipt-absent state is not exact C6")
        validate_worktree(c6_entries, head, head_tree)
        return c6, c6_commit.tree, None
    require(
        git_predicate("merge-base", "--is-ancestor", r6, head),
        "R6 is not an ancestor of HEAD",
    )
    r6_commit = parse_commit(r6)
    require(
        r6_commit.parent == c6 and r6_commit.message == R6_MESSAGE,
        "R6 topology changed",
    )
    r6_entries = parse_tree(r6_commit.tree)
    expected_r6_delta = tuple(
        (path, status, mode) for path, status, mode, _role in R6_POLICY_ROWS
    )
    validate_exact_delta(
        changed_entries(c6_entries, r6_entries), expected_r6_delta, "R6"
    )
    _v5._v4.validate_current_source(r6_entries, "R6")
    retained = tuple(
        sorted(
            (
                set(authority_modes)
                | {
                    POLICY_RELATIVE,
                    PREDECESSOR_CAPTURE_RELATIVE,
                    LOCAL_CLOSURE_RELATIVE,
                    SUCCESSOR_CAPTURE_RELATIVE,
                    RECEIPT_RELATIVE,
                }
            )
            - {CURRENT_SOURCE_RELATIVE}
        )
    )
    for oid in _ancestry_commits(r6, head):
        tree = r6_commit.tree if oid == r6 else parse_descendant_tree(oid)
        entries = parse_tree(tree)
        for path in retained:
            require(
                entries.get(path) == r6_entries.get(path),
                f"retained v6 authority changed: {path}",
            )
        _v5._v4.validate_current_source(entries, f"descendant {oid[:12]}")
    validate_worktree(head_entries, head, head_tree)
    return c6, c6_commit.tree, r6


def validate_receipt_bytes(
    receipt_raw: bytes,
    predecessor_raw: bytes,
    local_raw: bytes,
    successor_raw: bytes,
    c6_entries: dict[str, Any],
    c6: str,
    c6_tree: str,
    capture_schema: dict[str, Any],
    local_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> dict[str, Any]:
    receipt = parse_json(receipt_raw, "composite-v6 receipt")
    validate_schema_instance(receipt, receipt_schema, "composite-v6 receipt")
    expected = derive_receipt(
        predecessor_raw,
        local_raw,
        successor_raw,
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
        local_schema,
    )
    require(
        receipt == expected, "composite-v6 receipt differs from raw-capture derivation"
    )
    return receipt


def static_result(head: str, head_tree: str, c6: str, r6: str | None) -> dict[str, Any]:
    return {
        "c5_commit": C5_COMMIT,
        "c6_commit": c6,
        "head": head,
        "r6_commit": r6,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v6-static-validation/v1",
        "tree": head_tree,
    }


def validate_static() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c6, c6_tree, r6 = validate_topology(head, head_tree)
    c6_entries = parse_tree(c6_tree)
    capture_schema, local_schema, receipt_schema = validate_schema_authorities(
        c6_entries
    )
    predecessor_raw = tree_blob(c6_entries, PREDECESSOR_CAPTURE_RELATIVE)
    derive_phase(
        predecessor_raw,
        "predecessor_failure",
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
    )
    if r6 is not None:
        r6_entries = parse_tree(parse_commit(r6).tree)
        validate_receipt_bytes(
            tree_blob(r6_entries, RECEIPT_RELATIVE),
            predecessor_raw,
            tree_blob(r6_entries, LOCAL_CLOSURE_RELATIVE),
            tree_blob(r6_entries, SUCCESSOR_CAPTURE_RELATIVE),
            c6_entries,
            c6,
            c6_tree,
            capture_schema,
            local_schema,
            receipt_schema,
        )
    return static_result(head, head_tree, c6, r6)


def bounded_stdin() -> bytes:
    raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    require(
        0 < len(raw) <= MAX_JSON_BYTES, "standard-input JSON size is outside the bound"
    )
    return raw


def bounded_regular_fd(fd: int, label: str) -> bytes:
    require(type(fd) is int and fd >= 3, f"{label} descriptor is outside the bound")
    try:
        before = os.fstat(fd)
        offset = os.lseek(fd, 0, os.SEEK_CUR)
    except OSError as error:
        raise ContractError(f"cannot inspect {label} descriptor: {error}") from None
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o600
        and 0 < before.st_size <= MAX_JSON_BYTES
        and offset == 0,
        f"{label} is not one new mode-0600 bounded regular file at offset zero",
    )
    raw = b""
    try:
        while len(raw) < before.st_size:
            chunk = os.read(fd, before.st_size - len(raw))
            require(chunk != b"", f"{label} descriptor ended early")
            raw += chunk
        require(os.read(fd, 1) == b"", f"{label} descriptor grew during read")
        after = os.fstat(fd)
    except OSError as error:
        raise ContractError(f"cannot read {label} descriptor: {error}") from None
    require(
        (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ),
        f"{label} descriptor identity changed during read",
    )
    return raw


def derive_receipt_command(local_fd: int, successor_fd: int) -> dict[str, Any]:
    require(
        local_fd != successor_fd,
        "local-closure and successor-capture descriptors must be distinct",
    )
    head, head_tree = validate_repository()
    c6, c6_tree, r6 = validate_topology(head, head_tree)
    require(
        r6 is None and head == c6, "receipt derivation requires exact receipt-absent C6"
    )
    c6_entries = parse_tree(c6_tree)
    capture_schema, local_schema, receipt_schema = validate_schema_authorities(
        c6_entries
    )
    local_raw = bounded_regular_fd(local_fd, "local-closure input")
    successor_raw = bounded_regular_fd(successor_fd, "successor-capture input")
    value = derive_receipt(
        tree_blob(c6_entries, PREDECESSOR_CAPTURE_RELATIVE),
        local_raw,
        successor_raw,
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
        local_schema,
    )
    validate_schema_instance(value, receipt_schema, "derived composite-v6 receipt")
    final_head, final_tree = validate_repository()
    final_c6, final_c6_tree, final_r6 = validate_topology(final_head, final_tree)
    require(
        final_r6 is None
        and (final_head, final_tree, final_c6, final_c6_tree)
        == (head, head_tree, c6, c6_tree),
        "repository state changed during receipt derivation",
    )
    return value


def validate_receipt_command() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c6, c6_tree, r6 = validate_topology(head, head_tree)
    require(r6 is not None, "receipt validation requires R6 or a retained descendant")
    c6_entries = parse_tree(c6_tree)
    r6_entries = parse_tree(parse_commit(r6).tree)
    capture_schema, local_schema, receipt_schema = validate_schema_authorities(
        c6_entries
    )
    receipt_raw = bounded_stdin()
    require(
        receipt_raw == tree_blob(r6_entries, RECEIPT_RELATIVE),
        "receipt stdin differs from R6 blob",
    )
    validate_receipt_bytes(
        receipt_raw,
        tree_blob(c6_entries, PREDECESSOR_CAPTURE_RELATIVE),
        tree_blob(r6_entries, LOCAL_CLOSURE_RELATIVE),
        tree_blob(r6_entries, SUCCESSOR_CAPTURE_RELATIVE),
        c6_entries,
        c6,
        c6_tree,
        capture_schema,
        local_schema,
        receipt_schema,
    )
    return {
        **static_result(head, head_tree, c6, r6),
        "schema": "pid-rs/ksg-rev4-m1a-composite-v6-receipt-validation/v1",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
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
        if arguments.validate_static:
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
    except ContractError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
