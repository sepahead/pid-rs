#!/usr/bin/env python3
"""Prove that the certifier static policy fails closed on representative mutations."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


MUTATIONS = (
    (
        "implicit_float_conversion",
        "src/directed.rs",
        "Float::with_val_round(precision_bits, 0, Round::Down)",
        "Float::with_val(precision_bits, 0)",
    ),
    (
        "implicit_log_rounding",
        "src/directed.rs",
        "log_lower.ln_round(Round::Down)",
        "log_lower.ln()",
    ),
    (
        "nearest_rounding",
        "src/directed.rs",
        "Round::Down",
        "Round::Nearest",
    ),
    (
        "binary64_escape",
        "src/directed.rs",
        "let result = Enclosure {",
        "let _escaped = lower_sum.to_f64();\n    let result = Enclosure {",
    ),
    (
        "unsafe_function_surface",
        "src/lib.rs",
        "#![forbid(unsafe_code)]",
        "#![allow(unsafe_code)]\nunsafe fn qualification_only_unsafe_surface() {}",
    ),
    (
        "float_outside_wrapper",
        "src/exact.rs",
        "use rug::Rational;",
        "use rug::{Float, Rational};",
    ),
    (
        "reordered_float_import_outside_wrapper",
        "src/exact.rs",
        "use rug::Rational;",
        "use rug::{Rational, Float};",
    ),
    (
        "aliased_round_outside_wrapper",
        "src/exact.rs",
        "use rug::Rational;",
        "use rug::float::Round as Direction;\nuse rug::Rational;",
    ),
    (
        "unmanifested_compile_time_include",
        "src/lib.rs",
        "mod digest;",
        "include!(\"../rogue.inc\");\nmod digest;",
    ),
    (
        "unmanifested_compile_time_string",
        "src/extract.rs",
        "use std::collections::BTreeMap;",
        "const ROGUE: &str = include_str!(\"../rogue.txt\");\nuse std::collections::BTreeMap;",
    ),
    (
        "unmanifested_compile_time_bytes",
        "src/extract.rs",
        "use std::collections::BTreeMap;",
        "const ROGUE: &[u8] = include_bytes!(\"../rogue.bin\");\nuse std::collections::BTreeMap;",
    ),
    (
        "aliased_unmanifested_compile_time_string",
        "src/extract.rs",
        "use std::collections::BTreeMap;",
        "use core::include_str as load_unbound;\nconst ROGUE: &str = load_unbound!(\"../rogue.txt\");\nuse std::collections::BTreeMap;",
    ),
    (
        "unmanifested_path_module",
        "src/lib.rs",
        "mod digest;",
        "#[path = \"../rogue.rs\"]\nmod rogue;\nmod digest;",
    ),
    (
        "unmanifested_cfg_attr_path_module",
        "src/lib.rs",
        "mod digest;",
        "#[cfg_attr(all(), path = \"../rogue.rs\")]\nmod rogue;\nmod digest;",
    ),
    (
        "direct_native_sys_dependency_surface",
        "Cargo.toml",
        "[dependencies]\n",
        '[dependencies]\ngmp-mpfr-sys = { version = "=1.7.1", default-features = false, features = ["mpfr", "use-system-libs"] }\n',
    ),
    (
        "effective_feature_report_overclaim",
        "src/report.rs",
        "manifest_requested_rug_features",
        "configured_rug_features",
    ),
    (
        "missing_directed_multiplication",
        "src/directed.rs",
        "term_lower.mul_assign_round(coefficient, Round::Down)",
        "term_lower *= coefficient",
    ),
    (
        "negative_coefficient_endpoint_swap",
        "src/directed.rs",
        "(log_upper, log_lower)",
        "(log_lower, log_upper)",
    ),
    (
        "positive_sign_includes_zero_boundary",
        "src/directed.rs",
        "else if self.lower.to_rational() > 0",
        "else if self.lower.to_rational() >= 0",
    ),
    (
        "negative_sign_includes_zero_boundary",
        "src/directed.rs",
        "else if self.upper.to_rational() < 0",
        "else if self.upper.to_rational() <= 0",
    ),
    (
        "target_vector_match_shortcut",
        "src/extract.rs",
        "if require_target && row.state.target != realization.target {",
        "if require_target && row.state.target != realization.target && realization.target.len() == 1 {",
    ),
    (
        "source_one_vector_match_shortcut",
        "src/extract.rs",
        "(mask & 0b01 == 0 || state.source_one == realization.source_one)",
        "(mask & 0b01 == 0 || state.source_one == realization.source_one || state.source_one.len() > 1)",
    ),
    (
        "keyed_mass_target_union_nesting_removed",
        "src/extract.rs",
        "|| row_count > target_union",
        "|| false",
    ),
    (
        "target_union_source_union_nesting_removed",
        "src/extract.rs",
        "|| target_union > union",
        "|| false",
    ),
    (
        "source_manifest_path_redirected",
        "src/lib.rs",
        '("src/exact.rs", include_bytes!("exact.rs"))',
        '("src/exact.rs", include_bytes!("error.rs"))',
    ),
    (
        "build_script_route_changed",
        "Cargo.toml",
        'build = "build.rs"',
        'build = "rogue-build.rs"',
    ),
    (
        "resource_preflight_removed",
        "src/lib.rs",
        "report::validate_resource_bounds(&extraction)?;",
        "let _resource_preflight_removed = &extraction;",
    ),
    (
        "target_width_report_restatement",
        "src/report.rs",
        "let target_width_met = interval.width() <= policy.target_width;",
        "let target_width_met = true;",
    ),
    (
        "incremental_expression_limit_removed",
        "src/exact.rs",
        "if self.terms.len() >= MAX_TERMS_PER_EXPRESSION",
        "if false",
    ),
    (
        "incremental_cumulative_limit_removed",
        "src/extract.rs",
        "validate_cumulative_resource_growth(&cumulative)?;",
        "let _cumulative_limit_removed = &cumulative;",
    ),
    (
        "redundancy_event_changed_to_joint",
        "src/lattice2.rs",
        "&[0b01, 0b10]",
        "&[0b11]",
    ),
    (
        "mobius_coefficient_change",
        "src/lattice2.rs",
        "[-1, -1, 1, 1]",
        "[-1, -1, 1, 0]",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="certifier crate root",
    )
    return parser.parse_args()


def run_checker(checker: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(checker), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    root = parse_args().root.resolve()
    checker = root / "scripts" / "check-static-policy.py"
    baseline = run_checker(checker, root)
    if baseline.returncode != 0:
        print("self-test error: baseline static policy does not pass", file=sys.stderr)
        print(baseline.stderr, file=sys.stderr)
        return 1

    killed = 0
    for name, relative_path, old, new in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="pid-certified-sxpid-policy-") as temporary:
            mutant = Path(temporary) / "certified-sxpid"
            shutil.copytree(root, mutant)
            target = mutant / relative_path
            text = target.read_text(encoding="utf-8")
            if text.count(old) == 0:
                print(
                    f"self-test error: mutation {name!r} cannot find its source fragment",
                    file=sys.stderr,
                )
                return 1
            target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
            result = run_checker(checker, mutant)
            if result.returncode == 0:
                print(
                    f"self-test error: static policy accepted mutation {name!r}",
                    file=sys.stderr,
                )
                return 1
            killed += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-certified-sxpid-policy-"
    ) as temporary:
        mutant = Path(temporary) / "certified-sxpid"
        shutil.copytree(root, mutant)
        rogue = mutant / "src" / "rogue.rs"
        rogue.write_text(
            "use rug::Float;\n"
            "pub(crate) fn implicit_rounding() -> Float {\n"
            "    Float::with_val(53, 1.25)\n"
            "}\n",
            encoding="utf-8",
            newline="",
        )
        library = mutant / "src" / "lib.rs"
        text = library.read_text(encoding="utf-8")
        library.write_text(
            text.replace("mod report;\n", "mod report;\nmod rogue;\n", 1),
            encoding="utf-8",
            newline="",
        )
        result = run_checker(checker, mutant)
        if result.returncode == 0:
            print(
                "self-test error: static policy accepted an unmanifested Rust module",
                file=sys.stderr,
            )
            return 1
        killed += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-certified-sxpid-policy-"
    ) as temporary:
        mutant = Path(temporary) / "certified-sxpid"
        shutil.copytree(root, mutant)
        helper = mutant / "helper.rs"
        helper.write_text(
            'pub(crate) const UNMANIFESTED_BUILD_INPUT: &str = "drift";\n',
            encoding="utf-8",
            newline="",
        )
        build_script = mutant / "build.rs"
        text = build_script.read_text(encoding="utf-8")
        build_script.write_text(
            text.replace(
                "use std::env;\n",
                "mod helper;\nuse std::env;\n",
                1,
            ),
            encoding="utf-8",
            newline="",
        )
        result = run_checker(checker, mutant)
        if result.returncode == 0:
            print(
                "self-test error: static policy accepted an unmanifested build-script module",
                file=sys.stderr,
            )
            return 1
        killed += 1

    if killed != len(MUTATIONS) + 2:
        print("self-test error: mutation accounting changed", file=sys.stderr)
        return 1
    print(f"OK: certified-sxpid static policy killed all {killed} representative mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
