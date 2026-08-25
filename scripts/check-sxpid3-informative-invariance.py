#!/usr/bin/env python3
"""Exact bounded audit of SxPID3 lattice semantics and informative invariance.

This checker independently reconstructs the three-source antichain carrier, redundancy order,
zeta matrix, exact Mobius inverse, sigma/kappa distinction, a minimal supported event witness, and
every labeled binary count table of total mass 1 through 5.  On all 20,348 tables it checks by
exact positive-rational products that every informative cumulative, and therefore every fixed
Mobius atom, is determined by the complete source marginal rather than the target kernel.  The
tables represent 20,164 primitive rational laws after common-factor reduction.

The exhaustive computation is bounded software evidence.  The accompanying Lean theorem is the
arbitrary-finite-alphabet algebraic proof.  Neither route proves MGW paper correspondence, current
Rust refinement, a misinformative or net invariance, sampling-to-population inference, a
continuous-estimator result, causality, scientific priority, or model-independent PID validity.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import math
import sys
from typing import Final, Iterable, Iterator, Sequence


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-sxpid3-informative-invariance.py requires "
        "Python 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


FORMAT: Final[str] = "/pid-rs/sxpid3-informative-invariance-check/v1"
SOURCE_BITS: Final[tuple[int, ...]] = (1, 2, 4)
MASKS: Final[tuple[int, ...]] = tuple(range(1, 8))
SOURCE_STATES: Final[tuple[tuple[int, int, int], ...]] = tuple(
    itertools.product(range(2), repeat=3)
)
TARGET_VALUES: Final[tuple[int, ...]] = tuple(range(2))
JOINT_STATES: Final[tuple[tuple[tuple[int, int, int], int], ...]] = tuple(
    (source, target) for source in SOURCE_STATES for target in TARGET_VALUES
)
MAX_TOTAL: Final[int] = 5
EXPECTED_ANTICHAINS: Final[tuple[tuple[int, ...], ...]] = (
    (1,), (2,), (3,), (4,), (5,), (6,), (7,),
    (1, 2), (1, 4), (1, 6), (2, 4), (2, 5), (3, 4),
    (3, 5), (3, 6), (5, 6), (1, 2, 4), (3, 5, 6),
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
# Same-route semantic drift anchor, not an independent truth source, paper-correspondence proof,
# or Rust-refinement result.  The explicit antichain, zeta, Mobius, and mask pins above remain the
# human-reviewable acceptance anchors; this digest binds their combined version-1 registry.
EXPECTED_SEMANTIC_REGISTRY_SHA256: Final[str] = (
    "34243da13712935eb39935b01461d4837235c5ad4bcbfee0a4c02e25b4fed0be"
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


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
    """MGW/Williams--Beer order: every right branch contains a left branch."""
    return all(any(mask_subset(a, b) for a in left) for b in right)


def zeta_matrix(nodes: Sequence[tuple[int, ...]]) -> list[list[int]]:
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
        pivot = next((row for row in range(column, size) if augmented[row][column]), None)
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
            sum((Fraction(left[i][k]) * Fraction(right[k][j]) for k in range(len(right))),
                start=Fraction(0))
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
        require(
            all(value.denominator == 1 for value in row),
            "MOBIUS.integer_coefficient",
        )
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
    return any(
        all(anchor[index] == candidate[index] for index, bit in enumerate(SOURCE_BITS) if mask & bit)
        for mask in antichain
    )


def verify_mask_coordinate_binding() -> None:
    require(SOURCE_BITS == (1, 2, 4), "MASK.source_bit_registry")
    anchor = (0, 0, 0)
    flips = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    expected = (
        (False, True, True),
        (True, False, True),
        (True, True, False),
    )
    observed = tuple(
        tuple(event_matches((bit,), anchor, candidate) for bit in (1, 2, 4))
        for candidate in flips
    )
    require(observed == expected, "MASK.coordinate_sentinels")


def compositions(total: int, width: int) -> Iterator[tuple[int, ...]]:
    """All labeled weak compositions in lexicographic bar positions."""
    if width == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for tail in compositions(total - first, width - 1):
            yield (first,) + tail


def source_marginal(joint_counts: Sequence[int]) -> tuple[int, ...]:
    return tuple(
        joint_counts[2 * source_index] + joint_counts[2 * source_index + 1]
        for source_index in range(len(SOURCE_STATES))
    )


def informative_products_from_source(
    counts: Sequence[int],
    nodes: Sequence[tuple[int, ...]],
) -> tuple[Fraction, ...]:
    total = sum(counts)
    require(total > 0, "INVARIANCE.positive_total")
    products: list[Fraction] = []
    for antichain in nodes:
        product = Fraction(1)
        for anchor_index, anchor_count in enumerate(counts):
            if anchor_count == 0:
                continue
            anchor = SOURCE_STATES[anchor_index]
            event_count = sum(
                candidate_count
                for candidate, candidate_count in zip(SOURCE_STATES, counts, strict=True)
                if event_matches(antichain, anchor, candidate)
            )
            require(0 < event_count <= total, "INVARIANCE.source_event_bounds")
            product *= Fraction(total, event_count) ** anchor_count
        products.append(product)
    return tuple(products)


def informative_products_from_joint(
    counts: Sequence[int],
    nodes: Sequence[tuple[int, ...]],
) -> tuple[Fraction, ...]:
    total = sum(counts)
    require(total > 0, "INVARIANCE.positive_total")
    products: list[Fraction] = []
    for antichain in nodes:
        product = Fraction(1)
        for joint_index, cell_count in enumerate(counts):
            if cell_count == 0:
                continue
            anchor = JOINT_STATES[joint_index][0]
            # Keep this route independent of the cached eight-cell source aggregation.
            event_count = sum(
                candidate_count
                for (candidate_source, _candidate_target), candidate_count in
                zip(JOINT_STATES, counts, strict=True)
                if event_matches(antichain, anchor, candidate_source)
            )
            require(0 < event_count <= total, "INVARIANCE.joint_event_bounds")
            product *= Fraction(total, event_count) ** cell_count
        products.append(product)
    return tuple(products)


def mobius_products(
    cumulatives: Sequence[Fraction], mobius: Sequence[Sequence[Fraction]]
) -> tuple[Fraction, ...]:
    values: list[Fraction] = []
    for row in mobius:
        product = Fraction(1)
        for cumulative, coefficient in zip(cumulatives, row, strict=True):
            require(coefficient.denominator == 1, "MOBIUS.integer_coefficient")
            product *= cumulative ** coefficient.numerator
        values.append(product)
    return tuple(values)


def misinformative_product(
    joint_counts: Sequence[int], antichain: tuple[int, ...]
) -> Fraction:
    total = sum(joint_counts)
    require(total > 0, "NEGATIVE_CONTROL.positive_total")
    target_counts = tuple(
        sum(
            joint_counts[index]
            for index, (_, candidate_target) in enumerate(JOINT_STATES)
            if candidate_target == target
        )
        for target in TARGET_VALUES
    )
    product = Fraction(1)
    for joint_index, cell_count in enumerate(joint_counts):
        if cell_count == 0:
            continue
        anchor_source, anchor_target = JOINT_STATES[joint_index]
        restricted_count = sum(
            candidate_count
            for (candidate_source, candidate_target), candidate_count in
            zip(JOINT_STATES, joint_counts, strict=True)
            if candidate_target == anchor_target
            and event_matches(antichain, anchor_source, candidate_source)
        )
        target_count = target_counts[anchor_target]
        require(0 < restricted_count <= target_count <= total, "NEGATIVE_CONTROL.event_bounds")
        product *= Fraction(target_count, restricted_count) ** cell_count
    return product


def sigma(mask: int) -> tuple[int, ...]:
    return tuple(bit for bit in SOURCE_BITS if mask & bit)


def kappa(mask: int) -> tuple[int, ...]:
    return (mask,)


def event_on_support(
    antichain: tuple[int, ...],
    anchor: tuple[int, int, int],
    support: Iterable[tuple[int, int, int]],
) -> set[tuple[int, int, int]]:
    return {candidate for candidate in support if event_matches(antichain, anchor, candidate)}


def verify_sigma_kappa() -> dict[str, object]:
    masks = tuple(mask for mask in MASKS if mask.bit_count() > 1)
    for mask in masks:
        require(redundancy_le(sigma(mask), kappa(mask)), "SIGMA_KAPPA.forward_order")
        require(not redundancy_le(kappa(mask), sigma(mask)), "SIGMA_KAPPA.strict_poset")
        for anchor in SOURCE_STATES:
            sigma_event = event_on_support(sigma(mask), anchor, SOURCE_STATES)
            kappa_event = event_on_support(kappa(mask), anchor, SOURCE_STATES)
            require(kappa_event <= sigma_event, "SIGMA_KAPPA.event_inclusion")

    anchor = (0, 0, 0)
    witness = (0, 1, 0)
    mask = 3
    singleton_support = (anchor,)
    witness_support = (anchor, witness)
    require(
        event_on_support(sigma(mask), anchor, singleton_support)
        == event_on_support(kappa(mask), anchor, singleton_support),
        "SIGMA_KAPPA.no_unconditional_event_strictness",
    )
    require(
        witness in event_on_support(sigma(mask), anchor, witness_support)
        and witness not in event_on_support(kappa(mask), anchor, witness_support),
        "SIGMA_KAPPA.support_witness",
    )
    # One supported row cannot distinguish two anchor-containing events; two rows suffice.
    for one_row in SOURCE_STATES:
        support = (one_row,)
        require(
            event_on_support(sigma(mask), one_row, support)
            == event_on_support(kappa(mask), one_row, support),
            "SIGMA_KAPPA.minimality_one_row",
        )

    witness_joint_counts = [0] * len(JOINT_STATES)
    witness_joint_counts[JOINT_STATES.index((anchor, 0))] = 1
    witness_joint_counts[JOINT_STATES.index((witness, 0))] = 1
    source_counts = source_marginal(witness_joint_counts)
    informative_sigma = informative_products_from_source(source_counts, (sigma(mask),))[0]
    informative_kappa = informative_products_from_source(source_counts, (kappa(mask),))[0]
    require(informative_sigma == 1, "SIGMA_KAPPA.witness_sigma_product")
    require(informative_kappa == 4, "SIGMA_KAPPA.witness_kappa_product")
    # With a constant target, the corresponding misinformative products equal the informative
    # products, so both signed-net products are exactly one.  Net-only checking misses the event
    # distinction.
    misinformative_sigma = informative_sigma
    misinformative_kappa = informative_kappa
    require(
        informative_sigma / misinformative_sigma
        == informative_kappa / misinformative_kappa
        == 1,
        "SIGMA_KAPPA.net_only_blindness",
    )
    return {
        "masks_checked": list(masks),
        "minimal_supported_rows": 2,
        "witness": {
            "anchor": list(anchor),
            "candidate": list(witness),
            "mask": mask,
            "informative_product_kappa": str(informative_kappa),
            "informative_product_sigma": str(informative_sigma),
            "net_product_both": "1",
        },
    }


def verify_prohibited_invariance_transfer() -> dict[str, object]:
    """Same source marginal does not imply misinformative or signed-net invariance."""
    first = (0, 0, 0)
    second = (1, 1, 1)
    constant_target = [0] * len(JOINT_STATES)
    copied_target = [0] * len(JOINT_STATES)
    constant_target[JOINT_STATES.index((first, 0))] = 1
    constant_target[JOINT_STATES.index((second, 0))] = 1
    copied_target[JOINT_STATES.index((first, 0))] = 1
    copied_target[JOINT_STATES.index((second, 1))] = 1
    require(
        source_marginal(constant_target) == source_marginal(copied_target),
        "NEGATIVE_CONTROL.source_marginal",
    )
    top = (7,)
    informative_constant = informative_products_from_joint(constant_target, (top,))[0]
    informative_copied = informative_products_from_joint(copied_target, (top,))[0]
    misinformative_constant = misinformative_product(constant_target, top)
    misinformative_copied = misinformative_product(copied_target, top)
    net_constant = informative_constant / misinformative_constant
    net_copied = informative_copied / misinformative_copied
    require(
        informative_constant == informative_copied == 4,
        "NEGATIVE_CONTROL.informative_invariant",
    )
    require(
        misinformative_constant == 4 and misinformative_copied == 1,
        "NEGATIVE_CONTROL.misinformative_changes",
    )
    require(net_constant == 1 and net_copied == 4, "NEGATIVE_CONTROL.net_changes")
    return {
        "constant_target": {
            "informative_product": "4",
            "misinformative_product": "4",
            "net_product": "1",
        },
        "copied_target": {
            "informative_product": "4",
            "misinformative_product": "1",
            "net_product": "4",
        },
        "node": "07",
        "same_source_marginal": True,
    }


def verify_exhaustive_invariance(
    nodes: Sequence[tuple[int, ...]], mobius: Sequence[Sequence[Fraction]]
) -> dict[str, int]:
    source_cache: dict[tuple[int, ...], tuple[Fraction, ...]] = {}
    table_count = 0
    primitive_law_count = 0
    informative_cumulative_verdicts = 0
    informative_atom_verdicts = 0
    for total in range(1, MAX_TOTAL + 1):
        for joint_counts in compositions(total, len(JOINT_STATES)):
            table_count += 1
            primitive_law_count += int(math.gcd(*joint_counts) == 1)
            marginal = source_marginal(joint_counts)
            source_products = source_cache.get(marginal)
            if source_products is None:
                source_products = informative_products_from_source(marginal, nodes)
                source_cache[marginal] = source_products
            joint_products = informative_products_from_joint(joint_counts, nodes)
            require(joint_products == source_products, "INVARIANCE.cumulative_product")
            informative_cumulative_verdicts += len(nodes)
            source_atoms = mobius_products(source_products, mobius)
            joint_atoms = mobius_products(joint_products, mobius)
            require(joint_atoms == source_atoms, "INVARIANCE.atom_product")
            informative_atom_verdicts += len(nodes)

    require(table_count == 20_348, "EXHAUSTIVE.table_count")
    require(primitive_law_count == 20_164, "EXHAUSTIVE.primitive_law_count")
    require(len(source_cache) == 1_286, "EXHAUSTIVE.source_marginal_count")
    require(informative_cumulative_verdicts == 366_264, "EXHAUSTIVE.cumulative_verdicts")
    require(informative_atom_verdicts == 366_264, "EXHAUSTIVE.atom_verdicts")
    return {
        "binary_labeled_count_tables": table_count,
        "distinct_source_marginal_counts": len(source_cache),
        "informative_cumulative_product_verdicts": informative_cumulative_verdicts,
        "informative_atom_product_verdicts": informative_atom_verdicts,
        "maximum_total_count": MAX_TOTAL,
        "primitive_rational_laws": primitive_law_count,
    }


def main() -> int:
    nodes = enumerate_antichains()
    require(nodes == EXPECTED_ANTICHAINS, "ANTICHAIN.registry")
    verify_mask_coordinate_binding()
    zeta = zeta_matrix(nodes)
    zeta_signatures = tuple("".join(map(str, row)) for row in zeta)
    require(zeta_signatures == EXPECTED_ZETA_SIGNATURES, "ZETA.row_signatures")
    require(sum(map(sum, zeta)) == 129, "ZETA.one_count")
    mobius = inverse_matrix_exact(zeta)
    require(sparse_integer_rows(mobius) == EXPECTED_MOBIUS_SPARSE, "MOBIUS.sparse_rows")
    expected_identity = identity(len(nodes))
    require(matrix_product(mobius, zeta) == expected_identity, "MOBIUS.left_inverse")
    require(matrix_product(zeta, mobius) == expected_identity, "MOBIUS.right_inverse")
    mobius_nonzero = sum(value != 0 for row in mobius for value in row)
    require(mobius_nonzero == 65, "MOBIUS.nonzero_count")
    require(
        {value for row in mobius for value in row} <= {Fraction(-1), Fraction(0), Fraction(1)},
        "MOBIUS.coefficient_range",
    )
    require(
        max(max(sum(value != 0 for value in row) for row in mobius),
            max(sum(mobius[row][column] != 0 for row in range(len(nodes)))
                for column in range(len(nodes)))) == 8,
        "MOBIUS.maximum_support",
    )

    sigma_kappa = verify_sigma_kappa()
    prohibited_transfer = verify_prohibited_invariance_transfer()
    exhaustive = verify_exhaustive_invariance(nodes, mobius)
    result = {
        "exhaustive_binary_scope": exhaustive,
        "format": FORMAT,
        "gate": "GO",
        "lattice": {
            "antichain_count": len(nodes),
            "mobius_nonzero_count": mobius_nonzero,
            "mobius_values": [-1, 0, 1],
            "two_sided_inverse": True,
            "zeta_one_count": sum(map(sum, zeta)),
        },
        "nonclaims": [
            "not_mgw_paper_correspondence",
            "not_misinformative_or_signed_net_invariance",
            "not_rust_parser_binary64_or_api_refinement",
            "not_arbitrary_alphabet_exhaustiveness",
            "not_sampling_to_population_continuous_estimator_causal_or_priority_claim",
        ],
        "prohibited_transfer_witness": prohibited_transfer,
        "sigma_kappa": sigma_kappa,
        "theorem_scope": {
            "changed": "finite target alphabet and target-conditioned allocation may differ; the complete source marginal is unchanged",
            "conclusion": "all averaged informative cumulatives agree; every coordinate of any one fixed linear transform agrees (called Mobius atoms only after separately proving the coefficient matrix is the intended inverse)",
            "fixed": "finite source product alphabet, complete source marginal, source events, lattice, coefficients, logarithm base; the two target alphabets may differ but must each be finite",
            "required_probability_semantics": "nonnegative total-one laws, nonempty collection family, positive-support averaging",
        },
    }
    semantic_registry_sha256 = canonical_sha256(
        {
            "antichains": [list(node) for node in nodes],
            "mobius": [[int(value) for value in row] for row in mobius],
            "sigma_kappa": sigma_kappa,
            "prohibited_transfer_witness": prohibited_transfer,
            "theorem_scope": result["theorem_scope"],
            "zeta": zeta,
        }
    )
    require(
        semantic_registry_sha256 == EXPECTED_SEMANTIC_REGISTRY_SHA256,
        "SEMANTIC.registry_sha256",
    )
    result["semantic_registry_sha256"] = semantic_registry_sha256
    print(canonical_json(result), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ArithmeticError, RuntimeError, ValueError) as error:
        print(f"SxPID3 informative invariance: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
