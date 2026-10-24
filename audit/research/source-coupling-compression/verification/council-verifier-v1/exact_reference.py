"""Exact categorical MGW reference for three binary original sources.

This is a separately written Python verification module, not production Rust.
A returned positive Fraction P represents ln(P)/N nats; P itself has no units.
No logarithms or floats are evaluated. No scientific work runs at import.
See FIRST.md and INTERFACE.md for exposure, limits and unclosed edges.
"""

from fractions import Fraction
from itertools import combinations
from math import gcd

SCHEMA = "mgw-three-binary-source-reference-v1"
MAX_TARGET_SIZE = 4
MAX_TOTAL_COUNT = 32768
MAX_OCCUPIED_CELLS = 32
MAX_INTEGER_BITS = 1048576
MAX_RETAINED_COMPONENT_BITS = 67108864

Branch = tuple[int, ...]
Node = tuple[Branch, ...]
MaskKey = tuple[int, ...]
JointKey = tuple[int, int, int, int]
COMPONENTS = ("plus", "minus", "net")


class ReferenceError(ValueError):
    """Invalid count law or failed exact semantic/algebra obligation."""


class ReferenceResourceError(ReferenceError):
    """Predeclared exact-reference resource limit exceeded."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceError(message)


def _bounded(value: Fraction) -> Fraction:
    """Check both reduced integers, retaining exact signs through P versus 1."""
    _require(value > 0, "product must be a positive rational")
    if (
        value.numerator.bit_length() > MAX_INTEGER_BITS
        or value.denominator.bit_length() > MAX_INTEGER_BITS
    ):
        raise ReferenceResourceError("product integer bit cap exceeded")
    return value


def _multiply(left: Fraction, right: Fraction) -> Fraction:
    """Cross-cancel before allocation; conservatively preflight integer sizes."""
    _require(left > 0 and right > 0, "nonpositive product factor")
    a, b = left.numerator, left.denominator
    c, d = right.numerator, right.denominator
    first, second = gcd(a, d), gcd(c, b)
    a, d = a // first, d // first
    c, b = c // second, b // second
    if (
        a.bit_length() + c.bit_length() > MAX_INTEGER_BITS
        or b.bit_length() + d.bit_length() > MAX_INTEGER_BITS
    ):
        raise ReferenceResourceError("multiplication preflight bit cap exceeded")
    return _bounded(Fraction(a * c, b * d))


def _power(base: Fraction, exponent: int) -> Fraction:
    """Preflight before an exact power; negative exponents invert the base."""
    _require(type(exponent) is int, "exponent must be an exact integer")
    _require(base > 0, "power base must be positive")
    if exponent == 0:
        return Fraction(1)
    if exponent < 0:
        base = Fraction(base.denominator, base.numerator)
        exponent = -exponent
    if (
        base.numerator.bit_length() * exponent > MAX_INTEGER_BITS
        or base.denominator.bit_length() * exponent > MAX_INTEGER_BITS
    ):
        raise ReferenceResourceError("power preflight bit cap exceeded")
    return _bounded(base**exponent)


def _divide(left: Fraction, right: Fraction) -> Fraction:
    _require(right > 0, "division by nonpositive product")
    return _multiply(left, Fraction(right.denominator, right.numerator))


def _subsets() -> tuple[Branch, ...]:
    return tuple(
        branch
        for length in range(1, 4)
        for branch in combinations((1, 2, 3), length)
    )


def _below(lower: Node, upper: Node) -> bool:
    return all(
        any(set(lower_branch).issubset(upper_branch) for lower_branch in lower)
        for upper_branch in upper
    )


def _mask(node: Node) -> MaskKey:
    return tuple(sorted(sum(1 << (i - 1) for i in branch) for branch in node))


def _event(node: Node, anchor: tuple[int, ...], source: tuple[int, ...]) -> bool:
    return any(
        all(source[i - 1] == anchor[i - 1] for i in branch)
        for branch in node
    )


def _truth_event(node: Node, matched: frozenset[int]) -> bool:
    return any(set(branch).issubset(matched) for branch in node)


def _original_carrier() -> tuple[Node, ...]:
    """Enumerate complete original antichains, independently of observed support."""
    branches = _subsets()
    families = []
    for length in range(1, len(branches) + 1):
        for family in combinations(branches, length):
            if any(
                set(a).issubset(b) or set(b).issubset(a)
                for a, b in combinations(family, 2)
            ):
                continue
            families.append(tuple(sorted(family)))
    _require(len(families) == 18, "complete carrier must have eighteen nodes")
    _require(len(set(families)) == 18, "duplicate original node")
    ordered = tuple(
        sorted(
            families,
            key=lambda node: (
                sum(other != node and _below(other, node) for other in families),
                node,
            ),
        )
    )
    _require(len({_mask(node) for node in ordered}) == 18, "noninjective mask keys")
    for a in ordered:
        _require(_below(a, a), "nonreflexive carrier order")
        for b in ordered:
            _require(
                a == b or not (_below(a, b) and _below(b, a)),
                "nonantisymmetric carrier order",
            )
            for c in ordered:
                _require(
                    not (_below(a, b) and _below(b, c)) or _below(a, c),
                    "nontransitive carrier order",
                )
    # Full binary source alphabets realize every matched-coordinate pattern.
    patterns = tuple(
        frozenset(pattern)
        for length in range(4)
        for pattern in combinations((1, 2, 3), length)
    )
    for a in ordered:
        for b in ordered:
            truth_order = all(
                not _truth_event(b, pattern) or _truth_event(a, pattern)
                for pattern in patterns
            )
            _require(_below(a, b) == truth_order, "order/DNF truth-table mismatch")
    return ordered


def _matrices(nodes: tuple[Node, ...]) -> tuple[tuple, tuple]:
    """Invert the explicit zeta matrix by Fraction Gauss-Jordan elimination."""
    size = len(nodes)
    zeta = tuple(
        tuple(int(_below(beta, alpha)) for beta in nodes) for alpha in nodes
    )
    for row in range(size):
        _require(zeta[row][row] == 1, "nonunit zeta diagonal")
        for col in range(row + 1, size):
            _require(zeta[row][col] == 0, "carrier is not a linear extension")
    work = [
        [Fraction(value) for value in zeta[row]]
        + [Fraction(int(row == col)) for col in range(size)]
        for row in range(size)
    ]
    for col in range(size):
        pivot = next((row for row in range(col, size) if work[row][col]), None)
        _require(pivot is not None, "singular zeta matrix")
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
        divisor = work[col][col]
        work[col] = [value / divisor for value in work[col]]
        for row in range(size):
            if row == col:
                continue
            multiplier = work[row][col]
            work[row] = [
                old - multiplier * pivot_value
                for old, pivot_value in zip(work[row], work[col])
            ]
    for row in range(size):
        for col in range(size):
            _require(work[row][col] == int(row == col), "elimination did not yield I")
    rational_inverse = tuple(tuple(row[size:]) for row in work)
    _require(
        all(value.denominator == 1 for row in rational_inverse for value in row),
        "zeta inverse has noninteger entry",
    )
    inverse = tuple(
        tuple(value.numerator for value in row) for row in rational_inverse
    )
    for row in range(size):
        for col in range(size):
            expected = int(row == col)
            _require(
                sum(zeta[row][j] * inverse[j][col] for j in range(size)) == expected,
                "Z times U differs from I",
            )
            _require(
                sum(inverse[row][j] * zeta[j][col] for j in range(size)) == expected,
                "U times Z differs from I",
            )
    return zeta, inverse


def _validate_counts(
    counts: dict[JointKey, int], target_size: int
) -> tuple[tuple[tuple[JointKey, int], ...], int, int]:
    _require(type(target_size) is int, "target_size must be an exact integer")
    _require(1 <= target_size <= MAX_TARGET_SIZE, "target alphabet outside 1..4")
    _require(type(counts) is dict, "counts must be an exact dict")
    if len(counts) > MAX_OCCUPIED_CELLS:
        raise ReferenceResourceError("joint-key count cap exceeded")
    positive = []
    total = 0
    zeros = 0
    for key, count in counts.items():
        _require(type(key) is tuple and len(key) == 4, "joint key must have four entries")
        _require(all(type(value) is int for value in key), "labels must be exact integers")
        _require(all(value in (0, 1) for value in key[:3]), "source label is not binary")
        _require(0 <= key[3] < target_size, "target label outside declared alphabet")
        _require(type(count) is int, "count must be an exact integer")
        _require(count >= 0, "negative count")
        if count > MAX_TOTAL_COUNT:
            raise ReferenceResourceError("single count exceeds total-count cap")
        total += count
        if total > MAX_TOTAL_COUNT:
            raise ReferenceResourceError("total-count cap exceeded")
        if count:
            positive.append((key, count))
        else:
            zeros += 1
    _require(total > 0, "empty or zero-total count law")
    _require(len(positive) <= 8 * target_size, "occupied support exceeds full alphabet")
    return tuple(sorted(positive)), total, zeros


def _bit_sum(values) -> int:
    return sum(
        value.numerator.bit_length() + value.denominator.bit_length()
        for value in values
    )


def _retained_limit(cumulative: dict, atoms: dict) -> int:
    total = sum(
        _bit_sum(stage[component].values())
        for stage in (cumulative, atoms)
        for component in COMPONENTS
    )
    if total > MAX_RETAINED_COMPONENT_BITS:
        raise ReferenceResourceError("retained component-bit cap exceeded")
    return total


def _sign(product: Fraction) -> int:
    """Information sign: -1, 0 or 1, because natural log is strictly increasing."""
    return (product > 1) - (product < 1)


def evaluate_counts(
    counts: dict[JointKey, int], *, target_size: int = 4
) -> dict:
    """Evaluate one supplied empirical count law on the original 18-node carrier.

    Missing categories mean zero. Explicit zeros are validated then omitted.
    All keys and counts must have exact Python types; bool and float are invalid.
    Returned products are Fractions for ln(product)/total_count, in nats.
    No magnitude intervals, raw-data provenance or inference are certified.
    """
    occupied, total, explicit_zeros = _validate_counts(counts, target_size)
    nodes = _original_carrier()
    zeta, inverse = _matrices(nodes)
    keys = tuple(_mask(node) for node in nodes)
    target_counts = {target: 0 for target in range(target_size)}
    source_counts = {}
    for joint, count in occupied:
        target_counts[joint[3]] += count
        source_counts[joint[:3]] = source_counts.get(joint[:3], 0) + count
    cumulative = {component: {} for component in COMPONENTS}
    atoms = {component: {} for component in COMPONENTS}
    event_counts = {}
    for node, key in zip(nodes, keys):
        values = {component: Fraction(1) for component in COMPONENTS}
        local_counts = []
        for joint, weight in occupied:
            source, target = joint[:3], joint[3]
            event_total = 0
            event_target = 0
            for other, count in occupied:
                if _event(node, source, other[:3]):
                    event_total += count
                    if other[3] == target:
                        event_target += count
            target_total = target_counts[target]
            _require(
                0 < weight <= event_target <= event_total <= total,
                "positive anchor is not contained in its source event",
            )
            _require(
                event_target <= target_total <= total,
                "target-restricted event count is invalid",
            )
            bases = {
                "plus": Fraction(total, event_total),
                "minus": Fraction(target_total, event_target),
                "net": Fraction(total * event_target, event_total * target_total),
            }
            for component in COMPONENTS:
                values[component] = _multiply(
                    values[component], _power(bases[component], weight)
                )
            local_counts.append(
                (joint, weight, event_total, event_target, target_total)
            )
        _require(
            _divide(values["plus"], values["minus"]) == values["net"],
            "cumulative component ratio mismatch",
        )
        for component in COMPONENTS:
            cumulative[component][key] = values[component]
        event_counts[key] = tuple(local_counts)
        _retained_limit(cumulative, atoms)
    for row, key in enumerate(keys):
        for component in COMPONENTS:
            value = Fraction(1)
            for col, other in enumerate(keys):
                exponent = inverse[row][col]
                if exponent:
                    value = _multiply(
                        value, _power(cumulative[component][other], exponent)
                    )
            atoms[component][key] = value
        _require(
            _divide(atoms["plus"][key], atoms["minus"][key]) == atoms["net"][key],
            "atom component ratio mismatch",
        )
        _require(atoms["plus"][key] >= 1, "negative informative component atom")
        _require(atoms["minus"][key] >= 1, "negative misinformative component atom")
        _retained_limit(cumulative, atoms)
    for row, key in enumerate(keys):
        for component in COMPONENTS:
            reconstructed = Fraction(1)
            for col, other in enumerate(keys):
                if zeta[row][col]:
                    reconstructed = _multiply(reconstructed, atoms[component][other])
            _require(
                reconstructed == cumulative[component][key],
                "keyed component product zeta reconstruction mismatch",
            )
    mi_product = Fraction(1)
    for joint, weight in occupied:
        source_total = source_counts[joint[:3]]
        target_total = target_counts[joint[3]]
        direct_ratio = Fraction(total * weight, source_total * target_total)
        mi_product = _multiply(mi_product, _power(direct_ratio, weight))
    top = (7,)
    _require(cumulative["net"][top] == mi_product, "top product differs from joint MI")
    all_atoms = Fraction(1)
    for key in keys:
        all_atoms = _multiply(all_atoms, atoms["net"][key])
    _require(all_atoms == mi_product, "all atom products do not reconstruct joint MI")
    return {
        "schema": SCHEMA,
        "target_size": target_size,
        "total_count": total,
        "positive_joint_cells": len(occupied),
        "explicit_zero_entries_omitted": explicit_zeros,
        "keys": keys,
        "source_sets": {key: node for key, node in zip(keys, nodes)},
        "zeta": zeta,
        "inverse": inverse,
        "inverse_absolute_entry_sum": sum(abs(value) for row in inverse for value in row),
        "cumulative": cumulative,
        "atoms": atoms,
        "signs": {
            stage: {
                component: {
                    key: _sign(products[component][key]) for key in keys
                }
                for component in COMPONENTS
            }
            for stage, products in (("cumulative", cumulative), ("atoms", atoms))
        },
        "event_counts": event_counts,
        "mutual_information_product": mi_product,
        "retained_component_bits": _retained_limit(cumulative, atoms),
        "limits": {
            "max_total_count": MAX_TOTAL_COUNT,
            "max_target_size": MAX_TARGET_SIZE,
            "max_integer_bits": MAX_INTEGER_BITS,
            "max_retained_component_bits": MAX_RETAINED_COMPONENT_BITS,
        },
        "checks": {
            "carrier_nodes": 18,
            "truth_patterns": 8,
            "inverse_identity_entries_per_direction": 324,
            "component_zeta_reconstructions": 54,
            "cumulative_component_ratios": 18,
            "atom_component_ratios": 18,
            "joint_mi_top_and_full_sum": True,
        },
    }


def product_as_hex(product: Fraction) -> dict[str, str]:
    """Optional exact transport without changing Python decimal-integer guards."""
    _require(type(product) is Fraction, "transport input must be an exact Fraction")
    _bounded(product)
    return {
        "numerator_hex": format(product.numerator, "x"),
        "denominator_hex": format(product.denominator, "x"),
    }
