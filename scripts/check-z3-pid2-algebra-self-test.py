#!/usr/bin/env python3
"""Mutation test proving each pinned PID2 and PID3 SMT obligation can fail semantically."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-z3-pid2-algebra.py"
spec = importlib.util.spec_from_file_location("check_z3_pid2_algebra", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Z3 PID2 algebra checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


z3 = checker.find_z3()
checker.verify_all(z3)


def require_exact_sat_and_rejection(path: Path, label: str) -> None:
    process = checker.run_z3(z3, path)
    if process.returncode != 0 or process.stdout != "sat\n" or process.stderr != "":
        raise SystemExit(
            f"{label}: mutation did not return exact SAT: "
            f"exit={process.returncode}, stdout={process.stdout!r}, "
            f"stderr={process.stderr!r}"
        )
    try:
        checker.require_unsat(z3, path)
    except checker.Z3AlgebraError:
        pass
    else:
        raise SystemExit(f"{label}: SAT mutation unexpectedly passed")

mutated_anchor = checker.MUTATION_ANCHOR.replace(b" Real 0)", b" Real 1)")
if mutated_anchor == checker.MUTATION_ANCHOR:
    raise SystemExit("mutation anchor did not change")

for proof_spec in checker.PROOFS:
    original = checker.PROOF_DIR / proof_spec.filename
    raw = original.read_bytes()
    if raw.count(checker.MUTATION_ANCHOR) != 1:
        raise SystemExit(f"{proof_spec.filename}: expected exactly one mutation anchor")
    mutated = raw.replace(checker.MUTATION_ANCHOR, mutated_anchor, 1)

    with tempfile.TemporaryDirectory(prefix="pid-rs-z3-mutation-") as directory:
        path = Path(directory) / proof_spec.filename
        path.write_bytes(mutated)
        require_exact_sat_and_rejection(path, f"{proof_spec.filename} common-offset")


# These PID2 mutations attack three independent semantic dimensions rather than the shared
# mutation-offset row. They remain exact QF_LRA statements; none models binary64 or Rust.
pid2_semantic_mutations = (
    (
        "pid2-reconstruction.smt2",
        b"(+ (- mi_joint mi_s1 mi_s2) redundancy)",
        b"(- (- mi_joint mi_s1 mi_s2) redundancy)",
        "PID2 synergy sign",
    ),
    (
        "pid2-source-swap.smt2",
        b"(define-fun swapped_unique_s1 () Real (- mi_s2 redundancy))",
        b"(define-fun swapped_unique_s1 () Real (- mi_s1 redundancy))",
        "PID2 source-swap coordinate",
    ),
    (
        "pid2-self-redundancy-mobius.smt2",
        b"(define-fun recovered_s1 () Real (+ atom_redundancy atom_unique_s1))",
        b"(define-fun recovered_s1 () Real (+ atom_redundancy atom_unique_s2))",
        "PID2 Mobius reconstruction row",
    ),
)

for filename, old, new, label in pid2_semantic_mutations:
    original = checker.PROOF_DIR / filename
    raw = original.read_bytes()
    if raw.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one mutation anchor")
    mutated = raw.replace(old, new, 1)
    with tempfile.TemporaryDirectory(prefix="pid-rs-z3-pid2-semantic-") as directory:
        path = Path(directory) / filename
        path.write_bytes(mutated)
        require_exact_sat_and_rejection(path, label)

print(
    f"OK: {len(checker.PROOFS)} common-offset and "
    f"{len(pid2_semantic_mutations)} independent PID2 sign/coordinate/row QF_LRA mutations "
    "returned exact SAT and were rejected; no binary64, Rust-refinement, or estimator claim"
)
