#!/usr/bin/env python3
"""Mutation tests for check-source-errata.py."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable


if sys.version_info < (3, 11):
    raise SystemExit("check-source-errata-self-test.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-source-errata.py"
REGISTRY = ROOT / "audit/source-errata.json"
SCHEMA = ROOT / "audit/schemas/source-errata.schema.json"
EXPECTED_MUTATION_COUNT = 17
MUTATION_COUNT = 0


def canonical_write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def run_checker(*arguments: str) -> subprocess.CompletedProcess[str]:
    optimization_flags = [] if __debug__ else ["-O"]
    return subprocess.run(
        [sys.executable, *optimization_flags, "-I", "-S", str(CHECKER), *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def expect_failure(
    directory: Path,
    name: str,
    base: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
    *,
    root: Path = ROOT,
) -> None:
    global MUTATION_COUNT
    candidate = copy.deepcopy(base)
    mutate(candidate)
    path = directory / f"{name}.json"
    canonical_write(path, candidate)
    process = run_checker(
        "--registry",
        str(path),
        "--schema",
        str(SCHEMA),
        "--root",
        str(root),
    )
    combined = process.stdout + process.stderr
    if process.returncode == 0 or expected not in combined:
        raise RuntimeError(
            f"{name}: expected failure containing {expected!r}, got "
            f"status {process.returncode}:\n{combined}"
        )
    MUTATION_COUNT += 1


def record(registry: dict[str, Any], record_id: str) -> dict[str, Any]:
    return next(item for item in registry["records"] if item["id"] == record_id)


def source(registry: dict[str, Any], source_id: str) -> dict[str, Any]:
    return next(item for item in registry["sources"] if item["source_id"] == source_id)


def main() -> int:
    global MUTATION_COUNT
    baseline = run_checker()
    if baseline.returncode != 0:
        raise RuntimeError(
            f"baseline checker failed:\n{baseline.stderr}{baseline.stdout}"
        )
    base = json.loads(REGISTRY.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pid-rs-source-errata-") as raw:
        directory = Path(raw)

        expect_failure(
            directory,
            "wrong-equation-14-units",
            base,
            lambda value: record(value, "ehrlich-v3-equation-14-units")[
                "proposed_resolution"
            ].update(
                {
                    "text": "Multiply the natural-log expression by ln(2) to report bits; pid-rs uses bits = nats * ln(2)."
                }
            ),
            "Equation (14) unit correction",
        )
        expect_failure(
            directory,
            "algorithm-6-omitted-antichain",
            base,
            lambda value: record(value, "ehrlich-v3-algorithm-6-wiring")[
                "proposed_resolution"
            ].update(
                {
                    "text": "Use compute_epsilons(S, T), compute_n_alpha(S, eps), and compute_n_T(T, eps)."
                }
            ),
            "omits antichain from epsilon routine",
        )
        expect_failure(
            directory,
            "algorithm-6-wrong-target-routine",
            base,
            lambda value: record(value, "ehrlich-v3-algorithm-6-wiring")[
                "proposed_resolution"
            ].update(
                {
                    "text": "Use compute_epsilons(S, T, antichain), compute_n_alpha(S, antichain, eps), and compute_n_alpha(T, antichain, eps)."
                }
            ),
            "uses wrong target routine",
        )
        expect_failure(
            directory,
            "fabricated-author-confirmation",
            base,
            lambda value: record(value, "ehrlich-v3-equation-8-overlap-factor")[
                "upstream_confirmation"
            ].update(
                {
                    "status": "author_confirmed_erratum",
                    "summary": "The authors confirmed it.",
                }
            ),
            "fabricates author/publisher confirmation",
        )
        expect_failure(
            directory,
            "missing-source-hash",
            base,
            lambda value: source(value, "ehrlich-arxiv-2311.06373v3")["retrieval"].pop(
                "sha256"
            ),
            "wrong keys",
        )
        expect_failure(
            directory,
            "wrong-source-hash",
            base,
            lambda value: source(value, "ehrlich-arxiv-2311.06373v3")[
                "retrieval"
            ].update({"sha256": "0" * 64}),
            "observed retrieval hash mismatch",
        )
        expect_failure(
            directory,
            "wrong-mgw-source-hash",
            base,
            lambda value: source(value, "mgw-arxiv-2002.03356v5")["retrieval"].update(
                {"sha256": "0" * 64}
            ),
            "observed retrieval hash mismatch",
        )
        expect_failure(
            directory,
            "missing-physical-locator",
            base,
            lambda value: record(value, "ehrlich-v3-equation-8-overlap-factor")[
                "locator"
            ].pop("physical_pdf_pages"),
            "wrong keys",
        )
        expect_failure(
            directory,
            "missing-test-binding",
            base,
            lambda value: record(value, "ehrlich-v3-equation-14-units").update(
                {"test_bindings": []}
            ),
            "exactly one scoped binding",
        )
        expect_failure(
            directory,
            "missing-test-marker",
            base,
            lambda value: record(value, "ehrlich-v3-equation-14-units")[
                "test_bindings"
            ][0].update({"marker": "missing source erratum marker"}),
            "binding marker mismatch",
        )
        expect_failure(
            directory,
            "ehrlich-to-mgw-construction-transfer",
            base,
            lambda value: record(value, "ehrlich-v3-equation-8-overlap-factor").update(
                {"construction_id": "mgw-categorical-shared-exclusions"}
            ),
            "construction transfer detected",
        )
        expect_failure(
            directory,
            "schick-to-ehrlich-construction-transfer",
            base,
            lambda value: record(
                value, "schick-poland-v2-discrete-recovery-normalization"
            ).update(
                {"construction_id": "ehrlich-analytical-continuous-shared-exclusions"}
            ),
            "construction transfer detected",
        )
        expect_failure(
            directory,
            "false-mgw-xor-synergy",
            base,
            lambda value: value["construction_firewall"][
                "mgw_uniform_binary_xor"
            ].update({"expected_synergy_nats": "1.58496 bits"}),
            "MGW XOR synergy must remain ln(4/3) nats, not 1.58496 bits",
        )
        expect_failure(
            directory,
            "overbroad-cantor-no-mod-null",
            base,
            lambda value: record(value, "schick-poland-v2-borel-isomorphism-density")[
                "proposed_resolution"
            ].update(
                {
                    "text": "A Cantor law proves no mod-null measure-space representation exists."
                }
            ),
            "overbroad Cantor/mod-null wording is forbidden",
        )
        expect_failure(
            directory,
            "source-obligation-promoted-to-erratum",
            base,
            lambda value: record(
                value, "schick-poland-v2-null-event-rcp-version"
            ).update({"issue_class": "source_erratum_candidate"}),
            "issue-class mismatch",
        )

        fixture_root = directory / "source-marker-fixture"
        binding_paths = {
            "crates/pid-core/src/isx.rs",
            "crates/pid-core/src/pid3.rs",
            "crates/pid-core/tests/isx.rs",
            "scripts/generate-sxpid2-exhaustive-oracle.py",
        }
        for relative in sorted(binding_paths):
            destination = fixture_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        marker_path = fixture_root / "crates/pid-core/tests/isx.rs"
        marker = "Source-erratum binding: ehrlich-v3-equation-14-units."
        marker_text = marker_path.read_text(encoding="utf-8")
        if marker_text.count(marker) != 1:
            raise RuntimeError("source-marker baseline is not unique")
        marker_path.write_text(
            marker_text.replace(marker, "removed marker", 1), encoding="utf-8"
        )
        expect_failure(
            directory,
            "bound-source-marker-removed",
            base,
            lambda _value: None,
            "test marker missing",
            root=fixture_root,
        )

        symlink_root = directory / "source-symlink-fixture"
        for relative in sorted(binding_paths):
            destination = symlink_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        symlink_path = symlink_root / "crates/pid-core/src/isx.rs"
        symlink_target = symlink_path.with_name("isx-target.rs")
        shutil.copyfile(symlink_path, symlink_target)
        symlink_path.unlink()
        symlink_path.symlink_to(symlink_target.name)
        expect_failure(
            directory,
            "bound-source-symlink",
            base,
            lambda _value: None,
            "test binding route contains a symbolic link",
            root=symlink_root,
        )

    if MUTATION_COUNT != EXPECTED_MUTATION_COUNT:
        raise RuntimeError(
            f"mutation accounting mismatch: {MUTATION_COUNT} != {EXPECTED_MUTATION_COUNT}"
        )
    print(
        "source-errata self-test: OK "
        f"({MUTATION_COUNT}/{EXPECTED_MUTATION_COUNT} mutations rejected)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
