"""Replay the four-moment angular certificate using exact rational arithmetic."""

from argparse import ArgumentParser
from copy import deepcopy
from fractions import Fraction
from functools import cache
from hashlib import sha256
import json
from math import comb
from pathlib import Path


MOMENTS = 4
LAST_TERM = 12
GRID = 4096
LAST_INDEX = 2048
TOLERANCE = Fraction(1, 1_000_000)
WIDTH_LIMIT = Fraction(1, 64)
CERTIFICATE = Path(__file__).with_name("certificate.json")
IDENTITY = {
    "paper": "Ehrlich et al., arXiv:2311.06373v3",
    "model": "four scalar radian angles; normalized positive two-harmonic torus density",
    "gauge": "fixed common radian coordinates and product Lebesgue measure",
    "atom": "signed averaged top atom J-R(1)-R(2/3)+2R(1/2), in nats",
    "truncation": "four even moments in J only; proper terms exact",
    "radius": "absolute amplitude sum in (0,1/2]",
    "upper_witness": "a=r,b=0",
    "tolerance": "strict true relative error 1/1000000 with actual atom denominator",
    "certificate": "twelve finite terms with one-sided geometric remainders",
}


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def canonical(record):
    return (
        json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def exact_pair(value):
    return [str(value.numerator), str(value.denominator)]


@cache
def cosine_moment(index):
    return Fraction(comb(2 * index, index), 4**index)


def denominator(index):
    return 2 * index * (2 * index - 1)


@cache
def proper_coefficient(weight, index):
    return cosine_moment(index) * (
        weight ** (2 * index - 1) / (2 * index - 1)
        - weight ** (2 * index) / (2 * index)
    )


def bounds(radius):
    """Return the uniform upper bound, axial numerator lower bound and axial atom upper bound."""
    require(
        isinstance(radius, Fraction) and 0 < radius <= Fraction(1, 2),
        "outside the stated exact field",
    )
    squared = radius * radius
    powers = [Fraction(1)]
    for _ in range(LAST_TERM + 1):
        powers.append(powers[-1] * squared)
    remainder_index = LAST_TERM + 1
    terms = range(MOMENTS + 1, LAST_TERM + 1)
    uniform = 8 * (
        sum(cosine_moment(j) * powers[j - 1] / denominator(j) for j in terms)
        + cosine_moment(remainder_index)
        * powers[LAST_TERM]
        / (denominator(remainder_index) * (1 - squared))
    )
    tail = sum(cosine_moment(j) * powers[j] / denominator(j) for j in terms)
    half = Fraction(1, 2)
    two_thirds = Fraction(2, 3)

    def proper_prefix(weight):
        return sum(
            proper_coefficient(weight, j) * powers[j] for j in range(1, LAST_TERM + 1)
        )

    exponent = 2 * LAST_TERM + 1
    remainder = (
        powers[remainder_index]
        * half**exponent
        / (exponent * (1 - squared * half * half))
    )
    upper_atom = 2 * (proper_prefix(half) + remainder) - proper_prefix(two_thirds)
    return uniform, tail, upper_atom


def grid_result():
    lower = upper = None
    for index in range(1, LAST_INDEX + 1):
        uniform, tail, upper_atom = bounds(Fraction(index, GRID))
        if uniform < TOLERANCE:
            lower = index, uniform
        if upper is None and upper_atom > 0 and tail > TOLERANCE * upper_atom:
            upper = index, tail, upper_atom
    require(lower is not None and upper is not None, "one endpoint is missing")
    lower_index, uniform = lower
    upper_index, tail, upper_atom = upper
    width = Fraction(upper_index - lower_index, GRID)
    require(0 < width <= WIDTH_LIMIT, "interval exceeds registered width")
    return {
        "schema": "angular-four-radius-certificate-v1",
        "identity": IDENTITY,
        "lower_index": lower_index,
        "upper_index": upper_index,
        "width": exact_pair(width),
        "uniform_slack": exact_pair(TOLERANCE - uniform),
        "axial_tail_lower": exact_pair(tail),
        "axial_atom_upper": exact_pair(upper_atom),
        "failure_slack": exact_pair(tail - TOLERANCE * upper_atom),
    }


def read_certificate(raw, expected):
    # Canonical bytes also fix key uniqueness, integer types and reduced fraction spellings.
    require(
        len(raw) <= 8192 and raw == canonical(expected),
        "certificate differs from the exact grid result",
    )
    return json.loads(raw)


def self_test(expected):
    changes = [
        ("identity", "gauge", "degrees with a rescaled source"),
        ("identity", "tolerance", "relative to the full mutual information J"),
        ("identity", "truncation", "replace all proper terms by four moments"),
        ("identity", "upper_witness", "a=0,b=r"),
        ("identity", "certificate", "use a majorant crossing for failure"),
        ("top", "lower_index", expected["lower_index"] + 1),
        ("top", "upper_index", expected["upper_index"] - 1),
        ("top", "width", ["0", "1"]),
        ("top", "failure_slack", ["0", "1"]),
        ("top", "uniform_slack", expected["failure_slack"]),
        ("top", "axial_atom_upper", expected["axial_tail_lower"]),
        ("top", "axial_tail_lower", expected["axial_atom_upper"]),
    ]
    for location, key, wrong in changes:
        record = deepcopy(expected)
        destination = record["identity"] if location == "identity" else record
        destination[key] = wrong
        try:
            read_certificate(canonical(record), expected)
        except ValueError:
            continue
        raise RuntimeError(f"accepted altered field {key}")
    for radius in (Fraction(0), Fraction(3, 4), Fraction(1), Fraction(2), 0.25):
        try:
            bounds(radius)
        except ValueError:
            continue
        raise RuntimeError(f"accepted unsupported input {radius}")
    for index in (expected["lower_index"], expected["upper_index"]):
        uniform, tail, upper_atom = bounds(Fraction(index, GRID))
        require(
            uniform > 0 and tail > 0 and upper_atom > 0,
            "invalid positive endpoint control",
        )
    return len(changes) + 5


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="also check the altered records and unsupported inputs",
    )
    args = parser.parse_args()
    expected = grid_result()
    raw = CERTIFICATE.read_bytes()
    record = read_certificate(raw, expected)
    lower_radius = Fraction(record["lower_index"], GRID)
    upper_radius = Fraction(record["upper_index"], GRID)
    uniform, _, _ = bounds(lower_radius)
    _, tail, upper_atom = bounds(upper_radius)
    scale = 10**12
    scaled_upper = uniform * scale
    scaled_lower = tail / upper_atom * scale
    output = {
        "certificate_sha256": sha256(raw).hexdigest(),
        "grid_points": LAST_INDEX,
        "uniform_radius": str(lower_radius),
        "failure_radius": str(upper_radius),
        "width": str(upper_radius - lower_radius),
        "display_denominator": scale,
        "uniform_ceiling_numerator": -(
            -scaled_upper.numerator // scaled_upper.denominator
        ),
        "axial_floor_numerator": scaled_lower.numerator // scaled_lower.denominator,
    }
    if args.self_test:
        output["negative_controls_rejected"] = self_test(expected)
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
