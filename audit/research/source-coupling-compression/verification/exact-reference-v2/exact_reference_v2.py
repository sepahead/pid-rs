"""Exact categorical MGW reference for three binary original sources.

This is a separately written Python verification module, not production Rust.
A returned positive Fraction P represents ln(P)/N nats; P itself has no units.
No logarithms or floats are evaluated. No scientific work runs at import.
Version 2 delays products with prime maps; see FIRST.md and CORRESPONDENCE.md.
"""

from fractions import Fraction
from itertools import combinations

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



# Factor maps use prime -> signed integer exponent, with zero entries omitted.
# They are internal exact representations; no logarithms or float tests are used.

def _raw_factor_add(left: dict[int, int], right, scale: int = 1) -> dict[int, int]:
    _require(type(scale) is int, "factor scale must be an exact integer")
    result = left.copy()
    for prime, exponent in right:
        new_exponent = result.get(prime, 0) + scale * exponent
        if new_exponent:
            result[prime] = new_exponent
        else:
            result.pop(prime, None)
    return result


def _factor_bounds(factors: dict[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """Inclusive integer-bit bounds for reduced numerator and denominator."""
    num_low = num_high = den_low = den_high = 0
    for prime, exponent in factors.items():
        _require(type(prime) is int and prime >= 2, "invalid internal factor")
        _require(type(exponent) is int and exponent != 0, "invalid internal exponent")
        bits = prime.bit_length()
        if exponent > 0:
            num_low += exponent * (bits - 1)
            num_high += exponent * bits
        else:
            den_low -= exponent * (bits - 1)
            den_high -= exponent * bits
    return (
        (num_low + 1, max(1, num_high)),
        (den_low + 1, max(1, den_high)),
    )


def _capped_integer_multiply(left: int, right: int) -> int:
    """Never allocate an integer product exceeding the unchanged bit cap."""
    if MAX_INTEGER_BITS < 1:
        raise ReferenceResourceError("product integer bit cap exceeded")
    _require(left > 0 and right > 0, "nonpositive integer factor")
    if left.bit_length() > MAX_INTEGER_BITS or right.bit_length() > MAX_INTEGER_BITS:
        raise ReferenceResourceError("product integer bit cap exceeded")
    if left == 1:
        return right
    if right == 1:
        return left
    bits = left.bit_length() + right.bit_length()
    if bits - 1 > MAX_INTEGER_BITS:
        raise ReferenceResourceError("product integer bit cap exceeded")
    if bits > MAX_INTEGER_BITS:
        # Construct 2^cap-1 without an intermediate with cap+1 bits.
        ceiling = ((1 << (MAX_INTEGER_BITS - 1)) - 1) * 2 + 1
        if left > ceiling // right:
            raise ReferenceResourceError("product integer bit cap exceeded")
    result = left * right
    if result.bit_length() > MAX_INTEGER_BITS:
        raise ReferenceResourceError("product integer bit cap exceeded")
    return result


def _capped_integer_power(base: int, exponent: int) -> int:
    _require(base >= 2 and exponent > 0, "invalid positive prime power")
    if MAX_INTEGER_BITS < 1:
        raise ReferenceResourceError("product integer bit cap exceeded")
    if base.bit_length() * exponent <= MAX_INTEGER_BITS:
        return base**exponent
    if (base.bit_length() - 1) * exponent >= MAX_INTEGER_BITS:
        raise ReferenceResourceError("product integer bit cap exceeded")
    # Ambiguous boundary: use exact guarded squaring rather than a loose refusal.
    result = 1
    power = base
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = _capped_integer_multiply(result, power)
        remaining //= 2
        if remaining:
            power = _capped_integer_multiply(power, power)
    return result


def _balanced_integer_product(values: list[int]) -> int:
    if not values:
        if MAX_INTEGER_BITS < 1:
            raise ReferenceResourceError("product integer bit cap exceeded")
        return 1
    level = sorted(values, key=int.bit_length)
    while len(level) > 1:
        next_level = []
        for index in range(0, len(level) - 1, 2):
            next_level.append(_capped_integer_multiply(level[index], level[index + 1]))
        if len(level) & 1:
            next_level.append(level[-1])
        level = next_level
    return level[0]


def _factor_integers(factors: dict[int, int]) -> tuple[int, int]:
    numerator = []
    denominator = []
    for prime, exponent in sorted(factors.items()):
        if exponent > 0:
            numerator.append(_capped_integer_power(prime, exponent))
        else:
            denominator.append(_capped_integer_power(prime, -exponent))
    return (
        _balanced_integer_product(numerator),
        _balanced_integer_product(denominator),
    )


def _factor_exact_bits(factors: dict[int, int]) -> tuple[int, int]:
    numerator, denominator = _factor_integers(factors)
    return numerator.bit_length(), denominator.bit_length()


def _factor_power(factors: dict[int, int], exponent: int) -> dict[int, int]:
    """Preserve v1's bit_length(base integer)*abs(exponent) preflight."""
    _require(type(exponent) is int, "exponent must be an exact integer")
    if exponent == 0:
        return {}
    magnitude = abs(exponent)
    bounds = _factor_bounds(factors)
    if any(low * magnitude > MAX_INTEGER_BITS for low, high in bounds):
        raise ReferenceResourceError("power preflight bit cap exceeded")
    if any(high * magnitude > MAX_INTEGER_BITS for low, high in bounds):
        bits = _factor_exact_bits(factors)
        if any(value * magnitude > MAX_INTEGER_BITS for value in bits):
            raise ReferenceResourceError("power preflight bit cap exceeded")
    return {prime: exponent * power for prime, power in factors.items()}


def _cross_cancelled_operands(left: dict[int, int], right: dict[int, int]):
    """Prime-map counterpart of v1's two cross gcds, retaining operand split."""
    first = {}
    second = {}
    for prime in left.keys() | right.keys():
        a = left.get(prime, 0)
        b = right.get(prime, 0)
        if a > 0 and b < 0:
            common = min(a, -b)
            a -= common
            b += common
        elif a < 0 and b > 0:
            common = min(-a, b)
            a += common
            b -= common
        if a:
            first[prime] = a
        if b:
            second[prime] = b
    return first, second


def _factor_multiply(left: dict[int, int], right: dict[int, int]) -> dict[int, int]:
    """Preserve v1's exact cross-cancelled operand bit-sum preflight."""
    first, second = _cross_cancelled_operands(left, right)
    first_bounds = _factor_bounds(first)
    second_bounds = _factor_bounds(second)
    if any(
        first_bounds[i][0] + second_bounds[i][0] > MAX_INTEGER_BITS
        for i in (0, 1)
    ):
        raise ReferenceResourceError("multiplication preflight bit cap exceeded")
    if any(
        first_bounds[i][1] + second_bounds[i][1] > MAX_INTEGER_BITS
        for i in (0, 1)
    ):
        a_bits = _factor_exact_bits(first)
        b_bits = _factor_exact_bits(second)
        if any(a_bits[i] + b_bits[i] > MAX_INTEGER_BITS for i in (0, 1)):
            raise ReferenceResourceError("multiplication preflight bit cap exceeded")
    return _raw_factor_add(left, right.items())


def _factor_divide(left: dict[int, int], right: dict[int, int]) -> dict[int, int]:
    return _factor_multiply(left, {prime: -power for prime, power in right.items()})


def _factor_payload_limit(cumulative: dict, atoms: dict) -> None:
    """Count repeated coordinates separately, exactly as v1's payload metric."""
    values = [
        factors
        for stage in (cumulative, atoms)
        for component in COMPONENTS
        for factors in stage[component].values()
    ]
    all_bounds = [_factor_bounds(factors) for factors in values]
    lower = sum(part[0] for bounds in all_bounds for part in bounds)
    upper = sum(part[1] for bounds in all_bounds for part in bounds)
    if lower > MAX_RETAINED_COMPONENT_BITS:
        raise ReferenceResourceError("retained component-bit cap exceeded")
    if upper > MAX_RETAINED_COMPONENT_BITS:
        exact = 0
        for factors in values:
            exact += sum(_factor_exact_bits(factors))
            if exact > MAX_RETAINED_COMPONENT_BITS:
                raise ReferenceResourceError("retained component-bit cap exceeded")


def _count_factorizer():
    """Return a per-law cache of immutable factorizations of bounded counts."""
    cache = {1: ()}

    def factor(value: int) -> tuple[tuple[int, int], ...]:
        _require(
            type(value) is int and 1 <= value <= MAX_TOTAL_COUNT,
            "count factorization outside declared positive count domain",
        )
        if value in cache:
            return cache[value]
        remaining = value
        divisor = 2
        factors = []
        while divisor * divisor <= remaining:
            exponent = 0
            while remaining % divisor == 0:
                remaining //= divisor
                exponent += 1
            if exponent:
                factors.append((divisor, exponent))
            divisor = 3 if divisor == 2 else divisor + 2
        if remaining > 1:
            factors.append((remaining, 1))
        reconstructed = 1
        for prime, exponent in factors:
            reconstructed *= prime**exponent
        _require(reconstructed == value, "small-count factorization reconstruction")
        result = tuple(factors)
        cache[value] = result
        return result

    return factor


def evaluate_counts(
    counts: dict[JointKey, int], *, target_size: int = 4
) -> dict:
    """Same exact v1 interface; delay large rational products using prime maps."""
    occupied, total, explicit_zeros = _validate_counts(counts, target_size)
    nodes = _original_carrier()
    zeta, inverse = _matrices(nodes)
    keys = tuple(_mask(node) for node in nodes)
    target_counts = {target: 0 for target in range(target_size)}
    source_counts = {}
    for joint, count in occupied:
        target_counts[joint[3]] += count
        source_counts[joint[:3]] = source_counts.get(joint[:3], 0) + count
    cumulative_factors = {component: {} for component in COMPONENTS}
    atom_factors = {component: {} for component in COMPONENTS}
    event_counts = {}
    factor_count = _count_factorizer()
    total_factors = factor_count(total)
    pair_cache = {}
    fraction_cache = {}

    def output_pair(factors):
        cache_key = tuple(sorted(factors.items()))
        if cache_key not in pair_cache:
            pair_cache[cache_key] = _factor_integers(factors)
        return pair_cache[cache_key]

    def output_fraction(factors):
        cache_key = tuple(sorted(factors.items()))
        if cache_key not in fraction_cache:
            numerator, denominator = output_pair(factors)
            # Ordinary shipped normalization; no private constructor or bypass.
            fraction_cache[cache_key] = _bounded(Fraction(numerator, denominator))
        return fraction_cache[cache_key]

    for node, key in zip(nodes, keys):
        values = {component: {} for component in COMPONENTS}
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
            event_factors = factor_count(event_total)
            event_target_factors = factor_count(event_target)
            target_factors = factor_count(target_total)
            plus = _raw_factor_add({}, total_factors)
            plus = _raw_factor_add(plus, event_factors, -1)
            minus = _raw_factor_add({}, target_factors)
            minus = _raw_factor_add(minus, event_target_factors, -1)
            # Independently assemble N*v/(u*t), rather than divide the two maps.
            net = _raw_factor_add({}, total_factors)
            net = _raw_factor_add(net, event_target_factors)
            net = _raw_factor_add(net, event_factors, -1)
            net = _raw_factor_add(net, target_factors, -1)
            bases = {"plus": plus, "minus": minus, "net": net}
            for component in COMPONENTS:
                values[component] = _factor_multiply(
                    values[component], _factor_power(bases[component], weight)
                )
            local_counts.append(
                (joint, weight, event_total, event_target, target_total)
            )
        _require(
            _factor_divide(values["plus"], values["minus"]) == values["net"],
            "cumulative component ratio mismatch",
        )
        for component in COMPONENTS:
            cumulative_factors[component][key] = values[component]
        event_counts[key] = tuple(local_counts)
        _factor_payload_limit(cumulative_factors, atom_factors)
    for row, key in enumerate(keys):
        for component in COMPONENTS:
            value = {}
            for col, other in enumerate(keys):
                exponent = inverse[row][col]
                if exponent:
                    value = _factor_multiply(
                        value,
                        _factor_power(cumulative_factors[component][other], exponent),
                    )
            atom_factors[component][key] = value
        _require(
            _factor_divide(atom_factors["plus"][key], atom_factors["minus"][key])
            == atom_factors["net"][key],
            "atom component ratio mismatch",
        )
        # Sign checks remain at the original logical checkpoint. Integer pairs
        # may be materialized early here, cached for ordinary Fraction output.
        plus_num, plus_den = output_pair(atom_factors["plus"][key])
        minus_num, minus_den = output_pair(atom_factors["minus"][key])
        _require(plus_num >= plus_den, "negative informative component atom")
        _require(minus_num >= minus_den, "negative misinformative component atom")
        _factor_payload_limit(cumulative_factors, atom_factors)
    for row, key in enumerate(keys):
        for component in COMPONENTS:
            reconstructed = {}
            for col, other in enumerate(keys):
                if zeta[row][col]:
                    reconstructed = _factor_multiply(
                        reconstructed, atom_factors[component][other]
                    )
            _require(
                reconstructed == cumulative_factors[component][key],
                "keyed component product zeta reconstruction mismatch",
            )
    mi_factors = {}
    for joint, weight in occupied:
        source_total = source_counts[joint[:3]]
        target_total = target_counts[joint[3]]
        ratio = _raw_factor_add({}, total_factors)
        ratio = _raw_factor_add(ratio, factor_count(weight))
        ratio = _raw_factor_add(ratio, factor_count(source_total), -1)
        ratio = _raw_factor_add(ratio, factor_count(target_total), -1)
        mi_factors = _factor_multiply(mi_factors, _factor_power(ratio, weight))
    top = (7,)
    _require(
        cumulative_factors["net"][top] == mi_factors,
        "top product differs from joint MI",
    )
    all_atoms = {}
    for key in keys:
        all_atoms = _factor_multiply(all_atoms, atom_factors["net"][key])
    _require(
        all_atoms == mi_factors, "all atom products do not reconstruct joint MI"
    )
    cumulative = {component: {} for component in COMPONENTS}
    atoms = {component: {} for component in COMPONENTS}
    for key in keys:
        for component in COMPONENTS:
            cumulative[component][key] = output_fraction(cumulative_factors[component][key])
        _retained_limit(cumulative, atoms)
    for key in keys:
        for component in COMPONENTS:
            atoms[component][key] = output_fraction(atom_factors[component][key])
        _retained_limit(cumulative, atoms)
    mi_product = output_fraction(mi_factors)
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
