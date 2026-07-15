#!/usr/bin/env python3
"""Mutation test proving each pinned PID2 SMT obligation can fail semantically."""

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
        process = checker.run_z3(z3, path)
        if process.returncode != 0 or process.stdout != "sat\n" or process.stderr != "":
            raise SystemExit(
                f"{proof_spec.filename}: mutation did not return exact SAT: "
                f"exit={process.returncode}, stdout={process.stdout!r}, "
                f"stderr={process.stderr!r}"
            )
        try:
            checker.require_unsat(z3, path)
        except checker.Z3AlgebraError:
            pass
        else:
            raise SystemExit(f"{proof_spec.filename}: SAT mutation unexpectedly passed")

print(f"OK: {len(checker.PROOFS)} PID2 algebra mutations returned exact SAT and were rejected")
