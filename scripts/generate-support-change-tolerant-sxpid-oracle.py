#!/usr/bin/env python3
"""Generate bounded support-change-tolerant categorical SxPID evidence.

Each evidence case fixes one finite row table and a full redundancy lattice. The
table embeds in the complete Cartesian product of its coordinate alphabets; product
cells not listed in the table have implicit zero mass under both compared laws.
It permits listed cells to enter or leave support without assuming a positive
support-mass floor. The generator is implementation-separated from pid-rs: it does
not import the Rust implementation. It uses exact ``Fraction`` arithmetic for
probabilities and lattice coefficients, and ``Decimal`` only to evaluate natural
logarithms. Decimal values in the resulting fixture are comparison references, not
certified real-number enclosures or authorship-independent review.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = (
    ROOT
    / "crates/pid-core/tests/fixtures/support_change_tolerant_sxpid_oracle.json"
)
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SCHEMA = "pid-rs/support-change-tolerant-sxpid-oracle"
SCHEMA_REVISION = 1
DECIMAL_PRECISION = 160
DECIMAL_REFERENCE_DIGITS = 80
TOLERANCE = Decimal("1e-130")
REFERENCE_TOLERANCE = Decimal("1e-75")
SEED = 0x53585049445F4652

Rational = Fraction
Antichain = tuple[int, ...]
Realization = tuple[int, ...]
Neighborhoods = tuple[frozenset[int], ...]


class OracleError(RuntimeError):
    """The standalone construction or committed fixture is inconsistent."""


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


def decimal(value: Rational | int) -> Decimal:
    if isinstance(value, int):
        return Decimal(value)
    return Decimal(value.numerator) / Decimal(value.denominator)


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise OracleError("oracle produced a non-finite Decimal")
    if value == 0:
        return "0"
    return format(+value, f".{DECIMAL_REFERENCE_DIGITS}g")


def fraction_text(value: Rational) -> str:
    return f"{value.numerator}/{value.denominator}"


def xlogx(value: Rational) -> Decimal:
    if value == 0:
        return Decimal(0)
    return -decimal(value) * decimal(value).ln()


def subprobability_entropy(values: Sequence[Rational]) -> Decimal:
    return sum((xlogx(value) for value in values), Decimal(0))


def binary_entropy(value: Rational) -> Decimal:
    return xlogx(value) + xlogx(1 - value)


def total_variation(
    left: Sequence[Rational], right: Sequence[Rational]
) -> Rational:
    return sum(
        (abs(x - y) for x, y in zip(left, right, strict=True)),
        Rational(0),
    ) / 2


def common_residuals(
    left: Sequence[Rational], right: Sequence[Rational]
) -> tuple[
    tuple[Rational, ...],
    tuple[Rational, ...],
    tuple[Rational, ...],
    Rational,
]:
    common = tuple(min(x, y) for x, y in zip(left, right, strict=True))
    left_residual = tuple(
        x - overlap for x, overlap in zip(left, common, strict=True)
    )
    right_residual = tuple(
        y - overlap for y, overlap in zip(right, common, strict=True)
    )
    eta = sum(left_residual, Rational(0))
    if eta != sum(right_residual, Rational(0)):
        raise OracleError("left and right residual masses differ")
    if eta != total_variation(left, right):
        raise OracleError("residual mass does not equal total variation")
    if sum(common, Rational(0)) != 1 - eta:
        raise OracleError("common mass does not equal one minus total variation")
    return common, left_residual, right_residual, eta


def ell(eta: Rational) -> Decimal:
    retained = 1 - eta
    return Decimal(0) if retained == 0 else xlogx(retained)


def gamma_union(branch_count: int, eta: Rational) -> Decimal:
    retained = 1 - eta
    if retained == 0:
        return Decimal(0)
    return decimal(retained) * (
        Decimal(1)
        + Decimal(branch_count) * decimal(eta) / decimal(retained)
    ).ln()


def fannes(alphabet_size: int, eta: Rational) -> Decimal:
    if alphabet_size < 2:
        raise OracleError("Fannes alphabet must contain at least two points")
    if eta > Rational(alphabet_size - 1, alphabet_size):
        return Decimal(alphabet_size).ln()
    return binary_entropy(eta) + decimal(eta) * Decimal(alphabet_size - 1).ln()


def antichain_leq(lower: Antichain, upper: Antichain) -> bool:
    """Return the Williams--Beer redundancy-lattice order relation."""

    return all(
        any(lower_mask & upper_mask == lower_mask for lower_mask in lower)
        for upper_mask in upper
    )


@lru_cache(maxsize=None)
def antichains(source_count: int) -> tuple[Antichain, ...]:
    masks = tuple(range(1, 1 << source_count))
    result: list[Antichain] = []
    for size in range(1, len(masks) + 1):
        for candidate in combinations(masks, size):
            if all(
                left & right not in (left, right)
                for left, right in combinations(candidate, 2)
            ):
                result.append(candidate)
    ordered = tuple(result)
    if ordered != tuple(sorted(ordered, key=lambda node: (len(node), node))):
        raise OracleError("antichain enumeration is not size-then-lexicographic")
    return ordered


@lru_cache(maxsize=None)
def order_data(
    nodes: tuple[Antichain, ...],
) -> tuple[tuple[int, ...], tuple[tuple[int, ...], ...]]:
    relation = tuple(
        tuple(antichain_leq(lower, upper) for upper in nodes)
        for lower in nodes
    )
    predecessors = tuple(
        tuple(
            lower
            for lower in range(len(nodes))
            if lower != upper and relation[lower][upper]
        )
        for upper in range(len(nodes))
    )
    remaining = set(range(len(nodes)))
    ordered: list[int] = []
    while remaining:
        ready = sorted(
            node for node in remaining if not (set(predecessors[node]) & remaining)
        )
        if not ready:
            raise OracleError("redundancy lattice contains a cycle")
        ordered.extend(ready)
        remaining.difference_update(ready)
    return tuple(ordered), predecessors


def mobius_invert(
    nodes: Sequence[Antichain], cumulative: dict[Antichain, Decimal]
) -> dict[Antichain, Decimal]:
    node_tuple = tuple(nodes)
    matrix = mobius_matrix(node_tuple)
    values = tuple(cumulative[node] for node in node_tuple)
    atoms = {
        node: sum(
            (
                Decimal(coefficient) * value
                for coefficient, value in zip(row, values, strict=True)
            ),
            Decimal(0),
        )
        for node, row in zip(node_tuple, matrix, strict=True)
    }
    _ordered, predecessors = order_data(node_tuple)
    for node_index, node in enumerate(node_tuple):
        reconstructed = atoms[node] + sum(
            (atoms[node_tuple[lower]] for lower in predecessors[node_index]),
            Decimal(0),
        )
        if abs(reconstructed - cumulative[node]) > TOLERANCE:
            raise OracleError("Mobius inversion did not reconstruct a cumulative")
    return atoms


@lru_cache(maxsize=None)
def mobius_matrix(
    nodes: tuple[Antichain, ...],
) -> tuple[tuple[int, ...], ...]:
    rows = [[0 for _ in nodes] for _ in nodes]
    ordered, predecessors = order_data(nodes)
    for row_index in ordered:
        rows[row_index][row_index] = 1
        for lower in predecessors[row_index]:
            for column in range(len(nodes)):
                rows[row_index][column] -= rows[lower][column]
    for upper_index, upper in enumerate(nodes):
        for column in range(len(nodes)):
            reconstructed = sum(
                rows[lower_index][column]
                for lower_index, lower in enumerate(nodes)
                if antichain_leq(lower, upper)
            )
            if reconstructed != (1 if upper_index == column else 0):
                raise OracleError("Mobius matrix is not the inverse of zeta")
    return tuple(tuple(row) for row in rows)


def sx_neighborhoods(
    realizations: Sequence[Realization], node: Antichain
) -> tuple[Neighborhoods, Neighborhoods, Neighborhoods]:
    source_count = len(realizations[0]) - 1
    source_rows: list[frozenset[int]] = []
    joint_rows: list[frozenset[int]] = []
    target_rows: list[frozenset[int]] = []
    for left in realizations:
        source_matches: set[int] = set()
        joint_matches: set[int] = set()
        target_matches: set[int] = set()
        for index, right in enumerate(realizations):
            source_union = any(
                all(
                    left[source] == right[source]
                    for source in range(source_count)
                    if mask & (1 << source)
                )
                for mask in node
            )
            target_equal = left[-1] == right[-1]
            if source_union:
                source_matches.add(index)
            if source_union and target_equal:
                joint_matches.add(index)
            if target_equal:
                target_matches.add(index)
        source_rows.append(frozenset(source_matches))
        joint_rows.append(frozenset(joint_matches))
        target_rows.append(frozenset(target_matches))
    return tuple(source_rows), tuple(joint_rows), tuple(target_rows)


def neighborhood_mass(
    probabilities: Sequence[Rational], neighborhood: frozenset[int]
) -> Rational:
    return sum((probabilities[index] for index in neighborhood), Rational(0))


def g_function(
    neighborhoods: Neighborhoods, probabilities: Sequence[Rational]
) -> Decimal:
    total = Decimal(0)
    for index, probability in enumerate(probabilities):
        if probability:
            mass = neighborhood_mass(probabilities, neighborhoods[index])
            if mass < probability:
                raise OracleError("reflexive neighborhood lost its own probability")
            total -= decimal(probability) * decimal(mass).ln()
    return total


def local_cumulatives(
    neighborhoods: tuple[Neighborhoods, Neighborhoods, Neighborhoods],
    probabilities: Sequence[Rational],
    realization_index: int,
) -> tuple[Decimal, Decimal, Decimal]:
    source_rows, joint_rows, target_rows = neighborhoods
    source_mass = neighborhood_mass(
        probabilities, source_rows[realization_index]
    )
    joint_mass = neighborhood_mass(probabilities, joint_rows[realization_index])
    target_mass = neighborhood_mass(
        probabilities, target_rows[realization_index]
    )
    if min(source_mass, joint_mass, target_mass) <= 0:
        raise OracleError("positive realization has a zero event probability")
    informative = -decimal(source_mass).ln()
    misinformative = (decimal(target_mass) / decimal(joint_mass)).ln()
    return informative, misinformative, informative - misinformative


def system(
    realizations: Sequence[Realization], source_count: int
) -> tuple[
    tuple[Antichain, ...],
    tuple[tuple[int, ...], ...],
    tuple[tuple[Neighborhoods, Neighborhoods, Neighborhoods], ...],
]:
    return cached_system(tuple(realizations), source_count)


@lru_cache(maxsize=None)
def cached_system(
    realizations: tuple[Realization, ...], source_count: int
) -> tuple[
    tuple[Antichain, ...],
    tuple[tuple[int, ...], ...],
    tuple[tuple[Neighborhoods, Neighborhoods, Neighborhoods], ...],
]:
    if not realizations or any(
        len(realization) != source_count + 1 for realization in realizations
    ):
        raise OracleError("invalid realization width")
    if len(set(realizations)) != len(realizations):
        raise OracleError("duplicate ambient realization")
    nodes = antichains(source_count)
    matrix = mobius_matrix(nodes)
    neighborhoods = tuple(
        sx_neighborhoods(realizations, node) for node in nodes
    )
    return nodes, matrix, neighborhoods


def law_values(
    realizations: Sequence[Realization],
    source_count: int,
    probabilities: Sequence[Rational],
) -> dict[str, Any]:
    nodes, _matrix, neighborhoods = system(realizations, source_count)
    plus: dict[Antichain, Decimal] = {}
    minus: dict[Antichain, Decimal] = {}
    net: dict[Antichain, Decimal] = {}
    for node, (source_rows, joint_rows, target_rows) in zip(
        nodes, neighborhoods, strict=True
    ):
        informative = g_function(source_rows, probabilities)
        misinformative = g_function(joint_rows, probabilities) - g_function(
            target_rows, probabilities
        )
        plus[node] = informative
        minus[node] = misinformative
        net[node] = informative - misinformative
    plus_atoms = mobius_invert(nodes, plus)
    minus_atoms = mobius_invert(nodes, minus)
    net_atoms = mobius_invert(nodes, net)
    for node in nodes:
        if abs(plus_atoms[node] - minus_atoms[node] - net_atoms[node]) > TOLERANCE:
            raise OracleError("atom components do not reconstruct their net")
    full_mask = (1 << source_count) - 1
    return {
        "atoms": [
            {
                "informative_nats": decimal_text(plus_atoms[node]),
                "misinformative_nats": decimal_text(minus_atoms[node]),
                "net_nats": decimal_text(net_atoms[node]),
                "sets": list(node),
            }
            for node in nodes
        ],
        "joint_mi_nats": decimal_text(sum(net_atoms.values(), Decimal(0))),
        "subset_mis_nats": [
            decimal_text(net[(mask,)]) for mask in range(1, full_mask + 1)
        ],
    }


def pointwise_atom(
    realizations: Sequence[Realization],
    source_count: int,
    probabilities: Sequence[Rational],
    realization: Realization,
    node: Antichain,
) -> tuple[Decimal, Decimal, Decimal]:
    try:
        realization_index = realizations.index(realization)
    except ValueError as error:
        raise OracleError("pointwise realization is outside the ambient table") from error
    if probabilities[realization_index] == 0:
        raise OracleError("pointwise realization has zero probability")
    nodes, _matrix, neighborhoods = system(realizations, source_count)
    local_plus: dict[Antichain, Decimal] = {}
    local_minus: dict[Antichain, Decimal] = {}
    local_net: dict[Antichain, Decimal] = {}
    for current, current_neighborhoods in zip(
        nodes, neighborhoods, strict=True
    ):
        informative, misinformative, net_value = local_cumulatives(
            current_neighborhoods, probabilities, realization_index
        )
        local_plus[current] = informative
        local_minus[current] = misinformative
        local_net[current] = net_value
    return (
        mobius_invert(nodes, local_plus)[node],
        mobius_invert(nodes, local_minus)[node],
        mobius_invert(nodes, local_net)[node],
    )


def probabilities_from_counts(counts: Sequence[int]) -> tuple[Rational, ...]:
    if any(count < 0 for count in counts):
        raise OracleError("negative empirical count")
    total = sum(counts)
    if total <= 0:
        raise OracleError("empty empirical law")
    return tuple(Rational(count, total) for count in counts)


def expected_law(
    realizations: Sequence[Realization],
    source_count: int,
    counts: Sequence[int],
) -> dict[str, Any]:
    return law_values(
        realizations, source_count, probabilities_from_counts(counts)
    )


def law_pair(
    name: str,
    category: str,
    source_count: int,
    realizations: Sequence[Realization],
    p_counts: Sequence[int],
    q_counts: Sequence[int],
    evidence_boundary: str,
) -> dict[str, Any]:
    if len(realizations) != len(p_counts) or len(realizations) != len(q_counts):
        raise OracleError("law-pair arrays have different lengths")
    p = probabilities_from_counts(p_counts)
    q = probabilities_from_counts(q_counts)
    pair = {
        "category": category,
        "evidence_boundary": evidence_boundary,
        "name": name,
        "p_counts": list(p_counts),
        "p_expected": expected_law(realizations, source_count, p_counts),
        "p_probabilities": [fraction_text(value) for value in p],
        "q_counts": list(q_counts),
        "q_expected": expected_law(realizations, source_count, q_counts),
        "q_probabilities": [fraction_text(value) for value in q],
        "realizations": [list(value) for value in realizations],
        "source_count": source_count,
    }
    check_pair_bounds(pair)
    return pair


def values_for_pair(
    pair: dict[str, Any]
) -> tuple[
    tuple[Realization, ...],
    tuple[Rational, ...],
    tuple[Rational, ...],
    tuple[Antichain, ...],
    tuple[tuple[int, ...], ...],
    tuple[tuple[Neighborhoods, Neighborhoods, Neighborhoods], ...],
]:
    realizations = tuple(tuple(value) for value in pair["realizations"])
    source_count = pair["source_count"]
    p = probabilities_from_counts(pair["p_counts"])
    q = probabilities_from_counts(pair["q_counts"])
    nodes, matrix, neighborhoods = system(realizations, source_count)
    return realizations, p, q, nodes, matrix, neighborhoods


def numeric_components(
    realizations: Sequence[Realization],
    source_count: int,
    probabilities: Sequence[Rational],
) -> tuple[
    tuple[tuple[Decimal, ...], tuple[Decimal, ...], tuple[Decimal, ...]],
    tuple[tuple[Decimal, ...], tuple[Decimal, ...], tuple[Decimal, ...]],
]:
    nodes, _matrix, neighborhoods = system(realizations, source_count)
    cumulatives = [[], [], []]
    for source_rows, joint_rows, target_rows in neighborhoods:
        informative = g_function(source_rows, probabilities)
        misinformative = g_function(joint_rows, probabilities) - g_function(
            target_rows, probabilities
        )
        for output, value in zip(
            cumulatives,
            (informative, misinformative, informative - misinformative),
            strict=True,
        ):
            output.append(value)
    atoms = []
    for component in cumulatives:
        atom_map = mobius_invert(
            nodes, dict(zip(nodes, component, strict=True))
        )
        atoms.append([atom_map[node] for node in nodes])
    return (
        tuple(tuple(component) for component in cumulatives),  # type: ignore[return-value]
        tuple(tuple(component) for component in atoms),  # type: ignore[return-value]
    )


def check_pair_bounds(pair: dict[str, Any]) -> None:
    realizations, p, q, nodes, matrix, _neighborhoods = values_for_pair(pair)
    p_cumulative, p_atoms = numeric_components(
        realizations, pair["source_count"], p
    )
    q_cumulative, q_atoms = numeric_components(
        realizations, pair["source_count"], q
    )
    _common, left_residual, right_residual, eta = common_residuals(p, q)
    entropy_left = subprobability_entropy(left_residual)
    entropy_right = subprobability_entropy(right_residual)
    entropy_max = max(entropy_left, entropy_right)
    ell_value = ell(eta)
    gammas = tuple(gamma_union(len(node), eta) for node in nodes)
    for node_index, _node in enumerate(nodes):
        direct_bounds = (
            entropy_max + gammas[node_index],
            entropy_max + gammas[node_index] + ell_value,
            entropy_left
            + entropy_right
            + 2 * gammas[node_index]
            + ell_value,
        )
        for component in range(3):
            difference = abs(
                p_cumulative[component][node_index]
                - q_cumulative[component][node_index]
            )
            if difference > direct_bounds[component] + TOLERANCE:
                raise OracleError(
                    f"{pair['name']} violates a direct continuity bound"
                )
    for row_index, row in enumerate(matrix):
        row_sum = sum(row)
        weighted_gamma = sum(
            (
                Decimal(abs(coefficient)) * gamma
                for coefficient, gamma in zip(row, gammas, strict=True)
            ),
            Decimal(0),
        )
        atom_bounds = (
            entropy_max + weighted_gamma,
            entropy_max + weighted_gamma + Decimal(abs(row_sum)) * ell_value,
            entropy_left
            + entropy_right
            + 2 * weighted_gamma
            + Decimal(abs(row_sum)) * ell_value,
        )
        for component in range(3):
            difference = abs(
                p_atoms[component][row_index]
                - q_atoms[component][row_index]
            )
            if difference > atom_bounds[component] + TOLERANCE:
                raise OracleError(
                    f"{pair['name']} violates a Mobius continuity bound"
                )


def sharp_star_realizations(branch_count: int) -> tuple[int, tuple[Realization, ...], Antichain]:
    if branch_count == 1:
        # The second source separates the two ambient cells that the tested
        # singleton node deliberately treats as equivalent.
        return 2, ((0, 0, 0), (0, 1, 0), (1, 2, 0)), (1,)
    source_count = branch_count
    center = (0,) * source_count + (0,)
    leaves = tuple(
        tuple(
            0 if source == leaf - 1 else leaf
            for source in range(source_count)
        )
        + (0,)
        for leaf in range(1, branch_count + 1)
    )
    donor = (branch_count + 1,) * source_count + (0,)
    return source_count, (center, *leaves, donor), tuple(
        1 << source for source in range(source_count)
    )


def build_sharp_gamma_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for branch_count in range(1, 5):
        source_count, realizations, node = sharp_star_realizations(branch_count)
        counts = [0, *([1] * branch_count), 1]
        shifted = [1, *([1] * branch_count), 0]
        name = f"sharp_gamma_j{branch_count}"
        pair = law_pair(
            name,
            "sharp_gamma",
            source_count,
            realizations,
            counts,
            shifted,
            "exact common-mass sharpness for the listed empirical Sx node",
        )
        pairs.append(pair)
        _, p, q, nodes, _matrix, neighborhoods = values_for_pair(pair)
        index = nodes.index(node)
        common, _left, _right, eta = common_residuals(p, q)
        source_rows = neighborhoods[index][0]
        common_term = sum(
            (
                decimal(common[row])
                * (
                    decimal(neighborhood_mass(p, source_rows[row]))
                    / decimal(neighborhood_mass(q, source_rows[row]))
                ).ln()
                for row in range(len(realizations))
                if common[row]
            ),
            Decimal(0),
        )
        expected_gamma = gamma_union(branch_count, eta)
        total_difference = abs(
            g_function(source_rows, p) - g_function(source_rows, q)
        )
        residual_entropy = subprobability_entropy(
            common_residuals(p, q)[1]
        )
        if abs(abs(common_term) - expected_gamma) > TOLERANCE:
            raise OracleError("gamma_J sharpness construction is not exact")
        if abs(total_difference - residual_entropy - expected_gamma) > TOLERANCE:
            raise OracleError("gamma_J total star identity is not exact")
        cases.append(
            {
                "branch_count": branch_count,
                "common_term_absolute_nats": decimal_text(abs(common_term)),
                "eta": fraction_text(eta),
                "gamma_j_nats": decimal_text(expected_gamma),
                "node_masks": list(node),
                "pair_name": name,
                "residual_entropy_nats": decimal_text(residual_entropy),
                "total_difference_nats": decimal_text(total_difference),
            }
        )
    return pairs, cases


def build_fannes_falsifiers() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    three_realizations = (
        (0, 0, 0, 0),
        (0, 1, 1, 0),
        (2, 0, 2, 0),
        (3, 3, 0, 0),
        (4, 4, 4, 0),
    )
    three_pair = law_pair(
        "fannes_three_source_five_cell",
        "fannes_falsifier",
        3,
        three_realizations,
        (0, 3, 3, 3, 1),
        (1, 3, 3, 3, 0),
        "exact five-cell empirical counterexample at the bottom singleton antichain",
    )

    pairs = tuple(combinations(range(4), 2))
    four_realizations = [(0, 0, 0, 0, 0)]
    for leaf, pair_indices in enumerate(pairs, start=1):
        four_realizations.append(
            tuple(
                0 if source in pair_indices else leaf for source in range(4)
            )
            + (0,)
        )
    four_pair = law_pair(
        "fannes_four_source_six_pair_star",
        "fannes_falsifier",
        4,
        tuple(four_realizations),
        (0, 1, 1, 1, 1, 1, 1),
        (1, 1, 2, 2, 2, 2, 2),
        "exact seven-cell empirical counterexample at the six-pair antichain",
    )

    records = []
    for pair, node, alphabet_size, lhs, rhs, identity in (
        (
            three_pair,
            (1, 2, 4),
            5,
            6**9,
            4 * 5**9,
            "6^9 > 4*5^9",
        ),
        (
            four_pair,
            (3, 5, 6, 9, 10, 12),
            7,
            11**11,
            9 * 2**34,
            "11^11 > 9*2^34",
        ),
    ):
        realizations, p, q, nodes, _matrix, neighborhoods = values_for_pair(pair)
        index = nodes.index(node)
        source_rows = neighborhoods[index][0]
        difference = abs(g_function(source_rows, p) - g_function(source_rows, q))
        eta = total_variation(p, q)
        fannes_value = fannes(alphabet_size, eta)
        if difference <= fannes_value or lhs <= rhs:
            raise OracleError("retained Fannes falsifier is not strict")
        common, left_residual, _right_residual, _ = common_residuals(p, q)
        common_term = sum(
            (
                decimal(common[row])
                * (
                    decimal(neighborhood_mass(p, source_rows[row]))
                    / decimal(neighborhood_mass(q, source_rows[row]))
                ).ln()
                for row in range(len(realizations))
                if common[row]
            ),
            Decimal(0),
        )
        gamma = gamma_union(len(node), eta)
        gamma_sharp = abs(abs(common_term) - gamma) <= TOLERANCE
        residual_entropy = subprobability_entropy(left_residual)
        if pair["name"] == "fannes_three_source_five_cell":
            if not gamma_sharp:
                raise OracleError("five-cell Fannes witness did not attain gamma_3")
            if abs(difference - residual_entropy - gamma) > TOLERANCE:
                raise OracleError("five-cell total difference is not E(a)+gamma_3")
        elif gamma_sharp:
            raise OracleError("six-pair Fannes record must not claim gamma sharpness")
        # Constant targets make the same change appear in the misinformative
        # cumulative, while the net cumulative remains zero.
        p_components, _ = numeric_components(
            realizations, pair["source_count"], p
        )
        q_components, _ = numeric_components(
            realizations, pair["source_count"], q
        )
        if abs(abs(p_components[1][index] - q_components[1][index]) - difference) > TOLERANCE:
            raise OracleError("constant-target minus change differs from plus")
        if abs(p_components[2][index] - q_components[2][index]) > TOLERANCE:
            raise OracleError("constant-target net cumulative is nonzero")
        records.append(
            {
                "alphabet_size": alphabet_size,
                "branch_count": len(node),
                "common_term_absolute_nats": decimal_text(abs(common_term)),
                "difference_nats": decimal_text(difference),
                "eta": fraction_text(eta),
                "exact_inequality": identity,
                "exact_inequality_lhs": lhs,
                "exact_inequality_rhs": rhs,
                "fannes_nats": decimal_text(fannes_value),
                "gamma_j_nats": decimal_text(gamma),
                "gamma_sharp": gamma_sharp,
                "node_masks": list(node),
                "pair_name": pair["name"],
                "residual_entropy_nats": decimal_text(residual_entropy),
                "strict_excess_nats": decimal_text(difference - fannes_value),
            }
        )
    return [three_pair, four_pair], records


def build_rare_support_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    previous_ratio = Decimal(0)
    for exponent in (4, 6, 8, 10, 12):
        denominator = 1 << exponent
        name = f"rare_support_t_equals_s1_e{exponent}"
        pair = law_pair(
            name,
            "rare_support",
            2,
            ((0, 0, 0), (1, 0, 1)),
            (1, 0),
            (denominator - 1, 1),
            "the rare point exists only under q, so its pointwise magnitude is not a keyed cross-law difference",
        )
        pairs.append(pair)
        realizations, _p, q, _nodes, _matrix, _neighborhoods = values_for_pair(
            pair
        )
        eta = Rational(1, denominator)
        entropy = binary_entropy(eta)
        ratio = entropy / (Decimal(2) * decimal(eta))
        informative, misinformative, net = pointwise_atom(
            realizations, 2, q, (1, 0, 1), (1,)
        )
        expected_local = -decimal(eta).ln()
        if abs(informative - expected_local) > TOLERANCE:
            raise OracleError("rare pointwise informative value is not -ln(epsilon)")
        if abs(misinformative) > TOLERANCE or abs(net - expected_local) > TOLERANCE:
            raise OracleError("rare pointwise unique-S1 components are incorrect")
        law = law_values(realizations, 2, q)
        unique = next(atom for atom in law["atoms"] if atom["sets"] == [1])
        if abs(Decimal(unique["net_nats"]) - entropy) > REFERENCE_TOLERANCE:
            raise OracleError("rare-support averaged unique information is not h2")
        if ratio <= previous_ratio:
            raise OracleError("rare-support h2/L1 ratios did not increase")
        previous_ratio = ratio
        records.append(
            {
                "averaged_unique_s1_nats": decimal_text(entropy),
                "epsilon": fraction_text(eta),
                "exponent": exponent,
                "l1_distance": fraction_text(2 * eta),
                "node_masks": [1],
                "pair_name": name,
                "rare_pointwise_informative_nats": decimal_text(informative),
                "rare_pointwise_misinformative_nats": decimal_text(
                    misinformative
                ),
                "rare_pointwise_net_nats": decimal_text(net),
                "rare_realization": [1, 0, 1],
                "unique_to_l1_ratio": decimal_text(ratio),
            }
        )
    return pairs, records


def build_net_residual_shortcut() -> tuple[dict[str, Any], dict[str, Any]]:
    pair = law_pair(
        "net_residual_max_shortcut",
        "net_residual_shortcut",
        2,
        (
            (0, 0, 0),
            (1, 0, 1),
            (1, 0, 2),
            (2, 0, 1),
        ),
        (2, 0, 9, 9),
        (0, 2, 9, 9),
        "falsifies max(Ea,Eb) only for the signed residual step; it does not establish global sharpness of the whole atom modulus",
    )
    realizations, p, q, nodes, _matrix, _neighborhoods = values_for_pair(pair)
    left_pointwise = pointwise_atom(
        realizations, 2, p, (0, 0, 0), (1,)
    )[2]
    right_pointwise = pointwise_atom(
        realizations, 2, q, (1, 0, 1), (1,)
    )[2]
    expected_left = Decimal(10).ln()
    expected_right = (Decimal(40) / Decimal(121)).ln()
    eta = Rational(1, 10)
    residual_difference = decimal(eta) * (
        left_pointwise - right_pointwise
    )
    entropy_max = xlogx(eta)
    closed = Decimal(1).scaleb(-1) * (
        Decimal(10) / (Decimal(40) / Decimal(121))
    ).ln()
    alternative_closed = decimal(Rational(1, 5)) * (
        Decimal(11) / Decimal(2)
    ).ln()
    _p_cumulatives, p_atoms = numeric_components(realizations, 2, p)
    _q_cumulatives, q_atoms = numeric_components(realizations, 2, q)
    unique_s1_index = nodes.index((1,))
    whole_unique_net_difference = abs(
        p_atoms[2][unique_s1_index] - q_atoms[2][unique_s1_index]
    )
    common_mass = Rational(9, 10)
    whole_common_term = decimal(common_mass) * (
        (Decimal(1) + decimal(eta)) / decimal(common_mass)
    ).ln()
    whole_closed = residual_difference + whole_common_term
    if abs(left_pointwise - expected_left) > TOLERANCE:
        raise OracleError("left residual pointwise value is not ln(10)")
    if abs(right_pointwise - expected_right) > TOLERANCE:
        raise OracleError("right residual pointwise value is not ln(40/121)")
    if abs(residual_difference - closed) > TOLERANCE:
        raise OracleError("residual-difference closed form is incorrect")
    if abs(residual_difference - alternative_closed) > TOLERANCE:
        raise OracleError("general-family residual closed form is incorrect")
    if residual_difference <= entropy_max:
        raise OracleError("max residual-entropy shortcut is not falsified")
    if abs(whole_unique_net_difference - whole_closed) > TOLERANCE:
        raise OracleError("whole unique-S1 net closed form is incorrect")
    return pair, {
        "eta": fraction_text(eta),
        "exact_inequality": "(1-eta)^2 > 0",
        "left_pointwise_net_closed_form": "ln(10)",
        "left_pointwise_net_nats": decimal_text(left_pointwise),
        "left_residual_realization": [0, 0, 0],
        "max_residual_entropy_nats": decimal_text(entropy_max),
        "node_masks": [1],
        "pair_name": pair["name"],
        "residual_difference_closed_form": "(1/5) ln(11/2)",
        "residual_difference_nats": decimal_text(residual_difference),
        "right_pointwise_net_closed_form": "ln(40/121)",
        "right_pointwise_net_nats": decimal_text(right_pointwise),
        "right_residual_realization": [1, 0, 1],
        "strict_excess_nats": decimal_text(residual_difference - entropy_max),
        "whole_common_term_closed_form": "(9/10) ln(11/9)",
        "whole_common_term_nats": decimal_text(whole_common_term),
        "whole_unique_net_difference_closed_form": (
            "(1/5) ln(11/2) + (9/10) ln(11/9)"
        ),
        "whole_unique_net_difference_nats": decimal_text(
            whole_unique_net_difference
        ),
    }


class SplitMix64:
    """Small specified PRNG used only to select the bounded raw count tables."""

    def __init__(self, seed: int) -> None:
        self.state = seed & ((1 << 64) - 1)

    def next_u64(self) -> int:
        mask = (1 << 64) - 1
        self.state = (self.state + 0x9E3779B97F4A7C15) & mask
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        return (value ^ (value >> 31)) & mask

    def bounded(self, bound: int) -> int:
        if bound <= 0:
            raise OracleError("invalid PRNG bound")
        return self.next_u64() % bound


def generated_counts(
    rng: SplitMix64, cell_count: int, source_count: int, case_index: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    counts = [rng.bounded(9) for _ in range(cell_count)]
    # Deterministically retain zeros and prevent an empty table.
    for index in range(case_index, cell_count, 7):
        counts[index] = 0
    if sum(counts) == 0:
        counts[0] = 1
    changed = counts.copy()
    moves = 5 + 2 * source_count + case_index
    for move in range(moves):
        occupied = [index for index, count in enumerate(changed) if count]
        source = occupied[rng.bounded(len(occupied))]
        target = rng.bounded(cell_count - 1)
        if target >= source:
            target += 1
        amount = 1 + rng.bounded(changed[source])
        if move == 0:
            amount = changed[source]
        changed[source] -= amount
        changed[target] += amount
    if counts == changed:
        raise OracleError("seeded pair did not change")
    return tuple(counts), tuple(changed)


def build_seeded_corpus() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = SplitMix64(SEED)
    pairs: list[dict[str, Any]] = []
    case_names: list[str] = []
    for source_count in (2, 3, 4):
        realizations = tuple(product((0, 1), repeat=source_count + 1))
        for case_index in range(2):
            p_counts, q_counts = generated_counts(
                rng, len(realizations), source_count, case_index
            )
            name = f"seeded_m{source_count}_case{case_index}"
            pair = law_pair(
                name,
                "seeded_bound_corpus",
                source_count,
                realizations,
                p_counts,
                q_counts,
                "bounded seeded empirical tables challenge every cumulative and atom plus/minus/net inequality; they are not exhaustive",
            )
            pairs.append(pair)
            case_names.append(name)
    return pairs, {
        "algorithm": "SplitMix64 with modulo-bounded draws",
        "case_names": case_names,
        "cases_per_source_count": 2,
        "seed_decimal": str(SEED),
        "source_counts": [2, 3, 4],
    }


def mobius_summary(source_count: int) -> dict[str, Any]:
    nodes = antichains(source_count)
    matrix = mobius_matrix(nodes)
    bottom = tuple(1 << source for source in range(source_count))
    row_sums = [sum(row) for row in matrix]
    expected = [1 if node == bottom else 0 for node in nodes]
    if row_sums != expected:
        raise OracleError("Mobius row-sum cancellation identity failed")
    norms = [sum(abs(coefficient) for coefficient in row) for row in matrix]
    coefficient_counts = Counter(
        coefficient for row in matrix for coefficient in row
    )
    norm_histogram = Counter(norms)
    return {
        "bottom_node_masks": list(bottom),
        "coefficient_counts": [
            {"coefficient": value, "count": coefficient_counts[value]}
            for value in sorted(coefficient_counts)
        ],
        "max_absolute_row_norm": max(norms),
        "node_count": len(nodes),
        "row_norm_histogram": [
            {"count": norm_histogram[norm], "norm": norm}
            for norm in sorted(norm_histogram)
        ],
        "row_sum_one_count": row_sums.count(1),
        "row_sum_zero_count": row_sums.count(0),
        "source_count": source_count,
    }


def build_fixture() -> dict[str, Any]:
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        sharp_pairs, sharp_cases = build_sharp_gamma_cases()
        fannes_pairs, fannes_cases = build_fannes_falsifiers()
        rare_pairs, rare_cases = build_rare_support_cases()
        net_pair, net_case = build_net_residual_shortcut()
        seeded_pairs, seeded_metadata = build_seeded_corpus()
        law_pairs = [
            *sharp_pairs,
            *fannes_pairs,
            *rare_pairs,
            net_pair,
            *seeded_pairs,
        ]
        total_tables = 2 * len(law_pairs)
        return {
            "arithmetic": {
                "decimal_precision_digits": DECIMAL_PRECISION,
                "decimal_reference_digits": DECIMAL_REFERENCE_DIGITS,
                "decimal_role": (
                    "reference values for scoped binary64 comparisons only; "
                    "not certified real-number enclosures"
                ),
                "fraction_arithmetic": "exact",
                "logarithm": "natural",
                "third_party_dependencies": [],
            },
            "bound_formulae": {
                "direct_minus": "Emax + gamma_J(B) + ell",
                "direct_net": "Ea + Eb + gamma_J(A) + gamma_J(B) + ell",
                "direct_plus": "Emax + gamma_J(A)",
                "ell": "-(1-eta) ln(1-eta)",
                "gamma_j": "(1-eta) ln(1 + J eta/(1-eta)); gamma_j(1)=0 at eta=1",
                "mobius_minus": "Emax + sum |M| gamma_J(B) + |row_sum| ell",
                "mobius_net": "Ea + Eb + sum |M|(gamma_J(A)+gamma_J(B)) + |row_sum| ell",
                "mobius_plus": "Emax + sum |M| gamma_J(A)",
            },
            "fannes_falsifiers": fannes_cases,
            "generator": {
                "imports_pid_rs": False,
                "path": "scripts/generate-support-change-tolerant-sxpid-oracle.py",
                "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "standard_library_only": True,
            },
            "law_pairs": law_pairs,
            "mobius_cases": [
                mobius_summary(source_count) for source_count in (2, 3, 4)
            ],
            "net_residual_shortcut": net_case,
            "nonclaims": [
                "the fixture covers only the listed finite empirical count tables",
                "the seeded corpus is bounded and is not exhaustive",
                "Decimal comparisons are reference-only and are not certified real-number bounds",
                "software agreement is not an asymptotic theorem or external review",
                "the Fannes examples falsify that shortcut for the named Sx cumulatives, not every possible continuity modulus",
                "gamma_J sharpness is established only for the listed common-mass constructions",
                "the net residual witness replays one whole unique-S1 net-atom equality and falsifies replacing two signed residual budgets by their maximum inside that proof step; the finite fixture does not prove its asymptotic coefficient-two limit",
                "the rare pointwise value occurs on new support and is not a keyed cross-law pointwise difference",
            ],
            "rare_support_cases": rare_cases,
            "schema": SCHEMA,
            "schema_revision": SCHEMA_REVISION,
            "seeded_corpus": seeded_metadata,
            "sharp_gamma_cases": sharp_cases,
            "tested_domain": {
                "bound_components_per_node": [
                    "cumulative informative",
                    "cumulative misinformative",
                    "cumulative net",
                    "atom informative",
                    "atom misinformative",
                    "atom net",
                ],
                "law_pair_count": len(law_pairs),
                "lattice_node_counts": [
                    {"node_count": len(antichains(source_count)), "source_count": source_count}
                    for source_count in (2, 3, 4)
                ],
                "public_count_tables_replayed": total_tables,
                "public_rust_route": "pid_core::stable::categorical::discrete_sxpid_n",
                "source_counts": [2, 3, 4],
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="replace the committed fixture and SHA-256 sidecar",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="check the committed fixture (also the default)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = build_fixture()
    raw = canonical_json_bytes(fixture)
    digest = hashlib.sha256(raw).hexdigest()
    sidecar = f"{digest}  {OUTPUT.name}\n"
    if args.write:
        OUTPUT.write_bytes(raw)
        SIDECAR.write_text(sidecar, encoding="utf-8", newline="")
        print(f"wrote support-change-tolerant SxPID fixture; SHA-256 {digest}")
        return 0
    try:
        committed = OUTPUT.read_bytes()
        committed_sidecar = SIDECAR.read_text(encoding="utf-8")
    except OSError as error:
        print(f"support-change-tolerant SxPID fixture error: {error}")
        return 1
    if committed != raw:
        print("support-change-tolerant SxPID fixture error: committed data is stale")
        return 1
    if committed_sidecar != sidecar:
        print(
            "support-change-tolerant SxPID fixture error: SHA-256 sidecar is stale"
        )
        return 1
    selected_mode = "--check" if args.check else "default check"
    print(
        "OK "
        f"({selected_mode}): support-change-tolerant SxPID fixture matches "
        f"SHA-256 {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
