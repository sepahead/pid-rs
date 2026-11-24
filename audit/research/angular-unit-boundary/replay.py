"""Recompute the unit-axis order, the endpoint values and two four-moment examples."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent


def run(script, *arguments):
    interpreter = [sys.executable, *(["-O"] if not __debug__ else []), "-I", "-S", "-B"]
    command = [*interpreter, str(HERE / script), *map(str, arguments)]
    return subprocess.run(command, capture_output=True, check=True, timeout=120).stdout


def worked_bounds(second_radius, outer_radius):
    if not 0 < second_radius < outer_radius <= 1:
        raise ValueError("worked radii must be positive, ordered and at most one")
    k5, c5 = Fraction(7, 2560), Fraction(63, 256)
    upper = 4 * k5 * second_radius**8 / (1 - second_radius**2)
    lower = 3 * k5 * c5 * outer_radius**8
    if not 0 < upper < Fraction(1, 10**6) < lower:
        raise ValueError("the two four-moment bounds must give strict opposite signs")
    return upper, lower


def check_examples_reject_bad_inputs():
    invalid = [
        (Fraction(0), Fraction(39, 100)),
        (Fraction(39, 100), Fraction(3, 10)),
        (Fraction(3, 10), Fraction(101, 100)),
        (Fraction(37, 100), Fraction(39, 100)),
        (Fraction(3, 10), Fraction(31, 100)),
    ]
    for pair in invalid:
        try:
            worked_bounds(*pair)
        except ValueError:
            continue
        raise ValueError("a changed radius or tolerance decision was accepted")
    return len(invalid)


def read_independent_program(name):
    folder = HERE / "independent"
    raw = run("independent/" + name + ".py")
    if raw != (folder / (name + ".json")).read_bytes():
        raise ValueError(name + " differs from its original returned bytes")
    return json.loads(raw)


def check_independent_routes(candidate_scale, candidate, outer_radius):
    # The published source removes one final blank line from the original reader.
    original = (HERE / "independent/axial_coefficient.py").read_bytes() + b"\n"
    if hashlib.sha256(original).hexdigest() != "9a293bdfdb4e2a9d281afe1705e5b283e469da070e788a657e870ad85db677f0":
        raise ValueError("the exact originally returned axial source cannot be reconstructed")
    coefficient = read_independent_program("axial_coefficient")
    dyadic = read_independent_program("dyadic_prefix")
    directional = read_independent_program("four_directions")
    order = candidate["order"]
    if coefficient["least"] != order or dyadic["primary"]["minimal_even_terms"] != order:
        raise ValueError("the other order computations disagree")
    for key, dyadic_key in (("previous", "F_previous_times_10_to_24"),
                            ("current", "F_minimal_times_10_to_24")):
        bounds = [
            (candidate[key], candidate_scale),
            (coefficient[key]["F_scaled"], coefficient["scaled_residual_denominator"]),
            (dyadic["primary"][dyadic_key], 10**24),
            (dyadic["doubled"][dyadic_key], 10**24),
        ]
        left = max(Fraction(interval[0], scale) for interval, scale in bounds)
        right = min(Fraction(interval[1], scale) for interval, scale in bounds)
        if left > right:
            raise ValueError("the separately scaled residual intervals are disjoint")
    n22 = directional["three_tenths_N22"]
    if not n22["pure-second"]["ppm_times_10_to_12"][1] < 10**12 < n22["pure-first"]["ppm_times_10_to_12"][0]:
        raise ValueError("the different directional calculation must separate the axes")
    second_constant = Fraction(directional["universal_coefficient_for_r_to_eight"])
    if not second_constant * outer_radius**8 == Fraction(directional["lower_bound_at_39_over_100"]) > Fraction(1, 10**6):
        raise ValueError("the independent all-direction bound must exceed the tolerance")
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="also require five changed radius examples to be rejected")
    args = parser.parse_args()

    candidate_bytes = (HERE / "certificate.json").read_bytes()
    if run("prefix_order.py") != candidate_bytes:
        raise ValueError("directed partial sum and signed record differ")
    judge = json.loads(run("judge.py", HERE / "certificate.json", "--self-test"))
    endpoint = run("boundary.py")
    if endpoint != (HERE / "boundary-values.json").read_bytes():
        raise ValueError("boundary scalar record differs")
    upper, lower = worked_bounds(Fraction(3, 10), Fraction(39, 100))
    result = {
        "order": judge["order"],
        "rejected": judge["rejected"],
        "scalar": json.loads(endpoint),
        "independent_axial_signs": judge["independent_enclosures"],
        "r_3_over_10_second_axis_upper": [upper.numerator, upper.denominator],
        "r_39_over_100_every_direction_lower": [lower.numerator, lower.denominator],
    }
    candidate = json.loads(candidate_bytes)
    result["independent_programs_replayed"] = check_independent_routes(candidate["scale"], candidate, Fraction(39, 100))
    if args.self_test:
        result["rejected_changed_radius_examples"] = check_examples_reject_bad_inputs()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
