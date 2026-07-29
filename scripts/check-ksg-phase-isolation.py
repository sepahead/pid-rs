#!/usr/bin/env python3
"""Fail closed on KSG revision-4 Git-phase contamination.

This checker authenticates a bounded Git ancestry envelope and compares the
Git-visible candidate filesystem with the declared scientific baseline.  It is
deliberately a provenance/firewall check, not a numerical or scientific proof.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
from typing import Any, Iterable, cast


SCRIPT_PATH = Path(__file__)
ROOT = SCRIPT_PATH.resolve().parent.parent

SCIENTIFIC_BASELINE = "e96122b56c15e895c081379210103d1a26eac25f"
SCIENTIFIC_BASELINE_TREE = "fee2346732da20af0cde32844fcab527ec2d6c4a"
DELIVERY_PARENT = "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"
DELIVERY_PARENT_TREE = "13b15a7564fdd52df16e2e4380f6293db4ea4367"
FORMAL_ANCHOR = "118e1de6a2d6d2ae33fe7bdc224736257e42a83f"
FORMAL_ANCHOR_TREE = "d02ffc69a7045984c1cf58f3adbd39b7e3af0e89"
RECOVERY_ANCHOR = "ca24ab8ebade81a94ffc001531abaf5a5579d5e9"
RECOVERY_ANCHOR_TREE = "82b0aec08c5fd71b6f67d653f05a32f097745a03"
INTEGRATION_ANCHOR = "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"
INTEGRATION_ANCHOR_TREE = "88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e6f"
M1A_SCIENTIFIC_COMMIT = "dc7b8de0a87443ef2bcde71b19938642f1af2197"
M1A_SCIENTIFIC_TREE = "88b24c0ba4fcad4bd749b9146486143397b6a6eb"
CORRECTIVE_PARENT = "af50935be9ecf9a81aeb30c56b45059652468746"
CORRECTIVE_PARENT_TREE = "ada3860eb696c9a5d634728365acdb5958e7c4e6"
CURRENT_ANCHOR = "af50935be9ecf9a81aeb30c56b45059652468746"
CURRENT_ANCHOR_TREE = "ada3860eb696c9a5d634728365acdb5958e7c4e6"
PHASE_PATH_POLICY = (
    "audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json"
)
PHASE_PATH_POLICY_SHA256 = (
    "61a54281b492604bdf12bf7ef9b53ab44a773a4fd9dbe9081beb48643a8e07ad"
)
PACKAGE_STATS_SHA256 = (
    "204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e"
)
PACKAGE_ARCHIVE_SCRIPT_SHA256 = (
    "13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256"
)
PACKAGE_GENERATOR_SHA256 = (
    "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
)
HISTORICAL_ECOSYSTEM_METHOD_CATALOG_SHA256 = (
    "1d1f1765209062b8fdc31faed1870de960c53f50ac8d3925a8ac27198aeab313"
)
CURRENT_METHOD_CATALOG_SHA256 = (
    "637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"
)
MAX_POST_ANCHOR_COMMITS = 1

CORRECTIVE_EVIDENCE = (
    "audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md"
)
PUBLIC_CI_FAILURE_RECEIPT = (
    "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json"
)
PUBLIC_CI_FAILURE_RECEIPT_SHA256 = (
    "9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87"
)
EXPECTED_CORRECTIVE_POLICY_ENTRIES = (
    (".github/workflows/ci.yml", "M", "verification_wiring"),
    ("CHANGELOG.md", "M", "documentation_release"),
    (
        "audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json",
        "A",
        "phase_authority",
    ),
    (
        PUBLIC_CI_FAILURE_RECEIPT,
        "A",
        "corrective_evidence",
    ),
    (CORRECTIVE_EVIDENCE, "A", "corrective_evidence"),
    (
        "scripts/check-certified-sxpid2-claim.py",
        "M",
        "claim_adjudication",
    ),
    (
        "scripts/check-foundational-sxpid-audit-pdf.sh",
        "M",
        "verification_wiring",
    ),
    (
        "scripts/check-ksg-phase-isolation-self-test.py",
        "M",
        "verification_tool",
    ),
    ("scripts/check-ksg-phase-isolation.py", "M", "verification_tool"),
)
EXPECTED_CORRECTIVE_REVIEW_CLASS_CONTRACTS = {
    "claim_adjudication": (
        "Keep the certified-SxPID2 claim gate bound to the corrected execution container without changing its mathematics or adjudication.",
        (
            "Rebind only the certified-job and complete-workflow SHA-256 constants to the reviewed tooling correction; preserve revision-3 evidence, semantics, mutation inventory, and claim boundaries byte-for-byte.",
        ),
    ),
    "corrective_evidence": (
        "Preserve machine and human evidence for the failed af509 public run and the bounded correction it forced.",
        (
            "Bind the terminal run, exact commit and tree, job counts, failed job and step identities, exact errors, decoded-log digests, skipped-step noncredit, correction, and required whole-run rerun.",
            "Classify both missing executables as provisioning failures rather than mathematical counterexamples, while retaining integration NO-GO until a fresh complete public run succeeds.",
        ),
    ),
    "documentation_release": (
        "Keep the operator-visible change history aligned with the exact execution-container correction.",
        (
            "Record the two explicitly provisioned executable prerequisites under Unreleased without claiming a release, green hosted run, scientific advance, or publication acceptance.",
        ),
    ),
    "phase_authority": (
        "Isolate the second corrective wave from the already-pushed dc7-to-af509 scientific and custody milestone.",
        (
            "Require the complete nine-path candidate to enter as one direct child of exact commit af50935be9ecf9a81aeb30c56b45059652468746 and tree ada3860eb696c9a5d634728365acdb5958e7c4e6 while retaining dc7 and the prior phase authority as immutable history.",
            "Reject deletions, non-policy paths, repeated post-anchor transitions, mechanically altered review classes, and any candidate that changes scientific, package, catalog, release, identity, PID2, PID3, or frontier bytes.",
        ),
    ),
    "verification_tool": (
        "Make the observed hosted failures permanent fail-closed regression and custody tests.",
        (
            "Bind the prior dc7-to-af509 workflow transform, the exact two-fault af509 tooling correction, the foundational-paper lake preflight, the certified-claim digest-only rebind, the canonical failure receipt, and the complete nine-path delta.",
            "Run normal and optimized hostile suites covering tool omission, duplication, placement, version, checksum, cache, order, receipt, policy, Git history, staged-tree, and checker self-reference failures.",
        ),
    ),
    "verification_wiring": (
        "Repair exactly the two missing executable prerequisites observed on the af509 public run.",
        (
            "Add chktex to the fresh Ubuntu formal-PDF toolchain without weakening or moving the paper gate.",
            "Provision both the formal-PDF job and the existing certified-SxPID2 Lean checker with the same checksum-pinned Elan 4.2.3, pinned cache action, Lean-toolchain and Mathlib-manifest cache bindings, cache fetch, and build route already exercised by the formal proof job.",
            "Require the directly invocable foundational-paper checker to preflight lake before executing its descriptor-factorization Lean route.",
        ),
    ),
}

# The complete single-parent chain between the delivery commit and the
# corrective anchor. Tree pins preserve the earlier integration exactly and
# prevent a same-message or same-path substitute from entering the envelope.
DECLARED_COMMIT_CHAIN = (
    (
        "8bcf33fb0e755727386aff69c8e703b96de87809",
        DELIVERY_PARENT,
        "a5778ae827f126676745e1a56984fd1dfa439fd9",
    ),
    (
        "afc45ff27e5af7fe04e44f2bb9f4147fb472c81e",
        "8bcf33fb0e755727386aff69c8e703b96de87809",
        "8278a4321da607554ff840a97fabbb57578b7f37",
    ),
    (
        FORMAL_ANCHOR,
        "afc45ff27e5af7fe04e44f2bb9f4147fb472c81e",
        FORMAL_ANCHOR_TREE,
    ),
    (
        RECOVERY_ANCHOR,
        FORMAL_ANCHOR,
        RECOVERY_ANCHOR_TREE,
    ),
    (
        INTEGRATION_ANCHOR,
        RECOVERY_ANCHOR,
        INTEGRATION_ANCHOR_TREE,
    ),
    (
        M1A_SCIENTIFIC_COMMIT,
        INTEGRATION_ANCHOR,
        M1A_SCIENTIFIC_TREE,
    ),
    (
        CURRENT_ANCHOR,
        M1A_SCIENTIFIC_COMMIT,
        CURRENT_ANCHOR_TREE,
    ),
)

DELIVERY_CHANGED_BLOBS = {
    "audit/evidence/codex-goal-prompt-2026-07-26.md": (
        "100644",
        "dc984b2586970c71a6eafe262604dd9e8d6b988723a8aa6b46df8ae7d58adab2",
    ),
    "audit/evidence/completion-active-resume.md": (
        "100644",
        "3ce82abc139316ec511c7e920fb7dddebf5a38e5402be1b7e022fbcc2a773846",
    ),
    "audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md": (
        "100644",
        "61ba9897f7323a88bccc9f683d752cbb0a1408e1ec71268615c5619d9aeacf29",
    ),
    "audit/evidence/completion-run-ledger-2026-07-25.md": (
        "100644",
        "86881ba4deaa1be0ada75925dc6f739f6f0385612590989f9519d020453addce",
    ),
}

# These paths remain full scientific-baseline controls even if a checker edit
# tries to relabel one as allowed.  The global protected projection covers all
# other non-allowlisted paths.
PINNED_PROTECTED_BLOBS = {
    ".gitignore": (
        "100644",
        "918f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
    ),
    "crates/pid-core/src/bin/exp0.rs": (
        "100644",
        "b9b19ec42ce129246c1bdcc044501843eba5e405f19c090180b9ad5f32a34409",
    ),
    "crates/pid-core/src/discrete_pid.rs": (
        "100644",
        "fa62dfec9e142cb4b1cc1266ab9837d07ba8869bfd739ec25cebea40f37d90e4",
    ),
    "crates/pid-core/src/pid2.rs": (
        "100644",
        "a1b34699b57105cb9da6aeb176efe6d0bfbb3342af4f28584f31675a26798d20",
    ),
    "crates/pid-core/tests/imin.rs": (
        "100644",
        "9ddd08c8ce736b5c7f539c4ace1d271336fe7bfe879dabe3155fef737b2cc2a0",
    ),
    "crates/pid-core/tests/pid2.rs": (
        "100644",
        "72a3949ff68227fe9cf20085fdc75bab9a4307574bcf1e782cba9c61c104c101",
    ),
    "crates/pid-python/src/lib.rs": (
        "100644",
        "b434c47bc3179cedd2c4d90321f3b07bf737ca0160736febc0569460849ab229",
    ),
    "crates/pid-python/tests/test_experimental_migration.py": (
        "100644",
        "758d5c01e3f93cba5afdc505ec4229abbd911418d4ce28559e048efd9379d239",
    ),
    "crates/pid-python/tests/test_v1.py": (
        "100644",
        "eb6b2d48a7d92143a71ae34e136b0d03cdfad266955ff8a02e7aa7bec4298939",
    ),
}

# Review-selected files whose complete candidate bytes are additionally
# visible as individual SHA-256 pins.  The generated block below supplies the
# expected mode/hash values; changing this reviewed path inventory is a manual
# review action, not part of mechanical fact rebasing.
BOUND_ALLOWED_PATHS = (
    ".github/workflows/ci.yml",
    ".gitleaks.toml",
    "AGENTS.md",
    "CHANGELOG.md",
    "ECOSYSTEM_CAPABILITIES.md",
    "FORMAL_TOOL_ADOPTION_AUDIT.md",
    "METHODS.md",
    "audit/evidence/assurance-registry.json",
    "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
    "audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md",
    "audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json",
    "audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md",
    "audit/evidence/ksg-rev4-phase-path-policy.json",
    "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json",
    "audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md",
    "audit/evidence/sxpid2-exact-product-mutation-suite.json",
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
    "audit/evidence/task-dispositions.json",
    "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
    "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
    "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
    "audit/formal/latex/formal-tool-adoption-audit.tex",
    "audit/tools/certified-sxpid/README.md",
    "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
    "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "audit/tools/certified-sxpid/scripts/verify_certificate.py",
    "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
    "crates/pid-core/identity/software-identity-reference-v1.json",
    "crates/pid-core/src/isx.rs",
    "crates/pid-core/src/ksg.rs",
    "crates/pid-core/src/pid3.rs",
    "crates/pid-core/src/stats.rs",
    "crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256",
    "crates/pid-core/tests/isx.rs",
    "crates/pid-core/tests/ksg.rs",
    "crates/pid-core/tests/ksg_report.rs",
    "crates/pid-core/tests/parallel_bit_identity.rs",
    "ecosystem-capabilities.json",
    "justfile",
    "method-catalog.json",
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "release-scope-1.0.json",
    "scripts/README.md",
    "scripts/check-certified-sxpid2-claim-self-test.py",
    "scripts/check-certified-sxpid2-claim.py",
    "scripts/check-ecosystem-capabilities-self-test.py",
    "scripts/check-ecosystem-capabilities.py",
    "scripts/check-foundational-sxpid-audit-pdf.sh",
    "scripts/check-ksg-harmonic-exact-enclosure-self-test.py",
    "scripts/check-ksg-harmonic-exact-enclosure.py",
    "scripts/check-ksg-harmonic-modular-certificate-self-test.py",
    "scripts/check-ksg-harmonic-modular-certificate.py",
    "scripts/check-ksg-harmonic-revision-self-test.py",
    "scripts/check-ksg-harmonic-revision.py",
    "scripts/check-review-evidence-self-test.py",
    "scripts/check-review-evidence.py",
    "scripts/generate-ksg-harmonic-modular-certificate.py",
    "scripts/generate-ksg-local-arithmetic-oracle.py",
    "scripts/verify-package-archives.sh",
)

# These two files necessarily cannot be included in a digest stored inside the
# checker itself.  Their paths and modes remain part of the exact delta.  Their
# bytes acquire custody only when an independently pre-pinned Git tree/commit
# anchors them.  A tree derived after a coordinated checker/policy mutation is
# post-hoc consistency, not an external trust anchor.
SELF_UNHASHED_PATHS = frozenset(
    {
        "scripts/check-ksg-phase-isolation-self-test.py",
        "scripts/check-ksg-phase-isolation.py",
    }
)

# BEGIN GENERATED PHASE FACTS
EXPECTED_CHANGED_PATHS: tuple[str, ...] = (
    '.github/workflows/ci.yml',
    '.gitleaks.toml',
    'AGENTS.md',
    'CHANGELOG.md',
    'ECOSYSTEM_CAPABILITIES.md',
    'FORMAL_TOOL_ADOPTION_AUDIT.md',
    'KNOWN_LIMITATIONS.md',
    'METHODS.md',
    'MIGRATION.md',
    'README.md',
    'RELEASE_SCOPE_1_0.md',
    'audit/evidence/assurance-registry.json',
    'audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json',
    'audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md',
    'audit/evidence/codex-goal-prompt-2026-07-26.md',
    'audit/evidence/completion-active-resume.md',
    'audit/evidence/completion-execution-plan-2026-07-26.md',
    'audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md',
    'audit/evidence/completion-run-ledger-2026-07-25.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-prompt.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-receipt.json',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-1.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-2.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-4.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-responses.md',
    'audit/evidence/fable5-formal-methods-recovery-runner-20260727T062149Z.mjs',
    'audit/evidence/fable5-ksg-rev4-adjudication-20260727.json',
    'audit/evidence/fable5-ksg-rev4-adjudication-20260727.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-context.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-receipt.json',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-response.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-prompt-20260726T160252Z.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-recovery-manifest-20260727.json',
    'audit/evidence/fable5-ksg-rev4-preclosure-runner-20260726T160252Z.mjs',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-adjudication.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-adjudication.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-completion-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-context.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-oversize-negative-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-prompt.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r1-a1.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r1-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r2-a1.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r2-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r3-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-responses.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-runner.mjs',
    'audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json',
    'audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md',
    'audit/evidence/ksg-rev4-integration-reconstruction-map-2026-07-26.md',
    'audit/evidence/ksg-rev4-phase-path-policy.json',
    'audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json',
    'audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md',
    'audit/evidence/ksg-rev4-recovery-ledger-20260727.json',
    'audit/evidence/ksg-rev4-recovery-ledger-20260727.md',
    'audit/evidence/recover-fable5-ksg-rev4-preclosure-20260727.py',
    'audit/evidence/sxpid2-exact-product-mutation-suite.json',
    'audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json',
    'audit/evidence/task-dispositions.json',
    'audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md',
    'audit/formal/latex/certified-sxpid2-executable-assurance.tex',
    'audit/formal/latex/exact-log-product-sxpid2-assurance.tex',
    'audit/formal/latex/formal-tool-adoption-audit.tex',
    'audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean',
    'audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean',
    'audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean',
    'audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2',
    'audit/tools/certified-sxpid/README.md',
    'audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py',
    'audit/tools/certified-sxpid/scripts/check-independent-verifier.py',
    'audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py',
    'audit/tools/certified-sxpid/scripts/verify_certificate.py',
    'claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/call-site-map.md',
    'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json',
    'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json.sha256',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v1.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/decision-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/decision.md',
    'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json',
    'claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations.md',
    'claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/revision-index.md',
    'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md',
    'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md',
    'crates/pid-core/README.md',
    'crates/pid-core/identity/software-identity-reference-v1.json',
    'crates/pid-core/src/isx.rs',
    'crates/pid-core/src/ksg.rs',
    'crates/pid-core/src/pid3.rs',
    'crates/pid-core/src/stats.rs',
    'crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot',
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json',
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256',
    'crates/pid-core/tests/isx.rs',
    'crates/pid-core/tests/ksg.rs',
    'crates/pid-core/tests/ksg_report.rs',
    'crates/pid-core/tests/parallel_bit_identity.rs',
    'ecosystem-capabilities.json',
    'justfile',
    'method-catalog.json',
    'output/pdf/certified-sxpid2-executable-assurance.pdf',
    'output/pdf/exact-log-product-sxpid2-assurance.pdf',
    'output/pdf/formal-tool-adoption-audit.pdf',
    'release-scope-1.0.json',
    'scripts/README.md',
    'scripts/check-certified-sxpid2-claim-self-test.py',
    'scripts/check-certified-sxpid2-claim.py',
    'scripts/check-ecosystem-capabilities-self-test.py',
    'scripts/check-ecosystem-capabilities.py',
    'scripts/check-foundational-sxpid-audit-pdf.sh',
    'scripts/check-ksg-harmonic-exact-enclosure-self-test.py',
    'scripts/check-ksg-harmonic-exact-enclosure.py',
    'scripts/check-ksg-harmonic-modular-certificate-self-test.py',
    'scripts/check-ksg-harmonic-modular-certificate.py',
    'scripts/check-ksg-harmonic-revision-self-test.py',
    'scripts/check-ksg-harmonic-revision.py',
    'scripts/check-ksg-phase-isolation-self-test.py',
    'scripts/check-ksg-phase-isolation.py',
    'scripts/check-lean-ksg-integer-harmonic-self-test.py',
    'scripts/check-lean-ksg-integer-harmonic.py',
    'scripts/check-review-evidence-self-test.py',
    'scripts/check-review-evidence.py',
    'scripts/check-z3-ksg-integer-harmonic-self-test.py',
    'scripts/check-z3-ksg-integer-harmonic.py',
    'scripts/generate-ksg-harmonic-modular-certificate.py',
    'scripts/generate-ksg-local-arithmetic-oracle.py',
    'scripts/verify-package-archives.sh',
)
EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS: tuple[str, ...] = (
    '.github/workflows/ci.yml',
    'CHANGELOG.md',
    'scripts/check-certified-sxpid2-claim.py',
    'scripts/check-foundational-sxpid-audit-pdf.sh',
    'scripts/check-ksg-phase-isolation-self-test.py',
    'scripts/check-ksg-phase-isolation.py',
)
EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES: tuple[str, ...] = (
    'audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json',
    'audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json',
    'audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md',
)
EXPECTED_ALLOWLIST_SHA256 = '1682d196fed775cc491a45e1904808d6de108dcb1f18d10401332abab8e147e2'
EXPECTED_CHANGED_PROJECTION_SHA256 = '05868feb7a3742175befb79cef8e2824d2c9134dc524edf9e67c4398aac041bd'
EXPECTED_PROTECTED_PROJECTION_SHA256 = 'c3686fa6a7f13a355b9038a97c6009aea1824055d9b037312c66075ee7e7be09'
EXPECTED_BASELINE_PATH_COUNT = 437
EXPECTED_PROTECTED_PATH_COUNT = 381
EXPECTED_BOUND_ALLOWED_BLOBS: dict[str, tuple[str, str]] = {
    '.github/workflows/ci.yml': ('100644', '5bca9f1af50b2441e6c3363c372f47097441d783702ce858e0b8f03b964eb357'),
    '.gitleaks.toml': ('100644', '6dfc7f6c79218afc873db40963cee0b73340558648d4c191db82d31d277b891b'),
    'AGENTS.md': ('100644', '3ff7faea1bd4adb197899d7b584bba6640613e3c3e5b09e87bd2e574a729fcad'),
    'CHANGELOG.md': ('100644', 'ab812e901a6734c2c35ae5b0288d535f3c9227d2d3a6a32f1af4ed5cf7dc7a2c'),
    'ECOSYSTEM_CAPABILITIES.md': ('100644', '1c6a822b25642ab870e44444d7e48cddb26056be82225eb308d06ca66d0cd702'),
    'FORMAL_TOOL_ADOPTION_AUDIT.md': ('100644', '2151a865d5fe503bb50a42a578c747be64104228c519efeb6ad7000d3b827b25'),
    'METHODS.md': ('100644', '3512e829502dbacb67977a1c808fc59af0461568989e00b363800444fea4ab19'),
    'audit/evidence/assurance-registry.json': ('100644', '5ceb2e47469dda5b8750ba8627014a7b634596ea4ae74c0b52873e19fe8d8a9a'),
    'audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json': ('100644', 'f9f0156abd4370857099f215a313b95621510d591e5726d52c856670324eb8d3'),
    'audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md': ('100644', 'aee278366f2bf990a5333dbaace7f190cb3191dfd2c2d972d8cf8ce33abe5004'),
    'audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json': ('100644', '61a54281b492604bdf12bf7ef9b53ab44a773a4fd9dbe9081beb48643a8e07ad'),
    'audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md': ('100644', '2f673ced6cff152060e8830cc0320fc08d02b3c00feabef0200e0a4e9fe780c0'),
    'audit/evidence/ksg-rev4-phase-path-policy.json': ('100644', '297b4cb3fc60422796d64b2b5a23763d5c9d46f09ad3abe049e5a01c1330d5b2'),
    'audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json': ('100644', '9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87'),
    'audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md': ('100644', '87b7c5cc8927e0d5a0675057acf68b9bcea7348d55950578a134bacca898662a'),
    'audit/evidence/sxpid2-exact-product-mutation-suite.json': ('100644', '031a449c4239d74d0584c5f244ca18c852555d442ae7a880c2d750a02d5bcb0a'),
    'audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json': ('100644', 'c36da6d5c55d553a6a647818cf15e6143a7914409370b096e6f6492f5731131d'),
    'audit/evidence/task-dispositions.json': ('100644', 'a99d28238ef8b1e210c8a4835e5d9fbfc272a6b774f32439eb78f72092a6c4c1'),
    'audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md': ('100644', '987c9fd759db8532f3f405c5604c13fd111b55ae5e4cb110a934a692e6aea98c'),
    'audit/formal/latex/certified-sxpid2-executable-assurance.tex': ('100644', '297c9fdfae897b2136a3eb870a81c0ab0b3553d1056c1c87492dd0e6fbafdf61'),
    'audit/formal/latex/exact-log-product-sxpid2-assurance.tex': ('100644', 'da4c75446de4e16e8414b8ec137d122c43a4e50eb0c7d7d976c4f3f621f9bccd'),
    'audit/formal/latex/formal-tool-adoption-audit.tex': ('100644', 'bf01b6c2f56b07cd1e379bb7d778923abb39e96b422130d4ab4814071ed6809c'),
    'audit/tools/certified-sxpid/README.md': ('100644', '61171ae73138570ecede4b1607b04f576807b6e92af1538539b38a0fca21f063'),
    'audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py': ('100644', '274de5313301b7f9ea671f817698f321852aa8a3c542d73c1e31d22f876a7fb8'),
    'audit/tools/certified-sxpid/scripts/check-independent-verifier.py': ('100644', '4327afdcce04421544481e0af9abf15dd3709ea75c5df994cb33b3ce3de91c17'),
    'audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py': ('100644', '04dc49e0ad42cd7b931aa51a3602f58dc789483c23d4aff4de5de8d25716efbf'),
    'audit/tools/certified-sxpid/scripts/verify_certificate.py': ('100644', 'c90572571eac9b5cd5cd11d526a211dd0dfa7ab45274f6c038c0f8338cd2958e'),
    'claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json': ('100644', '898414abc5bed5af483a966399bf68cbad8892a3c67da241555947d565c55585'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md': ('100644', '5eed715b409ce52271aa33dfba9466d566b78ef878438fdf7948f9a0135a9f7d'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md': ('100644', '31313a2069af8a02409aa466176c2c2105915344842be965983182ae236c1dc9'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md': ('100644', '8907de510080c53ef19de8e80f131f409588d88441205b11e34e6de59f7aa52f'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md': ('100644', '35aa45ed5cea6b0671a7012f048269e2970a5d39c50724fe1090c6fce0466fd7'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md': ('100644', 'dcbdf594796dd9559a8882ff47599b1045f9671801e7f5ef26cd3edcbe355bf2'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md': ('100644', '9a9ec2894bf69513f04260bdeb991d454c65be693179868691513f69b7d7a346'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md': ('100644', 'ab2974c309e40e36eba1c7e9fbe1d71e7a36aaf25eb91ec4d63d65e819c04f69'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md': ('100644', '7feba281c710a34e98cb75665b8a1e1adb63bbd31b972812945895faedb33046'),
    'crates/pid-core/identity/software-identity-reference-v1.json': ('100644', '517ddcce5f101675cd2cb3b718e3b132dedf928460624aae9b94d22fafe97032'),
    'crates/pid-core/src/isx.rs': ('100644', '7a3577a0148cafaf93c2d6a982bd3b04b3499b917a1f59b63bdbca30b68a809d'),
    'crates/pid-core/src/ksg.rs': ('100644', '0f5109dda054a0222ed796209b10d22196348eddac76d8d53dd78b4e03a95250'),
    'crates/pid-core/src/pid3.rs': ('100644', 'f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd'),
    'crates/pid-core/src/stats.rs': ('100644', '204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e'),
    'crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot': ('100644', 'a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b'),
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json': ('100644', '560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c'),
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256': ('100644', 'fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7'),
    'crates/pid-core/tests/isx.rs': ('100644', 'ce041e8e27900ac3d76b97526e43f56057d071cb987d8a53de3a7b51dd16b3ee'),
    'crates/pid-core/tests/ksg.rs': ('100644', '544192cac6c00957e1e05a4cc320c069453060eb1fe676131f83b155c1ee6daa'),
    'crates/pid-core/tests/ksg_report.rs': ('100644', '724c1fad3ce11ce14b789efda0edccfe96a6f3334d077cad075dd667683b0f44'),
    'crates/pid-core/tests/parallel_bit_identity.rs': ('100644', '611a31e1b76536b1b1b712cdbd7713dc5caad24f354b0c507e2779bbf8f3cb28'),
    'ecosystem-capabilities.json': ('100644', 'd6070882c9a9b380dac568c38685a79f45bc7bfe08d0622e5525d72fd16e67e5'),
    'justfile': ('100644', '8dc0c452b1b95a080e93091fd4c18d32864daed903c415bf422f366c4edb91b2'),
    'method-catalog.json': ('100644', '637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f'),
    'output/pdf/certified-sxpid2-executable-assurance.pdf': ('100644', '2370637b750578fc1818279f6001f4143dd8e1e3d48136077a6953ceb2ee795c'),
    'output/pdf/formal-tool-adoption-audit.pdf': ('100644', 'e7d4fa04700b9cbe8d9a4701525341f1743a4a28e624c31a2e8726b69fc9147c'),
    'release-scope-1.0.json': ('100644', '4fe9e5e4ba7b31a609b73127ee7c34ffcd33765e87363c1b50f3d26145c4319d'),
    'scripts/README.md': ('100644', '4ea701794c455021aff8c991aac8a127fde1bcabed390e2dc0b5037f475b3a83'),
    'scripts/check-certified-sxpid2-claim-self-test.py': ('100644', 'cac22cb1af20e8b020d67ec1124515179db4cc93ddc4885d43d83a49dd46a24f'),
    'scripts/check-certified-sxpid2-claim.py': ('100644', 'e9d3249a3d17a23656152d2d7524a5cc30e87c6ef98cb5693de92f5e1928143c'),
    'scripts/check-ecosystem-capabilities-self-test.py': ('100644', 'ea85fa013af2136a16850583459be4c2fd9fb0b736e1852f619a125cacd2b0a3'),
    'scripts/check-ecosystem-capabilities.py': ('100644', '42ac86f8899928c79646eb03aafc747ebef59185d7f09579a07b7efd4ecf5120'),
    'scripts/check-foundational-sxpid-audit-pdf.sh': ('100755', '43dd9229592d44a89734a071b40f7eb89233442b4bca40ae750d6703927bd099'),
    'scripts/check-ksg-harmonic-exact-enclosure-self-test.py': ('100755', 'afc2ca44795f86b3dd9c74d2c07234ae9e0372737cdae7d718ec2db2e5204782'),
    'scripts/check-ksg-harmonic-exact-enclosure.py': ('100755', 'b7c4df526703adc3dd8f5f04471b027decb256bfaaaa2d32ff9f918253546468'),
    'scripts/check-ksg-harmonic-modular-certificate-self-test.py': ('100755', '1eebc0d575b730753d98659baee5e1f76f17c783e112a9610b731d5f07618c65'),
    'scripts/check-ksg-harmonic-modular-certificate.py': ('100755', '201b046957cee263ad4864acd84ab18095db4bbfc5a23bf90c2bb836b986afec'),
    'scripts/check-ksg-harmonic-revision-self-test.py': ('100644', '6212bca982da4e5d4c1affa945c7ac8fed254fbc4f5d775798427549c0b837cc'),
    'scripts/check-ksg-harmonic-revision.py': ('100644', '083aee3ba1cb59b8a5cfc921ac6558fd7e347ef6a0deddb6b81ef07f78e2d950'),
    'scripts/check-review-evidence-self-test.py': ('100755', '9830fbd2ee837f0f592bfc1d5461bdeefb3f7a0d95f9536b987b3a5226af5538'),
    'scripts/check-review-evidence.py': ('100755', '6f5c34a8bcfcb3b1b3cb666f955c6ef35b024cc4073214fbe677aa1b61140ade'),
    'scripts/generate-ksg-harmonic-modular-certificate.py': ('100755', '969c4a5a5a8f6a9054de0154a331824bf2034223c30cb3a76f5e975f6f68a1c3'),
    'scripts/generate-ksg-local-arithmetic-oracle.py': ('100755', 'a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b'),
    'scripts/verify-package-archives.sh': ('100755', '13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256'),
}
# END GENERATED PHASE FACTS




EXPECTED_PARALLEL_U64_CONSTANTS = {
    "ISX_REDUNDANCY_BITS": 4608069949341512143,
    "KSG_LOCAL_TERMS_CHECKSUM": 13714940533915299,
    "KSG_LOCAL_TERM_0": 4611372573292626839,
    "KSG_LOCAL_TERM_LAST": 4609053335123176929,
    "KSG_LOCAL_TERM_MID": 4608683422432580648,
    "PID2_RED_BITS": 4608069949341512143,
    "PID2_SYN_BITS": 4591732782175321776,
    "PID2_UNQ1_BITS": 4590324628665003600,
    "PID2_UNQ2_BITS": 13821388618758275492,
    "PID3_ATOM_001_BITS": 13803885910316517056,
    "PID3_ATOM_111_BITS": 4587721666143603408,
    "PID3_ATOM_CHECKSUM": 9260367673031411424,
    "PID3_RED_CHECKSUM": 12358916445650220,
}
FORBIDDEN_PID2_SYN_BITS = 4591732782175321784

EXPECTED_PARALLEL_TESTS = (
    "block_bootstrap_matches_serial_reference",
    "bootstrap_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "discrete_pid2_is_bit_identical_across_repeated_calls",
    "isx_redundancy_matches_serial_reference",
    "ksg_local_mi_terms_match_serial_reference",
    "ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "pid2_atoms_match_serial_reference",
    "pid2_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "pid3_atoms_match_serial_reference",
    "pid3_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "red_degree_discrete_is_bit_identical_across_repeated_calls",
    "vul_degree_discrete_is_bit_identical_across_repeated_calls",
)

EXPECTED_RELEASE_REVISIONS = {
    "pid-core.experimental.continuous.pid2": (
        "separate-biased-term-pid2-integer-harmonic-v2"
    ),
    "pid-core.experimental.hierarchy": (
        "hierarchy-screening-with-integer-harmonic-ksg-v2"
    ),
    "pid-core.experimental.pipelines.pid2-screening": (
        "deterministic-pair-enumeration-with-integer-harmonic-pid2-v2"
    ),
    "pid-core.experimental.pipelines.same-sample-quantization": (
        "equal-width-same-sample-v1"
    ),
    "pid-core.research.isx-heuristics": (
        "heuristic-baselines-with-integer-harmonic-ksg-v2"
    ),
    "pid-core.stable.imin": (
        "empirical-specific-information-minimum-with-quantized-provenance-v1"
    ),
}

FORBIDDEN_COMBINED_RELEASE_REVISIONS = frozenset(
    {
        (
            "deterministic-pair-enumeration-with-integer-harmonic-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "empirical-specific-information-minimum-with-quantized-provenance-"
            "and-represented-input-exact-synergy-sum-v2"
        ),
        "equal-width-same-sample-with-represented-input-exact-imin-synergy-sum-v2",
        (
            "heuristic-baselines-with-integer-harmonic-ksg-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "hierarchy-screening-with-integer-harmonic-ksg-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "separate-biased-term-pid2-with-integer-harmonic-inputs-and-"
            "represented-input-exact-synergy-sum-v2"
        ),
    }
)

FORBIDDEN_CHANGED_PATH_PREFIXES = (
    "claims/IMIN-TIE-SWAP-001/",
    "claims/PID2-REPRESENTED-SUM-001/",
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/",
    "claims/SX-COUNT-EVENT-BRIDGE-001/",
    "crates/pid-python/",
)
FORBIDDEN_CHANGED_PATH_FRAGMENTS = (
    "exact_binary64_sum",
    "finite-convergence",
    "finite_convergence",
    "frontier",
    "imin-tie",
    "pid2-represented-sum",
    "sx-certified-averaged-pid3",
    "sx-count-event-bridge",
)
FORBIDDEN_EXACT_CHANGED_PATHS = frozenset(
    {
        "crates/pid-core/src/bin/exp0.rs",
        "crates/pid-core/src/discrete_pid.rs",
        "crates/pid-core/src/pid2.rs",
        "crates/pid-core/tests/imin.rs",
        "crates/pid-core/tests/imin_numerical_boundary.rs",
        "crates/pid-core/tests/pid2.rs",
        "scripts/check-imin-tie-boundary-self-test.py",
        "scripts/check-imin-tie-boundary.py",
        "scripts/check-pid2-represented-sum-self-test.py",
        "scripts/check-pid2-represented-sum.py",
        "scripts/generate-exact-binary64-sum-oracle.py",
    }
)
CORRECTIVE_PUBLICATION_PATHS = frozenset(
    {
        "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
        "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
        "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
        "audit/formal/latex/formal-tool-adoption-audit.tex",
        "output/pdf/certified-sxpid2-executable-assurance.pdf",
        "output/pdf/exact-log-product-sxpid2-assurance.pdf",
        "output/pdf/formal-tool-adoption-audit.pdf",
    }
)

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_RESOLVED_GIT_EXECUTABLE: Path | None = None

FORBIDDEN_LOCAL_CONFIG_KEYS = frozenset(
    {
        "attr.tree",
        "core.attributesfile",
        "core.excludesfile",
        "core.fsmonitor",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "extensions.worktreeconfig",
        "index.sparse",
    }
)
FORBIDDEN_LOCAL_CONFIG_PREFIXES = (
    "filter.",
    "include.",
    "includeif.",
)

EXPECTED_CRITICAL_GATE_SEQUENCE = (
    "validate_checker_source_model",
    "validate_repository_context",
    "collect_candidate_snapshot",
    "validate_commit_envelope",
    "validate_phase_path_policy",
    "validate_staged_tree_custody",
    "validate_effective_attributes",
    "validate_changed_path_firewall",
    "validate_public_ci_failure_evidence",
    "validate_ci_corrective_firewall",
    "validate_claim_checker_workflow_rebind",
    "validate_foundational_pdf_lake_preflight",
    "validate_package_archive_corrective_firewall",
    "validate_ecosystem_corrective_firewall",
    "validate_stats_firewall",
    "validate_parallel_semantics",
    "validate_release_firewall",
    "validate_identity_firewall",
    "validate_repository_context",
    "collect_candidate_snapshot",
    "validate_staged_tree_custody",
)


class PhaseIsolationError(RuntimeError):
    """A bounded ancestry, tree, custody, or phase-firewall check failed."""


@dataclass(frozen=True)
class GitEntry:
    mode: str
    kind: str
    oid: str
    sha256: str


@dataclass(frozen=True)
class CandidateSnapshot:
    entries: dict[str, GitEntry]
    head: str
    head_entries: dict[str, GitEntry]
    tracked_modifications: tuple[str, ...]
    untracked: tuple[str, ...]


@dataclass(frozen=True)
class FileEvidence:
    path: str
    mode: int
    size: int
    mtime_ns: int
    sha256: str


@dataclass(frozen=True)
class GitBinaryIdentity:
    executable: FileEvidence
    version: str


@dataclass(frozen=True)
class RepositoryContext:
    git_binary: GitBinaryIdentity
    root: str
    git_boundary: FileEvidence
    git_dir: str
    common_git_dir: str
    local_config: FileEvidence
    local_config_semantics_sha256: str
    info_attributes_absent: bool
    worktree_config_absent: bool
    replacement_refs_sha256: str


@dataclass(frozen=True)
class PhasePolicyEntry:
    path: str
    status: str
    review_class: str
    rationale: str
    obligations: tuple[str, ...]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseIsolationError(message)


def require_strict_json_equal(
    actual: object,
    expected: object,
    label: str,
    *,
    path: str = "$",
) -> None:
    """Compare JSON values without Python's bool/int/float coercions."""

    require(
        type(actual) is type(expected),
        f"{label} has the wrong JSON type at {path}: "
        f"expected {type(expected).__name__}, observed {type(actual).__name__}",
    )
    if isinstance(expected, dict):
        actual_dict = cast(dict[str, object], actual)
        expected_dict = cast(dict[str, object], expected)
        require(
            set(actual_dict) == set(expected_dict),
            f"{label} object keys changed at {path}",
        )
        for key, expected_value in expected_dict.items():
            require_strict_json_equal(
                actual_dict[key],
                expected_value,
                label,
                path=f"{path}/{key}",
            )
        return
    if isinstance(expected, list):
        actual_list = cast(list[object], actual)
        expected_list = cast(list[object], expected)
        require(
            len(actual_list) == len(expected_list),
            f"{label} array length changed at {path}",
        )
        for index, (actual_value, expected_value) in enumerate(
            zip(actual_list, expected_list, strict=True)
        ):
            require_strict_json_equal(
                actual_value,
                expected_value,
                label,
                path=f"{path}/{index}",
            )
        return
    require(actual == expected, f"{label} value changed at {path}")


