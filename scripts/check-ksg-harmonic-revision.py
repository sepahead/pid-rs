#!/usr/bin/env python3
"""Check the exact and bounded executable evidence for KSG-INTEGER-HARMONIC-001.

The exact Fraction route covers every rectangular-arithmetic tuple through n=16. The binary64
route covers the committed 8,198-cell Decimal corpus and inherits IEEE-754 arithmetic. Its
8-epsilon comparator
first rounds each stored Decimal reference to binary64; the separate directed-enclosure checker
handles error against the exact harmonic rational. Neither route is a universal error bound,
neighbor-search proof, estimator-consistency result, or application-validity claim.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import unicodedata
from fractions import Fraction
from pathlib import Path
from typing import Any

EXPECTED_CASES = 8_198
EXPECTED_EXHAUSTIVE_CASES = 6_920
EXPECTED_STRESS_CASES = 1_278
EXPECTED_STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)
EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_EPSILON_MULTIPLES = 8
EXPECTED_ROUNDED_REFERENCE_MAX_ERROR = (
    EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_EPSILON_MULTIPLES * sys.float_info.epsilon
)
EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_TIES = 40
EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES = 32
ALLOWED_ROUNDED_REFERENCE_MAX_ERROR = (
    EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES * sys.float_info.epsilon
)
EXPECTED_ROUNDED_REFERENCE_FIRST_MAXIMUM = (4_096, 1, 2_048, 2_048)
EXPECTED_FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
EXPECTED_FIXTURE_SCHEMA_REVISION = 2
EXPECTED_GENERATOR_PATH = "scripts/generate-ksg-local-arithmetic-oracle.py"
EXPECTED_GENERATOR_SHA256 = (
    "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
)
EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_FIXTURE_SIDECAR_SHA256 = (
    "fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7"
)
EXACT_ENCLOSURE_CHECKER_RELATIVE_PATH = "scripts/check-ksg-harmonic-exact-enclosure.py"
EXPECTED_EXACT_ENCLOSURE_CHECKER_SHA256 = (
    "b7c4df526703adc3dd8f5f04471b027decb256bfaaaa2d32ff9f918253546468"
)
EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS = 240
EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS = 114
EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 354
EXPECTED_SELECTED_ENDPOINT_POSITIVE_ZEROS = 354
EXPECTED_SELECTED_ENDPOINT_NEGATIVE_ZEROS = 0
EXPECTED_SELECTED_ENDPOINT_NONZEROS = 0
EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 150
EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 0
EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS = 121
EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NEGATIVE_ZEROS = 0
EXPECTED_ENDPOINT_CANCELLATION_RULE = (
    "{nx,ny}={k-1,n-1}; cancel equal symbolic harmonic terms before Decimal evaluation"
)
README_RELATIVE_PATH = "README.md"
REQUIRED_README_KSG_MARKERS = (
    "6,920 exhaustive rectangular-arithmetic outer-box tuples through 16\n"
    "  samples plus 1,278 fixed stress tuples through one million samples.",
    "The outer box is not\n  asserted to equal the runtime unique-shell image.",
)
FORBIDDEN_README_KSG_MARKERS = (
    "6,920 exhaustive feasible tuples",
    "The outer box equals the runtime unique-shell image.",
)

# (unchanged definition revision, superseded estimator revision, active estimator revision).
# Every family here can directly or transitively emit a scalar changed by the integer-harmonic
# KSG arithmetic. Keeping the prior revision in the table gives the mutation suite a precise stale
# state to replay rather than accepting an unconstrained "not old" check.
KSG_RELEASE_REVISIONS = {
    "pid-core.stable.continuous": (
        "ksg1-product-small-ball-v1",
        "strict-unique-shell-report-v3",
        "strict-unique-shell-integer-harmonic-report-v4",
    ),
    "pid-core.experimental.continuous.co-information": (
        "co-information-algebra-v1",
        "ksg-derived-co-information-v1",
        "ksg-derived-co-information-integer-harmonic-v2",
    ),
    "pid-core.experimental.continuous.isx": (
        "common-coordinate-radius-v1",
        "strict-unique-shell-isx-v3",
        "strict-unique-shell-integer-harmonic-isx-v4",
    ),
    "pid-core.experimental.continuous.pid2": (
        "continuous-isx-pid2-algebra-v1",
        "separate-biased-term-pid2-v1",
        "separate-biased-term-pid2-integer-harmonic-v2",
    ),
    "pid-core.experimental.continuous.incomplete-pid3": (
        "incomplete-pid3-availability-v1",
        "equal-ambient-branch-screen-v1",
        "equal-ambient-branch-screen-integer-harmonic-v2",
    ),
    "pid-core.research.raw-ksg": (
        "kraskov-stoegbauer-grassberger-2004-v1",
        "ksg-chebyshev-raw-v1",
        "ksg-chebyshev-integer-harmonic-raw-v2",
    ),
    "pid-core.research.raw-isx": (
        "ehrlich-et-al-2024-isx-intersection-v1",
        "ehrlich-local-knn-raw-v1",
        "ehrlich-local-knn-integer-harmonic-raw-v2",
    ),
    "pid-core.research.raw-co-information": (
        "shannon-co-information-inclusion-exclusion-v1",
        "ksg-co-information-raw-v1",
        "ksg-co-information-integer-harmonic-raw-v2",
    ),
    # The family owns Python migration `compute_pid2`, which combines a heuristic redundancy term
    # with KSG MI inputs changed by this milestone. Standalone Rust heuristic redundancy scalars
    # remain on the excluded non-cancelling general-digamma path and are numerically unchanged.
    "pid-core.research.isx-heuristics": (
        "heuristic-baselines-v1",
        "heuristic-baselines-v1",
        "heuristic-baselines-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.research.mixed-dimension-pid3": (
        "mixed-dimensional-pid3-reference-v1",
        "mixed-dimensional-pid3-reference-v1",
        "mixed-dimensional-pid3-integer-harmonic-reference-v2",
    ),
    "pid-core.research.hyperbolic": (
        "hyperbolic-geometry-v1",
        "lorentz-geometry-safe-rust-v1",
        "lorentz-geometry-and-integer-harmonic-ksg-safe-rust-v2",
    ),
    "pid-core.experimental.hierarchy": (
        "hierarchy-screening-v1",
        "hierarchy-screening-v1",
        "hierarchy-screening-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.experimental.pipelines.pid3-permutation": (
        "pid3-permutation-null-v1",
        "explicit-seed-pid3-permutation-v1",
        "explicit-seed-pid3-permutation-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.experimental.pipelines.pls-selection-and-composition": (
        "pls-selection-composition-v1",
        "deterministic-pls-cv-v1",
        "deterministic-pls-cv-and-integer-harmonic-pid-composition-v2",
    ),
    "pid-core.experimental.pipelines.pid2-screening": (
        "pid2-pair-screen-v1",
        "deterministic-pair-enumeration-v1",
        "deterministic-pair-enumeration-with-integer-harmonic-pid2-v2",
    ),
}

# Every current family outside the KSG migration is a negative control. Exact definition and
# estimator strings make an accidental transitive over-bump fail closed. Later cross-lane
# same-sample additions are bound at their independently reviewed revisions; they are protected
# current objects, never retroactively classified as KSG-affected work.
KSG_PROTECTED_RELEASE_REVISIONS = {
    "pid-core.infrastructure": (
        "pid-core-infrastructure-v2",
        "pid-core-infrastructure-v2",
    ),
    "pid-core.stable.categorical": (
        "makkeh-gutknecht-wibral-2021-empirical-v1",
        "direct-empirical-pmf-mobius-v1",
    ),
    "pid-core.stable.quantized": (
        "fitted-quantized-categorical-sxpid-v1",
        "equal-width-fit-transform-plus-empirical-pmf-v1",
    ),
    "pid-core.stable.imin": (
        "williams-beer-2010-imin-plus-fixed-quantizer-composition-v1",
        "empirical-specific-information-minimum-with-quantized-provenance-v1",
    ),
    "pid-core.stable.preprocessing": (
        "preprocessing-utilities-v1",
        "preprocessing-safe-rust-v1",
    ),
    "pid-core.diagnostics.distance-matrix": (
        "metric-distance-matrix-v1",
        "upper-triangle-exact-v1",
    ),
    "pid-core.diagnostics.geometry": (
        "diagnostic-formulas-v1",
        "diagnostic-safe-rust-v1",
    ),
    "pid-core.diagnostics.invariants": (
        "empirical-shannon-invariants-v1",
        "empirical-count-map-v1",
    ),
    "pid-core.diagnostics.support": (
        "continuous-sample-diagnostics-v1",
        "exact-observation-diagnostics-v1",
    ),
    "pid-core.experimental.continuous.shared-ksg-config": (
        "kraskov-stoegbauer-grassberger-2004-config-v1",
        "ksg-chebyshev-config-v1",
    ),
    "pid-core.experimental.pipelines.block-resampling": (
        "moving-block-bootstrap-v2",
        "explicit-seed-block-bootstrap-v1",
    ),
    "pid-core.experimental.pipelines.logistic-regression": (
        "penalized-logistic-regression-v1",
        "newton-irls-v1",
    ),
    "pid-core.experimental.pipelines.fdr-adjustment": (
        "bh-by-fdr-v1",
        "deterministic-sorted-pvalues-v1",
    ),
    "pid-core.experimental.pipelines.quantized-sxpid-bootstrap": (
        "quantized-sxpid2-block-bootstrap-v2",
        "explicit-seed-quantized-bootstrap-v2",
    ),
    "pid-core.experimental.pipelines.row-bootstrap": (
        "callback-row-bootstrap-v2",
        "separated-schedule-perturbation-streams-v2",
    ),
    "pid-core.experimental.pipelines.permutation-contracts": (
        "permutation-contracts-v1",
        "explicit-seed-permutation-v1",
    ),
    "pid-core.experimental.pipelines.row-permutation": (
        "callback-row-permutation-v1",
        "explicit-seed-row-permutation-v1",
    ),
    "pid-core.experimental.pipelines.gaussian-noise-provenance": (
        "typed-added-gaussian-noise-v1",
        "content-bound-row-major-gaussian-application-v1",
    ),
    "pid-core.experimental.pipelines.jitter-preprocessing": (
        "legacy-seeded-jitter-v1",
        "seeded-jitter-v1",
    ),
    "pid-core.experimental.pipelines.same-sample-quantization": (
        "same-sample-quantization-provenance-v3",
        "not-an-estimator-v1",
    ),
    "pid-core.experimental.pipelines.same-sample-quantized-imin": (
        "williams-beer-imin-evaluation-sample-exact-significand-composition-v2",
        "exact-significand-same-evaluation-sample-plus-empirical-imin-v2",
    ),
    "pid-core.experimental.pipelines.same-sample-quantized-sxpid": (
        "mgw-shared-exclusions-evaluation-sample-exact-significand-composition-v2",
        "exact-significand-same-evaluation-sample-plus-empirical-mgw-sxpid-v2",
    ),
}
KSG_AFFECTED_RELEASE_FAMILIES_SHA256 = (
    "a0c7f7f625e787a86d08435d8eb1fbcea0c045813efd774215b58c59a73271f2"
)
KSG_PROTECTED_RELEASE_FAMILIES_SHA256 = (
    "6daed366b2e03b4df211897633bcc97f20460fc93f2a6992070170601706a6f1"
)
KSG_PROTECTED_RELEASE_METADATA_SHA256 = (
    "24e2f99f8e11d2e2270c77e92f9aa8b4bddecea24574fa39d8980e8616141d19"
)

KSG_CATALOG_METHOD_IDS = (
    "co-information.continuous-raw",
    "co-information.continuous-report",
    "mutual-information.hyperbolic-ksg",
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "mutual-information.ksg1-sensitivity-trajectories",
    "pid.continuous-pid2",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "pipelines.hierarchy-screening",
    "pipelines.pid2-screening",
    "pipelines.pid3-permutation",
    "pipelines.pls-pid-composition",
    "shannon-invariants.continuous-ksg-composition",
    "shared-exclusions.continuous-heuristics",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
    "software.python-experimental-migration-bindings",
    "software.python-v1-bindings",
    "validation.exp0",
)
KSG_CATALOG_ROOT_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
)
KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS = ("mutual-information.ksg1-shared-config",)
KSG_FORMAL_CATALOG_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
)
KSG_REQUIRED_CATALOG_EVIDENCE = (
    "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/"
    "decimal-reference-metric-conflation-v4.md",
    "scripts/check-ksg-harmonic-exact-enclosure-self-test.py",
    "scripts/check-ksg-harmonic-exact-enclosure.py",
    "scripts/check-ksg-harmonic-revision-self-test.py",
    "scripts/check-ksg-harmonic-revision.py",
)
KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE = (
    "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json",
    "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean",
    "audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    "ksg-harmonic-modular-certificate-v1.json",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    "ksg-harmonic-modular-certificate-v1.json.sha256",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-replay-lean-4.33.0-2026-08-11.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json",
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md",
    "scripts/check-ksg-harmonic-modular-certificate-self-test.py",
    "scripts/check-ksg-harmonic-modular-certificate.py",
    "scripts/check-lean-ksg-integer-harmonic-self-test.py",
    "scripts/check-lean-ksg-integer-harmonic.py",
    "scripts/check-z3-ksg-integer-harmonic-self-test.py",
    "scripts/check-z3-ksg-integer-harmonic.py",
    "scripts/generate-ksg-harmonic-modular-certificate.py",
)
KSG_AFFECTED_CATALOG_METHODS_SHA256 = (
    "9887b31cbc1e89dcf7117503e81baa5ee8575d3514033d0500c1c6f4e5680e5a"
)
KSG_REVIEWED_PROTECTED_CATALOG_METHODS_SHA256 = (
    "a2a09646dd8d2bc1ec03817e086482f6432cd946a9d55d7fd29aec83d189898e"
)
KSG_UNCHANGED_PROTECTED_CATALOG_METHODS_SHA256 = (
    "110867adfb4d9c35795b45f39f9d12a5316304647dae713b0e3b66cdafa08a84"
)
KSG_REVIEWED_CROSS_LANE_CATALOG_METHOD_IDS = (
    "pid.fitted-quantized-imin",
    "pid.same-sample-quantized-imin",
    "pipelines.quantized-sxpid-bootstrap",
    "pipelines.same-sample-quantization",
    "quantization.same-sample-exact-significand",
    "shared-exclusions.same-sample-quantized",
    "validation.certified-sxpid2-reference",
)
KSG_REVIEWED_CROSS_LANE_CATALOG_METHODS_SHA256 = (
    "08aba448e452bfbe848f5e304e995e20845abc4372ba7e9f022a28d5e02c6b4a"
)
# Later, independently reviewed records stay outside the KSG reverse closure. Their exact current
# projections include the versioned Lean 4.33 evidence-path migration; this classification records
# that chronology without treating those methods as KSG evidence or weakening their hash pins.
KSG_POST_REVISION_PROTECTED_CATALOG_METHOD_IDS = (
    "shared-exclusions.categorical",
    "validation.dependency-color-sxpid-concentration",
    "validation.finite-alphabet-plugin-convergence",
    "validation.foundational-shared-exclusions-audit",
    "validation.support-change-tolerant-averaged-sxpid-continuity",
    "validation.two-source-sxpid-count-atom-bridge",
)
KSG_POST_REVISION_PROTECTED_CATALOG_METHODS_SHA256 = (
    "b35cea46676914e1529de5ae4e1e8f17896145e451a9a00ed3d24306d484d3fe"
)
KSG_CURRENT_PROTECTED_CATALOG_METHODS_SHA256 = (
    "18087fc97ae12709828b86e70b401dd388007b67bf13a761788c1dcba89c74d1"
)
KSG_PROTECTED_CATALOG_REFERENCES_SHA256 = (
    "dfa02422f456880a5c03830ed730db835d45211cd07558738f02afce7f81f654"
)
KSG_PROTECTED_CATALOG_METADATA_SHA256 = (
    "14cc8ececb23de3367f0629e85cb105c3a674f7499fdc09946bdcae9932ad6fb"
)
KSG_FORBIDDEN_CATALOG_TOKENS = (
    "PID2-REPRESENTED-SUM-001",
    "IMIN-TIE-SWAP-001",
    "exact_binary64_sum",
    "represented-input-exact",
)

ACTIVE_PACKET_RELATIVE_PATH = "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"

EXPECTED_ACTIVE_PACKET_SHA256 = (
    "35ea79ed4cdf46cfd68105cb6385cc8d37b2c256130b40ab616b9211c7143f32"
)

PRECLOSURE_PACKET_STAGE = "preclosure_core_manifest_must_be_regenerated_at_m1c"
FINAL_PACKET_STAGE = "immutable_integration_go_m1c"
EXPECTED_PACKET_STAGE = PRECLOSURE_PACKET_STAGE
EXPECTED_PACKET_STATUS = "integration_no_go"

EXPECTED_PACKET_PATHS = (
    "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json",
    "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean",
    "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean",
    "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean",
    "audit/formal/lean/lake-manifest.json",
    "audit/formal/lean/lakefile.toml",
    "audit/formal/lean/lean-toolchain",
    "audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/call-site-map.md",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json.sha256",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/decision-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/decision.md",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json",
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/formal-replay-lean-4.33.0-2026-08-11.md",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/obligations.md",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index.md",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v2.md",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v3.md",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md",
    "claims/KSG-INTEGER-HARMONIC-001/routes.md",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256",
    "scripts/check-ksg-harmonic-exact-enclosure-self-test.py",
    "scripts/check-ksg-harmonic-exact-enclosure.py",
    "scripts/check-ksg-harmonic-modular-certificate-self-test.py",
    "scripts/check-ksg-harmonic-modular-certificate.py",
    "scripts/check-lean-ksg-integer-harmonic-self-test.py",
    "scripts/check-lean-ksg-integer-harmonic.py",
    "scripts/check-z3-ksg-integer-harmonic-self-test.py",
    "scripts/check-z3-ksg-integer-harmonic.py",
    "scripts/generate-ksg-harmonic-modular-certificate.py",
    "scripts/generate-ksg-local-arithmetic-oracle.py",
)
EXPECTED_HISTORICAL_HASHES = {
    "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md": "e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md": "d17e8eed0f3944d2d4a8dd0e67cf44ffc7ddfb1a5d2194269d17a4003a9f6fa0",
    "claims/KSG-INTEGER-HARMONIC-001/call-site-map.md": "048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md": "726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md": "2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md": "457f55ef444b931cefa05d0dcb06d084cd51f510810080a80a30f0b9f5d59071",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md": "0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md": "8d4f289d5b1ee9a10995bd8ae1bc086ae276812d1e09005c9006a730adab0949",
    "claims/KSG-INTEGER-HARMONIC-001/decision-v2.md": "540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26",
    "claims/KSG-INTEGER-HARMONIC-001/decision.md": "0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md": "6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md": "f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc",
    "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md": "eeb7b369792ebc882428829ccc62cb472ab5e3b137f1231cbc7f722de759321b",
    "claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md": "ff4ea026728be041c01b97b91ddadfabc8e619f1ce292ccf131637c15e2dcfdb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md": "d5e2f5bf6fc4f05a298d388ebecbf0bfcbb256c0b1e1e26de8a27d8f059782cb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md": "b6d886b5dc75c2dd1ae0e12ef4a3a9c842b68093fb541abe45dab19111970c53",
    "claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md": "565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071",
    "claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md": "2665ff3e7ddd0c4b845882267a6c6c2d2b9e96c3840f01a10e403300b5dc640c",
    "claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md": "0853760aa6e7e0952a5f4f1f945e05c9328863ef544a576bada44da033f94e5f",
    "claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md": "87ea622cf0cea2827cc7637315c4f76e29d53b82a5479c37afd9d20841fc6343",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md": "1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md": "062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": "322c3f633d0e1316a401e92b10afb541ee82cb9ba94afef88f4a2937c934b6ff",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md": "83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md": "e0f7badb2a5f929c3d91fd7193d2ab3fe4e9cf7a2ae83995b7465c2bae2a7724",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md": "2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md": "a2d29661b07a4b855c97ec6fb2e371bb4f422a1bdb3e24f5291a3022b49e889d",
    "claims/KSG-INTEGER-HARMONIC-001/obligations.md": "b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md": "b3c5c83cdb883acbc7cfc750cd97bab1d6e3d3bd3eb70ec8aabd840897cc4c15",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md": "1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md": "c8100a713bb5f557396398972346d081fe1f1ac3bfc67b749257a88b3f82c855",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v2.md": "5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v3.md": "ed1f9324eb537eb4e752d7b147942562290ab9f6aeeab453fa91f7d73c80d9bc",
    "claims/KSG-INTEGER-HARMONIC-001/routes.md": "23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256",
}

EXPECTED_CLAIM_FACTS = {
    "arithmetic": {
        "coefficient_vector": [1, 1, -1, -1],
        "exact_bound": "-D <= T <= D",
        "exact_term": "T = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)",
        "information_unit": "nats",
        "negative_values_permitted": True,
        "silent_clamping_forbidden": True,
        "typed_analytic_premise": "psi(m) = H_(m-1) - gamma for used positive integers",
    },
    "binary64_corpus": {
        "allowed_finite_corpus_error_epsilon_multiples": 32,
        "canonical_endpoint_negative_zero_count": 0,
        "canonical_endpoint_nonzero_count": 0,
        "canonical_endpoint_positive_zero_count": 354,
        "case_count": 8198,
        "direct_compiled_full_partition_assertion": True,
        "exhaustive_case_count": 6920,
        "naive_prefix_ordinary_left_negative_zero_count": 0,
        "naive_prefix_ordinary_left_nonzero_count": 121,
        "rounded_reference_first_maximum_tuple_n_k_nx_ny": [4096, 1, 2048, 2048],
        "rounded_reference_first_maximum_zero_based_row": 7598,
        "rounded_reference_maximum_error_epsilon_multiples": 8,
        "rounded_reference_maximum_error_is_ulp_claim": False,
        "rounded_reference_maximum_error_measure": "abs(selected_binary64 - "
        "binary64(stored_decimal_text)) in "
        "nats",
        "rounded_reference_maximum_error_tie_count": 40,
        "selected_full_corpus_negative_zero_count": 0,
        "selected_full_corpus_nonzero_count": 7844,
        "selected_full_corpus_positive_zero_count": 354,
        "selected_neumaier_prefix_ordinary_left_negative_zero_count": 0,
        "selected_neumaier_prefix_ordinary_left_nonzero_count": 150,
        "source_swap_bit_asymmetry_count": 0,
        "stress_case_count": 1278,
        "structural_endpoint_count": 354,
        "structural_endpoint_exhaustive_count": 240,
        "structural_endpoint_stress_count": 114,
        "structural_rule_is_frozen_corpus_iff": True,
        "structural_rule_is_universal_iff": False,
    },
    "domains": {
        "exclusive_map": "k-1 <= nx,ny < n; x=nx+1; y=ny+1",
        "inclusive_map": "k <= x,y <= n; pass anchor-inclusive counts directly",
        "inventoried_runtime_argument_outer_box": "n >= 2; 1 <= k < n; k <= x,y <= n",
        "pure_arithmetic_lean_domain": "n >= 1; 1 <= k <= n; k <= x,y <= n",
        "runtime_candidate_constraint": "x+y <= n+k",
        "runtime_candidate_constraint_basis": "conditional finite-set source-shell "
        "union/intersection cardinality for an eligible row with finite positive joint "
        "radius, exact count maps, anchor-inclusive source counts, and strict-radius "
        "predecessor counts",
        "runtime_candidate_lower_bound": "H_(k-1)+H_(n-1)-H_(floor((n+k)/2)-1)-H_(ceil((n+k)/2)-1)",
        "runtime_candidate_status": "conditional_source_lemma_not_revision4_promoted_"
        "project_theorem; stronger_bound_pending_exact_formal_compiled_mutation_"
        "provenance_routes",
        "runtime_shell_image_equals_outer_box": False,
    },
    "exact_rational_enclosure": {
        "binary64_conversion_mismatch_count": 0,
        "decimal_directed_rounding_is_computational_premise": True,
        "exact_comparator_firewall_control_count": 2,
        "exact_difference_comparison_count": 8198,
        "exact_difference_comparator": "exact Fraction(Decimal) subtraction and rational "
        "ordering after canonical finite-Decimal validation",
        "exact_enclosure_checker_sha256": "b7c4df526703adc3dd8f5f04471b027decb256bfaaaa2d32ff9f918253546468",
        "exact_enclosure_mutation_count": 29,
        "exact_enclosure_self_test_sha256": "afc2ca44795f86b3dd9c74d2c07234ae9e0372737cdae7d718ec2db2e5204782",
        "exact_rounded_vector_sha256": "1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747",
        "exhaustive_fraction_containment_count": 6920,
        "guard_precision_decimal_digits": 160,
        "maximum_error_lower_nats": "2.167446422088005150275671429474969824136427179560898493282553682662172266784817744579758400790213907338588461575762025354130852141897942153682690e-15",
        "maximum_error_unique": True,
        "maximum_error_upper_epsilon_multiples_less_than": "9.761311",
        "maximum_error_upper_nats": "2.167446422088005150275671429474969824136427179560898493282553682662172266784817744579758400790213907338588461575762025354130852141897942153690778e-15",
        "maximum_selected_binary64_hex": "-0x1.6b52fe6a01407p+2",
        "maximum_tuple_n_k_nx_ny": [4096, 4, 2049, 2049],
        "maximum_zero_based_row": 7673,
        "stored_decimal_exact_rounded_maximum_difference_nats": "8.18e-77",
        "stored_decimal_exact_rounded_maximum_difference_reduced_fraction": (
            "409/(5*10^78)"
        ),
        "stored_decimal_exact_rounded_maximum_difference_tuple_n_k_nx_ny": [
            65536,
            64,
            32799,
            32799,
        ],
        "stored_decimal_exact_rounded_maximum_difference_zero_based_row": 7952,
        "stored_decimal_exact_rounded_numeric_mismatch_count": 5934,
        "stored_decimal_exact_rounded_textual_mismatch_count": 6509,
        "strict_epsilon_threshold_rounding": "ROUND_FLOOR",
        "target_precision_decimal_digits": 80,
    },
    "formal": {
        "historical_formal_assurance_v4_role": (
            "historical_lean_4_32_execution_record_preserved_byte_for_byte"
        ),
        "historical_formal_assurance_v4_sha256": "322c3f633d0e1316a401e92b10afb541ee82cb9ba94afef88f4a2937c934b6ff",
        "lean_4_33_checker_sha256": "020034884471ace9bcae1c8aa0b303a223758964278b6a0b1ac9ff5eeea94684",
        "lean_4_33_evidence_sha256": "d25f18530305e404d1d24a6eab2bda5f57b226d3db97c50ba4265c0c85ee9c35",
        "lean_4_33_lake_manifest_sha256": "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af",
        "lean_4_33_lakefile_sha256": "ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0",
        "lean_4_33_mathlib_revision": "db584cd6d46c92f209a44c0f1c829460d327499d",
        "lean_4_33_observed_version": "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit d8b18978322de05a8f3dba51ef03cf5461676c17, Release)",
        "lean_4_33_replay_addendum_sha256": "b5a974d3bc0cd66e37a963e33d87100c80c038d106f9bf19f27682062f848eae",
        "lean_4_33_self_test_sha256": "0bb0c999ad8bc20137deda54620d2983a5bd0ecaf4a74f81cbde23f997560517",
        "lean_4_33_source_commit": "d8b18978322de05a8f3dba51ef03cf5461676c17",
        "lean_4_33_toolchain": "leanprover/lean4:v4.33.0",
        "lean_4_33_toolchain_sha256": "302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b",
        "lean_active_source_sha256": "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4",
        "lean_mutation_count": 14,
        "lean_theorem_count": 19,
        "revision2_lean_source_sha256": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
        "shared_cuts": [
            "analytic_digamma_premise",
            "human_coefficient_signs",
            "human_exclusive_inclusive_index_map",
            "chosen_domain_and_theorem_statements",
            "deliberate_z3_raw_and_token_pin_rebase_and_statement_approval",
        ],
        "z3_checker_sha256": "2e0579820c02423e6d15bf81f6ee7470563a121908b4d06e5168b6508f991680",
        "z3_firewall_control_count": 52,
        "z3_firewall_control_group_counts": {
            "custody_transport_result": 11,
            "lexer_parser": 16,
            "profile_type": 25,
        },
        "z3_local_bound_sha256": "33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
        "z3_mutation_count": 12,
        "z3_negated_unsat_count": 4,
        "z3_parser_profile": "bounded complete ASCII S-expression parse with exact ordered "
        "per-file command/declaration/assertion profiles and Bool/Int/Real type checking",
        "z3_positive_sat_preflight_count": 4,
        "z3_raw_and_token_pins_are_correlated": True,
        "z3_retained_dual_rebase_boundary": {
            "classification": "negative_result_not_verification_evidence",
            "mutant_raw_sha256": "88e67f4289caf81770c9457d3ac77de4f470fe56d8bf3eb0a8139ac42c23ec52",
            "mutant_token_stream_sha256": "f8c8334b0cd73a55072e833463ae6ec43bd0f6042c0f7e888eff01b8f75caa8e",
            "negated_obligation": "unsat",
            "positive_preflight": "sat",
            "retained_semantic_mutants_still_sat": 12,
        },
        "z3_self_test_sha256": "927a21d119686d8e5a03755e8cf48581a2879bb67c835c295fdefcede26ec101",
        "z3_semantic_countermodel_count": 12,
        "z3_solver_input_transport": "single-read validated in-memory snapshots sent via "
        "standard input",
        "z3_token_stream_sha256": {
            "ksg-digamma-cancellation.smt2": "46d504aea109ae875598404a7d680e8dceb93635a4f91ab3d11bd51b08de5292",
            "ksg-index-maps.smt2": "7e655ca85f042c4275042fc8e9368a72aef10b1e0cbde3dce7b87c67769a7f2c",
            "ksg-local-bound-v4.smt2": "9f20298f0fb6a630167995b96638f6446a07e4005b9bc1a265a136302a73f284",
            "ksg-symmetric-range.smt2": "e7d9605f13384e1f7d04b0f1b6b4a61848adc70a6ae1925a06eeeddca2475aa1",
        },
        "z3_uses_uninterpreted_harmonic": True,
    },
    "modular_certificate": {
        "certificate_sha256": "5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f",
        "checker_sha256": "201b046957cee263ad4864acd84ab18095db4bbfc5a23bf90c2bb836b986afec",
        "composite_mutation_modulus": 1000001,
        "composite_mutation_reaches_miller_rabin_after_small_prime_prefilter": True,
        "maximum_reciprocal_summand_index": 999999,
        "mutation_count": 28,
        "nonendpoint_count": 7844,
        "odd_prime_reflection_identity": "H_(p-1-t) = H_t mod p for 0 <= t <= p-1",
        "pre_artifact_observation_is_final_custody": False,
        "pre_artifact_observation_sha256": "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc",
        "rejected_prime": 1000003,
        "rejected_prime_collision_indices_zero_based": [8045, 8049, 8069, 8093],
        "rejected_prime_collisions_are_one_reflection_event": True,
        "rejected_prime_residue_digest": "d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111",
        "residue_implication_direction": "nonzero residue implies exact rational "
        "nonzero",
        "selected_prime_reflected_indices": [33, 37, 81],
        "selected_prime_reflection_is_separation_proof": False,
        "selected_prime_role": "redundant fault diversity only, not CRT",
        "selected_primes": [1000033, 1000037, 1000081],
        "selected_residue_digests": [
            "931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b",
            "09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479",
            "20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0",
        ],
        "self_test_sha256": "1eebc0d575b730753d98659baee5e1f76f17c783e112a9610b731d5f07618c65",
        "strict_json_type_firewall_control_count": 2,
        "strict_recursive_json_type_shape_value_equality": True,
        "zero_residue_implies_exact_zero": False,
    },
    "object_firewall": [
        "ksg_local_integer_arithmetic_only",
        "no_transfer_to_complete_ksg_estimator",
        "no_transfer_to_continuous_ehrlich_isx",
        "no_transfer_to_continuous_pid2",
        "no_transfer_to_categorical_mgw_sxpid",
        "no_transfer_to_williams_beer_imin",
        "no_transfer_to_fitted_quantized_sxpid",
        "no_transfer_to_project_heuristics",
        "no_transfer_to_incomplete_or_mixed_dimension_pid3",
        "no_transfer_to_wrappers_identity_consumers_or_applications",
    ],
    "witnesses": {
        "c30_false_nonstructural_gap": {
            "absolute_term": "1/105",
            "counterexample_relation": "0 < |T| = 1/105 < 1/7 = 1/(n-1)",
            "false_claim": "every nonstructural nonzero satisfies |T| >= 1/(n-1)",
            "helper_arguments_n_k_x_y": [8, 2, 3, 5],
            "one_over_n_minus_one": "1/7",
            "structural_endpoint": False,
        },
        "w0_smallest_bound": {
            "arithmetic_box_endpoint_sharpness": True,
            "domain": "rectangular_arithmetic_helper",
            "helper_tuples_n_k_x_y": [
                [2, 1, 1, 1],
                [2, 1, 1, 2],
                [2, 1, 2, 1],
                [2, 1, 2, 2],
            ],
            "helper_values_nats": ["1", "0", "0", "-1"],
            "runtime_unique_shell_attainability_claim": False,
        },
        "w1": {
            "exact_target": "107/210",
            "helper_arguments_k_n_x_y": [2, 8, 5, 2],
            "ordered_counts": [4, 1],
            "radius": 79,
            "selected_bits": "0x3fe04e04e04e04e0",
        },
        "w2": {
            "exact_mean": "71/840",
            "helper_arguments_k_n_x_y": [2, 8, 5, 2],
            "inclusive_counts": [5, 2],
            "ordered_binary64_position_difference": 8,
            "ulp_claim": False,
        },
        "w2b": {
            "all_coordinate_values_unique": True,
            "all_joint_shells_unique_and_positive": True,
            "input_literal_encoding": "Rust binary64 decimal literals",
            "k": 1,
            "row_diagnostics": [
                {
                    "joint_radius": "1",
                    "n_alpha": 1,
                    "n_t": 3,
                    "row": 0,
                    "selected_bits": "0x0000000000000000",
                },
                {
                    "joint_radius": "1",
                    "n_alpha": 1,
                    "n_t": 3,
                    "row": 1,
                    "selected_bits": "0x0000000000000000",
                },
                {
                    "joint_radius": "2",
                    "n_alpha": 1,
                    "n_t": 3,
                    "row": 2,
                    "selected_bits": "0x0000000000000000",
                },
            ],
            "sample_count": 3,
            "sample_proves_population_support": False,
            "source1_literals": ["0", "1", "3"],
            "source2_literals": ["0", "10", "30"],
            "target_literals": ["0", "0.4", "0.8"],
        },
    },
}
INTEGRATION_GATE_IDS = (
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
EXPECTED_OPEN_INTEGRATION_GATES = INTEGRATION_GATE_IDS

EXPECTED_REVISION_HISTORY = [
    {"active": False, "revision": 1, "status": "retained_superseded"},
    {"active": False, "revision": 2, "status": "retained_superseded"},
    {"active": False, "revision": 3, "status": "frozen_preclosure_no_go"},
    {"active": True, "revision": 4, "status": "integration_no_go"},
]

EXPECTED_REVIEWED_V4_ARTIFACT_SHA256 = {
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md": (
        "4e6f462fadf3f6457feb188e9021d6cfccd8a964c8025a17987e207d5621ab83"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md": (
        "dd9392166e5e81d5974d771db17124dcbb7edec7599ccd85d145262f81a1b78f"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md": (
        "1196ed9154fc035fb4497a5146d777e15f19777677c914f5856a5bf1920b7a7e"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/"
    "decimal-reference-metric-conflation-v4.md": (
        "1d517a7b30656cc1048d6b227acd5c466838895ef77b850353926dc4efb6aa16"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md": (
        "b43ac9aecde6d02fe49bdf7c6256218ff2754b374549500a787fc1a7c34df2e7"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json": (
        "6fc2d3aabeb6a35f1f7d90d774c17817227e09f378341e90430ac611b857c680"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md": (
        "284a024ef730df20a7802e15565a181ef538f56b030d6a7e72f04fb8b7846da0"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": (
        "322c3f633d0e1316a401e92b10afb541ee82cb9ba94afef88f4a2937c934b6ff"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/formal-replay-lean-4.33.0-2026-08-11.md": (
        "b5a974d3bc0cd66e37a963e33d87100c80c038d106f9bf19f27682062f848eae"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md": (
        "8e23490c394910acee0a2c902c7829e2e9fe579b13fa0fb9de2c22c83d2686bd"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md": (
        "1e8bd67cc9f2fcb898f88c7e983a250fd2ff0ea346782f8adf96fd4aaf8f9858"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md": (
        "56e347372cd1f2a0c889878722578615517d34a35b1217e1aaec03f42d2fda0a"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/revision-index.md": (
        "f4863fd319a1a3b2f39477d6a5b5b80b38f78a0f1f3604934d72f93a99e92511"
    ),
    "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md": (
        "3dc19ce49d3743d23269c8ac9b2f8d63f13b509b1de3b7ac61e720a570607379"
    ),
}

REQUIRED_V4_PROSE_MARKERS = {
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md": (
        "ordered-binary64 positions. This wording does not assert eight ULPs",
        "The selected Neumaier-prefix "
        "ordinary-left route is "
        "nonzero on 150/354 endpoints",
        "A separately constructed naive-prefix route gives 121/354",
        "n_alpha = 1 = k\nn_t     = 3 = n",
        "All-unique samples do not prove the declared population-support model.",
        "this witness does not establish runtime attainability of `-D`.",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md": (
        "rectangular positive-integer arithmetic domain",
        "n >= 2\n1 <= k < n\nk <= x <= n\nk <= y <= n.",
        "sharp two-sided bound over that rectangular arithmetic domain",
        "The `-D` tuple is not asserted to be realizable by a runtime\n"
        "unique-shell geometry.",
        "neither it nor `x+y <= n+k` is promoted\n"
        "into the revision-4 theorem inventory",
        "The fixture contains 8,198 unique ordered rows: 6,920 exhaustive rectangular-arithmetic\n"
        "outer-box rows",
        "“Exhaustive” does not mean\nruntime-realizable.",
        "354 rows, split into 240 exhaustive and 114 stress rows.",
        "selected endpoint outputs          = 354 positive zeros",
        "selected endpoint negative zeros   = 0",
        "The `8*EPSILON` quantity first rounds each "
        "stored Decimal reference to binary64.",
        "exact-rational maximum upper bound < 9.761311 * f64::EPSILON nats",
        "selected value at exact maximum    = -0x1.6b52fe6a01407p+2",
        "selected full-corpus outputs        = 354 positive zeros, 0 negative zeros, 7,844 nonzeros",
        "The full-corpus partition is now counted directly by compiled Rust",
        "The strict epsilon\ncomparison uses a downward-rounded threshold",
        "Its baseline-first self-test kills 29/29\nregistered mutations",
        "differ textually from the exact-rational correctly rounded\n"
        "80-digit strings on 6,509 rows and differ numerically on 5,934 rows.",
        "ordinary four-term left association is nonzero at 150/354",
        "A separately constructed naive prefix has a\ndifferent 121/354 result",
        "It checks 19 theorem declarations and kills "
        "14/14 baseline-first semantic mutations.",
        "four satisfiable positive preflights, four "
        "unsatisfiable negated obligations, and 12/12",
        "The repaired self-test rejects 52/52 controls",
        "A retained well-typed wrong-theorem dual-rebase witness",
        "three primes provide redundant fault diversity, not CRT reconstruction",
        "maximum reciprocal summand denominator/index `999999`",
        "self-test kills 28/28 registered mutations",
        "reject 2/2 registered Boolean/integer firewall controls",
        "A separately implemented 160-digit directed-rounding\nenclosure",
        "only a historical pre-artifact observation; "
        "it is not current certificate custody.",
        "W1 reaches production-private ordered KSG diagnostics at zero-based row 5:",
        "categorical Makkeh--Gutknecht--Wibral shared-exclusions PID;",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md": (
        "every reciprocal-summand denominator/index occurring in the\nfrozen row.",
        "maximum reciprocal-summand denominator/index, then every `1/j` summand\ndenominator",
        "nonzero residue => exact rational nonzero.",
        "The "
        "selected "
        "triple "
        "provides "
        "redundant "
        "fault "
        "diversity. "
        "It is not "
        "CRT "
        "reconstruction",
        "Canonical "
        "current "
        "custody "
        "is\n"
        "`5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f`.",
        "registered composite-modulus mutation uses `1000001=101*9901`",
        "reaches the deterministic u32 Miller--Rabin witness loop",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/"
    "decimal-reference-metric-conflation-v4.md": (
        "## Separately implemented directed-enclosure route",
        "It shares\nthe formula, generated row order, and structural-endpoint classification",
        "exhaustive\nrectangular-arithmetic outer-box rows; this is not a runtime-shell-image enumeration.",
        "engine separation is not failure independence.",
        "converted exactly to\n`Fraction`",
        "separate exact-comparator firewall",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md": (
        "The old route also validated a file and later passed its path to Z3.",
        "reads all four proof files once into immutable byte snapshots",
        "The 52 controls do not enlarge the theorem, obligation, or semantic-mutation count.",
        "This is a retained negative result.",
        "88e67f4289caf81770c9457d3ac77de4f470fe56d8bf3eb0a8139ac42c23ec52",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": (
        "19 exact Lean theorems",
        "four\nseparately encoded conditional QF_UFLIRA obligations",
        "inventoried rectangular arithmetic outer box",
        "not asserted to equal the runtime unique-shell image",
        "must not be described as\ntwo failure-independent proofs",
        "12/12 Z3 mutants returning exact",
        "52 SMT grammar/profile/pin/snapshot/transport/result controls",
        "tripwire against rebasing only the raw-hash field",
        "wrong digamma theorem with raw SHA-256",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/formal-replay-lean-4.33.0-2026-08-11.md": (
        "historical Lean 4.32.0 execution and scope record, preserved byte-for-byte",
        "current machine-readable Lean 4.33.0 theorem and axiom-inventory evidence",
        "They are not current 4.33.0 identities.",
        "does\nnot retroactively claim that the earlier execution used Lean 4.33.0.",
        "host-bounded identity captured by the current evidence on\nDarwin arm64.",
        "its observed platform\nfield is a distinct runtime fact",
        "PositiveIntegerDigammaPremise` remains a typed unproved\npremise.",
        "does not establish count geometry, binary64 refinement, the full KSG\nestimator",
        "nor promotes the packet from its recorded `integration_no_go` lifecycle\nstate.",
        "none substitutes for another.",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md": (
        "repository and publication integration                    NO-GO",
        "Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are deliberately",
        "sharp rectangular-arithmetic-domain signed bound, W0 helper boundary",
        "shared\n    prompts, premises, and evidence cuts recorded",
        "52 firewall controls are not semantic mutants",
        "direct compiled 8,198-row `+0/-0/nonzero=354/0/7844` partition",
        "post-hoc trees do not close checker\n   self-reference",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md": (
        "sharp rectangular-arithmetic-domain signed bound",
        "all 6,920 exhaustive rectangular-arithmetic outer-box rows",
        "separately implemented Python binary64 replay",
        "shared formula, corpus, row order, endpoint branch, selected association",
        "their role is\nredundant fault diversity, "
        "not three independent proofs and not CRT.",
        "conditional `x+y<=n+k` and balanced constrained lower-bound candidate",
        "separate 52/52 firewall controls",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md": (
        "sharp rectangular-arithmetic-domain signed local bound",
        "Kill 28 modular certificate mutations.",
        "unsigned canonical M1a implementation commit",
        "Only after G1/M1a and final I1/Q1/H1 closure",
        "Qualify `x+y<=n+k` and its balanced lower bound.",
        "52/52 grammar/profile/type/token/snapshot/stdin/result controls are separate",
        "Every arrow is conjunctive. A green "
        "exact/formal/modular branch cannot close "
        "repository\nintegration while another "
        "branch is open.",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md": (
        "The modular checker separately recomputes prime admissibility",
        "all 6,920 exhaustive rectangular-arithmetic outer-box containments, not a runtime-shell image",
        "The binary64 loader separately reconstructs the exact exhaustive/stress row sequence",
        "The formal layer does not represent "
        "Rust, binary64, neighbor geometry, "
        "estimator statistics, or\nPID objects.",
        "Its\n28-mutant suite additionally rejects the stale harmonic-denominator object name",
        "The Z3 checker lexes bounded ASCII and parses all input as S-expressions",
        "separately rejects `2/2` type-firewall controls",
        "composite-modulus mutation is `1000001=101*9901`",
        "independently pre-pinned\npristine tree rejects it",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md": (
        "- **Correction:** status is "
        "`integration_no_go`; catalog, "
        "release, audience, identity, phase,\n",
        "- **False allegation:** counting the anchor and `k` joint neighbours forces "
        "`n_alpha >= k+1`.",
        "`0<|T|=1/105<1/7=1/(n-1)` exactly.",
        "The then-canonical `ae4645c3...`\n"
        "  artifact was superseded by C31; current certificate custody is",
        "complete SHA-256 bytes separately from the packet",
        "exact keys and scalar types, separately\n  reconstructed ordered rows",
        "the maximum reciprocal summand\n  denominator/index is `999999`",
        "## C32 — rectangular sharpness was conflated with runtime-shell attainability",
        "`x+y=|A union B|+k+1<=n+k=3`",
        "## C33 — compiled Rust did not directly scan the full output partition",
        "## C34 — raw SMT substring checks admitted grammar and snapshot false greens",
        "## C35 — modular certificate equality admitted Boolean/integer coercion",
        "## C36 — Decimal difference ordering relied on implicit context exactness",
        "## C37 — implementation purity was called statistical independence",
        "## C38 — W1/W2 helper tuples did not machine-label their field order",
        "## C39 — the rejected modular collision mechanism and field correlation were unstated",
        "## C40 — a provisional checkpoint was mislabeled as the canonical M1a anchor",
        "## C41 — the runtime count constraint advanced from hypothesis to conditional lemma only",
        "## C42 — the composite-modulus mutation stopped at the small-prime prefilter",
        "## C43 — phase self-custody was mistaken for an internal property",
        "ordinary `candidate-tree=not-requested` output is not closure evidence",
    ),
    "claims/KSG-INTEGER-HARMONIC-001/revision-index.md": (
        "certificate with 28 mutations",
        "The only active revision is 4.",
    ),
    "scripts/check-z3-ksg-integer-harmonic.py": (
        "Check separately encoded exact KSG harmonic/index obligations with pinned Z3.",
        "universal rational harmonic monotonicity are separately kernel-checked in Lean",
        "the statements, signs, maps, and analytic premise remain shared human cuts.",
    ),
    "scripts/check-z3-ksg-integer-harmonic-self-test.py": (
        "Twelve solver-level semantic mutants remain the scientific countermodel evidence class.",
    ),
}

FORBIDDEN_V4_PROSE_MARKERS = (
    "This exact local result therefore proves categorical MGW SxPID.",
    "Repository/publication integration is GO.",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_strict_json_equal(
    actual: object,
    expected: object,
    label: str,
    *,
    path: str = "$",
) -> None:
    """Compare JSON values without Python's bool/int/float equality coercions."""

    require(
        type(actual) is type(expected),
        f"{label} has the wrong JSON type at {path}: "
        f"expected {type(expected).__name__}, observed {type(actual).__name__}",
    )
    if isinstance(expected, dict):
        require(
            set(actual) == set(expected),  # type: ignore[arg-type]
            f"{label} object keys changed at {path}",
        )
        for key, expected_value in expected.items():
            require_strict_json_equal(
                actual[key],  # type: ignore[index]
                expected_value,
                label,
                path=f"{path}/{key}",
            )
        return
    if isinstance(expected, list):
        require(
            len(actual) == len(expected),  # type: ignore[arg-type]
            f"{label} array length changed at {path}",
        )
        for index, (actual_value, expected_value) in enumerate(
            zip(actual, expected, strict=True)  # type: ignore[arg-type]
        ):
            require_strict_json_equal(
                actual_value,
                expected_value,
                label,
                path=f"{path}/{index}",
            )
        return
    require(actual == expected, f"{label} value changed at {path}")


