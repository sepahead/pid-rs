#!/usr/bin/env python3
"""Validate the append-only KSG M1a composite-v4 evidence contract.

This checker validates durable Git and hosted-observation facts.  It is not a
PID estimator, a mathematical proof, scientific review, or application gate.
"""

from __future__ import annotations

import argparse
import base64
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import Any
import zipfile


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-ksg-m1a-composite-v4.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
GIT = Path("/usr/bin/git")

REPOSITORY = "sepahead/pid-rs"
BASE_COMMIT = "bc3aa80fb6025e709c2906a08bce25a4fac40578"
BASE_TREE = "7d87f87953a42edb91e40880d918471c7cbe4414"
CORRECTION_COMMIT = "7473e62acef6077c2c1147e09d5d1297f2a2874b"
IMPLEMENTATION_COMMIT = "cb3f58f0b190454cb3f1090de8798261ec78f194"
EXPECTED_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"

C4_MESSAGE = "Migrate KSG M1a composite receipt contract\n"
R4_MESSAGE = "Record KSG M1a composite v4 receipt\n"
BASE_MESSAGE = (
    "Repair KSG M1a hosted recovery wiring\n\n"
    "Sealed-index-SHA256: "
    "13f637307c3f99535385df22d74f87d45206338ed4dc0ad6632f2d4958d0b92f\n"
    "Sealed-index-Size: 89027\n"
)
CORRECTION_MESSAGE = (
    "Correct KSG M1a hosted custody wiring\n\n"
    "Sealed-index-SHA256: "
    "f9d1f42a758c3dfe55ec1d313229b14c0c462db9d753b5b1d59a4008f1f232bc\n"
    "Sealed-index-Size: 87963\n"
)
IMPLEMENTATION_MESSAGE = "Harden KSG integer-harmonic runtime correspondence\n"

CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v4.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v4-self-test.py"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v4.py"
LEAN_CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
LEAN_R9_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-15-r9.json"
)
LEAN_R9_REJECTED_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-15-r9-prepublication-closure-rejected-2026-08-17.json"
)
LEAN_R9_REJECTED_SHA256 = (
    "fb162cc40da3059b61eab9024f4aa38cf6daf2d84ef7e1d8a26dc7d345291e70"
)
LEAN_R9_REJECTED_SIZE_BYTES = 132710
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v4.schema.json"
CAPTURE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v4.schema.json"
)
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v4-path-policy-v1.json"
COUNTEREXAMPLE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-v3-impossibility-2026-08-15.json"
)
PROCESS_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v4-process-2026-08-15.md"
PROCESS_TEX_RELATIVE = "audit/formal/latex/ksg-m1a-composite-v4-process.tex"
PROCESS_PDF_RELATIVE = "output/pdf/ksg-m1a-composite-v4-process.pdf"
PROCESS_PDF_GATE_RELATIVE = "scripts/check-ksg-m1a-composite-v4-process-pdf.sh"
PROCESS_VISUAL_RECEIPT_RELATIVE = (
    "audit/evidence/ksg-m1a-composite-v4-process-visual-receipt-2026-08-17.md"
)
PROCESS_FIGURE_PDF_RELATIVE = (
    "audit/formal/latex/figures/ksg-m1a-composite-v4-process/"
    "c4-r4-acyclic-custody.pdf"
)
PROCESS_FIGURE_SVG_RELATIVE = (
    "audit/formal/latex/figures/ksg-m1a-composite-v4-process/"
    "c4-r4-acyclic-custody.svg"
)
WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v4.yml"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_SCHEMA_RELATIVE = "audit/schemas/current-source-state-v1.schema.json"
RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json"
CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json"
)
V3_RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v3-2026-08-13.json"

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
V4_SCHEMA_DEFINITIONS = {
    CAPTURE_SCHEMA_RELATIVE: {
        "id": "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v4.schema.json",
        "sha256": "7512e24e3256baaacca2d75a23a9ae2a530cd987f6460788d2b431175f41c8d1",
        "size_bytes": 6664,
        "required": [
            "capture_tool",
            "captures",
            "nonimplications",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        ],
    },
    SCHEMA_RELATIVE: {
        "id": "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-receipt-v4.schema.json",
        "sha256": "8492da6dfd704667515e7b9da88d501de34903e5e2b52582106211b07f48528e",
        "size_bytes": 11292,
        "required": [
            "capture_binding",
            "contract_authorities",
            "nonimplications",
            "observations",
            "repository",
            "schema",
            "schema_revision",
            "subject",
            "verdict",
        ],
    },
}
EXPECTED_WORKFLOW_SHA256 = (
    "541f4bcfe7135c63f4e4b76c5d119b2c64e60550e365885c4ac98f9c8c48df04"
)
EXPECTED_WORKFLOW_SIZE_BYTES = 2213
EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "3d86ff2826e5d5048d711250a0904a78e763a85939edbbdf12685ced0b601164"
LEAN_R8_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-14-r8.json"
)
LEAN_R8_SHA256 = "86251c48c0f720d1ca021dcac87dfbf6e1a54adf409ea8a8981102cea1769611"
LEAN_REPLAY_SCHEMA = "pid-rs/lean-current-project-replay/v2"

POLICY_NONIMPLICATIONS = [
    "This policy declares and checks only the exact process/documentation and operational C4 and R4 deltas; it records no scientific-code or result change.",
    "A path role, Git object, checker result, hosted run, capture, or receipt is not a PID definition, estimator validation, calibration result, review disposition, or application gate.",
    "No evidence transfers among categorical MGW, Schick-Poland, Ehrlich continuous shared exclusions, KSG mutual information, Williams-Beer I_min, PID2, PID3, quantized or mixed-support routes, resampling procedures, or downstream objectives.",
]
C4_POLICY_ROWS = (
    (
        ".github/workflows/ksg-m1a-composite-v4.yml",
        "A",
        "100644",
        "dedicated_hosted_gate",
    ),
    ("AGENTS.md", "M", "100644", "operational_and_scientific_object_guide"),
    ("CHANGELOG.md", "M", "100644", "append_only_change_record"),
    (
        "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md",
        "M",
        "100644",
        "prospective_research_integrity_documentation",
    ),
    (
        "audit/evidence/completion-active-resume.md",
        "M",
        "100644",
        "current_replay_pointer",
    ),
    (CURRENT_SOURCE_RELATIVE, "M", "100644", "self_excluding_source_state"),
    (
        PROCESS_VISUAL_RECEIPT_RELATIVE,
        "A",
        "100644",
        "process_visual_review_receipt",
    ),
    (COUNTEREXAMPLE_RELATIVE, "A", "100644", "v3_impossibility_counterexample"),
    (POLICY_RELATIVE, "A", "100644", "c4_r4_path_policy"),
    (PROCESS_RELATIVE, "A", "100644", "process_record_markdown"),
    (
        LEAN_R9_REJECTED_RELATIVE,
        "A",
        "100644",
        "prepublication_replay_execution_passed_closure_rejected",
    ),
    (LEAN_R9_RELATIVE, "A", "100644", "current_lean_replay_receipt"),
    (
        "audit/evidence/mathematical-workflow-visual-receipt-2026-08-16.md",
        "A",
        "100644",
        "prospective_research_integrity_visual_review",
    ),
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
        PROCESS_FIGURE_PDF_RELATIVE,
        "A",
        "100644",
        "process_custody_diagram_derivative",
    ),
    (
        PROCESS_FIGURE_SVG_RELATIVE,
        "A",
        "100644",
        "process_custody_diagram_source",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.pdf",
        "M",
        "100644",
        "prospective_research_integrity_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/four-object-assurance-chain.svg",
        "M",
        "100644",
        "prospective_research_integrity_vector_source",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.pdf",
        "M",
        "100644",
        "prospective_research_integrity_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/invalidation-publication-state-machine.svg",
        "M",
        "100644",
        "prospective_research_integrity_vector_source",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.pdf",
        "M",
        "100644",
        "prospective_research_integrity_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/obligation-dag-minimal-cuts.svg",
        "M",
        "100644",
        "prospective_research_integrity_vector_source",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.pdf",
        "M",
        "100644",
        "prospective_research_integrity_vector_derivative",
    ),
    (
        "audit/formal/latex/figures/mathematical-workflow/shared-oracle-correlated-routes.svg",
        "M",
        "100644",
        "prospective_research_integrity_vector_source",
    ),
    (PROCESS_TEX_RELATIVE, "A", "100644", "process_publication_source"),
    (
        "audit/formal/latex/mathematical-problem-solving-workflow.tex",
        "M",
        "100644",
        "prospective_research_integrity_publication_source",
    ),
    (
        "audit/formal/requirements-pdf.txt",
        "M",
        "100644",
        "pdf_verifier_dependency_lock",
    ),
    (CURRENT_SOURCE_SCHEMA_RELATIVE, "M", "100644", "current_source_schema"),
    (CAPTURE_SCHEMA_RELATIVE, "A", "100644", "hosted_capture_schema"),
    (SCHEMA_RELATIVE, "A", "100644", "typed_receipt_schema"),
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
    (PROCESS_PDF_RELATIVE, "A", "100644", "process_publication_pdf"),
    (
        "output/pdf/mathematical-problem-solving-workflow.pdf",
        "M",
        "100644",
        "prospective_research_integrity_publication_pdf",
    ),
    (
        "output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv",
        "M",
        "100644",
        "prospective_research_integrity_rendering_receipt",
    ),
    ("scripts/README.md", "M", "100644", "script_process_guide"),
    (CAPTURE_TOOL_RELATIVE, "A", "100644", "bounded_hosted_capture_tool"),
    (
        "scripts/check-current-source-state-v1-self-test.py",
        "M",
        "100755",
        "current_source_hostile_suite",
    ),
    ("scripts/check-current-source-state-v1.py", "M", "100755", "current_source_gate"),
    ("scripts/check-formal-pdf-set.sh", "M", "100755", "formal_pdf_inventory_gate"),
    ("scripts/check-formal-pdf-style.py", "M", "100755", "formal_pdf_style_gate"),
    (PROCESS_PDF_GATE_RELATIVE, "A", "100755", "process_pdf_reproduction_gate"),
    (SELF_TEST_RELATIVE, "A", "100644", "composite_v4_hostile_suite"),
    (CHECKER_RELATIVE, "A", "100644", "composite_v4_semantic_gate"),
    (
        "scripts/check-lean-toolchain-freeze-self-test.py",
        "M",
        "100644",
        "lean_replay_hostile_suite",
    ),
    ("scripts/check-lean-toolchain-freeze.py", "M", "100644", "lean_replay_gate"),
    (
        "scripts/check-mathematical-workflow-pdf-self-test.sh",
        "M",
        "100755",
        "prospective_research_integrity_pdf_hostile_suite",
    ),
    (
        "scripts/check-mathematical-workflow-pdf.sh",
        "M",
        "100755",
        "prospective_research_integrity_pdf_gate",
    ),
    (
        "scripts/check-post-commit-source-state-v2-self-test.py",
        "M",
        "100644",
        "postcommit_source_hostile_suite",
    ),
    (
        "scripts/check-post-commit-source-state-v2.py",
        "M",
        "100644",
        "postcommit_source_gate",
    ),
    ("scripts/generate-lean-4.33-replay.py", "M", "100644", "lean_replay_generator"),
)

V3_FROZEN = {
    ".github/workflows/ci.yml": (
        68913,
        "61283264499a7b6069a4e5e9563c72541ab101b69379f3ace75a12cd4bf4b175",
        "80b576448a3053f615580265056eeb9ab0b70b1b",
    ),
    "audit/evidence/current-source-state-v1.json": (
        176095,
        "8dabf1b65040e1ee6e55b21b67fc1094248ec62a619b8efdf8ab0565b8e20c57",
        "c0743888c7dd8eb22c2162b47219073744790fba",
    ),
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json": (
        114567,
        "345296eca6d944fbc40d1133b862a7ff047a6083123b023e1533a2f22cf4a2c5",
        "7e6e86bb0677b6feb73f99395e7fde2ec0805852",
    ),
    "scripts/check-current-source-state-v1.py": (
        25651,
        "5be09a05b734d2c04d5a509cb919c630f37e9651d1e4bbd4b8fc2a34aff86591",
        "54f68f03f526f7a1cb1ca1c5ce5ac729ef0b4529",
    ),
    "scripts/check-ksg-m1a-hosted-recovery.py": (
        246860,
        "6c422718b32d9ad22b74a22d1ea56b73ebe3b312412f28b3319f4085598d66cc",
        "32fc45c58ea9a7da0f96b0a0fdc6a98271fb70ab",
    ),
    "scripts/check-ksg-m1a-hosted-recovery-self-test.py": (
        140677,
        "ce8cf3b23e9fa735f01b56bb6d90b18332f5b60d9b20738080b00356bbcef35f",
        "1147c93ec08561ffd9cad8dbc6ffe9cf539ca5f8",
    ),
}
V3_RETAINED_PATHS = (
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json",
    "scripts/check-ksg-m1a-hosted-recovery.py",
    "scripts/check-ksg-m1a-hosted-recovery-self-test.py",
)
V3_FROZEN_LABELS = {
    ".github/workflows/ci.yml": "ci_workflow",
    "audit/evidence/current-source-state-v1.json": "current_source_manifest",
    "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json": "v3_schema",
    "scripts/check-current-source-state-v1.py": "current_source_checker",
    "scripts/check-ksg-m1a-hosted-recovery.py": "v3_checker",
    "scripts/check-ksg-m1a-hosted-recovery-self-test.py": "v3_self_test",
}

