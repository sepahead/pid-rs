#!/usr/bin/env python3
"""Check independently encoded exact KSG harmonic/index obligations with pinned Z3.

The SMT route proves four-term cancellation under explicit positive-integer digamma instances,
the min/max range identity and source symmetry for an arbitrary harmonic-value function, the
exclusive/inclusive index maps, and the local full-tail bound under explicit harmonic-order
instances. It does not prove the digamma premise, define or prove monotonicity of harmonic finite
sums, or establish neighbor geometry, estimator behavior, support, floating point, PID semantics,
or Rust refinement. The finite-sum definition, recurrence, monotonicity, and unconditional
rational harmonic bound are checked separately by Lean.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "audit/formal/z3-ksg-harmonic"
EXPECTED_Z3_VERSION = "Z3 version 4.16.0 - 64 bit"
TIMEOUT_SECONDS = 30
COUNTEREXAMPLE_ASSERTION = b"(assert (not theorem_holds))"
POSITIVE_ASSERTION = b"(assert theorem_holds)"


class Z3KsgHarmonicError(RuntimeError):
    """A source, pin, satisfiability preflight, or exact UNSAT check failed."""


@dataclass(frozen=True)
class ProofSpec:
    filename: str
    sha256: str
    obligation: str
    typed_premise: str


PROOFS = (
    ProofSpec(
        filename="ksg-digamma-cancellation.smt2",
        sha256="8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4",
        obligation="four-term exact-real cancellation at four positive integer arguments",
        typed_premise=(
            "four asserted instances psi(m)=harmonic(m-1)-euler_constant; analytic truth open"
        ),
    ),
    ProofSpec(
        filename="ksg-index-maps.smt2",
        sha256="71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1",
        obligation="exclusive count+1 and anchor-inclusive identity maps with exact domains",
        typed_premise="declared integer count bounds; neighbor production and geometry open",
    ),
    ProofSpec(
        filename="ksg-local-bound-v4.smt2",
        sha256="33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
        obligation=(
            "direct/range equality and full-tail bound under explicit local harmonic-order premises"
        ),
        typed_premise=(
            "H(k-1)<=H(min-1)<=H(max-1)<=H(n-1); universal harmonic monotonicity is proved in Lean"
        ),
    ),
    ProofSpec(
        filename="ksg-symmetric-range.smt2",
        sha256="add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9",
        obligation="min/max range reassociation and source exchange for arbitrary harmonic values",
        typed_premise="positive integer index order only; harmonic values are uninterpreted",
    ),
)


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Z3KsgHarmonicError(message)


def find_z3(explicit: str | None = None) -> Path:
    candidate = explicit if explicit is not None else shutil.which("z3")
    require(candidate is not None, "z3 executable was not found on PATH")
    path = Path(candidate).expanduser().resolve()
    require(
        path.is_file() and os.access(path, os.X_OK), f"z3 is not executable: {path}"
    )
    return path


def z3_version(z3: Path) -> str:
    process = subprocess.run(
        [str(z3), "--version"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    require(
        process.returncode == 0
        and process.stdout == EXPECTED_Z3_VERSION + "\n"
        and process.stderr == "",
        "unexpected z3 version result: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    return process.stdout.strip()


def require_exact_proof_set() -> None:
    require(
        PROOF_DIR.is_dir() and not PROOF_DIR.is_symlink(),
        f"proof directory is missing or symlinked: {PROOF_DIR}",
    )
    expected = {spec.filename for spec in PROOFS}
    actual = {entry.name for entry in PROOF_DIR.iterdir()}
    require(
        actual == expected,
        f"proof manifest mismatch: missing={sorted(expected - actual)}, "
        f"unexpected={sorted(actual - expected)}",
    )


def validate_proof_source(path: Path, expected_sha256: str) -> bytes:
    require(
        path.is_file() and not path.is_symlink(), f"proof is not a regular file: {path}"
    )
    raw = path.read_bytes()
    require(
        file_sha256(raw) == expected_sha256,
        f"proof digest mismatch for {path.name}: got {file_sha256(raw)}",
    )
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Z3KsgHarmonicError(f"proof is not UTF-8: {path}") from error
    required_counts = {
        "(set-logic QF_UFLIRA)": 1,
        "(define-fun theorem_holds () Bool": 1,
        COUNTEREXAMPLE_ASSERTION.decode("ascii"): 1,
        "(check-sat)": 1,
        "(exit)": 1,
    }
    for marker, expected_count in required_counts.items():
        require(
            source.count(marker) == expected_count,
            f"{path.name}: expected {expected_count} occurrence of {marker!r}, "
            f"got {source.count(marker)}",
        )
    forbidden = (
        "(forall",
        "(exists",
        "(check-sat-assuming",
        "(get-model",
        "(get-proof",
        "(include",
        "(push",
        "(pop",
        "(reset",
    )
    present = [marker for marker in forbidden if marker in source]
    require(not present, f"{path.name} contains forbidden solver commands: {present}")
    require("(assert" in source, f"{path.name} contains no assertion")
    return raw


def run_z3(z3: Path, proof: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(z3), "-smt2", str(proof)],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def require_exact_result(
    process: subprocess.CompletedProcess[str],
    expected: str,
    label: str,
) -> None:
    require(
        process.returncode == 0
        and process.stdout == expected + "\n"
        and process.stderr == "",
        f"{label} did not return exact {expected.upper()}: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )


def require_unsat(z3: Path, proof: Path) -> None:
    require_exact_result(run_z3(z3, proof), "unsat", proof.name)


def require_satisfiable_positive_preflight(z3: Path, path: Path, raw: bytes) -> None:
    require(
        raw.count(COUNTEREXAMPLE_ASSERTION) == 1,
        f"{path.name}: counterexample assertion is absent or ambiguous",
    )
    positive = raw.replace(COUNTEREXAMPLE_ASSERTION, POSITIVE_ASSERTION, 1)
    with tempfile.TemporaryDirectory(prefix="pid-ksg-z3-positive-") as directory:
        candidate = Path(directory) / path.name
        candidate.write_bytes(positive)
        require_exact_result(
            run_z3(z3, candidate), "sat", f"{path.name} positive preflight"
        )


def verify_all(z3: Path) -> str:
    version = z3_version(z3)
    require_exact_proof_set()
    for spec in PROOFS:
        path = PROOF_DIR / spec.filename
        raw = validate_proof_source(path, spec.sha256)
        require_satisfiable_positive_preflight(z3, path, raw)
        require_unsat(z3, path)
    return version


def main() -> int:
    try:
        z3 = find_z3()
        version = verify_all(z3)
        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-check/v2",
            "status": "passed",
            "z3_version": version,
            "checker_source_sha256": file_sha256(Path(__file__).resolve().read_bytes()),
            "proofs": [
                {
                    "filename": spec.filename,
                    "sha256": spec.sha256,
                    "obligation": spec.obligation,
                    "typed_premise": spec.typed_premise,
                    "positive_preflight": "sat",
                    "negated_obligation": "unsat",
                }
                for spec in PROOFS
            ],
            "boundary": (
                "Quantifier-free exact Int/Real/uninterpreted-function obligations only. The "
                "local bound uses explicit harmonic-order premises; finite-sum recurrence and "
                "universal rational harmonic monotonicity are independently checked in Lean. "
                "Digamma truth, count geometry, binary64, estimators, support, PID semantics, "
                "Rust refinement, calibration, and consumers remain outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG integer-harmonic check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