def normalized_claim_path_key(relative: str) -> str:
    return unicodedata.normalize("NFC", relative).casefold()


def require_exact_claim_tree_inventory(
    repo_root: Path,
    packet_files: dict[str, str],
) -> None:
    """Reject every unlisted file, directory, alias, and symlink in this claim tree."""

    claim_relative = Path("claims/KSG-INTEGER-HARMONIC-001")
    claim_root = repo_root / claim_relative
    require(claim_root.is_dir(), "claim packet root is absent or is not a directory")
    require(not claim_root.is_symlink(), "claim packet root is a symlink")

    allowed_files = {
        relative
        for relative in packet_files
        if Path(relative).is_relative_to(claim_relative)
    }
    allowed_files.add(ACTIVE_PACKET_RELATIVE_PATH)
    allowed_directories = {claim_relative.as_posix()}
    for relative in allowed_files:
        parent = Path(relative).parent
        while parent != claim_relative.parent:
            allowed_directories.add(parent.as_posix())
            if parent == claim_relative:
                break
            parent = parent.parent

    observed_files: set[str] = set()
    observed_directories: set[str] = {claim_relative.as_posix()}
    normalized_nodes: dict[str, str] = {}
    for directory, child_directories, child_files in os.walk(
        claim_root,
        topdown=True,
        followlinks=False,
    ):
        directory_path = Path(directory)
        child_directories.sort()
        child_files.sort()
        for name, is_directory in (
            *((name, True) for name in child_directories),
            *((name, False) for name in child_files),
        ):
            node = directory_path / name
            relative = node.relative_to(repo_root).as_posix()
            try:
                mode = node.lstat().st_mode
            except OSError as error:
                fail(f"claim-tree node is unreadable: {relative}: {error}")
            require(
                not stat.S_ISLNK(mode), f"claim tree contains a symlink: {relative}"
            )
            if is_directory:
                require(
                    stat.S_ISDIR(mode),
                    f"claim-tree directory entry has the wrong type: {relative}",
                )
                observed_directories.add(relative)
            else:
                require(
                    stat.S_ISREG(mode),
                    f"claim-tree file entry is not regular: {relative}",
                )
                observed_files.add(relative)

            normalized = normalized_claim_path_key(relative)
            require(
                normalized not in normalized_nodes,
                "claim tree contains a case/Unicode-normalized path collision: "
                f"{normalized_nodes.get(normalized)!r} versus {relative!r}",
            )
            normalized_nodes[normalized] = relative

    require(
        observed_files == allowed_files,
        "claim-tree exact file inventory changed: "
        f"missing={sorted(allowed_files - observed_files)}, "
        f"unexpected={sorted(observed_files - allowed_files)}",
    )
    require(
        observed_directories == allowed_directories,
        "claim-tree exact directory inventory changed: "
        f"missing={sorted(allowed_directories - observed_directories)}, "
        f"unexpected={sorted(observed_directories - allowed_directories)}",
    )


