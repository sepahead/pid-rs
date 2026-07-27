#!/usr/bin/env python3
"""Independently enclose the frozen KSG integer-harmonic arithmetic corpus.

This standard-library-only checker does not import pid-rs, the fixture generator, or another
checker.  It reconstructs the schema-2 row order, builds 160-digit directed-rounding bounds for
every harmonic prefix through H_999999, and proves that both endpoints of every resulting interval
round to the same 80-digit ROUND_HALF_EVEN Decimal.

The Python binary64 audit separately reproduces the selected Neumaier-prefix/sorted-range
expression.  Its rigorous error intervals are against the enclosed exact harmonic rational.  The
older 8-epsilon observation instead compares with the fixture Decimal after conversion to
binary64; these are deliberately different reference metrics.

Shared cuts are explicit: both routes use the digest-bound frozen rows and the exact identity
H_(k-1) + H_(n-1) - H_(nx) - H_(ny).  Decimal directed rounding and the host's Python binary64
operations are trusted execution assumptions.  Success is finite-corpus evidence only, not a
universal error theorem, an authenticity or cross-platform identity claim, a Rust-source or
compiled-binary conformance claim, a neighbor-count proof, an estimator validation result, a
support-model result, a PID theorem, or an application-validity claim.
"""

from __future__ import annotations

import argparse
from decimal import (
    Context,
    Decimal,
    DecimalException,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
)
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import sys
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RELATIVE_PATH = (
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
)
SIDECAR_RELATIVE_PATH = FIXTURE_RELATIVE_PATH + ".sha256"
GENERATOR_RELATIVE_PATH = "scripts/generate-ksg-local-arithmetic-oracle.py"

FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
FIXTURE_SCHEMA_REVISION = 2
EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_GENERATOR_SHA256 = (
    "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
)
EXPECTED_SIDECAR_TEXT = (
    EXPECTED_FIXTURE_SHA256 + "  ksg_local_arithmetic_oracle.json\n"
)

EXHAUSTIVE_MAX_SAMPLES = 16
STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)
EXHAUSTIVE_ROW_COUNT = 6_920
STRESS_ROW_COUNT = 1_278
ROW_COUNT = 8_198
EXHAUSTIVE_ENDPOINT_COUNT = 240
STRESS_ENDPOINT_COUNT = 114
ENDPOINT_COUNT = 354
MAXIMUM_RECIPROCAL_SUMMAND_INDEX = 999_999

ENCLOSURE_PRECISION = 160
REFERENCE_ROUNDING_PRECISION = 80
LOWER_ROUNDING = ROUND_FLOOR
UPPER_ROUNDING = ROUND_CEILING
REFERENCE_ROUNDING = ROUND_HALF_EVEN
EXPECTED_EXACT_ROUNDED_VECTOR_SHA256 = (
    "1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747"
)

EXPECTED_STORED_TEXT_MISMATCH_COUNT = 6_509
EXPECTED_STORED_NUMERIC_MISMATCH_COUNT = 5_934
EXPECTED_STORED_BINARY64_MISMATCH_COUNT = 0
EXPECTED_STORED_MAX_DISCREPANCY = Fraction(818, 10**79)
EXPECTED_STORED_MAX_DISCREPANCY_TEXT = "8.18E-77"
EXPECTED_STORED_MAX_DISCREPANCY_ROW_INDEX = 7_952
EXPECTED_STORED_MAX_DISCREPANCY_ROW = (65_536, 64, 32_799, 32_799)
EXPECTED_STORED_MAX_DISCREPANCY_TIES = 1

EXPECTED_EXACT_ERROR_MAX_ROW_INDEX = 7_673
EXPECTED_EXACT_ERROR_MAX_ROW = (4_096, 4, 2_049, 2_049)
EXPECTED_EXACT_ERROR_MAX_TIES = 1
EXPECTED_EXACT_ERROR_MAX_ACTUAL_HEX = "-0x1.6b52fe6a01407p+2"
EXPECTED_EXACT_ERROR_LOWER = Decimal(
    "2.167446422088005150275671429474969824136427179560898493282553682662172266784"
    "817744579758400790213907338588461575762025354130852141897942153682690E-15"
)
EXPECTED_EXACT_ERROR_UPPER = Decimal(
    "2.167446422088005150275671429474969824136427179560898493282553682662172266784"
    "817744579758400790213907338588461575762025354130852141897942153690778E-15"
)
EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT = "9.761311"
EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER = 32

EXPECTED_ROUNDED_REFERENCE_MAX_EPSILON_MULTIPLIER = 8
EXPECTED_ROUNDED_REFERENCE_MAX_TIES = 40
EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW_INDEX = 7_598
EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW = (4_096, 1, 2_048, 2_048)
EXPECTED_SELECTED_POSITIVE_ZERO_COUNT = 354
EXPECTED_SELECTED_NEGATIVE_ZERO_COUNT = 0
EXPECTED_SELECTED_NONZERO_COUNT = 7_844

