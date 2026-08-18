#!/usr/bin/env python3
"""Validate the append-only KSG M1a composite-v5 correction contract.

The contract preserves the published C4 commit and records its failed hosted
qualification attempt without granting that attempt qualification credit.  It
then permits one exact C5 bounded repair and one exact R5 hosted receipt.  This
is operational evidence only: no PID, estimator, mathematical, security, or
application-validity conclusion is derived here.
"""

from __future__ import annotations

import argparse
import base64
from collections import defaultdict
from dataclasses import dataclass
import hashlib
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
        "ERROR: check-ksg-m1a-composite-v5.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"

C4_COMMIT = "da253576a5f76e99633fff4de5cf1118f967b90d"
C4_TREE = "916245b95f90bd98b8bd37a72e148fb9328d5c52"
C4_PARENT = "bc3aa80fb6025e709c2906a08bce25a4fac40578"
C4_MESSAGE = "Migrate KSG M1a composite receipt contract\n"
C4_IDENTITY = (
    b"author Sepehr Mahmoudian <sepmhn@gmail.com> 1786999943 +0200",
    b"committer Sepehr Mahmoudian <sepmhn@gmail.com> 1786999943 +0200",
)
C5_MESSAGE = "Repair KSG M1a composite v5 contract\n"
R5_MESSAGE = "Record KSG M1a composite v5 receipt\n"
FORBIDDEN_R4_MESSAGE = "Record KSG M1a composite v4 receipt\n"

CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v5.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v5-self-test.py"
CAPTURE_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v5.py"
CAPTURE_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v5.schema.json"
)
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v5.schema.json"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v5-path-policy-v1.json"
PREDECESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-"
    "hosted-capture-v5-2026-08-18.json"
)
SUCCESSOR_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v5-2026-08-18.json"
)
RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v5-2026-08-18.json"
CURRENT_SOURCE_RELATIVE = "audit/evidence/current-source-state-v1.json"
LEAN_R9_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-15-r9.json"
)
LEAN_R10_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r10.json"
)
V4_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v4.yml"
V5_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v5.yml"
PROCESS_ARTIFACTS = (
    (
        "audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md",
        "100644",
        "operational_boundary_record",
    ),
    (
        "audit/evidence/ksg-rev4-m1a-composite-v5-boundary-visual-receipt-2026-08-18.md",
        "100644",
        "operational_boundary_visual_receipt",
    ),
    (
        "audit/formal/latex/ksg-m1a-composite-v5-boundary.tex",
        "100644",
        "operational_boundary_latex_source",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg",
        "100644",
        "operational_boundary_vector_source",
    ),
    (
        "audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf",
        "100644",
        "operational_boundary_vector_derivative",
    ),
    (
        "output/pdf/ksg-m1a-composite-v5-boundary.pdf",
        "100644",
        "operational_boundary_publication_pdf",
    ),
    (
        "output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv",
        "100644",
        "operational_boundary_rendering_receipt",
    ),
    (
        "scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh",
        "100755",
        "operational_boundary_pdf_gate",
    ),
    (
        "scripts/check-ksg-m1a-composite-v5-boundary-pdf-self-test.sh",
        "100755",
        "operational_boundary_pdf_gate_self_test",
    ),
)

V4_CAPTURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json"
)
V4_RECEIPT_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json"
FORBIDDEN_R4_PATHS = (V4_CAPTURE_RELATIVE, V4_RECEIPT_RELATIVE)

V4_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v4.py"
V4_CHECKER_SHA256 = "8fb61c4fcc831be1847ddec7448e2dbeb6f2f51b915b4b6cd91df561c491b5bb"
V4_CHECKER_SIZE_BYTES = 141530
V4_CAPTURE_PRIMITIVE = {
    "path": "scripts/capture-ksg-m1a-composite-v4.py",
    "sha256": "7cf9a6fe57c2a828def8789524069e14a21d35739a5019b4310613c8f44065ef",
    "size_bytes": 34626,
}
V4_WORKFLOW_SHA256 = "541f4bcfe7135c63f4e4b76c5d119b2c64e60550e365885c4ac98f9c8c48df04"
V4_WORKFLOW_SIZE_BYTES = 2213
LEAN_R9_SHA256 = "e9136696563e007f98498080bb7a769c60353df83537ee90976ee9cc66c0873f"
LEAN_R9_SIZE_BYTES = 132912

