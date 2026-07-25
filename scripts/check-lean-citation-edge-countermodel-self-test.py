#!/usr/bin/env python3
"""Mutation-test the Lean citation-edge countermodel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = (
    ROOT
    / "audit/formal/lean-citation-edge/PidCitationEdgeCountermodel.lean"
)
EXPECTED_SOURCE_SHA256 = (
    "3c867cf1e5348bc6876f0d370ed746867ec90790a1bb1cd8a49fc7f00c0ee112"
)

MUTATIONS = (
    (
        "collapse_nontrivial_group",
        "abbrev C2 := ZMod 2",
        "abbrev C2 := ZMod 1",
    ),
    (
        "replace_right_identity_with_zero",
        "def rightArrow : C2 →+ C2 := AddMonoidHom.id C2",
        "def rightArrow : C2 →+ C2 := zeroHom C2 C2",
    ),
    (
        "erase_kernel_from_exactness",
        "  incoming.range = outgoing.ker",
        "  incoming.range = ⊤",
    ),
    (
        "claim_adjacent_arrow_bijective",
        "      ¬Function.Bijective adjacentArrow ∧",
        "      Function.Bijective adjacentArrow ∧",
    ),
    (
        "claim_adjacent_arrow_surjective",
        "      ¬Function.Surjective adjacentArrow ∧",
        "      Function.Surjective adjacentArrow ∧",
    ),
)


class MutationError(RuntimeError):
    """The baseline or a scientifically meaningful mutation did not fail closed."""


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
        require(baseline.returncode == 0, f"baseline Lean source failed: {baseline.stderr}")

        source_text = SOURCE.read_text(encoding="utf-8")
        results: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-citation-edge-lean-mutations-"
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
            "schema": "pid-rs/lean-citation-edge-countermodel-mutations/v1",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "mutations_killed": len(results),
            "mutations": results,
            "boundary": (
                "Mutations show that the Lean proof uses nontriviality, right-arrow identity, "
                "image/kernel exactness, and both negative adjacent-arrow conclusions. They do "
                "not validate the motivic premise or source-arrow binding."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, subprocess.SubprocessError, MutationError) as error:
        print(f"Lean citation-edge countermodel self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