def projection_sha256(value: object) -> str:
    projected = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(projected).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{label} contains a duplicate object key: {key}")
            value[key] = item
        return value

    def reject_nonfinite(token: str) -> None:
        fail(f"{label} contains a non-finite JSON number: {token}")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_nonfinite,
        )
        canonical = canonical_json_bytes(value)
    except (UnicodeError, json.JSONDecodeError) as error:
        fail(f"{label} is not canonical finite UTF-8 JSON: {error}")
    require(isinstance(value, dict), f"{label} root is not an object")
    require(raw == canonical, f"{label} is not canonical JSON")
    return value


FINAL_AUTHORITY_START = "<!-- pid-rs:ksg-harmonic-final-authority:start -->\n"
FINAL_AUTHORITY_END = "<!-- pid-rs:ksg-harmonic-final-authority:end -->"


def parse_final_authority(path: Path, artifact: str) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    require(
        source.count(FINAL_AUTHORITY_START) == 1
        and source.count(FINAL_AUTHORITY_END) == 1,
        f"{artifact}: final authority sentinels are absent or duplicated",
    )
    prefix, remainder = source.split(FINAL_AUTHORITY_START, 1)
    authority_text, suffix = remainder.split(FINAL_AUTHORITY_END, 1)
    require(
        prefix.startswith("# ") and suffix.startswith("\n"),
        f"{artifact}: final authority is not embedded in a headed Markdown artifact",
    )
    authority = parse_canonical_json(
        authority_text.encode("utf-8"),
        f"{artifact} final authority",
    )
    require(
        authority.get("schema") == "pid-rs/ksg-harmonic-final-authority"
        and type(authority.get("schema_revision")) is int
        and authority.get("schema_revision") == 1
        and authority.get("claim_id") == "KSG-INTEGER-HARMONIC-001"
        and type(authority.get("revision")) is int
        and authority.get("revision") == 4
        and authority.get("artifact") == artifact
        and authority.get("status") == "integration_go"
        and authority.get("packet_stage") == FINAL_PACKET_STAGE,
        f"{artifact}: final authority identity/lifecycle fields changed",
    )
    return authority


