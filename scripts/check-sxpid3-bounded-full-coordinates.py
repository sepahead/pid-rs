#!/usr/bin/env python3
"""Exact bounded audit of 108 keyed scalar categorical SxPID3 expressions.

This standalone standard-library checker reconstructs the fixed binary three-source carrier,
event truth table, redundancy order, zeta matrix, and exact Mobius inverse.  It then enumerates
all 20,348 labeled 16-cell count vectors with total one through five and computes the exact
positive-rational product underlying 18 lattice keys times two representation stages (cumulative
values and Mobius atoms) times three components (informative, misinformative, and signed net).
These are 108 keyed scalar audit expressions, not 108 lattice nodes, 108 atoms, or 108 independent
degrees of freedom.

It retains the original route-native fraction stream and additionally encodes the products in a
route-neutral representation within the explicit v2 table-bound prime-exponent protocol.  This
standalone checker compares its computed digest only with an embedded, externally supplied
expected digest: it neither loads nor executes or source-binds an independent route.  A later
closed receipt is required before claiming paired-route execution or agreement.

The result is bounded executable evidence for this one binary corpus.  It is not a logarithm
enclosure, paper-correspondence proof, arbitrary-alphabet theorem, parser/certificate proof,
current Rust refinement, population result, or closure of SxPID3 Programs A--E.  Pointwise
expressions are deliberately not evaluated by this averaged-expression checker.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import struct
import sys
from typing import Final, Iterator, NamedTuple, Protocol, Sequence


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
        "ERROR: check-sxpid3-bounded-full-coordinates.py requires "
        "CPython 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


FORMAT: Final[str] = "/pid-rs/sxpid3-bounded-full-coordinates/v2"
DEFINITION_REVISION: Final[str] = (
    "makkeh-gutknecht-wibral-2021-empirical-sxpid3-nats-v1"
)
EVENT_REVISION: Final[str] = "mgw-sxpid3-dnf-target-intersection-v1"
AUDIT_EXPRESSION_REVISION: Final[str] = (
    "sxpid3-audit-lexicographic-antichain-order-averaged-keyed-expressions-108-v3"
)
SOURCE_BITS: Final[tuple[int, ...]] = (1, 2, 4)
MASKS: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7)
SOURCE_STATES: Final[tuple[tuple[int, int, int], ...]] = (
    (0, 0, 0),
    (0, 0, 1),
    (0, 1, 0),
    (0, 1, 1),
    (1, 0, 0),
    (1, 0, 1),
    (1, 1, 0),
    (1, 1, 1),
)
TARGET_VALUES: Final[tuple[int, ...]] = (0, 1)
JOINT_STATES: Final[tuple[tuple[tuple[int, int, int], int], ...]] = (
    ((0, 0, 0), 0),
    ((0, 0, 0), 1),
    ((0, 0, 1), 0),
    ((0, 0, 1), 1),
    ((0, 1, 0), 0),
    ((0, 1, 0), 1),
    ((0, 1, 1), 0),
    ((0, 1, 1), 1),
    ((1, 0, 0), 0),
    ((1, 0, 0), 1),
    ((1, 0, 1), 0),
    ((1, 0, 1), 1),
    ((1, 1, 0), 0),
    ((1, 1, 0), 1),
    ((1, 1, 1), 0),
    ((1, 1, 1), 1),
)
SOURCE_INDEX: Final[dict[tuple[int, int, int], int]] = {
    state: index for index, state in enumerate(SOURCE_STATES)
}
JOINT_INDEX: Final[dict[tuple[tuple[int, int, int], int], int]] = {
    state: index for index, state in enumerate(JOINT_STATES)
}
MAX_TOTAL: Final[int] = 5
EXPECTED_TABLES_BY_TOTAL: Final[tuple[int, ...]] = (16, 136, 816, 3_876, 15_504)
EXPECTED_PRIMITIVE_BY_TOTAL: Final[tuple[int, ...]] = (16, 120, 800, 3_740, 15_488)

EXPECTED_ANTICHAINS: Final[tuple[tuple[int, ...], ...]] = (
    (1,),
    (2,),
    (3,),
    (4,),
    (5,),
    (6,),
    (7,),
    (1, 2),
    (1, 4),
    (1, 6),
    (2, 4),
    (2, 5),
    (3, 4),
    (3, 5),
    (3, 6),
    (5, 6),
    (1, 2, 4),
    (3, 5, 6),
)
# This checker intentionally uses a lexicographic audit order.  It is not the positional order of
# Rust `discrete_antichains_3`; the key-based bridge below is the only permitted translation.
EXPECTED_AUDIT_STABLE_KEYS: Final[tuple[str, ...]] = (
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "01+02",
    "01+04",
    "01+06",
    "02+04",
    "02+05",
    "03+04",
    "03+05",
    "03+06",
    "05+06",
    "01+02+04",
    "03+05+06",
)
EXPECTED_RUST_STABLE_KEYS: Final[tuple[str, ...]] = (
    "01",
    "02",
    "04",
    "03",
    "05",
    "06",
    "07",
    "01+02",
    "01+04",
    "01+06",
    "02+04",
    "02+05",
    "03+04",
    "03+05",
    "03+06",
    "05+06",
    "01+02+04",
    "03+05+06",
)
EXPECTED_AUDIT_TO_RUST_NODE_INDEX: Final[tuple[int, ...]] = (
    0, 1, 3, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
)
RUST_ANTICHAIN_SOURCE: Final[Path] = (
    Path(__file__).resolve().parents[1] / "crates/pid-core/src/discrete_pid.rs"
)
EXPECTED_RUST_ANTICHAIN_FUNCTION_SHA256: Final[str] = (
    "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb07"
)
EXPECTED_ZETA_SIGNATURES: Final[tuple[str, ...]] = (
    "100000011100000010",
    "010000010011000010",
    "111000011111111011",
    "000100001010100010",
    "100110011111110111",
    "010101011111101111",
    "111111111111111111",
    "000000010000000010",
    "000000001000000010",
    "000000011100000010",
    "000000000010000010",
    "000000010011000010",
    "000000001010100010",
    "100000011111110011",
    "010000011111101011",
    "000100011111100111",
    "000000000000000010",
    "000000011111100011",
)
EXPECTED_MOBIUS_SPARSE: Final[tuple[tuple[tuple[int, int], ...], ...]] = (
    ((0, 1), (9, -1)),
    ((1, 1), (11, -1)),
    ((2, 1), (13, -1), (14, -1), (17, 1)),
    ((3, 1), (12, -1)),
    ((4, 1), (13, -1), (15, -1), (17, 1)),
    ((5, 1), (14, -1), (15, -1), (17, 1)),
    ((2, -1), (4, -1), (5, -1), (6, 1), (13, 1), (14, 1), (15, 1), (17, -1)),
    ((7, 1), (16, -1)),
    ((8, 1), (16, -1)),
    ((7, -1), (8, -1), (9, 1), (16, 1)),
    ((10, 1), (16, -1)),
    ((7, -1), (10, -1), (11, 1), (16, 1)),
    ((8, -1), (10, -1), (12, 1), (16, 1)),
    ((0, -1), (9, 1), (13, 1), (17, -1)),
    ((1, -1), (11, 1), (14, 1), (17, -1)),
    ((3, -1), (12, 1), (15, 1), (17, -1)),
    ((16, 1),),
    ((7, 1), (8, 1), (9, -1), (10, 1), (11, -1), (12, -1), (16, -1), (17, 1)),
)

AUDIT_EXPRESSION_BLOCKS: Final[tuple[tuple[str, str], ...]] = (
    ("cumulative", "informative"),
    ("cumulative", "misinformative"),
    ("cumulative", "net"),
    ("atom", "informative"),
    ("atom", "misinformative"),
    ("atom", "net"),
)

# Same-route regression/drift anchors settled from the first complete reviewed replay.  The
# checker derives each object again and rejects drift.  These digests are not logically independent
# evidence and do not establish that the frozen formulas correspond to the paper or to Rust.
EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256: Final[str] = (
    "6ada33aa90382316ae0757ed7f449e9fa9a35db3a7d4aec8aa3660a4c6e3c3d5"
)
EXPECTED_EVENT_TRUTH_SHA256: Final[str] = (
    "7bcf2a3b5d03566f8b402f387e95942969606af32d76cd02f8ee2b0e85546087"
)
EXPECTED_SEMANTIC_REGISTRY_SHA256: Final[str] = (
    "7cf8b96fe5ce3039f6fd98fbf59adb7c442018e630680b6e7998bb6cdf5c2ba6"
)
EXPECTED_CORPUS_STREAM_SHA256: Final[str] = (
    "5eb678eba27eea449ea5c0875c2a930ec5fcd0764718aaddfae8283fbdfc6309"
)
EXPECTED_ROUTE_NATIVE_RESULT_STREAM_SHA256: Final[str] = (
    "315592501f49021ed86218ba1c277b9e9b764ace9621c8b4df61bb5868f3ead0"
)
TABLE_BOUND_AUDIT_DOMAIN: Final[bytes] = (
    b"pid-rs.sxpid3.table-bound-audit-expressions.v2\0"
)
# A separately implemented route is intended to reproduce this route-neutral representation within
# the explicit v2 table-bound protocol.  This checker binds only the embedded expected digest, not
# independent source or execution.  Any later paired-route agreement claim needs a closed receipt.
EXPECTED_NEUTRAL_CROSS_ROUTE_RESULT_STREAM_SHA256: Final[str] = (
    "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8"
)
EXPECTED_NEUTRAL_FRAMING_UNIT_SHA256: Final[str] = (
    "035c467bcf756e4009db452ec43f48747ce0f70ebdb43780d9925bf5124c24d2"
)
EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK: Final[
    dict[str, dict[str, int]]
] = {
    "atom.informative": {"negative": 0, "positive": 145_100, "zero": 221_164},
    "atom.misinformative": {"negative": 0, "positive": 71_468, "zero": 294_796},
    "atom.net": {"negative": 31_284, "positive": 96_768, "zero": 238_212},
    "cumulative.informative": {"negative": 0, "positive": 321_856, "zero": 44_408},
    "cumulative.misinformative": {"negative": 0, "positive": 278_984, "zero": 87_280},
    "cumulative.net": {"negative": 29_496, "positive": 252_816, "zero": 83_952},
}

CENSUS_INTERPRETATION: Final[dict[str, object]] = {
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

SIGN_SEMANTICS: Final[dict[str, object]] = {
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

METHOD_PROVENANCE_AND_NOVELTY: Final[dict[str, object]] = {
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

CROSS_ROUTE_ASSURANCE: Final[dict[str, object]] = {
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

P1_SEPARATE_LANE_STATUS: Final[dict[str, object]] = {
    "result": "source_marginal_informative_invariance",
    "relationship": "outside_this_artifact_and_separate_lane",
    "replayed_by_this_checker": False,
    "result_imported_by_this_checker": False,
    "semantic_transfer_to_this_bounded_audit": "none",
    "status_inferred_by_this_checker": False,
}

LEGACY_SCHEMA_TERMINOLOGY: Final[dict[str, object]] = {
    "retained_token": "full-coordinates",
    "retained_locations": ["historical_filename", "v2_format_identifier"],
    "compatibility_reason": "preserve_v2_artifact_routing_and_consumers",
    "meaning_in_this_artifact": "108_keyed_scalar_audit_expressions",
    "does_not_mean_independent_coordinates_or_degrees_of_freedom": True,
    "rename_required_at_next_schema_boundary": True,
}


class FullProducts(NamedTuple):
    cumulative_informative: tuple[Fraction, ...]
    cumulative_misinformative: tuple[Fraction, ...]
    cumulative_net: tuple[Fraction, ...]
    atom_informative: tuple[Fraction, ...]
    atom_misinformative: tuple[Fraction, ...]
    atom_net: tuple[Fraction, ...]

    def audit_expressions(self) -> tuple[Fraction, ...]:
        return (
            self.cumulative_informative
            + self.cumulative_misinformative
            + self.cumulative_net
            + self.atom_informative
            + self.atom_misinformative
            + self.atom_net
        )


class DigestSink(Protocol):
    """Minimal byte-sink interface shared by hashlib and the framing recorder."""

    def update(self, value: bytes, /) -> object:
        ...


class FramingRecorder:
    """Record update boundaries for the structural neutral-framing unit check."""

    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    def update(self, value: bytes, /) -> None:
        self.chunks.append(bytes(value))


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def fraction_token(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def stable_key(antichain: tuple[int, ...]) -> str:
    return "+".join(f"{mask:02x}" for mask in antichain)


def rust_antichain_stable_keys() -> tuple[str, ...]:
    """Read and pin only Rust's current 18-node order; this is not numerical refinement."""
    source = RUST_ANTICHAIN_SOURCE.read_text(encoding="utf-8", errors="strict")
    match = re.search(
        r"(pub\(crate\) fn discrete_antichains_3\(\) -> \[\[u8; 3\]; 18\] \{\n"
        r".*?\n\})\n\n/// Compute specific information",
        source,
        flags=re.DOTALL,
    )
    require(match is not None, "RUST_ORDER.function_shape")
    function_source = match.group(1)
    require(
        hashlib.sha256(function_source.encode("utf-8")).hexdigest()
        == EXPECTED_RUST_ANTICHAIN_FUNCTION_SHA256,
        "RUST_ORDER.function_sha256",
    )
    rows = re.findall(
        r"^\s*\[(0b[01]+|0), (0b[01]+|0), (0b[01]+|0)\],$",
        function_source,
        flags=re.MULTILINE,
    )
    require(len(rows) == 18, "RUST_ORDER.row_count")
    keys = tuple(
        stable_key(tuple(int(token, 2) for token in row if token != "0"))
        for row in rows
    )
    require(keys == EXPECTED_RUST_STABLE_KEYS, "RUST_ORDER.stable_keys")
    return keys


