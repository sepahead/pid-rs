#!/usr/bin/env python3
"""Fail-closed mutation tests for the Lean 4.33 exact-log-product gate."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Callable, NoReturn


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-lean-exact-log-product.py"
SOURCE = ROOT / "audit/formal/lean-exact-log-product/PidExactLogProduct.lean"
EXPECTED_SOURCE_SHA256 = (
    "f0727ea3061d561ba89ba49edebece971ce03bdecf03e0c32774a1c080dc07bf"
)
EXPECTED_THEOREM_NAMES = (
    "log_finset_zpow_product",
    "scaled_log_sum_eq_log_product",
    "scaled_log_pos_iff",
    "scaled_log_neg_iff",
    "scaled_log_eq_zero_iff",
    "two_nontrivial_logs_cancel",
    "retained_five_term_product_eq_one",
)
EXPECTED_QUALIFIED_THEOREMS = tuple(
    f"PidExactLogProduct.{name}" for name in EXPECTED_THEOREM_NAMES
)


class MutationError(RuntimeError):
    """The baseline, a positive control, or a required mutation behaved incorrectly."""


def fail(message: str) -> NoReturn:
    raise MutationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pid_rs_check_lean_exact_log_product", CHECKER_PATH
    )
    require(spec is not None and spec.loader is not None, "cannot load production checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checker(
    checker: ModuleType,
    source: Path,
    source_digest: str,
    *,
    theorem_inventory: tuple[str, ...] | None = None,
) -> tuple[int, str]:
    original_source = checker.SOURCE
    original_digest = checker.EXPECTED_SOURCE_SHA256
    original_theorems = checker.THEOREMS
    output = io.StringIO()
    try:
        checker.SOURCE = source
        checker.EXPECTED_SOURCE_SHA256 = source_digest
        if theorem_inventory is not None:
            checker.THEOREMS = theorem_inventory
        with redirect_stdout(output), redirect_stderr(output):
            status = checker.main()
    finally:
        checker.SOURCE = original_source
        checker.EXPECTED_SOURCE_SHA256 = original_digest
        checker.THEOREMS = original_theorems
    return status, output.getvalue()


def replace_once(source: str, before: str, after: str, name: str) -> str:
    require(source.count(before) == 1, f"mutation anchor is absent or ambiguous: {name}")
    return source.replace(before, after, 1)


def swap_declaration_names(source: str) -> str:
    first = "theorem scaled_log_pos_iff"
    second = "theorem scaled_log_neg_iff"
    require(source.count(first) == 1, "positive declaration anchor")
    require(source.count(second) == 1, "negative declaration anchor")
    temporary = "theorem exact_log_product_temporary_name"
    return source.replace(first, temporary, 1).replace(second, first, 1).replace(
        temporary, second, 1
    )


def introduce_unpermitted_axiom_dependency(source: str) -> str:
    source = replace_once(
        source,
        "/-- The retained five-term empirical witness",
        "set_option warningAsError false in\n"
        "/-- The retained five-term empirical witness",
        "unpermitted_axiom_warning_scope",
    )
    return replace_once(
        source,
        "  norm_num\n\nend PidExactLogProduct",
        "  exact sorryAx _ true\n\nend PidExactLogProduct",
        "unpermitted_axiom_dependency",
    )


def main() -> int:
    try:
        require(
            hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA256,
            "Lean source digest drifted",
        )
        checker = load_checker()
        require(
            checker.EXPECTED_THEOREM_NAMES == EXPECTED_THEOREM_NAMES,
            "production source theorem registry drifted",
        )
        require(
            checker.EXPECTED_QUALIFIED_THEOREMS == EXPECTED_QUALIFIED_THEOREMS,
            "production qualified theorem registry drifted",
        )
        baseline_status, baseline_output = run_checker(
            checker, SOURCE, EXPECTED_SOURCE_SHA256
        )
        require(
            baseline_status == 0,
            f"unmutated production checker failed:\n{baseline_output}",
        )

        source_text = SOURCE.read_text(encoding="utf-8")
        source_mutations: tuple[tuple[str, Callable[[str], str], str], ...] = (
            (
                "replace_log_zpow_with_log_pow",
                lambda text: replace_once(
                    text,
                    "Real.log_zpow (argument i) (exponent i)",
                    "Real.log_pow (argument i) (exponent i)",
                    "replace_log_zpow_with_log_pow",
                ),
                "Lean kernel check failed",
            ),
            (
                "reverse_positive_product_order",
                lambda text: replace_once(
                    text,
                    "0 < (1 / (n : ℝ)) * Real.log product ↔ 1 < product := by",
                    "0 < (1 / (n : ℝ)) * Real.log product ↔ product < 1 := by",
                    "reverse_positive_product_order",
                ),
                "Lean kernel check failed",
            ),
            (
                "remove_negative_one_exclusion",
                lambda text: replace_once(
                    text,
                    "    · exact hproduct_one\n    · linarith\n",
                    "    · exact hproduct_one\n    · exact hproduct_neg_one\n",
                    "remove_negative_one_exclusion",
                ),
                "Lean kernel check failed",
            ),
            (
                "negate_nonsyntactic_cancellation",
                lambda text: replace_once(
                    text,
                    "Real.log x + Real.log x⁻¹ = 0 ∧ 0 < x⁻¹ ∧ x ≠ 1 ∧ x⁻¹ ≠ 1 := by",
                    "Real.log x + Real.log x⁻¹ ≠ 0 ∧ 0 < x⁻¹ ∧ x ≠ 1 ∧ x⁻¹ ≠ 1 := by",
                    "negate_nonsyntactic_cancellation",
                ),
                "Lean kernel check failed",
            ),
            (
                "falsify_retained_product",
                lambda text: replace_once(
                    text,
                    "(8 / 15 : ℚ)⁻¹ * (4 / 5 : ℚ) * (8 / 9 : ℚ) * (4 / 3 : ℚ) * (16 / 9 : ℚ)⁻¹ = 1 := by",
                    "(8 / 15 : ℚ)⁻¹ * (4 / 5 : ℚ) * (8 / 9 : ℚ) * (4 / 3 : ℚ) * (16 / 9 : ℚ)⁻¹ = 2 := by",
                    "falsify_retained_product",
                ),
                "Lean kernel check failed",
            ),
            (
                "remove_zero_product_positivity_premise",
                lambda text: replace_once(
                    text,
                    "theorem scaled_log_eq_zero_iff {product : ℝ} {n : ℕ}\n"
                    "    (hproduct : 0 < product) (hn : 0 < n) :",
                    "theorem scaled_log_eq_zero_iff {product : ℝ} {n : ℕ}\n"
                    "    (hn : 0 < n) :",
                    "remove_zero_product_positivity_premise",
                ),
                "Lean kernel check failed",
            ),
            (
                "inject_sorry",
                lambda text: replace_once(
                    text,
                    "  norm_num\n\nend PidExactLogProduct",
                    "  sorry\n\nend PidExactLogProduct",
                    "inject_sorry",
                ),
                "prohibited proof escape",
            ),
            (
                "inject_axiom",
                lambda text: replace_once(
                    text,
                    "theorem retained_five_term_product_eq_one :",
                    "axiom retained_five_term_product_eq_one :",
                    "inject_axiom",
                ),
                "prohibited proof escape",
            ),
            (
                "rename_checked_theorem",
                lambda text: replace_once(
                    text,
                    "theorem scaled_log_neg_iff",
                    "theorem scaled_log_negative_iff",
                    "rename_checked_theorem",
                ),
                "source theorem inventory changed",
            ),
            (
                "remove_checked_theorem_declaration",
                lambda text: replace_once(
                    text,
                    "theorem retained_five_term_product_eq_one :",
                    "def retained_five_term_product_eq_one :",
                    "remove_checked_theorem_declaration",
                ),
                "source theorem inventory changed",
            ),
            (
                "insert_extra_theorem_declaration",
                lambda text: replace_once(
                    text,
                    "\nend PidExactLogProduct",
                    "\ntheorem unexpected_extra_theorem : True := by trivial\n\n"
                    "end PidExactLogProduct",
                    "insert_extra_theorem_declaration",
                ),
                "source theorem inventory changed",
            ),
            (
                "reorder_theorem_declarations",
                swap_declaration_names,
                "source theorem inventory changed",
            ),
            (
                "unpermitted_axiom_dependency",
                introduce_unpermitted_axiom_dependency,
                "theorem axiom inventory changed",
            ),
        )

        results: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-exact-log-product-mutations-"
        ) as raw:
            directory = Path(raw)
            for index, (name, mutate, expected_message) in enumerate(source_mutations):
                mutant_text = mutate(source_text)
                mutant = directory / f"Mutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                mutant_digest = sha256_bytes(mutant_text.encode("utf-8"))
                status, output = run_checker(checker, mutant, mutant_digest)
                require(status != 0, f"scientific mutation survived: {name}")
                require(
                    expected_message in output,
                    f"{name}: expected {expected_message!r}, got:\n{output}",
                )
                results.append(
                    {"name": name, "killed": True, "mutant_sha256": mutant_digest}
                )

            inventory_mutations = (
                ("remove_theorem_from_checker_inventory", EXPECTED_QUALIFIED_THEOREMS[:-1]),
                (
                    "insert_theorem_into_checker_inventory",
                    EXPECTED_QUALIFIED_THEOREMS
                    + ("PidExactLogProduct.unexpected_extra_theorem",),
                ),
                (
                    "reorder_checker_theorem_inventory",
                    (
                        EXPECTED_QUALIFIED_THEOREMS[1],
                        EXPECTED_QUALIFIED_THEOREMS[0],
                        *EXPECTED_QUALIFIED_THEOREMS[2:],
                    ),
                ),
            )
            for name, inventory in inventory_mutations:
                status, output = run_checker(
                    checker,
                    SOURCE,
                    EXPECTED_SOURCE_SHA256,
                    theorem_inventory=inventory,
                )
                require(status != 0, f"checker inventory mutation survived: {name}")
                require(
                    "checker theorem audit inventory changed" in output,
                    f"unexpected {name} failure:\n{output}",
                )
                results.append(
                    {
                        "name": name,
                        "killed": True,
                        "mutant_sha256": sha256_bytes("\n".join(inventory).encode("utf-8")),
                    }
                )

            decoy_text = source_text + r'''

/- A nested comment /- sorry -/ containing admit, axiom, and unsafe is not live Lean code. -/
def exactLogProductProofEscapeDecoy : String :=
  "sorry admit axiom unsafe with an escaped quote: \""
'''
            decoy = directory / "CommentStringDecoy.lean"
            decoy.write_text(decoy_text, encoding="utf-8")
            decoy_digest = sha256_bytes(decoy_text.encode("utf-8"))
            status, output = run_checker(checker, decoy, decoy_digest)
            require(status == 0, f"comment/string decoy was rejected:\n{output}")

        evidence = {
            "schema": "pid-rs/lean-exact-log-product-mutations/v2",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": hashlib.sha256(CHECKER_PATH.read_bytes()).hexdigest(),
            "self_test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "baseline_checker_passed": True,
            "mutations_killed": len(results),
            "mutations": results,
            "comment_string_decoy_passed": True,
            "boundary": (
                "These mutations show fail-closed sensitivity to the generic log/product/sign "
                "proof, retained exact-zero witness, proof escapes, source declaration order, "
                "qualified checker inventory, and one unpermitted axiom dependency. They do not "
                "bind concrete SxPID events, Rust, binary64, sampling, or scientific validity."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, MutationError) as error:
        print(f"Lean exact-log-product self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