RECOVERY_RUNS = {
    "ci": 31773937366,
    "codeql": 31773937102,
}
RECOVERY_ANALYSIS_IDS = {
    "actions": 1617732991,
    "javascript-typescript": 1617732745,
    "python": 1617735963,
    "rust": 1617735749,
}
LANGUAGE_ORDER = ("actions", "javascript-typescript", "python", "rust")
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

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BODY_BYTES = 22 * 1024 * 1024
MAX_CAPTURE_ROWS = 4096
MAX_PAGES = 64
MAX_JSON_DEPTH = 96
MAX_INTEGER_DIGITS = 32
MAX_GIT_OUTPUT = 64 * 1024 * 1024
MAX_BLOB_BYTES = 32 * 1024 * 1024
MAX_ZIP_MEMBERS = 4096

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
CURRENT_SOURCE_BINDING_KEYS = {
    "commit_binding",
    "excluded_paths",
    "generated_at",
    "projection_algorithm",
    "scope_kind",
}
CURRENT_SOURCE_PROJECTION_KEYS = {"entries", "entries_sha256", "entry_count"}
CURRENT_SOURCE_CRITICAL_ARTIFACTS = (
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
CURRENT_SOURCE_SUBPROJECTIONS = (
    ("claim_packets", ("claims/",)),
    ("formal_sources_and_receipts", ("audit/formal/",)),
    ("generated_pdf_set", ("output/pdf/",)),
    ("release_documents", ("README.md", "RELEASE_NOTES.md", "CHANGELOG.md")),
)
CURRENT_SOURCE_PDFS = (
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "output/pdf/ecosystem-compatibility-audit.pdf",
    "output/pdf/exact-log-product-sxpid2-assurance.pdf",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "output/pdf/ksg-m1a-composite-v4-process.pdf",
    "output/pdf/mathematical-problem-solving-workflow.pdf",
    "output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf",
    "output/pdf/two-source-sxpid-count-atom-bridge.pdf",
)
CURRENT_SOURCE_NONIMPLICATIONS = [
    "This deterministic consistency record is not authentication or attestation.",
    "It does not claim its own final SHA-256 or containing commit.",
    "It does not establish line review, human review, independent review, or institutional review.",
    "It does not establish source-to-formal correspondence, implementation refinement, estimator validity, or application validity.",
    "A generated PDF hash establishes byte identity only, not semantic or visual correctness.",
    "Ignored build products and Git object-store bytes are outside the source projection.",
    "The projection records repository index modes and worktree bytes; it is not an object-store integrity proof.",
]
COUNTEREXAMPLE_NONIMPLICATIONS = [
    "The counterexample does not invalidate the KSG implementation or any mathematical theorem.",
    "A successful CodeQL run is not estimator validation, scientific review, or application evidence.",
    "A contract defect does not transfer to categorical MGW SxPID, continuous Ehrlich PID, PID2, PID3, Williams-Beer I_min, or any downstream objective.",
    "Unique provider identifiers are opaque observations; their numerical order has no scientific meaning.",
    "Missing historical sealed-index bytes are not reconstructed, fabricated, or relabeled.",
]


class ContractError(RuntimeError):
    """A v4 contract predicate failed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise ContractError(message)


def exact_int(value: Any, label: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, f"{label} is not an exact integer")
    return value


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(type(value) is dict and set(value) == keys, f"{label} keys changed")
    return value


def canonical_json(value: Any, *, pretty: bool) -> bytes:
    try:
        if pretty:
            rendered = json.dumps(
                value, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False
            )
            return (rendered + "\n").encode("ascii")
        return (
            json.dumps(
                value,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
    except (RecursionError, TypeError, ValueError) as error:
        raise ContractError(f"cannot canonicalize JSON: {error}") from None


def current_source_projection_bytes(value: Any) -> bytes:
    """Match the current-source generator's newline-free compact JSON framing."""
    rendered = canonical_json(value, pretty=False)
    require(
        rendered.endswith(b"\n"),
        "current-source projection framing lost its terminal newline",
    )
    return rendered[:-1]


def _scan_json_depth(raw: bytes, label: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            require(depth <= MAX_JSON_DEPTH, f"{label} exceeds JSON depth bound")
        elif byte in (0x5D, 0x7D):
            depth -= 1
            require(depth >= 0, f"{label} has an invalid closing delimiter")
    require(not in_string and depth == 0, f"{label} has incomplete JSON structure")


def parse_json(raw: bytes, label: str, *, canonical: bool = True) -> Any:
    require(0 < len(raw) <= MAX_JSON_BYTES, f"{label} size is outside the bound")
    _scan_json_depth(raw, label)

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def integer(token: str) -> int:
        digits = token[1:] if token.startswith("-") else token
        require(
            0 < len(digits) <= MAX_INTEGER_DIGITS,
            f"{label} contains an oversized integer token",
        )
        return int(token)

    def reject_float(_token: str) -> Any:
        raise ContractError(f"{label} contains a floating-point token")

    def reject_constant(_token: str) -> Any:
        raise ContractError(f"{label} contains a non-finite token")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique,
            parse_int=integer,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as error:
        raise ContractError(f"cannot parse {label}: {error}") from None
    if canonical:
        require(
            raw == canonical_json(value, pretty=True), f"{label} is not canonical JSON"
        )
    return value


SCHEMA_ANNOTATIONS = {"$defs", "$id", "$schema", "description", "title"}
SCHEMA_ASSERTIONS = {
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
SCHEMA_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}


def _schema_token(value: Any) -> bytes:
    return canonical_json(value, pretty=False)


def _schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "array": type(value) is list,
        "boolean": type(value) is bool,
        "integer": type(value) is int,
        "null": value is None,
        "number": type(value) in {int, float},
        "object": type(value) is dict,
        "string": type(value) is str,
    }.get(expected, False)


def validate_schema_instance(
    instance: Any, schema: Any, label: str, *, definition_only: bool = False
) -> None:
    """Evaluate the repository's deliberately small, closed JSON-Schema subset."""
    require(type(schema) is dict, f"{label} schema root is not an object")
    root = schema

    def resolve(reference: Any) -> dict[str, Any]:
        require(
            type(reference) is str and reference.startswith("#/"),
            f"{label} has a non-local schema reference",
        )
        value: Any = root
        for raw_component in reference[2:].split("/"):
            component = raw_component.replace("~1", "/").replace("~0", "~")
            require(
                type(value) is dict and component in value,
                f"{label} has an unresolved schema reference",
            )
            value = value[component]
        require(type(value) is dict, f"{label} schema reference is not an object")
        return value

    active: set[int] = set()
    complete: set[int] = set()

    def validate_definition(rule: Any, path: str, depth: int) -> None:
        require(depth <= MAX_JSON_DEPTH, f"{label} schema exceeds depth bound")
        require(type(rule) is dict, f"{path} schema node is not an object")
        identity = id(rule)
        if identity in complete:
            return
        require(identity not in active, f"{path} has a recursive schema reference")
        active.add(identity)
        try:
            unknown = set(rule) - SCHEMA_ANNOTATIONS - SCHEMA_ASSERTIONS
            require(not unknown, f"{path} has unsupported schema keywords")
            definitions = rule.get("$defs")
            if definitions is not None:
                require(type(definitions) is dict, f"{path} $defs is not an object")
                for name, child in definitions.items():
                    require(type(name) is str, f"{path} $defs key is not a string")
                    validate_definition(child, f"{path}.$defs.{name}", depth + 1)
            if "$ref" in rule:
                require(
                    not (set(rule) - SCHEMA_ANNOTATIONS - {"$ref"}),
                    f"{path} has assertions beside $ref",
                )
                validate_definition(resolve(rule["$ref"]), f"{path}.$ref", depth + 1)
            expected = rule.get("type")
            if expected is not None:
                accepted = [expected] if type(expected) is str else expected
                require(
                    type(accepted) is list
                    and accepted
                    and all(
                        type(item) is str and item in SCHEMA_TYPES for item in accepted
                    )
                    and len(accepted) == len(set(accepted)),
                    f"{path} has an invalid type declaration",
                )
            variants = rule.get("oneOf")
            if variants is not None:
                require(type(variants) is list and variants, f"{path} oneOf changed")
                for index, variant in enumerate(variants):
                    validate_definition(variant, f"{path}.oneOf[{index}]", depth + 1)
            properties = rule.get("properties")
            if properties is not None:
                require(type(properties) is dict, f"{path} properties changed")
                for name, child in properties.items():
                    require(type(name) is str, f"{path} property name changed")
                    validate_definition(child, f"{path}.properties.{name}", depth + 1)
            additional = rule.get("additionalProperties")
            require(
                additional is None or type(additional) in {bool, dict},
                f"{path} additionalProperties changed",
            )
            if type(additional) is dict:
                validate_definition(
                    additional, f"{path}.additionalProperties", depth + 1
                )
            if "items" in rule:
                validate_definition(rule["items"], f"{path}.items", depth + 1)
            required = rule.get("required")
            if required is not None:
                require(
                    type(required) is list
                    and all(type(item) is str for item in required)
                    and len(required) == len(set(required)),
                    f"{path} required list changed",
                )
            for key in ("maxItems", "minItems", "minLength"):
                if key in rule:
                    require(
                        type(rule[key]) is int and rule[key] >= 0,
                        f"{path} {key} changed",
                    )
            if "minimum" in rule:
                require(type(rule["minimum"]) is int, f"{path} minimum changed")
            if "uniqueItems" in rule:
                require(
                    type(rule["uniqueItems"]) is bool, f"{path} uniqueItems changed"
                )
            if "pattern" in rule:
                require(type(rule["pattern"]) is str, f"{path} pattern changed")
                try:
                    re.compile(rule["pattern"])
                except re.error as error:
                    raise ContractError(f"{path} pattern is invalid: {error}") from None
            if "enum" in rule:
                choices = rule["enum"]
                require(type(choices) is list and choices, f"{path} enum changed")
                tokens = [_schema_token(choice) for choice in choices]
                require(len(tokens) == len(set(tokens)), f"{path} enum is not unique")
        finally:
            active.remove(identity)
        complete.add(identity)

    validate_definition(root, f"{label} schema", 0)
    if definition_only:
        return

    def visit(value: Any, rule: dict[str, Any], path: str, depth: int) -> None:
        require(depth <= MAX_JSON_DEPTH, f"{path} exceeds schema depth bound")
        if "$ref" in rule:
            visit(value, resolve(rule["$ref"]), path, depth + 1)
            return
        if "oneOf" in rule:
            matches = 0
            for variant in rule["oneOf"]:
                try:
                    visit(value, variant, path, depth + 1)
                except ContractError:
                    continue
                matches += 1
            require(matches == 1, f"{path} does not have exactly one oneOf match")
        expected = rule.get("type")
        if expected is not None:
            accepted = [expected] if type(expected) is str else expected
            require(
                any(_schema_type_matches(value, item) for item in accepted),
                f"{path} has the wrong JSON type",
            )
        if "const" in rule:
            require(
                _schema_token(value) == _schema_token(rule["const"]),
                f"{path} differs from schema const",
            )
        if "enum" in rule:
            require(
                any(
                    _schema_token(value) == _schema_token(item) for item in rule["enum"]
                ),
                f"{path} is outside schema enum",
            )
        if "minimum" in rule and type(value) in {int, float}:
            require(value >= rule["minimum"], f"{path} is below schema minimum")
        if type(value) is dict:
            properties = rule.get("properties", {})
            required = rule.get("required", [])
            require(
                not (set(required) - set(value)), f"{path} lacks required properties"
            )
            for key, item in value.items():
                if key in properties:
                    visit(item, properties[key], f"{path}.{key}", depth + 1)
                else:
                    additional = rule.get("additionalProperties", True)
                    require(
                        additional is not False, f"{path} has an additional property"
                    )
                    if type(additional) is dict:
                        visit(item, additional, f"{path}.{key}", depth + 1)
        if type(value) is list:
            if "minItems" in rule:
                require(len(value) >= rule["minItems"], f"{path} has too few items")
            if "maxItems" in rule:
                require(len(value) <= rule["maxItems"], f"{path} has too many items")
            if rule.get("uniqueItems"):
                tokens = [_schema_token(item) for item in value]
                require(len(tokens) == len(set(tokens)), f"{path} items are not unique")
            if "items" in rule:
                for index, item in enumerate(value):
                    visit(item, rule["items"], f"{path}[{index}]", depth + 1)
        if type(value) is str:
            if "minLength" in rule:
                require(len(value) >= rule["minLength"], f"{path} is too short")
            if "pattern" in rule:
                require(
                    re.fullmatch(rule["pattern"], value) is not None,
                    f"{path} does not match schema pattern",
                )

    visit(instance, root, label, 0)


def validate_contract_schema_definition(
    schema: Any,
    label: str,
    *,
    expected_id: str,
    expected_required: list[str],
    expected_sha256: str,
    expected_size_bytes: int,
    raw: bytes,
) -> None:
    """Validate both the supported schema graph and its exact public root contract."""
    require(
        len(raw) == expected_size_bytes
        and sha256(raw) == expected_sha256
        and canonical_json(schema, pretty=True) == raw,
        f"{label} schema exact bytes changed",
    )
    validate_schema_instance({}, schema, label, definition_only=True)
    require(type(schema) is dict, f"{label} schema root is not an object")
    require(
        schema.get("$schema") == JSON_SCHEMA_DIALECT
        and schema.get("$id") == expected_id
        and schema.get("type") == "object"
        and schema.get("additionalProperties") is False
        and schema.get("required") == expected_required,
        f"{label} schema identity or closed root contract changed",
    )

    def require_closed_objects(rule: Any, path: str, depth: int) -> None:
        require(depth <= MAX_JSON_DEPTH, f"{label} closure exceeds depth bound")
        require(type(rule) is dict, f"{path} schema node is not an object")
        expected_type = rule.get("type")
        accepted = (
            [expected_type] if type(expected_type) is str else expected_type or []
        )
        if "object" in accepted:
            properties = rule.get("properties")
            required = rule.get("required")
            require(
                type(properties) is dict
                and type(required) is list
                and rule.get("additionalProperties") is False
                and set(properties) == set(required),
                f"{path} is not a closed exact-key object schema",
            )
        for namespace in ("$defs", "properties"):
            children = rule.get(namespace, {})
            if type(children) is dict:
                for name, child in children.items():
                    require_closed_objects(
                        child, f"{path}.{namespace}.{name}", depth + 1
                    )
        additional = rule.get("additionalProperties")
        if type(additional) is dict:
            require_closed_objects(
                additional, f"{path}.additionalProperties", depth + 1
            )
        items = rule.get("items")
        if type(items) is dict:
            require_closed_objects(items, f"{path}.items", depth + 1)
        variants = rule.get("oneOf", [])
        if type(variants) is list:
            for index, variant in enumerate(variants):
                require_closed_objects(variant, f"{path}.oneOf[{index}]", depth + 1)

    require_closed_objects(schema, f"{label} schema", 0)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def lean_source_cuts(raw: bytes) -> tuple[str, str, str, bytes]:
    """Extract three final r9 cuts and normalize the C4/Lean checksum cycle."""

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"Lean checker source is not UTF-8: {error}") from None
    patterns = (
        (
            "projection",
            re.compile(
                r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64',
        ),
        (
            "composite-v4 checker",
            re.compile(
                r'^EXPECTED_COMPOSITE_V4_CHECKER_OPERATIONAL_SHA256 = "([0-9a-f]{64})"$',
                re.MULTILINE,
            ),
            'EXPECTED_COMPOSITE_V4_CHECKER_OPERATIONAL_SHA256 = "0" * 64',
        ),
        (
            "composite-v4 operational map",
            re.compile(
                r'^    "scripts/check-ksg-m1a-composite-v4\.py": "([0-9a-f]{64})",$',
                re.MULTILINE,
            ),
            '    "scripts/check-ksg-m1a-composite-v4.py": "0" * 64,',
        ),
    )
    values: list[str] = []
    normalized = source
    for label, pattern, replacement in patterns:
        matches = list(pattern.finditer(normalized))
        require(len(matches) == 1, f"Lean {label} cut is not unique and final")
        value = matches[0].group(1)
        require(value != "0" * 64, f"Lean {label} cut remains a placeholder")
        values.append(value)
        normalized = pattern.sub(replacement, normalized, count=1)
    return values[0], values[1], values[2], normalized.encode("utf-8")


def lean_replay_projection_sha256(receipt: dict[str, Any]) -> str:
    """Reproduce the Lean checker projection without importing repository code."""

    projected = dict(receipt)
    custody = projected.get("custody_gate_sha256")
    require(type(custody) is dict, "r9 custody-gate inventory is malformed")
    self_test_path = "scripts/check-lean-toolchain-freeze-self-test.py"
    require(self_test_path in custody, "r9 self-test custody is absent")
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
        raise ContractError(f"cannot project r9 replay receipt: {error}") from None
    return sha256(raw)


def validate_lean_r9_contract(
    v4_checker_raw: bytes,
    lean_checker_raw: bytes,
    rejected_r9_raw: bytes,
    r9_raw: bytes,
) -> None:
    """Bind the separately generated r9 receipt across the three acyclic cuts."""

    checker_digest = sha256(v4_checker_raw)
    projection, composite_cut, operational_cut, normalized = lean_source_cuts(
        lean_checker_raw
    )
    require(
        composite_cut == checker_digest and operational_cut == checker_digest,
        "Lean composite-v4 checker cuts do not bind the C4 checker bytes",
    )
    require(
        EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 != "0" * 64
        and sha256(normalized) == EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256,
        "normalized Lean checker authority changed",
    )
    rejected_r9 = parse_json(
        rejected_r9_raw, "prepublication closure-rejected Lean r9 candidate"
    )
    require(
        len(rejected_r9_raw) == LEAN_R9_REJECTED_SIZE_BYTES
        and sha256(rejected_r9_raw) == LEAN_R9_REJECTED_SHA256
        and type(rejected_r9) is dict
        and rejected_r9.get("schema") == LEAN_REPLAY_SCHEMA
        and rejected_r9.get("status") == "passed",
        "prepublication closure-rejected Lean r9 candidate changed",
    )
    r9 = parse_json(r9_raw, "Lean r9 replay receipt")
    require(
        type(r9) is dict and r9.get("schema") == LEAN_REPLAY_SCHEMA,
        "Lean r9 replay schema changed",
    )
    prior_hashes = r9.get("prior_replay_preservation_sha256")
    prior_schemas = r9.get("prior_replay_schema")
    require(
        type(prior_hashes) is dict
        and type(prior_schemas) is dict
        and prior_hashes.get(LEAN_R8_RELATIVE) == LEAN_R8_SHA256
        and prior_schemas.get(LEAN_R8_RELATIVE) == LEAN_REPLAY_SCHEMA,
        "Lean r9 does not preserve the exact r8 replay authority",
    )
    require(
        LEAN_R9_REJECTED_RELATIVE not in prior_hashes
        and LEAN_R9_REJECTED_RELATIVE not in prior_schemas,
        "closure-rejected replay candidate entered the accepted prior-replay lineage",
    )
    operational = r9.get("operational_wiring_sha256")
    require(
        type(operational) is dict
        and operational.get(CHECKER_RELATIVE) == checker_digest
        and operational.get(LEAN_R9_REJECTED_RELATIVE)
        == LEAN_R9_REJECTED_SHA256,
        "Lean r9 operational map does not bind the C4 checker and rejected-candidate bytes",
    )
    require(
        lean_replay_projection_sha256(r9) == projection,
        "Lean r9 projection cut changed",
    )
    final_custody = r9.get("custody_gate_sha256")
    replay_custody = r9.get("replay_custody_gate_sha256")
    require(
        type(final_custody) is dict
        and type(replay_custody) is dict
        and final_custody.get(LEAN_CHECKER_RELATIVE) == sha256(lean_checker_raw),
        "Lean r9 final checker custody changed",
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
        "Lean r9 projection line is not exactly reconstructable",
    )
    replay_checker_raw = lean_checker_raw.replace(
        final_projection_line, placeholder_projection_line, 1
    )
    require(
        replay_custody.get(LEAN_CHECKER_RELATIVE) == sha256(replay_checker_raw),
        "Lean r9 replay-time checker custody changed",
    )


def git_object_id(kind: str, raw: bytes) -> str:
    header = f"{kind} {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def validate_relative_path(path: str, label: str) -> PurePosixPath:
    require(type(path) is str and path != "", f"{label} is not a nonempty string")
    pure = PurePosixPath(path)
    require(
        not pure.is_absolute()
        and pure.as_posix() == path
        and all(part not in {"", ".", ".."} for part in pure.parts),
        f"{label} is not a canonical repository-relative path",
    )
    return pure


def _stat_identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def read_repository_file(relative: str, *, maximum: int, mode: int) -> bytes:
    pure = validate_relative_path(relative, "repository file path")
    require(ROOT.resolve(strict=True) == ROOT, "repository root route is not canonical")
    try:
        root_before = ROOT.lstat()
    except OSError as error:
        raise ContractError(f"cannot stat repository root: {error}") from None
    require(
        stat.S_ISDIR(root_before.st_mode)
        and not (root_before.st_mode & (stat.S_IWGRP | stat.S_IWOTH)),
        "unsafe repository root metadata",
    )
    directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_DIRECTORY
    try:
        root_fd = os.open(ROOT, directory_flags)
    except OSError as error:
        raise ContractError(f"cannot open repository root: {error}") from None
    descriptors = [root_fd]
    route: list[tuple[int, str, os.stat_result]] = []
    try:
        root_opened = os.fstat(root_fd)
        require(
            _stat_identity(root_before) == _stat_identity(root_opened),
            "opened repository root identity differs",
        )
        parent_fd = root_fd
        for component in pure.parts[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            require(
                stat.S_ISDIR(before.st_mode)
                and not (before.st_mode & (stat.S_IWGRP | stat.S_IWOTH)),
                f"unsafe repository directory: {relative}",
            )
            child_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            descriptors.append(child_fd)
            opened = os.fstat(child_fd)
            require(
                _stat_identity(before) == _stat_identity(opened),
                f"repository directory identity differs: {relative}",
            )
            route.append((parent_fd, component, opened))
            parent_fd = child_fd
        leaf = pure.parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == mode
            and 0 <= before.st_size <= maximum,
            f"unsafe repository file metadata: {relative}",
        )
        descriptor = os.open(
            leaf, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent_fd
        )
        descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        require(
            _stat_identity(before) == _stat_identity(opened),
            f"opened repository file identity differs: {relative}",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", f"short read: {relative}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"file grew during read: {relative}")
        closed = os.fstat(descriptor)
        after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(
            _stat_identity(before)
            == _stat_identity(opened)
            == _stat_identity(closed)
            == _stat_identity(after),
            f"repository file identity changed during read: {relative}",
        )
        for route_parent, component, route_opened in route:
            route_after = os.stat(component, dir_fd=route_parent, follow_symlinks=False)
            require(
                _stat_identity(route_opened) == _stat_identity(route_after),
                f"repository directory route changed: {relative}",
            )
        root_after = ROOT.lstat()
        require(
            _stat_identity(root_before)
            == _stat_identity(root_opened)
            == _stat_identity(root_after),
            "repository root changed during file read",
        )
        return b"".join(chunks)
    except OSError as error:
        raise ContractError(
            f"cannot read repository file {relative}: {error}"
        ) from None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _git_environment() -> dict[str, str]:
    allowed = ("PATH", "TMPDIR", "LANG", "LC_ALL", "TZ")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_bounded_process(
    command: tuple[str, ...],
    *,
    input_bytes: bytes | None,
    stdout_maximum: int,
    stderr_maximum: int,
    timeout_seconds: int,
) -> BoundedProcessResult:
    require(
        input_bytes is None or len(input_bytes) <= 1024 * 1024,
        "subprocess input exceeds bound",
    )
    process: subprocess.Popen[bytes] | None = None
    selector = selectors.DefaultSelector()
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
            start_new_session=True,
        )
        require(
            process.stdout is not None and process.stderr is not None,
            "subprocess pipes are unavailable",
        )
        if input_bytes is not None:
            require(process.stdin is not None, "subprocess input pipe is unavailable")
            process.stdin.write(input_bytes)
            process.stdin.close()
        for stream, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        outputs: dict[str, bytearray] = {
            "stdout": bytearray(),
            "stderr": bytearray(),
        }
        limits = {"stdout": stdout_maximum, "stderr": stderr_maximum}
        deadline = time.monotonic() + timeout_seconds
        while selector.get_map():
            remaining = deadline - time.monotonic()
            require(remaining > 0, "subprocess exceeded time bound")
            events = selector.select(min(remaining, 0.25))
            if not events:
                continue
            for key, _mask in events:
                label = key.data
                stream = key.fileobj
                chunk = os.read(stream.fileno(), 64 * 1024)
                if chunk == b"":
                    selector.unregister(stream)
                    continue
                outputs[label].extend(chunk)
                require(
                    len(outputs[label]) <= limits[label],
                    f"subprocess {label} exceeds bound",
                )
        remaining = deadline - time.monotonic()
        require(remaining > 0, "subprocess exceeded time bound")
        returncode = process.wait(timeout=remaining)
        return BoundedProcessResult(
            returncode, bytes(outputs["stdout"]), bytes(outputs["stderr"])
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ContractError(f"bounded subprocess failed: {error}") from None
    finally:
        selector.close()
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def git(
    *arguments: str, input_bytes: bytes | None = None, maximum: int = MAX_GIT_OUTPUT
) -> bytes:
    command = (
        os.fspath(GIT),
        "--no-optional-locks",
        "-c",
        "core.commitGraph=false",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.excludesFile=/dev/null",
        "-c",
        "protocol.file.allow=never",
        "-C",
        os.fspath(ROOT),
        *arguments,
    )
    result = run_bounded_process(
        command,
        input_bytes=input_bytes,
        stdout_maximum=maximum,
        stderr_maximum=1024 * 1024,
        timeout_seconds=180,
    )
    require(
        result.returncode == 0,
        "Git failed: " + result.stderr.decode("utf-8", errors="replace").strip(),
    )
    return result.stdout


def git_text(*arguments: str) -> str:
    raw = git(*arguments, maximum=1024 * 1024)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ContractError(f"Git text is not ASCII: {error}") from None
    require(text.endswith("\n") and "\n" not in text[:-1], "Git text is not one line")
    return text[:-1]


def git_predicate(*arguments: str) -> bool:
    command = (
        os.fspath(GIT),
        "--no-optional-locks",
        "-c",
        "core.commitGraph=false",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.excludesFile=/dev/null",
        "-c",
        "protocol.file.allow=never",
        "-C",
        os.fspath(ROOT),
        *arguments,
    )
    result = run_bounded_process(
        command,
        input_bytes=None,
        stdout_maximum=0,
        stderr_maximum=1024 * 1024,
        timeout_seconds=180,
    )
    require(
        result.stdout == b"",
        "Git predicate emitted unexpected output",
    )
    require(result.returncode in {0, 1}, "Git predicate returned an invalid status")
    return result.returncode == 0


@lru_cache(maxsize=4096)
def exact_object(oid: str, kind: str, maximum: int = MAX_BLOB_BYTES) -> bytes:
    require(SHA1_RE.fullmatch(oid) is not None, f"invalid {kind} object id")
    response = git(
        "cat-file",
        "--batch",
        input_bytes=(oid + "\n").encode("ascii"),
        maximum=maximum + 1024,
    )
    header, separator, body = response.partition(b"\n")
    fields = header.split(b" ")
    require(
        separator == b"\n"
        and len(fields) == 3
        and fields[0] == oid.encode("ascii")
        and fields[1] == kind.encode("ascii")
        and fields[2].isdigit(),
        f"Git object batch header changed for {oid}",
    )
    size = int(fields[2])
    require(0 <= size <= maximum, f"Git object size exceeds bound for {oid}")
    require(
        len(body) == size + 1 and body[-1:] == b"\n",
        f"Git object batch framing changed for {oid}",
    )
    raw = body[:size]
    require(git_object_id(kind, raw) == oid, f"Git object digest changed for {oid}")
    return raw


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    oid: str


def _parse_tree_object(tree: str, prefix: str, output: dict[str, TreeEntry]) -> None:
    raw = exact_object(tree, "tree")
    offset = 0
    previous_key = b""
    while offset < len(raw):
        space = raw.find(b" ", offset)
        nul = raw.find(b"\0", space + 1)
        require(space > offset and nul > space, "malformed raw Git tree")
        mode_raw = raw[offset:space]
        name_raw = raw[space + 1 : nul]
        oid_raw = raw[nul + 1 : nul + 21]
        require(len(oid_raw) == 20, "Git tree object ID is truncated")
        try:
            mode = mode_raw.decode("ascii")
            name = name_raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ContractError(f"Git tree field is not UTF-8/ASCII: {error}") from None
        require("/" not in name and name not in {"", ".", ".."}, "unsafe Git tree name")
        oid = oid_raw.hex()
        path = f"{prefix}/{name}" if prefix else name
        validate_relative_path(path, "Git tree path")
        tree_key = name_raw + (b"/" if mode == "40000" else b"")
        require(tree_key > previous_key, "Git tree order changed")
        previous_key = tree_key
        if mode == "40000":
            _parse_tree_object(oid, path, output)
        else:
            require(mode in {"100644", "100755", "120000"}, "unsupported Git tree mode")
            require(path not in output, "duplicate Git tree path")
            exact_object(oid, "blob")
            output[path] = TreeEntry(mode, oid)
        offset = nul + 21
    require(offset == len(raw), "Git tree has trailing bytes")


def parse_tree(tree: str) -> dict[str, TreeEntry]:
    require(SHA1_RE.fullmatch(tree) is not None, "invalid tree id")
    result: dict[str, TreeEntry] = {}
    _parse_tree_object(tree, "", result)
    return result


@dataclass(frozen=True)
class Commit:
    oid: str
    tree: str
    parent: str
    author: bytes
    committer: bytes
    message: str


def parse_identity(line: bytes, role: str) -> tuple[str, str, int, str]:
    pattern = re.compile(
        rb"^"
        + role.encode("ascii")
        + rb" ([^\n<>]+) <([^\n<>]+)> ([0-9]+) ([+-][0-9]{4})$"
    )
    match = pattern.fullmatch(line)
    require(match is not None, f"{role} identity is malformed")
    require(
        match.group(1).decode("utf-8") == EXPECTED_NAME
        and match.group(2).decode("ascii") == EXPECTED_EMAIL,
        f"{role} human identity changed",
    )
    timezone_text = match.group(4).decode("ascii")
    require(timezone_text == "+0200", f"{role} timezone changed")
    return (
        match.group(1).decode("utf-8"),
        match.group(2).decode("ascii"),
        int(match.group(3)),
        timezone_text,
    )


def parse_commit(oid: str) -> Commit:
    raw = exact_object(oid, "commit", maximum=1024 * 1024)
    header, separator, message_raw = raw.partition(b"\n\n")
    lines = header.split(b"\n")
    require(
        separator == b"\n\n" and len(lines) == 4,
        "commit envelope is not exact unsigned form",
    )
    require(
        lines[0].startswith(b"tree ") and lines[1].startswith(b"parent "),
        "commit ancestry header changed",
    )
    tree = lines[0][5:].decode("ascii")
    parent = lines[1][7:].decode("ascii")
    require(
        SHA1_RE.fullmatch(tree) is not None and SHA1_RE.fullmatch(parent) is not None,
        "commit tree/parent malformed",
    )
    author_identity = parse_identity(lines[2], "author")
    committer_identity = parse_identity(lines[3], "committer")
    require(author_identity == committer_identity, "author/committer identity changed")
    try:
        message = message_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"commit message is not UTF-8: {error}") from None
    return Commit(oid, tree, parent, lines[2], lines[3], message)