def check_final_artifact_authorities(
    repo_root: Path,
    packet_files: dict[str, str],
) -> None:
    evidence_relative = "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md"
    decision_relative = "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md"
    evidence = parse_final_authority(
        require_regular_packet_file(repo_root, evidence_relative),
        "evidence_matrix_v4",
    )
    require(
        set(evidence)
        == {
            "artifact",
            "claim_id",
            "gate_receipts",
            "packet_stage",
            "revision",
            "schema",
            "schema_revision",
            "status",
        },
        "evidence matrix final-authority fields changed",
    )
    gate_receipts = evidence.get("gate_receipts")
    require(type(gate_receipts) is dict, "final evidence gate receipts are absent")
    require(
        list(gate_receipts) == sorted(INTEGRATION_GATE_IDS),
        "final evidence gate-receipt inventory/order changed",
    )
    for gate_id, receipt in gate_receipts.items():
        require(
            type(receipt) is dict, f"{gate_id}: final gate receipt is not an object"
        )
        require(
            set(receipt) == {"path", "sha256", "status"}
            and receipt.get("status") == "closed",
            f"{gate_id}: final gate receipt fields/status changed",
        )
        relative = receipt.get("path")
        digest = receipt.get("sha256")
        require(
            type(relative) is str
            and type(digest) is str
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            f"{gate_id}: final gate receipt path/digest is invalid",
        )
        require(
            relative in packet_files and packet_files[relative] == digest,
            f"{gate_id}: final gate receipt is not content-bound into the packet",
        )
        require_regular_packet_file(repo_root, relative)

    decision = parse_final_authority(
        require_regular_packet_file(repo_root, decision_relative),
        "decision_v4",
    )
    require(
        set(decision)
        == {
            "artifact",
            "claim_id",
            "closed_integration_gates",
            "evidence_matrix_sha256",
            "implementation_commit",
            "packet_stage",
            "revision",
            "schema",
            "schema_revision",
            "status",
        },
        "decision final-authority fields changed",
    )
    require_strict_json_equal(
        decision.get("closed_integration_gates"),
        list(INTEGRATION_GATE_IDS),
        "decision closed integration gates",
    )
    require(
        decision.get("evidence_matrix_sha256") == packet_files[evidence_relative],
        "decision does not bind the final evidence matrix",
    )
    require(
        type(decision.get("implementation_commit")) is str
        and re.fullmatch(r"[0-9a-f]{40}", decision["implementation_commit"])
        is not None,
        "decision implementation commit is not a full lowercase Git object id",
    )