SCOPE_BOUNDARY = (
    "finite frozen 8,198-row corpus only; same-repository digest binding is an internal integrity "
    "check, not artifact authenticity; not a universal error theorem, cross-platform identity "
    "claim, Rust-source or compiled-binary conformance claim, neighbor-count proof, estimator "
    "validation result, support-model result, PID theorem, or application-validity claim"
)
EXPECTED_SCOPE_BOUNDARY_SHA256 = (
    "3d987ad05a5a65d708b2dacfd945f5800e86febb2a3ee0cc3afee092c3d53ddd"
)


class CheckError(RuntimeError):
    """The enclosure, custody, metric separation, or frozen observations failed."""


class Row(NamedTuple):
    """One independently reconstructed fixture row."""

    sample_count: int
    k: int
    x_count: int
    y_count: int


class ErrorInterval(NamedTuple):
    """Directed Decimal enclosure of one absolute binary64 error."""

    lower: Decimal
    upper: Decimal


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def exact_finite_decimal_distance(left: Decimal, right: Decimal) -> Fraction:
    """Return the exact distance between two finite Decimal values."""

    require(
        type(left) is Decimal and type(right) is Decimal,
        "exact Decimal comparator received a non-Decimal operand",
    )
    require(
        left.is_finite() and right.is_finite(),
        "exact Decimal comparator received a non-finite operand",
    )
    return abs(Fraction(left) - Fraction(right))


def check_exact_decimal_comparator() -> None:
    """Pin exact conversion, subtraction, signed-zero, and display linkage."""

    long_tail = Decimal("1." + "0" * 159 + "1")
    require(
        exact_finite_decimal_distance(long_tail, Decimal(0)) == Fraction(long_tail),
        "exact Decimal comparator rounded a long-tail witness",
    )
    require(
        exact_finite_decimal_distance(Decimal("-0"), Decimal("0")) == 0,
        "exact Decimal comparator changed signed-zero equality",
    )
    require(
        Fraction(Decimal(EXPECTED_STORED_MAX_DISCREPANCY_TEXT))
        == EXPECTED_STORED_MAX_DISCREPANCY,
        "stored-discrepancy exact fraction and presentation text diverged",
    )


def require_exact_int_field(
    mapping: dict[str, Any],
    key: str,
    expected: int,
    label: str,
) -> None:
    value = mapping.get(key)
    require(
        type(value) is int and value == expected,
        f"{label} changed or is not a JSON integer",
    )


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def reject_nonfinite_json(token: str) -> None:
    raise CheckError(f"non-finite JSON token: {token}")


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


def parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_json,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise CheckError(f"{label} is not finite UTF-8 JSON: {error}") from error
    require(isinstance(value, dict), f"{label} top level is not an object")
    require(raw == canonical_json_bytes(value), f"{label} is not canonical JSON")
    return value


def reconstruct_rows() -> tuple[list[Row], int]:
    exhaustive = [
        Row(sample_count, k, x_count, y_count)
        for sample_count in range(2, EXHAUSTIVE_MAX_SAMPLES + 1)
        for k in range(1, sample_count)
        for x_count in range(k - 1, sample_count)
        for y_count in range(k - 1, sample_count)
    ]
    stress: list[Row] = []
    for sample_count in STRESS_SAMPLE_SIZES:
        k_values = sorted(
            {
                value
                for value in (
                    1,
                    2,
                    3,
                    4,
                    8,
                    16,
                    64,
                    sample_count // 2,
                    sample_count - 1,
                )
                if 1 <= value < sample_count
            }
        )
        for k in k_values:
            count_values = sorted(
                {
                    k - 1,
                    min(k, sample_count - 1),
                    (k + sample_count - 1) // 2,
                    sample_count - 2,
                    sample_count - 1,
                }
            )
            for x_count in count_values:
                for y_count in count_values:
                    stress.append(Row(sample_count, k, x_count, y_count))

    require(len(exhaustive) == EXHAUSTIVE_ROW_COUNT, "exhaustive row count changed")
    require(len(stress) == STRESS_ROW_COUNT, "stress row count changed")
    rows = exhaustive + stress
    require(len(rows) == ROW_COUNT, "total row count changed")
    require(len(rows) == len(set(rows)), "reconstructed rows are not unique")
    return rows, len(exhaustive)


def is_endpoint(row: Row) -> bool:
    return (row.x_count, row.y_count) in (
        (row.k - 1, row.sample_count - 1),
        (row.sample_count - 1, row.k - 1),
    )