def parse_descendant_tree(oid: str) -> str:
    """Read a descendant tree without imposing the C4/R4 human envelope."""
    raw = exact_object(oid, "commit", maximum=1024 * 1024)
    header, separator, _message_raw = raw.partition(b"\n\n")
    require(separator == b"\n\n", "descendant commit envelope is malformed")
    tree_lines = [line for line in header.split(b"\n") if line.startswith(b"tree ")]
    require(len(tree_lines) == 1, "descendant commit tree header changed")
    try:
        tree = tree_lines[0][5:].decode("ascii")
    except UnicodeDecodeError as error:
        raise ContractError(f"descendant tree is not ASCII: {error}") from None
    require(SHA1_RE.fullmatch(tree) is not None, "descendant tree is malformed")
    return tree


def changed_entries(
    before: dict[str, TreeEntry], after: dict[str, TreeEntry]
) -> tuple[tuple[str, str, str], ...]:
    result: list[tuple[str, str, str]] = []
    for path in sorted(set(before) | set(after)):
        old = before.get(path)
        new = after.get(path)
        if old == new:
            continue
        if old is None:
            require(new is not None, "impossible added entry")
            result.append((path, "A", new.mode))
        elif new is None:
            result.append((path, "D", old.mode))
        else:
            require(old.mode == new.mode, f"mode changed for {path}")
            result.append((path, "M", new.mode))
    return tuple(result)