# These two byte identities are frozen with the C5 commit.  They intentionally
# bind the retired live v4 trigger and the replacement v5 trigger separately.
RETIRED_V4_WORKFLOW_SHA256 = "TO_BE_FROZEN"
RETIRED_V4_WORKFLOW_SIZE_BYTES = 0
V5_WORKFLOW_SHA256 = "TO_BE_FROZEN"
V5_WORKFLOW_SIZE_BYTES = 0
V5_PDF_PREREQUISITE_BLOCKS = (
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
V5_PUBLICATION_STEP_MARKER = (
    b"      - name: Validate the bounded successor publication\n"
)
CAPTURE_SCHEMA_SHA256 = (
    "cbacb1bd7b5896a497312fd2a2809a33e43699bb3e4eb081d19cde6803b69c24"
)
CAPTURE_SCHEMA_SIZE_BYTES = 14123
RECEIPT_SCHEMA_SHA256 = (
    "b721d392f724f463633a71ed984909696a9b9fb450dc6bd3aa09f8feac38642e"
)
RECEIPT_SCHEMA_SIZE_BYTES = 10246

CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "The two retrieval repetitions are correlated observations of provider state, not independent replications.",
    "The predecessor failure phase records terminal failures; it grants no hosted-success, R4-receipt, mathematical, estimator, or application-validation credit.",
    "A successful successor run is not mathematical, estimator, security, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not observations foreign-keyed to the workflow run or its historical execution window.",
    "Failed-job log bytes record provider output but do not by themselves establish a unique defect cause or remediation.",
    "Capture time, network completeness, provider response order, and trusted provider time are not claimed.",
    "The capture makes no claim about any PID functional, objective, estimator, or downstream use.",
]
RECEIPT_NONIMPLICATIONS = [
    "C4 is a published commit, but its hosted qualification attempt failed and receives zero qualification, R4-receipt, mathematical, estimator, or application-validation credit.",
    "R4 is permanently unissued; the v5 repair does not create, reconstruct, rename, or backdate a v4 receipt.",
    "C5 makes bounded repairs to named failure surfaces and R5 records fresh attempt-1 hosted success; neither rewrites C4 history nor proves a unique root cause.",
    "The two retrieval repetitions are correlated provider observations, not independent replications or a transparency log.",
    "CodeQL analysis and alert observations are repository-level current-state snapshots, not run-historical foreign-key evidence.",
    "Captured provider bytes and identifiers do not authenticate themselves or establish trusted provider time.",
    "Failed-job log bytes preserve observed output but do not by themselves prove a unique defect cause or that the successor repair is the only possible remedy.",
    "A passing checker, workflow, capture, or receipt is not mathematical proof, estimator validation, security certification, scientific review, or application approval.",
    "No result transfers among KSG mutual information, categorical or continuous shared exclusions, I_min, PID2, PID3, quantized or mixed-support routes, resampling procedures, or downstream objectives.",
    "Git and SHA-256 identities bind named bytes and topology only; they do not establish authorship, authenticity, independent reproduction, or indefinite storage durability.",
]

