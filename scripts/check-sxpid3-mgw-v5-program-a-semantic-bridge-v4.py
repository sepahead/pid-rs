#!/usr/bin/env python3
"""Check the bounded MGW-v5-to-SxPID3 Program-A semantic bridge.

This checker reconstructs the three-source antichain carrier, order, zeta matrix,
integer Mobius inverse, source-label automorphisms, and Boolean event/count bridge
from small definitions.  It also binds one human-readable source map and one
machine-readable record to fixed bytes.

It does not fetch or interpret the paper, prove that the source map is a faithful
reading, execute Rust, enclose logarithms, verify a parser, or close Programs A--E.
Those boundaries are part of the checked record.
"""

from __future__ import annotations

import ast
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
from typing import Final, Iterable, Mapping, Sequence


if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py "
        "requires CPython 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DOCUMENT_PATH: Final[Path] = (
    ROOT / "claims/SX-CERTIFIED-AVERAGED-PID3-001/source-correspondence-v4.md"
)
RECORD_PATH: Final[Path] = (
    ROOT / "audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json"
)
CONVENTIONS_PATH: Final[Path] = (
    ROOT / "claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
)
PRIMARY_ROUTE_PATH: Final[Path] = (
    ROOT / "scripts/check-sxpid3-bounded-full-coordinates.py"
)
INDEPENDENT_ROUTE_PATH: Final[Path] = (
    ROOT / "scripts/check-sxpid3-all108-independent.py"
)

FORMAT: Final[str] = "pid-rs/sxpid3-mgw-v5-program-a-semantic-bridge/v4"
EXPECTED_DOCUMENT_SHA256: Final[str] = (
    "b4e6fbcdc289e7a8e6c3af42509b568606e61b8908b59661b895bd9ca5eb72cb"
)
EXPECTED_DOCUMENT_BYTES: Final[int] = 33_942
EXPECTED_RECORD_SHA256: Final[str] = (
    "dbc43a78e88d5e35cce5e01ec69f676eef8c68bda2f5eae5994f61d21fe5db24"
)
EXPECTED_RECORD_BYTES: Final[int] = 17_458

EXPECTED_COMPATIBILITY_FILES: Final[dict[str, dict[str, object]]] = {
    "conventions": {
        "bytes": 11_831,
        "path": "claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md",
        "sha256": "2d14bea9d6f0a2d07493ddaf7d89a130f4ad62680319cb9efba465590c2250c7",
    },
    "independent_route": {
        "bytes": 62_762,
        "path": "scripts/check-sxpid3-all108-independent.py",
        "sha256": "8670614f168408110109207b2da746664ea0f3a54196362c1e76be97ad418ad7",
    },
    "primary_route": {
        "bytes": 63_836,
        "path": "scripts/check-sxpid3-bounded-full-coordinates.py",
        "sha256": "d9d1c540930855b31f8190fdb2095d215c736f6f6c3d19c60e2a353923be06d2",
    },
}

EXPECTED_COMPATIBILITY_EDGE: Final[dict[str, object]] = {
    "files": EXPECTED_COMPATIBILITY_FILES,
    "result": "derived_carrier_zeta_and_mobius_equal_frozen_conventions_and_route_registries",
    "scope": "exact_registry_compatibility_not_logical_independence_event_implementation_or_rust_refinement",
}

SOURCE_BITS: Final[tuple[int, ...]] = (1, 2, 4)
EXPECTED_KEYS: Final[tuple[str, ...]] = (
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "01+02",
    "01+04",
    "01+06",
    "02+04",
    "02+05",
    "03+04",
    "03+05",
    "03+06",
    "05+06",
    "01+02+04",
    "03+05+06",
)
EXPECTED_DIGESTS: Final[dict[str, str]] = {
    "carrier_keys_sha256": "eac2b9ff616cce863e48c78fb0398c8ba81a582771f7d68e619c3262929d14a2",
    "event_truth_sha256": "20c8ce30c38c7b6ac57415cfb7f8aa19144b56177bb2d8dc3dc717d193393b19",
    "mobius_sha256": "c1eb37aec49ae76dec3399f0800ac2d0fb41f1779ddb27d13a5fc44664edb460",
    "source_permutations_sha256": "e494891dbedb2bbfbbd0e8afa77e55210de693b9bceb62ee179481efe73a6ef6",
    "zeta_sha256": "07c5e2d47550b6903a4fac886be68f43e9f518153bf735c6f1f2d643d1249d3e",
}

