#!/usr/bin/env python3
"""Generate and check the concise PID-only mathematical audit protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-pid-mathematical-audit-protocol.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
CATALOG = "method-catalog.json"
CATALOG_SCHEMA = "audit/schemas/method-catalog.schema.json"
ERRATA = "audit/source-errata.json"
ERRATA_SCHEMA = "audit/schemas/source-errata.schema.json"
ASSURANCE = "audit/evidence/assurance-registry-typed-view-v1.json"
ASSURANCE_SCHEMA = "audit/schemas/assurance-registry-typed-view-v1.schema.json"
VIEW = "audit/evidence/pid-mathematical-audit-protocol-v1.json"
VIEW_SCHEMA = "audit/schemas/pid-mathematical-audit-protocol-v1.schema.json"
MARKDOWN = "PID_MATHEMATICAL_AUDIT_PROTOCOL.md"
GENERATOR = "scripts/check-pid-mathematical-audit-protocol.py"
INDEPENDENCE_DIMENSIONS = (
    "semantic",
    "implementation",
    "custody",
    "institutional",
    "data",
)


class ProtocolError(RuntimeError):
    """The PID-only protocol is stale or invalid."""


def load_schema_validator() -> tuple[type[ValueError], Any]:
    path = ROOT / "scripts/json_schema_subset.py"
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit("JSON-schema validator is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        source = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            source.extend(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size
    ):
        raise SystemExit("JSON-schema validator changed during exact-source read")
    module = types.ModuleType("pid_protocol_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source), str(path), "exec", dont_inherit=True, optimize=sys.flags.optimize
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


SchemaValidationError, validate_json_schema = load_schema_validator()


OBJECT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "mgw-categorical-shared-exclusions",
        "label": "MGW categorical shared exclusions",
        "construction_kind": "paper-defined finite-categorical measure and PID",
        "reference_ids": ("makkeh-2021",),
        "construction_id": "mgw-categorical-shared-exclusions",
        "method_ids": ("shared-exclusions.categorical",),
        "scientific_object": "Pointwise informative and misinformative shared-exclusion quantities, their signed empirical joint-law averages, and categorical PID atoms.",
        "domain_support": "Fixed finite categorical alphabets; empirical rows define the plug-in joint PMF.",
        "units": "pid-rs outputs nats; paper values may require an explicit unit conversion.",
        "sample_role": "The supplied categorical rows define the empirical distribution evaluated by the plug-in functional.",
        "acceptance_obligations": (
            "Bind the exact category encoding, empirical PMF, source antichain, target, atom convention, and units.",
            "Check pointwise informative/misinformative terms, averaging, and Mobius reconstruction on declared finite fixtures.",
        ),
        "boundaries": (
            "Do not transfer a value, theorem, or implementation claim to Ehrlich continuous shared exclusions, Schick-Poland general measure theory, or Williams-Beer I_min.",
            "Finite-fixture and exact-algebra evidence is not population calibration or application validity.",
        ),
    },
    {
        "id": "gutknecht-parthood-formal-logic",
        "label": "Gutknecht parthood and formal logic",
        "construction_kind": "paper-defined conceptual and formal foundation",
        "reference_ids": ("gutknecht-2021",),
        "construction_id": None,
        "method_ids": (
            "validation.foundational-shared-exclusions-audit",
            "validation.two-source-sxpid-count-atom-bridge",
        ),
        "scientific_object": "Parthood and formal-logic structures for information decomposition and the redundancy lattice.",
        "domain_support": "Formal/conceptual objects under the paper's stated premises; no standalone sampling model is introduced by this index.",
        "units": "Not applicable to the formal structure itself; linked numerical constructions retain their own units.",
        "sample_role": "None at the formal-object layer; executable fixtures are separately scoped evidence.",
        "acceptance_obligations": (
            "State the exact formal proposition and map every repository definition to it before crediting a proof or executable check.",
            "Keep the source-to-formal and formal-to-executable correspondence edges separate.",
        ),
        "boundaries": (
            "This source is not by itself a numerical estimator or a mapping theorem among categorical, continuous, and general-measure constructions.",
            "A formal theorem does not automatically prove source transcription, Rust refinement, binary64 behavior, or application validity.",
        ),
    },
    {
        "id": "schick-poland-general-measure",
        "label": "Schick-Poland proposed general measure construction",
        "construction_kind": "paper-proposed measure-theoretic construction",
        "reference_ids": ("schick-poland-2021",),
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "method_ids": ("unsupported.mixed-support-continuous-pid",),
        "scientific_object": "Auxiliary-indicator, regular-conditional-probability, and Radon-Nikodym construction for a finite source family under stated Radon/Borel premises.",
        "domain_support": "The paper proposes discrete, continuous, and mixed coverage under its stated measure-theoretic premises; pid-rs leaves recorded pointwise/version obligations open.",
        "units": "No pid-rs numerical output; source conventions must be checked before any future implementation.",
        "sample_role": "No implemented estimator or row-level evaluation role exists in pid-rs.",
        "acceptance_obligations": (
            "Resolve or explicitly retain every version-selection, normalization, representation, and topological obligation in the source-errata registry.",
            "Require a separate mapping theorem before claiming recovery of MGW categorical or Ehrlich continuous objects.",
        ),
        "boundaries": (
            "pid-rs does not implement this construction.",
            "Reviewer-derived open obligations are not author-confirmed errata and do not prove the proposed construction false.",
        ),
    },
    {
        "id": "ehrlich-continuous-shared-exclusions",
        "label": "Ehrlich continuous shared exclusions",
        "construction_kind": "paper-defined analytic functional and kNN estimator",
        "reference_ids": ("ehrlich-2024",),
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "method_ids": (
            "shared-exclusions.continuous-report",
            "shared-exclusions.continuous-raw",
            "shared-exclusions.continuous-heuristics",
            "validation.csxpid-reference-code",
        ),
        "scientific_object": "Gauge-dependent purely continuous shared-exclusions functional and source-disjunction nearest-neighbor estimator.",
        "domain_support": "Purely continuous full-dimensional population laws under explicit support premises; sample diagnostics cannot prove those population premises.",
        "units": "pid-rs evaluates and reports nats.",
        "sample_role": "Rows are the estimator sample after any separately declared preprocessing; support remains a population declaration.",
        "acceptance_obligations": (
            "Bind gauge, metric, k, strict/inclusive count conventions, support contract, units, and all source-correction candidates.",
            "Test the source-disjunction and target-count channels separately; retain finite-fixture scope and all open source-correspondence edges.",
        ),
        "boundaries": (
            "Do not infer categorical MGW, general-measure Schick-Poland, hyperbolic, singular, atomic, quantized, or mixed-support validity.",
            "Heuristics do not estimate the paper functional; bounded reference agreement is not a general refinement or consistency theorem.",
        ),
    },
    {
        "id": "ksg-mutual-information",
        "label": "KSG1 mutual information",
        "construction_kind": "paper-defined continuous mutual-information estimator",
        "reference_ids": ("kraskov-2004",),
        "construction_id": None,
        "method_ids": (
            "mutual-information.ksg1-report",
            "mutual-information.ksg1-raw",
            "mutual-information.ksg1-sensitivity-trajectories",
            "mutual-information.ksg1-shared-config",
        ),
        "scientific_object": "KSG estimator 1 for continuous mutual information using the repository's declared max-product metric and neighbor/count conventions.",
        "domain_support": "Continuous population model under the explicit support contract; ties and finite samples provide one-sided diagnostics only.",
        "units": "nats.",
        "sample_role": "Paired rows form the estimator sample; preprocessing and sample selection must be separately bound.",
        "acceptance_obligations": (
            "Bind metric, k, strict marginal counts, tie policy, negative handling, support contract, and report/scalar surface.",
            "Keep integer-harmonic, neighbor-search, floating-point, statistical, and application evidence as distinct obligations.",
        ),
        "boundaries": (
            "KSG mutual-information evidence does not validate a shared-exclusions functional or PID atom construction.",
            "A stable report-first API is not a universal estimator-consistency or high-dimensional-validity claim.",
        ),
    },
    {
        "id": "continuous-pid2-composition",
        "label": "Continuous two-source PID composition",
        "construction_kind": "paper-defined four-atom construction with separately estimated terms and project wrappers",
        "reference_ids": ("ehrlich-2024", "kraskov-2004"),
        "construction_id": None,
        "component_construction_routes": (
            (
                "ehrlich-analytical-continuous-shared-exclusions",
                "ehrlich-continuous-shared-exclusions",
            ),
        ),
        "method_ids": ("pid.continuous-pid2",),
        "scientific_object": "The signed two-source Red, Unq1, Unq2, and Syn coordinates composed from Ehrlich shared-exclusions redundancy and separately estimated KSG mutual-information terms.",
        "domain_support": "The intersection of every component term's declared support and sampling premises; no premise transfers merely because terms share rows.",
        "units": "nats for every component term and all four atoms.",
        "sample_role": "Same-sample, split-sample, and cross-fit routes have distinct selection/evaluation roles that must be retained.",
        "acceptance_obligations": (
            "Bind every component estimator identity, support premise, sample split, failure, and signed four-coordinate atom result.",
            "Check Red + Unq1 + Unq2 + Syn reconstruction separately from component correctness, joint uncertainty, calibration, and application validity.",
        ),
        "boundaries": (
            "This four-coordinate PID2 result is not an incomplete or full 18-coordinate PID3 result.",
            "Algebraic reconstruction and separately green component tests do not establish joint statistical validity or calibrated atom uncertainty.",
        ),
    },
    {
        "id": "incomplete-continuous-pid3-availability",
        "label": "Incomplete continuous PID3 availability diagnostic",
        "construction_kind": "project-defined partial 18-coordinate availability diagnostic",
        "reference_ids": ("ehrlich-2024",),
        "construction_id": None,
        "component_construction_routes": (
            (
                "ehrlich-analytical-continuous-shared-exclusions",
                "ehrlich-continuous-shared-exclusions",
            ),
        ),
        "method_ids": ("pid.incomplete-continuous-pid3",),
        "scientific_object": "A partial report over the three-source 18-coordinate redundancy/atom lattice that exposes only coordinates whose required implemented branches are available.",
        "domain_support": "Only ambient-dimension-compatible implemented coordinates under their explicit continuous support premises; absence is reported rather than imputed.",
        "units": "nats for each available redundancy or atom coordinate; unavailable coordinates have no numeric value.",
        "sample_role": "The same rows feed each attempted coordinate; availability does not transfer support or correctness among coordinates.",
        "acceptance_obligations": (
            "Bind the exact 18-coordinate antichain inventory and record every available and unavailable redundancy/atom coordinate without imputation.",
            "Bind support, metric, k, source dimensions, failure reasons, and the dependency set for each exact atom combination.",
        ),
        "boundaries": (
            "The diagnostic is not a complete PID3, and an absent coordinate is not zero.",
            "Partial algebraic combinations do not validate or recover the research-only mixed-dimensional full lattice.",
        ),
    },
    {
        "id": "full-continuous-pid3-research-lattice",
        "label": "Full continuous PID3 research lattice reproduction",
        "construction_kind": "paper-defined 18-atom research reproduction with mixed-dimensional branches",
        "reference_ids": ("ehrlich-2024",),
        "construction_id": None,
        "component_construction_routes": (
            (
                "ehrlich-analytical-continuous-shared-exclusions",
                "ehrlich-continuous-shared-exclusions",
            ),
        ),
        "method_ids": ("pid.mixed-dimension-pid3",),
        "scientific_object": "All 18 three-source shared-exclusions redundancy coordinates and their 18 Möbius-inverted PID atoms under the paper-defined mixed-dimensional lattice algorithm.",
        "domain_support": "Purely continuous declared support plus an explicit research opt-in; singleton and pair-source neighborhoods have incompatible raw ambient-dimension scaling without a separate derivation.",
        "units": "nats for all 18 redundancies and 18 atoms under the fixed gauge and preprocessing.",
        "sample_role": "The same estimator rows feed every antichain branch; a runtime research opt-in permits reproduction but does not validate the estimand statistically.",
        "acceptance_obligations": (
            "Bind all 18 antichains, every estimated redundancy, the exact Möbius order, all 18 signed atoms, metric, gauge, k, preprocessing, support declaration, and research opt-in.",
            "Check complete lattice reconstruction separately from mixed-dimensional small-ball consistency, finite-sample bias, calibration, and application validity.",
        ),
        "boundaries": (
            "This is research-only reproduction; equal source dimensions and a passing 18-atom reconstruction do not establish a common small-ball reference measure or estimator consistency.",
            "It is not the project-defined incomplete availability diagnostic, Schick-Poland's proposed general-measure construction, or a mixed/atomic-support estimator.",
        ),
    },
    {
        "id": "williams-beer-imin",
        "label": "Williams-Beer I_min",
        "construction_kind": "paper-defined finite-categorical redundancy and PID",
        "reference_ids": ("williams-beer-2010",),
        "construction_id": None,
        "method_ids": ("pid.imin",),
        "scientific_object": "Minimum-specific-information redundancy and its finite-categorical PID atoms.",
        "domain_support": "Fixed finite categorical alphabets represented by an empirical PMF.",
        "units": "pid-rs outputs nats.",
        "sample_role": "The supplied categorical rows define the empirical distribution evaluated by the plug-in estimator.",
        "acceptance_obligations": (
            "Bind source/target encodings, empirical PMF, lattice, units, and resource budget.",
            "Test canonical laws and reconstruction without borrowing MGW shared-exclusions values or axioms.",
        ),
        "boundaries": (
            "I_min is a different redundancy measure from MGW and Ehrlich shared exclusions.",
            "Fitted-quantized compositions change the estimand and must be reviewed under the wrapper object as well.",
        ),
    },
    {
        "id": "project-wrappers-and-compositions",
        "label": "pid-rs project wrappers and compositions",
        "construction_kind": "project-defined or paper-derived software composition",
        "reference_ids": (),
        "construction_id": None,
        "method_ids": (
            "shared-exclusions.fitted-quantized",
            "pid.fitted-quantized-imin",
            "shared-exclusions.same-sample-quantized",
            "pid.same-sample-quantized-imin",
            "software.sxpid-interpretation-contract",
            "pipelines.quantized-sxpid-bootstrap",
            "pipelines.pid2-screening",
            "pipelines.pid3-permutation",
            "pipelines.pls-pid-composition",
            "pipelines.hierarchy-screening",
        ),
        "scientific_object": "Fitted-quantized, same-sample, interpretation, resampling, screening, selection, and report compositions defined by their catalog rows.",
        "domain_support": "Inherited only through each explicitly named component, plus wrapper-specific fit/evaluation, transform, dependence, and resource contracts.",
        "units": "Inherited from the named component and required to remain explicit; no generic wrapper unit is inferred.",
        "sample_role": "Training, evaluation, selection, resampling, synthetic, and externally specified roles must remain distinguishable in every serialized result.",
        "acceptance_obligations": (
            "Bind component versions, transform/metric/quantizer identity, fit and evaluation rows, RNG stream, failures, and output interpretation.",
            "Review the wrapper composition separately from every component's scientific and executable obligations.",
        ),
        "boundaries": (
            "A wrapper, binding, run log, digest, resampling result, or report adds no mapping theorem, calibration theorem, scientific novelty, or application validity.",
            "Same-sample descriptive and training-fitted routes are different estimands and may not share provenance by implication.",
        ),
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--emit-json", action="store_true")
    parser.add_argument("--emit-markdown", action="store_true")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if sum((arguments.emit_json, arguments.emit_markdown, arguments.write)) > 1:
        parser.error("select at most one output mode")
    return arguments


def reject_constant(value: str) -> Any:
    raise ProtocolError(f"non-finite JSON constant is forbidden: {value}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ProtocolError(f"cannot canonicalize JSON: {error}") from error


def load_regular_bytes(path: Path, label: str) -> bytes:
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ProtocolError(f"{label} is not a single-link regular file: {path}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            raw = bytearray()
            while chunk := os.read(descriptor, 1024 * 1024):
                raw.extend(chunk)
            closed = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = os.lstat(path)
    except OSError as error:
        raise ProtocolError(f"cannot read {label} {path}: {error}") from error

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(raw) == before.st_size
    ):
        raise ProtocolError(f"{label} changed during exact read: {path}")
    return bytes(raw)


def load_json(path: Path, label: str) -> tuple[Any, bytes]:
    raw = load_regular_bytes(path, label)
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ProtocolError) as error:
        raise ProtocolError(f"cannot parse {label} {path}: {error}") from error
    if raw != canonical_bytes(value):
        raise ProtocolError(f"{label} is not canonical sorted UTF-8 JSON: {path}")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_authority(
    root: Path, path: str, schema_path: str, label: str
) -> tuple[dict[str, Any], bytes]:
    value, raw = load_json(root / path, label)
    schema, _ = load_json(root / schema_path, f"{label} schema")
    try:
        validate_json_schema(value, schema, name=label)
    except SchemaValidationError as error:
        raise ProtocolError(str(error)) from error
    return value, raw


def make_source_record(
    reference: dict[str, Any], observed_by_arxiv: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    observed = observed_by_arxiv.get(reference["arxiv"])
    if observed is not None:
        return {
            "arxiv": reference["arxiv"],
            "doi": reference["doi"],
            "locator": observed["retrieval"]["url"],
            "observed_revision": observed["arxiv_revision"],
            "observed_sha256": observed["retrieval"]["sha256"],
            "pin_status": "retrieved_revision_and_hash",
            "reference_id": reference["id"],
            "title": reference["title"],
        }
    if reference["doi"] is not None and not reference["doi"].startswith(
        "10.48550/arXiv"
    ):
        pin_status = "doi_locator_without_local_byte_pin"
    else:
        pin_status = "catalog_locator_without_local_byte_pin"
    return {
        "arxiv": reference["arxiv"],
        "doi": reference["doi"],
        "locator": reference["url"],
        "observed_revision": None,
        "observed_sha256": None,
        "pin_status": pin_status,
        "reference_id": reference["id"],
        "title": reference["title"],
    }


def make_expected(root: Path) -> dict[str, Any]:
    catalog, catalog_raw = load_authority(
        root, CATALOG, CATALOG_SCHEMA, "method catalog"
    )
    errata, errata_raw = load_authority(root, ERRATA, ERRATA_SCHEMA, "source errata")
    assurance, assurance_raw = load_authority(
        root, ASSURANCE, ASSURANCE_SCHEMA, "typed assurance view"
    )
    if catalog.get("schema_revision") != 1 or errata.get("schema_revision") != 1:
        raise ProtocolError("unsupported catalog or source-errata schema revision")
    if assurance.get("schema_revision") != 1 or not assurance.get("derived_view_only"):
        raise ProtocolError(
            "unsupported typed-assurance view revision or authority status"
        )
    if assurance.get("transitive_chain_status") != "not_established":
        raise ProtocolError("typed assurance unexpectedly claims a transitive chain")

    methods = {item["id"]: item for item in catalog["methods"]}
    references = {item["id"]: item for item in catalog["references"]}
    assurance_families = {item["family_id"]: item for item in assurance["families"]}
    errata_records = {item["id"]: item for item in errata["records"]}
    known_constructions = {item["id"] for item in errata["constructions"]}
    assigned_methods = [
        method_id for spec in OBJECT_SPECS for method_id in spec["method_ids"]
    ]
    duplicate_assignments = sorted(
        {
            method_id
            for method_id in assigned_methods
            if assigned_methods.count(method_id) > 1
        }
    )
    if duplicate_assignments:
        raise ProtocolError(
            "catalog rows are assigned to multiple protocol objects: "
            f"{duplicate_assignments}"
        )
    observed_by_arxiv = {
        item["arxiv_revision"].removeprefix("arXiv:").split("v", 1)[0]: item
        for item in errata["sources"]
    }
    specs_by_id = {spec["id"]: spec for spec in OBJECT_SPECS}

    first_family = assurance["families"][0]
    edge_template = [
        {"id": edge["correspondence_edge"], "meaning": edge["meaning"]}
        for edge in first_family["edges"]
    ]
    for family in assurance["families"]:
        candidate = [
            {"id": edge["correspondence_edge"], "meaning": edge["meaning"]}
            for edge in family["edges"]
        ]
        if candidate != edge_template:
            raise ProtocolError(
                f"assurance family {family['family_id']} has a different edge vocabulary"
            )

    objects = []
    for spec in OBJECT_SPECS:
        missing_methods = sorted(set(spec["method_ids"]) - set(methods))
        missing_references = sorted(set(spec["reference_ids"]) - set(references))
        if missing_methods or missing_references:
            raise ProtocolError(
                f"{spec['id']} has missing catalog bindings: methods={missing_methods}, "
                f"references={missing_references}"
            )
        method_rows = [methods[method_id] for method_id in spec["method_ids"]]
        linked_references = {
            link["reference_id"]
            for method in method_rows
            for link in method["reference_links"]
        }
        if not set(spec["reference_ids"]).issubset(linked_references):
            raise ProtocolError(
                f"{spec['id']} reference is not linked by its indexed methods"
            )
        family_ids = sorted(
            {
                family
                for method in method_rows
                for family in method["release_scope_families"]
            }
        )
        unknown_families = sorted(set(family_ids) - set(assurance_families))
        if unknown_families:
            raise ProtocolError(
                f"{spec['id']} references unknown assurance families: {unknown_families}"
            )
        construction_id = spec["construction_id"]
        if construction_id is not None and construction_id not in known_constructions:
            raise ProtocolError(
                f"{spec['id']} references an unknown source construction: {construction_id}"
            )
        for reference_id in spec["reference_ids"]:
            reference_arxiv = references[reference_id]["arxiv"]
            observed_source = observed_by_arxiv.get(reference_arxiv)
            if (
                construction_id is not None
                and observed_source is not None
                and observed_source["construction_id"] != construction_id
            ):
                raise ProtocolError(
                    f"{spec['id']} source pin belongs to a different construction"
                )
        record_ids = sorted(
            record_id
            for record_id, record in errata_records.items()
            if record["construction_id"] == construction_id
        )
        component_routes = []
        for routed_construction_id, via_object_id in spec.get(
            "component_construction_routes", ()
        ):
            if routed_construction_id not in known_constructions:
                raise ProtocolError(
                    f"{spec['id']} routes an unknown component construction: "
                    f"{routed_construction_id}"
                )
            via_spec = specs_by_id.get(via_object_id)
            if via_spec is None:
                raise ProtocolError(
                    f"{spec['id']} routes source review through an unknown object: "
                    f"{via_object_id}"
                )
            if via_spec["construction_id"] != routed_construction_id:
                raise ProtocolError(
                    f"{spec['id']} component route does not match its via-object "
                    "primary construction"
                )
            routed_record_ids = sorted(
                record_id
                for record_id, record in errata_records.items()
                if record["construction_id"] == routed_construction_id
            )
            component_routes.append(
                {
                    "construction_id": routed_construction_id,
                    "source_observation_ids": routed_record_ids,
                    "transfer_status": "dependency_pointer_only_no_credit",
                    "via_object_id": via_object_id,
                }
            )
        source_records = [
            make_source_record(references[reference_id], observed_by_arxiv)
            for reference_id in spec["reference_ids"]
        ]
        if not source_records:
            source_records = [
                {
                    "arxiv": None,
                    "doi": None,
                    "locator": "method-catalog.json schema revision 1",
                    "observed_revision": "pid-rs/method-catalog revision 1",
                    "observed_sha256": sha256(catalog_raw),
                    "pin_status": "project_catalog_revision",
                    "reference_id": "pid-rs-project-definition",
                    "title": "pid-rs project-defined wrapper and composition records",
                }
            ]
        objects.append(
            {
                "acceptance_obligations": list(spec["acceptance_obligations"]),
                "assurance_families": [
                    {
                        "edges": [
                            {
                                "edge": edge["correspondence_edge"],
                                "status": edge["correspondence_status"],
                            }
                            for edge in assurance_families[family_id]["edges"]
                        ],
                        "family_id": family_id,
                        "software_stability": assurance_families[family_id][
                            "software_stability"
                        ],
                        "transitive_five_edge_chain_claimed": assurance_families[
                            family_id
                        ]["transitive_five_edge_chain_claimed"],
                    }
                    for family_id in family_ids
                ],
                "boundaries": list(spec["boundaries"]),
                "catalog_method_ids": list(spec["method_ids"]),
                "component_source_review_routes": component_routes,
                "construction_kind": spec["construction_kind"],
                "domain_support": spec["domain_support"],
                "id": spec["id"],
                "label": spec["label"],
                "review_record_ids": [],
                "sample_role": spec["sample_role"],
                "scientific_object": spec["scientific_object"],
                "source_observation_ids": record_ids,
                "source_records": source_records,
                "units": spec["units"],
            }
        )

    review_records = [
        {
            key: record[key]
            for key in (
                "evidence_class",
                "id",
                "independence",
                "object_count",
                "reviewer_class",
                "scope_precision",
                "status",
            )
        }
        for record in assurance["review_records"]
    ]
    return {
        "authorities": [
            {
                "path": CATALOG,
                "role": "method_provenance_and_availability",
                "schema": catalog["schema"],
                "schema_revision": catalog["schema_revision"],
                "sha256": sha256(catalog_raw),
            },
            {
                "path": ERRATA,
                "role": "source_observations_and_construction_firewall",
                "schema": errata["schema"],
                "schema_revision": errata["schema_revision"],
                "sha256": sha256(errata_raw),
            },
            {
                "path": ASSURANCE,
                "role": "typed_assurance_and_review_projection",
                "schema": assurance["schema"],
                "schema_revision": assurance["schema_revision"],
                "sha256": sha256(assurance_raw),
            },
        ],
        "correspondence_edges": edge_template,
        "derived_view_only": True,
        "evidence_and_review": {
            "evidence_classes": [
                {"class": key, "meaning": value}
                for key, value in sorted(
                    assurance["evidence_class_definitions"].items()
                )
            ],
            "independence_dimensions": list(INDEPENDENCE_DIMENSIONS),
            "review_records": review_records,
            "rule": "Evidence class, reviewer class, scope, and each independence dimension are non-interchangeable. No object receives review credit unless an exact review record is explicitly bound to it.",
        },
        "generated_by": GENERATOR,
        "nonimplications": [
            "No result transfers between indexed objects without a premise-explicit mapping theorem or an explicitly scoped empirical comparison naming both objects.",
            "Shared notation, authors, citations, code, fixtures, tests, units, or repository location do not identify scientific objects.",
            "Inventory, model review, line review, human review, formal proof, execution evidence, and release facts are not substitutes for one another.",
            "A formal or algebraic result does not by itself establish source correspondence, executable refinement, floating-point behavior, statistical validity, or application validity.",
            "Source observations and candidate corrections remain reviewer-derived until exact author or publisher confirmation is recorded.",
            "A stable API, binding, hash, run log, or generated view is not a scientific novelty, authenticity, calibration, or application-validity claim.",
            "A catalog row or assurance family indexed under multiple objects is a shared route, not object equivalence, exhaustive ownership, or transferred evidence.",
            "A component source-review route is a discovery and dependency pointer only: every observation must be re-adjudicated for the selected object, and the route transfers no applicability, reviewer disposition, implementation binding, correspondence status, or independence credit.",
        ],
        "object_order": [spec["id"] for spec in OBJECT_SPECS],
        "objects": objects,
        "review_sequence": [
            {
                "step": 1,
                "acceptance_rule": "Select exactly one indexed object and record source, construction, estimand, domain/support, units, sample role, and requested claim; otherwise stop.",
            },
            {
                "step": 2,
                "acceptance_rule": "Verify the exact source locator/revision and apply only source-errata records with the same construction_id; missing byte pins remain explicit.",
            },
            {
                "step": 3,
                "acceptance_rule": "Bind exact catalog rows, implementation surfaces, features, component identities, transforms, metrics, gauges, quantizers, and downstream consumers. Follow every registered component source-review route, but re-adjudicate each observation for the selected object without transferring credit.",
            },
            {
                "step": 4,
                "acceptance_rule": "Status source-to-specification and specification-to-formal edges independently; a proof receives no source correspondence by implication.",
            },
            {
                "step": 5,
                "acceptance_rule": "Status formal-to-executable and executable-to-language/numeric edges independently, including branches, indexing, support logic, and finite precision.",
            },
            {
                "step": 6,
                "acceptance_rule": "Run exact scoped tests and hostile controls in the declared toolchains; preserve failures and negative evidence, and inspect results rather than inheriting reported green status.",
            },
            {
                "step": 7,
                "acceptance_rule": "Record evidence class, reviewer class, exact artifact/blob/scope, and all five independence dimensions without promotion or transitive credit.",
            },
            {
                "step": 8,
                "acceptance_rule": "State open correspondence edges and nonclaims; application use requires separately satisfied sampling, support, calibration, and domain premises.",
            },
        ],
        "schema": "pid-rs/pid-mathematical-audit-protocol",
        "schema_revision": 1,
        "title": "PID mathematical audit protocol and object index",
        "transitive_chain_status": assurance["transitive_chain_status"],
    }


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def compact_list(values: list[str], limit: int = 3) -> str:
    shown = values[:limit]
    rendered = ", ".join(f"`{markdown_escape(value)}`" for value in shown) or "none"
    if len(values) > limit:
        rendered += f"; +{len(values) - limit} more"
    return rendered


def source_summary(records: list[dict[str, Any]]) -> str:
    rendered = []
    for record in records:
        if record["observed_revision"]:
            revision = record["observed_revision"]
        elif record["doi"]:
            revision = f"doi:{record['doi']}"
        elif record["arxiv"]:
            revision = f"arXiv:{record['arxiv']}"
        else:
            revision = record["locator"]
        rendered.append(
            f"`{record['reference_id']}`: {revision} ({record['pin_status']})"
        )
    return "; ".join(rendered)


def render_markdown(view: dict[str, Any]) -> str:
    lines = [
        "# PID mathematical audit protocol",
        "",
        "<!-- Generated by scripts/check-pid-mathematical-audit-protocol.py; edit its bounded protocol specification or the bound machine authorities. -->",
        "",
        "This concise PID-only index is a **non-authoritative derived review aid**. It binds the "
        "method catalog, source-observation firewall, and typed assurance view; those records retain "
        "their stated authority. It deliberately excludes unrelated research-process case studies. "
        "A shared author, symbol, implementation, or citation never substitutes for an explicit "
        "mapping between scientific objects.",
        "",
        "## Object index",
        "",
        "| Object | Source pin state | Scientific domain | Catalog index | Assurance index | Hard boundary |",
        "|---|---|---|---|---|---|",
    ]
    for item in view["objects"]:
        cells = [
            f"`{item['id']}` — {markdown_escape(item['label'])}",
            markdown_escape(source_summary(item["source_records"])),
            markdown_escape(item["domain_support"]),
            compact_list(item["catalog_method_ids"]),
            compact_list(
                [family["family_id"] for family in item["assurance_families"]]
            ),
            markdown_escape(item["boundaries"][0]),
        ]
        for cell in cells:
            if len(cell.split()) > 120:
                raise ProtocolError(
                    f"object-index cell exceeds 120 words for {item['id']}"
                )
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## Review sequence", ""])
    for step in view["review_sequence"]:
        lines.append(f"{step['step']}. {step['acceptance_rule']}")
    lines.extend(["", "## Object cards", ""])
    for item in view["objects"]:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- **Construction:** {item['construction_kind']}. {item['scientific_object']}",
                f"- **Domain/support:** {item['domain_support']}",
                f"- **Units:** {item['units']}",
                f"- **Sample role:** {item['sample_role']}",
                f"- **Source:** {source_summary(item['source_records'])}.",
                f"- **Catalog rows:** {compact_list(item['catalog_method_ids'], limit=len(item['catalog_method_ids']))}.",
                f"- **Source observations:** {compact_list(item['source_observation_ids'], limit=len(item['source_observation_ids']))}.",
                "- **Component source-review routes:** "
                + compact_list(
                    [
                        f"{route['construction_id']} via {route['via_object_id']} "
                        f"({len(route['source_observation_ids'])} observations; dependency pointer only, no credit)"
                        for route in item["component_source_review_routes"]
                    ],
                    limit=len(item["component_source_review_routes"]),
                )
                + ".",
                f"- **Assurance families:** {compact_list([family['family_id'] for family in item['assurance_families']], limit=len(item['assurance_families']))}.",
                "- **Acceptance obligations:** "
                + " ".join(item["acceptance_obligations"]),
                "- **Nonclaims:** " + " ".join(item["boundaries"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Correspondence and evidence firewall",
            "",
            "Every family retains five separate edges; the current typed view states that no "
            "transitive chain is established:",
            "",
        ]
    )
    for index, edge in enumerate(view["correspondence_edges"], start=1):
        lines.append(f"{index}. `{edge['id']}` — {edge['meaning']}")
    lines.extend(
        [
            "",
            view["evidence_and_review"]["rule"],
            "",
            "| Evidence class | Meaning |",
            "|---|---|",
        ]
    )
    for item in view["evidence_and_review"]["evidence_classes"]:
        lines.append(f"| `{item['class']}` | {markdown_escape(item['meaning'])} |")
    lines.extend(
        [
            "",
            "Independence must be recorded separately for `semantic`, `implementation`, `custody`, "
            "`institutional`, and `data`. The currently bound object cards contain no explicit "
            "object-level review-record bindings; no review completion is inferred.",
            "",
            "## Nonimplications",
            "",
            *[f"- {item}" for item in view["nonimplications"]],
            "",
            "## Bound authority bytes",
            "",
        ]
    )
    for authority in view["authorities"]:
        lines.append(
            f"- `{authority['path']}` — `{authority['schema']}` revision "
            f"`{authority['schema_revision']}`, SHA-256 `{authority['sha256']}`."
        )
    lines.append("")
    return "\n".join(lines)


def validate_view(
    actual: dict[str, Any], schema: dict[str, Any], expected: dict[str, Any]
) -> None:
    try:
        validate_json_schema(actual, schema, name="pid-mathematical-audit-protocol")
    except SchemaValidationError as error:
        raise ProtocolError(str(error)) from error
    if canonical_bytes(actual) != canonical_bytes(expected):
        raise ProtocolError("PID protocol JSON is stale; regenerate with --write")


def validate_outputs(root: Path, expected: dict[str, Any]) -> None:
    schema, _ = load_json(root / VIEW_SCHEMA, "PID protocol schema")
    actual, actual_raw = load_json(root / VIEW, "PID protocol")
    validate_view(actual, schema, expected)
    if actual_raw != canonical_bytes(expected):
        raise ProtocolError("PID protocol JSON is not the expected canonical bytes")
    markdown = load_regular_bytes(root / MARKDOWN, "PID protocol Markdown")
    if markdown != render_markdown(expected).encode("utf-8"):
        raise ProtocolError(
            "PID_MATHEMATICAL_AUDIT_PROTOCOL.md is stale; regenerate with --write"
        )


def write_outputs(root: Path, view: dict[str, Any]) -> None:
    (root / VIEW).parent.mkdir(parents=True, exist_ok=True)
    (root / VIEW).write_bytes(canonical_bytes(view))
    (root / MARKDOWN).write_text(render_markdown(view), encoding="utf-8", newline="")


def main() -> int:
    arguments = parse_args()
    try:
        expected = make_expected(arguments.root)
        schema, _ = load_json(arguments.root / VIEW_SCHEMA, "PID protocol schema")
        validate_json_schema(expected, schema, name="expected-PID-protocol")
        if arguments.emit_json:
            sys.stdout.buffer.write(canonical_bytes(expected))
        elif arguments.emit_markdown:
            sys.stdout.write(render_markdown(expected))
        elif arguments.write:
            write_outputs(arguments.root, expected)
            print("PID mathematical audit protocol: GENERATED")
        else:
            validate_outputs(arguments.root, expected)
            print(
                "PID mathematical audit protocol: PASS "
                f"({len(expected['objects'])} objects; no transitive chain)"
            )
    except (OSError, ProtocolError, SchemaValidationError) as error:
        print(f"PID mathematical audit protocol: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
