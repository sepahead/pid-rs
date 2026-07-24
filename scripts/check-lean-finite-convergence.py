#!/usr/bin/env python3
"""Build the pinned Lean proof of finite-alphabet deterministic convergence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit" / "formal" / "lean"
TOOLCHAIN = "leanprover/lean4:v4.32.0"
MATHLIB_URL = "https://github.com/leanprover-community/mathlib4.git"
MATHLIB_REVISION = "81a5d257c8e410db227a6665ed08f64fea08e997"
EXPECTED_MANIFEST_SHA256 = (
    "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
)
EXPECTED_PACKAGE_PINS = {
    "mathlib": (
        MATHLIB_URL,
        MATHLIB_REVISION,
        "v4.32.0",
        False,
    ),
    "plausible": (
        "https://github.com/leanprover-community/plausible",
        "e12c1910fe855cbfc38803cd4e55543906d5fa62",
        "main",
        True,
    ),
    "LeanSearchClient": (
        "https://github.com/leanprover-community/LeanSearchClient",
        "c5d5b8fe6e5158def25cd28eb94e4141ad97c843",
        "main",
        True,
    ),
    "importGraph": (
        "https://github.com/leanprover-community/import-graph",
        "7e9612bf0b9ee66db3cb5b9988a35afc706f5a12",
        "main",
        True,
    ),
    "proofwidgets": (
        "https://github.com/leanprover-community/ProofWidgets4",
        "6e311e2a844da9b2cc3971187df2fe0066947b93",
        "main",
        True,
    ),
    "aesop": (
        "https://github.com/leanprover-community/aesop",
        "a7dbf0c63b694e47f425f3dcddbc0e178bb432d3",
        "master",
        True,
    ),
    "Qq": (
        "https://github.com/leanprover-community/quote4",
        "38d591e778f100aec9762bb582f9c7f55f50e9dc",
        "master",
        True,
    ),
    "batteries": (
        "https://github.com/leanprover-community/batteries",
        "023ce7d62a0531e22a5331e20b587817a80d49ff",
        "main",
        True,
    ),
    "Cli": (
        "https://github.com/leanprover/lean4-cli",
        "88679d088c9720c27ebdf2ba4dafe17341747f94",
        "v4.32.0",
        True,
    ),
}
EXPECTED_LAKEFILE = """name = "pid-finite-convergence"
version = "0.1.0"
defaultTargets = ["PidFiniteConvergence"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4.git"
rev = "v4.32.0"

[[lean_lib]]
name = "PidFiniteConvergence"
"""
EXPECTED_SOURCES = {
    "PidFiniteConvergence.lean",
    "PidFiniteConvergence/Dependence.lean",
    "PidFiniteConvergence/Deterministic.lean",
    "PidFiniteConvergence/FractionalCover.lean",
    "PidFiniteConvergence/LocalContinuity.lean",
    "PidFiniteConvergence/SupportChangeContinuity.lean",
    "PidFiniteConvergence/SxEventBridge.lean",
}
EXPECTED_ROOT_SOURCE = """import PidFiniteConvergence.Dependence
import PidFiniteConvergence.Deterministic
import PidFiniteConvergence.FractionalCover
import PidFiniteConvergence.LocalContinuity
import PidFiniteConvergence.SupportChangeContinuity
import PidFiniteConvergence.SxEventBridge
"""
EXPECTED_SUPPORT_CHANGE_THEOREMS = (
    "overlap_add_left_residual",
    "overlap_add_right_residual",
    "left_residual_nonnegative",
    "right_residual_nonnegative",
    "left_or_right_residual_eq_zero",
    "left_residual_sub_right_residual",
    "abs_sub_eq_left_add_right_residual",
    "sum_left_residual_eq_sum_right_residual",
    "sum_abs_sub_eq_two_mul_sum_left_residual",
    "sum_overlap_eq_one_sub_sum_left_residual",
    "left_residual_le_of_nonnegative",
    "right_residual_le_of_nonnegative",
    "residual_eq_zero_outside_positive_support",
    "positive_support_card_positive_of_sum_positive",
    "sum_positive_support_eq_sum",
    "left_right_positive_support_disjoint",
    "residual_entropy_nonnegative",
    "sum_neg_mul_log_le_card_mul_neg_mul_log_average",
    "residual_entropy_le_card_mul_neg_mul_log_average",
    "card_mul_neg_mul_log_average_eq_mass_mul_log_card_div_mass",
    "residual_entropy_le_mass_mul_log_card_div_mass",
    "card_mul_card_le_balanced_ambient",
    "add_residual_entropy_le_mass_mul_log_card_product_div_mass_sq",
    "add_residual_entropy_le_balanced_ambient_bound",
    "overlap_residual_entropy_sum_le_balanced_ambient_bound",
    "residual_weighted_component_between_zero_and_entropy",
    "abs_residual_weighted_signed_value_le_entropy",
    "abs_component_residual_sub_le_max_entropy",
    "abs_signed_residual_sub_le_add_entropy",
    "abs_overlap_component_residual_sub_le_max_entropy",
    "abs_overlap_signed_residual_sub_le_add_entropy",
    "mobius_row_sum_eq_ite_bot",
    "equivalence_union_common_modulus_zero",
    "equivalence_union_common_modulus_one",
    "equivalence_union_common_modulus_nonnegative",
    "equivalence_union_common_modulus_le_linear",
    "equivalence_union_common_modulus_closed_interval_bounds",
)
EXPECTED_SX_EVENT_BRIDGE_THEOREMS = (
    "source_collection_equivalence",
    "target_equivalence",
    "source_target_collection_equivalence",
    "equivalence_class_neighborhood_anchor_mem",
    "finite_equivalence_union_anchor_mem",
    "source_branch_is_equivalence_class",
    "target_branch_is_equivalence_class",
    "source_target_branch_is_equivalence_class",
    "source_branch_anchor_mem",
    "target_branch_anchor_mem",
    "source_target_branch_anchor_mem",
    "sx_source_event_equivalence_union",
    "sx_target_restricted_event_equivalence_union",
    "sx_target_event_equivalence_union",
    "sx_source_event_anchor_mem",
    "sx_target_restricted_event_anchor_mem",
    "source_target_branch_event_eq_inter",
    "sx_target_restricted_event_eq_inter",
    "sx_keyed_events_fixed_across_laws",
    "sx_source_event_mass_positive",
    "sx_target_event_mass_positive",
    "sx_target_restricted_event_mass_positive",
)
EXPECTED_FRACTIONAL_COVER_THEOREMS = (
    "equivalence_class_neighborhood_eq_of_related",
    "equivalence_class_event_mass_positive_on_support",
    "positive_support_filter_event_sum_eq_event_mass",
    "equivalence_class_cover_weight_le_one",
    "equivalence_neighborhood_overlap_load_eq_cover_sum",
    "equivalence_class_overlap_load_le_total",
    "finite_event_mass_nonnegative",
    "equivalence_neighborhood_overlap_load_nonnegative",
    "finite_event_mass_mono",
    "finite_event_mass_union_le",
    "finite_event_mass_biUnion_le_sum",
    "finite_equivalence_union_event_mass_positive_on_support",
    "finite_equivalence_union_ratio_le_branch_sum",
    "finite_equivalence_union_overlap_load_le_of_nonempty",
    "finite_equivalence_union_overlap_load_le",
    "finite_equivalence_union_fractional_cover_bound",
    "finite_equivalence_union_fractional_cover_bounds",
    "sx_source_fractional_cover_bound",
    "sx_target_restricted_fractional_cover_bound",
    "sx_target_fractional_cover_bound",
)
REMOVED_ENVIRONMENT_KEYS = (
    "ELAN_TOOLCHAIN",
    "LEAN_PATH",
    "LEAN_SRC_PATH",
    "LEAN_SYSROOT",
)
TIMEOUT_SECONDS = 900
GIT_TIMEOUT_SECONDS = 30


class LeanProofError(RuntimeError):
    """Raised when the pinned formal artifact cannot be checked."""


def read_regular_text(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise LeanProofError(f"could not read UTF-8 file {path}: {error}") from error


def read_regular_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise LeanProofError(f"could not read file {path}: {error}") from error


def check_toolchain() -> None:
    actual = read_regular_text(PROJECT / "lean-toolchain")
    if actual != f"{TOOLCHAIN}\n":
        raise LeanProofError(
            f"lean-toolchain must contain exactly {TOOLCHAIN!r} and one newline"
        )


def check_lakefile() -> None:
    actual = read_regular_text(PROJECT / "lakefile.toml")
    if actual != EXPECTED_LAKEFILE:
        raise LeanProofError(
            "lakefile.toml does not match the pinned project declaration"
        )


def check_manifest() -> None:
    path = PROJECT / "lake-manifest.json"
    raw = read_regular_bytes(path)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != EXPECTED_MANIFEST_SHA256:
        raise LeanProofError(
            "Lake manifest byte digest mismatch: "
            f"expected {EXPECTED_MANIFEST_SHA256}, found {actual_sha256}"
        )
    try:
        manifest = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise LeanProofError(f"invalid Lake manifest JSON: {error}") from error
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LeanProofError("Lake manifest packages must be a list")
    if not all(isinstance(package, dict) for package in packages):
        raise LeanProofError("each Lake manifest package must be an object")
    package_map = {package.get("name"): package for package in packages}
    if len(package_map) != len(packages):
        raise LeanProofError("Lake manifest package names must be unique")
    expected_names = set(EXPECTED_PACKAGE_PINS)
    actual_names = set(package_map)
    if actual_names != expected_names:
        raise LeanProofError(
            "Lake manifest package set mismatch: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )
    for name, (
        url,
        revision,
        input_revision,
        inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        package = package_map[name]
        expected = {
            "type": "git",
            "url": url,
            "rev": revision,
            "inputRev": input_revision,
            "inherited": inherited,
        }
        mismatches = {
            key: (expected_value, package.get(key))
            for key, expected_value in expected.items()
            if package.get(key) != expected_value
        }
        if mismatches:
            raise LeanProofError(f"{name} manifest pin mismatch: {mismatches}")


def check_sources() -> int:
    sources = sorted(
        source
        for source in PROJECT.rglob("*.lean")
        if ".lake" not in source.relative_to(PROJECT).parts
    )
    if not sources:
        raise LeanProofError("Lean project contains no source files")
    relative_sources = {source.relative_to(PROJECT).as_posix() for source in sources}
    if relative_sources != EXPECTED_SOURCES:
        raise LeanProofError(
            "Lean source manifest mismatch: "
            f"missing={sorted(EXPECTED_SOURCES - relative_sources)}, "
            f"unexpected={sorted(relative_sources - EXPECTED_SOURCES)}"
        )
    placeholder = re.compile(r"\b(?:admit|axiom|constant|sorry|sorryAx)\b")
    for source in sources:
        text = read_regular_text(source)
        if (
            source == PROJECT / "PidFiniteConvergence.lean"
            and text != EXPECTED_ROOT_SOURCE
        ):
            raise LeanProofError(
                "PidFiniteConvergence.lean must import the pinned checked submodule set exactly"
            )
        if source.parent == PROJECT / "PidFiniteConvergence" and (
            "set_option warningAsError true\n" not in text
        ):
            raise LeanProofError(f"the checked module must enable warningAsError: {source}")
        match = placeholder.search(text)
        if match is not None:
            raise LeanProofError(
                f"forbidden proof placeholder or declaration in {source}: {match.group(0)}"
            )
        if source == (
            PROJECT
            / "PidFiniteConvergence"
            / "SupportChangeContinuity.lean"
        ):
            theorem_pattern = re.compile(
                r"(?m)^(?:@\[[^\n]+\]\s+)?(?:theorem|lemma)\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\b"
            )
            actual_theorems = tuple(theorem_pattern.findall(text))
            if actual_theorems != EXPECTED_SUPPORT_CHANGE_THEOREMS:
                raise LeanProofError(
                    "support-change-tolerant theorem inventory mismatch: "
                    f"expected={EXPECTED_SUPPORT_CHANGE_THEOREMS}, "
                    f"found={actual_theorems}"
                )
        if source == (
            PROJECT
            / "PidFiniteConvergence"
            / "SxEventBridge.lean"
        ):
            required_dependent_product_fragments = (
                "sourceValue : sourceIndex → Type v",
                "((source : sourceIndex) → sourceValue source) × targetValue",
                "[∀ source, Fintype (sourceValue source)]",
                "[∀ source, DecidableEq (sourceValue source)]",
            )
            missing_fragments = tuple(
                fragment
                for fragment in required_dependent_product_fragments
                if fragment not in text
            )
            if missing_fragments:
                raise LeanProofError(
                    "finite categorical Sx event bridge must use the exact "
                    "heterogeneous dependent Cartesian product; "
                    f"missing={missing_fragments}"
                )
            if "sourceValue : Type v" in text:
                raise LeanProofError(
                    "finite categorical Sx event bridge regressed to a shared "
                    "source-value alphabet"
                )
            theorem_pattern = re.compile(
                r"(?m)^(?:@\[[^\n]+\]\s+)?(?:theorem|lemma)\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\b"
            )
            actual_theorems = tuple(theorem_pattern.findall(text))
            if actual_theorems != EXPECTED_SX_EVENT_BRIDGE_THEOREMS:
                raise LeanProofError(
                    "finite categorical Sx event-bridge theorem inventory mismatch: "
                    f"expected={EXPECTED_SX_EVENT_BRIDGE_THEOREMS}, "
                    f"found={actual_theorems}"
                )
        if source == (
            PROJECT
            / "PidFiniteConvergence"
            / "FractionalCover.lean"
        ):
            theorem_pattern = re.compile(
                r"(?m)^(?:@\[[^\n]+\]\s+)?(?:theorem|lemma)\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\b"
            )
            actual_theorems = tuple(theorem_pattern.findall(text))
            if actual_theorems != EXPECTED_FRACTIONAL_COVER_THEOREMS:
                raise LeanProofError(
                    "finite equivalence-union fractional-cover theorem "
                    "inventory mismatch: "
                    f"expected={EXPECTED_FRACTIONAL_COVER_THEOREMS}, "
                    f"found={actual_theorems}"
                )
    return len(sources)


def find_lake() -> Path:
    candidate = shutil.which("lake")
    if candidate is None:
        raise LeanProofError("lake was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"lake is not an executable file: {path}")
    return path


def find_git() -> Path:
    candidate = shutil.which("git")
    if candidate is None:
        raise LeanProofError("git was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"git is not an executable file: {path}")
    return path


def run_git(git: Path, checkout: Path, arguments: list[str], description: str) -> str:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    try:
        process = subprocess.run(
            [str(git), "-C", str(checkout), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}: {process.stderr.strip()}"
        )
    return process.stdout


def check_dependency_checkouts(git: Path) -> None:
    packages_directory = PROJECT / ".lake" / "packages"
    for name, (
        url,
        revision,
        _input_revision,
        _inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        checkout = packages_directory / name
        if not checkout.is_dir() or checkout.is_symlink():
            raise LeanProofError(
                f"dependency checkout is not a regular directory: {checkout}"
            )
        top_level = Path(
            run_git(
                git, checkout, ["rev-parse", "--show-toplevel"], f"{name} root check"
            ).strip()
        )
        if top_level.resolve() != checkout.resolve():
            raise LeanProofError(
                f"dependency checkout root mismatch for {name}: {top_level}"
            )
        actual_revision = run_git(
            git, checkout, ["rev-parse", "--verify", "HEAD"], f"{name} revision check"
        ).strip()
        if actual_revision != revision:
            raise LeanProofError(
                f"dependency revision mismatch for {name}: "
                f"expected {revision}, found {actual_revision}"
            )
        actual_url = run_git(
            git,
            checkout,
            ["config", "--local", "--get", "remote.origin.url"],
            f"{name} origin check",
        ).strip()
        if actual_url != url:
            raise LeanProofError(
                f"dependency origin mismatch for {name}: expected {url}, found {actual_url}"
            )
        status = run_git(
            git,
            checkout,
            ["status", "--porcelain=v1", "--untracked-files=all"],
            f"{name} cleanliness check",
        )
        if status:
            raise LeanProofError(f"dependency checkout is not clean: {name}")


def run_checked(
    command: list[str],
    description: str,
    *,
    input_text: str | None = None,
) -> str:
    environment = os.environ.copy()
    for key in REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    try:
        process = subprocess.run(
            command,
            cwd=PROJECT,
            env=environment,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}:\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout


def support_change_axiom_audit_source() -> str:
    declarations = "\n".join(
        "    ``PidFiniteConvergence." + theorem + ","
        for theorem in EXPECTED_SUPPORT_CHANGE_THEOREMS
    )
    return f"""import PidFiniteConvergence
import Lean.Util.CollectAxioms

open Lean

run_cmd do
  let allowed :=
    ({{}} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let declarations : Array Name := #[
{declarations}
  ]
  for declaration in declarations do
    let used ← collectAxioms declaration
    for assumption in used do
      unless allowed.contains assumption do
        throwError
          m!"unexpected logical assumption {{assumption}} used by {{declaration}}"
"""


def sx_event_bridge_axiom_audit_source() -> str:
    declarations = "\n".join(
        "    ``PidFiniteConvergence." + theorem + ","
        for theorem in EXPECTED_SX_EVENT_BRIDGE_THEOREMS
    )
    return f"""import PidFiniteConvergence
import Lean.Util.CollectAxioms

open Lean

run_cmd do
  let allowed :=
    ({{}} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let declarations : Array Name := #[
{declarations}
  ]
  for declaration in declarations do
    let used ← collectAxioms declaration
    for assumption in used do
      unless allowed.contains assumption do
        throwError
          m!"unexpected logical assumption {{assumption}} used by {{declaration}}"
"""


def fractional_cover_axiom_audit_source() -> str:
    declarations = "\n".join(
        "    ``PidFiniteConvergence." + theorem + ","
        for theorem in EXPECTED_FRACTIONAL_COVER_THEOREMS
    )
    return f"""import PidFiniteConvergence
import Lean.Util.CollectAxioms

open Lean

run_cmd do
  let allowed :=
    ({{}} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let declarations : Array Name := #[
{declarations}
  ]
  for declaration in declarations do
    let used ← collectAxioms declaration
    for assumption in used do
      unless allowed.contains assumption do
        throwError
          m!"unexpected logical assumption {{assumption}} used by {{declaration}}"
"""


def check_version(lake: Path) -> str:
    output = run_checked([str(lake), "env", "lean", "--version"], "Lean version check")
    lines = output.splitlines()
    if (
        len(lines) != 1
        or re.fullmatch(r"Lean \(version 4\.32\.0, .+\)", lines[0]) is None
    ):
        raise LeanProofError(f"unexpected Lean version output: {output!r}")
    return lines[0]


def main() -> int:
    try:
        check_toolchain()
        check_lakefile()
        check_manifest()
        source_count = check_sources()
        lake = find_lake()
        git = find_git()
        version = check_version(lake)
        check_dependency_checkouts(git)
        run_checked([str(lake), "build", "PidFiniteConvergence"], "Lean proof build")
        run_checked(
            [str(lake), "env", "leanchecker", "PidFiniteConvergence"],
            "Lean kernel replay",
        )
        run_checked(
            [str(lake), "env", "lean", "--stdin"],
            "support-change-tolerant theorem axiom-basis audit",
            input_text=support_change_axiom_audit_source(),
        )
        run_checked(
            [str(lake), "env", "lean", "--stdin"],
            "finite categorical Sx event-bridge axiom-basis audit",
            input_text=sx_event_bridge_axiom_audit_source(),
        )
        run_checked(
            [str(lake), "env", "lean", "--stdin"],
            "finite equivalence-union fractional-cover axiom-basis audit",
            input_text=fractional_cover_axiom_audit_source(),
        )
    except LeanProofError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: checked {source_count} Lean sources for the deterministic finite-alphabet "
        f"convergence, dependency-color, local-continuity, support-change-tolerant core, "
        f"heterogeneous finite categorical Sx event bridge, and equivalence-union "
        f"fractional-cover bound ({version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