EXPECTED_SOURCE: Final[dict[str, object]] = {
    "acquisition_replay": {
        "commands": [
            "curl --proto '=https' --tlsv1.2 -fL --retry 2 --connect-timeout 15 --max-time 120 -o 2002.03356v5.pdf https://arxiv.org/pdf/2002.03356v5",
            "curl --proto '=https' --tlsv1.2 -fL --retry 2 --connect-timeout 15 --max-time 120 -o 2002.03356v5-source.tar https://export.arxiv.org/e-print/2002.03356v5",
            "shasum -a 256 2002.03356v5.pdf 2002.03356v5-source.tar",
            "wc -c 2002.03356v5.pdf 2002.03356v5-source.tar",
            "test \"$(tar -tf 2002.03356v5-source.tar | grep -Fxc 'apstemplate.tex')\" -eq 1",
            "tar -xOf 2002.03356v5-source.tar apstemplate.tex | shasum -a 256",
            "tar -xOf 2002.03356v5-source.tar apstemplate.tex | wc -c",
        ],
        "completed_on_utc_date": "2026-09-03",
        "result": "freshly_retrieved_pdf_archive_and_unique_member_match_recorded_sha256_and_byte_counts",
        "scope": "owner_controlled_network_replay_not_independent_custody_authentication_or_trusted_time",
    },
    "arxiv": "2002.03356v5",
    "authors": ["Abdullah Makkeh", "Aaron J. Gutknecht", "Michael Wibral"],
    "doi": "10.1103/PhysRevE.103.032149",
    "pdf": {
        "bytes": 1_002_114,
        "sha256": "5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6",
        "url": "https://arxiv.org/pdf/2002.03356v5",
    },
    "source_archive": {
        "bytes": 489_040,
        "sha256": "6420b90ccd5c1e971e19b41c24676b0ed3276aa47f1b3ceadc49bac219bf9584",
        "url": "https://export.arxiv.org/e-print/2002.03356v5",
    },
    "source_member": {
        "bytes": 142_869,
        "path": "apstemplate.tex",
        "sha256": "60ac061c9874149d65d6fab21e627ca66f96d9e4d4990d1ee243632776faaf61",
    },
    "title": "Introducing a differentiable measure of pointwise shared information",
}

