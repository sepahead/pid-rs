#!/usr/bin/env python3
"""Generate a standalone high-precision two-source categorical SxPID corpus.

This program intentionally uses only Python's standard library and never imports pid-rs,
its Python bindings, or the public csxpid implementation.  It evaluates the empirical event
probabilities in the published shared-exclusions definition directly with Decimal arithmetic,
then performs the four-node two-source Mobius inversion.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json"
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SCHEMA = "pid-rs/sxpid2-exhaustive-oracle"
SCHEMA_REVISION = 1
DECIMAL_PRECISION = 80
MAX_TOTAL_SAMPLES = 4
PRIMARY_REFERENCE = "https://arxiv.org/abs/2002.03356"

# Lexicographic (s1, s2, target) state order.  Every nonempty integer count table over these
# eight states with total mass <= MAX_TOTAL_SAMPLES is included.
STATES = tuple(
    (source_one, source_two, target)
    for source_one in (0, 1)
    for source_two in (0, 1)
    for target in (0, 1)
)

# Canonical two-source redundancy-lattice order: unique one, unique two, synergy, redundancy.
NODES = ((0b01,), (0b10,), (0b11,), (0b01, 0b10))
ATOM_NAMES = ("unique_one", "unique_two", "synergy", "redundancy")


class OracleError(RuntimeError):
    """The standalone definition or committed corpus is internally inconsistent."""


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
    # Unary plus applies the active context once and keeps a deterministic scientific/fixed
    # representation that both Python Decimal and Rust f64 parsers accept.
    return str(+value)


def compositions(total: int, slots: int) -> Iterator[tuple[int, ...]]:
    """Yield all ordered nonnegative integer compositions in lexicographic order."""

    if slots == 1:
        yield (total,)
        return
    for head in range(total + 1):
        for tail in compositions(total - head, slots - 1):
            yield (head, *tail)


def state_matches_collection(
    state: tuple[int, int, int],
    realization: tuple[int, int, int],
    source_mask: int,
) -> bool:
    return all(
        source_mask & (1 << source_index) == 0
        or state[source_index] == realization[source_index]
        for source_index in range(2)
    )


def event_mass(
    counts: tuple[int, ...],
    realization: tuple[int, int, int],
    collections: tuple[int, ...],
    *,
    require_target: bool,
) -> int:
    mass = 0
    for state, count in zip(STATES, counts, strict=True):
        if require_target and state[2] != realization[2]:
            continue
        if any(
            state_matches_collection(state, realization, collection)
            for collection in collections
        ):
            mass += count
    return mass


def target_mass(counts: tuple[int, ...], target: int) -> int:
    return sum(
        count
        for state, count in zip(STATES, counts, strict=True)
        if state[2] == target
    )


def invert_two(cumulative: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    redundancy = cumulative[3]
    unique_one = cumulative[0] - redundancy
    unique_two = cumulative[1] - redundancy
    synergy = cumulative[2] - unique_one - unique_two - redundancy
    return unique_one, unique_two, synergy, redundancy


def mutual_information(
    counts: tuple[int, ...],
    source_key: Any,
) -> Decimal:
    total = sum(counts)
    source_masses: dict[Any, int] = {}
    target_masses: dict[int, int] = {}
    joint_masses: dict[tuple[Any, int], int] = {}
    for state, count in zip(STATES, counts, strict=True):
        if count == 0:
            continue
        source = source_key(state)
        target = state[2]
        source_masses[source] = source_masses.get(source, 0) + count
        target_masses[target] = target_masses.get(target, 0) + count
        key = (source, target)
        joint_masses[key] = joint_masses.get(key, 0) + count

    total_decimal = Decimal(total)
    result = Decimal(0)
    for (source, target), joint_mass in sorted(joint_masses.items(), key=repr):
        joint_probability = Decimal(joint_mass) / total_decimal
        ratio = (
            Decimal(joint_mass)
            * total_decimal
            / Decimal(source_masses[source] * target_masses[target])
        )
        result += joint_probability * ratio.ln()
    return result


def evaluate_count_table(counts: tuple[int, ...]) -> dict[str, Any]:
    total = sum(counts)
    if total <= 0:
        raise OracleError("count table must have positive total mass")

    averaged_plus = [Decimal(0) for _ in NODES]
    averaged_minus = [Decimal(0) for _ in NODES]
    total_decimal = Decimal(total)

    for realization, count in zip(STATES, counts, strict=True):
        if count == 0:
            continue
        probability = Decimal(count) / total_decimal
        p_target = Decimal(target_mass(counts, realization[2])) / total_decimal
        cumulative_plus: list[Decimal] = []
        cumulative_minus: list[Decimal] = []
        for collections in NODES:
            union_mass = event_mass(
                counts,
                realization,
                collections,
                require_target=False,
            )
            target_union_mass = event_mass(
                counts,
                realization,
                collections,
                require_target=True,
            )
            if union_mass <= 0 or target_union_mass <= 0:
                raise OracleError("positive-mass realization left a defining event empty")
            p_union = Decimal(union_mass) / total_decimal
            p_target_union = Decimal(target_union_mass) / total_decimal
            cumulative_plus.append(-p_union.ln())
            cumulative_minus.append((p_target / p_target_union).ln())

        pointwise_plus = invert_two(tuple(cumulative_plus))
        pointwise_minus = invert_two(tuple(cumulative_minus))
        for index in range(len(NODES)):
            averaged_plus[index] += probability * pointwise_plus[index]
            averaged_minus[index] += probability * pointwise_minus[index]

    atoms = {}
    for name, informative, misinformative in zip(
        ATOM_NAMES,
        averaged_plus,
        averaged_minus,
        strict=True,
    ):
        atoms[name] = {
            "informative": decimal_text(informative),
            "misinformative": decimal_text(misinformative),
            "net": decimal_text(informative - misinformative),
        }

    return {
        "atoms": atoms,
        "counts": list(counts),
        "mutual_information": {
            "source_one_target": decimal_text(
                mutual_information(counts, lambda state: state[0])
            ),
            "source_two_target": decimal_text(
                mutual_information(counts, lambda state: state[1])
            ),
            "joint_sources_target": decimal_text(
                mutual_information(counts, lambda state: (state[0], state[1]))
            ),
        },
        "total_samples": total,
    }


def build_corpus() -> dict[str, Any]:
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        cases = [
            evaluate_count_table(counts)
            for total in range(1, MAX_TOTAL_SAMPLES + 1)
            for counts in compositions(total, len(STATES))
        ]

        expected_count = sum(
            1
            for total in range(1, MAX_TOTAL_SAMPLES + 1)
            for _ in compositions(total, len(STATES))
        )
        if len(cases) != expected_count:
            raise OracleError("exhaustive composition count changed")

        generator_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        return {
            "arithmetic": {
                "decimal_precision_digits": DECIMAL_PRECISION,
                "logarithm": "natural",
                "probability_source": "exact integer empirical counts",
            },
            "bounds": {
                "alphabet": "binary source_one, source_two, and target",
                "case_count": len(cases),
                "max_total_samples": MAX_TOTAL_SAMPLES,
                "state_order": [list(state) for state in STATES],
                "table_rule": "every nonempty ordered count table within the stated bound",
            },
            "cases": cases,
            "generator": {
                "imports_pid_rs": False,
                "path": "scripts/generate-sxpid2-exhaustive-oracle.py",
                "sha256": generator_sha256,
                "third_party_dependencies": [],
            },
            "limitations": [
                "implementation-path independence is not external review",
                "the corpus proves agreement only on the declared finite binary count-table bound",
                "the corpus does not prove population, estimator, or application validity",
                "the corpus does not prove the three-source or four-source lattice implementation",
            ],
            "primary_reference": PRIMARY_REFERENCE,
            "schema": SCHEMA,
            "schema_revision": SCHEMA_REVISION,
        }


def xor_case(corpus: dict[str, Any]) -> dict[str, Any]:
    xor_counts = [0] * len(STATES)
    wanted = {(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)}
    for index, state in enumerate(STATES):
        xor_counts[index] = int(state in wanted)
    return next(case for case in corpus["cases"] if case["counts"] == xor_counts)


def self_test(corpus: dict[str, Any]) -> None:
    expected_cases = 494
    if corpus["bounds"]["case_count"] != expected_cases:
        raise OracleError(
            f"expected {expected_cases} exhaustive tables, found "
            f"{corpus['bounds']['case_count']}"
        )
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        case = xor_case(corpus)
        redundancy = Decimal(case["atoms"]["redundancy"]["net"])
        synergy = Decimal(case["atoms"]["synergy"]["net"])
        expected_redundancy = (Decimal(2) / Decimal(3)).ln()
        expected_synergy = (Decimal(4) / Decimal(3)).ln()
        tolerance = Decimal("1e-70")
        if abs(redundancy - expected_redundancy) > tolerance:
            raise OracleError("XOR redundancy does not equal ln(2/3)")
        if abs(synergy - expected_synergy) > tolerance:
            raise OracleError("XOR synergy does not equal ln(4/3)")
        atom_sum = sum(
            Decimal(atom["net"]) for atom in case["atoms"].values()
        )
        joint_mi = Decimal(case["mutual_information"]["joint_sources_target"])
        if abs(atom_sum - joint_mi) > tolerance:
            raise OracleError("XOR atoms do not reconstruct joint mutual information")


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
        print(f"oracle corpus error: {error}")
        return 1
    if committed != raw:
        print("oracle corpus error: committed corpus is stale; rerun with --write")
        return 1
    if committed_sidecar != sidecar:
        print("oracle corpus error: committed SHA-256 sidecar is stale")
        return 1
    print(
        f"OK: {len(corpus['cases'])} exhaustive high-precision SxPID2 tables match "
        f"SHA-256 {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