def stable_external_regular_file(
    path: Path, *, label: str
) -> tuple[FileEvidence, bytes]:
    try:
        before = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"{label}: cannot inspect {path}: {error}") from error
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{label}: {path} must resolve to a regular non-symlink file",
    )
    try:
        first = path.read_bytes()
        middle = path.lstat()
        second = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{label}: cannot read stable bytes: {error}"
        ) from error
    identity_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
    )
    require(
        all(getattr(before, name) == getattr(middle, name) for name in identity_fields)
        and all(
            getattr(middle, name) == getattr(after, name) for name in identity_fields
        )
        and first == second,
        f"{label}: bytes or metadata changed during observation",
    )
    evidence = FileEvidence(
        path=str(path),
        mode=stat.S_IMODE(after.st_mode),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        sha256=hashlib.sha256(first).hexdigest(),
    )
    return evidence, first


def resolved_git_executable() -> Path:
    global _RESOLVED_GIT_EXECUTABLE
    if _RESOLVED_GIT_EXECUTABLE is not None:
        return _RESOLVED_GIT_EXECUTABLE
    discovered = shutil.which("git")
    require(discovered is not None, "cannot locate Git executable")
    candidate = Path(discovered)
    require(candidate.is_absolute(), "Git executable lookup was not absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise PhaseIsolationError(f"cannot resolve Git executable: {error}") from error
    require(resolved.is_absolute(), "resolved Git executable is not absolute")
    _RESOLVED_GIT_EXECUTABLE = resolved
    return resolved


def scrubbed_git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PAGER": "cat",
            "TZ": "UTC",
        }
    )
    return environment