def decimal_from_fixture(text: Any, row_index: int) -> Decimal:
    require(type(text) is str, f"row {row_index}: expected_nats is not a string")
    try:
        value = Decimal(text)
    except InvalidOperation as error:
        raise CheckError(f"row {row_index}: expected_nats is not Decimal") from error
    require(value.is_finite(), f"row {row_index}: expected_nats is not finite")
    require(str(value) == text, f"row {row_index}: expected_nats is not canonical Decimal text")
    return value


def load_digest_bound_fixture(
    repo_root: Path,
) -> tuple[dict[str, Any], list[Row], list[Decimal]]:
    fixture_path = repo_root / FIXTURE_RELATIVE_PATH
    sidecar_path = repo_root / SIDECAR_RELATIVE_PATH
    generator_path = repo_root / GENERATOR_RELATIVE_PATH

    fixture_raw = fixture_path.read_bytes()
    require(
        sha256(fixture_raw) == EXPECTED_FIXTURE_SHA256,
        "fixture bytes changed from the frozen schema-2 digest",
    )
    fixture = parse_canonical_json(fixture_raw, "fixture")
    require(
        sidecar_path.read_bytes() == EXPECTED_SIDECAR_TEXT.encode("ascii"),
        "fixture SHA-256 sidecar changed",
    )
    require(
        sha256(generator_path.read_bytes()) == EXPECTED_GENERATOR_SHA256,
        "fixture generator bytes changed from the frozen digest",
    )

    require(fixture.get("schema") == FIXTURE_SCHEMA, "fixture schema changed")
    require_exact_int_field(
        fixture,
        "schema_revision",
        FIXTURE_SCHEMA_REVISION,
        "fixture schema revision",
    )
    generator = fixture.get("generator")
    require(type(generator) is dict, "fixture generator metadata is absent")
    require(generator.get("path") == GENERATOR_RELATIVE_PATH, "fixture generator path changed")
    require(
        generator.get("sha256") == EXPECTED_GENERATOR_SHA256,
        "fixture generator metadata digest changed",
    )
    require(generator.get("imports_pid_rs") is False, "fixture declares a pid-rs import")
    require(
        generator.get("third_party_dependencies") == [],
        "fixture declares a third-party generator dependency",
    )

    arithmetic = fixture.get("arithmetic")
    bounds = fixture.get("bounds")
    require(type(arithmetic) is dict, "fixture arithmetic metadata is absent")
    require(type(bounds) is dict, "fixture bounds metadata is absent")
    require_exact_int_field(
        arithmetic,
        "decimal_precision_digits",
        REFERENCE_ROUNDING_PRECISION,
        "fixture Decimal precision",
    )
    require(
        arithmetic.get("exact_identity")
        == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity changed",
    )
    require(arithmetic.get("logarithm_unit") == "nats", "fixture unit changed")
    require_exact_int_field(
        arithmetic,
        "endpoint_cancellation_exact_zero_case_count",
        ENDPOINT_COUNT,
        "fixture endpoint total",
    )
    require_exact_int_field(
        arithmetic,
        "endpoint_cancellation_exact_zero_exhaustive_case_count",
        EXHAUSTIVE_ENDPOINT_COUNT,
        "fixture exhaustive endpoint total",
    )
    require_exact_int_field(
        arithmetic,
        "endpoint_cancellation_exact_zero_stress_case_count",
        STRESS_ENDPOINT_COUNT,
        "fixture stress endpoint total",
    )
    require_exact_int_field(
        bounds,
        "exhaustive_case_count",
        EXHAUSTIVE_ROW_COUNT,
        "fixture exhaustive row count",
    )
    require_exact_int_field(
        bounds,
        "exhaustive_max_samples",
        EXHAUSTIVE_MAX_SAMPLES,
        "fixture exhaustive bound",
    )
    require_exact_int_field(
        bounds,
        "stress_case_count",
        STRESS_ROW_COUNT,
        "fixture stress row count",
    )
    stress_sample_sizes = bounds.get("stress_sample_sizes")
    require(
        type(stress_sample_sizes) is list
        and all(type(value) is int for value in stress_sample_sizes)
        and tuple(stress_sample_sizes) == STRESS_SAMPLE_SIZES,
        "fixture stress sample sizes changed or contain a non-integer",
    )

    rows, exhaustive_cut = reconstruct_rows()
    cases = fixture.get("cases")
    require(type(cases) is list, "fixture cases are absent")
    require(len(cases) == len(rows), "fixture row count differs from reconstruction")
    stored_values: list[Decimal] = []
    expected_keys = {"expected_nats", "k", "sample_count", "x_count", "y_count"}
    for row_index, (case, row) in enumerate(zip(cases, rows, strict=True)):
        require(type(case) is dict, f"row {row_index}: case is not an object")
        require(set(case) == expected_keys, f"row {row_index}: case fields changed")
        for field, expected in (
            ("sample_count", row.sample_count),
            ("k", row.k),
            ("x_count", row.x_count),
            ("y_count", row.y_count),
        ):
            require(type(case[field]) is int, f"row {row_index}: {field} is not an integer")
            require(case[field] == expected, f"row {row_index}: reconstructed order changed")
        require(
            1 <= row.k < row.sample_count
            and row.k - 1 <= row.x_count < row.sample_count
            and row.k - 1 <= row.y_count < row.sample_count,
            f"row {row_index}: count tuple is outside the exact identity domain",
        )
        stored_values.append(decimal_from_fixture(case["expected_nats"], row_index))

    exhaustive_endpoints = sum(is_endpoint(row) for row in rows[:exhaustive_cut])
    stress_endpoints = sum(is_endpoint(row) for row in rows[exhaustive_cut:])
    require(
        exhaustive_endpoints == EXHAUSTIVE_ENDPOINT_COUNT,
        "reconstructed exhaustive endpoint count changed",
    )
    require(
        stress_endpoints == STRESS_ENDPOINT_COUNT,
        "reconstructed stress endpoint count changed",
    )
    require(
        max(
            index
            for row in rows
            for index in (
                row.k - 1,
                row.sample_count - 1,
                row.x_count,
                row.y_count,
            )
        )
        == MAXIMUM_RECIPROCAL_SUMMAND_INDEX,
        "maximum reciprocal summand index changed",
    )
    return fixture, rows, stored_values


