#!/usr/bin/env python3
"""Hostile self-test for check-zeta-pid-transfer-firewall.py."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-zeta-pid-transfer-firewall.py"
WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
TEX = ROOT / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
MUTATION_EXPECTATIONS = {
    "covariance-overclaim": "COUNTERMODEL.covariance_identity",
    "moment-overclaim": "COUNTERMODEL.inertia_separation",
    "gauge-overclaim": "COUNTERMODEL.congruence_moment_drift",
    "mapping-route-omission": "MAPPING.negative_route_registry",
    "source-record-route-omission": "SOURCE_RECORD.negative_route_registry",
}
EXPECTED_REVIEWED_SOURCE_RECORD = {
    "quantifier_scope": "liminf_T_to_infinity",
    "multiplicity_counted_denominator": "N(T,2T)",
    "c1_star_definition": "sqrt(2)*tan(1/sqrt(2))/(1+(1/sqrt(2))*tan(1/sqrt(2)))",
    "optimized_bound_definition": "2-1/c1_star",
    "optimized_bound_decimal_prefix": "0.672500703679...",
    "reviewed_paper_pdf_sha256": (
        "6792988e6cd0e17690621ce898abd5d534f98407741bc7cb14bbe7d07c77d72f"
    ),
}
EXPECTED_STDOUT_SHA256 = (
    "23f70a7810b8717426dc8f3cdbdfa4dc4bd1998f82223a5fee95258ea753e744"
)
EXPECTED_MAPPING_FIELDS = [
    "M1_domain_to_hermitian",
    "M2_decomposition",
    "M3_positive_semidefinite_part",
    "M4_rank_semantics",
    "M5_positive_index_semantics",
    "M6_coordinates_scale_units",
    "M7_trace_frobenius_total_relation",
    "M8_error_budget",
    "M9_transport_to_claimed_pid_object",
]
EXPECTED_WORKFLOW_SENTINELS = [
    "Split by zero ordinate as $G=A+E$",
    "Proposition 4.1(ii) gives $\\widehat A=P+Q$",
    "0.672500703679...",
    "Absent any one item, the route must abstain.",
    "scripts/check-zeta-pid-transfer-firewall.py",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(*arguments: str, optimized: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", str(CHECKER), *arguments))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def expect_rejection(label: str, expected_code: str, *arguments: str) -> None:
    for optimized in (False, True):
        result = run(*arguments, optimized=optimized)
        require(
            result.returncode == 1,
            f"mutation returned the wrong status ({label}, optimized={optimized}):\n"
            f"{result.stdout}{result.stderr}",
        )
        require(result.stdout == "", f"mutation wrote stdout: {label}")
        expected_stderr = f"zeta-to-PID transfer firewall: {expected_code}\n"
        require(
            result.stderr == expected_stderr,
            f"mutation failed for the wrong reason ({label}, optimized={optimized}):\n"
            f"expected {expected_stderr!r}\nobserved {result.stderr!r}",
        )


def replace_exact_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected one source occurrence")
    return text.replace(old, new, 1)


def main() -> int:
    normal = run()
    optimized = run(optimized=True)
    require(normal.returncode == 0, normal.stdout + normal.stderr)
    require(optimized.returncode == 0, optimized.stdout + optimized.stderr)
    require(normal.stdout == optimized.stdout, "normal and optimized outputs differ")
    require(
        hashlib.sha256(normal.stdout.encode("utf-8")).hexdigest()
        == EXPECTED_STDOUT_SHA256,
        "canonical stdout identity",
    )
    payload = json.loads(normal.stdout)
    require(
        set(payload)
        == {
            "countermodels",
            "format",
            "mapping_decision",
            "mapping_negative_routes",
            "required_mapping_fields",
            "reviewed_source_record",
            "reviewed_source_record_negative_routes",
            "reviewed_source_record_scope",
            "schema_acceptance_is_not_evidence",
            "scope",
            "workflow_section_sha256",
            "workflow_sentinels",
        },
        "output key set",
    )
    require(payload["format"] == "/pid-rs/zeta-pid-transfer-firewall/v1", "format")
    require(payload["scope"] == "negative_controls_and_workflow_only", "scope")
    require(
        payload["mapping_decision"] == "ABSTAIN_NO_PID_MAPPING_SUBMITTED",
        "mapping status",
    )
    require(
        payload["reviewed_source_record_scope"]
        == "local_record_binding_not_external_comparator_replay",
        "reviewed source-record scope",
    )
    require(
        payload["schema_acceptance_is_not_evidence"] is True,
        "schema non-evidence boundary",
    )
    require(
        payload["countermodels"]
        == {
            "covariance_equal": True,
            "independent_mi_ln2_coefficient": "0",
            "parity_mi_ln2_coefficient": "1",
            "same_inertia_different_moments_under_congruence": True,
            "same_moments_different_inertia": True,
        },
        "exact countermodel summary",
    )
    require(
        payload["required_mapping_fields"] == EXPECTED_MAPPING_FIELDS,
        "exact M1--M9 registry",
    )
    require(
        payload["mapping_negative_routes"]
        == [
            *(f"MAPPING.{field}" for field in EXPECTED_MAPPING_FIELDS),
            "MAPPING.circular_atom_embedding",
            "MAPPING.lambda_is_not_ksg_k",
        ],
        "exact mapping mutation registry",
    )
    require(
        payload["reviewed_source_record"] == EXPECTED_REVIEWED_SOURCE_RECORD,
        "reviewed source-record values",
    )
    require(
        payload["reviewed_source_record_negative_routes"]
        == [f"SOURCE_RECORD.{field}" for field in EXPECTED_REVIEWED_SOURCE_RECORD],
        "exact reviewed source-record mutation registry",
    )
    require(
        payload["workflow_section_sha256"]
        == "4818b40530b1cd15daed7093703a980470d102227a8597ed5dc7e38a8acf9744",
        "workflow section identity",
    )
    require(
        payload["workflow_sentinels"] == EXPECTED_WORKFLOW_SENTINELS,
        "workflow sentinel registry",
    )
    for mutation, expected_code in MUTATION_EXPECTATIONS.items():
        expect_rejection(mutation, expected_code, "--mutation", mutation)

    workflow = WORKFLOW.read_text(encoding="utf-8")
    tex = TEX.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="pid-rs-zeta-pid-firewall-") as directory:
        temporary = Path(directory)
        workflow_copy = temporary / "workflow.md"
        tex_copy = temporary / "workflow.tex"

        def reject_source_mutation(
            label: str, expected_code: str, old: str, new: str
        ) -> None:
            mutated_workflow = replace_exact_once(workflow, old, new, label)
            mutated_tex = replace_exact_once(tex, old, new, label)
            workflow_copy.write_text(mutated_workflow, encoding="utf-8")
            tex_copy.write_text(mutated_tex, encoding="utf-8")
            expect_rejection(
                label,
                expected_code,
                "--workflow",
                str(workflow_copy),
                "--tex",
                str(tex_copy),
            )

        reject_source_mutation(
            "wrong-load-bearing-constant",
            "SOURCE_RECORD.optimized_constant_exact_context.count:0",
            "$2-1/c_1^*=$ `0.672500703679...`",
            "$2-1/c_1^*=$ `0.6725008...`",
        )
        reject_source_mutation(
            "missing-M9",
            "MAPPING.M9_source",
            "9. `M9_transport_to_claimed_pid_object`: transport the matrix conclusion back to "
            "the exact\n   functional, estimator, and implementation claimed.",
            "9. `M9_transport_to_claimed_pid_object`: record the matrix conclusion without "
            "transporting it to the claimed object.",
        )
        reject_source_mutation(
            "conflated-decomposition",
            "MATH.typed_chain_conflation",
            "single informal $P+Q+E$ slogan.\n",
            "single informal $P+Q+E$ slogan.\n\n"
            "The shorthand $P+Q+E$ is a complete proof description.\n",
        )
        reject_source_mutation(
            "paper-artifact-digest-drift",
            "SOURCE_RECORD.reviewed_paper_pdf_sha256.count:0",
            "SHA-256 `6792988e6cd0e17690621ce898abd5d534f98407741bc7cb14bbe7d07c77d72f`",
            f"SHA-256 `{'0' * 64}`",
        )
        reject_source_mutation(
            "paper-visible-record-drift",
            "SOURCE_RECORD.reviewed_paper_pdf_sha256.prose_binding:0",
            "- `reviewed_paper_pdf_sha256="
            "6792988e6cd0e17690621ce898abd5d534f98407741bc7cb14bbe7d07c77d72f`",
            f"- `reviewed_paper_pdf_sha256={'0' * 64}`",
        )
        reject_source_mutation(
            "literal-registry-deletion",
            "SOURCE_RECORD.literal_registry.count:0",
            "The publication firewall therefore retains the literal source/PDF sentinels",
            "The publication omits its literal source/PDF sentinels",
        )
        reject_source_mutation(
            "otherwise-unreviewed-section-drift",
            "WORKFLOW.section_sha256",
            "The claimed advance is unconditional and asymptotic.",
            "The claimed advance is unconditional and  asymptotic.",
        )

        mismatched_workflow = replace_exact_once(
            workflow,
            "The claimed advance is unconditional and asymptotic.",
            "The claimed advance is conditionally described.",
            "embedded-byte-mismatch",
        )
        workflow_copy.write_text(mismatched_workflow, encoding="utf-8")
        tex_copy.write_text(tex, encoding="utf-8")
        expect_rejection(
            "embedded-byte-mismatch",
            "WORKFLOW.embedded_bytes",
            "--workflow",
            str(workflow_copy),
            "--tex",
            str(tex_copy),
        )

    print(
        "OK: zeta-to-PID firewall rejected 5 mechanism/record overclaims and 8 "
        "source/publication mutations at exact causal codes in normal and optimized modes"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"zeta-to-PID transfer firewall self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