EXPECTED_ANCHORS: Final[list[dict[str, object]]] = [
    {
        "id": "MGW-SUBSET-OR",
        "paper_locator": "PDF page 2, Equation (4)",
        "source_lines": [67, 71],
        "local_role": "singleton-branch antichain special case, not one joint-source mask",
        "preserved_assumptions": "finite categorical sources and equality statements for individual realized source values",
        "changed_conventions": "paper subset notation is represented by an antichain of singleton bit masks; numerical units change only at the later bits-to-nats step",
        "prohibited_inference": "Equation (4) does not replace conjunction inside a collection in Equation (6)",
        "required_evidence": "independent source review plus formal event and parser-to-Rust refinement before implementation correspondence is closed",
    },
    {
        "id": "MGW-DNF-EVENT",
        "paper_locator": "PDF page 3, Equations (5)--(8)",
        "source_lines": [73, 87],
        "local_role": "OR across source collections and AND within each collection",
        "preserved_assumptions": "a nonempty finite family of nonempty source collections evaluated at one realized source tuple",
        "changed_conventions": "source-index collections become sorted nonzero masks and their antichain becomes a stable hexadecimal key",
        "prohibited_inference": "branch order symmetry is not source-label permutation invariance",
        "required_evidence": "formal event semantics and compiled implementation refinement; the finite truth table alone checks only the three-source equality kernel",
    },
    {
        "id": "MGW-EXCLUSION-FORM",
        "paper_locator": "PDF page 4, Equation (12)",
        "source_lines": [121, 138],
        "local_role": "equivalent local shared-exclusion probability expression",
        "preserved_assumptions": "the same source event, realized target event, and positive probabilities needed by the logarithmic ratio",
        "changed_conventions": "the exclusion form is retained as a mathematical cross-check and is not the executable event implementation used here",
        "prohibited_inference": "an equivalent population expression is not a Rust refinement proof",
        "required_evidence": "an algebraic correspondence proof and numerical or compiled-code comparison if this alternative form is used operationally",
    },
    {
        "id": "MGW-ZETA-RELATION",
        "paper_locator": "PDF page 5, Equation (13)",
        "source_lines": [143, 154],
        "local_role": "pointwise cumulative equals the sum of atoms at lower-or-equal antichains",
        "preserved_assumptions": "the complete finite antichain carrier and the published redundancy order",
        "changed_conventions": "the repository fixes cumulative nodes as matrix rows, atom nodes as columns, and a declared stable key order",
        "prohibited_inference": "the equation alone does not choose a matrix row/column convention",
        "required_evidence": "concrete carrier completeness and order-orientation checks before a matrix can be identified as the intended zeta transform",
    },
    {
        "id": "MGW-COMPONENT-SPLIT",
        "paper_locator": "PDF page 5, Equations (14a), (15a), and (15b)",
        "source_lines": [158, 174],
        "local_role": "net equals informative minus misinformative; each local component is nonnegative",
        "preserved_assumptions": "the paper-defined pointwise component split on supported finite categorical events",
        "changed_conventions": "paper bits are converted to repository nats by multiplication with the positive constant ln(2)",
        "prohibited_inference": "component nonnegativity does not imply signed-net nonnegativity",
        "required_evidence": "componentwise formula correspondence and sign-preserving unit conversion; net claims require their own subtraction analysis",
    },
    {
        "id": "MGW-AVERAGING",
        "paper_locator": "PDF page 8, Equation (17)",
        "source_lines": [248, 266],
        "local_role": "average every local value with the complete joint source-target law",
        "preserved_assumptions": "expectation over the complete joint source-target distribution and evaluation only where the joint mass is positive",
        "changed_conventions": "population probabilities are replaced by empirical count weights c_z/N for the declared plug-in law",
        "prohibited_inference": "the weight is not the event probability and not uniform over supported keys",
        "required_evidence": "producer and parser refinement showing that decoded counts implement the same complete-joint-law weighting",
    },
    {
        "id": "MGW-ANTICHAIN-ORDER",
        "paper_locator": "PDF page 13, Appendix A order display",
        "source_lines": [562, 570],
        "local_role": "alpha <= beta iff every collection in beta contains one collection in alpha",
        "preserved_assumptions": "the full antichain carrier and the published subset quantifiers defining the redundancy order",
        "changed_conventions": "finite source subsets are encoded as bit masks and nodes are serialized in a project-defined stable key order",
        "prohibited_inference": "reversing the order and transposing zeta is not the declared convention",
        "required_evidence": "carrier-completeness and independently encoded order checks tied to the source statement",
    },
    {
        "id": "MGW-MOBIUS",
        "paper_locator": "PDF page 14, Appendix Equation (A1) and Theorem A.1",
        "source_lines": [597, 607],
        "local_role": "invert the finite down-set zeta relation separately for plus and minus",
        "preserved_assumptions": "finite-poset Mobius inversion on the complete published antichain order, applied componentwise",
        "changed_conventions": "the inverse is constructed by exact rational elimination in the repository's explicit matrix orientation",
        "prohibited_inference": "an inverse matrix does not establish event or implementation correspondence",
        "required_evidence": "two-sided inverse checks plus a separately established link to the frozen carrier, order, and implementation semantics",
    },
    {
        "id": "MGW-COMPONENT-LATTICE-MONOTONICITY",
        "paper_locator": "PDF page 6, Theorem IV.2; proof in Appendix A",
        "source_lines": [208, 211, 638, 652],
        "local_role": "informative and misinformative cumulative functions increase monotonically on the redundancy lattice",
        "preserved_assumptions": "the paper's full redundancy lattice, finite categorical probability model, and separate informative and misinformative cumulatives",
        "changed_conventions": "only notation and the positive bits-to-nats scale change; no theorem strengthening is claimed",
        "prohibited_inference": "do not infer atom nonnegativity or signed-net monotonicity from this theorem",
        "required_evidence": "a source-to-formal theorem correspondence before monotonicity is used as mechanized evidence in this repository",
    },
    {
        "id": "MGW-COMPONENT-ATOM-NONNEGATIVITY",
        "paper_locator": "PDF page 6, Theorem IV.3; proof in Appendix A",
        "source_lines": [212, 215, 797, 806],
        "local_role": "paper theorem for full-lattice pointwise informative and misinformative atoms",
        "preserved_assumptions": "the complete published lattice and the pointwise informative or misinformative component atoms",
        "changed_conventions": "only notation and the positive bits-to-nats scale change; the signed-net difference remains outside the theorem",
        "prohibited_inference": "do not transfer the theorem to net atoms, truncated lattices, or another PID",
        "required_evidence": "publication-to-formal correspondence on the complete carrier before the theorem receives formal-proof credit",
    },
]

EXPECTED_STATUS: Final[dict[str, object]] = {
    "complete_target": "proposed_open",
    "d2_event_count_bridge": "exact_generic_indicator_argument_with_bounded_executable_reconstruction",
    "h1_independent_human_custody": "open",
    "l1_carrier": "exact_fin3_executable_reconstruction_formal_completeness_open",
    "l2_order_zeta_mobius": "exact_fin3_executable_reconstruction_dual_formal_routes_open",
    "program_a": "partial_open",
    "programs_closed": 0,
    "programs_total": 5,
    "s1_source_correspondence": "owner_controlled_source_review_recorded_independent_external_review_open",
}

