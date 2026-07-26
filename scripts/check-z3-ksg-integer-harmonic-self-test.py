#!/usr/bin/env python3
"""Baseline-first semantic mutation suite for the independently encoded KSG SMT route."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-z3-ksg-integer-harmonic.py"
spec = importlib.util.spec_from_file_location("check_z3_ksg_harmonic", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Z3 KSG harmonic checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


MUTATIONS = (
    (
        "ksg-digamma-cancellation.smt2",
        "nonzero_cancellation_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-digamma-cancellation.smt2",
        "misbind_y_digamma_premise",
        b"(assert (= (psi y) (- (harmonic (- y 1)) euler_constant)))",
        b"(assert (= (psi y) (- (harmonic (- x 1)) euler_constant)))",
    ),
    (
        "ksg-symmetric-range.smt2",
        "nonzero_range_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_min_with_left_argument",
        b"(define-fun min_xy () Int (ite (<= x y) x y))",
        b"(define-fun min_xy () Int x)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_max_with_left_argument",
        b"(define-fun max_xy () Int (ite (<= x y) y x))",
        b"(define-fun max_xy () Int x)",
    ),
    (
        "ksg-index-maps.smt2",
        "nonzero_exclusive_predecessor_offset",
        b"(define-fun mutation_offset () Int 0)",
        b"(define-fun mutation_offset () Int 1)",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_exclusive_x_twice",
        b"(define-fun exclusive_x () Int (+ nx 1))",
        b"(define-fun exclusive_x () Int (+ nx 2))",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_anchor_inclusive_x",
        b"(define-fun inclusive_argument_x () Int inclusive_x)",
        b"(define-fun inclusive_argument_x () Int (+ inclusive_x 1))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "tighten_local_lower_bound",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_lower_harmonic_order_premise",
        b"(assert (<= h_k h_min))",
        b"(assert (<= h_min h_k))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_middle_harmonic_order_premise",
        b"(assert (<= h_min h_max))",
        b"(assert (<= h_max h_min))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_upper_harmonic_order_premise",
        b"(assert (<= h_max h_n))",
        b"(assert (<= h_n h_max))",
    ),
)


class MutationError(RuntimeError):
    """The baseline failed or a meaningful SMT mutation was not exposed as SAT."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def main() -> int:
    try:
        z3 = checker.find_z3()
        version = checker.verify_all(z3)
        results: list[dict[str, object]] = []
        for index, (filename, name, before, after) in enumerate(MUTATIONS):
            original = checker.PROOF_DIR / filename
            raw = original.read_bytes()
            require(
                raw.count(before) == 1,
                f"mutation anchor is absent or ambiguous: {name}",
            )
            mutated = raw.replace(before, after, 1)
            with tempfile.TemporaryDirectory(
                prefix="pid-ksg-z3-mutation-"
            ) as directory:
                path = Path(directory) / f"Mutation{index}-{filename}"
                path.write_bytes(mutated)
                process = checker.run_z3(z3, path)
                checker.require_exact_result(process, "sat", name)
                try:
                    checker.require_unsat(z3, path)
                except checker.Z3KsgHarmonicError:
                    pass
                else:
                    raise MutationError(f"SAT mutation unexpectedly passed: {name}")
            results.append(
                {
                    "proof": filename,
                    "name": name,
                    "killed": True,
                    "mutant_sha256": hashlib.sha256(mutated).hexdigest(),
                }
            )

        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-mutations/v2",
            "status": "passed",
            "z3_version": version,
            "checker_source_sha256": checker.file_sha256(
                Path(__file__).resolve().read_bytes()
            ),
            "mutations_killed": len(results),
            "mutations": results,
            "boundary": (
                "Mutations expose changed cancellation, premise binding, min/max, exclusive "
                "successor, inclusive identity, predecessor consequences, explicit harmonic "
                "order premises, and the local bound as SAT. They do not validate the analytic "
                "digamma premise, harmonic finite-sum recurrence or monotonicity, count geometry, "
                "estimator, support, floating-point, PID, or Rust claims."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        MutationError,
        checker.Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG harmonic self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
