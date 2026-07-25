#!/usr/bin/env python3
"""Fail-closed semantic and report-mutation suite for exact SxPID2 products."""

from __future__ import annotations

import copy
import importlib.util
import os
import subprocess
import sys
import types
from pathlib import Path
from typing import Any, Callable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

SOURCE = SCRIPT_DIR / "_exact_product.py"


def _run_certifier(input_raw: bytes) -> bytes:
    target = Path(
        os.environ.get(
            "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target/certified-sxpid")
        )
    )
    suffix = ".exe" if os.name == "nt" else ""
    binary = (target / "debug" / f"pid-certified-sxpid{suffix}").resolve()
    exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
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
            "certifier failed during exact-product self-test: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return bytes(completed.stdout)


def _reseal(certificate: dict[str, Any]) -> bytes:
    certificate["payload_sha256"] = exact.canonical_digest(certificate["payload"])
    return exact.canonical_json_bytes(certificate)


def _expect_rejection(name: str, action: Callable[[], Any]) -> None:
    try:
        action()
    except (RuntimeError, ValueError, ZeroDivisionError):
        return
    raise AssertionError(f"exact-product route accepted mutation {name!r}")


def _load_source(raw: bytes, name: str) -> Any:
    code = compile(raw, str(SOURCE), "exec", dont_inherit=True, optimize=0)
    module = types.ModuleType(name)
    module.__file__ = str(SOURCE)
    module.__loader__ = None
    module.__package__ = ""
    module.__spec__ = importlib.util.spec_from_loader(
        name, loader=None, origin=str(SOURCE)
    )
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _mutated_module(old: str, new: str, name: str) -> Any:
    source = SOURCE.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise AssertionError(
            f"semantic mutation {name!r} expected one source site, found {count}"
        )
    return _load_source(source.replace(old, new, 1).encode("utf-8"), name)


def _semantic_mutations(
    input_raw: bytes, certificate_raw: bytes, counts: list[int]
) -> int:
    mutations = (
        (
            "source_union_becomes_intersection",
            "event_matches = any(\n            _matches_collection(state, realization, mask) for mask in masks\n        )",
            "event_matches = all(\n            _matches_collection(state, realization, mask) for mask in masks\n        )",
        ),
        (
            "target_restriction_is_inverted",
            "target_restricted_match = state[2] == realization[2]",
            "target_restricted_match = state[2] != realization[2]",
        ),
        (
            "empirical_multiplicity_is_discarded",
            "return argument**row_count",
            "return argument**1",
        ),
        (
            "synergy_mobius_sign_is_flipped",
            "    (-1, -1, 1, 1),\n",
            "    (-1, -1, 1, -1),\n",
        ),
        (
            "local_net_uses_product_instead_of_quotient",
            "informative / misinformative == net,",
            "informative * misinformative == net,",
        ),
        (
            "exact_sign_comparator_is_reversed",
            "return (self.product > 1) - (self.product < 1)",
            "return (self.product < 1) - (self.product > 1)",
        ),
    )
    killed = 0
    for index, (name, old, new) in enumerate(mutations):
        mutant = _mutated_module(old, new, f"pid_exact_product_mutant_{index}")

        def action() -> None:
            derived = mutant.derive_products(counts)
            exact.verify_certificate(input_raw, certificate_raw, derived)

        _expect_rejection(name, action)
        killed += 1
    return killed


