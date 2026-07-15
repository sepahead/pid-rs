#!/usr/bin/env python3
"""Generate high-precision reference values for the KSG local count term.

The program uses only Python's standard library.  For positive integer arguments the Euler
constant cancels from the four digamma terms, leaving an exact harmonic-number identity.  Decimal
arithmetic evaluates that identity independently of pid-rs and its Python bindings.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
SCHEMA_REVISION = 1
DECIMAL_PRECISION = 80
EXHAUSTIVE_MAX_SAMPLES = 16
STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4096, 65_536, 1_000_000)


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


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise OracleError("reference calculation produced a non-finite Decimal")
    return str(+value)


def exhaustive_arguments() -> list[tuple[int, int, int, int]]:
    """Enumerate every feasible count tuple within the declared small-sample bound."""

    return [
        (sample_count, k, x_count, y_count)
        for sample_count in range(2, EXHAUSTIVE_MAX_SAMPLES + 1)
        for k in range(1, sample_count)
        for x_count in range(k - 1, sample_count)
        for y_count in range(k - 1, sample_count)
    ]


def stress_arguments() -> list[tuple[int, int, int, int]]:
    """Select deterministic boundary/interior tuples through one million samples."""

    arguments: list[tuple[int, int, int, int]] = []
    for sample_count in STRESS_SAMPLE_SIZES:
        k_values = sorted(
            {
                value
                for value in (1, 2, 3, 4, 8, 16, 64, sample_count // 2, sample_count - 1)
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
                    arguments.append((sample_count, k, x_count, y_count))
    return arguments


def selected_harmonics(indices: set[int]) -> dict[int, Decimal]:
    if not indices or min(indices) < 0:
        raise OracleError("harmonic indices must be nonnegative")
    result = {0: Decimal(0)} if 0 in indices else {}
    total = Decimal(0)
    for index in range(1, max(indices) + 1):
        total += Decimal(1) / Decimal(index)
        if index in indices:
            result[index] = +total
    if result.keys() != indices:
        raise OracleError("failed to evaluate every requested harmonic number")
    return result


def build_corpus() -> dict[str, Any]:
    exhaustive = exhaustive_arguments()
    stress = stress_arguments()
    arguments = exhaustive + stress
    if len(arguments) != len(set(arguments)):
        raise OracleError("bounded and stress argument sets must be disjoint and unique")

    indices = {
        index
        for sample_count, k, x_count, y_count in arguments
        for index in (k - 1, sample_count - 1, x_count, y_count)
    }
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        harmonics = selected_harmonics(indices)
        cases = [
            {
                "expected_nats": decimal_text(
                    harmonics[k - 1]
                    + harmonics[sample_count - 1]
                    - harmonics[x_count]
                    - harmonics[y_count]
                ),
                "k": k,
                "sample_count": sample_count,
                "x_count": x_count,
                "y_count": y_count,
            }
            for sample_count, k, x_count, y_count in arguments
        ]

    generator_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "arithmetic": {
            "decimal_precision_digits": DECIMAL_PRECISION,
            "exact_identity": "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
            "logarithm_unit": "nats",
        },
        "bounds": {
            "exhaustive_case_count": len(exhaustive),
            "exhaustive_max_samples": EXHAUSTIVE_MAX_SAMPLES,
            "exhaustive_rule": "2 <= n <= bound; 1 <= k < n; k-1 <= nx,ny < n",
            "stress_case_count": len(stress),
            "stress_sample_sizes": list(STRESS_SAMPLE_SIZES),
        },
        "cases": cases,
        "generator": {
            "imports_pid_rs": False,
            "path": "scripts/generate-ksg-local-arithmetic-oracle.py",
            "sha256": generator_sha256,
            "third_party_dependencies": [],
        },
        "limitations": [
            "this checks the integer digamma combination, not neighbor-count correctness",
            "the exhaustive result is finite and the larger sample sizes are selected stress points",
            "arithmetic agreement is not a statistical consistency or application-validity claim",
            "implementation-path diversity is not external review",
        ],
        "schema": SCHEMA,
        "schema_revision": SCHEMA_REVISION,
    }


def self_test(corpus: dict[str, Any]) -> None:
    expected_exhaustive = 6_920
    if corpus["bounds"]["exhaustive_case_count"] != expected_exhaustive:
        raise OracleError("exhaustive tuple count changed")
    cases = {
        (case["sample_count"], case["k"], case["x_count"], case["y_count"]): Decimal(
            case["expected_nats"]
        )
        for case in corpus["cases"]
    }
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        tolerance = Decimal("1e-70")
        if abs(cases[(4, 1, 0, 0)] - Decimal(11) / Decimal(6)) > tolerance:
            raise OracleError("n=4, k=1 boundary case does not equal 11/6")
        if abs(cases[(4, 2, 1, 1)] - Decimal(5) / Decimal(6)) > tolerance:
            raise OracleError("n=4, k=2 boundary case does not equal 5/6")
        if abs(cases[(4, 3, 3, 3)] + Decimal(1) / Decimal(3)) > tolerance:
            raise OracleError("n=4, k=3 dense-count case does not equal -1/3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the committed corpus and SHA-256 sidecar",
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
        print(f"wrote {len(corpus['cases'])} cases; SHA-256 {digest}")
        return 0

    try:
        committed = OUTPUT.read_bytes()
        committed_sidecar = SIDECAR.read_text(encoding="utf-8")
    except OSError as error:
        print(f"reference corpus error: {error}")
        return 1
    if committed != raw:
        print("reference corpus error: committed corpus is stale; rerun with --write")
        return 1
    if committed_sidecar != sidecar:
        print("reference corpus error: committed SHA-256 sidecar is stale")
        return 1
    print(
        f"OK: {len(corpus['cases'])} high-precision KSG local arithmetic cases match "
        f"SHA-256 {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
