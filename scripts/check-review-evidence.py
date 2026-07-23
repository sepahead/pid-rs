#!/usr/bin/env python3
"""Generate and validate bounded review-evidence registries and the tagged file inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, cast

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
SCOPE = ROOT / "release-scope-1.0.json"
ASSURANCE_REGISTRY = ROOT / "audit" / "evidence" / "assurance-registry.json"
TASK_DISPOSITIONS = ROOT / "audit" / "evidence" / "task-dispositions.json"
FILE_REVIEW_LEDGER = ROOT / "audit" / "evidence" / "FILE_REVIEW_LEDGER.csv"
ASSURANCE_SCHEMA = ROOT / "audit" / "schemas" / "assurance-registry.schema.json"
TASK_SCHEMA = ROOT / "audit" / "schemas" / "task-dispositions.schema.json"
HANDOFF_INTAKE = ROOT / "audit" / "evidence" / "handoff-intake.json"

TAG = "v0.9.0"
TAG_OBJECT = "dafa6cc9655eee70b4524ac92993c0dd820477e0"
TAGGED_COMMIT = "a9a275157237999c8da6ab813130d74f6113dec9"
INTAKE_COMMIT = "85b3d3e463cad77e4fd36c434dfe1633e2420825"
HANDOFF_LEDGER_DECLARED_COMMIT = "64060035ea36e380004949f06dd226dcc7242b96"
HANDOFF_LEDGER_SHA256 = (
    "d1a03ea81d2dcb2a99f58c19c292bdcd62c5164273eea0e41704bfed21ed8b8d"
)

LAYER_SPECS = (
    ("definition", "DEF"),
    ("exact_algebra", "ALG"),
    ("rust_refinement", "RUST"),
    ("floating_point_numerical_behavior", "NUM"),
    ("statistical_application_validity", "STAT"),
)

PID2_Z3_EVIDENCE = (
    "audit/formal/z3/pid2-reconstruction.smt2",
    "audit/formal/z3/pid2-self-redundancy-mobius.smt2",
    "audit/formal/z3/pid2-source-swap.smt2",
    "scripts/check-z3-pid2-algebra-self-test.py",
    "scripts/check-z3-pid2-algebra.py",
)
PID2_Z3_FAMILIES = {
    "pid-core.stable.categorical",
    "pid-core.stable.imin",
    "pid-core.experimental.continuous.pid2",
}
PID3_Z3_EVIDENCE = (
    "audit/formal/z3/pid3-mobius-reconstruction.smt2",
    "audit/formal/z3/pid3-source-permutation.smt2",
    "scripts/check-z3-pid2-algebra-self-test.py",
    "scripts/check-z3-pid2-algebra.py",
)
PID3_Z3_FAMILIES = {
    "pid-core.experimental.continuous.incomplete-pid3",
    "pid-core.research.mixed-dimension-pid3",
}
PID_Z3_EVIDENCE = (
    "audit/formal/z3/pid2-reconstruction.smt2",
    "audit/formal/z3/pid2-self-redundancy-mobius.smt2",
    "audit/formal/z3/pid2-source-swap.smt2",
    "audit/formal/z3/pid3-mobius-reconstruction.smt2",
    "audit/formal/z3/pid3-source-permutation.smt2",
    "scripts/check-z3-pid2-algebra-self-test.py",
    "scripts/check-z3-pid2-algebra.py",
)
FINITE_ALPHABET_CONVERGENCE_EVIDENCE = (
    "FINITE_ALPHABET_PLUGIN_CONVERGENCE.md",
    "audit/formal/latex/finite-alphabet-plugin-convergence.tex",
    "audit/formal/lean/PidFiniteConvergence.lean",
    "audit/formal/lean/PidFiniteConvergence/Deterministic.lean",
    "audit/formal/lean/lake-manifest.json",
    "audit/formal/lean/lakefile.toml",
    "audit/formal/lean/lean-toolchain",
    "crates/pid-core/tests/finite_alphabet_plugin_oracle.rs",
    "crates/pid-core/tests/fixtures/finite_alphabet_plugin_oracle.json",
    "crates/pid-core/tests/fixtures/finite_alphabet_plugin_oracle.json.sha256",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "scripts/check-finite-alphabet-convergence-pdf.sh",
    "scripts/check-lean-finite-convergence.py",
    "scripts/generate-finite-alphabet-plugin-oracle.py",
)
FINITE_ALPHABET_CONVERGENCE_FAMILIES = {
    "pid-core.diagnostics.invariants",
    "pid-core.stable.categorical",
    "pid-core.stable.imin",
    "pid-core.stable.quantized",
}
DEPENDENCY_COLORED_SXPID_FAMILIES = {
    "pid-core.stable.categorical",
}
DEPENDENCY_COLORED_SXPID_EVIDENCE = (
    "DEPENDENCY_COLORED_SXPID_CONCENTRATION.md",
    "audit/formal/latex/dependency-colored-sxpid-concentration.tex",
    "audit/formal/lean/PidFiniteConvergence/Dependence.lean",
    "crates/pid-core/tests/dependency_colored_sxpid_oracle.rs",
    "crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json",
    "crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json.sha256",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "scripts/check-dependency-colored-sxpid-pdf.sh",
    "scripts/generate-dependency-colored-sxpid-oracle.py",
)

LEDGER_COLUMNS = (
    "path",
    "git_blob_id",
    "sha256",
    "bytes",
    "lines",
    "language",
    "generated",
    "generator",
    "public_surface",
    "security_critical",
    "science_critical",
    "authority_critical",
    "reviewer",
    "review_status",
    "requirements",
    "assumptions",
    "defects",
    "tests",
    "evidence",
    "disposition",
    "completed_at",
)

FAMILY_EVIDENCE: dict[str, tuple[str, ...]] = {
    "pid-core.infrastructure": (
        "audit/api/public-api/pid-core-signature-revisions.json",
        "audit/schemas/public-rust-api-signature-revisions.schema.json",
        "crates/pid-core/build.rs",
        "crates/pid-core/build_support.rs",
        "crates/pid-core/identity/software-identity-reference-v1.json",
        "crates/pid-core/src/identity.rs",
        "crates/pid-core/src/matrix.rs",
        "crates/pid-core/src/resource.rs",
        "crates/pid-core/tests/continuous_resource_contracts.rs",
        "crates/pid-core/tests/discrete_resource_contracts.rs",
        "crates/pid-core/tests/software_identity.rs",
        "crates/pid-core/tests/software_identity_build.rs",
        "crates/pid-python/src/v1.rs",
        "crates/pid-python/tests/test_v1.py",
        "scripts/check-release-scope.py",
        "scripts/check-software-identity-self-test.py",
        "scripts/check-software-identity.py",
    ),
    "pid-core.stable.categorical": (
        *FINITE_ALPHABET_CONVERGENCE_EVIDENCE,
        *DEPENDENCY_COLORED_SXPID_EVIDENCE,
        "crates/pid-core/src/sxpid.rs",
        "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
        "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json.sha256",
        "crates/pid-core/tests/sxpid_axioms.rs",
        "crates/pid-core/tests/sxpid_exhaustive_oracle.rs",
        "crates/pid-core/tests/sxpid_properties.rs",
        "scripts/generate-sxpid2-exhaustive-oracle.py",
        *PID2_Z3_EVIDENCE,
    ),
    "pid-core.stable.quantized": (
        *FINITE_ALPHABET_CONVERGENCE_EVIDENCE,
        "crates/pid-core/src/quantizer.rs",
        "crates/pid-core/tests/fitted_quantized_sxpid.rs",
        "crates/pid-core/tests/preprocess.rs",
    ),
    "pid-core.stable.imin": (
        *FINITE_ALPHABET_CONVERGENCE_EVIDENCE,
        "crates/pid-core/src/discrete_pid.rs",
        "crates/pid-core/tests/discrete_pid_properties.rs",
        "crates/pid-core/tests/imin.rs",
        *PID2_Z3_EVIDENCE,
    ),
    "pid-core.stable.continuous": (
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/src/stats.rs",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256",
        "crates/pid-core/tests/ksg.rs",
        "crates/pid-core/tests/ksg_report.rs",
        "scripts/generate-ksg-local-arithmetic-oracle.py",
    ),
    "pid-core.stable.preprocessing": (
        "crates/pid-core/src/preprocess.rs",
        "crates/pid-core/tests/preprocess.rs",
    ),
    "pid-core.diagnostics.distance-matrix": (
        "crates/pid-core/src/distance_matrix.rs",
        "crates/pid-core/tests/distance_matrix.rs",
    ),
    "pid-core.diagnostics.geometry": (
        "crates/pid-core/src/geometry.rs",
        "crates/pid-core/tests/geometry.rs",
    ),
    "pid-core.diagnostics.invariants": (
        *FINITE_ALPHABET_CONVERGENCE_EVIDENCE,
        "crates/pid-core/src/invariants.rs",
        "crates/pid-core/tests/invariants.rs",
    ),
    "pid-core.diagnostics.support": (
        "crates/pid-core/src/support.rs",
        "crates/pid-core/tests/continuous_reports.rs",
    ),
    "pid-core.experimental.continuous.co-information": (
        "crates/pid-core/src/ci.rs",
        "crates/pid-core/tests/continuous_reports.rs",
    ),
    "pid-core.experimental.continuous.isx": (
        "crates/pid-core/src/isx.rs",
        "crates/pid-core/tests/isx.rs",
        "crates/pid-core/tests/sxpid_gaussian_oracle.rs",
    ),
    "pid-core.experimental.continuous.shared-ksg-config": (
        "crates/pid-core/src/isx.rs",
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
        "crates/pid-core/tests/cross_validation.rs",
        "scripts/generate-ksg-local-arithmetic-oracle.py",
    ),
    "pid-core.experimental.continuous.pid2": (
        "crates/pid-core/src/pid2.rs",
        "crates/pid-core/tests/gaussian_pid_atoms.rs",
        "crates/pid-core/tests/pid2.rs",
        *PID2_Z3_EVIDENCE,
    ),
    "pid-core.experimental.continuous.incomplete-pid3": (
        "crates/pid-core/src/pid3.rs",
        "crates/pid-core/tests/pid3_partial.rs",
        *PID3_Z3_EVIDENCE,
    ),
    "pid-core.research.raw-ksg": (
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/src/stats.rs",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256",
        "crates/pid-core/tests/ksg.rs",
        "scripts/generate-ksg-local-arithmetic-oracle.py",
    ),
    "pid-core.research.raw-isx": (
        "crates/pid-core/src/isx.rs",
        "crates/pid-core/tests/isx.rs",
    ),
    "pid-core.research.raw-co-information": (
        "crates/pid-core/src/ci.rs",
        "crates/pid-core/tests/continuous_reports.rs",
    ),
    "pid-core.research.isx-heuristics": (
        "crates/pid-core/src/isx.rs",
        "crates/pid-core/tests/known_failures.rs",
    ),
    "pid-core.research.mixed-dimension-pid3": (
        "crates/pid-core/src/pid3.rs",
        "crates/pid-core/tests/known_failures.rs",
        "crates/pid-core/tests/pid3.rs",
        *PID3_Z3_EVIDENCE,
    ),
    "pid-core.research.hyperbolic": (
        "crates/pid-core/src/hyperbolic.rs",
        "crates/pid-core/tests/hyperbolic_mi.rs",
    ),
    "pid-core.experimental.hierarchy": (
        "crates/pid-core/src/hierarchy.rs",
        "crates/pid-core/tests/hierarchy.rs",
    ),
    "pid-core.experimental.pipelines.block-resampling": (
        "crates/pid-core/src/bootstrap.rs",
        "crates/pid-core/tests/sxpid_bootstrap.rs",
    ),
    "pid-core.experimental.pipelines.same-sample-quantization": (
        "crates/pid-core/src/same_sample.rs",
        "crates/pid-core/tests/known_failures.rs",
    ),
    "pid-core.experimental.pipelines.logistic-regression": (
        "crates/pid-core/src/logistic.rs",
        "crates/pid-core/src/pipeline.rs",
    ),
    "pid-core.experimental.pipelines.fdr-adjustment": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/permutation_and_fdr.rs",
    ),
    "pid-core.experimental.pipelines.quantized-sxpid-bootstrap": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/sxpid_bootstrap.rs",
    ),
    "pid-core.experimental.pipelines.row-bootstrap": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/sxpid_bootstrap.rs",
    ),
    "pid-core.experimental.pipelines.permutation-contracts": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/permutation_and_fdr.rs",
    ),
    "pid-core.experimental.pipelines.pid3-permutation": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/permutation_and_fdr.rs",
    ),
    "pid-core.experimental.pipelines.row-permutation": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/permutation_and_fdr.rs",
    ),
    "pid-core.experimental.pipelines.pls-selection-and-composition": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/src/pls.rs",
        "crates/pid-core/tests/cross_validation.rs",
    ),
    "pid-core.experimental.pipelines.pid2-screening": (
        "crates/pid-core/src/pipeline.rs",
        "crates/pid-core/tests/cross_validation.rs",
    ),
    "pid-core.experimental.pipelines.gaussian-noise-provenance": (
        "crates/pid-core/src/observation.rs",
        "crates/pid-core/src/preprocess.rs",
        "crates/pid-core/tests/observation_noise.rs",
        "crates/pid-core/tests/preprocess.rs",
    ),
    "pid-core.experimental.pipelines.jitter-preprocessing": (
        "crates/pid-core/src/preprocess.rs",
        "crates/pid-core/tests/preprocess.rs",
    ),
}

ALGEBRA_NOT_APPLICABLE = {
    "pid-core.infrastructure",
    "pid-core.stable.preprocessing",
    "pid-core.diagnostics.distance-matrix",
    "pid-core.diagnostics.support",
    "pid-core.experimental.pipelines.block-resampling",
    "pid-core.experimental.pipelines.same-sample-quantization",
    "pid-core.experimental.pipelines.logistic-regression",
    "pid-core.experimental.pipelines.row-bootstrap",
    "pid-core.experimental.pipelines.permutation-contracts",
    "pid-core.experimental.pipelines.row-permutation",
    "pid-core.experimental.pipelines.gaussian-noise-provenance",
    "pid-core.experimental.pipelines.jitter-preprocessing",
}
ALGEBRA_UNPROVED = {
    "pid-core.research.isx-heuristics",
}
STATISTICS_NOT_APPLICABLE = {
    "pid-core.infrastructure",
    "pid-core.stable.preprocessing",
    "pid-core.diagnostics.distance-matrix",
}
NUMERICS_NOT_APPLICABLE = {"pid-core.infrastructure"}

LOCAL_EVIDENCE_TASKS = {
    *(f"T{index:03d}" for index in range(10)),
    "T130",
    "T131",
    "T132",
    "T133",
    "T134",
    "T135",
    "T138",
    "T149",
}
EXTERNAL_TASKS = {"T139", "T142", "T144", "T153"}
FORMAL_EVIDENCE_TASKS = {"T132", "T133"}
MILESTONE_IMPLEMENTED_TASKS = {"T145", "T146", "T147", "T148"}
REMOVED_CLAIM_TASKS: set[str] = set()

TASK_EVIDENCE: dict[str, tuple[str, ...]] = {
    "T000": (
        "audit/evidence/FILE_REVIEW_LEDGER.csv",
        "audit/evidence/handoff-intake.json",
        "audit/evidence/repository-snapshot.json",
    ),
    "T001": ("audit/evidence/FILE_REVIEW_LEDGER.csv",),
    "T002": ("audit/evidence/FILE_REVIEW_LEDGER.csv",),
    "T003": ("release-scope-1.0.json",),
    "T004": ("KNOWN_LIMITATIONS.md", "audit/evidence/assurance-registry.json"),
    "T005": (".github/workflows/ci.yml", "RELEASE_AUDIT.md"),
    "T006": ("audit/evidence/handoff-intake.json", "KNOWN_LIMITATIONS.md"),
    "T007": ("Cargo.lock", "deny.toml", ".github/workflows/ci.yml"),
    "T008": (
        "audit/evidence/assurance-registry.json",
        "audit/evidence/task-dispositions.json",
    ),
    "T009": ("release-scope-1.0.json", "RELEASE_SCOPE_1_0.md"),
    "T130": ("audit/evidence/assurance-registry.json",),
    "T131": ("audit/evidence/assurance-registry.json",),
    "T132": PID_Z3_EVIDENCE,
    "T133": PID_Z3_EVIDENCE,
    "T134": (
        "scripts/generate-sxpid2-exhaustive-oracle.py",
        "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
    ),
    "T135": (
        "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
        "crates/pid-core/tests/sxpid_exhaustive_oracle.rs",
    ),
    "T138": (
        "scripts/generate-ksg-local-arithmetic-oracle.py",
        "scripts/generate-sxpid2-exhaustive-oracle.py",
        "crates/pid-core/src/stats.rs",
        "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
        "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
        "crates/pid-core/tests/sxpid_exhaustive_oracle.rs",
    ),
    "T145": (
        "crates/pid-core/src/quantizer.rs",
        "crates/pid-core/tests/fitted_quantized_sxpid.rs",
        "MIGRATION.md",
    ),
    "T146": (
        "crates/pid-core/src/ksg.rs",
        "crates/pid-core/tests/ksg_report.rs",
        "MIGRATION.md",
    ),
    "T147": (
        ".github/workflows/review-release.yml",
        "RELEASE_NOTES.md",
        "scripts/check-release-state.sh",
    ),
    "T148": (
        "release-scope-1.0.json",
        "scripts/check-release-scope.py",
    ),
    "T149": ("audit/evidence/assurance-registry.json",),
}


class ReviewEvidenceError(RuntimeError):
    """A registry, disposition, tag identity, or file inventory is inconsistent."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReviewEvidenceError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def canonical_json_bytes(value: Any) -> bytes:
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


