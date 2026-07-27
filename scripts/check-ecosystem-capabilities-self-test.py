#!/usr/bin/env python3
"""Exercise fail-closed mutations for the ecosystem capability contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-ecosystem-capabilities.py"
SPEC = importlib.util.spec_from_file_location(
    "check_ecosystem_capabilities", CHECKER_PATH
)
if SPEC is None or SPEC.loader is None:
    raise SystemExit(f"cannot load checker: {CHECKER_PATH}")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


Mutation = Callable[[dict[str, Any]], None]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def canonical_write(path: Path, value: Any) -> str:
    raw = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def binding(contract: dict[str, Any], binding_id: str) -> dict[str, Any]:
    return next(
        item for item in contract["source_bindings"] if item["id"] == binding_id
    )


def consumer(contract: dict[str, Any], consumer_id: str) -> dict[str, Any]:
    return next(item for item in contract["consumers"] if item["id"] == consumer_id)


def requirement(
    contract: dict[str, Any], consumer_id: str, requirement_id: str
) -> dict[str, Any]:
    return next(
        item
        for item in consumer(contract, consumer_id)["requirements"]
        if item["id"] == requirement_id
    )


def gap(contract: dict[str, Any], consumer_id: str, gap_id: str) -> dict[str, Any]:
    return next(
        item
        for item in consumer(contract, consumer_id)["gaps"]
        if item["id"] == gap_id
    )


def evidence_record(
    contract: dict[str, Any],
    consumer_id: str,
    requirement_id: str,
    evidence_class: str,
) -> dict[str, Any]:
    return next(
        item
        for item in requirement(contract, consumer_id, requirement_id)["evidence"][
            "present"
        ]
        if item["class"] == evidence_class
    )


def catalog_method(catalog: dict[str, Any], method_id: str) -> dict[str, Any]:
    return next(item for item in catalog["methods"] if item["id"] == method_id)


def validate(
    root: Path,
    contract: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    CHECKER.validate_contract(root, contract, schema)


def expect_rejected(
    name: str,
    base_contract: dict[str, Any],
    schema: dict[str, Any],
    mutation: Mutation,
) -> None:
    validate(ROOT, base_contract, schema)
    candidate = copy.deepcopy(base_contract)
    mutation(candidate)
    try:
        validate(ROOT, candidate, schema)
    except CHECKER.EcosystemContractError:
        return
    raise AssertionError(f"mutation did not fail closed: {name}")


def collect_local_paths(contract: dict[str, Any]) -> set[str]:
    paths = {item["path"] for item in contract["source_bindings"]}
    paths.update(
        {
            "audit/evidence/repository-snapshot-envelope.json",
            "audit/evidence/repository-snapshot.json.sha256",
        }
    )
    for item in contract["consumers"]:
        for req in item["requirements"]:
            for record in req["evidence"]["present"]:
                paths.update(record["paths"])
        for item_gap in item["gaps"]:
            paths.update(item_gap["evidence_paths"])
    return paths


def copy_fixture(root: Path, contract: dict[str, Any]) -> None:
    for relative in sorted(collect_local_paths(contract)):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def update_binding_digest(
    root: Path,
    contract: dict[str, Any],
    binding_id: str,
) -> str:
    item = binding(contract, binding_id)
    digest = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest()
    item["sha256"] = digest
    return digest


def rebind_moving_authority_digests(
    root: Path, contract: dict[str, Any]
) -> None:
    for binding_id in sorted(
        CHECKER.HISTORICAL_BASE_MOVING_AUTHORITY_SHA256
    ):
        update_binding_digest(root, contract, binding_id)


def swap_moving_authority_hashes(contract: dict[str, Any]) -> None:
    catalog = binding(contract, "method-catalog")
    scope = binding(contract, "release-scope")
    catalog["sha256"], scope["sha256"] = scope["sha256"], catalog["sha256"]


def mutate_reviewed_need_after_live_rebind(contract: dict[str, Any]) -> None:
    rebind_moving_authority_digests(ROOT, contract)
    requirement(contract, "crebain", "crebain.frozen-map")["need"] = (
        "Crebain needs a different but still bounded frozen-map statement."
    )


def mutate_historical_evidence_after_live_rebind(
    contract: dict[str, Any],
) -> None:
    rebind_moving_authority_digests(ROOT, contract)
    consumer(contract, "prisoma")["historical_evidence"][0]["scope"] = (
        "A different bounded historical scope."
    )


def mutate_inventory_after_live_rebind(contract: dict[str, Any]) -> None:
    rebind_moving_authority_digests(ROOT, contract)
    contract["inventory_scope"] = (
        "A different selected and non-exhaustive historical inventory boundary."
    )


def expect_bound_mutation_rejected(
    name: str,
    base_contract: dict[str, Any],
    schema: dict[str, Any],
    mutation: Callable[[Path, dict[str, Any]], None],
) -> None:
    with tempfile.TemporaryDirectory(prefix="pid-rs-ecosystem-self-test-") as temp:
        root = Path(temp)
        candidate = copy.deepcopy(base_contract)
        copy_fixture(root, candidate)
        validate(root, candidate, schema)
        mutation(root, candidate)
        try:
            validate(root, candidate, schema)
        except CHECKER.EcosystemContractError:
            return
        raise AssertionError(f"bound mutation did not fail closed: {name}")


def mutate_release_scope_status(root: Path, contract: dict[str, Any]) -> None:
    scope_path = root / binding(contract, "release-scope")["path"]
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    next(
        claim
        for claim in scope["integration_claims"]
        if claim["integration_id"] == "crebain"
    )["claim_status"] = "qualified"
    scope_digest = canonical_write(scope_path, scope)
    binding(contract, "release-scope")["sha256"] = scope_digest

    assurance_path = root / binding(contract, "assurance-registry")["path"]
    assurance = json.loads(assurance_path.read_text(encoding="utf-8"))
    assurance["release_scope_sha256"] = scope_digest
    binding(contract, "assurance-registry")["sha256"] = canonical_write(
        assurance_path, assurance
    )


def mutate_method_availability(root: Path, contract: dict[str, Any]) -> None:
    catalog_path = root / binding(contract, "method-catalog")["path"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_method(catalog, "shared-exclusions.categorical")[
        "code_availability"
    ] = "external"
    binding(contract, "method-catalog")["sha256"] = canonical_write(
        catalog_path, catalog
    )


def mutate_method_constraint_and_rebind(
    root: Path, contract: dict[str, Any]
) -> None:
    catalog_path = root / binding(contract, "method-catalog")["path"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_method(catalog, "shared-exclusions.categorical")[
        "constraints"
    ] = "This method can replace every external application decision."
    binding(contract, "method-catalog")["sha256"] = canonical_write(
        catalog_path, catalog
    )


def mutate_assurance_coverage(root: Path, contract: dict[str, Any]) -> None:
    assurance_path = root / binding(contract, "assurance-registry")["path"]
    assurance = json.loads(assurance_path.read_text(encoding="utf-8"))
    assurance["families"] = assurance["families"][1:]
    binding(contract, "assurance-registry")["sha256"] = canonical_write(
        assurance_path, assurance
    )


def mutate_assurance_semantic_escalation(
    root: Path, contract: dict[str, Any]
) -> None:
    assurance_path = root / binding(contract, "assurance-registry")["path"]
    assurance = json.loads(assurance_path.read_text(encoding="utf-8"))
    family = next(
        item
        for item in assurance["families"]
        if item["family_id"] == "pid-core.experimental.continuous.pid2"
    )
    layer = family["layers"]["statistical_application_validity"]
    layer["assurance"]["status"] = "TESTED"
    layer["assurance"]["evidence_tier"] = "IMPLEMENTATION_TEST"
    layer["gaps"][0]["disposition"] = "OPEN_LOCAL"
    binding(contract, "assurance-registry")["sha256"] = canonical_write(
        assurance_path, assurance
    )


def mutate_snapshot_identity(root: Path, contract: dict[str, Any]) -> None:
    snapshot_path = root / binding(contract, "repository-snapshot")["path"]
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    next(
        row for row in snapshot["repositories"] if row["name"] == "prisoma"
    )["commit_sha"] = "0" * 40
    digest = canonical_write(snapshot_path, snapshot)
    binding(contract, "repository-snapshot")["sha256"] = digest
    (root / "audit/evidence/repository-snapshot.json.sha256").write_text(
        f"{digest}  repository-snapshot.json\n",
        encoding="ascii",
    )
    envelope_path = root / "audit/evidence/repository-snapshot-envelope.json"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    envelope["snapshot_sha256"] = digest
    canonical_write(envelope_path, envelope)


def promote_readme_assumption_certificate(contract: dict[str, Any]) -> None:
    item = requirement(
        contract, "galadriel", "galadriel.dependent-windows"
    )
    item["evidence"]["missing_classes"].remove("assumption-certificate")
    item["evidence"]["present"].append(
        {"class": "assumption-certificate", "paths": ["README.md"]}
    )
    item["evidence"]["present"].sort(key=lambda record: record["class"])
    gap(
        contract, "galadriel", "galadriel.dependent-windows"
    )["missing_evidence_classes"].remove("assumption-certificate")


def promote_schema2_as_scientific_replay(contract: dict[str, Any]) -> None:
    item = requirement(contract, "crebain", "crebain.runlog-binding")
    item["evidence"]["missing_classes"].remove("runlog-replay")
    item["evidence"]["present"].append(
        {
            "class": "runlog-replay",
            "paths": [
                "crates/pid-runlog/src/lib.rs",
                "crates/pid-runlog/tests/replay_cli.rs",
            ],
        }
    )
    item["evidence"]["present"].sort(key=lambda record: record["class"])
    gap(contract, "crebain", "crebain.runlog-binding")[
        "missing_evidence_classes"
    ].remove("runlog-replay")


def downgrade_scientific_replay_to_schema2(contract: dict[str, Any]) -> None:
    item = requirement(contract, "crebain", "crebain.runlog-binding")
    item["primary_method_ids"].remove(
        "software.scientific-outcome-contract-foundation"
    )
    item["local_method_maturity"] = "stable"
    schema2_paths = [
        "crates/pid-runlog/src/lib.rs",
        "crates/pid-runlog/tests/replay_cli.rs",
    ]
    evidence_record(
        contract,
        "crebain",
        "crebain.runlog-binding",
        "bounded-software-test",
    )["paths"] = schema2_paths
    evidence_record(
        contract,
        "crebain",
        "crebain.runlog-binding",
        "implementation-contract",
    )["paths"] = schema2_paths
    promote_schema2_as_scientific_replay(contract)


def erase_crebain_local_assurance_obligations(
    contract: dict[str, Any],
) -> None:
    item = requirement(contract, "crebain", "crebain.frozen-map")
    for evidence_class in (
        "certified-numerical-bound",
        "deductive-rust-refinement",
    ):
        item["evidence"]["required_classes"].remove(evidence_class)
        item["evidence"]["missing_classes"].remove(evidence_class)
    item["gap_ids"].remove("crebain.local-assurance")
    gap(contract, "crebain", "crebain.local-assurance")[
        "affected_requirement_ids"
    ].remove("crebain.frozen-map")


def erase_continuous_statistical_validation(
    contract: dict[str, Any],
) -> None:
    item = requirement(
        contract, "galadriel", "galadriel.continuous-pid2"
    )
    item["evidence"]["required_classes"].remove("statistical-validation")
    item["evidence"]["missing_classes"].remove("statistical-validation")
    gap(contract, "galadriel", "galadriel.continuous-pid2")[
        "missing_evidence_classes"
    ].remove("statistical-validation")


def erase_haldir_retained_boundary(contract: dict[str, Any]) -> None:
    item = requirement(contract, "haldir", "haldir.authorization")
    item["local_method_maturity"] = "unavailable"
    item["evidence"]["required_classes"].append("implementation-contract")
    item["evidence"]["required_classes"].sort()
    item["evidence"]["missing_classes"].append("implementation-contract")
    item["evidence"]["missing_classes"].sort()
    local_gap = gap(contract, "haldir", "haldir.authorization-local")
    local_gap["disposition"] = "OPEN_LOCAL"
    local_gap["missing_evidence_classes"].append("implementation-contract")
    local_gap["missing_evidence_classes"].sort()


def launder_haldir_assumption_certificate(
    contract: dict[str, Any],
) -> None:
    item = requirement(
        contract, "haldir", "haldir.dependency-certificate"
    )
    item["evidence"]["missing_classes"].remove("assumption-certificate")
    item["evidence"]["present"].append(
        {
            "class": "assumption-certificate",
            "paths": [
                "crates/pid-core/src/sxpid.rs",
                "crates/pid-core/tests/sxpid_properties.rs",
            ],
        }
    )
    item["evidence"]["present"].sort(key=lambda record: record["class"])
    gap(contract, "haldir", "haldir.dependency-certificate")[
        "missing_evidence_classes"
    ].remove("assumption-certificate")


def main() -> int:
    base_contract = CHECKER.load_json(
        ROOT / "ecosystem-capabilities.json", canonical=True
    )
    schema = CHECKER.load_json(
        ROOT / "audit/schemas/ecosystem-capabilities.schema.json",
        canonical=True,
    )
    validate(ROOT, base_contract, schema)

    mutations: list[tuple[str, Mutation]] = [
        (
            "unknown top-level field",
            lambda value: value.__setitem__("unexpected", True),
        ),
        (
            "schema revision drift",
            lambda value: value.__setitem__("schema_revision", 2),
        ),
        (
            "claim-boundary drift",
            lambda value: value.__setitem__("claim_boundary", "A broader claim."),
        ),
        (
            "claim exclusion removed",
            lambda value: value["claims_not_made"].pop(),
        ),
        (
            "consumer removed",
            lambda value: value["consumers"].pop(),
        ),
        (
            "consumer order drift",
            lambda value: value["consumers"].reverse(),
        ),
        (
            "external integration included",
            lambda value: value["consumers"].append(
                copy.deepcopy(value["consumers"][0])
            ),
        ),
        (
            "excluded integration removed",
            lambda value: value["excluded_integration_ids"].clear(),
        ),
        (
            "stale moving authority hash",
            lambda value: binding(value, "method-catalog").__setitem__(
                "sha256", "0" * 64
            ),
        ),
        (
            "missing moving authority hash",
            lambda value: binding(value, "assurance-registry").pop("sha256"),
        ),
        (
            "swapped moving authority hashes",
            swap_moving_authority_hashes,
        ),
        (
            "binding path drift",
            lambda value: binding(value, "method-catalog").__setitem__(
                "path", "README.md"
            ),
        ),
        (
            "binding role drift",
            lambda value: binding(value, "release-scope").__setitem__(
                "role", "A substituted authority role."
            ),
        ),
        (
            "evidence vocabulary drift",
            lambda value: value["evidence_class_definitions"][0].__setitem__(
                "meaning", "Changed meaning."
            ),
        ),
        (
            "local maturity vocabulary drift",
            lambda value: value["local_method_maturity_definitions"][
                0
            ].__setitem__("meaning", "Changed meaning."),
        ),
        (
            "historical source removed",
            lambda value: consumer(value, "prisoma")[
                "historical_requirement_sources"
            ].pop(),
        ),
        (
            "historical source order drift",
            lambda value: consumer(value, "crebain")[
                "historical_requirement_sources"
            ].reverse(),
        ),
        (
            "requirement cites unselected historical source",
            lambda value: requirement(
                value, "crebain", "crebain.adapter"
            )["historical_source_paths"].append("docs/UNSELECTED.md"),
        ),
        (
            "selected historical source becomes uncited",
            lambda value: requirement(
                value, "crebain", "crebain.signed-atoms"
            )["historical_source_paths"].remove(
                "docs/PLANT_APPLY_OBSERVATION_V1.md"
            ),
        ),
        (
            "unknown primary method",
            lambda value: requirement(
                value, "haldir", "haldir.signed-interpretation"
            )["primary_method_ids"].append("unknown.method"),
        ),
        (
            "validation method as primary",
            lambda value: requirement(
                value, "haldir", "haldir.signed-interpretation"
            )["primary_method_ids"].append(
                "validation.finite-alphabet-plugin-convergence"
            ),
        ),
        (
            "unsupported method as primary",
            lambda value: requirement(
                value, "prisoma", "prisoma.mixed-support"
            )["primary_method_ids"].append(
                "unsupported.mixed-support-continuous-pid"
            ),
        ),
        (
            "local method as unsupported boundary",
            lambda value: requirement(
                value, "prisoma", "prisoma.mixed-support"
            )["boundary_method_ids"].__setitem__(
                0, "shared-exclusions.categorical"
            ),
        ),
        (
            "nonvalidation method in validation role",
            lambda value: requirement(
                value, "prisoma", "prisoma.row-law"
            )["validation_method_ids"].__setitem__(
                0, "shared-exclusions.categorical"
            ),
        ),
        (
            "false family mapping",
            lambda value: requirement(
                value, "prisoma", "prisoma.row-law"
            )["release_scope_family_ids"].__setitem__(
                0, "pid-core.stable.quantized"
            ),
        ),
        (
            "familyless software forced into family",
            lambda value: requirement(
                value, "crebain", "crebain.runlog-binding"
            )["release_scope_family_ids"].append("pid-core.infrastructure"),
        ),
        (
            "experimental route promoted to stable",
            lambda value: requirement(
                value, "crebain", "crebain.runlog-binding"
            ).__setitem__("local_method_maturity", "stable"),
        ),
        (
            "unavailable route gains primary implementation",
            lambda value: (
                requirement(value, "crebain", "crebain.adapter")[
                    "primary_method_ids"
                ].append("shared-exclusions.categorical"),
                requirement(value, "crebain", "crebain.adapter")[
                    "release_scope_family_ids"
                ].append("pid-core.stable.categorical"),
            ),
        ),
        (
            "stable route loses primary implementation",
            lambda value: (
                requirement(value, "crebain", "crebain.signed-atoms")[
                    "primary_method_ids"
                ].clear(),
                requirement(value, "crebain", "crebain.signed-atoms")[
                    "release_scope_family_ids"
                ].clear(),
            ),
        ),
        (
            "unavailable route omits implementation gap",
            lambda value: (
                requirement(value, "crebain", "crebain.adapter")["evidence"][
                    "required_classes"
                ].remove("implementation-contract"),
                requirement(value, "crebain", "crebain.adapter")["evidence"][
                    "missing_classes"
                ].remove("implementation-contract"),
                gap(value, "crebain", "crebain.adapter")[
                    "missing_evidence_classes"
                ].remove("implementation-contract"),
            ),
        ),
        (
            "present and missing evidence overlap",
            lambda value: requirement(
                value, "crebain", "crebain.adapter"
            )["evidence"]["present"].append(
                {
                    "class": "consumer-commit-integration",
                    "paths": ["release-scope-1.0.json"],
                }
            ),
        ),
        (
            "gap leaves missing evidence unassigned",
            lambda value: gap(value, "crebain", "crebain.adapter")[
                "missing_evidence_classes"
            ].pop(),
        ),
        (
            "orphan forward gap link",
            lambda value: requirement(
                value, "crebain", "crebain.adapter"
            )["gap_ids"].clear(),
        ),
        (
            "gap owner drift",
            lambda value: gap(value, "crebain", "crebain.adapter").__setitem__(
                "owner", "pid-rs"
            ),
        ),
        (
            "gap priority drift",
            lambda value: gap(value, "crebain", "crebain.adapter").__setitem__(
                "priority", "P2"
            ),
        ),
        (
            "P0 gap loses negative challenges",
            lambda value: gap(value, "crebain", "crebain.adapter")[
                "negative_tests"
            ].clear(),
        ),
        (
            "retained boundary disposition removed",
            lambda value: gap(
                value, "haldir", "haldir.authorization-local"
            ).__setitem__("disposition", "OPEN_LOCAL"),
        ),
        (
            "missing evidence path",
            lambda value: requirement(
                value, "crebain", "crebain.signed-atoms"
            )["evidence"]["present"][0]["paths"].__setitem__(
                0, "missing-evidence.txt"
            ),
        ),
        (
            "affirmative compatibility wording",
            lambda value: consumer(value, "crebain").__setitem__(
                "summary", "A compatible route is available."
            ),
        ),
        (
            "README substituted for bounded test",
            lambda value: evidence_record(
                value,
                "crebain",
                "crebain.frozen-map",
                "bounded-software-test",
            ).__setitem__("paths", ["README.md"]),
        ),
        (
            "README promoted to assumption certificate",
            promote_readme_assumption_certificate,
        ),
        (
            "prose substituted for executable negative mutation",
            lambda value: evidence_record(
                value,
                "prisoma",
                "prisoma.mixed-support",
                "negative-mutation",
            ).__setitem__("paths", ["README.md"]),
        ),
        (
            "schema 2 replay promoted to schema 3 scientific replay",
            promote_schema2_as_scientific_replay,
        ),
        (
            "scientific replay coherently downgraded to schema 2",
            downgrade_scientific_replay_to_schema2,
        ),
        (
            "negation camouflage hides an affirmative overclaim",
            lambda value: requirement(
                value, "crebain", "crebain.adapter"
            ).__setitem__(
                "need",
                (
                    "This statement does not claim general validation; the route "
                    "is certified safe and deployable."
                ),
            ),
        ),
        (
            "external authorization responsibility laundered as local",
            lambda value: (
                gap(
                    value, "haldir", "haldir.authorization-external"
                ).__setitem__("disposition", "OPEN_LOCAL"),
                gap(
                    value, "haldir", "haldir.authorization-external"
                ).__setitem__("owner", "pid-rs"),
            ),
        ),
        (
            "historical Haldir sources recast as PID authorization demand",
            lambda value: requirement(
                value, "haldir", "haldir.authorization"
            ).__setitem__(
                "need",
                (
                    "The selected Haldir sources require pid-rs PID as an "
                    "authorization primitive."
                ),
            ),
        ),
        (
            "local numerical and refinement obligations erased",
            erase_crebain_local_assurance_obligations,
        ),
        (
            "continuous statistical-validation obligation erased",
            erase_continuous_statistical_validation,
        ),
        (
            "Haldir retained authority boundary coherently erased",
            erase_haldir_retained_boundary,
        ),
        (
            "signed-atom implementation evidence laundered within family",
            lambda value: evidence_record(
                value,
                "crebain",
                "crebain.signed-atoms",
                "implementation-contract",
            ).__setitem__(
                "paths",
                [
                    "crates/pid-core/src/sxpid.rs",
                    "crates/pid-core/tests/dependency_colored_sxpid_oracle.rs",
                ],
            ),
        ),
        (
            "preprocessing test evidence laundered within family",
            lambda value: evidence_record(
                value,
                "galadriel",
                "galadriel.preprocessing",
                "bounded-software-test",
            ).__setitem__(
                "paths",
                ["crates/pid-core/tests/preprocess.rs"],
            ),
        ),
        (
            "Haldir assumption certificate laundered within family",
            launder_haldir_assumption_certificate,
        ),
        (
            "one-family implementation evidence covers two families",
            lambda value: evidence_record(
                value,
                "prisoma",
                "prisoma.heldout-quantized",
                "implementation-contract",
            ).__setitem__(
                "paths",
                [
                    "crates/pid-core/src/sxpid.rs",
                    "crates/pid-core/tests/sxpid_exhaustive_oracle.rs",
                ],
            ),
        ),
        (
            "selected inventory scope escalated",
            lambda value: value.__setitem__(
                "inventory_scope",
                "An exhaustive inventory of every historical and current capability.",
            ),
        ),
        (
            "bounded historical integration erased",
            lambda value: consumer(value, "prisoma")[
                "historical_evidence"
            ].clear(),
        ),
        (
            "consumer semantics changed after live authority rebind",
            mutate_reviewed_need_after_live_rebind,
        ),
        (
            "historical evidence changed after live authority rebind",
            mutate_historical_evidence_after_live_rebind,
        ),
        (
            "inventory boundary changed after live authority rebind",
            mutate_inventory_after_live_rebind,
        ),
    ]
    overclaims = (
        "The consumer integration is complete and validated.",
        "This route is certified safe and deployable.",
        "The requirement is fully satisfied.",
        "The implementation meets all consumer needs.",
        "This is ready for mission authorization.",
        "The consumer adapter is integrated and verified.",
    )
    for index, wording in enumerate(overclaims, start=1):
        mutations.append(
            (
                f"affirmative overclaim variant {index}",
                lambda value, claim=wording: requirement(
                    value, "crebain", "crebain.adapter"
                ).__setitem__("need", claim),
            )
        )
    for name, mutation in mutations:
        expect_rejected(name, base_contract, schema, mutation)

    bound_mutations = [
        ("release-scope claim escalation", mutate_release_scope_status),
        ("selected method loses local availability", mutate_method_availability),
        (
            "method constraint changed with a coherent authority rebind",
            mutate_method_constraint_and_rebind,
        ),
        ("assurance family removed", mutate_assurance_coverage),
        (
            "assurance layer semantic escalation",
            mutate_assurance_semantic_escalation,
        ),
        ("historical snapshot identity drift", mutate_snapshot_identity),
    ]
    for name, mutation in bound_mutations:
        expect_bound_mutation_rejected(
            name, base_contract, schema, mutation
        )

    raw_rejections = {
        "duplicate key": b'{"schema":1,"schema":2}\n',
        "nonfinite number": b'{"value":NaN}\n',
        "noncanonical JSON": b'{ "schema": "pid-rs/ecosystem-capabilities" }\n',
        "missing final LF": canonical_bytes(base_contract).rstrip(b"\n"),
    }
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ecosystem-json-self-test-"
    ) as temp:
        for name, raw in raw_rejections.items():
            path = Path(temp) / f"{name.replace(' ', '-')}.json"
            path.write_bytes(raw)
            try:
                CHECKER.load_json(path, canonical=True)
            except CHECKER.EcosystemContractError:
                continue
            raise AssertionError(f"raw JSON mutation did not fail closed: {name}")

    maturity, snapshots, integrations, assurance = CHECKER.validate_contract(
        ROOT, base_contract, schema
    )
    rendered = CHECKER.render_markdown(
        base_contract, maturity, snapshots, integrations, assurance
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ecosystem-markdown-self-test-"
    ) as temp:
        markdown = Path(temp) / "ECOSYSTEM_CAPABILITIES.md"
        CHECKER.check_or_write_markdown(markdown, rendered, write=True)
        markdown.write_text(rendered + "stale\n", encoding="utf-8")
        try:
            CHECKER.check_or_write_markdown(markdown, rendered, write=False)
        except CHECKER.EcosystemContractError:
            pass
        else:
            raise AssertionError("stale generated Markdown did not fail closed")

    total = len(mutations) + len(bound_mutations) + len(raw_rejections) + 1
    print(f"ecosystem capability self-test passed: {total} mutations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
