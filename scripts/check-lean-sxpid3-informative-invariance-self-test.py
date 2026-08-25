#!/usr/bin/env python3
"""Hostile tests for the separate Lean SxPID3 informative-invariance lane."""

from __future__ import annotations

import ast
import hashlib
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Callable


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-lean-sxpid3-informative-invariance-self-test.py requires "
        "Python 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-lean-sxpid3-informative-invariance.py"
SOURCE = (
    ROOT
    / "audit/formal/lean-sxpid3-informative-invariance"
    / "PidSxPid3InformativeInvariance.lean"
)
EXPECTED_CHECKER_STDOUT_SHA256 = (
    "4133a2c6fc1fe2217914631f3d7fff1af8d1ea37c209f3b55b9b0f8780b6a8b4"
)
EXPECTED_CHECKER_SOURCE_SHA256 = (
    "297c92b7d00272167c4be36c33fb17fb57d8f4958f3ce89615e4200bd30205fc"
)


class SelfTestError(RuntimeError):
    """A required hostile control failed to fail closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def compile_exact_module(path: Path, expected_sha256: str, name: str) -> ModuleType:
    require(
        path.is_file() and not path.is_symlink(),
        f"required regular Python source is missing: {path}",
    )
    source = path.read_bytes()
    require(
        sha256_bytes(source) == expected_sha256,
        f"Python source digest drifted: {path}",
    )
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    code = compile(
        source,
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


def load_checker() -> ModuleType:
    return compile_exact_module(
        CHECKER_PATH,
        EXPECTED_CHECKER_SOURCE_SHA256,
        "pid_sxpid3_informative_invariance_checker",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def make_unchecked_hash_pyc_fixture(directory: Path) -> tuple[Path, str]:
    source = directory / "hostile_loader_fixture.py"
    source.write_text('ROUTE = "bytecode"\n', encoding="utf-8")
    cached = Path(
        py_compile.compile(
            str(source),
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
    )
    require(cached.is_file(), "hostile bytecode fixture was not created")
    bytecode = cached.read_bytes()
    require(
        len(bytecode) >= 16 and int.from_bytes(bytecode[4:8], "little") == 1,
        "hostile bytecode fixture is not unchecked-hash bytecode",
    )
    require(b"bytecode" in bytecode, "hostile bytecode payload is absent")
    source.write_text('ROUTE = "source"\n', encoding="utf-8")
    return source, sha256_bytes(source.read_bytes())


def check_unchecked_hash_pyc_controls(checker: ModuleType) -> int:
    global CHECKER_PATH, EXPECTED_CHECKER_SOURCE_SHA256

    with tempfile.TemporaryDirectory(prefix="pid-sxpid3-hostile-pyc-") as raw:
        source, source_sha256 = make_unchecked_hash_pyc_fixture(Path(raw))

        original_checker_path = CHECKER_PATH
        original_checker_sha256 = EXPECTED_CHECKER_SOURCE_SHA256
        CHECKER_PATH = source
        EXPECTED_CHECKER_SOURCE_SHA256 = source_sha256
        try:
            loaded = load_checker()
            require(
                getattr(loaded, "ROUTE", None) == "source",
                "self-test loader executed unchecked-hash bytecode",
            )
        finally:
            EXPECTED_CHECKER_SOURCE_SHA256 = original_checker_sha256
            CHECKER_PATH = original_checker_path

        original_base_checker = checker.BASE_CHECKER
        original_base_checker_sha256 = checker.EXPECTED_BASE_CHECKER_SHA256
        checker.BASE_CHECKER = source
        checker.EXPECTED_BASE_CHECKER_SHA256 = source_sha256
        try:
            loaded = checker.load_base_checker()
            require(
                getattr(loaded, "ROUTE", None) == "source",
                "production loader executed unchecked-hash bytecode",
            )
        finally:
            checker.EXPECTED_BASE_CHECKER_SHA256 = original_base_checker_sha256
            checker.BASE_CHECKER = original_base_checker

    return 2


def replace_exact_once(text: str, old: str, new: str, name: str) -> str:
    require(text.count(old) == 1, f"{name}: expected one replacement target")
    return text.replace(old, new, 1)


def replace_in_segment(
    text: str,
    start_marker: str,
    end_marker: str,
    old: str,
    new: str,
    name: str,
) -> str:
    require(text.count(start_marker) == 1, f"{name}: start marker is ambiguous")
    prefix, suffix = text.split(start_marker, 1)
    require(suffix.count(end_marker) == 1, f"{name}: end marker is ambiguous")
    segment, tail = suffix.split(end_marker, 1)
    require(segment.count(old) == 1, f"{name}: target is ambiguous")
    return prefix + start_marker + segment.replace(old, new, 1) + end_marker + tail


def heterogeneous_tautology(text: str) -> str:
    text = replace_in_segment(
        text,
        "theorem averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- Exact path invariance precedes calculus:",
        """    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative rightLaw collections := by
  rw [averaged_informative_cumulative_factors_through_source_marginal]
  rw [averaged_informative_cumulative_factors_through_source_marginal]
  unfold averagedInformativeCumulativeFromSourceMarginal
  simp_rw [hSourceMarginal]

