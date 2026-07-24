#!/usr/bin/env python3
"""Independent exact-integer verifier for certified categorical SxPID2 reports.

This program deliberately does not import the Rust certifier, Rug, MPFR, GMP, NumPy, SymPy, or
another numerical package.  It treats every certificate field as untrusted input.  From the
canonical count table it independently reconstructs:

* the four source-event unions and their target intersections;
* all informative, misinformative, and direct signed-net cumulative expressions;
* the fixed two-source Möbius transform and all twelve atom expressions; and
* the exact log-linear term list for all 24 coordinates.

For a positive rational x, the verifier range-reduces x = 2**e * y with 1 <= y < 2 and bounds
ln(y) through

    ln(y) = 2 * sum(k >= 0, z**(2*k+1)/(2*k+1)),  z = (y-1)/(y+1).

Here 0 <= z <= 1/3.  Every finite-series operation uses outward fixed-point integer rounding.  The
omitted positive tail after m terms obeys

    tail <= 2*z**(2*m+1) / ((2*m+1)*(1-z**2))
         <= 9*z**(2*m+1) / (4*(2*m+1)).

The checker adaptively increases its fixed-point scale until its independently derived enclosure
is a subset of the dyadic interval asserted by the certificate.  Failure to prove containment is
a rejection, not numerical agreement.

Trust boundary: the Python interpreter, its arbitrary-precision integer and Fraction semantics,
the SHA-256 implementation, this source file, and the reviewed mathematical argument above remain
trusted.  No claim about data provenance, population inference, pid-core binary64 output,
higher-source/continuous PID, or downstream application validity follows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import marshal
import os
import re
import stat
import sys
import types
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, NoReturn, Sequence, cast

try:
    import tomllib
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised only on unsupported Python runtimes.
    tomllib = None  # type: ignore[assignment]

INPUT_SCHEMA: Final = "pid-rs/categorical-sxpid2-count-table/v1"
REPORT_SCHEMA: Final = "pid-rs/certified-sxpid-report/v1"
VERIFICATION_SCHEMA: Final = "pid-rs/certified-sxpid-independent-verification/v1"
EXPRESSION_SCHEMA: Final = "pid-rs/exact-log-linear/v1"
DEFINITION_REVISION: Final = "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1"
RESOURCE_POLICY_ID: Final = "sxpid2-certification-default-v1"
UNITS: Final = "nats"

MAX_INPUT_BYTES: Final = 4 * 1024 * 1024
MAX_CERTIFICATE_BYTES: Final = 11 * 1024 * 1024
MAX_ROWS: Final = 4096
MAX_STATE_WIDTH: Final = 32
MAX_TOKEN_BYTES: Final = 128
MAX_COUNT_DIGITS: Final = 1024
MAX_TOTAL_COUNT_BITS: Final = 8192
MAX_REPORT_INTEGER_DIGITS: Final = 4096
MAX_JSON_INTEGER_DIGITS: Final = 24
MAX_DYADIC_EXPONENT_ABS: Final = 65_536
MAX_FIXED_POINT_BITS: Final = 2048
MAX_TERMS_PER_EXPRESSION: Final = 4096
MAX_CUMULATIVE_EXTRACTION_TERMS: Final = 1638
MAX_CANONICAL_PAYLOAD_BYTES: Final = 10 * 1024 * 1024
MAX_SOURCE_MANIFEST_MEMBER_BYTES: Final = 4 * 1024 * 1024
MAX_SOURCE_MANIFEST_BYTES: Final = 32 * 1024 * 1024
MAX_VERIFIER_SOURCE_BYTES: Final = 2 * 1024 * 1024
FIXED_POINT_PRECISIONS: Final = (256, 384, 512, 768, 1024, 1536, 2048)

NODE_IDS: Final = ("source_one", "source_two", "joint_sources", "redundancy")
ATOM_IDS: Final = ("unique_one", "unique_two", "synergy", "redundancy")
COMPONENT_IDS: Final = ("informative", "misinformative", "net")
MOBIUS: Final = (
    (1, 0, 0, -1),
    (0, 1, 0, -1),
    (-1, -1, 1, 1),
    (0, 0, 0, 1),
)
ZETA: Final = (
    (1, 0, 0, 1),
    (0, 1, 0, 1),
    (1, 1, 1, 1),
    (0, 0, 0, 1),
)
LATTICE_VALUE: Final = {
    "cumulative_node_order": [
        {"id": "source_one", "source_collection_masks": [1]},
        {"id": "source_two", "source_collection_masks": [2]},
        {"id": "joint_sources", "source_collection_masks": [3]},
        {"id": "redundancy", "source_collection_masks": [1, 2]},
    ],
    "atom_order": list(ATOM_IDS),
    "mobius_atom_from_cumulative": [list(row) for row in MOBIUS],
    "zeta_cumulative_from_atom": [list(row) for row in ZETA],
}
PRECISION_POLICY_VALUE: Final = {
    "id": RESOURCE_POLICY_ID,
    "initial_bits": 128,
    "maximum_bits": 4096,
    "maximum_iterations": 6,
    "growth_factor": 2,
    "target_width": {"significand": "1", "exponent2": -160},
    "structural_limits": {
        "maximum_input_bytes": MAX_INPUT_BYTES,
        "maximum_rows": MAX_ROWS,
        "maximum_state_width": MAX_STATE_WIDTH,
        "maximum_token_bytes": MAX_TOKEN_BYTES,
        "maximum_count_digits": MAX_COUNT_DIGITS,
        "maximum_total_count_bits": MAX_TOTAL_COUNT_BITS,
        "maximum_terms_per_expression": 4096,
        "maximum_total_exact_terms": 8192,
        "maximum_cumulative_extraction_terms": 1638,
        "maximum_estimated_exact_term_json_bytes": 8 * 1024 * 1024,
        "maximum_canonical_payload_bytes": 10 * 1024 * 1024,
    },
}
ARITHMETIC_VALUE: Final = {
    "locked_rug_crate_version": "1.30.0",
    "locked_transitive_gmp_mpfr_sys_crate_version": "1.7.1",
    "manifest_requested_rug_features": ["float", "rational", "std"],
    "direct_gmp_mpfr_sys_dependency_status": (
        "absent_to_remove_direct_dependency_feature_injection_surface"
    ),
    "effective_dependency_feature_resolution_status": (
        "not_self_reported_or_bound_official_qualification_separately_requires_"
        "default_locked_metadata_graph"
    ),
    "compiled_native_version_constants_status": (
        "not_reported_no_direct_native_sys_api_dependency"
    ),
    "runtime_native_version_probe": "not_performed_by_safe_rust_wrapper",
    "native_archive_digests": None,
    "native_archive_digest_status": (
        "absent_not_claimed_external_build_evidence_required_for_archive_binding"
    ),
    "authoritative_endpoint_encoding": (
        "normalized_exact_dyadic_significand_times_2^exponent2"
    ),
}
LOCKED_REGISTRY_PACKAGES: Final = {
    "rug": {
        "source": "registry+https://github.com/rust-lang/crates.io-index",
        "checksum": "07a8857882aec59d27254b02481c709327c13de6fad1da60bfc4f9783eaaa61e",
    },
    "gmp-mpfr-sys": {
        "source": "registry+https://github.com/rust-lang/crates.io-index",
        "checksum": "7db155b537cb791b133341f99f68371d86ee7fa4c79aacfbc376d72d23c70531",
    },
}
TOOL_BINDING_STATIC_VALUE: Final = {
    "source_manifest_encoding": (
        "domain_tag_then_repeated_u64be_path_length_path_u64be_content_length_content"
    ),
    "canonical_json_encoding": (
        "serde_json_value_recursive_lexicographic_object_keys_no_floats_v1"
    ),
    "executable_digest_status": (
        "absent_runtime_tool_does_not_self_attest_its_executable"
    ),
    "project_distribution_route": "source_only_policy",
    "artifact_distribution_status": "not_verified_by_runtime",
}
BUILD_CONTEXT_SCHEMA: Final = "pid-rs/certified-sxpid-build-context/v1"
BUILD_CONTEXT_SCOPE: Final = (
    "non_exhaustive_cargo_profile_metadata_only_external_evidence_required_for_"
    "effective_dependency_feature_resolution_rustc_wrappers_effective_flags_cargo_"
    "linker_native_compiler_and_cache_content"
)
NATIVE_CACHE_POLICIES: Final = (
    "default_gmp_mpfr_sys_cache_selection",
    "explicit_gmp_mpfr_sys_cache_present_path_not_recorded",
)
PERMITTED_CLAIM: Final = (
    "For this canonical exact two-source empirical count table, pinned SxPID definition "
    "and lattice, precision policy, and locked dependency versions, each emitted dyadic "
    "interval encloses the tool-encoded exact-real averaged categorical SxPID coordinate, "
    "conditional on the recorded source wrapper, explicitly non-exhaustive build context, "
    "and unverified effective dependency-feature resolution, native-library, compiler, "
    "effective-build-flags, and data-meaning trust boundary. Manifest-requested Rug "
    "features and locked crate versions are reported; compiled native version constants, "
    "native archive digests, and executable digests are absent and are not claimed."
)
EXCLUDED_CLAIMS: Final = [
    "pid-core_binary64_correctness",
    "population_or_sampling_assumptions",
    "estimator_consistency_or_calibration",
    "continuous_ksg_isx_or_pid",
    "three_or_four_source_sxpid",
    "imin",
    "pointwise_sxpid",
    "quantization_equivalence",
    "input_data_authenticity_or_provenance",
    "mpfr_gmp_rug_or_compiler_correctness",
    "downstream_application_validity",
    "formal_verification_of_all_pid_rs",
]
SOURCE_MANIFEST_FILES: Final = (
    "build.rs",
    "Cargo.lock",
    "Cargo.toml",
    "README.md",
    "src/digest.rs",
    "src/directed.rs",
    "src/error.rs",
    "src/evaluate.rs",
    "src/exact.rs",
    "src/extract.rs",
    "src/lattice2.rs",
    "src/lib.rs",
    "src/main.rs",
    "src/report.rs",
    "src/resource.rs",
    "src/schema.rs",
)
SOURCE_MANIFEST_DOMAIN: Final = b"pid-certified-sxpid-source-manifest-v1\0"
TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9._:+-]+$")
CANONICAL_UNSIGNED_RE: Final = re.compile(r"^(0|[1-9][0-9]*)$")
CANONICAL_POSITIVE_RE: Final = re.compile(r"^[1-9][0-9]*$")
CANONICAL_SIGNED_RE: Final = re.compile(r"^(0|-?[1-9][0-9]*)$")
LOWER_HEX_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_VERIFIER_SOURCE_PATH: Final = Path(os.path.realpath(__file__))


class VerificationError(Exception):
    """Fail-closed input, schema, reconstruction, or proof error."""


def _stable_regular_file_bytes(path: Path, maximum: int, label: str) -> bytes:
    """Read one bounded regular file and reject link/race-shaped evidence."""

    try:
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise VerificationError(
                f"{label} is not a regular non-symlink file: {path}"
            )
        if before.st_size > maximum:
            raise VerificationError(f"{label} exceeds {maximum} bytes: {path}")
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            identity_opened = (
                opened.st_dev,
                opened.st_ino,
                opened.st_size,
                opened.st_mtime_ns,
            )
            if identity_opened != identity_before:
                raise VerificationError(f"{label} changed before it was opened: {path}")
            raw = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
    except VerificationError:
        raise
    except OSError as error:
        raise VerificationError(f"cannot read {label} {path}: {error}") from error
    if len(raw) > maximum:
        raise VerificationError(f"{label} exceeds {maximum} bytes: {path}")
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_after != identity_opened or len(raw) != after.st_size:
        raise VerificationError(f"{label} changed while it was read: {path}")
    return raw


_INITIAL_VERIFIER_SOURCE_BYTES: Final = _stable_regular_file_bytes(
    _VERIFIER_SOURCE_PATH, MAX_VERIFIER_SOURCE_BYTES, "independent verifier source"
)
_INITIAL_VERIFIER_SOURCE_SHA256: Final = hashlib.sha256(
    _INITIAL_VERIFIER_SOURCE_BYTES
).hexdigest()


@dataclass(frozen=True, order=True)
class State:
    source_one: tuple[str, ...]
    source_two: tuple[str, ...]
    target: tuple[str, ...]


@dataclass(frozen=True)
class Row:
    state: State
    count: int


@dataclass(frozen=True)
class NormalizedInput:
    document: dict[str, Any]
    rows: tuple[Row, ...]
    total_count: int
    source_widths: tuple[int, int]
    target_width: int
    raw_sha256: str
    semantic_sha256: str


@dataclass(frozen=True)
class Coordinate:
    kind: str
    node: str
    component: str
    expression: Mapping[Fraction, Fraction]

    @property
    def identity(self) -> dict[str, str]:
        return {"kind": self.kind, "node": self.node, "component": self.component}


@dataclass(frozen=True)
class DyadicInterval:
    lower: Fraction
    upper: Fraction


@dataclass(frozen=True)
class VerificationResult:
    report: dict[str, Any]


Expression = dict[Fraction, Fraction]


def _reject_json_float(_: str) -> NoReturn:
    raise VerificationError("JSON floating-point numbers are forbidden")


def _parse_json_integer(text: str) -> int:
    if len(text.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
        raise VerificationError("JSON integer exceeds the structural digit limit")
    return int(text, 10)


def _reject_json_constant(text: str) -> NoReturn:
    raise VerificationError(f"nonstandard JSON constant is forbidden: {text}")


def _python_integer_text_limit() -> int:
    getter = getattr(sys, "get_int_max_str_digits", None)
    if getter is None:
        return 0
    return cast(int, getter())


def _require_python_integer_text_capacity() -> None:
    limit = _python_integer_text_limit()
    if limit != 0 and limit < MAX_REPORT_INTEGER_DIGITS:
        raise VerificationError(
            "Python's integer-text conversion limit is "
            f"{limit}; the verifier requires 0 (unlimited) or at least "
            f"{MAX_REPORT_INTEGER_DIGITS}"
        )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def parse_json(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_int=_parse_json_integer,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        VerificationError,
    ) as error:
        if isinstance(error, VerificationError):
            raise
        raise VerificationError(
            f"{label} is not accepted strict UTF-8 JSON: {error}"
        ) from error


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise VerificationError(f"canonical JSON encoding failed: {error}") from error


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_hex(canonical_json_bytes(value))


def _expect_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must be an object")
    return value


def _expect_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise VerificationError(f"{label} must be an array")
    return value


def _expect_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise VerificationError(f"{label} must be a string")
    return value


def _expect_bounded_single_line_string(
    value: Any, label: str, maximum_bytes: int
) -> str:
    text = _expect_string(value, label)
    encoded = text.encode("utf-8")
    if (
        not encoded
        or len(encoded) > maximum_bytes
        or any(character in text for character in ("\0", "\n", "\r"))
        or any(not character.isprintable() for character in text)
    ):
        raise VerificationError(
            f"{label} must be a nonempty bounded single-line string"
        )
    return text


def _expect_build_token(value: Any, label: str) -> str:
    text = _expect_bounded_single_line_string(value, label, 256)
    if TOKEN_RE.fullmatch(text) is None:
        raise VerificationError(f"{label} is not a canonical build token")
    return text


def _expect_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise VerificationError(f"{label} must be a boolean")
    return value


def _expect_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VerificationError(f"{label} must be an integer")
    return cast(int, value)


def _require_keys(
    value: Mapping[str, Any], expected: Iterable[str], label: str
) -> None:
    expected_set = set(expected)
    actual = set(value)
    if actual != expected_set:
        missing = sorted(expected_set - actual)
        unknown = sorted(actual - expected_set)
        raise VerificationError(
            f"{label} key mismatch: missing={missing}, unknown={unknown}"
        )


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if not _strictly_equal(actual, expected):
        raise VerificationError(f"{label} mismatch")


def _strictly_equal(actual: Any, expected: Any) -> bool:
    """Compare JSON-like values without Python's bool/int coercion."""

    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _strictly_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strictly_equal(left, right) for left, right in zip(actual, expected)
        )
    return bool(actual == expected)