def git_process(
    *arguments: str,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    git = resolved_git_executable()
    process = subprocess.run(
        [
            str(git),
            "-c",
            "core.replaceRefs=false",
            "-c",
            "advice.detachedHead=false",
            "-c",
            f"core.attributesFile={os.devnull}",
            "-c",
            f"core.excludesFile={os.devnull}",
            *arguments,
        ],
        cwd=ROOT,
        env=scrubbed_git_environment(),
        input=input_bytes,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        if not detail:
            detail = process.stdout.decode("utf-8", errors="replace").strip()
        raise PhaseIsolationError(
            f"git {' '.join(arguments)} failed with {process.returncode}: {detail}"
        )
    return process


def git_text(*arguments: str) -> str:
    raw = git_process(*arguments).stdout
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            f"git {' '.join(arguments)} returned non-UTF-8 text"
        ) from error


def canonical_relative_path(raw: bytes, *, label: str) -> str:
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{label}: non-UTF-8 repository path") from error
    path = PurePosixPath(value)
    require(
        bool(value)
        and not path.is_absolute()
        and str(path) == value
        and "." not in path.parts
        and ".." not in path.parts
        and "\\" not in value
        and "\n" not in value
        and "\r" not in value,
        f"{label}: non-canonical repository path {value!r}",
    )
    return value


def parse_tree(commit: str) -> dict[str, GitEntry]:
    raw = git_process("ls-tree", "-r", "-z", "--full-tree", commit).stdout
    entries: dict[str, GitEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode_raw, kind_raw, oid_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            kind = kind_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                f"cannot parse canonical Git tree entry at {commit}"
            ) from error
        path = canonical_relative_path(raw_path, label=f"tree {commit}")
        require(path not in entries, f"tree {commit}: duplicate path {path!r}")
        require(mode in {"100644", "100755"}, f"tree {commit}: forbidden mode {mode}")
        require(kind == "blob", f"tree {commit}: forbidden object type {kind}")
        require(bool(HEX40_RE.fullmatch(oid)), f"tree {commit}: invalid object id")
        entries[path] = GitEntry(mode=mode, kind=kind, oid=oid, sha256="")
    return entries


def parse_index() -> dict[str, GitEntry]:
    raw = git_process("ls-files", "--stage", "-z").stdout
    entries: dict[str, GitEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
            stage = stage_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                "cannot parse canonical Git index entry"
            ) from error
        path = canonical_relative_path(raw_path, label="Git index")
        require(path not in entries, f"Git index: duplicate path {path!r}")
        require(stage == "0", f"Git index: nonzero merge stage at {path!r}")
        require(mode in {"100644", "100755"}, f"Git index: forbidden mode at {path!r}")
        require(bool(HEX40_RE.fullmatch(oid)), "Git index: invalid object id")
        entries[path] = GitEntry(mode=mode, kind="blob", oid=oid, sha256="")
    return entries


def sha256_blobs(object_ids: Iterable[str]) -> dict[str, str]:
    ordered = tuple(sorted(set(object_ids)))
    if not ordered:
        return {}
    payload = "".join(f"{oid}\n" for oid in ordered).encode("ascii")
    raw = git_process("cat-file", "--batch", input_bytes=payload).stdout
    cursor = 0
    result: dict[str, str] = {}
    for expected_oid in ordered:
        newline = raw.find(b"\n", cursor)
        require(newline >= 0, "truncated git cat-file batch header")
        header = raw[cursor:newline]
        cursor = newline + 1
        fields = header.split(b" ")
        require(len(fields) == 3, "invalid git cat-file batch header")
        oid = fields[0].decode("ascii", errors="strict")
        kind = fields[1].decode("ascii", errors="strict")
        try:
            size = int(fields[2].decode("ascii", errors="strict"))
        except ValueError as error:
            raise PhaseIsolationError("invalid git cat-file object size") from error
        require(oid == expected_oid, "git cat-file batch order/object mismatch")
        require(kind == "blob" and size >= 0, f"{oid}: expected a nonnegative blob")
        end = cursor + size
        require(end < len(raw), f"{oid}: truncated git cat-file blob")
        blob = raw[cursor:end]
        cursor = end
        require(raw[cursor : cursor + 1] == b"\n", f"{oid}: missing batch delimiter")
        cursor += 1
        result[oid] = hashlib.sha256(blob).hexdigest()
    require(cursor == len(raw), "git cat-file batch returned trailing bytes")
    return result


def hydrate_tree(entries: dict[str, GitEntry]) -> dict[str, GitEntry]:
    hashes = sha256_blobs(entry.oid for entry in entries.values())
    return {
        path: GitEntry(
            mode=entry.mode,
            kind=entry.kind,
            oid=entry.oid,
            sha256=hashes[entry.oid],
        )
        for path, entry in entries.items()
    }


def stable_regular_file(relative: str) -> tuple[str, bytes]:
    candidate = ROOT / relative
    current = ROOT
    for component in PurePosixPath(relative).parts[:-1]:
        current = current / component
        try:
            metadata = current.lstat()
        except OSError as error:
            raise PhaseIsolationError(
                f"{relative!r}: cannot inspect parent directory: {error}"
            ) from error
        require(
            stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"{relative!r}: parent path is not a real directory",
        )
    try:
        before = candidate.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{relative!r}: candidate path is missing: {error}"
        ) from error
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{relative!r}: candidate must be a regular non-symlink file",
    )
    require(
        before.st_nlink == 1, f"{relative!r}: hard-linked candidate file is forbidden"
    )
    permissions = stat.S_IMODE(before.st_mode)
    require(
        permissions in {0o644, 0o755},
        f"{relative!r}: non-canonical permissions {permissions:#o}",
    )
    try:
        first = candidate.read_bytes()
        middle = candidate.lstat()
        second = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{relative!r}: cannot read stable bytes: {error}"
        ) from error
    identity_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
    )
    require(
        all(getattr(before, name) == getattr(middle, name) for name in identity_fields)
        and all(
            getattr(middle, name) == getattr(after, name) for name in identity_fields
        )
        and first == second,
        f"{relative!r}: candidate bytes changed during observation",
    )
    mode = "100755" if permissions == 0o755 else "100644"
    return mode, first


