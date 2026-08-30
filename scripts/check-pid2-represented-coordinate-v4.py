#!/usr/bin/env python3
"""Check bounded PID2 represented-coordinate arithmetic without host floating point.

The exact model uses integers and ``fractions.Fraction`` only.  It checks binary64
round-to-nearest, ties-to-even behavior for already represented coordinates; it does not model
how an estimator obtained those coordinates.  Source custody and compiled Rust executions are
separate, explicitly reported scopes.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SIGN_MASK = 1 << 63
EXPONENT_MASK = 0x7FF << 52
FRACTION_MASK = (1 << 52) - 1
U64_MASK = (1 << 64) - 1
POSITIVE_INFINITY_BITS = 0x7FF0_0000_0000_0000
NEGATIVE_INFINITY_BITS = 0xFFF0_0000_0000_0000
CANONICAL_NAN_BITS = 0x7FF8_0000_0000_0000
MAXIMUM_FINITE_BITS = 0x7FEF_FFFF_FFFF_FFFF
IDENTITY_GUARD_MAX_ORDERED_DISTANCE = 32
FAMILY_MAX_SCALE = 1023
EXPECTED_FAMILY_CASES = 1023

SOURCE_SHA256 = {
    "crates/pid-core/src/exact_binary64.rs": (
        "6e7d6be525878638e4be253aff9bd74d25dd94afb53f1b520fb8e4e1a0a8cdfb"
    ),
    "crates/pid-core/src/pid2.rs": (
        "d9fe89db5fcabd1b2666be5581726b18c8bf465b71d7ebc21e3fe3089007e147"
    ),
    "crates/pid-core/tests/pid2.rs": (
        "967a26dac7633841ac14670e5f4d3362e0a4cfcf35beed72ef264d8b9d5b70bf"
    ),
    "crates/pid-core/src/bin/exp0.rs": (
        "b839bf15602b4ffcd68f201f547cf48c7e4648400600afa9721cfb391d09e0ec"
    ),
}

PID2_UNIT_TESTS = (
    "candidate_synergy_distinguishes_exact_reduction_from_neumaier_reduction",
    "checked_constructor_rejects_both_finite_identity_erasure_directions",
    "checked_constructor_rejects_exact_candidate_synergy_overflow",
    "conditioning_rejects_nonfinite_absolute_constituent_sum",
    "conditioning_reports_all_terms_zero",
    "conditioning_reports_amplification_beyond_binary64_range",
    "conditioning_reports_exact_cancellation",
    "conditioning_reports_finite_amplification",
    "exact_candidate_rejects_the_historical_direct_compensation_witness",
    "exact_guard_accepts_a_witness_rejected_by_left_association",
    "exact_guard_accepts_a_witness_rejected_by_neumaier_overflow",
    "exact_reconstruction_limb_visits_are_fully_charged",
    "identity_guard_rejects_false_sixteen_times_joint_scale_bound_witness",
    "k_scale_four_is_the_named_exact_times_sixteen_case",
    "ordinary_scale_guard_accepts_exact_distance_32",
    "ordinary_scale_guard_rejects_exact_distance_33",
    "every_scale_family_member_accepts_then_exact_scaling_reaches_one_rejected_endpoint",
)

PID2_INTEGRATION_REQUIRED = (
    "pid2_checked_constructor_accepts_inclusive_32_position_near_zero_boundary",
    "pid2_checked_constructor_rejects_33_position_near_zero_boundary",
    "pid2_checked_constructor_accepts_negative_31_position_near_zero_boundary",
    "pid2_checked_constructor_rejects_negative_32_position_near_zero_boundary",
    "pid2_checked_constructor_obeys_all_field_local_signed_zero_rules",
    "pid2_checked_constructor_exact_synergy_is_source_order_independent",
    "pid2_checked_constructor_recovers_representable_synergy_after_intermediate_overflow",
    "pid2_checked_constructor_rejects_tiny_identity_erased_by_exact_atom_reconstruction",
)

EXP0_REQUIRED = (
    "atom_estimator_instability_is_typed_and_non_gating",
    "optional_synergy_uses_checked_exact_pid2_arithmetic",
    "pid2_synergy_classification_propagates_unexpected_errors",
)

EXPECTED_PID2_UNIT_COUNT = 17
EXPECTED_PID2_INTEGRATION_COUNT = 18
EXPECTED_EXP0_COUNT = 34
COMPILED_PROFILES = ("debug", "release")
COMMAND_TIMEOUT_SECONDS = 900
MAX_CAPTURE_BYTES = 2 * 1024 * 1024

MODEL_OUTPUT = (
    "OK: scope=model; exact integer/Fraction PID2 model checked 1023 accepted scale-family "
    "seeds, 1023 scaled cases reaching one rejected endpoint, all 16 signed-zero tuples, "
    "Neumaier steps, the "
    "declared boundary/overflow controls, and all 5 conditioning outcomes; source=not-read; "
    "compiled=not-run; no estimator, "
    "calibration, paper-defect, or Rust-refinement claim"
)
MODEL_SOURCE_OUTPUT = (
    "OK: scope=model-source; exact integer/Fraction PID2 model checked 1023 accepted "
    "scale-family seeds, 1023 scaled cases reaching one rejected endpoint, all 16 signed-zero "
    "tuples, Neumaier "
    "steps, the declared boundary/overflow controls, and all 5 conditioning outcomes; source=4 "
    "exact files; compiled=not-run; "
    "no estimator, calibration, paper-defect, or Rust-refinement claim"
)
FULL_OUTPUT = (
    "OK: scope=full; exact integer/Fraction PID2 model checked 1023 accepted scale-family "
    "seeds, 1023 scaled cases reaching one rejected endpoint, all 16 signed-zero tuples, "
    "Neumaier steps, the "
    "declared boundary/overflow controls, and all 5 conditioning outcomes; source=4 exact files; "
    "compiled=2 profiles with "
    "17 PID2 unit, 18 PID2 integration, and 34 exp0 tests per profile; no estimator, "
    "calibration, paper-defect, or Rust-refinement claim"
)


class AssuranceError(RuntimeError):
    """Raised when a represented-coordinate obligation fails closed."""


@dataclass(frozen=True)
class ConstructorOutcome:
    status: str
    atoms: tuple[int, int, int, int] | None


@dataclass(frozen=True)
class ConditioningOutcome:
    status: str
    absolute_sum: int
    retained_fraction: int | None
    amplification_factor: int | None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssuranceError(message)


def is_finite_bits(bits: int) -> bool:
    return bits & EXPONENT_MASK != EXPONENT_MASK


def is_nan_bits(bits: int) -> bool:
    return bits & EXPONENT_MASK == EXPONENT_MASK and bits & FRACTION_MASK != 0


def is_infinite_bits(bits: int) -> bool:
    return bits & ~SIGN_MASK == POSITIVE_INFINITY_BITS


def is_zero_bits(bits: int) -> bool:
    return bits & ~SIGN_MASK == 0


def negate_bits(bits: int) -> int:
    return bits ^ SIGN_MASK


def finite_bits_to_fraction(bits: int) -> Fraction:
    require(is_finite_bits(bits), f"non-finite bits in exact conversion: 0x{bits:016x}")
    exponent_field = (bits >> 52) & 0x7FF
    fraction_field = bits & FRACTION_MASK
    if exponent_field == 0:
        significand = fraction_field
        binary_power = -1074
    else:
        significand = (1 << 52) | fraction_field
        binary_power = exponent_field - 1023 - 52
    numerator = -significand if bits & SIGN_MASK else significand
    if binary_power >= 0:
        return Fraction(numerator << binary_power, 1)
    return Fraction(numerator, 1 << -binary_power)


def floor_log2_fraction(value: Fraction) -> int:
    require(value > 0, "floor_log2_fraction requires a positive value")
    numerator = value.numerator
    denominator = value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < denominator << exponent:
            exponent -= 1
    elif numerator << -exponent < denominator:
        exponent -= 1
    return exponent


def round_ratio_to_integer(numerator: int, denominator: int) -> int:
    require(numerator >= 0 and denominator > 0, "invalid nonnegative rounding ratio")
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = remainder << 1
    if twice_remainder > denominator or (
        twice_remainder == denominator and quotient & 1 == 1
    ):
        quotient += 1
    return quotient


def scaled_round_to_integer(value: Fraction, binary_power: int) -> int:
    require(value >= 0, "scaled rounding requires a nonnegative value")
    if binary_power >= 0:
        return round_ratio_to_integer(
            value.numerator << binary_power, value.denominator
        )
    return round_ratio_to_integer(
        value.numerator, value.denominator << -binary_power
    )


def round_fraction_to_binary64_bits(value: Fraction) -> int:
    if value == 0:
        return 0
    sign = SIGN_MASK if value < 0 else 0
    magnitude = abs(value)
    exponent = floor_log2_fraction(magnitude)
    if exponent < -1022:
        significand = scaled_round_to_integer(magnitude, 1074)
        if significand == 0:
            return sign
        if significand >= 1 << 52:
            return sign | (1 << 52)
        return sign | significand

    significand = scaled_round_to_integer(magnitude, 52 - exponent)
    if significand == 1 << 53:
        significand = 1 << 52
        exponent += 1
    if exponent > 1023:
        return sign | POSITIVE_INFINITY_BITS
    require(
        (1 << 52) <= significand < (1 << 53),
        "normal binary64 significand escaped its exact range",
    )
    exponent_field = exponent + 1023
    return sign | (exponent_field << 52) | (significand - (1 << 52))


def exact_sum_bits(terms: tuple[int, ...]) -> int:
    require(all(is_finite_bits(term) for term in terms), "exact sum received non-finite input")
    total = sum((finite_bits_to_fraction(term) for term in terms), Fraction(0, 1))
    return round_fraction_to_binary64_bits(total)


def rounded_add_bits(left: int, right: int) -> int:
    if is_nan_bits(left) or is_nan_bits(right):
        return CANONICAL_NAN_BITS
    if is_infinite_bits(left) or is_infinite_bits(right):
        if is_infinite_bits(left) and is_infinite_bits(right):
            if (left ^ right) & SIGN_MASK:
                return CANONICAL_NAN_BITS
            return left
        return left if is_infinite_bits(left) else right
    if is_zero_bits(left) and is_zero_bits(right):
        return SIGN_MASK if left & SIGN_MASK and right & SIGN_MASK else 0
    total = finite_bits_to_fraction(left) + finite_bits_to_fraction(right)
    return round_fraction_to_binary64_bits(total)


def rounded_subtract_bits(left: int, right: int) -> int:
    return rounded_add_bits(left, negate_bits(right))


def rounded_multiply_bits(left: int, right: int) -> int:
    require(
        is_finite_bits(left) and is_finite_bits(right),
        "rounded product requires finite operands",
    )
    product = finite_bits_to_fraction(left) * finite_bits_to_fraction(right)
    if product == 0:
        return SIGN_MASK if (left ^ right) & SIGN_MASK else 0
    return round_fraction_to_binary64_bits(product)


def rounded_positive_divide_bits(numerator: int, denominator: int) -> int:
    require(
        is_finite_bits(numerator)
        and is_finite_bits(denominator)
        and numerator & SIGN_MASK == 0
        and denominator & SIGN_MASK == 0
        and not is_zero_bits(denominator),
        "positive division requires finite nonnegative bits and a positive denominator",
    )
    quotient = finite_bits_to_fraction(numerator) / finite_bits_to_fraction(denominator)
    return round_fraction_to_binary64_bits(quotient)


def absolute_greater_or_equal(left: int, right: int) -> bool:
    if is_nan_bits(left) or is_nan_bits(right):
        return False
    if is_infinite_bits(left):
        return True
    if is_infinite_bits(right):
        return False
    return abs(finite_bits_to_fraction(left)) >= abs(finite_bits_to_fraction(right))


def neumaier_trace(terms: tuple[int, ...]) -> tuple[tuple[tuple[int, int], ...], int]:
    running = 0
    correction = 0
    trace: list[tuple[int, int]] = []
    for term in terms:
        next_running = rounded_add_bits(running, term)
        if absolute_greater_or_equal(running, term):
            increment = rounded_add_bits(
                rounded_subtract_bits(running, next_running), term
            )
        else:
            increment = rounded_add_bits(
                rounded_subtract_bits(term, next_running), running
            )
        correction = rounded_add_bits(correction, increment)
        running = next_running
        trace.append((running, correction))
    return tuple(trace), rounded_add_bits(running, correction)


def sequential_sum_bits(terms: tuple[int, ...]) -> int:
    total = 0
    for term in terms:
        total = rounded_add_bits(total, term)
    return total


def historical_synergy_bits(i1: int, i2: int, joint: int, redundancy: int) -> int:
    return rounded_add_bits(
        rounded_subtract_bits(rounded_subtract_bits(joint, i1), i2), redundancy
    )


def exact_synergy_bits(i1: int, i2: int, joint: int, redundancy: int) -> int:
    return exact_sum_bits((joint, negate_bits(i1), negate_bits(i2), redundancy))


def ordered_float_bits(bits: int) -> int:
    return bits | SIGN_MASK if bits & SIGN_MASK == 0 else (~bits) & U64_MASK


def ordered_distance(left: int, right: int) -> int:
    return abs(ordered_float_bits(left) - ordered_float_bits(right))


def identity_matches(expected: int, terms: tuple[int, ...]) -> bool:
    reconstructed = exact_sum_bits(terms)
    return is_finite_bits(reconstructed) and ordered_distance(reconstructed, expected) <= (
        IDENTITY_GUARD_MAX_ORDERED_DISTANCE
    )


def modeled_constructor(i1: int, i2: int, joint: int, redundancy: int) -> ConstructorOutcome:
    inputs = (i1, i2, joint, redundancy)
    if not all(is_finite_bits(value) for value in inputs):
        return ConstructorOutcome("input_nonfinite", None)
    unique_one = rounded_subtract_bits(i1, redundancy)
    unique_two = rounded_subtract_bits(i2, redundancy)
    synergy = exact_synergy_bits(i1, i2, joint, redundancy)
    atoms = (redundancy, unique_one, unique_two, synergy)
    if not all(is_finite_bits(value) for value in atoms):
        return ConstructorOutcome("atom_nonfinite", atoms)
    if not (
        identity_matches(i1, (redundancy, unique_one))
        and identity_matches(i2, (redundancy, unique_two))
        and identity_matches(joint, atoms)
    ):
        return ConstructorOutcome("identity_rejected", atoms)
    return ConstructorOutcome("accepted", atoms)


def modeled_conditioning(value: int, signed_terms: tuple[int, ...]) -> ConditioningOutcome:
    require(
        is_finite_bits(value) and all(is_finite_bits(term) for term in signed_terms),
        "conditioning model requires finite represented inputs",
    )
    absolute_terms = tuple(term & ~SIGN_MASK for term in signed_terms)
    absolute_sum = exact_sum_bits(absolute_terms)
    if not is_finite_bits(absolute_sum):
        return ConditioningOutcome("absolute_sum_nonfinite", absolute_sum, None, None)
    if is_zero_bits(absolute_sum):
        return ConditioningOutcome("all_terms_zero", absolute_sum, None, None)
    absolute_value = value & ~SIGN_MASK
    retained = rounded_positive_divide_bits(absolute_value, absolute_sum)
    if is_zero_bits(value):
        return ConditioningOutcome("exact_cancellation", absolute_sum, retained, None)
    amplification = round_fraction_to_binary64_bits(
        finite_bits_to_fraction(absolute_sum) / finite_bits_to_fraction(absolute_value)
    )
    if not is_finite_bits(amplification):
        return ConditioningOutcome(
            "amplification_exceeds_binary64", absolute_sum, retained, None
        )
    return ConditioningOutcome("finite", absolute_sum, retained, amplification)


def require_bits(actual: int, expected: int, label: str) -> None:
    require(
        actual == expected,
        f"{label}: expected 0x{expected:016x}, got 0x{actual:016x}",
    )


def check_rounding_primitives() -> None:
    unit = Fraction(1, 1 << 1074)
    require_bits(round_fraction_to_binary64_bits(unit), 1, "minimum subnormal")
    require_bits(round_fraction_to_binary64_bits(unit / 2), 0, "zero-side even tie")
    require_bits(
        round_fraction_to_binary64_bits(3 * unit / 2), 2, "subnormal even tie"
    )
    require_bits(
        round_fraction_to_binary64_bits(finite_bits_to_fraction(MAXIMUM_FINITE_BITS)),
        MAXIMUM_FINITE_BITS,
        "maximum finite identity",
    )
    overflow_midpoint = Fraction(1 << 1024, 1) - Fraction(1 << 970, 1)
    require_bits(
        round_fraction_to_binary64_bits(overflow_midpoint),
        POSITIVE_INFINITY_BITS,
        "overflow midpoint tie",
    )


def check_identity_erasure_directions() -> None:
    one = 0x3FF0_0000_0000_0000
    huge = 0x7E37_E43C_8800_759C
    for coordinates in ((one, 0, 0, huge), (0, one, 0, huge)):
        outcome = modeled_constructor(*coordinates)
        require(
            outcome.status == "identity_rejected",
            "finite identity-erasure direction was not rejected",
        )


def check_direct_compensation_15_49() -> None:
    i1 = 0x46D2_FA52_B582_F1F7
    i2 = 0xC6DF_8D03_96DF_4FCE
    joint = 0x4688_AEBF_760D_4051
    redundancy = 0x46DF_89C6_8C94_7EE9
    unique_one = rounded_subtract_bits(i1, redundancy)
    unique_two = rounded_subtract_bits(i2, redundancy)
    historical = historical_synergy_bits(i1, i2, joint, redundancy)
    exact = exact_synergy_bits(i1, i2, joint, redundancy)
    require_bits(historical, 0x46E6_70F6_B4D0_A362, "15/49 historical synergy")
    require_bits(exact, 0x46E6_70F6_B4D0_A361, "15/49 exact synergy")
    historical_reconstruction = exact_sum_bits(
        (redundancy, unique_one, unique_two, historical)
    )
    exact_reconstruction = exact_sum_bits((redundancy, unique_one, unique_two, exact))
    require(
        ordered_distance(historical_reconstruction, joint) == 15,
        "historical 15-position reconstruction changed",
    )
    require(
        ordered_distance(exact_reconstruction, joint) == 49,
        "exact 49-position reconstruction changed",
    )
    require(
        modeled_constructor(i1, i2, joint, redundancy).status == "identity_rejected",
        "the exact 49-position constructor witness must be rejected",
    )


def check_candidate_exact_vs_neumaier() -> None:
    coordinates = (
        0x4395_0F65_78A6_93C8,
        0xC373_5876_98E1_0B0B,
        0x4399_6DC6_03DA_8752,
        0xBC46_9A3C_16C4_C8C1,
    )
    i1, i2, joint, redundancy = coordinates
    terms = (joint, negate_bits(i1), negate_bits(i2), redundancy)
    exact = exact_sum_bits(terms)
    _, neumaier = neumaier_trace(terms)
    require_bits(exact, 0x4382_68FC_62D8_6C99, "candidate exact reduction")
    require_bits(neumaier, 0x4382_68FC_62D8_6C9A, "candidate Neumaier reduction")
    outcome = modeled_constructor(*coordinates)
    require(outcome.status == "accepted", "exact candidate witness must be accepted")
    require(outcome.atoms is not None, "accepted candidate witness has no atoms")
    require_bits(outcome.atoms[3], exact, "constructor exact candidate synergy")


def check_guard_left_association_5_155() -> None:
    coordinates = (
        0x4072_352E_2888_9826,
        0x4044_88B4_EBC8_8F45,
        0x3FF8_4372_5BB2_F39B,
        0x4042_8166_6D28_8D41,
    )
    outcome = modeled_constructor(*coordinates)
    require(outcome.status == "accepted", "5/155 exact witness must be accepted")
    require(outcome.atoms is not None, "5/155 accepted witness has no atoms")
    exact = exact_sum_bits(outcome.atoms)
    left = sequential_sum_bits(outcome.atoms)
    _, neumaier = neumaier_trace(outcome.atoms)
    require_bits(exact, 0x3FF8_4372_5BB2_F3A0, "5/155 exact reconstruction")
    require_bits(left, 0x3FF8_4372_5BB2_F300, "5/155 left reconstruction")
    require(ordered_distance(exact, coordinates[2]) == 5, "exact distance is not 5")
    require(ordered_distance(left, coordinates[2]) == 155, "left distance is not 155")
    require(
        ordered_distance(neumaier, coordinates[2]) == 5,
        "Neumaier control no longer agrees with the exact guard on the 5/155 witness",
    )


def check_guard_neumaier_overflow_trace() -> None:
    i1 = 0x7FD8_0000_0000_0000
    i2 = 0x7FD8_0000_0000_0000
    joint = 0x7FE8_0000_0000_0000
    redundancy = 0xFFE0_0000_0000_0000
    outcome = modeled_constructor(i1, i2, joint, redundancy)
    require(outcome.status == "accepted", "Neumaier guard discriminator must be accepted")
    require(outcome.atoms is not None, "Neumaier guard discriminator has no atoms")
    require(
        outcome.atoms
        == (
            0xFFE0_0000_0000_0000,
            0x7FEC_0000_0000_0000,
            0x7FEC_0000_0000_0000,
            0xFFE0_0000_0000_0000,
        ),
        "Neumaier guard discriminator atom bits changed",
    )
    candidate_terms = (joint, negate_bits(i1), negate_bits(i2), redundancy)
    _, neumaier_candidate = neumaier_trace(candidate_terms)
    require_bits(neumaier_candidate, redundancy, "Neumaier candidate discriminator")
    trace, neumaier_reconstruction = neumaier_trace(outcome.atoms)
    expected_trace = (
        (0xFFE0_0000_0000_0000, 0),
        (0x7FD8_0000_0000_0000, 0),
        (POSITIVE_INFINITY_BITS, NEGATIVE_INFINITY_BITS),
        (POSITIVE_INFINITY_BITS, CANONICAL_NAN_BITS),
    )
    require(trace == expected_trace, "Neumaier guard step trace changed")
    require(is_nan_bits(neumaier_reconstruction), "Neumaier guard result must be NaN")
    exact_reconstruction = exact_sum_bits(outcome.atoms)
    require_bits(exact_reconstruction, joint, "exact Neumaier-guard reconstruction")
    require(ordered_distance(exact_reconstruction, joint) == 0, "exact guard lost identity")


def check_signed_zero_tuples() -> None:
    observed = 0
    for i1 in (0, SIGN_MASK):
        for i2 in (0, SIGN_MASK):
            for joint in (0, SIGN_MASK):
                for redundancy in (0, SIGN_MASK):
                    outcome = modeled_constructor(i1, i2, joint, redundancy)
                    require(outcome.status == "accepted", "signed-zero tuple was rejected")
                    require(outcome.atoms is not None, "signed-zero tuple has no atoms")
                    expected_unique_one = SIGN_MASK if i1 == SIGN_MASK and redundancy == 0 else 0
                    expected_unique_two = SIGN_MASK if i2 == SIGN_MASK and redundancy == 0 else 0
                    expected = (
                        redundancy,
                        expected_unique_one,
                        expected_unique_two,
                        0,
                    )
                    require(outcome.atoms == expected, "field-local signed-zero rule changed")
                    observed += 1
    require(observed == 16, "signed-zero enumeration did not cover 16 tuples")


def check_guard_boundaries() -> None:
    ordinary_32 = (
        0xC0BF_8D66_2B97_A649,
        0x4109_3D1A_13E4_C232,
        0xC073_5EB8_36C1_2CC0,
        0x40CC_E37D_3383_9B57,
    )
    accepted = modeled_constructor(*ordinary_32)
    require(accepted.status == "accepted", "ordinary distance-32 boundary was rejected")
    require(accepted.atoms is not None, "ordinary distance-32 boundary has no atoms")
    require(
        ordered_distance(exact_sum_bits(accepted.atoms), ordinary_32[2]) == 32,
        "ordinary accepted boundary is not distance 32",
    )

    ordinary_33 = (
        0xBFE4_EC19_92F1_B794,
        0xBFC4_614C_6039_E98B,
        0x3F76_B2AF_711E_5A91,
        0xBFE7_2423_A04E_5292,
    )
    rejected = modeled_constructor(*ordinary_33)
    require(rejected.status == "identity_rejected", "ordinary distance-33 boundary passed")
    require(rejected.atoms is not None, "ordinary distance-33 boundary has no atoms")
    require(
        ordered_distance(exact_sum_bits(rejected.atoms), ordinary_33[2]) == 33,
        "ordinary rejected boundary is not distance 33",
    )

    one = 0x3FF0_0000_0000_0000
    for payload, expected_status in ((32, "accepted"), (33, "identity_rejected")):
        outcome = modeled_constructor(payload, one, payload, one)
        require(outcome.status == expected_status, "positive near-zero boundary changed")
    for payload, expected_status in ((31, "accepted"), (32, "identity_rejected")):
        negative_payload = SIGN_MASK | payload
        outcome = modeled_constructor(negative_payload, one, negative_payload, one)
        require(outcome.status == expected_status, "negative near-zero boundary changed")


def check_false_sixteen_joint_bound() -> None:
    coordinates = (
        0x7FE4_4DCF_B32F_7B9B,
        0x7FBF_7961_1391_5533,
        MAXIMUM_FINITE_BITS,
        0x7FD1_E3B3_ADC8_20E6,
    )
    outcome = modeled_constructor(*coordinates)
    require(outcome.status == "identity_rejected", "false 16|J| witness must reject")
    require(outcome.atoms is not None, "false 16|J| witness has no finite atom tuple")
    expected_atoms = (
        0x7FD1_E3B3_ADC8_20E6,
        0x7FD6_B7EB_B896_D650,
        0xFFC4_0AB6_D1C7_9732,
        0x7FE0_B4DE_0142_6A31,
    )
    require(outcome.atoms == expected_atoms, "false 16|J| witness atom bits changed")
    joint_magnitude = abs(finite_bits_to_fraction(coordinates[2]))
    exact_scale_bound = 16 * joint_magnitude
    require(
        all(
            abs(finite_bits_to_fraction(atom)) <= joint_magnitude
            for atom in outcome.atoms
        ),
        "false 16|J| witness no longer satisfies the stronger max-atom <= |J| premise",
    )
    require(
        all(
            abs(finite_bits_to_fraction(atom)) <= exact_scale_bound
            for atom in outcome.atoms
        ),
        "false 16|J| witness no longer satisfies the exact-real scale premise",
    )
    require_bits(exact_sum_bits(outcome.atoms), POSITIVE_INFINITY_BITS, "false-bound sum")


def family_member(k_scale: int) -> tuple[int, int, int, int]:
    require(1 <= k_scale <= FAMILY_MAX_SCALE, "family scale is outside 1..=1023")
    i2 = ((0x7FC - k_scale) << 52) | (FRACTION_MASK - 1)
    joint = ((0x7FE - k_scale) << 52) | FRACTION_MASK
    return (0, i2, joint, 0)


def check_scale_family() -> None:
    endpoint = (0, 0x7FCF_FFFF_FFFF_FFFE, 0x7FEF_FFFF_FFFF_FFFF, 0)
    observed = 0
    for k_scale in range(1, FAMILY_MAX_SCALE + 1):
        coordinates = family_member(k_scale)
        outcome = modeled_constructor(*coordinates)
        require(outcome.status == "accepted", f"family seed k={k_scale} was rejected")
        require(outcome.atoms is not None, f"family seed k={k_scale} has no atoms")
        expected_synergy = ((0x7FE - k_scale) << 52) | (1 << 51)
        require_bits(outcome.atoms[3], expected_synergy, f"family synergy k={k_scale}")
        expected_reconstruction = (0x7FF - k_scale) << 52
        reconstruction = exact_sum_bits(outcome.atoms)
        require_bits(reconstruction, expected_reconstruction, f"family reconstruction k={k_scale}")
        require(
            ordered_distance(reconstruction, coordinates[2]) == 1,
            f"family seed k={k_scale} is not one ordered position from J",
        )
        factor = (0x3FF + k_scale) << 52
        scaled = tuple(rounded_multiply_bits(value, factor) for value in coordinates)
        require(scaled == endpoint, f"family scaled endpoint changed at k={k_scale}")
        scaled_outcome = modeled_constructor(*scaled)
        require(
            scaled_outcome.status == "identity_rejected",
            f"family scaled endpoint k={k_scale} did not reject",
        )
        require(scaled_outcome.atoms is not None, "scaled endpoint lost its finite atoms")
        require_bits(
            scaled_outcome.atoms[3],
            0x7FE8_0000_0000_0000,
            f"scaled endpoint synergy k={k_scale}",
        )
        require_bits(
            exact_sum_bits(scaled_outcome.atoms),
            POSITIVE_INFINITY_BITS,
            f"scaled endpoint reconstruction k={k_scale}",
        )
        observed += 1
    require(observed == EXPECTED_FAMILY_CASES, "scale-family cardinality changed")

    times_sixteen = family_member(4)
    require(times_sixteen[1] == 0x7F8F_FFFF_FFFF_FFFE, "k=4 I2 bits changed")
    require(times_sixteen[2] == 0x7FAF_FFFF_FFFF_FFFF, "k=4 J bits changed")
    factor = (0x3FF + 4) << 52
    require_bits(factor, 0x4030_0000_0000_0000, "k=4 exact times-sixteen factor")


def check_overflow_controls() -> None:
    exact_synergy_overflow = (
        0xFC80_0000_0000_0000,
        0xFC80_0000_0000_0000,
        MAXIMUM_FINITE_BITS,
        0x7C80_0000_0000_0000,
    )
    require(
        modeled_constructor(*exact_synergy_overflow).status == "atom_nonfinite",
        "exact candidate-synergy overflow did not reject at the atom boundary",
    )

    intermediate_overflow = (
        SIGN_MASK | MAXIMUM_FINITE_BITS,
        MAXIMUM_FINITE_BITS,
        MAXIMUM_FINITE_BITS,
        0,
    )
    accepted = modeled_constructor(*intermediate_overflow)
    require(
        accepted.status == "accepted",
        "representable exact synergy after sequential intermediate overflow was rejected",
    )
    require(accepted.atoms is not None, "intermediate-overflow witness has no atoms")
    require(
        accepted.atoms
        == (0, SIGN_MASK | MAXIMUM_FINITE_BITS, MAXIMUM_FINITE_BITS, MAXIMUM_FINITE_BITS),
        "intermediate-overflow accepted atoms changed",
    )


def check_conditioning_branches() -> None:
    all_zero = modeled_conditioning(0, (0, SIGN_MASK))
    require(
        all_zero == ConditioningOutcome("all_terms_zero", 0, None, None),
        "all-terms-zero conditioning branch changed",
    )

    exact_cancellation = modeled_conditioning(
        0,
        (0x3FF0_0000_0000_0000, 0xBFF0_0000_0000_0000),
    )
    require(
        exact_cancellation
        == ConditioningOutcome(
            "exact_cancellation", 0x4000_0000_0000_0000, 0, None
        ),
        "exact-cancellation conditioning branch changed",
    )

    finite = modeled_conditioning(
        0x3FE0_0000_0000_0000,
        (0x3FF0_0000_0000_0000, 0xBFE0_0000_0000_0000),
    )
    require(finite.status == "finite", "finite conditioning status changed")
    require_bits(finite.absolute_sum, 0x3FF8_0000_0000_0000, "finite absolute sum")
    require_bits(
        finite.retained_fraction or 0,
        0x3FD5_5555_5555_5555,
        "finite retained",
    )
    require_bits(
        finite.amplification_factor or 0,
        0x4008_0000_0000_0000,
        "finite amplification",
    )

    amplification_overflow = modeled_conditioning(
        1,
        (0x3FF0_0000_0000_0000,),
    )
    require(
        amplification_overflow
        == ConditioningOutcome(
            "amplification_exceeds_binary64",
            0x3FF0_0000_0000_0000,
            1,
            None,
        ),
        "amplification-overflow conditioning branch changed",
    )

    absolute_sum_overflow = modeled_conditioning(
        0x3FF0_0000_0000_0000,
        (MAXIMUM_FINITE_BITS, MAXIMUM_FINITE_BITS),
    )
    require(
        absolute_sum_overflow
        == ConditioningOutcome(
            "absolute_sum_nonfinite", POSITIVE_INFINITY_BITS, None, None
        ),
        "nonfinite-absolute-sum conditioning rejection changed",
    )


def run_exact_model() -> None:
    check_rounding_primitives()
    check_identity_erasure_directions()
    check_direct_compensation_15_49()
    check_candidate_exact_vs_neumaier()
    check_guard_left_association_5_155()
    check_guard_neumaier_overflow_trace()
    check_signed_zero_tuples()
    check_guard_boundaries()
    check_false_sixteen_joint_bound()
    check_scale_family()
    check_overflow_controls()
    check_conditioning_branches()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_regular_file(path: Path, label: str) -> None:
    require(path.is_file() and not path.is_symlink(), f"{label} is not a regular file: {path}")


def check_source(repo_root: Path) -> None:
    require(repo_root.is_dir() and not repo_root.is_symlink(), "repository root is not a real directory")
    for relative, expected_sha256 in SOURCE_SHA256.items():
        path = repo_root / relative
        require_regular_file(path, relative)
        actual_sha256 = sha256_file(path)
        require(
            actual_sha256 == expected_sha256,
            f"source digest mismatch for {relative}: expected {expected_sha256}, got {actual_sha256}",
        )

    pid2_source = (repo_root / "crates/pid-core/src/pid2.rs").read_text(encoding="utf-8")
    exact_source = (repo_root / "crates/pid-core/src/exact_binary64.rs").read_text(encoding="utf-8")
    integration_source = (repo_root / "crates/pid-core/tests/pid2.rs").read_text(encoding="utf-8")
    exp0_source = (repo_root / "crates/pid-core/src/bin/exp0.rs").read_text(encoding="utf-8")

    production_start = pid2_source.index("impl Pid2Result {")
    production_end = pid2_source.index("#[cfg(test)]", production_start)
    production_constructor = pid2_source[production_start:production_end]
    for marker in (
        "const PID2_RECONSTRUCTION_MAX_ORDERED_POSITIONS: u64 = 32;",
        "let syn = exact_binary64_sum([est.mi_s1s2_t, -est.mi_s1_t, -est.mi_s2_t, red]);",
        "fn identity_matches<const N: usize>(expected: f64, terms: [f64; N]) -> bool",
        "<= PID2_RECONSTRUCTION_MAX_ORDERED_POSITIONS",
    ):
        require(pid2_source.count(marker) == 1, f"PID2 production marker changed: {marker}")
    require(
        "compensated_sum" not in production_constructor,
        "PID2 checked-constructor block unexpectedly reaches compensated_sum",
    )
    for marker in (
        "pub(crate) fn exact_binary64_sum<const N: usize>(terms: [f64; N]) -> f64",
        "Exact cancellation, including a collection containing only signed zeros, is canonicalized to",
        "round-to-nearest with ties to",
    ):
        require(marker in exact_source, f"exact-binary64 marker changed: {marker}")
    for test_name in PID2_UNIT_TESTS:
        require(pid2_source.count(f"fn {test_name}()") == 1, f"missing PID2 unit test {test_name}")
    for test_name in PID2_INTEGRATION_REQUIRED:
        require(
            integration_source.count(f"fn {test_name}()") == 1,
            f"missing PID2 integration test {test_name}",
        )
    for test_name in EXP0_REQUIRED:
        require(exp0_source.count(f"fn {test_name}()") == 1, f"missing exp0 test {test_name}")
    require(
        "Err(PidError::NumericalInstability { .. }) => Ok(ScientificOutcome::Abstained"
        in exp0_source,
        "exp0 numerical-instability abstention arm changed",
    )
    require("Err(error) => Err(error)," in exp0_source, "exp0 unexpected-error propagation changed")


def run_cargo_test(repo_root: Path, command: tuple[str, ...], label: str) -> str:
    cargo = shutil.which("cargo")
    require(cargo is not None, "cargo executable was not found on PATH")
    try:
        process = subprocess.run(
            (cargo, *command),
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AssuranceError(f"{label} could not execute: {error}") from error
    captured_size = len(process.stdout.encode()) + len(process.stderr.encode())
    require(captured_size <= MAX_CAPTURE_BYTES, f"{label} output exceeded the bounded capture")
    require(
        process.returncode == 0,
        f"{label} failed: exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    return process.stdout


def require_test_output(
    stdout: str,
    expected_count: int,
    required_names: tuple[str, ...],
    label: str,
) -> None:
    require(stdout.count(f"running {expected_count} tests\n") == 1, f"{label} test count changed")
    summary = re.compile(
        rf"test result: ok\. {expected_count} passed; 0 failed; 0 ignored; 0 measured; "
        r"[0-9]+ filtered out; finished in [^\n]+\n"
    )
    require(len(summary.findall(stdout)) == 1, f"{label} exact success summary changed")
    for test_name in required_names:
        require(
            stdout.count(f"test {test_name} ... ok\n") == 1
            or stdout.count(f"test pid2::tests::{test_name} ... ok\n") == 1
            or stdout.count(f"test tests::{test_name} ... ok\n") == 1,
            f"{label} did not execute {test_name} exactly once",
        )


def check_compiled(repo_root: Path) -> None:
    for profile in COMPILED_PROFILES:
        release = ("--release",) if profile == "release" else ()
        unit_stdout = run_cargo_test(
            repo_root,
            (
                "test",
                "--locked",
                *release,
                "-p",
                "pid-core",
                "--features",
                "experimental-continuous",
                "--lib",
                "pid2::tests::",
                "--",
                "--test-threads=1",
            ),
            f"PID2 unit {profile}",
        )
        require_test_output(
            unit_stdout,
            EXPECTED_PID2_UNIT_COUNT,
            PID2_UNIT_TESTS,
            f"PID2 unit {profile}",
        )

        integration_stdout = run_cargo_test(
            repo_root,
            (
                "test",
                "--locked",
                *release,
                "-p",
                "pid-core",
                "--all-features",
                "--test",
                "pid2",
                "--",
                "--test-threads=1",
            ),
            f"PID2 integration {profile}",
        )
        require_test_output(
            integration_stdout,
            EXPECTED_PID2_INTEGRATION_COUNT,
            PID2_INTEGRATION_REQUIRED,
            f"PID2 integration {profile}",
        )

        exp0_stdout = run_cargo_test(
            repo_root,
            (
                "test",
                "--locked",
                *release,
                "-p",
                "pid-core",
                "--all-features",
                "--bin",
                "exp0",
                "--",
                "--test-threads=1",
            ),
            f"exp0 {profile}",
        )
        require_test_output(
            exp0_stdout,
            EXPECTED_EXP0_COUNT,
            EXP0_REQUIRED,
            f"exp0 {profile}",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("model", "model-source", "full"),
        default="full",
        help="model only; model plus exact source custody; or model, source, and compiled tests",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root used only by model-source and full scopes",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        run_exact_model()
        if arguments.scope in {"model-source", "full"}:
            check_source(arguments.repo_root)
        if arguments.scope == "full":
            check_compiled(arguments.repo_root)
    except (AssuranceError, OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    outputs = {
        "model": MODEL_OUTPUT,
        "model-source": MODEL_SOURCE_OUTPUT,
        "full": FULL_OUTPUT,
    }
    print(outputs[arguments.scope])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
