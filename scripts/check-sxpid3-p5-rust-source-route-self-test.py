#!/usr/bin/env python3
"""Fail-closed mutation suite for the P5-v2 Rust lexical source route."""

from __future__ import annotations

import ast
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Final, NamedTuple


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CHECKER_RELATIVE: Final[Path] = Path("scripts/check-sxpid3-p5-rust-source-route.py")
PRIMARY_CHECKER_RELATIVE: Final[Path] = Path(
    "scripts/check-sxpid3-bounded-full-coordinates.py"
)
DISCRETE_PID_RELATIVE: Final[Path] = Path("crates/pid-core/src/discrete_pid.rs")
SXPID_RELATIVE: Final[Path] = Path("crates/pid-core/src/sxpid.rs")
SELF_RELATIVE: Final[Path] = Path(
    "scripts/check-sxpid3-p5-rust-source-route-self-test.py"
)
EXPECTED_STDOUT_SHA256: Final[str] = (
    "a8cdab4307bf3bc46b03ad6487282a5ab4f0768959d1370f008860de978f22d0"
)
EXPECTED_CHECKER_SOURCE_SHA256: Final[str] = (
    "1bb15e5a45c2e5fdde8b8d933df64cc875f26b1d79fb048f2a68af57d9b3f603"
)
EXPECTED_PRIMARY_CHECKER_SOURCE_SHA256: Final[str] = (
    "d9d1c540930855b31f8190fdb2095d215c736f6f6c3d19c60e2a353923be06d2"
)
EXPECTED_MANIFEST_SHA256: Final[str] = (
    "e0ef5a05bbade1ccbd83767ee0e1e39f05276790bb2b433dd8e5fff7ea83046a"
)
EXPECTED_STABLE_KEYS: Final[list[str]] = [
    "01",
    "02",
    "04",
    "03",
    "05",
    "06",
    "07",
    "01+02",
    "01+04",
    "01+06",
    "02+04",
    "02+05",
    "03+04",
    "03+05",
    "03+06",
    "05+06",
    "01+02+04",
    "03+05+06",
]
EXPECTED_BOUNDARIES: Final[list[str]] = [
    "lexical_source_route_only",
    "rust_name_resolution_not_formally_verified",
    "compiled_rust_refinement_open",
    "rust_numeric_values_not_compared",
    "binary64_refinement_not_established",
    "108_keyed_scalar_audit_expressions_not_108_atoms_or_nodes",
    "108_keyed_scalar_audit_expressions_not_108_independent_degrees_of_freedom",
    "git_commit_identity_not_established",
    "release_identity_not_established",
    "source_authenticity_not_established",
    "artifact_authenticity_not_established",
    "GO_is_lane_local_lexical_obligations_only_not_scientific_validation",
    "bounded_repeated_read_race_detection_not_atomic_snapshot_live_monitor_or_authenticity",
    "claimed_construct_outer_attributes_are_exactly_bounded",
    "module_level_inner_cfg_and_cfg_attr_are_rejected",
    "attribute_guard_is_conservative_lexical_not_full_Rust_parsing_or_cfg_evaluation",
]
TIMEOUT_SECONDS: Final[int] = 30


class Mutation(NamedTuple):
    label: str
    relative_path: Path
    transform: Callable[[str], str]
    expected_code: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_isolated_python() -> None:
    require(sys.implementation.name == "cpython", "PYTHON.implementation")
    require(sys.version_info >= (3, 11), "PYTHON.minimum_version")
    require(sys.flags.ignore_environment == 1, "PYTHON.ignore_environment")
    require(sys.flags.safe_path == 1, "PYTHON.safe_path")
    require(sys.flags.isolated == 1, "PYTHON.isolated")
    require(sys.flags.no_site == 1, "PYTHON.no_site")
    require(sys.flags.dont_write_bytecode == 1, "PYTHON.dont_write_bytecode")
    require(sys.flags.optimize in (0, 1), "PYTHON.optimize")


def contains_assert_statement(path: Path) -> bool:
    tree = ast.parse(
        path.read_text(encoding="utf-8", errors="strict"), filename=str(path)
    )
    return any(isinstance(node, ast.Assert) for node in ast.walk(tree))


def checked_checker_source_sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(digest == EXPECTED_CHECKER_SOURCE_SHA256, "checker source identity")
    return digest


def child_environment() -> dict[str, str]:
    return {
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
    }


def run_with_flags(
    checker: Path,
    repo_root: Path,
    interpreter_flags: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        *interpreter_flags,
        str(checker),
        "--repo-root",
        str(repo_root),
    ]
    return subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        env=child_environment(),
    )


def run(
    checker: Path, repo_root: Path, optimized: bool
) -> subprocess.CompletedProcess[str]:
    flags = ("-I", "-S", "-B", "-O") if optimized else ("-I", "-S", "-B")
    return run_with_flags(
        checker,
        repo_root,
        flags,
    )


def run_pair(
    checker: Path, repo_root: Path
) -> tuple[subprocess.CompletedProcess[str], ...]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        normal_future = executor.submit(run, checker, repo_root, False)
        optimized_future = executor.submit(run, checker, repo_root, True)
        return normal_future.result(), optimized_future.result()


