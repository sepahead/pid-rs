#!/usr/bin/env python3
"""Exhaust and regress exact product-one cancellations with nonempty log terms."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

EVIDENCE = (
    REPOSITORY_ROOT
    / "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json"
)
WITNESS = (0, 0, 1, 1, 1, 4, 1, 0)
WITNESS_IDENTITY = ("atom", "unique_one", "net")

Expression = dict[Fraction, Fraction]


def _compositions(total: int, width: int) -> Iterator[tuple[int, ...]]:
    if width == 1:
        yield (total,)
        return
    for head in range(total + 1):
        for tail in _compositions(total - head, width - 1):
            yield (head, *tail)


def _add_term(expression: Expression, coefficient: Fraction, argument: Fraction) -> None:
    if coefficient == 0 or argument == 1:
        return
    combined = expression.get(argument, Fraction(0)) + coefficient
    if combined == 0:
        expression.pop(argument, None)
    else:
        expression[argument] = combined


def _linear_combination(
    expressions: Sequence[Mapping[Fraction, Fraction]], coefficients: Sequence[int]
) -> Expression:
    result: Expression = {}
    for expression, scale in zip(expressions, coefficients, strict=True):
        for argument, coefficient in expression.items():
            _add_term(result, coefficient * scale, argument)
    return result


def _derive_expressions(counts: Sequence[int]) -> dict[tuple[str, str, str], Expression]:
    total = sum(counts)
    cumulative = {
        component: [dict() for _ in exact.NODE_MASKS]
        for component in exact.COMPONENT_IDS
    }
    for realization, row_count in zip(exact.STATES, counts, strict=True):
        if row_count == 0:
            continue
        target_count = sum(
            count
            for state, count in zip(exact.STATES, counts, strict=True)
            if state[2] == realization[2]
        )
        weight = Fraction(row_count, total)
        for node_index, masks in enumerate(exact.NODE_MASKS):
            union_count = exact._event_count(  # noqa: SLF001 - independent audit script.
                exact.STATES, counts, realization, masks, require_target=False
            )
            target_union_count = exact._event_count(  # noqa: SLF001
                exact.STATES, counts, realization, masks, require_target=True
            )
            arguments = (
                Fraction(total, union_count),
                Fraction(target_count, target_union_count),
                Fraction(total * target_union_count, union_count * target_count),
            )
            for component, argument in zip(
                exact.COMPONENT_IDS, arguments, strict=True
            ):
                _add_term(cumulative[component][node_index], weight, argument)

    atoms = {
        component: [
            _linear_combination(cumulative[component], row) for row in exact.MOBIUS
        ]
        for component in exact.COMPONENT_IDS
    }
    result: dict[tuple[str, str, str], Expression] = {}
    for kind, identifiers, components in (
        ("cumulative", exact.NODE_IDS, cumulative),
        ("atom", exact.ATOM_IDS, atoms),
    ):
        for component in exact.COMPONENT_IDS:
            for identifier, expression in zip(
                identifiers, components[component], strict=True
            ):
                result[(kind, identifier, component)] = expression
    return result


def _binary() -> Path:
    target = Path(
        os.environ.get(
            "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target/certified-sxpid")
        )
    )
    suffix = ".exe" if os.name == "nt" else ""
    binary = (target / "debug" / f"pid-certified-sxpid{suffix}").resolve()
    exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
    return binary


def _run_certifier(raw_input: bytes) -> tuple[bytes, Path]:
    binary = _binary()
    completed = subprocess.run(
        [str(binary), "-"],
        cwd=REPOSITORY_ROOT,
        input=raw_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    exact.require(
        completed.returncode == 0,
        "certifier rejected the minimized boundary witness: "
        + completed.stderr.decode("utf-8", errors="replace"),
    )
    return bytes(completed.stdout), binary


def _reseal(certificate: dict[str, Any]) -> bytes:
    certificate["payload_sha256"] = exact.canonical_digest(certificate["payload"])
    return exact.canonical_json_bytes(certificate)


def main() -> int:
    cases: list[dict[str, Any]] = []
    tables_checked = 0
    coordinates_checked = 0
    counts_by_total: dict[str, int] = {}
    for total in range(1, 9):
        total_cases = 0
        for counts in _compositions(total, len(exact.STATES)):
            tables_checked += 1
            derived = exact.derive_products(counts)
            expressions = _derive_expressions(counts)
            by_identity = derived.by_identity()
            for identity, expression in expressions.items():
                coordinates_checked += 1
                if expression and by_identity[identity].product == 1:
                    total_cases += 1
                    cases.append(
                        {
                            "total": total,
                            "support_size": sum(count > 0 for count in counts),
                            "counts": list(counts),
                            "identity": list(identity),
                            "canonical_term_count": len(expression),
                        }
                    )
        counts_by_total[str(total)] = total_cases

    exact.require(
        all(counts_by_total[str(total)] == 0 for total in range(1, 8)),
        "a nonempty product-one expression appeared below total count eight",
    )
    exact.require(counts_by_total["8"] == 16, "n=8 boundary case count changed")
    exact.require(
        all(case["support_size"] == 5 for case in cases),
        "a boundary case has support size other than five",
    )
    exact.require(
        all(
            case["identity"][0] == "atom"
            and case["identity"][1] in ("unique_one", "unique_two")
            and case["identity"][2] == "net"
            for case in cases
        ),
        "a boundary case lies outside the two net unique atoms",
    )

    raw_input = exact.canonical_input(WITNESS)
    certificate_raw, binary = _run_certifier(raw_input)
    derived = exact.derive_products(WITNESS)
    exact.verify_certificate(raw_input, certificate_raw, derived)
    certificate = exact.parse_json(certificate_raw, "boundary certificate")
    coordinate = next(
        item
        for item in certificate["payload"]["coordinates"]
        if (
            item["identity"]["kind"],
            item["identity"]["node"],
            item["identity"]["component"],
        )
        == WITNESS_IDENTITY
    )
    exact.require(
        len(coordinate["exact_terms"]) == 5,
        "minimized witness no longer has five nonempty canonical terms",
    )
    exact.require(
        coordinate["interval"]["decision"] == "unresolved_sign"
        and coordinate["interval"]["exact_zero_witness"] is None,
        "interval-local boundary semantics changed",
    )
    exact.require(
        coordinate["exact_product"]["decision"] == "certified_exact_zero"
        and coordinate["exact_product"]["exact_zero_witness"]
        == "exact_multiplicative_product_equals_one",
        "exact-product boundary semantics changed",
    )

    mutant = copy.deepcopy(certificate)
    mutant_coordinate = next(
        item
        for item in mutant["payload"]["coordinates"]
        if item["identity"] == coordinate["identity"]
    )
    mutant_coordinate["exact_product"]["decision"] = "certified_positive"
    try:
        exact.verify_certificate(raw_input, _reseal(mutant), derived)
    except exact.ProductVerificationError:
        mutation_killed = True
    else:
        mutation_killed = False
    exact.require(mutation_killed, "false exact-product sign mutation survived")

    payload = {
        "schema": "pid-rs/sxpid2-nonsyntactic-exact-zero-boundary/v1",
        "status": "passed",
        "scope": {
            "alphabet": "binary source_one, source_two, and target",
            "totals_exhausted": [1, 2, 3, 4, 5, 6, 7, 8],
            "tables_checked": tables_checked,
            "coordinates_checked": coordinates_checked,
        },
        "findings": {
            "nonsyntactic_product_one_coordinates_by_total": counts_by_total,
            "n8_coordinate_count": len(cases),
            "all_n8_support_sizes": sorted({case["support_size"] for case in cases}),
            "all_n8_identities": sorted({tuple(case["identity"]) for case in cases}),
            "minimized_witness": {
                "counts": list(WITNESS),
                "identity": list(WITNESS_IDENTITY),
                "canonical_term_count": len(coordinate["exact_terms"]),
                "interval_decision": coordinate["interval"]["decision"],
                "exact_product_decision": coordinate["exact_product"]["decision"],
                "legacy_empty_term_only_classifier_would_certify_zero": not bool(
                    coordinate["exact_terms"]
                ),
            },
            "false_exact_product_sign_mutation_killed": mutation_killed,
        },
        "cases": cases,
        "bindings": {
            "certifier_executable_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "boundary_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "exact_product_source_sha256": hashlib.sha256(
                (SCRIPT_DIR / "_exact_product.py").read_bytes()
            ).hexdigest(),
            "live_input_sha256": hashlib.sha256(raw_input).hexdigest(),
            "live_certificate_sha256": hashlib.sha256(certificate_raw).hexdigest(),
        },
        "claim_boundary": (
            "Finite binary empirical arithmetic only. Minimality is relative to total count and "
            "support size in the exhausted binary table space; no population, scientific-axiom, "
            "higher-source, continuous-PID, or downstream-validity claim follows."
        ),
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_bytes(exact.canonical_json_bytes(payload) + b"\n")
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
