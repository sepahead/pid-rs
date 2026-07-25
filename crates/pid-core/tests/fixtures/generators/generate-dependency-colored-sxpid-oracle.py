#!/usr/bin/env python3
"""Generate fraction-exact and high-precision dependency-colored SxPID challenges.

This program uses only the Python standard library. It uses Fraction arithmetic for finite laws
and 400-digit Decimal arithmetic for logarithms. It does not import pid-rs, another PID package,
or a simulation library.

The output is bounded executable evidence. It includes adversarial binary64 reconstruction cases,
but it is not a proof of the general probability theorem, an external review, or a binary64 error
theorem.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path
import struct
from typing import Any, TypeAlias


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json"
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SCHEMA = "pid-rs/dependency-colored-sxpid-oracle"
SCHEMA_REVISION = 7
DECIMAL_PRECISION = 400
TOLERANCE = Decimal("1e-350")

BitRow: TypeAlias = tuple[int, int, int]
SxState: TypeAlias = tuple[tuple[int, int], int, int]
Antichain: TypeAlias = tuple[int, ...]


class OracleError(RuntimeError):
    """The standalone calculation or committed fixture is inconsistent."""


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


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise OracleError("oracle produced a non-finite Decimal")
    return str(+value)


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def as_decimal(value: Fraction | int) -> Decimal:
    value = Fraction(value)
    return Decimal(value.numerator) / Decimal(value.denominator)


def exact_effective_color_proxy(class_sizes: tuple[int, ...] | list[int]) -> Fraction:
    """Return the exact proxy when all pairwise square-root products are rational."""
    proxy = Fraction(sum(class_sizes))
    for left, right in combinations(class_sizes, 2):
        product_value = left * right
        root = math.isqrt(product_value)
        if root * root != product_value:
            raise OracleError("class profile does not have an exact rational proxy")
        proxy += 2 * root
    return proxy


def parity(value: int) -> int:
    return value.bit_count() & 1


def build_pairwise_counterexample() -> dict[str, Any]:
    vectors = tuple(range(1, 16))
    outcomes = {
        latent: tuple(parity(vector & latent) for vector in vectors)
        for latent in range(16)
    }
    for position in range(len(vectors)):
        counts = Counter(row[position] for row in outcomes.values())
        if counts != Counter({0: 8, 1: 8}):
            raise OracleError("a finite-field linear form is not fair")
    for left, right in combinations(range(len(vectors)), 2):
        counts = Counter((row[left], row[right]) for row in outcomes.values())
        if counts != Counter({(0, 0): 4, (0, 1): 4, (1, 0): 4, (1, 1): 4}):
            raise OracleError("finite-field linear forms are not pairwise independent")
    all_zero = sum(all(bit == 0 for bit in row) for row in outcomes.values())
    if all_zero != 1:
        raise OracleError("finite-field all-zero event has the wrong multiplicity")
    false_bound = Decimal(2) * (Decimal(-15) / Decimal(2)).exp()
    failure_probability = Fraction(all_zero, len(outcomes))
    if as_decimal(failure_probability) <= false_bound:
        raise OracleError("pairwise counterexample does not falsify the i.i.d. bound")
    return {
        "alphabet_size": 2,
        "false_color_count": 1,
        "false_iid_bound_at_l1_error_one": decimal_text(false_bound),
        "failure_probability": fraction_text(failure_probability),
        "latent_dimension": 4,
        "row_count": len(vectors),
        "statement": (
            "all nonzero binary linear forms are pairwise independent, but the complete "
            "collection is not mutually independent"
        ),
    }


def build_copied_color_counterexample() -> dict[str, Any]:
    base_count = 4
    color_count = 3
    sample_size = base_count * color_count
    latent_assignments = tuple(product((0, 1), repeat=base_count))
    failure_assignments = []
    within_color_patterns = [Counter() for _ in range(color_count)]
    for latent in latent_assignments:
        observations = tuple(bit for _ in range(color_count) for bit in latent)
        for color in range(color_count):
            start = color * base_count
            within_color_patterns[color][
                observations[start : start + base_count]
            ] += 1
        zero_count = observations.count(0)
        empirical_zero = Fraction(zero_count, sample_size)
        l1_error = abs(empirical_zero - Fraction(1, 2)) * 2
        if l1_error == 1:
            failure_assignments.append(latent)
    expected_patterns = Counter({latent: 1 for latent in latent_assignments})
    if any(patterns != expected_patterns for patterns in within_color_patterns):
        raise OracleError("a copied-color class is not jointly uniform")
    if failure_assignments != [(0, 0, 0, 0), (1, 1, 1, 1)]:
        raise OracleError("copied-color L1 failure assignments are incorrect")
    failure_probability = Fraction(
        len(failure_assignments), len(latent_assignments)
    )
    false_no_color_bound = Decimal(2) * (
        -Decimal(sample_size) / Decimal(2)
    ).exp()
    valid_color_bound = Decimal(2) * (
        -Decimal(sample_size) / Decimal(2 * color_count)
    ).exp()
    if not false_no_color_bound < as_decimal(failure_probability) <= valid_color_bound:
        raise OracleError("copied-color counterexample has inconsistent bounds")
    class_sizes = [base_count] * color_count
    proxy = exact_effective_color_proxy(class_sizes)
    if proxy != color_count * sample_size:
        raise OracleError("balanced copied-color proxy is not d times n")
    return {
        "base_independent_bits": base_count,
        "class_sizes": class_sizes,
        "color_count": color_count,
        "effective_color_factor": fraction_text(proxy / sample_size),
        "enumerated_latent_assignments": len(latent_assignments),
        "failure_assignments": ["0000", "1111"],
        "failure_probability_at_l1_error_one": fraction_text(failure_probability),
        "false_bound_without_color_factor": decimal_text(false_no_color_bound),
        "proxy": fraction_text(proxy),
        "sample_size": sample_size,
        "valid_bound_with_color_factor": decimal_text(valid_color_bound),
        "within_color_classes_factor_jointly": True,
        "within_color_pattern_probability": fraction_text(
            Fraction(1, len(latent_assignments))
        ),
    }


def build_adaptive_color_counterexample() -> dict[str, Any]:
    sample_size = 8
    color_count = 2
    cases = []
    for latent in (0, 1):
        rows = (latent,) * sample_size
        selected_color = latent
        empirical_zero = Fraction(rows.count(0), sample_size)
        l1_error = abs(empirical_zero - Fraction(1, 2)) * 2
        if l1_error != 1:
            raise OracleError("adaptive-color construction does not have unit L1 error")
        cases.append(
            {
                "latent_bit": latent,
                "selected_color": selected_color,
                "conditional_row_value": latent,
                "l1_error": fraction_text(l1_error),
            }
        )
    false_bound = Decimal(2) * (
        -Decimal(sample_size) / Decimal(2 * color_count)
    ).exp()
    if false_bound >= 1:
        raise OracleError("adaptive-color example does not falsify the claimed bound")
    return {
        "enumerated_cases": cases,
        "failure_probability_at_l1_error_one": "1/1",
        "false_bound": decimal_text(false_bound),
        "sample_size": sample_size,
        "violated_conditional_premise": (
            "conditioning on the selected color changes every row law from fair to degenerate"
        ),
    }


def build_singleton_color_counterexample() -> dict[str, Any]:
    sample_size = 8
    class_sizes = [1] * sample_size
    proxy = exact_effective_color_proxy(class_sizes)
    errors = []
    for latent in (0, 1):
        rows = (latent,) * sample_size
        empirical_zero = Fraction(rows.count(0), sample_size)
        errors.append(abs(empirical_zero - Fraction(1, 2)) * 2)
    if errors != [Fraction(1), Fraction(1)]:
        raise OracleError("singleton-color construction does not have unit L1 error")
    if proxy != sample_size * sample_size:
        raise OracleError("singleton-color proxy must equal n squared")
    return {
        "class_sizes": class_sizes,
        "effective_color_factor": fraction_text(proxy / sample_size),
        "enumerated_latent_assignments": 2,
        "failure_probability_at_l1_error_one": "1/1",
        "proxy": fraction_text(proxy),
        "sample_size": sample_size,
        "statement": "all rows can equal one common fair bit, so no convergence follows",
    }


def build_unspecified_mixing_counterexample() -> dict[str, Any]:
    """Refute use of a mixing label as if it implied the one-color theorem."""
    sample_size = 2
    flip_probability = Fraction(1, 100)
    failure_probability = 1 - flip_probability
    same_pair_probability = failure_probability / 2
    flip_pair_probability = flip_probability / 2
    two_row_law = (
        ((0, 0), same_pair_probability),
        ((0, 1), flip_pair_probability),
        ((1, 0), flip_pair_probability),
        ((1, 1), same_pair_probability),
    )
    if sum((probability for _, probability in two_row_law), Fraction(0)) != 1:
        raise OracleError("mixing-label counterexample is not a probability law")
    for coordinate in (0, 1):
        marginal_one = sum(
            (
                probability
                for rows, probability in two_row_law
                if rows[coordinate] == 1
            ),
            Fraction(0),
        )
        if marginal_one != Fraction(1, 2):
            raise OracleError("mixing-label counterexample is not stationary and fair")
    false_one_color_bound = Decimal(2) * Decimal(-1).exp()
    if as_decimal(failure_probability) <= false_one_color_bound:
        raise OracleError("mixing-label counterexample does not falsify the i.i.d. bound")
    return {
        "alphabet_size": 2,
        "false_iid_bound_at_l1_error_one": decimal_text(false_one_color_bound),
        "failure_probability_at_l1_error_one": fraction_text(failure_probability),
        "flip_probability": fraction_text(flip_probability),
        "sample_size": sample_size,
        "statement": (
            "a stationary fair two-state Markov chain has geometrically decaying transition "
            "dependence but does not satisfy the one-color mutual-independence premise"
        ),
        "two_row_joint_law": [
            {
                "probability": fraction_text(probability),
                "rows": list(rows),
            }
            for rows, probability in two_row_law
        ],
    }


def build_net_weight_half_factor_counterexample() -> dict[str, Any]:
    """Retain the superseded generic range example outside the SxPID-specific result."""
    delta = Fraction(1, 5)
    row_norm = 4
    log_floor = Fraction(1)
    signed_weights = (-delta / 2, delta / 2)
    row_values = (-row_norm * log_floor, row_norm * log_floor)
    weighted_change = abs(
        sum(
            (
                weight * value
                for weight, value in zip(
                    signed_weights, row_values, strict=True
                )
            ),
            Fraction(0),
        )
    )
    valid_bound = row_norm * log_floor * delta
    false_half_bound = valid_bound / 2
    if weighted_change != valid_bound or weighted_change <= false_half_bound:
        raise OracleError("net-weight range counterexample does not attain its bound")
    return {
        "delta_l1": fraction_text(delta),
        "false_half_bound": fraction_text(false_half_bound),
        "log_floor": fraction_text(log_floor),
        "mobius_absolute_row_sum": row_norm,
        "row_values": [fraction_text(value) for value in row_values],
        "signed_weights": [fraction_text(value) for value in signed_weights],
        "statement": (
            "a generic range-only net weight term can attain row_norm times "
            "log_floor times delta_l1; this construction is not claimed to be "
            "SxPID-realizable"
        ),
        "sxpid_specific_status": (
            "superseded for two-source SxPID-specific range conclusions"
        ),
        "weighted_change": fraction_text(weighted_change),
    }


def ordinary_diamond_gradient(
    common: Fraction,
    left_exclusive: Fraction,
    right_exclusive: Fraction,
) -> dict[str, Fraction]:
    """Return the four ordinary-diamond gradient coordinates exactly."""
    if common <= 0 or left_exclusive < 0 or right_exclusive < 0:
        raise OracleError("ordinary-diamond masses are outside their declared domain")
    reciprocal_common = 1 / common
    reciprocal_left = 1 / (common + left_exclusive)
    reciprocal_right = 1 / (common + right_exclusive)
    reciprocal_union = 1 / (common + left_exclusive + right_exclusive)
    return {
        "a": (
            reciprocal_left
            + reciprocal_right
            - reciprocal_common
            - reciprocal_union
        ),
        "b": reciprocal_left - reciprocal_union,
        "c": reciprocal_right - reciprocal_union,
        "o": Fraction(0),
    }


def assert_exact_ordinary_diamond_diameter(
    name: str,
    common: Fraction,
    left_exclusive: Fraction,
    right_exclusive: Fraction,
    gradient: dict[str, Fraction],
) -> None:
    """Check the exact four-coordinate ordinary-diamond diameter."""
    observed = max(
        abs(left - right)
        for left in gradient.values()
        for right in gradient.values()
    )
    expected = 1 / common - 1 / (
        common + max(left_exclusive, right_exclusive)
    )
    if observed != expected:
        raise OracleError(f"{name}: exact ordinary-diamond diameter failed")


def build_conditioned_diamond_gradient_cases() -> list[dict[str, Any]]:
    """Audit all 64 ordered lifted-gradient pairs on exact rational cases."""
    raw_cases = (
        (
            "interior-asymmetric",
            (
                Fraction(1, 10),
                Fraction(1, 5),
                Fraction(3, 10),
                Fraction(1, 20),
                Fraction(1, 4),
                Fraction(1, 10),
            ),
        ),
        (
            "positive-cross-near-sharp",
            (
                Fraction(1, 1000),
                Fraction(0),
                Fraction(0),
                Fraction(0),
                Fraction(0),
                Fraction(999, 1000),
            ),
        ),
        (
            "negative-cross-near-sharp",
            (
                Fraction(1, 1000),
                Fraction(0),
                Fraction(0),
                Fraction(0),
                Fraction(999, 1000),
                Fraction(0),
            ),
        ),
        (
            "zero-complement-components",
            (
                Fraction(1, 4),
                Fraction(0),
                Fraction(1, 4),
                Fraction(1, 4),
                Fraction(1, 4),
                Fraction(0),
            ),
        ),
        (
            "small-common-asymmetric",
            (
                Fraction(1, 10000),
                Fraction(999, 10000),
                Fraction(0),
                Fraction(0),
                Fraction(0),
                Fraction(9, 10),
            ),
        ),
        (
            "zero-lift-boundary",
            (
                Fraction(1, 4),
                Fraction(1, 4),
                Fraction(1, 2),
                Fraction(0),
                Fraction(0),
                Fraction(0),
            ),
        ),
        (
            "unnormalized-algebra-only",
            (
                Fraction(2),
                Fraction(3),
                Fraction(5),
                Fraction(7),
                Fraction(11),
                Fraction(13),
            ),
        ),
    )
    coordinate_order = ("Fa", "Fb", "Fc", "Fo", "Xa", "Xb", "Xc", "Xo")
    output = []
    for name, masses in raw_cases:
        x_a, x_b, x_c, y_a, y_b, y_c = masses
        if x_a <= 0 or any(value < 0 for value in masses[1:]):
            raise OracleError(f"{name}: conditioned-diamond masses violate the theorem domain")
        base = ordinary_diamond_gradient(x_a, x_b, x_c)
        total = ordinary_diamond_gradient(
            x_a + y_a,
            x_b + y_b,
            x_c + y_c,
        )
        assert_exact_ordinary_diamond_diameter(
            f"{name} base",
            x_a,
            x_b,
            x_c,
            base,
        )
        assert_exact_ordinary_diamond_diameter(
            f"{name} full",
            x_a + y_a,
            x_b + y_b,
            x_c + y_c,
            total,
        )
        gradients = {
            **{f"F{coordinate}": total[coordinate] for coordinate in ("a", "b", "c", "o")},
            **{
                f"X{coordinate}": total[coordinate] - base[coordinate]
                for coordinate in ("a", "b", "c", "o")
            },
        }
        reciprocal_x_a = 1 / x_a
        reciprocal_x_ab = 1 / (x_a + x_b)
        reciprocal_x_ac = 1 / (x_a + x_c)
        reciprocal_x_abc = 1 / (x_a + x_b + x_c)
        reciprocal_total_a = 1 / (x_a + y_a)
        reciprocal_total_ab = 1 / (x_a + x_b + y_a + y_b)
        reciprocal_total_ac = 1 / (x_a + x_c + y_a + y_c)
        observed_candidate_differences = (
            gradients["Fb"] - gradients["Fa"],
            gradients["Fc"] - gradients["Fa"],
            gradients["Xa"] - gradients["Fa"],
            gradients["Fb"] - gradients["Xb"],
            gradients["Fc"] - gradients["Xc"],
            gradients["Xa"] - gradients["Xb"],
            gradients["Xa"] - gradients["Xc"],
            gradients["Fb"] - gradients["Xc"],
            gradients["Fc"] - gradients["Xb"],
        )
        closed_form_candidate_differences = (
            reciprocal_total_a - reciprocal_total_ac,
            reciprocal_total_a - reciprocal_total_ab,
            (
                reciprocal_x_a
                + reciprocal_x_abc
                - reciprocal_x_ab
                - reciprocal_x_ac
            ),
            reciprocal_x_ab - reciprocal_x_abc,
            reciprocal_x_ac - reciprocal_x_abc,
            (
                reciprocal_x_a
                - reciprocal_x_ac
                + reciprocal_total_ac
                - reciprocal_total_a
            ),
            (
                reciprocal_x_a
                - reciprocal_x_ab
                + reciprocal_total_ab
                - reciprocal_total_a
            ),
            (
                reciprocal_total_ab
                - reciprocal_total_ac
                + reciprocal_x_ac
                - reciprocal_x_abc
            ),
            (
                reciprocal_total_ac
                - reciprocal_total_ab
                + reciprocal_x_ab
                - reciprocal_x_abc
            ),
        )
        if observed_candidate_differences != closed_form_candidate_differences:
            raise OracleError(
                f"{name}: conditioned-diamond candidate identities failed"
            )

        reciprocal_nested_x_a = reciprocal_x_a
        reciprocal_nested_x_ab = reciprocal_x_ab
        reciprocal_nested_total_a = reciprocal_total_a
        reciprocal_nested_total_ab = reciprocal_total_ab
        nested_gradients = (
            reciprocal_nested_total_ab - reciprocal_nested_total_a,
            reciprocal_nested_total_ab,
            (
                reciprocal_nested_total_ab
                - reciprocal_nested_total_a
                - reciprocal_nested_x_ab
                + reciprocal_nested_x_a
            ),
            reciprocal_nested_total_ab - reciprocal_nested_x_ab,
            Fraction(0),
        )
        nested_candidate_lower = min(nested_gradients[0], nested_gradients[3])
        nested_candidate_upper = max(nested_gradients[1], nested_gradients[2])
        nested_candidate_diameter = (
            nested_candidate_upper - nested_candidate_lower
        )
        nested_closed_form_diameter = max(
            reciprocal_nested_total_a,
            reciprocal_nested_x_ab,
            reciprocal_nested_x_a - reciprocal_nested_x_ab,
            reciprocal_nested_x_a - reciprocal_nested_total_a,
        )
        nested_exact_diameter = max(nested_gradients) - min(nested_gradients)
        if not (
            nested_exact_diameter
            == nested_candidate_diameter
            == nested_closed_form_diameter
        ):
            raise OracleError(
                f"{name}: conditioned-nested exact diameter identity failed"
            )
        full_union_mass = sum(masses)
        bound = 1 / x_a
        refined_bound = bound - 1 / full_union_mass
        ordered_differences = [
            (
                left,
                right,
                abs(gradients[left] - gradients[right]),
            )
            for left in coordinate_order
            for right in coordinate_order
        ]
        if len(ordered_differences) != 64:
            raise OracleError("conditioned-diamond ordered-pair audit is incomplete")
        if any(
            difference > refined_bound
            for _, _, difference in ordered_differences
        ):
            raise OracleError(
                f"{name}: refined conditioned-diamond diameter bound failed"
            )
        maximum = max(difference for _, _, difference in ordered_differences)
        if maximum != max(observed_candidate_differences):
            raise OracleError(
                f"{name}: conditioned-diamond candidate diameter is not exact"
            )
        maximizing_pairs = [
            [left, right]
            for left, right, difference in ordered_differences
            if difference == maximum
        ]
        maximum_ratio = maximum / bound
        maximum_refined_ratio = maximum / refined_bound
        oriented_fb_minus_xc = gradients["Fb"] - gradients["Xc"]
        if not Fraction(0) <= maximum_ratio <= Fraction(1):
            raise OracleError(f"{name}: normalized conditioned-diamond diameter is invalid")
        if not Fraction(0) <= maximum_refined_ratio <= Fraction(1):
            raise OracleError(
                f"{name}: refined normalized conditioned-diamond diameter is invalid"
            )
        if full_union_mass <= 1:
            probability_bound = bound - 1
            if refined_bound > probability_bound or maximum > probability_bound:
                raise OracleError(
                    f"{name}: probability-domain diameter corollary failed"
                )
        if name in {"positive-cross-near-sharp", "negative-cross-near-sharp"}:
            if maximum_ratio != Fraction(999, 1000):
                raise OracleError(f"{name}: the near-sharp ratio changed")
            if maximum_refined_ratio != Fraction(1):
                raise OracleError(f"{name}: the refined bound is no longer attained")
            hard_pairs = {("Fb", "Xc"), ("Fc", "Xb")}
            if not any(tuple(pair) in hard_pairs for pair in maximizing_pairs):
                raise OracleError(f"{name}: a hard crossed pair is no longer near sharp")
            expected_oriented = (
                Fraction(999)
                if name == "positive-cross-near-sharp"
                else Fraction(-999)
            )
            if oriented_fb_minus_xc != expected_oriented:
                raise OracleError(f"{name}: the oriented near-sharp difference changed")
        if name == "zero-lift-boundary" and any(
            gradients[coordinate] != 0 for coordinate in ("Xa", "Xb", "Xc", "Xo")
        ):
            raise OracleError("zero-lift boundary has a nonzero conditioned coordinate")
        if name == "unnormalized-algebra-only" and sum(masses) <= 1:
            raise OracleError("unnormalized algebra case no longer exceeds unit total mass")
        output.append(
            {
                "gradient_values": {
                    coordinate: fraction_text(gradients[coordinate])
                    for coordinate in coordinate_order
                },
                "masses": {
                    "x_a": fraction_text(x_a),
                    "x_b": fraction_text(x_b),
                    "x_c": fraction_text(x_c),
                    "y_a": fraction_text(y_a),
                    "y_b": fraction_text(y_b),
                    "y_c": fraction_text(y_c),
                },
                "maximum_normalized_diameter": fraction_text(maximum_ratio),
                "maximum_normalized_refined_diameter": fraction_text(
                    maximum_refined_ratio
                ),
                "maximizing_ordered_pairs": maximizing_pairs,
                "mass_scope": (
                    "probability-region-compatible"
                    if full_union_mass <= 1
                    else "algebra-only-unnormalized"
                ),
                "name": name,
                "oriented_fb_minus_xc": fraction_text(oriented_fb_minus_xc),
                "ordered_pair_count": len(ordered_differences),
                "reciprocal_x_a_bound": fraction_text(bound),
                "refined_diameter_bound": fraction_text(refined_bound),
            }
        )
    return output


def build_conditioned_diamond_extremal_regimes() -> list[dict[str, Any]]:
    """Realize all nine exact conditioned-diamond minimum/maximum regimes."""
    raw_cases = (
        ("Fa", "Fb", (1, 1, 1, 1, 1, 4)),
        ("Fa", "Fc", (1, 1, 1, 1, 4, 1)),
        ("Fa", "Xa", (1, 1, 1, 1, 1, 1)),
        ("Xb", "Fb", (2, 1, 2, 2, 1, 2)),
        ("Xb", "Fc", (2, 1, 1, 3, 3, 1)),
        ("Xb", "Xa", (1, 1, 1, 2, 2, 1)),
        ("Xc", "Fb", (2, 1, 1, 3, 1, 3)),
        ("Xc", "Fc", (2, 2, 1, 2, 2, 1)),
        ("Xc", "Xa", (1, 1, 1, 2, 1, 2)),
    )
    output = []
    for expected_minimum, expected_maximum, integer_masses in raw_cases:
        denominator = sum(integer_masses)
        masses = tuple(Fraction(value, denominator) for value in integer_masses)
        x_a, x_b, x_c, y_a, y_b, y_c = masses
        if sum(masses) != 1 or any(value <= 0 for value in masses):
            raise OracleError("conditioned-diamond regime is not an interior probability case")
        base = ordinary_diamond_gradient(x_a, x_b, x_c)
        total = ordinary_diamond_gradient(
            x_a + y_a,
            x_b + y_b,
            x_c + y_c,
        )
        gradients = {
            **{f"F{coordinate}": total[coordinate] for coordinate in ("a", "b", "c", "o")},
            **{
                f"X{coordinate}": total[coordinate] - base[coordinate]
                for coordinate in ("a", "b", "c", "o")
            },
        }
        minimum = min(gradients.values())
        maximum = max(gradients.values())
        minimum_labels = [
            label for label, value in gradients.items() if value == minimum
        ]
        maximum_labels = [
            label for label, value in gradients.items() if value == maximum
        ]
        if minimum_labels != [expected_minimum] or maximum_labels != [expected_maximum]:
            raise OracleError(
                "conditioned-diamond regime no longer has its unique extrema"
            )
        output.append(
            {
                "diameter": fraction_text(maximum - minimum),
                "masses": {
                    "x_a": fraction_text(x_a),
                    "x_b": fraction_text(x_b),
                    "x_c": fraction_text(x_c),
                    "y_a": fraction_text(y_a),
                    "y_b": fraction_text(y_b),
                    "y_c": fraction_text(y_c),
                },
                "maximum_coordinate": expected_maximum,
                "minimum_coordinate": expected_minimum,
            }
        )
    if {
        (case["minimum_coordinate"], case["maximum_coordinate"])
        for case in output
    } != {
        (minimum, maximum)
        for minimum in ("Fa", "Xb", "Xc")
        for maximum in ("Fb", "Fc", "Xa")
    }:
        raise OracleError("conditioned-diamond extremal regime audit is incomplete")
    return output


def build_conditioned_diamond_negative_lift_counterexamples() -> list[dict[str, Any]]:
    """Show that separate endpoint validity does not replace componentwise nonnegativity."""
    raw_cases = (
        (
            "negative-left-exclusive-lift",
            (Fraction(1, 4), Fraction(1, 4), Fraction(0)),
            (Fraction(0), Fraction(-1, 4), Fraction(1, 2)),
            {"Fb": Fraction(8, 3), "Xc": Fraction(-2)},
            Fraction(14, 3),
        ),
        (
            "negative-right-exclusive-lift",
            (Fraction(1, 4), Fraction(0), Fraction(1, 4)),
            (Fraction(0), Fraction(1, 2), Fraction(-1, 4)),
            {"Fc": Fraction(8, 3), "Xb": Fraction(-2)},
            Fraction(14, 3),
        ),
        (
            "negative-common-lift",
            (Fraction(1, 2), Fraction(0), Fraction(0)),
            (Fraction(-1, 4), Fraction(3, 4), Fraction(0)),
            {"Fc": Fraction(3), "Xc": Fraction(3)},
            Fraction(3),
        ),
    )
    output = []
    labels = ("y_a", "y_b", "y_c")
    coordinate_order = ("Fa", "Fb", "Fc", "Fo", "Xa", "Xb", "Xc", "Xo")
    for name, x, y, expected_values, expected_maximum in raw_cases:
        full = tuple(
            x_value + y_value for x_value, y_value in zip(x, y, strict=True)
        )
        if x[0] <= 0 or full[0] <= 0 or any(
            value < 0 for value in x[1:] + full[1:]
        ):
            raise OracleError(f"{name}: base or full diamond is invalid")
        violated = [
            [label, fraction_text(value)]
            for label, value in zip(labels, y, strict=True)
            if value < 0
        ]
        if len(violated) != 1:
            raise OracleError(f"{name}: expected exactly one negative lift increment")
        base_gradient = ordinary_diamond_gradient(*x)
        full_gradient = ordinary_diamond_gradient(*full)
        values = {
            **{
                f"F{coordinate}": full_gradient[coordinate]
                for coordinate in ("a", "b", "c", "o")
            },
            **{
                f"X{coordinate}": full_gradient[coordinate] - base_gradient[coordinate]
                for coordinate in ("a", "b", "c", "o")
            },
        }
        for coordinate, expected in expected_values.items():
            if values[coordinate] != expected:
                raise OracleError(f"{name}: coordinate {coordinate} changed")
        ordered_differences = [
            (left, right, abs(values[left] - values[right]))
            for left in coordinate_order
            for right in coordinate_order
        ]
        maximum = max(value for _, _, value in ordered_differences)
        maximizing_pairs = [
            [left, right]
            for left, right, value in ordered_differences
            if value == maximum
        ]
        claimed_bound = 1 / x[0]
        if maximum != expected_maximum or maximum <= claimed_bound:
            raise OracleError(f"{name}: example no longer violates the claimed bound")
        output.append(
            {
                "base_masses": [fraction_text(value) for value in x],
                "claimed_reciprocal_bound": fraction_text(claimed_bound),
                "full_masses": [fraction_text(value) for value in full],
                "gradient_values": {
                    coordinate: fraction_text(values[coordinate])
                    for coordinate in coordinate_order
                },
                "maximum_diameter": fraction_text(maximum),
                "maximizing_ordered_pairs": maximizing_pairs,
                "name": name,
                "statement": (
                    "separately valid base and full diamonds do not suffice when a "
                    "componentwise lift increment is negative"
                ),
                "violated_lift": violated[0],
            }
        )
    return output


def build_class_profiles() -> list[dict[str, Any]]:
    profiles = ([10], [5, 5], [1, 9], [1, 1, 1, 1], [1, 4, 9])
    output = []
    for class_sizes in profiles:
        sample_size = sum(class_sizes)
        proxy = exact_effective_color_proxy(class_sizes)
        occupied = len(class_sizes)
        if proxy < sample_size:
            raise OracleError("effective-color proxy is below n")
        if proxy > occupied * sample_size:
            raise OracleError("effective-color proxy exceeds r times n")
        output.append(
            {
                "class_sizes": class_sizes,
                "effective_color_factor": fraction_text(proxy / sample_size),
                "occupied_colors": occupied,
                "proxy": fraction_text(proxy),
                "sample_size": sample_size,
            }
        )
    return output


def build_telescoping_checks() -> list[dict[str, Any]]:
    output = []
    for count in (1, 2, 5, 10, 100):
        actual = sum(
            (Fraction(1, index * (index + 1)) for index in range(1, count + 1)),
            Fraction(0),
        )
        expected = Fraction(count, count + 1)
        if actual != expected:
            raise OracleError("anytime allocation did not telescope exactly")
        output.append(
            {
                "prefix_terms": count,
                "spent_fraction_of_alpha": fraction_text(actual),
            }
        )
    return output


def antichain_leq(lower: Antichain, upper: Antichain) -> bool:
    return all(
        any(lower_mask & upper_mask == lower_mask for lower_mask in lower)
        for upper_mask in upper
    )


def mobius_invert(
    nodes: tuple[Antichain, ...], cumulative: dict[Antichain, Decimal]
) -> dict[Antichain, Decimal]:
    remaining = set(nodes)
    atoms: dict[Antichain, Decimal] = {}
    while remaining:
        ready = sorted(
            node
            for node in remaining
            if not any(
                other != node and antichain_leq(other, node)
                for other in remaining
            )
        )
        if not ready:
            raise OracleError("redundancy lattice contains a cycle")
        for node in ready:
            lower_sum = sum(
                (
                    value
                    for lower, value in atoms.items()
                    if lower != node and antichain_leq(lower, node)
                ),
                Decimal(0),
            )
            atoms[node] = cumulative[node] - lower_sum
            remaining.remove(node)
    for node in nodes:
        reconstructed = sum(
            (
                atom
                for lower, atom in atoms.items()
                if antichain_leq(lower, node)
            ),
            Decimal(0),
        )
        if abs(reconstructed - cumulative[node]) > TOLERANCE:
            raise OracleError("Mobius atoms do not reconstruct a cumulative value")
    return atoms


def sxpid2_oracle(states: tuple[SxState, ...]) -> dict[str, Any]:
    nodes: tuple[Antichain, ...] = ((1,), (2,), (3,), (1, 2))
    total = sum(count for _, _, count in states)
    if total <= 0:
        raise OracleError("SxPID table has no mass")
    averaged = {
        node: {"informative": Decimal(0), "misinformative": Decimal(0)}
        for node in nodes
    }
    pointwise = []
    for sources, target, count in states:
        cumulative_plus: dict[Antichain, Decimal] = {}
        cumulative_minus: dict[Antichain, Decimal] = {}
        for node in nodes:
            union_count = 0
            target_union_count = 0
            target_count = 0
            for other_sources, other_target, other_count in states:
                matches_union = any(
                    all(
                        other_sources[index] == sources[index]
                        for index in range(2)
                        if mask & (1 << index)
                    )
                    for mask in node
                )
                if matches_union:
                    union_count += other_count
                    if other_target == target:
                        target_union_count += other_count
                if other_target == target:
                    target_count += other_count
            if min(union_count, target_union_count, target_count) <= 0:
                raise OracleError("SxPID event probability is zero on a supported row")
            p_union = Decimal(union_count) / Decimal(total)
            p_target = Decimal(target_count) / Decimal(total)
            p_target_union = Decimal(target_union_count) / Decimal(total)
            cumulative_plus[node] = -p_union.ln()
            cumulative_minus[node] = (p_target / p_target_union).ln()
        atoms_plus = mobius_invert(nodes, cumulative_plus)
        atoms_minus = mobius_invert(nodes, cumulative_minus)
        weight = Decimal(count) / Decimal(total)
        entries = []
        for node in nodes:
            plus = atoms_plus[node]
            minus = atoms_minus[node]
            averaged[node]["informative"] += weight * plus
            averaged[node]["misinformative"] += weight * minus
            entries.append(
                {
                    "informative_nats": decimal_text(plus),
                    "misinformative_nats": decimal_text(minus),
                    "net_nats": decimal_text(plus - minus),
                    "node_masks": list(node),
                }
            )
        pointwise.append(
            {
                "count": count,
                "sources": list(sources),
                "target": target,
                "atoms": entries,
            }
        )
    averaged_entries = []
    for node in nodes:
        plus = averaged[node]["informative"]
        minus = averaged[node]["misinformative"]
        averaged_entries.append(
            {
                "informative_nats": decimal_text(plus),
                "misinformative_nats": decimal_text(minus),
                "net_nats": decimal_text(plus - minus),
                "node_masks": list(node),
            }
        )
    return {"averaged_atoms": averaged_entries, "pointwise": pointwise}


def sxpid2_states(counts: tuple[int, ...]) -> tuple[SxState, ...]:
    """Build a full binary two-source/target count table in lexicographic order."""
    labels = tuple(
        ((source_1, source_2), target)
        for source_1, source_2, target in product((0, 1), repeat=3)
    )
    if len(counts) != len(labels) or min(counts) <= 0:
        raise OracleError("full binary SxPID counts must contain eight positive values")
    return tuple(
        (sources, target, count)
        for (sources, target), count in zip(labels, counts, strict=True)
    )


def normalized_state_law(states: tuple[SxState, ...]) -> dict[tuple[tuple[int, int], int], Fraction]:
    total = sum(count for _, _, count in states)
    if total <= 0:
        raise OracleError("state law has no mass")
    law: dict[tuple[tuple[int, int], int], Fraction] = {}
    for sources, target, count in states:
        key = (sources, target)
        if key in law or count <= 0:
            raise OracleError("state law has a duplicate or non-positive cell")
        law[key] = Fraction(count, total)
    return law


def sxpid_atom_maps(
    result: dict[str, Any],
) -> tuple[
    dict[Antichain, dict[str, Decimal]],
    dict[tuple[tuple[int, int], int, Antichain], dict[str, Decimal]],
]:
    averaged: dict[Antichain, dict[str, Decimal]] = {}
    for atom in result["averaged_atoms"]:
        node = tuple(atom["node_masks"])
        averaged[node] = {
            "informative": Decimal(atom["informative_nats"]),
            "misinformative": Decimal(atom["misinformative_nats"]),
            "net": Decimal(atom["net_nats"]),
        }
    pointwise: dict[
        tuple[tuple[int, int], int, Antichain], dict[str, Decimal]
    ] = {}
    for point in result["pointwise"]:
        sources = tuple(point["sources"])
        if len(sources) != 2:
            raise OracleError("two-source oracle returned the wrong source width")
        for atom in point["atoms"]:
            node = tuple(atom["node_masks"])
            pointwise[(sources, point["target"], node)] = {
                "informative": Decimal(atom["informative_nats"]),
                "misinformative": Decimal(atom["misinformative_nats"]),
                "net": Decimal(atom["net_nats"]),
            }
    return averaged, pointwise


def build_sxpid2_modulus_cases() -> list[dict[str, Any]]:
    """Challenge the sharper two-source SxPID-specific local-continuity bounds."""
    raw_cases = (
        (
            "full-binary-balanced-perturbation",
            sxpid2_states((8, 10, 12, 14, 16, 18, 20, 22)),
            sxpid2_states((9, 9, 13, 13, 17, 17, 21, 21)),
        ),
        (
            "xor-support-skew-perturbation",
            (
                ((0, 0), 0, 4),
                ((0, 1), 1, 12),
                ((1, 0), 1, 12),
                ((1, 1), 0, 36),
            ),
            (
                ((0, 0), 0, 5),
                ((0, 1), 1, 11),
                ((1, 0), 1, 13),
                ((1, 1), 0, 35),
            ),
        ),
        (
            "full-binary-near-support-boundary",
            sxpid2_states((5, 10, 10, 10, 10, 15, 20, 20)),
            sxpid2_states((1, 10, 10, 10, 10, 15, 20, 24)),
        ),
        (
            "full-binary-realizable-near-tight",
            sxpid2_states((10, 100, 200, 10, 250, 10, 10, 10)),
            sxpid2_states((1, 100, 200, 10, 250, 10, 10, 19)),
        ),
        (
            "two-cell-q-component-cap",
            (((0, 0), 0, 40), ((1, 1), 1, 60)),
            (((0, 0), 0, 14), ((1, 1), 1, 86)),
        ),
        (
            "two-cell-q-net-cap",
            (((0, 0), 0, 45), ((1, 1), 1, 55)),
            (((0, 0), 0, 10), ((1, 1), 1, 90)),
        ),
    )
    nodes: tuple[Antichain, ...] = ((1,), (2,), (3,), (1, 2))

    output = []
    for name, p_states, q_states in raw_cases:
        p_law = normalized_state_law(p_states)
        q_law = normalized_state_law(q_states)
        if p_law.keys() != q_law.keys():
            raise OracleError("local-modulus laws do not have common support")
        delta = sum(abs(q_law[key] - p_law[key]) for key in p_law)
        p_min = min(p_law.values())
        if not delta < 2 * p_min:
            raise OracleError("local-modulus SxPID pair violates the strict support margin")
        eta = delta / 2
        decimal_delta = as_decimal(delta)
        decimal_eta = as_decimal(eta)
        decimal_p_min = as_decimal(p_min)
        modulus = (decimal_p_min / (decimal_p_min - decimal_eta)).ln()
        refined_synergy_modulus = modulus - decimal_eta
        if refined_synergy_modulus < 0:
            raise OracleError(f"{name}: refined synergy modulus is negative")
        log_floor = (Decimal(1) / decimal_p_min).ln()
        h_nats = (Decimal(2) / (Decimal(1) + decimal_p_min)).ln()
        diamond_ceiling_nats = log_floor - Decimal(2) * h_nats
        q_floor = decimal_p_min - decimal_eta
        q_log_floor = (Decimal(1) / q_floor).ln()
        q_h_nats = (Decimal(2) / (Decimal(1) + q_floor)).ln()
        q_diamond_ceiling_nats = q_log_floor - Decimal(2) * q_h_nats
        if not Decimal(0) <= diamond_ceiling_nats <= log_floor:
            raise OracleError(
                f"{name}: the diamond ceiling must lie in the exact-real range [0, L]"
            )
        if not (
            diamond_ceiling_nats
            <= q_diamond_ceiling_nats
            <= q_log_floor
        ):
            raise OracleError(
                f"{name}: the q-law diamond ceiling is outside its declared range"
            )
        p_result = sxpid2_oracle(p_states)
        q_result = sxpid2_oracle(q_states)
        p_averaged, p_pointwise = sxpid_atom_maps(p_result)
        q_averaged, q_pointwise = sxpid_atom_maps(q_result)
        if p_pointwise.keys() != q_pointwise.keys():
            raise OracleError("local-modulus pointwise keys do not agree")

        bound_entries = []
        maximum_pointwise_ratio = {
            "informative": Decimal(0),
            "misinformative": Decimal(0),
            "net": Decimal(0),
        }
        maximum_synergy_pointwise_ratio = {
            "informative": Decimal(0),
            "misinformative": Decimal(0),
            "net": Decimal(0),
        }
        maximum_averaged_ratio = {
            "informative": Decimal(0),
            "misinformative": Decimal(0),
            "net": Decimal(0),
        }
        for node in nodes:
            is_synergy = node == (3,)
            pointwise_modulus = (
                refined_synergy_modulus if is_synergy else modulus
            )
            pointwise_bounds = {
                "informative": pointwise_modulus,
                "misinformative": pointwise_modulus,
                "net": pointwise_modulus,
            }
            component_weight_range = (
                diamond_ceiling_nats if is_synergy else log_floor
            )
            net_weight_range = (
                diamond_ceiling_nats if is_synergy else log_floor - h_nats
            )
            component_caps = [
                log_floor,
                pointwise_modulus + decimal_eta * component_weight_range,
            ]
            net_caps = [
                Decimal(2) * log_floor,
                pointwise_modulus + decimal_delta * net_weight_range,
            ]
            if is_synergy:
                component_caps.append(q_diamond_ceiling_nats)
                net_caps.append(
                    diamond_ceiling_nats + q_diamond_ceiling_nats
                )
            component_bound = min(component_caps)
            net_bound = min(net_caps)
            if is_synergy and name == "two-cell-q-component-cap":
                if component_bound != q_diamond_ceiling_nats:
                    raise OracleError(
                        f"{name}: the q-law component endpoint cap is not active"
                    )
            if is_synergy and name == "two-cell-q-net-cap":
                if net_bound != diamond_ceiling_nats + q_diamond_ceiling_nats:
                    raise OracleError(
                        f"{name}: the q-law net endpoint cap is not active"
                    )
            averaged_bounds = {
                "informative": component_bound,
                "misinformative": component_bound,
                "net": net_bound,
            }
            if (
                averaged_bounds["informative"] > log_floor
                or averaged_bounds["misinformative"] > log_floor
                or averaged_bounds["net"] > Decimal(2) * log_floor
            ):
                raise OracleError(f"{name}: an averaged bound exceeds its range cap")
            for key in p_pointwise:
                if key[2] != node:
                    continue
                for component, bound in pointwise_bounds.items():
                    change = abs(
                        q_pointwise[key][component] - p_pointwise[key][component]
                    )
                    if change > bound + TOLERANCE:
                        raise OracleError(
                            f"{name}: pointwise {component} atom exceeds its modulus"
                        )
                    maximum_pointwise_ratio[component] = max(
                        maximum_pointwise_ratio[component],
                        change / bound if bound else Decimal(0),
                    )
                    if is_synergy:
                        maximum_synergy_pointwise_ratio[component] = max(
                            maximum_synergy_pointwise_ratio[component],
                            change / bound if bound else Decimal(0),
                        )
            for component, bound in averaged_bounds.items():
                change = abs(
                    q_averaged[node][component] - p_averaged[node][component]
                )
                if change > bound + TOLERANCE:
                    raise OracleError(
                        f"{name}: averaged {component} atom exceeds its modulus"
                    )
                maximum_averaged_ratio[component] = max(
                    maximum_averaged_ratio[component],
                    change / bound if bound else Decimal(0),
                )
            bound_entries.append(
                {
                    "atom_family": "synergy" if is_synergy else "redundancy-or-unique",
                    "averaged_bounds_nats": {
                        component: decimal_text(value)
                        for component, value in averaged_bounds.items()
                    },
                    "node_masks": list(node),
                    "pointwise_bounds_nats": {
                        component: decimal_text(value)
                        for component, value in pointwise_bounds.items()
                    },
                }
            )
        if name == "full-binary-realizable-near-tight":
            if (
                delta != Fraction(3, 100)
                or eta != Fraction(3, 200)
                or p_min != Fraction(1, 60)
                or p_min / (p_min - eta) != 10
            ):
                raise OracleError("near-tight law lost its exact support geometry")
            if not (
                Decimal("0.97")
                < maximum_synergy_pointwise_ratio["misinformative"]
                <= Decimal(1)
            ):
                raise OracleError(
                    "near-tight misinformative ratio left the bounded interval (0.97, 1]"
                )
            if not (
                Decimal("0.95")
                < maximum_synergy_pointwise_ratio["net"]
                <= Decimal(1)
            ):
                raise OracleError(
                    "near-tight net ratio left the bounded interval (0.95, 1]"
                )
        output.append(
            {
                "bounds_by_node": bound_entries,
                "delta_l1": fraction_text(delta),
                "eta_total_variation": fraction_text(eta),
                "h_nats": decimal_text(h_nats),
                "diamond_ceiling_nats": decimal_text(diamond_ceiling_nats),
                "lambda_nats": decimal_text(modulus),
                "log_support_floor_nats": decimal_text(log_floor),
                "maximum_averaged_to_bound_ratio": {
                    component: decimal_text(value)
                    for component, value in maximum_averaged_ratio.items()
                },
                "maximum_pointwise_to_bound_ratio": {
                    component: decimal_text(value)
                    for component, value in maximum_pointwise_ratio.items()
                },
                "maximum_synergy_pointwise_to_bound_ratio": {
                    component: decimal_text(value)
                    for component, value in maximum_synergy_pointwise_ratio.items()
                },
                "name": name,
                "p_min": fraction_text(p_min),
                "p_population_count_table": state_count_table(p_states),
                "p_sxpid2": p_result,
                "q_population_count_table": state_count_table(q_states),
                "q_sxpid2": q_result,
                "q_diamond_ceiling_nats": decimal_text(
                    q_diamond_ceiling_nats
                ),
                "refined_synergy_modulus_nats": decimal_text(
                    refined_synergy_modulus
                ),
            }
        )
    return output


def build_non_synergy_refined_modulus_counterexamples() -> list[dict[str, Any]]:
    """Show that the synergy-only modulus cannot replace Lambda for other atoms."""
    raw_cases = (
        (
            "redundancy-informative-and-net",
            ((0, 0), 0),
            ((1, 1), 1),
            (1, 2),
            ("informative", "net"),
        ),
        (
            "redundancy-misinformative",
            ((0, 0), 0),
            ((1, 1), 0),
            (1, 2),
            ("misinformative",),
        ),
        (
            "source-one-unique-informative-and-net",
            ((1, 1), 1),
            ((0, 1), 0),
            (1,),
            ("informative", "net"),
        ),
        (
            "source-one-unique-misinformative",
            ((1, 1), 1),
            ((0, 1), 1),
            (1,),
            ("misinformative",),
        ),
        (
            "source-two-unique-informative-and-net",
            ((1, 1), 1),
            ((1, 0), 0),
            (2,),
            ("informative", "net"),
        ),
        (
            "source-two-unique-misinformative",
            ((1, 1), 1),
            ((1, 0), 1),
            (2,),
            ("misinformative",),
        ),
    )
    eta = Fraction(1, 10)
    expected_lambda = (Decimal(5) / Decimal(4)).ln()
    refined_synergy_modulus = expected_lambda - as_decimal(eta)
    output = []
    for name, first, second, node, components in raw_cases:
        first_sources, first_target = first
        second_sources, second_target = second
        p_states = (
            (first_sources, first_target, 1),
            (second_sources, second_target, 1),
        )
        q_states = (
            (first_sources, first_target, 2),
            (second_sources, second_target, 3),
        )
        p_result = sxpid2_oracle(p_states)
        q_result = sxpid2_oracle(q_states)
        p_atom = pointwise_atom(
            p_result,
            list(first_sources),
            first_target,
            list(node),
        )
        q_atom = pointwise_atom(
            q_result,
            list(first_sources),
            first_target,
            list(node),
        )
        changes = {}
        for component in components:
            field = f"{component}_nats"
            change = abs(Decimal(q_atom[field]) - Decimal(p_atom[field]))
            if abs(change - expected_lambda) > TOLERANCE:
                raise OracleError(f"{name}: non-synergy change does not attain Lambda")
            if change <= refined_synergy_modulus:
                raise OracleError(f"{name}: false all-atom refinement was not violated")
            changes[component] = decimal_text(change)
        output.append(
            {
                "attained_lambda_nats": decimal_text(expected_lambda),
                "components": list(components),
                "first_sources": list(first_sources),
                "first_target": first_target,
                "name": name,
                "node_masks": list(node),
                "p_population_count_table": state_count_table(p_states),
                "q_population_count_table": state_count_table(q_states),
                "refined_synergy_modulus_nats": decimal_text(
                    refined_synergy_modulus
                ),
                "stored_component_changes_nats": changes,
            }
        )
    return output


def duplicate_source_states(law: tuple[Fraction, ...]) -> tuple[SxState, ...]:
    """Encode a binary `(X, T)` law as `S1 = S2 = X` integer counts."""
    if len(law) != 4 or sum(law) != 1 or min(law) < 0:
        raise OracleError("duplicate-source law must be a binary probability law")
    denominator = math.lcm(*(value.denominator for value in law))
    labels = ((0, 0), (0, 1), (1, 0), (1, 1))
    states = []
    for (source, target), probability_value in zip(labels, law, strict=True):
        count = probability_value.numerator * (
            denominator // probability_value.denominator
        )
        if count > 0:
            states.append(((source, source), target, count))
    return tuple(states)


def state_count_table(states: tuple[SxState, ...]) -> list[dict[str, Any]]:
    return [
        {
            "count": count,
            "sources": list(sources),
            "target": target,
        }
        for sources, target, count in states
    ]


def averaged_atom(
    result: dict[str, Any], node_masks: list[int]
) -> dict[str, Any]:
    matches = [
        atom
        for atom in result["averaged_atoms"]
        if atom["node_masks"] == node_masks
    ]
    if len(matches) != 1:
        raise OracleError("SxPID oracle did not contain one requested averaged atom")
    return matches[0]


def pointwise_atom(
    result: dict[str, Any],
    sources: list[int],
    target: int,
    node_masks: list[int],
) -> dict[str, Any]:
    points = [
        point
        for point in result["pointwise"]
        if point["sources"] == sources and point["target"] == target
    ]
    if len(points) != 1:
        raise OracleError("SxPID oracle did not contain one requested realization")
    matches = [
        atom for atom in points[0]["atoms"] if atom["node_masks"] == node_masks
    ]
    if len(matches) != 1:
        raise OracleError("SxPID oracle did not contain one requested pointwise atom")
    return matches[0]


def window_row(u_bits: tuple[int, ...], v_bits: tuple[int, ...], index: int) -> BitRow:
    first = u_bits[index] | u_bits[index + 1]
    second = v_bits[index] | v_bits[index + 1]
    return (first, second, first ^ second)


def probability(counter: Counter[Any], key: Any, total: int) -> Fraction:
    return Fraction(counter[key], total)


def assert_factorization(
    joint: Counter[Any], marginals: list[Counter[Any]], total: int
) -> None:
    for outcome, count in joint.items():
        expected = Fraction(1)
        for index, value in enumerate(outcome):
            expected *= probability(marginals[index], value, total)
        if Fraction(count, total) != expected:
            raise OracleError("declared independent window rows do not factor")
    support = list(product(*(tuple(marginal) for marginal in marginals)))
    for outcome in support:
        expected = Fraction(1)
        for index, value in enumerate(outcome):
            expected *= probability(marginals[index], value, total)
        if probability(joint, outcome, total) != expected:
            raise OracleError("window factorization misses a zero-count outcome")


def build_window_case() -> dict[str, Any]:
    row_count = 6
    width = 2
    innovation_count = row_count + width - 1
    marginal_by_row = [Counter() for _ in range(row_count)]
    adjacent = Counter()
    lag_two = Counter()
    colors = {0: Counter(), 1: Counter()}
    total = 0
    for bits in product((0, 1), repeat=2 * innovation_count):
        u_bits = bits[:innovation_count]
        v_bits = bits[innovation_count:]
        rows = tuple(window_row(u_bits, v_bits, index) for index in range(row_count))
        total += 1
        for index, row in enumerate(rows):
            marginal_by_row[index][row] += 1
        adjacent[(rows[0], rows[1])] += 1
        lag_two[(rows[0], rows[2])] += 1
        colors[0][(rows[0], rows[2], rows[4])] += 1
        colors[1][(rows[1], rows[3], rows[5])] += 1
    expected_total = 1 << (2 * innovation_count)
    if total != expected_total:
        raise OracleError("window enumeration size is incorrect")
    if any(marginal != marginal_by_row[0] for marginal in marginal_by_row[1:]):
        raise OracleError("fixed window rows do not have a common law")
    assert_factorization(lag_two, [marginal_by_row[0], marginal_by_row[2]], total)
    assert_factorization(
        colors[0], [marginal_by_row[0], marginal_by_row[2], marginal_by_row[4]], total
    )
    assert_factorization(
        colors[1], [marginal_by_row[1], marginal_by_row[3], marginal_by_row[5]], total
    )
    adjacent_discrepancies = []
    for outcome in product(tuple(marginal_by_row[0]), tuple(marginal_by_row[1])):
        observed = probability(adjacent, outcome, total)
        expected = probability(marginal_by_row[0], outcome[0], total) * probability(
            marginal_by_row[1], outcome[1], total
        )
        adjacent_discrepancies.append(abs(observed - expected))
    maximum_adjacent_discrepancy = max(adjacent_discrepancies)
    if maximum_adjacent_discrepancy == 0:
        raise OracleError("adjacent overlapping windows unexpectedly factor")
    reduced_counts = []
    divisor = 0
    for row, count in sorted(marginal_by_row[0].items()):
        divisor = count if divisor == 0 else math.gcd(divisor, count)
        reduced_counts.append((row, count))
    sx_states = tuple(
        ((first, second), target, count // divisor)
        for (first, second, target), count in reduced_counts
    )
    expected_states: tuple[SxState, ...] = (
        ((0, 0), 0, 1),
        ((0, 1), 1, 3),
        ((1, 0), 1, 3),
        ((1, 1), 0, 9),
    )
    if sx_states != expected_states:
        raise OracleError("window population count table is not the expected OR/XOR law")
    return {
        "adjacent_rows_factor": False,
        "color_classes": [[0, 2, 4], [1, 3, 5]],
        "color_classes_factor_jointly": True,
        "innovation_count_per_stream": innovation_count,
        "lag_two_rows_factor": True,
        "maximum_adjacent_factorization_error": fraction_text(
            maximum_adjacent_discrepancy
        ),
        "population_count_table": [
            {
                "count": count,
                "sources": list(sources),
                "target": target,
            }
            for sources, target, count in sx_states
        ],
        "row_count": row_count,
        "sxpid2": sxpid2_oracle(sx_states),
        "window_definition": {
            "source_1": "U_t OR U_(t+1)",
            "source_2": "V_t OR V_(t+1)",
            "target": "source_1 XOR source_2",
        },
        "window_width": width,
    }


def build_log_modulus_checks() -> list[dict[str, Any]]:
    cases = (
        (
            (Fraction(1, 4), Fraction(1, 4), Fraction(1, 2)),
            (Fraction(26, 100), Fraction(24, 100), Fraction(1, 2)),
        ),
        (
            (Fraction(1, 20), Fraction(3, 20), Fraction(4, 5)),
            (Fraction(3, 50), Fraction(7, 50), Fraction(4, 5)),
        ),
        (
            (Fraction(1, 10), Fraction(1, 5), Fraction(7, 10)),
            (Fraction(1, 100), Fraction(1, 5), Fraction(79, 100)),
        ),
    )
    output = []
    for p, q in cases:
        if sum(p) != 1 or sum(q) != 1 or min(p) <= 0 or min(q) <= 0:
            raise OracleError("log-modulus fixture is not a common-support law pair")
        delta = sum(abs(left - right) for left, right in zip(p, q, strict=True))
        p_min = min(p)
        if not delta < 2 * p_min:
            raise OracleError("log-modulus fixture violates the strict support margin")
        x = as_decimal(delta) / (Decimal(2) * as_decimal(p_min))
        modulus = -(Decimal(1) - x).ln()
        maximum_change = Decimal(0)
        maximum_ratio = Decimal(0)
        for mask in range(1, 1 << len(p)):
            p_event = sum(
                (value for index, value in enumerate(p) if mask & (1 << index)),
                Fraction(0),
            )
            q_event = sum(
                (value for index, value in enumerate(q) if mask & (1 << index)),
                Fraction(0),
            )
            event_change = abs(as_decimal(q_event).ln() - as_decimal(p_event).ln())
            maximum_change = max(maximum_change, event_change)
            maximum_ratio = max(maximum_ratio, event_change / modulus)
            if event_change > modulus + TOLERANCE:
                raise OracleError("high-precision event log exceeds the local modulus")
        output.append(
            {
                "delta_l1": fraction_text(delta),
                "maximum_log_change": decimal_text(maximum_change),
                "maximum_to_modulus_ratio": decimal_text(maximum_ratio),
                "modulus": decimal_text(modulus),
                "p": [fraction_text(value) for value in p],
                "p_min": fraction_text(p_min),
                "q": [fraction_text(value) for value in q],
            }
        )
    return output


def exact_binary64_decimal(value: float) -> Decimal:
    """Return the exact real value represented by one finite binary64 input."""
    if not math.isfinite(value):
        raise OracleError("binary64 stability input is not finite")
    return Decimal.from_float(value)


def binary64_bits_text(value: float) -> str:
    """Return the exact binary64 payload as a fixed-width hexadecimal string."""
    if not math.isfinite(value):
        raise OracleError("binary64 bit-pattern input is not finite")
    bits = struct.unpack(">Q", struct.pack(">d", value))[0]
    return f"0x{bits:016x}"


def build_binary64_stability_challenges() -> dict[str, Any]:
    """Build bounded cases for stable evaluation of the refined modulus and diamond ceiling."""
    raw_modulus_cases = (
        (
            "eta-zero",
            "0.25",
            "0",
            "zero",
            "none",
            False,
        ),
        (
            "tiny-ratio-cancellation",
            "0.4",
            "4e-18",
            "series",
            "ratio-log-minus-eta",
            True,
        ),
        (
            "moderate-ratio",
            "0.2",
            "0.03",
            "series",
            "none",
            False,
        ),
        (
            "branch-seam-below-half",
            "0.5",
            "0.24999999999999997",
            "series",
            "none",
            False,
        ),
        (
            "branch-seam-at-half",
            "0.5",
            "0.25",
            "series",
            "none",
            False,
        ),
        (
            "branch-seam-above-half",
            "0.5",
            "0.25000000000000006",
            "quotient-log",
            "none",
            False,
        ),
        (
            "extreme-normal-above-half",
            "1e-300",
            "5.1e-301",
            "quotient-log",
            "none",
            False,
        ),
        (
            "near-boundary-normal-floor",
            "0.4",
            "0.399999999999",
            "quotient-log",
            "ratio-log1p-minus-eta",
            True,
        ),
        (
            "near-boundary-subnormal-floor",
            "1e-300",
            "9.999999999999999e-301",
            "quotient-log",
            "ratio-log1p-minus-eta",
            True,
        ),
        (
            "upper-floor-ratio-lower-endpoint",
            "1.0",
            "0.9999999999999999",
            "quotient-log",
            "none",
            False,
        ),
    )
    modulus_cases = []
    for (
        name,
        p_min_input,
        eta_input,
        adaptive_branch,
        naive_route,
        naive_route_must_fail,
    ) in raw_modulus_cases:
        p_min = float(p_min_input)
        eta = float(eta_input)
        q_floor = p_min - eta
        if not (
            math.isfinite(p_min)
            and math.isfinite(eta)
            and 0 < p_min <= 1
            and 0 <= eta < p_min
            and q_floor > 0
        ):
            raise OracleError(f"{name}: invalid binary64 modulus inputs")
        ratio = eta / p_min
        p_min_exact = exact_binary64_decimal(p_min)
        eta_exact = exact_binary64_decimal(eta)
        if ratio > 0.5:
            q_floor_fraction = Fraction.from_float(q_floor)
            if Fraction.from_float(p_min) - Fraction.from_float(eta) != q_floor_fraction:
                raise OracleError(f"{name}: upper-branch floor subtraction is not exact")
            q_floor_exact = exact_binary64_decimal(q_floor)
        else:
            q_floor_exact = p_min_exact - eta_exact
        if q_floor_exact <= 0:
            raise OracleError(f"{name}: exact binary64 inputs have a non-positive floor")
        selected_branch = (
            "zero"
            if eta == 0
            else "series"
            if ratio <= 0.5
            else "quotient-log"
        )
        if selected_branch != adaptive_branch:
            raise OracleError(f"{name}: stored adaptive modulus branch is stale")
        if name == "branch-seam-below-half":
            if eta != math.nextafter(0.25, 0.0):
                raise OracleError("lower modulus seam input is not the adjacent binary64 value")
        elif name == "branch-seam-at-half":
            if eta != 0.25 or eta / p_min != 0.5:
                raise OracleError("central modulus seam input is not exactly one half")
        elif name == "branch-seam-above-half":
            if eta != math.nextafter(0.25, math.inf):
                raise OracleError("upper modulus seam input is not the adjacent binary64 value")
        elif name == "extreme-normal-above-half":
            smallest_normal = float.fromhex("0x1.0p-1022")
            if not (
                p_min >= smallest_normal
                and eta >= smallest_normal
                and q_floor >= smallest_normal
                and ratio > 0.5
            ):
                raise OracleError(
                    "extreme modulus case is not normal or does not select the upper branch"
                )
        elif name == "near-boundary-subnormal-floor":
            smallest_normal = float.fromhex("0x1.0p-1022")
            if not (
                p_min >= smallest_normal
                and eta >= smallest_normal
                and 0 < q_floor < smallest_normal
                and ratio > 0.5
            ):
                raise OracleError(
                    "near-boundary modulus case does not have the required subnormal floor"
                )
        elif name == "upper-floor-ratio-lower-endpoint":
            if not (
                p_min == 1.0
                and eta == math.nextafter(1.0, 0.0)
                and q_floor == float.fromhex("0x1.0p-53")
            ):
                raise OracleError(
                    "upper modulus endpoint case does not attain q_floor / p_min = 2^-53"
                )
        floor_ratio = q_floor / p_min
        if ratio > 0.5 and not (
            math.isfinite(floor_ratio)
            and floor_ratio >= float.fromhex("0x1.0p-53")
            and floor_ratio <= math.nextafter(0.5, 0.0)
        ):
            raise OracleError(
                f"{name}: upper-branch represented floor ratio is outside "
                "[2^-53, nextDown(1/2)]"
            )
        lambda_nats = (p_min_exact / q_floor_exact).ln()
        refined_modulus_nats = lambda_nats - eta_exact
        if lambda_nats < 0 or refined_modulus_nats < 0:
            raise OracleError(f"{name}: exact binary64 modulus is negative")
        if (
            name == "extreme-normal-above-half"
            and refined_modulus_nats == lambda_nats
        ):
            raise OracleError(
                "the Decimal context did not resolve the extreme refined subtraction"
            )
        if naive_route_must_fail and refined_modulus_nats == 0:
            raise OracleError(f"{name}: a must-fail route needs a positive comparison scale")
        modulus_cases.append(
            {
                "adaptive_branch": adaptive_branch,
                "eta_binary64_bits": binary64_bits_text(eta),
                "eta_input": eta_input,
                "expected_lambda_nats": decimal_text(lambda_nats),
                "expected_refined_modulus_nats": decimal_text(
                    refined_modulus_nats
                ),
                "name": name,
                "naive_route": naive_route,
                "naive_route_must_fail": naive_route_must_fail,
                "p_min_binary64_bits": binary64_bits_text(p_min),
                "p_min_input": p_min_input,
                "q_floor_binary64": repr(q_floor),
                "q_floor_binary64_bits": binary64_bits_text(q_floor),
            }
        )

    raw_diamond_cases = (
        (
            "q-floor-seam-below-half",
            "0.49999999999999994",
            "log-domain",
            False,
        ),
        (
            "q-floor-seam-at-half",
            "0.5",
            "log-domain",
            False,
        ),
        (
            "q-floor-seam-above-half",
            "0.5000000000000001",
            "atanh-transform",
            False,
        ),
        (
            "q-floor-near-one",
            "0.9999999999999999",
            "atanh-transform",
            True,
        ),
        (
            "q-floor-one",
            "1.0",
            "atanh-transform",
            False,
        ),
        (
            "q-floor-subnormal",
            "5e-324",
            "log-domain",
            True,
        ),
    )
    diamond_cases = []
    for name, q_floor_input, adaptive_branch, naive_route_must_fail in raw_diamond_cases:
        q_floor = float(q_floor_input)
        if not math.isfinite(q_floor) or not 0 < q_floor <= 1:
            raise OracleError(f"{name}: invalid binary64 diamond-floor input")
        selected_branch = (
            "atanh-transform" if q_floor > 0.5 else "log-domain"
        )
        if selected_branch != adaptive_branch:
            raise OracleError(f"{name}: stored adaptive diamond branch is stale")
        if name == "q-floor-seam-below-half":
            if q_floor != math.nextafter(0.5, 0.0):
                raise OracleError("lower diamond seam input is not adjacent to one half")
        elif name == "q-floor-seam-at-half":
            if q_floor != 0.5:
                raise OracleError("central diamond seam input is not exactly one half")
        elif name == "q-floor-seam-above-half":
            if q_floor != math.nextafter(0.5, math.inf):
                raise OracleError("upper diamond seam input is not adjacent to one half")
        q_floor_exact = exact_binary64_decimal(q_floor)
        diamond_ceiling_nats = (
            Decimal(0)
            if q_floor == 1.0
            else Decimal(2) * (Decimal(1) + q_floor_exact).ln()
            - q_floor_exact.ln()
            - Decimal(4).ln()
        )
        if diamond_ceiling_nats < 0:
            raise OracleError(f"{name}: exact binary64 diamond ceiling is negative")
        if naive_route_must_fail and diamond_ceiling_nats == 0:
            raise OracleError(f"{name}: a must-fail route needs a positive comparison scale")
        diamond_cases.append(
            {
                "adaptive_branch": adaptive_branch,
                "expected_diamond_ceiling_nats": decimal_text(
                    diamond_ceiling_nats
                ),
                "name": name,
                "naive_route": "product-ratio-log",
                "naive_route_must_fail": naive_route_must_fail,
                "q_floor_binary64_bits": binary64_bits_text(q_floor),
                "q_floor_input": q_floor_input,
            }
        )

    return {
        "diamond_ceiling_cases": diamond_cases,
        "modulus_cases": modulus_cases,
        "reference_input_model": (
            "400-digit Decimal functions applied to the exact real values of the binary64 "
            "numbers parsed from the stored decimal inputs; stored hexadecimal payloads bind "
            "each parsed operand and represented subtraction result"
        ),
    }


def build_support_and_marginal_challenges() -> dict[str, Any]:
    boundary_p = (Fraction(1, 4), Fraction(3, 4))
    boundary_q = (Fraction(0), Fraction(1))
    p_min = min(boundary_p)
    boundary_delta = sum(
        abs(left - right)
        for left, right in zip(boundary_p, boundary_q, strict=True)
    )
    if boundary_delta != 2 * p_min:
        raise OracleError("support deletion is not at the strict L1 boundary")
    if boundary_q[boundary_p.index(p_min)] != 0:
        raise OracleError("support deletion did not remove the minimum-mass cell")
    rho = Fraction(9, 10)
    p_rho = (
        (1 + rho) / 4,
        (1 - rho) / 4,
        (1 - rho) / 4,
        (1 + rho) / 4,
    )
    q_rho = (
        (1 - rho) / 4,
        (1 + rho) / 4,
        (1 + rho) / 4,
        (1 - rho) / 4,
    )
    p_marginals = (
        p_rho[0] + p_rho[1],
        p_rho[2] + p_rho[3],
        p_rho[0] + p_rho[2],
        p_rho[1] + p_rho[3],
    )
    q_marginals = (
        q_rho[0] + q_rho[1],
        q_rho[2] + q_rho[3],
        q_rho[0] + q_rho[2],
        q_rho[1] + q_rho[3],
    )
    if p_marginals != q_marginals or set(p_marginals) != {Fraction(1, 2)}:
        raise OracleError("marginal-only challenge does not preserve fair marginals")
    pointwise_difference = (as_decimal(1 + rho) / as_decimal(1 - rho)).ln()
    p_states = duplicate_source_states(p_rho)
    q_states = duplicate_source_states(q_rho)
    p_sxpid = sxpid2_oracle(p_states)
    q_sxpid = sxpid2_oracle(q_states)
    p_pointwise = pointwise_atom(p_sxpid, [0, 0], 0, [1, 2])
    q_pointwise = pointwise_atom(q_sxpid, [0, 0], 0, [1, 2])
    oracle_pointwise_difference = abs(
        Decimal(p_pointwise["net_nats"]) - Decimal(q_pointwise["net_nats"])
    )
    if abs(oracle_pointwise_difference - pointwise_difference) > TOLERANCE:
        raise OracleError("marginal-only SxPID pointwise change is incorrect")

    baseline_states: tuple[SxState, ...] = (((0, 0), 0, 1),)
    baseline_sxpid = sxpid2_oracle(baseline_states)
    baseline_redundancy = Decimal(
        averaged_atom(baseline_sxpid, [1, 2])["net_nats"]
    )
    if abs(baseline_redundancy) > TOLERANCE:
        raise OracleError("one-cell duplicate-source redundancy must be zero")
    entropy_ratios = []
    previous = Decimal(0)
    for exponent in (4, 6, 8, 10, 12):
        epsilon = Fraction(1, 1 << exponent)
        value = as_decimal(epsilon)
        entropy = -value * value.ln() - (Decimal(1) - value) * (
            Decimal(1) - value
        ).ln()
        ratio = entropy / (Decimal(2) * value)
        if ratio <= previous:
            raise OracleError("new-support entropy ratio did not increase")
        alternative_states: tuple[SxState, ...] = (
            ((0, 0), 0, (1 << exponent) - 1),
            ((1, 1), 1, 1),
        )
        alternative_sxpid = sxpid2_oracle(alternative_states)
        alternative_redundancy = Decimal(
            averaged_atom(alternative_sxpid, [1, 2])["net_nats"]
        )
        if abs(alternative_redundancy - entropy) > TOLERANCE:
            raise OracleError("new-support SxPID redundancy is not binary entropy")
        previous = ratio
        entropy_ratios.append(
            {
                "averaged_redundancy_nats": decimal_text(entropy),
                "epsilon": fraction_text(epsilon),
                "population_count_table": state_count_table(alternative_states),
                "redundancy_to_l1_ratio": decimal_text(ratio),
            }
        )
    return {
        "marginal_only": {
            "all_individual_marginals": [fraction_text(value) for value in p_marginals],
            "pointwise_change_nats": decimal_text(pointwise_difference),
            "p_population_count_table": state_count_table(p_states),
            "p_pointwise_redundancy_nats": p_pointwise["net_nats"],
            "q_population_count_table": state_count_table(q_states),
            "q_pointwise_redundancy_nats": q_pointwise["net_nats"],
            "rho": fraction_text(rho),
            "source_construction": "S1 = S2 = X",
        },
        "new_support": {
            "baseline_population_count_table": state_count_table(baseline_states),
            "cases": entropy_ratios,
            "source_target_construction": "S1 = S2 = T",
            "statement": (
                "the redundancy change is binary entropy and has no uniform linear L1 bound"
            ),
        },
        "support_deletion_boundary": {
            "delta_l1": fraction_text(boundary_delta),
            "p": [fraction_text(value) for value in boundary_p],
            "p_min": fraction_text(p_min),
            "q": [fraction_text(value) for value in boundary_q],
            "statement": "a supported cell disappears exactly at delta equal to twice p_min",
        },
    }


def build_fixture() -> dict[str, Any]:
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        fixture = {
            "arithmetic": {
                "decimal_precision_digits": DECIMAL_PRECISION,
                "fraction_arithmetic": "exact",
                "third_party_dependencies": [],
            },
            "binary64_stability_challenges": build_binary64_stability_challenges(),
            "challenge_cases": {
                "adaptive_coloring": build_adaptive_color_counterexample(),
                "conditioned_diamond_negative_lift": (
                    build_conditioned_diamond_negative_lift_counterexamples()
                ),
                "copied_colors": build_copied_color_counterexample(),
                "net_weight_half_factor": (
                    build_net_weight_half_factor_counterexample()
                ),
                "non_synergy_refined_modulus": (
                    build_non_synergy_refined_modulus_counterexamples()
                ),
                "pairwise_independence": build_pairwise_counterexample(),
                "singleton_colors": build_singleton_color_counterexample(),
                "support_and_marginals": build_support_and_marginal_challenges(),
                "unspecified_mixing": build_unspecified_mixing_counterexample(),
            },
            "class_profiles": build_class_profiles(),
            "conditioned_diamond_gradient_cases": (
                build_conditioned_diamond_gradient_cases()
            ),
            "conditioned_diamond_extremal_regimes": (
                build_conditioned_diamond_extremal_regimes()
            ),
            "generator": {
                "path": "scripts/generate-dependency-colored-sxpid-oracle.py",
                "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "standard_library_only": True,
            },
            "log_modulus_cases": build_log_modulus_checks(),
            "local_sxpid2_modulus_cases": build_sxpid2_modulus_cases(),
            "method_provenance": {
                "definition_origin": "project-defined",
                "paper_defined_target": "categorical shared-exclusions PID",
                "scientific_novelty_claim": "none",
            },
            "schema": SCHEMA,
            "schema_revision": SCHEMA_REVISION,
            "scope_boundary": (
                "bounded fraction-exact and 400-digit Decimal challenges; not a general theorem, "
                "binary64 certificate, external review, or continuous-PID result"
            ),
            "telescoping_checks": build_telescoping_checks(),
            "window_case": build_window_case(),
        }
    return fixture


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the committed fixture and SHA-256 sidecar",
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
        print(f"wrote dependency-colored SxPID fixture; SHA-256 {digest}")
        return 0
    try:
        committed = OUTPUT.read_bytes()
        committed_sidecar = SIDECAR.read_text(encoding="utf-8")
    except OSError as error:
        print(f"dependency-colored SxPID fixture error: {error}")
        return 1
    if committed != raw:
        print("dependency-colored SxPID fixture error: committed data is stale")
        return 1
    if committed_sidecar != sidecar:
        print("dependency-colored SxPID fixture error: SHA-256 sidecar is stale")
        return 1
    print(f"OK: dependency-colored SxPID fixture matches SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
