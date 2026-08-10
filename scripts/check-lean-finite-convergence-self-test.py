#!/usr/bin/env python3
"""Prove that the Lean finite-convergence source gate fails closed."""

from __future__ import annotations

from collections.abc import Callable
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-lean-finite-convergence.py"
SOURCE_PROJECT = ROOT / "audit" / "formal" / "lean"
COUNT_BRIDGE = (
    SOURCE_PROJECT / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean"
)
OBSERVED_NATIVE_DECIDE_AXIOM = (
    "PidFiniteConvergence.SemanticScratch.binary_key_univ_eq."
    "_native.native_decide.ax_1_1"
)


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pid_rs_check_lean_finite_convergence", CHECKER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load checker module specification: {CHECKER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_exact_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8", errors="strict")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"mutation fixture {path} contains {count} copies of {old!r}; expected one"
        )
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def append_text(path: Path, addition: str) -> None:
    source = path.read_text(encoding="utf-8", errors="strict")
    path.write_text(source + addition, encoding="utf-8")


def copy_source_fixture(checker: ModuleType, destination: Path) -> None:
    for relative in sorted(checker.EXPECTED_SOURCES):
        source = SOURCE_PROJECT / relative
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f"source fixture is not a regular file: {source}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def remove_root_import(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence.lean",
        "import PidFiniteConvergence.SxEventBridge\n",
        "",
    )


def rename_declaration(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "Deterministic.lean",
        "theorem eventually_positive_of_tendsto ",
        "theorem eventually_positive_of_tendsto_mutated ",
    )


def change_declaration_kind(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "Deterministic.lean",
        "theorem eventually_positive_of_tendsto ",
        "def eventually_positive_of_tendsto ",
    )


def drift_contract_bytes(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergenceSemanticContract.lean",
        "\n/- Unreviewed semantic-contract byte drift. -/\n",
    )


def change_contract_statement(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergenceSemanticContract.lean",
        "sxSourceEvent collections anchor ∩ targetBranchEvent anchor := by",
        "sxSourceEvent collections anchor ∪ targetBranchEvent anchor := by",
    )


def weaken_empirical_law_nonnegative_statement(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        """    0 ≤ empiricalLaw count key := by
  unfold empiricalLaw
  positivity
""",
        """    count key = count key := by
  rfl
""",
    )


def add_forbidden_axiom(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergence" / "LocalContinuity.lean",
        "\naxiom injected_unproved_statement : False\n",
    )


def regress_heterogeneous_key_while_spoofing_comments(project: Path) -> None:
    path = project / "PidFiniteConvergence" / "SxEventBridge.lean"
    replace_exact_once(
        path,
        "  ((source : sourceIndex) → sourceValue source) × targetValue",
        """  targetValue × ((source : sourceIndex) → sourceValue source)

/- A raw-text-only guard could be fooled by this stale comment:
sourceValue : sourceIndex → Type v
((source : sourceIndex) → sourceValue source) × targetValue
[∀ source, Fintype (sourceValue source)]
[∀ source, DecidableEq (sourceValue source)]
-/""",
    )


def widen_two_source_scope_boundary(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        "\n/- This bridge formally verifies Rust and its executable outputs. -/\n",
    )


def add_native_decide_to_semantic_contract(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergenceSemanticContract.lean",
        "        sxPid2AllBinaryKeys := by\n    decide\n  constructor\n",
        "        sxPid2AllBinaryKeys := by\n    native_decide\n  constructor\n",
    )


Mutation = tuple[str, Callable[[Path], None], str]


MUTATIONS: tuple[Mutation, ...] = (
    (
        "missing-root-import",
        remove_root_import,
        "must import the pinned checked submodule set exactly",
    ),
    (
        "declaration-rename",
        rename_declaration,
        "source declaration inventory mismatch in PidFiniteConvergence/Deterministic.lean",
    ),
    (
        "declaration-kind-change",
        change_declaration_kind,
        "source declaration inventory mismatch in PidFiniteConvergence/Deterministic.lean",
    ),
    (
        "semantic-contract-byte-drift",
        drift_contract_bytes,
        "Lean semantic-contract source digest mismatch",
    ),
    (
        "semantic-contract-statement-change",
        change_contract_statement,
        "Lean semantic-contract source digest mismatch",
    ),
    (
        "two-source-empirical-law-same-name-weakening",
        weaken_empirical_law_nonnegative_statement,
        "Lean two-source count/event bridge source digest mismatch",
    ),
    (
        "forbidden-axiom",
        add_forbidden_axiom,
        "forbidden proof placeholder, declaration, or native evaluator",
    ),
    (
        "heterogeneous-key-regression-with-comment-spoof",
        regress_heterogeneous_key_while_spoofing_comments,
        "must use the exact heterogeneous dependent Cartesian product",
    ),
    (
        "two-source-residual-scope-widening",
        widen_two_source_scope_boundary,
        "contains a forbidden residual-scope widening claim",
    ),
    (
        "semantic-contract-native-decide",
        add_native_decide_to_semantic_contract,
        "forbidden proof placeholder, declaration, or native evaluator",
    ),
)


def swap_source_one_collection(path: Path) -> None:
    replace_exact_once(path, "  | .sourceOne => {{0}}\n", "  | .sourceOne => {{1}}\n")
    replace_exact_once(path, "  | .sourceTwo => {{1}}\n", "  | .sourceTwo => {{0}}\n")