def load_json_bytes(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReviewEvidenceError(f"cannot parse {label}: {error}") from error


def git_output(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ReviewEvidenceError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def git_bytes(*args: str) -> bytes:
    process = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", "replace").strip()
        raise ReviewEvidenceError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout


def load_handoff_intake() -> dict[str, Any]:
    raw = HANDOFF_INTAKE.read_bytes()
    intake = load_json_bytes(raw, label="handoff-intake.json")
    if raw != canonical_json_bytes(intake):
        raise ReviewEvidenceError("handoff intake is not canonical JSON")
    if not isinstance(intake, dict) or not isinstance(intake.get("pid_ledger"), dict):
        raise ReviewEvidenceError("handoff intake has no PID ledger identity")
    ledger = intake["pid_ledger"]
    expected_ledger = {
        "sha256": HANDOFF_LEDGER_SHA256,
        "task_count": 159,
        "task_id_set": "T000..T158 inclusive",
    }
    for key, expected in expected_ledger.items():
        if ledger.get(key) != expected:
            raise ReviewEvidenceError(f"handoff intake PID ledger {key} differs from dispositions")
    if intake.get("repository_frozen_commit") != INTAKE_COMMIT:
        raise ReviewEvidenceError("handoff intake repository commit differs from dispositions")
    if intake.get("disposition", {}).get("completion_evidence") is not False:
        raise ReviewEvidenceError("handoff intake must remain non-completion evidence")
    return intake


def require_release_boundary(*, require_handoff_object: bool = False) -> None:
    load_handoff_intake()
    if git_output("rev-parse", f"refs/tags/{TAG}") != TAG_OBJECT:
        raise ReviewEvidenceError("review tag object differs from the immutable release boundary")
    if git_output("rev-parse", f"refs/tags/{TAG}^{{commit}}") != TAGGED_COMMIT:
        raise ReviewEvidenceError("review tag peels to a different commit")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", INTAKE_COMMIT, TAGGED_COMMIT],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestry.returncode != 0:
        raise ReviewEvidenceError("tagged commit does not descend from the recorded intake cut")
    object_type = subprocess.run(
        ["git", "cat-file", "-t", HANDOFF_LEDGER_DECLARED_COMMIT],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if object_type.returncode == 0:
        if object_type.stdout.strip() != "commit":
            raise ReviewEvidenceError("handoff ledger commit identity is not a commit object")
        old_ancestry = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                HANDOFF_LEDGER_DECLARED_COMMIT,
                TAGGED_COMMIT,
            ],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if old_ancestry.returncode == 0:
            raise ReviewEvidenceError(
                "handoff ledger commit is unexpectedly an ancestor of the tagged commit"
            )
        if old_ancestry.returncode != 1:
            raise ReviewEvidenceError("cannot determine handoff ledger commit lineage")
    elif require_handoff_object:
        raise ReviewEvidenceError(
            "handoff ledger commit object is required for evidence regeneration"
        )


def safe_repo_file(relative: str) -> Path:
    candidate_relative = Path(relative)
    if not relative or candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise ReviewEvidenceError(f"unsafe evidence path: {relative!r}")
    current = ROOT
    for component in candidate_relative.parts:
        current /= component
        if current.is_symlink():
            raise ReviewEvidenceError(f"symlink evidence path is forbidden: {relative!r}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(ROOT.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ReviewEvidenceError(f"missing or escaping evidence path: {relative!r}") from error
    if not resolved.is_file():
        raise ReviewEvidenceError(f"evidence path is not a regular file: {relative!r}")
    return resolved


def load_release_scope() -> tuple[dict[str, Any], bytes]:
    raw = SCOPE.read_bytes()
    scope = load_json_bytes(raw, label="release-scope-1.0.json")
    if raw != canonical_json_bytes(scope):
        raise ReviewEvidenceError("release scope is not canonical JSON")
    if not isinstance(scope, dict) or not isinstance(scope.get("families"), list):
        raise ReviewEvidenceError("release scope has no family list")
    return scope, raw


def layer_status(family_id: str, layer_name: str, stability: str) -> str:
    if layer_name == "definition":
        return "DOCUMENTED"
    if layer_name == "rust_refinement":
        return "TESTED"
    if layer_name == "exact_algebra":
        if family_id in ALGEBRA_NOT_APPLICABLE:
            return "NOT_APPLICABLE"
        if family_id in ALGEBRA_UNPROVED:
            return "UNPROVED"
        if family_id in PID2_Z3_FAMILIES or family_id in PID3_Z3_FAMILIES:
            return "BOUNDED"
        return "TESTED"
    if layer_name == "floating_point_numerical_behavior":
        return "NOT_APPLICABLE" if family_id in NUMERICS_NOT_APPLICABLE else "BOUNDED"
    if family_id in STATISTICS_NOT_APPLICABLE:
        return "NOT_APPLICABLE"
    if stability in {"experimental", "research-only", "unsupported"}:
        return "NOT_CLAIMED"
    return "ASSUMPTION_GATED"


def assurance_claim(
    layer_name: str, status: str, family_id: str, family: dict[str, Any]
) -> str:
    if layer_name == "definition":
        return (
            f"The registry records definition revision {family['definition_revision']} for "
            f"{family_id}; documentation evidence is not an independent validation."
        )
    if layer_name == "exact_algebra":
        if status == "NOT_APPLICABLE":
            return "No exact scientific-algebra qualification applies to this declared family."
        if status == "UNPROVED":
            return "No complete exact-algebra proof is claimed for this family."
        if family_id in FINITE_ALPHABET_CONVERGENCE_FAMILIES:
            if family_id in DEPENDENCY_COLORED_SXPID_FAMILIES:
                prefix = (
                    "Pinned Lean proves only deterministic exact-real continuity and "
                    "dependency-color algebraic lemmas for categorical SxPID. It does not encode "
                    "the stochastic theorem, the complete SxPID method, Rust refinement, or "
                    "binary64 behavior. "
                )
            else:
                prefix = (
                    "Pinned Lean proves only generic deterministic exact-real continuity lemmas. "
                    "It does not encode the stochastic theorem, a complete PID or Shannon method, "
                    "Rust refinement, or binary64 behavior. "
                )
            if family_id in PID2_Z3_FAMILIES:
                return prefix + (
                    "Separate pinned QF_LRA queries cover only two-source reconstruction, "
                    "formula-level source exchange, and four-node inversion identities."
                )
            return prefix + (
                "Checked fixtures exercise selected method identities and inputs; they are not "
                "an all-input proof."
            )
        if family_id in PID2_Z3_FAMILIES:
            return (
                "Pinned QF_LRA counterexample queries establish only the two-source four-atom "
                "reconstruction, formula-level source exchange, and four-node inversion "
                "identities over exact reals; estimator premises and larger lattices remain open."
            )
        if family_id in PID3_Z3_FAMILIES:
            return (
                "Pinned QF_LRA counterexample queries establish only 18-node three-source "
                "Mobius inversion, zeta reconstruction, and formula-level equivariance for "
                "two adjacent source swaps over exact reals; estimator premises, Rust "
                "refinement, floating-point behavior, and four-source lattices remain open."
            )
        return "Checked tests exercise selected identities and fixtures, not an all-input proof."
    if layer_name == "rust_refinement":
        return (
            "The safe-Rust implementation is exercised by checked tests; no deductive "
            "end-to-end refinement proof is inferred."
        )
    if layer_name == "floating_point_numerical_behavior":
        if status == "NOT_APPLICABLE":
            return "No floating-point scientific-result claim applies to this family."
        return "Numerical evidence is bounded to checked fixtures, profiles, and declared inputs."
    if status == "NOT_APPLICABLE":
        return "No statistical or application-validity claim applies to this family."
    if status == "NOT_CLAIMED":
        return "Statistical and application qualification is not claimed for this family."
    return "Use remains gated by the declared support domain and caller-supplied provenance."


def evidence_tier(layer_name: str, status: str) -> str:
    if status in {"NOT_APPLICABLE", "UNPROVED"}:
        return "NONE"
    if status in {"NOT_CLAIMED", "ASSUMPTION_GATED"}:
        return "ASSUMPTION_DECLARATION"
    if layer_name == "definition":
        return "DOCUMENTATION"
    if layer_name == "floating_point_numerical_behavior":
        return "BOUNDED_TEST"
    if status == "BOUNDED":
        return "BOUNDED_TEST"
    return "IMPLEMENTATION_TEST"


def assumption_statement(layer_name: str, family: dict[str, Any]) -> tuple[str, str, str]:
    if layer_name == "definition":
        return (
            "maintainers",
            "The release-scope family identifier and definition revision identify the intended public boundary.",
            "A mismatch can make callers reason about the wrong estimand or API boundary.",
        )
    if layer_name == "exact_algebra":
        if family["id"] in FINITE_ALPHABET_CONVERGENCE_FAMILIES:
            if family["id"] in DEPENDENCY_COLORED_SXPID_FAMILIES:
                formal_scope = (
                    "deterministic exact-real continuity and dependency-color algebra for "
                    "categorical SxPID"
                )
            else:
                formal_scope = "generic deterministic exact-real continuity"
            return (
                "maintainers",
                f"The pinned Lean artifact covers {formal_scope} only. The stochastic theorem, "
                "complete method definitions, Rust refinement, and binary64 behavior are outside "
                "it; every other fixture remains bounded to its listed inputs.",
                "Treating the partial formal core or bounded fixtures as an end-to-end method, "
                "implementation, numerical, or distributional proof would exceed the evidence.",
            )
        if family["id"] in PID2_Z3_FAMILIES:
            return (
                "maintainers",
                "The pinned obligations cover formula-level QF_LRA identities only; estimator "
                "symmetry premises, floating-point refinement, and larger lattices are outside "
                "their scope.",
                "Treating the bounded proof as an estimator or higher-source proof would exceed "
                "the recorded evidence.",
            )
        if family["id"] in PID3_Z3_FAMILIES:
            return (
                "maintainers",
                "The pinned obligations cover formula-level QF_LRA identities on the complete "
                "18-node three-source lattice only. Estimator premises, asymptotics, Rust "
                "refinement, floating-point behavior, and distributional claims are outside "
                "their scope.",
                "Treating the bounded proof as an estimator, implementation, numerical, or "
                "distributional proof would exceed the recorded evidence.",
            )
        return (
            "maintainers",
            "Checked identities and fixtures cover only their explicit finite domains and tolerances.",
            "An unchecked input can expose an algebraic defect not ruled out by the recorded tests.",
        )
    if layer_name == "rust_refinement":
        return (
            "maintainers",
            "Checked build and test profiles represent only the declared toolchains, features, and platforms.",
            "An unqualified profile can differ from the implementation behavior exercised by evidence.",
        )
    if layer_name == "floating_point_numerical_behavior":
        return (
            "caller",
            "Inputs remain inside the declared finite, support, and resource constraints.",
            "Conditioning, overflow, or finite-precision error can invalidate an out-of-domain result.",
        )
    return (
        "caller",
        str(family["support_domain"]),
        "Violating the declared domain can invalidate scientific or application interpretation.",
    )


def gap_record(layer_name: str, status: str) -> tuple[str, str]:
    if status == "NOT_APPLICABLE":
        return "The layer is outside the declared family claim.", "NOT_APPLICABLE"
    if layer_name == "definition":
        return (
            "Independent definition review is not recorded by this artifact.",
            "BLOCKED_EXTERNAL",
        )
    if layer_name == "exact_algebra":
        return (
            "No accepted complete formal proof over the declared family is recorded.",
            "OPEN_LOCAL",
        )
    if layer_name == "rust_refinement":
        return (
            "No accepted deductive end-to-end Rust refinement proof is recorded.",
            "OPEN_LOCAL",
        )
    if layer_name == "floating_point_numerical_behavior":
        return (
            "No global floating-point error bound or all-input conditioning theorem is recorded.",
            "OPEN_LOCAL",
        )
    return (
        "No deployment, field-validity, or universal-consistency qualification is recorded.",
        "NOT_CLAIMED",
    )


def build_assurance_registry() -> dict[str, Any]:
    scope, scope_raw = load_release_scope()
    families = scope["families"]
    scope_ids = [family.get("id") for family in families]
    if len(scope_ids) != 35 or len(scope_ids) != len(set(scope_ids)):
        raise ReviewEvidenceError("release scope must contain exactly 35 unique families")
    if set(scope_ids) != set(FAMILY_EVIDENCE):
        missing = sorted(set(scope_ids) - set(FAMILY_EVIDENCE))
        extra = sorted(set(FAMILY_EVIDENCE) - set(scope_ids))
        raise ReviewEvidenceError(
            f"family evidence map mismatch; missing={missing!r}, extra={extra!r}"
        )

    records: list[dict[str, Any]] = []
    for index, family in enumerate(families, start=1):
        family_id = family["id"]
        stability = family["software_stability"]
        evidence = sorted(
            {
                "KNOWN_LIMITATIONS.md",
                "crates/pid-core/README.md",
                "release-scope-1.0.json",
                *FAMILY_EVIDENCE[family_id],
            }
        )
        layers: dict[str, Any] = {}
        for layer_name, layer_code in LAYER_SPECS:
            status = layer_status(family_id, layer_name, stability)
            owner, statement, consequence = assumption_statement(layer_name, family)
            gap_statement, disposition = gap_record(layer_name, status)
            prefix = f"F{index:03d}-{layer_code}"
            layers[layer_name] = {
                "assumptions": [
                    {
                        "failure_consequence": consequence,
                        "id": f"ASM-{prefix}",
                        "owner": owner,
                        "statement": statement,
                    }
                ],
                "assurance": {
                    "claim": assurance_claim(layer_name, status, family_id, family),
                    "evidence": evidence,
                    "evidence_tier": evidence_tier(layer_name, status),
                    "id": f"ASSUR-{prefix}",
                    "status": status,
                },
                "gaps": [
                    {
                        "disposition": disposition,
                        "id": f"GAP-{prefix}",
                        "statement": gap_statement,
                    }
                ],
            }
        records.append(
            {
                "definition_revision": family["definition_revision"],
                "estimator_revision": family["estimator_revision"],
                "family_id": family_id,
                "layers": layers,
                "software_stability": stability,
            }
        )

    return {
        "families": records,
        "generated_by": "scripts/check-review-evidence.py",
        "release_boundary": {
            "final_decision_claimed": False,
            "independent_review_claimed": False,
            "tag": TAG,
            "tag_object_sha": TAG_OBJECT,
            "tagged_commit_sha": TAGGED_COMMIT,
            "v0_9_source_review_status": "COMPLETED",
            "v0_9_task_qualification_claimed": False,
            "v1_0_qualification_status": "NOT_QUALIFIED",
        },
        "release_scope_sha256": hashlib.sha256(scope_raw).hexdigest(),
        "schema": "pid-rs/assurance-registry",
        "schema_revision": 1,
    }


def task_scope_note(task_id: str) -> str:
    notes = {
        "T132": (
            "Pinned QF_LRA obligations cover exact-real PID2 source exchange and PID3 "
            "formula-level equivariance for two adjacent source swaps. They do not establish "
            "estimator symmetry premises, Rust or floating-point refinement, a Lean "
            "development, or any four-source result."
        ),
        "T133": (
            "Pinned QF_LRA obligations cover inversion followed by reconstruction on the "
            "two-source four-node lattice and the complete three-source 18-node lattice. "
            "Four-source lattices, estimator premises, Rust refinement, floating-point "
            "behavior, and a complete mechanized development remain open."
        ),
        "T138": (
            "Bounded evidence covers 494 nonempty binary SxPID2 count tables with total mass "
            "at most four and 8,198 KSG local-digamma cases exhaustive through 16 samples plus "
            "fixed stress tuples through one million. Broader high-precision estimator coverage, "
            "neighbor search, support validity, and application validity remain open."
        ),
        "T145": (
            "The 0.9 milestone implements domain-separated quantizer input and categorical-output "
            "hashes with migration and vector tests; the task's full 1.0 acceptance record remains open."
        ),
        "T146": (
            "The 0.9 milestone removes the permanently false KSG fallback field and tests the "
            "truthful backend report; the task's full 1.0 acceptance record remains open."
        ),
        "T147": (
            "The 0.9 milestone reconciles the immutable source-review release, tag, citation, "
            "archive, and promotion boundary; final 1.0 publication qualification remains open."
        ),
        "T148": (
            "The 0.9 milestone records definition and estimator revisions separately from crate "
            "and schema versions for all release-scope families; full 1.0 acceptance remains open."
        ),
        "T156": (
            "Cross-repository compatibility is not claimed, but the required local convergence "
            "manifest and explicit handoff remain absent, so this task stays open."
        ),
    }
    if task_id in notes:
        return notes[task_id]
    if task_id in EXTERNAL_TASKS:
        return (
            "The required independent custody, reproduction, or review evidence is external and "
            "is not represented as completed by this repository artifact."
        )
    if task_id in LOCAL_EVIDENCE_TASKS:
        return (
            "A bounded local inventory, registry, or oracle artifact is recorded, but the full "
            "twenty-lens task acceptance and independent completion evidence remain open."
        )
    return (
        "This artifact records no complete task-acceptance packet; implementation and full 1.0 "
        "qualification are not inferred."
    )


def build_task_dispositions() -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for index in range(159):
        task_id = f"T{index:03d}"
        if task_id in REMOVED_CLAIM_TASKS:
            disposition = "CLAIM_REMOVED"
            reason = "ASSOCIATED_CROSS_REPOSITORY_CLAIM_REMOVED"
        elif task_id in EXTERNAL_TASKS:
            disposition = "BLOCKED_EXTERNAL"
            reason = "EXTERNAL_CUSTODY_OR_REPRODUCTION_REQUIRED"
        elif task_id in MILESTONE_IMPLEMENTED_TASKS:
            disposition = "OPEN_LOCAL"
            reason = "MILESTONE_IMPLEMENTED_FULL_QUALIFICATION_OPEN"
        elif task_id == "T156":
            disposition = "OPEN_LOCAL"
            reason = "CROSS_REPOSITORY_QUALIFICATION_NOT_CLAIMED"
        else:
            disposition = "OPEN_LOCAL"
            reason = (
                "BOUNDED_FORMAL_EVIDENCE_ADDED"
                if task_id in FORMAL_EVIDENCE_TASKS
                else (
                    "LOCAL_REGISTRY_OR_INVENTORY_ADDED"
                    if task_id in LOCAL_EVIDENCE_TASKS
                    else "FULL_ACCEPTANCE_RECORD_NOT_PRESENT"
                )
            )
        tasks.append(
            {
                "evidence": list(
                    TASK_EVIDENCE.get(task_id, ("audit/evidence/handoff-intake.json",))
                ),
                "local_evidence_status": (
                    "IMPLEMENTED_AT_SOURCE_REVIEW_MILESTONE"
                    if task_id in MILESTONE_IMPLEMENTED_TASKS
                    else (
                        "ARTIFACT_ADDED_UNREVIEWED"
                        if task_id in LOCAL_EVIDENCE_TASKS
                        else "NOT_ASSESSED_FOR_TASK_CLOSURE"
                    )
                ),
                "implementation_state": (
                    "IMPLEMENTED_AT_0_9_MILESTONE"
                    if task_id in MILESTONE_IMPLEMENTED_TASKS
                    else (
                        "BOUNDED_EVIDENCE_ADDED_POST_TAG"
                        if task_id in LOCAL_EVIDENCE_TASKS
                        else "NOT_ESTABLISHED_BY_THIS_ARTIFACT"
                    )
                ),
                "reason_code": reason,
                "scope_note": task_scope_note(task_id),
                "task_id": task_id,
                "v0_9_source_review_disposition": "NOT_USED_TO_QUALIFY_TASK",
                "v1_0_disposition": disposition,
            }
        )
    counts = {
        status: sum(task["v1_0_disposition"] == status for task in tasks)
        for status in ("BLOCKED_EXTERNAL", "CLAIM_REMOVED", "OPEN_LOCAL")
    }
    return {
        "generated_by": "scripts/check-review-evidence.py",
        "release_boundary": {
            "final_decision_claimed": False,
            "independent_completion_claimed": False,
            "qualification_note": (
                "Bounded implementation evidence does not satisfy the full 1.0 task completion rule."
            ),
            "tag": TAG,
            "tag_object_sha": TAG_OBJECT,
            "tagged_commit_sha": TAGGED_COMMIT,
            "v0_9_source_review_status": "COMPLETED",
            "v1_0_qualification_status": "NOT_QUALIFIED",
        },
        "schema": "pid-rs/task-dispositions",
        "schema_revision": 1,
        "source": {
            "handoff_ledger_declared_commit": HANDOFF_LEDGER_DECLARED_COMMIT,
            "handoff_ledger_lineage_status": "NOT_ANCESTOR_OF_TAGGED_COMMIT",
            "handoff_ledger_sha256": HANDOFF_LEDGER_SHA256,
            "intake_commit_lineage_status": "ANCESTOR_OF_TAGGED_COMMIT",
            "intake_repository_commit": INTAKE_COMMIT,
            "task_id_set": "T000..T158 inclusive",
        },
        "summary": {
            "blocked_external": counts["BLOCKED_EXTERNAL"],
            "claim_removed": counts["CLAIM_REMOVED"],
            "open_local": counts["OPEN_LOCAL"],
            "qualified_complete": 0,
            "task_count": len(tasks),
        },
        "tasks": tasks,
    }


def language_for(path: str, data: bytes) -> tuple[str, int]:
    suffix = Path(path).suffix.lower()
    basename = Path(path).name
    mapping = {
        ".cff": "YAML",
        ".cfg": "configuration",
        ".json": "JSON",
        ".jsonl": "JSON Lines",
        ".md": "Markdown",
        ".py": "Python",
        ".pyi": "Python type stub",
        ".rs": "Rust",
        ".sh": "shell",
        ".svg": "SVG",
        ".toml": "TOML",
        ".txt": "text",
        ".yaml": "YAML",
        ".yml": "YAML",
    }
    language = mapping.get(suffix)
    if basename in {"Cargo.lock", "Cargo.toml", "deny.toml", "justfile"}:
        language = "TOML" if basename != "justfile" else "Just"
    elif basename.startswith("LICENSE"):
        language = "license text"
    elif basename in {".editorconfig", ".gitattributes", ".gitignore", ".mailmap"}:
        language = "configuration"
    if b"\0" in data:
        return language or "binary", 0
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return language or "binary", 0
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    return language or "text", lines


def generated_by(path: str) -> tuple[bool, str]:
    if path in {"Cargo.lock", "fuzz/Cargo.lock"}:
        return True, "cargo generate-lockfile"
    if path.startswith("audit/api/public-api/"):
        return True, "scripts/check-public-api-snapshots.sh"
    if path == "RELEASE_SCOPE_1_0.md":
        return (
            True,
            "python3 scripts/check-release-scope.py --print-markdown > RELEASE_SCOPE_1_0.md",
        )
    if path.startswith("audit/evidence/repository-snapshot"):
        return True, "scripts/collect-repository-snapshot.py"
    if path in {
        "crates/pid-core/tests/fixtures/csxpid_reference.json",
        "crates/pid-core/tests/fixtures/csxpid_reference.json.sha256",
    }:
        return True, "scripts/generate-csxpid-reference.py"
    if path == "audit/evidence/handoff-intake.json.sha256":
        return True, "shasum -a 256 audit/evidence/handoff-intake.json"
    if path == "fuzz/corpus/SHA256SUMS":
        return True, "sha256 digest inventory of fuzz/corpus seeds"
    return False, "not applicable"


def public_surface(path: str) -> bool:
    if path.endswith(("README.md", ".pyi")) or path in {
        "README.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "CONTRIBUTING.md",
        "KNOWN_LIMITATIONS.md",
        "MIGRATION.md",
        "RELEASE_NOTES.md",
        "RELEASE_SCOPE_1_0.md",
        "SECURITY.md",
        "Cargo.toml",
        "release-scope-1.0.json",
    }:
        return True
    return path.startswith("crates/") and (
        "/src/" in path or "/examples/" in path or path.endswith("Cargo.toml")
    )


def criticality(path: str) -> tuple[bool, bool, bool]:
    security = (
        path.startswith((".github/", "scripts/", "fuzz/"))
        or path in {"Cargo.lock", "Cargo.toml", "SECURITY.md", "deny.toml"}
        or any(token in path for token in ("resource", "runlog", "replay"))
    )
    science = (
        path.startswith("crates/pid-core/")
        or path in {
            "README.md",
            "KNOWN_LIMITATIONS.md",
            "MIGRATION.md",
            "RELEASE_SCOPE_1_0.md",
            "release-scope-1.0.json",
        }
    )
    authority = (
        path.startswith((".github/workflows/", "audit/evidence/", "audit/schemas/"))
        or path
        in {
            "CITATION.cff",
            "RELEASE_AUDIT.md",
            "RELEASE_NOTES.md",
            "RELEASE_REPRODUCTION.md",
            "SECURITY.md",
        }
    )
    return security, science, authority


def tagged_tree() -> list[tuple[str, str, bytes]]:
    raw = git_bytes("ls-tree", "-rz", "--full-tree", TAGGED_COMMIT)
    identities: list[tuple[str, str]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, encoded_path = item.split(b"\t", 1)
        mode, object_type, encoded_oid = metadata.split(b" ", 2)
        if object_type != b"blob":
            raise ReviewEvidenceError(
                f"unsupported tagged tree entry type {object_type!r} at {encoded_path!r}"
            )
        try:
            path = encoded_path.decode("utf-8")
            oid = encoded_oid.decode("ascii")
        except UnicodeDecodeError as error:
            raise ReviewEvidenceError("tagged tree paths and object IDs must be UTF-8/ASCII") from error
        if mode not in {b"100644", b"100755", b"120000"}:
            raise ReviewEvidenceError(f"unexpected blob mode {mode!r} for {path!r}")
        identities.append((path, oid))
    process = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input=("\n".join(oid for _, oid in identities) + "\n").encode("ascii"),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", "replace").strip()
        raise ReviewEvidenceError(f"git cat-file --batch failed: {detail}")
    records: list[tuple[str, str, bytes]] = []
    offset = 0
    for path, oid in identities:
        line_end = process.stdout.find(b"\n", offset)
        if line_end < 0:
            raise ReviewEvidenceError("truncated git cat-file batch header")
        header = process.stdout[offset:line_end].split(b" ")
        if len(header) != 3 or header[0] != oid.encode("ascii") or header[1] != b"blob":
            raise ReviewEvidenceError(f"unexpected git cat-file batch header for {path!r}")
        try:
            size = int(header[2])
        except ValueError as error:
            raise ReviewEvidenceError(f"invalid git object size for {path!r}") from error
        data_start = line_end + 1
        data_end = data_start + size
        if data_end >= len(process.stdout) or process.stdout[data_end : data_end + 1] != b"\n":
            raise ReviewEvidenceError(f"truncated git blob payload for {path!r}")
        records.append((path, oid, process.stdout[data_start:data_end]))
        offset = data_end + 1
    if offset != len(process.stdout):
        raise ReviewEvidenceError("unexpected trailing bytes from git cat-file batch")
    records.sort(key=lambda item: item[0].encode("utf-8"))
    if len(records) != 186:
        raise ReviewEvidenceError(
            f"tagged tree file count differs from the frozen 186-file inventory: {len(records)}"
        )
    return records


def build_file_review_ledger() -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=LEDGER_COLUMNS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for path, blob_id, data in tagged_tree():
        language, lines = language_for(path, data)
        generated, generator = generated_by(path)
        security, science, authority = criticality(path)
        writer.writerow(
            {
                "path": path,
                "git_blob_id": blob_id,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "lines": lines,
                "language": language,
                "generated": str(generated).lower(),
                "generator": generator,
                "public_surface": str(public_surface(path)).lower(),
                "security_critical": str(security).lower(),
                "science_critical": str(science).lower(),
                "authority_critical": str(authority).lower(),
                "reviewer": "UNASSIGNED",
                "review_status": "INVENTORIED_NOT_REVIEWED",
                "requirements": "T000;T001;T002",
                "assumptions": "exact-tag tree inventory only; no line review inferred",
                "defects": "not assessed by inventory",
                "tests": "scripts/check-review-evidence-self-test.py",
                "evidence": f"git tree {TAGGED_COMMIT}",
                "disposition": "inventory only; independent or human review not claimed",
                "completed_at": "",
            }
        )
    return stream.getvalue().encode("utf-8")


def load_schema(path: Path) -> dict[str, Any]:
    value = load_json_bytes(path.read_bytes(), label=str(path.relative_to(ROOT)))
    if not isinstance(value, dict):
        raise ReviewEvidenceError(f"schema is not an object: {path}")
    return cast(dict[str, Any], value)


def validate_evidence_paths(value: dict[str, Any]) -> None:
    evidence_paths: set[str] = set()
    if value.get("schema") == "pid-rs/assurance-registry":
        for family in value["families"]:
            for layer in family["layers"].values():
                evidence_paths.update(layer["assurance"]["evidence"])
    elif value.get("schema") == "pid-rs/task-dispositions":
        for task in value["tasks"]:
            evidence_paths.update(task["evidence"])
    else:
        raise ReviewEvidenceError("unknown evidence registry schema")
    for path in sorted(evidence_paths):
        safe_repo_file(path)


def validate_assurance_registry(raw: bytes) -> dict[str, Any]:
    value = load_json_bytes(raw, label="assurance-registry.json")
    schema = load_schema(ASSURANCE_SCHEMA)
    validate_json_schema(value, schema, name="assurance-registry.json")
    if raw != canonical_json_bytes(value):
        raise ReviewEvidenceError("assurance registry is not canonical JSON")
    expected = build_assurance_registry()
    if value != expected:
        raise ReviewEvidenceError("assurance registry differs from its canonical projection")
    family_ids = [family["family_id"] for family in value["families"]]
    scope, _ = load_release_scope()
    if family_ids != [family["id"] for family in scope["families"]]:
        raise ReviewEvidenceError("assurance families differ from release-scope order")
    expected_layer_names = {name for name, _ in LAYER_SPECS}
    all_ids: set[str] = set()
    for family in value["families"]:
        if set(family["layers"]) != expected_layer_names:
            raise ReviewEvidenceError("family does not have exactly the five required layers")
        for layer in family["layers"].values():
            identifiers = {
                layer["assurance"]["id"],
                *(item["id"] for item in layer["assumptions"]),
                *(item["id"] for item in layer["gaps"]),
            }
            if all_ids.intersection(identifiers):
                raise ReviewEvidenceError("assurance, assumption, and gap IDs must be unique")
            all_ids.update(identifiers)
    validate_evidence_paths(value)
    return cast(dict[str, Any], value)


def validate_task_dispositions(raw: bytes) -> dict[str, Any]:
    value = load_json_bytes(raw, label="task-dispositions.json")
    schema = load_schema(TASK_SCHEMA)
    validate_json_schema(value, schema, name="task-dispositions.json")
    if raw != canonical_json_bytes(value):
        raise ReviewEvidenceError("task dispositions are not canonical JSON")
    expected = build_task_dispositions()
    if value != expected:
        raise ReviewEvidenceError("task dispositions differ from the canonical projection")
    expected_ids = [f"T{index:03d}" for index in range(159)]
    task_ids = [task["task_id"] for task in value["tasks"]]
    if task_ids != expected_ids:
        raise ReviewEvidenceError("task dispositions must cover exactly T000 through T158")
    if any(task["v1_0_disposition"] == "QUALIFIED_COMPLETE" for task in value["tasks"]):
        raise ReviewEvidenceError("no 1.0 task may be represented as qualified complete")
    validate_evidence_paths(value)
    return cast(dict[str, Any], value)


def validate_file_review_ledger(raw: bytes) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReviewEvidenceError("file-review ledger must be UTF-8") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
        raise ReviewEvidenceError("file-review ledger must have the exact 21 required columns")
    rows = list(reader)
    if reader.restkey is not None or any(None in row for row in rows):
        raise ReviewEvidenceError("file-review ledger has malformed CSV rows")
    if len(rows) != 186 or len({row["path"] for row in rows}) != 186:
        raise ReviewEvidenceError("file-review ledger must cover 186 unique tagged paths")
    for row in rows:
        if len(row["git_blob_id"]) != 40 or any(
            character not in "0123456789abcdef" for character in row["git_blob_id"]
        ):
            raise ReviewEvidenceError("file-review ledger contains an invalid Git blob ID")
        if len(row["sha256"]) != 64 or any(
            character not in "0123456789abcdef" for character in row["sha256"]
        ):
            raise ReviewEvidenceError("file-review ledger contains an invalid SHA-256 digest")
        if row["generated"] not in {"true", "false"}:
            raise ReviewEvidenceError("file-review ledger generated flags must be boolean text")
        if row["generated"] == "true" and row["generator"] == "not applicable":
            raise ReviewEvidenceError("generated file has no reproducible generator record")
        for column in LEDGER_COLUMNS[:-1]:
            if column != "completed_at" and row[column] == "":
                raise ReviewEvidenceError(f"file-review ledger has an empty {column} value")
    if any(row["reviewer"] != "UNASSIGNED" for row in rows):
        raise ReviewEvidenceError("inventory must not infer reviewer assignment")
    if any(row["review_status"] != "INVENTORIED_NOT_REVIEWED" for row in rows):
        raise ReviewEvidenceError("inventory must not infer completed review")
    if any(row["completed_at"] for row in rows):
        raise ReviewEvidenceError("inventory-only rows cannot have completion timestamps")
    if raw != build_file_review_ledger():
        raise ReviewEvidenceError("file-review ledger differs from the exact tagged tree")
    return rows


def write_outputs() -> None:
    ASSURANCE_REGISTRY.write_bytes(canonical_json_bytes(build_assurance_registry()))
    TASK_DISPOSITIONS.write_bytes(canonical_json_bytes(build_task_dispositions()))
    FILE_REVIEW_LEDGER.write_bytes(build_file_review_ledger())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite the three deterministic evidence artifacts before validation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        require_release_boundary(require_handoff_object=args.write)
        for path in (
            SCOPE,
            ASSURANCE_SCHEMA,
            TASK_SCHEMA,
            HANDOFF_INTAKE,
        ):
            safe_repo_file(str(path.relative_to(ROOT)))
        if args.write:
            write_outputs()
        assurance = validate_assurance_registry(ASSURANCE_REGISTRY.read_bytes())
        tasks = validate_task_dispositions(TASK_DISPOSITIONS.read_bytes())
        rows = validate_file_review_ledger(FILE_REVIEW_LEDGER.read_bytes())
    except (
        OSError,
        ReviewEvidenceError,
        SchemaValidationError,
        TypeError,
        ValueError,
    ) as error:
        print(f"review evidence error: {error}", file=sys.stderr)
        return 1
    print(
        "OK: review evidence binds "
        f"{len(assurance['families'])} families, {tasks['summary']['open_local']} open and "
        f"{tasks['summary']['blocked_external']} externally blocked 1.0 tasks "
        f"({tasks['summary']['claim_removed']} claim-removed, 0 complete), and "
        f"{len(rows)} inventory-only tagged files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