def require_regular_packet_file(repo_root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    require(relative != "", "packet contains an empty path")
    require(
        relative == relative_path.as_posix(),
        f"packet path is not canonical POSIX text: {relative}",
    )
    require(
        not relative_path.is_absolute()
        and all(part not in ("", ".", "..") for part in relative_path.parts),
        f"packet path escapes the repository: {relative}",
    )

    target = repo_root
    for part in relative_path.parts:
        target = target / part
        require(not target.is_symlink(), f"packet path traverses a symlink: {relative}")
    try:
        mode = target.lstat().st_mode
    except OSError as error:
        fail(f"packet target is absent or unreadable: {relative}: {error}")
    require(stat.S_ISREG(mode), f"packet target is not a regular file: {relative}")
    require(
        target.lstat().st_nlink == 1,
        f"packet target has an external hardlink alias: {relative}",
    )
    try:
        target.resolve(strict=True).relative_to(repo_root)
    except (OSError, ValueError) as error:
        fail(f"packet target resolves outside the repository: {relative}: {error}")
    return target


def check_claim_route(repo_root: Path) -> dict[str, Any]:
    manifest_path = require_regular_packet_file(repo_root, ACTIVE_PACKET_RELATIVE_PATH)
    manifest_raw = manifest_path.read_bytes()
    require(
        hashlib.sha256(manifest_raw).hexdigest() == EXPECTED_ACTIVE_PACKET_SHA256,
        "active revision-4 packet digest changed",
    )
    manifest = parse_canonical_json(manifest_raw, "active revision-4 packet")
    require(
        set(manifest)
        == {
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
        "active revision-4 packet top-level fields changed",
    )
    require(
        manifest.get("schema") == "pid-rs/ksg-harmonic-active-packet",
        "active packet schema changed",
    )
    require_strict_json_equal(
        manifest.get("schema_revision"),
        1,
        "active packet schema revision",
    )
    require(
        manifest.get("claim_id") == "KSG-INTEGER-HARMONIC-001",
        "active packet claim id changed",
    )
    require_strict_json_equal(
        manifest.get("active_revision"),
        4,
        "active packet revision",
    )
    require(
        manifest.get("status") == EXPECTED_PACKET_STATUS, "active packet status changed"
    )
    require(
        manifest.get("packet_stage") == EXPECTED_PACKET_STAGE, "packet stage changed"
    )
    status = manifest.get("status")
    stage = manifest.get("packet_stage")
    require(
        (status, stage)
        in {
            ("integration_no_go", PRECLOSURE_PACKET_STAGE),
            ("integration_go", FINAL_PACKET_STAGE),
        },
        f"unsupported status/stage lifecycle tuple: {(status, stage)!r}",
    )

    revision_history = manifest.get("revision_history")
    require_strict_json_equal(
        revision_history,
        EXPECTED_REVISION_HISTORY,
        "active packet revision history",
    )
    active_rows = [
        row
        for row in revision_history
        if isinstance(row, dict) and row.get("active") is True
    ]
    require(
        len(active_rows) == 1,
        "active packet does not contain exactly one active revision",
    )
    require(
        active_rows[0]
        == {"active": True, "revision": 4, "status": EXPECTED_PACKET_STATUS},
        "active packet selects a revision or status outside the reviewed revision-4 state",
    )

    packet_files = manifest.get("packet_files")
    require(isinstance(packet_files, dict), "active packet file map is not an object")
    require(
        list(packet_files) == sorted(packet_files),
        "active packet file map is not ordered",
    )
    for relative, expected_digest in packet_files.items():
        require(isinstance(relative, str), "active packet contains a non-string path")
        require(
            isinstance(expected_digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_digest) is not None,
            f"active packet contains an invalid SHA-256 for {relative}",
        )
        require_regular_packet_file(repo_root, relative)
    require(
        tuple(packet_files) == EXPECTED_PACKET_PATHS,
        "active packet exact path set changed",
    )
    require(
        ACTIVE_PACKET_RELATIVE_PATH not in packet_files,
        "active packet includes itself and creates a digest cycle",
    )
    require(
        "scripts/check-ksg-harmonic-revision.py" not in packet_files
        and "scripts/check-ksg-harmonic-revision-self-test.py" not in packet_files,
        "active packet includes its checker or self-test and creates a digest cycle",
    )
    require_exact_claim_tree_inventory(repo_root, packet_files)
    for relative, expected_digest in packet_files.items():
        target = require_regular_packet_file(repo_root, relative)
        require(
            hashlib.sha256(target.read_bytes()).hexdigest() == expected_digest,
            f"active packet file digest mismatch: {relative}",
        )
    for relative, expected_digest in EXPECTED_REVIEWED_V4_ARTIFACT_SHA256.items():
        require(
            packet_files.get(relative) == expected_digest,
            f"reviewed revision-4 artifact bytes changed: {relative}",
        )

    historical_hashes = manifest.get("historical_hashes")
    require(
        historical_hashes == EXPECTED_HISTORICAL_HASHES,
        "frozen historical hashes changed",
    )
    require(
        list(historical_hashes) == sorted(historical_hashes),
        "historical hash map is not ordered",
    )
    for relative, expected_digest in EXPECTED_HISTORICAL_HASHES.items():
        require(
            packet_files.get(relative) == expected_digest,
            f"historical hash is not bound into the packet file map: {relative}",
        )

    facts = manifest.get("facts")
    require_strict_json_equal(
        facts,
        EXPECTED_CLAIM_FACTS,
        "reviewed revision-4 scalar facts",
    )
    require_strict_json_equal(
        manifest.get("open_integration_gates"),
        list(EXPECTED_OPEN_INTEGRATION_GATES),
        "revision-4 open integration gates",
    )

    linked_digests = {
        "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json": facts["formal"][
            "lean_4_33_evidence_sha256"
        ],
        "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean": facts["formal"][
            "revision2_lean_source_sha256"
        ],
        "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean": facts["formal"][
            "revision2_lean_source_sha256"
        ],
        "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean": facts["formal"][
            "lean_active_source_sha256"
        ],
        "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2": facts["formal"][
            "z3_local_bound_sha256"
        ],
        "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": facts["formal"][
            "historical_formal_assurance_v4_sha256"
        ],
        "claims/KSG-INTEGER-HARMONIC-001/"
        "formal-replay-lean-4.33.0-2026-08-11.md": facts["formal"][
            "lean_4_33_replay_addendum_sha256"
        ],
        "audit/formal/lean/lake-manifest.json": facts["formal"][
            "lean_4_33_lake_manifest_sha256"
        ],
        "audit/formal/lean/lakefile.toml": facts["formal"]["lean_4_33_lakefile_sha256"],
        "audit/formal/lean/lean-toolchain": facts["formal"][
            "lean_4_33_toolchain_sha256"
        ],
        "scripts/check-lean-ksg-integer-harmonic.py": facts["formal"][
            "lean_4_33_checker_sha256"
        ],
        "scripts/check-lean-ksg-integer-harmonic-self-test.py": facts["formal"][
            "lean_4_33_self_test_sha256"
        ],
        "claims/KSG-INTEGER-HARMONIC-001/certificates/"
        "ksg-harmonic-modular-certificate-v1.json": facts["modular_certificate"][
            "certificate_sha256"
        ],
        "scripts/check-z3-ksg-integer-harmonic-self-test.py": facts["formal"][
            "z3_self_test_sha256"
        ],
        "scripts/check-z3-ksg-integer-harmonic.py": facts["formal"][
            "z3_checker_sha256"
        ],
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json": (
            EXPECTED_FIXTURE_SHA256
        ),
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256": (
            EXPECTED_FIXTURE_SIDECAR_SHA256
        ),
        "scripts/generate-ksg-local-arithmetic-oracle.py": EXPECTED_GENERATOR_SHA256,
        "scripts/check-ksg-harmonic-exact-enclosure.py": facts[
            "exact_rational_enclosure"
        ]["exact_enclosure_checker_sha256"],
        "scripts/check-ksg-harmonic-exact-enclosure-self-test.py": facts[
            "exact_rational_enclosure"
        ]["exact_enclosure_self_test_sha256"],
        "scripts/check-ksg-harmonic-modular-certificate.py": facts[
            "modular_certificate"
        ]["checker_sha256"],
        "scripts/check-ksg-harmonic-modular-certificate-self-test.py": facts[
            "modular_certificate"
        ]["self_test_sha256"],
    }
    for relative, expected_digest in linked_digests.items():
        require(
            packet_files.get(relative) == expected_digest,
            f"reviewed fact is not linked to its packet digest: {relative}",
        )

    historical_formal = require_regular_packet_file(
        repo_root,
        "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md",
    ).read_text(encoding="utf-8")
    require(
        "leanprover/lean4:v4.32.0" in historical_formal
        and "8c9756b28d64dab099da31a4c09229a9e6a2ef35" in historical_formal
        and "leanprover/lean4:v4.33.0" not in historical_formal,
        "historical formal-assurance-v4 toolchain identity was conflated with current replay",
    )
    current_lean_evidence = json.loads(
        require_regular_packet_file(
            repo_root,
            "audit/evidence/lean-ksg-integer-harmonic-4.33.0.json",
        ).read_bytes()
    )
    require(
        isinstance(current_lean_evidence, dict),
        "current Lean evidence is not an object",
    )
    formal_facts = facts["formal"]
    require_strict_json_equal(
        {
            "checker_source_sha256": current_lean_evidence.get("checker_source_sha256"),
            "lake_manifest_sha256": current_lean_evidence.get("lake_manifest_sha256"),
            "lean_toolchain": current_lean_evidence.get("lean_toolchain"),
            "lean_version": current_lean_evidence.get("lean_version"),
            "retained_v2_source_sha256": current_lean_evidence.get(
                "retained_v2_source_sha256"
            ),
            "source_revision": current_lean_evidence.get("source_revision"),
            "source_sha256": current_lean_evidence.get("source_sha256"),
            "status": current_lean_evidence.get("status"),
            "theorems_kernel_checked": current_lean_evidence.get(
                "theorems_kernel_checked"
            ),
        },
        {
            "checker_source_sha256": formal_facts["lean_4_33_checker_sha256"],
            "lake_manifest_sha256": formal_facts["lean_4_33_lake_manifest_sha256"],
            "lean_toolchain": formal_facts["lean_4_33_toolchain"],
            "lean_version": formal_facts["lean_4_33_observed_version"],
            "retained_v2_source_sha256": formal_facts["revision2_lean_source_sha256"],
            "source_revision": 4,
            "source_sha256": formal_facts["lean_active_source_sha256"],
            "status": "passed",
            "theorems_kernel_checked": formal_facts["lean_theorem_count"],
        },
        "current Lean 4.33 evidence-to-packet binding",
    )

    formal_v3 = (
        repo_root / "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md"
    ).read_bytes()
    require(len(formal_v3) == 1_985, "formal-assurance-v3 byte length changed")
    require(len(formal_v3.splitlines()) == 40, "formal-assurance-v3 line count changed")

    for relative, markers in REQUIRED_V4_PROSE_MARKERS.items():
        source = require_regular_packet_file(repo_root, relative).read_text(
            encoding="utf-8"
        )
        for marker in markers:
            require(
                marker in source,
                f"revision-4 semantic prose marker absent: {relative}: {marker!r}",
            )
    claim_prose = "\n".join(
        require_regular_packet_file(repo_root, relative).read_text(encoding="utf-8")
        for relative in packet_files
        if relative.startswith("claims/KSG-INTEGER-HARMONIC-001/")
        and relative.endswith(".md")
    )
    for marker in FORBIDDEN_V4_PROSE_MARKERS:
        require(
            marker not in claim_prose,
            f"claim packet contains a forbidden scientific promotion: {marker!r}",
        )

    certificate_relative = (
        "claims/KSG-INTEGER-HARMONIC-001/certificates/"
        "ksg-harmonic-modular-certificate-v1.json"
    )
    certificate = parse_canonical_json(
        require_regular_packet_file(repo_root, certificate_relative).read_bytes(),
        "bounded modular certificate",
    )
    selected = certificate.get("selected_prime_certificates")
    require(isinstance(selected, list), "selected modular records are not an array")
    require(
        all(isinstance(record, dict) for record in selected),
        "selected modular array contains a non-object record",
    )
    modular = facts["modular_certificate"]
    require_strict_json_equal(
        [record.get("prime") for record in selected],
        modular["selected_primes"],
        "selected modular prime inventory",
    )
    require_strict_json_equal(
        [record.get("residue_u32be_sha256") for record in selected],
        modular["selected_residue_digests"],
        "selected modular residue digests",
    )
    for record in selected:
        total = record.get("counts", {}).get("total", {})
        require_strict_json_equal(
            total.get("endpoint_zero_count"),
            354,
            "selected modular endpoint count",
        )
        require_strict_json_equal(
            total.get("nonendpoint_nonzero_count"),
            7_844,
            "selected modular nonendpoint count",
        )
    rejected = certificate.get("rejected_prime_negative_control")
    require(isinstance(rejected, dict), "rejected modular negative control is absent")
    require_strict_json_equal(
        rejected.get("prime"),
        modular["rejected_prime"],
        "rejected prime",
    )
    require(
        rejected.get("residue_u32be_sha256")
        == modular["rejected_prime_residue_digest"],
        "rejected-prime residue digest changed",
    )
    collisions = rejected.get("collisions")
    require(isinstance(collisions, list), "rejected-prime collisions are not an array")
    require(
        all(isinstance(collision, dict) for collision in collisions),
        "rejected-prime collision array contains a non-object record",
    )
    require_strict_json_equal(
        [collision.get("fixture_index_zero_based") for collision in collisions],
        modular["rejected_prime_collision_indices_zero_based"],
        "rejected-prime zero-based collision indices",
    )
    statement = certificate.get("statement")
    require(isinstance(statement, dict), "modular certificate statement is absent")
    require(
        statement.get("residue_implication_direction")
        == "nonzero_modular_residue_implies_exact_rational_nonzero",
        "modular residue implication direction changed",
    )
    require(
        statement.get("selected_prime_set_role")
        == "redundant_fault_diversity_only_not_crt",
        "selected modular primes were promoted to CRT",
    )
    require(
        statement.get("zero_residue_nonimplication")
        == "zero_modular_residue_does_not_imply_exact_rational_zero",
        "rejected-prime zero-residue non-implication changed",
    )

    final_artifacts = (
        "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md",
        "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md",
    )
    if EXPECTED_PACKET_STATUS == "integration_no_go":
        require(
            manifest.get("packet_stage") == PRECLOSURE_PACKET_STAGE
            and manifest.get("open_integration_gates")
            == list(EXPECTED_OPEN_INTEGRATION_GATES)
            and len(EXPECTED_OPEN_INTEGRATION_GATES) > 0,
            "preclosure lifecycle tuple is internally inconsistent",
        )
        for relative in final_artifacts:
            final_path = repo_root / relative
            require(
                not final_path.exists() and not final_path.is_symlink(),
                f"preclosure packet unexpectedly contains final artifact: {relative}",
            )
    else:
        require(
            EXPECTED_PACKET_STATUS == "integration_go",
            f"unsupported packet lifecycle status: {EXPECTED_PACKET_STATUS}",
        )
        require(
            manifest.get("packet_stage") == FINAL_PACKET_STAGE
            and EXPECTED_OPEN_INTEGRATION_GATES == ()
            and manifest.get("open_integration_gates") == [],
            "final lifecycle tuple retains a preclosure stage or open integration gate",
        )
        for relative in final_artifacts:
            require(
                relative in packet_files,
                f"final packet does not map required artifact: {relative}",
            )
            require_regular_packet_file(repo_root, relative)
        check_final_artifact_authorities(repo_root, packet_files)
    return manifest


def require_default_integration_go(manifest: dict[str, Any]) -> None:
    status = manifest.get("status")
    gates = manifest.get("open_integration_gates")
    gate_count = len(gates) if isinstance(gates, list) else -1
    require(
        status == "integration_go" and gates == [],
        "default integration gate remains closed: "
        f"status={status!r}; open_integration_gates={gate_count}; "
        "use scoped routes for preclosure diagnostics",
    )


def mask_rust(source: str, *, mask_strings: bool) -> str:
    """Mask Rust comments and optionally strings while preserving positions and newlines."""

    masked = list(source)
    index = 0
    while index < len(source):
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            if end < 0:
                end = len(source)
            for position in range(index, end):
                masked[position] = " "
            index = end
            continue
        if source.startswith("/*", index):
            depth = 1
            end = index + 2
            while end < len(source) and depth:
                if source.startswith("/*", end):
                    depth += 1
                    end += 2
                elif source.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            require(depth == 0, "unterminated Rust block comment")
            for position in range(index, end):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue

        raw_match = re.match(r"(?:br|r)(?P<hashes>#{0,255})\"", source[index:])
        if raw_match:
            hashes = raw_match.group("hashes")
            terminator = '"' + hashes
            content_start = index + raw_match.end()
            end_start = source.find(terminator, content_start)
            require(end_start >= 0, "unterminated Rust raw string")
            end = end_start + len(terminator)
            if mask_strings:
                for position in range(index, end):
                    if masked[position] != "\n":
                        masked[position] = " "
            index = end
            continue

        quote_index = index
        if source.startswith('b"', index):
            quote_index += 1
        if source[quote_index : quote_index + 1] == '"':
            end = quote_index + 1
            escaped = False
            while end < len(source):
                character = source[end]
                if character == '"' and not escaped:
                    end += 1
                    break
                if character == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False
                end += 1
            require(
                end <= len(source) and source[end - 1] == '"',
                "unterminated Rust string",
            )
            if mask_strings:
                for position in range(index, end):
                    if masked[position] != "\n":
                        masked[position] = " "
            index = end
            continue
        index += 1
    return "".join(masked)


def mask_rust_noncode(source: str) -> str:
    """Mask Rust comments and strings for live-code structural checks."""

    return mask_rust(source, mask_strings=True)


def mask_rust_comments(source: str) -> str:
    """Mask Rust comments while retaining live string-literal values."""

    return mask_rust(source, mask_strings=False)


def rust_function_span(masked_source: str, name: str) -> tuple[int, int]:
    marker = f"fn {name}("
    start = masked_source.find(marker)
    require(start >= 0, f"Rust function is absent: {name}")
    require(
        masked_source.find(marker, start + 1) < 0,
        f"Rust function is duplicated: {name}",
    )
    opening = masked_source.find("{", start)
    require(opening >= 0, f"Rust function body is absent: {name}")
    depth = 0
    for index in range(opening, len(masked_source)):
        if masked_source[index] == "{":
            depth += 1
        elif masked_source[index] == "}":
            depth -= 1
            if depth == 0:
                return opening + 1, index
    fail(f"Rust function body is unterminated: {name}")


def rust_function_body(masked_source: str, name: str) -> str:
    start, end = rust_function_span(masked_source, name)
    return masked_source[start:end]


def require_runtime_estimator_revision(
    comments_masked_source: str,
    structure_masked_source: str,
    function_name: str,
    expected_revision: str,
) -> None:
    start, end = rust_function_span(structure_masked_source, function_name)
    body = comments_masked_source[start:end]
    field = "estimator_revision:"
    marker = f'{field} "{expected_revision}",'
    require(
        body.count(field) == 1, f"runtime estimator field changed in {function_name}"
    )
    require(
        body.count(marker) == 1,
        f"runtime estimator revision changed in {function_name}: expected {expected_revision}",
    )


