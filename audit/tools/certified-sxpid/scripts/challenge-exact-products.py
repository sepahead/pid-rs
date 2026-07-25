#!/usr/bin/env python3
"""Deterministic evolutionary falsifier for larger exact SxPID2 count tables.

This is a bounded counterexample search, not a proof.  Fitness is exact: for a coordinate
``log(R)/n``, candidates at the fixed total ``n`` are ordered using the positive rational ``R``.
Every evaluated table also passes the direct-event, local-net, direct-MI, component, and zeta
identities in ``_exact_product``.  The final candidate (and any discovered counterexample after
deterministic one-step minimization) is post-checked against a live Rust certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Final, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

DEFAULT_SEED: Final = 0x5358504944322026
DEFAULT_TOTAL: Final = 64
DEFAULT_POPULATION: Final = 96
DEFAULT_GENERATIONS: Final = 96


@dataclass(frozen=True)
class Fitness:
    rank: int
    product: Fraction
    identity: tuple[str, str, str]
    violation: bool

    def sort_key(self) -> tuple[int, Fraction, tuple[str, str, str]]:
        return (self.rank, self.product, self.identity)


@dataclass(frozen=True)
class Evaluated:
    counts: tuple[int, ...]
    derived: exact.DerivedProducts
    fitness: Fitness


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=lambda text: int(text, 0), default=DEFAULT_SEED)
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL)
    parser.add_argument("--population", type=int, default=DEFAULT_POPULATION)
    parser.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument(
        "--output", type=Path, help="write the canonical complete search log"
    )
    parser.add_argument("--certifier", type=Path, help="prebuilt certifier executable")
    return parser.parse_args(argv)


def _default_binary() -> Path:
    target = Path(
        os.environ.get(
            "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target/certified-sxpid")
        )
    )
    suffix = ".exe" if os.name == "nt" else ""
    return target / "debug" / f"pid-certified-sxpid{suffix}"


def _run_certifier(binary: Path, input_raw: bytes) -> bytes:
    completed = subprocess.run(
        [str(binary), "-"],
        cwd=REPOSITORY_ROOT,
        input=input_raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise exact.ProductVerificationError(
            "certifier failed during evolutionary post-check: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return bytes(completed.stdout)


def _fitness(derived: exact.DerivedProducts) -> Fitness:
    # The published SxPID informative and misinformative partial atoms are the falsification
    # target.  No axiom or atom from a different PID measure enters this search.
    partial_atoms = [
        coordinate
        for coordinate in derived.coordinates
        if coordinate.kind == "atom"
        and coordinate.component in ("informative", "misinformative")
    ]
    violations = [coordinate for coordinate in partial_atoms if coordinate.product < 1]
    if violations:
        witness = min(
            violations, key=lambda coordinate: (coordinate.product, coordinate.identity)
        )
        return Fitness(0, witness.product, witness.identity, True)

    nonzero = [coordinate for coordinate in partial_atoms if coordinate.product > 1]
    if nonzero:
        boundary = min(
            nonzero, key=lambda coordinate: (coordinate.product, coordinate.identity)
        )
        return Fitness(1, boundary.product, boundary.identity, False)

    return Fitness(2, Fraction(1, 1), ("atom", "all", "partial"), False)


def _evaluate(
    counts: tuple[int, ...], cache: dict[tuple[int, ...], Evaluated]
) -> Evaluated:
    cached = cache.get(counts)
    if cached is not None:
        return cached
    derived = exact.derive_products(counts)
    result = Evaluated(counts, derived, _fitness(derived))
    cache[counts] = result
    return result


def _random_composition(rng: random.Random, total: int) -> tuple[int, ...]:
    counts = [0] * len(exact.STATES)
    for _ in range(total):
        counts[rng.randrange(len(counts))] += 1
    return tuple(counts)


def _normalize_total(rng: random.Random, counts: list[int], total: int) -> None:
    while sum(counts) > total:
        positive = [index for index, count in enumerate(counts) if count > 0]
        counts[rng.choice(positive)] -= 1
    while sum(counts) < total:
        counts[rng.randrange(len(counts))] += 1


def _breed(
    rng: random.Random,
    left: tuple[int, ...],
    right: tuple[int, ...],
    total: int,
) -> tuple[int, ...]:
    child = [
        left[index] if rng.getrandbits(1) == 0 else right[index]
        for index in range(len(left))
    ]
    _normalize_total(rng, child, total)
    shifts = 1 + rng.randrange(4)
    for _ in range(shifts):
        donors = [index for index, count in enumerate(child) if count > 0]
        donor = rng.choice(donors)
        receiver = rng.randrange(len(child) - 1)
        if receiver >= donor:
            receiver += 1
        child[donor] -= 1
        child[receiver] += 1
    return tuple(child)


def _evaluated_sort_key(value: Evaluated) -> tuple[Any, ...]:
    return (*value.fitness.sort_key(), value.counts)


def _one_minimize_violation(counts: tuple[int, ...]) -> tuple[int, ...]:
    """Return a deterministic deletion-1-minimal witness for any partial-atom violation."""

    current = counts
    changed = True
    while changed:
        changed = False
        for index, count in enumerate(current):
            if count == 0 or sum(current) == 1:
                continue
            candidate = list(current)
            candidate[index] -= 1
            derived = exact.derive_products(candidate)
            evaluated = Evaluated(tuple(candidate), derived, _fitness(derived))
            if evaluated.fitness.violation:
                current = tuple(candidate)
                changed = True
                break
    return current


def _fraction_object(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def search(
    *,
    seed: int,
    total: int,
    population_size: int,
    generations: int,
    binary: Path,
) -> dict[str, Any]:
    exact.require(total >= 2, "evolutionary total must be at least two")
    exact.require(population_size >= 8, "population must be at least eight")
    exact.require(generations >= 1, "generation count must be positive")
    rng = random.Random(seed)
    cache: dict[tuple[int, ...], Evaluated] = {}

    concentrated = tuple([total] + [0] * (len(exact.STATES) - 1))
    uniform = [total // len(exact.STATES)] * len(exact.STATES)
    _normalize_total(rng, uniform, total)
    population: set[tuple[int, ...]] = {concentrated, tuple(uniform)}
    while len(population) < population_size:
        population.add(_random_composition(rng, total))

    generation_log: list[dict[str, Any]] = []
    global_best: Evaluated | None = None
    for generation in range(generations):
        evaluated = sorted(
            (_evaluate(counts, cache) for counts in population),
            key=_evaluated_sort_key,
        )
        best = evaluated[0]
        if global_best is None or _evaluated_sort_key(best) < _evaluated_sort_key(
            global_best
        ):
            global_best = best
        generation_log.append(
            {
                "generation": generation,
                "unique_population": len(population),
                "unique_evaluations_total": len(cache),
                "best_counts": list(best.counts),
                "best_identity": list(best.fitness.identity),
                "best_product": _fraction_object(best.fitness.product),
                "violation_found": best.fitness.violation,
            }
        )
        if best.fitness.violation:
            global_best = best
            break

        survivor_count = max(4, population_size // 4)
        survivors = [item.counts for item in evaluated[:survivor_count]]
        next_population = set(survivors)
        while len(next_population) < population_size:
            left = rng.choice(survivors)
            right = rng.choice(survivors)
            next_population.add(_breed(rng, left, right, total))
        population = next_population

    if global_best is None:
        raise exact.ProductVerificationError(
            "evolutionary search produced no evaluated table"
        )

    minimized = global_best.counts
    if global_best.fitness.violation:
        minimized = _one_minimize_violation(global_best.counts)
    final_derived = exact.derive_products(minimized)
    final_input = exact.canonical_input(minimized)
    final_certificate = _run_certifier(binary, final_input)
    final_checks = exact.verify_certificate(
        final_input, final_certificate, final_derived
    )
    final_fitness = _fitness(final_derived)

    canonical_log = exact.canonical_json_bytes(generation_log)
    return {
        "schema": "pid-rs/sxpid2-exact-product-evolutionary-falsifier/v1",
        "status": "counterexample_found"
        if final_fitness.violation
        else "no_counterexample_found_within_search",
        "configuration": {
            "seed_decimal": seed,
            "seed_hex": hex(seed),
            "fixed_total": total,
            "population": population_size,
            "generation_limit": generations,
            "state_order": [list(state) for state in exact.STATES],
            "fitness": (
                "exact rational product R for the closest nonzero informative or "
                "misinformative SxPID atom at fixed n; R<1 is a negative-partial-atom witness"
            ),
        },
        "search": {
            "generations_executed": len(generation_log),
            "unique_count_tables_evaluated": len(cache),
            "generation_log_sha256": hashlib.sha256(canonical_log).hexdigest(),
            "generation_log": generation_log,
        },
        "best_or_minimized_witness": {
            "counts": list(minimized),
            "total": sum(minimized),
            "identity": list(final_fitness.identity),
            "exact_product": _fraction_object(final_fitness.product),
            "violation": final_fitness.violation,
            "deletion_one_minimized_if_violation": final_fitness.violation,
        },
        "live_post_check": {
            "certificate_sha256": hashlib.sha256(final_certificate).hexdigest(),
            "certifier_executable_sha256": exact.sha256_file(binary),
            "expression_products": final_checks.expression_products,
            "exact_signs": final_checks.exact_signs,
        },
        "bindings": {
            "exact_product_source_sha256": exact.sha256_file(
                SCRIPT_DIR / "_exact_product.py"
            ),
            "challenge_source_sha256": exact.sha256_file(Path(__file__).resolve()),
        },
        "negative_boundary": (
            "Failure to find a counterexample is bounded search evidence only. It is not a "
            "universal nonnegativity proof, does not validate other PID definitions, and does "
            "not establish population, sampling, numerical-estimator, or application validity."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(argv)
    try:
        binary = (
            arguments.certifier.resolve()
            if arguments.certifier is not None
            else _default_binary().resolve()
        )
        exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
        result = search(
            seed=arguments.seed,
            total=arguments.total,
            population_size=arguments.population,
            generations=arguments.generations,
            binary=binary,
        )
        raw = exact.canonical_json_bytes(result) + b"\n"
        if arguments.output is not None:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_bytes(raw)
        sys.stdout.buffer.write(raw)
        return 2 if result["status"] == "counterexample_found" else 0
    except (
        OSError,
        subprocess.SubprocessError,
        exact.ProductVerificationError,
    ) as error:
        print(f"exact-product evolutionary challenge failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
