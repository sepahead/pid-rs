#!/usr/bin/env python3
"""Mutation self-test for check-citation-edge-countermodel.py."""

from __future__ import annotations

from collections.abc import Callable
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-citation-edge-countermodel.py"
WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
TEX = ROOT / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
APPLICATION_RECORD = ROOT / "audit/evidence/x-thread-citation-edge-application.json"
SOURCE_MANIFEST = ROOT / "audit/evidence/x-thread-citation-source-manifest.json"


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def expect_rejection(label: str, *arguments: str) -> None:
    result = run(*arguments)
    require(result.returncode != 0, f"mutation survived: {label}\n{result.stdout}{result.stderr}")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_application_case(
    application_path: Path,
    manifest_path: Path,
    application: dict[str, object],
    manifest: dict[str, object],
) -> None:
    manifest_raw = canonical_bytes(manifest)
    manifest_path.write_bytes(manifest_raw)
    application["source_manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    application_path.write_bytes(canonical_bytes(application))


def object_by_id(items: object, field: str, identifier: str) -> dict[str, object]:
    require(isinstance(items, list), f"{field} collection is not an array")
    matches = [item for item in items if isinstance(item, dict) and item.get(field) == identifier]
    require(len(matches) == 1, f"expected one {field}={identifier!r}")
    return matches[0]


def main() -> int:
    canonical = run()
    require(canonical.returncode == 0, canonical.stdout + canonical.stderr)
    payload = json.loads(canonical.stdout)
    require(payload["invalid_transfer_witnessed"] is True, "canonical witness was not reported")
    require(payload["scope"] == "local_exact_sequence_inference_only", "scope drifted")
    require(
        payload["application_record_id"] == "X-VECTOR-BUNDLE-CITATION-EDGE-001",
        "application record was not reported",
    )
    require(
        payload["equation_27_disposition"] == "FALSE_UNDER_RECORDED_SOURCE_PREMISES",
        "equation (27) disposition drifted",
    )
    require(
        payload["blast_radius_state"] == "DOWNSTREAM_PROOF_ROUTE_REOPENED",
        "blast-radius state drifted",
    )

    for mutation in ("bind-adjacent-arrow", "collapse-middle", "break-exactness"):
        expect_rejection(mutation, "--mutation", mutation)

    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    tex_text = TEX.read_text(encoding="utf-8")
    application_value = json.loads(APPLICATION_RECORD.read_text(encoding="utf-8"))
    manifest_value = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pid-rs-citation-edge-self-test-") as directory:
        temporary = Path(directory)
        workflow_copy = temporary / "workflow.md"
        tex_copy = temporary / "workflow.tex"
        application_copy = temporary / "application.json"
        manifest_copy = temporary / "manifest.json"

        workflow_copy.write_text(
            workflow_text.replace("Citation-edge type check", "Citation edge removed", 1),
            encoding="utf-8",
        )
        tex_copy.write_text(tex_text, encoding="utf-8")
        expect_rejection(
            "stale-embedded-markdown",
            "--workflow",
            str(workflow_copy),
            "--tex",
            str(tex_copy),
        )

        removed_field = "Named source arrow (domain -> codomain):"
        workflow_copy.write_text(workflow_text.replace(removed_field, "Source arrow:", 1), encoding="utf-8")
        tex_copy.write_text(tex_text.replace(removed_field, "Source arrow:", 1), encoding="utf-8")
        expect_rejection(
            "missing-source-arrow-field",
            "--workflow",
            str(workflow_copy),
            "--tex",
            str(tex_copy),
        )

        for label, retained_text in (
            ("missing-corrected-equation-disposition", "Equation (27) is therefore false"),
            ("missing-distinct-proof-preservation", "materially distinct valid proof or solution"),
            ("missing-correlated-model-warning", "Repeated passes by the same model"),
            (
                "missing-lean-countermodel-binding",
                "audit/formal/lean-citation-edge/PidCitationEdgeCountermodel.lean",
            ),
        ):
            workflow_copy.write_text(
                workflow_text.replace(retained_text, f"removed-{label}", 1),
                encoding="utf-8",
            )
            tex_copy.write_text(
                tex_text.replace(retained_text, f"removed-{label}", 1),
                encoding="utf-8",
            )
            expect_rejection(
                label,
                "--workflow",
                str(workflow_copy),
                "--tex",
                str(tex_copy),
            )

        def reject_application_mutation(
            label: str,
            mutate: Callable[[dict[str, object], dict[str, object]], None],
        ) -> None:
            application = copy.deepcopy(application_value)
            manifest = copy.deepcopy(manifest_value)
            mutate(application, manifest)
            write_application_case(application_copy, manifest_copy, application, manifest)
            expect_rejection(
                label,
                "--application-record",
                str(application_copy),
                "--source-manifest",
                str(manifest_copy),
            )

        def neighboring_arrow_swap(application: dict[str, object], _: dict[str, object]) -> None:
            binding = object_by_id(
                application["predicate_bindings"],
                "binding_id",
                "ABH-T7223-RIGHT-SURJECTIVE",
            )
            binding["source_arrow_id"] = "ABH-T7223-LEFT-NU"

        reject_application_mutation("neighboring-arrow-swap", neighboring_arrow_swap)

        def remove_source_span(_: dict[str, object], manifest: dict[str, object]) -> None:
            artifact = object_by_id(manifest["artifacts"], "artifact_id", "abh-2306.04631v3")
            artifact_spans = artifact["spans"]
            require(isinstance(artifact_spans, list), "ABH spans are not an array")
            artifact["spans"] = [
                span
                for span in artifact_spans
                if not isinstance(span, dict)
                or span.get("span_id") != "abh-theorem-7.2.2-point-3"
            ]

        reject_application_mutation("source-span-removal", remove_source_span)

        def reverse_arrow(application: dict[str, object], _: dict[str, object]) -> None:
            arrow = object_by_id(
                application["local_arrows"],
                "arrow_id",
                "DRAFT-EQ27-NU-SPECIALIZATION",
            )
            domain = arrow["domain"]
            codomain = arrow["codomain"]
            arrow["domain"] = codomain
            arrow["codomain"] = domain
            arrow["signature"] = f"{codomain} -> {domain}"

        reject_application_mutation("arrow-reversal", reverse_arrow)

        def remove_hypothesis(application: dict[str, object], _: dict[str, object]) -> None:
            hypotheses = application["hypotheses"]
            require(isinstance(hypotheses, list), "hypotheses are not an array")
            application["hypotheses"] = [
                hypothesis
                for hypothesis in hypotheses
                if not isinstance(hypothesis, dict)
                or hypothesis.get("hypothesis_id") != "H-RSO-COMPATIBLE-PAIR"
            ]

        reject_application_mutation("missing-hypothesis", remove_hypothesis)

        def false_equation_disposition(application: dict[str, object], _: dict[str, object]) -> None:
            conclusion = application["conclusion"]
            require(isinstance(conclusion, dict), "conclusion is not an object")
            conclusion["equation_disposition"] = "SUPPORTED"

        reject_application_mutation("false-equation-disposition", false_equation_disposition)

        def source_digest_drift(
            application: dict[str, object], manifest: dict[str, object]
        ) -> None:
            artifact = object_by_id(manifest["artifacts"], "artifact_id", "abh-2306.04631v3")
            artifact["sha256"] = "0" * 64
            binding = object_by_id(
                application["source_bindings"], "artifact_id", "abh-2306.04631v3"
            )
            binding["sha256"] = "0" * 64

        reject_application_mutation("source-digest-drift", source_digest_drift)

        def source_page_drift(_: dict[str, object], manifest: dict[str, object]) -> None:
            artifact = object_by_id(manifest["artifacts"], "artifact_id", "abh-2306.04631v3")
            span = object_by_id(artifact["spans"], "span_id", "abh-theorem-7.2.1")
            span["page_start"] = 69

        reject_application_mutation("source-page-drift", source_page_drift)

    print("OK: citation-edge countermodel checker rejected 16/16 mutations")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"citation-edge countermodel self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