def shifted_harmonic_table(max_argument: int) -> list[float]:
    """Return table[m] = H_(m-1) using the production compensation policy."""

    table = [0.0] * (max_argument + 1)
    total = 0.0
    correction = 0.0
    for argument in range(2, max_argument + 1):
        value = 1.0 / float(argument - 1)
        next_total = total + value
        if abs(total) >= abs(value):
            correction += (total - next_total) + value
        else:
            correction += (value - next_total) + total
        total = next_total
        table[argument] = total + correction
    return table


def naive_shifted_harmonic_table(max_argument: int) -> list[float]:
    """Return table[m] = H_(m-1) using ordinary left-associated binary64 sums."""

    table = [0.0] * (max_argument + 1)
    total = 0.0
    for argument in range(2, max_argument + 1):
        total += 1.0 / float(argument - 1)
        table[argument] = total
    return table


def harmonic_term(table: list[float], k: int, n: int, x: int, y: int) -> float:
    require(0 < k <= x <= n and k <= y <= n, "invalid positive-integer count domain")
    lower = min(x, y)
    upper = max(x, y)
    return (table[n] - table[upper]) - (table[lower] - table[k])


def exact_harmonic(index: int) -> Fraction:
    return sum(
        (Fraction(1, denominator) for denominator in range(1, index + 1)), Fraction()
    )


def is_endpoint_cancellation_case(case: dict[str, Any]) -> bool:
    low = case["k"] - 1
    high = case["sample_count"] - 1
    return (case["x_count"], case["y_count"]) in ((low, high), (high, low))


def check_exact_route() -> None:
    cases = 0
    for n in range(2, 17):
        harmonics = [exact_harmonic(index) for index in range(n)]
        for k in range(1, n):
            for nx in range(k - 1, n):
                for ny in range(k - 1, n):
                    direct = (
                        harmonics[k - 1]
                        + harmonics[n - 1]
                        - harmonics[nx]
                        - harmonics[ny]
                    )
                    lower = min(nx + 1, ny + 1)
                    upper = max(nx + 1, ny + 1)
                    ranged = (harmonics[n - 1] - harmonics[upper - 1]) - (
                        harmonics[lower - 1] - harmonics[k - 1]
                    )
                    require(
                        direct == ranged,
                        f"exact range identity failed at {(n, k, nx, ny)}",
                    )
                    cases += 1
    require(cases == EXPECTED_EXHAUSTIVE_CASES, f"exact case count changed: {cases}")
    require(
        exact_harmonic(3) - 2 * exact_harmonic(0) == Fraction(11, 6),
        "n=4,k=1 sparse boundary changed",
    )
    require(
        exact_harmonic(1) + exact_harmonic(3) - 2 * exact_harmonic(1) == Fraction(5, 6),
        "n=4,k=2 boundary changed",
    )
    require(
        exact_harmonic(2) + exact_harmonic(3) - 2 * exact_harmonic(3)
        == Fraction(-1, 3),
        "n=4,k=3 dense boundary changed",
    )