def tree_blob(entries: dict[str, TreeEntry], path: str) -> bytes:
    entry = entries.get(path)
    require(entry is not None, f"tree path is absent: {path}")
    return exact_object(entry.oid, "blob")


def validate_repository() -> tuple[str, str]:
    require(GIT.resolve(strict=True) == GIT, "fixed Git route is not canonical")
    git_stat = GIT.lstat()
    require(
        stat.S_ISREG(git_stat.st_mode)
        and stat.S_IMODE(git_stat.st_mode) == 0o755
        and not (git_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)),
        "fixed Git metadata changed",
    )
    require(ROOT.resolve(strict=True) == ROOT, "repository root route is not canonical")
    git_dir_expected = ROOT / ".git"
    git_dir_stat = git_dir_expected.lstat()
    require(
        stat.S_ISDIR(git_dir_stat.st_mode)
        and not (git_dir_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH))
        and git_dir_expected.resolve(strict=True) == git_dir_expected,
        "repository Git directory metadata changed",
    )
    config_raw = read_repository_file(".git/config", maximum=1024 * 1024, mode=0o644)
    require(
        re.search(rb"(?im)^\s*\[\s*include(?:if)?\b", config_raw) is None,
        "repository-local Git include routing is unsupported",
    )
    require(
        not os.path.lexists(ROOT / ".git/config.worktree"),
        "worktree-scoped Git configuration is unsupported",
    )
    for relative in (".git/info/exclude", ".git/info/attributes"):
        path = ROOT / relative
        if path.exists():
            raw = read_repository_file(relative, maximum=1024 * 1024, mode=0o644)
            try:
                decoded = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ContractError(
                    f"repository-local Git rules are not UTF-8: {relative}: {error}"
                ) from None
            effective = [
                line
                for line in decoded.splitlines()
                if line and not line.startswith("#")
            ]
            require(
                not effective,
                f"effective repository-local Git rules unsupported: {relative}",
            )
    config_rows = git(
        "config", "--local", "--null", "--list", "--no-includes", maximum=1024 * 1024
    )
    forbidden_config = (
        "core.fsmonitor",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "core.splitindex",
        "core.worktree",
        "extensions.objectformat",
        "extensions.partialclone",
        "extensions.refstorage",
        "extensions.worktreeconfig",
        "filter.",
        "include.",
        "includeif.",
        "index.sparse",
        "remote.origin.promisor",
    )
    config_keys: list[str] = []
    for record in config_rows.split(b"\0"):
        if not record:
            continue
        key_raw, separator, _value = record.partition(b"\n")
        require(separator == b"\n", "repository-local Git config row is malformed")
        try:
            key = key_raw.decode("ascii").lower()
        except UnicodeDecodeError as error:
            raise ContractError(
                f"repository-local Git config key is not ASCII: {error}"
            ) from None
        config_keys.append(key)
    require(
        not any(
            key == prefix or key.startswith(prefix)
            for key in config_keys
            for prefix in forbidden_config
        ),
        "repository-local Git routing/configuration is unsupported",
    )
    require(
        git_text("rev-parse", "--show-toplevel") == os.fspath(ROOT),
        "Git toplevel changed",
    )
    require(
        git_text("rev-parse", "--is-shallow-repository") == "false",
        "shallow repository unsupported",
    )
    git_dir = Path(git_text("rev-parse", "--absolute-git-dir"))
    common_dir = Path(
        git_text("rev-parse", "--path-format=absolute", "--git-common-dir")
    )
    require(
        git_dir == common_dir == git_dir_expected and git_dir.parent == ROOT,
        "linked worktree/common-dir routing unsupported",
    )
    for relative in (
        "info/grafts",
        "objects/info/alternates",
        "objects/info/http-alternates",
        "shallow",
    ):
        require(
            not (git_dir / relative).exists(),
            f"unsupported Git routing file: {relative}",
        )
    require(
        git("for-each-ref", "--format=%(refname)", "refs/replace/") == b"",
        "replacement refs unsupported",
    )
    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    require(
        SHA1_RE.fullmatch(head) is not None and SHA1_RE.fullmatch(tree) is not None,
        "HEAD identity malformed",
    )
    return head, tree


def validate_worktree(entries: dict[str, TreeEntry], head: str, tree: str) -> None:
    for path, entry in sorted(entries.items()):
        require(
            entry.mode in {"100644", "100755"}, f"tracked non-file unsupported: {path}"
        )
        mode = 0o755 if entry.mode == "100755" else 0o644
        raw = read_repository_file(path, maximum=MAX_BLOB_BYTES, mode=mode)
        require(
            raw == exact_object(entry.oid, "blob"),
            f"tracked worktree bytes differ from HEAD: {path}",
        )
    untracked = git("ls-files", "--others", "--exclude-standard", "-z")
    require(untracked == b"", "repository-visible untracked paths are present")
    require(
        git_predicate("diff", "--quiet", "--cached", head, "--"),
        "primary index differs from HEAD",
    )
    require(
        git_text("rev-parse", "HEAD") == head
        and git_text("rev-parse", "HEAD^{tree}") == tree,
        "HEAD changed during worktree validation",
    )


def validate_v3_authorities(base_entries: dict[str, TreeEntry]) -> None:
    for path, (size, digest, oid) in V3_FROZEN.items():
        entry = base_entries.get(path)
        mode = (
            "100755" if path == "scripts/check-current-source-state-v1.py" else "100644"
        )
        require(entry == TreeEntry(mode, oid), f"frozen v3 entry changed: {path}")
        raw = tree_blob(base_entries, path)
        require(
            len(raw) == size and sha256(raw) == digest,
            f"frozen v3 bytes changed: {path}",
        )


def validate_v3_retention(entries: dict[str, TreeEntry], label: str) -> None:
    """Keep historical v3 authorities immutable without freezing the live manifest."""
    for path in V3_RETAINED_PATHS:
        size, digest, oid = V3_FROZEN[path]
        mode = "100644"
        entry = entries.get(path)
        require(entry == TreeEntry(mode, oid), f"{label} changed v3 authority: {path}")
        raw = tree_blob(entries, path)
        require(
            len(raw) == size and sha256(raw) == digest,
            f"{label} changed v3 authority bytes: {path}",
        )
    require(
        V3_RECEIPT_RELATIVE not in entries,
        f"{label} introduced the reserved, uninstantiable v3 receipt",
    )


def expected_counterexample() -> dict[str, Any]:
    frozen: dict[str, dict[str, Any]] = {}
    for path, label in V3_FROZEN_LABELS.items():
        size, digest, oid = V3_FROZEN[path]
        frozen[label] = {
            "git_blob_oid_sha1": oid,
            "path": path,
            "sha256": digest,
            "size_bytes": size,
        }
    return {
        "counterexample": {
            "codeql_order": {
                "analysis_ids_in_required_language_order": [
                    RECOVERY_ANALYSIS_IDS[name] for name in LANGUAGE_ORDER
                ],
                "analysis_ids_strictly_increasing": False,
                "analysis_ids_unique": True,
                "languages": list(LANGUAGE_ORDER),
                "provider_order_claimed": False,
                "run_id": RECOVERY_RUNS["codeql"],
            },
            "source_state_topology": {
                "bc3_source_projection_entry_count": 731,
                "bc3_tree_entry_count": 732,
                "required_receipt_child_additions": 3,
                "required_receipt_child_source_projection_entry_count": 734,
                "v3_allows_current_source_manifest_modification": False,
                "v3_required_delta_entry_count": 3,
            },
        },
        "decision": {
            "composite_v3_receipt_issued": False,
            "disposition": "uninstantiable_for_the_exact_bc3_recovery_subject",
            "repair_class": "append_only_contract_revision",
            "rewrite_or_relabel_v3_forbidden": True,
        },
        "evidence_class": (
            "project_defined_contract_counterexample_not_scientific_evidence"
        ),
        "frozen_authorities": frozen,
        "nonimplications": COUNTEREXAMPLE_NONIMPLICATIONS,
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v3-impossibility/v1",
        "schema_revision": 1,
        "subject": {
            "recovery_commit": BASE_COMMIT,
            "recovery_tree": BASE_TREE,
            "v3_receipt_path": V3_RECEIPT_RELATIVE,
        },
    }


def validate_counterexample(entries: dict[str, TreeEntry]) -> None:
    raw = tree_blob(entries, COUNTEREXAMPLE_RELATIVE)
    value = parse_json(raw, "composite-v3 impossibility counterexample")
    root = exact_keys(
        value,
        {
            "counterexample",
            "decision",
            "evidence_class",
            "frozen_authorities",
            "nonimplications",
            "repository",
            "schema",
            "schema_revision",
            "subject",
        },
        "composite-v3 impossibility counterexample",
    )
    exact_int(root["schema_revision"], "counterexample schema revision", 1)
    require(root == expected_counterexample(), "counterexample content changed")


def current_source_entries(entries: dict[str, TreeEntry]) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    for path, entry in sorted(entries.items()):
        if path == CURRENT_SOURCE_RELATIVE:
            continue
        raw = tree_blob(entries, path)
        projected.append(
            {
                "git_mode": entry.mode,
                "path": path,
                "sha256": sha256(raw),
                "size_bytes": len(raw),
            }
        )
    return projected