def git_blob_oid(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def parse_untracked() -> tuple[str, ...]:
    # Deliberately do not use --exclude-standard: workstation-local info/exclude bytes are not
    # portable to a fresh clone and therefore cannot be a semantic candidate-enumeration input.
    # The only ignore grammar is the exact tracked and protected root .gitignore.
    raw = git_process(
        "ls-files",
        "--others",
        "--exclude-from=.gitignore",
        "-z",
    ).stdout
    paths = [
        canonical_relative_path(item, label="untracked candidate")
        for item in raw.split(b"\0")
        if item
    ]
    require(paths == sorted(paths), "Git returned non-canonical untracked path order")
    require(len(paths) == len(set(paths)), "Git returned duplicate untracked paths")
    return tuple(paths)


def collect_candidate_snapshot() -> CandidateSnapshot:
    head = git_text("rev-parse", "HEAD^{commit}")
    require(bool(HEX40_RE.fullmatch(head)), "HEAD did not resolve to an exact commit")
    head_entries = parse_tree(head)
    index_entries = parse_index()
    require(
        {
            path: (entry.mode, entry.kind, entry.oid)
            for path, entry in index_entries.items()
        }
        == {
            path: (entry.mode, entry.kind, entry.oid)
            for path, entry in head_entries.items()
        },
        "Git index differs from HEAD; phase input requires an unstaged index",
    )
    untracked = parse_untracked()
    require(
        not set(untracked).intersection(index_entries),
        "candidate path is both tracked and untracked",
    )

    entries: dict[str, GitEntry] = {}
    tracked_modifications: list[str] = []
    for path in sorted((*index_entries.keys(), *untracked)):
        mode, raw = stable_regular_file(path)
        entry = GitEntry(
            mode=mode,
            kind="blob",
            oid=git_blob_oid(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
        )
        entries[path] = entry
        head_entry = head_entries.get(path)
        if head_entry is not None and (
            mode != head_entry.mode or entry.oid != head_entry.oid
        ):
            tracked_modifications.append(path)
    return CandidateSnapshot(
        entries=entries,
        head=head,
        head_entries=head_entries,
        tracked_modifications=tuple(tracked_modifications),
        untracked=untracked,
    )


def changed_paths(
    baseline: dict[str, GitEntry], candidate: dict[str, GitEntry]
) -> tuple[str, ...]:
    result: list[str] = []
    for path in sorted(set(baseline).union(candidate)):
        left = baseline.get(path)
        right = candidate.get(path)
        if (
            left is None
            or right is None
            or (left.mode, left.kind, left.sha256)
            != (right.mode, right.kind, right.sha256)
        ):
            result.append(path)
    return tuple(result)


def classified_delta(
    base: dict[str, GitEntry], candidate: dict[str, GitEntry]
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for path in changed_paths(base, candidate):
        left = base.get(path)
        right = candidate.get(path)
        status = "A" if left is None else "D" if right is None else "M"
        result.append((path, status))
    return tuple(result)


def changed_projection(
    baseline: dict[str, GitEntry],
    candidate: dict[str, GitEntry],
    paths: Iterable[str],
) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths).difference(SELF_UNHASHED_PATHS)):
        left = baseline.get(path)
        right = candidate.get(path)
        status = "A" if left is None else "D" if right is None else "M"
        if right is None:
            line = f"{status}\0{path}\0-\0-\n"
        else:
            line = f"{status}\0{path}\0{right.mode}\0{right.sha256}\n"
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def path_projection(entries: dict[str, GitEntry], paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        entry = entries[path]
        digest.update(
            f"{path}\0{entry.mode}\0{entry.kind}\0{entry.sha256}\n".encode("utf-8")
        )
    return digest.hexdigest()


def allowlist_digest(paths: Iterable[str]) -> str:
    ordered = tuple(paths)
    payload = "".join(f"{path}\n" for path in ordered).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def commit_identity(commit: str) -> tuple[str, tuple[str, ...]]:
    raw = git_process("cat-file", "-p", commit).stdout
    try:
        header = raw.split(b"\n\n", 1)[0].decode("ascii")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{commit}: non-ASCII commit header") from error
    tree_values = [line[5:] for line in header.splitlines() if line.startswith("tree ")]
    parent_values = [
        line[7:] for line in header.splitlines() if line.startswith("parent ")
    ]
    require(
        len(tree_values) == 1 and bool(HEX40_RE.fullmatch(tree_values[0])),
        f"{commit}: invalid tree header",
    )
    require(
        all(bool(HEX40_RE.fullmatch(parent)) for parent in parent_values),
        f"{commit}: invalid parent header",
    )
    return tree_values[0], tuple(parent_values)


def is_ancestor(ancestor: str, descendant: str) -> bool:
    process = git_process(
        "merge-base", "--is-ancestor", ancestor, descendant, check=False
    )
    if process.returncode == 0:
        return True
    if process.returncode == 1:
        return False
    detail = process.stderr.decode("utf-8", errors="replace").strip()
    raise PhaseIsolationError(
        f"cannot resolve ancestry {ancestor}..{descendant}: {detail}"
    )


def git_boundary_evidence(path: Path) -> FileEvidence:
    try:
        before = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"cannot inspect .git boundary: {error}") from error
    require(not stat.S_ISLNK(before.st_mode), "symlinked .git boundary is forbidden")
    if stat.S_ISREG(before.st_mode):
        require(before.st_nlink == 1, "hard-linked .git file is forbidden")
        evidence, _raw = stable_external_regular_file(path, label=".git boundary")
        return evidence
    require(stat.S_ISDIR(before.st_mode), ".git must be a file or directory")
    try:
        after = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"cannot replay .git boundary: {error}") from error
    fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")
    require(
        all(getattr(before, name) == getattr(after, name) for name in fields),
        ".git directory metadata changed during observation",
    )
    descriptor = (
        f"directory\0{before.st_dev}\0{before.st_ino}\0"
        f"{before.st_mode}\0{before.st_nlink}\0{before.st_size}\0"
        f"{before.st_mtime_ns}\n"
    ).encode("ascii")
    return FileEvidence(
        path=str(path),
        mode=stat.S_IMODE(before.st_mode),
        size=before.st_size,
        mtime_ns=before.st_mtime_ns,
        sha256=hashlib.sha256(descriptor).hexdigest(),
    )


def parse_local_config(raw: bytes) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            raw_key, raw_value = record.split(b"\n", 1)
            key = raw_key.decode("utf-8").lower()
            value = raw_value.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                "cannot parse isolated local Git configuration"
            ) from error
        require(key and "\n" not in key and "\0" not in value, "invalid local Git key")
        result.append((key, value))
    for key, _value in result:
        require(
            key not in FORBIDDEN_LOCAL_CONFIG_KEYS
            and not any(
                key.startswith(prefix) for prefix in FORBIDDEN_LOCAL_CONFIG_PREFIXES
            ),
            f"forbidden local Git configuration key: {key}",
        )
    return tuple(result)


def validate_absent_git_path(path: Path, *, label: str) -> None:
    require(
        not path.exists() and not path.is_symlink(),
        f"Git overlay file is forbidden: {label}",
    )


