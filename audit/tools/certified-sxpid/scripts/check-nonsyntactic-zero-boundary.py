#!/usr/bin/env python3
"""Exhaust and regress exact product-one cancellations with nonempty log terms."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(SCRIPT_DIR))

import _exact_product as exact  # noqa: E402

EVIDENCE = (
    REPOSITORY_ROOT
    / "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json"
)
WITNESS = (0, 0, 1, 1, 1, 4, 1, 0)
WITNESS_IDENTITY = ("atom", "unique_one", "net")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
DYNAMIC_REPLAY_BINDINGS = frozenset(
    {
        "certifier_executable_sha256",
        "live_certificate_sha256",
    }
)
EXPECTED_BINDING_KEYS = frozenset(
    {
        "boundary_script_sha256",
        "certifier_executable_sha256",
        "exact_product_source_sha256",
        "live_certificate_sha256",
        "live_certificate_replay_projection_sha256",
        "live_input_sha256",
    }
)
EXPECTED_CERTIFICATE_KEYS = frozenset({"payload", "payload_sha256"})
EXPECTED_CERTIFICATE_TOOL_BINDING_KEYS = frozenset(
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
DYNAMIC_CERTIFICATE_TOOL_BINDINGS = frozenset(
    {
        "runtime_source_manifest_sha256",
    }
)
EXPECTED_CERTIFICATE_BUILD_CONTEXT_KEYS = frozenset(
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
DYNAMIC_CERTIFICATE_BUILD_CONTEXT_KEYS = frozenset(
    {
        "build_host",
        "build_target",
        "rustc_verbose_version",
    }
)

Expression = dict[Fraction, Fraction]


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-evidence",
        action="store_true",
        help=(
            "replace the committed historical execution receipt; ordinary qualification "
            "is read-only and compares its declared stable projection"
        ),
    )
    return parser.parse_args(argv)


def _evidence_projection(document: Any) -> dict[str, Any]:
    canonical = exact.parse_json(
        exact.canonical_json_bytes(document),
        "canonical boundary evidence projection",
    )
    exact.require(isinstance(canonical, dict), "boundary evidence is not an object")
    projection = copy.deepcopy(canonical)
    bindings = projection.get("bindings")
    exact.require(isinstance(bindings, dict), "boundary evidence bindings are absent")
    exact.require(
        set(bindings) == EXPECTED_BINDING_KEYS,
        "boundary evidence binding inventory changed",
    )
    for key, value in bindings.items():
        exact.require(
            isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None,
            f"boundary evidence binding {key!r} is not a SHA-256 digest",
        )
    for key in DYNAMIC_REPLAY_BINDINGS:
        del bindings[key]
    return projection


def _load_committed_evidence() -> dict[str, Any]:
    try:
        raw = EVIDENCE.read_bytes()
    except OSError as error:
        raise exact.ProductVerificationError(
            f"cannot read committed boundary evidence: {error}"
        ) from error
    document = exact.parse_json(raw, "committed boundary evidence")
    exact.require(
        raw == exact.canonical_json_bytes(document) + b"\n",
        "committed boundary evidence is not canonical JSON plus one LF",
    )
    exact.require(isinstance(document, dict), "committed boundary evidence is not an object")
    return document


def _certificate_replay_projection_digest(certificate: Any) -> str:
    canonical = exact.parse_json(
        exact.canonical_json_bytes(certificate),
        "canonical boundary certificate projection",
    )
    exact.require(isinstance(canonical, dict), "boundary certificate is not an object")
    exact.require(
        set(canonical) == EXPECTED_CERTIFICATE_KEYS,
        "boundary certificate outer inventory changed",
    )
    exact.require(
        isinstance(canonical["payload_sha256"], str)
        and SHA256_PATTERN.fullmatch(canonical["payload_sha256"]) is not None,
        "boundary certificate payload digest is not a SHA-256 digest",
    )
    payload = canonical.get("payload")
    exact.require(
        isinstance(payload, dict),
        "boundary certificate payload is not an object",
    )
    exact.require(
        canonical["payload_sha256"] == exact.canonical_digest(payload),
        "boundary certificate payload digest does not match its payload",
    )
    tool_binding = payload.get("tool_binding")
    exact.require(
        isinstance(tool_binding, dict),
        "boundary certificate tool binding is not an object",
    )
    exact.require(
        set(tool_binding) == EXPECTED_CERTIFICATE_TOOL_BINDING_KEYS,
        "boundary certificate tool-binding inventory changed",
    )
    runtime_source_manifest = tool_binding["runtime_source_manifest_sha256"]
    exact.require(
        isinstance(runtime_source_manifest, str)
        and SHA256_PATTERN.fullmatch(runtime_source_manifest) is not None,
        "boundary certificate runtime source-manifest binding is not a SHA-256 digest",
    )
    build_context = tool_binding["build_context"]
    exact.require(
        isinstance(build_context, dict),
        "boundary certificate build context is not an object",
    )
    exact.require(
        set(build_context) == EXPECTED_CERTIFICATE_BUILD_CONTEXT_KEYS,
        "boundary certificate build-context inventory changed",
    )
    for key, value in build_context.items():
        exact.require(
            isinstance(value, str) and bool(value),
            f"boundary certificate build-context field {key!r} is not nonempty text",
        )
    for key in DYNAMIC_CERTIFICATE_TOOL_BINDINGS:
        del tool_binding[key]
    for key in DYNAMIC_CERTIFICATE_BUILD_CONTEXT_KEYS:
        del build_context[key]
    return exact.canonical_digest(payload)


def _compositions(total: int, width: int) -> Iterator[tuple[int, ...]]:
    if width == 1:
        yield (total,)
        return
    for head in range(total + 1):
        for tail in _compositions(total - head, width - 1):
            yield (head, *tail)


def _add_term(expression: Expression, coefficient: Fraction, argument: Fraction) -> None:
    if coefficient == 0 or argument == 1:
        return
    combined = expression.get(argument, Fraction(0)) + coefficient
    if combined == 0:
        expression.pop(argument, None)
    else:
        expression[argument] = combined


def _linear_combination(
    expressions: Sequence[Mapping[Fraction, Fraction]], coefficients: Sequence[int]
) -> Expression:
    result: Expression = {}
    for expression, scale in zip(expressions, coefficients, strict=True):
        for argument, coefficient in expression.items():
            _add_term(result, coefficient * scale, argument)
    return result


def _derive_expressions(counts: Sequence[int]) -> dict[tuple[str, str, str], Expression]:
    total = sum(counts)
    cumulative = {
        component: [dict() for _ in exact.NODE_MASKS]
        for component in exact.COMPONENT_IDS
    }
    for realization, row_count in zip(exact.STATES, counts, strict=True):
        if row_count == 0:
            continue
        target_count = sum(
            count
            for state, count in zip(exact.STATES, counts, strict=True)
            if state[2] == realization[2]
        )
        weight = Fraction(row_count, total)
        for node_index, masks in enumerate(exact.NODE_MASKS):
            union_count = exact._event_count(  # noqa: SLF001 - independent audit script.
                exact.STATES, counts, realization, masks, require_target=False
            )
            target_union_count = exact._event_count(  # noqa: SLF001
                exact.STATES, counts, realization, masks, require_target=True
            )
            arguments = (
                Fraction(total, union_count),
                Fraction(target_count, target_union_count),
                Fraction(total * target_union_count, union_count * target_count),
            )
            for component, argument in zip(
                exact.COMPONENT_IDS, arguments, strict=True
            ):
                _add_term(cumulative[component][node_index], weight, argument)

    atoms = {
        component: [
            _linear_combination(cumulative[component], row) for row in exact.MOBIUS
        ]
        for component in exact.COMPONENT_IDS
    }
    result: dict[tuple[str, str, str], Expression] = {}
    for kind, identifiers, components in (
        ("cumulative", exact.NODE_IDS, cumulative),
        ("atom", exact.ATOM_IDS, atoms),
    ):
        for component in exact.COMPONENT_IDS:
            for identifier, expression in zip(
                identifiers, components[component], strict=True
            ):
                result[(kind, identifier, component)] = expression
    return result


def _binary() -> Path:
    target = Path(
        os.environ.get(
            "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target/certified-sxpid")
        )
    )
    suffix = ".exe" if os.name == "nt" else ""
    binary = (target / "debug" / f"pid-certified-sxpid{suffix}").resolve()
    exact.require(binary.is_file(), f"certifier executable is absent: {binary}")
    return binary


def _run_certifier(raw_input: bytes) -> tuple[bytes, Path]:
    binary = _binary()
    completed = subprocess.run(
        [str(binary), "-"],
        cwd=REPOSITORY_ROOT,
        input=raw_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    exact.require(
        completed.returncode == 0,
        "certifier rejected the minimized boundary witness: "
        + completed.stderr.decode("utf-8", errors="replace"),
    )
    return bytes(completed.stdout), binary


def _reseal(certificate: dict[str, Any]) -> bytes:
    certificate["payload_sha256"] = exact.canonical_digest(certificate["payload"])
    return exact.canonical_json_bytes(certificate)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(argv)
    cases: list[dict[str, Any]] = []
    tables_checked = 0
    coordinates_checked = 0
    counts_by_total: dict[str, int] = {}
    for total in range(1, 9):
        total_cases = 0
        for counts in _compositions(total, len(exact.STATES)):
            tables_checked += 1
            derived = exact.derive_products(counts)
            expressions = _derive_expressions(counts)
            by_identity = derived.by_identity()
            for identity, expression in expressions.items():
                coordinates_checked += 1
                if expression and by_identity[identity].product == 1:
                    total_cases += 1
                    cases.append(
                        {
                            "total": total,
                            "support_size": sum(count > 0 for count in counts),
                            "counts": list(counts),
                            "identity": list(identity),
                            "canonical_term_count": len(expression),
                        }
                    )
        counts_by_total[str(total)] = total_cases

    exact.require(
        all(counts_by_total[str(total)] == 0 for total in range(1, 8)),
        "a nonempty product-one expression appeared below total count eight",
    )
    exact.require(counts_by_total["8"] == 16, "n=8 boundary case count changed")
    exact.require(
        all(case["support_size"] == 5 for case in cases),
        "a boundary case has support size other than five",
    )
    exact.require(
        all(
            case["identity"][0] == "atom"
            and case["identity"][1] in ("unique_one", "unique_two")
            and case["identity"][2] == "net"
            for case in cases
        ),
        "a boundary case lies outside the two net unique atoms",
    )

    raw_input = exact.canonical_input(WITNESS)
    certificate_raw, binary = _run_certifier(raw_input)
    derived = exact.derive_products(WITNESS)
    exact.verify_certificate(raw_input, certificate_raw, derived)
    certificate = exact.parse_json(certificate_raw, "boundary certificate")
    coordinate = next(
        item
        for item in certificate["payload"]["coordinates"]
        if (
            item["identity"]["kind"],
            item["identity"]["node"],
            item["identity"]["component"],
        )
        == WITNESS_IDENTITY
    )
    exact.require(
        len(coordinate["exact_terms"]) == 5,
        "minimized witness no longer has five nonempty canonical terms",
    )
    exact.require(
        coordinate["interval"]["decision"] == "unresolved_sign"
        and coordinate["interval"]["exact_zero_witness"] is None,
        "interval-local boundary semantics changed",
    )
    exact.require(
        coordinate["exact_product"]["decision"] == "certified_exact_zero"
        and coordinate["exact_product"]["exact_zero_witness"]
        == "exact_multiplicative_product_equals_one",
        "exact-product boundary semantics changed",
    )

    mutant = copy.deepcopy(certificate)
    mutant_coordinate = next(
        item
        for item in mutant["payload"]["coordinates"]
        if item["identity"] == coordinate["identity"]
    )
    mutant_coordinate["exact_product"]["decision"] = "certified_positive"
    try:
        exact.verify_certificate(raw_input, _reseal(mutant), derived)
    except exact.ProductVerificationError:
        mutation_killed = True
    else:
        mutation_killed = False
    exact.require(mutation_killed, "false exact-product sign mutation survived")

    payload = {
        "schema": "pid-rs/sxpid2-nonsyntactic-exact-zero-boundary/v1",
        "status": "passed",
        "scope": {
            "alphabet": "binary source_one, source_two, and target",
            "totals_exhausted": [1, 2, 3, 4, 5, 6, 7, 8],
            "tables_checked": tables_checked,
            "coordinates_checked": coordinates_checked,
        },
        "findings": {
            "nonsyntactic_product_one_coordinates_by_total": counts_by_total,
            "n8_coordinate_count": len(cases),
            "all_n8_support_sizes": sorted({case["support_size"] for case in cases}),
            "all_n8_identities": sorted({tuple(case["identity"]) for case in cases}),
            "minimized_witness": {
                "counts": list(WITNESS),
                "identity": list(WITNESS_IDENTITY),
                "canonical_term_count": len(coordinate["exact_terms"]),
                "interval_decision": coordinate["interval"]["decision"],
                "exact_product_decision": coordinate["exact_product"]["decision"],
                "legacy_empty_term_only_classifier_would_certify_zero": not bool(
                    coordinate["exact_terms"]
                ),
            },
            "false_exact_product_sign_mutation_killed": mutation_killed,
        },
        "cases": cases,
        "bindings": {
            "certifier_executable_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "boundary_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "exact_product_source_sha256": hashlib.sha256(
                (SCRIPT_DIR / "_exact_product.py").read_bytes()
            ).hexdigest(),
            "live_input_sha256": hashlib.sha256(raw_input).hexdigest(),
            "live_certificate_sha256": hashlib.sha256(certificate_raw).hexdigest(),
            "live_certificate_replay_projection_sha256": (
                _certificate_replay_projection_digest(certificate)
            ),
        },
        "claim_boundary": (
            "Finite binary empirical arithmetic only. Minimality is relative to total count and "
            "support size in the exhausted binary table space; no population, scientific-axiom, "
            "higher-source, continuous-PID, or downstream-validity claim follows."
        ),
    }
    if arguments.update_evidence:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_bytes(exact.canonical_json_bytes(payload) + b"\n")
    else:
        committed = _load_committed_evidence()
        exact.require(
            _evidence_projection(payload) == _evidence_projection(committed),
            "live boundary result changed the committed declared stable evidence projection",
        )
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
