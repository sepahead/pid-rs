#!/usr/bin/env python3
"""Mutation tests for the certified-SxPID2 claim revision checker."""

from __future__ import annotations

import copy
import hashlib
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
    count = text[path].count(old)
    if count != 1:
        raise RuntimeError(
            f"self-test fixture token count in {path} is {count}, expected 1: {old!r}"
        )
    text[path] = text[path].replace(old, new, 1)
    raw_text_hashes = dict(snapshot.raw_text_sha256)
    raw_text_hashes[path] = hashlib.sha256(
        text[path].encode("utf-8")
    ).hexdigest()
    source_hashes = dict(snapshot.sha256)
    if path in source_hashes:
        source_hashes[path] = raw_text_hashes[path]
    return CHECK.Snapshot(
        text=text,
        json_values=copy.deepcopy(snapshot.json_values),
        sha256=source_hashes,
        raw_text_sha256=raw_text_hashes,
    )


def transformed_text(
    snapshot: Any, path: str, transform: Callable[[str], str]
) -> Any:
    text = dict(snapshot.text)
    text[path] = transform(text[path])
    raw_text_hashes = dict(snapshot.raw_text_sha256)
    raw_text_hashes[path] = hashlib.sha256(
        text[path].encode("utf-8")
    ).hexdigest()
    source_hashes = dict(snapshot.sha256)
    if path in source_hashes:
        source_hashes[path] = raw_text_hashes[path]
    return CHECK.Snapshot(
        text=text,
        json_values=copy.deepcopy(snapshot.json_values),
        sha256=source_hashes,
        raw_text_sha256=raw_text_hashes,
    )


