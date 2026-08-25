#!/usr/bin/env python3
"""Bounded SxPID3 verifier with a described implementation-disjoint design.

Scientific scope
----------------
This program checks a prospective audit transcription of the finite categorical
shared-exclusions construction on exactly the labeled binary 16-cell count
tables with 1 <= N <= 5.  The transcription is intended to represent
Makkeh--Gutknecht--Wibral (MGW) equations (6), (13), (14a), (15a), (15b), and
(17), specialized to natural logarithms and empirical count weights; paper
correspondence remains an external premise.  Equation (13) is the pointwise
zeta/Möbius relation, equation (17) averages local values with empirical joint
weights, and finite linear averaging commutes with the finite zeta/Möbius
combination.  A versioned mask-lex audit key
registry is treated as serialization for this checker, not as a shipped pid-rs
public order and not as the source of the event or lattice semantics.  The 108
expressions are 18 antichain keys times two representation stages (cumulative
values and Möbius atoms) times three components (informative, misinformative,
and signed net).  They are not
108 lattice nodes, 108 atoms, or 108 independent degrees of freedom.

Implementation-disjoint choices under shared semantics
------------------------------------------------------
* count tables are obtained by lexicographic stars-and-bars unranking;
* antichains and the redundancy order are generated from subset semantics;
* union-event masses are obtained from cylinder marginals by
  inclusion-exclusion, never by scanning an OR predicate over supported rows;
* atom products are obtained by recursive poset subtraction, never by a
  matrix inverse; and
* exact positive rationals are represented by signed exponents of the primes
  2, 3, and 5, never by Fraction or a symbolic algebra package.

The result is exhaustive computational evidence only for the stated finite
domain and 2,197,584 keyed scalar expression evaluations.  It is not a theorem over
arbitrary alphabets or counts, a proof of the MGW paper-to-code transcription,
a probability/population statement, a Rust refinement result, a floating-point
or interval certificate, or a scientific-novelty claim.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import sys
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


class VerificationError(RuntimeError):
    """A deterministic fail-closed verification error."""


def require(condition: bool, message: str) -> None:
    """Raise even under ``python -O``; never use ``assert`` for obligations."""

    if not condition:
        raise VerificationError(message)


def require_isolated_cpython() -> None:
    """Fail closed unless execution uses the declared, source-first interpreter lane."""

    require(sys.implementation.name == "cpython", "PYTHON.implementation")
    require(sys.version_info >= (3, 11), "PYTHON.minimum_version")
    require(sys.flags.ignore_environment == 1, "PYTHON.ignore_environment")
    require(sys.flags.safe_path is True, "PYTHON.safe_path")
    require(sys.flags.isolated == 1, "PYTHON.isolated")
    require(sys.flags.no_site == 1, "PYTHON.no_site")
    require(sys.flags.dont_write_bytecode == 1, "PYTHON.dont_write_bytecode")
    require(sys.flags.optimize in (0, 1), "PYTHON.optimize")


try:
    require_isolated_cpython()
except VerificationError as bootstrap_error:
    print(f"FAIL: {bootstrap_error}", file=sys.stderr)
    raise SystemExit(1) from None


SOURCE_COUNT = 3
CELL_COUNT = 16
MAX_TOTAL = 5
PRIMES = (2, 3, 5)
COMPONENTS = ("informative", "misinformative", "net")
BLOCKS = (
    ("cumulative", "informative"),
    ("cumulative", "misinformative"),
    ("cumulative", "net"),
    ("atom", "informative"),
    ("atom", "misinformative"),
    ("atom", "net"),
)
AUDIT_EXPRESSION_REVISION = "sxpid3-mask-lex-antichain-order-averaged-108-v1"

# This literal pins only this prospective audit serialization.  It is not the
# positional order of the shipped Rust registry.  The carrier is generated
# independently from all nonempty subsets of masks 1..7 below.
EXPECTED_NODE_KEYS = (
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

EXPECTED_TABLES_BY_TOTAL = (16, 136, 816, 3_876, 15_504)
EXPECTED_PRIMITIVE_BY_TOTAL = (16, 120, 800, 3_740, 15_488)
EXPECTED_TABLE_COUNT = 20_348
EXPECTED_PRIMITIVE_COUNT = 20_164
EXPECTED_SUPPORT_PAIR_COUNT = 77_520
EXPECTED_AUDIT_EXPRESSION_COUNT = 108
EXPECTED_AUDIT_EXPRESSION_VERDICTS = 2_197_584
EXPECTED_ZETA_ONES = 129
EXPECTED_MOBIUS_NONZERO = 65

TABLE_BOUND_AUDIT_DOMAIN = b"pid-rs.sxpid3.table-bound-audit-expressions.v2\0"
CELL_INDEX_FORMULA = "cell_index=8*s1+4*s2+2*s3+t"

# Filled only after an independently reviewed first execution.  These bind the
# exact byte-level definitions in digest_corpus(), digest_lattice(), and the
# canonical result stream in run_full().
EXPECTED_CORPUS_SHA256 = "474da2048645445d5f221f50c7d0992cadc8819eba3674107f2a69059ced9b4e"
EXPECTED_LATTICE_SHA256 = "342351464631a4d9407195e8ece42cb765ab80495366b98661eacac4c939023b"
EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256 = "da4d8e7ea2793983f8758a7c72dfa8b0ac1ffaeb67fba57711064f1ceb6840d4"
EXPECTED_PROBE_SHA256 = "0be8300134d62a7f0b0ea2f34f21b2cc76d96460f443ac75f6106697bd8510b5"
EXPECTED_ROUTE_NATIVE_RESULT_SHA256 = "4996153f04315852492bbff45548ad241f8aeaacad11e25ab510bc86267c201a"
EXPECTED_TABLE_BOUND_RESULT_SHA256 = "20c234cc664ad903aa66689d33d95b2db5bca5da3b0f9ee0b497d1246e3139b8"
EXPECTED_FRAMING_PROBE_SHA256 = "f115265206099bac95b22149dc83c98fed2de93c4265a001c232266e02f4d813"

# A result from another implementation may be compared with these counts, but
# this verifier does not import or call that implementation.  Each block has
# 20,348 * 18 = 366,264 exact decisions.
EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK = {
    "atom.informative": {"negative": 0, "positive": 145_100, "zero": 221_164},
    "atom.misinformative": {"negative": 0, "positive": 71_468, "zero": 294_796},
    "atom.net": {"negative": 31_284, "positive": 96_768, "zero": 238_212},
    "cumulative.informative": {"negative": 0, "positive": 321_856, "zero": 44_408},
    "cumulative.misinformative": {"negative": 0, "positive": 278_984, "zero": 87_280},
    "cumulative.net": {"negative": 29_496, "positive": 252_816, "zero": 83_952},
}

CENSUS_INTERPRETATION = {
    "enumeration_weighting": "unweighted",
    "enumerated_objects": "labelled_16_cell_count_vectors",
    "count_vector_cell_order": CELL_INDEX_FORMULA,
    "applies_to_blocks": [f"{kind}.{component}" for kind, component in BLOCKS],
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

SIGN_SEMANTICS = {
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

METHOD_PROVENANCE_AND_NOVELTY = {
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

ROUTE_ASSURANCE = {
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


ExponentVector = tuple[int, int, int]
ZERO_EXPONENTS: ExponentVector = (0, 0, 0)


def add(left: ExponentVector, right: ExponentVector) -> ExponentVector:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def sub(left: ExponentVector, right: ExponentVector) -> ExponentVector:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def scale(value: ExponentVector, coefficient: int) -> ExponentVector:
    return (
        coefficient * value[0],
        coefficient * value[1],
        coefficient * value[2],
    )


def factor_positive_integer(value: int) -> ExponentVector:
    """Return the unique prime-exponent representation on the bounded domain."""

    require(isinstance(value, int) and not isinstance(value, bool), "factor is not an integer")
    require(1 <= value <= MAX_TOTAL, f"factor {value} leaves the N<=5 domain")
    residual = value
    exponents: list[int] = []
    for prime in PRIMES:
        exponent = 0
        while residual % prime == 0:
            residual //= prime
            exponent += 1
        exponents.append(exponent)
    require(residual == 1, f"unrepresented prime factor in {value}")
    return (exponents[0], exponents[1], exponents[2])


FACTOR_CACHE = tuple(factor_positive_integer(value) for value in range(1, MAX_TOTAL + 1))


def exponent_ratio(numerator: int, denominator: int) -> ExponentVector:
    require(numerator > 0 and denominator > 0, "nonpositive exact-product factor")
    return sub(FACTOR_CACHE[numerator - 1], FACTOR_CACHE[denominator - 1])


_SIGN_CACHE: dict[ExponentVector, int] = {ZERO_EXPONENTS: 0}


def compare_product_with_one(value: ExponentVector) -> int:
    """Compare a prime-exponent rational with one by exact cross multiplication."""

    cached = _SIGN_CACHE.get(value)
    if cached is not None:
        return cached
    numerator = 1
    denominator = 1
    for prime, exponent in zip(PRIMES, value):
        if exponent > 0:
            numerator *= prime**exponent
        elif exponent < 0:
            denominator *= prime ** (-exponent)
    result = (numerator > denominator) - (numerator < denominator)
    _SIGN_CACHE[value] = result
    return result


def numerator_denominator(value: ExponentVector) -> tuple[int, int]:
    """Materialize a normalized rational only for compact diagnostic witnesses."""

    numerator = 1
    denominator = 1
    for prime, exponent in zip(PRIMES, value):
        if exponent > 0:
            numerator *= prime**exponent
        elif exponent < 0:
            denominator *= prime ** (-exponent)
    return numerator, denominator


def sign_name(sign: int) -> str:
    require(sign in (-1, 0, 1), f"invalid log-sign/comparison code {sign}")
    return ("negative", "zero", "positive")[sign + 1]


def stable_key(node: Sequence[int]) -> str:
    return "+".join(f"{mask:02x}" for mask in node)


def is_strict_subset(left: int, right: int) -> bool:
    return left != right and (left & right) == left


def generate_antichains() -> tuple[tuple[int, ...], ...]:
    """Generate the carrier semantically; no generated registry is imported."""

    nodes: list[tuple[int, ...]] = []
    for selector in range(1, 1 << 7):
        candidate = tuple(mask for mask in range(1, 8) if selector & (1 << (mask - 1)))
        incomparable = all(
            not is_strict_subset(left, right) and not is_strict_subset(right, left)
            for left, right in itertools.combinations(candidate, 2)
        )
        if incomparable:
            nodes.append(candidate)
    nodes.sort(key=lambda node: (len(node), node))
    result = tuple(nodes)
    require(len(result) == 18, f"semantic antichain carrier has {len(result)} nodes, not 18")
    require(tuple(stable_key(node) for node in result) == EXPECTED_NODE_KEYS, "node-key contract drift")
    return result


NODES = generate_antichains()
NODE_INDEX = {node: index for index, node in enumerate(NODES)}


def redundancy_leq(lower: Sequence[int], upper: Sequence[int]) -> bool:
    """Williams--Beer redundancy order used by MGW equation (13)."""

    return all(any((a & b) == a for a in lower) for b in upper)


def build_order() -> tuple[tuple[bool, ...], ...]:
    order = tuple(tuple(redundancy_leq(lower, upper) for lower in NODES) for upper in NODES)
    # Rows are upper/cumulative nodes, columns are lower/atom nodes.
    for index in range(len(NODES)):
        require(order[index][index], "redundancy order is not reflexive")
    for left in range(len(NODES)):
        for right in range(len(NODES)):
            if order[left][right] and order[right][left]:
                require(left == right, "redundancy order is not antisymmetric")
            for third in range(len(NODES)):
                if order[left][right] and order[right][third]:
                    require(order[left][third], "redundancy order is not transitive")
    require(sum(value for row in order for value in row) == EXPECTED_ZETA_ONES, "zeta-one count drift")
    bottom = NODE_INDEX[(1, 2, 4)]
    top = NODE_INDEX[(7,)]
    require(all(order[index][bottom] for index in range(len(NODES))), "declared bottom is not below all nodes")
    require(all(order[top][index] for index in range(len(NODES))), "declared top is not above all nodes")
    return order


ORDER = build_order()
STRICT_LOWERS = tuple(
    tuple(lower for lower in range(len(NODES)) if lower != upper and ORDER[upper][lower])
    for upper in range(len(NODES))
)
TOPOLOGICAL_NODE_ORDER = tuple(sorted(range(len(NODES)), key=lambda index: (len(STRICT_LOWERS[index]), index)))


def derive_mobius_rows_recursively() -> tuple[tuple[int, ...], ...]:
    """Derive atom-from-cumulative coefficients by poset recursion, not inversion."""

    rows: list[tuple[int, ...] | None] = [None] * len(NODES)
    for node_index in TOPOLOGICAL_NODE_ORDER:
        row = [0] * len(NODES)
        row[node_index] = 1
        for lower in STRICT_LOWERS[node_index]:
            lower_row = rows[lower]
            if lower_row is None:
                raise VerificationError("non-topological recursive Möbius traversal")
            for column, coefficient in enumerate(lower_row):
                row[column] -= coefficient
        rows[node_index] = tuple(row)
    result = tuple(row for row in rows if row is not None)
    require(len(result) == len(NODES), "missing recursive Möbius row")
    require(all(coefficient in (-1, 0, 1) for row in result for coefficient in row), "unexpected Möbius coefficient")
    require(
        sum(coefficient != 0 for row in result for coefficient in row) == EXPECTED_MOBIUS_NONZERO,
        "Möbius nonzero-count drift",
    )
    # Both products are checked entrywise, but no inverse routine is involved.
    for row_index in range(len(NODES)):
        for column in range(len(NODES)):
            mz = sum(result[row_index][middle] * int(ORDER[middle][column]) for middle in range(len(NODES)))
            zm = sum(int(ORDER[row_index][middle]) * result[middle][column] for middle in range(len(NODES)))
            expected = int(row_index == column)
            require(mz == expected, f"recursive MZ identity failed at ({row_index},{column})")
            require(zm == expected, f"recursive ZM identity failed at ({row_index},{column})")
    return result


MOBIUS_ROWS = derive_mobius_rows_recursively()


def audit_expression_registry() -> tuple[str, ...]:
    registry = tuple(f"{kind}.{component}.{stable_key(node)}" for kind, component in BLOCKS for node in NODES)
    require(len(registry) == EXPECTED_AUDIT_EXPRESSION_COUNT, "audit-expression registry is not length 108")
    require(len(set(registry)) == len(registry), "duplicate audit-expression key")
    return registry


AUDIT_EXPRESSION_REGISTRY = audit_expression_registry()


def sha256_lines(lines: Iterable[str], domain: bytes) -> str:
    digest = hashlib.sha256(domain)
    for line in lines:
        encoded = line.encode("ascii")
        digest.update(struct.pack(">H", len(encoded)))
        digest.update(encoded)
    return digest.hexdigest()


def digest_lattice() -> str:
    digest = hashlib.sha256(b"pid-rs.sxpid3.independent.lattice.v1\0")
    for index, node in enumerate(NODES):
        key = stable_key(node).encode("ascii")
        digest.update(struct.pack(">BH", index, len(key)))
        digest.update(key)
        digest.update(bytes(int(value) for value in ORDER[index]))
        for coefficient in MOBIUS_ROWS[index]:
            digest.update(struct.pack(">b", coefficient))
    return digest.hexdigest()


def combination_count(n: int, k: int) -> int:
    return math.comb(n, k) if 0 <= k <= n else 0


def unrank_lex_combination(n: int, k: int, rank: int) -> tuple[int, ...]:
    """Unrank a k-subset of range(n) in lexicographic order."""

    require(0 <= rank < combination_count(n, k), "combination rank outside domain")
    chosen: list[int] = []
    next_minimum = 0
    remaining_rank = rank
    for position in range(k):
        remaining_slots = k - position - 1
        maximum = n - remaining_slots
        selected = None
        for candidate in range(next_minimum, maximum):
            suffixes = combination_count(n - candidate - 1, remaining_slots)
            if remaining_rank < suffixes:
                selected = candidate
                break
            remaining_rank -= suffixes
        if selected is None:
            raise VerificationError("combination unranking exhausted candidates")
        chosen.append(selected)
        next_minimum = selected + 1
    require(remaining_rank == 0, "combination unranking left a residual rank")
    return tuple(chosen)


def rank_lex_combination(n: int, k: int, chosen: Sequence[int]) -> int:
    require(len(chosen) == k, "combination has wrong cardinality")
    require(tuple(chosen) == tuple(sorted(set(chosen))), "combination is not strictly increasing")
    require(all(0 <= value < n for value in chosen), "combination member outside domain")
    rank = 0
    next_minimum = 0
    for position, selected in enumerate(chosen):
        remaining_slots = k - position - 1
        for candidate in range(next_minimum, selected):
            rank += combination_count(n - candidate - 1, remaining_slots)
        next_minimum = selected + 1
    require(rank < combination_count(n, k), "combination rank overflow")
    return rank


def separators_to_counts(total: int, separators: Sequence[int]) -> tuple[int, ...]:
    require(len(separators) == CELL_COUNT - 1, "wrong separator count")
    counts: list[int] = []
    previous = -1
    for separator in separators:
        counts.append(separator - previous - 1)
        previous = separator
    counts.append(total + CELL_COUNT - 2 - previous)
    result = tuple(counts)
    require(len(result) == CELL_COUNT and all(count >= 0 for count in result), "invalid star/bar gaps")
    require(sum(result) == total, "star/bar gaps have wrong total")
    return result


def counts_to_separators(counts: Sequence[int]) -> tuple[int, ...]:
    require(len(counts) == CELL_COUNT, "count vector has wrong length")
    require(all(isinstance(count, int) and count >= 0 for count in counts), "invalid count vector")
    separators: list[int] = []
    stars_seen = 0
    for index, count in enumerate(counts[:-1]):
        stars_seen += count
        separators.append(stars_seen + index)
    return tuple(separators)


TOTAL_OFFSETS = tuple(
    sum(combination_count(previous + CELL_COUNT - 1, CELL_COUNT - 1) for previous in range(1, total))
    for total in range(1, MAX_TOTAL + 1)
)


def unrank_count_vector(ordinal: int) -> tuple[int, ...]:
    require(0 <= ordinal < EXPECTED_TABLE_COUNT, "count-vector ordinal outside bounded corpus")
    total = 1
    while total < MAX_TOTAL and ordinal >= TOTAL_OFFSETS[total]:
        total += 1
    local_rank = ordinal - TOTAL_OFFSETS[total - 1]
    separators = unrank_lex_combination(total + CELL_COUNT - 1, CELL_COUNT - 1, local_rank)
    counts = separators_to_counts(total, separators)
    require(rank_count_vector(counts) == ordinal, "count-vector rank/unrank mismatch")
    return counts


def rank_count_vector(counts: Sequence[int]) -> int:
    total = sum(counts)
    require(1 <= total <= MAX_TOTAL, "count vector leaves 1<=N<=5")
    separators = counts_to_separators(counts)
    local_rank = rank_lex_combination(total + CELL_COUNT - 1, CELL_COUNT - 1, separators)
    ordinal = TOTAL_OFFSETS[total - 1] + local_rank
    require(0 <= ordinal < EXPECTED_TABLE_COUNT, "ranked count vector left corpus")
    return ordinal


def iter_count_vectors() -> Iterator[tuple[int, tuple[int, ...]]]:
    for ordinal in range(EXPECTED_TABLE_COUNT):
        yield ordinal, unrank_count_vector(ordinal)


def digest_corpus() -> tuple[str, tuple[int, ...], tuple[int, ...], int]:
    digest = hashlib.sha256(b"pid-rs.sxpid3.independent.corpus.v1\0")
    tables_by_total = [0] * MAX_TOTAL
    primitive_by_total = [0] * MAX_TOTAL
    support_pairs = 0
    seen: set[tuple[int, ...]] = set()
    for ordinal, counts in iter_count_vectors():
        require(counts not in seen, "duplicate count vector in ranked corpus")
        seen.add(counts)
        total = sum(counts)
        tables_by_total[total - 1] += 1
        support_pairs += sum(count > 0 for count in counts)
        common_divisor = 0
        for count in counts:
            common_divisor = math.gcd(common_divisor, count)
        if common_divisor == 1:
            primitive_by_total[total - 1] += 1
        digest.update(struct.pack(">IB", ordinal, total))
        digest.update(bytes(counts))
    require(len(seen) == EXPECTED_TABLE_COUNT, "bounded corpus cardinality drift")
    require(tuple(tables_by_total) == EXPECTED_TABLES_BY_TOTAL, "per-total table counts drift")
    require(tuple(primitive_by_total) == EXPECTED_PRIMITIVE_BY_TOTAL, "primitive-law counts drift")
    require(sum(primitive_by_total) == EXPECTED_PRIMITIVE_COUNT, "primitive-law total drift")
    require(support_pairs == EXPECTED_SUPPORT_PAIR_COUNT, "supported table-realization count drift")
    require(
        sum(EXPECTED_TABLES_BY_TOTAL) == math.comb(21, 16) - 1 == EXPECTED_TABLE_COUNT,
        "stars-and-bars hockey-stick identity drift",
    )
    return digest.hexdigest(), tuple(tables_by_total), tuple(primitive_by_total), support_pairs


def decode_cell(cell: int) -> tuple[int, int]:
    """Return (source_code, target), with source bits 0..2 = S1..S3."""

    require(0 <= cell < CELL_COUNT, "cell index outside binary table")
    source_code = ((cell >> 3) & 1) | (((cell >> 2) & 1) << 1) | (((cell >> 1) & 1) << 2)
    target = cell & 1
    return source_code, target


def canonical_cell_index(s1: int, s2: int, s3: int, target: int) -> int:
    """Canonical binary-table index ``8*s1 + 4*s2 + 2*s3 + target``."""

    require(s1 in (0, 1) and s2 in (0, 1) and s3 in (0, 1), "source bit outside cell domain")
    require(target in (0, 1), "target bit outside cell domain")
    return 8 * s1 + 4 * s2 + 2 * s3 + target


def encode_cell(source_code: int, target: int) -> int:
    require(0 <= source_code < 8 and target in (0, 1), "binary state outside cell domain")
    return canonical_cell_index(
        source_code & 1,
        (source_code >> 1) & 1,
        (source_code >> 2) & 1,
        target,
    )


@dataclass(frozen=True)
class Marginals:
    total: int
    target: tuple[int, int]
    # [target_or_2_for_all][mask][keyed source_code]
    cylinders: tuple[tuple[tuple[int, ...], ...], ...]


def build_cylinder_marginals(counts: Sequence[int]) -> Marginals:
    require(len(counts) == CELL_COUNT, "count table has wrong cell count")
    total = sum(counts)
    require(1 <= total <= MAX_TOTAL, "count table leaves bounded total")
    by_source_target = [[0, 0] for _ in range(8)]
    for cell, count in enumerate(counts):
        source_code, target = decode_cell(cell)
        by_source_target[source_code][target] += count
    target_masses = tuple(sum(by_source_target[source][target] for source in range(8)) for target in (0, 1))
    targets: list[tuple[tuple[int, ...], ...]] = []
    for target_selector in (0, 1, 2):
        masks: list[tuple[int, ...]] = [tuple([0] * 8)]
        for mask in range(1, 8):
            values: list[int] = []
            for keyed_source in range(8):
                mass = 0
                for candidate_source in range(8):
                    if (candidate_source & mask) != (keyed_source & mask):
                        continue
                    if target_selector == 2:
                        mass += by_source_target[candidate_source][0] + by_source_target[candidate_source][1]
                    else:
                        mass += by_source_target[candidate_source][target_selector]
                values.append(mass)
            masks.append(tuple(values))
        targets.append(tuple(masks))
    return Marginals(total=total, target=(target_masses[0], target_masses[1]), cylinders=tuple(targets))


def union_mass_by_inclusion_exclusion(
    marginals: Marginals,
    node: Sequence[int],
    keyed_source: int,
    target: int | None,
) -> int:
    """Mass of an MGW OR-of-AND cylinders using inclusion-exclusion."""

    require(bool(node) and tuple(node) in NODE_INDEX, "unknown antichain node")
    target_selector = 2 if target is None else target
    total = 0
    for selected in range(1, 1 << len(node)):
        intersection_mask = 0
        subset_size = 0
        for branch_index, branch_mask in enumerate(node):
            if selected & (1 << branch_index):
                intersection_mask |= branch_mask
                subset_size += 1
        cylinder_mass = marginals.cylinders[target_selector][intersection_mask][keyed_source]
        if subset_size % 2 == 1:
            total += cylinder_mass
        else:
            total -= cylinder_mass
    return total


@dataclass(frozen=True)
class TableProducts:
    cumulative: tuple[tuple[ExponentVector, ...], ...]
    atom: tuple[tuple[ExponentVector, ...], ...]

    def flattened(self) -> tuple[ExponentVector, ...]:
        return tuple(
            value
            for family in (self.cumulative, self.atom)
            for component in family
            for value in component
        )


def recursive_atoms(cumulative: Sequence[ExponentVector]) -> tuple[ExponentVector, ...]:
    require(len(cumulative) == len(NODES), "cumulative vector has wrong length")
    atoms: list[ExponentVector | None] = [None] * len(NODES)
    for node_index in TOPOLOGICAL_NODE_ORDER:
        value = cumulative[node_index]
        for lower in STRICT_LOWERS[node_index]:
            lower_value = atoms[lower]
            if lower_value is None:
                raise VerificationError("atom recursion visited an unfinished lower node")
            value = sub(value, lower_value)
        atoms[node_index] = value
    result = tuple(value for value in atoms if value is not None)
    require(len(result) == len(NODES), "atom recursion omitted a node")
    return result


def compute_table_products(counts: Sequence[int]) -> TableProducts:
    marginals = build_cylinder_marginals(counts)
    plus = [ZERO_EXPONENTS for _ in NODES]
    minus = [ZERO_EXPONENTS for _ in NODES]
    for cell, count in enumerate(counts):
        if count == 0:
            continue
        source_code, target_value = decode_cell(cell)
        target_mass = marginals.target[target_value]
        require(0 < count <= target_mass <= marginals.total, "invalid positive-support target mass")
        for node_index, node in enumerate(NODES):
            union_mass = union_mass_by_inclusion_exclusion(marginals, node, source_code, None)
            joint_mass = union_mass_by_inclusion_exclusion(marginals, node, source_code, target_value)
            require(
                0 < count <= joint_mass <= union_mass <= marginals.total,
                "MGW union/joint event mass bounds failed",
            )
            require(joint_mass <= target_mass, "MGW joint event is not inside target event")
            plus[node_index] = add(
                plus[node_index],
                scale(exponent_ratio(marginals.total, union_mass), count),
            )
            minus[node_index] = add(
                minus[node_index],
                scale(exponent_ratio(target_mass, joint_mass), count),
            )
    net = tuple(sub(plus[index], minus[index]) for index in range(len(NODES)))
    cumulative = (tuple(plus), tuple(minus), net)
    atoms = tuple(recursive_atoms(component) for component in cumulative)
    for node_index in range(len(NODES)):
        require(atoms[2][node_index] == sub(atoms[0][node_index], atoms[1][node_index]), "atom net-lane mismatch")
    return TableProducts(cumulative=cumulative, atom=atoms)


def reconstruct_cumulative(atoms: Sequence[ExponentVector], node_index: int) -> ExponentVector:
    value = ZERO_EXPONENTS
    for lower_index, is_lower in enumerate(ORDER[node_index]):
        if is_lower:
            value = add(value, atoms[lower_index])
    return value


def transform_source_permutation(counts: Sequence[int], permutation: Sequence[int]) -> tuple[int, ...]:
    """Map old source index i to new source index permutation[i]."""

    require(tuple(sorted(permutation)) == (0, 1, 2), "invalid source permutation")
    transformed = [0] * CELL_COUNT
    for cell, count in enumerate(counts):
        source_code, target = decode_cell(cell)
        new_source = 0
        for old_index, new_index in enumerate(permutation):
            if source_code & (1 << old_index):
                new_source |= 1 << new_index
        transformed[encode_cell(new_source, target)] += count
    return tuple(transformed)


def transform_mask(mask: int, permutation: Sequence[int]) -> int:
    transformed = 0
    for old_index, new_index in enumerate(permutation):
        if mask & (1 << old_index):
            transformed |= 1 << new_index
    return transformed


def source_permutation_expression_map(permutation: Sequence[int]) -> tuple[int, ...]:
    node_map: list[int] = []
    for node in NODES:
        transformed_node = tuple(sorted(transform_mask(mask, permutation) for mask in node))
        require(transformed_node in NODE_INDEX, "source permutation left antichain carrier")
        node_map.append(NODE_INDEX[transformed_node])
    expression_map: list[int] = []
    for block_index in range(len(BLOCKS)):
        base = block_index * len(NODES)
        expression_map.extend(base + mapped for mapped in node_map)
    require(
        tuple(sorted(expression_map)) == tuple(range(EXPECTED_AUDIT_EXPRESSION_COUNT)),
        "audit-expression permutation is not bijective",
    )
    return tuple(expression_map)


def transform_binary_relabel(counts: Sequence[int], flip_mask: int) -> tuple[int, ...]:
    """Independently flip any of S1,S2,S3,T; low flip bits follow that order."""

    require(0 <= flip_mask < 16, "binary relabel mask outside domain")
    transformed = [0] * CELL_COUNT
    for cell, count in enumerate(counts):
        source_code, target = decode_cell(cell)
        source_code ^= flip_mask & 0b111
        target ^= (flip_mask >> 3) & 1
        transformed[encode_cell(source_code, target)] += count
    return tuple(transformed)


def append_products(cache: array[int], products: Sequence[ExponentVector]) -> None:
    require(len(products) == EXPECTED_AUDIT_EXPRESSION_COUNT, "table does not have 108 audit-expression products")
    for value in products:
        for exponent in value:
            require(-(1 << 15) <= exponent < (1 << 15), "prime exponent exceeds signed-i16 cache")
            cache.append(exponent)


def cache_offset(ordinal: int, expression_index: int = 0) -> int:
    return (ordinal * EXPECTED_AUDIT_EXPRESSION_COUNT + expression_index) * len(PRIMES)


def cached_product(cache: array[int], ordinal: int, expression_index: int) -> ExponentVector:
    offset = cache_offset(ordinal, expression_index)
    return (cache[offset], cache[offset + 1], cache[offset + 2])


def begin_table_bound_frame(
    digest: "hashlib._Hash",
    ordinal: int,
    counts: Sequence[int],
) -> None:
    """Bind one table before its 108 keyed scalar expression records."""

    require(0 <= ordinal < EXPECTED_TABLE_COUNT, "table frame ordinal outside bounded corpus")
    require(len(counts) == CELL_COUNT, "table frame does not contain exactly 16 counts")
    require(
        all(isinstance(count, int) and not isinstance(count, bool) and 0 <= count <= 255 for count in counts),
        "table frame count is not a u8",
    )
    require(rank_count_vector(counts) == ordinal, "table frame ordinal/count binding mismatch")
    # Iteration order is the byte order of counts[0]..counts[15], where the
    # index is exactly 8*s1 + 4*s2 + 2*s3 + t.
    digest.update(struct.pack(">I", ordinal))
    digest.update(bytes(counts))


def append_table_bound_expression_record(
    digest: "hashlib._Hash",
    expression_index: int,
    value: ExponentVector,
    sign: int,
) -> None:
    require(0 <= expression_index < EXPECTED_AUDIT_EXPRESSION_COUNT, "audit-expression index outside registry")
    require(sign in (-1, 0, 1), "audit-expression log-sign/comparison code outside {-1,0,1}")
    key = AUDIT_EXPRESSION_REGISTRY[expression_index].encode("ascii")
    digest.update(struct.pack(">BH", expression_index, len(key)))
    digest.update(key)
    digest.update(struct.pack(">qqqb", value[0], value[1], value[2], sign))


def update_route_native_result_digest(
    digest: "hashlib._Hash",
    ordinal: int,
    expression_index: int,
    value: ExponentVector,
    sign: int,
) -> None:
    """Retain the pre-v2 route-native stream separately for continuity only."""

    key = AUDIT_EXPRESSION_REGISTRY[expression_index].encode("ascii")
    digest.update(struct.pack(">IBH", ordinal, expression_index, len(key)))
    digest.update(key)
    digest.update(struct.pack(">qqqb", value[0], value[1], value[2], sign))


def framing_probe_digest() -> str:
    """Exercise table identity/order and keyed record framing with real tables."""

    digest = hashlib.sha256(TABLE_BOUND_AUDIT_DOMAIN)
    fixtures = (
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 2),
        (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    )
    for counts in fixtures:
        ordinal = rank_count_vector(counts)
        begin_table_bound_frame(digest, ordinal, counts)
        flattened = compute_table_products(counts).flattened()
        require(len(flattened) == EXPECTED_AUDIT_EXPRESSION_COUNT, "framing probe lost an expression")
        for expression_index, value in enumerate(flattened):
            append_table_bound_expression_record(
                digest,
                expression_index,
                value,
                compare_product_with_one(value),
            )
    return digest.hexdigest()


def probe_digest() -> str:
    """Small, literal-bound semantic probe used by process-level mutation tests."""

    # Nonuniform weights, multiple source patterns, both target values, and a
    # replicated table ensure that every event/product lane is exercised.
    fixtures = (
        (2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0),
        (1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5),
    )
    digest = hashlib.sha256(b"pid-rs.sxpid3.independent.probe.v1\0")
    for fixture_index, counts in enumerate(fixtures):
        products = compute_table_products(counts)
        flattened = products.flattened()
        require(len(flattened) == EXPECTED_AUDIT_EXPRESSION_COUNT, "probe table lost an audit expression")
        for expression_index, value in enumerate(flattened):
            sign = compare_product_with_one(value)
            update_route_native_result_digest(digest, fixture_index, expression_index, value, sign)
            if expression_index >= 54:
                component = (expression_index - 54) // 18
                node = (expression_index - 54) % 18
                require(
                    reconstruct_cumulative(products.atom[component], node) == products.cumulative[component][node],
                    "probe zeta reconstruction failed",
                )
    # One nontrivial source permutation and a full bit complement are semantic
    # rather than array-position checks.
    source_permutation = (1, 2, 0)
    expression_map = source_permutation_expression_map(source_permutation)
    sentinel = [0] * CELL_COUNT
    sentinel[encode_cell(0b001, 0)] = 1
    permuted_sentinel = transform_source_permutation(tuple(sentinel), source_permutation)
    require(
        permuted_sentinel[encode_cell(0b010, 0)] == 1 and sum(permuted_sentinel) == 1,
        "source-permutation direction sentinel failed",
    )
    original = compute_table_products(fixtures[1]).flattened()
    transformed = compute_table_products(transform_source_permutation(fixtures[1], source_permutation)).flattened()
    for expression_index, mapped in enumerate(expression_map):
        require(original[expression_index] == transformed[mapped], "probe source-permutation equivariance failed")
    relabeled = compute_table_products(transform_binary_relabel(fixtures[2], 0b1111)).flattened()
    require(original != relabeled, "probe fixtures unexpectedly alias")
    require(
        compute_table_products(fixtures[2]).flattened() == relabeled,
        "probe binary-relabel invariance failed",
    )
    target_sentinel = [0] * CELL_COUNT
    target_sentinel[encode_cell(0b000, 0)] = 1
    flipped_target_sentinel = transform_binary_relabel(tuple(target_sentinel), 0b1000)
    require(
        flipped_target_sentinel[encode_cell(0b000, 1)] == 1 and sum(flipped_target_sentinel) == 1,
        "target-relabel direction sentinel failed",
    )
    replication_base = [0] * CELL_COUNT
    replication_base[encode_cell(0b000, 0)] = 1
    replication_base[encode_cell(0b111, 1)] = 1
    base = compute_table_products(tuple(replication_base)).flattened()
    replicated = compute_table_products(tuple(2 * count for count in replication_base)).flattened()
    require(tuple(scale(value, 2) for value in base) == replicated, "probe replication power law failed")
    return digest.hexdigest()


def verify_pins(corpus_sha256: str, probe_sha256: str, framing_sha256: str) -> None:
    lattice_sha256 = digest_lattice()
    # Frozen legacy byte-domain label retained solely to preserve the pre-v2
    # registry digest anchor; "coordinate-registry" is not current terminology.
    expression_registry_sha256 = sha256_lines(
        AUDIT_EXPRESSION_REGISTRY,
        b"pid-rs.sxpid3.independent.coordinate-registry.v1\0",
    )
    require(corpus_sha256 == EXPECTED_CORPUS_SHA256, f"corpus digest drift: {corpus_sha256}")
    require(lattice_sha256 == EXPECTED_LATTICE_SHA256, f"lattice digest drift: {lattice_sha256}")
    require(
        expression_registry_sha256 == EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256,
        f"audit-expression registry digest drift: {expression_registry_sha256}",
    )
    require(probe_sha256 == EXPECTED_PROBE_SHA256, f"semantic probe digest drift: {probe_sha256}")
    require(
        framing_sha256 == EXPECTED_FRAMING_PROBE_SHA256,
        f"table-bound framing probe digest drift: {framing_sha256}",
    )


def run_probe() -> dict[str, object]:
    corpus_sha256, tables_by_total, primitive_by_total, support_pairs = digest_corpus()
    semantic_probe_sha256 = probe_digest()
    framing_sha256 = framing_probe_digest()
    verify_pins(corpus_sha256, semantic_probe_sha256, framing_sha256)
    return {
        "schema": "pid-rs.sxpid3-all108-independent-probe.v2",
        "status": "GO",
        "corpus_sha256": corpus_sha256,
        "lattice_sha256": digest_lattice(),
        "audit_expression_registry_sha256": EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256,
        "semantic_probe_sha256": semantic_probe_sha256,
        "table_bound_framing_probe_sha256": framing_sha256,
        "tables_by_total": list(tables_by_total),
        "primitive_laws_by_total": list(primitive_by_total),
        "supported_table_realization_pairs": support_pairs,
    }


def run_full() -> dict[str, object]:
    corpus_sha256, tables_by_total, primitive_by_total, support_pairs = digest_corpus()
    semantic_probe_sha256 = probe_digest()
    framing_sha256 = framing_probe_digest()
    verify_pins(corpus_sha256, semantic_probe_sha256, framing_sha256)

    table_bound_digest = hashlib.sha256(TABLE_BOUND_AUDIT_DOMAIN)
    route_native_digest = hashlib.sha256(b"pid-rs.sxpid3.independent.all108-results.v1\0")
    cache = array("h")
    bounded_sign_counts_by_audit_expression_block = {
        f"{kind}.{component}": {"negative": 0, "positive": 0, "zero": 0}
        for kind, component in BLOCKS
    }
    reconstruction_checks = 0
    cumulative_net_checks = 0
    atom_net_checks = 0
    component_nonnegativity_checks = 0
    first_negative_log_value_witnesses: dict[str, dict[str, object]] = {}

    for ordinal, counts in iter_count_vectors():
        products = compute_table_products(counts)
        flattened = products.flattened()
        append_products(cache, flattened)
        begin_table_bound_frame(table_bound_digest, ordinal, counts)
        for node_index in range(len(NODES)):
            require(
                products.cumulative[2][node_index]
                == sub(products.cumulative[0][node_index], products.cumulative[1][node_index]),
                "cumulative exact net identity failed",
            )
            cumulative_net_checks += 1
            require(
                products.atom[2][node_index]
                == sub(products.atom[0][node_index], products.atom[1][node_index]),
                "atom exact net identity failed",
            )
            atom_net_checks += 1
            for component_index in range(len(COMPONENTS)):
                require(
                    reconstruct_cumulative(products.atom[component_index], node_index)
                    == products.cumulative[component_index][node_index],
                    "recursive atom zeta reconstruction failed",
                )
                reconstruction_checks += 1
        for expression_index, value in enumerate(flattened):
            sign = compare_product_with_one(value)
            block_index = expression_index // len(NODES)
            kind, component = BLOCKS[block_index]
            bounded_sign_counts_by_audit_expression_block[f"{kind}.{component}"][sign_name(sign)] += 1
            append_table_bound_expression_record(table_bound_digest, expression_index, value, sign)
            update_route_native_result_digest(route_native_digest, ordinal, expression_index, value, sign)
            if sign < 0 and component == "net" and kind not in first_negative_log_value_witnesses:
                numerator, denominator = numerator_denominator(value)
                node_index = expression_index % len(NODES)
                decoded_support = []
                for support_cell, support_count in enumerate(counts):
                    if support_count == 0:
                        continue
                    support_source, support_target = decode_cell(support_cell)
                    decoded_support.append(
                        {
                            "cell": support_cell,
                            "s1": support_source & 1,
                            "s2": (support_source >> 1) & 1,
                            "s3": (support_source >> 2) & 1,
                            "t": support_target,
                            "count": support_count,
                        }
                    )
                first_negative_log_value_witnesses[kind] = {
                    "table_ordinal": ordinal,
                    "total_count": sum(counts),
                    "counts_cell_0_through_15": list(counts),
                    "decoded_positive_support": decoded_support,
                    "audit_expression_key": AUDIT_EXPRESSION_REGISTRY[expression_index],
                    "antichain_masks": [f"{mask:02x}" for mask in NODES[node_index]],
                    "antichain_source_collections": [
                        [f"S{source_index + 1}" for source_index in range(SOURCE_COUNT) if mask & (1 << source_index)]
                        for mask in NODES[node_index]
                    ],
                    "prime_exponents_2_3_5": list(value),
                    "exact_product_Q_is_strictly_positive": True,
                    "witnessed_comparison": "Q<1",
                    "exact_product_numerator": str(numerator),
                    "exact_product_denominator": str(denominator),
                    "averaged_value_nats": f"(1/{sum(counts)}) * ln({numerator}/{denominator}) < 0",
                    "witness_scope": "bounded empirical count-table witness, not a population theorem",
                }
            if component in ("informative", "misinformative"):
                require(sign >= 0, f"negative {kind} {component} audit expression in bounded corpus")
                component_nonnegativity_checks += 1

    require(
        len(cache) == EXPECTED_AUDIT_EXPRESSION_VERDICTS * len(PRIMES),
        "audit-expression product cache length drift",
    )
    require(
        bounded_sign_counts_by_audit_expression_block
        == EXPECTED_BOUNDED_SIGN_COUNTS_BY_AUDIT_EXPRESSION_BLOCK,
        "bounded sign counts by audit-expression block drift",
    )
    require(reconstruction_checks == EXPECTED_TABLE_COUNT * 54, "zeta reconstruction count drift")
    require(cumulative_net_checks == EXPECTED_TABLE_COUNT * 18, "cumulative net check count drift")
    require(atom_net_checks == EXPECTED_TABLE_COUNT * 18, "atom net check count drift")
    require(component_nonnegativity_checks == EXPECTED_TABLE_COUNT * 72, "component nonnegativity count drift")
    require(
        set(first_negative_log_value_witnesses) == {"cumulative", "atom"},
        "missing negative signed-net log-value witness",
    )

    permutations = tuple(itertools.permutations(range(SOURCE_COUNT)))
    permutation_maps = {permutation: source_permutation_expression_map(permutation) for permutation in permutations}
    source_permutation_checks = 0
    binary_relabel_checks = 0
    replication_checks = 0
    replication_pairs = 0

    for ordinal, counts in iter_count_vectors():
        for permutation in permutations:
            transformed_counts = transform_source_permutation(counts, permutation)
            transformed_ordinal = rank_count_vector(transformed_counts)
            for expression_index, mapped_expression in enumerate(permutation_maps[permutation]):
                require(
                    cached_product(cache, ordinal, expression_index)
                    == cached_product(cache, transformed_ordinal, mapped_expression),
                    "exhaustive source-permutation equivariance failed",
                )
                source_permutation_checks += 1
        original_start = cache_offset(ordinal)
        original_stop = original_start + EXPECTED_AUDIT_EXPRESSION_COUNT * len(PRIMES)
        for flip_mask in range(16):
            transformed_counts = transform_binary_relabel(counts, flip_mask)
            transformed_ordinal = rank_count_vector(transformed_counts)
            transformed_start = cache_offset(transformed_ordinal)
            transformed_stop = transformed_start + EXPECTED_AUDIT_EXPRESSION_COUNT * len(PRIMES)
            require(
                cache[original_start:original_stop] == cache[transformed_start:transformed_stop],
                "exhaustive binary category-relabel invariance failed",
            )
            binary_relabel_checks += EXPECTED_AUDIT_EXPRESSION_COUNT

        common_divisor = 0
        for count in counts:
            common_divisor = math.gcd(common_divisor, count)
        total = sum(counts)
        if common_divisor == 1:
            for multiplier in range(2, MAX_TOTAL // total + 1):
                replicated_counts = tuple(multiplier * count for count in counts)
                replicated_ordinal = rank_count_vector(replicated_counts)
                for expression_index in range(EXPECTED_AUDIT_EXPRESSION_COUNT):
                    require(
                        cached_product(cache, replicated_ordinal, expression_index)
                        == scale(cached_product(cache, ordinal, expression_index), multiplier),
                        "exhaustive admitted replication power law failed",
                    )
                    replication_checks += 1
                replication_pairs += 1

    require(source_permutation_checks == EXPECTED_TABLE_COUNT * 6 * 108, "source permutation check count drift")
    require(binary_relabel_checks == EXPECTED_TABLE_COUNT * 16 * 108, "binary relabel check count drift")
    require(replication_pairs == 184, "primitive replication-pair count drift")
    require(replication_checks == 19_872, "replication audit-expression check count drift")

    route_native_sha256 = route_native_digest.hexdigest()
    table_bound_sha256 = table_bound_digest.hexdigest()
    require(
        route_native_sha256 == EXPECTED_ROUTE_NATIVE_RESULT_SHA256,
        f"route-native result digest drift: {route_native_sha256}",
    )
    require(
        table_bound_sha256 == EXPECTED_TABLE_BOUND_RESULT_SHA256,
        f"table-bound all-expression result digest drift: {table_bound_sha256}",
    )
    source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "pid-rs.sxpid3-all108-independent-result.v2",
        "status": "GO",
        "census_interpretation": CENSUS_INTERPRETATION,
        "sign_semantics": SIGN_SEMANTICS,
        "method_provenance_and_novelty": METHOD_PROVENANCE_AND_NOVELTY,
        "route_assurance": ROUTE_ASSURANCE,
        "scope": {
            "sources": 3,
            "source_alphabet": [0, 1],
            "target_alphabet": [0, 1],
            "total_count_min": 1,
            "total_count_max": 5,
            "labeled_count_tables": EXPECTED_TABLE_COUNT,
            "primitive_rational_laws": EXPECTED_PRIMITIVE_COUNT,
            "nonprimitive_rescaled_count_vectors": EXPECTED_TABLE_COUNT - EXPECTED_PRIMITIVE_COUNT,
            "includes_nonprimitive_rescalings": True,
            "keyed_scalar_audit_expressions_per_table": EXPECTED_AUDIT_EXPRESSION_COUNT,
            "audit_expression_evaluations": EXPECTED_AUDIT_EXPRESSION_VERDICTS,
            "audit_expression_factorization": {
                "antichain_keys": 18,
                "representation_stage_count": 2,
                "representation_stages": [
                    {"name": "cumulative values", "audit_expressions_per_component": 18},
                    {"name": "Möbius atoms", "audit_expressions_per_component": 18},
                ],
                "components": ["informative", "misinformative", "net"],
                "not_claimed": ["108 lattice nodes", "108 atoms", "108 independent degrees of freedom"],
            },
        },
        "construction": {
            "corpus": "lexicographic stars-and-bars rank/unrank",
            "event_mass": "cylinder marginals plus inclusion-exclusion",
            "lattice": "semantic nonempty antichains and redundancy order",
            "atom_recovery": "recursive strict-lower poset subtraction",
            "exact_positive_product_encoding": "prime-exponent vectors with signed integer exponents over [2,3,5]",
            "audit_expression_registry": AUDIT_EXPRESSION_REVISION,
            "table_bound_stream": {
                "version": 2,
                "domain_ascii": "pid-rs.sxpid3.table-bound-audit-expressions.v2\\0",
                "neutrality_scope": "route_and_representation_neutral_within_v2",
                "table_frame": "u32 big-endian ordinal followed by 16 canonical u8 counts",
                "cell_order": CELL_INDEX_FORMULA,
                "expression_record": "u8 index, u16 key length, ASCII key, three i64 exponents for exact positive Q, i8 log_sign/comparison-to-one",
            },
        },
        "counts": {
            "tables_by_total": list(tables_by_total),
            "primitive_laws_by_total": list(primitive_by_total),
            "supported_table_realization_pairs": support_pairs,
            "cumulative_net_identities": cumulative_net_checks,
            "atom_net_identities": atom_net_checks,
            "zeta_reconstructions": reconstruction_checks,
            "component_nonnegativity_checks": component_nonnegativity_checks,
            "source_permutation_audit_expression_checks": source_permutation_checks,
            "binary_relabel_audit_expression_checks": binary_relabel_checks,
            "primitive_replication_pairs": replication_pairs,
            "replication_audit_expression_checks": replication_checks,
        },
        "bounded_sign_counts_by_audit_expression_block": bounded_sign_counts_by_audit_expression_block,
        "first_negative_log_value_witnesses": first_negative_log_value_witnesses,
        "digests": {
            "checker_source_sha256": source_sha256,
            "corpus_sha256": corpus_sha256,
            "lattice_sha256": digest_lattice(),
            "audit_expression_registry_sha256": EXPECTED_AUDIT_EXPRESSION_REGISTRY_SHA256,
            "semantic_probe_sha256": semantic_probe_sha256,
            "table_bound_framing_probe_sha256": framing_sha256,
            "table_bound_all_expression_result_sha256": table_bound_sha256,
            "route_native_v1_result_sha256": route_native_sha256,
        },
        "positive_results": [
            "All 108 keyed scalar audit expressions (18 antichains x 2 representation stages--cumulative values and Möbius atoms--x 3 components) were present exactly once per table.",
            "Every cumulative reconstructed from recursively derived atom products on the bounded corpus.",
            "All six source permutations and all 16 choices of independently flipping the binary labels of S1,S2,S3,T were equivariant on every table.",
            "All admitted primitive-table replications obeyed the exact product power law.",
            "No informative or misinformative cumulative or atom was negative in the bounded corpus.",
        ],
        "negative_results": [
            "Signed-net negativity occurs in 29,496 cumulative and 31,284 atom instances in the bounded corpus and therefore must not be clamped.",
            "The finite search does not prove component nonnegativity, invariance, or correctness outside this domain.",
            "No binary64 or other floating-point correspondence, logarithm-magnitude certificate, or Rust refinement is established.",
            "This route does not establish population validity or scientific novelty.",
            "This standalone lane does not bind, import, or execute the primary source; a later source-bound paired-execution closed receipt is required.",
        ],
        "shared_semantic_cuts": [
            "The standalone lane depends on a human transcription intended to represent MGW equations (6), (13), (14a), (15a), (15b), and (17); this is not a paper-correspondence proof.",
            "Equation (13) supplies the pointwise zeta/Möbius relation; equation (17) averages local values with empirical joint weights; finite linear averaging commutes with the finite zeta/Möbius combination.",
            "The standalone lane uses the declared binary cell/mask convention, empirical count weighting, natural-log specialization, redundancy-order meaning, N<=5 domain, and prospective mask-lex 18-node/108-key audit registry.",
            "The route- and representation-neutral-within-v2 stream binds each table ordinal to all 16 counts in cell_index=8*s1+4*s2+2*s3+t order before its 108 full expression keys, indices, exact positive-product exponent vectors, and log_sign/comparison-to-one codes.",
            "The expected bounded sign counts and table-bound digest are embedded external comparison pins, not independently obtained primary-route evidence.",
            "The standalone lane neither binds nor imports nor executes the primary source, so a matching embedded digest does not establish paired source/execution agreement.",
            "The construction describes implementation-disjoint design choices under shared semantics; a later source-bound paired-execution closed receipt is required.",
            "Described implementation disjointness does not close paper-to-code correspondence, scientific validation, artifact authenticity, external custody, or arbitrary-domain theorem obligations.",
        ],
        "evidence_boundary": (
            "Exhaustive bounded computational evidence for binary S1,S2,S3,T and 1<=N<=5 only; "
            "not an arbitrary-alphabet/count theorem, paper-correspondence proof, probability result, paired-source receipt, or accepted certificate."
        ),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="run the bounded semantic/mutation probe only")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = run_probe() if args.probe else run_full()
    except (VerificationError, ValueError, OverflowError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, separators=(",", ": ")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
