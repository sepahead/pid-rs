#!/usr/bin/env python3
"""Fail-closed mutation suite for the implementation-disjoint-design SxPID3 lane."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


class SelfTestError(RuntimeError):
    pass


EXPECTED_CHECKER_SOURCE_SHA256 = "8670614f168408110109207b2da746664ea0f3a54196362c1e76be97ad418ad7"
EXPECTED_FULL_STDOUT_SHA256 = "63e1470075f7fca88e9a8d82d52cdfcb56d389b4b3c7ac4d5ccba5071d6c2212"
EXPECTED_PROBE_STDOUT_SHA256 = "70164d375465299f4f00070313ec7e754ad99dc0dd27a4dd47ade03dde4b1308"
EXPECTED_TABLE_BOUND_RESULT_SHA256 = "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8"
EXPECTED_FRAMING_PROBE_SHA256 = "f115265206099bac95b22149dc83c98fed2de93c4265a001c232266e02f4d813"
EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK = {
    "atom.informative": {"negative": 0, "positive": 145_100, "zero": 221_164},
    "atom.misinformative": {"negative": 0, "positive": 71_468, "zero": 294_796},
    "atom.net": {"negative": 31_284, "positive": 96_768, "zero": 238_212},
    "cumulative.informative": {"negative": 0, "positive": 321_856, "zero": 44_408},
    "cumulative.misinformative": {"negative": 0, "positive": 278_984, "zero": 87_280},
    "cumulative.net": {"negative": 29_496, "positive": 252_816, "zero": 83_952},
}
EXPECTED_CENSUS_INTERPRETATION = {
    "enumeration_weighting": "unweighted",
    "enumerated_objects": "labelled_16_cell_count_vectors",
    "count_vector_cell_order": "cell_index=8*s1+4*s2+2*s3+t",
    "applies_to_blocks": [
        "cumulative.informative",
        "cumulative.misinformative",
        "cumulative.net",
        "atom.informative",
        "atom.misinformative",
        "atom.net",
    ],
    "block_denominator": {
        "kind": "table_node_pairs",
        "value": 366_264,
        "factorization": {"labelled_count_vectors": 20_348, "antichain_nodes": 18},
    },
    "total_count_5_share": {
        "numerator": 15_504,
        "denominator": 20_348,
        "exact_fraction": "15504/20348",
        "rounded_percentage": 76.19,
        "percentage_rounding": "two_decimal_places",
    },
    "normalized_law_repetition": {
        "nonprimitive_count_vectors": 184,
        "meaning": "repeat_normalized_empirical_laws_already_represented_by_primitive_vectors",
    },
    "support": {"maximum_positive_cells": 5, "full_support_16_cell_laws": 0},
    "within_table_audit_expression_dependencies": {
        "audit_expression_count": 108,
        "algebraically_independent": False,
        "exact_dependency_families": [
            {
                "family": "cumulative_net_identity",
                "instances_per_table": 18,
                "identity": "cumulative.net=cumulative.informative-cumulative.misinformative",
            },
            {
                "family": "atom_net_identity",
                "instances_per_table": 18,
                "identity": "atom.net=atom.informative-atom.misinformative",
            },
            {
                "family": "zeta_reconstruction",
                "components": 3,
                "nodes_per_component": 18,
                "instances_per_table": 54,
                "identity": "cumulative=zeta_sum_of_atoms_equivalently_atom_is_Mobius_inversion",
            },
        ],
        "eighteen_base_cumulative_values": {
            "per_component_count": 18,
            "rank": "not_adjudicated",
            "algebraic_independence": "not_adjudicated",
        },
    },
    "prevalence_or_probability_interpretation": False,
    "interpretation_nonclaims": ["prevalence", "sampling_probability", "population_probability"],
}
EXPECTED_SIGN_SEMANTICS = {
    "exact_product_symbol": "Q",
    "every_exact_product_strictly_positive": True,
    "reported_classification": "sign((1/N) * ln(Q))",
    "equivalent_exact_product_comparison": {
        "negative": "Q<1",
        "zero": "Q=1",
        "positive": "Q>1",
    },
    "zero_meaning": {
        "averaged_log_expression": "zero",
        "exact_product": "Q=1",
        "product_zero": False,
    },
    "exact_product_zero_possible": False,
    "magnitude_certified": False,
    "stream_i8_semantics": "log_sign_equivalently_comparison_of_exact_positive_Q_to_one",
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
        "intended_equation_labels": ["(6)", "(13)", "(14a)", "(15a)", "(15b)", "(17)"],
        "equation_roles": {
            "(13)": "pointwise_zeta_Mobius_relation",
            "(17)": "averages_local_values_with_empirical_joint_weights",
        },
        "finite_averaging_relation": {
            "classification": "paper-derived",
            "statement": "finite_linear_averaging_commutes_with_finite_zeta_Mobius_combination",
        },
        "publication_to_checker_correspondence": "external_premise",
        "machine_checked_correspondence": False,
    },
    "redundancy_lattice": {
        "classification": "paper-defined",
        "name": "Williams--Beer redundancy lattice",
        "title": "Nonnegative Decomposition of Multivariate Information",
        "authors": ["Paul L. Williams", "Randall D. Beer"],
        "arxiv_only": "arXiv:1004.2515",
        "doi_asserted": False,
        "transferred_scope": "redundancy_lattice_only",
        "i_min_transfer": False,
    },
    "finite_poset_methods": {
        "classification": "paper-defined",
        "historical_status": "classical",
        "methods": ["finite-poset Möbius inversion", "finite inclusion-exclusion"],
        "title": "On the Foundations of Combinatorial Theory I. Theory of Möbius Functions",
        "author": "Gian-Carlo Rota",
        "year": 1964,
        "doi": "10.1007/BF00531932",
    },
    "project_defined": [
        "108_key_audit_expression_registry",
        "bounded_sign_counts_by_audit_expression_block",
        "prime_exponent_exact_product_encoding",
        "v2_route_and_representation_neutral_table_bound_stream",
        "process_level_mutation_suite",
        "implementation_disjoint_checker_route",
    ],
    "novelty_nonclaims": {
        "new_pid_measure": False,
        "new_mathematical_theorem": False,
        "priority_claim": False,
    },
    "numeric_correspondence_nonclaims": {
        "binary64_correspondence": False,
        "floating_point_correspondence": False,
        "logarithm_magnitude_correspondence": False,
    },
}
EXPECTED_ROUTE_ASSURANCE = {
    "relationship": "implementation_disjoint_design_under_shared_semantics_described_not_source_bound",
    "implementation_disjoint_design_described": True,
    "semantically_independent": False,
    "implementation_disjoint_dimensions": [
        "count_table_enumeration",
        "antichain_generation",
        "event_mass_evaluation",
        "atom_recovery",
        "exact_product_encoding",
    ],
    "shared_semantics": [
        "human_MGW_formula_transcription",
        "binary_cell_and_mask_convention",
        "empirical_count_weighting",
        "natural_log_specialization",
        "redundancy_order_meaning",
        "N_le_5_domain_definition",
        "108_key_audit_registry",
    ],
    "standalone_primary_binding": {
        "primary_source_bound": False,
        "primary_source_imported": False,
        "primary_source_executed": False,
    },
    "route_and_representation_neutral_v2_digest": {
        "comparison_target": "embedded_external_expected_digest",
        "paired_source_bound_execution_established": False,
        "agreement_claim": "standalone_expected_digest_match_only",
    },
    "required_later_closure": "source_bound_paired_execution_closed_receipt",
    "status": "GO",
    "go_meaning": "lane_local_obligations_passed",
    "scientific_validation": False,
}
SELF_TEST_GATE_SCOPE = {
    "status": "GO",
    "go_meaning": "self_test_lane_local_obligations_passed",
    "scientific_validation": False,
    "mutation_suite_completeness": False,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def require_isolated_cpython() -> None:
    require(sys.implementation.name == "cpython", "PYTHON.implementation")
    require(sys.version_info >= (3, 11), "PYTHON.minimum_version")
    require(sys.flags.ignore_environment == 1, "PYTHON.ignore_environment")
    require(sys.flags.safe_path is True, "PYTHON.safe_path")
    require(sys.flags.isolated == 1, "PYTHON.isolated")
    require(sys.flags.no_site == 1, "PYTHON.no_site")
    require(sys.flags.dont_write_bytecode == 1, "PYTHON.dont_write_bytecode")
    require(sys.flags.optimize in (0, 1), "PYTHON.optimize")


require_isolated_cpython()


@dataclass(frozen=True)
class Mutation:
    name: str
    old: str
    new: str


MUTATIONS = (
    Mutation(
        "accept-comparable-antichain-members",
        "not is_strict_subset(left, right) and not is_strict_subset(right, left)",
        "not is_strict_subset(left, right) or not is_strict_subset(right, left)",
    ),
    Mutation(
        "lexicographic-node-order-without-cardinality",
        "nodes.sort(key=lambda node: (len(node), node))",
        "nodes.sort(key=lambda node: (node, len(node)))",
    ),
    Mutation(
        "swap-audit-keys-03-04",
        '    "02",\n    "03",\n    "04",\n    "05",',
        '    "02",\n    "04",\n    "03",\n    "05",',
    ),
    Mutation(
        "reverse-redundancy-subset-test",
        "return all(any((a & b) == a for a in lower) for b in upper)",
        "return all(any((a & b) == b for a in lower) for b in upper)",
    ),
    Mutation(
        "swap-s1-s2-cell-decoding",
        "((cell >> 3) & 1) | (((cell >> 2) & 1) << 1) | (((cell >> 1) & 1) << 2)",
        "((cell >> 2) & 1) | (((cell >> 3) & 1) << 1) | (((cell >> 1) & 1) << 2)",
    ),
    Mutation(
        "reverse-inclusion-exclusion-parity",
        "if subset_size % 2 == 1:\n            total += cylinder_mass",
        "if subset_size % 2 == 0:\n            total += cylinder_mass",
    ),
    Mutation(
        "discard-prior-branches-in-intersection-mask",
        "intersection_mask |= branch_mask",
        "intersection_mask = branch_mask",
    ),
    Mutation(
        "omit-target-intersection",
        "target_selector = 2 if target is None else target",
        "target_selector = 2",
    ),
    Mutation(
        "uniform-support-weight-in-informative-lane",
        "scale(exponent_ratio(marginals.total, union_mass), count)",
        "scale(exponent_ratio(marginals.total, union_mass), 1)",
    ),
    Mutation(
        "uniform-support-weight-in-misinformative-lane",
        "scale(exponent_ratio(target_mass, joint_mass), count)",
        "scale(exponent_ratio(target_mass, joint_mass), 1)",
    ),
    Mutation(
        "use-joint-mass-in-informative-denominator",
        "exponent_ratio(marginals.total, union_mass)",
        "exponent_ratio(marginals.total, joint_mass)",
    ),
    Mutation(
        "use-total-mass-in-misinformative-numerator",
        "exponent_ratio(target_mass, joint_mass)",
        "exponent_ratio(marginals.total, joint_mass)",
    ),
    Mutation(
        "add-components-for-signed-net",
        "net = tuple(sub(plus[index], minus[index]) for index in range(len(NODES)))",
        "net = tuple(add(plus[index], minus[index]) for index in range(len(NODES)))",
    ),
    Mutation(
        "add-strict-lower-atoms-instead-of-subtracting",
        "value = sub(value, lower_value)",
        "value = add(value, lower_value)",
    ),
    Mutation(
        "omit-atom-net-block",
        "for kind, component in BLOCKS for node in NODES",
        "for kind, component in BLOCKS[:-1] for node in NODES",
    ),
    Mutation(
        "replace-prime-five-with-seven",
        "PRIMES = (2, 3, 5)",
        "PRIMES = (2, 3, 7)",
    ),
    Mutation(
        "off-by-one-final-stars-and-bars-gap",
        "counts.append(total + CELL_COUNT - 2 - previous)",
        "counts.append(total + CELL_COUNT - 1 - previous)",
    ),
    Mutation(
        "off-by-one-counts-to-separators",
        "separators.append(stars_seen + index)",
        "separators.append(stars_seen + index + 1)",
    ),
    Mutation(
        "compare-exact-product-with-one-backwards",
        "result = (numerator > denominator) - (numerator < denominator)",
        "result = (denominator > numerator) - (denominator < numerator)",
    ),
    Mutation(
        "leave-source-masks-unpermuted",
        "transformed |= 1 << new_index",
        "transformed |= 1 << old_index",
    ),
    Mutation(
        "omit-target-binary-relabel",
        "target ^= (flip_mask >> 3) & 1",
        "target ^= 0",
    ),
    Mutation(
        "wrong-replication-exponent",
        "tuple(scale(value, 2) for value in base)",
        "tuple(scale(value, 1) for value in base)",
    ),
    Mutation(
        "omit-canonical-counts-from-table-frame",
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(bytes(counts))',
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(b"")',
    ),
    Mutation(
        "reverse-canonical-counts-in-table-frame",
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(bytes(counts))',
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(bytes(reversed(counts)))',
    ),
    Mutation(
        "interleave-canonical-counts-in-wrong-order",
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(bytes(counts))',
        'digest.update(struct.pack(">I", ordinal))\n    digest.update(bytes(tuple(counts[::2]) + tuple(counts[1::2])))',
    ),
    Mutation(
        "omit-entire-table-frame-from-framing-probe",
        "        begin_table_bound_frame(digest, ordinal, counts)\n        flattened = compute_table_products(counts).flattened()",
        "        flattened = compute_table_products(counts).flattened()",
    ),
    Mutation(
        "reverse-table-frame-order-in-framing-probe",
        "    for counts in fixtures:\n        ordinal = rank_count_vector(counts)",
        "    for counts in reversed(fixtures):\n        ordinal = rank_count_vector(counts)",
    ),
)

FRAMING_MUTATIONS = {
    "omit-canonical-counts-from-table-frame",
    "reverse-canonical-counts-in-table-frame",
    "interleave-canonical-counts-in-wrong-order",
    "omit-entire-table-frame-from-framing-probe",
    "reverse-table-frame-order-in-framing-probe",
}

INTERPRETER_FLAG_CONTROLS = (
    ("missing-E", ("-P", "-S", "-B"), "PYTHON.ignore_environment"),
    ("missing-P", ("-E", "-S", "-B"), "PYTHON.safe_path"),
    ("missing-I", ("-E", "-P", "-S", "-B"), "PYTHON.isolated"),
    ("missing-S", ("-I", "-B"), "PYTHON.no_site"),
    ("missing-B", ("-I", "-S"), "PYTHON.dont_write_bytecode"),
    ("unsupported-OO", ("-I", "-S", "-B", "-OO"), "PYTHON.optimize"),
)


def run(command: list[str], timeout: int = 20) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def python_command(script: Path, *arguments: str, optimize: int) -> list[str]:
    require(optimize in (0, 1), "nested Python optimization mode outside {0,1}")
    flags = ["-I", "-S", "-B"]
    if optimize == 1:
        flags.append("-O")
    return [sys.executable, *flags, str(script), *arguments]


def verify_nested_interpreter_flag_controls(checker: Path) -> tuple[str, ...]:
    killed: list[str] = []
    for label, flags, expected_code in INTERPRETER_FLAG_CONTROLS:
        result = run([sys.executable, *flags, str(checker), "--probe"])
        require(result.returncode != 0, f"{label}: checker unexpectedly succeeded")
        require(result.stdout == b"", f"{label}: checker emitted stdout")
        expected_stderr = f"FAIL: {expected_code}\n".encode("ascii")
        require(
            result.stderr == expected_stderr,
            f"{label}: expected {expected_stderr!r}, found {result.stderr!r}",
        )
        killed.append(label)
    return tuple(killed)


def mutate_once(source: str, mutation: Mutation) -> str:
    occurrences = source.count(mutation.old)
    require(occurrences == 1, f"mutation {mutation.name} expected one anchor, found {occurrences}")
    changed = source.replace(mutation.old, mutation.new, 1)
    require(changed != source, f"mutation {mutation.name} did not change source")
    return changed


def main() -> int:
    checker = Path(__file__).with_name("check-sxpid3-all108-independent.py")
    require(checker.is_file(), f"checker not found: {checker}")
    source_bytes = checker.read_bytes()
    source = source_bytes.decode("utf-8")
    require(
        hashlib.sha256(source_bytes).hexdigest() == EXPECTED_CHECKER_SOURCE_SHA256,
        "checker source digest drift",
    )
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(source))),
        "checker contains an optimization-removable assert",
    )

    interpreter_flag_controls = verify_nested_interpreter_flag_controls(checker)

    full_normal = run(python_command(checker, optimize=0), timeout=90)
    full_optimized = run(python_command(checker, optimize=1), timeout=90)
    require(full_normal.returncode == 0, "normal full run failed")
    require(full_optimized.returncode == 0, "optimized full run failed")
    require(full_normal.stdout == full_optimized.stdout, "normal/-O full-run output differs")
    require(full_normal.stderr == b"" and full_optimized.stderr == b"", "full run emitted stderr")
    require(
        hashlib.sha256(full_normal.stdout).hexdigest() == EXPECTED_FULL_STDOUT_SHA256,
        "full-run stdout digest drift",
    )
    full_payload = json.loads(full_normal.stdout)
    require(full_payload["status"] == "GO", "full result status drift")
    require(
        full_payload["census_interpretation"] == EXPECTED_CENSUS_INTERPRETATION,
        "bounded-census interpretation metadata drift",
    )
    require(
        full_payload["sign_semantics"] == EXPECTED_SIGN_SEMANTICS,
        "log-sign/comparison semantics for exact positive products drift",
    )
    require(
        full_payload["method_provenance_and_novelty"] == EXPECTED_METHOD_PROVENANCE_AND_NOVELTY,
        "method provenance or novelty boundary drift",
    )
    require(
        full_payload["route_assurance"] == EXPECTED_ROUTE_ASSURANCE,
        "implementation-disjoint/shared-semantics assurance boundary drift",
    )
    require(
        full_payload["construction"]["audit_expression_registry"]
        == "sxpid3-mask-lex-antichain-order-averaged-108-v1",
        "audit-expression revision drift",
    )
    require(
        full_payload["digests"]["table_bound_all_expression_result_sha256"]
        == EXPECTED_TABLE_BOUND_RESULT_SHA256,
        "table-bound route/representation-neutral-v2 expected-digest match drift",
    )
    require(
        full_payload["digests"]["route_native_v1_result_sha256"]
        == "4996153f04315852492bbff45548ad241f8aeaacad11e25ab510bc86267c201a",
        "separate route-native continuity digest drift",
    )
    require(
        full_payload["digests"]["table_bound_framing_probe_sha256"]
        == EXPECTED_FRAMING_PROBE_SHA256,
        "table-bound framing probe drift",
    )
    require(
        full_payload["scope"]["audit_expression_factorization"]
        == {
            "antichain_keys": 18,
            "components": ["informative", "misinformative", "net"],
            "representation_stage_count": 2,
            "representation_stages": [
                {"name": "cumulative values", "audit_expressions_per_component": 18},
                {"name": "Möbius atoms", "audit_expressions_per_component": 18},
            ],
            "not_claimed": ["108 lattice nodes", "108 atoms", "108 independent degrees of freedom"],
        },
        "108-expression factorization or nonclaim drift",
    )
    require(
        full_payload["bounded_sign_counts_by_audit_expression_block"]
        == EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK,
        "bounded sign counts or six-block roster drift",
    )
    require("first_negative_witnesses" not in full_payload, "ambiguous negative-product witness key survived")
    negative_log_witnesses = full_payload["first_negative_log_value_witnesses"]
    require(set(negative_log_witnesses) == {"cumulative", "atom"}, "negative log-value witness roster drift")
    require(
        all(
            witness["exact_product_Q_is_strictly_positive"] is True
            and witness["witnessed_comparison"] == "Q<1"
            for witness in negative_log_witnesses.values()
        ),
        "negative log-value witness could be read as a negative exact product",
    )
    require(
        full_payload["construction"]["table_bound_stream"]["cell_order"]
        == "cell_index=8*s1+4*s2+2*s3+t",
        "canonical binary cell order drift",
    )
    require(
        full_payload["construction"]["table_bound_stream"]["neutrality_scope"]
        == "route_and_representation_neutral_within_v2",
        "v2 route/representation neutrality scope drift",
    )
    require(
        "exact positive Q" in full_payload["construction"]["table_bound_stream"]["expression_record"]
        and "log_sign/comparison-to-one"
        in full_payload["construction"]["table_bound_stream"]["expression_record"],
        "stream description ambiguously labels a positive product as signed",
    )
    require(
        all(
            "frozen pid-rs key order" not in statement
            and "public serialization" not in statement
            for statement in full_payload["shared_semantic_cuts"]
        ),
        "false shipped-order wording survived",
    )

    baseline_normal = run(python_command(checker, "--probe", optimize=0))
    baseline_optimized = run(python_command(checker, "--probe", optimize=1))
    require(baseline_normal.returncode == 0, "normal baseline probe failed")
    require(baseline_optimized.returncode == 0, "optimized baseline probe failed")
    require(baseline_normal.stdout == baseline_optimized.stdout, "normal/-O baseline probe output differs")
    require(baseline_normal.stderr == b"" and baseline_optimized.stderr == b"", "baseline emitted stderr")
    require(
        hashlib.sha256(baseline_normal.stdout).hexdigest() == EXPECTED_PROBE_STDOUT_SHA256,
        "probe stdout digest drift",
    )

    killed: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-sxpid3-independent-mutations-") as temporary:
        temporary_root = Path(temporary)
        for index, mutation in enumerate(MUTATIONS):
            mutant = temporary_root / f"mutant-{index:02d}.py"
            mutant.write_text(mutate_once(source, mutation), encoding="utf-8")
            normal = run(python_command(mutant, "--probe", optimize=0))
            optimized = run(python_command(mutant, "--probe", optimize=1))
            require(normal.returncode != 0, f"mutation survived normal mode: {mutation.name}")
            require(optimized.returncode != 0, f"mutation survived optimized mode: {mutation.name}")
            if mutation.name in FRAMING_MUTATIONS:
                marker = b"table-bound framing probe digest drift"
                require(marker in normal.stderr, f"framing mutation missed table-bound route: {mutation.name}")
                require(marker in optimized.stderr, f"optimized framing mutation missed table-bound route: {mutation.name}")
            killed.append(mutation.name)

    result = {
        "schema": "pid-rs.sxpid3-all108-independent-mutations.v2",
        "status": "GO",
        "gate_scope": SELF_TEST_GATE_SCOPE,
        "checker_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "self_test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "full_run_normal_optimized_byte_identical": True,
        "full_run_stdout_bytes": len(full_normal.stdout),
        "full_run_stdout_sha256": hashlib.sha256(full_normal.stdout).hexdigest(),
        "baseline_probe_stdout_sha256": hashlib.sha256(baseline_normal.stdout).hexdigest(),
        "mutation_count": len(MUTATIONS),
        "table_bound_framing_mutation_count": len(FRAMING_MUTATIONS),
        "nested_interpreter_flag_control_count": len(interpreter_flag_controls),
        "nested_interpreter_flag_controls": list(interpreter_flag_controls),
        "normal_killed": len(killed),
        "optimized_killed": len(killed),
        "mutations": killed,
        "execution_contract": {
            "python_implementation": "CPython",
            "minimum_python_version": "3.11",
            "required_flags": ["-I", "-S", "-B"],
            "admitted_optimization_modes": [0, 1],
        },
        "boundary": (
            "These process-level controls show that the selected faults fail closed on the bounded probe. "
            "The full-run byte identity and declared interpreter contract are bounded custody observations, not "
            "mathematical independence. They do not prove mutation completeness, source authenticity, or "
            "mathematical correctness."
        ),
    }
    print(json.dumps(result, sort_keys=True, indent=2, separators=(",", ": ")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SelfTestError, subprocess.TimeoutExpired, UnicodeError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
