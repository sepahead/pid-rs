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
    "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af"
)
EXPECTED_TOOLCHAIN_SHA256 = (
    "302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b"
)
EXPECTED_LAKEFILE_SHA256 = (
    "ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0"
)
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.33.0"
EXPECTED_LEAN_VERSION = "4.33.0"
EXPECTED_LEAN_COMMIT = "d8b18978322de05a8f3dba51ef03cf5461676c17"
EXPECTED_LEAN_BUILD = "Release"
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
LEAN_VERSION_LINE = re.compile(
    r"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    r"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
    r"commit (?P<commit>[0-9a-f]{40}), "
    r"(?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)"
)


class LeanExactProductError(RuntimeError):
    """The source, pinned environment, compilation, or axiom audit failed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanExactProductError(message)


def parse_lean_version_probe(probe: subprocess.CompletedProcess[str]) -> str:
    """Validate the exact release identity and one-line process transport."""

    require(
        probe.returncode == 0,
        f"Lean version probe exited unsuccessfully: {probe.returncode}",
    )
    require(
        probe.stderr == "",
        f"Lean version probe emitted unexpected stderr: {probe.stderr!r}",
    )
    require(
        probe.stdout.endswith("\n"),
        "Lean version probe stdout lacks its final newline",
    )
    line = probe.stdout[:-1]
    require(
        "\n" not in line and "\r" not in line,
        "Lean version probe did not emit exactly one LF line",
    )
    matched = LEAN_VERSION_LINE.fullmatch(line)
    require(matched is not None, f"unexpected Lean version output: {probe.stdout!r}")
    identity = (
        matched.group("version"),
        matched.group("commit"),
        matched.group("build"),
    )
    expected = (EXPECTED_LEAN_VERSION, EXPECTED_LEAN_COMMIT, EXPECTED_LEAN_BUILD)
    require(
        identity == expected,
        f"unexpected Lean portable identity: expected {expected!r}, found {identity!r}",
    )
    return line


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
        lean_version = parse_lean_version_probe(version)

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
            "lean_version": lean_version,
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