def directed_harmonic_prefixes() -> tuple[list[Decimal], list[Decimal], Context, Context]:
    require(ENCLOSURE_PRECISION == 160, "directed-enclosure precision changed")
    require(LOWER_ROUNDING == ROUND_FLOOR, "lower-bound rounding is not ROUND_FLOOR")
    require(UPPER_ROUNDING == ROUND_CEILING, "upper-bound rounding is not ROUND_CEILING")
    lower_context = Context(prec=ENCLOSURE_PRECISION, rounding=LOWER_ROUNDING)
    upper_context = Context(prec=ENCLOSURE_PRECISION, rounding=UPPER_ROUNDING)
    lower = [Decimal(0)] * (MAXIMUM_RECIPROCAL_SUMMAND_INDEX + 1)
    upper = [Decimal(0)] * (MAXIMUM_RECIPROCAL_SUMMAND_INDEX + 1)
    lower_total = Decimal(0)
    upper_total = Decimal(0)
    one = Decimal(1)
    for denominator in range(1, MAXIMUM_RECIPROCAL_SUMMAND_INDEX + 1):
        decimal_denominator = Decimal(denominator)
        lower_total = lower_context.add(
            lower_total,
            lower_context.divide(one, decimal_denominator),
        )
        upper_total = upper_context.add(
            upper_total,
            upper_context.divide(one, decimal_denominator),
        )
        lower[denominator] = lower_total
        upper[denominator] = upper_total
    require(lower[1] == upper[1] == Decimal(1), "H_1 enclosure changed")
    require(lower[2] == upper[2] == Decimal("1.5"), "H_2 enclosure changed")
    require(
        lower[-1] <= upper[-1],
        "terminal directed harmonic-prefix enclosure is inverted",
    )
    return lower, upper, lower_context, upper_context


def identity_enclosure(
    row: Row,
    lower_prefix: list[Decimal],
    upper_prefix: list[Decimal],
    lower_context: Context,
    upper_context: Context,
) -> tuple[Decimal, Decimal]:
    if is_endpoint(row):
        # Pairwise symbolic cancellation is exact.  Evaluating four independently rounded
        # prefixes here would manufacture a nonzero interval around a known rational zero.
        return Decimal(0), Decimal(0)

    lower = lower_context.subtract(
        lower_context.subtract(
            lower_context.add(
                lower_prefix[row.k - 1],
                lower_prefix[row.sample_count - 1],
            ),
            upper_prefix[row.x_count],
        ),
        upper_prefix[row.y_count],
    )
    upper = upper_context.subtract(
        upper_context.subtract(
            upper_context.add(
                upper_prefix[row.k - 1],
                upper_prefix[row.sample_count - 1],
            ),
            lower_prefix[row.x_count],
        ),
        lower_prefix[row.y_count],
    )
    require(lower <= upper, f"directed identity enclosure inverted for {row}")
    return lower, upper


def validate_exhaustive_fraction_containment(
    rows: list[Row],
    enclosures: list[tuple[Decimal, Decimal]],
) -> None:
    """Cross-check directedness against exact rationals on all 6,920 small rows."""

    harmonics = [Fraction(0)] * EXHAUSTIVE_MAX_SAMPLES
    total = Fraction(0)
    for denominator in range(1, EXHAUSTIVE_MAX_SAMPLES):
        total += Fraction(1, denominator)
        harmonics[denominator] = total
    for row_index in range(EXHAUSTIVE_ROW_COUNT):
        row = rows[row_index]
        exact = (
            harmonics[row.k - 1]
            + harmonics[row.sample_count - 1]
            - harmonics[row.x_count]
            - harmonics[row.y_count]
        )
        lower, upper = enclosures[row_index]
        require(
            Fraction(lower) <= exact <= Fraction(upper),
            f"row {row_index}: directed Decimal interval excludes the exact Fraction",
        )


