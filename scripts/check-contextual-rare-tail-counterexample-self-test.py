#!/usr/bin/env python3
"""Causal hostile suite for the contextual rare-tail counterexample checker."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Final, NoReturn


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CHECKER: Final[Path] = ROOT / "scripts/check-contextual-rare-tail-counterexample.py"
EVIDENCE: Final[Path] = ROOT / "audit/evidence/contextual-rare-tail-counterexample-v1.json"


class SelfTestError(RuntimeError):
    """A hostile case did not fail closed."""


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def command(checker: Path, evidence: Path) -> list[str]:
    result = [sys.executable]
    if sys.flags.optimize:
        result.append("-O")
    result.extend(["-I", "-S", "-B", str(checker), "--evidence", str(evidence)])
    return result


def run(checker: Path, evidence: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command(checker, evidence),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "")},
    )


def require_rejected(label: str, checker: Path, evidence: Path) -> None:
    completed = run(checker, evidence)
    if completed.returncode == 0:
        fail(f"{label}: hostile case was accepted")
    if b"ERROR: contextual rare-tail counterexample rejected:" not in completed.stderr:
        fail(f"{label}: checker failed without its fail-closed marker")


def canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def mutate_value(
    baseline: dict[str, Any],
    label: str,
    mutation: Callable[[dict[str, Any]], None],
    directory: Path,
) -> None:
    value = copy.deepcopy(baseline)
    mutation(value)
    path = directory / f"{label}.json"
    path.write_bytes(canonical(value))
    require_rejected(label, CHECKER, path)


def mutate_source(
    source: str,
    old: str,
    new: str,
    label: str,
    directory: Path,
) -> None:
    if source.count(old) != 1:
        fail(f"{label}: expected one source anchor, found {source.count(old)}")
    root = directory / label
    scripts = root / "scripts"
    evidence_directory = root / "audit/evidence"
    scripts.mkdir(parents=True)
    evidence_directory.mkdir(parents=True)
    checker_path = scripts / CHECKER.name
    evidence_path = evidence_directory / EVIDENCE.name
    checker_path.write_text(source.replace(old, new), encoding="utf-8")
    evidence_path.write_bytes(EVIDENCE.read_bytes())
    require_rejected(label, checker_path, evidence_path)


def main() -> int:
    baseline_run = run(CHECKER, EVIDENCE)
    if baseline_run.returncode != 0:
        fail(f"baseline checker failed: {baseline_run.stderr.decode('utf-8', 'replace')}")
    baseline = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if not isinstance(baseline, dict):
        fail("baseline evidence is not an object")
    source = CHECKER.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="pid-rs-contextual-tail-self-test-") as temporary:
        directory = Path(temporary)
        evidence_mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
            ("q", lambda value: value["inputs"].__setitem__("q", "222494/250000")),
            ("source-cell", lambda value: value["inputs"].__setitem__("source_cell_mass", "222493/250001")),
            ("activation", lambda value: value["inputs"].__setitem__("modulatory_activation", "A_m=r+c")),
            (
                "interval",
                lambda value: value["proof"].__setitem__(
                    "modulatory_joint_cell_open_interval", ["3.18e-25", "3.19e-25"]
                ),
            ),
            ("term-count", lambda value: value["proof"].__setitem__("nested_exp_taylor_terms", 179)),
            ("interval-digest", lambda value: value["proof"].__setitem__("exact_interval_digest", "0" * 64)),
            ("rounding", lambda value: value["proof"].__setitem__("rounding_boundary", "tail is small")),
            (
                "runtime-zero",
                lambda value: value["runtime_observation"].__setitem__(
                    "binary64_modulatory_one_minus_p_x1", "positive"
                ),
            ),
            (
                "source-sha",
                lambda value: value["source_observations"].__setitem__(
                    "contextual_replication_generator_sha256", "0" * 64
                ),
            ),
            (
                "source-attribution-boundary",
                lambda value: value["source_observations"].__setitem__(
                    "attribution_boundary", "defect in Wibral PID"
                ),
            ),
            ("status", lambda value: value.__setitem__("status", "universal PID validation")),
            ("units", lambda value: value.__setitem__("units", "bits")),
            ("unknown-field", lambda value: value.__setitem__("confidence", 1.0)),
            ("missing-nonclaim", lambda value: value["claim"].pop("does_not_refute")),
        ]
        for label, mutation in evidence_mutations:
            mutate_value(baseline, label, mutation, directory)

        noncanonical = directory / "noncanonical.json"
        noncanonical.write_text(json.dumps(baseline), encoding="utf-8")
        require_rejected("noncanonical", CHECKER, noncanonical)

        duplicate = directory / "duplicate.json"
        raw = EVIDENCE.read_text(encoding="utf-8")
        duplicate.write_text(raw.replace('  "format":', '  "format": "duplicate",\n  "format":', 1), encoding="utf-8")
        require_rejected("duplicate-key", CHECKER, duplicate)

        symbolic = directory / "symbolic.json"
        symbolic.symlink_to(EVIDENCE)
        require_rejected("symbolic-link", CHECKER, symbolic)

        hard = directory / "hard.json"
        os.link(EVIDENCE, hard)
        try:
            require_rejected("hard-link", CHECKER, hard)
        finally:
            hard.unlink()

        source_mutations = [
            (
                "SOURCE_CELL_MASS: Final[Fraction] = Q / 2",
                "SOURCE_CELL_MASS: Final[Fraction] = (1 - Q) / 2",
                "source-law-weight",
            ),
            ("activation_lower = 1 + e4_lower", "activation_lower = 2 + e4_lower", "activation-lower"),
            ("activation_upper = 1 + e4_upper", "activation_upper = 2 + e4_upper", "activation-upper"),
            ("exp_activation_lower * e2_lower", "exp_activation_lower", "combined-factor-lower"),
            ("exp_activation_upper * e2_upper", "exp_activation_upper", "combined-factor-upper"),
            ("NESTED_EXP_TERMS: Final[int] = 180", "NESTED_EXP_TERMS: Final[int] = 60", "weak-tail-bound"),
            ("Fraction(1, 2**54)", "Fraction(1, 2**100)", "rounding-half-gap"),
        ]
        for old, new, label in source_mutations:
            mutate_source(source, old, new, label, directory)

    print("OK: contextual rare-tail checker rejected 25 evidence, custody, semantic, and proof mutations")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as error:
        print(f"ERROR: contextual rare-tail self-test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