def _parse_canonical_positive(text: Any, label: str, maximum_digits: int) -> int:
    value = _expect_string(text, label)
    if len(value) > maximum_digits or CANONICAL_POSITIVE_RE.fullmatch(value) is None:
        raise VerificationError(f"{label} is not a bounded canonical positive integer")
    return int(value, 10)


def _parse_canonical_signed(text: Any, label: str, maximum_digits: int) -> int:
    value = _expect_string(text, label)
    if (
        len(value.lstrip("-")) > maximum_digits
        or CANONICAL_SIGNED_RE.fullmatch(value) is None
    ):
        raise VerificationError(f"{label} is not a bounded canonical signed integer")
    return int(value, 10)


def _validate_token_vector(value: Any, label: str) -> tuple[str, ...]:
    items = _expect_list(value, label)
    if not 1 <= len(items) <= MAX_STATE_WIDTH:
        raise VerificationError(f"{label} width must be in 1..={MAX_STATE_WIDTH}")
    result: list[str] = []
    for index, item in enumerate(items):
        token = _expect_string(item, f"{label}[{index}]")
        if (
            TOKEN_RE.fullmatch(token) is None
            or not 1 <= len(token.encode("ascii")) <= MAX_TOKEN_BYTES
        ):
            raise VerificationError(
                f"{label}[{index}] is not a canonical ASCII state token"
            )
        result.append(token)
    return tuple(result)


