"""Check two population bounds on a fixed finite amplitude and phase grid."""

import hashlib
import json
import math
import sys

import numpy as np


PHASE_COUNT = 2048
PARAMETER_COUNT = 67
MOMENTS = 8
TOLERANCE = 1e-15  # Absolute tolerance in nats for this binary64 diagnostic.
COSINES = np.cos(2 * np.pi * np.arange(PHASE_COUNT) / PHASE_COUNT)
COEFFICIENTS = tuple(1 / (2 * m * (2 * m - 1)) for m in range(1, MOMENTS + 1))


def proper(a, weight):
    """Average (1 + a cos v) log(1 + weight a cos v) at the phase points."""
    return float(np.mean((1 + a * COSINES) * np.log1p(weight * a * COSINES)))


def joint_terms(a, b, include):
    """Compute the full joint average and, if requested, its eight-moment sum."""
    full = 0.0
    partial = 0.0
    second = b * COSINES
    # A block has 64 rows and 2,048 columns. Every phase pair has equal weight.
    for start in range(0, PHASE_COUNT, 64):
        y = a * COSINES[start : start + 64, None] + second
        full += float(np.sum((1 + y) * np.log1p(y)))
        if include:
            square = np.square(y)
            # Horner's rule evaluates the same even polynomial at each phase pair.
            polynomial = np.full_like(y, COEFFICIENTS[-1])
            for coefficient in reversed(COEFFICIENTS[:-1]):
                polynomial *= square
                polynomial += coefficient
            partial += float(np.sum(square * polynomial))
    return full / PHASE_COUNT**2, partial / PHASE_COUNT**2


def amplitude_indices():
    return range(-(PARAMETER_COUNT // 2), PARAMETER_COUNT // 2 + 1)


def record_margin(record, pair_hash, i, j, margin):
    a, b = 3 * i / 100, 3 * j / 100
    if not math.isfinite(margin):
        raise ArithmeticError(f"nonfinite margin at ({a}, {b})")
    pair_hash.update(f"{i},{j}\n".encode("ascii"))
    record["pairs"] += 1
    if record["at"] is None or margin < record["minimum_margin_nats"]:
        record["minimum_margin_nats"] = margin
        record["at"] = [a, b]
        record["at_indices"] = [i, j]


def check_grid():
    lower = {"pairs": 0, "at": None, "minimum_margin_nats": None}
    tail = {"pairs": 0, "at": None, "minimum_margin_nats": None}
    lower_hash = hashlib.sha256()
    tail_hash = hashlib.sha256()
    indices = amplitude_indices()
    for i in indices:
        a = 3 * i / 100
        correction = -proper(a, 1.0) - proper(a, 2 / 3) + 2 * proper(a, 1 / 2)
        for j in indices:
            ring = abs(i) + abs(j)
            if ring == 0 or ring > 33:
                continue
            b = 3 * j / 100
            radius = 3 * ring / 100
            include_tail = ring <= 30
            full, partial = joint_terms(a, b, include_tail)
            atom = full + correction
            record_margin(lower, lower_hash, i, j, atom - (a * a / 8 + b * b / 4))
            if include_tail:
                bound = radius**18 / (18 * 17 * (1 - radius * radius))
                record_margin(tail, tail_hash, i, j, bound - (full - partial))
    for name, record in (("lower", lower), ("tail", tail)):
        if record["pairs"] == 0:
            raise ArithmeticError(f"empty set of {name} comparisons")
        if record["minimum_margin_nats"] < -TOLERANCE:
            raise ArithmeticError(f"{name} margin below tolerance at {record['at']}")
    lower["integer_pairs_sha256"] = lower_hash.hexdigest()
    tail["integer_pairs_sha256"] = tail_hash.hexdigest()
    return lower, tail


def examples():
    result = []
    for a, b in ((0.25, 0.25), (0.5, 0.0)):
        full, partial = joint_terms(a, b, True)
        marginal = proper(a, 1.0)
        values = {
            "atom_nats": full - marginal - proper(a, 2 / 3) + 2 * proper(a, 1 / 2),
            "lower_bound_nats": a * a / 8 + b * b / 4,
            "tail_nats": full - partial,
            "tail_bound_nats": (abs(a) + abs(b)) ** 18
            / (18 * 17 * (1 - (abs(a) + abs(b)) ** 2)),
            "added_conditional_information_nats": full - marginal,
        }
        if not all(math.isfinite(value) for value in values.values()):
            raise ArithmeticError(f"nonfinite example at ({a}, {b})")
        result.append({"a": a, "b": b, **values})
    return result


def main():
    try:
        with np.errstate(invalid="raise", divide="raise", over="raise"):
            lower, tail = check_grid()
            report = {
                "passed": True,
                "lower": lower,
                "tail": tail,
                "moments": MOMENTS,
                "phase_count": PHASE_COUNT,
                "parameter_count": PARAMETER_COUNT,
                "tolerance_nats": TOLERANCE,
                "numpy_version": np.__version__,
                "examples": examples(),
            }
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    except (ArithmeticError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
