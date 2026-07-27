#!/usr/bin/env python3
"""Independently replay the bounded KSG integer-harmonic modular certificate.

The checker does not import the generator.  It reconstructs the fixture row
sequence, uses deterministic Miller--Rabin primality checks, obtains modular
inverses through a batch-product/extended-Euclid route, and rebuilds every
u32-big-endian residue digest.

Success establishes an exact zero/nonzero classification only for the frozen
8,198 rows.  The three selected fields are redundant checks; they are not used
as a CRT theorem and do not classify harmonic zeros outside the corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = (
    ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
)
DEFAULT_GENERATOR = (
    ROOT / "scripts/generate-ksg-harmonic-modular-certificate.py"
)
DEFAULT_CERTIFICATE = (
    ROOT
    / "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    / "ksg-harmonic-modular-certificate-v1.json"
)
DEFAULT_SIDECAR = DEFAULT_CERTIFICATE.with_suffix(
    DEFAULT_CERTIFICATE.suffix + ".sha256"
)

SCHEMA = "pid-rs/ksg-harmonic-modular-certificate"
SCHEMA_REVISION = 1
CLAIM_ID = "KSG-INTEGER-HARMONIC-001"
CERTIFICATE_REVISION = 1
FIXTURE_PATH = "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
FIXTURE_SCHEMA_REVISION = 2
GENERATOR_PATH = "scripts/generate-ksg-harmonic-modular-certificate.py"

EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_GENERATOR_SHA256 = (
    "969c4a5a5a8f6a9054de0154a331824bf2034223c30cb3a76f5e975f6f68a1c3"
)
EXPECTED_CERTIFICATE_SHA256 = (
    "5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f"
)
PRE_ARTIFACT_OBSERVATION_SHA256 = (
    "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc"
)

EXHAUSTIVE_ROW_COUNT = 6_920
STRESS_ROW_COUNT = 1_278
ROW_COUNT = 8_198
EXHAUSTIVE_ENDPOINT_COUNT = 240
STRESS_ENDPOINT_COUNT = 114
ENDPOINT_COUNT = 354
NONENDPOINT_COUNT = 7_844
MAXIMUM_RECIPROCAL_SUMMAND_INDEX = 999_999
SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)
REJECTED_PRIME = 1_000_003
EXPECTED_RESIDUE_DIGESTS = {
    1_000_033: "931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b",
    1_000_037: "09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479",
    1_000_081: "20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0",
    1_000_003: "d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111",
}
EXPECTED_REJECTED_COLLISION_INDICES = (8_045, 8_049, 8_069, 8_093)
STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)


class CheckError(RuntimeError):
    """The certificate, its custody, or its independently replayed result failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def require_strict_json_equal(
    actual: object,
    expected: object,
    label: str,
    *,
    path: str = "$",
) -> None:
    """Compare JSON values without Python's bool/int/float coercions."""

    require(
        type(actual) is type(expected),
        f"{label} has the wrong JSON type at {path}: "
        f"expected {type(expected).__name__}, observed {type(actual).__name__}",
    )
    if isinstance(expected, dict):
        actual_dict = cast(dict[str, object], actual)
        expected_dict = cast(dict[str, object], expected)
        require(
            set(actual_dict) == set(expected_dict),
            f"{label} object keys changed at {path}",
        )
        for key, expected_value in expected_dict.items():
            require_strict_json_equal(
                actual_dict[key],
                expected_value,
                label,
                path=f"{path}/{key}",
            )
        return
    if isinstance(expected, list):
        actual_list = cast(list[object], actual)
        expected_list = cast(list[object], expected)
        require(
            len(actual_list) == len(expected_list),
            f"{label} array length changed at {path}",
        )
        for index, (actual_value, expected_value) in enumerate(
            zip(actual_list, expected_list, strict=True)
        ):
            require_strict_json_equal(
                actual_value,
                expected_value,
                label,
                path=f"{path}/{index}",
            )
        return
    require(actual == expected, f"{label} value changed at {path}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


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
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        canonical = canonical_json_bytes(value)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise CheckError(
            f"{label} is not finite canonical UTF-8 JSON: {error}"
        ) from error
    require(isinstance(value, dict), f"{label} top level is not an object")
    require(raw == canonical, f"{label} is not canonical JSON")
    return value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_prime_miller_rabin(value: int) -> bool:
    """Deterministic for the u32 moduli admitted by this certificate."""

    if value < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small_primes:
        if value % prime == 0:
            return value == prime

    odd_part = value - 1
    power_of_two = 0
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1
    for base in (2, 3, 5, 7, 11):
        if base >= value:
            continue
        witness = pow(base, odd_part, value)
        if witness in (1, value - 1):
            continue
        for _ in range(power_of_two - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


def inverse_extended_euclid(value: int, modulus: int) -> int:
    old_remainder, remainder = modulus, value
    old_coefficient, coefficient = 0, 1
    while remainder:
        quotient = old_remainder // remainder
        old_remainder, remainder = (
            remainder,
            old_remainder - quotient * remainder,
        )
        old_coefficient, coefficient = (
            coefficient,
            old_coefficient - quotient * coefficient,
        )
    require(old_remainder == 1, f"{value} is not invertible modulo {modulus}")
    return old_coefficient % modulus


def harmonic_prefix_batch(prime: int, maximum: int) -> list[int]:
    """Use one Euclidean inverse plus a product sweep, unlike the generator."""

    require(0 < prime < 2**32, f"modulus {prime} is outside the u32 range")
    require(is_prime_miller_rabin(prime), f"modulus {prime} is composite")
    require(
        maximum < prime,
        f"modulus {prime} is not above every denominator through {maximum}",
    )

    products = [1] * (maximum + 1)
    for denominator in range(1, maximum + 1):
        products[denominator] = (
            products[denominator - 1] * denominator
        ) % prime
    inverse_product = inverse_extended_euclid(products[maximum], prime)
    for denominator in range(maximum, 0, -1):
        inverse_denominator = (
            products[denominator - 1] * inverse_product
        ) % prime
        inverse_product = inverse_product * denominator % prime
        products[denominator] = inverse_denominator
    products[0] = 0

    total = 0
    for denominator in range(1, maximum + 1):
        total = (total + products[denominator]) % prime
        products[denominator] = total
    return products


def reconstruct_rows_independently() -> list[tuple[int, int, int, int]]:
    rows: list[tuple[int, int, int, int]] = []
    sample_count = 2
    while sample_count <= 16:
        k = 1
        while k < sample_count:
            x_count = k - 1
            while x_count < sample_count:
                y_count = k - 1
                while y_count < sample_count:
                    rows.append((sample_count, k, x_count, y_count))
                    y_count += 1
                x_count += 1
            k += 1
        sample_count += 1
    require(
        len(rows) == EXHAUSTIVE_ROW_COUNT,
        "independent exhaustive reconstruction count drifted",
    )

    for sample_count in STRESS_SAMPLE_SIZES:
        candidates = (
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
        k_values = list(dict.fromkeys(sorted(candidates)))
        k_values = [value for value in k_values if 1 <= value < sample_count]
        for k in k_values:
            candidates_for_count = (
                k - 1,
                k if k < sample_count else sample_count - 1,
                (k + sample_count - 1) // 2,
                sample_count - 2,
                sample_count - 1,
            )
            count_values = list(dict.fromkeys(sorted(candidates_for_count)))
            rows.extend(
                (sample_count, k, x_count, y_count)
                for x_count in count_values
                for y_count in count_values
            )
    require(len(rows) == ROW_COUNT, "independent total row reconstruction drifted")
    require(len(set(rows)) == ROW_COUNT, "independent row reconstruction has duplicates")
    return rows


def endpoint_from_multiset(row: tuple[int, int, int, int]) -> bool:
    sample_count, k, x_count, y_count = row
    return sorted((x_count, y_count)) == [k - 1, sample_count - 1]


def read_fixture_rows(raw: bytes) -> tuple[dict[str, Any], list[tuple[int, int, int, int]]]:
    fixture = parse_canonical_json(raw, "fixture")
    require(fixture.get("schema") == FIXTURE_SCHEMA, "fixture schema drifted")
    require_strict_json_equal(
        fixture.get("schema_revision"),
        FIXTURE_SCHEMA_REVISION,
        "fixture schema revision",
    )
    require(
        fixture.get("arithmetic", {}).get("exact_identity")
        == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity drifted",
    )
    cases = fixture.get("cases")
    require(isinstance(cases, list), "fixture cases are not an array")
    require(len(cases) == ROW_COUNT, "fixture row count drifted")

    rows: list[tuple[int, int, int, int]] = []
    for index, case in enumerate(cases):
        require(isinstance(case, dict), f"fixture row {index} is not an object")
        require(
            set(case)
            == {"expected_nats", "k", "sample_count", "x_count", "y_count"},
            f"fixture row {index} fields drifted",
        )
        row = (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        require(
            all(type(component) is int for component in row),
            f"fixture row {index} contains a non-integer argument",
        )
        sample_count, k, x_count, y_count = row
        require(
            2 <= sample_count
            and 1 <= k < sample_count
            and k - 1 <= x_count < sample_count
            and k - 1 <= y_count < sample_count,
            f"fixture row {index} violates the count domain",
        )
        require(
            isinstance(case["expected_nats"], str),
            f"fixture row {index} expected_nats is not text",
        )
        if endpoint_from_multiset(row):
            require(
                case["expected_nats"] == "0",
                f"fixture endpoint row {index} is not canonical exact zero",
            )
        rows.append(row)

    require(
        rows == reconstruct_rows_independently(),
        "fixture row order or argument set differs from independent reconstruction",
    )
    endpoint_split = (
        sum(endpoint_from_multiset(row) for row in rows[:EXHAUSTIVE_ROW_COUNT]),
        sum(endpoint_from_multiset(row) for row in rows[EXHAUSTIVE_ROW_COUNT:]),
    )
    require(
        endpoint_split == (EXHAUSTIVE_ENDPOINT_COUNT, STRESS_ENDPOINT_COUNT),
        f"fixture endpoint split drifted: {endpoint_split!r}",
    )
    maximum = max(
        max(k - 1, sample_count - 1, x_count, y_count)
        for sample_count, k, x_count, y_count in rows
    )
    require(
        maximum == MAXIMUM_RECIPROCAL_SUMMAND_INDEX,
        "fixture maximum reciprocal summand index drifted",
    )
    return fixture, rows


def residue_vector(
    rows: list[tuple[int, int, int, int]], prime: int
) -> list[int]:
    harmonics = harmonic_prefix_batch(prime, MAXIMUM_RECIPROCAL_SUMMAND_INDEX)
    residues: list[int] = []
    for sample_count, k, x_count, y_count in rows:
        residues.append(
            (
                harmonics[k - 1]
                + harmonics[sample_count - 1]
                - harmonics[x_count]
                - harmonics[y_count]
            )
            % prime
        )
    return residues


def u32be_digest(residues: list[int]) -> str:
    encoded = bytearray(4 * len(residues))
    cursor = 0
    for residue in residues:
        require(0 <= residue < 2**32, "residue is not an unsigned 32-bit value")
        encoded[cursor : cursor + 4] = residue.to_bytes(
            4, byteorder="big", signed=False
        )
        cursor += 4
    return sha256(bytes(encoded))


def classification_counts(
    rows: list[tuple[int, int, int, int]],
    residues: list[int],
    start: int,
    stop: int,
) -> dict[str, int]:
    require(len(rows) == len(residues), "row/residue vector length mismatch")
    buckets = {
        (True, True): 0,
        (True, False): 0,
        (False, True): 0,
        (False, False): 0,
    }
    for index in range(start, stop):
        endpoint = endpoint_from_multiset(rows[index])
        zero = residues[index] == 0
        buckets[(endpoint, zero)] += 1
    return {
        "endpoint_count": buckets[(True, True)] + buckets[(True, False)],
        "endpoint_nonzero_count": buckets[(True, False)],
        "endpoint_zero_count": buckets[(True, True)],
        "nonendpoint_count": buckets[(False, True)] + buckets[(False, False)],
        "nonendpoint_nonzero_count": buckets[(False, False)],
        "nonendpoint_zero_count": buckets[(False, True)],
        "row_count": stop - start,
    }


def all_counts(
    rows: list[tuple[int, int, int, int]], residues: list[int]
) -> dict[str, dict[str, int]]:
    return {
        "exhaustive": classification_counts(
            rows, residues, 0, EXHAUSTIVE_ROW_COUNT
        ),
        "stress": classification_counts(
            rows, residues, EXHAUSTIVE_ROW_COUNT, ROW_COUNT
        ),
        "total": classification_counts(rows, residues, 0, ROW_COUNT),
    }


def exact_collision_witness(
    index: int, row: tuple[int, int, int, int]
) -> dict[str, Any]:
    sample_count, k, x_count, y_count = row
    coefficients: dict[int, int] = {}
    for harmonic_index, coefficient in (
        (k - 1, 1),
        (sample_count - 1, 1),
        (x_count, -1),
        (y_count, -1),
    ):
        coefficients[harmonic_index] = (
            coefficients.get(harmonic_index, 0) + coefficient
        )
    coefficients = {
        harmonic_index: coefficient
        for harmonic_index, coefficient in coefficients.items()
        if coefficient != 0
    }
    require(
        sorted(coefficients.values()) == [-1, 1],
        f"collision row {index} does not reduce to one harmonic difference",
    )
    positive_index = next(
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == 1
    )
    negative_index = next(
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == -1
    )
    require(
        positive_index != negative_index,
        f"collision row {index} is structurally exact zero",
    )
    sign = "positive" if positive_index > negative_index else "negative"
    lower = min(positive_index, negative_index)
    upper = max(positive_index, negative_index)
    tail_coefficient = 1 if sign == "positive" else -1
    return {
        "exact_reduction": f"H_{positive_index} - H_{negative_index}",
        "fixture_index_zero_based": index,
        "fixture_ordinal_one_based": index + 1,
        "harmonic_difference": {
            "negative_coefficient_index": negative_index,
            "positive_coefficient_index": positive_index,
        },
        "row": {
            "k": k,
            "sample_count": sample_count,
            "x_count": x_count,
            "y_count": y_count,
        },
        "sign": sign,
        "strict_nonzero_witness": {
            "exact_form": (
                f"{tail_coefficient} * sum_(j={lower + 1}..{upper}) 1/j"
            ),
            "first_denominator": lower + 1,
            "last_denominator": upper,
            "tail_coefficient": tail_coefficient,
            "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive",
        },
    }


def expected_prime_record(
    rows: list[tuple[int, int, int, int]],
    prime: int,
    selected: bool,
) -> dict[str, Any]:
    residues = residue_vector(rows, prime)
    digest = u32be_digest(residues)
    require(
        digest == EXPECTED_RESIDUE_DIGESTS[prime],
        f"replayed residue digest drifted for prime {prime}: {digest}",
    )
    counts = all_counts(rows, residues)
    collision_indices = tuple(
        index
        for index, (row, residue) in enumerate(zip(rows, residues, strict=True))
        if residue == 0 and not endpoint_from_multiset(row)
    )

    if selected:
        require(
            not collision_indices,
            f"selected prime {prime} has nonendpoint collisions",
        )
        require(
            counts["total"]["endpoint_zero_count"] == ENDPOINT_COUNT
            and counts["total"]["endpoint_nonzero_count"] == 0
            and counts["total"]["nonendpoint_zero_count"] == 0
            and counts["total"]["nonendpoint_nonzero_count"] == NONENDPOINT_COUNT,
            f"selected prime {prime} does not separately classify every row",
        )
        return {
            "classification": "selected_per_field_separator",
            "counts": counts,
            "greater_than_every_reciprocal_summand_index": True,
            "prime": prime,
            "residue_u32be_sha256": digest,
        }

    require(
        collision_indices == EXPECTED_REJECTED_COLLISION_INDICES,
        f"rejected-prime collision indices drifted: {collision_indices!r}",
    )
    require(
        counts["total"]["endpoint_zero_count"] == ENDPOINT_COUNT
        and counts["total"]["endpoint_nonzero_count"] == 0
        and counts["total"]["nonendpoint_zero_count"]
        == len(EXPECTED_REJECTED_COLLISION_INDICES)
        and counts["total"]["nonendpoint_nonzero_count"]
        == NONENDPOINT_COUNT - len(EXPECTED_REJECTED_COLLISION_INDICES),
        "rejected-prime classification counts drifted",
    )
    return {
        "classification": "rejected_nonendpoint_collision_negative_control",
        "collisions": [
            exact_collision_witness(index, rows[index])
            for index in collision_indices
        ],
        "counts": counts,
        "greater_than_every_reciprocal_summand_index": True,
        "prime": prime,
        "residue_u32be_sha256": digest,
    }


def expected_static_certificate_parts(generator_digest: str) -> dict[str, Any]:
    return {
        "certificate_revision": CERTIFICATE_REVISION,
        "claim_id": CLAIM_ID,
        "corpus": {
            "fixture": {
                "path": FIXTURE_PATH,
                "schema": FIXTURE_SCHEMA,
                "schema_revision": FIXTURE_SCHEMA_REVISION,
                "sha256": EXPECTED_FIXTURE_SHA256,
            },
            "maximum_reciprocal_summand_index": MAXIMUM_RECIPROCAL_SUMMAND_INDEX,
            "ordered_row_count": ROW_COUNT,
            "segments": [
                {
                    "end_index_exclusive": EXHAUSTIVE_ROW_COUNT,
                    "endpoint_count": EXHAUSTIVE_ENDPOINT_COUNT,
                    "name": "exhaustive",
                    "nonendpoint_count": EXHAUSTIVE_ROW_COUNT
                    - EXHAUSTIVE_ENDPOINT_COUNT,
                    "row_count": EXHAUSTIVE_ROW_COUNT,
                    "start_index_inclusive": 0,
                },
                {
                    "end_index_exclusive": ROW_COUNT,
                    "endpoint_count": STRESS_ENDPOINT_COUNT,
                    "name": "stress",
                    "nonendpoint_count": STRESS_ROW_COUNT - STRESS_ENDPOINT_COUNT,
                    "row_count": STRESS_ROW_COUNT,
                    "start_index_inclusive": EXHAUSTIVE_ROW_COUNT,
                },
            ],
        },
        "generator": {
            "algorithm": "linear modular-inverse recurrence followed by harmonic prefix accumulation",
            "imports_pid_rs": False,
            "path": GENERATOR_PATH,
            "sha256": generator_digest,
            "third_party_dependencies": [],
        },
        "limitations": [
            "the iff classification is limited to the exact ordered 8,198-row frozen corpus",
            "the selected triple is redundant fault diversity, not a CRT or universal-zero theorem",
            "a zero residue alone does not prove that an exact rational is zero",
            "the route proves no estimator consistency, support, bias, PID-atom, or application claim",
            "generator/checker diversity is internal evidence, not independent external review",
        ],
        "pre_artifact_observation": {
            "sha256": PRE_ARTIFACT_OBSERVATION_SHA256,
            "status": "historical_first_result_only_not_final_artifact_custody",
        },
        "residue_encoding": {
            "byte_order": "big_endian",
            "digest_algorithm": "sha256",
            "include_zero_residues": True,
            "row_order": "exact_fixture_array_order",
            "signed": False,
            "word_bits": 32,
        },
        "schema": SCHEMA,
        "schema_revision": SCHEMA_REVISION,
        "statement": {
            "classification": (
                "for every frozen corpus row, the exact rational T is zero "
                "if and only if the row is a structural endpoint"
            ),
            "exact_term": "T = H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
            "nonendpoint_route": (
                "for each selected prime separately, a nonzero residue and invertible "
                "denominators imply the exact rational is nonzero"
            ),
            "residue_implication_direction": (
                "nonzero_modular_residue_implies_exact_rational_nonzero"
            ),
            "selected_prime_set_role": "redundant_fault_diversity_only_not_crt",
            "structural_endpoint_predicate": (
                "(nx == k-1 and ny == n-1) or (nx == n-1 and ny == k-1)"
            ),
            "structural_endpoint_route": (
                "the four exact harmonic terms cancel pairwise before field reduction"
            ),
            "zero_residue_nonimplication": (
                "zero_modular_residue_does_not_imply_exact_rational_zero"
            ),
        },
    }


def check(
    fixture_path: Path,
    generator_path: Path,
    certificate_path: Path,
    sidecar_path: Path,
) -> dict[str, Any]:
    fixture_raw = fixture_path.read_bytes()
    generator_raw = generator_path.read_bytes()
    certificate_raw = certificate_path.read_bytes()
    sidecar_text = sidecar_path.read_text(encoding="utf-8")

    fixture_digest = sha256(fixture_raw)
    generator_digest = sha256(generator_raw)
    certificate_digest = sha256(certificate_raw)
    require(
        fixture_digest == EXPECTED_FIXTURE_SHA256,
        f"fixture SHA-256 custody mismatch: {fixture_digest}",
    )
    require(
        generator_digest == EXPECTED_GENERATOR_SHA256,
        f"generator SHA-256 custody mismatch: {generator_digest}",
    )
    require(
        certificate_digest == EXPECTED_CERTIFICATE_SHA256,
        f"certificate SHA-256 custody mismatch: {certificate_digest}",
    )
    expected_sidecar = f"{certificate_digest}  {certificate_path.name}\n"
    require(sidecar_text == expected_sidecar, "certificate sidecar is stale or malformed")

    certificate = parse_canonical_json(certificate_raw, "certificate")
    _fixture, rows = read_fixture_rows(fixture_raw)

    static_parts = expected_static_certificate_parts(generator_digest)
    require(
        set(certificate)
        == set(static_parts)
        | {"selected_prime_certificates", "rejected_prime_negative_control"},
        "certificate top-level fields drifted",
    )
    for field, expected in static_parts.items():
        require_strict_json_equal(
            certificate.get(field),
            expected,
            f"certificate {field!r} drifted",
        )

    selected_records = certificate.get("selected_prime_certificates")
    require(isinstance(selected_records, list), "selected-prime records are not an array")
    require(
        len(selected_records) == len(SELECTED_PRIMES),
        "selected-prime record count drifted",
    )
    observed_selected_primes = tuple(
        record.get("prime") if isinstance(record, dict) else None
        for record in selected_records
    )
    require(
        observed_selected_primes == SELECTED_PRIMES,
        f"selected-prime order or membership drifted: {observed_selected_primes!r}",
    )
    require(
        len(set(observed_selected_primes)) == len(SELECTED_PRIMES),
        "selected-prime records contain a duplicate",
    )

    expected_selected = [
        expected_prime_record(rows, prime, selected=True)
        for prime in SELECTED_PRIMES
    ]
    require_strict_json_equal(
        selected_records,
        expected_selected,
        "selected-prime certificate records differ from independent replay",
    )

    rejected_record = certificate.get("rejected_prime_negative_control")
    require(
        isinstance(rejected_record, dict),
        "rejected-prime negative control is not an object",
    )
    require(
        rejected_record.get("prime") == REJECTED_PRIME,
        "rejected-prime identity drifted",
    )
    require(
        REJECTED_PRIME not in observed_selected_primes,
        "rejected prime was promoted into the selected set",
    )
    expected_rejected = expected_prime_record(rows, REJECTED_PRIME, selected=False)
    require_strict_json_equal(
        rejected_record,
        expected_rejected,
        "rejected-prime negative control differs from independent replay",
    )

    # The exact implication is one-way at the field boundary.  Endpoints are
    # zero by symbolic cancellation.  Nonendpoints are exact-nonzero because
    # each selected lane has a nonzero residue while all denominators are
    # invertible.  The rejected zero collisions demonstrate why the converse
    # "zero residue => exact zero" must not be used.
    for record in expected_selected:
        total = record["counts"]["total"]
        require(
            total["endpoint_zero_count"] == ENDPOINT_COUNT
            and total["nonendpoint_nonzero_count"] == NONENDPOINT_COUNT,
            "corpus-scoped iff implication did not close",
        )
    require(
        len(expected_rejected["collisions"])
        == len(EXPECTED_REJECTED_COLLISION_INDICES),
        "rejected-prime zero-residue counterexample disappeared",
    )

    return {
        "certificate_sha256": certificate_digest,
        "endpoint_split": {
            "exhaustive": EXHAUSTIVE_ENDPOINT_COUNT,
            "stress": STRESS_ENDPOINT_COUNT,
            "total": ENDPOINT_COUNT,
        },
        "nonendpoint_count": NONENDPOINT_COUNT,
        "rejected_prime_collision_count": len(EXPECTED_REJECTED_COLLISION_INDICES),
        "row_count": ROW_COUNT,
        "selected_prime_count": len(SELECTED_PRIMES),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--certificate", type=Path, default=DEFAULT_CERTIFICATE)
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = check(
            args.fixture,
            args.generator,
            args.certificate,
            args.sidecar,
        )
    except (OSError, UnicodeError, CheckError) as error:
        print(f"KSG modular certificate check error: {error}", file=sys.stderr)
        return 1
    print(
        "OK: bounded modular certificate replayed "
        f"{result['row_count']} rows; endpoints "
        f"{result['endpoint_split']['total']} "
        f"({result['endpoint_split']['exhaustive']}/"
        f"{result['endpoint_split']['stress']}), nonendpoints "
        f"{result['nonendpoint_count']} nonzero in each of "
        f"{result['selected_prime_count']} selected fields; rejected collisions "
        f"{result['rejected_prime_collision_count']}; certificate SHA-256 "
        f"{result['certificate_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