def build_exact_enclosures(
    rows: list[Row],
    stored_values: list[Decimal],
) -> tuple[list[tuple[Decimal, Decimal]], list[str], dict[str, Any]]:
    lower_prefix, upper_prefix, lower_context, upper_context = directed_harmonic_prefixes()
    require(
        REFERENCE_ROUNDING_PRECISION == 80,
        "exact-reference rounding precision changed",
    )
    require(
        REFERENCE_ROUNDING == ROUND_HALF_EVEN,
        "exact-reference rounding is not ROUND_HALF_EVEN",
    )
    reference_context = Context(
        prec=REFERENCE_ROUNDING_PRECISION,
        rounding=REFERENCE_ROUNDING,
    )
    enclosures: list[tuple[Decimal, Decimal]] = []
    exact_rounded_texts: list[str] = []
    digest = hashlib.sha256()
    stored_text_mismatches = 0
    stored_numeric_mismatches = 0
    stored_binary64_mismatches = 0
    maximum_discrepancy = Fraction(-1)
    maximum_discrepancy_rows: list[int] = []

    for row_index, (row, stored) in enumerate(
        zip(rows, stored_values, strict=True)
    ):
        lower, upper = identity_enclosure(
            row,
            lower_prefix,
            upper_prefix,
            lower_context,
            upper_context,
        )
        rounded_lower = reference_context.plus(lower)
        rounded_upper = reference_context.plus(upper)
        require(
            rounded_lower == rounded_upper,
            f"row {row_index}: directed endpoints do not prove one 80-digit rounding",
        )
        rounded_text = str(rounded_lower)
        digest.update(rounded_text.encode("ascii"))
        digest.update(b"\n")
        exact_rounded_texts.append(rounded_text)
        enclosures.append((lower, upper))

        stored_text_mismatches += str(stored) != rounded_text
        stored_numeric_mismatches += stored != rounded_lower
        stored_binary64_mismatches += (
            float(stored).hex() != float(rounded_text).hex()
        )
        discrepancy = exact_finite_decimal_distance(stored, rounded_lower)
        if discrepancy > maximum_discrepancy:
            maximum_discrepancy = discrepancy
            maximum_discrepancy_rows = [row_index]
        elif discrepancy == maximum_discrepancy:
            maximum_discrepancy_rows.append(row_index)

    validate_exhaustive_fraction_containment(rows, enclosures)
    exact_rounded_digest = digest.hexdigest()
    require(
        exact_rounded_digest == EXPECTED_EXACT_ROUNDED_VECTOR_SHA256,
        "80-digit exact-rounded vector digest changed",
    )
    require(
        stored_text_mismatches == EXPECTED_STORED_TEXT_MISMATCH_COUNT,
        "stored Decimal versus exact-rounded textual mismatch count changed",
    )
    require(
        stored_numeric_mismatches == EXPECTED_STORED_NUMERIC_MISMATCH_COUNT,
        "stored Decimal versus exact-rounded numeric mismatch count changed",
    )
    require(
        stored_binary64_mismatches == EXPECTED_STORED_BINARY64_MISMATCH_COUNT,
        "stored Decimal versus exact-rounded binary64 conversion mismatch count changed",
    )
    require(
        maximum_discrepancy == EXPECTED_STORED_MAX_DISCREPANCY,
        "maximum stored Decimal versus exact-rounded discrepancy changed",
    )
    require(
        maximum_discrepancy_rows
        == [EXPECTED_STORED_MAX_DISCREPANCY_ROW_INDEX]
        and rows[maximum_discrepancy_rows[0]]
        == Row(*EXPECTED_STORED_MAX_DISCREPANCY_ROW),
        "maximum stored Decimal discrepancy row or tie count changed",
    )
    require(
        len(maximum_discrepancy_rows) == EXPECTED_STORED_MAX_DISCREPANCY_TIES,
        "maximum stored Decimal discrepancy tie count changed",
    )
    observations = {
        "exact_rounded_digest": exact_rounded_digest,
        "stored_text_mismatches": stored_text_mismatches,
        "stored_numeric_mismatches": stored_numeric_mismatches,
        "stored_binary64_mismatches": stored_binary64_mismatches,
        "exact_discrepancy_comparison_count": len(rows),
        "maximum_discrepancy": EXPECTED_STORED_MAX_DISCREPANCY_TEXT,
        "maximum_discrepancy_row_index": maximum_discrepancy_rows[0],
    }
    return enclosures, exact_rounded_texts, observations


