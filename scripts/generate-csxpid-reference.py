#!/usr/bin/env python3
"""Regenerate the pinned external csxpid cross-validation fixture.

This script imports the authors' checkout directly, verifies its Git revision and the
scientific Python environment, generates deterministic samples with pid-rs's test RNG, and
writes the reference estimates plus their inputs as deterministic JSON. The resulting SHA-256
sidecar covers the complete machine-readable fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PINNED_REPOSITORY = "https://gitlab.gwdg.de/wibral/continuouspidestimator"
PINNED_COMMIT = "7bb984611a422cf7944ece68993fe3a27e2eadec"
PINNED_REQUIREMENTS_SHA256 = (
    "85535b45de1015c46b8eb2a74bd36c103b8b8233cf246fabb6a560eaac8b5284"
)
PINNED_PACKAGES = {
    "mpmath": "1.2.1",
    "numpy": "1.23.1",
    "scipy": "1.8.1",
    "setuptools": "63.2.0",
}
MASK_U64 = (1 << 64) - 1
LN_2 = float.fromhex("0x1.62e42fefa39efp-1")
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO_ROOT / "crates" / "pid-core" / "tests" / "fixtures" / "csxpid_reference.json"
)


class Rng64:
    """The xorshift64* generator used by crates/pid-core/tests/common/mod.rs."""

    def __init__(self, seed: int) -> None:
        self.state = seed

    def next_u64(self) -> int:
        value = self.state
        value ^= value >> 12
        value ^= (value << 25) & MASK_U64
        value ^= value >> 27
        self.state = value & MASK_U64
        return (self.state * 0x2545F4914F6CDD1D) & MASK_U64

    def next_f64(self) -> float:
        return (self.next_u64() >> 11) * (1.0 / float(1 << 53))


def git_output(checkout: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def git_bytes(checkout: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *args],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def verify_checkout(checkout: Path) -> None:
    actual_commit = git_output(checkout, "rev-parse", "HEAD")
    if actual_commit != PINNED_COMMIT:
        raise SystemExit(
            f"csxpid checkout is {actual_commit}; expected pinned commit {PINNED_COMMIT}"
        )
    if git_output(checkout, "status", "--short"):
        raise SystemExit("csxpid checkout must be clean")
    requirements = git_bytes(checkout, "show", f"{PINNED_COMMIT}:requirements.txt")
    actual_hash = hashlib.sha256(requirements).hexdigest()
    if actual_hash != PINNED_REQUIREMENTS_SHA256:
        raise SystemExit(
            f"requirements.txt SHA-256 is {actual_hash}; expected {PINNED_REQUIREMENTS_SHA256}"
        )


def verify_environment() -> None:
    actual_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    if actual_python != "3.10":
        raise SystemExit(f"Python {actual_python} is active; the reference requires Python 3.10")
    for package, expected in PINNED_PACKAGES.items():
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise SystemExit(f"{package}=={actual} is active; expected {package}=={expected}")


def bivariate_rows() -> list[list[float]]:
    rng = Rng64(987_654_321)
    rows = []
    for _ in range(80):
        base = rng.next_f64()
        source_2 = base + 0.5 * rng.next_f64()
        target = base + 0.25 * rng.next_f64()
        rows.append([base, source_2, target])
    return rows


def trivariate_rows() -> list[list[float]]:
    rng = Rng64(13_579)
    rows = []
    for _ in range(80):
        base = rng.next_f64()
        source_1 = base + 0.5 * rng.next_f64()
        source_2 = base + 0.25 * rng.next_f64()
        target = base + 0.125 * rng.next_f64()
        rows.append([base, source_1, source_2, target])
    return rows


def encode_antichain(antichain: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(source_set) for source_set in antichain]


def make_reference(checkout: Path) -> dict[str, Any]:
    sys.path.insert(0, str(checkout))

    import numpy as np

    from csxpid.estimator import PurelyContinuousSxPIDEstimator
    from csxpid.neighbors import SciPyKDTreesKNNFinder
    from csxpid.random_variable import ContinuousSpace, RandomVariable

    random_variable = RandomVariable(measurable_space=ContinuousSpace(dimension=1))

    rows_2 = bivariate_rows()
    data_2 = np.asarray(rows_2, dtype=np.float64)
    estimator_2 = PurelyContinuousSxPIDEstimator(
        S_rvs=[random_variable] * 2,
        T_rv=random_variable,
        knn_finder_class=SciPyKDTreesKNNFinder,
        k=3,
        noise_stddev=0,
        transformation=None,
    )
    redundancy_bits = estimator_2.estimate_redundancy(
        S=data_2[:, :2],
        T=data_2[:, 2:],
        antichain=((0,), (1,)),
        transform_variables=False,
    )

    rows_3 = trivariate_rows()
    data_3 = np.asarray(rows_3, dtype=np.float64)
    estimator_3 = PurelyContinuousSxPIDEstimator(
        S_rvs=[random_variable] * 3,
        T_rv=random_variable,
        knn_finder_class=SciPyKDTreesKNNFinder,
        k=3,
        noise_stddev=0,
        transformation=None,
    )
    atoms_bits = estimator_3.estimate(
        S=data_3[:, :3],
        T=data_3[:, 3:],
        transform_variables=False,
    )

    return {
        "provenance": {
            "schema": "pid-rs.csxpid-reference.v1",
            "generated_by": "scripts/generate-csxpid-reference.py",
            "paper": {
                "title": "Partial Information Decomposition for Continuous Variables based on Shared Exclusions: Analytical Formulation and Estimation",
                "doi": "10.1103/PhysRevE.110.014115",
                "arxiv": "2311.06373v3",
            },
            "upstream": {
                "repository": PINNED_REPOSITORY,
                "commit": PINNED_COMMIT,
                "requirements_sha256": PINNED_REQUIREMENTS_SHA256,
            },
            "environment": {
                "python": "3.10",
                "packages": PINNED_PACKAGES,
            },
            "estimator": {
                "class": "csxpid.estimator.PurelyContinuousSxPIDEstimator",
                "neighbor_backend": "csxpid.neighbors.SciPyKDTreesKNNFinder",
                "k": 3,
                "noise_stddev": 0,
                "transformation": None,
                "source_metric": "one-dimensional L-infinity",
                "target_metric": "one-dimensional L-infinity",
                "upstream_output_unit": "bits",
                "pid_rs_output_unit": "nats",
                "conversion": "nats = bits * ln(2)",
            },
            "fixture_generator": {
                "algorithm": "xorshift64*; 53-bit uniform f64 values",
                "rust_source": "crates/pid-core/tests/common/mod.rs",
            },
        },
        "cases": {
            "bivariate": {
                "seed": 987_654_321,
                "columns": ["s1", "s2", "target"],
                "rows": rows_2,
                "antichain": [[0], [1]],
                "redundancy_bits": float(redundancy_bits),
                "redundancy_nats": float(redundancy_bits) * LN_2,
            },
            "trivariate": {
                "seed": 13_579,
                "columns": ["s0", "s1", "s2", "target"],
                "rows": rows_3,
                "atoms": [
                    {
                        "antichain": encode_antichain(antichain),
                        "value_bits": float(value),
                        "value_nats": float(value) * LN_2,
                    }
                    for antichain, value in atoms_bits.items()
                ],
            },
        },
    }


def serialized_reference(reference: dict[str, Any]) -> bytes:
    return (json.dumps(reference, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def sidecar_path(output: Path) -> Path:
    return output.with_suffix(output.suffix + ".sha256")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csxpid-checkout",
        required=True,
        type=Path,
        help=f"clean checkout of {PINNED_REPOSITORY} at {PINNED_COMMIT}",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the tracked JSON and SHA-256 sidecar instead of rewriting them",
    )
    args = parser.parse_args()

    checkout = args.csxpid_checkout.resolve()
    verify_checkout(checkout)
    verify_environment()
    payload = serialized_reference(make_reference(checkout))
    digest = hashlib.sha256(payload).hexdigest()
    hash_line = f"{digest}  {args.output.name}\n".encode("ascii")

    if args.check:
        if args.output.read_bytes() != payload:
            raise SystemExit(f"{args.output} does not match the regenerated reference")
        if sidecar_path(args.output).read_bytes() != hash_line:
            raise SystemExit(f"{sidecar_path(args.output)} does not match the regenerated hash")
        print(f"verified {args.output} ({digest})")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    sidecar_path(args.output).write_bytes(hash_line)
    print(f"wrote {args.output} ({digest})")


if __name__ == "__main__":
    main()
