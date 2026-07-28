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
from typing import Any, Callable, Iterator, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

SOURCE = SCRIPT_DIR / "_exact_product.py"
BOUNDARY_SOURCE = SCRIPT_DIR / "check-nonsyntactic-zero-boundary.py"


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


def _load_boundary_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "pid_exact_product_boundary_projection_under_test",
        BOUNDARY_SOURCE,
    )
    exact.require(
        spec is not None and spec.loader is not None,
        "cannot construct the boundary-evidence projection module",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _boundary_evidence_projection_controls(certificate_raw: bytes) -> int:
    """Challenge the exact portability boundary of the historical receipt."""

    boundary = _load_boundary_module()
    expected_dynamic_bindings = frozenset(
        {
            "certifier_executable_sha256",
            "live_certificate_sha256",
        }
    )
    expected_binding_keys = frozenset(
        {
            "boundary_script_sha256",
            "certifier_executable_sha256",
            "exact_product_source_sha256",
            "live_certificate_replay_projection_sha256",
            "live_certificate_sha256",
            "live_input_sha256",
        }
    )
    expected_certificate_keys = frozenset({"payload", "payload_sha256"})
    expected_certificate_tool_binding_keys = frozenset(
        {
            "artifact_distribution_status",
            "build_context",
            "canonical_json_encoding",
            "cargo_lock_sha256",
            "executable_digest_status",
            "project_distribution_route",
            "runtime_source_manifest_sha256",
            "source_manifest_encoding",
        }
    )
    expected_dynamic_certificate_tool_bindings = frozenset(
        {
            "runtime_source_manifest_sha256",
        }
    )
    expected_certificate_build_context_keys = frozenset(
        {
            "build_host",
            "build_target",
            "cargo_profile_debug",
            "cargo_profile_name",
            "cargo_profile_optimization_level",
            "context_scope",
            "native_cache_policy",
            "rustc_verbose_version",
            "schema",
        }
    )
    expected_dynamic_certificate_build_context_keys = frozenset(
        {
            "build_host",
            "build_target",
            "rustc_verbose_version",
        }
    )
    exact.require(
        boundary.DYNAMIC_REPLAY_BINDINGS == expected_dynamic_bindings,
        "boundary dynamic replay-binding inventory drifted",
    )
    exact.require(
        boundary.EXPECTED_BINDING_KEYS == expected_binding_keys,
        "boundary complete replay-binding inventory drifted",
    )
    exact.require(
        boundary.EXPECTED_CERTIFICATE_KEYS == expected_certificate_keys,
        "boundary certificate outer inventory drifted",
    )
    exact.require(
        boundary.EXPECTED_CERTIFICATE_TOOL_BINDING_KEYS
        == expected_certificate_tool_binding_keys,
        "boundary certificate tool-binding inventory drifted",
    )
    exact.require(
        boundary.DYNAMIC_CERTIFICATE_TOOL_BINDINGS
        == expected_dynamic_certificate_tool_bindings,
        "boundary dynamic certificate-tool-binding inventory drifted",
    )
    exact.require(
        boundary.EXPECTED_CERTIFICATE_BUILD_CONTEXT_KEYS
        == expected_certificate_build_context_keys,
        "boundary certificate build-context inventory drifted",
    )
    exact.require(
        boundary.DYNAMIC_CERTIFICATE_BUILD_CONTEXT_KEYS
        == expected_dynamic_certificate_build_context_keys,
        "boundary dynamic certificate-build-context inventory drifted",
    )
    controls = 7

    committed = boundary._load_committed_evidence()  # noqa: SLF001
    baseline = boundary._evidence_projection(committed)  # noqa: SLF001

    for key in sorted(expected_dynamic_bindings):
        mutant = copy.deepcopy(committed)
        mutant["bindings"][key] = "f" * 64
        exact.require(
            boundary._evidence_projection(mutant) == baseline,  # noqa: SLF001
            f"declared dynamic boundary binding {key!r} entered the stable projection",
        )
        controls += 1

    stable_bindings = sorted(expected_binding_keys.difference(expected_dynamic_bindings))
    for key in stable_bindings:
        mutant = copy.deepcopy(committed)
        mutant["bindings"][key] = "f" * 64
        exact.require(
            boundary._evidence_projection(mutant) != baseline,  # noqa: SLF001
            f"stable boundary binding {key!r} escaped the projection",
        )
        controls += 1

    semantic_mutations: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
        ("schema", lambda value: value.update({"schema": value["schema"] + "-mutant"})),
        ("status", lambda value: value.update({"status": "mutated"})),
        ("scope", lambda value: value["scope"].update({"tables_checked": 0})),
        (
            "findings",
            lambda value: value["findings"].update({"n8_coordinate_count": 0}),
        ),
        ("cases", lambda value: value["cases"].clear()),
        (
            "claim_boundary",
            lambda value: value.update(
                {"claim_boundary": value["claim_boundary"] + " Mutated."}
            ),
        ),
    )
    for name, mutation in semantic_mutations:
        mutant = copy.deepcopy(committed)
        mutation(mutant)
        exact.require(
            boundary._evidence_projection(mutant) != baseline,  # noqa: SLF001
            f"boundary evidence field {name!r} escaped the stable projection",
        )
        controls += 1

    missing_binding = copy.deepcopy(committed)
    del missing_binding["bindings"]["live_input_sha256"]
    _expect_rejection(
        "boundary_projection_missing_binding",
        lambda: boundary._evidence_projection(missing_binding),  # noqa: SLF001
    )
    controls += 1

    extra_binding = copy.deepcopy(committed)
    extra_binding["bindings"]["unreviewed_sha256"] = "f" * 64
    _expect_rejection(
        "boundary_projection_extra_binding",
        lambda: boundary._evidence_projection(extra_binding),  # noqa: SLF001
    )
    controls += 1

    for key in ("live_input_sha256", "live_certificate_sha256"):
        malformed = copy.deepcopy(committed)
        malformed["bindings"][key] = "not-a-sha256"
        _expect_rejection(
            f"boundary_projection_malformed_{key}",
            lambda malformed=malformed: boundary._evidence_projection(  # noqa: SLF001
                malformed
            ),
        )
        controls += 1

    tuple_equivalent = copy.deepcopy(committed)
    tuple_equivalent["findings"]["all_n8_identities"] = [
        tuple(identity)
        for identity in tuple_equivalent["findings"]["all_n8_identities"]
    ]
    exact.require(
        boundary._evidence_projection(tuple_equivalent) == baseline,  # noqa: SLF001
        "JSON array/tuple normalization changed the boundary projection",
    )
    controls += 1

    certificate = exact.parse_json(certificate_raw, "boundary projection certificate")
    certificate_projection = boundary._certificate_replay_projection_digest(  # noqa: SLF001
        certificate
    )

    def reseal_projection_certificate(value: dict[str, Any]) -> None:
        value["payload_sha256"] = exact.canonical_digest(value["payload"])

    for key in sorted(expected_dynamic_certificate_tool_bindings):
        mutant = copy.deepcopy(certificate)
        mutant["payload"]["tool_binding"][key] = "f" * 64
        reseal_projection_certificate(mutant)
        exact.require(
            boundary._certificate_replay_projection_digest(mutant)  # noqa: SLF001
            == certificate_projection,
            f"dynamic certificate tool binding {key!r} entered the replay projection",
        )
        controls += 1

    for key in sorted(expected_dynamic_certificate_build_context_keys):
        mutant = copy.deepcopy(certificate)
        mutant["payload"]["tool_binding"]["build_context"][key] += "-mutant"
        reseal_projection_certificate(mutant)
        exact.require(
            boundary._certificate_replay_projection_digest(mutant)  # noqa: SLF001
            == certificate_projection,
            f"dynamic certificate build-context field {key!r} entered the replay projection",
        )
        controls += 1

    stable_tool_bindings = sorted(
        expected_certificate_tool_binding_keys.difference(
            expected_dynamic_certificate_tool_bindings.union({"build_context"})
        )
    )
    for key in stable_tool_bindings:
        mutant = copy.deepcopy(certificate)
        mutant["payload"]["tool_binding"][key] += "-mutant"
        reseal_projection_certificate(mutant)
        exact.require(
            boundary._certificate_replay_projection_digest(mutant)  # noqa: SLF001
            != certificate_projection,
            f"stable certificate tool binding {key!r} escaped the replay projection",
        )
        controls += 1

    stable_build_context_keys = sorted(
        expected_certificate_build_context_keys.difference(
            expected_dynamic_certificate_build_context_keys
        )
    )
    for key in stable_build_context_keys:
        mutant = copy.deepcopy(certificate)
        mutant["payload"]["tool_binding"]["build_context"][key] += "-mutant"
        reseal_projection_certificate(mutant)
        exact.require(
            boundary._certificate_replay_projection_digest(mutant)  # noqa: SLF001
            != certificate_projection,
            f"stable certificate build-context field {key!r} escaped the replay projection",
        )
        controls += 1

    report_mutant = copy.deepcopy(certificate)
    report_mutant["payload"]["cross_checks"]["all_passed"] = False
    reseal_projection_certificate(report_mutant)
    exact.require(
        boundary._certificate_replay_projection_digest(report_mutant)  # noqa: SLF001
        != certificate_projection,
        "certificate report content escaped the replay projection",
    )
    controls += 1

    missing_tool_binding = copy.deepcopy(certificate)
    del missing_tool_binding["payload"]["tool_binding"]
    reseal_projection_certificate(missing_tool_binding)
    _expect_rejection(
        "certificate_projection_missing_tool_binding",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            missing_tool_binding
        ),
    )
    controls += 1

    extra_tool_binding = copy.deepcopy(certificate)
    extra_tool_binding["payload"]["tool_binding"]["unreviewed"] = "value"
    reseal_projection_certificate(extra_tool_binding)
    _expect_rejection(
        "certificate_projection_extra_tool_binding",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            extra_tool_binding
        ),
    )
    controls += 1

    extra_outer_key = copy.deepcopy(certificate)
    extra_outer_key["unreviewed"] = "value"
    _expect_rejection(
        "certificate_projection_extra_outer_key",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            extra_outer_key
        ),
    )
    controls += 1

    malformed_payload_digest = copy.deepcopy(certificate)
    malformed_payload_digest["payload_sha256"] = "not-a-sha256"
    _expect_rejection(
        "certificate_projection_malformed_payload_digest",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            malformed_payload_digest
        ),
    )
    controls += 1

    wrong_payload_digest = copy.deepcopy(certificate)
    wrong_payload_digest["payload_sha256"] = "f" * 64
    _expect_rejection(
        "certificate_projection_wrong_payload_digest",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            wrong_payload_digest
        ),
    )
    controls += 1

    malformed_runtime_source_manifest = copy.deepcopy(certificate)
    malformed_runtime_source_manifest["payload"]["tool_binding"][
        "runtime_source_manifest_sha256"
    ] = "not-a-sha256"
    reseal_projection_certificate(malformed_runtime_source_manifest)
    _expect_rejection(
        "certificate_projection_malformed_runtime_source_manifest",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            malformed_runtime_source_manifest
        ),
    )
    controls += 1

    malformed_build_context = copy.deepcopy(certificate)
    malformed_build_context["payload"]["tool_binding"]["build_context"] = []
    reseal_projection_certificate(malformed_build_context)
    _expect_rejection(
        "certificate_projection_nonobject_build_context",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            malformed_build_context
        ),
    )
    controls += 1

    missing_build_context_field = copy.deepcopy(certificate)
    del missing_build_context_field["payload"]["tool_binding"]["build_context"][
        "build_host"
    ]
    reseal_projection_certificate(missing_build_context_field)
    _expect_rejection(
        "certificate_projection_missing_build_context_field",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            missing_build_context_field
        ),
    )
    controls += 1

    extra_build_context_field = copy.deepcopy(certificate)
    extra_build_context_field["payload"]["tool_binding"]["build_context"][
        "unreviewed"
    ] = "value"
    reseal_projection_certificate(extra_build_context_field)
    _expect_rejection(
        "certificate_projection_extra_build_context_field",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            extra_build_context_field
        ),
    )
    controls += 1

    empty_dynamic_build_context_field = copy.deepcopy(certificate)
    empty_dynamic_build_context_field["payload"]["tool_binding"]["build_context"][
        "build_target"
    ] = ""
    reseal_projection_certificate(empty_dynamic_build_context_field)
    _expect_rejection(
        "certificate_projection_empty_dynamic_build_context_field",
        lambda: boundary._certificate_replay_projection_digest(  # noqa: SLF001
            empty_dynamic_build_context_field
        ),
    )
    controls += 1

    exact.require(
        controls == 51,
        f"boundary-evidence projection control inventory drifted: {controls}",
    )
    return controls