def validate_input(raw: bytes) -> NormalizedInput:
    _require_python_integer_text_capacity()
    if len(raw) > MAX_INPUT_BYTES:
        raise VerificationError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    document = _expect_object(parse_json(raw, "count table"), "count table")
    _require_keys(
        document,
        ("schema", "definition_revision", "units", "resource_policy_id", "rows"),
        "count table",
    )
    _require_equal(document["schema"], INPUT_SCHEMA, "input schema")
    _require_equal(
        document["definition_revision"],
        DEFINITION_REVISION,
        "input definition revision",
    )
    _require_equal(document["units"], UNITS, "input units")
    _require_equal(
        document["resource_policy_id"], RESOURCE_POLICY_ID, "input resource policy"
    )
    raw_rows = _expect_list(document["rows"], "input rows")
    if not 1 <= len(raw_rows) <= MAX_ROWS:
        raise VerificationError(f"input row count must be in 1..={MAX_ROWS}")

    rows: list[Row] = []
    previous: State | None = None
    widths: tuple[int, int] | None = None
    target_width: int | None = None
    total = 0
    for index, raw_row in enumerate(raw_rows):
        row = _expect_object(raw_row, f"row {index}")
        _require_keys(row, ("source_states", "target_state", "count"), f"row {index}")
        sources = _expect_list(row["source_states"], f"row {index} source_states")
        if len(sources) != 2:
            raise VerificationError(
                f"row {index} must contain exactly two source states"
            )
        source_one = _validate_token_vector(sources[0], f"row {index} source one")
        source_two = _validate_token_vector(sources[1], f"row {index} source two")
        target = _validate_token_vector(row["target_state"], f"row {index} target")
        current_widths = (len(source_one), len(source_two))
        if widths is None:
            widths = current_widths
            target_width = len(target)
        elif current_widths != widths or len(target) != target_width:
            raise VerificationError(f"row {index} has inconsistent state widths")

        state = State(source_one, source_two, target)
        if previous is not None and state <= previous:
            relation = "duplicates" if state == previous else "precedes"
            raise VerificationError(
                f"row {index} {relation} the previous canonical state"
            )
        count = _parse_canonical_positive(
            row["count"], f"row {index} count", MAX_COUNT_DIGITS
        )
        total += count
        if total.bit_length() > MAX_TOTAL_COUNT_BITS:
            raise VerificationError(
                "input total count exceeds the structural bit limit"
            )
        rows.append(Row(state, count))
        previous = state

    if widths is None or target_width is None:
        raise VerificationError("nonempty input lost its state widths")
    return NormalizedInput(
        document=document,
        rows=tuple(rows),
        total_count=total,
        source_widths=widths,
        target_width=target_width,
        raw_sha256=sha256_hex(raw),
        semantic_sha256=canonical_digest(document),
    )


def _add_mass(table: dict[Any, int], key: Any, count: int) -> None:
    table[key] = table.get(key, 0) + count


def _add_term(
    expression: Expression, coefficient: Fraction, argument: Fraction
) -> None:
    if argument <= 0:
        raise VerificationError(
            "independent extraction produced a nonpositive log argument"
        )
    if coefficient == 0 or argument == 1:
        return
    combined = expression.get(argument, Fraction(0)) + coefficient
    if combined == 0:
        expression.pop(argument, None)
    else:
        if argument not in expression and len(expression) >= MAX_TERMS_PER_EXPRESSION:
            raise VerificationError(
                "one independently reconstructed exact expression would exceed "
                f"{MAX_TERMS_PER_EXPRESSION} terms"
            )
        expression[argument] = combined


def _linear_combination(
    expressions: Sequence[Expression], coefficients: Sequence[int]
) -> Expression:
    if len(expressions) != len(coefficients):
        raise VerificationError("internal linear-combination dimension mismatch")
    result: Expression = {}
    for expression, scale in zip(expressions, coefficients):
        for argument, coefficient in expression.items():
            _add_term(result, coefficient * scale, argument)
    return result


def _verify_integer_lattice() -> None:
    for row in range(4):
        for column in range(4):
            product = sum(
                ZETA[row][inner] * MOBIUS[inner][column] for inner in range(4)
            )
            if product != int(row == column):
                raise VerificationError(
                    "pinned independent zeta and Möbius matrices are not inverse"
                )


def _direct_mutual_information_expression(
    data: NormalizedInput, source_index: int
) -> Expression:
    source_masses: dict[Any, int] = {}
    target_masses: dict[tuple[str, ...], int] = {}
    joint_masses: dict[tuple[Any, tuple[str, ...]], int] = {}
    for row in data.rows:
        if source_index == 0:
            source: Any = row.state.source_one
        elif source_index == 1:
            source = row.state.source_two
        elif source_index == 2:
            source = (row.state.source_one, row.state.source_two)
        else:
            raise VerificationError("unsupported independent MI source index")
        _add_mass(source_masses, source, row.count)
        _add_mass(target_masses, row.state.target, row.count)
        _add_mass(joint_masses, (source, row.state.target), row.count)

    expression: Expression = {}
    for (source, target), joint_mass in sorted(joint_masses.items(), key=repr):
        coefficient = Fraction(joint_mass, data.total_count)
        argument = Fraction(
            joint_mass * data.total_count,
            source_masses[source] * target_masses[target],
        )
        _add_term(expression, coefficient, argument)
    return expression


def reconstruct_coordinates(data: NormalizedInput) -> list[Coordinate]:
    """Reconstruct all 24 expressions without reading report expression or lattice fields."""

    _verify_integer_lattice()
    source_one_mass: dict[tuple[str, ...], int] = {}
    source_two_mass: dict[tuple[str, ...], int] = {}
    joint_source_mass: dict[tuple[tuple[str, ...], tuple[str, ...]], int] = {}
    target_mass: dict[tuple[str, ...], int] = {}
    source_one_target_mass: dict[tuple[tuple[str, ...], tuple[str, ...]], int] = {}
    source_two_target_mass: dict[tuple[tuple[str, ...], tuple[str, ...]], int] = {}

    for row in data.rows:
        state = row.state
        _add_mass(source_one_mass, state.source_one, row.count)
        _add_mass(source_two_mass, state.source_two, row.count)
        _add_mass(joint_source_mass, (state.source_one, state.source_two), row.count)
        _add_mass(target_mass, state.target, row.count)
        _add_mass(source_one_target_mass, (state.source_one, state.target), row.count)
        _add_mass(source_two_target_mass, (state.source_two, state.target), row.count)

    cumulative: dict[str, list[Expression]] = {
        component: [{} for _ in range(4)] for component in COMPONENT_IDS
    }
    total = data.total_count
    for row in data.rows:
        state = row.state
        count = row.count
        target = target_mass[state.target]
        source_one = source_one_mass[state.source_one]
        source_two = source_two_mass[state.source_two]
        joint_source = joint_source_mass[(state.source_one, state.source_two)]
        source_one_target = source_one_target_mass[(state.source_one, state.target)]
        source_two_target = source_two_target_mass[(state.source_two, state.target)]

        # Inclusion-exclusion is an independent closed form for the disjunction event:
        # P(S1=s1 or S2=s2), with and without the keyed target restriction. The
        # target-restricted intersection equals this keyed row's count only because
        # validate_input requires each complete (s1, s2, t) state to occur exactly once.
        union_redundancy = source_one + source_two - joint_source
        target_union_redundancy = source_one_target + source_two_target - count
        unions = (source_one, source_two, joint_source, union_redundancy)
        target_unions = (
            source_one_target,
            source_two_target,
            count,
            target_union_redundancy,
        )
        weight = Fraction(count, total)

        for node_index, (union, target_union) in enumerate(zip(unions, target_unions)):
            if not (
                0 < count <= target_union <= union <= total
                and target_union <= target <= total
            ):
                raise VerificationError(
                    "independent event-count nesting failed at "
                    f"row {state!r}, node {NODE_IDS[node_index]}"
                )
            plus_argument = Fraction(total, union)
            minus_argument = Fraction(target, target_union)
            net_argument = Fraction(total * target_union, union * target)
            if plus_argument / minus_argument != net_argument:
                raise VerificationError(
                    "independent exact local signed-net identity failed"
                )
            _add_term(cumulative["informative"][node_index], weight, plus_argument)
            _add_term(cumulative["misinformative"][node_index], weight, minus_argument)
            _add_term(cumulative["net"][node_index], weight, net_argument)
        cumulative_terms = sum(
            len(expression)
            for component in COMPONENT_IDS
            for expression in cumulative[component]
        )
        if cumulative_terms > MAX_CUMULATIVE_EXTRACTION_TERMS:
            raise VerificationError(
                "independent cumulative extraction reached "
                f"{cumulative_terms} terms; maximum is "
                f"{MAX_CUMULATIVE_EXTRACTION_TERMS}"
            )

    for source_index in range(3):
        direct_mi = _direct_mutual_information_expression(data, source_index)
        if direct_mi != cumulative["net"][source_index]:
            raise VerificationError(
                f"independent direct-MI identity failed at node {NODE_IDS[source_index]}"
            )

    atoms: dict[str, list[Expression]] = {}
    for component in COMPONENT_IDS:
        atoms[component] = [
            _linear_combination(cumulative[component], row) for row in MOBIUS
        ]
        for index, zeta_row in enumerate(ZETA):
            reconstructed = _linear_combination(atoms[component], zeta_row)
            if reconstructed != cumulative[component][index]:
                raise VerificationError("independent exact zeta reconstruction failed")

    coordinates: list[Coordinate] = []
    for kind, node_ids, components in (
        ("cumulative", NODE_IDS, cumulative),
        ("atom", ATOM_IDS, atoms),
    ):
        for component in COMPONENT_IDS:
            for node_id, expression in zip(node_ids, components[component]):
                coordinates.append(Coordinate(kind, node_id, component, expression))
    if len(coordinates) != 24:
        raise VerificationError("independent extraction did not produce 24 coordinates")
    return coordinates


