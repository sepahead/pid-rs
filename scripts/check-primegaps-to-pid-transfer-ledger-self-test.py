#!/usr/bin/env python3
"""Causal hostile suite for check-primegaps-to-pid-transfer-ledger.py."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-primegaps-to-pid-transfer-ledger.py"
LEDGER = ROOT / "audit/evidence/primegaps-to-pid-transfer-ledger-v1.json"
SCHEMA = ROOT / "audit/schemas/primegaps-to-pid-transfer-ledger-v1.schema.json"
WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
PACKET = ROOT / "claims/SX-CERTIFIED-AVERAGED-PID3-001"
EXPECTED_STDOUT_SHA256 = "852e3373f680631e6cc31eb9ee98c27e82ca699a80d7755e07314fba7d37a59e"
EXPECTED_LEDGER_SHA256 = "18763feaa707ea797d409de7df7e152e77fc778d4bd631c2ca9734790a4c7bda"
EXPECTED_SCHEMA_SHA256 = "842701050fa82edf82691dac2fd5eae7c93806fed7f9c128d1a92255ba1dae47"
EXPECTED_ANCHOR_SHA256 = "78bccc50109c2778d7db5cc8ebf03f49fa1224e5072f347699d517a15956e590"
EXPECTED_LOCAL_BYTE_SHA256 = "c36778ce306c3d33dabe3458a81ff416b24385319b3eeee456d23136fd79a0f9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object expected: {path}")
    return value


def run(
    *,
    optimized: bool,
    ledger: Path = LEDGER,
    schema: Path = SCHEMA,
    workflow: Path = WORKFLOW,
    repository_root: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(
        (
            "-I",
            "-S",
            "-B",
            str(CHECKER),
            "--ledger",
            str(ledger),
            "--schema",
            str(schema),
            "--workflow",
            str(workflow),
            "--repository-root",
            str(repository_root),
        )
    )
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )


def expect_rejection(
    label: str,
    code: str,
    *,
    ledger: Path = LEDGER,
    schema: Path = SCHEMA,
    workflow: Path = WORKFLOW,
    repository_root: Path = ROOT,
) -> None:
    expected_stderr = f"PrimeGaps-to-PID transfer ledger: {code}\n"
    for optimized in (False, True):
        result = run(
            optimized=optimized,
            ledger=ledger,
            schema=schema,
            workflow=workflow,
            repository_root=repository_root,
        )
        require(
            result.returncode == 1,
            f"wrong status ({label}, optimized={optimized}):\n"
            f"{result.stdout}{result.stderr}",
        )
        require(
            result.stdout == "",
            f"rejected mutation wrote stdout ({label}, optimized={optimized})",
        )
        require(
            result.stderr == expected_stderr,
            f"wrong causal code ({label}, optimized={optimized}):\n"
            f"expected {expected_stderr!r}\nobserved {result.stderr!r}",
        )


def write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected one occurrence of {old!r}")
    return text.replace(old, new, 1)


def source_entry(value: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    matches = [
        entry
        for entry in value["source_manifest"]
        if entry["artifact_id"] == artifact_id
    ]
    require(len(matches) == 1, f"source fixture lookup: {artifact_id}")
    return matches[0]


def transfer_entry(value: dict[str, Any], entry_id: str) -> dict[str, Any]:
    matches = [entry for entry in value["transfer_entries"] if entry["id"] == entry_id]
    require(len(matches) == 1, f"transfer fixture lookup: {entry_id}")
    return matches[0]


def main() -> int:
    baseline = run(optimized=False)
    optimized = run(optimized=True)
    require(baseline.returncode == 0, baseline.stdout + baseline.stderr)
    require(optimized.returncode == 0, optimized.stdout + optimized.stderr)
    require(baseline.stderr == optimized.stderr == "", "baseline wrote stderr")
    require(baseline.stdout == optimized.stdout, "normal and optimized outputs differ")
    require(
        hashlib.sha256(baseline.stdout.encode("utf-8")).hexdigest()
        == EXPECTED_STDOUT_SHA256,
        "canonical stdout identity",
    )
    payload = json.loads(baseline.stdout)
    require(
        set(payload)
        == {
            "anchor_count",
            "anchor_registry_sha256",
            "council_independence_scope",
            "council_role_count",
            "decision_id_count",
            "external_artifact_count",
            "external_artifact_custody",
            "format",
            "gate",
            "ledger_sha256",
            "lens_count",
            "lens_registry_sha256",
            "nonclaims",
            "packet_status",
            "repository_artifact_count",
            "repository_byte_registry_sha256",
            "reviewed_source_commit",
            "schema_dialect",
            "schema_sha256",
            "schema_validation_scope",
            "schema_validator_sha256",
            "scope",
            "source_artifact_count",
            "source_preimage_binding_count",
            "transfer_id_count",
        },
        "output key set",
    )
    require(payload["gate"] == "GO", "bounded gate status")
    require(
        payload["scope"] == "ledger_semantics_identity_and_local_byte_custody_only",
        "scope",
    )
    require(payload["ledger_sha256"] == EXPECTED_LEDGER_SHA256, "ledger digest")
    require(payload["schema_sha256"] == EXPECTED_SCHEMA_SHA256, "schema digest")
    require(payload["anchor_registry_sha256"] == EXPECTED_ANCHOR_SHA256, "anchor digest")
    require(
        payload["repository_byte_registry_sha256"] == EXPECTED_LOCAL_BYTE_SHA256,
        "local-byte registry digest",
    )
    require(
        (
            payload["lens_count"],
            payload["transfer_id_count"],
            payload["decision_id_count"],
            payload["council_role_count"],
            payload["external_artifact_count"],
            payload["repository_artifact_count"],
            payload["source_artifact_count"],
            payload["source_preimage_binding_count"],
            payload["anchor_count"],
        )
        == (20, 12, 6, 4, 6, 13, 19, 13, 24),
        "exact registry counts",
    )
    require(
        payload["council_independence_scope"] == "correlated_advisory_only",
        "council boundary",
    )
    require(
        payload["external_artifact_custody"] == "hash_only_not_recovery",
        "external durability boundary",
    )
    require(
        payload["packet_status"] == "proposed_programs_A_through_E_open",
        "packet status",
    )
    require(len(payload["nonclaims"]) == 5, "nonclaim registry")

    ledger_base = load(LEDGER)
    schema_base = load(SCHEMA)
    workflow_base = WORKFLOW.read_text(encoding="utf-8")
    mutation_count = 0

    with tempfile.TemporaryDirectory(prefix="pid-rs-primegaps-ledger-self-test-") as directory:
        temporary = Path(directory)

        def reject_ledger(
            label: str,
            code: str,
            mutate: Callable[[dict[str, Any]], None],
        ) -> None:
            nonlocal mutation_count
            value = copy.deepcopy(ledger_base)
            mutate(value)
            path = temporary / f"{label}.ledger.json"
            write_json(path, value)
            expect_rejection(label, code, ledger=path)
            mutation_count += 1

        def reject_schema(
            label: str,
            code: str,
            mutate: Callable[[dict[str, Any]], None],
        ) -> None:
            nonlocal mutation_count
            value = copy.deepcopy(schema_base)
            mutate(value)
            path = temporary / f"{label}.schema.json"
            write_json(path, value)
            expect_rejection(label, code, schema=path)
            mutation_count += 1

        reject_schema(
            "schema-dialect-drift",
            "SCHEMA.dialect",
            lambda value: value.__setitem__(
                "$schema", "https://json-schema.org/draft/2019-09/schema"
            ),
        )
        reject_schema(
            "schema-mutable-id",
            "SCHEMA.id",
            lambda value: value.__setitem__(
                "$id",
                "https://github.com/sepahead/pid-rs/blob/main/audit/schemas/"
                "primegaps-to-pid-transfer-ledger-v1.schema.json",
            ),
        )
        reject_schema(
            "schema-weakened-source-count",
            "SCHEMA.sha256",
            lambda value: value["properties"]["source_manifest"].__setitem__(
                "minItems", 18
            ),
        )

        schema_duplicate = replace_once(
            SCHEMA.read_text(encoding="utf-8"),
            f'  "$id": "{schema_base["$id"]}",\n',
            f'  "$id": "{schema_base["$id"]}",\n'
            f'  "$id": "{schema_base["$id"]}",\n',
            "schema-duplicate-key",
        )
        schema_duplicate_path = temporary / "schema-duplicate-key.schema.json"
        schema_duplicate_path.write_text(schema_duplicate, encoding="utf-8")
        expect_rejection(
            "schema-duplicate-key", "SCHEMA.duplicate_key", schema=schema_duplicate_path
        )
        mutation_count += 1

        ledger_duplicate = replace_once(
            LEDGER.read_text(encoding="utf-8"),
            '  "council": {\n',
            '  "council": {},\n  "council": {\n',
            "ledger-duplicate-key",
        )
        ledger_duplicate_path = temporary / "ledger-duplicate-key.ledger.json"
        ledger_duplicate_path.write_text(ledger_duplicate, encoding="utf-8")
        expect_rejection(
            "ledger-duplicate-key", "LEDGER.duplicate_key", ledger=ledger_duplicate_path
        )
        mutation_count += 1

        noncanonical_path = temporary / "ledger-noncanonical.ledger.json"
        noncanonical_path.write_text(
            LEDGER.read_text(encoding="utf-8") + "\n", encoding="utf-8"
        )
        expect_rejection(
            "ledger-noncanonical", "LEDGER.canonical_json", ledger=noncanonical_path
        )
        mutation_count += 1

        def swap_lenses(value: dict[str, Any]) -> None:
            value["lens_review"][0], value["lens_review"][1] = (
                value["lens_review"][1],
                value["lens_review"][0],
            )

        reject_ledger("lens-order-swap", "LENS.registry", swap_lenses)

        lens_registry_marker = "#### Lenses 1--10: scientific object and inference contract\n"
        workflow_prefix, marker, workflow_lens_registry = workflow_base.partition(
            lens_registry_marker
        )
        require(marker == lens_registry_marker, "workflow-lens-name: registry marker")
        workflow_mutated = workflow_prefix + marker + replace_once(
            workflow_lens_registry,
            "| 5. Support/reference measure |",
            "| 5. Support and reference measure |",
            "workflow-lens-name",
        )
        workflow_path = temporary / "workflow-lens-name.md"
        workflow_path.write_text(workflow_mutated, encoding="utf-8")
        expect_rejection(
            "workflow-lens-name", "WORKFLOW.lens_registry", workflow=workflow_path
        )
        mutation_count += 1

        reject_ledger(
            "duplicate-transfer-id",
            "ID.transfer_entries.unique",
            lambda value: value["transfer_entries"][1].__setitem__(
                "id", value["transfer_entries"][0]["id"]
            ),
        )
        reject_ledger(
            "wrong-transfer-roster",
            "ID.transfer_entries.roster",
            lambda value: value["transfer_entries"][0].__setitem__(
                "id", "wrong-transfer-id"
            ),
        )
        reject_ledger(
            "duplicate-decision-id",
            "ID.design_decisions.unique",
            lambda value: value["design_decisions"][1].__setitem__(
                "id", value["design_decisions"][0]["id"]
            ),
        )
        reject_ledger(
            "duplicate-source-id",
            "ID.source_manifest.unique",
            lambda value: value["source_manifest"][1].__setitem__(
                "artifact_id", value["source_manifest"][0]["artifact_id"]
            ),
        )
        reject_ledger(
            "duplicate-council-id",
            "ID.council.unique",
            lambda value: value["council"]["roles"][1].__setitem__(
                "role", value["council"]["roles"][0]["role"]
            ),
        )

        def anchor_revision(value: dict[str, Any], revision: str) -> None:
            anchor = value["transfer_entries"][0]["source_anchors"][0]
            anchor["locator"] = anchor["locator"].replace(
                "1faa7b14e82ddebc2772dfb9153922f01b106477", revision
            )

        reject_ledger(
            "github-anchor-blob-main",
            "ANCHOR.github_revision",
            lambda value: anchor_revision(value, "main"),
        )
        reject_ledger(
            "github-anchor-wrong-commit",
            "ANCHOR.github_revision",
            lambda value: anchor_revision(
                value, "0faa7b14e82ddebc2772dfb9153922f01b106477"
            ),
        )
        reject_ledger(
            "github-anchor-wrong-path",
            "ANCHOR.registry_sha256",
            lambda value: value["transfer_entries"][0]["source_anchors"][0].__setitem__(
                "locator",
                value["transfer_entries"][0]["source_anchors"][0]["locator"].replace(
                    "README.md", "README2.md"
                ),
            ),
        )
        reject_ledger(
            "source-anchor-meaning-drift",
            "ANCHOR.registry_sha256",
            lambda value: value["transfer_entries"][0]["source_anchors"][0].__setitem__(
                "meaning", "A weakened and unreviewed source interpretation."
            ),
        )

        reject_ledger(
            "external-durability-overclaim",
            "SCHEMA.instance",
            lambda value: source_entry(value, "primegaps-git-tree").__setitem__(
                "durability", "public-git-object"
            ),
        )
        reject_ledger(
            "external-relative-locator",
            "SCHEMA.instance",
            lambda value: source_entry(value, "primegaps-blueprint-pdf").__setitem__(
                "locator", "blueprint.pdf"
            ),
        )
        reject_ledger(
            "external-digest-drift",
            "SOURCE.external_identity.primegaps-blueprint-pdf",
            lambda value: source_entry(value, "primegaps-blueprint-pdf").__setitem__(
                "sha256", "0" * 64
            ),
        )
        reject_ledger(
            "external-size-drift",
            "SOURCE.external_identity.primegaps-ci-job-log",
            lambda value: source_entry(value, "primegaps-ci-job-log").__setitem__(
                "size_bytes", 33295
            ),
        )
        reject_ledger(
            "external-false-preimage-fields",
            "SOURCE.external_preimage_fields.primegaps-interactive-paper",
            lambda value: source_entry(value, "primegaps-interactive-paper").update(
                {"source_sha256": "0" * 64, "source_size_bytes": 1}
            ),
        )

        reject_ledger(
            "local-preimage-digest-drift",
            "SOURCE.repository_identity.sxpid3-packet-bindings",
            lambda value: source_entry(value, "sxpid3-packet-bindings").__setitem__(
                "source_sha256", "0" * 64
            ),
        )
        reject_ledger(
            "local-current-digest-drift",
            "SOURCE.repository_identity.sxpid3-packet-bindings",
            lambda value: source_entry(value, "sxpid3-packet-bindings").__setitem__(
                "sha256", "0" * 64
            ),
        )

        repository_copy = temporary / "repository-copy"
        packet_copy = repository_copy / "claims/SX-CERTIFIED-AVERAGED-PID3-001"
        packet_copy.parent.mkdir(parents=True)
        shutil.copytree(PACKET, packet_copy)
        bindings_copy = packet_copy / "bindings.md"
        bindings_copy.write_bytes(bindings_copy.read_bytes() + b"\n")
        expect_rejection(
            "local-current-byte-drift",
            "SOURCE.repository_bytes.sxpid3-packet-bindings",
            repository_root=repository_copy,
        )
        mutation_count += 1

        coordinated = copy.deepcopy(ledger_base)
        coordinated_entry = source_entry(coordinated, "sxpid3-packet-bindings")
        coordinated_raw = bindings_copy.read_bytes()
        coordinated_entry["sha256"] = hashlib.sha256(coordinated_raw).hexdigest()
        coordinated_entry["size_bytes"] = len(coordinated_raw)
        coordinated_path = temporary / "coordinated-local-reseal.ledger.json"
        write_json(coordinated_path, coordinated)
        expect_rejection(
            "coordinated-local-reseal",
            "SOURCE.repository_identity.sxpid3-packet-bindings",
            ledger=coordinated_path,
            repository_root=repository_copy,
        )
        mutation_count += 1

        reject_ledger(
            "autoresearch-preserved-overclaim",
            "AUTORESEARCH.preserved_assumptions",
            lambda value: transfer_entry(
                value, "autoresearch-promotion-boundary"
            )["preserved_assumptions"].__setitem__(
                0,
                "Candidate-inaccessible judging is preserved from the reviewed PrimeGaps route.",
            ),
        )
        reject_ledger(
            "autoresearch-changed-assumption-loss",
            "AUTORESEARCH.changed_assumptions",
            lambda value: transfer_entry(
                value, "autoresearch-promotion-boundary"
            )["changed_assumptions"].pop(),
        )
        reject_ledger(
            "autoresearch-source-semantics-overclaim",
            "AUTORESEARCH.source_semantics",
            lambda value: transfer_entry(
                value, "autoresearch-promotion-boundary"
            ).__setitem__(
                "source_semantics",
                "PrimeGaps establishes a preregistered candidate-inaccessible search judge.",
            ),
        )

        reject_ledger(
            "council-independence-overclaim",
            "COUNCIL.registry_sha256",
            lambda value: value["council"]["roles"][1].__setitem__(
                "independence_limit", "This is fully independent external review."
            ),
        )
        reject_ledger(
            "durability-boundary-weakened",
            "SCHEMA.instance",
            lambda value: value.__setitem__(
                "source_manifest_boundary", "External URLs are durable custody."
            ),
        )
        reject_ledger(
            "reviewed-commit-drift",
            "SCHEMA.instance",
            lambda value: value.__setitem__("reviewed_source_commit", "0" * 40),
        )
        reject_ledger(
            "source-manifest-entry-deleted",
            "SCHEMA.instance",
            lambda value: value["source_manifest"].pop(),
        )
        reject_ledger(
            "repository-path-traversal",
            "SCHEMA.instance",
            lambda value: source_entry(value, "sxpid3-packet-bindings").__setitem__(
                "locator", "../bindings.md"
            ),
        )
        reject_ledger(
            "repository-preimage-field-deleted",
            "SCHEMA.instance",
            lambda value: source_entry(value, "sxpid3-packet-bindings").pop(
                "source_sha256"
            ),
        )
        reject_ledger(
            "unreviewed-semantic-drift",
            "LEDGER.sha256",
            lambda value: value["nontransfer_firewalls"].__setitem__(
                0,
                value["nontransfer_firewalls"][0] + " This sentence was not reviewed.",
            ),
        )

    require(mutation_count == 36, f"mutation registry count: {mutation_count}")
    print(
        "OK: PrimeGaps transfer-ledger checker rejected 36 causal schema, roster, "
        "anchor, URI, source-custody, autoresearch, independence, and reseal mutations "
        "in normal and optimized isolated modes"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"PrimeGaps-to-PID transfer ledger self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