def shifted_harmonic_table(max_argument: int) -> list[float]:
    """Reproduce table[m] = H_(m-1) with the selected Neumaier prefix policy."""

    table = [0.0] * (max_argument + 1)
    total = 0.0
    correction = 0.0
    for argument in range(2, max_argument + 1):
        value = 1.0 / float(argument - 1)
        next_total = total + value
        if abs(total) >= abs(value):
            correction += (total - next_total) + value
        else:
            correction += (value - next_total) + total
        total = next_total
        table[argument] = total + correction
    return table


def selected_sorted_range_term(table: list[float], row: Row) -> float:
    x_argument = row.x_count + 1
    y_argument = row.y_count + 1
    lower_argument = min(x_argument, y_argument)
    upper_argument = max(x_argument, y_argument)
    return (table[row.sample_count] - table[upper_argument]) - (
        table[lower_argument] - table[row.k]
    )


def absolute_error_interval(
    actual: float,
    exact_lower: Decimal,
    exact_upper: Decimal,
    lower_context: Context,
    upper_context: Context,
) -> ErrorInterval:
    actual_decimal = Decimal.from_float(actual)
    if actual_decimal < exact_lower:
        return ErrorInterval(
            lower_context.subtract(exact_lower, actual_decimal),
            upper_context.subtract(exact_upper, actual_decimal),
        )
    if actual_decimal > exact_upper:
        return ErrorInterval(
            lower_context.subtract(actual_decimal, exact_upper),
            upper_context.subtract(actual_decimal, exact_lower),
        )
    return ErrorInterval(
        Decimal(0),
        max(
            upper_context.subtract(actual_decimal, exact_lower),
            upper_context.subtract(exact_upper, actual_decimal),
        ),
    )


def check_absolute_error_interval_branches(
    lower_context: Context,
    upper_context: Context,
) -> None:
    """Exercise below, above, and interior branches against exact finite witnesses."""

    cases = (
        (
            "actual below exact interval",
            1.0,
            Decimal(2),
            Decimal(3),
            ErrorInterval(Decimal(1), Decimal(2)),
        ),
        (
            "actual above exact interval",
            4.0,
            Decimal(2),
            Decimal(3),
            ErrorInterval(Decimal(1), Decimal(2)),
        ),
        (
            "actual inside exact interval",
            2.25,
            Decimal(2),
            Decimal(3),
            ErrorInterval(Decimal(0), Decimal("0.75")),
        ),
    )
    for label, actual, exact_lower, exact_upper, expected in cases:
        observed = absolute_error_interval(
            actual,
            exact_lower,
            exact_upper,
            lower_context,
            upper_context,
        )
        require(observed == expected, f"absolute-error branch witness failed: {label}")


def intervals_prove_unique_maximum(
    candidate: ErrorInterval,
    other_maximum_upper: Decimal,
) -> bool:
    return candidate.lower > other_maximum_upper


def check_unique_maximum_predicate() -> None:
    require(
        intervals_prove_unique_maximum(
            ErrorInterval(Decimal(3), Decimal(4)),
            Decimal(2),
        ),
        "unique-maximum predicate rejects a strictly separated witness",
    )
    require(
        not intervals_prove_unique_maximum(
            ErrorInterval(Decimal(2), Decimal(4)),
            Decimal(2),
        ),
        "unique-maximum predicate accepts equality without strict separation",
    )
    require(
        not intervals_prove_unique_maximum(
            ErrorInterval(Decimal(1), Decimal(4)),
            Decimal(2),
        ),
        "unique-maximum predicate accepts overlapping error intervals",
    )


def strict_lower_threshold(
    multiplier: Decimal,
    unit: Decimal,
    context: Context,
) -> Decimal:
    """Construct a conservative threshold for a strict upper-bound comparison."""

    require(
        context.rounding == ROUND_FLOOR,
        "strict comparison threshold is not rounded downward",
    )
    return context.multiply(multiplier, unit)


