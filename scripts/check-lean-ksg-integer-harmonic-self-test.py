#!/usr/bin/env python3
"""Baseline-first mutation test for the scoped revision-4 Lean KSG harmonic proof."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-lean-ksg-integer-harmonic.py"
spec = importlib.util.spec_from_file_location("check_lean_ksg_harmonic", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Lean KSG harmonic checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


MUTATIONS = (
    (
        "shift_harmonic_denominator",
        "  ∑ i ∈ Finset.range m, (((i + 1 : ℕ) : ℚ)⁻¹)",
        "  ∑ i ∈ Finset.range m, (((i + 2 : ℕ) : ℚ)⁻¹)",
    ),
    (
        "reverse_harmonic_monotonicity",
        "theorem harmonic_monotone : Monotone harmonic := by",
        "theorem harmonic_monotone : Antitone harmonic := by",
    ),
    (
        "break_range_maximum",
        "harmonic (max x y - 1)) -",
        "harmonic (max x x - 1)) -",
    ),
    (
        "break_range_minimum",
        "(harmonic (min x y - 1) - harmonic (k - 1))",
        "(harmonic (min x x - 1) - harmonic (k - 1))",
    ),
    (
        "break_four_term_coefficient",
        "    psi k + psi n - psi x - psi y =\n"
        "      harmonicReal (k - 1) + harmonicReal (n - 1) -",
        "    psi k + psi n - psi x + psi y =\n"
        "      harmonicReal (k - 1) + harmonicReal (n - 1) -",
    ),
    (
        "shift_exclusive_argument_twice",
        "def exclusiveArgument (count : ℕ) : ℕ :=\n  count + 1",
        "def exclusiveArgument (count : ℕ) : ℕ :=\n  count + 2",
    ),
    (
        "shift_anchor_inclusive_argument",
        "def inclusiveArgument (count : ℕ) : ℕ :=\n  count",
        "def inclusiveArgument (count : ℕ) : ℕ :=\n  count + 1",
    ),
    (
        "make_exclusive_upper_bound_strict",
        "    k ≤ exclusiveArgument count ∧ exclusiveArgument count ≤ n := by",
        "    k ≤ exclusiveArgument count ∧ exclusiveArgument count < n := by",
    ),
    (
        "corrupt_exclusive_count_formula",
        "harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny := by",
        "harmonic (k - 1) + harmonic (n - 1) - harmonic (nx + 1) - harmonic ny := by",
    ),
    (
        "corrupt_source_swap_target",
        "    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x := by",
        "    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x + 1 := by",
    ),
    (
        "break_rational_to_real_range_cast",
        "    ((symmetricRangeTerm k n x y : ℚ) : ℝ) = symmetricRangeTermReal k n x y := by",
        "    ((symmetricRangeTerm k n x y : ℚ) : ℝ) = symmetricRangeTermReal k n x y + 1 := by",
    ),
    (
        "strengthen_zero_tail_to_one",
        "      0 ≤ lowerTail ∧ lowerTail ≤ fullTail := by",
        "      1 ≤ lowerTail ∧ lowerTail ≤ fullTail := by",
    ),
    (
        "reverse_rational_lower_bound",
        "    (-fullTail ≤ symmetricRangeTerm k n x y ∧",
        "    (fullTail ≤ symmetricRangeTerm k n x y ∧",
    ),
    (
        "offset_combined_real_value",
        "    psi k + psi n - psi x - psi y = value ∧",
        "    psi k + psi n - psi x - psi y = value + 1 ∧",
    ),
)


class MutationError(RuntimeError):
    """The baseline failed or a scientifically meaningful Lean mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def main() -> int:
    try:
        lake, _version = checker.verify_environment_and_source()
        baseline = checker.run_lean(lake, checker.SOURCE)
        require(
            baseline.returncode == 0,
            f"baseline Lean source failed before mutation: {baseline.stderr}",
        )
        require(
            not baseline.stderr.strip(),
            f"baseline Lean source emitted stderr before mutation: {baseline.stderr}",
        )

        source_text = checker.SOURCE.read_text(encoding="utf-8")
        results: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-ksg-harmonic-lean-mutations-"
        ) as directory:
            root = Path(directory)
            for index, (name, before, after) in enumerate(MUTATIONS):
                require(
                    source_text.count(before) == 1,
                    f"mutation anchor is absent or ambiguous: {name}",
                )
                mutant_text = source_text.replace(before, after, 1)
                mutant = root / f"Mutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                checked = checker.run_lean(lake, mutant)
                require(
                    checked.returncode != 0,
                    f"scientifically meaningful Lean mutation survived: {name}",
                )
                results.append(
                    {
                        "name": name,
                        "killed": True,
                        "mutant_sha256": hashlib.sha256(
                            mutant_text.encode("utf-8")
                        ).hexdigest(),
                    }
                )

        evidence = {
            "schema": "pid-rs/lean-ksg-integer-harmonic-mutations/v1",
            "status": "passed",
            "source_sha256": checker.EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": checker.sha256(Path(__file__).resolve()),
            "mutations_killed": len(results),
            "mutations": results,
            "boundary": (
                "These mutations show load-bearing use of the finite-sum denominator, harmonic "
                "monotonicity, min/max range, four signs, source symmetry, rational-to-real "
                "coercion, full-tail bounds, combined exact-real conclusion, exclusive successor, "
                "inclusive identity, and index bounds. They do not validate the typed digamma "
                "premise or any estimator, support, floating-point, PID, or Rust claim."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        MutationError,
        checker.LeanKsgHarmonicError,
    ) as error:
        print(f"Lean KSG harmonic self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
