#!/usr/bin/env python3
"""Fail closed on authoritative-arithmetic and semantic-kernel source drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


EXPECTED_SOURCE_FILES = (
    "digest.rs",
    "directed.rs",
    "error.rs",
    "evaluate.rs",
    "exact.rs",
    "extract.rs",
    "lattice2.rs",
    "lib.rs",
    "main.rs",
    "report.rs",
    "resource.rs",
    "schema.rs",
)
EXPECTED_ROOT_RUST_FILES = ("build.rs",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="certifier crate root (defaults to the parent of this script directory)",
    )
    return parser.parse_args()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    root = parse_args().root.resolve()
    src = root / "src"
    failures: list[str] = []
    source_text: dict[str, str] = {}
    actual_source_files = tuple(
        sorted(
            path.relative_to(src).as_posix()
            for path in src.rglob("*.rs")
            if path.is_file()
        )
    )
    require(
        actual_source_files == EXPECTED_SOURCE_FILES,
        "src: authoritative Rust source inventory changed; update and review the exact manifest",
        failures,
    )
    actual_root_rust_files = tuple(
        sorted(path.name for path in root.glob("*.rs") if path.is_file())
    )
    require(
        actual_root_rust_files == EXPECTED_ROOT_RUST_FILES,
        "crate root: Rust source inventory changed; an ordinary build-script module could bypass the exact manifest",
        failures,
    )
    for name in EXPECTED_SOURCE_FILES:
        path = src / name
        try:
            source_text[name] = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read required source {path}: {error}")

    if failures:
        return report(failures)

    directed = source_text["directed.rs"]
    try:
        build_source = (root / "build.rs").read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read required build script: {error}")
        build_source = ""
    all_source = "\n".join((*source_text.values(), build_source))
    for name, text in source_text.items():
        if name != "directed.rs":
            require(
                re.search(r"\bFloat\b", text) is None,
                f"{name}: raw Rug Float escaped the private directed-rounding module",
                failures,
            )
            require(
                re.search(r"\bRound\b", text) is None,
                f"{name}: Rug rounding mode escaped the private directed-rounding module",
                failures,
            )

    for forbidden in (
        "Float::with_val(",
        ".ln()",
        "set_prec(",
        "Round::Nearest",
        "Round::Zero",
        "Round::AwayZero",
        "to_f64(",
        "to_f32(",
    ):
        require(
            forbidden not in directed,
            f"directed.rs: forbidden authoritative arithmetic form {forbidden!r}",
            failures,
        )

    for fragment, count in (
        ("Float::with_val_round(", 4),
        (".ln_round(", 2),
        (".mul_assign_round(", 2),
        (".add_assign_round(", 2),
    ):
        require(
            directed.count(fragment) == count,
            f"directed.rs: expected exactly {count} occurrences of {fragment!r}",
            failures,
        )

    for fragment in (
        "(log_lower, log_upper)",
        "(log_upper, log_lower)",
        "left.lower.to_rational() - right.upper.to_rational()",
        "left.upper.to_rational() - right.lower.to_rational()",
        "else if self.lower.to_rational() > 0",
        "else if self.upper.to_rational() < 0",
        "if order == Ordering::Greater",
        "if order == Ordering::Less",
    ):
        require(
            fragment in directed,
            f"directed.rs: required interval-soundness fragment is absent: {fragment!r}",
            failures,
        )

    extract = source_text["extract.rs"]
    for fragment in (
        "if require_target && row.state.target != realization.target {\n            continue;\n        }",
        ".any(|mask| matches_collection(&row.state, realization, *mask))",
        "(mask & 0b01 == 0 || state.source_one == realization.source_one)",
        "(mask & 0b10 == 0 || state.source_two == realization.source_two)",
        "|| row_count > target_union",
        "|| target_union > union",
        "derived_net_argument /= &minus_argument",
        "if derived_net_argument != net_argument",
    ):
        require(
            fragment in extract,
            f"extract.rs: required event-semantic fragment is absent: {fragment!r}",
            failures,
        )

    lattice = source_text["lattice2.rs"]
    require(
        'const NODE_MASKS: [&[u8]; 4] = [&[0b01], &[0b10], &[0b11], &[0b01, 0b10]];'
        in lattice,
        "lattice2.rs: the pinned two-source event masks changed",
        failures,
    )
    require(
        "[[1, 0, 0, -1], [0, 1, 0, -1], [-1, -1, 1, 1], [0, 0, 0, 1]]"
        in lattice,
        "lattice2.rs: the pinned two-source Möbius matrix changed",
        failures,
    )
    require(
        "[[1, 0, 0, 1], [0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 1]]"
        in lattice,
        "lattice2.rs: the pinned two-source zeta matrix changed",
        failures,
    )

    require(
        re.search(r"\bunsafe\s*(?:\{|fn\b|impl\b|trait\b)", all_source) is None,
        "src: an unsafe block, function, implementation, or trait is forbidden",
        failures,
    )
    require(
        re.search(r"\binclude\s*!\s*\(", all_source) is None,
        "src: compile-time include! can introduce an unmanifested local source file",
        failures,
    )
    require(
        re.search(r"\binclude_str\s*!\s*\(", all_source) is None,
        "src: compile-time include_str! can introduce unmanifested semantic input",
        failures,
    )
    for name, text in (*source_text.items(), ("build.rs", build_source)):
        if name != "lib.rs":
            require(
                re.search(r"\binclude(?:_str|_bytes)?\b", text) is None,
                f"{name}: include macro identifiers are allowed only at pinned lib.rs evidence sites",
                failures,
            )
    require(
        re.search(r"#\s*\[[^\]]*\bpath\s*=", all_source) is None,
        "src: a path attribute can route a module to an unmanifested local source file",
        failures,
    )

    try:
        cargo = (root / "Cargo.toml").read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read Cargo.toml: {error}")
        cargo = ""
    try:
        cargo_document = tomllib.loads(cargo)
    except tomllib.TOMLDecodeError as error:
        failures.append(f"cannot parse Cargo.toml: {error}")
        cargo_document = {}
    dependencies = cargo_document.get("dependencies", {})
    require(
        isinstance(dependencies, dict),
        "Cargo.toml: dependencies must remain one ordinary table",
        failures,
    )
    if not isinstance(dependencies, dict):
        dependencies = {}
    require(
        'rug = { version = "=1.30.0", default-features = false, '
        'features = ["float", "rational", "std"] }' in cargo,
        "Cargo.toml: pinned Rug version/features changed",
        failures,
    )
    require(
        "gmp-mpfr-sys" not in dependencies,
        "Cargo.toml: direct gmp-mpfr-sys dependency would reopen command-line native-feature injection",
        failures,
    )
    require(
        "use-system-libs" not in cargo
        and "force-cross" not in cargo
        and "c-no-tests" not in cargo,
        "Cargo.toml: a forbidden native-library feature is present",
        failures,
    )
    require(
        'build = "build.rs"' in cargo,
        "Cargo.toml: the reviewed build script is not explicitly selected",
        failures,
    )
    require(
        "[lib]" not in cargo and "[[bin]]" not in cargo,
        "Cargo.toml: explicit library or binary target routing is outside the reviewed layout",
        failures,
    )

    metadata_command = [
        "cargo",
        "metadata",
        "--locked",
        "--offline",
        "--format-version",
        "1",
        "--manifest-path",
        str(root / "Cargo.toml"),
    ]
    try:
        metadata = subprocess.run(
            metadata_command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        failures.append(f"cannot execute locked Cargo metadata qualification: {error}")
        metadata = None
    if metadata is not None:
        require(
            metadata.returncode == 0,
            "Cargo metadata: default locked graph did not resolve offline",
            failures,
        )
        if metadata.returncode == 0:
            try:
                metadata_document = json.loads(metadata.stdout)
            except json.JSONDecodeError as error:
                failures.append(f"Cargo metadata: invalid JSON output: {error}")
            else:
                native_nodes = [
                    node
                    for node in metadata_document.get("resolve", {}).get("nodes", [])
                    if "gmp-mpfr-sys@1.7.1" in node.get("id", "")
                ]
                require(
                    len(native_nodes) == 1
                    and native_nodes[0].get("features") == ["mpfr"],
                    "Cargo metadata: default locked native-sys node must resolve exactly feature ['mpfr']",
                    failures,
                )

        feature_probe = subprocess.run(
            [
                *metadata_command,
                "--features",
                "gmp-mpfr-sys/use-system-libs",
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        require(
            feature_probe.returncode != 0
            and "gmp-mpfr-sys/use-system-libs" in feature_probe.stderr,
            "Cargo metadata: direct command-line native-sys feature injection did not fail closed",
            failures,
        )

    manifest = source_text["lib.rs"]
    for name in EXPECTED_SOURCE_FILES:
        require(
            f'("src/{name}", include_bytes!("{name}"))' in manifest,
            f"lib.rs: source manifest does not bind src/{name}",
            failures,
        )
    require(
        '("build.rs", include_bytes!("../build.rs"))' in manifest,
        "lib.rs: source manifest does not bind build.rs",
        failures,
    )
    for name in ("Cargo.lock", "Cargo.toml", "README.md"):
        require(
            f'("{name}", include_bytes!("../{name}"))' in manifest,
            f"lib.rs: source manifest does not bind {name}",
            failures,
        )
    source_manifest_block = manifest.split(
        "const SOURCE_MANIFEST: &[(&str, &[u8])] = &[", 1
    )
    require(
        len(source_manifest_block) == 2,
        "lib.rs: source manifest declaration changed",
        failures,
    )
    if len(source_manifest_block) == 2:
        source_manifest_entries = source_manifest_block[1].split("];", 1)[0]
    else:
        source_manifest_entries = ""
    require(
        source_manifest_entries.count("include_bytes!")
        == len(EXPECTED_SOURCE_FILES) + 4,
        "lib.rs: source manifest include count changed",
        failures,
    )
    require(
        'sha256_hex(include_bytes!("../Cargo.lock"))' in manifest,
        "lib.rs: independent Cargo.lock digest binding changed",
        failures,
    )
    require(
        manifest.count("include_bytes!") == len(EXPECTED_SOURCE_FILES) + 5,
        "lib.rs: include_bytes inventory changed outside the source manifest",
        failures,
    )
    require(
        manifest.count("include_bytes") == len(EXPECTED_SOURCE_FILES) + 5,
        "lib.rs: include_bytes identifier inventory changed",
        failures,
    )
    require(
        re.search(r"\binclude(?:_str)?\b", manifest) is None,
        "lib.rs: unreviewed include/include_str identifier is forbidden",
        failures,
    )
    require(
        "report::validate_resource_bounds(&extraction)?;" in manifest,
        "lib.rs: exact-expression resource preflight is not before evaluation",
        failures,
    )

    report_source = source_text["report.rs"]
    for fragment in (
        "manifest_requested_rug_features",
        "direct_gmp_mpfr_sys_dependency_status",
        "effective_dependency_feature_resolution_status",
        "compiled_native_version_constants_status",
        "effective_dependency_feature_resolution_rustc_wrappers",
    ):
        require(
            fragment in report_source,
            f"report.rs: dependency-feature trust boundary is absent: {fragment!r}",
            failures,
        )
    for forbidden in (
        "configured_rug_features",
        "configured_gmp_mpfr_sys_features",
        "compiled_gmp_version",
        "compiled_mpfr_version",
    ):
        require(
            forbidden not in report_source,
            f"report.rs: unbound native build evidence is misreported: {forbidden!r}",
            failures,
        )
    for fragment in (
        "let target_width_met = interval.width() <= policy.target_width;",
        "if !target_width_met {",
        "if terms > MAX_TERMS_PER_EXPRESSION",
        "if total_exact_terms > MAX_TOTAL_EXACT_TERMS",
        "> MAX_ESTIMATED_EXACT_TERM_JSON_BYTES",
        "if payload_bytes.len() > MAX_CANONICAL_PAYLOAD_BYTES",
    ):
        require(
            fragment in report_source,
            f"report.rs: required certificate resource bound is absent: {fragment!r}",
            failures,
        )

    exact_source = source_text["exact.rs"]
    require(
        "if self.terms.len() >= MAX_TERMS_PER_EXPRESSION" in exact_source,
        "exact.rs: per-expression growth is not bounded before insertion",
        failures,
    )
    require(
        "validate_cumulative_resource_growth(&cumulative)?;" in source_text["extract.rs"],
        "extract.rs: cumulative term growth is not bounded during extraction",
        failures,
    )
    require(
        "serde_json::to_writer_pretty" not in source_text["main.rs"],
        "main.rs: pretty output can bypass the compact certificate-output budget",
        failures,
    )

    if failures:
        return report(failures)
    print(
        "OK: certified-sxpid static policy applies representative drift guards to the directed "
        "arithmetic wrapper, two-source event semantics, lattice, source manifest, and native "
        "feature boundary"
    )
    return 0


def report(failures: list[str]) -> int:
    for failure in failures:
        print(f"static policy error: {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
