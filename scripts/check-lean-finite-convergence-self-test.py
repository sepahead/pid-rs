#!/usr/bin/env python3
"""Prove that the Lean finite-convergence source gate fails closed."""

from __future__ import annotations

import ast
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
ATOM_BRIDGE = SOURCE_PROJECT / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean"
ATOM_SEMANTIC_CONTRACT = (
    SOURCE_PROJECT / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
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


def check_version_parser(checker: ModuleType) -> int:
    """Exercise exact Lean release identity and strict stream framing."""

    valid = (
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        f"{checker.EXPECTED_LEAN_COMMIT}, Release)\n"
    )
    baseline = subprocess.CompletedProcess(
        args=["lake", "env", "lean", "--version"],
        returncode=0,
        stdout=valid,
        stderr="",
    )
    if checker.parse_lean_version_probe(baseline) != valid[:-1]:
        raise RuntimeError("valid Lean 4.33 release identity did not round-trip")
    cases = (
        ("nonzero", 1, valid, ""),
        ("stderr", 0, valid, "diagnostic\n"),
        ("missing-final-newline", 0, valid[:-1], ""),
        ("extra-line", 0, valid + "extra\n", ""),
        ("crlf", 0, valid[:-1] + "\r\n", ""),
        (
            "malformed-platform",
            0,
            valid.replace("arm64-apple-darwin24.6.0", "darwin", 1),
            "",
        ),
        ("wrong-version", 0, valid.replace("4.33.0", "4.32.2", 1), ""),
        (
            "wrong-commit",
            0,
            valid.replace(checker.EXPECTED_LEAN_COMMIT, "0" * 40, 1),
            "",
        ),
        (
            "uppercase-commit",
            0,
            valid.replace(
                checker.EXPECTED_LEAN_COMMIT,
                checker.EXPECTED_LEAN_COMMIT.upper(),
                1,
            ),
            "",
        ),
        ("debug-build", 0, valid.replace("Release)", "Debug)", 1), ""),
        ("trailing-space", 0, valid.replace(")\n", ") \n", 1), ""),
    )
    for name, returncode, stdout, stderr in cases:
        probe = subprocess.CompletedProcess(
            args=baseline.args,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
        try:
            checker.parse_lean_version_probe(probe)
        except checker.LeanProofError:
            continue
        raise RuntimeError(f"hostile Lean version probe survived: {name}")
    return len(cases)


def check_fresh_kernel_replay_route() -> None:
    """Bind the primary checker to a cache-independent LeanChecker invocation."""

    tree = ast.parse(CHECKER.read_text(encoding="utf-8", errors="strict"))
    matches: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "run_checked" or len(node.args) < 2:
            continue
        label = node.args[1]
        if isinstance(label, ast.Constant) and label.value == "Lean kernel replay":
            matches.append(node)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one Lean kernel replay route, found {len(matches)}"
        )
    command = matches[0].args[0]
    if not isinstance(command, ast.List) or len(command.elts) != 5:
        raise RuntimeError("Lean kernel replay argv is not the exact five-part list")
    executable = command.elts[0]
    if not (
        isinstance(executable, ast.Call)
        and isinstance(executable.func, ast.Name)
        and executable.func.id == "str"
        and len(executable.args) == 1
        and isinstance(executable.args[0], ast.Name)
        and executable.args[0].id == "lake"
        and not executable.keywords
    ):
        raise RuntimeError(
            "Lean kernel replay does not use the resolved Lake executable"
        )
    tail = tuple(
        element.value if isinstance(element, ast.Constant) else None
        for element in command.elts[1:]
    )
    if tail != ("env", "leanchecker", "--fresh", "PidFiniteConvergence"):
        raise RuntimeError(f"Lean kernel replay is not fresh: {tail!r}")


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


def replace_scoped_transparency_with_broad(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        "set_option backward.isDefEq.respectTransparency.types false in",
        "set_option backward.isDefEq.respectTransparency false",
    )


def remove_scoped_transparency(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        "set_option backward.isDefEq.respectTransparency.types false in\n",
        "",
    )


def add_scoped_transparency_to_option_free_module(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "SxEventBridge.lean",
        "set_option warningAsError true\n",
        "set_option warningAsError true\n"
        "set_option backward.isDefEq.respectTransparency.types false in\n",
    )


def remove_scoped_transparency_in_keyword(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        "set_option backward.isDefEq.respectTransparency.types false in",
        "set_option backward.isDefEq.respectTransparency.types false",
    )


def change_scoped_transparency_value(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        "set_option backward.isDefEq.respectTransparency.types false in",
        "set_option backward.isDefEq.respectTransparency.types true in",
    )


def move_scoped_transparency_to_wrong_command(project: Path) -> None:
    path = project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean"
    replace_exact_once(
        path,
        "set_option backward.isDefEq.respectTransparency.types false in\n",
        "",
    )
    replace_exact_once(
        path,
        "/-- The source collections defining each fixed two-source cumulative node. -/\n",
        "set_option backward.isDefEq.respectTransparency.types false in\n"
        "/-- The source collections defining each fixed two-source cumulative node. -/\n",
    )


def move_proof_term_transparency_to_wrong_proof(project: Path) -> None:
    path = project / "PidFiniteConvergenceSemanticContract.lean"
    replace_exact_once(
        path,
        "(sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor) = 23 :=\n"
        "  set_option backward.isDefEq.respectTransparency.types false in by",
        "(sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor) = 23 := by",
    )
    replace_exact_once(
        path,
        "sxPid2TargetRestrictedEvent .jointSources sxPid2AsymmetricAnchor := by",
        "sxPid2TargetRestrictedEvent .jointSources sxPid2AsymmetricAnchor :=\n"
        "  set_option backward.isDefEq.respectTransparency.types false in by",
    )


def move_scoped_transparency_with_comment_spoof(project: Path) -> None:
    move_scoped_transparency_to_wrong_command(project)
    append_text(
        project / "PidFiniteConvergence" / "TwoSourceCountEventBridge.lean",
        """
/- A raw-text target check could be spoofed by this stale reviewed shape:
set_option backward.isDefEq.respectTransparency.types false in
deriving instance Fintype for SxPid2Node
-/
""",
    )


def drift_sx_event_bridge_bytes(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergence" / "SxEventBridge.lean",
        "\n/- Unreviewed finite categorical Sx event-bridge byte drift. -/\n",
    )


def remove_atom_root_import(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence.lean",
        "import PidFiniteConvergence.TwoSourceMobiusAtomBridge\n",
        "",
    )


def rename_atom_declaration(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "theorem sx_pid2_zeta_after_mobius\n",
        "theorem sx_pid2_zeta_after_mobius_mutated\n",
    )


def drift_atom_bridge_bytes(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "\n/- Unreviewed two-source atom-bridge byte drift. -/\n",
    )


def drift_atom_semantic_contract_bytes(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean",
        "\n/- Unreviewed SxPID2 atom semantic-contract byte drift. -/\n",
    )


def change_atom_contract_coordinate_card(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean",
        "Fintype.card SxPid2Coordinate = 24 := by",
        "Fintype.card SxPid2Coordinate = 23 := by",
    )


def remove_atom_scope_boundary(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "The mathematics here is about the paper-defined finite categorical functional after its keyed",
        "The exact supplied-count scope begins after keyed",
    )


def widen_atom_scope_boundary(project: Path) -> None:
    append_text(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "\n/- This bridge proves component nonnegativity. -/\n",
    )


def weaken_atom_completeness_same_name(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """theorem sx_pid2_coordinate_order_complete :
    sxPid2CoordinateOrder.toFinset = (Finset.univ : Finset SxPid2Coordinate) := by
  decide
""",
        """theorem sx_pid2_coordinate_order_complete :
    sxPid2CoordinateOrder = sxPid2CoordinateOrder := by
  rfl
""",
    )


def swap_atom_node_order(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "[.sourceOne, .sourceTwo, .jointSources, .redundancy]",
        "[.sourceTwo, .sourceOne, .jointSources, .redundancy]",
    )


def swap_atom_output_order(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "[.uniqueOne, .uniqueTwo, .synergy, .redundancy]",
        "[.uniqueTwo, .uniqueOne, .synergy, .redundancy]",
    )


def swap_atom_component_order(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "[.informative, .misinformative, .net]",
        "[.misinformative, .informative, .net]",
    )


def change_atom_unique_sign(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "| .uniqueOne, .redundancy => -1",
        "| .uniqueOne, .redundancy => 1",
    )


def change_atom_net_component(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "| .net => localCumulativeNet law node anchor",
        "| .net => localCumulativeInformative law node anchor",
    )


def change_informative_count_denominator(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "(eventCount count (sxPid2SourceEvent node anchor) : ℚ)",
        "(eventCount count (targetBranchEvent anchor) : ℚ)",
    )


def change_misinformative_count_numerator(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "(eventCount count (targetBranchEvent anchor) : ℚ) /",
        "(totalCount count : ℚ) /",
    )


def change_empirical_weight(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """  ∑ anchor ∈ positiveSupport count,
    ((count anchor : ℝ) / (totalCount count : ℝ)) *
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ)
""",
        """  ∑ anchor ∈ positiveSupport count,
    ((totalCount count : ℝ) / (totalCount count : ℝ)) *
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ)
""",
    )


def change_product_exponent(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        "countComponentArgument count component node anchor ^ count anchor",
        "countComponentArgument count component node anchor ^ totalCount count",
    )


def change_rational_synergy_product(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """      (countCumulativeRationalProduct count component .jointSources *
        countCumulativeRationalProduct count component .redundancy) /
""",
        """      (countCumulativeRationalProduct count component .sourceOne *
        countCumulativeRationalProduct count component .redundancy) /
""",
    )


def change_scaled_log_factor(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """    averagedCumulativeCountExpression count component node =
      (1 / (totalCount count : ℝ)) *
""",
        """    averagedCumulativeCountExpression count component node =
      (totalCount count : ℝ) *
""",
    )


def change_contract_count_argument(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean",
        "weightedAnchorZeroZero = 2 / 3 ∧",
        "weightedAnchorZeroZero = 3 / 2 ∧",
    )


def change_contract_product_value(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean",
        """countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceOne = 256 / 27 ∧""",
        """countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceOne = 255 / 27 ∧""",
    )


def add_native_decide_to_atom_bridge(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """theorem sx_pid2_coordinate_order_complete :
    sxPid2CoordinateOrder.toFinset = (Finset.univ : Finset SxPid2Coordinate) := by
  decide
""",
        """theorem sx_pid2_coordinate_order_complete :
    sxPid2CoordinateOrder.toFinset = (Finset.univ : Finset SxPid2Coordinate) := by
  native_decide
""",
    )


def mutate_contract_count_argument(path: Path) -> None:
    replace_exact_once(
        path,
        "weightedAnchorZeroZero = 2 / 3 ∧",
        "weightedAnchorZeroZero = 3 / 2 ∧",
    )


def mutate_contract_product_value(path: Path) -> None:
    replace_exact_once(
        path,
        "countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceOne = 256 / 27 ∧",
        "countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceOne = 255 / 27 ∧",
    )


def mutate_contract_mobius_zero(path: Path) -> None:
    replace_exact_once(
        path,
        "sxPid2MobiusCoefficient .uniqueOne .sourceTwo = 0 ∧",
        "sxPid2MobiusCoefficient .uniqueOne .sourceTwo = 1 ∧",
    )


def mutate_contract_zeta_zero(path: Path) -> None:
    replace_exact_once(
        path,
        "sxPid2ZetaCoefficient .sourceOne .uniqueTwo = 0 ∧",
        "sxPid2ZetaCoefficient .sourceOne .uniqueTwo = 1 ∧",
    )


def mutate_contract_real_rational_cast(path: Path) -> None:
    replace_exact_once(
        path,
        """    countCoordinateRealProduct weightedAsymmetricCount coordinate =
      ((countCoordinateRationalProduct weightedAsymmetricCount coordinate : ℚ) : ℝ) := by
""",
        """    countCoordinateRealProduct weightedAsymmetricCount coordinate =
      ((countCoordinateRationalProduct weightedAsymmetricCount coordinate : ℚ) : ℝ) + 1 := by
""",
    )


def mutate_contract_positive_conclusion(path: Path) -> None:
    replace_exact_once(
        path,
        """example :
    0 < averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
      (.atom .informative .uniqueOne) := by
""",
        """example :
    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
      (.atom .informative .uniqueOne) < 0 := by
""",
    )


def mutate_contract_negative_conclusion(path: Path) -> None:
    replace_exact_once(
        path,
        """example :
    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
        (.atom .net .uniqueTwo) < 0 := by
""",
        """example :
    0 < averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
      (.atom .net .uniqueTwo) := by
""",
    )


def mutate_contract_zero_conclusion(path: Path) -> None:
    replace_exact_once(
        path,
        """    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
        (.atom .misinformative .uniqueOne) = 0 := by
""",
        """    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
        (.atom .misinformative .uniqueOne) = 1 := by
""",
    )


def mutate_contract_helper_inventory(path: Path) -> None:
    replace_exact_once(path, "    ``weighted_atom_products,\n", "")


def change_contract_mobius_zero(project: Path) -> None:
    mutate_contract_mobius_zero(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_zeta_zero(project: Path) -> None:
    mutate_contract_zeta_zero(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_real_rational_cast(project: Path) -> None:
    mutate_contract_real_rational_cast(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_positive_conclusion(project: Path) -> None:
    mutate_contract_positive_conclusion(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_negative_conclusion(project: Path) -> None:
    mutate_contract_negative_conclusion(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_zero_conclusion(project: Path) -> None:
    mutate_contract_zero_conclusion(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def change_contract_helper_inventory(project: Path) -> None:
    mutate_contract_helper_inventory(
        project / "PidFiniteConvergenceSxPid2AtomSemanticContract.lean"
    )


def weaken_mobius_zeta_inverse_same_name(project: Path) -> None:
    replace_exact_once(
        project / "PidFiniteConvergence" / "TwoSourceMobiusAtomBridge.lean",
        """theorem sx_pid2_zeta_after_mobius
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) (node : SxPid2Node) :
    sxPid2ZetaTransform (sxPid2MobiusTransform cumulative) node = cumulative node := by
  cases node
  all_goals simp [sxPid2ZetaTransform, sxPid2MobiusTransform] <;> abel
""",
        """theorem sx_pid2_zeta_after_mobius
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) (node : SxPid2Node) :
    cumulative node = cumulative node := by
  rfl
""",
    )


Mutation = tuple[str, Callable[[Path], None], str]


MUTATIONS: tuple[Mutation, ...] = (
    (
        "broad-transparency-compatibility",
        replace_scoped_transparency_with_broad,
        "must be exactly the three reviewed command-scoped Fintype-derivation routes",
    ),
    (
        "missing-scoped-transparency-compatibility",
        remove_scoped_transparency,
        "must be exactly the three reviewed command-scoped Fintype-derivation routes",
    ),
    (
        "extra-scoped-transparency-compatibility",
        add_scoped_transparency_to_option_free_module,
        "must be exactly the three reviewed command-scoped Fintype-derivation routes",
    ),
    (
        "unscoped-types-transparency-compatibility",
        remove_scoped_transparency_in_keyword,
        "must be exactly the three reviewed command-scoped Fintype-derivation routes",
    ),
    (
        "wrong-value-scoped-transparency-compatibility",
        change_scoped_transparency_value,
        "must be exactly the three reviewed command-scoped Fintype-derivation routes",
    ),
    (
        "moved-scoped-transparency-compatibility",
        move_scoped_transparency_to_wrong_command,
        "moved away from its reviewed Fintype-derivation or proof-term target",
    ),
    (
        "moved-proof-term-transparency-compatibility",
        move_proof_term_transparency_to_wrong_proof,
        "moved away from its reviewed Fintype-derivation or proof-term target",
    ),
    (
        "moved-transparency-with-comment-spoof",
        move_scoped_transparency_with_comment_spoof,
        "moved away from its reviewed Fintype-derivation or proof-term target",
    ),
    (
        "sx-event-bridge-byte-drift",
        drift_sx_event_bridge_bytes,
        "Lean finite categorical Sx event bridge source digest mismatch",
    ),
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
    (
        "missing-atom-root-import",
        remove_atom_root_import,
        "must import the pinned checked submodule set exactly",
    ),
    (
        "atom-declaration-rename",
        rename_atom_declaration,
        "source declaration inventory mismatch in PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean",
    ),
    (
        "atom-bridge-byte-drift",
        drift_atom_bridge_bytes,
        "Lean two-source Mobius/atom bridge source digest mismatch",
    ),
    (
        "atom-semantic-contract-byte-drift",
        drift_atom_semantic_contract_bytes,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-cardinality-change",
        change_atom_contract_coordinate_card,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-residual-scope-removal",
        remove_atom_scope_boundary,
        "must retain the exact residual-scope boundary",
    ),
    (
        "atom-residual-scope-widening",
        widen_atom_scope_boundary,
        "contains a forbidden residual-scope widening claim",
    ),
    (
        "atom-completeness-same-name-weakening",
        weaken_atom_completeness_same_name,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-node-order-swap",
        swap_atom_node_order,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-output-order-swap",
        swap_atom_output_order,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-component-order-swap",
        swap_atom_component_order,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-unique-sign-change",
        change_atom_unique_sign,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-net-component-change",
        change_atom_net_component,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-informative-count-denominator-change",
        change_informative_count_denominator,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-misinformative-count-numerator-change",
        change_misinformative_count_numerator,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-empirical-weight-change",
        change_empirical_weight,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-product-exponent-change",
        change_product_exponent,
        "lost its exact order, sign, component, count-argument, weighting, product, or scaling semantics",
    ),
    (
        "atom-rational-synergy-product-change",
        change_rational_synergy_product,
        "Lean two-source Mobius/atom bridge source digest mismatch",
    ),
    (
        "atom-scaled-log-factor-change",
        change_scaled_log_factor,
        "Lean two-source Mobius/atom bridge source digest mismatch",
    ),
    (
        "atom-contract-count-argument-change",
        change_contract_count_argument,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-product-value-change",
        change_contract_product_value,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-bridge-native-decide",
        add_native_decide_to_atom_bridge,
        "forbidden proof placeholder, declaration, or native evaluator",
    ),
    (
        "atom-contract-mobius-zero-change",
        change_contract_mobius_zero,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-zeta-zero-change",
        change_contract_zeta_zero,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-real-rational-cast-change",
        change_contract_real_rational_cast,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-positive-conclusion-change",
        change_contract_positive_conclusion,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-negative-conclusion-change",
        change_contract_negative_conclusion,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-zero-conclusion-change",
        change_contract_zero_conclusion,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "atom-contract-helper-inventory-change",
        change_contract_helper_inventory,
        "Lean SxPID2 atom semantic-contract source digest mismatch",
    ),
    (
        "K2-06-mobius-zeta-inverse-same-name-weakening",
        weaken_mobius_zeta_inverse_same_name,
        "Lean two-source Mobius/atom bridge source digest mismatch",
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


def change_mobius_unique_formula(path: Path) -> None:
    replace_exact_once(
        path,
        "| .uniqueOne => cumulative .sourceOne - cumulative .redundancy",
        "| .uniqueOne => cumulative .sourceOne + cumulative .redundancy",
    )


def change_mobius_synergy_formula(path: Path) -> None:
    replace_exact_once(
        path,
        "cumulative .jointSources - cumulative .sourceOne - cumulative .sourceTwo +",
        "cumulative .jointSources + cumulative .sourceOne - cumulative .sourceTwo +",
    )


def change_zeta_source_one_formula(path: Path) -> None:
    replace_exact_once(
        path,
        "| .sourceOne => atom .uniqueOne + atom .redundancy",
        "| .sourceOne => atom .uniqueTwo + atom .redundancy",
    )


def change_mobius_coefficient_sign(path: Path) -> None:
    replace_exact_once(
        path,
        "| .synergy, .sourceOne => -1",
        "| .synergy, .sourceOne => 1",
    )


def change_local_net_definition(path: Path) -> None:
    replace_exact_once(
        path,
        "| .net => localCumulativeNet law node anchor",
        "| .net => localCumulativeInformative law node anchor",
    )


def change_informative_argument_definition(path: Path) -> None:
    replace_exact_once(
        path,
        "(eventCount count (sxPid2SourceEvent node anchor) : ℚ)",
        "(eventCount count (targetBranchEvent anchor) : ℚ)",
    )


def change_misinformative_argument_definition(path: Path) -> None:
    replace_exact_once(
        path,
        "(eventCount count (targetBranchEvent anchor) : ℚ) /",
        "(totalCount count : ℚ) /",
    )


def change_averaged_count_weight(path: Path) -> None:
    replace_exact_once(
        path,
        """  ∑ anchor ∈ positiveSupport count,
    ((count anchor : ℝ) / (totalCount count : ℝ)) *
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ)
""",
        """  ∑ anchor ∈ positiveSupport count,
    ((totalCount count : ℝ) / (totalCount count : ℝ)) *
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ)
""",
    )


def change_rational_product_exponent(path: Path) -> None:
    replace_exact_once(
        path,
        "countComponentArgument count component node anchor ^ count anchor",
        "countComponentArgument count component node anchor ^ totalCount count",
    )


def change_real_unique_product_denominator(path: Path) -> None:
    replace_exact_once(
        path,
        """  | .uniqueOne =>
      countCumulativeRealProduct count component .sourceOne /
        countCumulativeRealProduct count component .redundancy
""",
        """  | .uniqueOne =>
      countCumulativeRealProduct count component .sourceOne /
        countCumulativeRealProduct count component .sourceTwo
""",
    )


def change_rational_synergy_product_formula(path: Path) -> None:
    replace_exact_once(
        path,
        """      (countCumulativeRationalProduct count component .jointSources *
        countCumulativeRationalProduct count component .redundancy) /
""",
        """      (countCumulativeRationalProduct count component .sourceOne *
        countCumulativeRationalProduct count component .redundancy) /
""",
    )


def change_scaled_log_statement(path: Path) -> None:
    replace_exact_once(
        path,
        """    averagedCumulativeCountExpression count component node =
      (1 / (totalCount count : ℝ)) *
""",
        """    averagedCumulativeCountExpression count component node =
      (totalCount count : ℝ) *
""",
    )


def omit_and_duplicate_coordinate(path: Path) -> None:
    replace_exact_once(
        path,
        """    .cumulative .informative .sourceOne,
    .cumulative .informative .sourceTwo,
""",
        """    .cumulative .informative .sourceOne,
    .cumulative .informative .sourceOne,
""",
    )


def change_net_subtraction_to_addition(path: Path) -> None:
    replace_exact_once(
        path,
        """    localCumulativeComponent law .net node anchor =
      localCumulativeComponent law .informative node anchor -
        localCumulativeComponent law .misinformative node anchor := by
""",
        """    localCumulativeComponent law .net node anchor =
      localCumulativeComponent law .informative node anchor +
        localCumulativeComponent law .misinformative node anchor := by
""",
    )


def change_atom_product_quotient_to_multiplication(path: Path) -> None:
    replace_exact_once(
        path,
        """  | .uniqueOne =>
      countCumulativeRealProduct count component .sourceOne /
        countCumulativeRealProduct count component .redundancy
""",
        """  | .uniqueOne =>
      countCumulativeRealProduct count component .sourceOne *
        countCumulativeRealProduct count component .redundancy
""",
    )


def reverse_product_comparison(path: Path) -> None:
    replace_exact_once(
        path,
        """    0 < averagedSxPid2Coordinate (empiricalLaw count) coordinate ↔
      1 < countCoordinateRealProduct count coordinate := by
""",
        """    0 < averagedSxPid2Coordinate (empiricalLaw count) coordinate ↔
      countCoordinateRealProduct count coordinate < 1 := by
""",
    )


def remove_log_product_positivity_premise(path: Path) -> None:
    replace_exact_once(
        path,
        """      exact pow_ne_zero _ (ne_of_gt (by
        exact_mod_cast count_component_argument_positive_on_support
          count component node h_total hanchor))
""",
        """      exact pow_ne_zero _ (by rfl)
""",
    )


LeanMutation = tuple[str, Callable[[Path], None]]


LEAN_SEMANTIC_MUTATIONS: tuple[LeanMutation, ...] = (
    ("source-one-source-two-swap", swap_source_one_collection),
    ("redundancy-union-to-joint", replace_redundancy_union_with_joint),
    ("target-restriction-erasure", erase_target_restriction),
    ("joint-node-to-marginal", replace_joint_with_source_one),
    ("positive-support-weakening", weaken_positive_support),
)


LEAN_ATOM_SEMANTIC_MUTATIONS: tuple[LeanMutation, ...] = (
    ("mobius-unique-formula", change_mobius_unique_formula),
    ("mobius-synergy-formula", change_mobius_synergy_formula),
    ("zeta-source-one-formula", change_zeta_source_one_formula),
    ("mobius-coefficient-sign", change_mobius_coefficient_sign),
    ("local-net-component", change_local_net_definition),
    ("informative-count-argument", change_informative_argument_definition),
    ("misinformative-count-argument", change_misinformative_argument_definition),
    ("averaged-count-weight", change_averaged_count_weight),
    ("rational-product-exponent", change_rational_product_exponent),
    ("real-unique-product-denominator", change_real_unique_product_denominator),
    ("rational-synergy-product", change_rational_synergy_product_formula),
    ("scaled-log-factor", change_scaled_log_statement),
    ("K2-07-coordinate-omission-duplication", omit_and_duplicate_coordinate),
    ("K2-10-net-subtraction-to-addition", change_net_subtraction_to_addition),
    (
        "K2-12-atom-product-quotient-to-multiplication",
        change_atom_product_quotient_to_multiplication,
    ),
    ("K2-13-product-comparison-reversal", reverse_product_comparison),
    (
        "K2-14-log-product-positivity-premise-removal",
        remove_log_product_positivity_premise,
    ),
)


LEAN_ATOM_CONTRACT_MUTATIONS: tuple[LeanMutation, ...] = (
    ("contract-count-argument", mutate_contract_count_argument),
    ("contract-cumulative-product", mutate_contract_product_value),
    ("contract-mobius-zero", mutate_contract_mobius_zero),
    ("contract-zeta-zero", mutate_contract_zeta_zero),
    ("contract-real-rational-cast", mutate_contract_real_rational_cast),
    ("contract-positive-conclusion", mutate_contract_positive_conclusion),
    ("contract-negative-conclusion", mutate_contract_negative_conclusion),
    ("contract-zero-conclusion", mutate_contract_zero_conclusion),
    ("contract-helper-inventory", mutate_contract_helper_inventory),
)


K2_LITERAL_MUTATION_MAP: tuple[tuple[str, str], ...] = (
    ("K2-06", "same-name weakening of the zeta-after-Mobius inverse theorem"),
    (
        "K2-07",
        "one omitted and one duplicated entry in the explicit 24-coordinate order",
    ),
    ("K2-10", "signed-net subtraction replaced by addition"),
    ("K2-12", "an atom-product quotient replaced by multiplication"),
    ("K2-13", "the positive product comparison reversed"),
    ("K2-14", "the log-product nonzero premise replaced by an invalid reflexive proof"),
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
            [str(lake), "env", "lean", "-t", "0", str(source)],
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


def check_lean_atom_semantic_mutations(checker: ModuleType) -> None:
    if not ATOM_BRIDGE.is_file() or ATOM_BRIDGE.is_symlink():
        raise RuntimeError(f"Mobius/atom bridge is not a regular file: {ATOM_BRIDGE}")
    lake = checker.find_lake()
    with tempfile.TemporaryDirectory(prefix="pid-lean-atom-bridge-") as temporary:
        temporary_root = Path(temporary)
        baseline = temporary_root / "baseline" / ATOM_BRIDGE.name
        baseline.parent.mkdir(parents=True)
        shutil.copy2(ATOM_BRIDGE, baseline)
        baseline_process = run_isolated_lean(checker, lake, baseline)
        if baseline_process.returncode != 0:
            raise RuntimeError(
                "unmodified isolated Mobius/atom bridge did not compile before mutation; "
                f"stdout={baseline_process.stdout!r}, stderr={baseline_process.stderr!r}"
            )

        for name, mutation in LEAN_ATOM_SEMANTIC_MUTATIONS:
            mutated = temporary_root / name / ATOM_BRIDGE.name
            mutated.parent.mkdir(parents=True)
            shutil.copy2(ATOM_BRIDGE, mutated)
            mutation(mutated)
            process = run_isolated_lean(checker, lake, mutated)
            if process.returncode == 0:
                raise RuntimeError(
                    f"{name}: pinned Lean accepted the Mobius/atom semantic mutation"
                )
            diagnostic = process.stdout + process.stderr
            if "error" not in diagnostic.lower():
                raise RuntimeError(
                    f"{name}: Lean failed without a proof-error diagnostic: {diagnostic!r}"
                )


def check_lean_atom_contract_mutations(checker: ModuleType) -> None:
    if not ATOM_SEMANTIC_CONTRACT.is_file() or ATOM_SEMANTIC_CONTRACT.is_symlink():
        raise RuntimeError(
            f"SxPID2 atom semantic contract is not a regular file: {ATOM_SEMANTIC_CONTRACT}"
        )
    lake = checker.find_lake()
    with tempfile.TemporaryDirectory(prefix="pid-lean-atom-contract-") as temporary:
        temporary_root = Path(temporary)
        baseline = temporary_root / "baseline" / ATOM_SEMANTIC_CONTRACT.name
        baseline.parent.mkdir(parents=True)
        shutil.copy2(ATOM_SEMANTIC_CONTRACT, baseline)
        baseline_process = run_isolated_lean(checker, lake, baseline)
        if baseline_process.returncode != 0:
            raise RuntimeError(
                "unmodified isolated SxPID2 atom semantic contract did not compile "
                "before mutation; "
                f"stdout={baseline_process.stdout!r}, stderr={baseline_process.stderr!r}"
            )

        for name, mutation in LEAN_ATOM_CONTRACT_MUTATIONS:
            mutated = temporary_root / name / ATOM_SEMANTIC_CONTRACT.name
            mutated.parent.mkdir(parents=True)
            shutil.copy2(ATOM_SEMANTIC_CONTRACT, mutated)
            mutation(mutated)
            process = run_isolated_lean(checker, lake, mutated)
            if process.returncode == 0:
                raise RuntimeError(
                    f"{name}: pinned Lean accepted the semantic-contract mutation"
                )
            diagnostic = process.stdout + process.stderr
            if "error" not in diagnostic.lower():
                raise RuntimeError(
                    f"{name}: Lean failed without an error diagnostic: {diagnostic!r}"
                )


def main() -> int:
    checker = load_checker()
    version_mutation_count = check_version_parser(checker)
    check_fresh_kernel_replay_route()
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
    check_lean_atom_semantic_mutations(checker)
    check_lean_atom_contract_mutations(checker)

    original_static_count = 10
    lean433_compatibility_mutation_count = 7
    new_mutation_count = (
        len(MUTATIONS)
        - original_static_count
        - lean433_compatibility_mutation_count
        + len(LEAN_ATOM_SEMANTIC_MUTATIONS)
        + len(LEAN_ATOM_CONTRACT_MUTATIONS)
    )
    if new_mutation_count < 24:
        raise RuntimeError(
            f"SxPID2 atom mutation coverage regressed below 24: {new_mutation_count}"
        )
    mutation_names = {
        *(name for name, _mutation, _message in MUTATIONS),
        *(name for name, _mutation in LEAN_ATOM_SEMANTIC_MUTATIONS),
        *(name for name, _mutation in LEAN_ATOM_CONTRACT_MUTATIONS),
    }
    for identifier, _description in K2_LITERAL_MUTATION_MAP:
        matches = tuple(
            name for name in mutation_names if name.startswith(f"{identifier}-")
        )
        if len(matches) != 1:
            raise RuntimeError(
                f"{identifier}: expected one literal mutation route, found {matches}"
            )
    k2_summary = "; ".join(
        f"{identifier}={description}"
        for identifier, description in K2_LITERAL_MUTATION_MAP
    )

    print(
        "OK: Lean finite-convergence gate self-test rejected "
        f"all {len(MUTATIONS)} static source mutations at their expected checker "
        f"diagnostics, including {lean433_compatibility_mutation_count} exact Lean "
        "4.33 scoped-transparency mutations, "
        f"{version_mutation_count} hostile Lean release-identity probes, "
        "an AST-bound leanchecker --fresh primary replay route, "
        f"all {len(LEAN_SEMANTIC_MUTATIONS)} baseline-first isolated "
        "count/event mutations, and all "
        f"{len(LEAN_ATOM_SEMANTIC_MUTATIONS)} baseline-first isolated Mobius/atom "
        "module mutations and "
        f"{len(LEAN_ATOM_CONTRACT_MUTATIONS)} baseline-first isolated atom-contract "
        "mutations with nonzero Lean status plus an error diagnostic; the new atom "
        f"surface contributes {new_mutation_count} mutations; literal map: {k2_summary}; "
        "kernel decide remains required and the observed "
        f"native evaluator axiom was {OBSERVED_NATIVE_DECIDE_AXIOM}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