""",
        """    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative leftLaw collections := by
  rfl

""",
        "heterogeneous-tautology",
    )
    text = replace_in_segment(
        text,
        "theorem probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- A fixed finite linear transform of cumulative coordinates.",
        """    averagedInformativeCumulativeOnPositiveSupport leftLaw collections =
        averagedInformativeCumulativeOnPositiveSupport rightLaw collections ∧
""",
        """    averagedInformativeCumulativeOnPositiveSupport leftLaw collections =
        averagedInformativeCumulativeOnPositiveSupport leftLaw collections ∧
""",
        "heterogeneous-probability-tautology-statement",
    )
    text = replace_in_segment(
        text,
        "theorem probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- A fixed finite linear transform of cumulative coordinates.",
        """  constructor
  · rw [averaged_informative_on_positive_support_eq_full
      leftLaw collections hLeftProbability.1]
    rw [averaged_informative_on_positive_support_eq_full
      rightLaw collections hRightProbability.1]
    exact averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw collections hSourceMarginal
  · constructor
""",
        """  constructor
  · rfl
  · constructor
""",
        "heterogeneous-probability-tautology-proof",
    )
    text = replace_in_segment(
        text,
        "theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- Probability-semantic atom corollary.",
        """      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw (collections nodeKey) hSourceMarginal)

""",
        """      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative leftLaw (collections nodeKey)) atomKey := by
  rfl

""",
        "heterogeneous-transform-tautology",
    )
    text = replace_in_segment(
        text,
        "theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "end PidFiniteConvergence",
        """      fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw (collections nodeKey) (hCollections nodeKey)
      hLeftProbability hRightProbability hSourceMarginal).1

""",
        """      fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport leftLaw (collections nodeKey)) atomKey := by
  rfl

""",
        "heterogeneous-probability-transform-tautology",
    )
    unused_parameters = (
        (
            "theorem averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target\n",
            "/-- Exact path invariance precedes calculus:",
            ("hSourceMarginal",),
        ),
        (
            "theorem probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target\n",
            "/-- A fixed finite linear transform of cumulative coordinates.",
            ("hSourceMarginal",),
        ),
        (
            "theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target\n",
            "/-- Probability-semantic atom corollary.",
            ("hSourceMarginal",),
        ),
        (
            "theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target\n",
            "end PidFiniteConvergence",
            (
                "hCollections",
                "hLeftProbability",
                "hRightProbability",
                "hSourceMarginal",
            ),
        ),
    )
    for start_marker, end_marker, names in unused_parameters:
        for name in names:
            text = replace_in_segment(
                text,
                start_marker,
                end_marker,
                f"({name} :",
                f"(_{name} :",
                f"heterogeneous-tautology-unused-{name}",
            )
    return text


def zero_fixed_transform(text: str) -> str:
    target = "coefficient atomKey nodeKey *"
    require(text.count(target) == 5, "zero-fixed-transform: expected five semantic sites")
    text = text.replace(target, "0 *")
    for name in ("coefficient", "atomKey"):
        text = replace_in_segment(
            text,
            "noncomputable def fixedLinearTransform\n",
            "/-- A fixed linear transform preserves fixed-source-marginal informative invariance",
            f"({name} :",
            f"(_{name} :",
            f"zero-fixed-transform-unused-{name}",
        )
    return text


def false_heterogeneous_plus_one(text: str) -> str:
    return replace_in_segment(
        text,
        "theorem averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- Exact path invariance precedes calculus:",
        """    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative rightLaw collections := by
