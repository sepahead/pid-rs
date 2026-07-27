#!/usr/bin/env python3
"""Generate the bounded modular certificate for the frozen KSG harmonic corpus.

This standard-library-only route is deliberately narrow.  It reduces

    H_(k-1) + H_(n-1) - H_(nx) - H_(ny)

in four prime fields for the exact 8,198 rows of the schema-2 arithmetic
fixture.  Each of three prime fields separately separates every structural
endpoint from every nonendpoint.  A fourth prime is retained because four
exact-nonzero rows collide with zero in that field.

The result is a corpus certificate, not a universal harmonic-zero theorem.
The selected primes are redundant fault-diversity lanes, not independent
proofs or a CRT argument.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
OUTPUT = (
    ROOT
    / "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    / "ksg-harmonic-modular-certificate-v1.json"
)
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")

SCHEMA = "pid-rs/ksg-harmonic-modular-certificate"
SCHEMA_REVISION = 1
CLAIM_ID = "KSG-INTEGER-HARMONIC-001"
CERTIFICATE_REVISION = 1

FIXTURE_PATH = "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
FIXTURE_SCHEMA_REVISION = 2
EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
GENERATOR_PATH = "scripts/generate-ksg-harmonic-modular-certificate.py"

EXHAUSTIVE_ROW_COUNT = 6_920
STRESS_ROW_COUNT = 1_278
ROW_COUNT = EXHAUSTIVE_ROW_COUNT + STRESS_ROW_COUNT
EXHAUSTIVE_ENDPOINT_COUNT = 240
STRESS_ENDPOINT_COUNT = 114
ENDPOINT_COUNT = EXHAUSTIVE_ENDPOINT_COUNT + STRESS_ENDPOINT_COUNT
NONENDPOINT_COUNT = ROW_COUNT - ENDPOINT_COUNT
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
PRE_ARTIFACT_OBSERVATION_SHA256 = (
    "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc"
)

STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)


class CertificateError(RuntimeError):
    """The corpus or generated finite-field certificate is inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CertificateError(message)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON key: {key!r}")
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


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    for divisor in range(3, math.isqrt(value) + 1, 2):
        if value % divisor == 0:
            return False
    return True


def row_tuple(case: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        case["sample_count"],
        case["k"],
        case["x_count"],
        case["y_count"],
    )


def is_structural_endpoint(row: tuple[int, int, int, int]) -> bool:
    sample_count, k, x_count, y_count = row
    return (x_count, y_count) in (
        (k - 1, sample_count - 1),
        (sample_count - 1, k - 1),
    )


def expected_rows() -> list[tuple[int, int, int, int]]:
    rows = [
        (sample_count, k, x_count, y_count)
        for sample_count in range(2, 17)
        for k in range(1, sample_count)
        for x_count in range(k - 1, sample_count)
        for y_count in range(k - 1, sample_count)
    ]
    require(len(rows) == EXHAUSTIVE_ROW_COUNT, "exhaustive row count drifted")

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
                    rows.append((sample_count, k, x_count, y_count))
    require(len(rows) == ROW_COUNT, "total row count drifted")
    require(len(set(rows)) == ROW_COUNT, "fixture argument rows are not unique")
    return rows


def read_frozen_fixture(path: Path) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(
        digest == EXPECTED_FIXTURE_SHA256,
        f"fixture custody mismatch: expected {EXPECTED_FIXTURE_SHA256}, observed {digest}",
    )
    value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    require(raw == canonical_json_bytes(value), "fixture is not canonical JSON")
    require(value.get("schema") == FIXTURE_SCHEMA, "fixture schema drifted")
    require(
        value.get("schema_revision") == FIXTURE_SCHEMA_REVISION,
        "fixture schema revision drifted",
    )
    require(
        value.get("arithmetic", {}).get("exact_identity")
        == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity drifted",
    )
    cases = value.get("cases")
    require(isinstance(cases, list), "fixture cases are not an array")
    require(len(cases) == ROW_COUNT, "fixture row count drifted")

    observed_rows: list[tuple[int, int, int, int]] = []
    for index, case in enumerate(cases):
        require(isinstance(case, dict), f"fixture row {index} is not an object")
        require(
            set(case)
            == {"expected_nats", "k", "sample_count", "x_count", "y_count"},
            f"fixture row {index} fields drifted",
        )
        row = row_tuple(case)
        sample_count, k, x_count, y_count = row
        require(
            all(
                isinstance(component, int) and not isinstance(component, bool)
                for component in row
            ),
            f"fixture row {index} has a non-integer argument",
        )
        require(
            2 <= sample_count
            and 1 <= k < sample_count
            and k - 1 <= x_count < sample_count
            and k - 1 <= y_count < sample_count,
            f"fixture row {index} violates the declared count domain",
        )
        require(
            isinstance(case["expected_nats"], str),
            f"fixture row {index} expected_nats is not text",
        )
        if is_structural_endpoint(row):
            require(
                case["expected_nats"] == "0",
                f"fixture endpoint row {index} is not canonical exact zero",
            )
        observed_rows.append(row)

    require(observed_rows == expected_rows(), "fixture row order or argument set drifted")
    endpoint_counts = (
        sum(is_structural_endpoint(row) for row in observed_rows[:EXHAUSTIVE_ROW_COUNT]),
        sum(is_structural_endpoint(row) for row in observed_rows[EXHAUSTIVE_ROW_COUNT:]),
    )
    require(
        endpoint_counts == (EXHAUSTIVE_ENDPOINT_COUNT, STRESS_ENDPOINT_COUNT),
        "fixture endpoint split drifted",
    )
    maximum = max(
        max(k - 1, sample_count - 1, x_count, y_count)
        for sample_count, k, x_count, y_count in observed_rows
    )
    require(
        maximum == MAXIMUM_RECIPROCAL_SUMMAND_INDEX,
        "maximum reciprocal summand index drifted",
    )
    return raw, value, cases