def validate_repository_context() -> RepositoryContext:
    require(not SCRIPT_PATH.is_symlink(), "phase checker itself must not be a symlink")
    git = resolved_git_executable()
    git_evidence, _git_raw = stable_external_regular_file(
        git, label="resolved Git executable"
    )
    require(
        bool(HEX64_RE.fullmatch(git_evidence.sha256)),
        "resolved Git executable digest is not canonical SHA-256",
    )
    version_raw = git_process("--version").stdout
    try:
        version = version_raw.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise PhaseIsolationError("Git version output is not UTF-8") from error
    require(
        version.startswith("git version ") and "\n" not in version,
        "Git version output has an unexpected shape",
    )
    git_identity = GitBinaryIdentity(executable=git_evidence, version=version)

    try:
        expected_root = ROOT.resolve(strict=True)
        reported_root = Path(git_text("rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as error:
        raise PhaseIsolationError(
            f"cannot resolve canonical repository root: {error}"
        ) from error
    require(
        reported_root == expected_root, "Git worktree root does not match checker root"
    )
    require(
        git_text("rev-parse", "--show-object-format=storage") == "sha1",
        "phase checker is pinned to this repository's SHA-1 Git object format",
    )
    require(
        git_text("rev-parse", "--is-shallow-repository") == "false",
        "shallow repositories are outside the ancestry claim",
    )

    dot_git = ROOT / ".git"
    boundary_evidence = git_boundary_evidence(dot_git)

    git_dir = Path(git_text("rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = ROOT / git_dir
    common_git_dir = Path(git_text("rev-parse", "--git-common-dir"))
    if not common_git_dir.is_absolute():
        common_git_dir = ROOT / common_git_dir
    try:
        resolved_git_dir = git_dir.resolve(strict=True)
        resolved_common_git_dir = common_git_dir.resolve(strict=True)
    except OSError as error:
        raise PhaseIsolationError(
            f"cannot resolve Git metadata directories: {error}"
        ) from error
    require(
        resolved_git_dir.is_dir() and resolved_common_git_dir.is_dir(),
        "Git metadata roots must resolve to directories",
    )

    for relative in ("info/grafts", "objects/info/alternates"):
        validate_absent_git_path(
            resolved_common_git_dir / relative,
            label=relative,
        )
    validate_absent_git_path(
        resolved_common_git_dir / "info/attributes",
        label="info/attributes",
    )
    validate_absent_git_path(
        resolved_git_dir / "config.worktree",
        label="config.worktree",
    )

    local_config, _local_config_raw = stable_external_regular_file(
        resolved_common_git_dir / "config",
        label="local Git configuration",
    )
    config_process = git_process(
        "config",
        "--no-includes",
        "--local",
        "--null",
        "--list",
    )
    config_semantics = parse_local_config(config_process.stdout)
    config_semantics_sha256 = hashlib.sha256(
        json.dumps(
            config_semantics,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()

    replacement_refs = git_process(
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace",
    ).stdout
    require(
        not replacement_refs,
        "Git replacement references are forbidden",
    )
    return RepositoryContext(
        git_binary=git_identity,
        root=str(expected_root),
        git_boundary=boundary_evidence,
        git_dir=str(resolved_git_dir),
        common_git_dir=str(resolved_common_git_dir),
        local_config=local_config,
        local_config_semantics_sha256=config_semantics_sha256,
        info_attributes_absent=True,
        worktree_config_absent=True,
        replacement_refs_sha256=hashlib.sha256(replacement_refs).hexdigest(),
    )


def validate_commit_envelope(head: str) -> None:
    require(
        (CURRENT_ANCHOR, CURRENT_ANCHOR_TREE)
        == (CORRECTIVE_PARENT, CORRECTIVE_PARENT_TREE),
        "current phase anchor is not the exact failed-public-run corrective parent",
    )
    baseline_tree, _baseline_parents = commit_identity(SCIENTIFIC_BASELINE)
    require(
        baseline_tree == SCIENTIFIC_BASELINE_TREE,
        "scientific baseline tree pin mismatch",
    )
    delivery_tree, delivery_parents = commit_identity(DELIVERY_PARENT)
    require(
        delivery_tree == DELIVERY_PARENT_TREE,
        "delivery parent tree pin mismatch",
    )
    require(
        delivery_parents == (SCIENTIFIC_BASELINE,),
        "delivery commit is not the exact direct child of the scientific baseline",
    )
    for commit, expected_parent, expected_tree in DECLARED_COMMIT_CHAIN:
        tree, parents = commit_identity(commit)
        require(tree == expected_tree, f"{commit}: declared tree pin mismatch")
        require(
            parents == (expected_parent,),
            f"{commit}: declared single-parent pin mismatch",
        )
    require(
        is_ancestor(CURRENT_ANCHOR, head),
        "HEAD does not descend from the exact current KSG anchor",
    )

    previous = CURRENT_ANCHOR
    later_raw = git_text(
        "rev-list", "--first-parent", "--reverse", f"{CURRENT_ANCHOR}..{head}"
    )
    later = tuple(later_raw.splitlines()) if later_raw else ()
    for commit in later:
        require(bool(HEX40_RE.fullmatch(commit)), "invalid post-anchor commit id")
        _tree, parents = commit_identity(commit)
        require(
            parents == (previous,),
            f"{commit}: post-anchor history must be a single-parent fast-forward",
        )
        previous = commit


def parse_name_status(raw: bytes, *, label: str) -> tuple[tuple[str, str], ...]:
    fields = raw.split(b"\0")
    if fields and not fields[-1]:
        fields.pop()
    require(len(fields) % 2 == 0, f"{label}: malformed Git name-status stream")
    result: list[tuple[str, str]] = []
    for index in range(0, len(fields), 2):
        try:
            status_value = fields[index].decode("ascii")
        except UnicodeDecodeError as error:
            raise PhaseIsolationError(f"{label}: non-ASCII Git status") from error
        require(
            status_value in {"A", "M", "D"},
            f"{label}: forbidden Git delta status {status_value!r}",
        )
        path = canonical_relative_path(fields[index + 1], label=label)
        result.append((path, status_value))
    require(
        tuple(path for path, _status in result)
        == tuple(sorted(path for path, _status in result)),
        f"{label}: Git delta paths are not canonical and sorted",
    )
    require(
        len(result) == len({path for path, _status in result}),
        f"{label}: duplicate Git delta path",
    )
    return tuple(result)


def post_anchor_history(
    head: str,
) -> tuple[
    tuple[str, tuple[tuple[str, str], ...], dict[str, GitEntry]],
    ...,
]:
    commits_raw = git_text(
        "rev-list",
        "--first-parent",
        "--reverse",
        f"{CURRENT_ANCHOR}..{head}",
    )
    commits = tuple(commits_raw.splitlines()) if commits_raw else ()
    require(
        len(commits) <= MAX_POST_ANCHOR_COMMITS,
        "post-anchor history exceeds the bounded commit count",
    )
    previous = CURRENT_ANCHOR
    result: list[tuple[str, tuple[tuple[str, str], ...], dict[str, GitEntry]]] = []
    for commit in commits:
        raw = git_process(
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "--no-renames",
            "-r",
            "-z",
            previous,
            commit,
        ).stdout
        result.append(
            (
                commit,
                parse_name_status(raw, label=f"post-anchor commit {commit}"),
                hydrate_tree(parse_tree(commit)),
            )
        )
        previous = commit
    return tuple(result)


def validate_phase_path_policy(
    snapshot: CandidateSnapshot,
    anchor: dict[str, GitEntry],
) -> tuple[PhasePolicyEntry, ...]:
    raw = read_candidate_bytes(PHASE_PATH_POLICY)
    require(
        hashlib.sha256(raw).hexdigest() == PHASE_PATH_POLICY_SHA256,
        "phase path policy digest differs from the manually reviewed authority",
    )
    policy = canonical_json_from_bytes(raw, label=PHASE_PATH_POLICY)
    require(isinstance(policy, dict), "phase path policy root must be an object")
    require(
        set(policy)
        == {
            "anchor",
            "authority",
            "deletions_permitted",
            "entries",
            "review_classes",
            "schema",
            "schema_revision",
        },
        "phase path policy has an unexpected top-level shape",
    )
    require(
        policy.get("schema") == "pid-rs/ksg-phase-path-policy",
        "phase path policy schema identifier is invalid",
    )
    require_strict_json_equal(
        policy.get("schema_revision"),
        3,
        "phase path policy schema revision",
    )
    require_strict_json_equal(
        policy.get("anchor"),
        {
            "commit": CURRENT_ANCHOR,
            "tree": CURRENT_ANCHOR_TREE,
        },
        "phase path policy anchor",
    )
    require(
        policy.get("deletions_permitted") is False,
        "phase path policy must forbid every deletion",
    )
    require_strict_json_equal(
        policy.get("authority"),
        {
            "authoritative": True,
            "mechanical_resealing_permitted": False,
            "scope": (
                "KSG revision-4 af509-anchored public-CI tooling correction "
                "only"
            ),
        },
        "phase path policy authority contract",
    )
    raw_entries = policy.get("entries")
    raw_classes = policy.get("review_classes")
    require(
        isinstance(raw_entries, list) and raw_entries,
        "phase path policy entries must be a nonempty array",
    )
    require(
        isinstance(raw_classes, dict) and raw_classes,
        "phase path policy review classes must be a nonempty object",
    )
    review_classes: dict[str, tuple[str, tuple[str, ...]]] = {}
    for class_name, class_value in raw_classes.items():
        require(
            isinstance(class_name, str)
            and class_name
            and isinstance(class_value, dict)
            and set(class_value) == {"obligations", "rationale"},
            f"phase path policy review class {class_name!r} has an unexpected shape",
        )
        rationale = class_value.get("rationale")
        obligations = class_value.get("obligations")
        require(
            isinstance(rationale, str)
            and len(rationale.strip()) >= 12
            and "\n" not in rationale,
            f"phase path policy review class {class_name!r} lacks a rationale",
        )
        require(
            isinstance(obligations, list)
            and obligations
            and all(
                isinstance(item, str) and item.strip() and "\n" not in item
                for item in obligations
            )
            and len(obligations) == len(set(obligations)),
            f"phase path policy review class {class_name!r} has invalid obligations",
        )
        review_classes[class_name] = (rationale, tuple(obligations))
    require(
        review_classes == EXPECTED_CORRECTIVE_REVIEW_CLASS_CONTRACTS,
        "corrective review-class rationale/obligation contracts changed",
    )
    entries: list[PhasePolicyEntry] = []
    for index, value in enumerate(raw_entries):
        require(
            isinstance(value, dict)
            and set(value) == {"path", "review_class", "status"},
            f"phase path policy entry {index} has an unexpected shape",
        )
        raw_path = value.get("path")
        require(
            isinstance(raw_path, str),
            f"phase path policy entry {index} has a non-string path",
        )
        path = canonical_relative_path(
            raw_path.encode("utf-8"),
            label=f"phase path policy entry {index}",
        )
        status_value = value.get("status")
        review_class = value.get("review_class")
        require(
            type(status_value) is str and status_value in {"A", "M"},
            f"phase path policy entry {path!r} is not classified A or M",
        )
        require(
            isinstance(review_class, str) and review_class in review_classes,
            f"phase path policy entry {path!r} references an unknown review class",
        )
        rationale, obligations = review_classes[review_class]
        entries.append(
            PhasePolicyEntry(
                path=path,
                status=status_value,
                review_class=review_class,
                rationale=rationale,
                obligations=obligations,
            )
        )
    require(
        tuple(entry.path for entry in entries)
        == tuple(sorted(entry.path for entry in entries))
        and len(entries) == len({entry.path for entry in entries}),
        "phase path policy entries are not sorted and duplicate-free",
    )
    observed_entries = tuple(
        (entry.path, entry.status, entry.review_class) for entry in entries
    )
    require(
        observed_entries == EXPECTED_CORRECTIVE_POLICY_ENTRIES,
        "corrective phase path/status/review-class inventory changed",
    )
    policy_delta = tuple((entry.path, entry.status) for entry in entries)
    actual_delta = classified_delta(anchor, snapshot.entries)
    require(
        all(status_value != "D" for _path, status_value in actual_delta),
        "candidate delta from current anchor contains a forbidden deletion",
    )
    require(
        actual_delta == policy_delta,
        "candidate anchor delta differs from the separately reviewed A/M path policy",
    )
    require(
        (PHASE_PATH_POLICY, "A") in policy_delta,
        "corrective phase path policy must classify itself as added",
    )

    policy_by_path = {entry.path: entry.status for entry in entries}
    expected_tree = dict(anchor)
    transitioned: set[str] = set()
    for commit, changes, commit_tree in post_anchor_history(snapshot.head):
        for path, status_value in changes:
            require(
                status_value != "D",
                f"{commit}: post-anchor history contains forbidden deletion of {path}",
            )
            require(
                path in policy_by_path,
                f"{commit}: post-anchor history touched non-policy path {path}",
            )
            require(
                path not in transitioned,
                f"{commit}: policy path changed after its exact final transition: {path}",
            )
            expected_status = policy_by_path[path]
            require(
                status_value == expected_status,
                (
                    f"{commit}: policy path {path} has invalid {status_value} "
                    f"transition; expected one exact {expected_status}"
                ),
            )
            final_entry = snapshot.entries.get(path)
            require(
                final_entry is not None,
                f"{commit}: final reviewed candidate path is absent: {path}",
            )
            expected_tree[path] = final_entry
            transitioned.add(path)
        require(
            commit_tree == expected_tree,
            (
                f"{commit}: post-anchor tree is not a monotone composition of "
                "exact anchor/absent and exact final reviewed path states"
            ),
        )
    if snapshot.head != CURRENT_ANCHOR:
        require(
            transitioned == set(policy_by_path),
            "committed-descendant history did not transition every policy path exactly once",
        )
    return tuple(entries)


def validate_staged_tree_custody(
    snapshot: CandidateSnapshot,
    expected_tree: str | None,
    checkpoint_commit: str | None,
) -> tuple[str | None, str | None]:
    require(
        expected_tree is not None or checkpoint_commit is None,
        "--checkpoint-commit requires --expected-candidate-tree",
    )
    if expected_tree is None:
        return None, None
    require(
        bool(HEX40_RE.fullmatch(expected_tree)),
        "expected candidate tree is not a canonical SHA-1 object id",
    )
    resolved_tree = git_text("rev-parse", f"{expected_tree}^{{tree}}")
    require(
        resolved_tree == expected_tree,
        "expected candidate tree does not resolve to the exact supplied tree id",
    )
    staged_entries = hydrate_tree(parse_tree(expected_tree))
    require(
        staged_entries == snapshot.entries,
        "external staged/checkpoint tree differs from the candidate snapshot",
    )
    if checkpoint_commit is not None:
        require(
            bool(HEX40_RE.fullmatch(checkpoint_commit)),
            "checkpoint commit is not a canonical SHA-1 object id",
        )
        commit_tree, parents = commit_identity(checkpoint_commit)
        require(
            commit_tree == expected_tree,
            "checkpoint commit tree differs from the externally supplied tree",
        )
        if checkpoint_commit != snapshot.head:
            require(
                parents == (snapshot.head,),
                "detached checkpoint commit is not the exact child of snapshot HEAD",
            )
    return expected_tree, checkpoint_commit


def canonical_json_from_bytes(raw: bytes, *, label: str) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PhaseIsolationError(f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> None:
        raise PhaseIsolationError(f"{label}: non-finite JSON token {token!r}")

    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PhaseIsolationError(
            f"{label}: invalid canonical JSON: {error}"
        ) from error
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    require(
        text == rendered,
        f"{label}: JSON is not sorted two-space ASCII form with one final LF",
    )
    return value


def read_candidate_bytes(relative: str) -> bytes:
    _mode, raw = stable_regular_file(relative)
    return raw


def git_blob_at(commit: str, relative: str) -> bytes:
    process = git_process("show", f"{commit}:{relative}")
    return process.stdout


def replace_unique_workflow_fragment(
    raw: bytes,
    before: bytes,
    after: bytes,
    *,
    label: str,
) -> bytes:
    require(
        raw.count(before) == 1,
        f"source workflow does not contain one exact {label} edit anchor",
    )
    return raw.replace(before, after, 1)


def pinned_lean_setup_and_cache() -> bytes:
    return (
        b"      - name: Install pinned Elan\n"
        b"        shell: bash\n"
        b"        env:\n"
        b"          ELAN_ARCHIVE_SHA256: "
        b"df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
        b"          ELAN_ARCHIVE_URL: "
        b"https://github.com/leanprover/elan/releases/download/v4.2.3/"
        b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          archive="$RUNNER_TEMP/elan-x86_64-unknown-linux-gnu.tar.gz"\n'
        b'          install_root="$RUNNER_TEMP/elan-v4.2.3"\n'
        b"          curl --fail --location --proto '=https' --retry 5 --show-error \\\n"
        b'            --tlsv1.2 --output "$archive" "$ELAN_ARCHIVE_URL"\n'
        b"          printf '%s  %s\\n' \"$ELAN_ARCHIVE_SHA256\" \"$archive\" \\\n"
        b"            | sha256sum --check --strict\n"
        b'          mkdir -p "$install_root"\n'
        b'          tar -xzf "$archive" -C "$install_root"\n'
        b'          "$install_root/elan-init" -y --default-toolchain none '
        b"--no-modify-path\n"
        b'          echo "$HOME/.elan/bin" >> "$GITHUB_PATH"\n'
        b"      - uses: actions/cache@"
        b"27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
        b"        with:\n"
        b"          path: audit/formal/lean/.lake\n"
        b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
        b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
        b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
        b"${{ github.sha }}\n"
        b"          restore-keys: lake-${{ runner.os }}-${{ runner.arch }}-"
        b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
        b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}\n"
    )


def pinned_mathlib_build() -> bytes:
    return (
        b"      - name: Fetch the Mathlib cache and build\n"
        b"        working-directory: audit/formal/lean\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b"          lake exe cache get\n"
        b"          lake build\n"
    )


def validate_public_ci_failure_evidence() -> None:
    raw = read_candidate_bytes(PUBLIC_CI_FAILURE_RECEIPT)
    require(
        hashlib.sha256(raw).hexdigest() == PUBLIC_CI_FAILURE_RECEIPT_SHA256,
        "public CI failure receipt differs from the independently reviewed bytes",
    )
    parsed = canonical_json_from_bytes(raw, label=PUBLIC_CI_FAILURE_RECEIPT)
    require(
        isinstance(parsed, dict),
        "public CI failure receipt root must be an object",
    )
    receipt = cast(dict[str, Any], parsed)
    require(
        set(receipt)
        == {
            "claim_boundary",
            "head",
            "jobs",
            "remediation",
            "run",
            "schema",
            "schema_revision",
            "status",
        },
        "public CI failure receipt top-level shape changed",
    )
    require_strict_json_equal(
        {
            "claim_boundary": receipt.get("claim_boundary"),
            "schema": receipt.get("schema"),
            "schema_revision": receipt.get("schema_revision"),
            "status": receipt.get("status"),
        },
        {
            "claim_boundary": (
                "Hosted CI execution and custody receipt for exact commit "
                "af50935be9ecf9a81aeb30c56b45059652468746 only. It records two "
                "missing-tool provisioning failures and 43 successful jobs. It "
                "gives no credit to skipped steps, does not settle full CI, and "
                "does not prove mathematical correctness, authenticity, "
                "portability, release readiness, publication acceptance, or "
                "downstream validity."
            ),
            "schema": "pid-rs/public-ci-failure-receipt",
            "schema_revision": 1,
            "status": "terminal_failure_retained",
        },
        "public CI failure receipt identity",
    )
    expected_head = {
        "branch": "main",
        "commit": CORRECTIVE_PARENT,
        "tree": CORRECTIVE_PARENT_TREE,
    }
    require_strict_json_equal(
        receipt.get("head"),
        expected_head,
        "public CI failure receipt head",
    )
    expected_run = {
        "attempt": 1,
        "conclusion": "failure",
        "created_at": "2026-07-28T23:49:13Z",
        "event": "push",
        "head_branch": "main",
        "head_sha": CORRECTIVE_PARENT,
        "html_url": "https://github.com/sepahead/pid-rs/actions/runs/30409192059",
        "id": 30409192059,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "run_number": 146,
        "status": "completed",
        "updated_at": "2026-07-29T00:09:24Z",
        "workflow_id": 297369773,
    }
    require_strict_json_equal(
        receipt.get("run"),
        expected_run,
        "public CI failure receipt run",
    )
    jobs_raw = receipt.get("jobs")
    require(isinstance(jobs_raw, dict), "public CI failure jobs must be an object")
    jobs = cast(dict[str, Any], jobs_raw)
    require(
        set(jobs)
        == {
            "failed",
            "ksg_phase_job",
            "lean_environment_control_job",
            "success_count",
            "total_count",
        },
        "public CI failure job inventory changed",
    )
    failed_raw = jobs.get("failed")
    require(
        isinstance(failed_raw, list) and len(failed_raw) == 2,
        "public CI failure receipt must contain exactly two failed jobs",
    )
    failed_jobs = cast(list[dict[str, Any]], failed_raw)
    require(
        all(isinstance(job, dict) for job in failed_jobs),
        "public CI failed-job entries must be objects",
    )
    require(
        set(failed_jobs[0])
        == {
            "completed_at",
            "conclusion",
            "failure",
            "id",
            "name",
            "skipped_actions_steps",
            "started_at",
            "status",
        },
        "public CI certified-SxPID2 failed-job shape changed",
    )
    require(
        set(failed_jobs[1])
        == {
            "completed_at",
            "completed_intra_step_routes",
            "conclusion",
            "credit_boundary",
            "failure",
            "id",
            "name",
            "skipped_actions_steps",
            "started_at",
            "status",
            "unreached_intra_step_routes",
        },
        "public CI formal-PDF failed-job shape changed",
    )
    failed_summaries = [
        {
            "completed_at": job.get("completed_at"),
            "conclusion": job.get("conclusion"),
            "failure": job.get("failure"),
            "id": job.get("id"),
            "name": job.get("name"),
            "started_at": job.get("started_at"),
            "status": job.get("status"),
        }
        for job in failed_jobs
    ]
    require_strict_json_equal(
        failed_summaries,
        [
            {
                "completed_at": "2026-07-28T23:53:12Z",
                "conclusion": "failure",
                "failure": {
                    "classification": "ci_tool_provisioning",
                    "exact_error": (
                        "Lean exact-log-product check failed: lake is not available"
                    ),
                    "log_digest_domain": (
                        "decoded bytes returned by the GitHub Actions job-logs "
                        "REST endpoint"
                    ),
                    "log_sha256": (
                        "4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10"
                    ),
                    "log_size_bytes": 108775,
                    "scientific_counterexample": False,
                    "step_name": (
                        "Run python3 scripts/check-lean-exact-log-product.py"
                    ),
                    "step_number": 18,
                },
                "id": 90441337083,
                "name": "Exact-count directed-rounding SxPID2 reference",
                "started_at": "2026-07-28T23:49:22Z",
                "status": "completed",
            },
            {
                "completed_at": "2026-07-28T23:50:38Z",
                "conclusion": "failure",
                "failure": {
                    "classification": "ci_tool_provisioning",
                    "exact_error": (
                        "ecosystem compatibility audit PDF check: missing command: "
                        "chktex"
                    ),
                    "first_failed_intra_step_route": (
                        "scripts/check-ecosystem-compatibility-audit-pdf.sh "
                        "--cross-toolchain"
                    ),
                    "log_digest_domain": (
                        "decoded bytes returned by the GitHub Actions job-logs "
                        "REST endpoint"
                    ),
                    "log_sha256": (
                        "4889d459eaf1c52f394612a593e4bf27718145169025d314f078f718f5cc932c"
                    ),
                    "log_size_bytes": 43692,
                    "scientific_counterexample": False,
                    "step_name": (
                        "Rebuild warning-free papers and compare text, page geometry, "
                        "and embedded fonts"
                    ),
                    "step_number": 5,
                },
                "id": 90441337159,
                "name": "Formal LaTeX / PDF inventory and cross-toolchain structure",
                "started_at": "2026-07-28T23:49:22Z",
                "status": "completed",
            },
        ],
        "public CI failed-job summaries",
    )
    failed_ids = tuple(cast(int, job.get("id")) for job in failed_jobs)
    require(
        failed_ids == tuple(sorted(set(failed_ids))),
        "public CI failed-job ids must be ordered and unique",
    )
    expected_skipped_actions = [
        {
            "conclusion": "skipped",
            "name": "Run python3 scripts/check-certified-sxpid2-claim.py",
            "number": 19,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": "Run python3 scripts/check-certified-sxpid2-claim-self-test.py",
            "number": 20,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": "Run cargo install cargo-deny --locked --version 0.20.2",
            "number": 21,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": (
                "Run cargo deny --manifest-path "
                "audit/tools/certified-sxpid/Cargo.toml --config "
                "audit/tools/certified-sxpid/deny.toml check"
            ),
            "number": 22,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": (
                "Post Run actions/setup-python@"
                "ece7cb06caefa5fff74198d8649806c4678c61a1"
            ),
            "number": 43,
            "status": "completed",
        },
    ]
    require_strict_json_equal(
        failed_jobs[0].get("skipped_actions_steps"),
        expected_skipped_actions,
        "public CI skipped Actions steps",
    )
    completed_pdf_routes = [
        "python3 scripts/check-formal-pdf-style.py",
        "python3 scripts/check-formal-pdf-style-self-test.py",
        "scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain",
        "scripts/check-dependency-colored-sxpid-pdf.sh --cross-toolchain",
    ]
    unreached_pdf_routes = [
        "scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain",
        "scripts/check-finite-alphabet-convergence-pdf.sh --cross-toolchain",
        "scripts/check-formal-tool-adoption-pdf.sh --cross-toolchain",
        "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain",
        "scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
        "scripts/check-support-change-tolerant-sxpid-pdf.sh --cross-toolchain",
    ]
    require_strict_json_equal(
        {
            "completed_intra_step_routes": failed_jobs[1].get(
                "completed_intra_step_routes"
            ),
            "credit_boundary": failed_jobs[1].get("credit_boundary"),
            "skipped_actions_steps": failed_jobs[1].get("skipped_actions_steps"),
            "unreached_intra_step_routes": failed_jobs[1].get(
                "unreached_intra_step_routes"
            ),
        },
        {
            "completed_intra_step_routes": completed_pdf_routes,
            "credit_boundary": (
                "GitHub Actions reports only the containing step as failed. This "
                "receipt gives no independent pass credit to any in-step paper "
                "route and no execution credit to routes after the first reported "
                "chktex error."
            ),
            "skipped_actions_steps": [],
            "unreached_intra_step_routes": unreached_pdf_routes,
        },
        "public CI formal-PDF composite-step credit boundary",
    )
    require_strict_json_equal(
        jobs.get("ksg_phase_job"),
        {
            "completed_at": "2026-07-29T00:09:23Z",
            "conclusion": "success",
            "id": 90441337099,
            "name": "KSG integer-harmonic arithmetic and phase isolation",
            "started_at": "2026-07-28T23:49:15Z",
            "status": "completed",
        },
        "public CI KSG control job",
    )
    require_strict_json_equal(
        jobs.get("lean_environment_control_job"),
        {
            "claim_boundary": (
                "This same-run success shows that the existing checksum-pinned "
                "Elan/cache/Mathlib-build route executed successfully in its own "
                "job. It is a tooling-pattern control, not evidence that another "
                "job inherited tools or that skipped SxPID2/PDF routes passed."
            ),
            "completed_at": "2026-07-28T23:53:42Z",
            "conclusion": "success",
            "id": 90441337145,
            "name": (
                "Finite-alphabet, dependency-color, support-change, and KSG "
                "harmonic proof cores"
            ),
            "provisioning_steps": [
                {
                    "conclusion": "success",
                    "name": "Install pinned Elan",
                    "number": 3,
                    "status": "completed",
                },
                {
                    "conclusion": "success",
                    "name": (
                        "Run actions/cache@"
                        "27d5ce7f107fe9357f9df03efb73ab90386fccae"
                    ),
                    "number": 4,
                    "status": "completed",
                },
                {
                    "conclusion": "success",
                    "name": "Fetch the Mathlib cache and build",
                    "number": 5,
                    "status": "completed",
                },
            ],
            "started_at": "2026-07-28T23:49:15Z",
            "status": "completed",
        },
        "public CI Lean-environment control job",
    )
    require_strict_json_equal(
        {
            "success_count": jobs.get("success_count"),
            "total_count": jobs.get("total_count"),
        },
        {"success_count": 43, "total_count": 45},
        "public CI job counts",
    )
    require(
        cast(int, jobs["success_count"]) + len(failed_jobs)
        == cast(int, jobs["total_count"]),
        "public CI success and failure counts do not close the job total",
    )
    expected_remediation = {
        "formal_pdf_job": [
            (
                "Install chktex in the fresh Ubuntu TeX toolchain before the "
                "unchanged cross-toolchain paper gate."
            ),
            (
                "Provision the pinned Lean and Mathlib environment for the "
                "statically reachable descriptor-factorization checker; this lake "
                "dependency was latent because the earlier chktex failure stopped "
                "the run first."
            ),
            (
                "Make the directly invocable foundational-paper route preflight "
                "lake."
            ),
        ],
        "scientific_claims_changed": False,
        "settled_full_ci": False,
        "sxpid2_job": [
            "Provision checksum-pinned Elan 4.2.3 inside the certified SxPID2 job.",
            (
                "Restore the pinned Lean and Mathlib environment before the "
                "unchanged exact-log-product kernel checker."
            ),
        ],
        "whole_run_rerun_required": True,
    }
    require_strict_json_equal(
        receipt.get("remediation"),
        expected_remediation,
        "public CI remediation and no-credit state",
    )
    require(
        commit_identity(CORRECTIVE_PARENT)[0] == CORRECTIVE_PARENT_TREE,
        "public CI receipt subject commit does not resolve to the pinned tree",
    )
    require(
        expected_head["commit"] == expected_run["head_sha"] == CORRECTIVE_PARENT,
        "public CI receipt commit bindings diverged",
    )

    memo_raw = read_candidate_bytes(CORRECTIVE_EVIDENCE)
    try:
        memo = memo_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "public CI corrective memo is not UTF-8"
        ) from error
    begin = "PUBLIC_CI_FAILURE_PARITY_BEGIN\n"
    end = "\nPUBLIC_CI_FAILURE_PARITY_END"
    require(
        memo.count(begin) == 1 and memo.count(end) == 1,
        "public CI corrective memo parity sentinels are not unique",
    )
    prefix, remainder = memo.split(begin, 1)
    parity_text, suffix = remainder.split(end, 1)
    require(
        prefix.endswith("```text\n") and suffix.startswith("\n```"),
        "public CI corrective memo parity block lost its exact code-fence boundary",
    )
    parity = canonical_json_from_bytes(
        (parity_text + "\n").encode("utf-8"),
        label="public CI corrective memo parity block",
    )
    first_failure = cast(dict[str, Any], failed_jobs[0]["failure"])
    second_failure = cast(dict[str, Any], failed_jobs[1]["failure"])
    expected_parity = {
        "failed_jobs": [
            {
                "conclusion": failed_jobs[0]["conclusion"],
                "exact_error": first_failure["exact_error"],
                "id": failed_jobs[0]["id"],
                "log_sha256": first_failure["log_sha256"],
                "log_size_bytes": first_failure["log_size_bytes"],
                "scientific_counterexample": first_failure[
                    "scientific_counterexample"
                ],
                "step_number": first_failure["step_number"],
            },
            {
                "conclusion": failed_jobs[1]["conclusion"],
                "exact_error": second_failure["exact_error"],
                "id": failed_jobs[1]["id"],
                "log_sha256": second_failure["log_sha256"],
                "log_size_bytes": second_failure["log_size_bytes"],
                "scientific_counterexample": second_failure[
                    "scientific_counterexample"
                ],
                "step_number": second_failure["step_number"],
            },
        ],
        "formal_pdf_intra_step": {
            "completed_routes": completed_pdf_routes,
            "failed_route": second_failure["first_failed_intra_step_route"],
            "unreached_routes": unreached_pdf_routes,
        },
        "head": {
            "commit": expected_head["commit"],
            "tree": expected_head["tree"],
        },
        "integration_disposition": (
            "NO-GO pending a fresh complete public rerun"
        ),
        "job_counts": {
            "failed": len(failed_jobs),
            "success": jobs["success_count"],
            "total": jobs["total_count"],
        },
        "ksg_job": {
            "conclusion": cast(dict[str, Any], jobs["ksg_phase_job"])[
                "conclusion"
            ],
            "id": cast(dict[str, Any], jobs["ksg_phase_job"])["id"],
            "status": cast(dict[str, Any], jobs["ksg_phase_job"])["status"],
        },
        "latent_dependencies": [
            {
                "classification": "statically discovered latent dependency",
                "missing_tool": "lake",
                "route": (
                    "scripts/check-foundational-sxpid-audit-pdf.sh "
                    "--cross-toolchain"
                ),
            }
        ],
        "observed_missing_tools": ["lake", "chktex"],
        "receipt_path": PUBLIC_CI_FAILURE_RECEIPT,
        "receipt_sha256": PUBLIC_CI_FAILURE_RECEIPT_SHA256,
        "remediation": {
            "settled_full_ci": expected_remediation["settled_full_ci"],
            "whole_run_rerun_required": expected_remediation[
                "whole_run_rerun_required"
            ],
        },
        "run": {
            "attempt": expected_run["attempt"],
            "conclusion": expected_run["conclusion"],
            "id": expected_run["id"],
            "number": expected_run["run_number"],
            "status": expected_run["status"],
        },
        "schema": "pid-rs/public-ci-failure-human-parity",
        "schema_revision": 1,
        "skipped_actions_steps": expected_skipped_actions,
    }
    require_strict_json_equal(
        parity,
        expected_parity,
        "public CI human/machine parity projection",
    )


def validate_ci_corrective_firewall() -> None:
    relative = ".github/workflows/ci.yml"
    prior_expected = git_blob_at(M1A_SCIENTIFIC_COMMIT, relative)
    phase_prefix = (
        b"      - name: Verify the exact KSG-only Git phase envelope\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          checkpoint="$(git rev-parse --verify HEAD)"\n'
    )
    normalized_phase_prefix = (
        b"      - name: Verify the exact KSG-only Git phase envelope\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          worktree_config=".git/config.worktree"\n'
        b'          expected_worktree_config_sha256="443a5f645c23c3d0c0aa09f634b2ad111d46ef61946b598a2fb311678ab47454"\n'
        b"          if [[ ! -d .git || -L .git ]]; then\n"
        b"            printf 'expected a real .git directory at the Actions checkout root\\n' >&2\n"
        b"            exit 1\n"
        b"          fi\n"
        b'          if [[ -e "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b'            if [[ ! -f "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b"              printf 'refusing non-regular checkout worktree config: %s\\n' \\\n"
        b'                "$worktree_config" >&2\n'
        b"              exit 1\n"
        b"            fi\n"
        b'            if [[ "$(stat -c \'%h\' "$worktree_config")" != "1" ]]; then\n'
        b"              printf 'refusing hard-linked checkout worktree config: %s\\n' \\\n"
        b'                "$worktree_config" >&2\n'
        b"              exit 1\n"
        b"            fi\n"
        b"            if ! printf '%s  %s\\n' \\\n"
        b'              "$expected_worktree_config_sha256" "$worktree_config" \\\n'
        b"              | sha256sum --check --strict --status\n"
        b"            then\n"
        b"              printf 'checkout worktree config bytes are not the reviewed inert residue\\n' >&2\n"
        b"              exit 1\n"
        b"            fi\n"
        b'            unlink -- "$worktree_config"\n'
        b"          fi\n"
        b'          if [[ -e "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b"            printf 'checkout worktree config survived exact normalization\\n' >&2\n"
        b"            exit 1\n"
        b"          fi\n"
        b'          checkpoint="$(git rev-parse --verify HEAD)"\n'
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        phase_prefix,
        normalized_phase_prefix,
        label="prior checkout residue normalization",
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        b"            latexmk \\\n            lmodern \\\n",
        (
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        label="prior lacheck package",
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        (
            b"          cargo deny --manifest-path "
            b"audit/tools/certified-sxpid/Cargo.toml check\n"
            b"          --config audit/tools/certified-sxpid/deny.toml\n"
        ),
        (
            b"          cargo deny --manifest-path "
            b"audit/tools/certified-sxpid/Cargo.toml\n"
            b"          --config audit/tools/certified-sxpid/deny.toml check\n"
        ),
        label="prior cargo-deny 0.20.2 common-option order",
    )
    corrective_parent = git_blob_at(CORRECTIVE_PARENT, relative)
    require(
        prior_expected == corrective_parent,
        "af509 workflow differs from the exact prior three-edit dc7 transform",
    )

    expected = corrective_parent
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        (
            b"            chktex \\\n"
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        label="formal PDF chktex package",
    )
    lean_setup = pinned_lean_setup_and_cache()
    mathlib_build = pinned_mathlib_build()
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"      - uses: actions/setup-python@"
            b"ece7cb06caefa5fff74198d8649806c4678c61a1 # v6\n"
            b"        with:\n"
            b'          python-version: "3.11"\n'
            b"      - run: >-\n"
            b"          cargo fetch --locked\n"
        ),
        (
            b"      - uses: actions/setup-python@"
            b"ece7cb06caefa5fff74198d8649806c4678c61a1 # v6\n"
            b"        with:\n"
            b'          python-version: "3.11"\n'
            + lean_setup
            + b"      - run: >-\n"
            b"          cargo fetch --locked\n"
        ),
        label="certified SxPID2 pinned Lean provisioning",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"      - run: python3 "
            b"audit/tools/certified-sxpid/scripts/challenge-exact-products.py\n"
            b"      - run: python3 scripts/check-lean-exact-log-product.py\n"
        ),
        (
            b"      - run: python3 "
            b"audit/tools/certified-sxpid/scripts/challenge-exact-products.py\n"
            + mathlib_build
            + b"      - run: python3 scripts/check-lean-exact-log-product.py\n"
        ),
        label="certified SxPID2 Mathlib build",
    )
    formal_checkout = (
        b"      - uses: actions/checkout@"
        b"9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
        b"        with:\n"
        b"          persist-credentials: false\n"
        b"      - name: Check the typed citation edge and adjacent-arrow countermodel\n"
    )
    expected = replace_unique_workflow_fragment(
        expected,
        formal_checkout,
        (
            b"      - uses: actions/checkout@"
            b"9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
            b"        with:\n"
            b"          persist-credentials: false\n"
            + lean_setup
            + mathlib_build
            + b"      - name: Check the typed citation edge and adjacent-arrow countermodel\n"
        ),
        label="formal PDF pinned Lean and Mathlib provisioning",
    )
    require(
        read_candidate_bytes(relative) == expected,
        "CI corrective workflow differs from the exact af509 tooling transform",
    )


def validate_claim_checker_workflow_rebind() -> None:
    checker_path = "scripts/check-certified-sxpid2-claim.py"
    expected = git_blob_at(CORRECTIVE_PARENT, checker_path)
    workflow = read_candidate_bytes(".github/workflows/ci.yml")
    workflow_lines = workflow.splitlines(keepends=True)
    starts = [
        index
        for index, line in enumerate(workflow_lines)
        if line == b"  certified-sxpid-reference:\n"
    ]
    require(
        len(starts) == 1,
        "corrected workflow does not contain one certified-SxPID2 job",
    )
    start = starts[0]
    end = next(
        (
            index
            for index in range(start + 1, len(workflow_lines))
            if re.fullmatch(rb"  [A-Za-z0-9_-]+:\n", workflow_lines[index])
            is not None
        ),
        len(workflow_lines),
    )
    job_digest = hashlib.sha256(b"".join(workflow_lines[start:end])).hexdigest()
    workflow_digest = hashlib.sha256(workflow).hexdigest()
    expected = replace_unique_workflow_fragment(
        expected,
        b"32670cfac1bcd508b2658db2950bbce4689ca695b29367b08b6f71c1010a30e2",
        job_digest.encode("ascii"),
        label="certified job digest rebind",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        b"b3cfb2be2bb310545faf8abc662333167745f863aab29f074d25a60b223ba02c",
        workflow_digest.encode("ascii"),
        label="complete workflow digest rebind",
    )
    require(
        read_candidate_bytes(checker_path) == expected,
        "certified-SxPID2 claim checker differs from its exact two-digest rebind",
    )


def validate_foundational_pdf_lake_preflight() -> None:
    relative = "scripts/check-foundational-sxpid-audit-pdf.sh"
    expected = git_blob_at(CORRECTIVE_PARENT, relative)
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm "
            b"chktex lacheck python3)\n"
        ),
        (
            b"commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm "
            b"chktex lacheck lake python3)\n"
        ),
        label="foundational PDF lake preflight",
    )
    require(
        read_candidate_bytes(relative) == expected,
        "foundational-paper checker differs from the exact lake-preflight transform",
    )


def validate_package_archive_corrective_firewall() -> None:
    stats_path = "crates/pid-core/src/stats.rs"
    archive_script_path = "scripts/verify-package-archives.sh"
    snapshot_path = (
        "crates/pid-core/tests/fixtures/"
        "generate-ksg-local-arithmetic-oracle.py.snapshot"
    )
    generator_path = "scripts/generate-ksg-local-arithmetic-oracle.py"
    stats = read_candidate_bytes(stats_path)
    snapshot = read_candidate_bytes(snapshot_path)
    canonical_generator = git_blob_at(CURRENT_ANCHOR, generator_path)
    require(
        hashlib.sha256(stats).hexdigest() == PACKAGE_STATS_SHA256,
        "package corrective stats.rs differs from its manually reviewed full blob",
    )
    require(
        hashlib.sha256(canonical_generator).hexdigest()
        == PACKAGE_GENERATOR_SHA256,
        "af509 canonical KSG generator differs from its reviewed digest",
    )
    require(
        read_candidate_bytes(generator_path) == canonical_generator,
        "canonical KSG generator changed in the corrective phase",
    )
    require(
        snapshot == canonical_generator,
        "packaged KSG generator snapshot differs from the exact af509 source bytes",
    )
    archive_script = read_candidate_bytes(archive_script_path)
    require(
        hashlib.sha256(archive_script).hexdigest()
        == PACKAGE_ARCHIVE_SCRIPT_SHA256,
        "package archive verifier differs from its manually reviewed full blob",
    )
    try:
        archive_script_text = archive_script.decode("utf-8")
        stats_text = stats.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "package corrective source is not UTF-8"
        ) from error
    for token, expected_count, label in (
        (
            "packaged_ksg_generator_snapshot_matches_workspace_source_when_available",
            1,
            "exact extracted-package test name",
        ),
        ("--exact", 1, "exact libtest filter"),
        ("--color never", 1, "deterministic libtest color"),
        ("running 1 test", 1, "one-test receipt"),
        ("test $archive_test_name ... ok", 1, "named-test receipt"),
        (
            "^test result: ok\\. 1 passed; 0 failed; 0 ignored; "
            "0 measured; [0-9]+ filtered out; finished in .+s$",
            1,
            "exact one-pass summary parser",
        ),
        ("absent-workspace branch", 1, "absent-generator precondition"),
    ):
        require(
            archive_script_text.count(token) == expected_count,
            f"package archive verifier changed {label}",
        )
    for token, label in (
        ("struct CargoPackageContext", "typed package-context marker"),
        (
            "cargo_package_context_rejects_duplicate_path_bindings",
            "duplicate package-context binding control",
        ),
        (
            "serde_json::from_slice::<CargoPackageContext>(ambiguous).is_err()",
            "duplicate marker rejection",
        ),
    ):
        require(
            stats_text.count(token) == 1,
            f"package stats corrective changed {label}",
        )


