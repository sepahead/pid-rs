#!/usr/bin/env python3
"""Kernel-check the finite citation-edge countermodel under pinned Lean/mathlib.

The checked theorem is intentionally local: it rejects transfer of an isomorphism or
surjectivity predicate to an adjacent arrow in an exact sequence. It does not formalize motivic
homotopy, validate an imported source theorem, establish a source-arrow correspondence, or prove
anything about PID.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = (
    ROOT
    / "audit/formal/lean-citation-edge/PidCitationEdgeCountermodel.lean"
)
EXPECTED_SOURCE_SHA256 = (
    "3c867cf1e5348bc6876f0d370ed746867ec90790a1bb1cd8a49fc7f00c0ee112"
)
EXPECTED_MANIFEST_SHA256 = (
    "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
)
EXPECTED_TOOLCHAIN_SHA256 = (
    "2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e"
)
EXPECTED_LAKEFILE_SHA256 = (
    "1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1"
)
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.32.0"
THEOREMS = (
    "PidCitationEdgeCountermodel.exact_at_internal_zero",
    "PidCitationEdgeCountermodel.exact_at_middle",
    "PidCitationEdgeCountermodel.exact_at_right",
    "PidCitationEdgeCountermodel.right_arrow_bijective",
    "PidCitationEdgeCountermodel.right_arrow_surjective",
    "PidCitationEdgeCountermodel.adjacent_arrow_not_surjective",
    "PidCitationEdgeCountermodel.adjacent_arrow_not_bijective",
    "PidCitationEdgeCountermodel.middle_nontrivial",
    "PidCitationEdgeCountermodel.retained_adjacent_arrow_countermodel",
)
PERMITTED_AXIOMS = frozenset(("propext", "Classical.choice", "Quot.sound"))
PROHIBITED_SOURCE = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")
REQUIRED_SCOPE_SENTINELS = (
    "same witness",
    "not independent mathematical counterexamples",
    "does not formalize motivic homotopy",
    "source-to-formal-arrow correspondence",
    "any PID result",
)


class LeanCitationEdgeError(RuntimeError):
    """The source, pinned environment, compilation, or axiom audit failed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanCitationEdgeError(message)


def parse_axiom_inventory(output: str) -> dict[str, frozenset[str]]:
    pattern = re.compile(
        r"'([^']+)' (?:depends on axioms: \[(.*?)\]|does not depend on any axioms)",
        re.DOTALL,
    )
    inventory: dict[str, frozenset[str]] = {}
    for match in pattern.finditer(output):
        payload = match.group(2)
        axioms = (
            frozenset()
            if payload is None
            else frozenset(part.strip() for part in payload.split(",") if part.strip())
        )
        inventory[match.group(1)] = axioms
    return inventory


def main() -> int:
    try:
        require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Lean source digest drifted")
        require(
            sha256(PROJECT / "lake-manifest.json") == EXPECTED_MANIFEST_SHA256,
            "pinned Lake manifest digest drifted",
        )
        require(
            sha256(PROJECT / "lean-toolchain") == EXPECTED_TOOLCHAIN_SHA256,
            "Lean toolchain file digest drifted",
        )
        require(
            sha256(PROJECT / "lakefile.toml") == EXPECTED_LAKEFILE_SHA256,
            "Lake configuration digest drifted",
        )
        require(
            (PROJECT / "lean-toolchain").read_text(encoding="utf-8").strip()
            == EXPECTED_TOOLCHAIN,
            "Lean toolchain identifier drifted",
        )

        source_text = SOURCE.read_text(encoding="utf-8")
        require(
            PROHIBITED_SOURCE.search(source_text) is None,
            "Lean source contains a prohibited proof escape",
        )
        for sentinel in REQUIRED_SCOPE_SENTINELS:
            require(sentinel in source_text, f"Lean scope sentinel is absent: {sentinel}")

        lake = shutil.which("lake")
        require(lake is not None, "lake is not available")
        version = subprocess.run(
            [lake, "env", "lean", "--version"],
            cwd=PROJECT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )
        require(version.returncode == 0, f"Lean version probe failed: {version.stderr}")
        require("Lean (version 4.32.0" in version.stdout, "unexpected Lean version")

        query = source_text + "\n" + "\n".join(
            f"#print axioms {theorem}" for theorem in THEOREMS
        ) + "\n"
        with tempfile.TemporaryDirectory(
            prefix="pid-citation-edge-lean-"
        ) as directory:
            query_path = Path(directory) / "PidCitationEdgeCountermodelCheck.lean"
            query_path.write_text(query, encoding="utf-8")
            checked = subprocess.run(
                [lake, "env", "lean", str(query_path)],
                cwd=PROJECT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=180,
            )
        require(checked.returncode == 0, f"Lean kernel check failed: {checked.stderr}")
        require(not checked.stderr.strip(), f"Lean emitted unexpected stderr: {checked.stderr}")

        inventory = parse_axiom_inventory(checked.stdout)
        require(set(inventory) == set(THEOREMS), "Lean theorem axiom inventory changed")
        for theorem, axioms in inventory.items():
            require(
                axioms <= PERMITTED_AXIOMS,
                f"theorem {theorem} uses unapproved axioms: {sorted(axioms)}",
            )

        result = {
            "schema": "pid-rs/lean-citation-edge-countermodel-check/v1",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "lake_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "lean_toolchain": EXPECTED_TOOLCHAIN,
            "lean_version": version.stdout.strip(),
            "theorems_kernel_checked": len(THEOREMS),
            "permitted_axioms": sorted(PERMITTED_AXIOMS),
            "boundary": (
                "Finite additive-group countermodel only. It is orthogonal implementation and "
                "kernel evidence for the same C2 witness checked by Python, not a second "
                "mathematical route; motivic source truth, arrow correspondence, and PID remain "
                "outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, subprocess.SubprocessError, LeanCitationEdgeError) as error:
        print(f"Lean citation-edge countermodel check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