def projected_descriptor(
    mapping: dict[str, dict[str, Any]], path: str, role: str
) -> dict[str, Any]:
    entry = mapping.get(path)
    require(entry is not None, f"current-source descriptor path is absent: {path}")
    return {
        "path": path,
        "role": role,
        "sha256": entry["sha256"],
        "size_bytes": entry["size_bytes"],
    }


def current_source_path_selected(path: str, selectors: tuple[str, ...]) -> bool:
    """Mirror the current-source v1 producer's established selector semantics."""
    return any(path == selector or path.startswith(selector) for selector in selectors)


def selected_projection(
    projected: list[dict[str, Any]], selectors: tuple[str, ...]
) -> dict[str, Any]:
    selected = [
        entry
        for entry in projected
        if current_source_path_selected(entry["path"], selectors)
    ]
    return {
        "entries_sha256": sha256(current_source_projection_bytes(selected)),
        "entry_count": len(selected),
    }


def validate_current_source(entries: dict[str, TreeEntry], label: str) -> None:
    raw = tree_blob(entries, CURRENT_SOURCE_RELATIVE)
    manifest = parse_json(raw, f"{label} current-source manifest")
    current_source_schema = parse_json(
        tree_blob(entries, CURRENT_SOURCE_SCHEMA_RELATIVE),
        f"{label} current-source schema",
    )
    validate_schema_instance(
        manifest, current_source_schema, f"{label} current-source manifest"
    )
    root = exact_keys(
        manifest, CURRENT_SOURCE_ROOT_KEYS, f"{label} current-source manifest"
    )
    binding = exact_keys(
        root["binding"], CURRENT_SOURCE_BINDING_KEYS, f"{label} current-source binding"
    )
    projection = exact_keys(
        root["source_projection"],
        CURRENT_SOURCE_PROJECTION_KEYS,
        f"{label} current-source projection",
    )
    exact_int(root["schema_revision"], f"{label} current-source schema revision", 1)
    exact_int(projection["entry_count"], f"{label} current-source entry count")
    expected = current_source_entries(entries)
    mapping = {entry["path"]: entry for entry in expected}
    expected_manifest = {
        "binding": {
            "commit_binding": (
                "not_self_asserted; resolve the manifest blob's containing commit from Git"
            ),
            "excluded_paths": [CURRENT_SOURCE_RELATIVE],
            "generated_at": "omitted_for_determinism",
            "projection_algorithm": (
                "newline-free canonical compact JSON of sorted repository .gitignore-aware "
                "tracked-plus-untracked entries {git_mode,path,sha256,size_bytes}; ambient "
                "global and .git/info excludes are ignored"
            ),
            "scope_kind": "self_excluding_worktree_source_projection",
        },
        "critical_artifacts": [
            projected_descriptor(mapping, path, role)
            for role, path in CURRENT_SOURCE_CRITICAL_ARTIFACTS
        ],
        "generated_by": "scripts/check-current-source-state-v1.py",
        "generated_pdfs": [
            projected_descriptor(mapping, path, "generated_pdf_byte_identity_only")
            for path in CURRENT_SOURCE_PDFS
        ],
        "historical_release": {
            "evidence_class": "tag_release_fact",
            "review_completion_inferred": False,
            "tag": "v0.9.0",
            "tag_object_sha": "dafa6cc9655eee70b4524ac92993c0dd820477e0",
            "tagged_commit_sha": "a9a275157237999c8da6ab813130d74f6113dec9",
        },
        "nonimplications": CURRENT_SOURCE_NONIMPLICATIONS,
        "repository": REPOSITORY,
        "review_inventory": {
            "artifact": "audit/evidence/FILE_REVIEW_LEDGER.csv",
            "evidence_scope": "historical_v0_9_0_exact_tag_tree_inventory",
            "human_reviewer_assignments": 0,
            "inventoried_files": 186,
            "line_review_dispositions": 0,
            "status": "inventory_is_not_review",
            "tagged_commit_sha": "a9a275157237999c8da6ab813130d74f6113dec9",
        },
        "schema": "pid-rs/current-source-state",
        "schema_revision": 1,
        "source_projection": {
            "entries": expected,
            "entries_sha256": sha256(current_source_projection_bytes(expected)),
            "entry_count": len(expected),
        },
        "subprojections": [
            {
                "name": name,
                "selectors": list(selectors),
                **selected_projection(expected, selectors),
            }
            for name, selectors in CURRENT_SOURCE_SUBPROJECTIONS
        ],
    }
    require(
        root == expected_manifest
        and binding == expected_manifest["binding"]
        and projection == expected_manifest["source_projection"],
        f"{label} current-source manifest does not project its containing tree",
    )


def validate_policy_value(value: Any) -> tuple[tuple[str, str, str], ...]:
    root = exact_keys(
        value,
        {
            "base",
            "c4",
            "nonimplications",
            "r4",
            "repository",
            "schema",
            "schema_revision",
        },
        "composite-v4 path policy",
    )
    exact_int(root["schema_revision"], "composite-v4 path-policy revision", 1)
    c4_rows = [
        {"mode": mode, "path": path, "role": role, "status": status}
        for path, status, mode, role in C4_POLICY_ROWS
    ]
    expected = {
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "c4": {
            "delta": c4_rows,
            "direct_parent_role": "hosted_recovery",
            "message": C4_MESSAGE,
        },
        "nonimplications": POLICY_NONIMPLICATIONS,
        "r4": {
            "delta": [
                {
                    "mode": "100644",
                    "path": CURRENT_SOURCE_RELATIVE,
                    "role": "self_excluding_source_state",
                    "status": "M",
                },
                {
                    "mode": "100644",
                    "path": CAPTURE_RELATIVE,
                    "role": "raw_hosted_capture",
                    "status": "A",
                },
                {
                    "mode": "100644",
                    "path": RECEIPT_RELATIVE,
                    "role": "typed_observation_receipt",
                    "status": "A",
                },
            ],
            "direct_parent_role": "c4_contract_migration",
            "message": R4_MESSAGE,
        },
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v4-path-policy/v1",
        "schema_revision": 1,
    }
    require(root == expected, "composite-v4 path policy changed")
    rendered = tuple((path, status, mode) for path, status, mode, _ in C4_POLICY_ROWS)
    require(
        rendered == tuple(sorted(set(rendered))),
        "composite-v4 hardcoded C4 policy is not sorted unique",
    )
    return rendered


def validate_policy(entries: dict[str, TreeEntry]) -> tuple[tuple[str, str, str], ...]:
    return validate_policy_value(
        parse_json(tree_blob(entries, POLICY_RELATIVE), "composite-v4 path policy")
    )


CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Capture time, network completeness, and provider response order are not claimed.",
    "Code-scanning alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to a workflow run or to that run's historical execution window.",
    "A successful hosted run is not mathematical, estimator, or application validation.",
    "The capture makes no claim about any PID functional, estimator, objective, or downstream use.",
]
RECEIPT_NONIMPLICATIONS = [
    "This receipt records bounded project-defined process observations, not authentication or attestation.",
    "Successful CI and CodeQL runs do not validate KSG mathematics, estimator behavior, calibration, or application fitness.",
    "The fixed CodeQL language order is a serialization contract; opaque provider identifiers have no numerical-order meaning.",
    "Code-scanning alert endpoints are repository-level current-state snapshots; role grouping does not attach them to a workflow run or reconstruct their state during that run.",
    "The receipt does not reconstruct, replace, or authenticate either unavailable historical sealed-index byte image.",
    "No result transfers to categorical MGW, Schick-Poland, Ehrlich continuous, Williams-Beer I_min, PID2, PID3, quantized, or mixed-support routes.",
    "No result transfers from a PID functional or estimator to an infomorphic objective without a separately named mapping theorem.",
]
ROLE_ORDER = (
    "recovery_ci",
    "recovery_codeql",
    "migration_ci",
    "migration_codeql",
    "migration_contract",
)
ROLE_KIND = {
    "recovery_ci": "ci",
    "recovery_codeql": "codeql",
    "migration_ci": "ci",
    "migration_codeql": "codeql",
    "migration_contract": "contract",
}
RECOVERY_ALERTS = {
    "dismissed": list(range(1, 47)),
    "fixed": list(range(158, 192)),
    "open": list(range(47, 158)),
}
RECOVERY_ANALYSIS_COUNTS = {
    "actions": {"results_count": 0, "rules_count": 17},
    "javascript-typescript": {"results_count": 0, "rules_count": 87},
    "python": {"results_count": 44, "rules_count": 43},
    "rust": {"results_count": 113, "rules_count": 25},
}
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


def parse_utc_timestamp(value: Any, label: str) -> datetime:
    require(
        type(value) is str and UTC_TIMESTAMP_RE.fullmatch(value) is not None,
        f"{label} timestamp is not canonical UTC",
    )
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as error:
        raise ContractError(
            f"{label} timestamp is not a calendar value: {error}"
        ) from None
    require(
        parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value,
        f"{label} timestamp round trip changed",
    )
    return parsed


POSTCOMMIT_NONIMPLICATIONS = [
    "This post-commit identity artifact is not authentication, authenticity, attestation, provenance, or proof of repository origin.",
    "It does not establish line review, human review, independent review, institutional review, or review completion.",
    "It does not establish scientific validity, estimator validity, formal correctness, source-to-formal correspondence, implementation refinement, numerical correctness, or application validity.",
    "Commit, tree, blob, and SHA-256 identifiers bind exact bytes under named algorithms; they do not confer trust or authenticity.",
    "Generation is bounded execution evidence for one committed state, not a CI-pass, release, tag, or fact about any other commit.",
    "Repeated endpoint checks are not an atomic history against concurrent filesystem or repository mutation.",
    "Repository-ignored products and Git object-store internals are outside this committed-tree identity projection.",
    "Emission uses standard output and validation uses standard input; this artifact does not bind storage location, filesystem identity, durability, or upload custody.",
]


def descriptor(entries: dict[str, TreeEntry], path: str) -> dict[str, Any]:
    raw = tree_blob(entries, path)
    return {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}


def contract_authorities(entries: dict[str, TreeEntry]) -> list[dict[str, Any]]:
    paths = (
        WORKFLOW_RELATIVE,
        COUNTEREXAMPLE_RELATIVE,
        PROCESS_RELATIVE,
        PROCESS_TEX_RELATIVE,
        PROCESS_PDF_RELATIVE,
        PROCESS_PDF_GATE_RELATIVE,
        PROCESS_VISUAL_RECEIPT_RELATIVE,
        PROCESS_FIGURE_PDF_RELATIVE,
        PROCESS_FIGURE_SVG_RELATIVE,
        POLICY_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        SCHEMA_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
    )
    return [descriptor(entries, path) for path in sorted(paths)]


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
        and value["response_kind"] in {"json", "zip"}
        and value["media_type"]
        in (
            {"application/json", "application/octet-stream"}
            if value["response_kind"] == "json"
            else {"application/zip", "application/octet-stream"}
        ),
        f"{label} scalar contract changed",
    )
    redirect = value["redirect"]
    if value["response_kind"] == "json":
        require(redirect is None, f"{label} JSON response unexpectedly redirected")
    elif redirect is not None:
        redirect_value = exact_keys(
            redirect,
            {"status_code", "target_host", "target_url_sha256"},
            f"{label} redirect",
        )
        require(
            redirect_value["status_code"] in {301, 302, 303, 307, 308}
            and type(redirect_value["status_code"]) is int
            and type(redirect_value["target_host"]) is str
            and redirect_value["target_host"].endswith(
                (".blob.core.windows.net", ".githubusercontent.com")
            )
            and SHA256_RE.fullmatch(redirect_value["target_url_sha256"]) is not None,
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
    if value["response_kind"] == "json":
        parse_json(raw, label, canonical=False)
    else:
        require(raw.startswith(b"PK"), f"{label} is not a ZIP archive")
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
    c4_entries: dict[str, TreeEntry],
    c4: str,
    c4_tree: str,
) -> tuple[dict[str, Any], CaptureRows]:
    value = parse_json(capture_raw, "composite-v4 hosted capture")
    capture_schema = parse_json(
        tree_blob(c4_entries, CAPTURE_SCHEMA_RELATIVE),
        "composite-v4 hosted-capture schema",
    )
    validate_schema_instance(value, capture_schema, "composite-v4 hosted capture")
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "nonimplications",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        "composite-v4 hosted capture",
    )
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v4"
        and root["schema_revision"] == 4
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS
        and root["capture_tool"] == descriptor(c4_entries, CAPTURE_TOOL_RELATIVE)
        and root["subject"]
        == {
            "contract_commit": c4,
            "contract_tree": c4_tree,
            "recovery_commit": BASE_COMMIT,
            "recovery_tree": BASE_TREE,
        },
        "composite-v4 capture identity changed",
    )
    runs = exact_keys(root["runs"], set(ROLE_ORDER), "composite-v4 capture runs")
    require(
        runs["recovery_ci"] == RECOVERY_RUNS["ci"]
        and runs["recovery_codeql"] == RECOVERY_RUNS["codeql"]
        and all(type(run_id) is int and run_id > 0 for run_id in runs.values())
        and len(set(runs.values())) == len(runs),
        "composite-v4 run identifiers changed or overlap",
    )
    retry_events = root["retry_events"]
    require(type(retry_events) is list, "capture retry events are not an array")
    retry_keys: list[tuple[str, int, int, str, int]] = []
    for event in retry_events:
        row = exact_keys(
            event,
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
            row["attempt"] in {1, 2}
            and type(row["attempt"]) is int
            and row["repetition"] in {1, 2}
            and type(row["repetition"]) is int
            and row["category"]
            in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(row["logical_request"]) is str
            and type(row["page"]) is int
            and row["page"] >= 0
            and type(row["path"]) is str
            and row["path"].startswith(f"/repos/{REPOSITORY}/")
            and SHA256_RE.fullmatch(row["response_sha256"]) is not None,
            "capture retry event changed",
        )
        exact_int(row["response_size_bytes"], "capture retry response size")
        require(
            row["response_size_bytes"] <= MAX_JSON_BYTES,
            "capture retry response exceeds bound",
        )
        retry_keys.append(
            (
                row["logical_request"],
                row["repetition"],
                row["page"],
                row["path"],
                row["attempt"],
            )
        )
    require(
        retry_keys == sorted(set(retry_keys)),
        "capture retry events are not sorted unique",
    )
    captures = root["captures"]
    require(
        type(captures) is list and 0 < len(captures) <= MAX_CAPTURE_ROWS,
        "capture response array count is outside the bound",
    )
    decoded = [
        decode_capture_row(row, f"capture response {index}")
        for index, row in enumerate(captures)
    ]
    require(
        sum(len(raw) for _row, raw in decoded) <= MAX_CAPTURE_BODY_BYTES,
        "retained provider bodies exceed the capture-tool budget",
    )
    keys = [
        (
            row["logical_request"],
            row["repetition"],
            row["page"],
            row["path"],
        )
        for row, _raw in decoded
    ]
    require(keys == sorted(set(keys)), "capture responses are not sorted unique")
    grouped: dict[tuple[str, int], list[tuple[dict[str, Any], bytes]]] = defaultdict(
        list
    )
    for row, raw in decoded:
        grouped[(row["logical_request"], row["repetition"])].append((row, raw))
    capture_request_keys = {
        (row["logical_request"], row["repetition"], row["page"], row["path"])
        for row, _raw in decoded
    }
    retry_groups: dict[tuple[str, int, int, str], list[int]] = defaultdict(list)
    for logical, repetition, page, path, attempt in retry_keys:
        key = (logical, repetition, page, path)
        require(
            key in capture_request_keys, "retry event has no successful request row"
        )
        retry_groups[key].append(attempt)
    for attempts in retry_groups.values():
        require(
            attempts == list(range(1, len(attempts) + 1)) and len(attempts) <= 2,
            "retry attempts are not consecutive and bounded",
        )
    return root, CaptureRows(dict(grouped))


