#!/usr/bin/env python3
"""Independent exact-rational audit of the Lyu--Clark--Raviv witness.

This checker imports only the Python standard library.  It does not import,
invoke, or copy the pid-rs implementation.  It constructs the three-source
antichain lattice, verifies the finite-law premises of Lyu--Clark--Raviv
Definition 6, derives the Lemma 4 recovering antichains and descriptor vector,
counts the keyed source-union and target events, performs Möbius inversion in
the additive group of formal logarithms of rationals, and averages the
resulting local atoms exactly.

The formal-log representation maps each prime to its rational exponent.  It
therefore represents averages of logarithms without evaluating a logarithm or
floating-point number.  For the two symmetric witnesses every averaged atom
has integral prime exponents and can be rendered as one exact rational ratio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
from typing import Iterable, Literal, Sequence

Mask = int
Antichain = tuple[Mask, ...]
Vector = tuple[int, int, int]
Row = tuple[Vector, Vector, Vector, Vector]
LatentRow = tuple[int, int, int, int, int, int, int, int, int]
EventMode = Literal["union", "intersection"]

SOURCE_LATENT_INDICES = ((0, 3, 6), (1, 4, 7), (2, 5, 8))
TARGET_LATENT_INDICES = (0, 4, 8)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def factor_integer(value: int) -> dict[int, int]:
    if value <= 0:
        raise ValueError("formal logarithms require positive integers")
    factors: dict[int, int] = {}
    divisor = 2
    while divisor * divisor <= value:
        while value % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            value //= divisor
        divisor += 1 if divisor == 2 else 2
    if value > 1:
        factors[value] = factors.get(value, 0) + 1
    return factors


@dataclass(frozen=True)
class LogMonomial:
    """An exact formal value sum_p exponent[p] * log(p)."""

    terms: tuple[tuple[int, Fraction], ...] = ()

    @staticmethod
    def from_terms(terms: dict[int, Fraction]) -> "LogMonomial":
        return LogMonomial(
            tuple(sorted((prime, exponent) for prime, exponent in terms.items() if exponent))
        )

    @staticmethod
    def log_fraction(value: Fraction) -> "LogMonomial":
        terms: dict[int, Fraction] = {}
        for prime, exponent in factor_integer(value.numerator).items():
            terms[prime] = terms.get(prime, Fraction(0)) + exponent
        for prime, exponent in factor_integer(value.denominator).items():
            terms[prime] = terms.get(prime, Fraction(0)) - exponent
        return LogMonomial.from_terms(terms)

    def as_dict(self) -> dict[int, Fraction]:
        return dict(self.terms)

    def __add__(self, other: "LogMonomial") -> "LogMonomial":
        terms = self.as_dict()
        for prime, exponent in other.terms:
            terms[prime] = terms.get(prime, Fraction(0)) + exponent
        return LogMonomial.from_terms(terms)

    def __sub__(self, other: "LogMonomial") -> "LogMonomial":
        return self + other.scale(Fraction(-1))

    def scale(self, weight: Fraction) -> "LogMonomial":
        return LogMonomial.from_terms(
            {prime: exponent * weight for prime, exponent in self.terms}
        )

    def exact_ratio(self) -> Fraction | None:
        if any(exponent.denominator != 1 for _, exponent in self.terms):
            return None
        numerator = 1
        denominator = 1
        for prime, exponent in self.terms:
            power = exponent.numerator
            if power >= 0:
                numerator *= prime**power
            else:
                denominator *= prime ** (-power)
        return Fraction(numerator, denominator)

    def json_value(self) -> dict[str, object]:
        ratio = self.exact_ratio()
        return {
            "formal_log_prime_exponents": {
                str(prime): str(exponent) for prime, exponent in self.terms
            },
            "exponentiated_ratio_if_rational": fraction_text(ratio) if ratio is not None else None,
        }


ZERO = LogMonomial()


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def source_subsets() -> tuple[Mask, ...]:
    return tuple(range(1, 1 << 3))


def is_subset(left: Mask, right: Mask) -> bool:
    return left & right == left


def is_antichain(collections: Sequence[Mask]) -> bool:
    return all(
        not is_subset(left, right) and not is_subset(right, left)
        for left, right in combinations(collections, 2)
    )


def antichain_lattice() -> tuple[Antichain, ...]:
    subsets = source_subsets()
    nodes = [
        tuple(choice)
        for size in range(1, len(subsets) + 1)
        for choice in combinations(subsets, size)
        if is_antichain(choice)
    ]
    if len(nodes) != 18:
        raise AssertionError(f"three-source lattice must contain 18 nodes, got {len(nodes)}")
    return tuple(nodes)


def leq(left: Antichain, right: Antichain) -> bool:
    """The redundancy order left <= right."""

    return all(any(is_subset(a, b) for a in left) for b in right)


def topological_nodes(nodes: Sequence[Antichain]) -> tuple[Antichain, ...]:
    lower_count = {
        node: sum(other != node and leq(other, node) for other in nodes) for node in nodes
    }
    ordered = tuple(sorted(nodes, key=lambda node: (lower_count[node], node)))
    positions = {node: index for index, node in enumerate(ordered)}
    for lower in nodes:
        for upper in nodes:
            if lower != upper and leq(lower, upper) and positions[lower] >= positions[upper]:
                raise AssertionError("invalid topological order")
    return ordered


def subset_text(mask: Mask) -> str:
    return "".join(str(index + 1) for index in range(3) if mask & (1 << index))


def antichain_text(node: Antichain) -> str:
    display_order = sorted(node, key=lambda mask: (mask.bit_count(), mask))
    return "{" + ",".join("{" + subset_text(mask) + "}" for mask in display_order) + "}"


def canonical_rows_json(rows: Sequence[Row]) -> bytes:
    serializable = [[list(s0), list(s1), list(s2), list(target)] for s0, s1, s2, target in rows]
    return json.dumps(serializable, sort_keys=True, separators=(",", ":")).encode("utf-8")


def row_digest(rows: Sequence[Row]) -> str:
    return hashlib.sha256(canonical_rows_json(rows)).hexdigest()


def recover_latent_rows(rows: Sequence[Row]) -> tuple[LatentRow, ...]:
    """Recover x1,...,x9 and verify the source/target coordinate binding."""

    latent_rows: list[LatentRow] = []
    for source_1, source_2, source_3, target in rows:
        latent = (
            source_1[0],
            source_2[0],
            source_3[0],
            source_1[1],
            source_2[1],
            source_3[1],
            source_1[2],
            source_2[2],
            source_3[2],
        )
        if target != tuple(latent[index] for index in TARGET_LATENT_INDICES):
            raise AssertionError("T must be exactly (x1,x5,x9)")
        sources = (source_1, source_2, source_3)
        for source_index, indices in enumerate(SOURCE_LATENT_INDICES):
            expected = tuple(latent[index] for index in indices)
            if expected != sources[source_index]:
                raise AssertionError("source coordinate/index-set binding failed")
        latent_rows.append(latent)
    return tuple(latent_rows)


def deterministic_given(values: Sequence[object], conditions: Sequence[object]) -> bool:
    if len(values) != len(conditions) or not values:
        raise ValueError("determinism check requires aligned nonempty samples")
    seen: dict[object, object] = {}
    for value, condition in zip(values, conditions, strict=True):
        previous = seen.setdefault(condition, value)
        if previous != value:
            return False
    return True


def exactly_independent(left: Sequence[object], right: Sequence[object]) -> bool:
    """Exact finite-law independence, including zero-probability cross-cells."""

    if len(left) != len(right) or not left:
        raise ValueError("independence check requires aligned nonempty samples")
    total = len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    joint_counts = Counter(zip(left, right, strict=True))
    return all(
        joint_counts[(left_value, right_value)] * total
        == left_count * right_count
        for left_value, left_count in left_counts.items()
        for right_value, right_count in right_counts.items()
    )


def mutually_independent(latent_rows: Sequence[LatentRow], indices: Sequence[int]) -> bool:
    """Exact mutual (not merely pairwise) independence of named components."""

    if not latent_rows or not indices:
        raise ValueError("mutual-independence check requires data and components")
    total = len(latent_rows)
    joint_counts = Counter(tuple(row[index] for index in indices) for row in latent_rows)
    marginals = [Counter(row[index] for row in latent_rows) for index in indices]
    supports = [tuple(sorted(counts)) for counts in marginals]
    return all(
        joint_counts[values] * total ** (len(indices) - 1)
        == product_of(marginals[position][value] for position, value in enumerate(values))
        for values in product(*supports)
    )


def product_of(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= value
    return result


def source_projection(row: Row, mask: Mask) -> tuple[Vector, ...]:
    return tuple(row[index] for index in range(3) if mask & (1 << index))


def entropy(values: Sequence[object]) -> LogMonomial:
    """Exact Shannon entropy represented as a rational linear form in logs."""

    if not values:
        raise ValueError("entropy requires a nonempty finite law")
    counts = Counter(values)
    total = len(values)
    return sum_monomials(
        LogMonomial.log_fraction(Fraction(total, count)).scale(Fraction(count, total))
        for count in counts.values()
    )


def source_mask_text(mask: Mask) -> str:
    return "{}" if mask == 0 else "{" + subset_text(mask) + "}"


def construction_audit(rows: Sequence[Row], system_name: str) -> dict[str, object]:
    """Bind generated rows to the paper's fair-bit/XOR witness definition."""

    latent_rows = recover_latent_rows(rows)
    if system_name == "hat":
        base_indices = (0, 1, 3, 4, 6, 7)
        expected_row_count = 64
        identities = {
            "x3=x1_xor_x2": all(row[2] == row[0] ^ row[1] for row in latent_rows),
            "x6=x4_xor_x5": all(row[5] == row[3] ^ row[4] for row in latent_rows),
            "x9=x7_xor_x8": all(row[8] == row[6] ^ row[7] for row in latent_rows),
        }
    elif system_name == "tilde":
        base_indices = (0, 1, 3, 4, 6)
        expected_row_count = 32
        identities = {
            "x3=x1_xor_x2": all(row[2] == row[0] ^ row[1] for row in latent_rows),
            "x6=x4_xor_x5": all(row[5] == row[3] ^ row[4] for row in latent_rows),
            "x9=x1_xor_x5": all(row[8] == row[0] ^ row[4] for row in latent_rows),
            "x8=x7_xor_x1_xor_x5": all(
                row[7] == row[6] ^ row[0] ^ row[4] for row in latent_rows
            ),
            "x9=x7_xor_x8": all(row[8] == row[6] ^ row[7] for row in latent_rows),
        }
    else:
        raise ValueError(f"unknown witness system: {system_name}")

    fair = {
        f"x{index + 1}": Counter(row[index] for row in latent_rows)
        == Counter({0: len(latent_rows) // 2, 1: len(latent_rows) // 2})
        for index in base_indices
    }
    base_mutually_independent = mutually_independent(latent_rows, base_indices)
    unique_rows = len(set(latent_rows)) == len(latent_rows)
    if (
        len(latent_rows) != expected_row_count
        or not unique_rows
        or not all(fair.values())
        or not base_mutually_independent
        or not all(identities.values())
    ):
        raise AssertionError(f"{system_name}: generated rows do not match the paper construction")

    return {
        "system": system_name,
        "equiprobable_unique_row_count": len(latent_rows),
        "base_latent_indices": [index + 1 for index in base_indices],
        "each_base_bit_fair": fair,
        "base_bits_mutually_independent": True,
        "deterministic_identities": identities,
        "source_and_target_index_sets_match": True,
    }


def hat_system() -> tuple[Row, ...]:
    rows: list[Row] = []
    for x1, x2, x4, x5, x7, x8 in product((0, 1), repeat=6):
        x3 = x1 ^ x2
        x6 = x4 ^ x5
        x9 = x7 ^ x8
        rows.append(((x1, x4, x7), (x2, x5, x8), (x3, x6, x9), (x1, x5, x9)))
    return tuple(rows)


def tilde_system() -> tuple[Row, ...]:
    rows: list[Row] = []
    for x1, x2, x4, x5, x7 in product((0, 1), repeat=5):
        x3 = x1 ^ x2
        x6 = x4 ^ x5
        x9 = x1 ^ x5
        x8 = x7 ^ x1 ^ x5
        rows.append(((x1, x4, x7), (x2, x5, x8), (x3, x6, x9), (x1, x5, x9)))
    return tuple(rows)


def relation_mutation_system() -> tuple[Row, ...]:
    """A killed mutation: restore an independent relation-bearing target bit."""

    rows: list[Row] = []
    for x1, x2, x4, x5, x7 in product((0, 1), repeat=5):
        x3 = x1 ^ x2
        x6 = x4 ^ x5
        x9 = x1 ^ x5 ^ x7
        x8 = x7 ^ x1 ^ x5
        rows.append(((x1, x4, x7), (x2, x5, x8), (x3, x6, x9), (x1, x5, x9)))
    return tuple(rows)


def collection_matches(row: Row, key: Row, mask: Mask) -> bool:
    return all(row[index] == key[index] for index in range(3) if mask & (1 << index))


def event_matches(row: Row, key: Row, node: Antichain, mode: EventMode) -> bool:
    branch_values = [collection_matches(row, key, mask) for mask in node]
    if mode == "union":
        return any(branch_values)
    if mode == "intersection":
        return all(branch_values)
    raise AssertionError(f"unhandled event mode {mode}")


@dataclass(frozen=True)
class AuditResult:
    row_count: int
    support_size: int
    event_mode: EventMode
    atoms: dict[str, dict[str, LogMonomial]]
    local_constant: dict[str, dict[str, bool]]
    mutual_information: LogMonomial
    reconstruction: LogMonomial

    def json_value(self) -> dict[str, object]:
        return {
            "row_count": self.row_count,
            "support_size": self.support_size,
            "event_mode": self.event_mode,
            "atoms": {
                node: {component: value.json_value() for component, value in components.items()}
                for node, components in sorted(self.atoms.items())
            },
            "local_atom_constant_on_support": {
                node: dict(sorted(components.items()))
                for node, components in sorted(self.local_constant.items())
            },
            "mutual_information": self.mutual_information.json_value(),
            "sum_of_net_atoms": self.reconstruction.json_value(),
        }


def sum_monomials(values: Iterable[LogMonomial]) -> LogMonomial:
    total = ZERO
    for value in values:
        total = total + value
    return total


def descriptor_model_audit(
    rows: Sequence[Row], system_name: str
) -> tuple[dict[str, object], dict[str, LogMonomial], LogMonomial]:
    """Verify Definition 6 and derive the complete Lemma 4 descriptor vector."""

    latent_rows = recover_latent_rows(rows)
    target_values = tuple(
        tuple(row[index] for index in TARGET_LATENT_INDICES) for row in latent_rows
    )

    determined_by_target = tuple(
        index
        for index in range(9)
        if deterministic_given(
            tuple(row[index] for row in latent_rows),
            target_values,
        )
    )
    if determined_by_target != TARGET_LATENT_INDICES:
        raise AssertionError(
            f"{system_name}: Definition 6(i) binding failed: {determined_by_target}"
        )

    source_component_independence = {
        f"S{source_index + 1}": mutually_independent(latent_rows, indices)
        for source_index, indices in enumerate(SOURCE_LATENT_INDICES)
    }
    if not all(source_component_independence.values()):
        raise AssertionError(f"{system_name}: Definition 6(ii) failed")

    recovery_antichains: dict[int, Antichain] = {}
    classifications: dict[str, dict[str, str]] = {}
    for target_index in TARGET_LATENT_INDICES:
        target_component = tuple(row[target_index] for row in latent_rows)
        recovering_masks: list[Mask] = []
        component_classification: dict[str, str] = {}
        for mask in range(1 << 3):
            source_values = tuple(source_projection(row, mask) for row in rows)
            recoverable = deterministic_given(target_component, source_values)
            independent = exactly_independent(target_component, source_values)
            if not recoverable and not independent:
                raise AssertionError(
                    f"{system_name}: Definition 6(iii) failed for "
                    f"x{target_index + 1}, B={source_mask_text(mask)}"
                )
            if recoverable:
                recovering_masks.append(mask)
            component_classification[source_mask_text(mask)] = (
                "recoverable_and_independent"
                if recoverable and independent
                else "recoverable"
                if recoverable
                else "independent"
            )

        minimal = tuple(
            mask
            for mask in recovering_masks
            if not any(
                candidate != mask and is_subset(candidate, mask)
                for candidate in recovering_masks
            )
        )
        if not is_antichain(minimal):
            raise AssertionError(f"{system_name}: minimal recovering sets are not an antichain")
        recovery_antichains[target_index] = minimal
        classifications[f"x{target_index + 1}"] = component_classification

    expected_recovery: dict[int, Antichain] = {
        0: (0b001, 0b110),
        4: (0b010, 0b101),
        8: (0b011, 0b100),
    }
    if recovery_antichains != expected_recovery:
        rendered = {
            f"x{index + 1}": antichain_text(node)
            for index, node in recovery_antichains.items()
        }
        raise AssertionError(f"{system_name}: unexpected recovering antichains: {rendered}")

    groups: dict[Antichain, list[int]] = {}
    for target_index, node in recovery_antichains.items():
        groups.setdefault(node, []).append(target_index)

    nodes = antichain_lattice()
    descriptor_vector = {
        antichain_text(node): entropy(
            tuple(
                tuple(row[index] for index in groups.get(node, ()))
                for row in latent_rows
            )
        )
        for node in nodes
    }
    log_two = LogMonomial.log_fraction(Fraction(2))
    nonzero_labels = {antichain_text(node) for node in expected_recovery.values()}
    for label, value in descriptor_vector.items():
        expected_value = log_two if label in nonzero_labels else ZERO
        if value != expected_value:
            raise AssertionError(f"{system_name}: unexpected Lemma 4 descriptor at {label}")

    target_component_entropies = {
        f"x{index + 1}": entropy(tuple(row[index] for row in latent_rows))
        for index in TARGET_LATENT_INDICES
    }
    descriptor_sum = sum_monomials(descriptor_vector.values())
    if descriptor_sum.exact_ratio() != Fraction(8):
        raise AssertionError(f"{system_name}: three one-bit descriptors must sum to log(8)")

    result: dict[str, object] = {
        "system": system_name,
        "source_index_sets": {
            f"J{index + 1}": [latent_index + 1 for latent_index in indices]
            for index, indices in enumerate(SOURCE_LATENT_INDICES)
        },
        "target_index_set": [index + 1 for index in TARGET_LATENT_INDICES],
        "definition6_i": {
            "holds": True,
            "indices_determined_by_target": [index + 1 for index in determined_by_target],
        },
        "definition6_ii": {
            "holds": True,
            "mutual_not_merely_pairwise_independence": source_component_independence,
        },
        "definition6_iii": {
            "holds": True,
            "all_24_target_component_source_group_cases_checked": True,
            "classification": classifications,
        },
        "minimal_recovering_antichains": {
            f"x{index + 1}": antichain_text(node)
            for index, node in recovery_antichains.items()
        },
        "target_component_entropies": {
            name: value.json_value() for name, value in target_component_entropies.items()
        },
        "lemma4_descriptor_vector": {
            label: value.json_value() for label, value in sorted(descriptor_vector.items())
        },
        "lemma4_descriptor_sum": descriptor_sum.json_value(),
    }
    return result, descriptor_vector, descriptor_sum


def evaluate(rows: Sequence[Row], mode: EventMode = "union") -> AuditResult:
    counts = Counter(rows)
    total_count = sum(counts.values())
    nodes = topological_nodes(antichain_lattice())
    strict_lower = {
        node: tuple(other for other in nodes if other != node and leq(other, node)) for node in nodes
    }

    local_atoms: dict[str, dict[str, list[LogMonomial]]] = {
        antichain_text(node): {"informative": [], "misinformative": [], "net": []}
        for node in nodes
    }
    averaged: dict[str, dict[str, LogMonomial]] = {
        antichain_text(node): {"informative": ZERO, "misinformative": ZERO, "net": ZERO}
        for node in nodes
    }
    average_top = ZERO

    for key, key_count in sorted(counts.items()):
        target_count = sum(count for row, count in counts.items() if row[3] == key[3])
        cumulatives: dict[Antichain, dict[str, LogMonomial]] = {}
        atoms: dict[Antichain, dict[str, LogMonomial]] = {}

        for node in nodes:
            event_count = sum(
                count for row, count in counts.items() if event_matches(row, key, node, mode)
            )
            joint_count = sum(
                count
                for row, count in counts.items()
                if row[3] == key[3] and event_matches(row, key, node, mode)
            )
            if event_count <= 0 or target_count <= 0 or joint_count <= 0:
                raise AssertionError("supported key must belong to every keyed event and joint event")

            ratios = {
                "informative": Fraction(total_count, event_count),
                "misinformative": Fraction(target_count, joint_count),
                "net": Fraction(joint_count * total_count, target_count * event_count),
            }
            cumulatives[node] = {
                component: LogMonomial.log_fraction(ratio) for component, ratio in ratios.items()
            }
            atoms[node] = {}
            for component in ("informative", "misinformative", "net"):
                lower_sum = sum_monomials(atoms[lower][component] for lower in strict_lower[node])
                atoms[node][component] = cumulatives[node][component] - lower_sum

        weight = Fraction(key_count, total_count)
        top_node = (0b111,)
        average_top = average_top + cumulatives[top_node]["net"].scale(weight)
        for node in nodes:
            node_name = antichain_text(node)
            for component in ("informative", "misinformative", "net"):
                value = atoms[node][component]
                local_atoms[node_name][component].append(value)
                averaged[node_name][component] = averaged[node_name][component] + value.scale(weight)

    reconstruction = sum_monomials(values["net"] for values in averaged.values())
    if reconstruction != average_top:
        raise AssertionError("Möbius atoms did not reconstruct the greatest-node mutual information")

    return AuditResult(
        row_count=total_count,
        support_size=len(counts),
        event_mode=mode,
        atoms=averaged,
        local_constant={
            node: {component: len(set(values)) == 1 for component, values in components.items()}
            for node, components in local_atoms.items()
        },
        mutual_information=average_top,
        reconstruction=reconstruction,
    )


def expected_families() -> dict[str, tuple[Fraction, Fraction, Fraction]]:
    """Map node names to hat/tilde net ratios and family multiplicity."""

    return {
        "{{1},{2},{3}}": (Fraction(16, 11), Fraction(8, 5), Fraction(1)),
        "{{1},{2}}": (Fraction(11, 10), Fraction(15, 14), Fraction(3)),
        "{{1},{23}}": (Fraction(25, 22), Fraction(49, 45), Fraction(3)),
        "{{12},{13},{23}}": (Fraction(352, 125), Fraction(540, 343), Fraction(1)),
    }


def family_nodes(representative: str) -> tuple[str, ...]:
    if representative == "{{1},{2},{3}}":
        return (representative,)
    if representative == "{{1},{2}}":
        return ("{{1},{2}}", "{{1},{3}}", "{{2},{3}}")
    if representative == "{{1},{23}}":
        return ("{{1},{23}}", "{{2},{13}}", "{{3},{12}}")
    if representative == "{{12},{13},{23}}":
        return (representative,)
    raise AssertionError(f"unknown representative {representative}")


def assert_exact_witness(hat: AuditResult, tilde: AuditResult) -> dict[str, object]:
    expected = expected_families()
    nonzero_nodes: set[str] = set()
    for representative, (hat_ratio, tilde_ratio, _) in expected.items():
        for node in family_nodes(representative):
            nonzero_nodes.add(node)
            if hat.atoms[node]["net"].exact_ratio() != hat_ratio:
                raise AssertionError(f"unexpected hat ratio at {node}")
            if tilde.atoms[node]["net"].exact_ratio() != tilde_ratio:
                raise AssertionError(f"unexpected tilde ratio at {node}")

    all_nodes = set(hat.atoms)
    if all_nodes != set(tilde.atoms) or len(all_nodes) != 18:
        raise AssertionError("witnesses must use the same complete 18-node lattice")
    for node in all_nodes - nonzero_nodes:
        if hat.atoms[node]["net"] != ZERO or tilde.atoms[node]["net"] != ZERO:
            raise AssertionError(f"expected exact zero at {node}")

    differing = sorted(node for node in all_nodes if hat.atoms[node]["net"] != tilde.atoms[node]["net"])
    if len(differing) != 8:
        raise AssertionError(f"expected 8/18 different atoms, got {len(differing)}")
    if hat.mutual_information.exact_ratio() != Fraction(8):
        raise AssertionError("hat atoms must reconstruct exp(3 ln 2) = 8")
    if tilde.mutual_information.exact_ratio() != Fraction(4):
        raise AssertionError("tilde atoms must reconstruct exp(2 ln 2) = 4")

    if not all(all(components.values()) for components in hat.local_constant.values()):
        raise AssertionError("hat local atoms unexpectedly vary over its equiprobable support")
    if not all(all(components.values()) for components in tilde.local_constant.values()):
        raise AssertionError("tilde local atoms unexpectedly vary over its equiprobable support")

    return {
        "lattice_node_count": 18,
        "different_net_atom_count": len(differing),
        "equal_net_atom_count": 18 - len(differing),
        "different_nodes": differing,
        "hat_mi_product": "8/1",
        "tilde_mi_product": "4/1",
        "every_local_component_atom_constant_on_hat_support": True,
        "every_local_component_atom_constant_on_tilde_support": True,
    }


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", type=Path)
    args = parser.parse_args()

    hat_rows = hat_system()
    tilde_rows = tilde_system()
    relation_rows = relation_mutation_system()
    hat = evaluate(hat_rows)
    tilde = evaluate(tilde_rows)
    exact_summary = assert_exact_witness(hat, tilde)
    hat_construction_audit = construction_audit(hat_rows, "hat")
    tilde_construction_audit = construction_audit(tilde_rows, "tilde")
    hat_descriptor_audit, hat_descriptors, hat_descriptor_sum = descriptor_model_audit(
        hat_rows, "hat"
    )
    tilde_descriptor_audit, tilde_descriptors, tilde_descriptor_sum = descriptor_model_audit(
        tilde_rows, "tilde"
    )
    if hat_descriptors != tilde_descriptors:
        raise AssertionError("the two generated laws must have equal Lemma 4 descriptor vectors")
    if hat.mutual_information == tilde.mutual_information:
        raise AssertionError("the descriptor collision must have unequal mutual information")
    if hat.atoms == tilde.atoms:
        raise AssertionError("the descriptor collision must distinguish the Sx atom vectors")

    # Mutation 1: replacing the paper-defined inclusive union by intersection
    # still defines a finite lattice calculation, but it must not reproduce the
    # native Sx atom vector.
    intersection_hat = evaluate(hat_rows, mode="intersection")
    if intersection_hat.atoms == hat.atoms:
        raise AssertionError("union-to-intersection mutation survived")

    # Mutation 2: substituting the now row-derived Lemma 4 descriptors for
    # SxPID atoms reconstructs the hat MI accidentally but provably overcounts
    # the tilde MI by log(2).
    if (
        hat_descriptor_sum != tilde_descriptor_sum
        or hat_descriptor_sum != hat.mutual_information
        or tilde_descriptor_sum == tilde.mutual_information
    ):
        raise AssertionError("descriptor-substitution mutation was not killed")

    # Mutation 3: changing the cross-coordinate relation changes the exact
    # distribution-dependent atom vector; the checker must detect it.
    relation_mutation = evaluate(relation_rows)
    if relation_mutation.atoms == tilde.atoms:
        raise AssertionError("relation mutation survived")

    repo = Path(__file__).resolve().parents[3]
    rust_test = repo / "crates/pid-core/tests/sxpid_relation_witness.rs"
    rust_kernel = repo / "crates/pid-core/src/sxpid.rs"
    evidence: dict[str, object] = {
        "schema": "pid-rs.foundation.sxpid-lcr-exact-audit.v2",
        "audit_date": "2026-07-25",
        "method": {
            "arithmetic": "fractions.Fraction plus formal prime-exponent logarithms",
            "event_semantics": "independently counted keyed equality-event unions",
            "lattice": "generated all nonempty antichains of the seven nonempty 3-source subsets",
            "mobius": "recursive exact inversion under independently generated redundancy order",
            "lcr_premises": (
                "exact finite-law tests of Definition 6(i)--(iii), followed by row-derived "
                "minimal recovering antichains and Lemma 4 entropies"
            ),
            "pid_rs_imported": False,
            "third_party_packages": False,
        },
        "bindings": {
            "checker_sha256": sha256_file(Path(__file__).resolve()),
            "rust_regression_sha256": sha256_file(rust_test),
            "rust_kernel_sha256": sha256_file(rust_kernel),
            "hat_rows_sha256": row_digest(hat_rows),
            "tilde_rows_sha256": row_digest(tilde_rows),
            "relation_mutation_rows_sha256": row_digest(relation_rows),
        },
        "descriptor_factorization_premises": {
            "paper_domain": "Lyu--Clark--Raviv Definition 6 finite witness laws",
            "row_construction": {
                "hat": hat_construction_audit,
                "tilde": tilde_construction_audit,
            },
            "hat": hat_descriptor_audit,
            "tilde": tilde_descriptor_audit,
            "complete_descriptor_vectors_equal": True,
            "mutual_information_values_differ": True,
            "sxpid_net_atom_vectors_differ": True,
            "sxpid_descriptor_factorization_refuted_on_this_witness": True,
        },
        "exact_summary": exact_summary,
        "hat": hat.json_value(),
        "tilde": tilde.json_value(),
        "mutations": {
            "union_to_intersection_killed": True,
            "union_result_digest": canonical_digest(hat.json_value()),
            "intersection_result_digest": canonical_digest(intersection_hat.json_value()),
            "three_one_bit_descriptor_substitution_killed_on_tilde": True,
            "descriptor_product": fraction_text(tilde_descriptor_sum.exact_ratio() or Fraction(0)),
            "tilde_required_product": "4/1",
            "cross_relation_mutation_killed": True,
            "tilde_result_digest": canonical_digest(tilde.json_value()),
            "relation_mutation_result_digest": canonical_digest(relation_mutation.json_value()),
        },
    }

    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.write_evidence:
        args.write_evidence.parent.mkdir(parents=True, exist_ok=True)
        args.write_evidence.write_text(rendered, encoding="utf-8")
        print(f"PASS: wrote {args.write_evidence}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