def _certificate_mutations(
    input_raw: bytes,
    certificate_raw: bytes,
    derived: exact.DerivedProducts,
) -> int:
    baseline = exact.parse_json(certificate_raw, "baseline certificate")
    exact.require(isinstance(baseline, dict), "baseline certificate is not an object")

    def mutate_and_reject(
        name: str, mutation: Callable[[dict[str, Any]], None]
    ) -> None:
        mutant = copy.deepcopy(baseline)
        mutation(mutant)
        _expect_rejection(
            name,
            lambda: exact.verify_certificate(input_raw, _reseal(mutant), derived),
        )

    def change_term(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_terms"]
        )
        argument = coordinate["exact_terms"][0]["log_argument"]
        argument["numerator"] = str(
            int(argument["numerator"]) + int(argument["denominator"])
        )

    def change_decision(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["interval"]["decision"] == "certified_negative"
        )
        coordinate["interval"]["decision"] = "certified_positive"

    def prevent_denominator_clearing(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_terms"]
        )
        coordinate["exact_terms"][0]["coefficient"] = {
            "numerator": "1",
            "denominator": "3",
        }

    def extreme_dyadic_exponent(certificate: dict[str, Any]) -> None:
        coordinate = certificate["payload"]["coordinates"][0]
        coordinate["interval"]["lower"] = {
            "significand": "1",
            "exponent2": 100_000,
        }

    def collapse_positive(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["interval"]["decision"] == "certified_positive"
        )
        coordinate["interval"]["lower"] = {"significand": "0", "exponent2": 0}
        coordinate["interval"]["upper"] = {"significand": "0", "exponent2": 0}
        coordinate["interval"]["decision"] = "certified_exact_zero"
        coordinate["interval"]["exact_zero_witness"] = (
            "canonical_exact_expression_has_no_terms"
        )

    def positive_interval_touches_zero_from_below(
        certificate: dict[str, Any],
    ) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_product"]["decision"] == "certified_positive"
        )
        coordinate["interval"]["lower"] = {
            "significand": "-1",
            "exponent2": -200,
        }
        coordinate["interval"]["upper"] = {"significand": "0", "exponent2": 0}
        coordinate["interval"]["decision"] = "unresolved_sign"
        coordinate["interval"]["exact_zero_witness"] = None

    def negative_interval_touches_zero_from_above(
        certificate: dict[str, Any],
    ) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_product"]["decision"] == "certified_negative"
        )
        coordinate["interval"]["lower"] = {"significand": "0", "exponent2": 0}
        coordinate["interval"]["upper"] = {
            "significand": "1",
            "exponent2": -200,
        }
        coordinate["interval"]["decision"] = "unresolved_sign"
        coordinate["interval"]["exact_zero_witness"] = None

    def duplicate_identity(certificate: dict[str, Any]) -> None:
        certificate["payload"]["coordinates"][1]["identity"] = copy.deepcopy(
            certificate["payload"]["coordinates"][0]["identity"]
        )

    def false_zero_witness(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["interval"]["decision"] == "certified_exact_zero"
        )
        coordinate["interval"]["exact_zero_witness"] = None

    def change_exact_product_decision(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_product"]["decision"] == "certified_negative"
        )
        coordinate["exact_product"]["decision"] = "certified_positive"

    def remove_exact_product_zero_witness(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_product"]["decision"] == "certified_exact_zero"
        )
        coordinate["exact_product"]["exact_zero_witness"] = None

    def forge_exact_product_preflight(certificate: dict[str, Any]) -> None:
        coordinate = next(
            item
            for item in certificate["payload"]["coordinates"]
            if item["exact_product"]["preflight"]["term_count"] > 0
        )
        coordinate["exact_product"]["preflight"][
            "projected_product_bits_upper_bound"
        ] = "1"

    mutations = (
        ("exact_log_term_argument", change_term),
        ("coefficient_does_not_clear_at_total", prevent_denominator_clearing),
        ("reported_sign_decision", change_decision),
        ("extreme_dyadic_exponent", extreme_dyadic_exponent),
        ("positive_interval_collapses_to_zero", collapse_positive),
        (
            "positive_product_interval_touches_zero_from_below",
            positive_interval_touches_zero_from_below,
        ),
        (
            "negative_product_interval_touches_zero_from_above",
            negative_interval_touches_zero_from_above,
        ),
        ("coordinate_identity_is_duplicated", duplicate_identity),
        ("exact_zero_witness_is_removed", false_zero_witness),
        ("exact_product_decision_is_reversed", change_exact_product_decision),
        ("exact_product_zero_witness_is_removed", remove_exact_product_zero_witness),
        ("exact_product_preflight_is_forged", forge_exact_product_preflight),
    )
    for name, mutation in mutations:
        mutate_and_reject(name, mutation)

    unsealed = copy.deepcopy(baseline)
    unsealed["payload"]["units"] = "bits"
    _expect_rejection(
        "payload_mutation_without_reseal",
        lambda: exact.verify_certificate(
            input_raw, exact.canonical_json_bytes(unsealed), derived
        ),
    )
    return len(mutations) + 1


