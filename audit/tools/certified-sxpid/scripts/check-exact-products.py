#!/usr/bin/env python3
"""Exhaustively bind exact log-products to all 494 live SxPID2 certificates."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
CERTIFIER_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

FIXTURE = (
    REPOSITORY_ROOT / "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json"
)
FIXTURE_SIDECAR = FIXTURE.with_suffix(FIXTURE.suffix + ".sha256")
GENERATOR = REPOSITORY_ROOT / "scripts/generate-sxpid2-exhaustive-oracle.py"
EXPECTED_FIXTURE_SHA256: Final = (
    "29c72afd551b446a5141ca54b25608386616d46572bf385bab94c9b56c14342d"
)
EXPECTED_GENERATOR_SHA256: Final = (
    "184404dddf0a1dac8caeecfb445036b2c73f02d303e2f88152dc17b485ea50cc"
)
EXPECTED_CASES: Final = 494


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--certifier",
        type=Path,
        help="prebuilt pid-certified-sxpid executable (default: repository target path)",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="do not build the default certifier executable first",
    )
    return parser.parse_args(argv)


def _default_binary() -> Path:
    target = Path(
        os.environ.get(
            "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target/certified-sxpid")
        )
    )
    suffix = ".exe" if os.name == "nt" else ""
    return target / "debug" / f"pid-certified-sxpid{suffix}"


def _build_default_binary() -> Path:
    binary = _default_binary()
    environment = dict(os.environ)
    environment["CARGO_TARGET_DIR"] = str(binary.parents[1])
    completed = subprocess.run(
        [
            "cargo",
            "build",
            "--quiet",
            "--locked",
            "--manifest-path",
            str(CERTIFIER_ROOT / "Cargo.toml"),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=600,
    )
    if completed.returncode != 0:
        raise exact.ProductVerificationError(
            "certifier build failed: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
    return binary


def _load_fixture() -> dict[str, Any]:
    raw = FIXTURE.read_bytes()
    exact.require(
        hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256,
        "exhaustive fixture digest drifted",
    )
    exact.require(
        FIXTURE_SIDECAR.read_text(encoding="utf-8").split()[0]
        == EXPECTED_FIXTURE_SHA256,
        "exhaustive fixture sidecar drifted",
    )
    exact.require(
        exact.sha256_file(GENERATOR) == EXPECTED_GENERATOR_SHA256,
        "exhaustive generator digest drifted",
    )
    fixture = exact.parse_json(raw, "exhaustive fixture")
    exact.require(isinstance(fixture, dict), "exhaustive fixture is not an object")
    exact.require(
        fixture.get("schema") == "pid-rs/sxpid2-exhaustive-oracle",
        "fixture schema mismatch",
    )
    exact.require(fixture.get("schema_revision") == 2, "fixture revision mismatch")
    bounds = fixture.get("bounds")
    exact.require(isinstance(bounds, dict), "fixture bounds are absent")
    exact.require(
        bounds.get("case_count") == EXPECTED_CASES, "fixture case bound mismatch"
    )
    exact.require(bounds.get("max_total_samples") == 4, "fixture sample bound mismatch")
    exact.require(
        tuple(tuple(state) for state in bounds.get("state_order", [])) == exact.STATES,
        "fixture state order mismatch",
    )
    cases = fixture.get("cases")
    exact.require(
        isinstance(cases, list) and len(cases) == EXPECTED_CASES,
        "fixture cases mismatch",
    )
    return fixture


def _run_certifier(binary: Path, input_raw: bytes) -> bytes:
    completed = subprocess.run(
        [str(binary), "-"],
        cwd=REPOSITORY_ROOT,
        input=input_raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise exact.ProductVerificationError(
            "live certifier rejected a bounded exhaustive table: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return bytes(completed.stdout)


def qualify(binary: Path) -> dict[str, Any]:
    fixture = _load_fixture()
    cases = fixture["cases"]
    totals = {
        "coordinates": 0,
        "event_constraints": 0,
        "local_net_identities": 0,
        "direct_mi_identities": 0,
        "component_net_identities": 0,
        "zeta_reconstructions": 0,
        "expression_products": 0,
        "exact_signs": 0,
        "exact_zeros": 0,
        "certified_positive": 0,
        "certified_negative": 0,
    }
    for case_index, case in enumerate(cases):
        exact.require(
            isinstance(case, dict), f"fixture case {case_index} is not an object"
        )
        counts = case.get("counts")
        exact.require(
            isinstance(counts, list), f"fixture case {case_index} counts are absent"
        )
        derived = exact.derive_products(counts)
        exact.require(
            derived.total == case.get("total_samples"),
            f"fixture case {case_index} total mismatch",
        )
        input_raw = exact.canonical_input(counts)
        certificate_raw = _run_certifier(binary, input_raw)
        checked = exact.verify_certificate(input_raw, certificate_raw, derived)
        totals["coordinates"] += len(derived.coordinates)
        totals["event_constraints"] += derived.checks.event_constraints
        totals["local_net_identities"] += derived.checks.local_net_identities
        totals["direct_mi_identities"] += derived.checks.direct_mi_identities
        totals["component_net_identities"] += derived.checks.component_net_identities
        totals["zeta_reconstructions"] += derived.checks.zeta_reconstructions
        totals["expression_products"] += checked.expression_products
        totals["exact_signs"] += checked.exact_signs
        totals["exact_zeros"] += checked.exact_zeros
        totals["certified_positive"] += checked.certified_positive
        totals["certified_negative"] += checked.certified_negative

    exact.require(
        totals["coordinates"] == EXPECTED_CASES * 24, "coordinate total changed"
    )
    exact.require(
        totals["expression_products"] == EXPECTED_CASES * 24, "product total changed"
    )
    exact.require(totals["exact_signs"] == EXPECTED_CASES * 24, "sign total changed")
    exact.require(totals["event_constraints"] == 5_280, "event-check total changed")
    exact.require(totals["local_net_identities"] == 5_280, "local-net total changed")
    exact.require(totals["direct_mi_identities"] == 1_482, "direct-MI total changed")
    exact.require(
        totals["component_net_identities"] == 3_952, "component-net total changed"
    )
    exact.require(totals["zeta_reconstructions"] == 5_928, "zeta total changed")
    exact.require(totals["exact_zeros"] == 5_886, "exact-zero total changed")
    exact.require(totals["certified_positive"] == 5_762, "positive-sign total changed")
    exact.require(totals["certified_negative"] == 208, "negative-sign total changed")
    exact.require(
        totals["exact_zeros"]
        + totals["certified_positive"]
        + totals["certified_negative"]
        == totals["coordinates"],
        "sign partition is incomplete",
    )
    return {
        "schema": "pid-rs/sxpid2-exact-product-qualification/v1",
        "status": "passed",
        "scope": {
            "alphabet": "binary source_one, source_two, and target",
            "maximum_total_samples": 4,
            "count_tables": EXPECTED_CASES,
            "coordinates_per_table": 24,
        },
        "checks": totals,
        "bindings": {
            "fixture_sha256": EXPECTED_FIXTURE_SHA256,
            "fixture_generator_sha256": EXPECTED_GENERATOR_SHA256,
            "exact_product_source_sha256": exact.sha256_file(
                SCRIPT_DIR / "_exact_product.py"
            ),
            "qualification_source_sha256": exact.sha256_file(Path(__file__).resolve()),
            "certifier_executable_sha256": exact.sha256_file(binary),
        },
        "claim_boundary": (
            "Bounded exact empirical arithmetic and live-certificate sign agreement only; "
            "not a population, estimator-calibration, higher-source, continuous-PID, data-"
            "provenance, or downstream-validity theorem."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(argv)
    try:
        if arguments.certifier is not None:
            binary = arguments.certifier.resolve()
            exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
        elif arguments.no_build:
            binary = _default_binary().resolve()
            exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
        else:
            binary = _build_default_binary().resolve()
        result = qualify(binary)
        sys.stdout.buffer.write(exact.canonical_json_bytes(result) + b"\n")
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        exact.ProductVerificationError,
    ) as error:
        print(f"exact-product qualification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