def validate_ecosystem_corrective_firewall() -> None:
    catalog_digest = hashlib.sha256(
        read_candidate_bytes("method-catalog.json")
    ).hexdigest()
    require(
        catalog_digest == CURRENT_METHOD_CATALOG_SHA256,
        "current method catalog differs from the manually reviewed corrective digest",
    )
    old = HISTORICAL_ECOSYSTEM_METHOD_CATALOG_SHA256.encode("ascii")
    new = CURRENT_METHOD_CATALOG_SHA256.encode("ascii")
    for relative in (
        "ECOSYSTEM_CAPABILITIES.md",
        "ecosystem-capabilities.json",
        "scripts/check-ecosystem-capabilities.py",
    ):
        historical = git_blob_at(M1A_SCIENTIFIC_COMMIT, relative)
        require(
            historical.count(old) == 1 and new not in historical,
            f"{relative}@dc7 lacks the unique historical catalog binding",
        )
        expected = historical.replace(old, new, 1)
        corrective_parent = git_blob_at(CORRECTIVE_PARENT, relative)
        require(
            corrective_parent == expected,
            f"{relative}@af509 differs from the exact one-digest dc7 transform",
        )
        require(
            read_candidate_bytes(relative) == corrective_parent,
            f"{relative} changed after the exact af509 ecosystem transform",
        )