JsonPath = tuple[str | int, ...]


def _scalar_leaf_paths(value: Any, prefix: JsonPath = ()) -> Iterator[JsonPath]:
    if isinstance(value, dict):
        for key in sorted(value):
            exact.require(isinstance(key, str), "JSON audit object key is not text")
            yield from _scalar_leaf_paths(value[key], (*prefix, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _scalar_leaf_paths(item, (*prefix, index))
    else:
        yield prefix


def _scalar_at(value: Any, path: JsonPath) -> Any:
    cursor = value
    for component in path:
        cursor = cursor[component]
    return cursor


def _replace_scalar(value: Any, path: JsonPath, replacement: Any) -> None:
    exact.require(bool(path), "cannot replace the root as a scalar leaf")
    cursor = value
    for component in path[:-1]:
        cursor = cursor[component]
    cursor[path[-1]] = replacement


def _alternate_json_scalar(value: Any) -> Any:
    if value is None:
        return "mutated-null"
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        if len(value) == 64 and all(character in "0123456789abcdef" for character in value):
            candidate = "f" * 64
            return "e" * 64 if value == candidate else candidate
        return value + "-mutant"
    raise AssertionError(f"unsupported JSON scalar type in leaf audit: {type(value)!r}")


def _exhaustive_projection_leaf_controls() -> tuple[int, int, int, int, int, int]:
    """Mutate every scalar leaf and recover exactly the declared 2+4 exclusions."""

    boundary = _load_boundary_module()
    committed = boundary._load_committed_evidence()  # noqa: SLF001
    evidence_projection = boundary._evidence_projection(committed)  # noqa: SLF001
    excluded_evidence_paths = {
        ("bindings", "certifier_executable_sha256"),
        ("bindings", "live_certificate_sha256"),
    }
    evidence_checked = 0
    evidence_excluded_equal = 0
    evidence_retained_changed = 0
    for path in _scalar_leaf_paths(committed):
        mutant = copy.deepcopy(committed)
        _replace_scalar(mutant, path, _alternate_json_scalar(_scalar_at(mutant, path)))
        projected = boundary._evidence_projection(mutant)  # noqa: SLF001
        evidence_checked += 1
        if path in excluded_evidence_paths:
            exact.require(
                projected == evidence_projection,
                f"declared outer exclusion changed the evidence projection: {path!r}",
            )
            evidence_excluded_equal += 1
        else:
            exact.require(
                projected != evidence_projection,
                f"retained outer scalar escaped the evidence projection: {path!r}",
            )
            evidence_retained_changed += 1

    boundary_input = exact.canonical_input(boundary.WITNESS)
    boundary_certificate_raw, _ = boundary._run_certifier(boundary_input)  # noqa: SLF001
    exact.verify_certificate(
        boundary_input,
        boundary_certificate_raw,
        exact.derive_products(boundary.WITNESS),
    )
    certificate = exact.parse_json(
        boundary_certificate_raw,
        "leaf-audit boundary certificate",
    )
    certificate_projection = boundary._certificate_replay_projection_digest(  # noqa: SLF001
        certificate
    )
    excluded_certificate_paths = {
        ("payload", "tool_binding", "runtime_source_manifest_sha256"),
        ("payload", "tool_binding", "build_context", "rustc_verbose_version"),
        ("payload", "tool_binding", "build_context", "build_host"),
        ("payload", "tool_binding", "build_context", "build_target"),
    }
    certificate_checked = 0
    certificate_excluded_equal = 0
    certificate_retained_changed = 0
    for payload_path in _scalar_leaf_paths(certificate["payload"]):
        path = ("payload", *payload_path)
        mutant = copy.deepcopy(certificate)
        _replace_scalar(mutant, path, _alternate_json_scalar(_scalar_at(mutant, path)))
        mutant["payload_sha256"] = exact.canonical_digest(mutant["payload"])
        projected = boundary._certificate_replay_projection_digest(  # noqa: SLF001
            mutant
        )
        certificate_checked += 1
        if path in excluded_certificate_paths:
            exact.require(
                projected == certificate_projection,
                f"declared certificate exclusion changed the replay projection: {path!r}",
            )
            certificate_excluded_equal += 1
        else:
            exact.require(
                projected != certificate_projection,
                f"retained certificate scalar escaped the replay projection: {path!r}",
            )
            certificate_retained_changed += 1

    exact.require(
        (
            evidence_checked,
            evidence_retained_changed,
            evidence_excluded_equal,
            certificate_checked,
            certificate_retained_changed,
            certificate_excluded_equal,
        )
        == (276, 274, 2, 960, 956, 4),
        "exhaustive replay-projection scalar-leaf partition drifted",
    )
    return (
        evidence_checked,
        evidence_retained_changed,
        evidence_excluded_equal,
        certificate_checked,
        certificate_retained_changed,
        certificate_excluded_equal,
    )


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
        boundary_projection_controls = _boundary_evidence_projection_controls(
            certificate_raw
        )
        (
            evidence_leaves,
            evidence_retained,
            evidence_excluded,
            certificate_leaves,
            certificate_retained,
            certificate_excluded,
        ) = _exhaustive_projection_leaf_controls()
        result = {
            "schema": "pid-rs/sxpid2-exact-product-mutation-suite/v1",
            "status": "passed",
            "semantic_source_mutations_killed": semantic,
            "certificate_mutations_killed": certificate,
            "structural_adversaries_rejected": structural,
            "preflight_before_powering_controls_passed": preflight_controls,
            "boundary_evidence_projection_controls_passed": (
                boundary_projection_controls
            ),
            "boundary_receipt_scalar_leaf_mutations_checked": evidence_leaves,
            "boundary_receipt_retained_leaf_changes_detected": evidence_retained,
            "boundary_receipt_declared_dynamic_leaf_invariances": evidence_excluded,
            "certificate_replay_scalar_leaf_mutations_checked": certificate_leaves,
            "certificate_replay_retained_leaf_changes_detected": certificate_retained,
            "certificate_replay_declared_variable_leaf_invariances": (
                certificate_excluded
            ),
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
