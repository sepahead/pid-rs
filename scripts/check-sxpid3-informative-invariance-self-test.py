#!/usr/bin/env python3
"""Hostile source-mutation suite for check-sxpid3-informative-invariance.py."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-sxpid3-informative-invariance-self-test.py requires "
        "Python 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-sxpid3-informative-invariance.py"
EXPECTED_STDOUT_SHA256 = "1b89ba80a0f43eb036e9b9cecad6897716d97fb4ea2b6505d2a24d31e34bdc53"
TIMEOUT_SECONDS = 120


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(
    path: Path, optimized: bool = False, *, isolated: bool = True
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if isolated:
        command.extend(("-I", "-S", "-B"))
    if optimized:
        command.append("-O")
    command.append(str(path))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        env={"PATH": __import__("os").environ.get("PATH", "")},
    )


def replace_once(source: str, old: str, new: str, label: str) -> str:
    require(source.count(old) == 1, f"{label}: mutation target count was {source.count(old)}")
    return source.replace(old, new, 1)


def main() -> int:
    unisolated = run(CHECKER, isolated=False)
    require(unisolated.returncode == 2, "non-isolated checker exit")
    require(unisolated.stdout == "", "non-isolated checker wrote stdout")
    require(
        unisolated.stderr
        == (
            "ERROR: check-sxpid3-informative-invariance.py requires "
            "Python 3.11+ -I -S -B, with -O optional\n"
        ),
        "non-isolated checker diagnostic",
    )
    baseline = run(CHECKER)
    optimized = run(CHECKER, optimized=True)
    require(baseline.returncode == optimized.returncode == 0, baseline.stderr + optimized.stderr)
    require(baseline.stderr == optimized.stderr == "", "baseline wrote stderr")
    require(baseline.stdout == optimized.stdout, "normal and optimized outputs differ")
    require(
        hashlib.sha256(baseline.stdout.encode("utf-8")).hexdigest()
        == EXPECTED_STDOUT_SHA256,
        "canonical stdout identity",
    )
    payload = json.loads(baseline.stdout)
    require(payload["gate"] == "GO", "baseline gate")
    require(
        payload["exhaustive_binary_scope"]
        == {
            "binary_labeled_count_tables": 20_348,
            "distinct_source_marginal_counts": 1_286,
            "informative_atom_product_verdicts": 366_264,
            "informative_cumulative_product_verdicts": 366_264,
            "maximum_total_count": 5,
            "primitive_rational_laws": 20_164,
        },
        "bounded corpus counts",
    )
    require(
        payload["prohibited_transfer_witness"]["constant_target"]
        != payload["prohibited_transfer_witness"]["copied_target"],
        "negative-control pair",
    )
    require(
        payload["semantic_registry_sha256"]
        == "34243da13712935eb39935b01461d4837235c5ad4bcbfee0a4c02e25b4fed0be",
        "semantic registry drift anchor",
    )

    source = CHECKER.read_text(encoding="utf-8")
    mutations = (
        (
            "missing-mask",
            "tuple(range(1, 8))",
            "tuple(range(1, 7))",
            "ANTICHAIN.registry",
        ),
        (
            "source-bit-registry",
            "SOURCE_BITS: Final[tuple[int, ...]] = (1, 2, 4)",
            "SOURCE_BITS: Final[tuple[int, ...]] = (2, 1, 4)",
            "MASK.source_bit_registry",
        ),
        (
            "coordinate-remap",
            "for index, bit in enumerate(SOURCE_BITS) if mask & bit",
            "for index, bit in enumerate(reversed(SOURCE_BITS)) if mask & bit",
            "MASK.coordinate_sentinels",
        ),
        (
            "zeta-transpose",
            "int(redundancy_le(atom, cumulative)) for atom in nodes",
            "int(redundancy_le(cumulative, atom)) for atom in nodes",
            "ZETA.row_signatures",
        ),
        (
            "zeta-row-permutation",
            "return [\n        [int(redundancy_le(atom, cumulative)) for atom in nodes]\n        for cumulative in nodes\n    ]",
            "return list(reversed([\n        [int(redundancy_le(atom, cumulative)) for atom in nodes]\n        for cumulative in nodes\n    ]))",
            "ZETA.row_signatures",
        ),
        (
            "mobius-row-alias",
            "return tuple(rows)",
            "return tuple(reversed(rows))",
            "MOBIUS.sparse_rows",
        ),
        (
            "event-inner-connective",
            "return any(\n        all(anchor[index] == candidate[index]",
            "return any(\n        any(anchor[index] == candidate[index]",
            "SIGMA_KAPPA.support_witness",
        ),
        (
            "source-count-weight",
            "product *= Fraction(total, event_count) ** anchor_count",
            "product *= Fraction(total, event_count)",
            "INVARIANCE.cumulative_product",
        ),
        (
            "joint-count-weight",
            "product *= Fraction(total, event_count) ** cell_count",
            "product *= Fraction(total, event_count)",
            "INVARIANCE.cumulative_product",
        ),
        (
            "joint-route-target-restriction",
            "if event_matches(antichain, anchor, candidate_source)",
            "if _candidate_target == JOINT_STATES[joint_index][1]\n"
            "                and event_matches(antichain, anchor, candidate_source)",
            "INVARIANCE.cumulative_product",
        ),
        (
            "target-restriction",
            "if candidate_target == anchor_target\n            and event_matches",
            "if candidate_target != anchor_target\n            and event_matches",
            "NEGATIVE_CONTROL.event_bounds",
        ),
        (
            "sigma-kappa-witness",
            "witness = (0, 1, 0)",
            "witness = (1, 1, 0)",
            "SIGMA_KAPPA.support_witness",
        ),
        (
            "copied-target-collapse",
            "copied_target[JOINT_STATES.index((second, 1))] = 1",
            "copied_target[JOINT_STATES.index((second, 0))] = 1",
            "NEGATIVE_CONTROL.misinformative_changes",
        ),
        (
            "omit-total-five",
            "for total in range(1, MAX_TOTAL + 1):",
            "for total in range(1, MAX_TOTAL):",
            "EXHAUSTIVE.table_count",
        ),
        (
            "primitive-law-count",
            "int(math.gcd(*joint_counts) == 1)",
            "int(math.gcd(*joint_counts) == 2)",
            "EXHAUSTIVE.primitive_law_count",
        ),
        (
            "semantic-registry-anchor",
            "34243da13712935eb39935b01461d4837235c5ad4bcbfee0a4c02e25b4fed0be",
            "34243da13712935eb39935b01461d4837235c5ad4bcbfee0a4c02e25b4fed0bd",
            "SEMANTIC.registry_sha256",
        ),
    )

    with tempfile.TemporaryDirectory(prefix="pid-rs-sxpid3-invariance-self-test-") as directory:
        temporary = Path(directory)
        for label, old, new, expected_code in mutations:
            mutated = replace_once(source, old, new, label)
            path = temporary / f"{label}.py"
            path.write_text(mutated, encoding="utf-8")
            result = run(path)
            expected_stderr = f"SxPID3 informative invariance: {expected_code}\n"
            require(result.returncode == 1, f"{label}: exit {result.returncode}")
            require(result.stdout == "", f"{label}: unexpected stdout {result.stdout!r}")
            require(
                result.stderr == expected_stderr,
                f"{label}: expected {expected_stderr!r}, found {result.stderr!r}",
            )

    summary = {
        "baseline_stdout_sha256": EXPECTED_STDOUT_SHA256,
        "format": "/pid-rs/sxpid3-informative-invariance-self-test/v1",
        "gate": "GO",
        "mutation_count": len(mutations),
        "nonisolated_checker_rejected": True,
        "optimized_parity": True,
    }
    print(json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        print(f"SxPID3 informative invariance self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
