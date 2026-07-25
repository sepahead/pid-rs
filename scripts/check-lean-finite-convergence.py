#!/usr/bin/env python3
"""Build the pinned Lean proof of finite-alphabet deterministic convergence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit" / "formal" / "lean"
TOOLCHAIN = "leanprover/lean4:v4.32.0"
MATHLIB_URL = "https://github.com/leanprover-community/mathlib4.git"
MATHLIB_REVISION = "81a5d257c8e410db227a6665ed08f64fea08e997"
EXPECTED_MANIFEST_SHA256 = (
    "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
)
EXPECTED_PACKAGE_PINS = {
    "mathlib": (
        MATHLIB_URL,
        MATHLIB_REVISION,
        "v4.32.0",
        False,
    ),
    "plausible": (
        "https://github.com/leanprover-community/plausible",
        "e12c1910fe855cbfc38803cd4e55543906d5fa62",
        "main",
        True,
    ),
    "LeanSearchClient": (
        "https://github.com/leanprover-community/LeanSearchClient",
        "c5d5b8fe6e5158def25cd28eb94e4141ad97c843",
        "main",
        True,
    ),
    "importGraph": (
        "https://github.com/leanprover-community/import-graph",
        "7e9612bf0b9ee66db3cb5b9988a35afc706f5a12",
        "main",
        True,
    ),
    "proofwidgets": (
        "https://github.com/leanprover-community/ProofWidgets4",
        "6e311e2a844da9b2cc3971187df2fe0066947b93",
        "main",
        True,
    ),
    "aesop": (
        "https://github.com/leanprover-community/aesop",
        "a7dbf0c63b694e47f425f3dcddbc0e178bb432d3",
        "master",
        True,
    ),
    "Qq": (
        "https://github.com/leanprover-community/quote4",
        "38d591e778f100aec9762bb582f9c7f55f50e9dc",
        "master",
        True,
    ),
    "batteries": (
        "https://github.com/leanprover-community/batteries",
        "023ce7d62a0531e22a5331e20b587817a80d49ff",
        "main",
        True,
    ),
    "Cli": (
        "https://github.com/leanprover/lean4-cli",
        "88679d088c9720c27ebdf2ba4dafe17341747f94",
        "v4.32.0",
        True,
    ),
}
EXPECTED_LAKEFILE = """name = "pid-finite-convergence"
version = "0.1.0"
defaultTargets = ["PidFiniteConvergence"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4.git"
rev = "v4.32.0"

[[lean_lib]]
name = "PidFiniteConvergence"
"""
EXPECTED_SOURCES = {
    "PidFiniteConvergence.lean",
    "PidFiniteConvergenceSemanticContract.lean",
    "PidFiniteConvergence/Dependence.lean",
    "PidFiniteConvergence/Deterministic.lean",
    "PidFiniteConvergence/FractionalCover.lean",
    "PidFiniteConvergence/LocalContinuity.lean",
    "PidFiniteConvergence/SupportChangeContinuity.lean",
    "PidFiniteConvergence/SxEventBridge.lean",
}
EXPECTED_ROOT_SOURCE = """import PidFiniteConvergence.Dependence
import PidFiniteConvergence.Deterministic
import PidFiniteConvergence.FractionalCover
import PidFiniteConvergence.LocalContinuity
import PidFiniteConvergence.SupportChangeContinuity
import PidFiniteConvergence.SxEventBridge
"""
EXPECTED_MODULE_DECLARATIONS = {
    "PidFiniteConvergence/Dependence.lean": (
        "theorem abs_event_sum_le_half_l1",
        "def positiveCoordinateEvent",
        "theorem sum_positive_coordinate_event_eq_half_l1",
        "theorem positive_cell_of_half_l1_control",
        "theorem abs_log_ratio_le_neg_log_one_sub",
        "theorem abs_log_change_le_local_modulus",
        "theorem local_log_modulus_mono",
        "theorem neg_log_one_sub_le_ratio",
        "theorem neg_log_one_sub_le_four_thirds",
        "theorem refined_log_modulus_linearized_chain",
        "theorem sum_le_effective_color_numerator",
        "theorem effective_color_numerator_le_card_mul_sum",
        "theorem effective_color_factor_bounds",
        "theorem abs_linear_row_le_abs_row_sum",
        "theorem abs_weighted_average_change_le",
        "theorem abs_weight_change_against_bounded_values_le_half_range",
        "theorem abs_weighted_average_change_le_pointwise_plus_half_range",
        "theorem telescoping_anytime_spending",
        "theorem telescoping_anytime_spending_le_one",
        "theorem concentration_radius_exponent_cancels",
    ),
    "PidFiniteConvergence/Deterministic.lean": (
        "theorem eventually_positive_of_tendsto",
        "theorem tendsto_event_mass",
        "theorem event_mass_positive_of_mem",
        "theorem event_mass_eventually_positive_of_mem",
        "theorem tendsto_log_of_positive",
        "theorem tendsto_neg_log_of_positive",
        "theorem tendsto_neg_mul_log",
        "theorem tendsto_neg_mul_log_zero",
        "theorem tendsto_log_ratio_of_positive",
        "theorem tendsto_finite_linear_combination",
        "theorem tendsto_finite_weighted_sum",
        "theorem tendsto_finite_minimum",
        "theorem tendsto_finite_weighted_log_ratio_linear_combination",
    ),
    "PidFiniteConvergence/FractionalCover.lean": (
        "def positiveMassSupport",
        "def equivalenceClassCoverWeight",
        "def equivalenceNeighborhoodOverlapLoad",
        "theorem equivalence_class_neighborhood_eq_of_related",
        "theorem equivalence_class_event_mass_positive_on_support",
        "theorem positive_support_filter_event_sum_eq_event_mass",
        "theorem equivalence_class_cover_weight_le_one",
        "theorem equivalence_neighborhood_overlap_load_eq_cover_sum",
        "theorem equivalence_class_overlap_load_le_total",
        "theorem finite_event_mass_nonnegative",
        "theorem equivalence_neighborhood_overlap_load_nonnegative",
        "theorem finite_event_mass_mono",
        "theorem finite_event_mass_union_le",
        "theorem finite_event_mass_biUnion_le_sum",
        "theorem finite_equivalence_union_event_mass_positive_on_support",
        "theorem finite_equivalence_union_ratio_le_branch_sum",
        "theorem finite_equivalence_union_overlap_load_le_of_nonempty",
        "theorem finite_equivalence_union_overlap_load_le",
        "theorem finite_equivalence_union_fractional_cover_bound",
        "theorem finite_equivalence_union_fractional_cover_bounds",
        "theorem sx_source_fractional_cover_bound",
        "theorem sx_target_restricted_fractional_cover_bound",
        "theorem sx_target_fractional_cover_bound",
    ),
    "PidFiniteConvergence/LocalContinuity.lean": (
        "theorem abs_zero_sum_weighted_sum_le_half_oscillation",
        "def negativeLogEventGradient",
        "theorem negative_log_event_gradient_diameter_le",
        "def nestedLogRatioGradient",
        "theorem nested_log_ratio_gradient_bounds",
        "theorem nested_log_ratio_gradient_diameter_le",
        "def intersectionPmiGradient",
        "theorem intersection_pmi_gradient_diameter_le",
        "inductive DiamondCoordinate",
        "def ordinaryDiamondGradientFromReciprocals",
        "theorem ordinary_diamond_gradient_exact_diameter_of_reciprocal_bounds",
        "theorem ordinary_diamond_gradient_refined_diameter_of_reciprocal_bounds",
        "theorem ordinary_diamond_gradient_diameter_of_reciprocal_bounds",
        "theorem ordinary_diamond_gradient_signs_of_reciprocal_bounds",
        "theorem ordinary_diamond_reciprocal_supermodular",
        "def ordinaryDiamondGradient",
        "theorem ordinary_diamond_gradient_exact_coordinate_diameter_le",
        "theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_left_le_right",
        "theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_right_le_left",
        "theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained",
        "theorem ordinary_diamond_gradient_refined_coordinate_diameter_le",
        "theorem ordinary_diamond_gradient_coordinate_diameter_le",
        "def ordinaryDiamondRatio",
        "theorem ordinary_diamond_ratio_cross_multiplication_bounds",
        "theorem ordinary_diamond_ratio_bounds",
        "def ordinaryDiamondPhi",
        "theorem ordinary_diamond_phi_nonnegative",
        "theorem ordinary_diamond_phi_le_floor_log_ceiling",
        "theorem ordinary_diamond_floor_log_ceiling_eq",
        "theorem ordinary_diamond_phi_le_floor_radius_sub_twice_correction",
        "theorem ordinary_diamond_phi_floor_bounds",
        "theorem ordinary_diamond_floor_radius_sub_twice_correction_nonnegative",
        "inductive ConditionedNestedCoordinate",
        "def conditionedNestedLiftedGradientFromReciprocals",
        "def conditionedNestedLiftedGradientLowerFromReciprocals",
        "def conditionedNestedLiftedGradientUpperFromReciprocals",
        "theorem conditioned_nested_lifted_gradient_candidate_diameter_eq_of_reciprocals",
        "theorem conditioned_nested_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds",
        "theorem conditioned_nested_lifted_gradient_diameter_of_reciprocal_bounds",
        "def conditionedNestedLiftedGradient",
        "def conditionedNestedLiftedGradientLower",
        "def conditionedNestedLiftedGradientUpper",
        "theorem conditioned_nested_lifted_gradient_between_candidate_extrema",
        "theorem conditioned_nested_lifted_gradient_lower_attained",
        "theorem conditioned_nested_lifted_gradient_upper_attained",
        "theorem conditioned_nested_lifted_gradient_exact_coordinate_diameter_le",
        "theorem conditioned_nested_lifted_gradient_exact_coordinate_diameter_attained",
        "theorem conditioned_nested_lifted_gradient_candidate_diameter_eq",
        "theorem conditioned_nested_lifted_gradient_closed_form_coordinate_diameter_le",
        "theorem conditioned_nested_lifted_gradient_closed_form_coordinate_diameter_attained",
        "theorem conditioned_nested_lifted_gradient_coordinate_diameter_le",
        "theorem conditioned_nested_lifted_gradient_zero_side_mass_witness",
        "theorem conditioned_nested_lifted_gradient_zero_side_mass_exact_diameter",
        "theorem conditioned_nested_lifted_gradient_no_positive_uniform_subtraction",
        "inductive ConditionedDiamondCoordinate",
        "def conditionedDiamondLiftedGradientFromReciprocals",
        "def conditionedDiamondLiftedGradientLowerFromReciprocals",
        "def conditionedDiamondLiftedGradientUpperFromReciprocals",
        "theorem conditioned_diamond_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds",
        "theorem conditioned_diamond_lifted_gradient_refined_diameter_of_reciprocal_bounds",
        "theorem conditioned_diamond_lifted_gradient_diameter_of_reciprocal_bounds",
        "def conditionedDiamondLiftedGradient",
        "def conditionedDiamondLiftedGradientLower",
        "def conditionedDiamondLiftedGradientUpper",
        "theorem conditioned_diamond_lifted_gradient_between_candidate_extrema",
        "theorem conditioned_diamond_lifted_gradient_lower_attained",
        "theorem conditioned_diamond_lifted_gradient_upper_attained",
        "theorem conditioned_diamond_lifted_gradient_exact_coordinate_diameter_le",
        "theorem conditioned_diamond_lifted_gradient_exact_coordinate_diameter_attained",
        "theorem conditioned_diamond_lifted_gradient_refined_coordinate_diameter_le",
        "theorem conditioned_diamond_lifted_gradient_refined_bound_attained_ordered",
        "theorem conditioned_diamond_lifted_gradient_refined_bound_attained",
        "theorem conditioned_diamond_lifted_gradient_probability_domain_coordinate_diameter_le",
        "theorem conditioned_diamond_lifted_gradient_probability_domain_absolute_coordinate_le",
        "theorem conditioned_diamond_lifted_gradient_coordinate_diameter_le",
        "theorem component_coordinate_bounds_of_nonnegative_top_sum",
        "theorem abs_mobius_row_change_le_abs_row_sum",
        "theorem net_value_bounds_of_component_bounds",
        "theorem component_weighted_average_bounds",
        "theorem net_weighted_average_bounds",
        "theorem abs_component_weight_change_le_half_range",
        "theorem abs_net_weight_change_le_range",
        "theorem abs_component_average_change_le",
        "theorem abs_net_average_change_le",
        "theorem abs_component_linear_row_average_change_le",
        "theorem abs_net_linear_row_average_change_le",
        "theorem segment_event_mass_lower_bound_factorized",
        "theorem segment_event_mass_positive_of_floor",
    ),
    "PidFiniteConvergence/SupportChangeContinuity.lean": (
        "def overlapMass",
        "def leftResidual",
        "def rightResidual",
        "theorem overlap_add_left_residual",
        "theorem overlap_add_right_residual",
        "theorem left_residual_nonnegative",
        "theorem right_residual_nonnegative",
        "theorem left_or_right_residual_eq_zero",
        "theorem left_residual_sub_right_residual",
        "theorem abs_sub_eq_left_add_right_residual",
        "theorem sum_left_residual_eq_sum_right_residual",
        "theorem sum_abs_sub_eq_two_mul_sum_left_residual",
        "theorem sum_overlap_eq_one_sub_sum_left_residual",
        "theorem left_residual_le_of_nonnegative",
        "theorem right_residual_le_of_nonnegative",
        "def residualEntropy",
        "def residualPositiveSupport",
        "theorem residual_eq_zero_outside_positive_support",
        "theorem positive_support_card_positive_of_sum_positive",
        "theorem sum_positive_support_eq_sum",
        "theorem left_right_positive_support_disjoint",
        "theorem residual_entropy_nonnegative",
        "theorem sum_neg_mul_log_le_card_mul_neg_mul_log_average",
        "theorem residual_entropy_le_card_mul_neg_mul_log_average",
        "theorem card_mul_neg_mul_log_average_eq_mass_mul_log_card_div_mass",
        "theorem residual_entropy_le_mass_mul_log_card_div_mass",
        "theorem card_mul_card_le_balanced_ambient",
        "theorem add_residual_entropy_le_mass_mul_log_card_product_div_mass_sq",
        "theorem add_residual_entropy_le_balanced_ambient_bound",
        "theorem overlap_residual_entropy_sum_le_balanced_ambient_bound",
        "theorem residual_weighted_component_between_zero_and_entropy",
        "theorem abs_residual_weighted_signed_value_le_entropy",
        "theorem abs_component_residual_sub_le_max_entropy",
        "theorem abs_signed_residual_sub_le_add_entropy",
        "theorem abs_overlap_component_residual_sub_le_max_entropy",
        "theorem abs_overlap_signed_residual_sub_le_add_entropy",
        "def downSetZetaMatrix",
        "theorem mobius_row_sum_eq_ite_bot",
        "def equivalenceUnionCommonModulus",
        "theorem equivalence_union_common_modulus_zero",
        "theorem equivalence_union_common_modulus_one",
        "theorem equivalence_union_common_modulus_nonnegative",
        "theorem equivalence_union_common_modulus_le_linear",
        "theorem equivalence_union_common_modulus_closed_interval_bounds",
    ),
    "PidFiniteConvergence/SxEventBridge.lean": (
        "abbrev CategoricalKey",
        "def sourceCollectionEquivalent",
        "def targetEquivalent",
        "def sourceTargetCollectionEquivalent",
        "theorem source_collection_equivalence",
        "theorem target_equivalence",
        "theorem source_target_collection_equivalence",
        "def sourceBranchEvent",
        "def targetBranchEvent",
        "def sourceTargetBranchEvent",
        "def IsEquivalenceClassNeighborhood",
        "def IsFiniteEquivalenceUnion",
        "theorem equivalence_class_neighborhood_anchor_mem",
        "theorem finite_equivalence_union_anchor_mem",
        "theorem source_branch_is_equivalence_class",
        "theorem target_branch_is_equivalence_class",
        "theorem source_target_branch_is_equivalence_class",
        "theorem source_branch_anchor_mem",
        "theorem target_branch_anchor_mem",
        "theorem source_target_branch_anchor_mem",
        "def sxSourceEvent",
        "def sxTargetRestrictedEvent",
        "theorem sx_source_event_equivalence_union",
        "theorem sx_target_restricted_event_equivalence_union",
        "theorem sx_target_event_equivalence_union",
        "theorem sx_source_event_anchor_mem",
        "theorem sx_target_restricted_event_anchor_mem",
        "theorem source_target_branch_event_eq_inter",
        "theorem sx_target_restricted_event_eq_inter",
        "structure SxKeyedEvents",
        "def sxKeyedEvents",
        "def sxKeyedEventsUnderLaw",
        "theorem sx_keyed_events_fixed_across_laws",
        "def finiteEventMass",
        "theorem sx_source_event_mass_positive",
        "theorem sx_target_event_mass_positive",
        "theorem sx_target_restricted_event_mass_positive",
    ),
}
EXPECTED_DECLARATION_COUNT = 225
EXPECTED_THEOREM_COUNT = 177
SEMANTIC_CONTRACT_SOURCE = "PidFiniteConvergenceSemanticContract.lean"
EXPECTED_SEMANTIC_CONTRACT_SHA256 = (
    "10cc4874aa763c103d2648db3d289735f809c29d97dd246a68f09c2c5f40b794"
)
REMOVED_ENVIRONMENT_KEYS = (
    "ELAN_TOOLCHAIN",
    "LEAN_PATH",
    "LEAN_SRC_PATH",
    "LEAN_SYSROOT",
)
TIMEOUT_SECONDS = 900
GIT_TIMEOUT_SECONDS = 30


class LeanProofError(RuntimeError):
    """Raised when the pinned formal artifact cannot be checked."""


SOURCE_DECLARATION_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\n]*\]\s+)*"
    r"(?:(?:noncomputable|private|protected|unsafe|partial|nonrec)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|inductive)\s+"
    r"([^\s({:\[]+)"
)


def read_regular_text(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise LeanProofError(f"could not read UTF-8 file {path}: {error}") from error


def read_regular_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise LeanProofError(f"could not read file {path}: {error}") from error


def check_toolchain() -> None:
    actual = read_regular_text(PROJECT / "lean-toolchain")
    if actual != f"{TOOLCHAIN}\n":
        raise LeanProofError(
            f"lean-toolchain must contain exactly {TOOLCHAIN!r} and one newline"
        )


def check_lakefile() -> None:
    actual = read_regular_text(PROJECT / "lakefile.toml")
    if actual != EXPECTED_LAKEFILE:
        raise LeanProofError(
            "lakefile.toml does not match the pinned project declaration"
        )


def check_manifest() -> None:
    path = PROJECT / "lake-manifest.json"
    raw = read_regular_bytes(path)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != EXPECTED_MANIFEST_SHA256:
        raise LeanProofError(
            "Lake manifest byte digest mismatch: "
            f"expected {EXPECTED_MANIFEST_SHA256}, found {actual_sha256}"
        )
    try:
        manifest = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise LeanProofError(f"invalid Lake manifest JSON: {error}") from error
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LeanProofError("Lake manifest packages must be a list")
    if not all(isinstance(package, dict) for package in packages):
        raise LeanProofError("each Lake manifest package must be an object")
    package_map = {package.get("name"): package for package in packages}
    if len(package_map) != len(packages):
        raise LeanProofError("Lake manifest package names must be unique")
    expected_names = set(EXPECTED_PACKAGE_PINS)
    actual_names = set(package_map)
    if actual_names != expected_names:
        raise LeanProofError(
            "Lake manifest package set mismatch: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )
    for name, (
        url,
        revision,
        input_revision,
        inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        package = package_map[name]
        expected = {
            "type": "git",
            "url": url,
            "rev": revision,
            "inputRev": input_revision,
            "inherited": inherited,
        }
        mismatches = {
            key: (expected_value, package.get(key))
            for key, expected_value in expected.items()
            if package.get(key) != expected_value
        }
        if mismatches:
            raise LeanProofError(f"{name} manifest pin mismatch: {mismatches}")


def mask_lean_comments_and_strings(text: str, path: Path) -> str:
    """Mask comments and strings while retaining line structure for source scans."""
    masked = list(text)
    index = 0
    block_depth = 0
    in_string = False
    while index < len(text):
        if block_depth:
            if text.startswith("/-", index):
                masked[index] = " "
                masked[index + 1] = " "
                block_depth += 1
                index += 2
            elif text.startswith("-/", index):
                masked[index] = " "
                masked[index + 1] = " "
                block_depth -= 1
                index += 2
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
            continue
        if in_string:
            if text[index] == "\\":
                masked[index] = " "
                index += 1
                if index < len(text):
                    if text[index] != "\n":
                        masked[index] = " "
                    index += 1
            elif text[index] == '"':
                masked[index] = " "
                in_string = False
                index += 1
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
            continue
        if text.startswith("/-", index):
            masked[index] = " "
            masked[index + 1] = " "
            block_depth = 1
            index += 2
        elif text.startswith("--", index):
            while index < len(text) and text[index] != "\n":
                masked[index] = " "
                index += 1
        elif text[index] == '"':
            masked[index] = " "
            in_string = True
            index += 1
        else:
            index += 1
    if block_depth:
        raise LeanProofError(f"unterminated block comment while scanning {path}")
    if in_string:
        raise LeanProofError(f"unterminated string while scanning {path}")
    return "".join(masked)


def source_declaration_inventory(text: str, path: Path) -> tuple[str, ...]:
    masked = mask_lean_comments_and_strings(text, path)
    return tuple(
        f"{match.group(1)} {match.group(2)}"
        for match in SOURCE_DECLARATION_PATTERN.finditer(masked)
    )


def expected_theorem_names() -> tuple[str, ...]:
    expected_module_sources = EXPECTED_SOURCES - {
        "PidFiniteConvergence.lean",
        SEMANTIC_CONTRACT_SOURCE,
    }
    actual_module_sources = set(EXPECTED_MODULE_DECLARATIONS)
    if actual_module_sources != expected_module_sources:
        raise LeanProofError(
            "internal imported-module inventory set mismatch: "
            f"missing={sorted(expected_module_sources - actual_module_sources)}, "
            f"unexpected={sorted(actual_module_sources - expected_module_sources)}"
        )
    declarations = tuple(
        declaration
        for module_declarations in EXPECTED_MODULE_DECLARATIONS.values()
        for declaration in module_declarations
    )
    if len(declarations) != EXPECTED_DECLARATION_COUNT:
        raise LeanProofError(
            "internal expected declaration inventory count mismatch: "
            f"expected {EXPECTED_DECLARATION_COUNT}, found {len(declarations)}"
        )
    allowed_kinds = {"theorem", "def", "abbrev", "structure", "inductive"}
    malformed = tuple(
        declaration
        for declaration in declarations
        if len(declaration.split(" ", 1)) != 2
        or declaration.split(" ", 1)[0] not in allowed_kinds
    )
    if malformed:
        raise LeanProofError(
            f"internal expected declaration inventory is malformed: {malformed}"
        )
    theorems = tuple(
        declaration.split(" ", 1)[1]
        for declaration in declarations
        if declaration.startswith("theorem ")
    )
    if len(theorems) != EXPECTED_THEOREM_COUNT:
        raise LeanProofError(
            "internal expected theorem inventory count mismatch: "
            f"expected {EXPECTED_THEOREM_COUNT}, found {len(theorems)}"
        )
    if len(set(theorems)) != len(theorems):
        raise LeanProofError("expected source theorem names must be globally unique")
    return theorems


def check_sources() -> tuple[int, int, tuple[str, ...]]:
    theorem_names = expected_theorem_names()
    sources = sorted(
        source
        for source in PROJECT.rglob("*.lean")
        if ".lake" not in source.relative_to(PROJECT).parts
    )
    if not sources:
        raise LeanProofError("Lean project contains no source files")
    relative_sources = {source.relative_to(PROJECT).as_posix() for source in sources}
    if relative_sources != EXPECTED_SOURCES:
        raise LeanProofError(
            "Lean source manifest mismatch: "
            f"missing={sorted(EXPECTED_SOURCES - relative_sources)}, "
            f"unexpected={sorted(relative_sources - EXPECTED_SOURCES)}"
        )
    placeholder = re.compile(r"\b(?:admit|axiom|constant|sorry|sorryAx)\b")
    for source in sources:
        text = read_regular_text(source)
        relative_source = source.relative_to(PROJECT).as_posix()
        if (
            source == PROJECT / "PidFiniteConvergence.lean"
            and text != EXPECTED_ROOT_SOURCE
        ):
            raise LeanProofError(
                "PidFiniteConvergence.lean must import the pinned checked submodule set exactly"
            )
        if (
            relative_source in EXPECTED_MODULE_DECLARATIONS
            or relative_source == SEMANTIC_CONTRACT_SOURCE
        ) and (
            "set_option warningAsError true\n" not in text
        ):
            raise LeanProofError(f"the checked module must enable warningAsError: {source}")
        masked = mask_lean_comments_and_strings(text, source)
        match = placeholder.search(masked)
        if match is not None:
            raise LeanProofError(
                f"forbidden proof placeholder or declaration in {source}: {match.group(0)}"
            )
        expected_declarations = EXPECTED_MODULE_DECLARATIONS.get(relative_source)
        if expected_declarations is not None:
            actual_declarations = source_declaration_inventory(text, source)
            if actual_declarations != expected_declarations:
                raise LeanProofError(
                    f"source declaration inventory mismatch in {relative_source}: "
                    f"expected={expected_declarations}, found={actual_declarations}"
                )
        if relative_source == SEMANTIC_CONTRACT_SOURCE:
            actual_sha256 = hashlib.sha256(read_regular_bytes(source)).hexdigest()
            if actual_sha256 != EXPECTED_SEMANTIC_CONTRACT_SHA256:
                raise LeanProofError(
                    "Lean semantic-contract source digest mismatch: "
                    f"expected {EXPECTED_SEMANTIC_CONTRACT_SHA256}, "
                    f"found {actual_sha256}"
                )
        if source == (
            PROJECT
            / "PidFiniteConvergence"
            / "SxEventBridge.lean"
        ):
            required_dependent_product_fragments = (
                "sourceValue : sourceIndex → Type v",
                "((source : sourceIndex) → sourceValue source) × targetValue",
                "[∀ source, Fintype (sourceValue source)]",
                "[∀ source, DecidableEq (sourceValue source)]",
            )
            missing_fragments = tuple(
                fragment
                for fragment in required_dependent_product_fragments
                if fragment not in masked
            )
            if missing_fragments:
                raise LeanProofError(
                    "finite categorical Sx event bridge must use the exact "
                    "heterogeneous dependent Cartesian product; "
                    f"missing={missing_fragments}"
                )
            if "sourceValue : Type v" in masked:
                raise LeanProofError(
                    "finite categorical Sx event bridge regressed to a shared "
                    "source-value alphabet"
                )
    return len(sources), EXPECTED_DECLARATION_COUNT, theorem_names


def find_lake() -> Path:
    candidate = shutil.which("lake")
    if candidate is None:
        raise LeanProofError("lake was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"lake is not an executable file: {path}")
    return path


def find_git() -> Path:
    candidate = shutil.which("git")
    if candidate is None:
        raise LeanProofError("git was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"git is not an executable file: {path}")
    return path


def run_git(git: Path, checkout: Path, arguments: list[str], description: str) -> str:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    try:
        process = subprocess.run(
            [str(git), "-C", str(checkout), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}: {process.stderr.strip()}"
        )
    return process.stdout


def check_dependency_checkouts(git: Path) -> None:
    packages_directory = PROJECT / ".lake" / "packages"
    for name, (
        url,
        revision,
        _input_revision,
        _inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        checkout = packages_directory / name
        if not checkout.is_dir() or checkout.is_symlink():
            raise LeanProofError(
                f"dependency checkout is not a regular directory: {checkout}"
            )
        top_level = Path(
            run_git(
                git, checkout, ["rev-parse", "--show-toplevel"], f"{name} root check"
            ).strip()
        )
        if top_level.resolve() != checkout.resolve():
            raise LeanProofError(
                f"dependency checkout root mismatch for {name}: {top_level}"
            )
        actual_revision = run_git(
            git, checkout, ["rev-parse", "--verify", "HEAD"], f"{name} revision check"
        ).strip()
        if actual_revision != revision:
            raise LeanProofError(
                f"dependency revision mismatch for {name}: "
                f"expected {revision}, found {actual_revision}"
            )
        actual_url = run_git(
            git,
            checkout,
            ["config", "--local", "--get", "remote.origin.url"],
            f"{name} origin check",
        ).strip()
        if actual_url != url:
            raise LeanProofError(
                f"dependency origin mismatch for {name}: expected {url}, found {actual_url}"
            )
        status = run_git(
            git,
            checkout,
            ["status", "--porcelain=v1", "--untracked-files=all"],
            f"{name} cleanliness check",
        )
        if status:
            raise LeanProofError(f"dependency checkout is not clean: {name}")


def run_checked(
    command: list[str],
    description: str,
    *,
    input_text: str | None = None,
) -> str:
    environment = os.environ.copy()
    for key in REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    try:
        process = subprocess.run(
            command,
            cwd=PROJECT,
            env=environment,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}:\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout


def theorem_axiom_audit_source(theorem_names: tuple[str, ...]) -> str:
    declarations = "\n".join(
        "    ``PidFiniteConvergence." + theorem + ","
        for theorem in theorem_names
    )
    return f"""import PidFiniteConvergence
import Lean.Util.CollectAxioms

open Lean

run_cmd do
  let allowed :=
    ({{}} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let declarations : Array Name := #[
{declarations}
  ]
  unless declarations.size == {EXPECTED_THEOREM_COUNT} do
    throwError
      m!"theorem axiom-audit inventory has {{declarations.size}} entries, "
        ++ m!"expected {EXPECTED_THEOREM_COUNT}"
  for declaration in declarations do
    let used ← collectAxioms declaration
    for assumption in used do
      unless allowed.contains assumption do
        throwError
          m!"unexpected logical assumption {{assumption}} used by {{declaration}}"
"""


def check_version(lake: Path) -> str:
    output = run_checked([str(lake), "env", "lean", "--version"], "Lean version check")
    lines = output.splitlines()
    if (
        len(lines) != 1
        or re.fullmatch(r"Lean \(version 4\.32\.0, .+\)", lines[0]) is None
    ):
        raise LeanProofError(f"unexpected Lean version output: {output!r}")
    return lines[0]


def main() -> int:
    try:
        check_toolchain()
        check_lakefile()
        check_manifest()
        source_count, declaration_count, theorem_names = check_sources()
        lake = find_lake()
        git = find_git()
        version = check_version(lake)
        check_dependency_checkouts(git)
        run_checked([str(lake), "build", "PidFiniteConvergence"], "Lean proof build")
        run_checked(
            [str(lake), "env", "leanchecker", "PidFiniteConvergence"],
            "Lean kernel replay",
        )
        run_checked(
            [str(lake), "env", "lean", SEMANTIC_CONTRACT_SOURCE],
            "Lean paper-facing semantic-contract check",
        )
        run_checked(
            [str(lake), "env", "lean", "--stdin"],
            "complete source-theorem axiom-basis audit",
            input_text=theorem_axiom_audit_source(theorem_names),
        )
    except LeanProofError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: checked {source_count} Lean sources with an exact ordered "
        f"{declaration_count}-declaration inventory across six imported modules, "
        f"all {len(theorem_names)} source theorems against the permitted axiom basis, "
        f"and the separate event/fractional-cover/generic-Mobius semantic contract "
        f"({version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