def audit_to_rust_key_bridge(
    audit_keys: Sequence[str], rust_keys: Sequence[str]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Construct both index maps by key equality, never by positional coincidence."""
    require(len(audit_keys) == len(set(audit_keys)) == 18, "ORDER_BRIDGE.audit_bijection")
    require(len(rust_keys) == len(set(rust_keys)) == 18, "ORDER_BRIDGE.rust_bijection")
    require(set(audit_keys) == set(rust_keys), "ORDER_BRIDGE.key_carrier")
    rust_index = {key: index for index, key in enumerate(rust_keys)}
    audit_index = {key: index for index, key in enumerate(audit_keys)}
    audit_to_rust = tuple(rust_index[key] for key in audit_keys)
    rust_to_audit = tuple(audit_index[key] for key in rust_keys)
    require(
        audit_to_rust == EXPECTED_AUDIT_TO_RUST_NODE_INDEX,
        "ORDER_BRIDGE.audit_to_rust",
    )
    require(
        all(
            rust_to_audit[audit_to_rust[index]] == index
            for index in range(len(audit_keys))
        ),
        "ORDER_BRIDGE.two_sided_inverse",
    )
    require(
        all(rust_keys[audit_to_rust[index]] == key for index, key in enumerate(audit_keys)),
        "ORDER_BRIDGE.key_preservation",
    )
    return audit_to_rust, rust_to_audit


def audit_expression_registry(keys: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        f"{scope}.{component}.{key}"
        for scope, component in AUDIT_EXPRESSION_BLOCKS
        for key in keys
    )


def mask_subset(left: int, right: int) -> bool:
    return left & right == left


def is_antichain(candidate: tuple[int, ...]) -> bool:
    return all(
        not mask_subset(left, right) and not mask_subset(right, left)
        for index, left in enumerate(candidate)
        for right in candidate[index + 1 :]
    )


def enumerate_antichains() -> tuple[tuple[int, ...], ...]:
    values = tuple(
        candidate
        for size in range(1, len(MASKS) + 1)
        for candidate in itertools.combinations(MASKS, size)
        if is_antichain(candidate)
    )
    return tuple(sorted(values, key=lambda antichain: (len(antichain), antichain)))


def redundancy_le(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    """Every branch of ``right`` contains at least one branch of ``left``."""
    return all(any(mask_subset(a, b) for a in left) for b in right)


def zeta_matrix(nodes: Sequence[tuple[int, ...]]) -> list[list[int]]:
    # Rows are cumulatives and columns are atoms.
    return [
        [int(redundancy_le(atom, cumulative)) for atom in nodes]
        for cumulative in nodes
    ]


def inverse_matrix_exact(matrix: Sequence[Sequence[int]]) -> list[list[Fraction]]:
    size = len(matrix)
    augmented = [
        [Fraction(value) for value in row]
        + [Fraction(int(row_index == column)) for column in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = next(
            (row for row in range(column, size) if augmented[row][column]),
            None,
        )
        require(pivot is not None, "MOBIUS.singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    left - factor * right
                    for left, right in zip(augmented[row], augmented[column], strict=True)
                ]
    return [row[size:] for row in augmented]


def matrix_product(
    left: Sequence[Sequence[Fraction | int]],
    right: Sequence[Sequence[Fraction | int]],
) -> list[list[Fraction]]:
    return [
        [
            sum(
                (Fraction(left[i][k]) * Fraction(right[k][j]) for k in range(len(right))),
                start=Fraction(0),
            )
            for j in range(len(right[0]))
        ]
        for i in range(len(left))
    ]


def identity(size: int) -> list[list[Fraction]]:
    return [[Fraction(int(row == column)) for column in range(size)] for row in range(size)]


def sparse_integer_rows(
    matrix: Sequence[Sequence[Fraction]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    rows: list[tuple[tuple[int, int], ...]] = []
    for row in matrix:
        require(all(value.denominator == 1 for value in row), "MOBIUS.integer_coefficient")
        rows.append(
            tuple(
                (column, value.numerator)
                for column, value in enumerate(row)
                if value
            )
        )
    return tuple(rows)


def event_matches(
    antichain: tuple[int, ...],
    anchor: tuple[int, int, int],
    candidate: tuple[int, int, int],
) -> bool:
    """OR across branches, AND across the selected coordinates inside one branch."""
    return any(
        all(
            anchor[index] == candidate[index]
            for index, bit in enumerate(SOURCE_BITS)
            if mask & bit
        )
        for mask in antichain
    )


def event_matches_difference_mask(
    antichain: tuple[int, ...],
    anchor: tuple[int, int, int],
    candidate: tuple[int, int, int],
) -> bool:
    """Second encoding: a branch matches iff no selected bit differs."""
    difference = sum(
        bit
        for bit, anchor_value, candidate_value in zip(
            SOURCE_BITS, anchor, candidate, strict=True
        )
        if anchor_value != candidate_value
    )
    return any(mask & difference == 0 for mask in antichain)


def verify_event_registry(nodes: Sequence[tuple[int, ...]]) -> str:
    require(SOURCE_BITS == (1, 2, 4), "MASK.source_bit_registry")
    require(SOURCE_STATES == tuple(itertools.product((0, 1), repeat=3)), "MASK.source_state_order")
    require(
        JOINT_STATES
        == tuple((source, target) for source in SOURCE_STATES for target in TARGET_VALUES),
        "MASK.joint_state_order",
    )
    require(
        all(
            index == 8 * source[0] + 4 * source[1] + 2 * source[2] + target
            for index, (source, target) in enumerate(JOINT_STATES)
        ),
        "MASK.cell_formula",
    )
    truth: list[list[int]] = []
    for node in nodes:
        row: list[int] = []
        for anchor in SOURCE_STATES:
            for candidate in SOURCE_STATES:
                direct = event_matches(node, anchor, candidate)
                second = event_matches_difference_mask(node, anchor, candidate)
                require(direct == second, "EVENT.dual_encoding")
                row.append(int(direct))
        truth.append(row)
    digest = canonical_sha256(truth)
    require(digest == EXPECTED_EVENT_TRUTH_SHA256, "EVENT.truth_registry_sha256")
    return digest


def permute_state(
    state: tuple[int, int, int], permutation: tuple[int, int, int]
) -> tuple[int, int, int]:
    return tuple(state[old_index] for old_index in permutation)  # type: ignore[return-value]


def permute_mask(mask: int, permutation: tuple[int, int, int]) -> int:
    return sum(
        1 << new_index
        for new_index, old_index in enumerate(permutation)
        if mask & (1 << old_index)
    )


def verify_source_permutations(nodes: Sequence[tuple[int, ...]]) -> int:
    node_set = set(nodes)
    permutations = tuple(itertools.permutations(range(3)))
    for permutation in permutations:
        node_map = {
            node: tuple(sorted(permute_mask(mask, permutation) for mask in node))
            for node in nodes
        }
        require(set(node_map.values()) == node_set, "PERMUTATION.carrier_bijection")
        for left in nodes:
            for right in nodes:
                require(
                    redundancy_le(left, right)
                    == redundancy_le(node_map[left], node_map[right]),
                    "PERMUTATION.order_automorphism",
                )
        for node in nodes:
            for anchor in SOURCE_STATES:
                for candidate in SOURCE_STATES:
                    require(
                        event_matches(node, anchor, candidate)
                        == event_matches(
                            node_map[node],
                            permute_state(anchor, permutation),
                            permute_state(candidate, permutation),
                        ),
                        "PERMUTATION.event_equivariance",
                    )
    return len(permutations)


def compositions(total: int, width: int) -> Iterator[tuple[int, ...]]:
    """All labeled weak compositions in a deterministic lexicographic recursion."""
    if width == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for tail in compositions(total - first, width - 1):
            yield (first,) + tail


def source_marginal(joint_counts: Sequence[int]) -> tuple[int, ...]:
    return tuple(
        sum(joint_counts[JOINT_INDEX[(source, target)]] for target in TARGET_VALUES)
        for source in SOURCE_STATES
    )


def target_marginal(joint_counts: Sequence[int]) -> tuple[int, ...]:
    return tuple(
        sum(
            joint_counts[JOINT_INDEX[(source, target)]]
            for source in SOURCE_STATES
        )
        for target in TARGET_VALUES
    )


def event_member_indices(
    nodes: Sequence[tuple[int, ...]],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                candidate_index
                for candidate_index, candidate in enumerate(SOURCE_STATES)
                if event_matches(node, anchor, candidate)
            )
            for anchor in SOURCE_STATES
        )
        for node in nodes
    )


def divide_products(
    numerator: Sequence[Fraction], denominator: Sequence[Fraction]
) -> tuple[Fraction, ...]:
    return tuple(
        left / right for left, right in zip(numerator, denominator, strict=True)
    )


def mobius_products(
    cumulatives: Sequence[Fraction], mobius: Sequence[Sequence[Fraction]]
) -> tuple[Fraction, ...]:
    products: list[Fraction] = []
    for row in mobius:
        product = Fraction(1)
        for cumulative, coefficient in zip(cumulatives, row, strict=True):
            require(coefficient.denominator == 1, "MOBIUS.integer_coefficient")
            product *= cumulative ** coefficient.numerator
        products.append(product)
    return tuple(products)


def full_products(
    joint_counts: Sequence[int],
    members: Sequence[Sequence[Sequence[int]]],
    mobius: Sequence[Sequence[Fraction]],
) -> FullProducts:
    total = sum(joint_counts)
    require(total > 0, "PRODUCT.positive_total")
    source_counts = source_marginal(joint_counts)
    target_counts = target_marginal(joint_counts)
    cumulative_plus: list[Fraction] = []
    cumulative_minus: list[Fraction] = []
    for node_index in range(len(members)):
        plus = Fraction(1)
        minus = Fraction(1)
        for joint_index, cell_count in enumerate(joint_counts):
            if cell_count == 0:
                continue
            anchor_source, anchor_target = JOINT_STATES[joint_index]
            anchor_index = SOURCE_INDEX[anchor_source]
            source_event_count = sum(
                source_counts[candidate_index]
                for candidate_index in members[node_index][anchor_index]
            )
            restricted_event_count = sum(
                joint_counts[
                    JOINT_INDEX[(SOURCE_STATES[candidate_index], anchor_target)]
                ]
                for candidate_index in members[node_index][anchor_index]
            )
            target_count = target_counts[anchor_target]
            require(
                0 < cell_count <= restricted_event_count <= source_event_count <= total,
                "PRODUCT.source_event_bounds",
            )
            require(
                restricted_event_count <= target_count <= total,
                "PRODUCT.target_event_bounds",
            )
            plus *= Fraction(total, source_event_count) ** cell_count
            minus *= Fraction(target_count, restricted_event_count) ** cell_count
        cumulative_plus.append(plus)
        cumulative_minus.append(minus)

    plus_tuple = tuple(cumulative_plus)
    minus_tuple = tuple(cumulative_minus)
    net_tuple = divide_products(plus_tuple, minus_tuple)
    atom_plus = mobius_products(plus_tuple, mobius)
    atom_minus = mobius_products(minus_tuple, mobius)
    atom_net = divide_products(atom_plus, atom_minus)
    return FullProducts(
        plus_tuple,
        minus_tuple,
        net_tuple,
        atom_plus,
        atom_minus,
        atom_net,
    )


def permute_joint_counts(
    counts: Sequence[int], permutation: tuple[int, int, int]
) -> tuple[int, ...]:
    output = [0] * len(JOINT_STATES)
    for index, count in enumerate(counts):
        source, target = JOINT_STATES[index]
        output[JOINT_INDEX[(permute_state(source, permutation), target)]] = count
    return tuple(output)


def verify_targeted_source_permutation_products(
    nodes: Sequence[tuple[int, ...]],
    members: Sequence[Sequence[Sequence[int]]],
    mobius: Sequence[Sequence[Fraction]],
) -> int:
    """Exercise all 108 product paths on three asymmetric tables under all six source maps.

    The carrier/order/event automorphism check is finite and exhaustive.  This separate paired-
    table regression is deliberately only targeted; it is not a full-corpus permutation replay.
    """
    node_index = {node: index for index, node in enumerate(nodes)}
    tables = (
        witness_counts({0: 2, 4: 1}),
        witness_counts({11: 1, 13: 1, 14: 1}),
        witness_counts({0: 1, 5: 1, 11: 1, 14: 2}),
    )
    checks = 0
    for counts in tables:
        original = full_products(counts, members, mobius)
        original_blocks = tuple(original)
        for permutation in itertools.permutations(range(3)):
            mapped_nodes = {
                node: tuple(sorted(permute_mask(mask, permutation) for mask in node))
                for node in nodes
            }
            permuted = full_products(
                permute_joint_counts(counts, permutation), members, mobius
            )
            for original_block, permuted_block in zip(
                original_blocks, tuple(permuted), strict=True
            ):
                for node in nodes:
                    require(
                        original_block[node_index[node]]
                        == permuted_block[node_index[mapped_nodes[node]]],
                        "PERMUTATION.targeted_product_equivariance",
                    )
                    checks += 1
    require(checks == 1_944, "PERMUTATION.targeted_product_check_count")
    return checks


def subset_mutual_information_product(
    joint_counts: Sequence[int], mask: int
) -> Fraction:
    total = sum(joint_counts)
    target_counts = target_marginal(joint_counts)
    source_counts: dict[tuple[int, ...], int] = {}
    source_target_counts: dict[tuple[tuple[int, ...], int], int] = {}
    projected_by_cell: list[tuple[int, ...]] = []
    for source, _ in JOINT_STATES:
        projected_by_cell.append(
            tuple(
                source[index]
                for index, bit in enumerate(SOURCE_BITS)
                if mask & bit
            )
        )
    for joint_index, cell_count in enumerate(joint_counts):
        if cell_count == 0:
            continue
        target = JOINT_STATES[joint_index][1]
        projected = projected_by_cell[joint_index]
        source_counts[projected] = source_counts.get(projected, 0) + cell_count
        key = (projected, target)
        source_target_counts[key] = source_target_counts.get(key, 0) + cell_count
    product = Fraction(1)
    for joint_index, cell_count in enumerate(joint_counts):
        if cell_count == 0:
            continue
        target = JOINT_STATES[joint_index][1]
        projected = projected_by_cell[joint_index]
        product *= Fraction(
            total * source_target_counts[(projected, target)],
            source_counts[projected] * target_counts[target],
        ) ** cell_count
    return product


def verify_product_identities(
    products: FullProducts,
    nodes: Sequence[tuple[int, ...]],
    zeta: Sequence[Sequence[int]],
    joint_counts: Sequence[int],
) -> tuple[int, int, int]:
    for plus, minus, net in zip(
        products.cumulative_informative,
        products.cumulative_misinformative,
        products.cumulative_net,
        strict=True,
    ):
        require(net == plus / minus, "RECONSTRUCTION.cumulative_net")
    for plus, minus, net in zip(
        products.atom_informative,
        products.atom_misinformative,
        products.atom_net,
        strict=True,
    ):
        require(net == plus / minus, "RECONSTRUCTION.atom_net")

    for cumulatives, atoms in (
        (products.cumulative_informative, products.atom_informative),
        (products.cumulative_misinformative, products.atom_misinformative),
        (products.cumulative_net, products.atom_net),
    ):
        for cumulative_index, row in enumerate(zeta):
            reconstructed = math.prod(
                atom for atom, included in zip(atoms, row, strict=True) if included
            )
            require(
                reconstructed == cumulatives[cumulative_index],
                "RECONSTRUCTION.zeta_product",
            )

    node_index = {node: index for index, node in enumerate(nodes)}
    for mask in MASKS:
        expected = subset_mutual_information_product(joint_counts, mask)
        require(
            products.cumulative_net[node_index[(mask,)]] == expected,
            "RECONSTRUCTION.self_redundancy",
        )
    return 36, 54, 7


def witness_counts(entries: dict[int, int]) -> tuple[int, ...]:
    counts = [0] * len(JOINT_STATES)
    for cell, count in entries.items():
        counts[cell] = count
    return tuple(counts)


def verify_retained_witnesses(
    nodes: Sequence[tuple[int, ...]],
    members: Sequence[Sequence[Sequence[int]]],
    mobius: Sequence[Sequence[Fraction]],
) -> dict[str, object]:
    index = {node: position for position, node in enumerate(nodes)}

    connective = full_products(witness_counts({0: 1, 4: 1}), members, mobius)
    require(
        connective.cumulative_informative[index[(1, 2)]]
        == connective.cumulative_misinformative[index[(1, 2)]]
        == 1,
        "WITNESS.outer_or",
    )
    require(
        connective.cumulative_informative[index[(3,)]]
        == connective.cumulative_misinformative[index[(3,)]]
        == 4,
        "WITNESS.inner_and",
    )

    target = full_products(witness_counts({0: 1, 1: 1}), members, mobius)
    require(
        target.cumulative_informative[index[(7,)]]
        == target.cumulative_misinformative[index[(7,)]]
        == target.cumulative_net[index[(7,)]]
        == 1,
        "WITNESS.target_intersection",
    )

    mask_order = full_products(witness_counts({0: 1, 2: 1}), members, mobius)
    require(
        mask_order.cumulative_informative[index[(3,)]] == 1
        and mask_order.cumulative_informative[index[(4,)]] == 4,
        "WITNESS.mask_order",
    )

    weighting = full_products(witness_counts({0: 2, 4: 1}), members, mobius)
    require(
        weighting.cumulative_informative[index[(3,)]]
        == weighting.cumulative_misinformative[index[(3,)]]
        == Fraction(27, 4),
        "WITNESS.empirical_count_weighting",
    )

    negative = full_products(witness_counts({11: 1, 13: 1, 14: 1}), members, mobius)
    negative_index = index[(2, 4)]
    require(
        negative.atom_informative[negative_index] == Fraction(9, 4)
        and negative.atom_misinformative[negative_index] == 4
        and negative.atom_net[negative_index] == Fraction(9, 16),
        "WITNESS.negative_net_atom",
    )

    exact_zero = full_products(witness_counts({11: 1, 13: 1, 15: 1}), members, mobius)
    zero_index = index[(6,)]
    require(
        exact_zero.atom_informative[zero_index]
        == exact_zero.atom_misinformative[zero_index]
        == Fraction(4, 3)
        and exact_zero.atom_net[zero_index] == 1,
        "WITNESS.exact_zero_residual",
    )

    nonsyntactic = full_products(
        witness_counts({4: 1, 5: 1, 8: 1, 9: 4, 12: 1}), members, mobius
    )
    nonsyntactic_index = index[(1,)]
    require(
        nonsyntactic.atom_informative[nonsyntactic_index]
        == nonsyntactic.atom_misinformative[nonsyntactic_index]
        == 3
        and nonsyntactic.atom_net[nonsyntactic_index] == 1,
        "WITNESS.nonsyntactic_product_one",
    )

    return {
        "empirical_count_weighting": {
            "audit_expression_key": "cumulative.informative.03",
            "product": "27/4",
        },
        "exact_zero": {
            "atom_informative_product": "4/3",
            "atom_misinformative_product": "4/3",
            "atom_net_product": "1/1",
            "audit_expression_key": "atom.net.06",
        },
        "negative_net": {
            "atom_informative_product": "9/4",
            "atom_misinformative_product": "4/1",
            "atom_net_product": "9/16",
            "audit_expression_key": "atom.net.02+04",
        },
        "nonsyntactic_product_one": {
            "atom_informative_product": "3/1",
            "atom_misinformative_product": "3/1",
            "atom_net_product": "1/1",
            "audit_expression_key": "atom.net.01",
        },
        "semantic_mutation_classes": [
            "outer_branch_or",
            "inner_mask_and",
            "target_intersection",
            "source_mask_order",
        ],
    }


def log_sign_class_name(value: Fraction) -> str:
    """Name sign(ln(value)) by comparing the strictly positive product with one."""
    if value < 1:
        return "negative"
    if value > 1:
        return "positive"
    return "zero"


def update_route_native_result_digest(
    digest: DigestSink, ordinal: int, counts: Sequence[int], products: Sequence[Fraction]
) -> None:
    # Legacy route-native v1 framing is retained byte-for-byte only as a same-route continuity
    # anchor: u32 ordinal, sixteen u8 counts, then 108 length-prefixed ASCII reduced fractions.
    # It is not the route-neutral representation within the explicit cross-route v2 protocol.
    # Corpus totals are at most five, so every count is one byte.
    digest.update(ordinal.to_bytes(4, "big"))
    digest.update(bytes(counts))
    for product in products:
        token = fraction_token(product).encode("ascii")
        digest.update(len(token).to_bytes(4, "big"))
        digest.update(token)


def prime_exponents_and_log_sign(value: Fraction) -> tuple[int, int, int, int]:
    """Encode prime exponents and sign(ln(value)); the rational value is always positive."""
    require(value > 0, "NEUTRAL_STREAM.positive_product")
    numerator = value.numerator
    denominator = value.denominator
    exponents: list[int] = []
    for prime in (2, 3, 5):
        exponent = 0
        while numerator % prime == 0:
            numerator //= prime
            exponent += 1
        while denominator % prime == 0:
            denominator //= prime
            exponent -= 1
        exponents.append(exponent)
    require(
        numerator == denominator == 1,
        "NEUTRAL_STREAM.unexpected_prime_factor",
    )
    log_sign = -1 if value < 1 else 1 if value > 1 else 0
    return exponents[0], exponents[1], exponents[2], log_sign


def update_neutral_cross_route_result_digest(
    digest: DigestSink,
    ordinal: int,
    counts: Sequence[int],
    audit_expression_keys: Sequence[str],
    products: Sequence[Fraction],
) -> None:
    """Append one complete table frame in the route-neutral representation within v2."""
    require(0 <= ordinal <= 0xFFFF_FFFF, "NEUTRAL_STREAM.ordinal_u32")
    require(len(counts) == len(JOINT_STATES) == 16, "NEUTRAL_STREAM.count_vector_length")
    require(
        all(type(count) is int and 0 <= count <= 0xFF for count in counts),
        "NEUTRAL_STREAM.count_vector_u8",
    )
    require(
        len(audit_expression_keys) == len(products) == 108,
        "NEUTRAL_STREAM.audit_expression_count",
    )
    digest.update(struct.pack(">I", ordinal))
    encoded_counts = bytes(counts)
    digest.update(encoded_counts)
    for audit_expression_index, (audit_expression_key, product) in enumerate(
        zip(audit_expression_keys, products, strict=True)
    ):
        key = audit_expression_key.encode("ascii")
        require(len(key) <= 0xFFFF, "NEUTRAL_STREAM.key_length_u16")
        digest.update(struct.pack(">BH", audit_expression_index, len(key)))
        digest.update(key)
        digest.update(struct.pack(">qqqb", *prime_exponents_and_log_sign(product)))


def verify_neutral_stream_framing_unit(
    audit_expression_keys: Sequence[str],
) -> str:
    """Check update boundaries and bytes for one deliberately non-corpus frame."""
    require(len(audit_expression_keys) == 108, "NEUTRAL_STREAM.framing_unit_registry")
    ordinal = 0x0102_0304
    counts = tuple(range(16))
    products = (
        Fraction(2),
        Fraction(1, 3),
        Fraction(1),
        *(Fraction(1) for _ in range(105)),
    )
    recorder = FramingRecorder()
    update_neutral_cross_route_result_digest(
        recorder, ordinal, counts, audit_expression_keys, products
    )
    require(len(recorder.chunks) == 2 + 3 * 108, "NEUTRAL_STREAM.framing_unit_chunk_count")
    require(
        recorder.chunks[0] == struct.pack(">I", ordinal),
        "NEUTRAL_STREAM.framing_unit_ordinal",
    )
    require(
        recorder.chunks[1] == bytes(range(16)),
        "NEUTRAL_STREAM.framing_unit_counts",
    )
    for audit_expression_index, audit_expression_key in enumerate(audit_expression_keys):
        offset = 2 + 3 * audit_expression_index
        encoded_key = audit_expression_key.encode("ascii")
        require(
            recorder.chunks[offset]
            == struct.pack(">BH", audit_expression_index, len(encoded_key)),
            "NEUTRAL_STREAM.framing_unit_record_header",
        )
        require(
            recorder.chunks[offset + 1] == encoded_key,
            "NEUTRAL_STREAM.framing_unit_record_key",
        )
        require(
            recorder.chunks[offset + 2]
            == struct.pack(
                ">qqqb",
                *prime_exponents_and_log_sign(products[audit_expression_index]),
            ),
            "NEUTRAL_STREAM.framing_unit_record_prime_exponents_and_log_sign",
        )
    digest = hashlib.sha256(TABLE_BOUND_AUDIT_DOMAIN)
    for chunk in recorder.chunks:
        digest.update(chunk)
    framing_sha256 = digest.hexdigest()
    require(
        framing_sha256 == EXPECTED_NEUTRAL_FRAMING_UNIT_SHA256,
        "NEUTRAL_STREAM.framing_unit_sha256",
    )
    return framing_sha256


def verify_exhaustive_corpus(
    nodes: Sequence[tuple[int, ...]],
    zeta: Sequence[Sequence[int]],
    mobius: Sequence[Sequence[Fraction]],
    members: Sequence[Sequence[Sequence[int]]],
    audit_expression_keys: Sequence[str],
) -> dict[str, object]:
    block_names = tuple(
        f"{scope}.{component}" for scope, component in AUDIT_EXPRESSION_BLOCKS
    )
    bounded_sign_counts_by_audit_expression_block = {
        block: {"negative": 0, "positive": 0, "zero": 0}
        for block in block_names
    }
    tables_by_total: list[int] = []
    primitive_by_total: list[int] = []
    table_count = 0
    primitive_count = 0
    supported_pairs = 0
    maximum_positive_cells = 0
    full_support_16_cell_laws = 0
    audit_expression_verdicts = 0
    strictly_positive_exact_product_checks = 0
    cumulative_net_checks = 0
    atom_net_checks = 0
    zeta_checks = 0
    self_redundancy_checks = 0
    replication_checks = 0
    corpus_digest = hashlib.sha256()
    route_native_result_digest = hashlib.sha256()
    neutral_cross_route_result_digest = hashlib.sha256(TABLE_BOUND_AUDIT_DOMAIN)

    for total in range(1, MAX_TOTAL + 1):
        total_tables = 0
        total_primitive = 0
        for counts in compositions(total, len(JOINT_STATES)):
            ordinal = table_count
            table_count += 1
            total_tables += 1
            gcd = math.gcd(*counts)
            is_primitive = gcd == 1
            primitive_count += int(is_primitive)
            total_primitive += int(is_primitive)
            positive_cells = sum(count > 0 for count in counts)
            supported_pairs += positive_cells
            maximum_positive_cells = max(maximum_positive_cells, positive_cells)
            full_support_16_cell_laws += int(positive_cells == len(JOINT_STATES))
            corpus_digest.update(bytes(counts))

            products = full_products(counts, members, mobius)
            audit_expressions = products.audit_expressions()
            require(
                len(audit_expressions) == 108,
                "AUDIT_EXPRESSION.per_table_count",
            )
            require(
                all(product > 0 for product in audit_expressions),
                "AUDIT_EXPRESSION.strictly_positive_exact_product",
            )
            strictly_positive_exact_product_checks += len(audit_expressions)
            update_route_native_result_digest(
                route_native_result_digest, ordinal, counts, audit_expressions
            )
            update_neutral_cross_route_result_digest(
                neutral_cross_route_result_digest,
                ordinal,
                counts,
                audit_expression_keys,
                audit_expressions,
            )
            audit_expression_verdicts += len(audit_expressions)

            net_count, zeta_count, self_count = verify_product_identities(
                products, nodes, zeta, counts
            )
            cumulative_net_checks += net_count // 2
            atom_net_checks += net_count // 2
            zeta_checks += zeta_count
            self_redundancy_checks += self_count

            blocks = (
                products.cumulative_informative,
                products.cumulative_misinformative,
                products.cumulative_net,
                products.atom_informative,
                products.atom_misinformative,
                products.atom_net,
            )
            for block_name, block in zip(block_names, blocks, strict=True):
                for product in block:
                    bounded_sign_counts_by_audit_expression_block[block_name][
                        log_sign_class_name(product)
                    ] += 1

            if gcd > 1:
                primitive_counts = tuple(count // gcd for count in counts)
                primitive_products = full_products(primitive_counts, members, mobius)
                for replicated, primitive in zip(
                    audit_expressions,
                    primitive_products.audit_expressions(),
                    strict=True,
                ):
                    require(replicated == primitive**gcd, "REPLICATION.product_power")
                    replication_checks += 1

        tables_by_total.append(total_tables)
        primitive_by_total.append(total_primitive)

    require(tuple(tables_by_total) == EXPECTED_TABLES_BY_TOTAL, "CORPUS.tables_by_total")
    require(
        tuple(primitive_by_total) == EXPECTED_PRIMITIVE_BY_TOTAL,
        "CORPUS.primitive_by_total",
    )
    require(table_count == 20_348, "CORPUS.table_count")
    require(primitive_count == 20_164, "CORPUS.primitive_law_count")
    require(table_count - primitive_count == 184, "CORPUS.nonprimitive_count")
    require(tables_by_total[-1] == 15_504, "CORPUS.total_count_five_tables")
    require(supported_pairs == 77_520, "CORPUS.supported_pair_count")
    require(maximum_positive_cells == 5, "CORPUS.maximum_positive_cells")
    require(full_support_16_cell_laws == 0, "CORPUS.full_support_law_count")
    require(
        audit_expression_verdicts == 2_197_584,
        "CORPUS.audit_expression_verdict_count",
    )
    require(
        strictly_positive_exact_product_checks == 2_197_584,
        "CORPUS.strictly_positive_exact_product_check_count",
    )
    require(cumulative_net_checks == 366_264, "CORPUS.cumulative_net_checks")
    require(atom_net_checks == 366_264, "CORPUS.atom_net_checks")
    require(zeta_checks == 1_098_792, "CORPUS.zeta_checks")
    require(self_redundancy_checks == 142_436, "CORPUS.self_redundancy_checks")
    require(replication_checks == 19_872, "CORPUS.replication_checks")

    corpus_sha256 = corpus_digest.hexdigest()
    route_native_result_sha256 = route_native_result_digest.hexdigest()
    neutral_cross_route_result_sha256 = neutral_cross_route_result_digest.hexdigest()
    require(corpus_sha256 == EXPECTED_CORPUS_STREAM_SHA256, "CORPUS.stream_sha256")
    require(
        route_native_result_sha256 == EXPECTED_ROUTE_NATIVE_RESULT_STREAM_SHA256,
        "ROUTE_NATIVE_RESULT.stream_sha256",
    )
    require(
        neutral_cross_route_result_sha256
        == EXPECTED_NEUTRAL_CROSS_ROUTE_RESULT_STREAM_SHA256,
        "NEUTRAL_STREAM.stream_sha256",
    )
    require(
        bounded_sign_counts_by_audit_expression_block
        == EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK,
        "AUDIT_EXPRESSION.bounded_sign_counts_by_block",
    )
    require(
        all(
            sum(counts_by_sign.values()) == 366_264
            for counts_by_sign in bounded_sign_counts_by_audit_expression_block.values()
        ),
        "AUDIT_EXPRESSION.sign_block_denominator",
    )

    # This is a bounded observation on the declared corpus, not a replacement for the published
    # component-nonnegativity theorem or its paper-to-code mapping.
    for block in (
        "cumulative.informative",
        "cumulative.misinformative",
        "atom.informative",
        "atom.misinformative",
    ):
        require(
            bounded_sign_counts_by_audit_expression_block[block]["negative"] == 0,
            "AUDIT_EXPRESSION.bounded_component_negative",
        )

    return {
        "atom_net_identity_checks": atom_net_checks,
        "averaged_keyed_scalar_audit_expression_product_verdicts": (
            audit_expression_verdicts
        ),
        "binary_labeled_count_tables": table_count,
        "route_native_result_stream_sha256": route_native_result_sha256,
        "corpus_stream_sha256": corpus_sha256,
        "cumulative_net_identity_checks": cumulative_net_checks,
        "maximum_total_count": MAX_TOTAL,
        "maximum_positive_cells": maximum_positive_cells,
        "neutral_cross_route_audit_expression_stream_sha256": (
            neutral_cross_route_result_sha256
        ),
        "pointwise_audit_expressions_evaluated": 0,
        "pointwise_scope_clarification": {
            "pointwise_atom_coordinates_or_values_output": False,
            "local_event_ratios_evaluated": True,
            "local_event_ratio_role": (
                "factors_aggregated_only_into_averaged_exact_products"
            ),
        },
        "primitive_rational_laws": primitive_count,
        "nonprimitive_rescaled_count_vectors": table_count - primitive_count,
        "replication_product_power_checks": replication_checks,
        "self_redundancy_checks": self_redundancy_checks,
        "strictly_positive_exact_product_checks": (
            strictly_positive_exact_product_checks
        ),
        "full_support_16_cell_laws": full_support_16_cell_laws,
        "sign_block_denominator_table_antichain_position_pairs": 366_264,
        "bounded_sign_counts_by_audit_expression_block": (
            bounded_sign_counts_by_audit_expression_block
        ),
        "supported_table_realization_pairs_counted": supported_pairs,
        "tables_by_total": tables_by_total,
        "zeta_product_reconstruction_checks": zeta_checks,
    }


def main() -> int:
    nodes = enumerate_antichains()
    require(nodes == EXPECTED_ANTICHAINS, "ANTICHAIN.registry")
    keys = tuple(stable_key(node) for node in nodes)
    require(keys == EXPECTED_AUDIT_STABLE_KEYS, "ANTICHAIN.audit_stable_keys")
    rust_keys = rust_antichain_stable_keys()
    audit_to_rust, rust_to_audit = audit_to_rust_key_bridge(keys, rust_keys)

    audit_expression_keys = audit_expression_registry(keys)
    require(
        len(audit_expression_keys) == 108
        and len(set(audit_expression_keys)) == 108,
        "AUDIT_EXPRESSION.registry_shape",
    )
    audit_expression_registry_sha256 = canonical_sha256(list(audit_expression_keys))
    require(
        audit_expression_registry_sha256
        == EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256,
        "AUDIT_EXPRESSION.registry_sha256",
    )

    event_sha256 = verify_event_registry(nodes)
    permutation_count = verify_source_permutations(nodes)
    zeta = zeta_matrix(nodes)
    zeta_signatures = tuple("".join(map(str, row)) for row in zeta)
    require(zeta_signatures == EXPECTED_ZETA_SIGNATURES, "ZETA.row_signatures")
    require(sum(map(sum, zeta)) == 129, "ZETA.one_count")
    mobius = inverse_matrix_exact(zeta)
    require(sparse_integer_rows(mobius) == EXPECTED_MOBIUS_SPARSE, "MOBIUS.sparse_rows")
    expected_identity = identity(len(nodes))
    require(matrix_product(mobius, zeta) == expected_identity, "MOBIUS.left_inverse")
    require(matrix_product(zeta, mobius) == expected_identity, "MOBIUS.right_inverse")
    require(
        sum(value != 0 for row in mobius for value in row) == 65,
        "MOBIUS.nonzero_count",
    )
    require(
        {value for row in mobius for value in row}
        <= {Fraction(-1), Fraction(0), Fraction(1)},
        "MOBIUS.coefficient_range",
    )

    semantic_registry = {
        "antichains": [list(node) for node in nodes],
        "audit_stable_keys": list(keys),
        "audit_to_rust_node_index_by_key": list(audit_to_rust),
        "audit_expression_keys": list(audit_expression_keys),
        "definition_revision": DEFINITION_REVISION,
        "event_revision": EVENT_REVISION,
        "event_truth_sha256": event_sha256,
        "joint_states": [[*source, target] for source, target in JOINT_STATES],
        "mobius_sparse": [
            [[column, coefficient] for column, coefficient in row]
            for row in EXPECTED_MOBIUS_SPARSE
        ],
        "source_bits": list(SOURCE_BITS),
        "rust_stable_keys": list(rust_keys),
        "zeta_signatures": list(zeta_signatures),
    }
    semantic_sha256 = canonical_sha256(semantic_registry)
    require(
        semantic_sha256 == EXPECTED_SEMANTIC_REGISTRY_SHA256,
        "SEMANTIC.registry_sha256",
    )

    members = event_member_indices(nodes)
    witnesses = verify_retained_witnesses(nodes, members, mobius)
    targeted_permutation_checks = verify_targeted_source_permutation_products(
        nodes, members, mobius
    )
    neutral_framing_unit_sha256 = verify_neutral_stream_framing_unit(
        audit_expression_keys
    )
    exhaustive = verify_exhaustive_corpus(
        nodes, zeta, mobius, members, audit_expression_keys
    )
    result = {
        "assumptions": [
            "three_ordered_binary_sources_and_one_binary_target",
            "nonnegative_integer_cell_counts_with_positive_total_one_through_five",
            "source_event_is_or_of_within_mask_conjunctions",
            "misinformative_event_is_source_event_intersected_with_keyed_target",
            "natural_log_audit_expression_is_one_over_total_times_log_of_exact_product",
            "108_keyed_scalar_audit_expressions_equal_18_antichain_positions_times_2_representation_stages_times_3_components",
            "row_cumulative_column_atom_zeta_orientation",
        ],
        "bounded_exhaustive_scope": exhaustive,
        "census_interpretation": CENSUS_INTERPRETATION,
        "audit_expression_registry": {
            "block_count": len(AUDIT_EXPRESSION_BLOCKS),
            "component_count": 3,
            "keyed_scalar_audit_expression_count": len(audit_expression_keys),
            "antichain_position_count": len(nodes),
            "representation_stage_count": 2,
            "representation_stages": ["cumulative_values", "mobius_atoms"],
            "revision": AUDIT_EXPRESSION_REVISION,
            "sha256": audit_expression_registry_sha256,
        },
        "cross_route_assurance": CROSS_ROUTE_ASSURANCE,
        "definition_revision": DEFINITION_REVISION,
        "digest_classification": {
            "audit_expression_registry_event_semantic_corpus_and_native_result": (
                "same_route_regression_and_drift_anchors_not_logically_independent_truth"
            ),
            "neutral_table_bound_audit_expression_result_stream": (
                "primary_result_compared_only_to_embedded_externally_supplied_"
                "expected_digest_not_paired_route_execution_or_proof"
            ),
        },
        "event_revision": EVENT_REVISION,
        "format": FORMAT,
        "gate": "GO",
        "gate_scope": {
            "meaning": "primary_lane_local_obligations_passed",
            "scientific_validation": False,
        },
        "legacy_schema_terminology": LEGACY_SCHEMA_TERMINOLOGY,
        "lattice": {
            "antichain_count": len(nodes),
            "event_truth_sha256": event_sha256,
            "mobius_nonzero_count": 65,
            "source_permutation_automorphisms_checked": permutation_count,
            "audit_to_rust_node_index_by_key": list(audit_to_rust),
            "rust_to_audit_node_index_by_key": list(rust_to_audit),
            "rust_order_source_function_sha256": (
                EXPECTED_RUST_ANTICHAIN_FUNCTION_SHA256
            ),
            "targeted_source_permutation_product_checks": targeted_permutation_checks,
            "two_sided_exact_inverse": True,
            "zeta_one_count": 129,
        },
        "method_provenance_and_novelty": METHOD_PROVENANCE_AND_NOVELTY,
        "nonclaims": [
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
        ],
        "p1_separate_lane_status": P1_SEPARATE_LANE_STATUS,
        "retained_witnesses": witnesses,
        "semantic_registry_sha256": semantic_sha256,
        "sign_semantics": SIGN_SEMANTICS,
        "serialization": {
            "cell_index_formula": "cell_index=8*s1+4*s2+2*s3+t",
            "neutral_cross_route_domain_ascii": (
                "pid-rs.sxpid3.table-bound-audit-expressions.v2\\0"
            ),
            "neutral_framing_unit_sha256": neutral_framing_unit_sha256,
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
        "status_classification": {
            "bounded_binary_products": "bounded_exhaustive_test",
            "p1_informative_invariance": "outside_artifact_separate_lane_not_replayed",
            "mgw_formula_correspondence": "external_premise_open",
            "independent_route_source_and_execution_binding": "absent",
            "paired_route_agreement": "requires_later_closed_receipt",
            "rust_refinement": "open",
        },
    }
    print(canonical_json(result), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ArithmeticError, OSError, RuntimeError, ValueError) as error:
        print(f"SxPID3 bounded audit expressions: {error}", file=sys.stderr)
        raise SystemExit(1)
