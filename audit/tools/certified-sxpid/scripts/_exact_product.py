#!/usr/bin/env python3
"""Exact multiplicative certificates for averaged empirical categorical SxPID2.

This module uses only the Python standard library.  It does not import pid-rs, the Rust
certifier, NumPy, SymPy, GMP, MPFR, or another numerical package.  Every result below is an
integer/Fraction calculation.

For an observed row ``z`` with count ``c_z`` and total count ``n``, let ``a`` be the count of a
source-event union, ``b`` the count of its intersection with the keyed target event, and ``t``
the keyed target count.  The three local log arguments are

    informative:     n / a
    misinformative:   t / b
    net:              n*b / (a*t).

The empirical average weights each logarithm by ``c_z/n``.  Therefore each cumulative is
``log(R)/n`` for the exact positive rational product ``R = product argument**c_z``.  Applying an
integer Mobius row only raises these cumulative products to signed integer powers, so every atom
has the same form.  Exact zero is equivalent to ``R == 1``; otherwise the sign is the exact
comparison of ``R`` with one.

Trust boundary: Python integer/Fraction semantics, this source, and the reviewed mathematical
reduction remain trusted.  The route proves a finite empirical arithmetic statement.  It does
not prove the shared-exclusions measure's scientific desiderata, population assumptions,
sampling validity, data provenance, higher-source lattices, continuous PID, or application
fitness.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Final, Iterable, NoReturn, Sequence

INPUT_SCHEMA: Final = "pid-rs/categorical-sxpid2-count-table/v1"
REPORT_SCHEMA: Final = "pid-rs/certified-sxpid-report/v2"
DEFINITION_REVISION: Final = "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1"
RESOURCE_POLICY_ID: Final = "sxpid2-certification-default-v2"
UNITS: Final = "nats"
MAX_INPUT_BYTES: Final = 4 * 1024 * 1024
MAX_CERTIFICATE_BYTES: Final = 11 * 1024 * 1024
MAX_INTEGER_DIGITS: Final = 4096
MAX_DYADIC_EXPONENT_ABS: Final = 65_536
MAX_TERMS_PER_EXPRESSION: Final = 4096
MAX_EXACT_PRODUCT_TERMS_PER_EXPRESSION: Final = 256
MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT: Final = 16_384
MAX_EXACT_PRODUCT_PROJECTED_BITS_PER_EXPRESSION: Final = 262_144
MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS: Final = 1_048_576

STATES: Final = tuple(
    (source_one, source_two, target)
    for source_one in (0, 1)
    for source_two in (0, 1)
    for target in (0, 1)
)
NODE_MASKS: Final = ((0b01,), (0b10,), (0b11,), (0b01, 0b10))
NODE_IDS: Final = ("source_one", "source_two", "joint_sources", "redundancy")
ATOM_IDS: Final = ("unique_one", "unique_two", "synergy", "redundancy")
COMPONENT_IDS: Final = ("informative", "misinformative", "net")
MOBIUS: Final = (
    (1, 0, 0, -1),
    (0, 1, 0, -1),
    (-1, -1, 1, 1),
    (0, 0, 0, 1),
)
ZETA: Final = (
    (1, 0, 0, 1),
    (0, 1, 0, 1),
    (1, 1, 1, 1),
    (0, 0, 0, 1),
)

CANONICAL_POSITIVE_RE: Final = re.compile(r"^[1-9][0-9]*$")
CANONICAL_SIGNED_RE: Final = re.compile(r"^(0|-?[1-9][0-9]*)$")


class ProductVerificationError(RuntimeError):
    """An exact derivation, certificate binding, or sign check failed closed."""


@dataclass(frozen=True)
class ProductCoordinate:
    """One coordinate represented exactly as ``value = log(product) / total``."""

    kind: str
    node: str
    component: str
    product: Fraction

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.kind, self.node, self.component)

    @property
    def exact_sign(self) -> int:
        return (self.product > 1) - (self.product < 1)


@dataclass(frozen=True)
class ReportProductPlan:
    factors: tuple[tuple[Fraction, int], ...]
    term_count: int
    maximum_absolute_exponent: int
    projected_product_bits_upper_bound: int

    @property
    def within_per_expression_limits(self) -> bool:
        return (
            self.term_count <= MAX_EXACT_PRODUCT_TERMS_PER_EXPRESSION
            and self.maximum_absolute_exponent
            <= MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT
            and self.projected_product_bits_upper_bound
            <= MAX_EXACT_PRODUCT_PROJECTED_BITS_PER_EXPRESSION
        )


@dataclass(frozen=True)
class DerivationChecks:
    event_constraints: int
    local_net_identities: int
    direct_mi_identities: int
    component_net_identities: int
    zeta_reconstructions: int


@dataclass(frozen=True)
class DerivedProducts:
    total: int
    coordinates: tuple[ProductCoordinate, ...]
    checks: DerivationChecks

    def by_identity(self) -> dict[tuple[str, str, str], ProductCoordinate]:
        result = {coordinate.identity: coordinate for coordinate in self.coordinates}
        if len(result) != len(self.coordinates):
            raise ProductVerificationError(
                "derived coordinate identities are not unique"
            )
        return result


@dataclass(frozen=True)
class CertificateChecks:
    expression_products: int
    exact_signs: int
    exact_zeros: int
    certified_positive: int
    certified_negative: int


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProductVerificationError(message)


def _matches_collection(
    state: tuple[int, int, int], realization: tuple[int, int, int], mask: int
) -> bool:
    return all(
        mask & (1 << source_index) == 0
        or state[source_index] == realization[source_index]
        for source_index in range(2)
    )


def _event_count(
    states: Sequence[tuple[int, int, int]],
    counts: Sequence[int],
    realization: tuple[int, int, int],
    masks: Sequence[int],
    *,
    require_target: bool,
) -> int:
    result = 0
    for state, count in zip(states, counts, strict=True):
        target_restricted_match = state[2] == realization[2]
        if require_target and not target_restricted_match:
            continue
        event_matches = any(
            _matches_collection(state, realization, mask) for mask in masks
        )
        if event_matches:
            result += count
    return result


def _weighted_factor(argument: Fraction, row_count: int) -> Fraction:
    """Lift one local log argument through its integer empirical multiplicity."""

    return argument**row_count


def _signed_power(value: Fraction, exponent: int) -> Fraction:
    if exponent >= 0:
        return value**exponent
    return Fraction(1, 1) / value ** (-exponent)


def _product_linear_combination(
    products: Sequence[Fraction], coefficients: Sequence[int]
) -> Fraction:
    require(
        len(products) == len(coefficients),
        "product linear combination has inconsistent dimensions",
    )
    result = Fraction(1, 1)
    for product, coefficient in zip(products, coefficients, strict=True):
        result *= _signed_power(product, coefficient)
    return result


def _verify_integer_lattice() -> None:
    for row in range(4):
        for column in range(4):
            product = sum(
                ZETA[row][inner] * MOBIUS[inner][column] for inner in range(4)
            )
            require(
                product == int(row == column), "pinned zeta/Mobius matrices disagree"
            )


def _validate_table(
    states: Sequence[tuple[int, int, int]], counts: Sequence[int]
) -> int:
    require(len(states) == len(counts), "state/count dimensions differ")
    require(len(states) > 0, "count table is empty")
    require(len(set(states)) == len(states), "complete states are not unique")
    require(
        all(len(state) == 3 for state in states),
        "each state must have two sources and a target",
    )
    require(
        all(
            isinstance(count, int) and not isinstance(count, bool) and count >= 0
            for count in counts
        ),
        "counts must be nonnegative integers",
    )
    total = sum(counts)
    require(total > 0, "count table has zero total")
    return total


def _direct_mi_product(
    states: Sequence[tuple[int, int, int]],
    counts: Sequence[int],
    source_index: int,
) -> Fraction:
    total = sum(counts)
    source_masses: dict[Any, int] = {}
    target_masses: dict[int, int] = {}
    joint_masses: dict[tuple[Any, int], int] = {}
    for state, count in zip(states, counts, strict=True):
        if count == 0:
            continue
        if source_index == 0:
            source: Any = state[0]
        elif source_index == 1:
            source = state[1]
        elif source_index == 2:
            source = (state[0], state[1])
        else:
            raise ProductVerificationError("unsupported direct-MI source index")
        target = state[2]
        source_masses[source] = source_masses.get(source, 0) + count
        target_masses[target] = target_masses.get(target, 0) + count
        joint_masses[(source, target)] = joint_masses.get((source, target), 0) + count

    result = Fraction(1, 1)
    for (source, target), joint in sorted(joint_masses.items(), key=repr):
        argument = Fraction(
            joint * total, source_masses[source] * target_masses[target]
        )
        result *= _weighted_factor(argument, joint)
    return result


def derive_products(
    counts: Sequence[int],
    states: Sequence[tuple[int, int, int]] = STATES,
) -> DerivedProducts:
    """Derive all 24 exact products by direct event scanning and integer Mobius powers."""

    total = _validate_table(states, counts)
    _verify_integer_lattice()
    cumulative = {
        component: [Fraction(1, 1) for _ in NODE_MASKS] for component in COMPONENT_IDS
    }
    event_constraints = 0
    local_net_identities = 0

    for realization, row_count in zip(states, counts, strict=True):
        if row_count == 0:
            continue
        target_count = sum(
            count
            for state, count in zip(states, counts, strict=True)
            if state[2] == realization[2]
        )
        for node_index, masks in enumerate(NODE_MASKS):
            union_count = _event_count(
                states, counts, realization, masks, require_target=False
            )
            target_union_count = _event_count(
                states, counts, realization, masks, require_target=True
            )
            require(
                0 < row_count <= target_union_count <= union_count <= total
                and target_union_count <= target_count <= total,
                f"event-count nesting failed at {realization}, node {NODE_IDS[node_index]}",
            )
            event_constraints += 1

            informative = Fraction(total, union_count)
            misinformative = Fraction(target_count, target_union_count)
            net = Fraction(total * target_union_count, union_count * target_count)
            require(
                informative / misinformative == net,
                "local informative/misinformative/net identity failed",
            )
            local_net_identities += 1
            for component, argument in zip(
                COMPONENT_IDS, (informative, misinformative, net), strict=True
            ):
                cumulative[component][node_index] *= _weighted_factor(
                    argument, row_count
                )

    direct_mi_identities = 0
    for source_index in range(3):
        require(
            cumulative["net"][source_index]
            == _direct_mi_product(states, counts, source_index),
            f"direct-MI product identity failed at {NODE_IDS[source_index]}",
        )
        direct_mi_identities += 1

    atoms: dict[str, list[Fraction]] = {}
    zeta_reconstructions = 0
    component_net_identities = 0
    for component in COMPONENT_IDS:
        atoms[component] = [
            _product_linear_combination(cumulative[component], row) for row in MOBIUS
        ]
        for node_index, zeta_row in enumerate(ZETA):
            require(
                _product_linear_combination(atoms[component], zeta_row)
                == cumulative[component][node_index],
                "exact multiplicative zeta reconstruction failed",
            )
            zeta_reconstructions += 1

    for coordinate_index in range(4):
        require(
            cumulative["net"][coordinate_index]
            == cumulative["informative"][coordinate_index]
            / cumulative["misinformative"][coordinate_index],
            "cumulative component product identity failed",
        )
        require(
            atoms["net"][coordinate_index]
            == atoms["informative"][coordinate_index]
            / atoms["misinformative"][coordinate_index],
            "atom component product identity failed",
        )
        component_net_identities += 2

    coordinates: list[ProductCoordinate] = []
    for kind, identifiers, component_products in (
        ("cumulative", NODE_IDS, cumulative),
        ("atom", ATOM_IDS, atoms),
    ):
        for component in COMPONENT_IDS:
            for identifier, product in zip(
                identifiers, component_products[component], strict=True
            ):
                require(product > 0, "derived exact product is not positive")
                coordinates.append(
                    ProductCoordinate(kind, identifier, component, product)
                )
    require(len(coordinates) == 24, "derivation did not produce 24 coordinates")
    return DerivedProducts(
        total=total,
        coordinates=tuple(coordinates),
        checks=DerivationChecks(
            event_constraints=event_constraints,
            local_net_identities=local_net_identities,
            direct_mi_identities=direct_mi_identities,
            component_net_identities=component_net_identities,
            zeta_reconstructions=zeta_reconstructions,
        ),
    )


def canonical_input(
    counts: Sequence[int],
    states: Sequence[tuple[int, int, int]] = STATES,
) -> bytes:
    _validate_table(states, counts)
    rows = [
        {
            "source_states": [[str(state[0])], [str(state[1])]],
            "target_state": [str(state[2])],
            "count": str(count),
        }
        for state, count in zip(states, counts, strict=True)
        if count > 0
    ]
    document = {
        "schema": INPUT_SCHEMA,
        "definition_revision": DEFINITION_REVISION,
        "units": UNITS,
        "resource_policy_id": RESOURCE_POLICY_ID,
        "rows": rows,
    }
    raw = canonical_json_bytes(document)
    require(
        len(raw) <= MAX_INPUT_BYTES,
        "canonical count table exceeds the input-byte limit",
    )
    return raw


def _reject_float(_: str) -> NoReturn:
    raise ProductVerificationError("JSON floating-point numbers are forbidden")


def _reject_constant(text: str) -> NoReturn:
    raise ProductVerificationError(f"nonstandard JSON constant is forbidden: {text}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def parse_json(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except ProductVerificationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ProductVerificationError(
            f"{label} is not strict UTF-8 JSON: {error}"
        ) from error


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ProductVerificationError(
            f"canonical JSON encoding failed: {error}"
        ) from error


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _canonical_integer(value: Any, *, positive: bool, label: str) -> int:
    require(isinstance(value, str), f"{label} is not an integer string")
    pattern = CANONICAL_POSITIVE_RE if positive else CANONICAL_SIGNED_RE
    require(pattern.fullmatch(value) is not None, f"{label} is not canonical")
    require(
        len(value.lstrip("-")) <= MAX_INTEGER_DIGITS,
        f"{label} exceeds the integer digit limit",
    )
    result = int(value, 10)
    require(not positive or result > 0, f"{label} is not positive")
    return result


def _report_rational(value: Any, label: str) -> Fraction:
    require(isinstance(value, dict), f"{label} is not an object")
    require(set(value) == {"numerator", "denominator"}, f"{label} keys differ")
    return Fraction(
        _canonical_integer(
            value["numerator"], positive=False, label=f"{label} numerator"
        ),
        _canonical_integer(
            value["denominator"], positive=True, label=f"{label} denominator"
        ),
    )


def _dyadic(value: Any, label: str) -> Fraction:
    require(isinstance(value, dict), f"{label} is not an object")
    require(set(value) == {"significand", "exponent2"}, f"{label} keys differ")
    significand = _canonical_integer(
        value["significand"], positive=False, label=f"{label} significand"
    )
    exponent = value["exponent2"]
    require(
        isinstance(exponent, int) and not isinstance(exponent, bool),
        f"{label} exponent is not an integer",
    )
    require(
        abs(exponent) <= MAX_DYADIC_EXPONENT_ABS,
        f"{label} exponent exceeds the structural limit",
    )
    require(
        (significand == 0 and exponent == 0)
        or (significand != 0 and significand % 2 != 0),
        f"{label} is not a normalized dyadic",
    )
    if exponent >= 0:
        return Fraction(significand << exponent, 1)
    return Fraction(significand, 1 << (-exponent))


def _product_plan_from_report_terms(
    terms: Any, total: int, label: str
) -> ReportProductPlan:
    require(isinstance(terms, list), f"{label} is not an array")
    require(
        len(terms) <= MAX_TERMS_PER_EXPRESSION,
        f"{label} exceeds the exact-term limit",
    )
    factors: list[tuple[Fraction, int]] = []
    maximum_absolute_exponent = 0
    projected_product_bits_upper_bound = 0
    for index, term in enumerate(terms):
        require(isinstance(term, dict), f"{label}[{index}] is not an object")
        require(
            set(term) == {"coefficient", "log_argument"},
            f"{label}[{index}] keys differ",
        )
        coefficient = _report_rational(
            term["coefficient"], f"{label}[{index}] coefficient"
        )
        argument = _report_rational(term["log_argument"], f"{label}[{index}] argument")
        require(argument > 0, f"{label}[{index}] argument is not positive")
        exponent = coefficient * total
        require(
            exponent.denominator == 1,
            f"{label}[{index}] coefficient times total is not an integer",
        )
        require(
            exponent.numerator != 0,
            f"{label}[{index}] has a zero denominator-cleared exponent",
        )
        absolute_exponent = abs(exponent.numerator)
        maximum_absolute_exponent = max(
            maximum_absolute_exponent, absolute_exponent
        )
        projected_product_bits_upper_bound += absolute_exponent * (
            argument.numerator.bit_length() + argument.denominator.bit_length()
        )
        factors.append((argument, exponent.numerator))
    return ReportProductPlan(
        tuple(factors),
        len(terms),
        maximum_absolute_exponent,
        projected_product_bits_upper_bound,
    )


def _product_from_admitted_report_plan(
    plan: ReportProductPlan, aggregate_admitted: bool
) -> Fraction:
    require(
        plan.within_per_expression_limits,
        "exact-product power requested before per-expression preflight admission",
    )
    require(
        aggregate_admitted or not plan.factors,
        "exact-product power requested before aggregate preflight admission",
    )
    result = Fraction(1, 1)
    for argument, exponent in plan.factors:
        result *= _signed_power(argument, exponent)
    if plan.factors:
        actual_bits = result.numerator.bit_length() + result.denominator.bit_length()
        require(
            actual_bits <= plan.projected_product_bits_upper_bound,
            "exact-product result exceeded its conservative preflight projection",
        )
    return result


def verify_certificate(
    input_raw: bytes, certificate_raw: bytes, derived: DerivedProducts
) -> CertificateChecks:
    """Bind all 24 direct products to report expressions, intervals, and sign decisions."""

    require(
        len(input_raw) <= MAX_INPUT_BYTES, "count table exceeds the input-byte limit"
    )
    require(
        len(certificate_raw) <= MAX_CERTIFICATE_BYTES,
        "certificate exceeds the certificate-byte limit",
    )
    envelope = parse_json(certificate_raw, "certificate")
    require(isinstance(envelope, dict), "certificate is not an object")
    require(
        set(envelope) == {"payload", "payload_sha256"},
        "certificate envelope keys differ",
    )
    payload = envelope["payload"]
    require(isinstance(payload, dict), "certificate payload is not an object")
    require(
        envelope["payload_sha256"] == canonical_digest(payload),
        "certificate payload digest mismatch",
    )
    require(payload.get("schema") == REPORT_SCHEMA, "certificate schema mismatch")
    require(payload.get("status") == "certified", "certificate status mismatch")
    require(
        payload.get("route") == "categorical_sxpid2_averaged",
        "certificate route mismatch",
    )
    require(
        payload.get("definition_revision") == DEFINITION_REVISION,
        "certificate definition revision mismatch",
    )
    require(payload.get("units") == UNITS, "certificate units mismatch")
    input_evidence = payload.get("input")
    require(isinstance(input_evidence, dict), "certificate input evidence is absent")
    input_document = parse_json(input_raw, "count table")
    require(
        input_evidence.get("raw_input_sha256") == hashlib.sha256(input_raw).hexdigest(),
        "certificate raw-input digest mismatch",
    )
    require(
        input_evidence.get("semantic_input_sha256") == canonical_digest(input_document),
        "certificate semantic-input digest mismatch",
    )
    require(
        input_evidence.get("total_count") == str(derived.total),
        "certificate total count mismatch",
    )

    coordinates = payload.get("coordinates")
    require(isinstance(coordinates, list), "certificate coordinates are absent")
    require(
        len(coordinates) == len(derived.coordinates) == 24, "coordinate count mismatch"
    )
    report_product_plans = [
        _product_plan_from_report_terms(
            reported.get("exact_terms") if isinstance(reported, dict) else None,
            derived.total,
            f"coordinate {index} exact terms",
        )
        for index, reported in enumerate(coordinates)
    ]
    aggregate_projection = sum(
        plan.projected_product_bits_upper_bound
        for plan in report_product_plans
        if plan.within_per_expression_limits
    )
    aggregate_admitted = (
        aggregate_projection <= MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS
    )

    expression_products = 0
    exact_signs = 0
    exact_zeros = 0
    positive = 0
    negative = 0
    seen: set[tuple[str, str, str]] = set()
    for index, (reported, expected, report_product_plan) in enumerate(
        zip(
            coordinates,
            derived.coordinates,
            report_product_plans,
            strict=True,
        )
    ):
        require(isinstance(reported, dict), f"coordinate {index} is not an object")
        identity = reported.get("identity")
        require(isinstance(identity, dict), f"coordinate {index} identity is absent")
        reported_identity = (
            identity.get("kind"),
            identity.get("node"),
            identity.get("component"),
        )
        require(
            reported_identity == expected.identity,
            f"coordinate {index} identity/order mismatch",
        )
        require(
            reported_identity not in seen, f"coordinate {index} identity is duplicated"
        )
        seen.add(reported_identity)  # type: ignore[arg-type]

        exact_product = reported.get("exact_product")
        require(
            isinstance(exact_product, dict),
            f"coordinate {index} exact product is absent",
        )
        require(
            set(exact_product)
            == {
                "status",
                "decision_source",
                "decision",
                "exact_zero_witness",
                "preflight",
            },
            f"coordinate {index} exact-product keys differ",
        )
        require(
            exact_product.get("status") == "compared",
            f"coordinate {index} bounded exact product was not compared",
        )
        require(
            exact_product.get("decision_source")
            == "bounded_exact_rational_product_after_integer_denominator_clearing",
            f"coordinate {index} exact-product source mismatch",
        )
        preflight = exact_product.get("preflight")
        require(
            isinstance(preflight, dict),
            f"coordinate {index} exact-product preflight is absent",
        )
        require(
            set(preflight)
            == {
                "term_count",
                "maximum_absolute_exponent",
                "projected_product_bits_upper_bound",
                "within_per_expression_limits",
                "admitted_under_total_projected_bits_limit",
            },
            f"coordinate {index} exact-product preflight keys differ",
        )
        require(
            preflight.get("term_count") == report_product_plan.term_count,
            f"coordinate {index} exact-product term count mismatch",
        )
        require(
            preflight.get("maximum_absolute_exponent")
            == str(report_product_plan.maximum_absolute_exponent),
            f"coordinate {index} exact-product exponent evidence mismatch",
        )
        require(
            preflight.get("projected_product_bits_upper_bound")
            == str(report_product_plan.projected_product_bits_upper_bound),
            f"coordinate {index} exact-product projection evidence mismatch",
        )
        require(
            preflight.get("within_per_expression_limits") is True,
            f"coordinate {index} exact-product per-expression admission mismatch",
        )
        require(
            aggregate_admitted
            and preflight.get("admitted_under_total_projected_bits_limit") is True,
            f"coordinate {index} exact-product total admission mismatch",
        )
        report_product = _product_from_admitted_report_plan(
            report_product_plan, aggregate_admitted
        )
        require(
            report_product == expected.product,
            f"coordinate {index} exact multiplicative product mismatch",
        )
        expression_products += 1

        interval = reported.get("interval")
        require(isinstance(interval, dict), f"coordinate {index} interval is absent")
        lower = _dyadic(interval.get("lower"), f"coordinate {index} lower")
        upper = _dyadic(interval.get("upper"), f"coordinate {index} upper")
        require(lower <= upper, f"coordinate {index} interval is inverted")
        decision = interval.get("decision")
        zero_witness = interval.get("exact_zero_witness")
        sign = expected.exact_sign
        if sign > 0:
            require(
                upper > 0,
                f"coordinate {index} interval contradicts exact positive sign",
            )
            require(
                exact_product.get("decision") == "certified_positive",
                f"coordinate {index} exact positive decision mismatch",
            )
            require(
                exact_product.get("exact_zero_witness") is None,
                f"coordinate {index} has a false exact-product zero witness",
            )
            positive += 1
        elif sign < 0:
            require(
                lower < 0,
                f"coordinate {index} interval contradicts exact negative sign",
            )
            require(
                exact_product.get("decision") == "certified_negative",
                f"coordinate {index} exact negative decision mismatch",
            )
            require(
                exact_product.get("exact_zero_witness") is None,
                f"coordinate {index} has a false exact-product zero witness",
            )
            negative += 1
        else:
            require(
                lower <= 0 <= upper,
                f"coordinate {index} interval excludes exact multiplicative zero",
            )
            require(
                exact_product.get("decision") == "certified_exact_zero",
                f"coordinate {index} exact-product zero decision mismatch",
            )
            require(
                exact_product.get("exact_zero_witness")
                == "exact_multiplicative_product_equals_one",
                f"coordinate {index} exact-product zero witness mismatch",
            )
            exact_zeros += 1
        exact_terms = reported.get("exact_terms")
        require(isinstance(exact_terms, list), f"coordinate {index} terms are absent")
        if exact_terms:
            expected_interval_decision = (
                "certified_positive"
                if lower > 0
                else "certified_negative"
                if upper < 0
                else "unresolved_sign"
            )
            require(
                zero_witness is None,
                f"coordinate {index} has a false interval zero witness",
            )
        else:
            expected_interval_decision = "certified_exact_zero"
            require(
                lower == 0 == upper,
                f"coordinate {index} empty expression is not exact-zero interval",
            )
            require(
                zero_witness == "canonical_exact_expression_has_no_terms",
                f"coordinate {index} interval zero witness mismatch",
            )
        require(
            decision == expected_interval_decision,
            f"coordinate {index} interval-local decision mismatch",
        )
        exact_signs += 1

    return CertificateChecks(
        expression_products=expression_products,
        exact_signs=exact_signs,
        exact_zeros=exact_zeros,
        certified_positive=positive,
        certified_negative=negative,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_signs(coordinates: Iterable[ProductCoordinate]) -> tuple[int, int, int]:
    positive = zero = negative = 0
    for coordinate in coordinates:
        if coordinate.exact_sign > 0:
            positive += 1
        elif coordinate.exact_sign < 0:
            negative += 1
        else:
            zero += 1
    return positive, zero, negative
