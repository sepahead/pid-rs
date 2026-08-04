#!/usr/bin/env python3
"""Mutation adequacy checks for check-ksg-harmonic-revision.py."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-ksg-harmonic-revision.py"
ACTIVE_PACKET = ROOT / "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
EXECUTION_MODES = (("normal", False), ("optimized", True))
SUCCESS_LINES = {
    "--release-only": (
        "KSG harmonic-revision release check passed: 15 affected and 22 protected families"
    ),
    "--source-only": "KSG harmonic-revision source check passed",
    "--exact-only": "KSG harmonic-revision exact check passed: 6,920 tuples",
    "--binary64-only": (
        "KSG harmonic-revision binary64 check passed: 8,198 Decimal cells; "
        "binary64-rounded-reference max 8 eps with 40 ties, allowed 32 eps; "
        "exact-rational error is checked separately; zero source-swap asymmetries"
    ),
    "--enclosure-only": (
        "KSG harmonic-revision exact-enclosure check passed: "
        "8,198 directed intervals; 6,920 exact-Fraction containments; "
        "29-mutation suite is a separate gate"
    ),
    "--catalog-only": (
        "KSG harmonic-revision catalog check passed: 20 affected and 6 formal-bound methods"
    ),
    "--claim-only": (
        "KSG harmonic-revision claim check passed: active revision 4 integration_no_go; "
        "70 mapped files; 35 historical hashes; "
        "stage=preclosure_core_manifest_must_be_regenerated_at_m1c"
    ),
}
PRECLOSURE_DEFAULT_FAILURE = (
    "KSG harmonic-revision check failed: default integration gate remains closed: "
    "status='integration_no_go'; open_integration_gates=13; "
    "use scoped routes for preclosure diagnostics"
)
EXPECTED_MUTATIONS = {
    "checker-model": 16,
    "fixture-custody": 2,
    "fixture-semantics": 12,
    "textual-source": 35,
    "release": 78,
    "catalog": 43,
}
EXPECTED_SCOPE_ISOLATION_PREFLIGHTS = 2
EXPECTED_CLAIM_MUTATIONS = {
    "custody": 3,
    "manifest-structure": 65,
    "resealed-semantics": 73,
}

KSG_STALE_RELEASE_REVISIONS = (
    (
        "pid-core.stable.continuous",
        "strict-unique-shell-report-v3",
    ),
    (
        "pid-core.experimental.continuous.co-information",
        "ksg-derived-co-information-v1",
    ),
    ("pid-core.experimental.continuous.isx", "strict-unique-shell-isx-v3"),
    (
        "pid-core.experimental.continuous.pid2",
        "separate-biased-term-pid2-v1",
    ),
    (
        "pid-core.experimental.continuous.incomplete-pid3",
        "equal-ambient-branch-screen-v1",
    ),
    ("pid-core.research.raw-ksg", "ksg-chebyshev-raw-v1"),
    ("pid-core.research.raw-isx", "ehrlich-local-knn-raw-v1"),
    ("pid-core.research.raw-co-information", "ksg-co-information-raw-v1"),
    (
        "pid-core.research.isx-heuristics",
        "heuristic-baselines-v1",
    ),
    (
        "pid-core.research.mixed-dimension-pid3",
        "mixed-dimensional-pid3-reference-v1",
    ),
    ("pid-core.research.hyperbolic", "lorentz-geometry-safe-rust-v1"),
    (
        "pid-core.experimental.hierarchy",
        "hierarchy-screening-v1",
    ),
    (
        "pid-core.experimental.pipelines.pid3-permutation",
        "explicit-seed-pid3-permutation-v1",
    ),
    (
        "pid-core.experimental.pipelines.pls-selection-and-composition",
        "deterministic-pls-cv-v1",
    ),
    (
        "pid-core.experimental.pipelines.pid2-screening",
        "deterministic-pair-enumeration-v1",
    ),
)

KSG_PROTECTED_RELEASE_FAMILIES = (
    "pid-core.infrastructure",
    "pid-core.stable.categorical",
    "pid-core.stable.quantized",
    "pid-core.stable.imin",
    "pid-core.stable.preprocessing",
    "pid-core.diagnostics.distance-matrix",
    "pid-core.diagnostics.geometry",
    "pid-core.diagnostics.invariants",
    "pid-core.diagnostics.support",
    "pid-core.experimental.continuous.shared-ksg-config",
    "pid-core.experimental.pipelines.block-resampling",
    "pid-core.experimental.pipelines.logistic-regression",
    "pid-core.experimental.pipelines.fdr-adjustment",
    "pid-core.experimental.pipelines.quantized-sxpid-bootstrap",
    "pid-core.experimental.pipelines.row-bootstrap",
    "pid-core.experimental.pipelines.permutation-contracts",
    "pid-core.experimental.pipelines.row-permutation",
    "pid-core.experimental.pipelines.gaussian-noise-provenance",
    "pid-core.experimental.pipelines.jitter-preprocessing",
    "pid-core.experimental.pipelines.same-sample-quantization",
    "pid-core.experimental.pipelines.same-sample-quantized-imin",
    "pid-core.experimental.pipelines.same-sample-quantized-sxpid",
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
KSG_FORMAL_CATALOG_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
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


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, mutation: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{mutation}: replacement anchor occurs {count} times instead of once")
    return text.replace(old, new, 1)


def run_checker(
    checker: Path,
    repo_root: Path,
    *,
    optimized: bool,
    route: str | None = None,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend([str(checker), "--repo-root", str(repo_root)])
    if route is not None:
        command.append(route)
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def require_exact_acceptance_in_all_modes(
    checker: Path,
    repo_root: Path,
    *,
    route: str | None = None,
    cwd: Path = ROOT,
) -> None:
    expected_stdout = SUCCESS_LINES[route] + "\n"
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=route,
            cwd=cwd,
        )
        if (
            result.returncode != 0
            or result.stdout != expected_stdout
            or result.stderr != ""
        ):
            fail(
                f"unmodified checker failed its exact {route or 'all'} contract in {mode} mode\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def require_rejection_in_all_modes(
    checker: Path,
    repo_root: Path,
    mutation: str,
    *,
    route: str | None = None,
    cwd: Path = ROOT,
) -> None:
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=route,
            cwd=cwd,
        )
        diagnostics = result.stderr.splitlines()
        if (
            result.returncode != 1
            or result.stdout != ""
            or len(diagnostics) != 1
            or not diagnostics[0].startswith("KSG harmonic-revision check failed: ")
        ):
            fail(
                f"{mutation}: checker did not fail through one clean diagnostic in {mode} mode\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def require_exact_rejection_in_all_modes(
    checker: Path,
    repo_root: Path,
    mutation: str,
    expected_detail: str,
    *,
    route: str | None = None,
    cwd: Path = ROOT,
) -> None:
    expected_stderr = f"KSG harmonic-revision check failed: {expected_detail}\n"
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=route,
            cwd=cwd,
        )
        if (
            result.returncode != 1
            or result.stdout != ""
            or result.stderr != expected_stderr
        ):
            fail(
                f"{mutation}: checker did not fail through the exact intended diagnostic "
                f"in {mode} mode\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def require_preclosure_default_rejection_in_all_modes(
    checker: Path,
    repo_root: Path,
    *,
    cwd: Path = ROOT,
) -> None:
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=None,
            cwd=cwd,
        )
        if (
            result.returncode != 1
            or result.stdout != ""
            or result.stderr != PRECLOSURE_DEFAULT_FAILURE + "\n"
        ):
            fail(
                "unmodified default checker did not fail through the exact preclosure "
                f"lifecycle diagnostic in {mode} mode\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def copy_route(destination: Path) -> None:
    for relative in (
        Path("crates/pid-core/src/stats.rs"),
        Path("crates/pid-core/src/ksg.rs"),
        Path("crates/pid-core/src/isx.rs"),
        Path("crates/pid-core/src/pid3.rs"),
        Path("crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"),
        Path("crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256"),
        Path("scripts/generate-ksg-local-arithmetic-oracle.py"),
        Path("scripts/check-ksg-harmonic-exact-enclosure.py"),
        Path("release-scope-1.0.json"),
        Path("README.md"),
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def copy_catalog_route(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "method-catalog.json", destination / "method-catalog.json")
    catalog = json.loads((ROOT / "method-catalog.json").read_bytes())
    affected = {
        method["id"]: method
        for method in catalog["methods"]
        if method["id"] in KSG_CATALOG_METHOD_IDS
    }
    if set(affected) != set(KSG_CATALOG_METHOD_IDS):
        fail(
            "catalog copy route cannot resolve the exact KSG-affected method inventory"
        )
    for method in affected.values():
        for relative_text in method["validation"]["evidence_paths"]:
            relative = Path(relative_text)
            if relative.is_absolute() or ".." in relative.parts:
                fail(
                    f"catalog copy route found escaping evidence path: {relative_text}"
                )
            source = ROOT / relative
            if not source.is_file():
                fail(
                    f"catalog copy route found absent evidence target: {relative_text}"
                )
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def copy_claim_route(destination: Path) -> None:
    manifest = json.loads(ACTIVE_PACKET.read_bytes())
    packet_files = manifest.get("packet_files")
    if not isinstance(packet_files, dict):
        fail("claim copy route cannot resolve the active packet file map")
    relatives = [Path(relative) for relative in packet_files]
    relatives.append(ACTIVE_PACKET.relative_to(ROOT))
    for relative in relatives:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            fail(f"claim copy route found a non-regular source: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def checker_rebound_to_manifest(
    checker_text: str,
    manifest_raw: bytes,
    mutation: str,
) -> str:
    baseline_digest = hashlib.sha256(ACTIVE_PACKET.read_bytes()).hexdigest()
    replacement_digest = hashlib.sha256(manifest_raw).hexdigest()
    return replace_once(
        checker_text,
        baseline_digest,
        replacement_digest,
        f"{mutation}-manifest-envelope",
    )


def checker_rebound_to_fixture(
    checker_text: str,
    fixture_raw: bytes,
    mutation: str,
) -> str:
    baseline_digest = hashlib.sha256(
        (
            ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
        ).read_bytes()
    ).hexdigest()
    replacement_digest = hashlib.sha256(fixture_raw).hexdigest()
    return replace_once(
        checker_text,
        baseline_digest,
        replacement_digest,
        f"{mutation}-fixture-digest",
    )


def write_rebound_manifest_case(
    checker_text: str,
    case_root: Path,
    temporary: Path,
    manifest_raw: bytes,
    mutation: str,
) -> Path:
    manifest_path = case_root / ACTIVE_PACKET.relative_to(ROOT)
    manifest_path.write_bytes(manifest_raw)
    checker = temporary / f"{mutation}-checker.py"
    checker.write_text(
        checker_rebound_to_manifest(checker_text, manifest_raw, mutation),
        encoding="utf-8",
    )
    return checker


def mutate_release_field(
    path: Path, family_id: str, field: str, value: str, mutation: str
) -> None:
    release = json.loads(path.read_text(encoding="utf-8"))
    matches = [
        family for family in release["families"] if family.get("id") == family_id
    ]
    if len(matches) != 1:
        fail(f"{mutation}: release family match count is {len(matches)}")
    matches[0][field] = value
    path.write_text(
        json.dumps(release, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_checker_mutations(checker_text: str, temporary: Path) -> list[str]:
    mutations = (
        (
            "corrupt-exact-k-index",
            "harmonics[k - 1]\n                        + harmonics[n - 1]",
            "harmonics[k]\n                        + harmonics[n - 1]",
            "--exact-only",
        ),
        (
            "accept-seven-eps",
            "EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_EPSILON_MULTIPLES = 8",
            "EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_EPSILON_MULTIPLES = 7",
            "--binary64-only",
        ),
        (
            "accept-wrong-case-count",
            "EXPECTED_CASES = 8_198",
            "EXPECTED_CASES = 8_197",
            "--binary64-only",
        ),
        (
            "accept-wrong-maximum-tie-count",
            "EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_TIES = 40",
            "EXPECTED_ROUNDED_REFERENCE_MAX_ERROR_TIES = 39",
            "--binary64-only",
        ),
        (
            "accept-wrong-endpoint-cancellation-count",
            "EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 354",
            "EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 353",
            "--binary64-only",
        ),
        (
            "shift-endpoint-cancellation-predicate",
            'low = case["k"] - 1',
            'low = case["k"]',
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-prefix-direct-left-nonzero-count",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 150",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 149",
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-prefix-direct-left-negative-zero-count",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 0",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 1",
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-endpoint-positive-zero-count",
            "EXPECTED_SELECTED_ENDPOINT_POSITIVE_ZEROS = 354",
            "EXPECTED_SELECTED_ENDPOINT_POSITIVE_ZEROS = 353",
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-endpoint-negative-zero-count",
            "EXPECTED_SELECTED_ENDPOINT_NEGATIVE_ZEROS = 0",
            "EXPECTED_SELECTED_ENDPOINT_NEGATIVE_ZEROS = 1",
            "--binary64-only",
        ),
        (
            "force-selected-endpoint-negative-zero",
            "return (table[n] - table[upper]) - (table[lower] - table[k])",
            "value = (table[n] - table[upper]) - (table[lower] - table[k])\n"
            "    return -0.0 if value == 0.0 else value",
            "--binary64-only",
        ),
        (
            "accept-wrong-naive-prefix-nonzero-count",
            "EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS = 121",
            "EXPECTED_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS = 120",
            "--binary64-only",
        ),
        (
            "substitute-selected-table-for-naive-prefix",
            "naive_table = naive_shifted_harmonic_table(max_argument)",
            "naive_table = table",
            "--binary64-only",
        ),
        (
            "loosen-reviewed-binary64-ceiling",
            "EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES = 32",
            "EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLES = 64",
            "--binary64-only",
        ),
        (
            "inject-selected-nan",
            "return (table[n] - table[upper]) - (table[lower] - table[k])",
            "value = (table[n] - table[upper]) - (table[lower] - table[k])\n"
            '    return float("nan") if (n, k, x, y) == (2, 1, 2, 2) else value',
            "--binary64-only",
        ),
        (
            "remove-default-lifecycle-gate",
            "        require_default_integration_go(manifest)",
            "        return 0",
            None,
        ),
    )
    killed: list[str] = []
    for mutation, old, new, route in mutations:
        mutated = replace_once(checker_text, old, new, mutation)
        checker = temporary / f"{mutation}.py"
        checker.write_text(mutated, encoding="utf-8")
        if route is None:
            for mode, optimized in EXECUTION_MODES:
                result = run_checker(
                    checker,
                    ROOT,
                    optimized=optimized,
                    route=None,
                )
                if not (
                    result.returncode == 0
                    and result.stdout == ""
                    and result.stderr == ""
                ):
                    fail(
                        f"{mutation}: lifecycle-removal sentinel did not expose the exact empty "
                        f"false green in {mode} mode\n"
                        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                    )
        else:
            require_rejection_in_all_modes(checker, ROOT, mutation, route=route)
        killed.append(mutation)
    return killed


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


def check_claim_custody_mutations(checker_text: str, temporary: Path) -> list[str]:
    killed: list[str] = []

    deletion = "claim-packet-mapped-file-deletion"
    deletion_root = temporary / deletion
    copy_claim_route(deletion_root)
    (deletion_root / "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md").unlink()
    require_rejection_in_all_modes(
        CHECKER,
        deletion_root,
        deletion,
        route="--claim-only",
    )
    killed.append(deletion)

    unresealed = "claim-packet-unresealed-leaf-edit"
    unresealed_root = temporary / unresealed
    copy_claim_route(unresealed_root)
    unresealed_path = (
        unresealed_root / "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"
    )
    unresealed_path.write_bytes(
        unresealed_path.read_bytes() + b"\nmutation: unresealed claim edit\n"
    )
    require_rejection_in_all_modes(
        CHECKER,
        unresealed_root,
        unresealed,
        route="--claim-only",
    )
    killed.append(unresealed)

    pin = "claim-checker-manifest-digest-pin"
    baseline_digest = hashlib.sha256(ACTIVE_PACKET.read_bytes()).hexdigest()
    mutated_checker = replace_once(
        checker_text,
        baseline_digest,
        "0" * 64,
        pin,
    )
    checker = temporary / f"{pin}.py"
    checker.write_text(mutated_checker, encoding="utf-8")
    require_rejection_in_all_modes(
        checker,
        ROOT,
        pin,
        route="--claim-only",
    )
    killed.append(pin)
    return killed


def check_claim_manifest_mutations(checker_text: str, temporary: Path) -> list[str]:
    baseline_raw = ACTIVE_PACKET.read_bytes()
    baseline = json.loads(baseline_raw)
    killed: list[str] = []

    symlink = "claim-packet-symlink-leaf"
    symlink_root = temporary / symlink
    copy_claim_route(symlink_root)
    symlink_path = symlink_root / "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"
    symlink_path.unlink()
    symlink_path.symlink_to("claim-v3.md")
    require_rejection_in_all_modes(
        CHECKER,
        symlink_root,
        symlink,
        route="--claim-only",
    )
    killed.append(symlink)

    def canonical_case(
        mutation: str,
        transform: Callable[[dict[str, Any]], None],
    ) -> None:
        case_root = temporary / mutation
        copy_claim_route(case_root)
        value = json.loads(json.dumps(baseline))
        transform(value)
        raw = canonical_json_bytes(value)
        checker = write_rebound_manifest_case(
            checker_text,
            case_root,
            temporary,
            raw,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            case_root,
            mutation,
            route="--claim-only",
        )
        killed.append(mutation)

    def path_escape(value: dict[str, Any]) -> None:
        value["packet_files"]["../outside-claim-artifact"] = "0" * 64

    canonical_case("claim-packet-path-escape", path_escape)

    def mapped_digest_mutation(value: dict[str, Any]) -> None:
        value["packet_files"]["claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"] = "0" * 64

    canonical_case("claim-packet-mapped-digest-mutation", mapped_digest_mutation)

    duplicate = "claim-packet-duplicate-json-key"
    duplicate_root = temporary / duplicate
    copy_claim_route(duplicate_root)
    duplicate_raw = baseline_raw.replace(
        b'{\n  "active_revision": 4,',
        b'{\n  "active_revision": 4,\n  "active_revision": 4,',
        1,
    )
    checker = write_rebound_manifest_case(
        checker_text,
        duplicate_root,
        temporary,
        duplicate_raw,
        duplicate,
    )
    require_rejection_in_all_modes(
        checker,
        duplicate_root,
        duplicate,
        route="--claim-only",
    )
    killed.append(duplicate)

    noncanonical = "claim-packet-noncanonical-json"
    noncanonical_root = temporary / noncanonical
    copy_claim_route(noncanonical_root)
    noncanonical_raw = baseline_raw + b"\n"
    checker = write_rebound_manifest_case(
        checker_text,
        noncanonical_root,
        temporary,
        noncanonical_raw,
        noncanonical,
    )
    require_rejection_in_all_modes(
        checker,
        noncanonical_root,
        noncanonical,
        route="--claim-only",
    )
    killed.append(noncanonical)

    canonical_case(
        "claim-packet-active-revision-change",
        lambda value: value.__setitem__("active_revision", 3),
    )

    def multiple_active(value: dict[str, Any]) -> None:
        value["revision_history"][2]["active"] = True

    canonical_case("claim-packet-multiple-active-revisions", multiple_active)
    canonical_case(
        "claim-packet-status-promotion",
        lambda value: value.__setitem__("status", "integration_go"),
    )
    canonical_case(
        "claim-packet-premature-final-stage",
        lambda value: value.__setitem__("packet_stage", "immutable_final_m1c"),
    )

    canonical_case(
        "claim-packet-active-revision-float",
        lambda value: value.__setitem__("active_revision", 4.0),
    )
    canonical_case(
        "claim-packet-schema-revision-boolean",
        lambda value: value.__setitem__("schema_revision", True),
    )

    def boolean_coefficient(value: dict[str, Any]) -> None:
        value["facts"]["arithmetic"]["coefficient_vector"][0] = True

    canonical_case("claim-packet-boolean-coefficient", boolean_coefficient)

    def promote_outer_box_to_exact_runtime_image(value: dict[str, Any]) -> None:
        value["facts"]["domains"]["runtime_shell_image_equals_outer_box"] = True

    canonical_case(
        "claim-packet-promote-outer-box-to-exact-runtime-image",
        promote_outer_box_to_exact_runtime_image,
    )

    def promote_runtime_candidate_status(value: dict[str, Any]) -> None:
        value["facts"]["domains"]["runtime_candidate_status"] = "project_theorem"

    canonical_case(
        "claim-packet-promote-runtime-candidate-status",
        promote_runtime_candidate_status,
    )

    def change_runtime_candidate_constraint_type(value: dict[str, Any]) -> None:
        value["facts"]["domains"]["runtime_candidate_constraint"] = False

    canonical_case(
        "claim-packet-runtime-candidate-constraint-boolean",
        change_runtime_candidate_constraint_type,
    )

    def change_runtime_candidate_bound(value: dict[str, Any]) -> None:
        value["facts"]["domains"]["runtime_candidate_lower_bound"] = "H_(k-1)-H_(n-1)"

    canonical_case(
        "claim-packet-change-runtime-candidate-bound",
        change_runtime_candidate_bound,
    )

    def remove_runtime_candidate_basis(value: dict[str, Any]) -> None:
        value["facts"]["domains"]["runtime_candidate_constraint_basis"] = (
            "unconditional runtime theorem"
        )

    canonical_case(
        "claim-packet-change-runtime-candidate-basis",
        remove_runtime_candidate_basis,
    )

    def disable_direct_compiled_partition(value: dict[str, Any]) -> None:
        value["facts"]["binary64_corpus"][
            "direct_compiled_full_partition_assertion"
        ] = False

    canonical_case(
        "claim-packet-disable-direct-compiled-partition",
        disable_direct_compiled_partition,
    )

    def change_exact_comparator(value: dict[str, Any]) -> None:
        value["facts"]["exact_rational_enclosure"]["exact_difference_comparator"] = (
            "ambient Decimal subtraction"
        )

    canonical_case("claim-packet-change-exact-comparator", change_exact_comparator)

    def boolean_exact_control_count(value: dict[str, Any]) -> None:
        value["facts"]["exact_rational_enclosure"][
            "exact_comparator_firewall_control_count"
        ] = True

    canonical_case(
        "claim-packet-boolean-exact-control-count",
        boolean_exact_control_count,
    )

    def change_exact_fraction(value: dict[str, Any]) -> None:
        value["facts"]["exact_rational_enclosure"][
            "stored_decimal_exact_rounded_maximum_difference_reduced_fraction"
        ] = "818/10^78"

    canonical_case("claim-packet-change-exact-fraction", change_exact_fraction)

    def change_z3_checker_hash(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_checker_sha256"] = "0" * 64

    canonical_case("claim-packet-change-z3-checker-hash", change_z3_checker_hash)

    def change_z3_firewall_count(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_firewall_control_count"] = 51

    canonical_case("claim-packet-change-z3-firewall-count", change_z3_firewall_count)

    def boolean_z3_firewall_group_count(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_firewall_control_group_counts"][
            "lexer_parser"
        ] = True

    canonical_case(
        "claim-packet-boolean-z3-firewall-group-count",
        boolean_z3_firewall_group_count,
    )

    def promote_raw_token_pin_independence(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_raw_and_token_pins_are_correlated"] = False

    canonical_case(
        "claim-packet-promote-z3-pin-independence",
        promote_raw_token_pin_independence,
    )

    def promote_z3_boundary(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_retained_dual_rebase_boundary"][
            "classification"
        ] = "verification_evidence"

    canonical_case("claim-packet-promote-z3-boundary", promote_z3_boundary)

    def change_z3_token_pin(value: dict[str, Any]) -> None:
        value["facts"]["formal"]["z3_token_stream_sha256"][
            "ksg-digamma-cancellation.smt2"
        ] = "0" * 64

    canonical_case("claim-packet-change-z3-token-pin", change_z3_token_pin)

    def promote_modular_reflection_to_proof(value: dict[str, Any]) -> None:
        value["facts"]["modular_certificate"][
            "selected_prime_reflection_is_separation_proof"
        ] = True

    canonical_case(
        "claim-packet-promote-modular-reflection-to-proof",
        promote_modular_reflection_to_proof,
    )

    def restore_prefilter_composite(value: dict[str, Any]) -> None:
        value["facts"]["modular_certificate"]["composite_mutation_modulus"] = 1_000_035

    canonical_case(
        "claim-packet-restore-prefilter-composite",
        restore_prefilter_composite,
    )

    def disable_miller_rabin_path(value: dict[str, Any]) -> None:
        value["facts"]["modular_certificate"][
            "composite_mutation_reaches_miller_rabin_after_small_prime_prefilter"
        ] = False

    canonical_case(
        "claim-packet-disable-miller-rabin-path",
        disable_miller_rabin_path,
    )

    def boolean_modular_type_control_count(value: dict[str, Any]) -> None:
        value["facts"]["modular_certificate"][
            "strict_json_type_firewall_control_count"
        ] = True

    canonical_case(
        "claim-packet-boolean-modular-type-control-count",
        boolean_modular_type_control_count,
    )

    def disable_strict_modular_json(value: dict[str, Any]) -> None:
        value["facts"]["modular_certificate"][
            "strict_recursive_json_type_shape_value_equality"
        ] = False

    canonical_case(
        "claim-packet-disable-strict-modular-json",
        disable_strict_modular_json,
    )

    def permute_w1_helper_order(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w1"]["helper_arguments_k_n_x_y"] = [
            8,
            2,
            5,
            2,
        ]

    canonical_case("claim-packet-permute-w1-helper-order", permute_w1_helper_order)

    def c30_absolute_term_number(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"]["absolute_term"] = (
            1 / 105
        )

    canonical_case(
        "claim-packet-c30-absolute-term-number",
        c30_absolute_term_number,
    )

    def c30_false_claim_number(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"]["false_claim"] = 0

    canonical_case("claim-packet-c30-false-claim-number", c30_false_claim_number)

    def c30_denominator_number(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"][
            "one_over_n_minus_one"
        ] = 1 / 7

    canonical_case(
        "claim-packet-c30-one-over-n-minus-one-number",
        c30_denominator_number,
    )

    def c30_boolean_argument(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"][
            "helper_arguments_n_k_x_y"
        ][0] = True

    canonical_case("claim-packet-c30-boolean-argument", c30_boolean_argument)

    def c30_relation_promotion(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"][
            "counterexample_relation"
        ] = "0 < |T| = 1/105 >= 1/7 = 1/(n-1)"

    canonical_case("claim-packet-c30-relation-promotion", c30_relation_promotion)

    def c30_integer_structural_flag(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["c30_false_nonstructural_gap"][
            "structural_endpoint"
        ] = 0

    canonical_case(
        "claim-packet-c30-integer-structural-flag",
        c30_integer_structural_flag,
    )

    def w0_restore_ambiguous_string(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"] = "n=2,k=1 realizes +D,-D,0"

    canonical_case(
        "claim-packet-w0-restore-ambiguous-string",
        w0_restore_ambiguous_string,
    )

    def w0_integer_sharpness_flag(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"][
            "arithmetic_box_endpoint_sharpness"
        ] = 1

    canonical_case(
        "claim-packet-w0-integer-sharpness-flag",
        w0_integer_sharpness_flag,
    )

    def w0_promote_domain_to_runtime(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"]["domain"] = (
            "runtime_unique_shell"
        )

    canonical_case(
        "claim-packet-w0-promote-domain-to-runtime",
        w0_promote_domain_to_runtime,
    )

    def w0_change_helper_tuple(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"]["helper_tuples_n_k_x_y"][3] = [
            2,
            1,
            1,
            1,
        ]

    canonical_case(
        "claim-packet-w0-change-helper-tuple",
        w0_change_helper_tuple,
    )

    def w0_change_helper_value(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"]["helper_values_nats"][3] = "0"

    canonical_case(
        "claim-packet-w0-change-helper-value",
        w0_change_helper_value,
    )

    def w0_promote_runtime_attainability(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w0_smallest_bound"][
            "runtime_unique_shell_attainability_claim"
        ] = True

    canonical_case(
        "claim-packet-w0-promote-runtime-attainability",
        w0_promote_runtime_attainability,
    )

    def w2b_integer_uniqueness_flag(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["all_coordinate_values_unique"] = 1

    canonical_case(
        "claim-packet-w2b-integer-uniqueness-flag",
        w2b_integer_uniqueness_flag,
    )

    def w2b_numeric_encoding(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["input_literal_encoding"] = 64

    canonical_case("claim-packet-w2b-numeric-encoding", w2b_numeric_encoding)

    def w2b_shell_flag_false(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["all_joint_shells_unique_and_positive"] = (
            False
        )

    canonical_case("claim-packet-w2b-shell-flag-false", w2b_shell_flag_false)

    def w2b_boolean_k(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["k"] = True

    canonical_case("claim-packet-w2b-boolean-k", w2b_boolean_k)

    def w2b_numeric_radius(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["row_diagnostics"][0]["joint_radius"] = 1

    canonical_case("claim-packet-w2b-numeric-radius", w2b_numeric_radius)

    def w2b_boolean_row(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["row_diagnostics"][0]["row"] = False

    canonical_case("claim-packet-w2b-boolean-row", w2b_boolean_row)

    def w2b_boolean_count(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["row_diagnostics"][1]["n_alpha"] = True

    canonical_case("claim-packet-w2b-boolean-count", w2b_boolean_count)

    def w2b_float_target_count(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["row_diagnostics"][2]["n_t"] = 3.0

    canonical_case("claim-packet-w2b-float-target-count", w2b_float_target_count)

    def w2b_changed_positive_zero_bits(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["row_diagnostics"][2]["selected_bits"] = (
            "0x8000000000000000"
        )

    canonical_case(
        "claim-packet-w2b-changed-positive-zero-bits",
        w2b_changed_positive_zero_bits,
    )

    def w2b_float_sample_count(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["sample_count"] = 3.0

    canonical_case("claim-packet-w2b-float-sample-count", w2b_float_sample_count)

    def w2b_integer_support_flag(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["sample_proves_population_support"] = 0

    canonical_case(
        "claim-packet-w2b-integer-support-flag",
        w2b_integer_support_flag,
    )

    def w2b_numeric_input_literal(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["target_literals"][1] = 0.4

    canonical_case(
        "claim-packet-w2b-numeric-input-literal",
        w2b_numeric_input_literal,
    )

    def w2b_numeric_source1_literal(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["source1_literals"][1] = 1

    canonical_case(
        "claim-packet-w2b-numeric-source1-literal",
        w2b_numeric_source1_literal,
    )

    def w2b_numeric_source2_literal(value: dict[str, Any]) -> None:
        value["facts"]["witnesses"]["w2b"]["source2_literals"][1] = 10

    canonical_case(
        "claim-packet-w2b-numeric-source2-literal",
        w2b_numeric_source2_literal,
    )

    def integer_inactive_flag(value: dict[str, Any]) -> None:
        value["revision_history"][0]["active"] = 0

    canonical_case("claim-packet-integer-inactive-flag", integer_inactive_flag)

    def extra_node_case(
        mutation: str,
        relative: Path,
        *,
        symlink_target: str | None = None,
    ) -> None:
        case_root = temporary / mutation
        copy_claim_route(case_root)
        target = case_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if symlink_target is None:
            target.write_bytes(
                canonical_json_bytes(
                    {
                        "active_revision": 5,
                        "claim_id": "KSG-INTEGER-HARMONIC-001",
                        "status": "integration_go",
                    }
                )
            )
        else:
            target.symlink_to(symlink_target)
        require_rejection_in_all_modes(
            CHECKER,
            case_root,
            mutation,
            route="--claim-only",
        )
        killed.append(mutation)

    extra_node_case(
        "claim-tree-extra-root-active-v5",
        Path("claims/KSG-INTEGER-HARMONIC-001/active-packet-v5.json"),
    )
    extra_node_case(
        "claim-tree-extra-nested-active-v5",
        Path("claims/KSG-INTEGER-HARMONIC-001/nested/active-packet-v5.json"),
    )
    extra_node_case(
        "claim-tree-extra-case-variant-active-v5",
        Path("claims/KSG-INTEGER-HARMONIC-001/Active-Packet-V5.JSON"),
    )
    extra_node_case(
        "claim-tree-extra-active-v5-symlink",
        Path("claims/KSG-INTEGER-HARMONIC-001/active-packet-v5.json"),
        symlink_target="active-packet-v4.json",
    )
    hardlink_mutation = "claim-tree-external-hardlink-alias"
    hardlink_root = temporary / hardlink_mutation
    copy_claim_route(hardlink_root)
    hardlink_leaf = hardlink_root / "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"
    external_leaf = temporary / f"{hardlink_mutation}-external.md"
    external_leaf.write_bytes(hardlink_leaf.read_bytes())
    hardlink_leaf.unlink()
    os.link(external_leaf, hardlink_leaf)
    require_rejection_in_all_modes(
        CHECKER,
        hardlink_root,
        hardlink_mutation,
        route="--claim-only",
    )
    killed.append(hardlink_mutation)
    return killed


def check_claim_resealed_semantic_mutations(
    checker_text: str,
    temporary: Path,
) -> list[str]:
    semantic_mutations = (
        (
            "claim-domain-runtime-k-le-n",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "n >= 2\n1 <= k < n\nk <= x <= n\nk <= y <= n.",
            "n >= 2\n1 <= k <= n\nk <= x <= n\nk <= y <= n.",
        ),
        (
            "claim-corpus-row-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The fixture contains 8,198 unique ordered rows",
            "The fixture contains 8,197 unique ordered rows",
        ),
        (
            "claim-corpus-outer-box-runtime-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "6,920 exhaustive rectangular-arithmetic\nouter-box rows",
            "6,920 exhaustive runtime-realizable\nunique-shell rows",
        ),
        (
            "claim-endpoint-segment-split",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "354 rows, split into 240 exhaustive and 114 stress rows.",
            "354 rows, split into 239 exhaustive and 115 stress rows.",
        ),
        (
            "claim-selected-signed-zero",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "selected endpoint negative zeros   = 0",
            "selected endpoint negative zeros   = 1",
        ),
        (
            "claim-selected-prefix-association-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "ordinary four-term left association is nonzero at 150/354",
            "ordinary four-term left association is nonzero at 149/354",
        ),
        (
            "claim-absolute-error-measure-not-ulp",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The `8*EPSILON` quantity first rounds each stored Decimal reference to binary64. "
            "It is not the\n"
            "error against the stored Decimal value or exact harmonic rational, not eight ULPs",
            "The `8*EPSILON` quantity directly measures the exact harmonic rational. "
            "It is\n"
            "eight ULPs",
        ),
        (
            "claim-selected-versus-naive-prefix-distinction",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "A separately constructed naive prefix has a\ndifferent 121/354 result",
            "The selected prefix has the same\n150/354 result",
        ),
        (
            "claim-enclosure-method-dependence",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "A separately implemented 160-digit directed-rounding\nenclosure",
            "An independent 160-digit directed-rounding\nenclosure",
        ),
        (
            "claim-lean-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "It checks 19 theorem declarations and kills 14/14 baseline-first semantic mutations.",
            "It checks 18 theorem declarations and kills 13/13 baseline-first semantic mutations.",
        ),
        (
            "claim-z3-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "four satisfiable positive preflights, four unsatisfiable negated obligations, and 12/12",
            "three satisfiable positive preflights, three unsatisfiable negated obligations, and 11/11",
        ),
        (
            "claim-formal-separate-encoding",
            Path("claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"),
            "four\nseparately encoded conditional QF_UFLIRA obligations",
            "four\nindependently encoded conditional QF_UFLIRA obligations",
        ),
        (
            "claim-formal-outer-box-not-runtime-image",
            Path("claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"),
            "The inventoried rectangular arithmetic outer box uses the stricter common domain "
            "`1 <= k < n`.\nIt is not asserted to equal the runtime unique-shell image.",
            "The estimator-facing domain is `1 <= k < n`.\n"
            "It equals the runtime unique-shell image.",
        ),
        (
            "claim-formal-shared-premise-independence",
            Path("claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"),
            "must not be described as\ntwo failure-independent proofs of harmonic monotonicity.",
            "are two failure-independent proofs of harmonic monotonicity.",
        ),
        (
            "claim-modular-implication-direction",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "nonzero residue => exact rational nonzero.",
            "zero residue => exact rational zero.",
        ),
        (
            "claim-modular-reciprocal-summand-domain",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "every reciprocal-summand denominator/index occurring in the\nfrozen row.",
            "every harmonic denominator in the frozen row.",
        ),
        (
            "claim-modular-invertibility-premise-object",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "maximum reciprocal-summand denominator/index, then every `1/j` summand\n"
            "denominator",
            "maximum harmonic denominator, then every denominator",
        ),
        (
            "claim-modular-crt-role",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "The selected triple provides redundant fault diversity. It is not CRT reconstruction",
            "The selected triple provides independent proof by CRT reconstruction",
        ),
        (
            "claim-historical-current-certificate-distinction",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "Canonical current custody is\n"
            "`5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f`.",
            "Canonical current custody is\n"
            "`1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`.",
        ),
        (
            "claim-mgw-nontransfer-firewall",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "categorical Makkeh--Gutknecht--Wibral shared-exclusions PID;",
            "categorical Makkeh--Gutknecht--Wibral shared-exclusions PID is proved;",
        ),
        (
            "claim-ordered-position-not-ulp",
            Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
            "ordered-binary64 positions. This wording does not assert eight ULPs",
            "ULPs. This wording asserts eight ULPs",
        ),
        (
            "claim-behavioral-naive-route-independence-overclaim",
            Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
            "A separately constructed naive-prefix route gives 121/354",
            "An independently validating naive-prefix route gives 121/354",
        ),
        (
            "claim-w2-all-unique-lower-endpoint",
            Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
            "n_alpha = 1 = k\nn_t     = 3 = n",
            "n_alpha = 2 = k+1\nn_t     = 3 = n",
        ),
        (
            "claim-w2-all-unique-support-boundary",
            Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
            "All-unique samples do not prove the declared population-support model.",
            "All-unique samples prove the declared population-support model.",
        ),
        (
            "claim-reciprocal-summand-denominator-object",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "maximum reciprocal summand denominator/index `999999`",
            "reduced denominator of `H_999999` is `999999`",
        ),
        (
            "claim-modular-mutation-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "self-test kills 28/28 registered mutations",
            "self-test kills 26/26 registered mutations",
        ),
        (
            "claim-preclosure-manifest-not-final",
            Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
            "Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are deliberately",
            "Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are already",
        ),
        (
            "claim-marker-preserving-mgw-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "Only a separate descendant M1c\n"
            "milestone may then create and bind immutable `evidence-matrix-v4.md` and "
            "`decision-v4.md`.",
            "Only a separate descendant M1c\n"
            "milestone may then create and bind immutable `evidence-matrix-v4.md` and "
            "`decision-v4.md`.\n\n"
            "This exact local result therefore proves categorical MGW SxPID.",
        ),
        (
            "claim-marker-preserving-integration-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
            "A failure is retained and routed\n"
            "to the smallest obligation; gates are not weakened to obtain a green result.",
            "A failure is retained and routed\n"
            "to the smallest obligation; gates are not weakened to obtain a green result.\n\n"
            "Repository/publication integration is GO.",
        ),
        (
            "claim-w1-index-base",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "W1 reaches production-private ordered KSG diagnostics at zero-based row 5:",
            "W1 reaches production-private ordered KSG diagnostics at one-based row 5:",
        ),
        (
            "claim-selected-positive-zero-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "selected endpoint outputs          = 354 positive zeros",
            "selected endpoint outputs          = 353 positive zeros",
        ),
        (
            "claim-selected-endpoint-nonzero-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "selected endpoint nonzeros         = 0",
            "selected endpoint nonzeros         = 1",
        ),
        (
            "claim-sharp-bound-weakened",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "-D <= T <= D.",
            "0 <= T <= D.",
        ),
        (
            "claim-rectangular-bound-promoted-to-runtime",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "sharp two-sided bound over that rectangular arithmetic domain",
            "sharp two-sided bound over the runtime estimator domain",
        ),
        (
            "claim-runtime-minus-d-attainability-promoted",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The `-D` tuple is not asserted to be realizable by a runtime\n"
            "unique-shell geometry.",
            "The `-D` tuple is asserted to be realizable by every runtime\n"
            "unique-shell geometry.",
        ),
        (
            "claim-c30-false-gap-restored",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "`0<|T|=1/105<1/7=1/(n-1)` exactly.",
            "`0<|T|=1/105>=1/7=1/(n-1)` exactly.",
        ),
        (
            "claim-c16-superseded-certificate-restored",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "The then-canonical `ae4645c3...`\n"
            "  artifact was superseded by C31; current certificate custody is",
            "The then-canonical `ae4645c3...`\n"
            "  artifact remains final certificate custody; current certificate custody is",
        ),
        (
            "claim-unicode-mgw-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "Only a separate descendant M1c\n"
            "milestone may then create and bind immutable `evidence-matrix-v4.md` and "
            "`decision-v4.md`.",
            "Only a separate descendant M1c\n"
            "milestone may then create and bind immutable `evidence-matrix-v4.md` and "
            "`decision-v4.md`.\n\n"
            "Therefore this establishes the categorical Makkeh–Gutknecht–Wibral theorem.",
        ),
        (
            "claim-integration-go-with-no-go-decoy",
            Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
            "repository and publication integration                    NO-GO",
            "repository and publication integration                    GO\n\n"
            "```text\n"
            "repository and publication integration                    NO-GO\n"
            "```",
        ),
        (
            "claim-routes-crt-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"),
            "their role is\nredundant fault diversity, not three independent proofs and not CRT.",
            "their role is an independent proof by CRT.",
        ),
        (
            "claim-route-rectangular-sharpness-promoted",
            Path("claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"),
            "sharp rectangular-arithmetic-domain signed bound",
            "sharp estimator-facing signed bound",
        ),
        (
            "claim-route-outer-box-runtime-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"),
            "all 6,920 exhaustive rectangular-arithmetic outer-box rows",
            "all 6,920 exhaustive runtime-realizable rows",
        ),
        (
            "claim-route-python-shared-cuts-erased",
            Path("claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"),
            "shared formula, corpus, row order, endpoint branch, selected association, and host "
            "binary64",
            "failure-independent replay",
        ),
        (
            "claim-obligations-conjunction-erasure",
            Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
            "Every arrow is conjunctive. A green exact/formal/modular branch cannot close "
            "repository\nintegration while another branch is open.",
            "Every arrow is optional. A green exact/formal/modular branch closes "
            "repository\nintegration while another branch is open.",
        ),
        (
            "claim-obligations-rectangular-sharpness-promoted",
            Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
            "sharp rectangular-arithmetic-domain signed local bound",
            "sharp runtime signed local bound",
        ),
        (
            "claim-obligations-modular-mutation-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
            "Kill 28 modular certificate mutations.",
            "Kill 26 modular certificate mutations.",
        ),
        (
            "claim-obligations-m1a-m1c-order",
            Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
            "Only after G1/M1a and final I1/Q1/H1 closure, create the immutable evidence matrix "
            "and decision at a separate descendant/re-anchored M1c.",
            "Before G1/M1a, create the immutable evidence matrix and decision at M1c.",
        ),
        (
            "claim-revision-index-modular-mutation-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/revision-index.md"),
            "certificate with 28 mutations",
            "certificate with 26 mutations",
        ),
        (
            "claim-integration-rectangular-sharpness-promoted",
            Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
            "sharp rectangular-arithmetic-domain signed bound, W0 helper boundary",
            "sharp estimator-facing signed bound, W0 runtime boundary",
        ),
        (
            "claim-decimal-shared-cuts-erased",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "decimal-reference-metric-conflation-v4.md"
            ),
            "It shares\nthe formula, generated row order, and structural-endpoint classification "
            "with the directed route,\nso engine separation is not failure independence.",
            "It shares no inputs with the directed route, so it is failure independent.",
        ),
        (
            "claim-decimal-outer-box-runtime-promotion",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "decimal-reference-metric-conflation-v4.md"
            ),
            "exhaustive\nrectangular-arithmetic outer-box rows; this is not a "
            "runtime-shell-image enumeration.",
            "exhaustive\nruntime-realizable unique-shell rows.",
        ),
        (
            "claim-implementation-modular-independence-overclaim",
            Path("claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md"),
            "The modular checker separately recomputes prime admissibility",
            "The modular checker independently proves prime admissibility",
        ),
        (
            "claim-implementation-outer-box-runtime-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md"),
            "all 6,920 exhaustive rectangular-arithmetic outer-box containments, not a "
            "runtime-shell image",
            "all 6,920 exhaustive runtime-shell containments",
        ),
        (
            "claim-implementation-refinement-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md"),
            "The formal layer does not represent Rust, binary64, neighbor geometry, estimator "
            "statistics, or\nPID objects.",
            "The formal layer proves Rust, binary64, neighbor geometry, estimator statistics, "
            "and\nPID objects.",
        ),
        (
            "claim-correction-ledger-status-promotion",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "- **Correction:** status is `integration_no_go`; catalog, release, audience, identity, "
            "phase,\n",
            "- **Correction:** status is `integration_go`; catalog, release, audience, identity, "
            "phase,\n",
        ),
        (
            "claim-correction-ledger-hash-independence-overclaim",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "complete SHA-256 bytes separately from the packet",
            "complete SHA-256 bytes independently prove the packet",
        ),
        (
            "claim-runtime-candidate-promoted",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "neither it nor `x+y <= n+k` is promoted\n"
            "into the revision-4 theorem inventory",
            "both it and `x+y <= n+k` are promoted\n"
            "into the revision-4 theorem inventory",
        ),
        (
            "claim-direct-compiled-partition-erased",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The full-corpus partition is now counted directly by compiled Rust",
            "The full-corpus partition is inferred without a direct compiled Rust count",
        ),
        (
            "claim-z3-firewall-count-inflated",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The repaired self-test rejects 52/52 controls",
            "The repaired self-test rejects 53/53 controls",
        ),
        (
            "claim-z3-controls-promoted-to-theorems",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "smtlib-shape-and-snapshot-v4.md"
            ),
            "The 52 controls do not enlarge the theorem, obligation, or semantic-mutation "
            "count.",
            "The 52 controls enlarge the theorem, obligation, and semantic-mutation count.",
        ),
        (
            "claim-z3-retained-boundary-promoted",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "smtlib-shape-and-snapshot-v4.md"
            ),
            "This is a retained negative result.",
            "This is positive verification evidence.",
        ),
        (
            "claim-z3-machine-boundary-promoted",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "smtlib-shape-and-snapshot-v4.json"
            ),
            '"classification": "negative_result_not_verification_evidence"',
            '"classification": "verification_evidence"',
        ),
        (
            "claim-z3-pin-independence-overclaim",
            Path("claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"),
            "These are correlated custody views of\n"
            "the same source, not two proofs.",
            "These are two independent proofs of the same source.",
        ),
        (
            "claim-decimal-exact-comparator-regression",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "decimal-reference-metric-conflation-v4.md"
            ),
            "each Decimal operand is converted exactly to\n`Fraction`",
            "each Decimal operand is subtracted in the ambient Decimal context",
        ),
        (
            "claim-modular-type-controls-inflated",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "reject 2/2 registered Boolean/integer firewall controls",
            "reject 3/3 registered Boolean/integer firewall controls",
        ),
        (
            "claim-modular-reflection-promoted-to-separation",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "it\ndoes not prove selected-prime separation.",
            "it\nproves selected-prime separation.",
        ),
        (
            "claim-modular-miller-rabin-path-erased",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "reaches the deterministic u32 Miller--Rabin witness loop",
            "stops at the small-prime prefilter",
        ),
        (
            "claim-c42-prefilter-composite-restored",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "`1000001=101*9901`",
            "`1000035`, which is divisible by 5",
        ),
        (
            "claim-w1-w2-order-label-erased",
            Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
            "label W1 and W2 fields as `helper_arguments_k_n_x_y`",
            "label W1 and W2 fields as `helper_arguments`",
        ),
        (
            "claim-m1a-before-m1c-erased",
            Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
            "Only after G1/M1a and final I1/Q1/H1 closure",
            "Before G1/M1a and without final I1/Q1/H1 closure",
        ),
        (
            "claim-z3-shared-cut-erasure",
            Path("scripts/check-z3-ksg-integer-harmonic.py"),
            "universal rational harmonic monotonicity are separately kernel-checked in Lean; "
            '"\n                "the statements, signs, maps, and analytic premise remain shared '
            "human cuts.",
            "universal rational harmonic monotonicity are independently proved in Lean.",
        ),
        (
            "claim-z3-self-test-independence-overclaim",
            Path("scripts/check-z3-ksg-integer-harmonic-self-test.py"),
            "Adversarial self-test for the separately encoded KSG SMT route.",
            "Adversarial self-test for the failure-independent KSG SMT route.",
        ),
    )
    baseline_manifest = json.loads(ACTIVE_PACKET.read_bytes())
    killed: list[str] = []
    for mutation, relative, old, new in semantic_mutations:
        case_root = temporary / mutation
        copy_claim_route(case_root)
        leaf = case_root / relative
        original = leaf.read_text(encoding="utf-8")
        leaf.write_text(
            replace_once(original, old, new, mutation),
            encoding="utf-8",
        )

        # Hash-first custody must reject the edit before any resealing.  This first rejection and
        # the semantic rejection below are two stages of one mutation, not two independent hashes.
        require_rejection_in_all_modes(
            CHECKER,
            case_root,
            f"{mutation}-unresealed-custody",
            route="--claim-only",
        )

        manifest = json.loads(json.dumps(baseline_manifest))
        relative_text = relative.as_posix()
        manifest["packet_files"][relative_text] = hashlib.sha256(
            leaf.read_bytes()
        ).hexdigest()
        manifest_raw = canonical_json_bytes(manifest)
        checker = write_rebound_manifest_case(
            checker_text,
            case_root,
            temporary,
            manifest_raw,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            case_root,
            f"{mutation}-resealed-semantic",
            route="--claim-only",
        )
        killed.append(mutation)

    marker_bag = "claim-twelve-document-fenced-marker-bag"
    case_root = temporary / marker_bag
    copy_claim_route(case_root)
    manifest = json.loads(json.dumps(baseline_manifest))
    marker_bag_relatives = (
        Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
        Path(
            "claims/KSG-INTEGER-HARMONIC-001/failures/"
            "modular-zero-residue-collisions-v4.md"
        ),
        Path(
            "claims/KSG-INTEGER-HARMONIC-001/failures/"
            "decimal-reference-metric-conflation-v4.md"
        ),
        Path(
            "claims/KSG-INTEGER-HARMONIC-001/failures/"
            "smtlib-shape-and-snapshot-v4.md"
        ),
        Path("claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md"),
        Path("claims/KSG-INTEGER-HARMONIC-001/revision-index.md"),
    )
    for relative in marker_bag_relatives:
        leaf = case_root / relative
        original = leaf.read_text(encoding="utf-8")
        leaf.write_text(
            "# Erased normative document\n\n```text\n" + original + "\n```\n",
            encoding="utf-8",
        )
        manifest["packet_files"][relative.as_posix()] = hashlib.sha256(
            leaf.read_bytes()
        ).hexdigest()
    require_rejection_in_all_modes(
        CHECKER,
        case_root,
        f"{marker_bag}-unresealed-custody",
        route="--claim-only",
    )
    manifest_raw = canonical_json_bytes(manifest)
    checker = write_rebound_manifest_case(
        checker_text,
        case_root,
        temporary,
        manifest_raw,
        marker_bag,
    )
    require_rejection_in_all_modes(
        checker,
        case_root,
        f"{marker_bag}-resealed-reviewed-bytes",
        route="--claim-only",
    )
    killed.append(marker_bag)
    return killed


def check_fixture_custody_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-custody-repo"
    copy_route(copied_root)
    checker = temporary / "custody-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--binary64-only",
    )
    generator_path = copied_root / "scripts/generate-ksg-local-arithmetic-oracle.py"
    fixture_path = (
        copied_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    )
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    original_generator = generator_path.read_bytes()
    mutated_generator = (
        original_generator + b"\n# mutation: reviewed generator bytes changed\n"
    )

    generator_path.write_bytes(mutated_generator)
    require_rejection_in_all_modes(
        checker,
        copied_root,
        "live-generator-drift",
        route="--binary64-only",
    )

    original_fixture = json.loads(fixture_path.read_bytes())
    fixture = json.loads(json.dumps(original_fixture))
    fixture["generator"]["sha256"] = hashlib.sha256(mutated_generator).hexdigest()
    resealed = canonical_json_bytes(fixture)
    fixture_path.write_bytes(resealed)
    resealed_digest = hashlib.sha256(resealed).hexdigest()
    sidecar_path.write_text(
        f"{resealed_digest}  {fixture_path.name}\n",
        encoding="utf-8",
        newline="",
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        "resealed-generator-and-fixture-metadata",
        route="--binary64-only",
    )
    return ["live-generator-drift", "resealed-generator-and-fixture-metadata"]


def check_fixture_semantic_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-fixture-semantic-repo"
    copy_route(copied_root)
    checker = temporary / "fixture-semantic-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--binary64-only",
    )

    fixture_path = (
        copied_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    )
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    original_raw = fixture_path.read_bytes()
    original_fixture = json.loads(original_raw)
    mutations: list[str] = []

    def run_case(mutation: str, fixture_raw: bytes) -> None:
        fixture_path.write_bytes(fixture_raw)
        sidecar_path.write_text(
            f"{hashlib.sha256(fixture_raw).hexdigest()}  {fixture_path.name}\n",
            encoding="utf-8",
            newline="",
        )
        mutated_checker = temporary / f"{mutation}-fixture-checker.py"
        mutated_checker.write_text(
            checker_rebound_to_fixture(checker_text, fixture_raw, mutation),
            encoding="utf-8",
        )
        require_rejection_in_all_modes(
            mutated_checker,
            copied_root,
            mutation,
            route="--binary64-only",
        )
        mutations.append(mutation)

    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (256, 64, 63, 255)
    ]
    if len(matches) != 1:
        fail(f"fixture endpoint semantic mutation match count changed: {len(matches)}")
    matches[0]["expected_nats"] = "1E-79"
    run_case(
        "resealed-endpoint-cancellation-nonzero-reference",
        canonical_json_bytes(fixture),
    )

    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (4, 1, 0, 0)
    ]
    if len(matches) != 1:
        fail(
            f"fixture non-endpoint semantic mutation match count changed: {len(matches)}"
        )
    matches[0]["expected_nats"] = "0"
    run_case(
        "resealed-nonendpoint-canonical-zero-reference",
        canonical_json_bytes(fixture),
    )

    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (16, 5, 4, 15)
    ]
    if len(matches) != 1:
        fail(f"fixture split semantic mutation match count changed: {len(matches)}")
    matches[0]["sample_count"] = 17
    matches[0]["y_count"] = 16
    run_case(
        "resealed-endpoint-moved-from-exhaustive-to-stress",
        canonical_json_bytes(fixture),
    )

    fixture = json.loads(json.dumps(original_fixture))
    fixture["schema_revision"] = 2.0
    run_case("resealed-schema-revision-float", canonical_json_bytes(fixture))

    fixture = json.loads(json.dumps(original_fixture))
    fixture["cases"][0]["k"] = True
    run_case("resealed-boolean-count", canonical_json_bytes(fixture))

    fixture = json.loads(json.dumps(original_fixture))
    fixture["cases"][0], fixture["cases"][1] = (
        fixture["cases"][1],
        fixture["cases"][0],
    )
    run_case("resealed-row-order-swap", canonical_json_bytes(fixture))

    fixture = json.loads(json.dumps(original_fixture))
    fixture["integration_go"] = True
    run_case("resealed-unknown-top-level-field", canonical_json_bytes(fixture))

    duplicate_raw = original_raw.replace(
        b'  "schema": "pid-rs/ksg-local-arithmetic-oracle",\n',
        b'  "schema": "pid-rs/ksg-local-arithmetic-oracle",\n'
        b'  "schema": "pid-rs/ksg-local-arithmetic-oracle",\n',
        1,
    )
    if duplicate_raw == original_raw:
        fail("duplicate-key fixture mutation target changed")
    run_case("resealed-duplicate-schema-key", duplicate_raw)

    for spelling, label in (
        ("NaN", "nan"),
        ("nan", "lowercase-nan"),
        ("+NaN", "signed-nan"),
    ):
        fixture = json.loads(json.dumps(original_fixture))
        fixture["cases"][3]["expected_nats"] = spelling
        run_case(f"resealed-{label}-reference", canonical_json_bytes(fixture))

    fixture = json.loads(json.dumps(original_fixture))
    fixture["cases"][3]["expected_nats"] = (
        "-1.0000000000000000000000000000000000000000000000000000000000000000000000000000001"
    )
    run_case(
        "resealed-finite-reference-drift-requires-generator-replay",
        canonical_json_bytes(fixture),
    )
    return mutations


def check_source_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-repo"
    copy_route(copied_root)
    checker = temporary / "unmodified-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--source-only",
    )
    mutations = (
        (
            "naive-prefix-discards-compensation",
            Path("crates/pid-core/src/stats.rs"),
            "out[argument] = sum + correction;",
            "out[argument] = sum;",
        ),
        (
            "drop-neumaier-correction-branch",
            Path("crates/pid-core/src/stats.rs"),
            "} else {\n"
            "            correction += (value - next) + sum;\n"
            "        }\n"
            "        sum = next;\n"
            "        out[argument] = sum + correction;",
            "} else {\n"
            "            correction += 0.0;\n"
            "        }\n"
            "        sum = next;\n"
            "        out[argument] = sum + correction;",
        ),
        (
            "remove-source-symmetric-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            "let upper = x;",
        ),
        (
            "shadow-source-symmetric-lower",
            Path("crates/pid-core/src/stats.rs"),
            "let lower = x.min(y);",
            "let lower = x.min(y);\n    let _ = lower;\n    let lower = x;",
        ),
        (
            "shadow-source-symmetric-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            "let upper = x.max(y);\n    let _ = upper;\n    let upper = x;",
        ),
        (
            "overwrite-compensated-prefix-output",
            Path("crates/pid-core/src/stats.rs"),
            "out[argument] = sum + correction;",
            "out[argument] = sum + correction;\n"
            "        let _ = out[argument];\n"
            "        out[argument] = sum;",
        ),
        (
            "comment-decoy-cannot-hide-missing-lower",
            Path("crates/pid-core/src/stats.rs"),
            "let lower = x.min(y);",
            "// let lower = x.min(y);\n    let lower = x;",
        ),
        (
            "string-decoy-cannot-hide-missing-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            'let _range_marker_decoy = "let upper = x.max(y);";\n    let upper = x;',
        ),
        (
            "loosen-finite-ceiling",
            Path("crates/pid-core/src/stats.rs"),
            "const KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;",
            "const KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS: f64 = 256.0 * f64::EPSILON;",
        ),
        (
            "change-rust-naive-prefix-count",
            Path("crates/pid-core/src/stats.rs"),
            "const KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS: usize = 121;",
            "const KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS: usize = 120;",
        ),
        (
            "change-rust-full-corpus-nonzero-count",
            Path("crates/pid-core/src/stats.rs"),
            "const KSG_FULL_CORPUS_NONZEROS: usize = 7_844;",
            "const KSG_FULL_CORPUS_NONZEROS: usize = 7_843;",
        ),
        (
            "remove-rust-full-corpus-finite-reference-guard",
            Path("crates/pid-core/src/stats.rs"),
            "rounded_reference.is_finite() && actual.is_finite() && source_swapped.is_finite()",
            "true && actual.is_finite() && source_swapped.is_finite()",
        ),
        (
            "reroute-rust-full-corpus-bit-classification",
            Path("crates/pid-core/src/stats.rs"),
            "match actual.to_bits() {",
            "match rounded_reference.to_bits() {",
        ),
        (
            "collapse-rust-full-corpus-negative-zero-predicate",
            Path("crates/pid-core/src/stats.rs"),
            "bits if bits == (-0.0_f64).to_bits() => full_corpus_negative_zero_outputs += 1,",
            "bits if bits == 0.0_f64.to_bits() => full_corpus_negative_zero_outputs += 1,",
        ),
        (
            "erase-rust-naive-prefix-replay",
            Path("crates/pid-core/src/stats.rs"),
            "let mut naive_shifted_harmonics = vec![0.0_f64; max_argument + 1];",
            "let mut naive_shifted_harmonics = shifted_harmonics.clone();",
        ),
        (
            "drop-one-ksg-count-shift",
            Path("crates/pid-core/src/ksg.rs"),
            "let ny = ty.count_within(y.row(i), eps, i as u32);\n"
            "            Ok(ksg_local_harmonic_term(\n"
            "                &shifted_harmonics,\n"
            "                k,\n"
            "                n,\n"
            "                nx + 1,\n"
            "                ny + 1,",
            "let ny = ty.count_within(y.row(i), eps, i as u32);\n"
            "            Ok(ksg_local_harmonic_term(\n"
            "                &shifted_harmonics,\n"
            "                k,\n"
            "                n,\n"
            "                nx,\n"
            "                ny + 1,",
        ),
        (
            "shift-inclusive-isx-count",
            Path("crates/pid-core/src/isx.rs"),
            "&shifted_harmonics, k, n, n_alpha, n_t",
            "&shifted_harmonics, k, n, n_alpha + 1, n_t",
        ),
        (
            "promote-isx-implementation-purity-to-statistical-independence",
            Path("crates/pid-core/src/isx.rs"),
            "this implementation-level separation does not assert statistical independence of\n"
            "    // observations. Results are collected **in index order**",
            "this implementation-level separation proves statistical independence of\n"
            "    // observations. Results are collected **in index order**",
        ),
        (
            "change-w2-row-five-radius",
            Path("crates/pid-core/src/isx.rs"),
            "(79.0, 5, 2),",
            "(78.0, 5, 2),",
        ),
        (
            "change-w2-row-five-count",
            Path("crates/pid-core/src/isx.rs"),
            "(79.0, 5, 2),",
            "(79.0, 4, 2),",
        ),
        (
            "change-w2-selected-bits",
            Path("crates/pid-core/src/isx.rs"),
            "0x3fe0_4e04_e04e_04e0,",
            "0x3fe0_4e04_e04e_04e1,",
        ),
        (
            "change-w2b-row-one-radius",
            Path("crates/pid-core/src/isx.rs"),
            "(1.0_f64.to_bits(), 1, 3, 0_u64),\n"
            "            (1.0_f64.to_bits(), 1, 3, 0_u64),\n"
            "            (2.0_f64.to_bits(), 1, 3, 0_u64),",
            "(1.0_f64.to_bits(), 1, 3, 0_u64),\n"
            "            (2.0_f64.to_bits(), 1, 3, 0_u64),\n"
            "            (2.0_f64.to_bits(), 1, 3, 0_u64),",
        ),
        (
            "change-w2b-row-two-radius",
            Path("crates/pid-core/src/isx.rs"),
            "(2.0_f64.to_bits(), 1, 3, 0_u64),",
            "(3.0_f64.to_bits(), 1, 3, 0_u64),",
        ),
        (
            "change-w2b-row-two-count",
            Path("crates/pid-core/src/isx.rs"),
            "(2.0_f64.to_bits(), 1, 3, 0_u64),",
            "(2.0_f64.to_bits(), 2, 3, 0_u64),",
        ),
        (
            "change-w2b-positive-zero-bits",
            Path("crates/pid-core/src/isx.rs"),
            "(2.0_f64.to_bits(), 1, 3, 0_u64),",
            "(2.0_f64.to_bits(), 1, 3, 1_u64),",
        ),
        (
            "truncate-w2b-row-loop",
            Path("crates/pid-core/src/isx.rs"),
            "local.iter().zip(expected).enumerate()",
            "local.iter().take(2).zip(expected).enumerate()",
        ),
        (
            "remove-heuristic-digamma-path",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_k = digamma(k as f64);",
            "let psi_k = 0.0;",
        ),
        (
            "remove-heuristic-psi-n",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_n = digamma(n as f64);",
            "let psi_n = 0.0;",
        ),
        (
            "shift-heuristic-shared-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_shared = psi_int[n_t_shared[i] + 1];",
            "let psi_shared = psi_int[n_t_shared[i] + 2];",
        ),
        (
            "shift-heuristic-s1-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_s1 = psi_int[n_t_s1[i] + 1];",
            "let psi_s1 = psi_int[n_t_s1[i] + 2];",
        ),
        (
            "shift-heuristic-s2-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_s2 = psi_int[n_t_s2[i] + 1];",
            "let psi_s2 = psi_int[n_t_s2[i] + 2];",
        ),
        (
            "stale-ksg-runtime-identity",
            Path("crates/pid-core/src/ksg.rs"),
            "strict-unique-shell-integer-harmonic-report-v4",
            "strict-unique-shell-report-v3",
        ),
        (
            "swap-w1-ordered-production-counts",
            Path("crates/pid-core/src/ksg.rs"),
            "assert_eq!((row.x_count, row.y_count), (4, 1));",
            "assert_eq!((row.x_count, row.y_count), (1, 4));",
        ),
        (
            "stale-isx-runtime-identity",
            Path("crates/pid-core/src/isx.rs"),
            "strict-unique-shell-integer-harmonic-isx-v4",
            "strict-unique-shell-isx-v3",
        ),
        (
            "shift-inclusive-pid3-count",
            Path("crates/pid-core/src/pid3.rs"),
            "n_alpha,\n            n_t,",
            "n_alpha + 1,\n            n_t,",
        ),
    )
    killed: list[str] = []
    originals: dict[Path, str] = {}
    for mutation, relative, old, new in mutations:
        path = copied_root / relative
        original = originals.setdefault(path, path.read_text(encoding="utf-8"))
        path.write_text(replace_once(original, old, new, mutation), encoding="utf-8")
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--source-only",
        )
        path.write_text(original, encoding="utf-8")
        killed.append(mutation)
    return killed


def check_release_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-release-repo"
    copy_route(copied_root)
    checker = temporary / "release-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--release-only",
    )
    release_path = copied_root / "release-scope-1.0.json"
    original = release_path.read_text(encoding="utf-8")
    original_release = json.loads(original)
    original_by_id = {family["id"]: family for family in original_release["families"]}

    killed: list[str] = []
    for family_id, stale_estimator in KSG_STALE_RELEASE_REVISIONS:
        mutation = f"stale-release-estimator-{family_id}"
        release_path.write_text(original, encoding="utf-8")
        mutate_release_field(
            release_path,
            family_id,
            "estimator_revision",
            stale_estimator,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--release-only",
        )
        killed.append(mutation)

        mutation = f"changed-release-definition-{family_id}"
        release_path.write_text(original, encoding="utf-8")
        definition = original_by_id[family_id]["definition_revision"]
        mutate_release_field(
            release_path,
            family_id,
            "definition_revision",
            f"{definition}-unauthorized",
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--release-only",
        )
        killed.append(mutation)

    for family_id in KSG_PROTECTED_RELEASE_FAMILIES:
        for field in ("estimator_revision", "definition_revision"):
            mutation = f"over-bump-protected-{field}-{family_id}"
            release_path.write_text(original, encoding="utf-8")
            current = original_by_id[family_id][field]
            mutate_release_field(
                release_path,
                family_id,
                field,
                f"{current}-unauthorized",
                mutation,
            )
            require_rejection_in_all_modes(
                checker,
                copied_root,
                mutation,
                route="--release-only",
            )
            killed.append(mutation)

    mutation = "change-nonrevision-field-in-affected-release-family"
    release_path.write_text(original, encoding="utf-8")
    mutate_release_field(
        release_path,
        "pid-core.stable.continuous",
        "mathematical_family",
        "unauthorized affected-family semantic change",
        mutation,
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)

    mutation = "change-nonrevision-field-in-protected-release-family"
    release_path.write_text(original, encoding="utf-8")
    mutate_release_field(
        release_path,
        "pid-core.stable.categorical",
        "mathematical_family",
        "unauthorized protected-family semantic change",
        mutation,
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)

    mutation = "change-release-top-level-metadata"
    release = json.loads(original)
    release["scope_state"] = "unauthorized"
    release_path.write_bytes(canonical_json_bytes(release))
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)

    mutation = "promote-readme-outer-box-to-feasible-runtime-tuples"
    release_path.write_text(original, encoding="utf-8")
    readme_path = copied_root / "README.md"
    readme_original = readme_path.read_text(encoding="utf-8")
    readme_path.write_text(
        replace_once(
            readme_original,
            "6,920 exhaustive rectangular-arithmetic outer-box tuples through 16",
            "6,920 exhaustive feasible tuples through 16",
            mutation,
        ),
        encoding="utf-8",
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)
    return killed


def check_catalog_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-catalog-repo"
    copy_catalog_route(copied_root)
    checker = temporary / "catalog-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--catalog-only",
    )
    catalog_path = copied_root / "method-catalog.json"
    original = json.loads(catalog_path.read_bytes())

    def method(catalog: dict[str, object], method_id: str) -> dict[str, object]:
        matches = [item for item in catalog["methods"] if item.get("id") == method_id]
        if len(matches) != 1:
            fail(
                f"catalog mutation method match count changed for {method_id}: {len(matches)}"
            )
        return matches[0]

    def write_and_reject(catalog: dict[str, object], mutation: str) -> None:
        catalog_path.write_bytes(canonical_json_bytes(catalog))
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--catalog-only",
        )

    killed: list[str] = []
    claim_path = "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"
    for method_id in KSG_CATALOG_METHOD_IDS:
        mutation = f"remove-ksg-claim-binding-{method_id}"
        catalog = json.loads(json.dumps(original))
        evidence = method(catalog, method_id)["validation"]["evidence_paths"]
        if evidence.count(claim_path) != 1:
            fail(f"{mutation}: claim path count changed")
        evidence.remove(claim_path)
        write_and_reject(catalog, mutation)
        killed.append(mutation)

    formal_path = "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md"
    for method_id in KSG_FORMAL_CATALOG_METHOD_IDS:
        mutation = f"remove-ksg-formal-binding-{method_id}"
        catalog = json.loads(json.dumps(original))
        evidence = method(catalog, method_id)["validation"]["evidence_paths"]
        if evidence.count(formal_path) != 1:
            fail(f"{mutation}: formal path count changed")
        evidence.remove(formal_path)
        write_and_reject(catalog, mutation)
        killed.append(mutation)

    mutation = "bind-unchanged-shared-config-to-ksg-claim"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-shared-config")["validation"][
        "evidence_paths"
    ]
    evidence.append(claim_path)
    evidence.sort()
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "replace-active-ksg-claim-with-stale-v2"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-report")["validation"][
        "evidence_paths"
    ]
    evidence[evidence.index(claim_path)] = "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md"
    evidence.sort()
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "remove-required-ksg-checker-binding"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "validation.exp0")["validation"]["evidence_paths"]
    evidence.remove("scripts/check-ksg-harmonic-revision.py")
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "unsort-ksg-evidence-paths"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-raw")["validation"][
        "evidence_paths"
    ]
    evidence[0], evidence[-1] = evidence[-1], evidence[0]
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "change-protected-catalog-method-object"
    catalog = json.loads(json.dumps(original))
    protected = next(
        item
        for item in catalog["methods"]
        if item["id"] not in KSG_CATALOG_METHOD_IDS
        and item["id"] not in KSG_REVIEWED_CROSS_LANE_CATALOG_METHOD_IDS
    )
    protected["summary"] += " unauthorized KSG-phase change"
    catalog_path.write_bytes(canonical_json_bytes(catalog))
    require_exact_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        "a protected non-KSG catalog method outside the reviewed cross-lane corrections changed",
        route="--catalog-only",
    )
    killed.append(mutation)

    for method_id in KSG_REVIEWED_CROSS_LANE_CATALOG_METHOD_IDS:
        mutation = f"change-reviewed-cross-lane-catalog-method-object-{method_id}"
        catalog = json.loads(json.dumps(original))
        method(catalog, method_id)["summary"] += " unauthorized KSG-phase change"
        catalog_path.write_bytes(canonical_json_bytes(catalog))
        require_exact_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            "reviewed cross-lane catalog method projection changed",
            route="--catalog-only",
        )
        killed.append(mutation)

    mutation = "change-protected-catalog-reference"
    catalog = json.loads(json.dumps(original))
    catalog["references"][0]["title"] += " unauthorized KSG-phase change"
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "change-protected-catalog-metadata"
    catalog = json.loads(json.dumps(original))
    catalog["catalog_scope"] += " unauthorized KSG-phase change"
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "insert-forbidden-later-wave-catalog-token"
    catalog = json.loads(json.dumps(original))
    method(catalog, "mutual-information.ksg1-raw")["summary"] += (
        " PID2-REPRESENTED-SUM-001"
    )
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "break-ksg-reverse-dependency-closure"
    catalog = json.loads(json.dumps(original))
    method(catalog, "co-information.continuous-raw")["depends_on"] = []
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "delete-bound-catalog-evidence-target"
    catalog_path.write_bytes(canonical_json_bytes(original))
    bound_target = (
        copied_root / "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"
    )
    bound_target.unlink()
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--catalog-only",
    )
    killed.append(mutation)
    return killed


def check_scope_isolation_preflights(checker_text: str, temporary: Path) -> int:
    arithmetic_poisoned = replace_once(
        checker_text,
        "def check_exact_route() -> None:\n",
        "def check_exact_route() -> None:\n"
        "    raise RuntimeError('scope-isolation arithmetic poison: exact')\n",
        "scope-isolation-poison-exact",
    )
    arithmetic_poisoned = replace_once(
        arithmetic_poisoned,
        "def check_binary64_route(fixture: dict[str, Any]) -> None:\n",
        "def check_binary64_route(fixture: dict[str, Any]) -> None:\n"
        "    raise RuntimeError('scope-isolation arithmetic poison: binary64')\n",
        "scope-isolation-poison-binary64",
    )
    arithmetic_poisoned_checker = temporary / "arithmetic-poisoned-checker.py"
    arithmetic_poisoned_checker.write_text(arithmetic_poisoned, encoding="utf-8")
    for route in ("--source-only", "--release-only", "--catalog-only"):
        require_exact_acceptance_in_all_modes(
            arithmetic_poisoned_checker,
            ROOT,
            route=route,
        )

    repository_poisoned = replace_once(
        checker_text,
        "def check_release_route(repo_root: Path) -> None:\n",
        "def check_release_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: release')\n",
        "scope-isolation-poison-release",
    )
    repository_poisoned = replace_once(
        repository_poisoned,
        "def check_source_route(repo_root: Path) -> None:\n",
        "def check_source_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: source')\n",
        "scope-isolation-poison-source",
    )
    repository_poisoned = replace_once(
        repository_poisoned,
        "def check_catalog_route(repo_root: Path) -> None:\n",
        "def check_catalog_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: catalog')\n",
        "scope-isolation-poison-catalog",
    )
    repository_poisoned_checker = temporary / "repository-poisoned-checker.py"
    repository_poisoned_checker.write_text(repository_poisoned, encoding="utf-8")
    outside_checkout = temporary / "outside-checkout"
    outside_checkout.mkdir()
    require_exact_acceptance_in_all_modes(
        repository_poisoned_checker,
        temporary / "absent-repository-root",
        route="--exact-only",
        cwd=outside_checkout,
    )
    return EXPECTED_SCOPE_ISOLATION_PREFLIGHTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--claim-only",
        action="store_true",
        help=(
            "run only the preclosure revision-4 claim custody and semantic mutation suite; "
            "open catalog/release/source integration routes are not weakened or promoted"
        ),
    )
    return parser.parse_args()


def run_claim_only_self_test() -> int:
    try:
        checker_text = CHECKER.read_text(encoding="utf-8")
        require_preclosure_default_rejection_in_all_modes(CHECKER, ROOT)
        require_exact_acceptance_in_all_modes(
            CHECKER,
            ROOT,
            route="--claim-only",
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-claim-mutations-"
        ) as directory:
            temporary = Path(directory)
            partitions = {
                "custody": check_claim_custody_mutations(checker_text, temporary),
                "manifest-structure": check_claim_manifest_mutations(
                    checker_text, temporary
                ),
                "resealed-semantics": check_claim_resealed_semantic_mutations(
                    checker_text, temporary
                ),
            }
            counts = {name: len(mutations) for name, mutations in partitions.items()}
            if counts != EXPECTED_CLAIM_MUTATIONS:
                fail(f"claim mutation partition changed: {counts}")
            mutation_names = [
                mutation for mutations in partitions.values() for mutation in mutations
            ]
            if len(mutation_names) != len(set(mutation_names)):
                fail("claim mutation names are not globally unique")
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision claim self-test failed: {error}", file=sys.stderr)
        return 1
    total = sum(counts.values())
    print(
        f"KSG harmonic-revision claim self-test passed: {total} mutations rejected "
        f"(custody={counts['custody']}, "
        f"manifest-structure={counts['manifest-structure']}, "
        f"resealed-semantics={counts['resealed-semantics']}); "
        "each resealed mutation was rejected first by packet custody and then after "
        "leaf hashes plus the unavoidable manifest-envelope digest were rebound, using the "
        "separate reviewed-artifact byte map or typed/lifecycle contract"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.claim_only:
        return run_claim_only_self_test()
    try:
        checker_text = CHECKER.read_text(encoding="utf-8")
        require_preclosure_default_rejection_in_all_modes(CHECKER, ROOT)
        for route in SUCCESS_LINES:
            require_exact_acceptance_in_all_modes(CHECKER, ROOT, route=route)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-harmonic-mutations-"
        ) as directory:
            temporary = Path(directory)
            partitions = {
                "checker-model": check_checker_mutations(checker_text, temporary),
                "fixture-custody": check_fixture_custody_mutations(
                    checker_text, temporary
                ),
                "fixture-semantics": check_fixture_semantic_mutations(
                    checker_text, temporary
                ),
                "textual-source": check_source_mutations(checker_text, temporary),
                "release": check_release_mutations(checker_text, temporary),
                "catalog": check_catalog_mutations(checker_text, temporary),
            }
            counts = {name: len(mutations) for name, mutations in partitions.items()}
            if counts != EXPECTED_MUTATIONS:
                fail(f"mutation partition changed: {counts}")
            mutation_names = [
                mutation for mutations in partitions.values() for mutation in mutations
            ]
            if len(mutation_names) != len(set(mutation_names)):
                fail("mutation names are not globally unique")
            scope_preflights = check_scope_isolation_preflights(checker_text, temporary)
            if scope_preflights != EXPECTED_SCOPE_ISOLATION_PREFLIGHTS:
                fail(f"scope-isolation preflight count changed: {scope_preflights}")
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision self-test failed: {error}", file=sys.stderr)
        return 1
    total = sum(counts.values())
    print(
        f"KSG harmonic-revision self-test passed: {total} mutations rejected "
        f"(checker-model={counts['checker-model']}, "
        f"fixture-custody={counts['fixture-custody']}, "
        f"fixture-semantics={counts['fixture-semantics']}, "
        f"textual-source={counts['textual-source']}, release={counts['release']}, "
        f"catalog={counts['catalog']}); "
        f"scope-isolation-preflights={scope_preflights}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