EXPECTED_BOUNDARIES: Final[list[str]] = [
    "paper_semantics_are_human_read_not_machine_interpreted",
    "external_source_bytes_are_hash_only_not_repository_custody",
    "no_canonical_input_parser_or_unique_reserialization_proof",
    "no_concrete_lean_or_second_solver_closure",
    "no_exact_logarithm_interval_or_magnitude_certificate",
    "no_compiled_rust_or_binary64_refinement",
    "no_population_sampling_estimator_or_application_claim",
    "no_independent_human_review_authentication_or_priority_claim",
]

EXPECTED_HISTORICAL_FALSE_GREEN_COVERAGE: Final[list[dict[str, str]]] = [
    {
        "current_control": "alternate_record_argument_rejected_normal_and_optimized",
        "id": "V1-FG-INPUT-ROUTE",
    },
    {
        "current_control": "canonical_boundary_deletion_resealed_then_semantically_rejected_normal_and_optimized",
        "id": "V1-FG-SCOPE-CUTS",
    },
    {
        "current_control": "canonical_anchor_mutation_resealed_then_semantically_rejected_normal_and_optimized",
        "id": "V1-FG-ANCHOR-SEMANTICS",
    },
    {
        "current_control": "canonical_claim_escalation_resealed_then_semantically_rejected_normal_and_optimized",
        "id": "V1-FG-CLAIM-SEMANTICS",
    },
    {
        "current_control": "canonical_source_title_mutation_resealed_then_semantically_rejected_normal_and_optimized",
        "id": "V1-FG-ROLE-TITLE",
    },
    {
        "current_control": "alternate_source_record_argument_rejected_normal_and_optimized",
        "id": "V2-FG-INPUT-ROUTE-VIA-SOURCE-RECORD",
    },
    {
        "current_control": "canonical_boundary_deletion_resealed_then_semantically_rejected_normal_and_optimized",
        "id": "V2-FG-SCOPE-CUTS-VIA-SOURCE-RECORD",
    },
]

EXPECTED_VALIDATION: Final[dict[str, object]] = {
    "canonical_record_policy": "utf8_lf_canonical_pretty_json_duplicate_keys_rejected_exact_bytes_bound",
    "coordinated_reseal_boundary": "deliberately_accepted_in_isolated_negative_control_no_semantic_or_review_credit",
    "historical_false_green_coverage": EXPECTED_HISTORICAL_FALSE_GREEN_COVERAGE,
    "required_replay_commands": [
        "python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py",
        "python3 -I -S -B -O scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py",
        "python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py",
        "python3 -I -S -B -O scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py",
    ],
    "schema_policy": "no_reusable_untrusted_certificate_schema_claimed_program_c_parser_and_schema_remain_open",
    "self_test_expected_observations": {
        "accepted_coordinated_reseal_boundary_diagnostics": 2,
        "alternate_input_rejections": 4,
        "baseline_executions": 2,
        "compatibility_drift_rejections": 6,
        "document_drift_rejections": 2,
        "record_reseal_rejections": 24,
        "semantic_source_rejections": 12,
    },
}