def _structural_adversaries() -> int:
    adversaries = (
        ("zero_total", lambda: exact.derive_products([0] * 8)),
        ("negative_count", lambda: exact.derive_products([-1, 1, 0, 0, 0, 0, 0, 0])),
        (
            "duplicate_complete_state",
            lambda: exact.derive_products([1, 1], ((0, 0, 0), (0, 0, 0))),
        ),
        (
            "duplicate_json_key",
            lambda: exact.parse_json(b'{"a":1,"a":2}', "duplicate-key adversary"),
        ),
    )
    for name, action in adversaries:
        _expect_rejection(name, action)
    return len(adversaries)


def _preflight_before_powering_controls() -> int:
    """Prove the auxiliary verifier reaches both admission guards before powering."""

    controls = (
        (
            "per-expression-preflight",
            exact._product_plan_from_report_terms(
                [
                    {
                        "coefficient": {
                            "numerator": str(
                                exact.MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT + 1
                            ),
                            "denominator": "1",
                        },
                        "log_argument": {"numerator": "2", "denominator": "1"},
                    }
                ],
                1,
                "per-expression preflight control",
            ),
            True,
        ),
        (
            "aggregate-preflight",
            exact._product_plan_from_report_terms(
                [
                    {
                        "coefficient": {"numerator": "1", "denominator": "1"},
                        "log_argument": {"numerator": "2", "denominator": "1"},
                    }
                ],
                1,
                "aggregate preflight control",
            ),
            False,
        ),
    )
    original_signed_power = exact._signed_power
    power_calls = 0

    def forbidden_power(argument: Any, exponent: int) -> Any:
        del argument, exponent
        nonlocal power_calls
        power_calls += 1
        raise AssertionError("exact-product powering occurred before preflight admission")

    exact._signed_power = forbidden_power
    try:
        for name, plan, aggregate_admitted in controls:
            _expect_rejection(
                name,
                lambda plan=plan, aggregate_admitted=aggregate_admitted: (
                    exact._product_from_admitted_report_plan(
                        plan, aggregate_admitted
                    )
                ),
            )
    finally:
        exact._signed_power = original_signed_power
    exact.require(power_calls == 0, "a rejected plan reached exact-product powering")
    return len(controls)


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    # This three-row table has exact positive, negative, and zero coordinates, so every
    # certificate-decision branch is challenged.
    counts = [0, 0, 0, 2, 0, 1, 1, 0]
    try:
        input_raw = exact.canonical_input(counts)
        certificate_raw = _run_certifier(input_raw)
        derived = exact.derive_products(counts)
        exact.verify_certificate(input_raw, certificate_raw, derived)
        semantic = _semantic_mutations(input_raw, certificate_raw, counts)
        certificate = _certificate_mutations(input_raw, certificate_raw, derived)
        structural = _structural_adversaries()
        preflight_controls = _preflight_before_powering_controls()
        result = {
            "schema": "pid-rs/sxpid2-exact-product-mutation-suite/v1",
            "status": "passed",
            "semantic_source_mutations_killed": semantic,
            "certificate_mutations_killed": certificate,
            "structural_adversaries_rejected": structural,
            "preflight_before_powering_controls_passed": preflight_controls,
            "total_adversaries": semantic + certificate + structural,
            "qualification_table": counts,
            "seed_or_randomness": None,
            "bindings": {
                "exact_product_source_sha256": exact.sha256_file(SOURCE),
                "self_test_source_sha256": exact.sha256_file(Path(__file__).resolve()),
                "certifier_executable_sha256": exact.sha256_file(
                    Path(
                        os.environ.get(
                            "CARGO_TARGET_DIR",
                            str(REPOSITORY_ROOT / "target/certified-sxpid"),
                        )
                    )
                    / "debug"
                    / (
                        "pid-certified-sxpid.exe"
                        if os.name == "nt"
                        else "pid-certified-sxpid"
                    )
                ),
            },
        }
        sys.stdout.buffer.write(exact.canonical_json_bytes(result) + b"\n")
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        exact.ProductVerificationError,
        AssertionError,
    ) as error:
        print(f"exact-product self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
