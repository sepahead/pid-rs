#!/usr/bin/env python3
"""Hostile process suite for the 108 keyed scalar SxPID3 audit expressions."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-sxpid3-bounded-full-coordinates-self-test.py requires "
        "CPython 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-sxpid3-bounded-full-coordinates.py"
EXPECTED_CHECKER_SOURCE_SHA256 = "d9d1c540930855b31f8190fdb2095d215c736f6f6c3d19c60e2a353923be06d2"
EXPECTED_STDOUT_SHA256 = "69e0844fccff4b28b34bcc9f9f8b8edc04a73a14fbfcced1fdd2edd27da6498f"
TIMEOUT_SECONDS = 180

EXPECTED_CENSUS_INTERPRETATION = {
    "enumeration_measure": "unweighted_counting_measure",
    "enumerated_objects": "labelled_16_cell_nonnegative_integer_count_vectors",
    "count_vector_cell_order": "cell_index=8*s1+4*s2+2*s3+t",
    "total_count_range_inclusive": {"minimum": 1, "maximum": 5},
    "total_labelled_count_vectors": 20_348,
    "tables_by_total_count": [16, 136, 816, 3_876, 15_504],
    "sign_block_denominator": {
        "kind": "labelled_table_antichain_position_pairs",
        "value": 366_264,
        "factorization": {
            "labelled_count_vectors": 20_348,
            "antichain_positions": 18,
        },
        "applies_to_exactly_six_audit_expression_blocks": True,
    },
    "total_count_5_share": {
        "count": 15_504,
        "numerator": 15_504,
        "denominator": 20_348,
        "exact_fraction": "15504/20348",
        "rounded_percent_2dp": "76.19%",
    },
    "normalized_rational_law_repetition": {
        "nonprimitive_count_vectors": 184,
        "meaning": (
            "duplicate_normalized_rational_laws_already_represented_by_primitive_vectors"
        ),
    },
    "support": {
        "maximum_positive_cells": 5,
        "full_support_16_cell_laws": 0,
        "reason": "total_count_at_most_5",
    },
    "within_table_algebraic_structure": {
        "antichain_positions": 18,
        "keyed_scalar_audit_expressions": 108,
        "audit_expression_family_is_algebraically_dependent": True,
        "dependency_families": {
            "cumulative_net_equals_informative_minus_misinformative": 18,
            "atom_net_equals_informative_minus_misinformative": 18,
            "zeta_reconstructs_18_cumulatives_from_18_atoms_per_component": 3,
            "zeta_cumulative_from_atom_identities_total": 54,
            "mobius_inverts_zeta_per_component": 3,
        },
        "independence_or_rank_of_18_base_cumulative_values": "not_adjudicated",
        "minimal_relation_basis_certified": False,
        "not_independent_coordinates_or_degrees_of_freedom": True,
    },
    "probability_or_prevalence_interpretation": False,
    "interpretation_nonclaims": [
        "sampling_probability",
        "population_probability",
        "empirical_prevalence",
    ],
}

EXPECTED_SIGN_SEMANTICS = {
    "exact_product_symbol": "Q",
    "exact_product_domain": "strictly_positive_rational",
    "every_enumerated_exact_product_strictly_positive": True,
    "reported_classification": "sign((1/N) * ln(Q))",
    "equivalent_exact_product_comparison": {
        "negative": "Q<1",
        "zero": "Q=1",
        "positive": "Q>1",
    },
    "zero_class_meaning": "ln(Q)=0_and_audit_expression_equals_zero",
    "zero_class_never_means_product_zero": True,
    "exact_product_zero_possible": False,
    "logarithm_magnitude_certified": False,
}

EXPECTED_METHOD_PROVENANCE_AND_NOVELTY = {
    "paper_defined_functional": {
        "classification": "paper-defined",
        "functional": "categorical_shared_exclusions_i_cap_sx",
        "title": "Introducing a Differentiable Measure of Pointwise Shared Information",
        "authors": ["Abdullah Makkeh", "Aaron J. Gutknecht", "Michael Wibral"],
        "citation": "Physical Review E 103, 032149 (2021)",
        "doi": "10.1103/PhysRevE.103.032149",
        "arxiv": "arXiv:2002.03356v5",
        "intended_equation_labels": [
            "(6)",
            "(13)",
            "(14a)",
            "(15a)",
            "(15b)",
            "(17)",
        ],
        "equation_roles": {
            "(13)": "pointwise_zeta_and_mobius_relation",
            "(17)": "empirical_joint_weighted_average_of_local_values",
        },
        "finite_averaging_linearity_bridge": (
            "finite_linear_averaging_commutes_with_the_finite_zeta_and_mobius_"
            "linear_combination"
        ),
        "equation_17_checked_source": "arXiv:2002.03356v5",
        "publication_to_checker_correspondence": "external_premise_open",
        "machine_checked_correspondence": False,
    },
    "redundancy_lattice_and_order": {
        "classification": "paper-defined",
        "name": "Williams--Beer redundancy lattice and order",
        "title": "Nonnegative Decomposition of Multivariate Information",
        "authors": ["Paul L. Williams", "Randall D. Beer"],
        "year": 2010,
        "arxiv": "arXiv:1004.2515",
        "doi_asserted": False,
        "transferred_scope": "finite_redundancy_lattice_and_order_only",
        "i_min_transfer": False,
    },
    "classical_methods": {
        "classification": "paper-defined",
        "historical_status": "classical",
        "methods": ["finite-poset Mobius inversion", "finite inclusion-exclusion"],
        "title": "On the Foundations of Combinatorial Theory I. Theory of Mobius Functions",
        "author": "Gian-Carlo Rota",
        "year": 1964,
        "doi": "10.1007/BF00531932",
    },
    "project_defined": [
        "108_keyed_scalar_audit_expression_registry",
        "unweighted_labelled_count_vector_census",
        "bounded_sign_counts_by_audit_expression_block",
        "fraction_exact_product_encoding",
        "v2_table_bound_route_neutral_cross_route_stream",
        "process_mutation_and_interpreter_flag_suites",
        "rust_antichain_source_text_order_bridge",
    ],
    "novelty_nonclaims": {
        "new_pid_measure": False,
        "new_mathematical_theorem": False,
        "scientific_priority_claim": False,
    },
}

EXPECTED_CROSS_ROUTE_ASSURANCE = {
    "relationship": "implementation_disjoint_design_not_adjudicated_by_this_checker",
    "implementation_disjoint_design": "not_adjudicated_by_this_checker",
    "independent_source_bytes_bound": False,
    "independent_route_executed": False,
    "paired_route_execution_agreement_claimed": False,
    "logically_independent": False,
    "comparison_performed": (
        "primary_computed_digest_equals_embedded_externally_supplied_expected_"
        "route_neutral_v2_digest"
    ),
    "embedded_expected_digest_authentication_or_custody_bound": False,
    "later_closed_receipt_required_for_paired_route_claim": True,
    "shared_declared_semantics": [
        "human_MGW_formula_transcription",
        "binary_cell_and_mask_convention",
        "empirical_count_weighting",
        "natural_log_specialization",
        "redundancy_order_meaning",
        "N_1_through_5_domain",
        "108_keyed_scalar_audit_expression_registry",
    ],
    "gate": "GO",
    "go_meaning": "primary_lane_local_obligations_passed",
    "scientific_validation": False,
}

EXPECTED_LEGACY_SCHEMA_TERMINOLOGY = {
    "retained_token": "full-coordinates",
    "retained_locations": ["historical_filename", "v2_format_identifier"],
    "compatibility_reason": "preserve_v2_artifact_routing_and_consumers",
    "meaning_in_this_artifact": "108_keyed_scalar_audit_expressions",
    "does_not_mean_independent_coordinates_or_degrees_of_freedom": True,
    "rename_required_at_next_schema_boundary": True,
}

EXPECTED_P1_SEPARATE_LANE_STATUS = {
    "result": "source_marginal_informative_invariance",
    "relationship": "outside_this_artifact_and_separate_lane",
    "replayed_by_this_checker": False,
    "result_imported_by_this_checker": False,
    "semantic_transfer_to_this_bounded_audit": "none",
    "status_inferred_by_this_checker": False,
}

EXPECTED_NONCLAIMS = [
    "not_mgw_paper_correspondence",
    "not_logarithm_interval_or_magnitude_certification",
    "not_binary64_or_floating_point_correspondence",
    "not_arbitrary_source_target_domains_or_total_counts",
    "not_pointwise_audit_expression_certification",
    "not_parser_schema_or_certificate_verification",
    "not_current_rust_or_python_api_refinement",
    "not_rust_name_resolution_compilation_execution_or_numeric_correspondence",
    "not_population_estimator_sampling_support_calibration_or_causal_claim",
    "not_global_mathematical_correctness_or_formula_correspondence",
    "not_artifact_authenticity_attestation_or_external_custody",
    "not_mutation_suite_completeness",
    "not_independent_route_source_or_execution_binding",
    "not_cross_route_logical_independence",
    "not_new_pid_measure_theorem_or_scientific_priority_claim",
    "not_scientific_validation",
    "not_programs_a_through_e_closure",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_with_options(
    path: Path, python_options: tuple[str, ...]
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, *python_options, str(path)]
    environment = {
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        env=environment,
    )


def run(path: Path, optimized: bool = False) -> subprocess.CompletedProcess[str]:
    python_options = (("-O",) if optimized else ()) + ("-I", "-S", "-B")
    return run_with_options(path, python_options)


def run_pair(
    path: Path,
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    """Run one exact script in admitted normal and optimized child lanes."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        baseline_future = executor.submit(run, path)
        optimized_future = executor.submit(run, path, True)
        return baseline_future.result(), optimized_future.result()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    require(source.count(old) == 1, f"{label}: mutation target count was {source.count(old)}")
    return source.replace(old, new, 1)