def sanitize_rust(source: str) -> str:
    output = list(source)
    length = len(source)
    cursor = 0

    def blank(start: int, end: int) -> None:
        for index in range(start, end):
            if output[index] != "\n":
                output[index] = " "

    while cursor < length:
        if source.startswith("//", cursor):
            end = source.find("\n", cursor + 2)
            end = length if end < 0 else end
            blank(cursor, end)
            cursor = end
            continue
        if source.startswith("/*", cursor):
            start = cursor
            depth = 1
            cursor += 2
            while cursor < length and depth:
                if source.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif source.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            require(depth == 0, "Rust source contains an unterminated block comment")
            blank(start, cursor)
            continue
        raw_match = re.match(r'(?:br|r)(#{0,255})"', source[cursor:])
        if raw_match is not None:
            start = cursor
            hashes = raw_match.group(1)
            cursor += raw_match.end()
            terminator = '"' + hashes
            end = source.find(terminator, cursor)
            require(end >= 0, "Rust source contains an unterminated raw string")
            cursor = end + len(terminator)
            blank(start, cursor)
            continue
        if source[cursor] == '"' or source.startswith('b"', cursor):
            start = cursor
            if source[cursor] == "b":
                cursor += 1
            cursor += 1
            escaped = False
            while cursor < length:
                character = source[cursor]
                cursor += 1
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    break
            else:
                raise PhaseIsolationError("Rust source contains an unterminated string")
            blank(start, cursor)
            continue
        cursor += 1
    return "".join(output)


def validate_parallel_semantics() -> None:
    relative = "crates/pid-core/tests/parallel_bit_identity.rs"
    raw = read_candidate_bytes(relative)
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{relative}: non-UTF-8 Rust source") from error
    expected_gate = '#![cfg(feature = "experimental-pipelines")]'
    require(
        source.startswith(expected_gate + "\n\n"),
        "parallel bit-identity test has a zero-test-capable crate gate",
    )
    require(
        '#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]'
        not in source,
        "parallel bit-identity test restored the false-zero serial gate",
    )
    sanitized = sanitize_rust(source)
    conditional_attributes = tuple(
        re.findall(
            r"#\s*(!?)\s*\[\s*(cfg(?:_attr)?|ignore)\b",
            sanitized,
        )
    )
    require(
        conditional_attributes == (("!", "cfg"),),
        "parallel bit-identity conditional/ignore attribute inventory changed",
    )
    require(
        not re.search(r"\bcfg\s*!\s*\(", sanitized),
        "parallel bit-identity target contains a runtime cfg! gate",
    )
    require(
        not re.search(r"\breturn\b", sanitized),
        "parallel bit-identity target contains an early-return bypass",
    )

    observed_constants: dict[str, list[int]] = {}
    for match in re.finditer(
        r"(?m)^\s*const\s+([A-Z][A-Z0-9_]*)\s*:\s*u64\s*=\s*([0-9_]+)\s*;",
        sanitized,
    ):
        observed_constants.setdefault(match.group(1), []).append(
            int(match.group(2).replace("_", ""))
        )
    for name, expected in EXPECTED_PARALLEL_U64_CONSTANTS.items():
        require(
            observed_constants.get(name) == [expected],
            f"parallel bit-identity constant {name} is not the unique KSG-only value",
        )
    require(
        observed_constants.get("PID2_SYN_BITS") != [FORBIDDEN_PID2_SYN_BITS],
        "later PID2 represented-sum synergy bits contaminated the KSG phase",
    )

    tests = tuple(
        sorted(
            re.findall(
                r"(?m)^\s*#\s*\[\s*test\s*\]\s*\n\s*fn\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                sanitized,
            )
        )
    )
    require(
        tests == EXPECTED_PARALLEL_TESTS,
        "parallel bit-identity test inventory no longer proves 12 nonzero serial tests",
    )


def validate_stats_firewall() -> None:
    relative = "crates/pid-core/src/stats.rs"
    try:
        source = read_candidate_bytes(relative).decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{relative}: non-UTF-8 Rust source") from error
    sanitized = sanitize_rust(source)
    for token in (
        "FINITE_SUM_LIMBS",
        "exact_binary64_sum",
        "round_finite_sum",
    ):
        require(
            not re.search(rf"\b{re.escape(token)}\b", sanitized),
            f"stats.rs contains forbidden later-wave exact-sum token {token}",
        )


def validate_release_firewall() -> None:
    relative = "release-scope-1.0.json"
    raw = read_candidate_bytes(relative)
    scope = canonical_json_from_bytes(raw, label=relative)
    require(isinstance(scope, dict), "release scope root must be an object")
    families = scope.get("families")
    require(
        isinstance(families, list) and len(families) == 35,
        "release scope must retain exactly 35 family objects",
    )
    by_id: dict[str, dict[str, Any]] = {}
    revisions: list[str] = []
    for index, family in enumerate(families):
        require(isinstance(family, dict), f"release family {index} must be an object")
        family_id = family.get("id")
        revision = family.get("estimator_revision")
        require(
            isinstance(family_id, str)
            and family_id
            and family_id not in by_id
            and isinstance(revision, str)
            and revision,
            f"release family {index} has invalid typed identity/revision",
        )
        by_id[family_id] = family
        revisions.append(revision)
    for family_id, expected in EXPECTED_RELEASE_REVISIONS.items():
        require(family_id in by_id, f"release family {family_id!r} is missing")
        require(
            by_id[family_id]["estimator_revision"] == expected,
            f"release family {family_id!r} is not at the KSG-only bridge revision",
        )
    for revision in revisions:
        lower = revision.lower()
        require(
            revision not in FORBIDDEN_COMBINED_RELEASE_REVISIONS
            and "represented-input" not in lower
            and "represented_input" not in lower
            and "exact-synergy-sum" not in lower,
            f"release scope contains later combined revision {revision!r}",
        )

    markdown = read_candidate_bytes("RELEASE_SCOPE_1_0.md")
    try:
        markdown_text = markdown.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError("RELEASE_SCOPE_1_0.md is not UTF-8") from error
    for forbidden in FORBIDDEN_COMBINED_RELEASE_REVISIONS:
        require(
            forbidden not in markdown_text,
            "rendered release scope contains a later combined revision",
        )
    for expected in EXPECTED_RELEASE_REVISIONS.values():
        require(
            markdown_text.count(expected) == 1,
            f"rendered release scope does not uniquely contain {expected!r}",
        )


def validate_identity_firewall() -> None:
    relative = "crates/pid-core/identity/software-identity-reference-v1.json"
    candidate = canonical_json_from_bytes(
        read_candidate_bytes(relative), label=relative
    )
    baseline = canonical_json_from_bytes(
        git_blob_at(SCIENTIFIC_BASELINE, relative),
        label=f"{relative}@scientific-baseline",
    )
    require(
        isinstance(candidate, dict) and isinstance(baseline, dict),
        "software identity roots must be objects",
    )
    candidate_artifacts = candidate.get("reference_artifacts")
    baseline_artifacts = baseline.get("reference_artifacts")
    require(
        isinstance(candidate_artifacts, list)
        and isinstance(baseline_artifacts, list)
        and len(candidate_artifacts) == len(baseline_artifacts) == 2,
        "software identity must retain exactly two reference artifacts",
    )
    normalized = json.loads(json.dumps(candidate))
    expected_digests = {
        "method_catalog": hashlib.sha256(
            read_candidate_bytes("method-catalog.json")
        ).hexdigest(),
        "proposed_release_scope": hashlib.sha256(
            read_candidate_bytes("release-scope-1.0.json")
        ).hexdigest(),
    }
    for index, (actual, historical) in enumerate(
        zip(candidate_artifacts, baseline_artifacts, strict=True)
    ):
        require(
            isinstance(actual, dict) and isinstance(historical, dict),
            f"software identity artifact {index} must be an object",
        )
        kind = actual.get("kind")
        require(
            isinstance(kind, str) and kind in expected_digests,
            f"software identity artifact {index} has an unauthorized kind",
        )
        require(
            actual.get("canonical_json_sha256") == expected_digests[kind],
            f"software identity artifact {kind!r} does not bind current canonical bytes",
        )
        normalized["reference_artifacts"][index]["canonical_json_sha256"] = (
            historical.get("canonical_json_sha256")
        )
    require(
        normalized == baseline,
        "software identity changed outside the two authorized forensic digests",
    )


def validate_changed_path_firewall(paths: Iterable[str]) -> None:
    for path in paths:
        lower = path.lower()
        require(
            path not in FORBIDDEN_EXACT_CHANGED_PATHS,
            f"forbidden later-wave path entered KSG phase: {path}",
        )
        require(
            not any(
                path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PATH_PREFIXES
            ),
            f"forbidden later-wave path prefix entered KSG phase: {path}",
        )
        require(
            not any(fragment in lower for fragment in FORBIDDEN_CHANGED_PATH_FRAGMENTS),
            f"forbidden later-wave path token entered KSG phase: {path}",
        )
        if lower.endswith((".pdf", ".tex")):
            require(
                path in CORRECTIVE_PUBLICATION_PATHS,
                f"unrelated PDF/TeX path entered KSG phase: {path}",
            )
        if path.startswith("audit/formal/"):
            require(
                path.startswith("audit/formal/lean-ksg-harmonic/")
                or path.startswith("audit/formal/z3-ksg-harmonic/")
                or path in CORRECTIVE_PUBLICATION_PATHS,
                f"unrelated formal path entered KSG phase: {path}",
            )