def harmonic_prefix_recurrence(prime: int, maximum: int) -> list[int]:
    """Build H_0..H_max modulo prime using the linear inverse recurrence."""

    require(is_prime(prime), f"modulus {prime} is not prime")
    require(
        maximum < prime,
        f"modulus {prime} does not invert every denominator through {maximum}",
    )
    values = [0] * (maximum + 1)
    if maximum == 0:
        return values
    values[1] = 1
    for denominator in range(2, maximum + 1):
        values[denominator] = (
            prime
            - (prime // denominator) * values[prime % denominator] % prime
        )
    total = 0
    for denominator in range(1, maximum + 1):
        total = (total + values[denominator]) % prime
        values[denominator] = total
    return values


def residues_for_prime(
    cases: list[dict[str, Any]], prime: int
) -> tuple[list[int], list[tuple[int, dict[str, Any]]]]:
    harmonics = harmonic_prefix_recurrence(
        prime, MAXIMUM_RECIPROCAL_SUMMAND_INDEX
    )
    residues: list[int] = []
    collisions: list[tuple[int, dict[str, Any]]] = []
    for index, case in enumerate(cases):
        sample_count, k, x_count, y_count = row_tuple(case)
        residue = (
            harmonics[k - 1]
            + harmonics[sample_count - 1]
            - harmonics[x_count]
            - harmonics[y_count]
        ) % prime
        residues.append(residue)
        if residue == 0 and not is_structural_endpoint(row_tuple(case)):
            collisions.append((index, case))
    return residues, collisions


def residue_digest(residues: list[int]) -> str:
    digest = hashlib.sha256()
    for residue in residues:
        require(0 <= residue < 2**32, "residue does not fit unsigned 32-bit encoding")
        digest.update(residue.to_bytes(4, byteorder="big", signed=False))
    return digest.hexdigest()


def split_counts(
    cases: list[dict[str, Any]], residues: list[int], start: int, end: int
) -> dict[str, int]:
    require(len(cases) == len(residues), "row/residue length mismatch")
    endpoint_zero = 0
    endpoint_nonzero = 0
    nonendpoint_zero = 0
    nonendpoint_nonzero = 0
    for case, residue in zip(cases[start:end], residues[start:end], strict=True):
        if is_structural_endpoint(row_tuple(case)):
            if residue == 0:
                endpoint_zero += 1
            else:
                endpoint_nonzero += 1
        elif residue == 0:
            nonendpoint_zero += 1
        else:
            nonendpoint_nonzero += 1
    return {
        "endpoint_count": endpoint_zero + endpoint_nonzero,
        "endpoint_nonzero_count": endpoint_nonzero,
        "endpoint_zero_count": endpoint_zero,
        "nonendpoint_count": nonendpoint_zero + nonendpoint_nonzero,
        "nonendpoint_nonzero_count": nonendpoint_nonzero,
        "nonendpoint_zero_count": nonendpoint_zero,
        "row_count": end - start,
    }


def all_split_counts(
    cases: list[dict[str, Any]], residues: list[int]
) -> dict[str, dict[str, int]]:
    return {
        "exhaustive": split_counts(cases, residues, 0, EXHAUSTIVE_ROW_COUNT),
        "stress": split_counts(cases, residues, EXHAUSTIVE_ROW_COUNT, ROW_COUNT),
        "total": split_counts(cases, residues, 0, ROW_COUNT),
    }


def harmonic_difference_witness(
    index: int, case: dict[str, Any]
) -> dict[str, Any]:
    sample_count, k, x_count, y_count = row_tuple(case)
    coefficients = Counter(
        {
            k - 1: 1,
            sample_count - 1: 1,
        }
    )
    coefficients[x_count] -= 1
    coefficients[y_count] -= 1
    coefficients = Counter(
        {harmonic_index: coefficient for harmonic_index, coefficient in coefficients.items() if coefficient}
    )
    positive = [
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == 1
    ]
    negative = [
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == -1
    ]
    require(
        len(coefficients) == 2 and len(positive) == 1 and len(negative) == 1,
        f"rejected collision row {index} did not reduce to one harmonic difference",
    )
    positive_index = positive[0]
    negative_index = negative[0]
    require(
        positive_index != negative_index,
        f"rejected collision row {index} reduced to exact zero",
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


def selected_prime_record(
    cases: list[dict[str, Any]], prime: int
) -> dict[str, Any]:
    residues, collisions = residues_for_prime(cases, prime)
    digest = residue_digest(residues)
    require(
        digest == EXPECTED_RESIDUE_DIGESTS[prime],
        f"selected-prime residue digest drifted for {prime}",
    )
    require(not collisions, f"selected prime {prime} has nonendpoint zero collisions")
    counts = all_split_counts(cases, residues)
    require(
        counts["total"]
        == {
            "endpoint_count": ENDPOINT_COUNT,
            "endpoint_nonzero_count": 0,
            "endpoint_zero_count": ENDPOINT_COUNT,
            "nonendpoint_count": NONENDPOINT_COUNT,
            "nonendpoint_nonzero_count": NONENDPOINT_COUNT,
            "nonendpoint_zero_count": 0,
            "row_count": ROW_COUNT,
        },
        f"selected prime {prime} does not classify the frozen corpus",
    )
    return {
        "classification": "selected_per_field_separator",
        "counts": counts,
        "greater_than_every_reciprocal_summand_index": True,
        "prime": prime,
        "residue_u32be_sha256": digest,
    }


def rejected_prime_record(
    cases: list[dict[str, Any]], prime: int
) -> dict[str, Any]:
    residues, collisions = residues_for_prime(cases, prime)
    digest = residue_digest(residues)
    require(
        digest == EXPECTED_RESIDUE_DIGESTS[prime],
        "rejected-prime residue digest drifted",
    )
    indices = tuple(index for index, _case in collisions)
    require(
        indices == EXPECTED_REJECTED_COLLISION_INDICES,
        f"rejected-prime collision indices drifted: {indices!r}",
    )
    counts = all_split_counts(cases, residues)
    require(
        counts["total"]["endpoint_zero_count"] == ENDPOINT_COUNT
        and counts["total"]["nonendpoint_zero_count"] == len(collisions)
        and counts["total"]["nonendpoint_nonzero_count"]
        == NONENDPOINT_COUNT - len(collisions),
        "rejected-prime collision classification drifted",
    )
    return {
        "classification": "rejected_nonendpoint_collision_negative_control",
        "collisions": [
            harmonic_difference_witness(index, case) for index, case in collisions
        ],
        "counts": counts,
        "greater_than_every_reciprocal_summand_index": True,
        "prime": prime,
        "residue_u32be_sha256": digest,
    }


def build_certificate(
    fixture_path: Path = FIXTURE,
) -> dict[str, Any]:
    fixture_raw, _fixture_value, cases = read_frozen_fixture(fixture_path)
    selected = [selected_prime_record(cases, prime) for prime in SELECTED_PRIMES]
    rejected = rejected_prime_record(cases, REJECTED_PRIME)
    generator_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    return {
        "certificate_revision": CERTIFICATE_REVISION,
        "claim_id": CLAIM_ID,
        "corpus": {
            "fixture": {
                "path": FIXTURE_PATH,
                "schema": FIXTURE_SCHEMA,
                "schema_revision": FIXTURE_SCHEMA_REVISION,
                "sha256": hashlib.sha256(fixture_raw).hexdigest(),
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
            "sha256": generator_sha256,
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
        "rejected_prime_negative_control": rejected,
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
        "selected_prime_certificates": selected,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE,
        help="schema-2 KSG arithmetic fixture (must match frozen SHA-256)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="certificate path (sidecar is this path plus .sha256)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the canonical certificate and SHA-256 sidecar",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        certificate = build_certificate(args.fixture)
        raw = canonical_json_bytes(certificate)
        digest = hashlib.sha256(raw).hexdigest()
        sidecar_path = args.output.with_suffix(args.output.suffix + ".sha256")
        sidecar = f"{digest}  {args.output.name}\n"

        if args.write:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(raw)
            sidecar_path.write_text(sidecar, encoding="utf-8", newline="")
            print(
                "wrote modular certificate: "
                f"{ROW_COUNT} rows, {len(SELECTED_PRIMES)} selected primes, "
                f"{len(EXPECTED_REJECTED_COLLISION_INDICES)} rejected-prime collisions; "
                f"SHA-256 {digest}"
            )
            return 0

        committed = args.output.read_bytes()
        committed_sidecar = sidecar_path.read_text(encoding="utf-8")
        require(
            committed == raw,
            "committed modular certificate is stale; rerun with --write",
        )
        require(committed_sidecar == sidecar, "certificate SHA-256 sidecar is stale")
    except (OSError, UnicodeError, json.JSONDecodeError, CertificateError) as error:
        print(f"KSG modular certificate generator error: {error}")
        return 1

    print(
        "OK: generated KSG modular certificate matches "
        f"{ROW_COUNT} frozen rows and SHA-256 {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