class CheckError(RuntimeError):
    """The semantic-bridge evidence is inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_regular(path: Path) -> bytes:
    require(path.is_file(), f"missing regular file: {path.relative_to(ROOT)}")
    require(not path.is_symlink(), f"symbolic link rejected: {path.relative_to(ROOT)}")
    return path.read_bytes()


def read_bound_compatibility_file(path: Path, identity: Mapping[str, object]) -> bytes:
    raw = read_regular(path)
    relative = str(path.relative_to(ROOT))
    require(identity["path"] == relative, f"compatibility path changed: {relative}")
    require(
        identity["bytes"] == len(raw), f"compatibility byte length changed: {relative}"
    )
    require(
        identity["sha256"] == sha256_bytes(raw),
        f"compatibility digest changed: {relative}",
    )
    return raw


def literal_assignment(raw: bytes, name: str, label: str) -> object:
    try:
        module = ast.parse(raw.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise CheckError(f"cannot parse compatibility source: {label}") from error
    matches: list[ast.expr] = []
    for statement in module.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
        ):
            matches.append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == name
            and statement.value is not None
        ):
            matches.append(statement.value)
    require(len(matches) == 1, f"{label}: assignment registry changed for {name}")
    try:
        return ast.literal_eval(matches[0])
    except (ValueError, TypeError) as error:
        raise CheckError(f"{label}: {name} is no longer a literal") from error


def sparse_integer_rows(
    matrix: Sequence[Sequence[int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        tuple((column, value) for column, value in enumerate(row) if value)
        for row in matrix
    )


def parse_conventions(
    raw: bytes,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[tuple[int, int], ...], ...]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CheckError("conventions are not UTF-8") from error

    carrier_rows = re.findall(
        r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`\([^`]*\)`\s*\|",
        text,
        flags=re.MULTILINE,
    )
    require(
        [int(index) for index, _key in carrier_rows] == list(range(18)),
        "conventions carrier table changed",
    )
    keys = tuple(key for _index, key in carrier_rows)

    zeta_rows = re.findall(
        r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([01]{18})`\s*\|$",
        text,
        flags=re.MULTILINE,
    )
    require(
        [(int(index), key) for index, key, _signature in zeta_rows]
        == list(enumerate(keys)),
        "conventions zeta row registry changed",
    )
    zeta_signatures = tuple(signature for _index, _key, signature in zeta_rows)

    mobius_rows: dict[int, tuple[tuple[int, int], ...]] = {}
    for index_text, expression in re.findall(
        r"^Pi\[\s*(\d+)\]\s*=\s*(.+)$", text, flags=re.MULTILINE
    ):
        terms = re.findall(r"([+-]?)\s*C\[(\d+)\]", expression)
        residual = re.sub(r"[+-]?\s*C\[\d+\]", "", expression)
        require(not residual.strip(), "conventions Mobius expression grammar changed")
        row_index = int(index_text)
        require(row_index not in mobius_rows, "duplicate conventions Mobius row")
        mobius_rows[row_index] = tuple(
            (int(column), -1 if sign == "-" else 1) for sign, column in terms
        )
    require(set(mobius_rows) == set(range(18)), "conventions Mobius rows changed")
    mobius_sparse = tuple(mobius_rows[index] for index in range(18))
    return keys, zeta_signatures, mobius_sparse


def validate_frozen_compatibility(
    keys: Sequence[str], zeta: Sequence[Sequence[int]], mobius: Sequence[Sequence[int]]
) -> dict[str, object]:
    conventions_raw = read_bound_compatibility_file(
        CONVENTIONS_PATH, EXPECTED_COMPATIBILITY_FILES["conventions"]
    )
    primary_raw = read_bound_compatibility_file(
        PRIMARY_ROUTE_PATH, EXPECTED_COMPATIBILITY_FILES["primary_route"]
    )
    independent_raw = read_bound_compatibility_file(
        INDEPENDENT_ROUTE_PATH, EXPECTED_COMPATIBILITY_FILES["independent_route"]
    )

    key_tuple = tuple(keys)
    zeta_signatures = tuple("".join(str(value) for value in row) for row in zeta)
    mobius_sparse = sparse_integer_rows(mobius)
    convention_keys, convention_zeta, convention_mobius = parse_conventions(
        conventions_raw
    )
    require(convention_keys == key_tuple, "derived carrier differs from conventions")
    require(convention_zeta == zeta_signatures, "derived zeta differs from conventions")
    require(
        convention_mobius == mobius_sparse,
        "derived Mobius inverse differs from conventions",
    )

    require(
        literal_assignment(
            primary_raw,
            "EXPECTED_AUDIT_STABLE_KEYS",
            "primary bounded route",
        )
        == key_tuple,
        "derived carrier differs from primary bounded-route registry",
    )
    require(
        literal_assignment(
            primary_raw, "EXPECTED_ZETA_SIGNATURES", "primary bounded route"
        )
        == zeta_signatures,
        "derived zeta differs from primary bounded-route registry",
    )
    require(
        literal_assignment(
            primary_raw, "EXPECTED_MOBIUS_SPARSE", "primary bounded route"
        )
        == mobius_sparse,
        "derived Mobius inverse differs from primary bounded-route registry",
    )
    require(
        literal_assignment(independent_raw, "EXPECTED_NODE_KEYS", "independent route")
        == key_tuple,
        "derived carrier differs from independent-route registry",
    )
    require(
        literal_assignment(independent_raw, "EXPECTED_ZETA_ONES", "independent route")
        == sum(value for row in zeta for value in row),
        "derived zeta census differs from independent-route registry",
    )
    require(
        literal_assignment(
            independent_raw, "EXPECTED_MOBIUS_NONZERO", "independent route"
        )
        == sum(value != 0 for row in mobius for value in row),
        "derived Mobius census differs from independent-route registry",
    )
    return EXPECTED_COMPATIBILITY_EDGE


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_record(raw: bytes) -> dict[str, object]:
    require(b"\r" not in raw, "record must use LF line endings")
    require(raw.endswith(b"\n"), "record must end with one LF")
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CheckError("record is not UTF-8") from error
    try:
        value = json.loads(decoded, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise CheckError("record is not valid JSON") from error
    require(isinstance(value, dict), "record root must be an object")
    require(
        raw == json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        "record is not canonical pretty JSON",
    )
    return value


def require_keys(value: Mapping[str, object], keys: Iterable[str], label: str) -> None:
    expected = set(keys)
    observed = set(value)
    require(
        observed == expected,
        f"{label} keys changed: expected={sorted(expected)!r}, observed={sorted(observed)!r}",
    )


def mask_subset(left: int, right: int) -> bool:
    return left & right == left


def is_antichain(candidate: Sequence[int]) -> bool:
    return all(
        not mask_subset(left, right) and not mask_subset(right, left)
        for left, right in itertools.combinations(candidate, 2)
    )


def generate_antichains() -> tuple[tuple[int, ...], ...]:
    masks = tuple(range(1, 1 << len(SOURCE_BITS)))
    generated: list[tuple[int, ...]] = []
    for selector in range(1, 1 << len(masks)):
        candidate = tuple(
            mask for index, mask in enumerate(masks) if selector & (1 << index)
        )
        if is_antichain(candidate):
            generated.append(candidate)
    return tuple(sorted(generated, key=lambda candidate: (len(candidate), candidate)))


def stable_key(antichain: Sequence[int]) -> str:
    return "+".join(f"{mask:02x}" for mask in antichain)


def antichain_le(left: Sequence[int], right: Sequence[int]) -> bool:
    return all(any(mask_subset(a, b) for a in left) for b in right)


def invert_integer_matrix(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    size = len(matrix)
    require(
        size > 0 and all(len(row) == size for row in matrix),
        "zeta matrix is not square",
    )
    augmented = [
        [Fraction(value) for value in row]
        + [Fraction(int(row_index == column_index)) for column_index in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = next(
            (row for row in range(column, size) if augmented[row][column]), None
        )
        require(pivot is not None, "zeta matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(size):
            if row == column or not augmented[row][column]:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_entry
                for value, pivot_entry in zip(
                    augmented[row], augmented[column], strict=True
                )
            ]
    inverse: list[list[int]] = []
    for row in augmented:
        tail = row[size:]
        require(
            all(value.denominator == 1 for value in tail),
            "Mobius inverse is not integral",
        )
        inverse.append([int(value) for value in tail])
    return inverse


def multiply(
    left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]
) -> list[list[int]]:
    return [
        [
            sum(left[row][k] * right[k][column] for k in range(len(right)))
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def identity(size: int) -> list[list[int]]:
    return [[int(row == column) for column in range(size)] for row in range(size)]


def mask_matches(mask: int, match: Sequence[bool]) -> bool:
    selected = [match[index] for index, bit in enumerate(SOURCE_BITS) if mask & bit]
    require(bool(selected), "zero source mask reached event evaluator")
    return all(selected)


def source_event(antichain: Sequence[int], match: Sequence[bool]) -> bool:
    return any(mask_matches(mask, match) for mask in antichain)


def permute_mask(mask: int, permutation: Sequence[int]) -> int:
    result = 0
    for old_index, new_index in enumerate(permutation):
        if mask & SOURCE_BITS[old_index]:
            result |= SOURCE_BITS[new_index]
    return result


def permute_match(
    match: Sequence[bool], permutation: Sequence[int]
) -> tuple[bool, ...]:
    result = [False] * len(SOURCE_BITS)
    for old_index, new_index in enumerate(permutation):
        result[new_index] = match[old_index]
    return tuple(result)


def first_witness(
    antichains: Sequence[Sequence[int]],
    left,
    right,
) -> dict[str, object]:
    for antichain in antichains:
        for match in itertools.product((False, True), repeat=len(SOURCE_BITS)):
            left_value = bool(left(antichain, match))
            right_value = bool(right(antichain, match))
            if left_value != right_value:
                return {
                    "antichain": stable_key(antichain),
                    "correct": left_value,
                    "match": "".join("1" if value else "0" for value in match),
                    "mutant": right_value,
                }
    raise CheckError("semantic mutant has no distinguishing witness")


def derive() -> tuple[dict[str, object], dict[str, object]]:
    antichains = generate_antichains()
    keys = tuple(stable_key(antichain) for antichain in antichains)
    require(keys == EXPECTED_KEYS, "generated Fin-3 antichain carrier changed")
    require(len(set(keys)) == 18, "carrier is not 18 unique stable keys")

    zeta = [
        [int(antichain_le(column, row)) for column in antichains] for row in antichains
    ]
    mobius = invert_integer_matrix(zeta)
    matrix_identity = identity(len(antichains))
    require(multiply(mobius, zeta) == matrix_identity, "MZ is not the identity")
    require(multiply(zeta, mobius) == matrix_identity, "ZM is not the identity")

    event_truth: list[dict[str, object]] = []
    target_truth: list[dict[str, object]] = []
    for antichain in antichains:
        for match in itertools.product((False, True), repeat=len(SOURCE_BITS)):
            event = source_event(antichain, match)
            event_truth.append(
                {
                    "event": event,
                    "key": stable_key(antichain),
                    "match": "".join("1" if value else "0" for value in match),
                }
            )
            for target_match in (False, True):
                intersection = event and target_match
                require(
                    int(intersection) <= int(event),
                    "target intersection exceeds source event",
                )
                require(
                    int(intersection) <= int(target_match),
                    "target intersection exceeds target event",
                )
                target_truth.append(
                    {
                        "event": event,
                        "intersection": intersection,
                        "key": stable_key(antichain),
                        "match": "".join("1" if value else "0" for value in match),
                        "target_match": target_match,
                    }
                )

    for antichain in antichains:
        require(
            source_event(antichain, (True, True, True)),
            f"keyed row is not anchored for {stable_key(antichain)}",
        )

    permutation_rows: list[dict[str, object]] = []
    for permutation in itertools.permutations(range(len(SOURCE_BITS))):
        mapping: dict[str, str] = {}
        transformed_antichains: list[tuple[int, ...]] = []
        for antichain in antichains:
            transformed = tuple(
                sorted(permute_mask(mask, permutation) for mask in antichain)
            )
            require(
                is_antichain(transformed),
                "source permutation did not preserve antichains",
            )
            transformed_antichains.append(transformed)
            mapping[stable_key(antichain)] = stable_key(transformed)
            for match in itertools.product((False, True), repeat=len(SOURCE_BITS)):
                require(
                    source_event(antichain, match)
                    == source_event(transformed, permute_match(match, permutation)),
                    "source permutation did not preserve event truth",
                )
        require(
            set(transformed_antichains) == set(antichains),
            "source permutation is not a carrier bijection",
        )
        for left in antichains:
            mapped_left = tuple(
                sorted(permute_mask(mask, permutation) for mask in left)
            )
            for right in antichains:
                mapped_right = tuple(
                    sorted(permute_mask(mask, permutation) for mask in right)
                )
                require(
                    antichain_le(left, right)
                    == antichain_le(mapped_left, mapped_right),
                    "source permutation did not preserve the order",
                )
        permutation_rows.append({"map": mapping, "permutation": list(permutation)})

    def within_or(antichain: Sequence[int], match: Sequence[bool]) -> bool:
        return any(
            any(match[index] for index, bit in enumerate(SOURCE_BITS) if mask & bit)
            for mask in antichain
        )

    def across_and(antichain: Sequence[int], match: Sequence[bool]) -> bool:
        return all(mask_matches(mask, match) for mask in antichain)

    event_witnesses = {
        "across_branches_and_instead_of_or": first_witness(
            antichains, source_event, across_and
        ),
        "equation_4_subset_or_substituted_for_equation_6_collection_and": first_witness(
            antichains, source_event, within_or
        ),
        "within_collection_or_instead_of_and": first_witness(
            antichains, source_event, within_or
        ),
    }

    order_witness = None
    for left in antichains:
        for right in antichains:
            if antichain_le(left, right) != antichain_le(right, left):
                order_witness = {
                    "left": stable_key(left),
                    "left_le_right": antichain_le(left, right),
                    "right": stable_key(right),
                    "right_le_left": antichain_le(right, left),
                }
                break
        if order_witness is not None:
            break
    require(order_witness is not None, "order-reversal witness is absent")

    derived = {
        "counts": {
            "antichains": len(antichains),
            "event_truth_cases": len(event_truth),
            "mobius_nonzero_entries": sum(
                value != 0 for row in mobius for value in row
            ),
            "nonzero_source_masks": (1 << len(SOURCE_BITS)) - 1,
            "order_pairs": sum(value for row in zeta for value in row),
            "source_label_permutations": len(permutation_rows),
            "target_intersection_truth_cases": len(target_truth),
            "zeta_entries": len(antichains) ** 2,
        },
        "digests": {
            "carrier_keys_sha256": sha256_bytes(canonical_json(list(keys))),
            "event_truth_sha256": sha256_bytes(canonical_json(event_truth)),
            "mobius_sha256": sha256_bytes(canonical_json(mobius)),
            "source_permutations_sha256": sha256_bytes(
                canonical_json(permutation_rows)
            ),
            "zeta_sha256": sha256_bytes(canonical_json(zeta)),
        },
        "generic_count_argument": {
            "coefficient_facts": [
                "indicator(E and T) <= indicator(E)",
                "indicator(E and T) <= indicator(T)",
                "the keyed positive row has all three indicators equal to one",
            ],
            "conclusion": "for arbitrary nonnegative row counts with a positive keyed row: 0<c_z<=V<=U<=N and V<=T_z<=N",
            "scope": "all finite categorical row sets because event membership depends only on the three equality bits and target equality bit",
        },
        "keys": list(keys),
        "witnesses": {
            **event_witnesses,
            "equal_supported_key_weighting_instead_of_count_weighting": {
                "correct_weighted_average": "1/3",
                "counts": [2, 1],
                "equal_key_average_mutant": "1/2",
                "local_values": [0, 1],
            },
            "omitted_target_intersection": {
                "correct_intersection": False,
                "event": True,
                "key": "01",
                "match": "100",
                "mutant_uses_event_without_target": True,
                "target_match": False,
            },
            "reversed_order": order_witness,
        },
    }
    require(derived["digests"] == EXPECTED_DIGESTS, "derived digest registry changed")
    require(
        derived["counts"]
        == {
            "antichains": 18,
            "event_truth_cases": 144,
            "mobius_nonzero_entries": 65,
            "nonzero_source_masks": 7,
            "order_pairs": 129,
            "source_label_permutations": 6,
            "target_intersection_truth_cases": 288,
            "zeta_entries": 324,
        },
        "derived finite census changed",
    )
    compatibility_edge = validate_frozen_compatibility(keys, zeta, mobius)
    return derived, compatibility_edge


def validate_record(
    record: dict[str, object],
    document_raw: bytes,
    derived: dict[str, object],
    compatibility_edge: dict[str, object],
) -> None:
    require_keys(
        record,
        (
            "anchors",
            "boundaries",
            "compatibility_edge",
            "derivation",
            "document",
            "format",
            "primary_source",
            "scope",
            "status",
            "validation",
        ),
        "record",
    )
    require(record["format"] == FORMAT, "record format changed")
    require(
        record["primary_source"] == EXPECTED_SOURCE, "primary-source identity changed"
    )
    require(record["anchors"] == EXPECTED_ANCHORS, "source-anchor map changed")
    require(record["status"] == EXPECTED_STATUS, "claim/program status changed")
    require(record["boundaries"] == EXPECTED_BOUNDARIES, "evidence boundaries changed")
    require(
        record["compatibility_edge"] == compatibility_edge,
        "frozen compatibility edge changed",
    )
    require(record["validation"] == EXPECTED_VALIDATION, "validation contract changed")
    require(record["derivation"] == derived, "recorded exact derivation changed")
    require(
        record["scope"]
        == {
            "pid": "categorical Makkeh--Gutknecht--Wibral shared exclusions only",
            "source_count": 3,
            "source_alphabet_cardinalities": "arbitrary positive finite for the generic equality-kernel/count argument",
            "target_cardinality": "arbitrary positive finite for the generic equality-kernel/count argument",
            "units": "paper bits mapped to repository nats by multiplication with ln(2)",
        },
        "scope changed",
    )
    require(
        record["document"]
        == {
            "bytes": len(document_raw),
            "path": "claims/SX-CERTIFIED-AVERAGED-PID3-001/source-correspondence-v4.md",
            "sha256": sha256_bytes(document_raw),
        },
        "document binding changed",
    )


def main() -> int:
    require(
        len(sys.argv) == 1,
        "canonical checker accepts no alternate input paths or arguments",
    )
    document_raw = read_regular(DOCUMENT_PATH)
    record_raw = read_regular(RECORD_PATH)
    require(
        len(document_raw) == EXPECTED_DOCUMENT_BYTES,
        "source-correspondence document byte length changed",
    )
    require(
        sha256_bytes(document_raw) == EXPECTED_DOCUMENT_SHA256,
        "source-correspondence document digest changed",
    )
    require(
        len(record_raw) == EXPECTED_RECORD_BYTES,
        "semantic-bridge record byte length changed",
    )
    require(
        sha256_bytes(record_raw) == EXPECTED_RECORD_SHA256,
        "semantic-bridge record digest changed",
    )
    record = load_record(record_raw)
    derived, compatibility_edge = derive()
    validate_record(record, document_raw, derived, compatibility_edge)
    print(
        "SxPID3 MGW-v5 Program-A semantic bridge v4: PASS "
        "(18 nodes, 129 order pairs, 324 zeta entries, 65 nonzero Mobius entries, "
        "6 source permutations; 3 frozen-registry compatibility files; "
        "Program A partial/open; Programs closed 0/5)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as error:
        print(
            f"ERROR: SxPID3 MGW-v5 Program-A semantic bridge v4: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
