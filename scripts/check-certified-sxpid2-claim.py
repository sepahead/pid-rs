#!/usr/bin/env python3
"""Fail closed when the revision-2 certified-SxPID2 assurance packet drifts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


if sys.version_info < (3, 11):
    raise SystemExit("check-certified-sxpid2-claim.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
METHOD_ID = "validation.certified-sxpid2-reference"
REPORT_SCHEMA = "pid-rs/certified-sxpid-report/v2"
VERIFICATION_SCHEMA = "pid-rs/certified-sxpid-independent-verification/v2"
RESOURCE_POLICY = "sxpid2-certification-default-v2"

TEXT_PATHS = (
    "audit/tools/certified-sxpid/src/report.rs",
    "audit/tools/certified-sxpid/src/resource.rs",
    "audit/tools/certified-sxpid/src/lib.rs",
    "audit/tools/certified-sxpid/scripts/verify_certificate.py",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v1.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v2.md",
    "justfile",
    ".github/workflows/ci.yml",
    "scripts/README.md",
    "scripts/check-formal-pdf-set.sh",
)

JSON_PATHS = (
    "method-catalog.json",
    "audit/evidence/sxpid2-exact-product-qualification.json",
    "audit/evidence/sxpid2-exact-product-mutation-suite.json",
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
    "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
    "audit/evidence/sxpid2-exact-product-lean-check.json",
)

HASH_PATHS = (
    "audit/tools/certified-sxpid/scripts/_exact_product.py",
    "audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "scripts/check-lean-exact-log-product.py",
    "audit/formal/lean-exact-log-product/PidExactLogProduct.lean",
    "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json",
    "scripts/generate-sxpid2-exhaustive-oracle.py",
)

REQUIRED_CATALOG_PATHS = frozenset(
    {
        "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
        "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
        "audit/formal/lean-exact-log-product/PidExactLogProduct.lean",
        "audit/tools/certified-sxpid/src/product.rs",
        "audit/tools/certified-sxpid/scripts/_exact_product.py",
        "audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
        "audit/tools/certified-sxpid/scripts/check-exact-products.py",
        "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
        "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
        "audit/evidence/sxpid2-exact-product-qualification.json",
        "audit/evidence/sxpid2-exact-product-mutation-suite.json",
        "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
        "audit/evidence/sxpid2-exact-product-evolutionary-challenge.json",
        "audit/evidence/sxpid2-exact-product-lean-check.json",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v2.md",
        "output/pdf/exact-log-product-sxpid2-assurance.pdf",
        "scripts/check-lean-exact-log-product.py",
        "scripts/check-exact-log-product-sxpid2-pdf.sh",
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-certified-sxpid2-claim-self-test.py",
    }
)

GATE_COMMANDS = (
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products.py",
    "python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py",
    "python3 scripts/check-lean-exact-log-product.py",
    "python3 scripts/check-certified-sxpid2-claim.py",
    "python3 scripts/check-certified-sxpid2-claim-self-test.py",
)


class ClaimPacketError(RuntimeError):
    """The live certifier, evidence, catalog, or versioned claim packet disagrees."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ClaimPacketError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def parse_json(raw: str, path: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ClaimPacketError) as error:
        raise ClaimPacketError(f"{path}: invalid strict JSON: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClaimPacketError(message)


@dataclass(frozen=True)
class Snapshot:
    text: Mapping[str, str]
    json_values: Mapping[str, Any]
    sha256: Mapping[str, str]


def read_snapshot(root: Path = ROOT) -> Snapshot:
    text: dict[str, str] = {}
    for relative in TEXT_PATHS:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"missing/nonregular text: {relative}")
        text[relative] = path.read_text(encoding="utf-8")
    values: dict[str, Any] = {}
    for relative in JSON_PATHS:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"missing/nonregular JSON: {relative}")
        values[relative] = parse_json(path.read_text(encoding="utf-8"), relative)
    hashes: dict[str, str] = {}
    for relative in HASH_PATHS:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"missing/nonregular bound source: {relative}")
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in REQUIRED_CATALOG_PATHS:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"missing/nonregular evidence: {relative}")
        require(path.stat().st_size > 0, f"empty evidence artifact: {relative}")
    return Snapshot(text=text, json_values=values, sha256=hashes)