def has_assert_statement(source: str) -> bool:
    return any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(source)))


def main() -> int:
    checker_bytes = CHECKER.read_bytes()
    require(
        hashlib.sha256(checker_bytes).hexdigest() == EXPECTED_CHECKER_SOURCE_SHA256,
        "checker source identity",
    )
    baseline, optimized = run_pair(CHECKER)
    require(
        baseline.returncode == optimized.returncode == 0,
        baseline.stderr + optimized.stderr,
    )
    require(baseline.stderr == optimized.stderr == "", "baseline wrote stderr")
    require(baseline.stdout == optimized.stdout, "normal and optimized outputs differ")
    require(
        hashlib.sha256(baseline.stdout.encode("utf-8")).hexdigest()
        == EXPECTED_STDOUT_SHA256,
        "canonical stdout identity",
    )
    payload = json.loads(baseline.stdout)
    require(payload["gate"] == "GO", "baseline gate")
    require(
        payload["assumptions"]
        == [
            "three_ordered_binary_sources_and_one_binary_target",
            "nonnegative_integer_cell_counts_with_positive_total_one_through_five",
            "source_event_is_or_of_within_mask_conjunctions",
            "misinformative_event_is_source_event_intersected_with_keyed_target",
            "natural_log_audit_expression_is_one_over_total_times_log_of_exact_product",
            "108_keyed_scalar_audit_expressions_equal_18_antichain_positions_times_2_representation_stages_times_3_components",
            "row_cumulative_column_atom_zeta_orientation",
        ],
        "assumption roster drift",
    )
    scope = payload["bounded_exhaustive_scope"]
    require(scope["binary_labeled_count_tables"] == 20_348, "bounded table count")
    require(scope["primitive_rational_laws"] == 20_164, "primitive-law count")
    require(
        scope["nonprimitive_rescaled_count_vectors"] == 184,
        "nonprimitive count-vector count",
    )
    require(scope["tables_by_total"][-1] == 15_504, "total-count-five table count")
    require(scope["maximum_positive_cells"] == 5, "maximum positive-cell count")
    require(scope["full_support_16_cell_laws"] == 0, "full-support law count")
    require(
        scope["averaged_keyed_scalar_audit_expression_product_verdicts"]
        == 2_197_584,
        "108 keyed scalar audit-expression verdict count",
    )
    require(
        scope["strictly_positive_exact_product_checks"] == 2_197_584,
        "strictly-positive exact-product check count",
    )
    require(
        scope["sign_block_denominator_table_antichain_position_pairs"]
        == 366_264,
        "sign-block denominator",
    )
    require(
        scope["pointwise_audit_expressions_evaluated"] == 0,
        "pointwise scope boundary",
    )
    require(
        scope["pointwise_scope_clarification"]
        == {
            "pointwise_atom_coordinates_or_values_output": False,
            "local_event_ratios_evaluated": True,
            "local_event_ratio_role": (
                "factors_aggregated_only_into_averaged_exact_products"
            ),
        },
        "pointwise factor-versus-output boundary",
    )
    require(
        scope["supported_table_realization_pairs_counted"] == 77_520,
        "supported-pair count",
    )
    require(
        payload["audit_expression_registry"]
        == {
            "block_count": 6,
            "component_count": 3,
            "keyed_scalar_audit_expression_count": 108,
            "antichain_position_count": 18,
            "representation_stage_count": 2,
            "representation_stages": ["cumulative_values", "mobius_atoms"],
            "revision": (
                "sxpid3-audit-lexicographic-antichain-order-averaged-"
                "keyed-expressions-108-v3"
            ),
            "sha256": "6ada33aa90382316ae0757ed7f449e9fa9a35db3a7d4aec8aa3660a4c6e3c3d5",
        },
        "audit-expression registry",
    )
    require(
        scope["route_native_result_stream_sha256"]
        == "315592501f49021ed86218ba1c277b9e9b764ace9621c8b4df61bb5868f3ead0",
        "route-native result-stream anchor",
    )
    require(
        scope["neutral_cross_route_audit_expression_stream_sha256"]
        == "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8",
        "neutral table-bound cross-route result stream",
    )
    require(
        payload["digest_classification"][
            "neutral_table_bound_audit_expression_result_stream"
        ]
        == (
            "primary_result_compared_only_to_embedded_externally_supplied_"
            "expected_digest_not_paired_route_execution_or_proof"
        ),
        "cross-route evidence ceiling",
    )
    require(
        payload["digest_classification"][
            "audit_expression_registry_event_semantic_corpus_and_native_result"
        ]
        == "same_route_regression_and_drift_anchors_not_logically_independent_truth",
        "same-route digest evidence ceiling",
    )
    require(
        payload["census_interpretation"] == EXPECTED_CENSUS_INTERPRETATION,
        "census interpretation or dependency boundary drift",
    )
    require(
        payload["sign_semantics"] == EXPECTED_SIGN_SEMANTICS,
        "sign semantics drift",
    )
    require(
        payload["method_provenance_and_novelty"]
        == EXPECTED_METHOD_PROVENANCE_AND_NOVELTY,
        "method provenance or novelty boundary drift",
    )
    require(
        payload["cross_route_assurance"] == EXPECTED_CROSS_ROUTE_ASSURANCE,
        "cross-route relationship or GO boundary drift",
    )
    require(
        payload["gate_scope"]
        == {
            "meaning": "primary_lane_local_obligations_passed",
            "scientific_validation": False,
        },
        "lane-local GO scope drift",
    )
    require(
        payload["legacy_schema_terminology"]
        == EXPECTED_LEGACY_SCHEMA_TERMINOLOGY,
        "legacy full-coordinates schema boundary drift",
    )
    require(
        payload["p1_separate_lane_status"] == EXPECTED_P1_SEPARATE_LANE_STATUS,
        "P1 separate-lane boundary drift",
    )
    require(
        payload["lattice"]["audit_to_rust_node_index_by_key"]
        == [0, 1, 3, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        "audit-to-Rust key bridge",
    )
    require(
        payload["lattice"]["rust_to_audit_node_index_by_key"]
        == [0, 1, 3, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        "Rust-to-audit key bridge",
    )
    require(
        payload["lattice"]["rust_order_source_function_sha256"]
        == "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb07",
        "Rust order source anchor",
    )
    require(payload["status_classification"]["rust_refinement"] == "open", "Rust nonclaim")
    require(
        payload["status_classification"]
        ["independent_route_source_and_execution_binding"]
        == "absent",
        "standalone independent-route binding nonclaim",
    )
    require(
        payload["status_classification"]["paired_route_agreement"]
        == "requires_later_closed_receipt",
        "paired-route receipt boundary",
    )
    require(
        payload["status_classification"]["p1_informative_invariance"]
        == "outside_artifact_separate_lane_not_replayed",
        "P1 status classification",
    )
    require(
        scope["bounded_sign_counts_by_audit_expression_block"]
        == {
            "atom.informative": {
                "negative": 0,
                "positive": 145_100,
                "zero": 221_164,
            },
            "atom.misinformative": {
                "negative": 0,
                "positive": 71_468,
                "zero": 294_796,
            },
            "atom.net": {
                "negative": 31_284,
                "positive": 96_768,
                "zero": 238_212,
            },
            "cumulative.informative": {
                "negative": 0,
                "positive": 321_856,
                "zero": 44_408,
            },
            "cumulative.misinformative": {
                "negative": 0,
                "positive": 278_984,
                "zero": 87_280,
            },
            "cumulative.net": {
                "negative": 29_496,
                "positive": 252_816,
                "zero": 83_952,
            },
        },
        "closed six-block bounded sign counts",
    )
    require(
        payload["retained_witnesses"]["negative_net"]["atom_net_product"] == "9/16",
        "negative witness",
    )
    require(
        payload["retained_witnesses"]["exact_zero"]["atom_net_product"] == "1/1",
        "exact-zero witness",
    )
    require(payload["nonclaims"] == EXPECTED_NONCLAIMS, "nonclaim roster drift")
    require(
        payload["serialization"]
        == {
            "cell_index_formula": "cell_index=8*s1+4*s2+2*s3+t",
            "neutral_cross_route_domain_ascii": (
                "pid-rs.sxpid3.table-bound-audit-expressions.v2\\0"
            ),
            "neutral_framing_unit_sha256": (
                "035c467bcf756e4009db452ec43f48747ce0f70ebdb43780d9925bf5124c24d2"
            ),
            "neutrality_scope": (
                "route_neutral_representation_scoped_strictly_to_explicit_v2"
            ),
            "neutral_table_frame": (
                "u32_ordinal_then_16_u8_counts_then_108_keyed_expression_records"
            ),
            "neutral_expression_record": (
                "u8_expression_index_then_u16_key_length_then_ascii_key_then_"
                "three_i64_prime_exponents_then_i8_log_sign"
            ),
            "log_sign_byte_semantics": (
                "minus1_if_Q_lt_1_zero_if_Q_eq_1_plus1_if_Q_gt_1"
            ),
            "route_native_stream_retained_separately": True,
        },
        "neutral stream serialization contract",
    )

    # These are interpreter-contract controls rather than source mutants.  Because `-I` implies
    # both `-E` and `-P`, the first two controls necessarily also omit `-I`; the dedicated
    # missing-`-I` control supplies `-E -P` explicitly so that only isolated mode is absent.
    interpreter_flag_controls = (
        ("missing-E", ("-P", "-S", "-B")),
        ("missing-P", ("-E", "-S", "-B")),
        ("missing-I", ("-E", "-P", "-S", "-B")),
        ("missing-S", ("-I", "-B")),
        ("missing-B", ("-I", "-S")),
        ("unsupported-OO", ("-OO", "-I", "-S", "-B")),
    )
    isolation_stderr = (
        "ERROR: check-sxpid3-bounded-full-coordinates.py requires "
        "CPython 3.11+ -I -S -B, with -O optional\n"
    )
    for label, python_options in interpreter_flag_controls:
        rejected = run_with_options(CHECKER, python_options)
        require(rejected.returncode == 2, f"{label}: exit {rejected.returncode}")
        require(rejected.stdout == "", f"{label}: unexpected stdout {rejected.stdout!r}")
        require(
            rejected.stderr == isolation_stderr,
            f"{label}: expected {isolation_stderr!r}, found {rejected.stderr!r}",
        )

    source = checker_bytes.decode("utf-8", errors="strict")
    require(not has_assert_statement(source), "checker contains optimization-removable assert")
    mutations = (
        (
            "missing-mask",
            "MASKS: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7)",
            "MASKS: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6)",
            "ANTICHAIN.registry",
        ),
        (
            "source-bit-registry",
            "SOURCE_BITS: Final[tuple[int, ...]] = (1, 2, 4)",
            "SOURCE_BITS: Final[tuple[int, ...]] = (2, 1, 4)",
            "MASK.source_bit_registry",
        ),
        (
            "cell-index-formula",
            "index == 8 * source[0] + 4 * source[1] + 2 * source[2] + target",
            "index == 4 * source[0] + 8 * source[1] + 2 * source[2] + target",
            "MASK.cell_formula",
        ),
        (
            "stable-key-width",
            "f\"{mask:02x}\" for mask in antichain",
            "f\"{mask:03x}\" for mask in antichain",
            "ANTICHAIN.audit_stable_keys",
        ),
        (
            "rust-order-swapped-03-04",
            '    "02",\n    "04",\n    "03",\n    "05",',
            '    "02",\n    "03",\n    "04",\n    "05",',
            "RUST_ORDER.stable_keys",
        ),
        (
            "rust-order-source-anchor",
            "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb07",
            "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb06",
            "RUST_ORDER.function_sha256",
        ),
        (
            "audit-to-rust-key-map",
            "0, 1, 3, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17",
            "0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17",
            "ORDER_BRIDGE.audit_to_rust",
        ),
        (
            "audit-expression-block-duplicate",
            '("cumulative", "informative"),',
            '("cumulative", "net"),',
            "AUDIT_EXPRESSION.registry_shape",
        ),
        (
            "audit-expression-block-drop",
            '    ("atom", "net"),\n',
            "",
            "AUDIT_EXPRESSION.registry_shape",
        ),
        (
            "audit-expression-block-swap",
            '    ("cumulative", "informative"),\n    ("cumulative", "misinformative"),',
            '    ("cumulative", "misinformative"),\n    ("cumulative", "informative"),',
            "AUDIT_EXPRESSION.registry_sha256",
        ),
        (
            "audit-expression-key-permutation",
            "        for key in keys\n",
            "        for key in reversed(keys)\n",
            "AUDIT_EXPRESSION.registry_sha256",
        ),
        (
            "audit-expression-registry-anchor",
            "6ada33aa90382316ae0757ed7f449e9fa9a35db3a7d4aec8aa3660a4c6e3c3d5",
            "6ada33aa90382316ae0757ed7f449e9fa9a35db3a7d4aec8aa3660a4c6e3c3d4",
            "AUDIT_EXPRESSION.registry_sha256",
        ),
        (
            "event-outer-or",
            "return any(\n        all(\n            anchor[index] == candidate[index]",
            "return all(\n        all(\n            anchor[index] == candidate[index]",
            "EVENT.dual_encoding",
        ),
        (
            "event-inner-and",
            "return any(\n        all(\n            anchor[index] == candidate[index]",
            "return any(\n        any(\n            anchor[index] == candidate[index]",
            "EVENT.dual_encoding",
        ),
        (
            "event-source-axis-remap",
            "zip(\n            SOURCE_BITS, anchor, candidate, strict=True",
            "zip(\n            reversed(SOURCE_BITS), anchor, candidate, strict=True",
            "EVENT.dual_encoding",
        ),
        (
            "event-truth-anchor",
            "7bcf2a3b5d03566f8b402f387e95942969606af32d76cd02f8ee2b0e85546087",
            "7bcf2a3b5d03566f8b402f387e95942969606af32d76cd02f8ee2b0e85546086",
            "EVENT.truth_registry_sha256",
        ),
        (
            "zeta-transpose",
            "int(redundancy_le(atom, cumulative)) for atom in nodes",
            "int(redundancy_le(cumulative, atom)) for atom in nodes",
            "ZETA.row_signatures",
        ),
        (
            "zeta-row-permutation",
            "return [\n        [int(redundancy_le(atom, cumulative)) for atom in nodes]\n        for cumulative in nodes\n    ]",
            "return list(reversed([\n        [int(redundancy_le(atom, cumulative)) for atom in nodes]\n        for cumulative in nodes\n    ]))",
            "ZETA.row_signatures",
        ),
        (
            "zeta-key-column-permutation",
            "int(redundancy_le(atom, cumulative)) for atom in nodes",
            "int(redundancy_le(atom, cumulative)) for atom in reversed(nodes)",
            "ZETA.row_signatures",
        ),
        (
            "mobius-row-reversal",
            "return [row[size:] for row in augmented]",
            "return list(reversed([row[size:] for row in augmented]))",
            "MOBIUS.sparse_rows",
        ),
        (
            "semantic-registry-anchor",
            "7cf8b96fe5ce3039f6fd98fbf59adb7c442018e630680b6e7998bb6cdf5c2ba6",
            "7cf8b96fe5ce3039f6fd98fbf59adb7c442018e630680b6e7998bb6cdf5c2ba7",
            "SEMANTIC.registry_sha256",
        ),
        (
            "target-intersection",
            "JOINT_INDEX[(SOURCE_STATES[candidate_index], anchor_target)]",
            "JOINT_INDEX[(SOURCE_STATES[candidate_index], 1 - anchor_target)]",
            "PRODUCT.source_event_bounds",
        ),
        (
            "empirical-count-weight",
            "plus *= Fraction(total, source_event_count) ** cell_count",
            "plus *= Fraction(total, source_event_count)",
            "WITNESS.empirical_count_weighting",
        ),
        (
            "misinformative-count-weight",
            "minus *= Fraction(target_count, restricted_event_count) ** cell_count",
            "minus *= Fraction(target_count, restricted_event_count)",
            "WITNESS.empirical_count_weighting",
        ),
        (
            "misinformative-target-mass",
            "minus *= Fraction(target_count, restricted_event_count) ** cell_count",
            "minus *= Fraction(total, restricted_event_count) ** cell_count",
            "WITNESS.target_intersection",
        ),
        (
            "net-multiplication",
            "left / right for left, right in zip(numerator, denominator, strict=True)",
            "left * right for left, right in zip(numerator, denominator, strict=True)",
            "WITNESS.negative_net_atom",
        ),
        (
            "self-redundancy-target-denominator",
            "source_counts[projected] * target_counts[target],",
            "source_counts[projected] * total,",
            "RECONSTRUCTION.self_redundancy",
        ),
        (
            "replication-exponent",
            'replicated == primitive**gcd, "REPLICATION.product_power"',
            'replicated == primitive ** (gcd + 1), "REPLICATION.product_power"',
            "REPLICATION.product_power",
        ),
        (
            "omit-total-five",
            "for total in range(1, MAX_TOTAL + 1):",
            "for total in range(1, MAX_TOTAL):",
            "CORPUS.tables_by_total",
        ),
        (
            "result-stream-anchor",
            "315592501f49021ed86218ba1c277b9e9b764ace9621c8b4df61bb5868f3ead0",
            "315592501f49021ed86218ba1c277b9e9b764ace9621c8b4df61bb5868f3ead1",
            "ROUTE_NATIVE_RESULT.stream_sha256",
        ),
        (
            "neutral-prime-order",
            "for prime in (2, 3, 5):",
            "for prime in (2, 5, 3):",
            "NEUTRAL_STREAM.framing_unit_sha256",
        ),
        (
            "neutral-result-stream-anchor",
            "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8",
            "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b9",
            "NEUTRAL_STREAM.stream_sha256",
        ),
        (
            "neutral-frame-omit-count-vector",
            "    digest.update(encoded_counts)\n",
            "    digest.update(b\"\")\n",
            "NEUTRAL_STREAM.framing_unit_counts",
        ),
        (
            "neutral-frame-reverse-count-vector",
            "    encoded_counts = bytes(counts)\n",
            "    encoded_counts = bytes(reversed(counts))\n",
            "NEUTRAL_STREAM.framing_unit_counts",
        ),
        (
            "neutral-frame-wrong-count-vector-order",
            "    encoded_counts = bytes(counts)\n",
            "    encoded_counts = bytes((*counts[1:], counts[0]))\n",
            "NEUTRAL_STREAM.framing_unit_counts",
        ),
        (
            "sign-count-anchor",
            '"atom.net": {"negative": 31_284, "positive": 96_768, "zero": 238_212}',
            '"atom.net": {"negative": 31_285, "positive": 96_768, "zero": 238_212}',
            "AUDIT_EXPRESSION.bounded_sign_counts_by_block",
        ),
    )
    ast_only_mutations = (
        (
            "assert-backslide",
            '    require(nodes == EXPECTED_ANTICHAINS, "ANTICHAIN.registry")',
            '    assert nodes == EXPECTED_ANTICHAINS, "ANTICHAIN.registry"',
        ),
    )

    with tempfile.TemporaryDirectory(prefix="pid-rs-sxpid3-full-self-test-") as directory:
        temporary = Path(directory)
        temporary_scripts = temporary / "scripts"
        temporary_scripts.mkdir()
        rust_source = ROOT / "crates/pid-core/src/discrete_pid.rs"
        temporary_rust_source = temporary / "crates/pid-core/src/discrete_pid.rs"
        temporary_rust_source.parent.mkdir(parents=True)
        temporary_rust_source.write_bytes(rust_source.read_bytes())
        for label, old, new, expected_code in mutations:
            mutated = replace_once(source, old, new, label)
            path = temporary_scripts / f"{label}.py"
            path.write_text(mutated, encoding="utf-8")
            result, optimized_result = run_pair(path)
            expected_stderr = f"SxPID3 bounded audit expressions: {expected_code}\n"
            for lane, observed in (("normal", result), ("optimized", optimized_result)):
                require(
                    observed.returncode == 1,
                    f"{label}/{lane}: exit {observed.returncode}",
                )
                require(
                    observed.stdout == "",
                    f"{label}/{lane}: unexpected stdout {observed.stdout!r}",
                )
                require(
                    observed.stderr == expected_stderr,
                    f"{label}/{lane}: expected {expected_stderr!r}, "
                    f"found {observed.stderr!r}",
                )
            require(
                result.stdout == optimized_result.stdout
                and result.stderr == optimized_result.stderr,
                f"{label}: normal/optimized rejection differed",
            )

        for label, old, new in ast_only_mutations:
            mutated = replace_once(source, old, new, label)
            require(
                has_assert_statement(mutated),
                f"{label}: assert mutation not detected",
            )

    summary = {
        "ast_only_control_count": len(ast_only_mutations),
        "baseline_stdout_sha256": EXPECTED_STDOUT_SHA256,
        "format": "/pid-rs/sxpid3-bounded-full-coordinates-self-test/v2",
        "gate": "GO",
        "gate_scope": {
            "meaning": "self_test_lane_local_obligations_passed",
            "scientific_validation": False,
            "mutation_suite_completeness": False,
            "artifact_authenticity_attestation_or_external_custody": False,
            "global_mathematical_correctness_or_formula_correspondence": False,
        },
        "interpreter_flag_hostile_control_count": len(interpreter_flag_controls),
        "legacy_schema_terminology": EXPECTED_LEGACY_SCHEMA_TERMINOLOGY,
        "nonclaims": [
            "not_artifact_authenticity_attestation_or_external_custody",
            "not_global_mathematical_correctness_or_formula_correspondence",
        ],
        "normal_optimized_parity": True,
        "process_mutation_count": len(mutations),
        "process_mutation_lanes": 2 * len(mutations),
    }
    print(json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        print(f"SxPID3 bounded audit expressions self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