def mutated_json(snapshot: Any, path: str, mutate: Callable[[Any], None]) -> Any:
    values = copy.deepcopy(snapshot.json_values)
    mutate(values[path])
    return CHECK.Snapshot(
        text=dict(snapshot.text),
        json_values=values,
        sha256=dict(snapshot.sha256),
        raw_text_sha256=dict(snapshot.raw_text_sha256),
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
            "downgrade-v3-claim-schema",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                CHECK.VERIFICATION_SCHEMA,
                CHECK.VERIFICATION_SCHEMA_V2,
            ),
            "revision-3 verification schema missing",
        ),
        (
            "erase-v3-cache-normalization-boundary",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                "not a portable semantic hash",
                "portable identity",
            ),
            "digest portability exclusion missing",
        ),
        (
            "erase-v3-cache-control",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_loaded_execution_cache_stability",
                "def check_loaded_execution_cache",
            ),
            "cache-stability control missing",
        ),
        (
            "erase-v3-live-code-control",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_post_import_execution_mutation",
                "def check_post_import_execution",
            ),
            "live-code mutation control missing",
        ),
        (
            "erase-v3-semantic-constant-controls",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_post_import_semantic_constant_mutations",
                "def check_post_import_constant_mutations",
            ),
            "semantic-constant mutation controls missing",
        ),
        (
            "erase-v3-normalization-source-mutant",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
                "def check_cache_normalization_source_mutation",
                "def check_cache_normalization_mutation",
            ),
            "cache-normalization source-mutation control missing",
        ),
        (
            "erase-v3-index-row",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
                "| 3 |",
                "| three |",
            ),
            "revision-3 index row missing",
        ),
        (
            "forge-v3-verifier-source-binding",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                baseline.sha256[
                    "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                ],
                "0" * 64,
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "swap-v3-source-digest-assignments",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ],
                    "__VERIFIER_DIGEST__",
                    1,
                )
                .replace(
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                    ],
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ],
                    1,
                )
                .replace(
                    "__VERIFIER_DIGEST__",
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                    ],
                    1,
                ),
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "move-v3-source-digest-from-row-to-prose",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ],
                    "0" * 64,
                    1,
                )
                + "\nRetained token: "
                + baseline.sha256[
                    "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                ]
                + "\n",
            ),
            "revision-3 verifier source digest table row differs",
        ),
        (
            "duplicate-v3-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    1,
                ),
            ),
            "revision-3 verifier source digest must have exactly one table row",
        ),
        (
            "hide-v3-source-binding-row-in-html-comment",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "<!--\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "-->"
                    ),
                    1,
                ),
            ),
            "HTML comments are forbidden in structured Markdown authority",
        ),
        (
            "hide-v3-source-binding-row-in-fenced-block",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "```text\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "```"
                    ),
                    1,
                ),
            ),
            "revision-3 verifier source digest must have exactly one table row",
        ),
        (
            "duplicate-v3-source-binding-without-outer-pipes",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text
                + "\n`audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                + "| `"
                + baseline.sha256[
                    "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                ]
                + "`\n",
            ),
            "noncanonical pipe-table row in structured Markdown authority",
        ),
        (
            "swap-incident-candidate-source-digests",
            transformed_text(
                baseline,
                CHECK.INCIDENT_PATH,
                lambda text: text.replace(
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ],
                    "__INCIDENT_VERIFIER_DIGEST__",
                    1,
                )
                .replace(
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                    ],
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/verify_certificate.py"
                    ],
                    1,
                )
                .replace(
                    "__INCIDENT_VERIFIER_DIGEST__",
                    baseline.sha256[
                        "audit/tools/certified-sxpid/scripts/check-independent-verifier.py"
                    ],
                    1,
                ),
            ),
            "incident candidate verifier digest table row differs",
        ),
        (
            "promote-portable-digest-to-supported",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
                (
                    "| Digests are portable semantic hashes across runtimes. "
                    "| No evidence; explicitly excluded | Unsupported "
                    "| Runtime implementation/version and marshal format can matter |"
                ),
                (
                    "| Digests are portable semantic hashes across runtimes. "
                    "| No evidence; explicitly excluded | Supported "
                    "| Runtime implementation/version and marshal format can matter |"
                ),
            ),
            "unsupported digest claim table row differs",
        ),
        (
            "duplicate-contradictory-portable-digest-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
                lambda text: text
                + "\n| Digests are portable semantic hashes across runtimes. "
                "| Claimed without evidence | Supported | Contradiction |\n",
            ),
            "unsupported digest claim must have exactly one table row",
        ),
        (
            "move-green-run-wording-under-supported",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    '- “the observed CI run was green”; or\n',
                    "",
                    1,
                ).replace(
                    "## Why the verifier revision is justified",
                    "The observed CI run was green.\n\n"
                    "## Why the verifier revision is justified",
                    1,
                ),
            ),
            "prohibited green-run wording missing",
        ),
        (
            "hide-supported-section-boundary-in-html-comment",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "<!--\n"
                        "## Why the verifier revision is justified\n"
                        "-->\n"
                        "The observed CI run was green.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "HTML comments are forbidden in structured Markdown authority",
        ),
        (
            "hide-supported-section-boundary-in-fenced-block",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "```text\n"
                        "## Why the verifier revision is justified\n"
                        "```\n"
                        "The observed CI run was green.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "prohibited green-run wording entered the supported section",
        ),
        (
            "duplicate-equivalent-supported-heading",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text
                + "\n## Supported wording ##\n"
                + "The observed CI run was green.\n",
            ),
            "expected one '## Supported wording' section",
        ),
        (
            "portable-hash-wording-entered-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text.replace(
                    "## Why the verifier revision is justified",
                    (
                        "The loaded-execution digest is a portable semantic hash.\n\n"
                        "## Why the verifier revision is justified"
                    ),
                    1,
                ),
            ),
            "prohibited wording entered the supported section",
        ),
        (
            "erase-retained-ci-runtime",
            mutated_text(
                baseline,
                CHECK.INCIDENT_PATH,
                "used CPython 3.11.15 on",
                "unspecified Python",
            ),
            "incident runtime missing",
        ),
        (
            "forge-retained-ci-log-digest",
            mutated_text(
                baseline,
                CHECK.INCIDENT_PATH,
                CHECK.INCIDENT_LOG_SHA256,
                "0" * 64,
            ),
            "incident retrieved-log digest missing",
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
            "catalog omits revision-3 source/evidence",
        ),
        (
            "remove-v3-incident-from-catalog",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog)["source_files"].remove(
                    CHECK.INCIDENT_PATH
                ),
            ),
            "catalog omits revision-3 source/evidence",
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
            "catalog-summary-universal-overclaim",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {
                        "summary": method(catalog)["summary"]
                        + " This universally proves all PID atoms nonnegative "
                        "and formally verifies pid-rs."
                    }
                ),
            ),
            "certifier catalog method exact reviewed projection changed",
        ),
        (
            "catalog-new-in-scientific-novelty-overclaim",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update(
                    {
                        "new_in_pid_rs": method(catalog)["new_in_pid_rs"]
                        + " This is a scientifically novel universal PID theorem."
                    }
                ),
            ),
            "certifier catalog method exact reviewed projection changed",
        ),
        (
            "catalog-method-nonfinite-json-number",
            mutated_json(
                baseline,
                "method-catalog.json",
                lambda catalog: method(catalog).update({"nonfinite": float("nan")}),
            ),
            "certifier catalog method cannot be canonically projected",
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
            "boundary-evidence-projection-control-erasure",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"boundary_evidence_projection_controls_passed": 50}
                ),
            ),
            "boundary-evidence projection control count drifted",
        ),
        (
            "boundary-receipt-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"boundary_receipt_scalar_leaf_mutations_checked": 275}
                ),
            ),
            "boundary-receipt scalar-leaf projection partition drifted",
        ),
        (
            "certificate-replay-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {"certificate_replay_retained_leaf_changes_detected": 955}
                ),
            ),
            "certificate-replay scalar-leaf projection partition drifted",
        ),
        (
            "boundary-replay-process-status-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value.update({"status": "failed"}),
            ),
            "boundary-replay process is not passed",
        ),
        (
            "boundary-replay-exhaustive-leaf-partition-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"][
                    "exhaustive_scalar_leaf_partition"
                ].update({"total_scalar_leaf_mutations_checked": 1_235}),
            ),
            "boundary-replay exhaustive scalar-leaf partition drifted",
        ),
        (
            "boundary-replay-process-source-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["bindings"].update(
                    {"boundary_script_sha256": "0" * 64}
                ),
            ),
            "boundary-replay process binding boundary_script_sha256",
        ),
        (
            "boundary-replay-complete-binding-inventory-erased",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"]["binding_inventory"].pop(),
            ),
            "boundary-replay complete binding inventory drifted",
        ),
        (
            "boundary-replay-outer-exclusion-broadened",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"]["dynamic_replay_bindings"].append(
                    "exact_product_source_sha256"
                ),
            ),
            "boundary-replay dynamic outer-binding inventory drifted",
        ),
        (
            "boundary-replay-inner-exclusion-erased",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"][
                    "certificate_projection_excluded_paths"
                ].pop(),
            ),
            "boundary-replay certificate exclusion inventory drifted",
        ),
        (
            "boundary-replay-ordinary-mode-made-writing",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"].update(
                    {"ordinary_mode": "write_tracked_evidence"}
                ),
            ),
            "boundary-replay ordinary mode drifted",
        ),
        (
            "boundary-replay-update-mode-made-implicit",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["verification"].update(
                    {"update_mode": "ordinary_execution"}
                ),
            ),
            "boundary-replay update mode drifted",
        ),
        (
            "boundary-replay-platform-boundary-overstated",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"].replace(
                            "No second operating system or architecture was executed",
                            "Every operating system and architecture was executed",
                        )
                    }
                ),
            ),
            "boundary-replay claim boundary omits",
        ),
        (
            "boundary-replay-platform-execution-lie",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"cross_platform_execution_performed": True}
                ),
            ),
            "boundary-replay platform-execution boundary drifted",
        ),
        (
            "boundary-replay-current-live-retention-overstated",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"current_live_receipt_retention": "full_external_custody"}
                ),
            ),
            "boundary-replay current-live retention boundary drifted",
        ),
        (
            "boundary-replay-historical-stdout-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["replay"].update(
                    {"historical_refresh_stdout_sha256": "0" * 64}
                ),
            ),
            "boundary-replay historical stdout/evidence binding drifted",
        ),
        (
            "boundary-replay-historical-certificate-binding-drift",
            mutated_json(
                baseline,
                "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
                lambda value: value["failure"].update(
                    {"historical_certificate_sha256": "0" * 64}
                ),
            ),
            "boundary-replay historical execution bindings drifted",
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
            "qualification-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-qualification.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"]
                        + " This end-to-end formally verifies pid-rs and proves "
                        "universal SxPID nonnegativity."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "nonsyntactic-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
                lambda value: value.update(
                    {
                        "claim_boundary": value["claim_boundary"]
                        + " This is also a universal population theorem."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "evolutionary-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
                lambda value: value.update(
                    {
                        "negative_boundary": value["negative_boundary"]
                        + " Nevertheless it is a universal nonnegativity proof "
                        "and validates all PID definitions."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "lean-boundary-contradictory-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-lean-check.json",
                lambda value: value.update(
                    {
                        "boundary": value["boundary"]
                        + " This formally verifies the complete SxPID2 certifier "
                        "and Python runtime."
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "mutation-evidence-injected-overclaim",
            mutated_json(
                baseline,
                "audit/evidence/sxpid2-exact-product-mutation-suite.json",
                lambda value: value.update(
                    {
                        "claim_boundary": (
                            "End-to-end formal verification of all PID software "
                            "and mathematics."
                        )
                    }
                ),
            ),
            "certified-SxPID evidence exact reviewed projection changed",
        ),
        (
            "just-gate-removed",
            mutated_text(
                baseline,
                "justfile",
                "python3 scripts/check-lean-exact-log-product.py",
                "true # removed",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "workflow-boundary-gate-writes-historical-evidence",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                (
                    "      - run: python3 "
                    "audit/tools/certified-sxpid/scripts/"
                    "check-nonsyntactic-zero-boundary.py"
                ),
                (
                    "      - run: python3 "
                    "audit/tools/certified-sxpid/scripts/"
                    "check-nonsyntactic-zero-boundary.py --update-evidence"
                ),
            ),
            "ordinary gate container must not update historical evidence",
        ),
        (
            "just-gate-moved-to-unused-recipe",
            transformed_text(
                baseline,
                "justfile",
                lambda text: text.replace(
                    "    python3 scripts/check-certified-sxpid2-claim.py\n",
                    "    true # claim gate removed\n",
                    1,
                )
                + "\nunused-retained-claim-gate:\n"
                + "    python3 scripts/check-certified-sxpid2-claim.py\n",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "release-audit-certified-sxpid-dependency-removed",
            mutated_text(
                baseline,
                "justfile",
                " formal-finite-convergence certified-sxpid citation-edge-countermodel ",
                " formal-finite-convergence citation-edge-countermodel ",
            ),
            "revision-3 release-audit dependency missing",
        ),
        (
            "ci-gate-removed",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
                "true # removed",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-commented-but-token-retained",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 scripts/check-certified-sxpid2-claim.py",
                "      # - run: python3 scripts/check-certified-sxpid2-claim.py",
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-moved-into-block-scalar",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 scripts/check-certified-sxpid2-claim.py",
                (
                    "    retained_gate_text: |\n"
                    "      - run: python3 scripts/check-certified-sxpid2-claim.py"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-moved-into-explicit-indent-block-scalar",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 scripts/check-certified-sxpid2-claim.py",
                (
                    "  retained_gate_text: |4\n"
                    "      - run: python3 scripts/check-certified-sxpid2-claim.py"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "ci-gate-disabled-by-step-condition",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "      - run: python3 scripts/check-certified-sxpid2-claim.py",
                (
                    "      - run: python3 scripts/check-certified-sxpid2-claim.py\n"
                    "        if: ${{ false }}"
                ),
            ),
            "revision-3 executable gate must occur once as an active command",
        ),
        (
            "invalid-commonmark-fence-cannot-hide-supported-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text
                + "\n```not-a-fence`\n"
                + "## Supported wording\n"
                + "the observed CI run was green\n"
                + "```\n",
            ),
            "unclosed fenced block in structured Markdown authority",
        ),
        (
            "setext-heading-cannot-duplicate-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text
                + "\nSupported wording\n"
                + "--\n"
                + "the observed CI run was green\n",
            ),
            "setext/horizontal headings are forbidden",
        ),
        (
            "markdown-emphasis-cannot-split-supported-overclaim",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                "## Why the verifier revision is justified",
                (
                    "The loaded-execution digest is a portable "
                    "**semantic hash**.\n\n"
                    "## Why the verifier revision is justified"
                ),
            ),
            "prohibited wording entered the supported section",
        ),
        (
            "raw-html-block-cannot-hide-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        '<script type="text/plain">\n'
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "</script>"
                    ),
                    1,
                ),
            ),
            "raw HTML is forbidden in structured Markdown authority",
        ),
        (
            "linked-label-cannot-hide-contradictory-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| [`audit/tools/certified-sxpid/scripts/verify_certificate.py`]"
                        "(../../audit/tools/certified-sxpid/scripts/verify_certificate.py) "
                        "| `0000000000000000000000000000000000000000000000000000000000000000` |"
                    ),
                    1,
                ),
            ),
            "linked pipe-table cells are forbidden",
        ),
        (
            "workflow-job-level-false-condition",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "  certified-sxpid-msrv:",
                "    if: ${{ false }}\n\n  certified-sxpid-msrv:",
            ),
            "certified-sxpid-reference workflow job exact digest changed",
        ),
        (
            "workflow-command-hidden-in-multiline-name",
            transformed_text(
                baseline,
                ".github/workflows/ci.yml",
                lambda text: text.replace(
                    "      - run: python3 scripts/check-certified-sxpid2-claim.py",
                    "",
                    1,
                ).replace(
                    "    name: Exact-count directed-rounding SxPID2 reference",
                    (
                        '    name: "Exact-count directed-rounding SxPID2 reference\n'
                        "      - run: python3 scripts/check-certified-sxpid2-claim.py\n"
                        '      "'
                    ),
                    1,
                ),
            ),
            "certified-sxpid-reference workflow job exact digest changed",
        ),
        (
            "just-shebang-exits-before-gates",
            mutated_text(
                baseline,
                "justfile",
                "certified-sxpid:\n",
                "certified-sxpid:\n    #!/bin/sh\n    exit 0\n",
            ),
            "certified-sxpid just recipe exact digest changed",
        ),
        (
            "workflow-jobs-container-disabled",
            mutated_text(
                baseline,
                ".github/workflows/ci.yml",
                "\njobs:\n",
                "\ndisabled_jobs:\n",
            ),
            "reviewed revision-3 execution container digest changed",
        ),
        (
            "just-global-shell-replaced-by-true",
            transformed_text(
                baseline,
                "justfile",
                lambda text: 'set shell := ["true"]\n\n' + text,
            ),
            "reviewed revision-3 execution container digest changed",
        ),
        (
            "html-entity-cannot-split-supported-overclaim",
            mutated_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                "## Why the verifier revision is justified",
                (
                    "The loaded-execution digest is a portable semantic "
                    "h&#97;sh.\n\n"
                    "## Why the verifier revision is justified"
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "emphasized-heading-cannot-duplicate-supported-section",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
                lambda text: text
                + "\n## Supported **wording**\n\n"
                + "the observed CI run was green\n",
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "equivalent-code-span-cannot-hide-duplicate-source-binding",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "| `` audit/tools/certified-sxpid/scripts/verify_certificate.py `` "
                        "| `0000000000000000000000000000000000000000000000000000000000000000` |"
                    ),
                    1,
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "token-retained-in-comment-cannot-reverse-claim-boundary",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                lambda text: text.replace(
                    "not a portable semantic hash",
                    "is a portable semantic hash",
                    1,
                )
                + "\n<!-- retained checker token: not a portable semantic hash -->\n",
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "multiline-raw-html-cannot-hide-source-binding-row",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
                lambda text: text.replace(
                    (
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |"
                    ),
                    (
                        "<script\n"
                        'type="text/plain"\n'
                        ">\n"
                        "| `audit/tools/certified-sxpid/scripts/verify_certificate.py` "
                        f"| `{baseline.sha256['audit/tools/certified-sxpid/scripts/verify_certificate.py']}` |\n"
                        "</script\n"
                        ">"
                    ),
                    1,
                ),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "crlf-authority-byte-drift",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
                lambda text: text.replace("\n", "\r\n"),
            ),
            "immutable revision-3 authority digest changed",
        ),
        (
            "historical-revision1-claim-rewrite",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v1.md",
                lambda _text: (
                    "# Claim revision 1\n\n"
                    "Revision 1 unconditionally proves every PID implementation correct.\n"
                ),
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-decision-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
                lambda text: text
                + "\n## Superseding statement\n\n"
                + "Revision 2 is unconditional formal verification and release authority.\n",
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-scope-expansion",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
                lambda text: text
                + "\n## Expanded scope\n\n"
                + "Revision 2 certifies continuous PID and all downstream applications.\n",
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "historical-revision2-evidence-overclaim",
            transformed_text(
                baseline,
                "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
                lambda text: text
                + "\n| End-to-end formal verification | Assumed | Supported | Unbounded |\n",
            ),
            "immutable retained historical packet digest changed",
        ),
        (
            "certifier-readme-formal-verification-overclaim",
            transformed_text(
                baseline,
                "audit/tools/certified-sxpid/README.md",
                lambda text: text
                + "\nThe verifier is formally verified and all SxPID atoms "
                + "have a proved sign.\n",
            ),
            "immutable reviewed certified-SxPID documentation digest changed",
        ),
        (
            "scripts-readme-formal-verification-overclaim",
            transformed_text(
                baseline,
                "scripts/README.md",
                lambda text: text
                + "\nThe certified SxPID2 verifier is end-to-end formally verified.\n",
            ),
            "immutable reviewed certified-SxPID documentation digest changed",
        ),
        (
            "formal-pdf-set-early-exit",
            mutated_text(
                baseline,
                "scripts/check-formal-pdf-set.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed certified-SxPID support-gate digest changed",
        ),
        (
            "certified-assurance-pdf-leaf-early-exit",
            mutated_text(
                baseline,
                "scripts/check-certified-sxpid2-assurance-pdf.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-pdf-leaf-early-exit",
            mutated_text(
                baseline,
                "scripts/check-exact-log-product-sxpid2-pdf.sh",
                "#!/usr/bin/env bash\n",
                "#!/usr/bin/env bash\nexit 0\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-policy-checker-early-exit",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-static-policy.py",
                "#!/usr/bin/env python3\n",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-policy-self-test-early-exit",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py",
                "#!/usr/bin/env python3\n",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "static-deny-policy-weakened",
            mutated_text(
                baseline,
                "audit/tools/certified-sxpid/deny.toml",
                'multiple-versions = "deny"',
                'multiple-versions = "allow"',
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "certified-assurance-tex-overclaim",
            transformed_text(
                baseline,
                "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
                lambda text: text
                + "\n% Contradictory mutant: end-to-end formal verification.\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-assurance-tex-overclaim",
            transformed_text(
                baseline,
                "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
                lambda text: text
                + "\n% Contradictory mutant: universal population theorem.\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
        ),
        (
            "exact-product-assurance-markdown-overclaim",
            transformed_text(
                baseline,
                "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
                lambda text: text
                + "\nThis formally verifies all PID software and mathematics.\n",
            ),
            "immutable reviewed executable/evidence artifact digest changed",
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