def require_token(snapshot: Snapshot, path: str, token: str, label: str) -> None:
    require(token in snapshot.text[path], f"{label} missing from {path}: {token!r}")


def validate(snapshot: Snapshot) -> None:
    # Live producer/verifier/schema agreement.
    require_token(snapshot, "audit/tools/certified-sxpid/src/report.rs", REPORT_SCHEMA, "report schema")
    require_token(snapshot, "audit/tools/certified-sxpid/src/resource.rs", RESOURCE_POLICY, "resource policy")
    verifier = "audit/tools/certified-sxpid/scripts/verify_certificate.py"
    for token, label in (
        (REPORT_SCHEMA, "verifier report schema"),
        (VERIFICATION_SCHEMA, "verification schema"),
        (RESOURCE_POLICY, "verifier resource policy"),
        ("not_compared_per_expression_preflight_limit", "product local abstention"),
        ("not_compared_total_preflight_limit", "product aggregate abstention"),
        ("certified_exact_zero", "product exact-zero decision"),
        ("exact_multiplicative_product_equals_one", "product zero witness"),
        ("src/product.rs", "verifier source manifest"),
    ):
        require_token(snapshot, verifier, token, label)
    require_token(snapshot, "audit/tools/certified-sxpid/src/lib.rs", '"src/product.rs"', "producer source manifest")

    # Historical revision remains explicit, and revision 2 names its changed semantics.
    decision_v1 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision.md"
    require_token(snapshot, decision_v1, "revision 1", "historical decision revision")
    require_token(snapshot, decision_v1, "Revision 1 must be re-adjudicated", "historical trigger")
    require_token(snapshot, decision_v1, "Historical revision 1 must not be silently rewritten", "historical preservation rule")
    claim_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v2.md"
    for token, label in (
        ("revision 2", "claim revision"),
        (REPORT_SCHEMA, "claim report schema"),
        (VERIFICATION_SCHEMA, "claim verification schema"),
        (RESOURCE_POLICY, "claim resource policy"),
        ("exact-product record has status `compared`", "claim product premise"),
        ("does not replace the dyadic interval", "claim lane separation"),
        ("no exact-product zero/sign claim is available", "claim abstention boundary"),
        ("defines no new PID measure", "claim provenance boundary"),
    ):
        require_token(snapshot, claim_v2, token, label)
    decision_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v2.md"
    require_token(snapshot, decision_v2, "historical decision remains", "revision preservation")
    require_token(snapshot, decision_v2, "Revision 2 requires a new revision", "revision-2 trigger")
    require_token(
        snapshot,
        decision_v2,
        "exact five-factor rational",
        "revision-2 retained-witness formal boundary",
    )
    bindings_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v2.md"
    require_token(
        snapshot,
        bindings_v2,
        "Six generic exact log/product/sign theorems",
        "revision-2 generic Lean inventory",
    )
    require_token(
        snapshot,
        bindings_v2,
        "separate exact-rational and Rust routes bind those",
        "revision-2 Lean-to-SxPID non-refinement boundary",
    )
    obligations_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v2.md"
    require_token(
        snapshot,
        obligations_v2,
        "six generic theorems plus one exact five-factor rational identity",
        "revision-2 Lean obligation inventory",
    )
    evidence_v2 = "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v2.md"
    require_token(
        snapshot,
        evidence_v2,
        "exact five-factor Lean identity",
        "revision-2 retained-witness evidence",
    )
    theorem_map_v2 = (
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v2.md"
    )
    require_token(
        snapshot,
        theorem_map_v2,
        "exact five-factor rational product identity",
        "revision-2 theorem/evidence boundary",
    )
    require_token(
        snapshot,
        theorem_map_v2,
        "the retained five-factor rational identity; exact-rational and Rust routes separately bind that",
        "revision-2 formal non-refinement boundary",
    )
    index = "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md"
    require_token(snapshot, index, "| 1 |", "revision-1 index row")
    require_token(snapshot, index, "| 2 |", "revision-2 index row")

    # Catalog must describe and inventory the actual v2 assurance route.
    catalog = snapshot.json_values["method-catalog.json"]
    require(isinstance(catalog, dict), "method catalog root is not an object")
    methods = catalog.get("methods")
    require(isinstance(methods, list), "method catalog has no methods array")
    matches = [item for item in methods if isinstance(item, dict) and item.get("id") == METHOD_ID]
    require(len(matches) == 1, f"expected one {METHOD_ID!r} catalog entry")
    method = matches[0]
    require(method.get("scientific_novelty_claim") == "none", "certifier acquired a scientific novelty claim")
    require(method.get("definition_origin") == "project-defined", "certifier definition origin drifted")
    require(method.get("implementation_origin") == "local-implementation", "certifier implementation origin drifted")
    source_files = method.get("source_files")
    require(isinstance(source_files, list), "certifier source_files is not an array")
    missing = sorted(REQUIRED_CATALOG_PATHS.difference(source_files))
    require(not missing, f"certifier catalog omits revision-2 source/evidence: {missing}")
    validation = method.get("validation")
    require(isinstance(validation, dict), "certifier validation block is absent")
    evidence_paths = validation.get("evidence_paths")
    require(isinstance(evidence_paths, list), "certifier evidence_paths is not an array")
    evidence_required = {
        path for path in REQUIRED_CATALOG_PATHS if path.startswith(("audit/evidence/", "audit/formal/", "claims/", "output/pdf/", "scripts/check-"))
    }
    missing_evidence = sorted(evidence_required.difference(evidence_paths))
    require(not missing_evidence, f"certifier validation omits revision-2 evidence: {missing_evidence}")
    combined_claim_text = "\n".join(
        str(method.get(field, "")) for field in ("summary", "new_in_pid_rs", "constraints")
    )
    for token in (
        "exact-product",
        "product-one",
        "not a population",
        "not end-to-end formally verified",
    ):
        require(token in combined_claim_text.lower(), f"catalog claim boundary omits {token!r}")

    # Recorded evidence must be self-identifying and retain its bounded negative result.
    qualification = snapshot.json_values["audit/evidence/sxpid2-exact-product-qualification.json"]
    require(qualification.get("schema") == "pid-rs/sxpid2-exact-product-qualification/v1", "qualification schema drifted")
    require(qualification.get("status") == "passed", "exact-product qualification is not passed")
    checks = qualification.get("checks", {})
    require(checks.get("expression_products") == 11_856, "qualification product count drifted")
    require(checks.get("exact_signs") == 11_856, "qualification sign count drifted")
    qualification_bindings = qualification.get("bindings", {})
    for field, relative in (
        ("exact_product_source_sha256", "audit/tools/certified-sxpid/scripts/_exact_product.py"),
        ("qualification_source_sha256", "audit/tools/certified-sxpid/scripts/check-exact-products.py"),
        ("fixture_sha256", "crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json"),
        ("fixture_generator_sha256", "scripts/generate-sxpid2-exhaustive-oracle.py"),
    ):
        require(
            qualification_bindings.get(field) == snapshot.sha256[relative],
            f"qualification binding {field} does not match {relative}",
        )

    mutations = snapshot.json_values["audit/evidence/sxpid2-exact-product-mutation-suite.json"]
    require(mutations.get("status") == "passed", "exact-product mutation suite is not passed")
    require(mutations.get("certificate_mutations_killed") == 13, "certificate-mutation count drifted")
    require(mutations.get("semantic_source_mutations_killed") == 6, "source-mutation count drifted")
    require(mutations.get("structural_adversaries_rejected") == 4, "structural-adversary count drifted")
    require(
        mutations.get("preflight_before_powering_controls_passed") == 2,
        "preflight-before-powering control count drifted",
    )
    require(mutations.get("total_adversaries") == 23, "exact-product adversary count drifted")
    require(
        mutations.get("certificate_mutations_killed", 0)
        + mutations.get("semantic_source_mutations_killed", 0)
        + mutations.get("structural_adversaries_rejected", 0)
        == mutations.get("total_adversaries"),
        "exact-product mutation subtotals do not reconstruct the total",
    )
    mutation_bindings = mutations.get("bindings", {})
    require(
        mutation_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "mutation evidence exact-product source binding drifted",
    )
    require(
        mutation_bindings.get("self_test_source_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py"
        ],
        "mutation evidence self-test source binding drifted",
    )

    boundary = snapshot.json_values["audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json"]
    require(boundary.get("status") == "passed", "non-syntactic zero boundary is not passed")
    findings = boundary.get("findings", {})
    require(findings.get("n8_coordinate_count") == 16, "total-eight product-one count drifted")
    witness = findings.get("minimized_witness", {})
    require(witness.get("counts") == [0, 0, 1, 1, 1, 4, 1, 0], "retained product-one witness drifted")
    require(witness.get("interval_decision") == "unresolved_sign", "counterexample interval boundary drifted")
    require(witness.get("exact_product_decision") == "certified_exact_zero", "counterexample product decision drifted")
    boundary_bindings = boundary.get("bindings", {})
    require(
        boundary_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "boundary evidence exact-product source binding drifted",
    )
    require(
        boundary_bindings.get("boundary_script_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py"
        ],
        "boundary evidence script binding drifted",
    )

    lean = snapshot.json_values["audit/evidence/sxpid2-exact-product-lean-check.json"]
    require(lean.get("status") == "passed", "Lean exact-product check is not passed")
    require(lean.get("theorems_kernel_checked") == 7, "Lean theorem count drifted")
    require("Generic log/product/sign algebra only" in lean.get("boundary", ""), "Lean boundary broadened")
    require(
        lean.get("source_sha256")
        == snapshot.sha256[
            "audit/formal/lean-exact-log-product/PidExactLogProduct.lean"
        ],
        "Lean evidence theorem-source binding drifted",
    )
    require(
        lean.get("checker_source_sha256")
        == snapshot.sha256["scripts/check-lean-exact-log-product.py"],
        "Lean evidence checker-source binding drifted",
    )

    challenge = snapshot.json_values["audit/evidence/sxpid2-exact-product-evolutionary-challenge.json"]
    require(challenge.get("status") == "no_counterexample_found_within_search", "evolutionary result status drifted")
    require(challenge.get("search", {}).get("unique_count_tables_evaluated") == 5_921, "evolutionary evaluation count drifted")
    require("not a universal nonnegativity proof" in challenge.get("negative_boundary", ""), "evolutionary negative boundary broadened")
    challenge_bindings = challenge.get("bindings", {})
    require(
        challenge_bindings.get("exact_product_source_sha256")
        == snapshot.sha256["audit/tools/certified-sxpid/scripts/_exact_product.py"],
        "evolutionary evidence exact-product source binding drifted",
    )
    require(
        challenge_bindings.get("challenge_source_sha256")
        == snapshot.sha256[
            "audit/tools/certified-sxpid/scripts/challenge-exact-products.py"
        ],
        "evolutionary evidence script binding drifted",
    )

    # Every normal entry point must execute the new gates; the formal inventory must include the paper.
    for path in ("justfile", ".github/workflows/ci.yml"):
        for command in GATE_COMMANDS:
            require_token(snapshot, path, command, "revision-2 executable gate")
    formal_set = "scripts/check-formal-pdf-set.sh"
    require_token(snapshot, formal_set, '"exact-log-product-sxpid2-assurance"', "formal PDF inventory")
    require_token(snapshot, formal_set, "scripts/check-exact-log-product-sxpid2-pdf.sh", "formal PDF replay")
    scripts_readme = "scripts/README.md"
    for token in (
        "check-certified-sxpid2-claim.py",
        "check-exact-log-product-sxpid2-pdf.sh",
        "bounded exact",
        "rational-product zero/sign extension",
    ):
        require_token(snapshot, scripts_readme, token, "script documentation")


def main() -> int:
    try:
        validate(read_snapshot())
        print("OK: certified SxPID2 claim revisions 1-2, schemas, evidence, catalog, and gates are coherent")
        return 0
    except (OSError, UnicodeError, ClaimPacketError) as error:
        print(f"certified SxPID2 claim check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