def replace_redundancy_union_with_joint(path: Path) -> None:
    replace_exact_once(
        path,
        "  | .redundancy => {{0}, {1}}\n",
        "  | .redundancy => {{0, 1}}\n",
    )


def erase_target_restriction(path: Path) -> None:
    replace_exact_once(
        path,
        "  sxTargetRestrictedEvent (sxPid2Collections node) anchor\n",
        "  sxSourceEvent (sxPid2Collections node) anchor\n",
    )


def replace_joint_with_source_one(path: Path) -> None:
    replace_exact_once(
        path,
        "  | .jointSources => {{0, 1}}\n",
        "  | .jointSources => {{0}}\n",
    )


def weaken_positive_support(path: Path) -> None:
    replace_exact_once(
        path,
        "  Finset.univ.filter fun key => 0 < count key\n",
        "  Finset.univ.filter fun key => 0 ≤ count key\n",
    )


LeanMutation = tuple[str, Callable[[Path], None]]


LEAN_SEMANTIC_MUTATIONS: tuple[LeanMutation, ...] = (
    ("source-one-source-two-swap", swap_source_one_collection),
    ("redundancy-union-to-joint", replace_redundancy_union_with_joint),
    ("target-restriction-erasure", erase_target_restriction),
    ("joint-node-to-marginal", replace_joint_with_source_one),
    ("positive-support-weakening", weaken_positive_support),
)


def expect_failure(
    checker: ModuleType,
    name: str,
    mutation: Callable[[Path], None],
    expected_message: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"pid-lean-{name}-") as temporary:
        project = Path(temporary) / "lean"
        copy_source_fixture(checker, project)
        mutation(project)
        original_project = checker.PROJECT
        checker.PROJECT = project
        try:
            checker.check_sources()
        except checker.LeanProofError as error:
            message = str(error)
            if expected_message not in message:
                raise RuntimeError(
                    f"{name}: checker failed for the wrong reason; "
                    f"expected {expected_message!r}, found {message!r}"
                ) from error
        else:
            raise RuntimeError(f"{name}: checker accepted the mutated source fixture")
        finally:
            checker.PROJECT = original_project


def run_isolated_lean(
    checker: ModuleType, lake: Path, source: Path
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for key in checker.REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    try:
        return subprocess.run(
            [str(lake), "env", "lean", str(source)],
            cwd=checker.PROJECT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=checker.TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"isolated Lean mutation replay failed: {error}") from error


def check_lean_semantic_mutations(checker: ModuleType) -> None:
    if not COUNT_BRIDGE.is_file() or COUNT_BRIDGE.is_symlink():
        raise RuntimeError(f"count/event bridge is not a regular file: {COUNT_BRIDGE}")
    lake = checker.find_lake()
    with tempfile.TemporaryDirectory(prefix="pid-lean-count-bridge-") as temporary:
        temporary_root = Path(temporary)
        baseline = temporary_root / "baseline" / COUNT_BRIDGE.name
        baseline.parent.mkdir(parents=True)
        shutil.copy2(COUNT_BRIDGE, baseline)
        baseline_process = run_isolated_lean(checker, lake, baseline)
        if baseline_process.returncode != 0:
            raise RuntimeError(
                "unmodified isolated count/event bridge did not compile before mutation; "
                f"stdout={baseline_process.stdout!r}, stderr={baseline_process.stderr!r}"
            )

        for name, mutation in LEAN_SEMANTIC_MUTATIONS:
            mutated = temporary_root / name / COUNT_BRIDGE.name
            mutated.parent.mkdir(parents=True)
            shutil.copy2(COUNT_BRIDGE, mutated)
            mutation(mutated)
            process = run_isolated_lean(checker, lake, mutated)
            if process.returncode == 0:
                raise RuntimeError(
                    f"{name}: pinned Lean accepted the semantic mutation"
                )
            diagnostic = process.stdout + process.stderr
            if "error" not in diagnostic.lower():
                raise RuntimeError(
                    f"{name}: Lean failed without a proof-error diagnostic: {diagnostic!r}"
                )


def main() -> int:
    checker = load_checker()
    source_count, declaration_count, theorem_names = checker.check_sources()
    if source_count != len(checker.EXPECTED_SOURCES):
        raise RuntimeError(
            f"baseline source count mismatch: {source_count} != "
            f"{len(checker.EXPECTED_SOURCES)}"
        )
    if declaration_count != checker.EXPECTED_DECLARATION_COUNT:
        raise RuntimeError(
            f"baseline declaration count mismatch: {declaration_count} != "
            f"{checker.EXPECTED_DECLARATION_COUNT}"
        )
    if len(theorem_names) != checker.EXPECTED_THEOREM_COUNT:
        raise RuntimeError(
            f"baseline theorem count mismatch: {len(theorem_names)} != "
            f"{checker.EXPECTED_THEOREM_COUNT}"
        )

    for name, mutation, expected_message in MUTATIONS:
        expect_failure(checker, name, mutation, expected_message)

    check_lean_semantic_mutations(checker)

    print(
        "OK: Lean finite-convergence gate self-test rejected "
        f"all {len(MUTATIONS)} static source mutations at their expected checker "
        f"diagnostics and all {len(LEAN_SEMANTIC_MUTATIONS)} baseline-first isolated "
        "Lean semantic mutations with nonzero Lean status plus an error diagnostic; "
        "kernel decide remains required and the observed "
        f"native evaluator axiom was {OBSERVED_NATIVE_DECIDE_AXIOM}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
