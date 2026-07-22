#!/usr/bin/env python3
"""Fail-closed runner for the bounded exact-real PID2 and PID3 SMT obligations."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "audit" / "formal" / "z3"
MUTATION_ANCHOR = b"(define-fun mutation_offset () Real 0)"
TIMEOUT_SECONDS = 20
EXPECTED_Z3_VERSION = "Z3 version 4.16.0 - 64 bit"


class Z3AlgebraError(RuntimeError):
    """Raised when an obligation cannot be established exactly as declared."""


@dataclass(frozen=True)
class ProofSpec:
    filename: str
    sha256: str
    obligation: str


PROOFS = (
    ProofSpec(
        filename="pid2-reconstruction.smt2",
        sha256="e43a7c3a2f75b06a3f1719a477cc4a707b04653b83968dc181afc35c9f339de8",
        obligation="two-source four-atom reconstruction",
    ),
    ProofSpec(
        filename="pid2-source-swap.smt2",
        sha256="01ff9b297dd690d9d2349246b7df05ac0dfc2ad22e164cdce14317db1602c3ec",
        obligation="two-source source-label exchange",
    ),
    ProofSpec(
        filename="pid2-self-redundancy-mobius.smt2",
        sha256="52e7de81fd844ed3fb260c33b9bacf26769e6932ec4d0f2639f8097926e19a84",
        obligation="two-source four-node Mobius and self-redundancy reconstruction",
    ),
    ProofSpec(
        filename="pid3-mobius-reconstruction.smt2",
        sha256="063da57b943b834c90657ba298b9ad5a9227f65cebce970ed56e62dd0b96e162",
        obligation="three-source 18-node Mobius and zeta reconstruction",
    ),
    ProofSpec(
        filename="pid3-source-permutation.smt2",
        sha256="002ecceec04a3a6d3fc36321aaa7c8ada8b8064389d035a1ffc7ba32b0137cad",
        obligation="three-source 18-node source-permutation equivariance",
    ),
)


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def find_z3(explicit: str | None = None) -> Path:
    candidate = explicit if explicit is not None else shutil.which("z3")
    if candidate is None:
        raise Z3AlgebraError("z3 executable was not found on PATH")
    path = Path(candidate).expanduser().resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise Z3AlgebraError(f"z3 executable is not an executable file: {path}")
    return path


def z3_version(z3: Path) -> str:
    try:
        process = subprocess.run(
            [str(z3), "--version"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Z3AlgebraError(f"could not execute z3 --version: {error}") from error
    if process.returncode != 0 or process.stderr != "":
        raise Z3AlgebraError(
            "z3 --version did not complete cleanly: "
            f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}"
        )
    lines = process.stdout.splitlines()
    if lines != [EXPECTED_Z3_VERSION]:
        raise Z3AlgebraError(f"unexpected z3 --version output: {process.stdout!r}")
    return lines[0]


def require_exact_proof_set(proof_dir: Path = PROOF_DIR) -> None:
    if not proof_dir.is_dir() or proof_dir.is_symlink():
        raise Z3AlgebraError(f"proof directory is missing or not a real directory: {proof_dir}")
    expected = {spec.filename for spec in PROOFS}
    actual = {entry.name for entry in proof_dir.iterdir()}
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise Z3AlgebraError(
            f"proof manifest mismatch: missing={missing}, unexpected={unexpected}"
        )


def validate_proof_source(path: Path, expected_sha256: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise Z3AlgebraError(f"proof is missing or not a regular file: {path}")
    raw = path.read_bytes()
    actual_sha256 = file_sha256(raw)
    if actual_sha256 != expected_sha256:
        raise Z3AlgebraError(
            f"proof digest mismatch for {path.name}: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Z3AlgebraError(f"proof is not UTF-8: {path}") from error
    required_counts = {
        "(set-logic QF_LRA)": 1,
        "(check-sat)": 1,
        "(exit)": 1,
        MUTATION_ANCHOR.decode("ascii"): 1,
    }
    for marker, expected_count in required_counts.items():
        count = source.count(marker)
        if count != expected_count:
            raise Z3AlgebraError(
                f"{path.name} must contain {expected_count} occurrence of {marker!r}; got {count}"
            )
    forbidden = (
        "(check-sat-assuming",
        "(get-model",
        "(get-proof",
        "(include",
        "(push",
        "(pop",
        "(reset",
    )
    present = [marker for marker in forbidden if marker in source]
    if present:
        raise Z3AlgebraError(f"{path.name} contains forbidden solver commands: {present}")
    if "(assert" not in source:
        raise Z3AlgebraError(f"{path.name} contains no assertion")
    return raw


def run_z3(z3: Path, proof: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [str(z3), "-smt2", str(proof)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Z3AlgebraError(f"z3 failed while checking {proof.name}: {error}") from error


def require_unsat(z3: Path, proof: Path) -> None:
    process = run_z3(z3, proof)
    if process.returncode != 0 or process.stdout != "unsat\n" or process.stderr != "":
        raise Z3AlgebraError(
            f"{proof.name} did not return exact UNSAT: "
            f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}"
        )


def verify_proof(z3: Path, proof: Path, expected_sha256: str) -> None:
    validate_proof_source(proof, expected_sha256)
    require_unsat(z3, proof)


def verify_all(z3: Path) -> str:
    version = z3_version(z3)
    require_exact_proof_set()
    for spec in PROOFS:
        verify_proof(z3, PROOF_DIR / spec.filename, spec.sha256)
    return version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Require exact UNSAT for the pinned PID2 and PID3 algebra obligations."
    )
    parser.add_argument(
        "--z3",
        help="path to the z3 CLI (default: resolve z3 from PATH)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        z3 = find_z3(args.z3)
        version = verify_all(z3)
    except Z3AlgebraError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: {len(PROOFS)} pinned QF_LRA PID algebra obligations returned exact UNSAT ({version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
