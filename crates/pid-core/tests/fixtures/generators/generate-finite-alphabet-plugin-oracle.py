#!/usr/bin/env python3
"""Generate bounded high-precision finite-alphabet PID comparison data.

This program uses only Python's standard library. It does not import pid-rs or another PID
implementation. It evaluates empirical shared-exclusion event probabilities and Williams--Beer
specific information directly with Decimal arithmetic. It then applies a generic finite-poset
Mobius inversion.

The output is bounded software evidence. It is not an asymptotic proof or external review.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from decimal import Decimal, localcontext
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "crates/pid-core/tests/fixtures/finite_alphabet_plugin_oracle.json"
SIDECAR = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
SCHEMA = "pid-rs/finite-alphabet-plugin-oracle"
SCHEMA_REVISION = 1
DECIMAL_PRECISION = 100

Antichain = tuple[int, ...]
State = tuple[tuple[int, ...], int, int]


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


def antichain_leq(lower: Antichain, upper: Antichain) -> bool:
    """Return the Williams--Beer redundancy-lattice order relation."""

    return all(
        any(lower_mask & upper_mask == lower_mask for lower_mask in lower)
        for upper_mask in upper
    )


def antichains(source_count: int) -> tuple[Antichain, ...]:
    masks = tuple(range(1, 1 << source_count))
    result = []
    for size in range(1, len(masks) + 1):
        for candidate in combinations(masks, size):
            if all(
                left & right not in (left, right)
                for left, right in combinations(candidate, 2)
            ):
                result.append(candidate)
    ordered = tuple(result)
    if ordered != tuple(sorted(ordered, key=lambda node: (len(node), node))):
        raise OracleError("antichain order is not canonical size-then-lexicographic order")
    if any(node != tuple(sorted(node)) for node in ordered):
        raise OracleError("an antichain contains noncanonical mask order")
    return ordered


def mobius_invert(
    nodes: tuple[Antichain, ...], cumulative: dict[Antichain, Decimal]
) -> dict[Antichain, Decimal]:
    """Invert a finite poset without relying on a repository lattice order."""

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
    tolerance = Decimal("1e-90")
    for node in nodes:
        reconstructed = sum(
            (
                atom
                for lower, atom in atoms.items()
                if antichain_leq(lower, node)
            ),
            Decimal(0),
        )
        if abs(reconstructed - cumulative[node]) > tolerance:
            raise OracleError("Mobius atoms do not reconstruct a lattice node")
    return atoms


def validate_states(states: Iterable[State], source_count: int) -> tuple[State, ...]:
    materialized = tuple(states)
    if not materialized:
        raise OracleError("count table must contain a positive state")
    if any(
        len(sources) != source_count or count <= 0
        for sources, _, count in materialized
    ):
        raise OracleError("state width and counts must match the declared table")
    keys = [(sources, target) for sources, target, _ in materialized]
    if len(keys) != len(set(keys)):
        raise OracleError("count table contains a duplicate realization")
    return materialized


def state_json(states: tuple[State, ...]) -> list[dict[str, Any]]:
    return [
        {"count": count, "realization": [*sources, target]}
        for sources, target, count in states
    ]


def full_binary_table(
    source_count: int, *, multiplier: int, offset: int, modulus: int
) -> tuple[State, ...]:
    states = []
    for index, values in enumerate(product((0, 1), repeat=source_count + 1)):
        count = 1 + ((index * multiplier + offset) % modulus)
        states.append((tuple(values[:-1]), values[-1], count))
    return tuple(states)


def target_mass(states: tuple[State, ...], target: int) -> int:
    return sum(count for _, state_target, count in states if state_target == target)


def matches_mask(
    candidate_sources: tuple[int, ...], realization_sources: tuple[int, ...], mask: int
) -> bool:
    return all(
        mask & (1 << index) == 0 or candidate == realization_sources[index]
        for index, candidate in enumerate(candidate_sources)
    )


def event_mass(
    states: tuple[State, ...],
    realization_sources: tuple[int, ...],
    realization_target: int,
    node: Antichain,
    *,
    require_target: bool,
) -> int:
    return sum(
        count
        for sources, target, count in states
        if (not require_target or target == realization_target)
        and any(matches_mask(sources, realization_sources, mask) for mask in node)
    )


def sxpid_components(
    states: tuple[State, ...], source_count: int
) -> tuple[
    tuple[Antichain, ...],
    dict[Antichain, tuple[Decimal, Decimal]],
    list[dict[str, Any]],
]:
    nodes = antichains(source_count)
    total = sum(count for _, _, count in states)
    total_decimal = Decimal(total)
    averaged = {node: [Decimal(0), Decimal(0)] for node in nodes}
    pointwise = []

    for sources, target, count in sorted(states, key=lambda state: (state[0], state[1])):
        p_target = Decimal(target_mass(states, target)) / total_decimal
        cumulative_plus: dict[Antichain, Decimal] = {}
        cumulative_minus: dict[Antichain, Decimal] = {}
        for node in nodes:
            union_count = event_mass(
                states, sources, target, node, require_target=False
            )
            target_union_count = event_mass(
                states, sources, target, node, require_target=True
            )
            if union_count <= 0 or target_union_count <= 0:
                raise OracleError("a supported realization has an empty defining event")
            p_union = Decimal(union_count) / total_decimal
            p_target_union = Decimal(target_union_count) / total_decimal
            cumulative_plus[node] = -p_union.ln()
            cumulative_minus[node] = (p_target / p_target_union).ln()

        atoms_plus = mobius_invert(nodes, cumulative_plus)
        atoms_minus = mobius_invert(nodes, cumulative_minus)
        probability = Decimal(count) / total_decimal
        pointwise_atoms = []
        for node in nodes:
            informative = atoms_plus[node]
            misinformative = atoms_minus[node]
            averaged[node][0] += probability * informative
            averaged[node][1] += probability * misinformative
            pointwise_atoms.append(
                {
                    "informative": decimal_text(informative),
                    "misinformative": decimal_text(misinformative),
                    "net": decimal_text(informative - misinformative),
                    "sets": list(node),
                }
            )
        pointwise.append(
            {
                "atoms": pointwise_atoms,
                "count": count,
                "realization": [*sources, target],
            }
        )

    return (
        nodes,
        {node: (values[0], values[1]) for node, values in averaged.items()},
        pointwise,
    )


def sxpid_case(
    name: str, states: Iterable[State], source_count: int, *, include_pointwise: bool
) -> dict[str, Any]:
    checked = validate_states(states, source_count)
    nodes, averaged, pointwise = sxpid_components(checked, source_count)
    result = {
        "atoms": [
            {
                "informative": decimal_text(averaged[node][0]),
                "misinformative": decimal_text(averaged[node][1]),
                "net": decimal_text(averaged[node][0] - averaged[node][1]),
                "sets": list(node),
            }
            for node in nodes
        ],
        "name": name,
        "source_count": source_count,
        "states": state_json(checked),
    }
    if include_pointwise:
        result["pointwise"] = pointwise
    return result


def source_value(sources: tuple[int, ...], mask: int) -> tuple[int, ...]:
    return tuple(value for index, value in enumerate(sources) if mask & (1 << index))


def specific_information(
    states: tuple[State, ...], mask: int, target: int
) -> Decimal:
    total = sum(count for _, _, count in states)
    target_count = target_mass(states, target)
    if target_count <= 0:
        raise OracleError("specific information is undefined for an absent target state")

    source_counts: dict[tuple[int, ...], int] = {}
    joint_counts: dict[tuple[int, ...], int] = {}
    for sources, state_target, count in states:
        source = source_value(sources, mask)
        source_counts[source] = source_counts.get(source, 0) + count
        if state_target == target:
            joint_counts[source] = joint_counts.get(source, 0) + count

    result = Decimal(0)
    for source, joint_count in sorted(joint_counts.items()):
        weight = Decimal(joint_count) / Decimal(target_count)
        ratio = Decimal(joint_count * total) / Decimal(
            source_counts[source] * target_count
        )
        result += weight * ratio.ln()
    return result


def imin_components(
    states: tuple[State, ...], source_count: int
) -> tuple[
    tuple[Antichain, ...],
    dict[Antichain, Decimal],
    dict[Antichain, Decimal],
]:
    nodes = antichains(source_count)
    targets = sorted({target for _, target, _ in states})
    total = Decimal(sum(count for _, _, count in states))
    target_counts = {target: target_mass(states, target) for target in targets}
    cache = {
        (mask, target): specific_information(states, mask, target)
        for mask in range(1, 1 << source_count)
        for target in targets
    }
    redundancies = {}
    for node in nodes:
        redundancies[node] = sum(
            (
                Decimal(target_counts[target])
                / total
                * min(cache[(mask, target)] for mask in node)
                for target in targets
            ),
            Decimal(0),
        )
    return nodes, redundancies, mobius_invert(nodes, redundancies)


def imin_case(name: str, states: Iterable[State], source_count: int) -> dict[str, Any]:
    checked = validate_states(states, source_count)
    nodes, redundancies, atoms = imin_components(checked, source_count)
    return {
        "lattice": [
            {
                "atom": decimal_text(atoms[node]),
                "redundancy": decimal_text(redundancies[node]),
                "sets": list(node),
            }
            for node in nodes
        ],
        "name": name,
        "source_count": source_count,
        "states": state_json(checked),
    }


def tie_case(
    name: str, states: tuple[State, ...], source_count: int
) -> dict[str, Any]:
    result = imin_case(name, states, source_count)
    target = 0
    values = {
        mask: specific_information(states, mask, target) for mask in (0b01, 0b10)
    }
    minimum = min(values.values())
    result["crossing_target"] = target
    result["specific_information"] = [
        {"source_mask": mask, "value": decimal_text(values[mask])}
        for mask in (0b01, 0b10)
    ]
    result["minimizer_masks"] = [mask for mask in (0b01, 0b10) if values[mask] == minimum]
    return result


def tie_tables() -> tuple[tuple[State, ...], tuple[State, ...], tuple[State, ...]]:
    tie_counts = (12, 2, 4, 4, 4, 4, 2, 12)
    left_counts = (12, 2, 3, 4, 5, 4, 2, 12)
    right_counts = (12, 2, 5, 4, 3, 4, 2, 12)
    keys = tuple(
        (tuple(values[:-1]), values[-1])
        for values in product((0, 1), repeat=3)
    )

    def table(counts: tuple[int, ...]) -> tuple[State, ...]:
        return tuple(
            (sources, target, count)
            for (sources, target), count in zip(keys, counts, strict=True)
        )

    return table(left_counts), table(tie_counts), table(right_counts)


def lift_tie_table_to_three_sources(states: tuple[State, ...]) -> tuple[State, ...]:
    """Add a balanced binary third source without changing the first two specific informations."""

    return tuple(
        ((*sources, source_three), target, count)
        for sources, target, count in states
        for source_three in (0, 1)
    )


def build_fixture() -> dict[str, Any]:
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        sxpid_cases = [
            sxpid_case(
                "nonuniform_binary_m2",
                full_binary_table(2, multiplier=5, offset=2, modulus=7),
                2,
                include_pointwise=False,
            ),
            sxpid_case(
                "nonuniform_binary_m3",
                full_binary_table(3, multiplier=7, offset=3, modulus=9),
                3,
                include_pointwise=False,
            ),
            sxpid_case(
                "nonuniform_binary_m4",
                full_binary_table(4, multiplier=11, offset=5, modulus=13),
                4,
                include_pointwise=False,
            ),
        ]

        common_states = (
            ((1, 1), 1, 3),
            ((1, 2), 0, 2),
            ((2, 1), 0, 4),
            ((2, 2), 1, 5),
        )
        rare_state = ((0, 0), 0, 1)
        pointwise_face_case = {
            "fixed_face": sxpid_case(
                "fixed_face_without_rare_state",
                common_states,
                2,
                include_pointwise=True,
            ),
            "late_rare_realization": [0, 0, 0],
            "with_late_rare": sxpid_case(
                "positive_rare_state_appended_last",
                (*common_states, rare_state),
                2,
                include_pointwise=True,
            ),
        }

        imin_cases = [
            imin_case(
                "nonuniform_binary_m2",
                full_binary_table(2, multiplier=5, offset=2, modulus=7),
                2,
            ),
            imin_case(
                "nonuniform_binary_m3",
                full_binary_table(3, multiplier=7, offset=3, modulus=9),
                3,
            ),
        ]
        left, tie, right = tie_tables()
        tie_crossing = [
            tie_case("m2_left_of_minimum_tie", left, 2),
            tie_case("m2_exact_minimum_tie", tie, 2),
            tie_case("m2_right_of_minimum_tie", right, 2),
            tie_case(
                "m3_left_of_minimum_tie",
                lift_tie_table_to_three_sources(left),
                3,
            ),
            tie_case(
                "m3_exact_minimum_tie",
                lift_tie_table_to_three_sources(tie),
                3,
            ),
            tie_case(
                "m3_right_of_minimum_tie",
                lift_tie_table_to_three_sources(right),
                3,
            ),
        ]

        fixture = {
            "arithmetic": {
                "decimal_precision_digits": DECIMAL_PRECISION,
                "logarithm": "natural",
                "probability_source": "exact positive integer empirical counts",
            },
            "claim_scope": "bounded software agreement; not an asymptotic proof",
            "generator": {
                "imports_pid_rs": False,
                "path": "scripts/generate-finite-alphabet-plugin-oracle.py",
                "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "third_party_dependencies": [],
            },
            "imin_cases": imin_cases,
            "imin_minimum_tie_crossing": tie_crossing,
            "limitations": [
                "the fixture covers only the listed finite empirical count tables",
                "agreement does not prove an asymptotic convergence theorem",
                "implementation-path independence is not external review",
                "binary64 comparisons include a stated rounding envelope",
                "an absent realization has no canonical pointwise atom in this fixture",
                "fitted quantizer wrapper checks are software-composition checks, "
                "not population claims",
            ],
            "method_scope": {
                "categorical_imin": {
                    "definition_status": "paper-defined",
                    "defining_reference": "https://arxiv.org/abs/1004.2515",
                    "tested_code": [
                        "pid_core::stable::imin::imin_pid2",
                        "pid_core::stable::imin::imin_pid3",
                    ],
                },
                "categorical_sxpid": {
                    "definition_status": "paper-defined",
                    "defining_reference": "https://doi.org/10.1103/PhysRevE.103.032149",
                    "tested_code": [
                        "pid_core::stable::categorical::discrete_sxpid_n",
                        "pid_core::stable::categorical::discrete_sxpid_n_averaged",
                    ],
                },
                "fitted_quantizer_wrappers": {
                    "composition_kind": "fitted quantizer plus categorical functional",
                    "definition_status": "project-defined",
                    "defining_reference": None,
                    "tested_code": [
                        "pid_core::stable::quantized::fitted_quantized_sxpid2",
                        "pid_core::stable::imin::imin_pid2_quantized",
                    ],
                },
            },
            "pointwise_fixed_face_case": pointwise_face_case,
            "schema": SCHEMA,
            "schema_revision": SCHEMA_REVISION,
            "sxpid_cases": sxpid_cases,
        }
        self_test(fixture)
        return fixture


def find_atom(case: dict[str, Any], sets: list[int], field: str) -> Decimal:
    entries = case.get("atoms", case.get("lattice"))
    for entry in entries:
        if entry["sets"] == sets:
            return Decimal(entry[field])
    raise OracleError(f"missing lattice node {sets}")


def self_test(fixture: dict[str, Any]) -> None:
    expected_counts = {2: 4, 3: 18, 4: 166}
    for source_count, expected_count in expected_counts.items():
        if len(antichains(source_count)) != expected_count:
            raise OracleError(f"unexpected m={source_count} antichain count")

    for case in fixture["sxpid_cases"]:
        if len(case["atoms"]) != expected_counts[case["source_count"]]:
            raise OracleError("SxPID fixture omitted a lattice atom")
        for atom in case["atoms"]:
            if Decimal(atom["net"]) != Decimal(atom["informative"]) - Decimal(
                atom["misinformative"]
            ):
                raise OracleError("SxPID net atom does not equal its component difference")
            for component in ("informative", "misinformative"):
                if Decimal(atom[component]) < Decimal("-1e-90"):
                    raise OracleError("SxPID component is negative beyond Decimal roundoff")

    face = fixture["pointwise_fixed_face_case"]
    rare = face["late_rare_realization"]
    with_rare_keys = [
        entry["realization"] for entry in face["with_late_rare"]["pointwise"]
    ]
    fixed_face_keys = [
        entry["realization"] for entry in face["fixed_face"]["pointwise"]
    ]
    if with_rare_keys[0] != rare or rare in fixed_face_keys:
        raise OracleError("late rare state does not exercise keyed pointwise output")
    if with_rare_keys[1:] != fixed_face_keys:
        raise OracleError("common pointwise keys did not shift by one position")
    if with_rare_keys != sorted(with_rare_keys) or fixed_face_keys != sorted(
        fixed_face_keys
    ):
        raise OracleError("pointwise realization keys are not in canonical order")
    for side in (face["with_late_rare"], face["fixed_face"]):
        for point in side["pointwise"]:
            for atom in point["atoms"]:
                for component in ("informative", "misinformative"):
                    if Decimal(atom[component]) < Decimal("-1e-90"):
                        raise OracleError(
                            "pointwise SxPID component is negative beyond Decimal roundoff"
                        )

    crossing = fixture["imin_minimum_tie_crossing"]
    if len(crossing) != 6:
        raise OracleError("expected two complete I_min tie-crossing series")
    for source_count, series in ((2, crossing[:3]), (3, crossing[3:])):
        if any(case["source_count"] != source_count for case in series):
            raise OracleError("I_min tie series has the wrong source count")
        if series[1]["minimizer_masks"] != [0b01, 0b10]:
            raise OracleError("middle I_min case is not an exact minimum tie")
        if (
            len(series[0]["minimizer_masks"]) != 1
            or len(series[2]["minimizer_masks"]) != 1
        ):
            raise OracleError("I_min perturbations do not have unique minimizers")
        if series[0]["minimizer_masks"] == series[2]["minimizer_masks"]:
            raise OracleError("I_min minimizer did not cross the exact tie")

    for case in [*fixture["imin_cases"], *crossing]:
        full_mask = (1 << case["source_count"]) - 1
        joint_information = find_atom(case, [full_mask], "redundancy")
        atom_sum = sum(
            (Decimal(entry["atom"]) for entry in case["lattice"]), Decimal(0)
        )
        if abs(atom_sum - joint_information) > Decimal("1e-90"):
            raise OracleError("I_min atoms do not reconstruct joint mutual information")


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
        print(f"wrote bounded finite-alphabet fixture; SHA-256 {digest}")
        return 0

    try:
        committed = OUTPUT.read_bytes()
        committed_sidecar = SIDECAR.read_text(encoding="utf-8")
    except OSError as error:
        print(f"oracle fixture error: {error}")
        return 1
    if committed != raw:
        print("oracle fixture error: committed data is stale; rerun with --write")
        return 1
    if committed_sidecar != sidecar:
        print("oracle fixture error: committed SHA-256 sidecar is stale")
        return 1
    print(f"OK: bounded finite-alphabet fixture matches SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