def verify_nested_python_flag_controls(checker: Path, repo_root: Path) -> int:
    controls = (
        (
            "missing-ignore-environment",
            ("-P", "-S", "-B"),
            "PYTHON.ignore_environment",
        ),
        ("missing-safe-path", ("-E", "-S", "-B"), "PYTHON.safe_path"),
        ("missing-isolated", ("-E", "-P", "-S", "-B"), "PYTHON.isolated"),
        ("missing-no-site", ("-I", "-B"), "PYTHON.no_site"),
        (
            "missing-no-bytecode",
            ("-I", "-S"),
            "PYTHON.dont_write_bytecode",
        ),
        (
            "unsupported-optimize",
            ("-I", "-S", "-B", "-OO"),
            "PYTHON.optimize",
        ),
    )
    for label, flags, expected_code in controls:
        result = run_with_flags(checker, repo_root, flags)
        require(result.returncode == 1, f"{label}: exit {result.returncode}")
        require(result.stdout == "", f"{label}: unexpected stdout {result.stdout!r}")
        expected_stderr = f"SxPID3 P5 Rust source route: {expected_code}\n"
        require(
            result.stderr == expected_stderr,
            f"{label}: expected {expected_stderr!r}, found {result.stderr!r}",
        )
    return len(controls)


def verify_production_read_only_help_surface(checker: Path, repo_root: Path) -> int:
    source = checker.read_text(encoding="utf-8", errors="strict")
    require("--test-only-reread-handshake" not in source, "production test hook present")
    require("test_handshake_directory" not in source, "production handshake parameter present")
    tree = ast.parse(source, filename=str(checker))
    write_method_names = {
        "chmod",
        "mkdir",
        "rename",
        "rmdir",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
    require(
        not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in write_method_names
            for node in ast.walk(tree)
        ),
        "production filesystem write call present",
    )
    require(
        not any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any(alias.name == "time" for alias in node.names)
            for node in ast.walk(tree)
        ),
        "production time dependency present",
    )
    lane_count = 0
    for optimized in (False, True):
        flags = ("-I", "-S", "-B", "-O") if optimized else ("-I", "-S", "-B")
        result = subprocess.run(
            [sys.executable, *flags, str(checker), "--help"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=child_environment(),
        )
        mode = "optimized" if optimized else "normal"
        require(result.returncode == 0, f"production help/{mode}: exit")
        require(result.stderr == "", f"production help/{mode}: stderr")
        require("--repo-root" in result.stdout, f"production help/{mode}: repo root")
        require("test-only" not in result.stdout, f"production help/{mode}: test hook")
        require("handshake" not in result.stdout, f"production help/{mode}: handshake")
        lane_count += 1
    return lane_count


def replace_once(old: str, new: str, label: str) -> Callable[[str], str]:
    def transform(source: str) -> str:
        count = source.count(old)
        require(count == 1, f"{label}: mutation target count was {count}")
        return source.replace(old, new, 1)

    return transform


def changed_sha256(value: str) -> str:
    require(len(value) == 64, "changed SHA-256 input length")
    replacement = "0" if value[-1] != "0" else "1"
    return value[:-1] + replacement


def helper_span(source: str) -> tuple[int, int]:
    marker = "pub(crate) fn discrete_antichains_3() -> [[u8; 3]; 18] {"
    start = source.find(marker)
    require(start >= 0, "helper mutation marker missing")
    opening = source.find("{", start + len(marker) - 1)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError("helper mutation block unbalanced")


def helper_missing(source: str) -> str:
    start, end = helper_span(source)
    return source[:start] + source[end:]


def helper_duplicated(source: str) -> str:
    start, end = helper_span(source)
    block = source[start:end]
    return source[:end] + "\n\n" + block + source[end:]


def helper_reordered(source: str) -> str:
    start, end = helper_span(source)
    block = source[start:end]
    old = "        [0b100, 0, 0],\n        [0b011, 0, 0],"
    new = "        [0b011, 0, 0],\n        [0b100, 0, 0],"
    require(block.count(old) == 1, "helper reorder mutation target")
    return source[:start] + block.replace(old, new, 1) + source[end:]


def helper_nested_in_module(source: str) -> str:
    start, end = helper_span(source)
    block = source[start:end]
    nested = "mod p5_hidden_scope {\n" + block + "\n}\n"
    return source[:start] + nested + source[end:]


def replace_once_in_region(
    source: str,
    start_marker: str,
    end_marker: str,
    old: str,
    new: str,
    label: str,
) -> str:
    require(source.count(start_marker) == 1, f"{label}: start marker count")
    start = source.index(start_marker)
    end = source.find(end_marker, start)
    require(end >= 0, f"{label}: end marker missing")
    region = source[start:end]
    require(region.count(old) == 1, f"{label}: mutation target count")
    return source[:start] + region.replace(old, new, 1) + source[end:]


def replace_once_in_sxpid3_target(
    old: str, new: str, label: str
) -> Callable[[str], str]:
    def transform(source: str) -> str:
        return replace_once_in_region(
            source,
            "fn sxpid3_from_states_with_cancellation(",
            "\n// ----------------------------------------------------------------------------------------------",
            old,
            new,
            label,
        )

    return transform


def replace_once_in_mobius(
    old: str, new: str, label: str
) -> Callable[[str], str]:
    def transform(source: str) -> str:
        return replace_once_in_region(
            source,
            "pub(crate) fn discrete_mobius_inversion_3(",
            "\n/// Check if antichain a",
            old,
            new,
            label,
        )

    return transform


def call_moved_outside_target(source: str) -> str:
    call = "    let antichains = discrete_antichains_3();\n"
    require(source.count(call) == 1, "moved call target count")
    without_call = source.replace(call, "", 1)
    marker = "fn sxpid3_from_states_with_cancellation("
    require(without_call.count(marker) == 1, "moved call function marker count")
    moved = (
        "fn p5_moved_antichain_call() {\n"
        "    let _antichains = discrete_antichains_3();\n"
        "}\n\n"
    )
    return without_call.replace(marker, moved + marker, 1)


def mobius_moved_to_wrong_module(source: str) -> str:
    member = " discrete_mobius_inversion_3,"
    require(source.count(member) == 1, "mobius wrong-module member count")
    source = source.replace(member, "", 1)
    marker = "use crate::error::{PidError, PidResult};"
    require(source.count(marker) == 1, "mobius wrong-module insertion marker")
    moved = "use crate::wrong_pid_module::discrete_mobius_inversion_3;\n"
    return source.replace(marker, moved + marker, 1)


def primary_audit_key_changed(source: str) -> str:
    return replace_once_in_region(
        source,
        "EXPECTED_AUDIT_STABLE_KEYS: Final[tuple[str, ...]] = (",
        "EXPECTED_RUST_STABLE_KEYS: Final[tuple[str, ...]] = (",
        '    "03",\n',
        '    "08",\n',
        "primary-audit-key-changed",
    )


def prepend_module_inner_cfg(source: str) -> str:
    return "#![cfg(any())]\n" + source


def prepend_module_inner_cfg_attr(source: str) -> str:
    return "#![cfg_attr(all(), cfg(any()))]\n" + source


def prepend_module_inner_raw_cfg(source: str) -> str:
    return "#![r#cfg(any())]\n" + source


def prepend_module_inner_raw_cfg_attr(source: str) -> str:
    return "#![r#cfg_attr(all(), cfg(any()))]\n" + source


def mutations() -> tuple[Mutation, ...]:
    helper_hash = "757fc435ee5fd0c9ccaded24029c43cece3355863be37d0df5f21521ca9ebb07"
    manifest_hash = EXPECTED_MANIFEST_SHA256
    call = "    let antichains = discrete_antichains_3();\n"
    return (
        Mutation(
            "discrete-module-inner-cfg",
            DISCRETE_PID_RELATIVE,
            prepend_module_inner_cfg,
            "DISCRETE_PID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "discrete-module-inner-cfg-attr",
            DISCRETE_PID_RELATIVE,
            prepend_module_inner_cfg_attr,
            "DISCRETE_PID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "discrete-module-inner-raw-cfg",
            DISCRETE_PID_RELATIVE,
            prepend_module_inner_raw_cfg,
            "DISCRETE_PID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "discrete-module-inner-raw-cfg-attr",
            DISCRETE_PID_RELATIVE,
            prepend_module_inner_raw_cfg_attr,
            "DISCRETE_PID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "helper-attached-cfg",
            DISCRETE_PID_RELATIVE,
            replace_once(
                "pub(crate) fn discrete_antichains_3()",
                "#[cfg(any())]\npub(crate) fn discrete_antichains_3()",
                "helper-attached-cfg",
            ),
            "HELPER.attached_outer_attribute",
        ),
        Mutation(
            "helper-missing",
            DISCRETE_PID_RELATIVE,
            helper_missing,
            "HELPER.definition_count",
        ),
        Mutation(
            "helper-duplicated",
            DISCRETE_PID_RELATIVE,
            helper_duplicated,
            "HELPER.definition_count",
        ),
        Mutation(
            "helper-renamed",
            DISCRETE_PID_RELATIVE,
            replace_once(
                "pub(crate) fn discrete_antichains_3()",
                "pub(crate) fn discrete_antichains_3_renamed()",
                "helper-renamed",
            ),
            "HELPER.definition_count",
        ),
        Mutation(
            "helper-reordered",
            DISCRETE_PID_RELATIVE,
            helper_reordered,
            "HELPER.stable_keys",
        ),
        Mutation(
            "helper-nested-module",
            DISCRETE_PID_RELATIVE,
            helper_nested_in_module,
            "HELPER.module_scope",
        ),
        Mutation(
            "mobius-attached-cfg-multiline",
            DISCRETE_PID_RELATIVE,
            replace_once(
                "pub(crate) fn discrete_mobius_inversion_3(\n",
                "#[cfg(\n    any()\n)]\n"
                "pub(crate) fn discrete_mobius_inversion_3(\n",
                "mobius-attached-cfg-multiline",
            ),
            "MOBIUS.attached_outer_attribute",
        ),
        Mutation(
            "mobius-signature-input-type",
            DISCRETE_PID_RELATIVE,
            replace_once_in_mobius(
                "    redundancies: &[f64],\n",
                "    redundancies: &mut [f64],\n",
                "mobius-signature-input-type",
            ),
            "MOBIUS.signature",
        ),
        Mutation(
            "mobius-output-iterator-reversed",
            DISCRETE_PID_RELATIVE,
            replace_once_in_mobius(
                "    antichains\n        .iter()\n        .enumerate()\n",
                "    antichains\n        .iter()\n        .rev()\n        .enumerate()\n",
                "mobius-output-iterator-reversed",
            ),
            "MOBIUS.output_mapping",
        ),
        Mutation(
            "mobius-output-atoms-index-rotated",
            DISCRETE_PID_RELATIVE,
            replace_once_in_mobius(
                "                value: atoms[idx],\n",
                "                value: atoms[(idx + 1) % atoms.len()],\n",
                "mobius-output-atoms-index-rotated",
            ),
            "MOBIUS.output_mapping",
        ),
        Mutation(
            "mobius-atoms-reversed-before-output",
            DISCRETE_PID_RELATIVE,
            replace_once_in_mobius(
                "    }\n\n    antichains\n",
                "    }\n\n    atoms.reverse();\n\n    antichains\n",
                "mobius-atoms-reversed-before-output",
            ),
            "ROUTE.manifest_sha256",
        ),
        Mutation(
            "primary-checker-source-path",
            PRIMARY_CHECKER_RELATIVE,
            replace_once(
                "crates/pid-core/src/discrete_pid.rs",
                "crates/pid-core/src/sxpid.rs",
                "primary-checker-source-path",
            ),
            "PRIMARY_CHECKER.source_sha256",
        ),
        Mutation(
            "primary-checker-helper-hash",
            PRIMARY_CHECKER_RELATIVE,
            replace_once(
                helper_hash,
                helper_hash[:-1] + "6",
                "primary-checker-helper-hash",
            ),
            "PRIMARY_CHECKER.source_sha256",
        ),
        Mutation(
            "primary-audit-key-changed",
            PRIMARY_CHECKER_RELATIVE,
            primary_audit_key_changed,
            "PRIMARY_CHECKER.source_sha256",
        ),
        Mutation(
            "sxpid-module-inner-cfg",
            SXPID_RELATIVE,
            prepend_module_inner_cfg,
            "SXPID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "sxpid-module-inner-raw-cfg",
            SXPID_RELATIVE,
            prepend_module_inner_raw_cfg,
            "SXPID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "sxpid-module-inner-raw-cfg-attr",
            SXPID_RELATIVE,
            prepend_module_inner_raw_cfg_attr,
            "SXPID.module_inner_cfg_or_cfg_attr",
        ),
        Mutation(
            "import-attached-cfg",
            SXPID_RELATIVE,
            replace_once(
                "use crate::discrete_pid::{\n",
                "#[cfg(any())]\nuse crate::discrete_pid::{\n",
                "import-attached-cfg",
            ),
            "IMPORT.attached_outer_attribute",
        ),
        Mutation(
            "import-attached-cfg-attr-multiline",
            SXPID_RELATIVE,
            replace_once(
                "use crate::discrete_pid::{\n",
                "#[cfg_attr(\n    all(),\n    cfg(any())\n)]\n"
                "use crate::discrete_pid::{\n",
                "import-attached-cfg-attr-multiline",
            ),
            "IMPORT.attached_outer_attribute",
        ),
        Mutation(
            "import-deleted",
            SXPID_RELATIVE,
            replace_once(
                "    discrete_antichains_3, ",
                "    ",
                "import-deleted",
            ),
            "IMPORT.antichain_member",
        ),
        Mutation(
            "import-aliased",
            SXPID_RELATIVE,
            replace_once(
                "    discrete_antichains_3, ",
                "    discrete_antichains_3 as wrong_antichains, ",
                "import-aliased",
            ),
            "IMPORT.antichain_member",
        ),
        Mutation(
            "import-moved-module",
            SXPID_RELATIVE,
            replace_once(
                "use crate::discrete_pid::{",
                "use crate::wrong_pid_module::{",
                "import-moved-module",
            ),
            "IMPORT.route",
        ),
        Mutation(
            "mobius-import-deleted",
            SXPID_RELATIVE,
            replace_once(
                " discrete_mobius_inversion_3,",
                "",
                "mobius-import-deleted",
            ),
            "IMPORT.mobius_member",
        ),
        Mutation(
            "mobius-import-aliased",
            SXPID_RELATIVE,
            replace_once(
                " discrete_mobius_inversion_3,",
                " discrete_mobius_inversion_3 as wrong_mobius,",
                "mobius-import-aliased",
            ),
            "IMPORT.mobius_member",
        ),
        Mutation(
            "mobius-import-wrong-module",
            SXPID_RELATIVE,
            mobius_moved_to_wrong_module,
            "IMPORT.definition_count",
        ),
        Mutation(
            "target-function-attached-cfg-with-comment",
            SXPID_RELATIVE,
            replace_once(
                "fn sxpid3_from_states_with_cancellation(\n",
                "#[cfg(any())]\n"
                "// hostile comment between the attached attribute and item\n"
                "fn sxpid3_from_states_with_cancellation(\n",
                "target-function-attached-cfg-with-comment",
            ),
            "TARGET_FUNCTION.attached_outer_attribute",
        ),
        Mutation(
            "target-fixed-arity",
            SXPID_RELATIVE,
            replace_once(
                "source_states: [&[Vec<usize>]; 3],",
                "source_states: [&[Vec<usize>]; 4],",
                "target-fixed-arity",
            ),
            "TARGET_FUNCTION.signature",
        ),
        Mutation(
            "call-changed",
            SXPID_RELATIVE,
            replace_once(
                call,
                "    let antichains = discrete_antichains_3(3);\n",
                "call-changed",
            ),
            "CALL.shape",
        ),
        Mutation(
            "call-duplicated",
            SXPID_RELATIVE,
            replace_once(call, call + call, "call-duplicated"),
            "CALL.global_count",
        ),
        Mutation(
            "call-moved-outside-target",
            SXPID_RELATIVE,
            call_moved_outside_target,
            "CALL.function_scope",
        ),
        Mutation(
            "collection-projection",
            SXPID_RELATIVE,
            replace_once(
                ".filter(|&m| m != 0).collect()",
                ".filter(|&m| m == 0).collect()",
                "collection-projection",
            ),
            "COLLECTION.projection",
        ),
        Mutation(
            "node-collections-shadow-reversed",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "        .collect();\n\n    let vars = [s0_states, s1_states, s2_states, target_states];",
                "        .collect();\n"
                "    let node_collections: Vec<Vec<u8>> =\n"
                "        node_collections.into_iter().rev().collect();\n\n"
                "    let vars = [s0_states, s1_states, s2_states, target_states];",
                "node-collections-shadow-reversed",
            ),
            "ROUTE.manifest_sha256",
        ),
        Mutation(
            "cumulative-iterator-reversed",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "        for (idx, collections) in node_collections.iter().enumerate() {\n",
                "        for (idx, collections) in node_collections.iter().rev().enumerate() {\n",
                "cumulative-iterator-reversed",
            ),
            "CUMULATIVE.positional_route",
        ),
        Mutation(
            "cumulative-node-terms-collection-changed",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "node_terms_with_cancellation(&pmf, rlz, collections, n_sources, p_t, cancellation)?;",
                "node_terms_with_cancellation(&pmf, rlz, &node_collections[0], n_sources, p_t, cancellation)?;",
                "cumulative-node-terms-collection-changed",
            ),
            "CUMULATIVE.positional_route",
        ),
        Mutation(
            "cumulative-plus-index-rotated",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "            cum_plus[idx] = ip;\n",
                "            cum_plus[(idx + 1) % m] = ip;\n",
                "cumulative-plus-index-rotated",
            ),
            "CUMULATIVE.positional_route",
        ),
        Mutation(
            "cumulative-minus-index-rotated",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "            cum_minus[idx] = im;\n",
                "            cum_minus[(idx + 1) % m] = im;\n",
                "cumulative-minus-index-rotated",
            ),
            "CUMULATIVE.positional_route",
        ),
        Mutation(
            "positive-inversion-input",
            SXPID_RELATIVE,
            replace_once(
                "let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_plus);",
                "let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_minus);",
                "positive-inversion-input",
            ),
            "INVERSION.positive",
        ),
        Mutation(
            "negative-inversion-input",
            SXPID_RELATIVE,
            replace_once(
                "let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_minus);",
                "let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_plus);",
                "negative-inversion-input",
            ),
            "INVERSION.negative",
        ),
        Mutation(
            "pi-plus-shadow-reversed",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "        let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_plus);\n",
                "        let pi_plus = discrete_mobius_inversion_3(&antichains, &cum_plus);\n"
                "        let pi_plus: Vec<_> = pi_plus.into_iter().rev().collect();\n",
                "pi-plus-shadow-reversed",
            ),
            "ROUTE.manifest_sha256",
        ),
        Mutation(
            "inversion-call-duplicated",
            SXPID_RELATIVE,
            replace_once(
                "        let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_minus);\n",
                "        let pi_minus = discrete_mobius_inversion_3(&antichains, &cum_minus);\n"
                "        let _extra_pi = discrete_mobius_inversion_3(&antichains, &cum_minus);\n",
                "inversion-call-duplicated",
            ),
            "INVERSION.call_count",
        ),
        Mutation(
            "result-struct-attached-cfg-between-bound-attributes",
            SXPID_RELATIVE,
            replace_once(
                "#[derive(Debug, Serialize)]\n#[non_exhaustive]\n"
                "pub struct DiscreteSxPid3Result {",
                "#[derive(Debug, Serialize)]\n#[cfg(any())]\n#[non_exhaustive]\n"
                "pub struct DiscreteSxPid3Result {",
                "result-struct-attached-cfg-between-bound-attributes",
            ),
            "RESULT.attached_outer_attribute",
        ),
        Mutation(
            "result-struct-bound-attributes-reordered",
            SXPID_RELATIVE,
            replace_once(
                "#[derive(Debug, Serialize)]\n#[non_exhaustive]\n"
                "pub struct DiscreteSxPid3Result {",
                "#[non_exhaustive]\n#[derive(Debug, Serialize)]\n"
                "pub struct DiscreteSxPid3Result {",
                "result-struct-bound-attributes-reordered",
            ),
            "RESULT.attached_outer_attribute",
        ),
        Mutation(
            "result-struct-bound-attribute-substituted",
            SXPID_RELATIVE,
            replace_once(
                "#[derive(Debug, Serialize)]\n#[non_exhaustive]\n"
                "pub struct DiscreteSxPid3Result {",
                "#[derive(Debug, Serialize)]\n#[allow(dead_code)]\n"
                "pub struct DiscreteSxPid3Result {",
                "result-struct-bound-attribute-substituted",
            ),
            "RESULT.attached_outer_attribute",
        ),
        Mutation(
            "result-pointwise-index-order",
            SXPID_RELATIVE,
            replace_once(
                "SxPointwiseAtom::new(pi_plus[i].value, pi_minus[i].value)",
                "SxPointwiseAtom::new(pi_plus[m - 1 - i].value, pi_minus[i].value)",
                "result-pointwise-index-order",
            ),
            "RESULT.pointwise_index_order",
        ),
        Mutation(
            "result-averaged-vector-order",
            SXPID_RELATIVE,
            replace_once(
                "    for a in &avg {\n",
                "    for a in avg.iter().rev() {\n",
                "result-averaged-vector-order",
            ),
            "RESULT.averaged_vector_order",
        ),
        Mutation(
            "atoms-avg-reversed-before-constructor",
            SXPID_RELATIVE,
            replace_once_in_sxpid3_target(
                "\n    Ok(DiscreteSxPid3Result {\n",
                "\n    atoms_avg.reverse();\n\n    Ok(DiscreteSxPid3Result {\n",
                "atoms-avg-reversed-before-constructor",
            ),
            "ROUTE.manifest_sha256",
        ),
        Mutation(
            "output-antichain-projection",
            SXPID_RELATIVE,
            replace_once(
                "        antichains: node_collections,\n",
                "        antichains: Vec::new(),\n",
                "output-antichain-projection",
            ),
            "RESULT.antichain_projection",
        ),
        Mutation(
            "result-output-order",
            SXPID_RELATIVE,
            replace_once(
                "        antichains: node_collections,\n        atoms: atoms_avg,\n",
                "        atoms: atoms_avg,\n        antichains: node_collections,\n",
                "result-output-order",
            ),
            "RESULT.output_order",
        ),
        Mutation(
            "optimization-removable-assert",
            CHECKER_RELATIVE,
            replace_once(
                'FORMAT: Final[str] = "/pid-rs/sxpid3-p5-rust-source-route/v2"',
                'assert True\n\nFORMAT: Final[str] = "/pid-rs/sxpid3-p5-rust-source-route/v2"',
                "optimization-removable-assert",
            ),
            "CHECKER.assert_statement",
        ),
        Mutation(
            "route-manifest-anchor",
            CHECKER_RELATIVE,
            replace_once(
                manifest_hash,
                changed_sha256(manifest_hash),
                "route-manifest-anchor",
            ),
            "ROUTE.manifest_sha256",
        ),
    )