def single_json_response(
    rows: CaptureRows, logical: str, repetition: int, path: str
) -> Any:
    values = rows.take(logical, repetition)
    require(
        len(values) == 1
        and values[0][0]["page"] == 0
        and values[0][0]["path"] == path
        and values[0][0]["response_kind"] == "json",
        f"single response shape changed: {logical}",
    )
    return parse_json(values[0][1], logical, canonical=False)


def paged_json_response(
    rows: CaptureRows,
    logical: str,
    repetition: int,
    path_prefix: str,
    field: str | None,
) -> list[Any]:
    values = rows.take(logical, repetition)
    require(
        0 < len(values) <= MAX_PAGES,
        f"paged response count is outside the bound: {logical}",
    )
    pages = [row["page"] for row, _raw in values]
    require(pages == list(range(1, len(values) + 1)), f"pagination changed: {logical}")
    combined: list[Any] = []
    lengths: list[int] = []
    totals: list[int] = []
    for page, (row, raw) in enumerate(values, start=1):
        separator = "&" if "?" in path_prefix else "?"
        expected_path = f"{path_prefix}{separator}per_page=100&page={page}"
        require(
            row["path"] == expected_path and row["response_kind"] == "json",
            f"pagination path changed: {logical} page {page}",
        )
        value = parse_json(raw, f"{logical} page {page}", canonical=False)
        if field is None:
            require(type(value) is list, f"{logical} page {page} is not an array")
            items = value
        else:
            require(
                type(value) is dict and type(value.get(field)) is list,
                f"{logical} page {page} shape changed",
            )
            items = value[field]
            total = value.get("total_count")
            require(type(total) is int and total >= 0, f"{logical} total_count changed")
            totals.append(total)
        lengths.append(len(items))
        combined.extend(items)
        require(
            len(combined) <= MAX_CAPTURE_ROWS,
            f"{logical} decoded row count exceeds the capture-tool bound",
        )
    require(lengths[-1] == 0, f"{logical} lacks an empty terminal page")
    require(
        all(length > 0 for length in lengths[:-1]), f"{logical} has an early empty page"
    )
    require(
        all(length == 100 for length in lengths[:-2]),
        f"{logical} has a short nonterminal data page",
    )
    if field is not None:
        require(
            len(set(totals)) == 1 and totals[0] == len(combined),
            f"{logical} total_count does not equal the paginated rows",
        )
    return combined


def normalized_run(value: Any, role: str, run_id: int, head: str) -> dict[str, Any]:
    require(type(value) is dict, f"{role} run response is not an object")
    repository = value.get("repository")
    head_repository = value.get("head_repository")
    expected = {
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
        expected["run_id"] == run_id
        and type(expected["run_id"]) is int
        and expected["head_sha"] == head
        and expected["head_branch"] == "main"
        and expected["run_attempt"] == 1
        and type(expected["run_attempt"]) is int
        and expected["status"] == "completed"
        and expected["conclusion"] == "success"
        and type(expected["workflow_id"]) is int
        and expected["workflow_id"] > 0
        and type(repository) is dict
        and repository.get("full_name") == REPOSITORY
        and type(head_repository) is dict
        and head_repository.get("full_name") == REPOSITORY
        and type(expected["repository_id"]) is int
        and expected["repository_id"] > 0
        and head_repository.get("id") == expected["repository_id"]
        and type(head_repository.get("id")) is int
        and all(type(expected[key]) is str for key in ("event", "name", "path")),
        f"{role} run identity or disposition changed",
    )
    if ROLE_KIND[role] == "ci":
        require(
            expected["workflow_id"] == 297369773
            and expected["name"] == "CI"
            and expected["path"] == ".github/workflows/ci.yml"
            and expected["event"] == "push",
            f"{role} CI workflow identity changed",
        )
    elif ROLE_KIND[role] == "codeql":
        require(
            expected["workflow_id"] == 310582096
            and expected["name"] == "Push on main"
            and expected["path"] == "dynamic/github-code-scanning/codeql"
            and expected["event"] == "dynamic",
            f"{role} CodeQL workflow identity changed",
        )
    else:
        require(
            expected["name"] == "KSG M1a composite v4"
            and expected["path"] == WORKFLOW_RELATIVE
            and expected["event"] == "push",
            "migration contract workflow identity changed",
        )
    return expected


def normalized_jobs(
    values: list[Any], role: str, run_id: int, head: str
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for value in values:
        require(type(value) is dict, f"{role} job is not an object")
        job_id = exact_int(value.get("id"), f"{role} job id", 1)
        steps_raw = value.get("steps")
        require(type(steps_raw) is list and steps_raw, f"{role} job steps are absent")
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
                and normalized["conclusion"] == "success"
                and type(normalized["name"]) is str
                and normalized["name"] != ""
                and type(normalized["number"]) is int
                and normalized["number"] > 0,
                f"{role} job step is incomplete or adverse",
            )
            steps.append(normalized)
        steps.sort(key=lambda item: item["number"])
        require(
            len(steps) == len({step["number"] for step in steps}),
            f"{role} job step numbers are not unique",
        )
        normalized_job = {
            "completed_at": value.get("completed_at"),
            "conclusion": value.get("conclusion"),
            "job_id": job_id,
            "name": value.get("name"),
            "started_at": value.get("started_at"),
            "status": value.get("status"),
            "steps": steps,
        }
        require(
            normalized_job["status"] == "completed"
            and normalized_job["conclusion"] == "success"
            and value.get("run_id") == run_id
            and type(value.get("run_id")) is int
            and value.get("run_attempt") == 1
            and type(value.get("run_attempt")) is int
            and value.get("head_sha") == head
            and all(
                type(normalized_job[key]) is str and normalized_job[key] != ""
                for key in ("completed_at", "name", "started_at")
            ),
            f"{role} job is incomplete or adverse",
        )
        started = parse_utc_timestamp(normalized_job["started_at"], f"{role} started")
        completed = parse_utc_timestamp(
            normalized_job["completed_at"], f"{role} completed"
        )
        require(started <= completed, f"{role} job timestamps are reversed")
        jobs.append(normalized_job)
    jobs.sort(key=lambda item: item["job_id"])
    require(
        len(jobs) == len({job["job_id"] for job in jobs}),
        f"{role} job IDs are not unique",
    )
    expected_count = (
        45 if ROLE_KIND[role] == "ci" else 4 if ROLE_KIND[role] == "codeql" else 1
    )
    require(len(jobs) == expected_count, f"{role} job count changed")
    names = tuple(sorted(job["name"] for job in jobs))
    if ROLE_KIND[role] == "ci":
        require(names == EXPECTED_CI_JOB_NAMES, f"{role} CI job-name roster changed")
    elif ROLE_KIND[role] == "codeql":
        require(
            names
            == tuple(sorted(f"Analyze ({language})" for language in LANGUAGE_ORDER)),
            f"{role} CodeQL job-name roster changed",
        )
    else:
        require(
            names == ("Validate the composite-v4 contract",),
            "migration contract job-name roster changed",
        )
        user_steps = {
            "Validate static contract in normal and optimized modes",
            "Reject the adversarial contract and capture vectors",
            "Upload the exact static result",
        }
        observed_steps = [step["name"] for step in jobs[0]["steps"]]
        require(
            all(observed_steps.count(name) == 1 for name in user_steps),
            "migration contract user-step roster changed",
        )
    return jobs


def zip_members(raw: bytes, label: str) -> list[dict[str, Any]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw), "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise ContractError(f"cannot parse {label} ZIP: {error}") from None
    members: list[dict[str, Any]] = []
    names: list[str] = []
    total = 0
    with archive:
        infos = archive.infolist()
        require(
            0 < len(infos) <= MAX_ZIP_MEMBERS,
            f"{label} member count is outside the bound",
        )
        for info in infos:
            require(
                not info.is_dir() and not (info.flag_bits & 1),
                f"{label} has a directory or encrypted member",
            )
            require(
                info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                f"{label} uses an unsupported compression method",
            )
            path = info.filename
            validate_relative_path(path, f"{label} member path")
            require(
                "\\" not in path and "\0" not in path, f"{label} member path is unsafe"
            )
            mode = info.external_attr >> 16
            require(
                mode == 0
                or (stat.S_ISREG(mode) and not (mode & (stat.S_IWGRP | stat.S_IWOTH))),
                f"{label} member mode is unsafe",
            )
            total += info.file_size
            require(total <= MAX_JSON_BYTES, f"{label} expands beyond bound")
            try:
                member = archive.read(info)
            except (
                NotImplementedError,
                OSError,
                RuntimeError,
                zipfile.BadZipFile,
            ) as error:
                raise ContractError(f"cannot read {label} member: {error}") from None
            require(len(member) == info.file_size, f"{label} member size changed")
            names.append(path)
            members.append(
                {"path": path, "sha256": sha256(member), "size_bytes": len(member)}
            )
    require(len(names) == len(set(names)), f"{label} member names are not unique")
    return sorted(members, key=lambda item: item["path"])


def member_bytes(raw: bytes, path: str, label: str) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            return archive.read(path)
    except (
        KeyError,
        NotImplementedError,
        OSError,
        RuntimeError,
        zipfile.BadZipFile,
    ) as error:
        raise ContractError(f"cannot read {label} member {path}: {error}") from None


def normalized_artifacts(
    values: list[Any],
    rows: CaptureRows,
    role: str,
    run_id: int,
    repository_id: int,
    head: str,
    repetition: int,
) -> tuple[list[dict[str, Any]], dict[int, bytes]]:
    artifacts: list[dict[str, Any]] = []
    archives: dict[int, bytes] = {}
    for value in values:
        require(type(value) is dict, f"{role} artifact is not an object")
        artifact_id = exact_int(value.get("id"), f"{role} artifact id", 1)
        logical = f"{role}_artifact_{artifact_id}"
        captures = rows.take(logical, repetition)
        path = f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
        require(
            len(captures) == 1
            and captures[0][0]["page"] == 0
            and captures[0][0]["path"] == path
            and captures[0][0]["response_kind"] == "zip",
            f"{role} artifact download shape changed",
        )
        archive = captures[0][1]
        api_digest = value.get("digest")
        api_size = value.get("size_in_bytes")
        workflow_run = value.get("workflow_run")
        require(
            type(api_digest) is str
            and api_digest == f"sha256:{sha256(archive)}"
            and type(api_size) is int
            and api_size == len(archive)
            and value.get("expired") is False
            and type(value.get("name")) is str
            and value["name"] != "",
            f"{role} artifact metadata does not bind the archive",
        )
        require(
            type(workflow_run) is dict
            and workflow_run.get("id") == run_id
            and type(workflow_run.get("id")) is int
            and workflow_run.get("head_sha") == head
            and workflow_run.get("head_branch") == "main"
            and workflow_run.get("repository_id") == repository_id
            and type(workflow_run.get("repository_id")) is int
            and workflow_run.get("head_repository_id") == repository_id
            and type(workflow_run.get("head_repository_id")) is int,
            f"{role} artifact is not joined to its run/head/repository",
        )
        archives[artifact_id] = archive
        artifacts.append(
            {
                "api_digest": api_digest,
                "archive_sha256": sha256(archive),
                "archive_size_bytes": len(archive),
                "artifact_id": artifact_id,
                "expired": False,
                "members": zip_members(archive, f"{role} artifact {artifact_id}"),
                "name": value["name"],
            }
        )
    artifacts.sort(key=lambda item: item["artifact_id"])
    require(
        len(artifacts) == len({item["artifact_id"] for item in artifacts}),
        f"{role} artifact IDs are duplicated",
    )
    return artifacts, archives


