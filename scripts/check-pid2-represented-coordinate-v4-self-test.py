#!/usr/bin/env python3
"""Hostile self-test for the PID2 represented-coordinate revision-4 checker.

The self-test executes a copied checker outside the live repository, audits its Python AST for
host-floating-point escape hatches, and requires independent semantic and source-custody mutations
to fail closed.  It does not execute Rust or make an estimator-validity claim.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-pid2-represented-coordinate-v4.py"
SOURCE_PATHS = (
    "crates/pid-core/src/exact_binary64.rs",
    "crates/pid-core/src/pid2.rs",
    "crates/pid-core/tests/pid2.rs",
    "crates/pid-core/src/bin/exp0.rs",
)
MODEL_OUTPUT = (
    "OK: scope=model; exact integer/Fraction PID2 model checked 1023 accepted scale-family "
    "seeds, 1023 scaled cases reaching one rejected endpoint, all 16 signed-zero tuples, "
    "Neumaier steps, the "
    "declared boundary/overflow controls, and all 5 conditioning outcomes; source=not-read; "
    "compiled=not-run; no estimator, "
    "calibration, paper-defect, or Rust-refinement claim\n"
)
MODEL_SOURCE_OUTPUT = (
    "OK: scope=model-source; exact integer/Fraction PID2 model checked 1023 accepted "
    "scale-family seeds, 1023 scaled cases reaching one rejected endpoint, all 16 signed-zero "
    "tuples, Neumaier "
    "steps, the declared boundary/overflow controls, and all 5 conditioning outcomes; source=4 "
    "exact files; compiled=not-run; "
    "no estimator, calibration, paper-defect, or Rust-refinement claim\n"
)
MAX_CAPTURE_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 120

SEMANTIC_MUTATIONS = (
    (
        "guard boundary",
        "IDENTITY_GUARD_MAX_ORDERED_DISTANCE = 32",
        "IDENTITY_GUARD_MAX_ORDERED_DISTANCE = 31",
    ),
    ("family cardinality", "FAMILY_MAX_SCALE = 1023", "FAMILY_MAX_SCALE = 1022"),
    (
        "ties-to-even comparator",
        "twice_remainder > denominator or (",
        "twice_remainder >= denominator or (",
    ),
    (
        "family synergy coordinate",
        "expected_synergy = ((0x7FE - k_scale) << 52) | (1 << 51)",
        "expected_synergy = ((0x7FE - k_scale) << 52) | (1 << 50)",
    ),
    (
        "family exact scaling factor",
        "factor = (0x3FF + k_scale) << 52",
        "factor = (0x3FE + k_scale) << 52",
    ),
    (
        "15-position control",
        '== 15,\n        "historical 15-position reconstruction changed"',
        '== 14,\n        "historical 15-position reconstruction changed"',
    ),
    (
        "49-position control",
        '== 49,\n        "exact 49-position reconstruction changed"',
        '== 48,\n        "exact 49-position reconstruction changed"',
    ),
    (
        "5-position exact guard",
        '== 5, "exact distance is not 5"',
        '== 4, "exact distance is not 5"',
    ),
    (
        "155-position left association",
        '== 155, "left distance is not 155"',
        '== 154, "left distance is not 155"',
    ),
    (
        "signed-zero unique coordinate",
        "expected_unique_one = SIGN_MASK if i1 == SIGN_MASK and redundancy == 0 else 0",
        "expected_unique_one = SIGN_MASK if i1 == SIGN_MASK and redundancy == SIGN_MASK else 0",
    ),
    (
        "constructor candidate reduction",
        "synergy = exact_synergy_bits(i1, i2, joint, redundancy)",
        "synergy = historical_synergy_bits(i1, i2, joint, redundancy)",
    ),
    (
        "inclusive identity bound",
        "and ordered_distance(reconstructed, expected) <= (",
        "and ordered_distance(reconstructed, expected) < (",
    ),
    (
        "false scale premise",
        "exact_scale_bound = 16 * joint_magnitude",
        "exact_scale_bound = 0 * joint_magnitude",
    ),
    (
        "Neumaier terminal trace",
        "(POSITIVE_INFINITY_BITS, CANONICAL_NAN_BITS),",
        "(POSITIVE_INFINITY_BITS, NEGATIVE_INFINITY_BITS),",
    ),
    (
        "scaled rejected endpoint",
        "endpoint = (0, 0x7FCF_FFFF_FFFF_FFFE, 0x7FEF_FFFF_FFFF_FFFF, 0)",
        "endpoint = (0, 0x7FCF_FFFF_FFFF_FFFD, 0x7FEF_FFFF_FFFF_FFFF, 0)",
    ),
    (
        "exact synergy overflow status",
        'modeled_constructor(*exact_synergy_overflow).status == "atom_nonfinite"',
        'modeled_constructor(*exact_synergy_overflow).status == "accepted"',
    ),
    (
        "minimum-subnormal encoder exponent",
        "scaled_round_to_integer(magnitude, 1074)",
        "scaled_round_to_integer(magnitude, 1073)",
    ),
    (
        "finite conditioning status",
        'require(finite.status == "finite", "finite conditioning status changed")',
        'require(finite.status == "all_terms_zero", "finite conditioning status changed")',
    ),
)


class SelfTestError(RuntimeError):
    """Raised when a hostile control does not behave as required."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def checker_command(script: Path, scope: str, repo_root: Path, optimized: bool) -> tuple[str, ...]:
    flags = ("-O",) if optimized else ()
    return (
        sys.executable,
        *flags,
        "-I",
        "-S",
        "-B",
        str(script),
        "--scope",
        scope,
        "--repo-root",
        str(repo_root),
    )