PREDECESSOR_RUNS = {
    "predecessor_ci": 32079866560,
    "predecessor_codeql": 32079865482,
    "predecessor_contract": 32079866461,
}
PREDECESSOR_REQUIRED_FAILED_JOB_IDS = {
    "predecessor_ci": {95540603816, 95540603850, 95540603999},
    "predecessor_codeql": set(),
    "predecessor_contract": {95540602684},
}
PREDECESSOR_REQUIRED_FAILURE_IDENTITIES = {
    "predecessor_ci": {
        95540603816: (
            "Package + semver + unused dependencies",
            ("Run scripts/check-release-state-self-test.sh",),
        ),
        95540603850: (
            "Exact-count directed-rounding SxPID2 reference",
            ("Run python3 -I -S -B scripts/check-certified-sxpid2-claim.py",),
        ),
        95540603999: (
            "Formal LaTeX / PDF inventory and cross-toolchain structure",
            ("Check the zeta-to-PID transfer firewall",),
        ),
    },
    "predecessor_codeql": {},
    "predecessor_contract": {
        95540602684: (
            "Validate the composite-v4 contract",
            ("Validate static contract in normal and optimized modes",),
        )
    },
}
PREDECESSOR_REQUIRED_LOG_MARKERS = {
    95540602684: ("ERROR: worktree-scoped Git configuration is unsupported",),
    95540603816: ("fatal: not a git repository",),
    95540603850: (
        "certified SxPID2 claim check failed: release-audit just dependency line exact digest changed",
    ),
    95540603999: ("zeta-to-PID transfer firewall: WORKFLOW.section_sha256",),
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

# Centralized exact policy rows.  This tuple is replaced once, immediately
# before C5 is committed, from the independently reviewed path inventory.
C5_POLICY_ROWS: tuple[tuple[str, str, str, str], ...] = ()
R5_POLICY_ROWS = (
    (
        CURRENT_SOURCE_RELATIVE,
        "M",
        "100644",
        "self_excluding_source_state",
    ),
    (RECEIPT_RELATIVE, "A", "100644", "derived_v5_receipt"),
    (
        SUCCESSOR_CAPTURE_RELATIVE,
        "A",
        "100644",
        "fresh_successor_hosted_capture",
    ),
)
POLICY_NONIMPLICATIONS: list[str] = []

MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_CAPTURE_BODY_BYTES = 22 * 1024 * 1024
MAX_CAPTURE_ROWS = 4096
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bootstrap_v4_primitives() -> Any:
    path = ROOT / V4_CHECKER_RELATIVE
    try:
        before = path.lstat()
        if not (
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o644
            and before.st_size == V4_CHECKER_SIZE_BYTES
        ):
            raise OSError("unsafe immutable v4 primitive metadata")
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
                raise OSError("immutable v4 primitive identity changed before read")
            raw = b""
            while len(raw) < opened.st_size:
                chunk = os.read(file_descriptor, opened.st_size - len(raw))
                if chunk == b"":
                    raise OSError("short immutable v4 primitive read")
                raw += chunk
            if os.read(file_descriptor, 1) != b"":
                raise OSError("immutable v4 primitive grew during read")
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
                raise OSError("immutable v4 primitive identity changed during read")
        finally:
            os.close(file_descriptor)
    except OSError as error:
        print(f"ERROR: cannot read immutable v4 primitives: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    if not (
        SCRIPT == ROOT / CHECKER_RELATIVE
        and len(raw) == V4_CHECKER_SIZE_BYTES
        and hashlib.sha256(raw).hexdigest() == V4_CHECKER_SHA256
    ):
        print("ERROR: immutable v4 primitive bytes changed", file=sys.stderr)
        raise SystemExit(2)
    module_name = "_pid_rs_immutable_composite_v4"
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
        print(f"ERROR: cannot load immutable v4 primitives: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    return module


_v4 = _bootstrap_v4_primitives()
ContractError = _v4.ContractError
require = _v4.require
exact_int = _v4.exact_int
exact_keys = _v4.exact_keys
canonical_json = _v4.canonical_json
parse_json = _v4.parse_json
validate_schema_instance = _v4.validate_schema_instance
sha256 = _v4.sha256
parse_tree = _v4.parse_tree
parse_commit = _v4.parse_commit
parse_descendant_tree = _v4.parse_descendant_tree
changed_entries = _v4.changed_entries
tree_blob = _v4.tree_blob
validate_repository = _v4.validate_repository
validate_worktree = _v4.validate_worktree
read_repository_file = _v4.read_repository_file
git = _v4.git
git_text = _v4.git_text
git_predicate = _v4.git_predicate
descriptor_v4 = _v4.descriptor
project_digest = _v4.projection_digest
single_json_response = _v4.single_json_response
paged_json_response = _v4.paged_json_response
normalized_artifacts_v4 = _v4.normalized_artifacts
validate_postcommit_artifact = _v4.validate_postcommit_artifact
normalized_analyses_v4 = _v4.normalized_analyses
normalized_alerts_v4 = _v4.normalized_alerts
member_bytes = _v4.member_bytes
parse_utc_timestamp = _v4.parse_utc_timestamp


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
    _v4.validate_contract_schema_definition(
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
            and _v4.validate_relative_path(path, f"{label}[{index}] path")
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
            "c5",
            "nonimplications",
            "r5",
            "repository",
            "schema",
            "schema_revision",
        },
        "composite-v5 path policy",
    )
    base = exact_keys(
        root["base"],
        {"commit", "r4_status", "reserved_absent_paths", "tree"},
        "composite-v5 policy base",
    )
    c5 = exact_keys(
        root["c5"], {"delta", "direct_parent_role", "message"}, "composite-v5 policy C5"
    )
    r5 = exact_keys(
        root["r5"], {"delta", "direct_parent_role", "message"}, "composite-v5 policy R5"
    )
    require(
        root["schema"] == "pid-rs/ksg-m1a-composite-v5-path-policy"
        and root["schema_revision"] == 1
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and base
        == {
            "commit": C4_COMMIT,
            "r4_status": "permanently_unissued",
            "reserved_absent_paths": list(FORBIDDEN_R4_PATHS),
            "tree": C4_TREE,
        }
        and c5["direct_parent_role"] == "published_c4_contract"
        and c5["message"] == C5_MESSAGE
        and r5["direct_parent_role"] == "c5_contract_repair"
        and r5["message"] == R5_MESSAGE
        and root["nonimplications"] == POLICY_NONIMPLICATIONS,
        "composite-v5 policy identity or nonimplication boundary changed",
    )
    c5_rows = _policy_rows(c5["delta"], "composite-v5 policy C5 delta")
    r5_rows = _policy_rows(r5["delta"], "composite-v5 policy R5 delta")
    require(C5_POLICY_ROWS and c5_rows == C5_POLICY_ROWS, "C5 policy rows changed")
    require(r5_rows == R5_POLICY_ROWS, "R5 policy rows changed")
    return tuple((path, status, mode) for path, status, mode, _role in c5_rows)


def validate_policy(entries: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    return validate_policy_value(
        parse_json(tree_blob(entries, POLICY_RELATIVE), "composite-v5 path policy")
    )


def validate_replay_values(r9_raw: bytes, r10: Any) -> None:
    require(type(r10) is dict, "Lean r10 current replay is not an object")
    prior_hashes = r10.get("prior_replay_preservation_sha256")
    prior_schemas = r10.get("prior_replay_schema")
    require(
        r10.get("schema") == "pid-rs/lean-current-project-replay/v2"
        and r10.get("status") == "passed"
        and type(prior_hashes) is dict
        and type(prior_schemas) is dict
        and prior_hashes.get(LEAN_R9_RELATIVE) == sha256(r9_raw)
        and prior_schemas.get(LEAN_R9_RELATIVE)
        == "pid-rs/lean-current-project-replay/v2",
        "Lean r10 does not classify exact r9 bytes as prior replay evidence",
    )


def validate_replay_pair(c5_entries: dict[str, Any]) -> None:
    r9_raw = require_exact_bytes(
        c5_entries,
        LEAN_R9_RELATIVE,
        LEAN_R9_SHA256,
        LEAN_R9_SIZE_BYTES,
        "Lean r9 prior replay",
    )
    r10 = parse_json(
        tree_blob(c5_entries, LEAN_R10_RELATIVE),
        "Lean r10 current replay",
        canonical=False,
    )
    validate_replay_values(r9_raw, r10)


def validate_exact_delta(
    actual: tuple[tuple[str, str, str], ...],
    expected: tuple[tuple[str, str, str], ...],
    label: str,
) -> None:
    require(actual == expected, f"{label} delta is not exact")


def validate_v5_workflow_prerequisites(raw: bytes) -> None:
    require(b"\r" not in raw, "successor workflow line endings changed")
    offsets: list[int] = []
    for index, block in enumerate(V5_PDF_PREREQUISITE_BLOCKS, start=1):
        require(
            raw.count(block) == 1,
            f"successor workflow PDF prerequisite block {index} changed",
        )
        offsets.append(raw.index(block))
    require(
        raw.count(V5_PUBLICATION_STEP_MARKER) == 1
        and offsets[0] < offsets[1] < raw.index(V5_PUBLICATION_STEP_MARKER),
        "successor workflow PDF prerequisites are not ordered before validation",
    )


def validate_schema_authorities(
    c5_entries: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    capture_raw = require_exact_bytes(
        c5_entries,
        CAPTURE_SCHEMA_RELATIVE,
        CAPTURE_SCHEMA_SHA256,
        CAPTURE_SCHEMA_SIZE_BYTES,
        "composite-v5 capture schema",
    )
    receipt_raw = require_exact_bytes(
        c5_entries,
        RECEIPT_SCHEMA_RELATIVE,
        RECEIPT_SCHEMA_SHA256,
        RECEIPT_SCHEMA_SIZE_BYTES,
        "composite-v5 receipt schema",
    )
    capture_schema = parse_json(capture_raw, "composite-v5 hosted-capture schema")
    validate_schema_instance(
        {}, capture_schema, "composite-v5 hosted-capture", definition_only=True
    )
    require(
        type(capture_schema) is dict
        and capture_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
        and capture_schema.get("$id")
        == "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v5.schema.json"
        and capture_schema.get("oneOf")
        == [
            {"$ref": "#/$defs/predecessorDocument"},
            {"$ref": "#/$defs/successorDocument"},
        ],
        "composite-v5 hosted-capture schema identity changed",
    )
    receipt_schema = _closed_schema(
        receipt_raw,
        "composite-v5 receipt",
        "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/ksg-rev4-m1a-composite-receipt-v5.schema.json",
        [
            "capture_bindings",
            "contract_authorities",
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
    return capture_schema, receipt_schema


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
    c5_entries: dict[str, Any],
    c5: str,
    c5_tree: str,
    capture_schema: dict[str, Any],
) -> tuple[dict[str, Any], CaptureRows]:
    value = parse_json(capture_raw, f"composite-v5 {phase} hosted capture")
    validate_schema_instance(
        value, capture_schema, f"composite-v5 {phase} hosted capture"
    )
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v4_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        f"composite-v5 {phase} capture",
    )
    expected_subject = {
        "predecessor_commit": C4_COMMIT,
        "predecessor_tree": C4_TREE,
    }
    if phase == "successor_qualification":
        expected_subject.update({"successor_commit": c5, "successor_tree": c5_tree})
    require(
        root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v5"
        and root["schema_revision"] == 5
        and type(root["schema_revision"]) is int
        and root["repository"] == REPOSITORY
        and root["phase"] == phase
        and root["subject"] == expected_subject
        and root["capture_tool"] == descriptor(c5_entries, CAPTURE_TOOL_RELATIVE)
        and root["immutable_v4_primitives"] == V4_CAPTURE_PRIMITIVE
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS,
        f"composite-v5 {phase} capture identity changed",
    )
    roles = PHASE_ROLES[phase]
    runs = exact_keys(root["runs"], set(roles), f"composite-v5 {phase} run map")
    require(
        all(type(item) is int and item > 0 for item in runs.values())
        and len(set(runs.values())) == 3
        and (phase != "predecessor_failure" or runs == PREDECESSOR_RUNS),
        f"composite-v5 {phase} run identifiers changed or overlap",
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
        version = "v4" if role.startswith("predecessor_") else "v5"
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
        required_failed <= failed
        and (role != "predecessor_contract" or failed == required_failed),
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
        require(names == _v4.EXPECTED_CI_JOB_NAMES, f"{role} CI job roster changed")
    elif ROLE_KIND[role] == "codeql":
        require(
            names
            == tuple(
                sorted(f"Analyze ({language})" for language in _v4.LANGUAGE_ORDER)
            ),
            f"{role} CodeQL job roster changed",
        )
    else:
        expected = (
            "Validate the composite-v4 contract"
            if role.startswith("predecessor_")
            else "Validate the composite-v5 correction contract"
        )
        require(names == (expected,), f"{role} contract job name changed")
        step_names = [item["name"] for item in jobs[0]["steps"]]
        if role == "predecessor_contract":
            required_steps = {
                "Validate static contract in normal and optimized modes",
                "Reject the adversarial contract and capture vectors",
                "Upload the exact static result",
            }
            require(
                all(step_names.count(name) == 1 for name in required_steps)
                and [
                    item["name"]
                    for item in jobs[0]["steps"]
                    if item["conclusion"] == "failure"
                ]
                == ["Validate static contract in normal and optimized modes"],
                "predecessor contract failure-step identity changed",
            )
        else:
            required_steps = {
                "Install the hash-pinned PDF verifier dependency",
                "Install the runner PDF toolchain",
                "Normalize only the reviewed inert checkout residue",
                "Recheck every bounded C4 failure surface",
                "Validate the bounded successor publication",
                "Validate fresh replay and current-source custody",
                "Validate static v5 contract in normal and optimized modes",
                "Upload the exact v5 static result",
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
    artifacts: list[dict[str, Any]], archives: dict[int, bytes], c5: str, c5_tree: str
) -> None:
    require(len(artifacts) == 1, "successor contract artifact count changed")
    artifact = artifacts[0]
    require(
        artifact["name"] == f"ksg-m1a-composite-v5-static-{c5}",
        "successor contract artifact name changed",
    )
    path = "ksg-m1a-composite-v5-static.json"
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
            "c4_commit": C4_COMMIT,
            "c5_commit": c5,
            "head": c5,
            "r5_commit": None,
            "result": "pass",
            "schema": "pid-rs/ksg-rev4-m1a-composite-v5-static-validation/v1",
            "tree": c5_tree,
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
        artifacts, archives = normalized_artifacts_v4(
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
            analyses = normalized_analyses_v4(analysis_values, jobs, head, role)
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
            alerts = normalized_alerts_v4(alert_values, role)
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
    c5_entries: dict[str, Any],
    c5: str,
    c5_tree: str,
    capture_schema: dict[str, Any],
) -> dict[str, Any]:
    capture, rows = validate_capture_root(
        capture_raw, phase, c5_entries, c5, c5_tree, capture_schema
    )
    head = C4_COMMIT if phase == "predecessor_failure" else c5
    tree = C4_TREE if phase == "predecessor_failure" else c5_tree
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
    c4_entries: dict[str, Any], c5_entries: dict[str, Any]
) -> list[dict[str, Any]]:
    values = [
        authority_descriptor(
            c4_entries, V4_CHECKER_RELATIVE, "immutable_v4_checker_primitives"
        ),
        authority_descriptor(
            c4_entries, V4_CAPTURE_PRIMITIVE["path"], "immutable_v4_capture_primitives"
        ),
        authority_descriptor(c4_entries, V4_WORKFLOW_RELATIVE, "published_c4_workflow"),
        authority_descriptor(c5_entries, V4_WORKFLOW_RELATIVE, "retired_v4_workflow"),
        authority_descriptor(c5_entries, V5_WORKFLOW_RELATIVE, "successor_v5_workflow"),
        authority_descriptor(c5_entries, CHECKER_RELATIVE, "v5_checker"),
        authority_descriptor(c5_entries, SELF_TEST_RELATIVE, "v5_checker_self_test"),
        authority_descriptor(c5_entries, CAPTURE_TOOL_RELATIVE, "v5_capture_tool"),
        authority_descriptor(c5_entries, CAPTURE_SCHEMA_RELATIVE, "v5_capture_schema"),
        authority_descriptor(c5_entries, RECEIPT_SCHEMA_RELATIVE, "v5_receipt_schema"),
        authority_descriptor(c5_entries, POLICY_RELATIVE, "v5_path_policy"),
        authority_descriptor(
            c5_entries, CURRENT_SOURCE_RELATIVE, "c5_current_source_state"
        ),
        authority_descriptor(c5_entries, LEAN_R9_RELATIVE, "prior_r9_lean_replay"),
        authority_descriptor(c5_entries, LEAN_R10_RELATIVE, "current_r10_lean_replay"),
    ]
    values.extend(
        authority_descriptor(c5_entries, path, role)
        for path, _mode, role in PROCESS_ARTIFACTS
    )
    return sorted(values, key=lambda item: (item["path"], item["role"]))


def derive_receipt(
    predecessor_raw: bytes,
    successor_raw: bytes,
    c5_entries: dict[str, Any],
    c5: str,
    c5_tree: str,
    capture_schema: dict[str, Any],
) -> dict[str, Any]:
    predecessor = derive_phase(
        predecessor_raw,
        "predecessor_failure",
        c5_entries,
        c5,
        c5_tree,
        capture_schema,
    )
    successor = derive_phase(
        successor_raw,
        "successor_qualification",
        c5_entries,
        c5,
        c5_tree,
        capture_schema,
    )
    validate_identifier_domains([predecessor, successor], "predecessor/successor")
    c4_entries = parse_tree(C4_TREE)
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
        "contract_authorities": contract_authorities(c4_entries, c5_entries),
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "observations": [predecessor, successor],
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v5",
        "schema_revision": 5,
        "subject": {
            "c4_commit": C4_COMMIT,
            "c4_tree": C4_TREE,
            "c5_commit": c5,
            "c5_tree": c5_tree,
        },
        "verdict": {
            "c4_hosted_qualification": "failed_zero_credit",
            "c4_publication": "published",
            "c5_bounded_repair": "pass",
            "c5_hosted_observation": "pass",
            "r4_receipt_issued": False,
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


def _validate_no_r4_history(c5: str, head: str) -> None:
    for oid in _new_reachable_commits(C4_COMMIT, head):
        tree = C4_TREE if oid == C4_COMMIT else parse_descendant_tree(oid)
        entries = parse_tree(tree)
        raw_commit = _v4.exact_object(oid, "commit", maximum=1024 * 1024)
        _headers, separator, message_raw = raw_commit.partition(b"\n\n")
        require(separator == b"\n\n", f"commit message envelope changed at {oid[:12]}")
        try:
            message = message_raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ContractError(
                f"descendant commit message is not UTF-8 at {oid[:12]}: {error}"
            ) from None
        validate_no_r4_tree_message(entries, message, oid)
    require(
        git_predicate("merge-base", "--is-ancestor", c5, head),
        "C5 is not an ancestor of HEAD",
    )


def validate_no_r4_tree_message(
    entries: dict[str, Any], message: str, oid: str
) -> None:
    require(
        all(path not in entries for path in FORBIDDEN_R4_PATHS),
        f"forbidden R4 path appeared in history at {oid[:12]}",
    )
    require(
        message != FORBIDDEN_R4_MESSAGE,
        "forbidden R4 commit message appeared in history",
    )


def validate_topology(head: str, head_tree: str) -> tuple[str, str, str | None]:
    c4 = parse_commit(C4_COMMIT)
    require(
        c4.tree == C4_TREE
        and c4.parent == C4_PARENT
        and c4.message == C4_MESSAGE
        and (c4.author, c4.committer) == C4_IDENTITY,
        "published C4 exact commit envelope changed",
    )
    c4_entries = parse_tree(C4_TREE)
    require_exact_bytes(
        c4_entries,
        V4_CHECKER_RELATIVE,
        V4_CHECKER_SHA256,
        V4_CHECKER_SIZE_BYTES,
        "immutable v4 checker primitives",
    )
    require_exact_bytes(
        c4_entries,
        V4_CAPTURE_PRIMITIVE["path"],
        V4_CAPTURE_PRIMITIVE["sha256"],
        V4_CAPTURE_PRIMITIVE["size_bytes"],
        "immutable v4 capture primitives",
    )
    require_exact_bytes(
        c4_entries,
        V4_WORKFLOW_RELATIVE,
        V4_WORKFLOW_SHA256,
        V4_WORKFLOW_SIZE_BYTES,
        "published C4 workflow",
    )
    require(
        all(path not in c4_entries for path in FORBIDDEN_R4_PATHS),
        "published C4 contains prospective R4 evidence",
    )
    head_entries = parse_tree(head_tree)
    receipt_present = RECEIPT_RELATIVE in head_entries
    if receipt_present:
        r5 = _v4.commit_introducing(RECEIPT_RELATIVE)
        r5_commit = parse_commit(r5)
        require(r5_commit.message == R5_MESSAGE, "R5 exact message changed")
        c5 = r5_commit.parent
    else:
        r5 = None
        c5 = head
    c5_commit = parse_commit(c5)
    require(
        c5_commit.parent == C4_COMMIT and c5_commit.message == C5_MESSAGE,
        "C5 is not the exact unsigned direct child of published C4",
    )
    c5_entries = parse_tree(c5_commit.tree)
    policy_delta = validate_policy(c5_entries)
    validate_exact_delta(
        changed_entries(c4_entries, c5_entries), policy_delta, "C5 path-policy"
    )
    require(
        PREDECESSOR_CAPTURE_RELATIVE in c5_entries
        and SUCCESSOR_CAPTURE_RELATIVE not in c5_entries
        and RECEIPT_RELATIVE not in c5_entries,
        "C5 failure/successor evidence phase separation changed",
    )
    require_exact_bytes(
        c5_entries,
        V4_CHECKER_RELATIVE,
        V4_CHECKER_SHA256,
        V4_CHECKER_SIZE_BYTES,
        "C5-retained immutable v4 checker primitives",
    )
    require_exact_bytes(
        c5_entries,
        V4_CAPTURE_PRIMITIVE["path"],
        V4_CAPTURE_PRIMITIVE["sha256"],
        V4_CAPTURE_PRIMITIVE["size_bytes"],
        "C5-retained immutable v4 capture primitives",
    )
    validate_replay_pair(c5_entries)
    _v4.validate_current_source(c5_entries, "C5")
    require_exact_bytes(
        c5_entries,
        V4_WORKFLOW_RELATIVE,
        RETIRED_V4_WORKFLOW_SHA256,
        RETIRED_V4_WORKFLOW_SIZE_BYTES,
        "retired live v4 workflow",
    )
    v5_workflow_raw = require_exact_bytes(
        c5_entries,
        V5_WORKFLOW_RELATIVE,
        V5_WORKFLOW_SHA256,
        V5_WORKFLOW_SIZE_BYTES,
        "successor live v5 workflow",
    )
    validate_v5_workflow_prerequisites(v5_workflow_raw)
    authority_modes = {
        V4_CHECKER_RELATIVE: "100644",
        V4_CAPTURE_PRIMITIVE["path"]: "100644",
        CHECKER_RELATIVE: "100644",
        SELF_TEST_RELATIVE: "100644",
        CAPTURE_TOOL_RELATIVE: "100644",
        CAPTURE_SCHEMA_RELATIVE: "100644",
        RECEIPT_SCHEMA_RELATIVE: "100644",
        POLICY_RELATIVE: "100644",
        PREDECESSOR_CAPTURE_RELATIVE: "100644",
        CURRENT_SOURCE_RELATIVE: "100644",
        LEAN_R9_RELATIVE: "100644",
        LEAN_R10_RELATIVE: "100644",
        V4_WORKFLOW_RELATIVE: "100644",
        V5_WORKFLOW_RELATIVE: "100644",
        **{path: mode for path, mode, _role in PROCESS_ARTIFACTS},
    }
    for path, mode in authority_modes.items():
        require(
            path in c5_entries and c5_entries[path].mode == mode,
            f"C5 authority absent or wrong mode: {path}",
        )
    require(
        read_repository_file(CHECKER_RELATIVE, maximum=_v4.MAX_BLOB_BYTES, mode=0o644)
        == tree_blob(c5_entries, CHECKER_RELATIVE),
        "executing v5 checker bytes differ from the C5 authority blob",
    )
    _validate_no_r4_history(c5, head)
    if r5 is None:
        require(head == c5, "receipt-absent state is not exact C5")
        validate_worktree(c5_entries, head, head_tree)
        return c5, c5_commit.tree, None
    require(
        git_predicate("merge-base", "--is-ancestor", r5, head),
        "R5 is not an ancestor of HEAD",
    )
    r5_commit = parse_commit(r5)
    require(
        r5_commit.parent == c5 and r5_commit.message == R5_MESSAGE,
        "R5 topology changed",
    )
    r5_entries = parse_tree(r5_commit.tree)
    expected_r5_delta = tuple(
        (path, status, mode) for path, status, mode, _role in R5_POLICY_ROWS
    )
    validate_exact_delta(
        changed_entries(c5_entries, r5_entries), expected_r5_delta, "R5"
    )
    _v4.validate_current_source(r5_entries, "R5")
    retained = tuple(
        sorted(
            (
                set(authority_modes)
                | {
                    POLICY_RELATIVE,
                    PREDECESSOR_CAPTURE_RELATIVE,
                    SUCCESSOR_CAPTURE_RELATIVE,
                    RECEIPT_RELATIVE,
                }
            )
            - {CURRENT_SOURCE_RELATIVE}
        )
    )
    for oid in _ancestry_commits(r5, head):
        tree = r5_commit.tree if oid == r5 else parse_descendant_tree(oid)
        entries = parse_tree(tree)
        for path in retained:
            require(
                entries.get(path) == r5_entries.get(path),
                f"retained v5 authority changed: {path}",
            )
        _v4.validate_current_source(entries, f"descendant {oid[:12]}")
    validate_worktree(head_entries, head, head_tree)
    return c5, c5_commit.tree, r5


def validate_receipt_bytes(
    receipt_raw: bytes,
    predecessor_raw: bytes,
    successor_raw: bytes,
    c5_entries: dict[str, Any],
    c5: str,
    c5_tree: str,
    capture_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> dict[str, Any]:
    receipt = parse_json(receipt_raw, "composite-v5 receipt")
    validate_schema_instance(receipt, receipt_schema, "composite-v5 receipt")
    expected = derive_receipt(
        predecessor_raw, successor_raw, c5_entries, c5, c5_tree, capture_schema
    )
    require(
        receipt == expected, "composite-v5 receipt differs from raw-capture derivation"
    )
    return receipt


def static_result(head: str, head_tree: str, c5: str, r5: str | None) -> dict[str, Any]:
    return {
        "c4_commit": C4_COMMIT,
        "c5_commit": c5,
        "head": head,
        "r5_commit": r5,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v5-static-validation/v1",
        "tree": head_tree,
    }


def validate_static() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c5, c5_tree, r5 = validate_topology(head, head_tree)
    c5_entries = parse_tree(c5_tree)
    capture_schema, receipt_schema = validate_schema_authorities(c5_entries)
    predecessor_raw = tree_blob(c5_entries, PREDECESSOR_CAPTURE_RELATIVE)
    derive_phase(
        predecessor_raw,
        "predecessor_failure",
        c5_entries,
        c5,
        c5_tree,
        capture_schema,
    )
    if r5 is not None:
        r5_entries = parse_tree(parse_commit(r5).tree)
        validate_receipt_bytes(
            tree_blob(r5_entries, RECEIPT_RELATIVE),
            predecessor_raw,
            tree_blob(r5_entries, SUCCESSOR_CAPTURE_RELATIVE),
            c5_entries,
            c5,
            c5_tree,
            capture_schema,
            receipt_schema,
        )
    return static_result(head, head_tree, c5, r5)


def bounded_stdin() -> bytes:
    raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
    require(
        0 < len(raw) <= MAX_JSON_BYTES, "standard-input JSON size is outside the bound"
    )
    return raw


def derive_receipt_command() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c5, c5_tree, r5 = validate_topology(head, head_tree)
    require(
        r5 is None and head == c5, "receipt derivation requires exact receipt-absent C5"
    )
    c5_entries = parse_tree(c5_tree)
    capture_schema, receipt_schema = validate_schema_authorities(c5_entries)
    value = derive_receipt(
        tree_blob(c5_entries, PREDECESSOR_CAPTURE_RELATIVE),
        bounded_stdin(),
        c5_entries,
        c5,
        c5_tree,
        capture_schema,
    )
    validate_schema_instance(value, receipt_schema, "derived composite-v5 receipt")
    return value


def validate_receipt_command() -> dict[str, Any]:
    head, head_tree = validate_repository()
    c5, c5_tree, r5 = validate_topology(head, head_tree)
    require(r5 is not None, "receipt validation requires R5 or a retained descendant")
    c5_entries = parse_tree(c5_tree)
    r5_entries = parse_tree(parse_commit(r5).tree)
    capture_schema, receipt_schema = validate_schema_authorities(c5_entries)
    receipt_raw = bounded_stdin()
    require(
        receipt_raw == tree_blob(r5_entries, RECEIPT_RELATIVE),
        "receipt stdin differs from R5 blob",
    )
    validate_receipt_bytes(
        receipt_raw,
        tree_blob(c5_entries, PREDECESSOR_CAPTURE_RELATIVE),
        tree_blob(r5_entries, SUCCESSOR_CAPTURE_RELATIVE),
        c5_entries,
        c5,
        c5_tree,
        capture_schema,
        receipt_schema,
    )
    return {
        **static_result(head, head_tree, c5, r5),
        "schema": "pid-rs/ksg-rev4-m1a-composite-v5-receipt-validation/v1",
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-static", action="store_true")
    modes.add_argument("--derive-receipt", action="store_true")
    modes.add_argument("--validate-receipt", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.validate_static:
            result = validate_static()
        elif arguments.derive_receipt:
            result = derive_receipt_command()
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
