#!/usr/bin/env python3
"""Prove that the Lean finite-convergence source gate fails closed."""

from __future__ import annotations

from collections.abc import Callable
import importlib.util
from pathlib import Path
import shutil
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-lean-finite-convergence.py"
SOURCE_PROJECT = ROOT / "audit" / "formal" / "lean"


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
        "forbidden-axiom",
        add_forbidden_axiom,
        "forbidden proof placeholder or declaration",
    ),
    (
        "heterogeneous-key-regression-with-comment-spoof",
        regress_heterogeneous_key_while_spoofing_comments,
        "must use the exact heterogeneous dependent Cartesian product",
    ),
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

    print(
        "OK: Lean finite-convergence gate self-test killed "
        f"all {len(MUTATIONS)} source mutations for their intended reasons"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