def load_fixture(repo_root: Path) -> dict[str, Any]:
    fixture_path = (
        repo_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    )
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    raw = fixture_path.read_bytes()
    require(
        sidecar_path.read_bytes()
        == f"{EXPECTED_FIXTURE_SHA256}  {fixture_path.name}\n".encode("ascii"),
        "fixture SHA-256 sidecar bytes changed",
    )
    require(
        hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256,
        "fixture bytes changed from the reviewed schema-2 digest",
    )
    fixture = parse_canonical_json(raw, "KSG arithmetic fixture")
    require(
        set(fixture)
        == {
            "arithmetic",
            "bounds",
            "cases",
            "generator",
            "limitations",
            "schema",
            "schema_revision",
        },
        "fixture top-level fields changed",
    )
    require(fixture.get("schema") == EXPECTED_FIXTURE_SCHEMA, "fixture schema changed")
    require_strict_json_equal(
        fixture.get("schema_revision"),
        EXPECTED_FIXTURE_SCHEMA_REVISION,
        "fixture schema revision",
    )
    arithmetic = fixture.get("arithmetic")
    require(type(arithmetic) is dict, "fixture arithmetic metadata is absent")
    require(
        set(arithmetic)
        == {
            "decimal_precision_digits",
            "endpoint_cancellation_exact_zero_case_count",
            "endpoint_cancellation_exact_zero_exhaustive_case_count",
            "endpoint_cancellation_exact_zero_rule",
            "endpoint_cancellation_exact_zero_stress_case_count",
            "exact_identity",
            "logarithm_unit",
        },
        "fixture arithmetic metadata fields changed",
    )
    require_strict_json_equal(
        arithmetic.get("decimal_precision_digits"),
        80,
        "fixture precision",
    )
    require_strict_json_equal(
        arithmetic.get("endpoint_cancellation_exact_zero_case_count"),
        EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture endpoint-cancellation exact-zero count",
    )
    require_strict_json_equal(
        arithmetic.get("endpoint_cancellation_exact_zero_exhaustive_case_count"),
        EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
        "fixture exhaustive endpoint-cancellation exact-zero count",
    )
    require(
        arithmetic.get("endpoint_cancellation_exact_zero_rule")
        == EXPECTED_ENDPOINT_CANCELLATION_RULE,
        "fixture endpoint-cancellation exact-zero rule changed",
    )
    require_strict_json_equal(
        arithmetic.get("endpoint_cancellation_exact_zero_stress_case_count"),
        EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS,
        "fixture stress endpoint-cancellation exact-zero count",
    )
    require(
        arithmetic.get("exact_identity") == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity changed",
    )
    require(
        arithmetic.get("logarithm_unit") == "nats", "fixture information unit changed"
    )
    cases = fixture.get("cases")
    require(type(cases) is list, "fixture cases are not an array")
    require(len(cases) == EXPECTED_CASES, "fixture case count changed")
    expected_rows = [
        (sample_count, k, x_count, y_count)
        for sample_count in range(2, 17)
        for k in range(1, sample_count)
        for x_count in range(k - 1, sample_count)
        for y_count in range(k - 1, sample_count)
    ]
    for sample_count in EXPECTED_STRESS_SAMPLE_SIZES:
        k_values = sorted(
            {
                value
                for value in (
                    1,
                    2,
                    3,
                    4,
                    8,
                    16,
                    64,
                    sample_count // 2,
                    sample_count - 1,
                )
                if 1 <= value < sample_count
            }
        )
        for k in k_values:
            count_values = sorted(
                {
                    k - 1,
                    min(k, sample_count - 1),
                    (k + sample_count - 1) // 2,
                    sample_count - 2,
                    sample_count - 1,
                }
            )
            expected_rows.extend(
                (sample_count, k, x_count, y_count)
                for x_count in count_values
                for y_count in count_values
            )
    require(
        len(expected_rows) == EXPECTED_CASES,
        "independent fixture row inventory changed",
    )
    expected_case_fields = {"expected_nats", "k", "sample_count", "x_count", "y_count"}
    for row_index, (case, expected_row) in enumerate(
        zip(cases, expected_rows, strict=True)
    ):
        require(type(case) is dict, f"fixture row {row_index} is not an object")
        require(
            set(case) == expected_case_fields,
            f"fixture row {row_index} fields changed",
        )
        observed_row = tuple(
            case[field] for field in ("sample_count", "k", "x_count", "y_count")
        )
        require(
            all(type(value) is int for value in observed_row),
            f"fixture row {row_index} contains a non-integer count",
        )
        require(
            observed_row == expected_row,
            f"fixture row {row_index} differs from the reconstructed row order",
        )
        expected_text = case.get("expected_nats")
        require(
            type(expected_text) is str, f"fixture row {row_index} reference is not text"
        )
        try:
            expected_decimal = Decimal(expected_text)
        except InvalidOperation as error:
            fail(f"fixture row {row_index} reference is not Decimal: {error}")
        require(
            expected_decimal.is_finite() and str(expected_decimal) == expected_text,
            f"fixture row {row_index} reference is nonfinite or noncanonical",
        )
    endpoint_cases = [
        case for case in fixture["cases"] if is_endpoint_cancellation_case(case)
    ]
    require(
        len(endpoint_cases) == EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture structural endpoint-cancellation case count changed",
    )
    require(
        all(case.get("expected_nats") == "0" for case in endpoint_cases),
        "fixture endpoint-cancellation references are not canonical exact positive zero",
    )
    canonical_zero_cases = [
        case for case in fixture["cases"] if case.get("expected_nats") == "0"
    ]
    require(
        len(canonical_zero_cases) == EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture canonical exact-zero reference count changed",
    )
    require(
        all(is_endpoint_cancellation_case(case) for case in canonical_zero_cases),
        "fixture contains a canonical exact-zero reference outside the endpoint rule",
    )
    endpoint_exhaustive_cases = [
        case for case in endpoint_cases if case["sample_count"] <= 16
    ]
    endpoint_stress_cases = [
        case for case in endpoint_cases if case["sample_count"] > 16
    ]
    require(
        len(endpoint_exhaustive_cases)
        == EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
        "fixture row-derived exhaustive endpoint-cancellation count changed",
    )
    require(
        len(endpoint_stress_cases) == EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS,
        "fixture row-derived stress endpoint-cancellation count changed",
    )
    bounds = fixture.get("bounds")
    require(type(bounds) is dict, "fixture bounds metadata is absent")
    require(
        set(bounds)
        == {
            "exhaustive_case_count",
            "exhaustive_max_samples",
            "exhaustive_rule",
            "stress_case_count",
            "stress_sample_sizes",
        },
        "fixture bounds metadata fields changed",
    )
    require_strict_json_equal(
        bounds.get("exhaustive_case_count"),
        EXPECTED_EXHAUSTIVE_CASES,
        "fixture exhaustive count",
    )
    require_strict_json_equal(
        bounds.get("exhaustive_max_samples"),
        16,
        "fixture exhaustive bound",
    )
    require(
        bounds.get("exhaustive_rule")
        == "2 <= n <= bound; 1 <= k < n; k-1 <= nx,ny < n",
        "fixture exhaustive domain changed",
    )
    require_strict_json_equal(
        bounds.get("stress_case_count"),
        EXPECTED_STRESS_CASES,
        "fixture stress count",
    )
    require(
        type(bounds.get("stress_sample_sizes")) is list
        and all(type(value) is int for value in bounds["stress_sample_sizes"])
        and tuple(bounds["stress_sample_sizes"]) == EXPECTED_STRESS_SAMPLE_SIZES,
        "fixture stress sample sizes changed or contain a non-integer",
    )
    generator = fixture.get("generator")
    require(isinstance(generator, dict), "fixture generator metadata is absent")
    require(
        generator.get("path") == EXPECTED_GENERATOR_PATH,
        "fixture generator path changed",
    )
    require(
        generator.get("imports_pid_rs") is False, "fixture generator imports pid-rs"
    )
    require(
        generator.get("third_party_dependencies") == [],
        "fixture generator dependency declaration changed",
    )
    live_generator = (repo_root / EXPECTED_GENERATOR_PATH).read_bytes()
    live_generator_sha256 = hashlib.sha256(live_generator).hexdigest()
    require(
        live_generator_sha256 == EXPECTED_GENERATOR_SHA256,
        "live generator bytes changed from the reviewed schema-2 revision-4 digest",
    )
    require(
        generator.get("sha256") == EXPECTED_GENERATOR_SHA256,
        "fixture is not bound to the reviewed live generator digest",
    )
    optimization = [] if sys.flags.optimize == 0 else ["-" + "O" * sys.flags.optimize]
    generator_replay = subprocess.run(
        [
            sys.executable,
            *optimization,
            str(repo_root / EXPECTED_GENERATOR_PATH),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        generator_replay.returncode == 0
        and generator_replay.stderr == ""
        and generator_replay.stdout
        == (
            "OK: 8198 high-precision KSG local arithmetic cases match SHA-256 "
            f"{EXPECTED_FIXTURE_SHA256}\n"
        ),
        "no-write fixture generator replay failed: "
        f"returncode={generator_replay.returncode}; stdout={generator_replay.stdout!r}; "
        f"stderr={generator_replay.stderr!r}",
    )
    return fixture


def check_binary64_route(fixture: dict[str, Any]) -> None:
    max_argument = max(case["sample_count"] for case in fixture["cases"])
    table = shifted_harmonic_table(max_argument)
    naive_table = naive_shifted_harmonic_table(max_argument)
    maximum_error = 0.0
    first_maximum: tuple[int, int, int, int] | None = None
    maximum_error_ties = 0
    swap_bit_asymmetries = 0
    selected_endpoint_positive_zeros = 0
    selected_endpoint_negative_zeros = 0
    selected_endpoint_nonzeros = 0
    endpoint_direct_left_nonzeros = 0
    endpoint_direct_left_negative_zeros = 0
    naive_prefix_direct_left_nonzeros = 0
    naive_prefix_direct_left_negative_zeros = 0
    selected_full_positive_zeros = 0
    selected_full_negative_zeros = 0
    selected_full_nonzeros = 0
    for case in fixture["cases"]:
        n = case["sample_count"]
        k = case["k"]
        x = case["x_count"] + 1
        y = case["y_count"] + 1
        actual = harmonic_term(table, k, n, x, y)
        swapped = harmonic_term(table, k, n, y, x)
        require(
            math.isfinite(actual) and math.isfinite(swapped),
            f"nonfinite selected binary64 term at {(n, k, case['x_count'], case['y_count'])}",
        )
        swap_bit_asymmetries += actual.hex() != swapped.hex()
        expected = float(case["expected_nats"])
        require(
            math.isfinite(expected),
            f"nonfinite rounded reference at {(n, k, case['x_count'], case['y_count'])}",
        )
        selected_full_positive_zeros += actual.hex() == "0x0.0p+0"
        selected_full_negative_zeros += actual.hex() == "-0x0.0p+0"
        selected_full_nonzeros += actual != 0.0
        if is_endpoint_cancellation_case(case):
            selected_endpoint_positive_zeros += actual.hex() == "0x0.0p+0"
            selected_endpoint_negative_zeros += actual.hex() == "-0x0.0p+0"
            selected_endpoint_nonzeros += actual != 0.0
            direct_left = ((table[k] + table[n]) - table[x]) - table[y]
            endpoint_direct_left_nonzeros += direct_left != 0.0
            endpoint_direct_left_negative_zeros += direct_left.hex() == "-0x0.0p+0"
            naive_direct_left = (
                (naive_table[k] + naive_table[n]) - naive_table[x]
            ) - naive_table[y]
            naive_prefix_direct_left_nonzeros += naive_direct_left != 0.0
            naive_prefix_direct_left_negative_zeros += (
                naive_direct_left.hex() == "-0x0.0p+0"
            )
        error = abs(actual - expected)
        if error > maximum_error:
            maximum_error = error
            first_maximum = (n, k, case["x_count"], case["y_count"])
            maximum_error_ties = 1
        elif error == maximum_error:
            maximum_error_ties += 1

    require(
        swap_bit_asymmetries == 0,
        f"found {swap_bit_asymmetries} source-swap asymmetries",
    )
    require(
        selected_endpoint_positive_zeros == EXPECTED_SELECTED_ENDPOINT_POSITIVE_ZEROS,
        "selected endpoint positive-zero count changed: "
        f"{selected_endpoint_positive_zeros}",
    )
    require(
        selected_endpoint_negative_zeros == EXPECTED_SELECTED_ENDPOINT_NEGATIVE_ZEROS,
        "selected endpoint negative-zero count changed: "
        f"{selected_endpoint_negative_zeros}",
    )
    require(
        selected_endpoint_nonzeros == EXPECTED_SELECTED_ENDPOINT_NONZEROS,
        f"selected endpoint nonzero count changed: {selected_endpoint_nonzeros}",
    )
    require(
        selected_full_positive_zeros == EXPECTED_ENDPOINT_CANCELLATION_ZEROS
        and selected_full_negative_zeros == 0
        and selected_full_nonzeros
        == EXPECTED_CASES - EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "selected full-corpus signed-zero/nonzero partition changed",
    )
    require(
        endpoint_direct_left_nonzeros == EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS,
        "selected-prefix ordinary-left endpoint nonzero count changed: "
        f"{endpoint_direct_left_nonzeros}",
    )
    require(
        endpoint_direct_left_negative_zeros
        == EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS,
        "selected-prefix ordinary-left endpoint negative-zero count changed: "
        f"{endpoint_direct_left_negative_zeros}",
    )
    require(
        naive_prefix_direct_left_nonzeros == EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS,
        "naive-prefix ordinary-left endpoint nonzero count changed: "
        f"{naive_prefix_direct_left_nonzeros}",
    )
    require(
        naive_prefix_direct_left_negative_zeros
        == EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NEGATIVE_ZEROS,
        "naive-prefix ordinary-left endpoint negative-zero count changed: "
        f"{naive_prefix_direct_left_negative_zeros}",
    )
    require(
        maximum_error == EXPECTED_ROUNDED_REFERENCE_MAX_ERROR,
        f"binary64-rounded-reference maximum changed: {maximum_error}",
    )
    require(
        first_maximum == EXPECTED_ROUNDED_REFERENCE_FIRST_MAXIMUM,
        f"first maximum-attaining tuple changed: {first_maximum}",
    )
    require(
        maximum_error_ties == EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_TIES,
        f"maximum-error tie multiplicity changed: {maximum_error_ties}",
    )
    require(
        EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES == 32,
        "reviewed binary64-rounded-reference ceiling multiplier changed",
    )
    require(
        ALLOWED_ROUNDED_REFERENCE_MAX_ERROR
        == EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES * sys.float_info.epsilon,
        "binary64-rounded-reference ceiling is not derived from the reviewed multiplier",
    )
    require(
        maximum_error <= ALLOWED_ROUNDED_REFERENCE_MAX_ERROR,
        "binary64-rounded-reference finite-corpus ceiling exceeded",
    )


def check_exact_enclosure_route(repo_root: Path) -> None:
    checker_path = require_regular_packet_file(
        repo_root,
        EXACT_ENCLOSURE_CHECKER_RELATIVE_PATH,
    )
    require(
        hashlib.sha256(checker_path.read_bytes()).hexdigest()
        == EXPECTED_EXACT_ENCLOSURE_CHECKER_SHA256,
        "exact-enclosure checker bytes changed from the reviewed route",
    )
    optimization = [] if sys.flags.optimize == 0 else ["-" + "O" * sys.flags.optimize]
    result = subprocess.run(
        [
            sys.executable,
            *optimization,
            str(checker_path),
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    required_output = (
        "digest-bound directed exact-rational enclosure for 8198 frozen schema-2 rows",
        "6920 exhaustive exact-Fraction containment witnesses",
        "6509 textually unequal, 5934 numerically unequal",
        "binary64 conversion mismatches 0",
        "unique maximum at zero-based row 7673 (4096, 4, 2049, 2049)",
        "selected value -0x1.6b52fe6a01407p+2",
        "strictly below 9.761311 epsilon and below 32 epsilon",
        "distinct binary64-rounded-reference comparator: maximum 8 epsilon; 40 ties",
        "not a universal error theorem, cross-platform identity claim",
    )
    require(
        result.returncode == 0 and result.stderr == "",
        "exact-enclosure checker failed:\n"
        f"stdout={result.stdout!r}; stderr={result.stderr!r}",
    )
    for fragment in required_output:
        require(
            fragment in result.stdout,
            f"exact-enclosure checker output lost reviewed fact: {fragment!r}",
        )


def load_release_families(repo_root: Path) -> dict[str, dict[str, Any]]:
    release_path = repo_root / "release-scope-1.0.json"
    release = json.loads(release_path.read_bytes())
    require(isinstance(release, dict), "release scope root is not an object")
    require(
        release.get("schema") == "pid-rs/release-scope", "release scope schema changed"
    )
    require(
        release.get("schema_revision") == 1, "release scope schema revision changed"
    )
    raw_families = release.get("families")
    require(isinstance(raw_families, list), "release scope families are not a list")
    families: dict[str, dict[str, Any]] = {}
    for index, family in enumerate(raw_families):
        require(isinstance(family, dict), f"release family {index} is not an object")
        family_id = family.get("id")
        require(
            isinstance(family_id, str) and family_id,
            f"release family {index} has no string id",
        )
        require(family_id not in families, f"duplicate release family id: {family_id}")
        families[family_id] = family
    return families


def require_release_revision(
    families: dict[str, dict[str, Any]],
    family_id: str,
    expected_definition: str,
    expected_estimator: str,
) -> None:
    require(family_id in families, f"release family is absent: {family_id}")
    family = families[family_id]
    require(
        family.get("definition_revision") == expected_definition,
        f"release definition revision changed for {family_id}: "
        f"expected {expected_definition}",
    )
    require(
        family.get("estimator_revision") == expected_estimator,
        f"release estimator revision changed for {family_id}: "
        f"expected {expected_estimator}",
    )


def check_release_route(repo_root: Path) -> None:
    release_path = repo_root / "release-scope-1.0.json"
    raw = release_path.read_bytes()
    release = json.loads(raw)
    canonical = (
        json.dumps(
            release,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    require(raw == canonical, "release scope is not canonical JSON")
    families = load_release_families(repo_root)
    require(
        len(KSG_RELEASE_REVISIONS) == 15,
        "KSG affected release-family inventory no longer contains exactly 15 rows",
    )
    require(
        len(KSG_PROTECTED_RELEASE_REVISIONS) == 22,
        "KSG protected release-family inventory no longer contains exactly 22 rows",
    )
    expected_ids = set(KSG_RELEASE_REVISIONS) | set(KSG_PROTECTED_RELEASE_REVISIONS)
    require(
        set(families) == expected_ids,
        "release family inventory changed: "
        f"missing={sorted(expected_ids - set(families))}, "
        f"unexpected={sorted(set(families) - expected_ids)}",
    )
    affected_rows = [
        family
        for family in release["families"]
        if family["id"] in KSG_RELEASE_REVISIONS
    ]
    protected_rows = [
        family
        for family in release["families"]
        if family["id"] in KSG_PROTECTED_RELEASE_REVISIONS
    ]
    metadata = {key: value for key, value in release.items() if key != "families"}
    require(
        projection_sha256(affected_rows) == KSG_AFFECTED_RELEASE_FAMILIES_SHA256,
        "a KSG-affected release family changed outside the reviewed full-object projection",
    )
    require(
        projection_sha256(protected_rows) == KSG_PROTECTED_RELEASE_FAMILIES_SHA256,
        "a protected release family changed during the KSG-only milestone",
    )
    require(
        projection_sha256(metadata) == KSG_PROTECTED_RELEASE_METADATA_SHA256,
        "release top-level metadata changed during the KSG-only milestone",
    )

    for family_id, (definition, previous_estimator, estimator) in sorted(
        KSG_RELEASE_REVISIONS.items()
    ):
        require(
            previous_estimator != estimator,
            f"{family_id}: estimator revision did not move",
        )
        require_release_revision(families, family_id, definition, estimator)
    for family_id, (definition, estimator) in sorted(
        KSG_PROTECTED_RELEASE_REVISIONS.items()
    ):
        require_release_revision(families, family_id, definition, estimator)

    readme = (repo_root / README_RELATIVE_PATH).read_text(encoding="utf-8")
    for marker in REQUIRED_README_KSG_MARKERS:
        require(
            readme.count(marker) == 1,
            f"README KSG outer-box marker count changed: {marker!r}",
        )
    for marker in FORBIDDEN_README_KSG_MARKERS:
        require(
            marker not in readme, f"README contains forbidden KSG wording: {marker!r}"
        )


def check_catalog_route(repo_root: Path) -> None:
    catalog_path = repo_root / "method-catalog.json"
    raw = catalog_path.read_bytes()
    catalog = json.loads(raw)
    require(isinstance(catalog, dict), "method catalog root is not an object")
    require(
        catalog.get("schema") == "pid-rs/method-catalog",
        "method catalog schema changed",
    )
    require(
        catalog.get("schema_revision") == 1, "method catalog schema revision changed"
    )
    canonical = (
        json.dumps(
            catalog,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    require(raw == canonical, "method catalog is not canonical JSON")

    methods = catalog.get("methods")
    references = catalog.get("references")
    require(isinstance(methods, list), "method catalog methods are not a list")
    require(isinstance(references, list), "method catalog references are not a list")
    require(len(methods) == 73, "method catalog no longer contains exactly 73 methods")
    require(
        len(references) == 45, "method catalog no longer contains exactly 45 references"
    )

    by_id: dict[str, dict[str, Any]] = {}
    for index, method in enumerate(methods):
        require(isinstance(method, dict), f"catalog method {index} is not an object")
        method_id = method.get("id")
        require(
            isinstance(method_id, str) and method_id,
            f"catalog method {index} has no id",
        )
        require(method_id not in by_id, f"duplicate catalog method id: {method_id}")
        by_id[method_id] = method
    require(list(by_id) == sorted(by_id), "method catalog ids are not sorted")
    require(
        set(KSG_CATALOG_METHOD_IDS) <= set(by_id),
        "one or more KSG-affected catalog methods are absent",
    )
    reverse_dependencies: dict[str, set[str]] = {
        method_id: set() for method_id in by_id
    }
    for method_id, method in by_id.items():
        dependencies = method.get("depends_on")
        require(
            isinstance(dependencies, list), f"{method_id}: depends_on is not a list"
        )
        require(
            dependencies == sorted(set(dependencies)),
            f"{method_id}: dependencies are not sorted and unique",
        )
        for dependency in dependencies:
            require(
                isinstance(dependency, str) and dependency in by_id,
                f"{method_id}: dependency target is absent: {dependency}",
            )
            reverse_dependencies[dependency].add(method_id)
    reverse_closure = set(KSG_CATALOG_ROOT_METHOD_IDS)
    frontier = list(KSG_CATALOG_ROOT_METHOD_IDS)
    while frontier:
        dependency = frontier.pop()
        for consumer in reverse_dependencies[dependency]:
            if consumer not in reverse_closure:
                reverse_closure.add(consumer)
                frontier.append(consumer)
    expected_reverse_closure = set(KSG_CATALOG_METHOD_IDS) | set(
        KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS
    )
    require(
        reverse_closure == expected_reverse_closure,
        "KSG reverse-dependency closure changed: "
        f"missing={sorted(expected_reverse_closure - reverse_closure)}, "
        f"unexpected={sorted(reverse_closure - expected_reverse_closure)}",
    )
    require(
        reverse_closure - set(KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS)
        == set(KSG_CATALOG_METHOD_IDS),
        "KSG affected catalog inventory is not the declared reverse closure minus the "
        "non-numerical shared-config exclusion",
    )

    protected_methods = [
        method for method in methods if method["id"] not in KSG_CATALOG_METHOD_IDS
    ]
    require(len(protected_methods) == 53, "protected catalog method count changed")
    unchanged_protected_methods = [
        method
        for method in protected_methods
        if method["id"] not in KSG_REVIEWED_CROSS_LANE_CATALOG_METHOD_IDS
        and method["id"] not in KSG_POST_REVISION_PROTECTED_CATALOG_METHOD_IDS
    ]
    reviewed_cross_lane_methods = [
        method
        for method in protected_methods
        if method["id"] in KSG_REVIEWED_CROSS_LANE_CATALOG_METHOD_IDS
    ]
    post_revision_protected_methods = [
        method
        for method in protected_methods
        if method["id"] in KSG_POST_REVISION_PROTECTED_CATALOG_METHOD_IDS
    ]
    legacy_protected_methods = [
        method
        for method in protected_methods
        if method["id"] not in KSG_POST_REVISION_PROTECTED_CATALOG_METHOD_IDS
    ]
    require(
        len(unchanged_protected_methods) == 40
        and len(reviewed_cross_lane_methods) == 7
        and len(post_revision_protected_methods) == 6,
        "reviewed cross-lane catalog partition changed",
    )
    require(
        projection_sha256(unchanged_protected_methods)
        == KSG_UNCHANGED_PROTECTED_CATALOG_METHODS_SHA256,
        "a protected non-KSG catalog method outside the reviewed cross-lane corrections changed",
    )
    require(
        projection_sha256(reviewed_cross_lane_methods)
        == KSG_REVIEWED_CROSS_LANE_CATALOG_METHODS_SHA256,
        "reviewed cross-lane catalog method projection changed",
    )
    require(
        projection_sha256(post_revision_protected_methods)
        == KSG_POST_REVISION_PROTECTED_CATALOG_METHODS_SHA256,
        "post-revision protected catalog method projection changed",
    )
    require(
        projection_sha256(legacy_protected_methods)
        == KSG_REVIEWED_PROTECTED_CATALOG_METHODS_SHA256,
        "legacy reviewed protected catalog method projection changed",
    )
    require(
        projection_sha256(protected_methods)
        == KSG_CURRENT_PROTECTED_CATALOG_METHODS_SHA256,
        "current protected catalog method projection changed",
    )
    require(
        projection_sha256(references) == KSG_PROTECTED_CATALOG_REFERENCES_SHA256,
        "catalog references changed during the KSG-only milestone",
    )
    metadata = {
        key: value
        for key, value in catalog.items()
        if key not in ("methods", "references")
    }
    require(
        projection_sha256(metadata) == KSG_PROTECTED_CATALOG_METADATA_SHA256,
        "catalog top-level metadata changed during the KSG-only milestone",
    )
    catalog_text = raw.decode("utf-8")
    for token in KSG_FORBIDDEN_CATALOG_TOKENS:
        require(
            token not in catalog_text,
            f"KSG-only catalog contains later-wave token: {token}",
        )

    claim_bound: set[str] = set()
    formal_bound: set[str] = set()
    for method_id, method in by_id.items():
        validation = method.get("validation")
        require(
            isinstance(validation, dict), f"{method_id}: validation block is absent"
        )
        evidence_paths = validation.get("evidence_paths")
        require(
            isinstance(evidence_paths, list),
            f"{method_id}: evidence_paths is not a list",
        )
        require(
            all(isinstance(path, str) and path for path in evidence_paths),
            f"{method_id}: evidence_paths contains a non-string or empty path",
        )
        if method_id in KSG_CATALOG_METHOD_IDS:
            require(
                evidence_paths == sorted(set(evidence_paths)),
                f"{method_id}: KSG evidence_paths are not sorted and unique",
            )
        evidence = set(evidence_paths)
        if method_id in KSG_CATALOG_METHOD_IDS:
            for relative in evidence_paths:
                evidence_path = Path(relative)
                require(
                    not evidence_path.is_absolute() and ".." not in evidence_path.parts,
                    f"{method_id}: evidence path escapes the repository: {relative}",
                )
                require(
                    (repo_root / evidence_path).is_file(),
                    f"{method_id}: bound evidence target is absent: {relative}",
                )
        if "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md" in evidence:
            claim_bound.add(method_id)
        if evidence & set(KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE):
            formal_bound.add(method_id)
        require(
            "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md" not in evidence
            and "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md" not in evidence
            and "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md" not in evidence,
            f"{method_id}: active catalog evidence cites a stale KSG claim revision",
        )

    require(
        claim_bound == set(KSG_CATALOG_METHOD_IDS),
        "KSG claim-bound method inventory changed: "
        f"missing={sorted(set(KSG_CATALOG_METHOD_IDS) - claim_bound)}, "
        f"unexpected={sorted(claim_bound - set(KSG_CATALOG_METHOD_IDS))}",
    )
    require(
        formal_bound == set(KSG_FORMAL_CATALOG_METHOD_IDS),
        "KSG formal-evidence method inventory changed: "
        f"missing={sorted(set(KSG_FORMAL_CATALOG_METHOD_IDS) - formal_bound)}, "
        f"unexpected={sorted(formal_bound - set(KSG_FORMAL_CATALOG_METHOD_IDS))}",
    )
    affected_methods = [
        method for method in methods if method["id"] in KSG_CATALOG_METHOD_IDS
    ]
    require(
        projection_sha256(affected_methods) == KSG_AFFECTED_CATALOG_METHODS_SHA256,
        "reviewed KSG-affected catalog method projection changed",
    )
    for method_id in KSG_CATALOG_METHOD_IDS:
        method = by_id[method_id]
        validation = method["validation"]
        evidence = set(validation["evidence_paths"])
        for path in KSG_REQUIRED_CATALOG_EVIDENCE:
            require(
                path in evidence,
                f"{method_id}: required KSG evidence path absent: {path}",
            )
        validation_text = json.dumps(validation, ensure_ascii=True).lower()
        require(
            "integer-harmonic" in validation_text
            or "integer harmonic" in validation_text,
            f"{method_id}: integer-harmonic validation boundary is absent",
        )
    for method_id in KSG_FORMAL_CATALOG_METHOD_IDS:
        evidence = set(by_id[method_id]["validation"]["evidence_paths"])
        for path in KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE:
            require(
                path in evidence,
                f"{method_id}: formal KSG evidence path absent: {path}",
            )

    shared_config_evidence = set(
        by_id["mutual-information.ksg1-shared-config"]["validation"]["evidence_paths"]
    )
    require(
        not any("KSG-INTEGER-HARMONIC-001" in path for path in shared_config_evidence),
        "unchanged shared KSG config is incorrectly bound to the arithmetic claim",
    )


def check_source_route(repo_root: Path) -> None:
    # These guards deliberately remain bounded textual evidence. They reject the named live-code
    # shadow/overwrite attacks after masking comments and strings, but they are not a compiler
    # def-use proof; compiled corpus and tiny count witnesses are the semantic backstop.
    stats_source = (repo_root / "crates/pid-core/src/stats.rs").read_text(
        encoding="utf-8"
    )
    ksg_source = (repo_root / "crates/pid-core/src/ksg.rs").read_text(encoding="utf-8")
    isx_source = (repo_root / "crates/pid-core/src/isx.rs").read_text(encoding="utf-8")
    pid3_source = (repo_root / "crates/pid-core/src/pid3.rs").read_text(
        encoding="utf-8"
    )
    stats = mask_rust_noncode(stats_source)
    ksg = mask_rust_noncode(ksg_source)
    isx = mask_rust_noncode(isx_source)
    pid3 = mask_rust_noncode(pid3_source)

    prefix_body = rust_function_body(stats, "shifted_harmonic_table")
    term_body = rust_function_body(stats, "ksg_local_harmonic_term")
    corpus_body = rust_function_body(
        stats, "ksg_integer_harmonic_range_matches_decimal_oracle"
    )
    heuristic_body = rust_function_body(isx, "isx_redundancy_heuristic_sketch")
    w1_body = rust_function_body(
        ksg, "ksg_ordered_count_witness_reaches_production_diagnostics"
    )
    w2_body = rust_function_body(
        isx, "ehrlich_inclusive_counts_reach_the_exact_integer_harmonic_local_term"
    )
    w2b_body = rust_function_body(
        isx, "ehrlich_all_unique_rows_attain_the_structural_zero_count_endpoint"
    )

    require(
        "this implementation-level separation does not assert statistical independence of\n"
        "    // observations. Results are collected **in index order**" in isx_source,
        "ISX implementation-purity/statistical-independence boundary changed",
    )
    require(
        "Each point is independent" not in isx_source,
        "ISX source reintroduced an unsupported statistical-independence statement",
    )

    for marker in (
        "pub(crate) fn shifted_harmonic_table(n: usize)",
        "pub(crate) fn ksg_local_harmonic_term(",
        "const KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS: usize = 121;",
        "const KSG_FULL_CORPUS_NONZEROS: usize = 7_844;",
        "const KSG_ROUNDED_REFERENCE_OBSERVED_MAX_ERROR_NATS: f64 = 8.0 * f64::EPSILON;",
        "const KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;",
        "let mut naive_shifted_harmonics = vec![0.0_f64; max_argument + 1];",
        "naive_prefix_direct_left_nonzeros, KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS,",
    ):
        require(marker in stats, f"shifted-harmonic source marker absent: {marker}")
    for marker in (
        "let mut full_corpus_positive_zero_outputs = 0_usize;",
        "let mut full_corpus_negative_zero_outputs = 0_usize;",
        "let mut full_corpus_nonzero_outputs = 0_usize;",
        "rounded_reference.is_finite() && actual.is_finite() && source_swapped.is_finite()",
        "match actual.to_bits()",
        "bits if bits == 0.0_f64.to_bits() => full_corpus_positive_zero_outputs += 1",
        "bits if bits == (-0.0_f64).to_bits() => full_corpus_negative_zero_outputs += 1",
        "_ => full_corpus_nonzero_outputs += 1",
        "full_corpus_nonzero_outputs,",
        "KSG_FULL_CORPUS_NONZEROS,",
    ):
        require(
            corpus_body.count(marker) == 1,
            f"direct compiled full-corpus partition marker count changed: {marker}",
        )
    for marker in (
        "let len = n.checked_add(1)",
        "for argument in 2..=n",
        "let value = 1.0 / (argument - 1) as f64;",
        "if sum.abs() >= value.abs()",
        "correction += (sum - next) + value;",
        "correction += (value - next) + sum;",
        "out[argument] = sum + correction;",
    ):
        require(
            prefix_body.count(marker) == 1,
            f"shifted-harmonic prefix marker count changed: {marker}",
        )
    require(
        prefix_body.count("out[argument]") == 1,
        "shifted-harmonic prefix output has multiple live reads or writes",
    )
    for marker in (
        "let lower = x.min(y);",
        "let upper = x.max(y);",
        "(shifted_harmonics[n] - shifted_harmonics[upper])",
        "(shifted_harmonics[lower] - shifted_harmonics[k])",
    ):
        require(
            term_body.count(marker) == 1,
            f"source-symmetric range marker count changed: {marker}",
        )
    require(
        term_body.count("let lower =") == 1,
        "lower range binding is shadowed or duplicated",
    )
    require(
        term_body.count("let upper =") == 1,
        "upper range binding is shadowed or duplicated",
    )

    require(
        ksg.count("ksg_local_harmonic_term(") == 4, "KSG direct call-site count changed"
    )
    require(
        len(re.findall(r"nx \+ 1,\s*ny \+ 1", ksg)) == 4,
        "KSG exclusive-count off-by-one map changed",
    )
    require(
        "digamma(" not in ksg and "digamma_int_table" not in ksg, "KSG retained digamma"
    )
    require_runtime_estimator_revision(
        mask_rust_comments(ksg_source),
        ksg,
        "ksg_mi_report_with_kernel_and_cancellation",
        "strict-unique-shell-integer-harmonic-report-v4",
    )
    for marker in (
        "let row = diagnostics[5];",
        "assert_eq!(row.joint_radius.to_bits(), 79.0_f64.to_bits());",
        "assert_eq!((row.x_count, row.y_count), (4, 1));",
        "assert_eq!(row.term_nats.to_bits(), 0x3fe0_4e04_e04e_04e0);",
    ):
        require(marker in w1_body, f"W1 production-diagnostic marker absent: {marker}")
    for marker in (
        "(79.0, 5, 2),",
        "local[5].term_nats.to_bits()",
        "0x3fe0_4e04_e04e_04e0",
    ):
        require(marker in w2_body, f"W2 production-diagnostic marker absent: {marker}")
    expected_w2b = """let expected: [(u64, usize, usize, u64); 3] = [
            (1.0_f64.to_bits(), 1, 3, 0_u64),
            (1.0_f64.to_bits(), 1, 3, 0_u64),
            (2.0_f64.to_bits(), 1, 3, 0_u64),
        ];"""
    require(
        w2b_body.count(expected_w2b) == 1,
        "W2b exact three-row radius/count/positive-zero array changed",
    )
    for marker in (
        "assert_eq!(local.len(), expected.len());",
        "local.iter().zip(expected).enumerate()",
        "diagnostic.joint_radius.to_bits()",
        "diagnostic.source_union_count",
        "diagnostic.target_count",
        "diagnostic.term_nats.to_bits()",
    ):
        require(
            marker in w2b_body, f"W2b production-diagnostic marker absent: {marker}"
        )

    require(
        isx.count("ksg_local_harmonic_term(") == 1,
        "ISX eligible call-site count changed",
    )
    require(
        "&shifted_harmonics, k, n, n_alpha, n_t" in isx,
        "ISX inclusive index map changed",
    )
    for marker in (
        "let psi_k = digamma(k as f64);",
        "let psi_n = digamma(n as f64);",
        "let psi_int = digamma_int_table(n)?;",
        "let psi_shared = psi_int[n_t_shared[i] + 1];",
        "let psi_s1 = psi_int[n_t_s1[i] + 1];",
        "let psi_s2 = psi_int[n_t_s2[i] + 1];",
        "psi_shared - 0.5 * (psi_s1 + psi_s2)",
        "let redundancy = psi_k + psi_n + avg_term;",
    ):
        require(
            marker in heuristic_body,
            f"non-cancelling heuristic marker absent: {marker}",
        )
    require_runtime_estimator_revision(
        mask_rust_comments(isx_source),
        isx,
        "isx_redundancy_report_with_local_terms",
        "strict-unique-shell-integer-harmonic-isx-v4",
    )

    require(
        pid3.count("ksg_local_harmonic_term(") == 1,
        "PID3 eligible call-site count changed",
    )
    require("n_alpha,\n            n_t," in pid3, "PID3 inclusive index map changed")
    require(
        "digamma(" not in pid3 and "digamma_int_table" not in pid3,
        "PID3 retained digamma",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="pid-rs checkout to inspect (defaults to this script's repository)",
    )
    route = parser.add_mutually_exclusive_group()
    route.add_argument(
        "--claim-only",
        action="store_true",
        help=(
            "check only canonical revision-4 claim custody and semantics; this preclosure route "
            "does not imply repository integration GO"
        ),
    )
    route.add_argument(
        "--release-only",
        action="store_true",
        help=(
            "check only the release-family migration; intended for isolated mutation replay, "
            "not as a substitute for the default complete claim checker"
        ),
    )
    route.add_argument(
        "--source-only",
        action="store_true",
        help="check only Rust source correspondence for isolated mutation replay",
    )
    route.add_argument(
        "--exact-only",
        action="store_true",
        help="check only the exact rational identity for isolated mutation replay",
    )
    route.add_argument(
        "--binary64-only",
        action="store_true",
        help="check only the committed binary64 corpus for isolated mutation replay",
    )
    route.add_argument(
        "--enclosure-only",
        action="store_true",
        help="check only the separate exact-rational directed-enclosure route",
    )
    route.add_argument(
        "--catalog-only",
        action="store_true",
        help="check only the exact KSG method-catalog binding for isolated mutation replay",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = args.repo_root.resolve()
        if args.claim_only:
            manifest = check_claim_route(repo_root)
            packet_files = manifest["packet_files"]
            historical_hashes = manifest["historical_hashes"]
            print(
                "KSG harmonic-revision claim check passed: active revision 4 "
                f"{manifest['status']}; {len(packet_files)} mapped files; "
                f"{len(historical_hashes)} historical hashes; "
                f"stage={manifest['packet_stage']}"
            )
            return 0
        if args.release_only:
            check_release_route(repo_root)
            print(
                "KSG harmonic-revision release check passed: 15 affected and "
                "22 protected families"
            )
            return 0
        if args.source_only:
            check_source_route(repo_root)
            print("KSG harmonic-revision source check passed")
            return 0
        if args.exact_only:
            check_exact_route()
            print("KSG harmonic-revision exact check passed: 6,920 tuples")
            return 0
        if args.binary64_only:
            check_binary64_route(load_fixture(repo_root))
            print(
                "KSG harmonic-revision binary64 check passed: 8,198 Decimal cells; "
                "binary64-rounded-reference max 8 eps with 40 ties, allowed 32 eps; "
                "exact-rational error is checked separately; zero source-swap asymmetries"
            )
            return 0
        if args.enclosure_only:
            check_exact_enclosure_route(repo_root)
            print(
                "KSG harmonic-revision exact-enclosure check passed: "
                "8,198 directed intervals; 6,920 exact-Fraction containments; "
                "29-mutation suite is a separate gate"
            )
            return 0
        if args.catalog_only:
            check_catalog_route(repo_root)
            print(
                "KSG harmonic-revision catalog check passed: 20 affected and 6 formal-bound methods"
            )
            return 0
        manifest = check_claim_route(repo_root)
        check_release_route(repo_root)
        check_exact_route()
        fixture = load_fixture(repo_root)
        check_binary64_route(fixture)
        check_exact_enclosure_route(repo_root)
        check_source_route(repo_root)
        check_catalog_route(repo_root)
        require_default_integration_go(manifest)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision check failed: {error}", file=sys.stderr)
        return 1
    print(
        "KSG harmonic-revision check passed: 6,920 exact tuples and 8,198 Decimal cells; "
        "binary64-rounded-reference max 8 eps with 40 ties, allowed 32 eps; "
        "exact-rational error is checked separately; zero source-swap asymmetries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
