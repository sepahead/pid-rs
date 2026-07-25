#!/usr/bin/env python3
"""Mutation-test the Lean descriptor-factorization firewall."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = (
    ROOT
    / "audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean"
)
EXPECTED_SOURCE_SHA256 = (
    "7e1e71d76d63137ae055f17b1b771fdd2eb01935c7210bca79142691f7f06034"
)

MUTATIONS = (
    (
        "remove_factorization_premise",
        "theorem equal_descriptors_and_factorization_force_equal_atoms\n"
        "    {sys desc atm : Type*}\n"
        "    (descriptor : sys → desc)\n"
        "    (atom : sys → atm)\n"
        "    (factor : desc → atm)\n"
        "    (hfactor : ∀ system, atom system = factor (descriptor system))\n"
        "    {left right : sys}\n",
        "theorem equal_descriptors_and_factorization_force_equal_atoms\n"
        "    {sys desc atm : Type*}\n"
        "    (descriptor : sys → desc)\n"
        "    (atom : sys → atm)\n"
        "    (factor : desc → atm)\n"
        "    {left right : sys}\n",
    ),
    (
        "replace_quantity_difference_with_equality",
        "    (hquantity : quantity left ≠ quantity right) :\n",
        "    (hquantity : quantity left = quantity right) :\n",
    ),
    (
        "replace_atom_difference_with_equality",
        "    (hatom : atom left ≠ atom right) :\n",
        "    (hatom : atom left = atom right) :\n",
    ),
)

SEMANTIC_COUNTERMODELS = r"""

namespace PidDescriptorFactorizationCountermodels

/-- Equal descriptors do not force equal atoms without a factorization premise. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Bool := fun value => value
    descriptor false = descriptor true ∧ atom false ≠ atom true := by
  decide

/-- If the two quantities are equal, a universal reconstruction can exist. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Unit := fun _ => ()
    let quantity : Bool → Unit := fun _ => ()
    descriptor false = descriptor true ∧
      quantity false = quantity true ∧
      ∃ reconstruct : Unit → Unit,
        ∀ system, reconstruct (atom system) = quantity system := by
  dsimp
  constructor
  · rfl
  constructor
  · rfl
  · exact ⟨fun _ => (), fun _ => rfl⟩

/-- If the two atoms are equal, descriptor factorization can exist. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Unit := fun _ => ()
    descriptor false = descriptor true ∧
      atom false = atom true ∧
      ∃ factor : Unit → Unit,
        ∀ system, atom system = factor (descriptor system) := by
  dsimp
  constructor
  · rfl
  constructor
  · rfl
  · exact ⟨fun _ => (), fun _ => rfl⟩

end PidDescriptorFactorizationCountermodels
"""


class MutationError(RuntimeError):
    """The baseline or mutation experiment did not fail closed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def run_lean(lake: str, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [lake, "env", "lean", str(source)],
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=180,
    )


def main() -> int:
    try:
        require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Lean source digest drifted")
        lake = shutil.which("lake")
        require(lake is not None, "lake is not available")
        baseline = run_lean(lake, SOURCE)
        require(
            baseline.returncode == 0,
            f"baseline Lean source failed: {baseline.stderr}",
        )

        source_text = SOURCE.read_text(encoding="utf-8")
        results: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-descriptor-factorization-mutations-"
        ) as directory:
            root = Path(directory)
            countermodels = root / "SemanticCountermodels.lean"
            countermodel_text = source_text + SEMANTIC_COUNTERMODELS
            countermodels.write_text(countermodel_text, encoding="utf-8")
            countermodel_check = run_lean(lake, countermodels)
            require(
                countermodel_check.returncode == 0,
                f"semantic premise countermodels failed: {countermodel_check.stderr}",
            )
            for index, (name, before, after) in enumerate(MUTATIONS):
                require(
                    source_text.count(before) == 1,
                    f"mutation anchor is absent or ambiguous: {name}",
                )
                mutant_text = source_text.replace(before, after, 1)
                mutant = root / f"Mutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                checked = run_lean(lake, mutant)
                require(
                    checked.returncode != 0,
                    f"scientifically meaningful proof mutation survived: {name}",
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
            "schema": "pid-rs/lean-descriptor-factorization-mutations/v1",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "mutations_killed": len(results),
            "mutations": results,
            "semantic_countermodels_kernel_checked": 3,
            "semantic_countermodels_sha256": hashlib.sha256(
                SEMANTIC_COUNTERMODELS.encode("utf-8")
            ).hexdigest(),
            "boundary": (
                "The source mutations show that the proof uses the factorization and "
                "distinctness premises; three kernel-checked finite countermodels separately "
                "show those premises cannot be dropped in general. Neither route binds the "
                "abstract descriptors or atoms to a concrete PID implementation."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, subprocess.SubprocessError, MutationError) as error:
        print(f"Lean descriptor-factorization self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
