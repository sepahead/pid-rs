#!/usr/bin/env python3
"""Mutation tests for the certified-SxPID2 claim revision checker."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
from typing import Any, Callable


if sys.version_info < (3, 11):
    raise SystemExit("check-certified-sxpid2-claim-self-test.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-certified-sxpid2-claim.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("pid_rs_certified_sxpid2_claim", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load certified-SxPID2 claim checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECK = load_checker()


def mutated_text(snapshot: Any, path: str, old: str, new: str) -> Any:
    text = dict(snapshot.text)
    if old not in text[path]:
        raise RuntimeError(f"self-test fixture token absent from {path}: {old!r}")
    text[path] = text[path].replace(old, new, 1)
    return CHECK.Snapshot(
        text=text,
        json_values=copy.deepcopy(snapshot.json_values),
        sha256=dict(snapshot.sha256),
    )


def mutated_json(snapshot: Any, path: str, mutate: Callable[[Any], None]) -> Any:
    values = copy.deepcopy(snapshot.json_values)
    mutate(values[path])
    return CHECK.Snapshot(
        text=dict(snapshot.text),
        json_values=values,
        sha256=dict(snapshot.sha256),
    )


def method(catalog: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in catalog["methods"] if item["id"] == CHECK.METHOD_ID)


def expect_failure(name: str, snapshot: Any, expected: str) -> None:
    try:
        CHECK.validate(snapshot)
    except CHECK.ClaimPacketError as error:
        if expected not in str(error):
            raise RuntimeError(f"{name}: wrong failure: {error}") from error
        return
    raise RuntimeError(f"{name}: mutation unexpectedly passed")


def main() -> int:
    baseline = CHECK.read_snapshot()
    CHECK.validate(baseline)
    mutations: list[tuple[str, Any, str]] = [
        (
            "producer-report-schema-downgrade",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/src/report.rs",
                CHECK.REPORT_SCHEMA,
                "pid-rs/certified-sxpid-report/v1",
            ),
            "report schema missing",
        ),
        (
            "verifier-schema-downgrade",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/verify_certificate.py",
                CHECK.VERIFICATION_SCHEMA,
                "pid-rs/certified-sxpid-independent-verification/v1",
            ),
            "verification schema missing",
        ),
        (
            "producer-manifest-omits-product",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/src/lib.rs",
                '("src/product.rs", include_bytes!("product.rs")),',
                "",
            ),
            "producer source manifest missing",
        ),
        (
            "erase-v1-readjudication-trigger",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md",
                "Revision 1 must be re-adjudicated",
                "Revision 1 may be reused",
            ),
            "historical trigger missing",
        ),
        (
            "broaden-v2-product-premise",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                "exact-product record has status `compared`",
                "exact-product record is present",
            ),
            "claim product premise missing",
        ),
        (
            "erase-v2-abstention",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                "no exact-product zero/sign claim is available",
                "a sign may be inferred",
            ),
            "claim abstention boundary missing",
        ),
        (
            "promote-lean-witness-to-end-to-end-refinement",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
                "the retained five-factor rational identity; exact-rational and Rust routes separately bind that",
                "Lean alone binds",
            ),
            "revision-2 formal non-refinement boundary missing",
        ),
        (
            "remove-product-source-from-catalog",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog)["source_files"].remove(
                    "audit/tools/certified-sxpid/src/product.rs"
                ),
            ),
            "catalog omits revision-2 source/evidence",
        ),
        (
            "invent-scientific-novelty",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {"scientific_novelty_claim": "new exact PID"}
                ),
            ),
            "acquired a scientific novelty claim",
        ),
        (
            "qualification-count-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value["checks"].update({"expression_products": 11_855}),
            ),
            "qualification product count drifted",
        ),
        (
            "mutation-subtotals-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update({"total_adversaries": 22}),
            ),
            "adversary count drifted",
        ),
        (
            "mutation-breakdown-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update({"certificate_mutations_killed": 10}),
            ),
            "certificate-mutation count drifted",
        ),
        (
            "preflight-before-powering-control-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"preflight_before_powering_controls_passed": 1}
                ),
            ),
            "preflight-before-powering control count drifted",
        ),
        (
            "qualification-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value["bindings"].update(
                    {"exact_product_source_sha256": "0" * 64}
                ),
            ),
            "qualification binding exact_product_source_sha256",
        ),
        (
            "mutation-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value["bindings"].update(
                    {"self_test_source_sha256": "0" * 64}
                ),
            ),
            "mutation evidence self-test source binding drifted",
        ),
        (
            "boundary-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value["bindings"].update(
                    {"boundary_script_sha256": "0" * 64}
                ),
            ),
            "boundary evidence script binding drifted",
        ),
        (
            "evolutionary-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value["bindings"].update(
                    {"challenge_source_sha256": "0" * 64}
                ),
            ),
            "evolutionary evidence script binding drifted",
        ),
        (
            "counterexample-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value["findings"]["minimized_witness"].update(
                    {"interval_decision": "certified_exact_zero"}
                ),
            ),
            "counterexample interval boundary drifted",
        ),
        (
            "lean-boundary-broadened",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update({"boundary": "Complete certifier verification."}),
            ),
            "Lean boundary broadened",
        ),
        (
            "lean-theorem-count-erased",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update({"theorems_kernel_checked": 6}),
            ),
            "Lean theorem count drifted",
        ),
        (
            "evolutionary-search-promoted-to-proof",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value.update({"negative_boundary": "Universal theorem."}),
            ),
            "evolutionary negative boundary broadened",
        ),
        (
            "just-gate-removed",
            mutated_text(
                baseline,
                "justfile",
                "python3 scripts/check-lean-exact-log-product.py",
                "true # removed",
            ),
            "revision-2 executable gate missing",
        ),
        (
            "ci-gate-removed",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
                "true # removed",
            ),
            "revision-2 executable gate missing",
        ),
        (
            "formal-paper-inventory-removed",
            mutated_text(
                baseline,
                "scripts/check-formal-pdf-set.sh",
                '"exact-log-product-sxpid2-assurance"',
                '"unregistered-exact-product-paper"',
            ),
            "formal PDF inventory missing",
        ),
    ]

    for name, snapshot, expected in mutations:
        expect_failure(name, snapshot, expected)
    print(f"OK: {len(mutations)} certified-SxPID2 revision mutations were rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