def seed_repository(destination: Path) -> None:
    for relative in (
        CHECKER_RELATIVE,
        PRIMARY_CHECKER_RELATIVE,
        DISCRETE_PID_RELATIVE,
        SXPID_RELATIVE,
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def verify_unstable_source_controls() -> tuple[int, int]:
    controls = (
        (DISCRETE_PID_RELATIVE, "DISCRETE_PID.unstable_source"),
        (SXPID_RELATIVE, "SXPID.unstable_source"),
    )
    wrapper_source = '''\
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def main() -> int:
    checker_path = Path(sys.argv[1]).resolve()
    repo_root = Path(sys.argv[2]).resolve()
    selected_path = (repo_root / sys.argv[3]).resolve()
    specification = importlib.util.spec_from_file_location(
        "pid_rs_p5_race_checker", checker_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("RACE.module_spec")
    checker = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(checker)
    checker.require_isolated_python()

    original_read_bytes = Path.read_bytes
    selected_read_count = 0

    def read_then_mutate(path: Path) -> bytes:
        nonlocal selected_read_count
        captured = original_read_bytes(path)
        if path.resolve() == selected_path:
            selected_read_count += 1
            if selected_read_count == 1:
                path.write_bytes(
                    captured + b"\\n// post-initial-read hostile mutation\\n"
                )
        return captured

    Path.read_bytes = read_then_mutate
    try:
        checker.build_result(repo_root, checker_path)
    finally:
        Path.read_bytes = original_read_bytes
    raise RuntimeError("RACE.post_initial_read_mutation_was_accepted")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, SyntaxError, UnicodeError, ValueError) as error:
        print(f"SxPID3 P5 Rust source route: {error}", file=sys.stderr)
        raise SystemExit(1)
'''
    process_count = 0
    for relative_path, expected_code in controls:
        for optimized in (False, True):
            with tempfile.TemporaryDirectory(
                prefix=f"pid-rs-p5v2-unstable-{relative_path.stem}-"
            ) as directory:
                temporary = Path(directory)
                seed_repository(temporary)
                wrapper = temporary / "post-initial-read-race-wrapper.py"
                wrapper.write_text(wrapper_source, encoding="utf-8")
                flags = (
                    ("-I", "-S", "-B", "-O")
                    if optimized
                    else ("-I", "-S", "-B")
                )
                command = [
                    sys.executable,
                    *flags,
                    str(wrapper),
                    str(temporary / CHECKER_RELATIVE),
                    str(temporary),
                    str(relative_path),
                ]
                process = subprocess.run(
                    command,
                    cwd=temporary,
                    check=False,
                    capture_output=True,
                    env=child_environment(),
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                )
                mode = "optimized" if optimized else "normal"
                require(
                    process.returncode == 1,
                    f"{relative_path}/{mode}: exit {process.returncode}",
                )
                require(
                    process.stdout == "",
                    f"{relative_path}/{mode}: stdout {process.stdout!r}",
                )
                expected_stderr = f"SxPID3 P5 Rust source route: {expected_code}\n"
                require(
                    process.stderr == expected_stderr,
                    f"{relative_path}/{mode}: expected {expected_stderr!r}, "
                    f"found {process.stderr!r}",
                )
                process_count += 1
    return len(controls), process_count


def verify_checker_source_comment_drift(
    baseline_stdout: str,
) -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-p5v2-source-comment-drift-") as directory:
        temporary = Path(directory)
        seed_repository(temporary)
        checker = temporary / CHECKER_RELATIVE
        source = checker.read_text(encoding="utf-8", errors="strict")
        old = "# Exact checker bytes are pinned by the companion self-test."
        new = "# Exact checker bytes are bound by the companion self-test."
        require(source.count(old) == 1, "source drift comment marker")
        checker.write_text(source.replace(old, new, 1), encoding="utf-8")
        normal, optimized = run_pair(checker, temporary)
        for mode, result in (("normal", normal), ("optimized", optimized)):
            require(result.returncode == 0, f"source drift/{mode}: exit")
            require(result.stderr == "", f"source drift/{mode}: stderr")
            require(
                result.stdout == baseline_stdout,
                f"source drift/{mode}: changed checker output",
            )
        try:
            checked_checker_source_sha256(checker)
        except RuntimeError as error:
            require(str(error) == "checker source identity", "source drift error code")
        else:
            raise RuntimeError("source drift was not rejected")
    return 1


def verify_failure(mutation: Mutation) -> None:
    with tempfile.TemporaryDirectory(
        prefix=f"pid-rs-p5v2-{mutation.label}-"
    ) as directory:
        temporary = Path(directory)
        seed_repository(temporary)
        target = temporary / mutation.relative_path
        original = target.read_text(encoding="utf-8", errors="strict")
        target.write_text(mutation.transform(original), encoding="utf-8")
        normal, optimized = run_pair(temporary / CHECKER_RELATIVE, temporary)
        expected_stderr = f"SxPID3 P5 Rust source route: {mutation.expected_code}\n"
        for mode, result in (("normal", normal), ("optimized", optimized)):
            require(
                result.returncode == 1,
                f"{mutation.label}/{mode}: exit {result.returncode}",
            )
            require(
                result.stdout == "",
                f"{mutation.label}/{mode}: unexpected stdout {result.stdout!r}",
            )
            require(
                result.stderr == expected_stderr,
                f"{mutation.label}/{mode}: expected {expected_stderr!r}, found {result.stderr!r}",
            )
        require(
            (normal.returncode, normal.stdout, normal.stderr)
            == (optimized.returncode, optimized.stdout, optimized.stderr),
            f"{mutation.label}: normal/-O failure mismatch",
        )


def main() -> int:
    require_isolated_python()
    checker = ROOT / CHECKER_RELATIVE
    checker_source_sha256 = checked_checker_source_sha256(checker)
    nested_flag_control_count = verify_nested_python_flag_controls(checker, ROOT)
    production_read_only_help_lane_count = verify_production_read_only_help_surface(
        checker, ROOT
    )
    normal, optimized = run_pair(checker, ROOT)
    require(
        normal.returncode == optimized.returncode == 0,
        normal.stderr + optimized.stderr,
    )
    require(normal.stderr == optimized.stderr == "", "baseline wrote stderr")
    require(normal.stdout == optimized.stdout, "baseline normal/-O output mismatch")
    stdout_sha256 = hashlib.sha256(normal.stdout.encode("utf-8")).hexdigest()
    require(stdout_sha256 == EXPECTED_STDOUT_SHA256, "baseline stdout identity")
    payload = json.loads(normal.stdout)
    require(payload["gate"] == "GO", "baseline gate")
    require(
        payload["route_manifest_sha256"] == EXPECTED_MANIFEST_SHA256,
        "baseline route manifest",
    )
    require(payload["boundaries"] == EXPECTED_BOUNDARIES, "baseline boundaries")
    require(
        payload["stable_rust_antichain_position_order"]["keys"]
        == EXPECTED_STABLE_KEYS,
        "baseline 18-key reconstruction",
    )
    require(
        payload["stable_rust_antichain_position_order"]["role"]
        == (
            "reconstructed_Rust_positional_order_connected_to_the_P5_audit_order_by_key_equality_not_lexicographic_identity"
        ),
        "baseline key-equality order bridge",
    )
    require(
        payload["audit_expression_context"]
        == {
            "expression_count": 108,
            "factorization": {
                "antichain_positions": 18,
                "components": ["informative", "misinformative", "net"],
                "representation_stage_count": 2,
                "representation_stages": ["cumulative_values", "mobius_atoms"],
            },
            "lexical_custody_role": (
                "binds_the_Rust_18_key_positional_carrier_to_the_P5_audit_registry_only_by_key_equality"
            ),
            "numeric_rust_expressions_compared": 0,
            "object_kind": "keyed_scalar_audit_expression",
            "prohibited_interpretations": [
                "108_lattice_nodes",
                "108_PID_atoms",
                "108_independent_degrees_of_freedom",
                "compiled_Rust_agreement",
                "binary64_refinement",
            ],
        },
        "baseline keyed scalar audit-expression context",
    )
    require(
        payload["scope"]
        == {
            "excluded": [
                "discrete_sxpid_n",
                "I_min_measure_estimator_and_lattice_semantics",
                "compiled_or_executed_Rust_behavior",
                "numeric_Rust_agreement",
                "binary64_refinement",
            ],
            "included_function": "sxpid3_from_states_with_cancellation",
            "included_result": "DiscreteSxPid3Result",
            "lexical_role": "antichain_key_carrier_and_positional_route",
            "source_count": 3,
        },
        "baseline scope",
    )
    require(
        payload["source_stability_scope"]
        == {
            "classification": "bounded_repeated_read_race_detection",
            "initial_capture": (
                "exact_source_bytes_decoded_and_used_for_all_lexical_checks"
            ),
            "pre_acceptance_check": (
                "one_sequential_end_of_build_exact_byte_reread_of_each_bound_source"
            ),
            "rust_paths": [str(DISCRETE_PID_RELATIVE), str(SXPID_RELATIVE)],
            "nonclaims": [
                "atomic_snapshot",
                "live_file_monitor",
                "source_authenticity",
                "artifact_authenticity",
                "commit_or_release_identity",
            ],
        },
        "baseline bounded repeated-read scope",
    )
    expected_anchor_ids = {
        "canonical_helper_call",
        "collection_projection",
        "cumulative_positional_route",
        "helper_definition",
        "import",
        "mobius_function_signature",
        "mobius_full_function_bytes",
        "mobius_import",
        "mobius_output_mapping",
        "primary_checker_full_source_bytes",
        "negative_inversion",
        "positive_inversion",
        "primary_checker_helper_hash_ast",
        "primary_checker_helper_route_ast",
        "primary_checker_path_ast",
        "result_averaged_vector_order",
        "result_declaration_order",
        "result_output_order",
        "result_pointwise_index_order",
        "target_function_signature",
        "target_full_function_bytes",
    }
    require(set(payload["anchors"]) == expected_anchor_ids, "baseline anchor registry")
    require(
        payload["anchors"]["primary_checker_full_source_bytes"]["sha256"]
        == EXPECTED_PRIMARY_CHECKER_SOURCE_SHA256,
        "baseline primary checker source identity",
    )
    require(
        payload["primary_checker_ast_binding"]["complete_source_sha256"]
        == EXPECTED_PRIMARY_CHECKER_SOURCE_SHA256,
        "baseline primary checker binding identity",
    )
    require(
        all(
            isinstance(anchor.get("role"), str)
            and anchor["role"]
            and re_full_sha256(anchor.get("sha256"))
            for anchor in payload["anchors"].values()
        ),
        "baseline role-separated anchor hashes",
    )
    require(not contains_assert_statement(checker), "checker contains assert statement")
    require(
        not contains_assert_statement(ROOT / SELF_RELATIVE),
        "self-test contains assert statement",
    )
    source_comment_drift_control_count = verify_checker_source_comment_drift(
        normal.stdout
    )
    unstable_source_control_count, unstable_source_process_count = (
        verify_unstable_source_controls()
    )

    hostile = mutations()
    for mutation in hostile:
        verify_failure(mutation)

    result = {
        "baseline_stdout_sha256": stdout_sha256,
        "checker_source_sha256": checker_source_sha256,
        "fail_closed_normal_and_optimized": True,
        "format": "/pid-rs/sxpid3-p5-rust-source-route-self-test/v2",
        "gate": "GO",
        "mutation_count": len(hostile),
        "nested_python_flag_control_count": nested_flag_control_count,
        "production_read_only_help_lane_count": production_read_only_help_lane_count,
        "route_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "source_comment_drift_control_count": source_comment_drift_control_count,
        "unstable_source_control_count": unstable_source_control_count,
        "unstable_source_process_count": unstable_source_process_count,
    }
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


def re_full_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        RuntimeError,
        SyntaxError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(f"SxPID3 P5 Rust source route self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