def validate_postcommit_artifact(
    artifacts: list[dict[str, Any]],
    archives: dict[int, bytes],
    entries: dict[str, TreeEntry],
    commit: str,
    tree: str,
    role: str,
) -> None:
    expected_names = {
        "coverage-lcov",
        f"post-commit-source-state-v2-{commit}",
        "workspace-sbom",
    }
    require(
        len(artifacts) == 3
        and len({item["name"] for item in artifacts}) == 3
        and {item["name"] for item in artifacts} == expected_names,
        f"{role} CI artifact names changed",
    )
    targets = [
        item
        for item in artifacts
        if item["name"].startswith("post-commit-source-state-v2-")
    ]
    require(len(targets) == 1, f"{role} postcommit artifact is not unique")
    target = targets[0]
    member_path = "pid-rs-post-commit-source-state-v2.json"
    matching_members = [
        item for item in target["members"] if item["path"] == member_path
    ]
    require(
        len(matching_members) == 1 and target["members"] == matching_members,
        f"{role} postcommit archive members changed",
    )
    raw = member_bytes(
        archives[target["artifact_id"]], member_path, f"{role} postcommit"
    )
    value = parse_json(raw, f"{role} postcommit artifact")
    root = exact_keys(
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
        f"{role} postcommit artifact",
    )
    manifest_raw = tree_blob(entries, CURRENT_SOURCE_RELATIVE)
    manifest = parse_json(manifest_raw, f"{role} current-source manifest")
    manifest_entry = entries[CURRENT_SOURCE_RELATIVE]
    binding = exact_keys(
        root["binding"],
        {"commit_oid", "git_object_format", "manifest", "tree_oid"},
        f"{role} postcommit binding",
    )
    manifest_binding = exact_keys(
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
        f"{role} postcommit manifest binding",
    )
    require(
        root["schema"] == "pid-rs/post-commit-source-state"
        and root["schema_revision"] == 2
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["generated_by"] == "scripts/check-post-commit-source-state-v2.py"
        and root["evidence_class"] == "post_commit_identity_evidence_only"
        and type(binding) is dict
        and binding.get("commit_oid") == commit
        and binding.get("tree_oid") == tree
        and binding.get("git_object_format") == "sha1"
        and manifest_binding
        == {
            "blob_oid": manifest_entry.oid,
            "path": CURRENT_SOURCE_RELATIVE,
            "schema": "pid-rs/current-source-state",
            "schema_revision": 1,
            "sha256": sha256(manifest_raw),
            "size_bytes": len(manifest_raw),
            "source_projection_entries_sha256": manifest["source_projection"][
                "entries_sha256"
            ],
            "source_projection_entry_count": manifest["source_projection"][
                "entry_count"
            ],
        }
        and root["checks"]
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
        and root["determinism"]
        == {
            "artifact_transport": "canonical_json_stdout_or_stdin_only",
            "commit_cycle": "none; the committed manifest excludes itself and this artifact is generated only after commit",
            "generated_at": "omitted_for_determinism",
            "storage_custody": "caller_owned_not_bound_by_this_artifact",
        }
        and root["nonimplications"] == POSTCOMMIT_NONIMPLICATIONS,
        f"{role} postcommit artifact does not bind its committed source tree",
    )


def validate_contract_artifact(
    artifacts: list[dict[str, Any]],
    archives: dict[int, bytes],
    c4: str,
    c4_tree: str,
) -> None:
    require(len(artifacts) == 1, "contract workflow artifact count changed")
    artifact = artifacts[0]
    require(
        artifact["name"] == f"ksg-m1a-composite-v4-static-{c4}",
        "contract workflow artifact name changed",
    )
    path = "ksg-m1a-composite-v4-static.json"
    matching_members = [item for item in artifact["members"] if item["path"] == path]
    require(
        len(matching_members) == 1 and artifact["members"] == matching_members,
        "contract workflow archive members changed",
    )
    raw = member_bytes(archives[artifact["artifact_id"]], path, "contract workflow")
    value = parse_json(raw, "contract workflow static result", canonical=False)
    require(
        raw == canonical_json(value, pretty=False)
        and value
        == {
            "c4_commit": c4,
            "head": c4,
            "r4_commit": None,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v4-static-validation/v1",
            "tree": c4_tree,
        },
        "contract workflow static result changed",
    )


def normalized_analyses(
    values: list[Any], jobs: list[dict[str, Any]], head: str, role: str
) -> list[dict[str, Any]]:
    candidates = [
        value
        for value in values
        if type(value) is dict
        and value.get("commit_sha") == head
        and value.get("ref") == "refs/heads/main"
    ]
    require(len(candidates) == 4, f"{role} exact-head CodeQL analysis count changed")
    by_language: dict[str, dict[str, Any]] = {}
    for value in candidates:
        category = value.get("category")
        require(type(category) is str, f"{role} CodeQL category changed")
        matches = [
            language
            for language in LANGUAGE_ORDER
            if category == f"/language:{language}"
        ]
        require(len(matches) == 1, f"{role} CodeQL language/category join changed")
        language = matches[0]
        require(language not in by_language, f"{role} CodeQL language is duplicated")
        matching_jobs = [job for job in jobs if job["name"] == f"Analyze ({language})"]
        require(len(matching_jobs) == 1, f"{role} CodeQL job/language join changed")
        analysis_id = exact_int(value.get("id"), f"{role} analysis id", 1)
        results_count = exact_int(value.get("results_count"), f"{role} results count")
        rules_count = exact_int(value.get("rules_count"), f"{role} rules count")
        require(
            type(value.get("error")) in {str, type(None)}
            and type(value.get("warning")) in {str, type(None)}
            and value.get("error") in {"", None}
            and value.get("warning") in {"", None}
            and rules_count > 0,
            f"{role} CodeQL error/warning type changed",
        )
        if role == "recovery_codeql":
            require(
                analysis_id == RECOVERY_ANALYSIS_IDS[language],
                "recovery CodeQL analysis ID/language join changed",
            )
            require(
                {
                    "results_count": results_count,
                    "rules_count": rules_count,
                }
                == RECOVERY_ANALYSIS_COUNTS[language],
                "recovery CodeQL result/rule counts changed",
            )
        by_language[language] = {
            "analysis_id": analysis_id,
            "category": category,
            "commit_sha": head,
            "error": value.get("error"),
            "job_join": "language_category_and_job_name",
            "language": language,
            "matching_job_id": matching_jobs[0]["job_id"],
            "ref": "refs/heads/main",
            "results_count": results_count,
            "rules_count": rules_count,
            "warning": value.get("warning"),
        }
    analyses = [by_language[language] for language in LANGUAGE_ORDER]
    ids = [item["analysis_id"] for item in analyses]
    require(len(ids) == len(set(ids)), f"{role} analysis IDs are not unique")
    return analyses


def normalized_alerts(values: dict[str, list[Any]], role: str) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for state in ("dismissed", "fixed", "open"):
        numbers: list[int] = []
        for value in values[state]:
            require(
                type(value) is dict and value.get("state") == state,
                f"{role} alert state changed",
            )
            numbers.append(exact_int(value.get("number"), f"{role} alert number", 1))
        numbers.sort()
        require(
            len(numbers) == len(set(numbers)),
            f"{role} {state} alert numbers are not unique",
        )
        result[state] = numbers
    all_numbers = [number for state in result.values() for number in state]
    require(
        len(all_numbers) == len(set(all_numbers)),
        f"{role} alert-state partitions overlap",
    )
    return result


def projection_digest(value: Any) -> str:
    return sha256(canonical_json(value, pretty=False))


def derive_observation(
    rows: CaptureRows,
    role: str,
    run_id: int,
    head: str,
    entries: dict[str, TreeEntry],
    tree: str,
) -> dict[str, Any]:
    repetitions: list[dict[str, Any]] = []
    for repetition in (1, 2):
        run_value = single_json_response(
            rows,
            f"{role}_run",
            repetition,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}",
        )
        run = normalized_run(run_value, role, run_id, head)
        job_values = paged_json_response(
            rows,
            f"{role}_jobs",
            repetition,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs",
            "jobs",
        )
        jobs = normalized_jobs(job_values, role, run_id, head)
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
        if ROLE_KIND[role] == "ci":
            validate_postcommit_artifact(artifacts, archives, entries, head, tree, role)
        elif ROLE_KIND[role] == "contract":
            validate_contract_artifact(artifacts, archives, head, tree)
        else:
            require(artifacts == [], f"{role} unexpectedly published artifacts")
        analyses: list[dict[str, Any]] = []
        alerts = {"dismissed": [], "fixed": [], "open": []}
        if ROLE_KIND[role] == "codeql":
            if role == "recovery_codeql":
                analysis_values = []
                for analysis_id in RECOVERY_ANALYSIS_IDS.values():
                    analysis_value = single_json_response(
                        rows,
                        f"{role}_analysis_{analysis_id}",
                        repetition,
                        f"/repos/{REPOSITORY}/code-scanning/analyses/{analysis_id}",
                    )
                    require(
                        type(analysis_value) is dict
                        and analysis_value.get("id") == analysis_id
                        and type(analysis_value.get("id")) is int,
                        "recovery CodeQL response path/body identity changed",
                    )
                    analysis_values.append(analysis_value)
            else:
                analysis_values = paged_json_response(
                    rows,
                    f"{role}_analyses",
                    repetition,
                    f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain",
                    None,
                )
            analyses = normalized_analyses(analysis_values, jobs, head, role)
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
        observation = {
            "alerts": alerts,
            "alerts_sha256": projection_digest(alerts),
            "analyses": analyses,
            "analyses_sha256": projection_digest(analyses),
            "artifacts": artifacts,
            "artifacts_sha256": projection_digest(artifacts),
            "jobs": jobs,
            "jobs_sha256": projection_digest(jobs),
            "kind": ROLE_KIND[role],
            "run": run,
        }
        repetitions.append(observation)
    require(
        canonical_json(repetitions[0], pretty=False)
        == canonical_json(repetitions[1], pretty=False),
        f"{role} repeated normalized observations differ",
    )
    return repetitions[0]


def derive_receipt(
    capture_raw: bytes,
    c4_entries: dict[str, TreeEntry],
    c4: str,
    c4_tree: str,
) -> dict[str, Any]:
    capture, rows = validate_capture_root(capture_raw, c4_entries, c4, c4_tree)
    observations: dict[str, dict[str, Any]] = {}
    for role in ROLE_ORDER:
        head = BASE_COMMIT if role.startswith("recovery_") else c4
        tree = BASE_TREE if role.startswith("recovery_") else c4_tree
        entries = parse_tree(tree)
        observations[role] = derive_observation(
            rows, role, capture["runs"][role], head, entries, tree
        )
    rows.finish()
    run_ids = [observation["run"]["run_id"] for observation in observations.values()]
    job_sets = [
        {job["job_id"] for job in observation["jobs"]}
        for observation in observations.values()
    ]
    require(len(run_ids) == len(set(run_ids)), "hosted run IDs overlap")
    repository_ids = [
        observation["run"]["repository_id"] for observation in observations.values()
    ]
    require(
        len(set(repository_ids)) == 1,
        "hosted observations disagree on repository numeric identity",
    )
    require(
        all(
            job_sets[left].isdisjoint(job_sets[right])
            for left in range(len(job_sets))
            for right in range(left + 1, len(job_sets))
        ),
        "hosted job identifier domains overlap",
    )
    all_analysis_ids = [
        analysis["analysis_id"]
        for observation in observations.values()
        for analysis in observation["analyses"]
    ]
    require(
        len(all_analysis_ids) == len(set(all_analysis_ids))
        and len(all_analysis_ids) == 8,
        "hosted analysis identifiers are not globally unique within their resource type",
    )
    all_artifact_ids = [
        artifact["artifact_id"]
        for observation in observations.values()
        for artifact in observation["artifacts"]
    ]
    require(
        len(all_artifact_ids) == len(set(all_artifact_ids)),
        "hosted artifact identifiers are not globally unique within their resource type",
    )
    require(
        observations["recovery_codeql"]["alerts"] == RECOVERY_ALERTS
        and observations["migration_codeql"]["alerts"] == RECOVERY_ALERTS,
        "repository-level CodeQL alert-state snapshot changed from the retained baseline or a new alert appeared",
    )
    return {
        "capture_binding": {
            "path": CAPTURE_RELATIVE,
            "sha256": sha256(capture_raw),
            "size_bytes": len(capture_raw),
        },
        "contract_authorities": contract_authorities(c4_entries),
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "observations": observations,
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v4",
        "schema_revision": 4,
        "subject": {
            "contract_commit": c4,
            "contract_tree": c4_tree,
            "recovery_commit": BASE_COMMIT,
            "recovery_tree": BASE_TREE,
        },
        "verdict": {
            "composite_v3_receipt_issued": False,
            "contract_migration": "pass",
            "hosted_observation": "pass",
            "scientific_validation": "not_adjudicated",
        },
    }