def check_binary64(
    rows: list[Row],
    stored_values: list[Decimal],
    enclosures: list[tuple[Decimal, Decimal]],
) -> dict[str, Any]:
    require(
        sys.float_info.radix == 2
        and sys.float_info.mant_dig == 53
        and sys.float_info.max_exp == 1_024,
        "host Python float is not the required IEEE-754 binary64 format",
    )
    table = shifted_harmonic_table(max(row.sample_count for row in rows))
    lower_context = Context(prec=ENCLOSURE_PRECISION, rounding=ROUND_FLOOR)
    upper_context = Context(prec=ENCLOSURE_PRECISION, rounding=ROUND_CEILING)
    check_absolute_error_interval_branches(lower_context, upper_context)
    check_unique_maximum_predicate()
    error_intervals: list[ErrorInterval] = []

    rounded_reference_maximum = -1.0
    rounded_reference_maximum_rows: list[int] = []
    swap_asymmetries = 0
    endpoint_positive_zeros = 0
    endpoint_negative_zeros = 0
    selected_positive_zeros = 0
    selected_negative_zeros = 0
    selected_nonzeros = 0
    for row_index, (row, stored, enclosure) in enumerate(
        zip(rows, stored_values, enclosures, strict=True)
    ):
        actual = selected_sorted_range_term(table, row)
        swapped = selected_sorted_range_term(
            table,
            Row(row.sample_count, row.k, row.y_count, row.x_count),
        )
        swap_asymmetries += actual.hex() != swapped.hex()
        selected_positive_zeros += actual.hex() == "0x0.0p+0"
        selected_negative_zeros += actual.hex() == "-0x0.0p+0"
        selected_nonzeros += actual != 0.0
        if is_endpoint(row):
            endpoint_positive_zeros += actual.hex() == "0x0.0p+0"
            endpoint_negative_zeros += actual.hex() == "-0x0.0p+0"

        exact_lower, exact_upper = enclosure
        error_interval = absolute_error_interval(
            actual,
            exact_lower,
            exact_upper,
            lower_context,
            upper_context,
        )
        require(
            Decimal(0) <= error_interval.lower <= error_interval.upper,
            f"row {row_index}: absolute-error enclosure is invalid",
        )
        error_intervals.append(error_interval)

        # This is intentionally the distinct, older comparator: both operands are binary64.
        rounded_reference_error = abs(actual - float(stored))
        if rounded_reference_error > rounded_reference_maximum:
            rounded_reference_maximum = rounded_reference_error
            rounded_reference_maximum_rows = [row_index]
        elif rounded_reference_error == rounded_reference_maximum:
            rounded_reference_maximum_rows.append(row_index)

    require(swap_asymmetries == 0, "selected sorted-range source-swap bits changed")
    require(
        endpoint_positive_zeros == ENDPOINT_COUNT and endpoint_negative_zeros == 0,
        "selected endpoint signed-zero behavior changed",
    )
    require(
        selected_positive_zeros == EXPECTED_SELECTED_POSITIVE_ZERO_COUNT
        and selected_negative_zeros == EXPECTED_SELECTED_NEGATIVE_ZERO_COUNT
        and selected_nonzeros == EXPECTED_SELECTED_NONZERO_COUNT,
        "selected full-corpus signed-zero/nonzero partition changed",
    )

    exact_maximum_row_index = max(
        range(len(error_intervals)),
        key=lambda index: error_intervals[index].upper,
    )
    exact_maximum = error_intervals[exact_maximum_row_index]
    other_maximum_upper = max(
        interval.upper
        for index, interval in enumerate(error_intervals)
        if index != exact_maximum_row_index
    )
    exact_maximum_ties = sum(
        interval.upper == exact_maximum.upper for interval in error_intervals
    )
    require(
        exact_maximum_row_index == EXPECTED_EXACT_ERROR_MAX_ROW_INDEX
        and rows[exact_maximum_row_index] == Row(*EXPECTED_EXACT_ERROR_MAX_ROW),
        "exact-rational error maximum row changed",
    )
    require(
        exact_maximum_ties == EXPECTED_EXACT_ERROR_MAX_TIES,
        "exact-rational error maximum upper-bound tie count changed",
    )
    require(
        intervals_prove_unique_maximum(exact_maximum, other_maximum_upper),
        "directed intervals no longer prove a unique exact-rational error maximum",
    )
    require(
        exact_maximum.lower == EXPECTED_EXACT_ERROR_LOWER
        and exact_maximum.upper == EXPECTED_EXACT_ERROR_UPPER,
        "exact-rational maximum error interval changed",
    )
    exact_maximum_actual_hex = selected_sorted_range_term(
        table,
        rows[exact_maximum_row_index],
    ).hex()
    require(
        exact_maximum_actual_hex == EXPECTED_EXACT_ERROR_MAX_ACTUAL_HEX,
        "selected binary64 value at the exact-rational maximum row changed",
    )

    epsilon_decimal = Decimal.from_float(sys.float_info.epsilon)
    require(
        EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT == "9.761311",
        "exact-rational strict epsilon multiplier changed or was conflated with 8",
    )
    require(
        EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER == 32,
        "exact-rational review ceiling changed",
    )
    # A strict comparison uses a downward-rounded threshold.  Comparing with an upper
    # threshold would not, in general, prove that the exact threshold was not crossed.
    exact_strict_threshold = strict_lower_threshold(
        Decimal(EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT),
        epsilon_decimal,
        lower_context,
    )
    allowed_threshold = strict_lower_threshold(
        Decimal(EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER),
        epsilon_decimal,
        lower_context,
    )
    require(
        exact_maximum.upper < exact_strict_threshold,
        "exact-rational error is not strictly below 9.761311 binary64 epsilon",
    )
    require(
        exact_maximum.upper < allowed_threshold,
        "exact-rational error exceeds the frozen 32-epsilon review ceiling",
    )

    expected_rounded_reference_maximum = (
        EXPECTED_ROUNDED_REFERENCE_MAX_EPSILON_MULTIPLIER
        * sys.float_info.epsilon
    )
    require(
        rounded_reference_maximum == expected_rounded_reference_maximum,
        "binary64-rounded-reference maximum is not exactly 8 epsilon",
    )
    require(
        len(rounded_reference_maximum_rows)
        == EXPECTED_ROUNDED_REFERENCE_MAX_TIES,
        "binary64-rounded-reference maximum tie count changed",
    )
    require(
        rounded_reference_maximum_rows[0]
        == EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW_INDEX
        and rows[rounded_reference_maximum_rows[0]]
        == Row(*EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW),
        "binary64-rounded-reference first maximum row changed",
    )
    return {
        "exact_error_lower": exact_maximum.lower,
        "exact_error_upper": exact_maximum.upper,
        "exact_error_row_index": exact_maximum_row_index,
        "exact_error_actual_hex": exact_maximum_actual_hex,
        "rounded_reference_maximum_epsilon": (
            EXPECTED_ROUNDED_REFERENCE_MAX_EPSILON_MULTIPLIER
        ),
        "rounded_reference_ties": len(rounded_reference_maximum_rows),
        "rounded_reference_first_row_index": rounded_reference_maximum_rows[0],
    }


