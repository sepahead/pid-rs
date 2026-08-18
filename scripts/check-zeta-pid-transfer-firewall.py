#!/usr/bin/env python3
"""Check exact countermodels and the zeta-to-PID transfer firewall.

This gate supplies negative-control and workflow evidence only.  It does not prove a PID theorem,
validate an estimator, verify the external zeta paper, or establish numerical stability.  The
matrix and distribution examples are exact finite countermodels to specific shortcut inferences.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Final


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
DEFAULT_TEX = ROOT / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
BEGIN = b"\\begin{markdown}\n"
END = b"\\end{markdown}"

MAPPING_REQUIREMENTS: Final[tuple[tuple[str, str], ...]] = (
    ("M1_domain_to_hermitian", "define $F:D\\to\\mathrm{Herm}(d(x))$"),
    ("M2_decomposition", "prove $F(x)=P(x)+Q(x)+E(x)$"),
    ("M3_positive_semidefinite_part", "prove $P(x)\\succeq0$"),
    (
        "M4_rank_semantics",
        "prove the rank bound and a noncircular implication",
    ),
    (
        "M5_positive_index_semantics",
        "prove a positive-index bound for $Q(x)$",
    ),
    (
        "M6_coordinates_scale_units",
        "fix coordinates, scale, units, source order, event semantics, and Möbius convention",
    ),
    (
        "M7_trace_frobenius_total_relation",
        "prove PID-specific trace and Frobenius bounds",
    ),
    (
        "M8_error_budget",
        "enclose every tail, approximation, representation, and numerical error",
    ),
    (
        "M9_transport_to_claimed_pid_object",
        "transport the matrix conclusion back to the exact functional, estimator, and "
        "implementation claimed",
    ),
)
MAPPING_FIELDS: Final[tuple[str, ...]] = tuple(
    field for field, _ in MAPPING_REQUIREMENTS
)
REVIEWED_SOURCE_RECORD_FIELDS: Final[dict[str, str]] = {
    "quantifier_scope": "liminf_T_to_infinity",
    "multiplicity_counted_denominator": "N(T,2T)",
    "c1_star_definition": "sqrt(2)*tan(1/sqrt(2))/(1+(1/sqrt(2))*tan(1/sqrt(2)))",
    "optimized_bound_definition": "2-1/c1_star",
    "optimized_bound_decimal_prefix": "0.672500703679...",
    "reviewed_paper_pdf_sha256": (
        "6792988e6cd0e17690621ce898abd5d534f98407741bc7cb14bbe7d07c77d72f"
    ),
}
EXPECTED_REVIEWED_SOURCE_RECORD_SHA256: Final[str] = (
    "5585c28428fa0ef9a56e2be0cff36e80d8e3e5076f306d4d5cb62c4c80f1304e"
)
PAPER_SHA256: Final[str] = REVIEWED_SOURCE_RECORD_FIELDS["reviewed_paper_pdf_sha256"]
SECTION_HEADING: Final[str] = (
    "### Zeta two-thirds source review: mathematics, methods, process, and the current PID "
    "no-direct-transfer disposition\n"
)
SECTION_END: Final[str] = "\n## AI model operating protocol\n"
EXPECTED_SECTION_SHA256: Final[str] = (
    "d1a1775dc38c04726b0c6f63feeb74e8f0d750e5fde8f3a76cdf041657d4d368"
)
WORKFLOW_SENTINELS: Final[tuple[str, ...]] = (
    "Split by zero ordinate as $G=A+E$",
    "Proposition 4.1(ii) gives $\\widehat A=P+Q$",
    "0.672500703679...",
    "Absent any one item, the route must abstain.",
    "scripts/check-zeta-pid-transfer-firewall.py",
)
MUTATIONS: Final[tuple[str, ...]] = (
    "covariance-overclaim",
    "moment-overclaim",
    "gauge-overclaim",
    "mapping-route-omission",
    "source-record-route-omission",
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _power_of_two_exponent(value: int) -> int:
    require(value > 0 and value & (value - 1) == 0, "MI.non_dyadic_probability_ratio")
    return value.bit_length() - 1


def _log2_fraction(value: Fraction) -> int:
    """Return exact log2 for a positive ratio whose numerator/denominator are powers of two."""

    require(value > 0, "MI.nonpositive_probability_ratio")
    return _power_of_two_exponent(value.numerator) - _power_of_two_exponent(
        value.denominator
    )


Distribution = dict[tuple[int, int, int], Fraction]


def independent_distribution() -> Distribution:
    return {
        (source_one, source_two, target): Fraction(1, 8)
        for source_one in (-1, 1)
        for source_two in (-1, 1)
        for target in (-1, 1)
    }


def parity_distribution() -> Distribution:
    return {
        (source_one, source_two, source_one * source_two): Fraction(1, 4)
        for source_one in (-1, 1)
        for source_two in (-1, 1)
    }


def expectation(
    distribution: Distribution, coordinate_product: tuple[int, ...]
) -> Fraction:
    return sum(
        (
            probability
            * _integer_product(outcome[index] for index in coordinate_product)
            for outcome, probability in distribution.items()
        ),
        start=Fraction(0),
    )


def _integer_product(values: Iterable[int]) -> int:
    product = 1
    for value in values:
        product *= value
    return product


def covariance(distribution: Distribution) -> tuple[tuple[Fraction, ...], ...]:
    require(sum(distribution.values(), start=Fraction(0)) == 1, "DIST.mass")
    means = tuple(expectation(distribution, (index,)) for index in range(3))
    return tuple(
        tuple(
            expectation(distribution, (row, column)) - means[row] * means[column]
            for column in range(3)
        )
        for row in range(3)
    )


def joint_source_target_mi_log2(distribution: Distribution) -> Fraction:
    """Exact coefficient of ln(2) in I((S1,S2);T), computed from dyadic masses."""

    source_mass: dict[tuple[int, int], Fraction] = {}
    target_mass: dict[int, Fraction] = {}
    for (source_one, source_two, target), probability in distribution.items():
        source_key = (source_one, source_two)
        source_mass[source_key] = source_mass.get(source_key, Fraction(0)) + probability
        target_mass[target] = target_mass.get(target, Fraction(0)) + probability
    value = Fraction(0)
    for (source_one, source_two, target), probability in distribution.items():
        ratio = probability / (
            source_mass[(source_one, source_two)] * target_mass[target]
        )
        value += probability * _log2_fraction(ratio)
    return value


@dataclass(frozen=True)
class DiagonalFacts:
    trace: int
    frobenius_squared: int
    positive_index: int
    negative_index: int
    zero_index: int
    rank: int


def diagonal_facts(diagonal: tuple[int, ...]) -> DiagonalFacts:
    positive = sum(value > 0 for value in diagonal)
    negative = sum(value < 0 for value in diagonal)
    zero = sum(value == 0 for value in diagonal)
    return DiagonalFacts(
        trace=sum(diagonal),
        frobenius_squared=sum(value * value for value in diagonal),
        positive_index=positive,
        negative_index=negative,
        zero_index=zero,
        rank=positive + negative,
    )


def mapping_failure_code(
    evidence: dict[str, bool], *, circular: bool, maps_lambda_to_ksg_k: bool
) -> str | None:
    for field in MAPPING_FIELDS:
        if evidence.get(field) is not True:
            return f"MAPPING.{field}"
    if circular:
        return "MAPPING.circular_atom_embedding"
    if maps_lambda_to_ksg_k:
        return "MAPPING.lambda_is_not_ksg_k"
    return None


def reviewed_source_record_failure_code(binding: dict[str, str]) -> str | None:
    for field, expected in REVIEWED_SOURCE_RECORD_FIELDS.items():
        if binding.get(field) != expected:
            return f"SOURCE_RECORD.{field}"
    return None


def check_mapping_policy(mutation: str | None) -> list[str]:
    complete = {field: True for field in MAPPING_FIELDS}
    observed: list[str] = []
    fields = (
        MAPPING_FIELDS[:-1] if mutation == "mapping-route-omission" else MAPPING_FIELDS
    )
    for field in fields:
        candidate = dict(complete)
        candidate[field] = False
        observed.append(
            mapping_failure_code(candidate, circular=False, maps_lambda_to_ksg_k=False)
            or ""
        )
    observed.append(
        mapping_failure_code(complete, circular=True, maps_lambda_to_ksg_k=False) or ""
    )
    observed.append(
        mapping_failure_code(complete, circular=False, maps_lambda_to_ksg_k=True) or ""
    )
    expected = [f"MAPPING.{field}" for field in MAPPING_FIELDS] + [
        "MAPPING.circular_atom_embedding",
        "MAPPING.lambda_is_not_ksg_k",
    ]
    require(observed == expected, "MAPPING.negative_route_registry")
    require(
        mapping_failure_code(complete, circular=False, maps_lambda_to_ksg_k=False)
        is None,
        "MAPPING.complete_schema_fixture",
    )
    return observed


def check_reviewed_source_record(mutation: str | None) -> list[str]:
    record_sha256 = hashlib.sha256(
        json.dumps(
            REVIEWED_SOURCE_RECORD_FIELDS,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    require(
        record_sha256 == EXPECTED_REVIEWED_SOURCE_RECORD_SHA256,
        "SOURCE_RECORD.definition_sha256",
    )
    observed: list[str] = []
    fields = (
        tuple(REVIEWED_SOURCE_RECORD_FIELDS)[:-1]
        if mutation == "source-record-route-omission"
        else tuple(REVIEWED_SOURCE_RECORD_FIELDS)
    )
    for field in fields:
        candidate = dict(REVIEWED_SOURCE_RECORD_FIELDS)
        candidate[field] = "mutated"
        observed.append(reviewed_source_record_failure_code(candidate) or "")
    expected = [f"SOURCE_RECORD.{field}" for field in REVIEWED_SOURCE_RECORD_FIELDS]
    require(observed == expected, "SOURCE_RECORD.negative_route_registry")
    require(
        reviewed_source_record_failure_code(dict(REVIEWED_SOURCE_RECORD_FIELDS))
        is None,
        "SOURCE_RECORD.canonical",
    )
    return observed


def check_workflow(workflow_path: Path, tex_path: Path) -> None:
    workflow = workflow_path.read_bytes()
    tex = tex_path.read_bytes()
    require(tex.count(BEGIN) == 1 and tex.count(END) == 1, "WORKFLOW.enclosure")
    embedded = tex.split(BEGIN, 1)[1].split(END, 1)[0]
    require(embedded == workflow, "WORKFLOW.embedded_bytes")
    text = workflow.decode("utf-8")
    require(text.count(SECTION_HEADING) == 1, "WORKFLOW.section_heading")
    require(text.count(SECTION_END) == 1, "WORKFLOW.section_end")
    section_start = text.index(SECTION_HEADING)
    section_end = text.index(SECTION_END, section_start)
    section = text[section_start:section_end]
    normalized = " ".join(section.split())

    source_record_intro = (
        "The executable firewall binds this visible local reviewed-source record. It is not a "
        "retained trusted statement or an external comparator replay:"
    )
    require(source_record_intro in normalized, "SOURCE_RECORD.visible_intro")
    expected_record_lines = tuple(
        f"- `{field}={value}`" for field, value in REVIEWED_SOURCE_RECORD_FIELDS.items()
    )
    for field, line in zip(
        REVIEWED_SOURCE_RECORD_FIELDS, expected_record_lines, strict=True
    ):
        observed_count = section.count(line)
        require(
            observed_count == 1,
            f"SOURCE_RECORD.{field}.prose_binding:{observed_count}",
        )
    record_lines = tuple(
        line
        for line in section.splitlines()
        if line.startswith("- `")
        and any(
            line.startswith(f"- `{field}=") for field in REVIEWED_SOURCE_RECORD_FIELDS
        )
    )
    require(record_lines == expected_record_lines, "SOURCE_RECORD.prose_order")

    ordered_anchors = (
        ("reviewed_paper_pdf_sha256", f"SHA-256 `{PAPER_SHA256}`"),
        ("multiplicity_denominator", "Write $N(T,2T)$ for all nontrivial zeros"),
        (
            "G_equals_A_plus_E",
            "Split by zero ordinate as $G=A+E$, where $A$ is the contribution",
        ),
        ("Ahat_equals_P_plus_Q", "Proposition 4.1(ii) gives $\\widehat A=P+Q$"),
        (
            "c1_star_definition",
            "$c_1^*=\\sqrt2\\tan(1/\\sqrt2)/(1+(1/\\sqrt2)\\tan(1/\\sqrt2))$",
        ),
        (
            "optimized_constant_exact_context",
            "$2-1/c_1^*=$ `0.672500703679...`",
        ),
        ("quantifier_scope", "These are liminf/epsilon-form constants"),
        (
            "fixed_dirichlet_extension",
            "Theorem E gives the corresponding $H(\\lambda)$",
        ),
        (
            "pid_target",
            "The direct pid-rs comparison target was the accepted bounded claim",
        ),
        ("transfer_audit", "#### Thirty-four-lens PID transfer audit"),
        ("mapping_firewall", "A future PID use must close every item below"),
        (
            "literal_registry",
            "The publication firewall therefore retains the literal source/PDF sentinels",
        ),
        ("abstention", "Absent any one item, the route must abstain."),
    )
    anchor_positions: list[int] = []
    for label, anchor in ordered_anchors:
        observed_count = section.count(anchor)
        require(observed_count == 1, f"SOURCE_RECORD.{label}.count:{observed_count}")
        anchor_positions.append(section.index(anchor))
    require(
        anchor_positions == sorted(anchor_positions),
        "WORKFLOW.zeta_anchor_order",
    )

    require(
        section.count("$2-1/c_1^*=$ `0.672500703679...`") == 1,
        "MATH.optimized_constant",
    )
    require(
        section.count("`0.6725008` is not the reviewed constant") == 1,
        "MATH.wrong_constant_rejection",
    )
    require(
        "This regrouping and the tail transfer are load-bearing; neither may be hidden inside a "
        "single informal $P+Q+E$ slogan." in normalized,
        "MATH.typed_chain",
    )
    require(
        "The shorthand $P+Q+E$ is a complete proof description." not in normalized,
        "MATH.typed_chain_conflation",
    )

    mapping_start_marker = "A future PID use must close every item below"
    mapping_end_marker = "\nThe corresponding executable negative-control plan"
    require(section.count(mapping_start_marker) == 1, "MAPPING.source_start")
    require(section.count(mapping_end_marker) == 1, "MAPPING.source_end")
    mapping_start = section.index(mapping_start_marker)
    mapping_end = section.index(mapping_end_marker, mapping_start)
    mapping_block = " ".join(section[mapping_start:mapping_end].split())
    for index, (field, requirement) in enumerate(MAPPING_REQUIREMENTS, start=1):
        source_anchor = f"{index}. `{field}`: {requirement}"
        require(source_anchor in mapping_block, f"MAPPING.M{index}_source")

    publication_registry = (
        "The publication firewall therefore retains the literal source/PDF sentinels `G=A+E`, "
        "`Ahat=P+Q`, `0.672500703679...`, and `M1-M9-incomplete=>abstain`."
    )
    require(publication_registry in normalized, "WORKFLOW.publication_registry")
    for sentinel in WORKFLOW_SENTINELS:
        require(sentinel in section, f"WORKFLOW.sentinel.{sentinel}")
    observed_section_sha256 = hashlib.sha256(section.encode("utf-8")).hexdigest()
    require(
        observed_section_sha256 == EXPECTED_SECTION_SHA256,
        "WORKFLOW.section_sha256",
    )


def run_checks(
    workflow_path: Path, tex_path: Path, mutation: str | None
) -> dict[str, object]:
    independent = independent_distribution()
    parity = parity_distribution()
    independent_covariance = covariance(independent)
    parity_covariance = covariance(parity)
    if mutation == "covariance-overclaim":
        parity_covariance = ((Fraction(0),),)
    require(
        independent_covariance == parity_covariance, "COUNTERMODEL.covariance_identity"
    )
    require(
        independent_covariance
        == (
            (Fraction(1), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(1)),
        ),
        "COUNTERMODEL.covariance_expected",
    )
    independent_mi = joint_source_target_mi_log2(independent)
    parity_mi = joint_source_target_mi_log2(parity)
    require(independent_mi == 0 and parity_mi == 1, "COUNTERMODEL.mi_separation")

    first = diagonal_facts((3, 4, -3, -4))
    second = diagonal_facts((5, -5, 0, 0))
    if mutation == "moment-overclaim":
        second = first
    require(first.trace == second.trace == 0, "COUNTERMODEL.trace_identity")
    require(
        first.frobenius_squared == second.frobenius_squared == 50,
        "COUNTERMODEL.frobenius_identity",
    )
    require(
        (first.rank, first.positive_index, first.negative_index)
        != (second.rank, second.positive_index, second.negative_index),
        "COUNTERMODEL.inertia_separation",
    )

    original = diagonal_facts((1, -1))
    congruent = diagonal_facts((4, -1))
    if mutation == "gauge-overclaim":
        congruent = original
    require(
        (original.positive_index, original.negative_index)
        == (congruent.positive_index, congruent.negative_index)
        == (1, 1),
        "COUNTERMODEL.congruence_inertia",
    )
    require(
        (original.trace, original.frobenius_squared)
        != (congruent.trace, congruent.frobenius_squared),
        "COUNTERMODEL.congruence_moment_drift",
    )

    mapping_routes = check_mapping_policy(mutation)
    source_record_routes = check_reviewed_source_record(mutation)
    check_workflow(workflow_path, tex_path)
    return {
        "countermodels": {
            "covariance_equal": True,
            "independent_mi_ln2_coefficient": str(independent_mi),
            "parity_mi_ln2_coefficient": str(parity_mi),
            "same_moments_different_inertia": True,
            "same_inertia_different_moments_under_congruence": True,
        },
        "format": "/pid-rs/zeta-pid-transfer-firewall/v1",
        "mapping_decision": "ABSTAIN_NO_PID_MAPPING_SUBMITTED",
        "mapping_negative_routes": mapping_routes,
        "reviewed_source_record": dict(REVIEWED_SOURCE_RECORD_FIELDS),
        "required_mapping_fields": list(MAPPING_FIELDS),
        "reviewed_source_record_negative_routes": source_record_routes,
        "reviewed_source_record_scope": "local_record_binding_not_external_comparator_replay",
        "schema_acceptance_is_not_evidence": True,
        "scope": "negative_controls_and_workflow_only",
        "workflow_section_sha256": EXPECTED_SECTION_SHA256,
        "workflow_sentinels": list(WORKFLOW_SENTINELS),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    parser.add_argument("--mutation", choices=MUTATIONS)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    payload = run_checks(arguments.workflow, arguments.tex, arguments.mutation)
    sys.stdout.write(canonical_json(payload))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"zeta-to-PID transfer firewall: {error}", file=sys.stderr)
        raise SystemExit(1)
