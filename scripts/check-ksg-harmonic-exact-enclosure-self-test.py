#!/usr/bin/env python3
"""Baseline-first mutation suite for the KSG exact-enclosure checker."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-ksg-harmonic-exact-enclosure.py"


class SelfTestError(RuntimeError):
    """The baseline failed or a load-bearing exact-enclosure mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    require(
        count == 1,
        f"{label}: expected exactly one source replacement target, found {count}",
    )
    return source.replace(old, new, 1)


def child_optimization_arguments() -> list[str]:
    require(
        sys.flags.optimize in (0, 1, 2),
        f"unsupported parent optimization level: {sys.flags.optimize}",
    )
    if sys.flags.optimize == 0:
        return []
    return ["-" + "O" * sys.flags.optimize]


def child_python_command(script: Path, *arguments: str) -> list[str]:
    return [
        sys.executable,
        *child_optimization_arguments(),
        str(script),
        *arguments,
    ]


def run_command(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def child_optimization_preflight() -> None:
    probe = run_command(
        [
            sys.executable,
            *child_optimization_arguments(),
            "-c",
            "import sys; print(sys.flags.optimize)",
        ]
    )
    require(
        probe.returncode == 0,
        "child-optimization preflight process failed:\n"
        + probe.stdout
        + probe.stderr,
    )
    require(
        probe.stdout == f"{sys.flags.optimize}\n",
        "child-optimization preflight did not preserve the parent level: "
        f"parent={sys.flags.optimize}, child={probe.stdout!r}",
    )


def baseline_first() -> str:
    child_optimization_preflight()
    baseline = run_command(
        child_python_command(CHECKER, "--repo-root", str(ROOT))
    )
    require(
        baseline.returncode == 0,
        "exact-enclosure checker baseline failed before mutation testing:\n"
        + baseline.stdout
        + baseline.stderr,
    )
    required_output = (
        "digest-bound directed exact-rational enclosure for 8198 frozen schema-2 rows",
        "1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747",
        "6920 exhaustive exact-Fraction containment witnesses",
        "6509 textually unequal, 5934 numerically unequal",
        "unique maximum discrepancy 8.18E-77 at zero-based row 7952 "
        "(65536, 64, 32799, 32799)",
        "binary64 conversion mismatches 0",
        "8198 exact Fraction(Decimal) discrepancy comparisons",
        "Python reproduction of selected Neumaier-prefix/sorted-range",
        "binary64 versus exact rational: unique maximum at zero-based row 7673 "
        "(4096, 4, 2049, 2049)",
        "selected value -0x1.6b52fe6a01407p+2",
        "strictly below 9.761311 epsilon and below 32 epsilon",
        "distinct binary64-rounded-reference comparator: maximum 8 epsilon; "
        "40 ties; first zero-based row 7598 (4096, 1, 2048, 2048)",
        "shared cuts/assumptions: same-repository digest-bound frozen rows and exact harmonic "
        "identity",
        "does not inspect Rust source or a compiled binary",
        "same-repository digest binding is an internal integrity check, not artifact authenticity",
        "not a universal error theorem, cross-platform identity claim, Rust-source or "
        "compiled-binary conformance claim",
    )
    for fragment in required_output:
        require(fragment in baseline.stdout, f"baseline output lost contract: {fragment}")
    require(
        baseline.stderr == "",
        "exact-enclosure checker baseline unexpectedly wrote stderr:\n"
        + baseline.stderr,
    )
    return CHECKER.read_text(encoding="utf-8")


def mutations() -> tuple[tuple[str, str, str], ...]:
    return (
        (
            "lower-rounding-direction",
            "LOWER_ROUNDING = ROUND_FLOOR",
            "LOWER_ROUNDING = ROUND_CEILING",
        ),
        (
            "upper-rounding-direction",
            "UPPER_ROUNDING = ROUND_CEILING",
            "UPPER_ROUNDING = ROUND_FLOOR",
        ),
        (
            "directed-precision",
            "ENCLOSURE_PRECISION = 160",
            "ENCLOSURE_PRECISION = 159",
        ),
        (
            "lower-rounding-operation",
            "    lower_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=LOWER_ROUNDING)\n"
            "    upper_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=UPPER_ROUNDING)",
            "    lower_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=UPPER_ROUNDING)\n"
            "    upper_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=UPPER_ROUNDING)",
        ),
        (
            "upper-rounding-operation",
            "    lower_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=LOWER_ROUNDING)\n"
            "    upper_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=UPPER_ROUNDING)",
            "    lower_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=LOWER_ROUNDING)\n"
            "    upper_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=LOWER_ROUNDING)",
        ),
        (
            "directed-precision-operation",
            "    lower_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=LOWER_ROUNDING)\n"
            "    upper_context = Context(prec=ENCLOSURE_PRECISION, "
            "rounding=UPPER_ROUNDING)",
            "    lower_context = Context(prec=159, rounding=LOWER_ROUNDING)\n"
            "    upper_context = Context(prec=159, rounding=UPPER_ROUNDING)",
        ),
        (
            "reconstructed-row-order",
            "STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)",
            "STRESS_SAMPLE_SIZES = (32, 17, 64, 256, 4_096, 65_536, 1_000_000)",
        ),
        (
            "symbolic-endpoint-branch",
            "    if is_endpoint(row):\n"
            "        # Pairwise symbolic cancellation is exact.",
            "    if False and is_endpoint(row):\n"
            "        # Pairwise symbolic cancellation is exact.",
        ),
        (
            "exact-rounded-vector-digest",
            "1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747",
            "0d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747",
        ),
        (
            "stored-numeric-mismatch-count",
            "EXPECTED_STORED_NUMERIC_MISMATCH_COUNT = 5_934",
            "EXPECTED_STORED_NUMERIC_MISMATCH_COUNT = 5_933",
        ),
        (
            "stored-text-mismatch-count",
            "EXPECTED_STORED_TEXT_MISMATCH_COUNT = 6_509",
            "EXPECTED_STORED_TEXT_MISMATCH_COUNT = 6_508",
        ),
        (
            "stored-binary64-mismatch-count",
            "EXPECTED_STORED_BINARY64_MISMATCH_COUNT = 0",
            "EXPECTED_STORED_BINARY64_MISMATCH_COUNT = 1",
        ),
        (
            "stored-maximum-row",
            "EXPECTED_STORED_MAX_DISCREPANCY_ROW_INDEX = 7_952",
            "EXPECTED_STORED_MAX_DISCREPANCY_ROW_INDEX = 7_951",
        ),
        (
            "exact-error-maximum-row",
            "EXPECTED_EXACT_ERROR_MAX_ROW_INDEX = 7_673",
            "EXPECTED_EXACT_ERROR_MAX_ROW_INDEX = 7_672",
        ),
        (
            "exact-error-maximum-tie",
            "EXPECTED_EXACT_ERROR_MAX_TIES = 1",
            "EXPECTED_EXACT_ERROR_MAX_TIES = 2",
        ),
        (
            "exact-error-maximum-selected-value",
            'EXPECTED_EXACT_ERROR_MAX_ACTUAL_HEX = "-0x1.6b52fe6a01407p+2"',
            'EXPECTED_EXACT_ERROR_MAX_ACTUAL_HEX = "-0x1.6b52fe6a01408p+2"',
        ),
        (
            "exact-error-reference-metric",
            "actual_decimal = Decimal.from_float(actual)",
            "actual_decimal = Decimal(str(actual))",
        ),
        (
            "below-interval-error-upper-endpoint",
            "    if actual_decimal < exact_lower:\n"
            "        return ErrorInterval(\n"
            "            lower_context.subtract(exact_lower, actual_decimal),\n"
            "            upper_context.subtract(exact_upper, actual_decimal),\n"
            "        )",
            "    if actual_decimal < exact_lower:\n"
            "        return ErrorInterval(\n"
            "            lower_context.subtract(exact_lower, actual_decimal),\n"
            "            upper_context.subtract(exact_lower, actual_decimal),\n"
            "        )",
        ),
        (
            "above-interval-error-upper-endpoint",
            "    if actual_decimal > exact_upper:\n"
            "        return ErrorInterval(\n"
            "            lower_context.subtract(actual_decimal, exact_upper),\n"
            "            upper_context.subtract(actual_decimal, exact_lower),\n"
            "        )",
            "    if actual_decimal > exact_upper:\n"
            "        return ErrorInterval(\n"
            "            lower_context.subtract(actual_decimal, exact_upper),\n"
            "            upper_context.subtract(actual_decimal, exact_upper),\n"
            "        )",
        ),
        (
            "inside-interval-error-farthest-endpoint",
            "        max(\n"
            "            upper_context.subtract(actual_decimal, exact_lower),",
            "        min(\n"
            "            upper_context.subtract(actual_decimal, exact_lower),",
        ),
        (
            "unique-maximum-separation-predicate",
            "    return candidate.lower > other_maximum_upper",
            "    return True",
        ),
        (
            "selected-full-corpus-nonzero-count",
            "EXPECTED_SELECTED_NONZERO_COUNT = 7_844",
            "EXPECTED_SELECTED_NONZERO_COUNT = 7_843",
        ),
        (
            "rounded-reference-metric",
            "rounded_reference_error = abs(actual - float(stored))",
            "rounded_reference_error = abs(actual - actual)",
        ),
        (
            "eight-versus-exact-bound-conflation",
            'EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT = "9.761311"',
            'EXPECTED_EXACT_STRICT_EPSILON_MULTIPLIER_TEXT = "8"',
        ),
        (
            "strict-threshold-rounding-direction",
            "        lower_context,\n"
            "    )\n"
            "    allowed_threshold = strict_lower_threshold(",
            "        upper_context,\n"
            "    )\n"
            "    allowed_threshold = strict_lower_threshold(",
        ),
        (
            "review-ceiling-loosening",
            "EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER = 32",
            "EXPECTED_ALLOWED_ERROR_EPSILON_MULTIPLIER = 64",
        ),
        (
            "rounded-reference-tie-count",
            "EXPECTED_ROUNDED_REFERENCE_MAX_TIES = 40",
            "EXPECTED_ROUNDED_REFERENCE_MAX_TIES = 39",
        ),
        (
            "rounded-reference-first-row",
            "EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW_INDEX = 7_598",
            "EXPECTED_ROUNDED_REFERENCE_FIRST_MAX_ROW_INDEX = 7_597",
        ),
        (
            "scope-output-wording",
            '"check, not artifact authenticity; not a universal error theorem, '
            'cross-platform identity "',
            '"check, artifact authenticity; a universal error theorem, '
            'cross-platform identity "',
        ),
    )


def run_mutation_suite(source: str) -> int:
    caught = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-exact-enclosure-self-test-") as raw:
        mutant_path = Path(raw) / CHECKER.name
        for label, old, new in mutations():
            mutant_source = replace_once(source, old, new, label)
            mutant_path.write_text(mutant_source, encoding="utf-8", newline="")
            result = run_command(
                child_python_command(
                    mutant_path,
                    "--repo-root",
                    str(ROOT),
                )
            )
            require(
                result.returncode != 0,
                f"{label}: load-bearing mutation survived:\n"
                + result.stdout
                + result.stderr,
            )
            require(
                "exact-enclosure check failed:" in result.stderr,
                f"{label}: mutation did not fail through the controlled checker boundary:\n"
                + result.stdout
                + result.stderr,
            )
            require(
                "Traceback" not in result.stderr,
                f"{label}: mutation escaped as a traceback:\n" + result.stderr,
            )
            caught += 1
    return caught


def comparator_controls() -> tuple[tuple[str, str, str], ...]:
    """Exact-comparator controls kept separate from the 29 scientific mutants."""

    return (
        (
            "exact-comparator-rounded-decimal-subtraction",
            "    return abs(Fraction(left) - Fraction(right))",
            "    return Fraction(abs(left - right))",
        ),
        (
            "exact-comparator-maximum-fraction",
            "EXPECTED_STORED_MAX_DISCREPANCY = Fraction(818, 10**79)",
            "EXPECTED_STORED_MAX_DISCREPANCY = Fraction(817, 10**79)",
        ),
    )


def run_comparator_controls(source: str) -> int:
    caught = 0
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-exact-comparator-controls-"
    ) as raw:
        mutant_path = Path(raw) / CHECKER.name
        for label, old, new in comparator_controls():
            mutant_source = replace_once(source, old, new, label)
            mutant_path.write_text(mutant_source, encoding="utf-8", newline="")
            result = run_command(
                child_python_command(
                    mutant_path,
                    "--repo-root",
                    str(ROOT),
                )
            )
            require(
                result.returncode != 0,
                f"{label}: exact-comparator control survived:\n"
                + result.stdout
                + result.stderr,
            )
            require(
                "exact-enclosure check failed:" in result.stderr
                and "Traceback" not in result.stderr,
                f"{label}: control escaped the controlled checker boundary:\n"
                + result.stdout
                + result.stderr,
            )
            caught += 1
    return caught


def main() -> int:
    try:
        source = baseline_first()
        caught = run_mutation_suite(source)
        require(caught == len(mutations()), "not every declared mutation ran")
        comparator_caught = run_comparator_controls(source)
        require(
            comparator_caught == len(comparator_controls()) == 2,
            "exact-comparator control inventory changed",
        )
    except (OSError, SelfTestError) as error:
        print(f"exact-enclosure self-test failed: {error}", file=sys.stderr)
        return 1
    print(
        "OK: exact-enclosure baseline passed and "
        f"{caught}/{len(mutations())} load-bearing mutations were rejected "
        f"(child optimize={sys.flags.optimize}); separately, "
        f"{comparator_caught}/{len(comparator_controls())} exact-comparator "
        "controls were rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