def commit_introducing(path: str) -> str:
    raw = git("log", "--format=%H", "--diff-filter=A", "--", path, maximum=1024 * 1024)
    try:
        commits = [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeDecodeError as error:
        raise ContractError(f"cannot parse path history for {path}: {error}") from None
    require(
        len(commits) == 1 and SHA1_RE.fullmatch(commits[0]) is not None,
        f"path introduction is not unique: {path}",
    )
    return commits[0]


def validate_contract_topology(head: str, head_tree: str) -> tuple[str, str | None]:
    base_commit = parse_commit(BASE_COMMIT)
    require(
        base_commit.tree == BASE_TREE
        and base_commit.parent == CORRECTION_COMMIT
        and base_commit.message == BASE_MESSAGE,
        "base recovery identity changed",
    )
    correction_commit = parse_commit(CORRECTION_COMMIT)
    implementation_commit = parse_commit(IMPLEMENTATION_COMMIT)
    require(
        correction_commit.parent == IMPLEMENTATION_COMMIT
        and correction_commit.message == CORRECTION_MESSAGE
        and implementation_commit.message == IMPLEMENTATION_MESSAGE,
        "correction/implementation ancestry or exact envelope changed",
    )
    base_entries = parse_tree(BASE_TREE)
    validate_v3_authorities(base_entries)
    validate_v3_retention(base_entries, "recovery base")
    head_entries = parse_tree(head_tree)
    validate_worktree(head_entries, head, head_tree)
    receipt_present = RECEIPT_RELATIVE in head_entries
    if receipt_present:
        r4 = commit_introducing(RECEIPT_RELATIVE)
        r4_commit = parse_commit(r4)
        require(r4_commit.message == R4_MESSAGE, "R4 commit message changed")
        c4 = r4_commit.parent
    else:
        r4 = None
        c4 = head
    c4_commit = parse_commit(c4)
    require(
        c4_commit.parent == BASE_COMMIT and c4_commit.message == C4_MESSAGE,
        "C4 is not the exact unsigned single-parent direct child of recovery",
    )
    c4_entries = parse_tree(c4_commit.tree)
    require(
        SCRIPT == ROOT / CHECKER_RELATIVE
        and read_repository_file(CHECKER_RELATIVE, maximum=MAX_BLOB_BYTES, mode=0o644)
        == tree_blob(c4_entries, CHECKER_RELATIVE),
        "executing checker bytes differ from the retained C4 checker blob",
    )
    validate_v3_retention(c4_entries, "C4")
    policy_delta = validate_policy(c4_entries)
    require(
        changed_entries(base_entries, c4_entries) == policy_delta,
        "C4 tree delta differs from path policy",
    )
    require(
        RECEIPT_RELATIVE not in c4_entries and CAPTURE_RELATIVE not in c4_entries,
        "C4 contains prospective R4 evidence",
    )
    validate_counterexample(c4_entries)
    validate_current_source(c4_entries, "C4")
    validate_lean_r9_contract(
        tree_blob(c4_entries, CHECKER_RELATIVE),
        tree_blob(c4_entries, LEAN_CHECKER_RELATIVE),
        tree_blob(c4_entries, LEAN_R9_REJECTED_RELATIVE),
        tree_blob(c4_entries, LEAN_R9_RELATIVE),
    )
    authority_modes = {
        CHECKER_RELATIVE: "100644",
        SELF_TEST_RELATIVE: "100644",
        CAPTURE_TOOL_RELATIVE: "100644",
        SCHEMA_RELATIVE: "100644",
        CAPTURE_SCHEMA_RELATIVE: "100644",
        POLICY_RELATIVE: "100644",
        COUNTEREXAMPLE_RELATIVE: "100644",
        PROCESS_RELATIVE: "100644",
        PROCESS_TEX_RELATIVE: "100644",
        PROCESS_PDF_RELATIVE: "100644",
        PROCESS_PDF_GATE_RELATIVE: "100755",
        PROCESS_VISUAL_RECEIPT_RELATIVE: "100644",
        PROCESS_FIGURE_PDF_RELATIVE: "100644",
        PROCESS_FIGURE_SVG_RELATIVE: "100644",
        WORKFLOW_RELATIVE: "100644",
        LEAN_R9_REJECTED_RELATIVE: "100644",
        LEAN_R9_RELATIVE: "100644",
    }
    for path, mode in authority_modes.items():
        require(
            path in c4_entries and c4_entries[path].mode == mode,
            f"C4 authority absent or wrong mode: {path}",
        )
    if r4 is None:
        require(head == c4, "receipt-absent state is not exact C4")
        return c4, None
    require(
        git_predicate("merge-base", "--is-ancestor", r4, head),
        "R4 is not an ancestor of HEAD",
    )
    r4_commit = parse_commit(r4)
    r4_entries = parse_tree(r4_commit.tree)
    validate_v3_retention(r4_entries, "R4")
    expected_r4_delta = (
        (CURRENT_SOURCE_RELATIVE, "M", "100644"),
        (CAPTURE_RELATIVE, "A", "100644"),
        (RECEIPT_RELATIVE, "A", "100644"),
    )
    require(
        changed_entries(c4_entries, r4_entries) == expected_r4_delta,
        "R4 delta is not exact",
    )
    validate_current_source(r4_entries, "R4")
    retained = (
        CHECKER_RELATIVE,
        SELF_TEST_RELATIVE,
        CAPTURE_TOOL_RELATIVE,
        SCHEMA_RELATIVE,
        CAPTURE_SCHEMA_RELATIVE,
        POLICY_RELATIVE,
        COUNTEREXAMPLE_RELATIVE,
        PROCESS_RELATIVE,
        PROCESS_TEX_RELATIVE,
        PROCESS_PDF_RELATIVE,
        PROCESS_PDF_GATE_RELATIVE,
        PROCESS_VISUAL_RECEIPT_RELATIVE,
        PROCESS_FIGURE_PDF_RELATIVE,
        PROCESS_FIGURE_SVG_RELATIVE,
        WORKFLOW_RELATIVE,
        LEAN_R9_REJECTED_RELATIVE,
        LEAN_R9_RELATIVE,
        RECEIPT_RELATIVE,
        CAPTURE_RELATIVE,
    )
    descendants = [
        r4,
        *git("rev-list", "--reverse", "--ancestry-path", f"{r4}..{head}")
        .decode("ascii")
        .splitlines(),
    ]
    for commit in descendants:
        commit_tree = r4_commit.tree if commit == r4 else parse_descendant_tree(commit)
        current_entries = parse_tree(commit_tree)
        validate_v3_retention(current_entries, f"descendant {commit[:12]}")
        for path in retained:
            expected = r4_entries[path]
            require(
                current_entries.get(path) == expected,
                f"retained v4 authority changed in descendant: {path}",
            )
        validate_current_source(current_entries, f"descendant {commit[:12]}")
    return c4, r4


def bounded_stdin() -> bytes:
    raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    require(
        0 < len(raw) <= MAX_JSON_BYTES,
        "standard-input JSON size is outside the bound",
    )
    return raw


def validate_receipt_bytes(
    receipt_raw: bytes,
    capture_raw: bytes,
    c4: str,
    c4_tree: str,
    c4_entries: dict[str, TreeEntry],
) -> dict[str, Any]:
    receipt = parse_json(receipt_raw, "composite-v4 receipt")
    receipt_schema = parse_json(
        tree_blob(c4_entries, SCHEMA_RELATIVE), "composite-v4 receipt schema"
    )
    validate_schema_instance(receipt, receipt_schema, "composite-v4 receipt")
    expected = derive_receipt(capture_raw, c4_entries, c4, c4_tree)
    require(
        receipt == expected,
        "composite-v4 receipt differs from the raw-capture derivation",
    )
    return receipt


def validate_static() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c4, r4 = validate_contract_topology(head, head_tree)
    c4_tree = parse_commit(c4).tree
    c4_entries = parse_tree(c4_tree)
    for relative, label in (
        (CAPTURE_SCHEMA_RELATIVE, "composite-v4 hosted-capture"),
        (SCHEMA_RELATIVE, "composite-v4 receipt"),
    ):
        definition = V4_SCHEMA_DEFINITIONS[relative]
        raw = tree_blob(c4_entries, relative)
        validate_contract_schema_definition(
            parse_json(raw, f"{label} schema"),
            label,
            expected_id=definition["id"],
            expected_required=definition["required"],
            expected_sha256=definition["sha256"],
            expected_size_bytes=definition["size_bytes"],
            raw=raw,
        )
    workflow_raw = tree_blob(c4_entries, WORKFLOW_RELATIVE)
    require(
        len(workflow_raw) == EXPECTED_WORKFLOW_SIZE_BYTES
        and sha256(workflow_raw) == EXPECTED_WORKFLOW_SHA256,
        "dedicated composite-v4 workflow exact bytes changed",
    )
    if r4 is not None:
        r4_entries = parse_tree(parse_commit(r4).tree)
        validate_receipt_bytes(
            tree_blob(r4_entries, RECEIPT_RELATIVE),
            tree_blob(r4_entries, CAPTURE_RELATIVE),
            c4,
            c4_tree,
            c4_entries,
        )
    return {
        "c4_commit": c4,
        "head": head,
        "r4_commit": r4,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v4-static-validation/v1",
        "tree": head_tree,
    }


def derive_receipt_command() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c4, r4 = validate_contract_topology(head, head_tree)
    require(
        r4 is None and head == c4,
        "receipt derivation requires exact receipt-absent C4",
    )
    return derive_receipt(bounded_stdin(), parse_tree(head_tree), c4, head_tree)


def validate_receipt_command() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c4, r4 = validate_contract_topology(head, head_tree)
    require(r4 is not None, "receipt validation requires R4 or a retained descendant")
    r4_entries = parse_tree(parse_commit(r4).tree)
    receipt_raw = bounded_stdin()
    require(
        receipt_raw == tree_blob(r4_entries, RECEIPT_RELATIVE),
        "receipt stdin differs from the R4 introduction blob",
    )
    c4_tree = parse_commit(c4).tree
    validate_receipt_bytes(
        receipt_raw,
        tree_blob(r4_entries, CAPTURE_RELATIVE),
        c4,
        c4_tree,
        parse_tree(c4_tree),
    )
    return {
        "c4_commit": c4,
        "head": head,
        "r4_commit": r4,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v4-receipt-validation/v1",
        "tree": head_tree,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-static", action="store_true")
    modes.add_argument("--derive-receipt", action="store_true")
    modes.add_argument("--validate-receipt", action="store_true")
    modes.add_argument(
        "--self-test-vector", action="store_true", help=argparse.SUPPRESS
    )
    modes.add_argument(
        "--self-test-schema-vector", action="store_true", help=argparse.SUPPRESS
    )
    modes.add_argument(
        "--self-test-schema-definition-vector",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    modes.add_argument(
        "--self-test-policy-vector", action="store_true", help=argparse.SUPPRESS
    )
    modes.add_argument(
        "--self-test-capture-vectors", action="store_true", help=argparse.SUPPRESS
    )
    modes.add_argument(
        "--self-test-receipt-vector", action="store_true", help=argparse.SUPPRESS
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.validate_static:
            result = validate_static()
        elif arguments.derive_receipt:
            result = derive_receipt_command()
        elif arguments.validate_receipt:
            result = validate_receipt_command()
        elif arguments.self_test_vector:
            raw = bounded_stdin()
            value = parse_json(raw, "composite-v4 self-test vector")
            require(
                current_source_path_selected("README.md", ("README.md",))
                and current_source_path_selected("README.md.backup", ("README.md",))
                and not current_source_path_selected("READM", ("README.md",)),
                "current-source v1 selector semantics changed",
            )
            result = {
                "current_source_compact_sha256": sha256(
                    current_source_projection_bytes(value)
                ),
                "result": "pass",
                "value_sha256": sha256(canonical_json(value, pretty=False)),
            }
        elif arguments.self_test_schema_vector:
            raw = bounded_stdin()
            vector = exact_keys(
                parse_json(raw, "composite-v4 schema self-test vector"),
                {"instance", "schema"},
                "composite-v4 schema self-test vector",
            )
            validate_schema_instance(
                vector["instance"], vector["schema"], "self-test instance"
            )
            result = {"result": "pass"}
        elif arguments.self_test_schema_definition_vector:
            vector = exact_keys(
                parse_json(
                    bounded_stdin(), "composite-v4 schema-definition self-test vector"
                ),
                {
                    "expected_id",
                    "expected_required",
                    "expected_sha256",
                    "expected_size_bytes",
                    "schema",
                },
                "composite-v4 schema-definition self-test vector",
            )
            require(
                type(vector["expected_id"]) is str
                and type(vector["expected_required"]) is list
                and all(type(item) is str for item in vector["expected_required"]),
                "schema-definition self-test authority changed",
            )
            schema_raw = canonical_json(vector["schema"], pretty=True)
            validate_contract_schema_definition(
                vector["schema"],
                "self-test contract",
                expected_id=vector["expected_id"],
                expected_required=vector["expected_required"],
                expected_sha256=vector["expected_sha256"],
                expected_size_bytes=exact_int(
                    vector["expected_size_bytes"],
                    "schema-definition self-test expected size",
                    1,
                ),
                raw=schema_raw,
            )
            result = {"result": "pass"}
        elif arguments.self_test_policy_vector:
            validate_policy_value(
                parse_json(bounded_stdin(), "composite-v4 policy self-test vector")
            )
            result = {"result": "pass"}
        elif arguments.self_test_capture_vectors:
            head, head_tree = validate_repository()
            c4, r4 = validate_contract_topology(head, head_tree)
            c4_tree = parse_commit(c4).tree
            vector = exact_keys(
                parse_json(bounded_stdin(), "composite-v4 capture self-test vectors"),
                {"negative", "positive"},
                "composite-v4 capture self-test vectors",
            )
            require(
                type(vector["negative"]) is list and vector["negative"],
                "capture negative-vector array is empty",
            )
            c4_entries = parse_tree(c4_tree)
            positive = derive_receipt(
                canonical_json(vector["positive"], pretty=True),
                c4_entries,
                c4,
                c4_tree,
            )
            for index, negative in enumerate(vector["negative"]):
                try:
                    derive_receipt(
                        canonical_json(negative, pretty=True),
                        c4_entries,
                        c4,
                        c4_tree,
                    )
                except ContractError:
                    continue
                raise ContractError(f"capture negative vector {index} was accepted")
            result = {
                "negative_count": len(vector["negative"]),
                "receipt": positive,
                "receipt_sha256": sha256(canonical_json(positive, pretty=True)),
                "result": "pass",
            }
        else:
            head, head_tree = validate_repository()
            c4, _r4 = validate_contract_topology(head, head_tree)
            c4_tree = parse_commit(c4).tree
            c4_entries = parse_tree(c4_tree)
            vector = exact_keys(
                parse_json(bounded_stdin(), "composite-v4 receipt self-test vector"),
                {"capture", "receipt"},
                "composite-v4 receipt self-test vector",
            )
            validate_receipt_bytes(
                canonical_json(vector["receipt"], pretty=True),
                canonical_json(vector["capture"], pretty=True),
                c4,
                c4_tree,
                c4_entries,
            )
            result = {"result": "pass"}
    except ContractError as error:
        if (
            arguments.self_test_vector
            or arguments.self_test_schema_vector
            or arguments.self_test_schema_definition_vector
            or arguments.self_test_policy_vector
            or arguments.self_test_receipt_vector
        ):
            result = {"result": "fail"}
        else:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
    except Exception:
        if (
            arguments.self_test_vector
            or arguments.self_test_schema_vector
            or arguments.self_test_schema_definition_vector
            or arguments.self_test_policy_vector
            or arguments.self_test_receipt_vector
        ):
            result = {"result": "fail"}
        else:
            print("ERROR: unexpected bounded validation failure", file=sys.stderr)
            return 1
    sys.stdout.buffer.write(
        canonical_json(result, pretty=bool(arguments.derive_receipt))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