def validate_checker_source_model() -> None:
    try:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SCRIPT_PATH))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise PhaseIsolationError(
            f"cannot inspect checker source model: {error}"
        ) from error
    assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    require(
        not assert_nodes,
        "checker source contains an optimization-removable assert statement",
    )
    require(
        tuple(sorted(EXPECTED_CHANGED_PATHS)) == EXPECTED_CHANGED_PATHS
        and len(EXPECTED_CHANGED_PATHS) == len(set(EXPECTED_CHANGED_PATHS)),
        "generated changed-path allowlist is not sorted and duplicate-free",
    )
    require(
        MAX_POST_ANCHOR_COMMITS == 1,
        "post-anchor commit bound is not exactly one direct child",
    )
    require(
        tuple(sorted(BOUND_ALLOWED_PATHS)) == BOUND_ALLOWED_PATHS
        and len(BOUND_ALLOWED_PATHS) == len(set(BOUND_ALLOWED_PATHS)),
        "reviewed full-blob path inventory is not sorted and duplicate-free",
    )
    require(
        SELF_UNHASHED_PATHS
        == frozenset(
            {
                "scripts/check-ksg-phase-isolation-self-test.py",
                "scripts/check-ksg-phase-isolation.py",
            }
        ),
        "cyclic self-unhashed inventory changed",
    )
    phase_functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_phase"
    ]
    require(
        len(phase_functions) == 1, "checker does not uniquely define validate_phase"
    )
    critical_names = set(EXPECTED_CRITICAL_GATE_SEQUENCE)

    def direct_statement_call(statement: ast.stmt) -> str | None:
        value: ast.expr | None = None
        if isinstance(statement, ast.Expr):
            value = statement.value
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in critical_names
        ):
            return value.func.id
        return None

    observed_direct = tuple(
        name
        for statement in phase_functions[0].body
        if (name := direct_statement_call(statement)) is not None
    )
    require(
        observed_direct == EXPECTED_CRITICAL_GATE_SEQUENCE,
        "checker direct top-level critical gate sequence changed",
    )
    observed_recursive = [
        node.func.id
        for node in ast.walk(phase_functions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in critical_names
    ]
    for critical in critical_names:
        require(
            observed_recursive.count(critical)
            == EXPECTED_CRITICAL_GATE_SEQUENCE.count(critical),
            f"checker recursive critical gate inventory changed: {critical}",
        )


def validate_effective_attributes(paths: Iterable[str]) -> None:
    ordered = tuple(sorted(paths))
    if not ordered:
        return
    payload = b"".join(path.encode("utf-8") + b"\0" for path in ordered)
    process = git_process(
        "check-attr",
        "-z",
        "--stdin",
        "filter",
        "working-tree-encoding",
        input_bytes=payload,
    )
    fields = process.stdout.split(b"\0")
    if fields and not fields[-1]:
        fields.pop()
    require(
        len(fields) == len(ordered) * 2 * 3,
        "cannot parse effective Git attributes for candidate delta",
    )
    for index in range(0, len(fields), 3):
        path = canonical_relative_path(fields[index], label="Git attribute path")
        attribute = fields[index + 1].decode("ascii", errors="strict")
        value = fields[index + 2].decode("utf-8", errors="strict")
        require(
            value == "unspecified",
            f"{path!r}: effective {attribute} attribute is forbidden ({value!r})",
        )


def current_facts(
    baseline: dict[str, GitEntry],
    anchor: dict[str, GitEntry],
    snapshot: CandidateSnapshot,
    context: RepositoryContext,
) -> dict[str, Any]:
    actual_changed = changed_paths(baseline, snapshot.entries)
    anchor_delta = classified_delta(anchor, snapshot.entries)
    protected = tuple(sorted(set(baseline).difference(actual_changed)))
    bound: dict[str, list[str]] = {}
    for path in BOUND_ALLOWED_PATHS:
        entry = snapshot.entries.get(path)
        require(entry is not None, f"reviewed full-blob path is missing: {path}")
        bound[path] = [entry.mode, entry.sha256]
    return {
        "allowlist_sha256": allowlist_digest(actual_changed),
        "baseline_path_count": len(baseline),
        "bound_allowed_blobs": bound,
        "anchor_delta": [
            {"path": path, "status": status_value}
            for path, status_value in anchor_delta
        ],
        "anchor_delta_path_count": len(anchor_delta),
        "changed_paths": list(actual_changed),
        "changed_projection_sha256": changed_projection(
            baseline, snapshot.entries, actual_changed
        ),
        "current_anchor": CURRENT_ANCHOR,
        "current_anchor_tree": CURRENT_ANCHOR_TREE,
        "current_head": snapshot.head,
        "diagnostic_only": True,
        "git_tcb": {
            "executable": context.git_binary.executable.path,
            "executable_sha256": context.git_binary.executable.sha256,
            "version": context.git_binary.version,
        },
        "git_context": {
            "common_git_dir": context.common_git_dir,
            "git_dir": context.git_dir,
            "info_attributes_absent": context.info_attributes_absent,
            "local_config_semantics_sha256": (context.local_config_semantics_sha256),
            "local_config_sha256": context.local_config.sha256,
            "replacement_refs_sha256": context.replacement_refs_sha256,
            "worktree_config_absent": context.worktree_config_absent,
        },
        "lifecycle": (
            "precommit-worktree"
            if snapshot.head == CURRENT_ANCHOR
            else "committed-descendant"
        ),
        "phase_path_policy": PHASE_PATH_POLICY,
        "phase_path_policy_sha256": hashlib.sha256(
            read_candidate_bytes(PHASE_PATH_POLICY)
        ).hexdigest(),
        "precommit_tracked_modifications": list(snapshot.tracked_modifications),
        "precommit_untracked_deliverables": list(snapshot.untracked),
        "protected_path_count": len(protected),
        "protected_projection_sha256": path_projection(baseline, protected),
        "schema": "pid-rs/ksg-phase-current-facts",
        "schema_revision": 1,
        "self_unhashed_paths": sorted(SELF_UNHASHED_PATHS),
    }


def render_tuple(name: str, values: list[str]) -> list[str]:
    lines = [f"{name} = ("]
    lines.extend(f"    {value!r}," for value in values)
    lines.append(")")
    return lines


def render_generated_block(facts: dict[str, Any]) -> str:
    lines = ["# BEGIN GENERATED PHASE FACTS"]
    lines.extend(
        render_tuple("EXPECTED_CHANGED_PATHS: tuple[str, ...]", facts["changed_paths"])
    )
    lines.extend(
        render_tuple(
            "EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS: tuple[str, ...]",
            facts["precommit_tracked_modifications"],
        )
    )
    lines.extend(
        render_tuple(
            "EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES: tuple[str, ...]",
            facts["precommit_untracked_deliverables"],
        )
    )
    lines.append(f"EXPECTED_ALLOWLIST_SHA256 = {facts['allowlist_sha256']!r}")
    lines.append(
        f"EXPECTED_CHANGED_PROJECTION_SHA256 = {facts['changed_projection_sha256']!r}"
    )
    lines.append(
        "EXPECTED_PROTECTED_PROJECTION_SHA256 = "
        f"{facts['protected_projection_sha256']!r}"
    )
    lines.append(f"EXPECTED_BASELINE_PATH_COUNT = {facts['baseline_path_count']}")
    lines.append(f"EXPECTED_PROTECTED_PATH_COUNT = {facts['protected_path_count']}")
    lines.append("EXPECTED_BOUND_ALLOWED_BLOBS: dict[str, tuple[str, str]] = {")
    for path, (mode, digest) in facts["bound_allowed_blobs"].items():
        lines.append(f"    {path!r}: ({mode!r}, {digest!r}),")
    lines.append("}")
    lines.append("# END GENERATED PHASE FACTS")
    return "\n".join(lines)


def validate_phase(
    *,
    expected_candidate_tree: str | None,
    checkpoint_commit: str | None,
) -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:
    validate_checker_source_model()
    repository_context = validate_repository_context()
    snapshot = collect_candidate_snapshot()
    validate_commit_envelope(snapshot.head)
    baseline = hydrate_tree(parse_tree(SCIENTIFIC_BASELINE))
    anchor = hydrate_tree(parse_tree(CURRENT_ANCHOR))
    policy_entries = validate_phase_path_policy(snapshot, anchor)
    custody = validate_staged_tree_custody(
        snapshot,
        expected_candidate_tree,
        checkpoint_commit,
    )
    if snapshot.head != CURRENT_ANCHOR:
        require(
            expected_candidate_tree is not None and checkpoint_commit == snapshot.head,
            (
                "committed lifecycle requires --expected-candidate-tree and "
                "--checkpoint-commit equal to exact HEAD"
            ),
        )
    delivery = hydrate_tree(parse_tree(DELIVERY_PARENT))
    require(
        len(baseline) == EXPECTED_BASELINE_PATH_COUNT,
        "scientific baseline path count changed",
    )
    tracked_ignore_sources = tuple(
        path
        for path in sorted(snapshot.entries)
        if path == ".gitignore" or path.endswith("/.gitignore")
    )
    require(
        tracked_ignore_sources == (".gitignore",),
        "candidate must contain exactly one root .gitignore visibility source",
    )

    delivery_changed = changed_paths(baseline, delivery)
    require(
        delivery_changed == tuple(sorted(DELIVERY_CHANGED_BLOBS)),
        "delivery commit changed-path envelope mismatch",
    )
    for path, (mode, digest) in DELIVERY_CHANGED_BLOBS.items():
        entry = delivery.get(path)
        require(
            entry is not None and (entry.mode, entry.sha256) == (mode, digest),
            f"delivery commit blob pin mismatch: {path}",
        )

    actual_changed = changed_paths(baseline, snapshot.entries)
    require(
        allowlist_digest(EXPECTED_CHANGED_PATHS) == EXPECTED_ALLOWLIST_SHA256,
        "reviewed allowlist digest does not match checker constants",
    )
    require(
        actual_changed == EXPECTED_CHANGED_PATHS,
        "candidate changed-path set differs from the exact KSG allowlist",
    )
    require(
        changed_projection(baseline, snapshot.entries, actual_changed)
        == EXPECTED_CHANGED_PROJECTION_SHA256,
        "candidate changed-byte projection digest mismatch",
    )

    protected = tuple(sorted(set(baseline).difference(EXPECTED_CHANGED_PATHS)))
    require(
        len(protected) == EXPECTED_PROTECTED_PATH_COUNT,
        "protected path count changed",
    )
    require(
        path_projection(baseline, protected) == EXPECTED_PROTECTED_PROJECTION_SHA256,
        "scientific-baseline protected projection pin mismatch",
    )
    for path in protected:
        left = baseline[path]
        right = snapshot.entries.get(path)
        require(
            right is not None
            and (right.mode, right.kind, right.sha256)
            == (left.mode, left.kind, left.sha256),
            f"protected path mode/type/blob changed: {path}",
        )
    for path, (mode, digest) in PINNED_PROTECTED_BLOBS.items():
        baseline_entry = baseline.get(path)
        candidate_entry = snapshot.entries.get(path)
        require(
            baseline_entry is not None
            and (baseline_entry.mode, baseline_entry.sha256) == (mode, digest),
            f"pinned protected baseline fact mismatch: {path}",
        )
        require(
            candidate_entry is not None
            and (candidate_entry.mode, candidate_entry.sha256) == (mode, digest),
            f"pinned protected candidate blob changed: {path}",
        )

    require(
        set(EXPECTED_BOUND_ALLOWED_BLOBS) == set(BOUND_ALLOWED_PATHS),
        "reviewed full-blob pin inventory does not match its path inventory",
    )
    for path, expected in EXPECTED_BOUND_ALLOWED_BLOBS.items():
        entry = snapshot.entries.get(path)
        require(
            entry is not None and (entry.mode, entry.sha256) == expected,
            f"reviewed full candidate blob changed: {path}",
        )

    if snapshot.head == CURRENT_ANCHOR:
        lifecycle = "precommit-worktree"
        require(
            snapshot.tracked_modifications == EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS,
            "precommit tracked-modification partition changed",
        )
        require(
            snapshot.untracked == EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES,
            "precommit untracked-deliverable partition changed",
        )
    else:
        lifecycle = "committed-descendant"
        require(
            not snapshot.tracked_modifications and not snapshot.untracked,
            "committed phase requires a clean tracked/untracked worktree",
        )

    validate_effective_attributes(entry.path for entry in policy_entries)
    validate_changed_path_firewall(actual_changed)
    validate_public_ci_failure_evidence()
    validate_ci_corrective_firewall()
    validate_claim_checker_workflow_rebind()
    validate_foundational_pdf_lake_preflight()
    validate_package_archive_corrective_firewall()
    validate_ecosystem_corrective_firewall()
    validate_stats_firewall()
    validate_parallel_semantics()
    validate_release_firewall()
    validate_identity_firewall()

    replay_context = validate_repository_context()
    replay = collect_candidate_snapshot()
    replay_custody = validate_staged_tree_custody(
        replay,
        expected_candidate_tree,
        checkpoint_commit,
    )
    require(
        replay_context == repository_context,
        "Git executable, configuration, metadata, or visibility context changed during replay",
    )
    require(
        replay == snapshot, "candidate filesystem or Git inputs changed during replay"
    )
    require(
        replay_custody == custody, "external staged-tree custody changed during replay"
    )
    return (
        lifecycle,
        len(actual_changed),
        len(protected),
        len(snapshot.tracked_modifications),
        len(snapshot.untracked),
        custody[0],
        repository_context.git_binary,
    )


DESCRIPTION = """\
Validate KSG revision-4 Git phase provenance on the Git-visible candidate
snapshot (HEAD-tracked files plus untracked deliverables not excluded by the
exact protected root .gitignore).

On success this proves only the pinned baseline -> delivery -> formal-anchor
single-parent envelope, the exact reviewed candidate delta, byte/mode/type
identity of protected paths, complete-byte pins for reviewed high-risk paths,
exact anchor/absent -> final-byte monotonicity of every reachable post-anchor
tree, and the bounded KSG-vs-later-wave firewall encoded here.

It does NOT prove arithmetic, formal-statement adequacy, Rust/compiler
conformance, estimator accuracy, support assumptions, PID validity,
statistical calibration, publication quality, remote/push state,
authenticity, trustworthiness of the identified Git executable, or absence of
hash collisions. Every path ignored by the protected root .gitignore,
including credentials, secrets, build products, caches, and editor state, is
outside the candidate snapshot; local info/exclude bytes are deliberately not
an input. No gate may silently depend on an ignored path. The checker and
self-test bytes are intentionally outside the self-stored digest projection.
Use the external tree/commit hooks to bind them to an independently pre-pinned,
separately reviewed staged tree.  A tree computed after checker mutation does
not close the self-reference cut; even pre-pinned custody is not an
authenticity proof.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--emit-current-facts-json",
        action="store_true",
        help=(
            "print canonical diagnostic facts for the current snapshot; this "
            "does not validate the reviewed constants"
        ),
    )
    group.add_argument(
        "--emit-current-facts-python",
        action="store_true",
        help=(
            "print a mechanically replaceable generated-constant block; this "
            "is diagnostic input requiring human review, not validation"
        ),
    )
    parser.add_argument(
        "--expected-candidate-tree",
        metavar="TREE",
        help=(
            "require the complete candidate snapshot, including the two "
            "self-unhashed scripts, to equal this externally created Git tree"
        ),
    )
    parser.add_argument(
        "--checkpoint-commit",
        metavar="COMMIT",
        help=(
            "additionally require this detached checkpoint commit to carry "
            "the supplied candidate tree and be HEAD or an exact child of HEAD"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.emit_current_facts_json or args.emit_current_facts_python:
            validate_checker_source_model()
            context = validate_repository_context()
            snapshot = collect_candidate_snapshot()
            validate_commit_envelope(snapshot.head)
            baseline = hydrate_tree(parse_tree(SCIENTIFIC_BASELINE))
            anchor = hydrate_tree(parse_tree(CURRENT_ANCHOR))
            validate_phase_path_policy(snapshot, anchor)
            validate_staged_tree_custody(
                snapshot,
                args.expected_candidate_tree,
                args.checkpoint_commit,
            )
            facts = current_facts(baseline, anchor, snapshot, context)
            if args.emit_current_facts_json:
                print(json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=True))
            else:
                print(render_generated_block(facts))
            return 0
        (
            lifecycle,
            changed,
            protected,
            tracked,
            untracked,
            candidate_tree,
            git_binary,
        ) = validate_phase(
            expected_candidate_tree=args.expected_candidate_tree,
            checkpoint_commit=args.checkpoint_commit,
        )
    except PhaseIsolationError as error:
        print(f"ERROR: KSG phase isolation: {error}", file=sys.stderr)
        return 1
    print(
        "OK: KSG phase provenance only; "
        f"lifecycle={lifecycle}; changed={changed}; protected={protected}; "
        f"tracked-worktree={tracked}; untracked-deliverables={untracked}; "
        f"baseline={SCIENTIFIC_BASELINE}; delivery={DELIVERY_PARENT}; "
        f"anchor={CURRENT_ANCHOR}; self-unhashed={len(SELF_UNHASHED_PATHS)}; "
        f"candidate-tree={candidate_tree or 'not-requested'}; "
        f"git={git_binary.executable.path}; "
        f"git-sha256={git_binary.executable.sha256}; "
        f"git-version={git_binary.version!r}. "
        "No arithmetic, estimator, PID, statistical, remote, or authenticity "
        "claim is implied."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
