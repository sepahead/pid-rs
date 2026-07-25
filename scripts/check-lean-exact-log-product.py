#!/usr/bin/env python3
"""Kernel-check the standalone exact log-product/sign theorem under pinned Lean/mathlib."""

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
SOURCE = ROOT / "audit/formal/lean-exact-log-product/PidExactLogProduct.lean"
EXPECTED_SOURCE_SHA256 = (
    "f0727ea3061d561ba89ba49edebece971ce03bdecf03e0c32774a1c080dc07bf"
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
    "PidExactLogProduct.log_finset_zpow_product",
    "PidExactLogProduct.scaled_log_sum_eq_log_product",
    "PidExactLogProduct.scaled_log_pos_iff",
    "PidExactLogProduct.scaled_log_neg_iff",
    "PidExactLogProduct.scaled_log_eq_zero_iff",
    "PidExactLogProduct.two_nontrivial_logs_cancel",
    "PidExactLogProduct.retained_five_term_product_eq_one",
)
PERMITTED_AXIOMS = "[propext, Classical.choice, Quot.sound]"
PROHIBITED_SOURCE = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")


class LeanExactProductError(RuntimeError):
    """The source, pinned environment, compilation, or axiom audit failed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanExactProductError(message)


def main() -> int:
    try:
        require(
            sha256(SOURCE) == EXPECTED_SOURCE_SHA256,
            "Lean theorem source digest drifted",
        )
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

        query = (
            source_text
            + "\n"
            + "\n".join(f"#print axioms {theorem}" for theorem in THEOREMS)
            + "\n"
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-exact-log-product-lean-"
        ) as directory:
            query_path = Path(directory) / "PidExactLogProductCheck.lean"
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
        require(
            not checked.stderr.strip(),
            f"Lean emitted unexpected stderr: {checked.stderr}",
        )
        lines = [line.strip() for line in checked.stdout.splitlines() if line.strip()]
        expected_lines = [
            f"'{theorem}' depends on axioms: {PERMITTED_AXIOMS}" for theorem in THEOREMS
        ]
        require(
            lines == expected_lines, f"Lean theorem axiom inventory changed: {lines!r}"
        )

        result = {
            "schema": "pid-rs/lean-exact-log-product-check/v1",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "lake_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "lean_toolchain": EXPECTED_TOOLCHAIN,
            "lean_version": version.stdout.strip(),
            "theorems_kernel_checked": len(THEOREMS),
            "permitted_axioms": ["propext", "Classical.choice", "Quot.sound"],
            "boundary": (
                "Generic log/product/sign algebra only; concrete SxPID event extraction, "
                "lattice binding, executable refinement, sampling, and scientific validity "
                "remain separate obligations."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, subprocess.SubprocessError, LeanExactProductError) as error:
        print(f"Lean exact-log-product check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
