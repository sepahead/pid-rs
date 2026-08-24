#!/usr/bin/env python3
"""Generate an independent exact oracle for finite-binary64 sums.

The oracle decodes input bit patterns to ``Fraction`` values and rounds their exact rational sum
to IEEE-754 binary64 using integer quotient/remainder arithmetic.  It never converts an expected
value through a Python ``float``.  A second common-``2^-1074`` integer representation cross-checks
the exact rational sum, but is not used by the rounding routine.

The corpus keeps the dense four-term suite and adds bounded variable-arity cases through 65 terms
for empty, unary, long-carry, overflow, subnormal, and extreme-cancellation paths.  It is
implementation-conformance evidence, not a proof of the Rust fixed-limb implementation, a
universal runtime checker, or an estimator-accuracy claim.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "crates/pid-core/tests/fixtures/exact_binary64_sum_oracle.json"
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SNAPSHOT = (
    ROOT
    / "crates/pid-core/tests/fixtures/generate-exact-binary64-sum-oracle.py.snapshot"
)
SCHEMA = "pid-rs/exact-binary64-sum-oracle"
SCHEMA_REVISION = 2
CORE_ARITY = 4
TESTED_ARITIES = (0, 1, 2, 3, 4, 5, 63, 64, 65)
DETERMINISTIC_CASES = 512

U64_MASK = (1 << 64) - 1
SIGN_MASK = 1 << 63
EXPONENT_MASK = 0x7FF << 52
FRACTION_MASK = (1 << 52) - 1
POSITIVE_INFINITY_BITS = 0x7FF0_0000_0000_0000

MINIMUM_SUBNORMAL = 0x0000_0000_0000_0001
MAXIMUM_SUBNORMAL = 0x000F_FFFF_FFFF_FFFF
MINIMUM_NORMAL = 0x0010_0000_0000_0000
ONE = 0x3FF0_0000_0000_0000
NEXT_UP_ONE = ONE + 1
NEXT_DOWN_TWO = 0x3FFF_FFFF_FFFF_FFFF
TWO = 0x4000_0000_0000_0000
MAXIMUM_FINITE = 0x7FEF_FFFF_FFFF_FFFF
POWER_NEGATIVE_53 = (1023 - 53) << 52
POWER_NEGATIVE_52 = (1023 - 52) << 52
POWER_970 = (1023 + 970) << 52


class OracleError(RuntimeError):
    """The reference calculation or committed corpus is internally inconsistent."""


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


def bits_text(bits: int) -> str:
    if not 0 <= bits <= U64_MASK:
        raise OracleError(f"binary64 bits out of range: {bits}")
    return f"0x{bits:016x}"


def negate_bits(bits: int) -> int:
    return bits ^ SIGN_MASK


def require_finite_bits(bits: int) -> None:
    if (bits & EXPONENT_MASK) == EXPONENT_MASK:
        raise OracleError(f"non-finite input bits: {bits_text(bits)}")


def finite_bits_to_fraction(bits: int) -> Fraction:
    """Decode one finite binary64 bit pattern without using host floating point."""

    require_finite_bits(bits)
    exponent_bits = (bits >> 52) & 0x7FF
    fraction_bits = bits & FRACTION_MASK
    sign = -1 if bits & SIGN_MASK else 1
    if exponent_bits == 0:
        return Fraction(sign * fraction_bits, 1 << 1074)

    significand = (1 << 52) | fraction_bits
    exponent = exponent_bits - 1023 - 52
    if exponent >= 0:
        return Fraction(sign * (significand << exponent), 1)
    return Fraction(sign * significand, 1 << -exponent)


def finite_bits_to_grid_integer(bits: int) -> int:
    """Represent one finite input as an integer multiple of ``2^-1074``."""

    require_finite_bits(bits)
    exponent_bits = (bits >> 52) & 0x7FF
    fraction_bits = bits & FRACTION_MASK
    if exponent_bits == 0:
        magnitude = fraction_bits
    else:
        magnitude = ((1 << 52) | fraction_bits) << (exponent_bits - 1)
    return -magnitude if bits & SIGN_MASK else magnitude


def floor_log2_fraction(value: Fraction) -> int:
    """Return ``floor(log2(value))`` for a strictly positive exact rational."""

    if value <= 0:
        raise OracleError("floor_log2_fraction requires a positive value")
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
    """Round a nonnegative rational to nearest integer, ties to even."""

    if numerator < 0 or denominator <= 0:
        raise OracleError(
            "round_ratio_to_integer requires a nonnegative positive-denominator ratio"
        )
    quotient, remainder = divmod(numerator, denominator)
    comparison = 2 * remainder - denominator
    if comparison > 0 or (comparison == 0 and quotient & 1):
        quotient += 1
    return quotient


def scaled_round_to_integer(value: Fraction, binary_power: int) -> int:
    """Round ``value / 2^binary_power`` to nearest integer, ties to even."""

    numerator = value.numerator
    denominator = value.denominator
    if binary_power >= 0:
        denominator <<= binary_power
    else:
        numerator <<= -binary_power
    return round_ratio_to_integer(numerator, denominator)


def round_fraction_to_binary64_bits(value: Fraction) -> int:
    """Correctly round an exact rational to binary64 bits without host floating point."""

    if value == 0:
        return 0
    sign = SIGN_MASK if value < 0 else 0
    magnitude = abs(value)
    minimum_normal = Fraction(1, 1 << 1022)

    if magnitude < minimum_normal:
        subnormal_significand = scaled_round_to_integer(magnitude, -1074)
        if subnormal_significand > 1 << 52:
            raise OracleError("subnormal rounding exceeded the minimum-normal boundary")
        if subnormal_significand == 1 << 52:
            return sign | MINIMUM_NORMAL
        return sign | subnormal_significand

    exponent = floor_log2_fraction(magnitude)
    if exponent > 1023:
        return sign | POSITIVE_INFINITY_BITS
    significand = scaled_round_to_integer(magnitude, exponent - 52)
    if significand == 1 << 53:
        significand >>= 1
        exponent += 1
    if exponent > 1023:
        return sign | POSITIVE_INFINITY_BITS
    if not 1 << 52 <= significand < 1 << 53:
        raise OracleError("normal significand left the 53-bit range")
    exponent_bits = exponent + 1023
    return sign | (exponent_bits << 52) | (significand - (1 << 52))


def exact_sum(inputs: tuple[int, ...]) -> Fraction:
    if len(inputs) not in TESTED_ARITIES:
        raise OracleError(f"unsupported fixture arity {len(inputs)}")
    rational = sum((finite_bits_to_fraction(bits) for bits in inputs), Fraction())
    grid_integer = sum(finite_bits_to_grid_integer(bits) for bits in inputs)
    if rational != Fraction(grid_integer, 1 << 1074):
        raise OracleError("Fraction and common-grid exact sums disagree")
    return rational


def named_inputs() -> list[tuple[str, tuple[int, int, int, int], int]]:
    """Return explicit boundary cases and their independently frozen expected bits."""

    return [
        (
            "exact-cancellation-positive-zero",
            (MINIMUM_SUBNORMAL, negate_bits(MINIMUM_SUBNORMAL), 0, 0),
            0,
        ),
        ("signed-zero-inputs-return-positive-zero", (SIGN_MASK, 0, SIGN_MASK, 0), 0),
        ("minimum-subnormal-addition", (MINIMUM_SUBNORMAL, MINIMUM_SUBNORMAL, 0, 0), 2),
        ("halfway-even-down-at-one", (ONE, POWER_NEGATIVE_53, 0, 0), ONE),
        ("halfway-even-up-at-one", (NEXT_UP_ONE, POWER_NEGATIVE_53, 0, 0), ONE + 2),
        (
            "halfway-plus-sticky-at-one",
            (ONE, POWER_NEGATIVE_53, MINIMUM_SUBNORMAL, 0),
            NEXT_UP_ONE,
        ),
        (
            "negative-halfway-plus-sticky-at-one",
            (
                negate_bits(ONE),
                negate_bits(POWER_NEGATIVE_53),
                negate_bits(MINIMUM_SUBNORMAL),
                0,
            ),
            negate_bits(NEXT_UP_ONE),
        ),
        ("rounding-carry-to-two", (NEXT_DOWN_TWO, POWER_NEGATIVE_53, 0, 0), TWO),
        ("exact-carry-to-two", (NEXT_DOWN_TWO, POWER_NEGATIVE_52, 0, 0), TWO),
        (
            "maximum-subnormal-plus-minimum-subnormal",
            (MAXIMUM_SUBNORMAL, MINIMUM_SUBNORMAL, 0, 0),
            MINIMUM_NORMAL,
        ),
        (
            "negative-maximum-subnormal-plus-minimum-subnormal",
            (negate_bits(MAXIMUM_SUBNORMAL), negate_bits(MINIMUM_SUBNORMAL), 0, 0),
            negate_bits(MINIMUM_NORMAL),
        ),
        (
            "minimum-normal-minus-minimum-subnormal",
            (MINIMUM_NORMAL, negate_bits(MINIMUM_SUBNORMAL), 0, 0),
            MAXIMUM_SUBNORMAL,
        ),
        (
            "minimum-normal-minus-maximum-subnormal",
            (MINIMUM_NORMAL, negate_bits(MAXIMUM_SUBNORMAL), 0, 0),
            MINIMUM_SUBNORMAL,
        ),
        (
            "cross-limb-carry",
            (0x00CF_FFFF_FFFF_FFFF, 0x0000_0000_0000_0800, 0, 0),
            0x00D0_0000_0000_0000,
        ),
        (
            "negative-cross-limb-carry",
            (
                negate_bits(0x00CF_FFFF_FFFF_FFFF),
                negate_bits(0x0000_0000_0000_0800),
                0,
                0,
            ),
            negate_bits(0x00D0_0000_0000_0000),
        ),
        (
            "cross-limb-borrow",
            (0x00D0_0000_0000_0000, negate_bits(0x0000_0000_0000_0800), 0, 0),
            0x00CF_FFFF_FFFF_FFFF,
        ),
        (
            "overflow-midpoint-minus-sticky",
            (MAXIMUM_FINITE, POWER_970, negate_bits(MINIMUM_SUBNORMAL), 0),
            MAXIMUM_FINITE,
        ),
        (
            "overflow-midpoint-ties-to-infinity",
            (MAXIMUM_FINITE, POWER_970, 0, 0),
            POSITIVE_INFINITY_BITS,
        ),
        (
            "overflow-midpoint-plus-sticky",
            (MAXIMUM_FINITE, POWER_970, MINIMUM_SUBNORMAL, 0),
            POSITIVE_INFINITY_BITS,
        ),
        (
            "negative-overflow-midpoint-minus-sticky",
            (negate_bits(MAXIMUM_FINITE), negate_bits(POWER_970), MINIMUM_SUBNORMAL, 0),
            negate_bits(MAXIMUM_FINITE),
        ),
        (
            "negative-overflow-midpoint-ties-to-infinity",
            (negate_bits(MAXIMUM_FINITE), negate_bits(POWER_970), 0, 0),
            negate_bits(POSITIVE_INFINITY_BITS),
        ),
        (
            "maximum-cancellation-with-tiny-tail",
            (MAXIMUM_FINITE, negate_bits(MAXIMUM_FINITE), ONE, MINIMUM_SUBNORMAL),
            ONE,
        ),
        (
            "four-positive-maximums-overflow",
            (MAXIMUM_FINITE, MAXIMUM_FINITE, MAXIMUM_FINITE, MAXIMUM_FINITE),
            POSITIVE_INFINITY_BITS,
        ),
        (
            "four-negative-maximums-overflow",
            (
                negate_bits(MAXIMUM_FINITE),
                negate_bits(MAXIMUM_FINITE),
                negate_bits(MAXIMUM_FINITE),
                negate_bits(MAXIMUM_FINITE),
            ),
            negate_bits(POSITIVE_INFINITY_BITS),
        ),
    ]


def variable_arity_inputs() -> list[tuple[str, tuple[int, ...], int]]:
    """Return frozen variable-length boundary, carry, and cancellation cases."""

    negative_minimum_subnormal = negate_bits(MINIMUM_SUBNORMAL)
    negative_maximum_finite = negate_bits(MAXIMUM_FINITE)
    return [
        ("arity-000-empty", (), 0),
        ("arity-001-maximum-finite", (MAXIMUM_FINITE,), MAXIMUM_FINITE),
        ("arity-001-negative-zero-canonicalizes", (SIGN_MASK,), 0),
        ("arity-001-minimum-subnormal", (MINIMUM_SUBNORMAL,), MINIMUM_SUBNORMAL),
        (
            "arity-002-maximum-cancellation",
            (MAXIMUM_FINITE, negative_maximum_finite),
            0,
        ),
        (
            "arity-002-positive-overflow",
            (MAXIMUM_FINITE, MAXIMUM_FINITE),
            POSITIVE_INFINITY_BITS,
        ),
        (
            "arity-002-subnormal-cancellation",
            (MINIMUM_SUBNORMAL, negative_minimum_subnormal),
            0,
        ),
        (
            "arity-003-extreme-cancellation-positive-tail",
            (MAXIMUM_FINITE, negative_maximum_finite, MINIMUM_SUBNORMAL),
            MINIMUM_SUBNORMAL,
        ),
        (
            "arity-003-extreme-cancellation-negative-tail",
            (negative_maximum_finite, MAXIMUM_FINITE, negative_minimum_subnormal),
            negative_minimum_subnormal,
        ),
        (
            "arity-003-halfway-plus-subnormal-sticky",
            (ONE, POWER_NEGATIVE_53, MINIMUM_SUBNORMAL),
            NEXT_UP_ONE,
        ),
        (
            "arity-005-halfway-plus-sticky-and-zeros",
            (ONE, POWER_NEGATIVE_53, MINIMUM_SUBNORMAL, 0, SIGN_MASK),
            NEXT_UP_ONE,
        ),
        (
            "arity-005-repeated-maximum-overflow",
            (MAXIMUM_FINITE,) * 5,
            POSITIVE_INFINITY_BITS,
        ),
        (
            "arity-063-repeated-minimum-subnormal",
            (MINIMUM_SUBNORMAL,) * 63,
            0x0000_0000_0000_003F,
        ),
        (
            "arity-063-repeated-maximum-overflow",
            (MAXIMUM_FINITE,) * 63,
            POSITIVE_INFINITY_BITS,
        ),
        (
            "arity-063-extreme-cancellation-positive-tail",
            (MAXIMUM_FINITE,) * 31
            + (negative_maximum_finite,) * 31
            + (MINIMUM_SUBNORMAL,),
            MINIMUM_SUBNORMAL,
        ),
        (
            "arity-063-repeated-full-significand-carry",
            (NEXT_DOWN_TWO,) * 63,
            0x405F_7FFF_FFFF_FFFF,
        ),
        (
            "arity-064-repeated-minimum-subnormal",
            (MINIMUM_SUBNORMAL,) * 64,
            0x0000_0000_0000_0040,
        ),
        (
            "arity-064-repeated-maximum-overflow",
            (MAXIMUM_FINITE,) * 64,
            POSITIVE_INFINITY_BITS,
        ),
        (
            "arity-064-extreme-exact-cancellation",
            (MAXIMUM_FINITE,) * 32 + (negative_maximum_finite,) * 32,
            0,
        ),
        (
            "arity-064-repeated-full-significand-carry",
            (NEXT_DOWN_TWO,) * 64,
            0x405F_FFFF_FFFF_FFFF,
        ),
        (
            "arity-065-repeated-minimum-subnormal",
            (MINIMUM_SUBNORMAL,) * 65,
            0x0000_0000_0000_0041,
        ),
        (
            "arity-065-repeated-maximum-overflow",
            (MAXIMUM_FINITE,) * 65,
            POSITIVE_INFINITY_BITS,
        ),
        (
            "arity-065-repeated-negative-maximum-overflow",
            (negative_maximum_finite,) * 65,
            negate_bits(POSITIVE_INFINITY_BITS),
        ),
        (
            "arity-065-extreme-cancellation-positive-tail",
            (MAXIMUM_FINITE,) * 32
            + (negative_maximum_finite,) * 32
            + (MINIMUM_SUBNORMAL,),
            MINIMUM_SUBNORMAL,
        ),
        (
            "arity-065-repeated-full-significand-carry",
            (NEXT_DOWN_TWO,) * 65,
            0x4060_3FFF_FFFF_FFFF,
        ),
    ]


def xorshift64(state: int) -> int:
    state ^= (state << 13) & U64_MASK
    state ^= state >> 7
    state ^= (state << 17) & U64_MASK
    return state & U64_MASK


def sanitize_finite(bits: int) -> int:
    if (bits & EXPONENT_MASK) == EXPONENT_MASK:
        bits = (bits & ~EXPONENT_MASK) | (0x7FE << 52)
    require_finite_bits(bits)
    return bits


def deterministic_inputs() -> list[tuple[int, int, int, int]]:
    """Build a reproducible, exponent-diverse four-term adversarial corpus."""

    state = 0xD1B5_4A32_D192_ED03
    cases: list[tuple[int, int, int, int]] = []
    for index in range(DETERMINISTIC_CASES):
        raw: list[int] = []
        for _ in range(4):
            state = xorshift64(state)
            raw.append(sanitize_finite(state))

        mode = index % 8
        if mode == 0:
            inputs = tuple(raw)
        elif mode == 1:
            inputs = (raw[0], negate_bits(raw[0]), raw[1], raw[2])
        elif mode == 2:
            base = raw[0] & ~SIGN_MASK
            inputs = (base, base, base, base)
        elif mode == 3:
            inputs = (raw[0], raw[1], negate_bits(raw[1]), negate_bits(raw[0]))
        elif mode == 4:
            inputs = (MAXIMUM_FINITE, negate_bits(MAXIMUM_FINITE), raw[0], raw[1])
        elif mode == 5:
            subnormal = tuple((bits & (SIGN_MASK | FRACTION_MASK)) for bits in raw)
            inputs = subnormal
        elif mode == 6:
            exponent = 1 + (raw[0] % 0x7FE)
            power = (raw[0] & SIGN_MASK) | (exponent << 52)
            predecessor = power - 1 if power & ~SIGN_MASK else power
            inputs = (power, predecessor, negate_bits(raw[1]), raw[2])
        else:
            inputs = (raw[0], negate_bits(raw[1]), raw[2], negate_bits(raw[3]))
        cases.append(tuple(sanitize_finite(bits) for bits in inputs))
    return cases


def build_case(identifier: str, kind: str, inputs: tuple[int, ...]) -> dict[str, Any]:
    value = exact_sum(inputs)
    return {
        "expected_bits": bits_text(round_fraction_to_binary64_bits(value)),
        "id": identifier,
        "inputs_bits": [bits_text(bits) for bits in inputs],
        "kind": kind,
    }


def build_corpus() -> dict[str, Any]:
    named = named_inputs()
    variable_arity = variable_arity_inputs()
    deterministic = deterministic_inputs()
    cases = [
        build_case(identifier, "named-boundary", inputs)
        for identifier, inputs, _ in named
    ]
    cases.extend(
        build_case(identifier, "variable-arity-boundary", inputs)
        for identifier, inputs, _ in variable_arity
    )
    cases.extend(
        build_case(f"deterministic-{index:04d}", "deterministic-adversarial", inputs)
        for index, inputs in enumerate(deterministic)
    )
    return {
        "arithmetic": {
            "input_domain": "zero or more finite IEEE-754 binary64 bit patterns at a declared tested arity",
            "rounding": "round-to-nearest, ties-to-even",
            "zero_sign": "positive on exact cancellation",
        },
        "bounds": {
            "core_arity": CORE_ARITY,
            "deterministic_case_count": len(deterministic),
            "named_case_count": len(named),
            "tested_arities": list(TESTED_ARITIES),
            "total_case_count": len(cases),
            "variable_arity_case_count": len(variable_arity),
        },
        "cases": cases,
        "generator": {
            "imports_pid_rs": False,
            "path": "scripts/generate-exact-binary64-sum-oracle.py",
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "third_party_dependencies": [],
        },
        "limitations": [
            "the finite corpus does not prove the universal fixed-limb implementation claim",
            "the expected path uses exact Fraction and integer arithmetic, not host floating point",
            "the oracle checks represented-input summation, not upstream estimator accuracy",
            "implementation-path diversity is not independent human review",
        ],
        "schema": SCHEMA,
        "schema_revision": SCHEMA_REVISION,
    }


def self_test(corpus: dict[str, Any]) -> None:
    expected_named = {
        identifier: expected for identifier, _, expected in named_inputs()
    }
    expected_variable = {
        identifier: expected for identifier, _, expected in variable_arity_inputs()
    }
    if corpus["bounds"] != {
        "core_arity": CORE_ARITY,
        "deterministic_case_count": DETERMINISTIC_CASES,
        "named_case_count": len(expected_named),
        "tested_arities": list(TESTED_ARITIES),
        "total_case_count": DETERMINISTIC_CASES
        + len(expected_named)
        + len(expected_variable),
        "variable_arity_case_count": len(expected_variable),
    }:
        raise OracleError("corpus bounds changed")

    case_by_id = {case["id"]: case for case in corpus["cases"]}
    if len(case_by_id) != len(corpus["cases"]):
        raise OracleError("case identifiers are not unique")
    for identifier, expected in (expected_named | expected_variable).items():
        observed = int(case_by_id[identifier]["expected_bits"], 16)
        if observed != expected:
            raise OracleError(
                f"named case {identifier} produced {bits_text(observed)}, "
                f"expected {bits_text(expected)}"
            )

    for case in corpus["cases"]:
        inputs = tuple(int(bits, 16) for bits in case["inputs_bits"])
        expected = int(case["expected_bits"], 16)
        if round_fraction_to_binary64_bits(exact_sum(inputs)) != expected:
            raise OracleError(f"case {case['id']} failed exact replay")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the committed corpus, SHA-256 sidecar, and exact generator snapshot",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus = build_corpus()
    self_test(corpus)
    raw = canonical_json_bytes(corpus)
    digest = hashlib.sha256(raw).hexdigest()
    sidecar = f"{digest}  {OUTPUT.name}\n"

    if args.write:
        OUTPUT.write_bytes(raw)
        SIDECAR.write_text(sidecar, encoding="utf-8", newline="")
        SNAPSHOT.write_bytes(Path(__file__).read_bytes())
        print(
            f"wrote {len(corpus['cases'])} cases, sidecar, and generator snapshot; "
            f"SHA-256 {digest}"
        )
        return 0

    try:
        committed = OUTPUT.read_bytes()
        committed_sidecar = SIDECAR.read_text(encoding="utf-8")
        committed_snapshot = SNAPSHOT.read_bytes()
    except OSError as error:
        print(f"exact binary64 sum oracle error: {error}")
        return 1
    if committed != raw:
        print(
            "exact binary64 sum oracle error: committed corpus is stale; rerun with --write"
        )
        return 1
    if committed_sidecar != sidecar:
        print("exact binary64 sum oracle error: committed SHA-256 sidecar is stale")
        return 1
    if committed_snapshot != Path(__file__).read_bytes():
        print(
            "exact binary64 sum oracle error: committed generator snapshot is stale; "
            "rerun with --write"
        )
        return 1
    print(f"OK: {len(corpus['cases'])} exact binary64 sum cases match SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