""",
        """    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative rightLaw collections + 1 := by
""",
        "false-heterogeneous-plus-one",
    )


def false_fixed_transform_plus_one(text: str) -> str:
    return replace_in_segment(
        text,
        "theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target\n",
        "/-- Probability-semantic atom corollary.",
        """      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative rightLaw (collections nodeKey)) atomKey := by
""",
        """      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative rightLaw (collections nodeKey)) atomKey + 1 := by
""",
        "false-fixed-transform-plus-one",
    )


def run_lean_allow_failure(
    base: ModuleType, lake: Path, source: Path
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for key in base.REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    return subprocess.run(
        [str(lake), "env", "lean", "-t", "0", str(source)],
        cwd=base.PROJECT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=base.TIMEOUT_SECONDS,
        check=False,
    )


def compile_source(base: ModuleType, lake: Path, source: Path, name: str) -> None:
    process = run_lean_allow_failure(base, lake, source)
    require(
        process.returncode == 0,
        f"{name}: well-formed source did not compile: "
        f"stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    require(
        process.stdout == "" and process.stderr == "",
        f"{name}: successful compile emitted diagnostics",
    )


def expect_digest_rejection(
    checker: ModuleType, base: ModuleType, source: Path, name: str
) -> None:
    original = checker.SOURCE
    checker.SOURCE = source
    try:
        checker.check_source(base)
    except RuntimeError as error:
        require(
            "standalone Lean source digest drifted" in str(error),
            f"{name}: digest rejection used wrong route: {error}",
        )
    else:
        raise SelfTestError(f"{name}: checker accepted semantic source drift")
    finally:
        checker.SOURCE = original


def check_semantic_mutations(checker: ModuleType, base: ModuleType, lake: Path) -> int:
    source_text = SOURCE.read_text(encoding="utf-8", errors="strict")
    with tempfile.TemporaryDirectory(prefix="pid-sxpid3-informative-mutations-") as raw:
        temporary = Path(raw)
        baseline = temporary / "baseline.lean"
        baseline.write_text(source_text, encoding="utf-8")
        compile_source(base, lake, baseline, "baseline")

        accepted: tuple[tuple[str, Callable[[str], str]], ...] = (
            ("heterogeneous-tautology", heterogeneous_tautology),
            ("zero-fixed-transform", zero_fixed_transform),
        )
        for name, mutation in accepted:
            path = temporary / f"{name}.lean"
            path.write_text(mutation(source_text), encoding="utf-8")
            compile_source(base, lake, path, name)
            expect_digest_rejection(checker, base, path, name)

        rejected: tuple[tuple[str, Callable[[str], str]], ...] = (
            ("false-heterogeneous-plus-one", false_heterogeneous_plus_one),
            ("false-fixed-transform-plus-one", false_fixed_transform_plus_one),
        )
        for name, mutation in rejected:
            path = temporary / f"{name}.lean"
            path.write_text(mutation(source_text), encoding="utf-8")
            process = run_lean_allow_failure(base, lake, path)
            require(process.returncode != 0, f"{name}: Lean accepted a false theorem")
            diagnostic = process.stdout + process.stderr
            require(
                "error" in diagnostic.lower(),
                f"{name}: Lean failed without an error diagnostic: {diagnostic!r}",
            )
    return len(accepted) + len(rejected)


def copy_static_fixture(checker: ModuleType, destination: Path) -> None:
    source_path = destination / "lane/source.lean"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(checker.SOURCE, source_path)
    project = destination / "project"
    for relative in (
        "PidFiniteConvergence.lean",
        *checker.EXPECTED_LOCAL_DEPENDENCIES,
    ):
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checker.PROJECT / relative, target)


def expect_static_failure(
    checker: ModuleType,
    base: ModuleType,
    name: str,
    mutation: Callable[[Path, Path], None],
    expected: str,
    *,
    accept_mutated_source_digest: bool = False,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"pid-sxpid3-static-{name}-") as raw:
        temporary = Path(raw)
        copy_static_fixture(checker, temporary)
        source = temporary / "lane/source.lean"
        project = temporary / "project"
        mutation(source, project)
        original_source = checker.SOURCE
        original_project = checker.PROJECT
        original_root = checker.AGGREGATE_ROOT
        original_lane = checker.LANE_DIRECTORY
        original_digest = checker.EXPECTED_SOURCE_SHA256
        checker.SOURCE = source
        checker.PROJECT = project
        checker.AGGREGATE_ROOT = project / "PidFiniteConvergence.lean"
        checker.LANE_DIRECTORY = source.parent
        if accept_mutated_source_digest:
            checker.EXPECTED_SOURCE_SHA256 = sha256_bytes(source.read_bytes())
        try:
            checker.check_source(base)
        except RuntimeError as error:
            require(expected in str(error), f"{name}: wrong rejection route: {error}")
        else:
            raise SelfTestError(f"{name}: checker accepted static mutation")
        finally:
            checker.EXPECTED_SOURCE_SHA256 = original_digest
            checker.LANE_DIRECTORY = original_lane
            checker.AGGREGATE_ROOT = original_root
            checker.PROJECT = original_project
            checker.SOURCE = original_source


def append_source(source: Path, _project: Path) -> None:
    source.write_text(
        source.read_text(encoding="utf-8") + "\n/- drift -/\n",
        encoding="utf-8",
    )


def mutate_import(source: Path, _project: Path) -> None:
    text = source.read_text(encoding="utf-8")
    source.write_text(
        replace_exact_once(
            text,
            "import Mathlib.Analysis.Calculus.Deriv.Basic",
            "import Mathlib.Analysis.Calculus.Deriv.Mul",
            "source-import",
        ),
        encoding="utf-8",
    )


def rename_theorem(source: Path, _project: Path) -> None:
    text = source.read_text(encoding="utf-8")
    source.write_text(
        replace_exact_once(
            text,
            "theorem averaged_informative_cumulative_factors_through_source_marginal\n",
            "theorem averaged_informative_cumulative_factors_through_source_marginal_mutated\n",
            "theorem-rename",
        ),
        encoding="utf-8",
    )


def mutate_dependency(_source: Path, project: Path) -> None:
    path = project / "PidFiniteConvergence/SxEventBridge.lean"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def mutate_deterministic_dependency(_source: Path, project: Path) -> None:
    path = project / "PidFiniteConvergence/Deterministic.lean"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def add_unexpected_lane_source(source: Path, _project: Path) -> None:
    (source.parent / "Unexpected.lean").write_text(
        "def unexpectedLaneDeclaration : Nat := 0\n", encoding="utf-8"
    )


def mutate_root(_source: Path, project: Path) -> None:
    path = project / "PidFiniteConvergence.lean"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def check_static_mutations(checker: ModuleType, base: ModuleType) -> int:
    cases = (
        ("source-byte", append_source, "standalone Lean source digest drifted", False),
        ("source-import", mutate_import, "standalone Lean import roster drifted", True),
        ("theorem-rename", rename_theorem, "standalone Lean declaration roster drifted", True),
        (
            "dependency-byte",
            mutate_dependency,
            "local Lean dependency digest drifted: "
            "PidFiniteConvergence/SxEventBridge.lean",
            False,
        ),
        (
            "deterministic-dependency-byte",
            mutate_deterministic_dependency,
            "local Lean dependency digest drifted: "
            "PidFiniteConvergence/Deterministic.lean",
            False,
        ),
        (
            "lane-source-manifest",
            add_unexpected_lane_source,
            "standalone Lean lane source manifest",
            False,
        ),
        ("aggregate-root-byte", mutate_root, "frozen aggregate Lean root digest drifted", False),
    )
    for name, mutation, expected, accept_digest in cases:
        expect_static_failure(
            checker,
            base,
            name,
            mutation,
            expected,
            accept_mutated_source_digest=accept_digest,
        )

    with tempfile.TemporaryDirectory(prefix="pid-sxpid3-base-checker-") as raw:
        mutated = Path(raw) / "checker.py"
        mutated.write_text(
            checker.BASE_CHECKER.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        original = checker.BASE_CHECKER
        checker.BASE_CHECKER = mutated
        try:
            checker.load_base_checker()
        except RuntimeError as error:
            require(
                "immutable aggregate checker digest drifted" in str(error),
                f"base-checker-byte: wrong rejection route: {error}",
            )
        else:
            raise SelfTestError("base-checker-byte: mutated checker was accepted")
        finally:
            checker.BASE_CHECKER = original

    original_project = base.PROJECT
    try:
        with tempfile.TemporaryDirectory(prefix="pid-sxpid3-config-") as raw:
            project = Path(raw)
            for name in ("lake-manifest.json", "lakefile.toml", "lean-toolchain"):
                shutil.copy2(original_project / name, project / name)
            base.PROJECT = project
            for name, function, expected in (
                (
                    "manifest-byte",
                    base.check_manifest,
                    "Lake manifest byte digest mismatch",
                ),
                (
                    "lakefile-byte",
                    base.check_lakefile,
                    "lakefile.toml does not match",
                ),
                (
                    "toolchain-byte",
                    base.check_toolchain,
                    "lean-toolchain must contain exactly",
                ),
            ):
                path = project / {
                    "manifest-byte": "lake-manifest.json",
                    "lakefile-byte": "lakefile.toml",
                    "toolchain-byte": "lean-toolchain",
                }[name]
                original_bytes = path.read_bytes()
                path.write_bytes(original_bytes + b"\n")
                try:
                    function()
                except RuntimeError as error:
                    require(expected in str(error), f"{name}: wrong rejection route: {error}")
                else:
                    raise SelfTestError(f"{name}: mutated configuration was accepted")
                path.write_bytes(original_bytes)
    finally:
        base.PROJECT = original_project

    wrong_version = subprocess.CompletedProcess(
        ["lean", "--version"],
        0,
        "Lean (version 4.33.0, aarch64-apple-darwin, "
        "commit 08b18978322de05a8f3dba51ef03cf5461676c17, Release)\n",
        "",
    )
    try:
        base.parse_lean_version_probe(wrong_version)
    except RuntimeError as error:
        require(
            "unexpected Lean portable identity" in str(error),
            f"version-transport: wrong rejection route: {error}",
        )
    else:
        raise SelfTestError("version-transport: wrong commit was accepted")
    return len(cases) + 5


def check_no_optimization_sensitive_asserts(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        f"{path.name} contains optimization-sensitive assert",
    )
    require(
        not any(
            isinstance(node, ast.Name) and node.id == "__debug__"
            for node in ast.walk(tree)
        ),
        f"{path.name} contains optimization-sensitive __debug__",
    )


def check_no_dynamic_source_loader(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    blocked_module = "".join(("import", "lib"))
    blocked_names = {
        "".join(("Source", "File", "Loader")),
        "_".join(("spec", "from", "file", "location")),
        "_".join(("module", "from", "spec")),
        "".join(("__", "import", "__")),
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            require(
                all(
                    alias.name != blocked_module
                    and not alias.name.startswith(blocked_module + ".")
                    for alias in node.names
                ),
                f"{path.name} imports dynamic source-loading machinery",
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            require(
                module != blocked_module
                and not module.startswith(blocked_module + "."),
                f"{path.name} imports dynamic source-loading machinery",
            )
        elif isinstance(node, ast.Name):
            require(
                node.id not in blocked_names,
                f"{path.name} uses a forbidden dynamic loader symbol",
            )
        elif isinstance(node, ast.Attribute):
            require(
                node.attr not in blocked_names,
                f"{path.name} uses a forbidden dynamic loader attribute",
            )


def run_checker(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,
        check=False,
    )


def check_nonisolated_checker_rejected() -> None:
    process = run_checker([sys.executable, str(CHECKER_PATH)])
    require(process.returncode == 2, "non-isolated checker exit")
    require(process.stdout == b"", "non-isolated checker wrote stdout")
    require(
        process.stderr
        == (
            b"ERROR: check-lean-sxpid3-informative-invariance.py requires "
            b"Python 3.11+ -I -S -B, with -O optional\n"
        ),
        "non-isolated checker diagnostic",
    )


def check_checker_parity() -> bytes:
    normal = run_checker(
        [sys.executable, "-I", "-S", "-B", str(CHECKER_PATH)]
    )
    optimized = run_checker(
        [sys.executable, "-O", "-I", "-S", "-B", str(CHECKER_PATH)]
    )
    require(normal.returncode == 0, f"normal checker failed: {normal.stderr!r}")
    require(optimized.returncode == 0, f"optimized checker failed: {optimized.stderr!r}")
    require(normal.stderr == b"" and optimized.stderr == b"", "checker emitted stderr")
    require(normal.stdout == optimized.stdout, "normal and optimized checker output differ")
    require(normal.stdout.endswith(b"\n"), "checker output lacks final LF")
    actual_sha256 = sha256_bytes(normal.stdout)
    require(
        actual_sha256 == EXPECTED_CHECKER_STDOUT_SHA256,
        "checker canonical stdout digest drifted: "
        f"expected {EXPECTED_CHECKER_STDOUT_SHA256}, found {actual_sha256}",
    )
    return normal.stdout


def main() -> int:
    try:
        check_nonisolated_checker_rejected()
        check_no_optimization_sensitive_asserts(CHECKER_PATH)
        check_no_optimization_sensitive_asserts(Path(__file__).resolve())
        check_no_dynamic_source_loader(CHECKER_PATH)
        check_no_dynamic_source_loader(Path(__file__).resolve())
        checker = load_checker()
        unchecked_hash_pyc_controls = check_unchecked_hash_pyc_controls(checker)
        base = checker.load_base_checker()
        checker_stdout = check_checker_parity()
        lake = base.find_lake()
        semantic_count = check_semantic_mutations(checker, base, lake)
        static_count = check_static_mutations(checker, base)
    except (OSError, UnicodeError, ImportError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    result = {
        "schema": "pid-rs/lean-sxpid3-informative-invariance-self-test/v1",
        "status": "passed",
        "checker_normal_optimized_identical": True,
        "checker_stdout_sha256": sha256_bytes(checker_stdout),
        "semantic_mutations": semantic_count,
        "static_and_transport_mutations": static_count,
        "accepted_semantic_weakenings_compiled_then_digest_rejected": 2,
        "false_theorem_statements_kernel_rejected": 2,
        "nonisolated_checker_rejected": True,
        "optimization_sensitive_asserts": 0,
        "dynamic_source_loader_routes": 0,
        "unchecked_hash_pyc_controls": unchecked_hash_pyc_controls,
        "source_sha256": checker.EXPECTED_SOURCE_SHA256,
    }
    import json

    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