def check_scope_boundary() -> None:
    require(
        sha256(SCOPE_BOUNDARY.encode("utf-8")) == EXPECTED_SCOPE_BOUNDARY_SHA256,
        "scope-boundary wording changed",
    )


def check(repo_root: Path) -> None:
    check_scope_boundary()
    check_exact_decimal_comparator()
    _, rows, stored_values = load_digest_bound_fixture(repo_root)
    enclosures, _, exact_observations = build_exact_enclosures(rows, stored_values)
    binary64_observations = check_binary64(rows, stored_values, enclosures)

    print(
        "OK: digest-bound directed exact-rational enclosure for "
        f"{len(rows)} frozen schema-2 rows"
    )
    print(
        "  exact-rounded 80-digit vector SHA-256 "
        f"{exact_observations['exact_rounded_digest']}; "
        f"{EXHAUSTIVE_ROW_COUNT} exhaustive exact-Fraction containment witnesses"
    )
    print(
        "  stored 80-digit Decimal prefix strings versus exact-rounded Decimal: "
        f"{exact_observations['stored_text_mismatches']} textually unequal, "
        f"{exact_observations['stored_numeric_mismatches']} numerically unequal; "
        f"unique maximum discrepancy {exact_observations['maximum_discrepancy']} "
        "at zero-based row "
        f"{exact_observations['maximum_discrepancy_row_index']} "
        f"{EXPECTED_STORED_MAX_DISCREPANCY_ROW}; binary64 conversion mismatches "
        f"{exact_observations['stored_binary64_mismatches']}; "
        f"{exact_observations['exact_discrepancy_comparison_count']} exact "
        "Fraction(Decimal) discrepancy comparisons"
    )
    print(
        "  Python reproduction of selected Neumaier-prefix/sorted-range binary64 versus exact "
        "rational: "
        f"unique maximum at zero-based row {binary64_observations['exact_error_row_index']} "
        f"{EXPECTED_EXACT_ERROR_MAX_ROW}; rigorous nats interval "
        f"[{binary64_observations['exact_error_lower']}, "
        f"{binary64_observations['exact_error_upper']}]; selected value "
        f"{binary64_observations['exact_error_actual_hex']}; strictly below "
        f"{EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT} epsilon and below "
        f"{EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER} epsilon"
    )
    print(
        "  distinct binary64-rounded-reference comparator: maximum "
        f"{binary64_observations['rounded_reference_maximum_epsilon']} epsilon; "
        f"{binary64_observations['rounded_reference_ties']} ties; first zero-based row "
        f"{binary64_observations['rounded_reference_first_row_index']} "
        f"{EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW}"
    )
    print(
        "  shared cuts/assumptions: same-repository digest-bound frozen rows and exact harmonic "
        "identity; trusts Python Decimal directed-rounding semantics and this host's Python "
        "binary64 operations; does not inspect Rust source or a compiled binary"
    )
    print(f"  scope: {SCOPE_BOUNDARY}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root containing the digest-bound fixture and generator",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        check(args.repo_root.resolve())
    except (CheckError, DecimalException, OSError, UnicodeError, ValueError) as error:
        print(f"exact-enclosure check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