def run_checker(
    script: Path,
    scope: str,
    repo_root: Path,
    optimized: bool = False,
) -> subprocess.CompletedProcess[str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
    }
    process = subprocess.run(
        checker_command(script, scope, repo_root, optimized),
        cwd=script.parent.parent,
        env=environment,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    captured = len(process.stdout.encode()) + len(process.stderr.encode())
    require(captured <= MAX_CAPTURE_BYTES, "checker output exceeded the bounded capture")
    return process


def require_success(
    process: subprocess.CompletedProcess[str], expected_stdout: str, label: str
) -> None:
    require(process.returncode == 0, f"{label} failed: {process.stderr!r}")
    require(process.stdout == expected_stdout, f"{label} stdout changed: {process.stdout!r}")
    require(process.stderr == "", f"{label} emitted stderr: {process.stderr!r}")


def require_semantic_failure(process: subprocess.CompletedProcess[str], label: str) -> None:
    require(process.returncode != 0, f"{label} mutation escaped with success")
    require(process.stdout == "", f"{label} mutation emitted stdout: {process.stdout!r}")
    require(
        process.stderr.startswith("ERROR: "),
        f"{label} did not fail through checker: {process.stderr!r}",
    )
    require(
        "Traceback" not in process.stderr,
        f"{label} mutation crashed instead of failing closed",
    )


def audit_no_host_float_oracle(source: str) -> None:
    tree = ast.parse(source, filename=str(CHECKER))
    forbidden_imports = {"array", "decimal", "math", "numpy", "struct"}
    forbidden_calls = {"float", "fromhex"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise SelfTestError(f"host float literal at line {node.lineno}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                require(
                    alias.name.split(".", 1)[0] not in forbidden_imports,
                    f"forbidden numeric import {alias.name} at line {node.lineno}",
                )
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            require(
                node.module.split(".", 1)[0] not in forbidden_imports,
                f"forbidden numeric import {node.module} at line {node.lineno}",
            )
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                require(
                    node.func.id not in forbidden_calls,
                    f"forbidden numeric call {node.func.id} at line {node.lineno}",
                )
            if isinstance(node.func, ast.Attribute):
                require(
                    node.func.attr not in forbidden_calls,
                    f"forbidden numeric call {node.func.attr} at line {node.lineno}",
                )


def copy_checker_root(destination: Path) -> Path:
    copied_checker = destination / "scripts/check-pid2-represented-coordinate-v4.py"
    copied_checker.parent.mkdir(parents=True)
    shutil.copyfile(CHECKER, copied_checker)
    for relative in SOURCE_PATHS:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return copied_checker


def mutate_once(source: str, old: str, new: str, label: str) -> str:
    occurrences = source.count(old)
    require(occurrences == 1, f"{label} mutation anchor count is {occurrences}, expected 1")
    return source.replace(old, new, 1)


def check_copied_root_isolation() -> int:
    source_failures = 0
    with tempfile.TemporaryDirectory(prefix="pid2-rev4-copy-") as temporary:
        temporary_root = Path(temporary)
        copied_root = temporary_root / "copied-repository"
        copied_checker = copy_checker_root(copied_root)
        nonexistent_root = temporary_root / "must-not-be-read"

        for optimized in (False, True):
            require_success(
                run_checker(copied_checker, "model", nonexistent_root, optimized),
                MODEL_OUTPUT,
                f"copied model optimized={optimized}",
            )
            require_success(
                run_checker(copied_checker, "model-source", copied_root, optimized),
                MODEL_SOURCE_OUTPUT,
                f"copied model-source optimized={optimized}",
            )

        digest_target = copied_root / SOURCE_PATHS[0]
        original = digest_target.read_bytes()
        digest_target.write_bytes(original + b"\n")
        require_semantic_failure(
            run_checker(copied_checker, "model-source", copied_root),
            "copied source digest",
        )
        digest_target.write_bytes(original)
        source_failures += 1

        missing_target = copied_root / SOURCE_PATHS[1]
        missing_bytes = missing_target.read_bytes()
        missing_target.unlink()
        require_semantic_failure(
            run_checker(copied_checker, "model-source", copied_root),
            "missing copied source",
        )
        missing_target.write_bytes(missing_bytes)
        source_failures += 1

        symlink_target = copied_root / SOURCE_PATHS[2]
        symlink_bytes = symlink_target.read_bytes()
        symlink_payload = temporary_root / "symlink-payload.rs"
        symlink_payload.write_bytes(symlink_bytes)
        symlink_target.unlink()
        symlink_target.symlink_to(symlink_payload)
        require_semantic_failure(
            run_checker(copied_checker, "model-source", copied_root),
            "symlinked copied source",
        )
        symlink_target.unlink()
        symlink_target.write_bytes(symlink_bytes)
        source_failures += 1

        root_link = temporary_root / "linked-repository"
        root_link.symlink_to(copied_root, target_is_directory=True)
        require_semantic_failure(
            run_checker(copied_checker, "model-source", root_link),
            "symlinked repository root",
        )
        source_failures += 1

        require_success(
            run_checker(copied_checker, "model-source", copied_root),
            MODEL_SOURCE_OUTPUT,
            "restored copied source root",
        )
    return source_failures


def check_semantic_mutations(source: str) -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="pid2-rev4-mutations-") as temporary:
        temporary_root = Path(temporary)
        for index, (label, old, new) in enumerate(SEMANTIC_MUTATIONS):
            mutation_root = temporary_root / f"mutation-{index:02d}"
            mutation_root.mkdir()
            mutated_checker = mutation_root / "check.py"
            mutated_checker.write_text(
                mutate_once(source, old, new, label),
                encoding="utf-8",
            )
            process = run_checker(
                mutated_checker,
                "model",
                mutation_root / "source-must-not-be-read",
            )
            require_semantic_failure(process, label)
            rejected += 1
    return rejected


def main() -> int:
    try:
        require(CHECKER.is_file() and not CHECKER.is_symlink(), "checker is not a regular file")
        source = CHECKER.read_text(encoding="utf-8")
        audit_no_host_float_oracle(source)
        source_failures = check_copied_root_isolation()
        semantic_failures = check_semantic_mutations(source)
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired, SelfTestError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "OK: PID2 represented-coordinate v4 hostile self-test; "
        f"AST host-float audit passed; {semantic_failures} semantic and "
        f"{source_failures} source-custody mutations failed closed; copied-root model/source "
        "passed under normal and -O; compiled=not-run; no estimator, calibration, "
        "paper-defect, or Rust-refinement claim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