def _rational_object(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def expression_terms(expression: Mapping[Fraction, Fraction]) -> list[dict[str, Any]]:
    return [
        {
            "coefficient": _rational_object(expression[argument]),
            "log_argument": _rational_object(argument),
        }
        for argument in sorted(expression)
    ]


def _integer_text_upper_bound(value: int) -> int:
    return max(abs(value).bit_length(), 1) + int(value < 0)


def _estimated_expression_json_bytes(
    expression: Mapping[Fraction, Fraction],
) -> int:
    total = 2
    for argument, coefficient in expression.items():
        total += (
            192
            + _integer_text_upper_bound(coefficient.numerator)
            + _integer_text_upper_bound(coefficient.denominator)
            + _integer_text_upper_bound(argument.numerator)
            + _integer_text_upper_bound(argument.denominator)
        )
    return total


def _floor_fraction_units(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise VerificationError("internal fixed-point denominator is nonpositive")
    return numerator // denominator


def _ceil_fraction_units(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise VerificationError("internal fixed-point denominator is nonpositive")
    return -((-numerator) // denominator)


def _mul_down(left: int, right: int, scale: int) -> int:
    return _floor_fraction_units(left * right, scale)


def _mul_up(left: int, right: int, scale: int) -> int:
    return _ceil_fraction_units(left * right, scale)


def _floor_log2_fraction(value: Fraction) -> int:
    if value <= 0:
        raise VerificationError(
            "logarithm range reduction requires a positive rational"
        )
    numerator = value.numerator
    denominator = value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < (denominator << exponent):
            exponent -= 1
    elif (numerator << (-exponent)) < denominator:
        exponent -= 1
    while exponent >= 0 and numerator >= (denominator << (exponent + 1)):
        exponent += 1
    while exponent < 0 and (numerator << (-(exponent + 1))) >= denominator:
        exponent += 1
    return exponent


def _scale_by_power_of_two(value: Fraction, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(value.numerator, value.denominator << exponent)
    return Fraction(value.numerator << (-exponent), value.denominator)


def _log_unit_interval(
    value: Fraction, bits: int, ln2: tuple[int, int]
) -> tuple[int, int]:
    """Return integer units L,U such that L/2**bits <= ln(value) <= U/2**bits."""

    if value <= 0:
        raise VerificationError("logarithm argument must be positive")
    if value == 1:
        return (0, 0)
    exponent = _floor_log2_fraction(value)
    reduced = _scale_by_power_of_two(value, exponent)
    if not Fraction(1) <= reduced < Fraction(2):
        raise VerificationError("exact power-of-two logarithm range reduction failed")
    lower, upper = _atanh_log_reduced_interval(reduced, bits)
    ln2_lower, ln2_upper = ln2
    if exponent >= 0:
        lower += exponent * ln2_lower
        upper += exponent * ln2_upper
    else:
        lower += exponent * ln2_upper
        upper += exponent * ln2_lower
    return (lower, upper)


def _atanh_log_reduced_interval(reduced: Fraction, bits: int) -> tuple[int, int]:
    """Direct series enclosure for ln(reduced), where 1 <= reduced <= 2."""

    if not Fraction(1) <= reduced <= Fraction(2):
        raise VerificationError("direct reduced logarithm argument escaped [1,2]")
    if reduced == 1:
        return (0, 0)
    scale = 1 << bits
    z = (reduced - 1) / (reduced + 1)
    z_lower = _floor_fraction_units(z.numerator * scale, z.denominator)
    z_upper = _ceil_fraction_units(z.numerator * scale, z.denominator)
    z2_lower = _mul_down(z_lower, z_lower, scale)
    z2_upper = _mul_up(z_upper, z_upper, scale)
    power_lower = z_lower
    power_upper = z_upper
    lower = 0
    upper = 0
    terms = max(32, (bits + 32) // 3 + 1)
    next_odd = 1
    for index in range(terms):
        odd = 2 * index + 1
        lower += _floor_fraction_units(2 * power_lower, odd)
        upper += _ceil_fraction_units(2 * power_upper, odd)
        power_lower = _mul_down(power_lower, z2_lower, scale)
        power_upper = _mul_up(power_upper, z2_upper, scale)
        next_odd = odd + 2
    upper += _ceil_fraction_units(9 * power_upper, 4 * next_odd)
    return (lower, upper)


def _evaluate_expression_units(
    expression: Mapping[Fraction, Fraction],
    bits: int,
    cache: dict[Fraction, tuple[int, int]],
) -> tuple[int, int]:
    if not expression:
        return (0, 0)
    scale = 1 << bits
    ln2 = cache.get(Fraction(2))
    if ln2 is None:
        ln2 = _atanh_log_reduced_interval(Fraction(2), bits)
        cache[Fraction(2)] = ln2
    lower = 0
    upper = 0
    for argument in sorted(expression):
        log_interval = cache.get(argument)
        if log_interval is None:
            log_interval = _log_unit_interval(argument, bits, ln2)
            cache[argument] = log_interval
        log_lower, log_upper = log_interval
        coefficient = expression[argument]
        if coefficient > 0:
            term_lower_numerator = coefficient.numerator * log_lower
            term_upper_numerator = coefficient.numerator * log_upper
            denominator = coefficient.denominator
        elif coefficient < 0:
            term_lower_numerator = coefficient.numerator * log_upper
            term_upper_numerator = coefficient.numerator * log_lower
            denominator = coefficient.denominator
        else:
            raise VerificationError(
                "independent canonical expression retained zero coefficient"
            )
        lower += _floor_fraction_units(term_lower_numerator, denominator)
        upper += _ceil_fraction_units(term_upper_numerator, denominator)
    if lower > upper:
        raise VerificationError(
            "independent fixed-point expression enclosure is inverted"
        )
    # `scale` is referenced here to make the fixed denominator explicit in this routine.
    if scale != 1 << bits:
        raise VerificationError("internal fixed-point scale identity failed")
    return (lower, upper)


def _parse_dyadic(value: Any, label: str) -> Fraction:
    document = _expect_object(value, label)
    _require_keys(document, ("significand", "exponent2"), label)
    significand = _parse_canonical_signed(
        document["significand"], f"{label}.significand", MAX_REPORT_INTEGER_DIGITS
    )
    exponent = _expect_int(document["exponent2"], f"{label}.exponent2")
    if abs(exponent) > MAX_DYADIC_EXPONENT_ABS:
        raise VerificationError(
            f"{label}.exponent2 exceeds the independent verifier resource bound"
        )
    if significand == 0:
        if exponent != 0:
            raise VerificationError(f"{label} zero is not normalized")
    elif significand % 2 == 0:
        raise VerificationError(f"{label} nonzero significand is not normalized to odd")
    if exponent >= 0:
        return Fraction(significand << exponent)
    return Fraction(significand, 1 << (-exponent))


def _parse_report_rational(value: Any, label: str) -> Fraction:
    document = _expect_object(value, label)
    _require_keys(document, ("numerator", "denominator"), label)
    numerator = _parse_canonical_signed(
        document["numerator"], f"{label}.numerator", MAX_REPORT_INTEGER_DIGITS
    )
    denominator = _parse_canonical_positive(
        document["denominator"], f"{label}.denominator", MAX_REPORT_INTEGER_DIGITS
    )
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise VerificationError(f"{label} is not a normalized rational")
    return result


def _validate_report_term_list(value: Any, label: str) -> list[dict[str, Any]]:
    terms = _expect_list(value, label)
    previous: Fraction | None = None
    for index, item in enumerate(terms):
        term = _expect_object(item, f"{label}[{index}]")
        _require_keys(term, ("coefficient", "log_argument"), f"{label}[{index}]")
        coefficient = _parse_report_rational(
            term["coefficient"], f"{label}[{index}].coefficient"
        )
        argument = _parse_report_rational(
            term["log_argument"], f"{label}[{index}].log_argument"
        )
        if coefficient == 0 or argument <= 0 or argument == 1:
            raise VerificationError(
                f"{label}[{index}] is not a canonical nontrivial log term"
            )
        if previous is not None and argument <= previous:
            raise VerificationError(
                f"{label} arguments are not strictly numerically increasing"
            )
        previous = argument
    return terms


def _validate_sha256(value: Any, label: str) -> str:
    text = _expect_string(value, label)
    if LOWER_HEX_RE.fullmatch(text) is None:
        raise VerificationError(
            f"{label} must be a lowercase SHA-256 hexadecimal digest"
        )
    return text


def source_manifest_digest(certifier_root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(SOURCE_MANIFEST_DOMAIN)
    total_bytes = 0
    for relative in SOURCE_MANIFEST_FILES:
        path = certifier_root / relative
        raw = _stable_regular_file_bytes(
            path,
            MAX_SOURCE_MANIFEST_MEMBER_BYTES,
            f"source-manifest member {relative}",
        )
        total_bytes += len(raw)
        if total_bytes > MAX_SOURCE_MANIFEST_BYTES:
            raise VerificationError(
                f"source manifest exceeds {MAX_SOURCE_MANIFEST_BYTES} bytes"
            )
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _parse_toml_document(raw: bytes, label: str) -> dict[str, Any]:
    """Parse one reviewed TOML artifact with the Python standard-library parser."""

    if tomllib is None:
        raise VerificationError(
            "Python 3.11 or later with tomllib is required to verify Cargo bindings"
        )
    try:
        decoded = raw.decode("utf-8", errors="strict")
        parsed = tomllib.loads(decoded)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise VerificationError(
            f"{label} is not accepted UTF-8 TOML: {error}"
        ) from error
    if not isinstance(parsed, dict):
        raise VerificationError(f"{label} must decode to a TOML table")
    return cast(dict[str, Any], parsed)


def _direct_dependency_tables(
    manifest: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    """Return root and target-specific direct dependency tables."""

    result: list[tuple[str, Mapping[str, Any]]] = []
    dependency_keys = ("dependencies", "dev-dependencies", "build-dependencies")
    for key in dependency_keys:
        value = manifest.get(key)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise VerificationError(f"Cargo.toml {key} must be a table")
        result.append((key, value))

    targets = manifest.get("target")
    if targets is None:
        return result
    if not isinstance(targets, dict):
        raise VerificationError("Cargo.toml target must be a table")
    for target_name, target_value in targets.items():
        if not isinstance(target_name, str) or not isinstance(target_value, dict):
            raise VerificationError("Cargo.toml target entry must be a named table")
        for key in dependency_keys:
            value = target_value.get(key)
            if value is None:
                continue
            if not isinstance(value, dict):
                raise VerificationError(
                    f"Cargo.toml target.{target_name}.{key} must be a table"
                )
            result.append((f"target.{target_name}.{key}", value))
    return result


def _validate_local_arithmetic_binding(
    certifier_root: Path, cargo_lock_raw: bytes
) -> None:
    """Bind reported arithmetic metadata to the reviewed Cargo manifest and lockfile."""

    manifest_raw = _stable_regular_file_bytes(
        certifier_root / "Cargo.toml",
        MAX_SOURCE_MANIFEST_MEMBER_BYTES,
        "certifier Cargo.toml",
    )
    manifest = _parse_toml_document(manifest_raw, "certifier Cargo.toml")
    for forbidden_table in ("patch", "replace"):
        if forbidden_table in manifest:
            raise VerificationError(
                f"Cargo.toml [{forbidden_table}] source substitution is outside the "
                "reviewed arithmetic binding"
            )
    if manifest.get("workspace") != {}:
        raise VerificationError(
            "Cargo.toml workspace configuration must be the pinned empty standalone table"
        )
    dependency_tables = _direct_dependency_tables(manifest)
    root_dependencies = next(
        (table for name, table in dependency_tables if name == "dependencies"), None
    )
    if root_dependencies is None:
        raise VerificationError("Cargo.toml has no root dependencies table")
    expected_rug = {
        "version": f"={ARITHMETIC_VALUE['locked_rug_crate_version']}",
        "default-features": False,
        "features": ARITHMETIC_VALUE["manifest_requested_rug_features"],
    }
    _require_equal(
        root_dependencies.get("rug"),
        expected_rug,
        "Cargo.toml Rug dependency against arithmetic evidence",
    )
    for table_name, table in dependency_tables:
        for dependency_name, dependency_specification in table.items():
            package_name = dependency_name
            if isinstance(dependency_specification, dict):
                declared_package = dependency_specification.get("package")
                if declared_package is not None:
                    if not isinstance(declared_package, str):
                        raise VerificationError(
                            f"Cargo.toml dependency package alias in {table_name} "
                            "must be a string"
                        )
                    package_name = declared_package
            if package_name == "gmp-mpfr-sys":
                raise VerificationError(
                    "Cargo.toml direct gmp-mpfr-sys dependency contradicts arithmetic "
                    f"evidence in {table_name}"
                )
            if package_name == "rug" and not (
                table_name == "dependencies" and dependency_name == "rug"
            ):
                raise VerificationError(
                    "Cargo.toml contains an additional direct Rug dependency surface in "
                    f"{table_name}"
                )
    manifest_features = manifest.get("features")
    if manifest_features not in (None, {}):
        raise VerificationError(
            "Cargo.toml package feature aliases are outside the v1 arithmetic binding"
        )

    lock = _parse_toml_document(cargo_lock_raw, "certifier Cargo.lock")
    raw_packages = lock.get("package")
    if not isinstance(raw_packages, list):
        raise VerificationError("Cargo.lock package must be an array of tables")
    packages: list[Mapping[str, Any]] = []
    for index, package in enumerate(raw_packages):
        if not isinstance(package, dict):
            raise VerificationError(f"Cargo.lock package {index} must be a table")
        packages.append(package)

    def named_packages(name: str) -> list[Mapping[str, Any]]:
        return [package for package in packages if package.get("name") == name]

    rug_packages = named_packages("rug")
    native_packages = named_packages("gmp-mpfr-sys")
    if len(rug_packages) != 1:
        raise VerificationError("Cargo.lock must contain exactly one Rug package")
    if len(native_packages) != 1:
        raise VerificationError(
            "Cargo.lock must contain exactly one gmp-mpfr-sys package"
        )
    _require_equal(
        rug_packages[0].get("version"),
        ARITHMETIC_VALUE["locked_rug_crate_version"],
        "Cargo.lock Rug version against arithmetic evidence",
    )
    _require_equal(
        native_packages[0].get("version"),
        ARITHMETIC_VALUE["locked_transitive_gmp_mpfr_sys_crate_version"],
        "Cargo.lock gmp-mpfr-sys version against arithmetic evidence",
    )
    for package_name, package in (
        ("rug", rug_packages[0]),
        ("gmp-mpfr-sys", native_packages[0]),
    ):
        expected_registry = LOCKED_REGISTRY_PACKAGES[package_name]
        _require_equal(
            package.get("source"),
            expected_registry["source"],
            f"Cargo.lock {package_name} registry source against reviewed binding",
        )
        _require_equal(
            package.get("checksum"),
            expected_registry["checksum"],
            f"Cargo.lock {package_name} checksum against reviewed binding",
        )
    rug_dependencies = rug_packages[0].get("dependencies")
    if not isinstance(rug_dependencies, list) or "gmp-mpfr-sys" not in rug_dependencies:
        raise VerificationError(
            "Cargo.lock Rug package does not bind the expected gmp-mpfr-sys dependency"
        )


def _validate_certificate_structure(
    raw: bytes,
    data: NormalizedInput,
    coordinates: Sequence[Coordinate],
    certifier_root: Path,
) -> tuple[dict[str, Any], list[tuple[Coordinate, DyadicInterval]], str]:
    if len(raw) > MAX_CERTIFICATE_BYTES:
        raise VerificationError(f"certificate exceeds {MAX_CERTIFICATE_BYTES} bytes")
    envelope = _expect_object(parse_json(raw, "certificate"), "certificate")
    _require_keys(envelope, ("payload_sha256", "payload"), "certificate")
    payload_digest = _validate_sha256(envelope["payload_sha256"], "payload_sha256")
    payload = _expect_object(envelope["payload"], "certificate payload")
    canonical_payload = canonical_json_bytes(payload)
    if len(canonical_payload) > MAX_CANONICAL_PAYLOAD_BYTES:
        raise VerificationError(
            f"canonical certificate payload exceeds {MAX_CANONICAL_PAYLOAD_BYTES} bytes"
        )
    if sha256_hex(canonical_payload) != payload_digest:
        raise VerificationError(
            "certificate payload SHA-256 does not match its canonical payload"
        )
    _require_keys(
        payload,
        (
            "schema",
            "status",
            "route",
            "definition_revision",
            "units",
            "input",
            "exact_expression",
            "lattice",
            "extraction_checks",
            "precision_policy",
            "arithmetic",
            "tool_binding",
            "coordinates",
            "cross_checks",
            "claim_boundary",
        ),
        "certificate payload",
    )
    _require_equal(payload["schema"], REPORT_SCHEMA, "report schema")
    _require_equal(payload["status"], "certified", "report status")
    _require_equal(payload["route"], "categorical_sxpid2_averaged", "report route")
    _require_equal(
        payload["definition_revision"], DEFINITION_REVISION, "report definition"
    )
    _require_equal(payload["units"], UNITS, "report units")

    input_evidence = _expect_object(payload["input"], "report input evidence")
    _require_keys(
        input_evidence,
        (
            "raw_input_sha256",
            "semantic_input_sha256",
            "row_count",
            "total_count",
            "source_state_widths",
            "target_state_width",
        ),
        "report input evidence",
    )
    _require_equal(
        input_evidence["raw_input_sha256"], data.raw_sha256, "raw input digest"
    )
    _require_equal(
        input_evidence["semantic_input_sha256"],
        data.semantic_sha256,
        "semantic input digest",
    )
    _require_equal(
        input_evidence["row_count"], len(data.rows), "input row count evidence"
    )
    _require_equal(
        _parse_canonical_positive(
            input_evidence["total_count"],
            "input total_count evidence",
            MAX_COUNT_DIGITS + 4,
        ),
        data.total_count,
        "input total count evidence",
    )
    _require_equal(
        input_evidence["source_state_widths"],
        list(data.source_widths),
        "source width evidence",
    )
    _require_equal(
        input_evidence["target_state_width"], data.target_width, "target width evidence"
    )

    lattice = _expect_object(payload["lattice"], "lattice binding")
    _require_keys(lattice, ("sha256", "value"), "lattice binding")
    _require_equal(lattice["value"], LATTICE_VALUE, "pinned lattice evidence")
    _require_equal(
        _validate_sha256(lattice["sha256"], "lattice digest"),
        canonical_digest(LATTICE_VALUE),
        "lattice digest",
    )

    precision = _expect_object(payload["precision_policy"], "precision policy binding")
    _require_keys(precision, ("sha256", "value"), "precision policy binding")
    _require_equal(precision["value"], PRECISION_POLICY_VALUE, "precision policy value")
    _require_equal(
        _validate_sha256(precision["sha256"], "precision policy digest"),
        canonical_digest(PRECISION_POLICY_VALUE),
        "precision policy digest",
    )

    extraction = _expect_object(payload["extraction_checks"], "extraction checks")
    _require_keys(
        extraction,
        (
            "positive_mass_constraints_checked",
            "local_net_ratio_identities_checked",
            "self_redundancy_identities_checked",
            "exact_mobius_reconstructions_checked",
            "all_passed",
        ),
        "extraction checks",
    )
    expected_rows_times_nodes = len(data.rows) * 4
    _require_equal(
        extraction["positive_mass_constraints_checked"],
        expected_rows_times_nodes,
        "positive mass check count",
    )
    _require_equal(
        extraction["local_net_ratio_identities_checked"],
        expected_rows_times_nodes,
        "local net check count",
    )
    _require_equal(
        extraction["self_redundancy_identities_checked"], 3, "MI identity count"
    )
    _require_equal(
        extraction["exact_mobius_reconstructions_checked"], 12, "Möbius check count"
    )
    _require_equal(
        _expect_bool(extraction["all_passed"], "extraction all_passed"), True, "checks"
    )

    exact_evidence = _expect_object(
        payload["exact_expression"], "exact expression evidence"
    )
    _require_keys(
        exact_evidence,
        ("schema", "coordinate_count", "coordinates_sha256", "resource_use"),
        "exact expression evidence",
    )
    _require_equal(exact_evidence["schema"], EXPRESSION_SCHEMA, "expression schema")
    _require_equal(
        exact_evidence["coordinate_count"], 24, "expression coordinate count"
    )
    expression_resource_use = _expect_object(
        exact_evidence["resource_use"], "expression resource use"
    )
    _require_keys(
        expression_resource_use,
        (
            "total_exact_terms",
            "maximum_terms_in_one_expression",
            "estimated_exact_term_json_bytes_upper_bound",
        ),
        "expression resource use",
    )

    raw_coordinates = _expect_list(payload["coordinates"], "certificate coordinates")
    if len(raw_coordinates) != 24 or len(coordinates) != 24:
        raise VerificationError(
            "certificate and independent reconstruction must each have 24 coordinates"
        )
    checked: list[tuple[Coordinate, DyadicInterval]] = []
    digest_items: list[dict[str, Any]] = []
    precision_traces: set[tuple[int, int]] = set()
    for index, (raw_coordinate, expected) in enumerate(
        zip(raw_coordinates, coordinates)
    ):
        coordinate = _expect_object(raw_coordinate, f"coordinate {index}")
        _require_keys(
            coordinate,
            ("identity", "exact_terms", "expression_sha256", "interval"),
            f"coordinate {index}",
        )
        _require_equal(
            coordinate["identity"], expected.identity, f"coordinate {index} identity"
        )
        reported_terms = _validate_report_term_list(
            coordinate["exact_terms"], f"coordinate {index} exact_terms"
        )
        expected_terms = expression_terms(expected.expression)
        _require_equal(
            reported_terms, expected_terms, f"coordinate {index} exact terms"
        )
        _require_equal(
            _validate_sha256(
                coordinate["expression_sha256"], f"coordinate {index} expression digest"
            ),
            canonical_digest(expected_terms),
            f"coordinate {index} expression digest",
        )
        digest_items.append(
            {"identity": expected.identity, "exact_terms": expected_terms}
        )

        interval = _expect_object(
            coordinate["interval"], f"coordinate {index} interval"
        )
        _require_keys(
            interval,
            (
                "lower",
                "upper",
                "final_working_precision_bits",
                "precision_iterations",
                "target_width_met",
                "decision",
                "exact_zero_witness",
            ),
            f"coordinate {index} interval",
        )
        lower = _parse_dyadic(interval["lower"], f"coordinate {index} lower")
        upper = _parse_dyadic(interval["upper"], f"coordinate {index} upper")
        if lower > upper:
            raise VerificationError(f"coordinate {index} interval is inverted")
        if upper - lower > Fraction(1, 1 << 160):
            raise VerificationError(f"coordinate {index} exceeds the v1 target width")
        _require_equal(
            _expect_bool(
                interval["target_width_met"], f"coordinate {index} target_width_met"
            ),
            True,
            f"coordinate {index} target-width result",
        )
        working_bits = _expect_int(
            interval["final_working_precision_bits"],
            f"coordinate {index} working precision",
        )
        iterations = _expect_int(
            interval["precision_iterations"], f"coordinate {index} precision iterations"
        )
        if (
            working_bits not in (128, 256, 512, 1024, 2048, 4096)
            or not 1 <= iterations <= 6
        ):
            raise VerificationError(
                f"coordinate {index} has an invalid precision-policy trace"
            )
        if working_bits != 128 << (iterations - 1):
            raise VerificationError(
                f"coordinate {index} precision and iteration evidence disagree"
            )
        precision_traces.add((working_bits, iterations))
        if expected.expression:
            expected_decision = (
                "certified_positive"
                if lower > 0
                else "certified_negative"
                if upper < 0
                else "unresolved_sign"
            )
            _require_equal(
                interval["exact_zero_witness"], None, f"coordinate {index} zero witness"
            )
        else:
            expected_decision = "certified_exact_zero"
            _require_equal(
                lower, Fraction(0), f"coordinate {index} exact-zero lower endpoint"
            )
            _require_equal(
                upper, Fraction(0), f"coordinate {index} exact-zero upper endpoint"
            )
            _require_equal(
                interval["exact_zero_witness"],
                "canonical_exact_expression_has_no_terms",
                f"coordinate {index} exact-zero witness",
            )
        _require_equal(
            interval["decision"], expected_decision, f"coordinate {index} sign decision"
        )
        checked.append((expected, DyadicInterval(lower, upper)))

    if len(precision_traces) != 1:
        raise VerificationError(
            "coordinate precision-policy traces are not globally consistent"
        )
    _require_equal(
        _validate_sha256(exact_evidence["coordinates_sha256"], "coordinate-set digest"),
        canonical_digest(digest_items),
        "coordinate-set digest",
    )
    expected_term_counts = [len(coordinate.expression) for coordinate in coordinates]
    if any(count > 4096 for count in expected_term_counts):
        raise VerificationError(
            "independent reconstruction exceeds the v1 per-expression term limit"
        )
    if sum(expected_term_counts) > 8192:
        raise VerificationError(
            "independent reconstruction exceeds the v1 total exact-term limit"
        )
    _require_equal(
        expression_resource_use["total_exact_terms"],
        sum(expected_term_counts),
        "total exact-term resource evidence",
    )
    _require_equal(
        expression_resource_use["maximum_terms_in_one_expression"],
        max(expected_term_counts, default=0),
        "maximum exact-term resource evidence",
    )
    estimated_bytes = _expect_int(
        expression_resource_use["estimated_exact_term_json_bytes_upper_bound"],
        "estimated exact-term JSON-byte bound",
    )
    expected_estimated_bytes = sum(
        _estimated_expression_json_bytes(coordinate.expression)
        for coordinate in coordinates
    )
    _require_equal(
        estimated_bytes,
        expected_estimated_bytes,
        "estimated exact-term JSON-byte resource evidence",
    )
    if not 0 <= expected_estimated_bytes <= 8 * 1024 * 1024:
        raise VerificationError(
            "independent exact-term JSON-byte estimate exceeds the v1 policy"
        )

    tool_binding = _expect_object(payload["tool_binding"], "tool binding")
    _require_keys(
        tool_binding,
        (
            "runtime_source_manifest_sha256",
            "source_manifest_encoding",
            "cargo_lock_sha256",
            "canonical_json_encoding",
            "build_context",
            "executable_digest_status",
            "project_distribution_route",
            "artifact_distribution_status",
        ),
        "tool binding",
    )
    _require_equal(
        tool_binding["source_manifest_encoding"],
        "domain_tag_then_repeated_u64be_path_length_path_u64be_content_length_content",
        "source-manifest encoding",
    )
    _require_equal(
        tool_binding["canonical_json_encoding"],
        TOOL_BINDING_STATIC_VALUE["canonical_json_encoding"],
        "canonical JSON encoding",
    )
    for field in (
        "source_manifest_encoding",
        "executable_digest_status",
        "project_distribution_route",
        "artifact_distribution_status",
    ):
        _require_equal(
            tool_binding[field],
            TOOL_BINDING_STATIC_VALUE[field],
            f"tool binding {field}",
        )
    local_source_manifest_digest = source_manifest_digest(certifier_root)
    _require_equal(
        _validate_sha256(
            tool_binding["runtime_source_manifest_sha256"],
            "runtime source-manifest digest",
        ),
        local_source_manifest_digest,
        "runtime source-manifest digest against local reviewed source",
    )
    cargo_lock = _stable_regular_file_bytes(
        certifier_root / "Cargo.lock",
        MAX_SOURCE_MANIFEST_MEMBER_BYTES,
        "certifier Cargo.lock",
    )
    _require_equal(
        _validate_sha256(tool_binding["cargo_lock_sha256"], "Cargo.lock digest"),
        sha256_hex(cargo_lock),
        "Cargo.lock digest against local reviewed source",
    )
    _validate_local_arithmetic_binding(certifier_root, cargo_lock)

    # These blocks do not participate in the mathematical containment proof.  Their complete v1
    # shape is nevertheless checked so a schema downgrade cannot hide or relabel them.
    arithmetic = _expect_object(payload["arithmetic"], "arithmetic evidence")
    _require_keys(
        arithmetic,
        (
            "locked_rug_crate_version",
            "locked_transitive_gmp_mpfr_sys_crate_version",
            "manifest_requested_rug_features",
            "direct_gmp_mpfr_sys_dependency_status",
            "effective_dependency_feature_resolution_status",
            "compiled_native_version_constants_status",
            "runtime_native_version_probe",
            "native_archive_digests",
            "native_archive_digest_status",
            "authoritative_endpoint_encoding",
        ),
        "arithmetic evidence",
    )
    _require_equal(arithmetic, ARITHMETIC_VALUE, "arithmetic evidence")

    build_context = _expect_object(tool_binding["build_context"], "build context")
    _require_keys(
        build_context,
        (
            "schema",
            "rustc_verbose_version",
            "build_host",
            "build_target",
            "cargo_profile_name",
            "cargo_profile_optimization_level",
            "cargo_profile_debug",
            "native_cache_policy",
            "context_scope",
        ),
        "build context",
    )
    _require_equal(
        build_context["schema"],
        BUILD_CONTEXT_SCHEMA,
        "build-context schema",
    )
    rustc_verbose_version = _expect_bounded_single_line_string(
        build_context["rustc_verbose_version"], "rustc verbose version", 8192
    )
    for field in (
        "build_host",
        "build_target",
        "cargo_profile_name",
        "cargo_profile_optimization_level",
        "cargo_profile_debug",
    ):
        _expect_build_token(build_context[field], f"build context {field}")
    expected_host_line = f"host: {build_context['build_host']}"
    host_lines = [
        segment.strip()
        for segment in rustc_verbose_version.split("|")
        if segment.strip().startswith("host:")
    ]
    _require_equal(
        host_lines,
        [expected_host_line],
        "build host against rustc verbose-version evidence",
    )
    native_cache_policy = _expect_string(
        build_context["native_cache_policy"], "native cache policy"
    )
    if native_cache_policy not in NATIVE_CACHE_POLICIES:
        raise VerificationError("native cache policy is not a declared v1 value")
    _require_equal(
        build_context["context_scope"], BUILD_CONTEXT_SCOPE, "build-context scope"
    )

    cross_checks = _expect_object(payload["cross_checks"], "cross checks")
    _require_keys(
        cross_checks,
        (
            "direct_net_vs_informative_minus_misinformative_overlaps_checked",
            "successive_interval_intersections_checked",
            "all_passed",
        ),
        "cross checks",
    )
    _require_equal(
        cross_checks["direct_net_vs_informative_minus_misinformative_overlaps_checked"],
        8,
        "direct-net overlap check count",
    )
    (_, global_iterations) = next(iter(precision_traces))
    _require_equal(
        cross_checks["successive_interval_intersections_checked"],
        24 * (global_iterations - 1),
        "successive interval-intersection count",
    )
    _require_equal(
        _expect_bool(cross_checks["all_passed"], "cross-check all_passed"),
        True,
        "cross-check result",
    )

    claim_boundary = _expect_object(payload["claim_boundary"], "claim boundary")
    _require_keys(
        claim_boundary, ("permitted_claim", "excluded_claims"), "claim boundary"
    )
    _require_equal(
        claim_boundary["permitted_claim"], PERMITTED_CLAIM, "permitted claim"
    )
    _require_equal(
        claim_boundary["excluded_claims"], EXCLUDED_CLAIMS, "excluded claims"
    )
    return payload, checked, local_source_manifest_digest


def _prove_containment(
    checked: Sequence[tuple[Coordinate, DyadicInterval]],
) -> tuple[int, dict[str, tuple[Fraction, Fraction]]]:
    last_failures: list[str] = []
    for bits in FIXED_POINT_PRECISIONS:
        if bits > MAX_FIXED_POINT_BITS:
            break
        cache: dict[Fraction, tuple[int, int]] = {}
        failures: list[str] = []
        independent: dict[str, tuple[Fraction, Fraction]] = {}
        scale = 1 << bits
        for coordinate, claimed in checked:
            lower_units, upper_units = _evaluate_expression_units(
                coordinate.expression, bits, cache
            )
            lower = Fraction(lower_units, scale)
            upper = Fraction(upper_units, scale)
            key = f"{coordinate.kind}/{coordinate.node}/{coordinate.component}"
            independent[key] = (lower, upper)
            if not (claimed.lower <= lower and upper <= claimed.upper):
                failures.append(key)
        if not failures:
            return bits, independent
        last_failures = failures
    raise VerificationError(
        "independent bounded-log enclosure could not prove containment by "
        f"{MAX_FIXED_POINT_BITS} bits; unresolved coordinates={last_failures}"
    )


def _normalized_code_object(code: types.CodeType) -> types.CodeType:
    """Remove filesystem-specific filenames while retaining executable bytecode metadata."""

    normalized_constants = tuple(
        _normalized_code_object(value) if isinstance(value, types.CodeType) else value
        for value in code.co_consts
    )
    return code.replace(
        co_filename="<pid-certified-sxpid-independent-verifier>",
        co_consts=normalized_constants,
    )


def _loaded_execution_sha256() -> str:
    """Hash the live module-owned function code plus critical semantic constants."""

    functions: list[tuple[str, types.FunctionType]] = []
    for name, value in globals().items():
        if isinstance(value, types.FunctionType) and value.__module__ == __name__:
            functions.append((name, value))
        elif isinstance(value, type) and value.__module__ == __name__:
            for attribute_name, attribute in vars(value).items():
                function: types.FunctionType | None = None
                if isinstance(attribute, types.FunctionType):
                    function = attribute
                elif isinstance(attribute, (staticmethod, classmethod)):
                    function = attribute.__func__
                elif isinstance(attribute, property):
                    function = attribute.fget
                if function is not None:
                    functions.append((f"{name}.{attribute_name}", function))

    digest = hashlib.sha256()
    digest.update(b"pid-certified-sxpid-independent-loaded-execution-v1\0")
    for name, function in sorted(functions):
        encoded_name = name.encode("utf-8")
        code_bytes = marshal.dumps(_normalized_code_object(function.__code__))
        digest.update(len(encoded_name).to_bytes(8, "big"))
        digest.update(encoded_name)
        digest.update(len(code_bytes).to_bytes(8, "big"))
        digest.update(code_bytes)

    semantic_constants = {
        "schemas": [
            INPUT_SCHEMA,
            REPORT_SCHEMA,
            VERIFICATION_SCHEMA,
            EXPRESSION_SCHEMA,
        ],
        "definition_revision": DEFINITION_REVISION,
        "resource_policy_id": RESOURCE_POLICY_ID,
        "units": UNITS,
        "limits": [
            MAX_INPUT_BYTES,
            MAX_CERTIFICATE_BYTES,
            MAX_ROWS,
            MAX_STATE_WIDTH,
            MAX_TOKEN_BYTES,
            MAX_COUNT_DIGITS,
            MAX_TOTAL_COUNT_BITS,
            MAX_REPORT_INTEGER_DIGITS,
            MAX_JSON_INTEGER_DIGITS,
            MAX_DYADIC_EXPONENT_ABS,
            MAX_FIXED_POINT_BITS,
            MAX_TERMS_PER_EXPRESSION,
            MAX_CUMULATIVE_EXTRACTION_TERMS,
            MAX_CANONICAL_PAYLOAD_BYTES,
            MAX_SOURCE_MANIFEST_MEMBER_BYTES,
            MAX_SOURCE_MANIFEST_BYTES,
            MAX_VERIFIER_SOURCE_BYTES,
        ],
        "fixed_point_precisions": list(FIXED_POINT_PRECISIONS),
        "node_ids": list(NODE_IDS),
        "atom_ids": list(ATOM_IDS),
        "component_ids": list(COMPONENT_IDS),
        "mobius": [list(row) for row in MOBIUS],
        "zeta": [list(row) for row in ZETA],
        "lattice": LATTICE_VALUE,
        "precision_policy": PRECISION_POLICY_VALUE,
        "arithmetic": ARITHMETIC_VALUE,
        "locked_registry_packages": LOCKED_REGISTRY_PACKAGES,
        "tool_binding": TOOL_BINDING_STATIC_VALUE,
        "build_context_schema": BUILD_CONTEXT_SCHEMA,
        "build_context_scope": BUILD_CONTEXT_SCOPE,
        "native_cache_policies": list(NATIVE_CACHE_POLICIES),
        "permitted_claim": PERMITTED_CLAIM,
        "excluded_claims": EXCLUDED_CLAIMS,
        "source_manifest_files": list(SOURCE_MANIFEST_FILES),
        "source_manifest_domain_hex": SOURCE_MANIFEST_DOMAIN.hex(),
        "regular_expressions": [
            [TOKEN_RE.pattern, TOKEN_RE.flags],
            [CANONICAL_UNSIGNED_RE.pattern, CANONICAL_UNSIGNED_RE.flags],
            [CANONICAL_POSITIVE_RE.pattern, CANONICAL_POSITIVE_RE.flags],
            [CANONICAL_SIGNED_RE.pattern, CANONICAL_SIGNED_RE.flags],
            [LOWER_HEX_RE.pattern, LOWER_HEX_RE.flags],
        ],
    }
    constant_bytes = canonical_json_bytes(semantic_constants)
    digest.update(len(constant_bytes).to_bytes(8, "big"))
    digest.update(constant_bytes)
    return digest.hexdigest()


def _assert_verifier_integrity() -> tuple[str, str]:
    """Reject source replacement or live execution-state mutation after module load."""

    current_source = _stable_regular_file_bytes(
        _VERIFIER_SOURCE_PATH, MAX_VERIFIER_SOURCE_BYTES, "independent verifier source"
    )
    if current_source != _INITIAL_VERIFIER_SOURCE_BYTES:
        raise VerificationError(
            "independent verifier source changed after the module was loaded"
        )
    current_execution_sha256 = _loaded_execution_sha256()
    if current_execution_sha256 != _INITIAL_LOADED_EXECUTION_SHA256:
        raise VerificationError(
            "independent verifier loaded execution changed after module initialization"
        )
    return _INITIAL_VERIFIER_SOURCE_SHA256, current_execution_sha256


def verify_certificate(
    input_raw: bytes, certificate_raw: bytes, certifier_root: Path
) -> VerificationResult:
    verifier_source_sha256, verifier_loaded_execution_sha256 = (
        _assert_verifier_integrity()
    )
    data = validate_input(input_raw)
    coordinates = reconstruct_coordinates(data)
    payload, checked, source_manifest_before = _validate_certificate_structure(
        certificate_raw, data, coordinates, certifier_root
    )
    bits, independent = _prove_containment(checked)
    source_manifest_after = source_manifest_digest(certifier_root)
    _require_equal(
        source_manifest_after,
        source_manifest_before,
        "local certifier source manifest stability",
    )
    verifier_source_after, verifier_loaded_execution_after = (
        _assert_verifier_integrity()
    )
    _require_equal(
        verifier_source_after,
        verifier_source_sha256,
        "independent verifier observed-source stability",
    )
    _require_equal(
        verifier_loaded_execution_after,
        verifier_loaded_execution_sha256,
        "independent verifier loaded-execution stability",
    )
    maximum_independent_width = max(
        (upper - lower for lower, upper in independent.values()), default=Fraction(0)
    )
    report = {
        "schema": VERIFICATION_SCHEMA,
        "status": "verified",
        "route": "independent_integer_rational_log_containment",
        "definition_revision": DEFINITION_REVISION,
        "units": UNITS,
        "input_sha256": data.raw_sha256,
        "certificate_sha256": sha256_hex(certificate_raw),
        "certificate_payload_sha256": canonical_digest(payload),
        "certifier_source_manifest_sha256": source_manifest_after,
        "verifier_source_sha256": verifier_source_sha256,
        "verifier_loaded_execution_sha256": verifier_loaded_execution_sha256,
        "python_runtime": {
            "implementation": sys.implementation.name,
            "version_info": [
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
                sys.version_info.releaselevel,
                sys.version_info.serial,
            ],
            "cache_tag": sys.implementation.cache_tag,
            "bits_per_digit": sys.int_info.bits_per_digit,
            "sizeof_digit": sys.int_info.sizeof_digit,
            "integer_text_max_digits": _python_integer_text_limit(),
            "hash_name": "sha256",
        },
        "coordinates_reconstructed": 24,
        "coordinate_term_lists_matched": 24,
        "dyadic_containments_proved": 24,
        "independent_direct_mi_identities_checked": 3,
        "fixed_point_precision_bits": bits,
        "maximum_independent_width": _rational_object(maximum_independent_width),
        "log_proof": {
            "range_reduction": "x=2^e*y_with_1<=y<2",
            "series": "ln(y)=2*sum_{k>=0}z^(2k+1)/(2k+1),z=(y-1)/(y+1)",
            "tail_bound": "tail<=9*z^(2m+1)/(4*(2m+1))_because_0<=z<=1/3",
            "rounding": "exact_integer_fixed_point_outward",
        },
        "trust_boundary": {
            "trusted": [
                "observed_verifier_source_and_loaded_execution",
                "python_source_loader_bytecode_compiler_and_process_integrity",
                "python_arbitrary_precision_integer_and_fraction_semantics",
                "python_json_utf8_and_sha256_implementations",
                "reviewed_log_series_and_tail_bound",
                "local_certifier_source_bytes_named_by_the_manifest",
            ],
            "not_trusted_for_containment": [
                "certificate_exact_terms",
                "certificate_lattice",
                "certificate_sign_decisions",
                "rug",
                "mpfr",
                "gmp",
                "rust_compiler",
                "certifier_executable",
            ],
            "excluded_claims": [
                "pid-core_binary64_correctness",
                "input_authenticity_or_scientific_meaning",
                "population_or_sampling_assumptions",
                "estimator_consistency_or_calibration",
                "continuous_or_higher_source_pid",
                "downstream_application_validity",
                "formal_verification_of_python_or_this_checker",
            ],
        },
    }
    return VerificationResult(report)


def _read_bounded(path: Path, maximum: int, label: str) -> bytes:
    try:
        with path.open("rb") as handle:
            raw = handle.read(maximum + 1)
    except OSError as error:
        raise VerificationError(f"cannot read {label} {path}: {error}") from error
    if len(raw) > maximum:
        raise VerificationError(f"{label} exceeds {maximum} bytes")
    return raw


def _safe_error_message(error: VerificationError) -> str:
    """Return a bounded ASCII error string suitable for the canonical JSON envelope."""

    try:
        text = str(error)
    except (
        Exception
    ):  # pragma: no cover - defensive against a malformed exception object.
        text = "verification failed with an unprintable error"
    encoded = text.encode("ascii", errors="backslashreplace")
    return encoded[:8192].decode("ascii")


def _arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independently reconstruct exact categorical SxPID2 expressions and prove that a "
            "certifier report's dyadic intervals contain them."
        )
    )
    parser.add_argument("input", type=Path, help="canonical exact count-table JSON")
    parser.add_argument("certificate", type=Path, help="certifier JSON output")
    parser.add_argument(
        "--certifier-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="reviewed standalone certifier source root (default: inferred from this script)",
    )
    return parser.parse_args(argv)


def _write_stdout_document(document: Mapping[str, Any]) -> bool:
    """Write and flush one canonical JSON line, returning false on transport failure."""

    try:
        sys.stdout.buffer.write(canonical_json_bytes(document) + b"\n")
        sys.stdout.buffer.flush()
    except (OSError, ValueError):
        # Prevent a second flush of the failed stream during interpreter shutdown from
        # replacing the deliberate transport-failure status with CPython's status 120.
        try:
            null_fd = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(null_fd, sys.stdout.fileno())
            finally:
                os.close(null_fd)
        except (OSError, ValueError):
            pass
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(sys.argv[1:] if argv is None else argv)
    try:
        input_raw = _read_bounded(arguments.input, MAX_INPUT_BYTES, "count table")
        certificate_raw = _read_bounded(
            arguments.certificate, MAX_CERTIFICATE_BYTES, "certificate"
        )
        result = verify_certificate(
            input_raw, certificate_raw, arguments.certifier_root.resolve()
        )
    except VerificationError as error:
        failure = {
            "schema": VERIFICATION_SCHEMA,
            "status": "rejected",
            "message": _safe_error_message(error),
        }
        return 2 if _write_stdout_document(failure) else 1
    return 0 if _write_stdout_document(result.report) else 1


_INITIAL_LOADED_EXECUTION_SHA256: Final = _loaded_execution_sha256()


if __name__ == "__main__":
    raise SystemExit(main())
