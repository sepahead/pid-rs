"""Check every anchor and rank of integer instances of both mean upper constructions."""
from fractions import Fraction
import json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def harmonic(m):
    return sum((Fraction(1, j) for j in range(1, m + 1)), Fraction(0))


def count(rows, anchor, k):
    assert_dimensions = len(rows[anchor]) in (2, 3) and all(len(row) == len(rows[anchor]) for row in rows)
    require(assert_dimensions and 0 < k < len(rows), "geometry or rank")
    diffs = []
    for index, row in enumerate(rows):
        if index != anchor:
            coords = [abs(a - b) for a, b in zip(row, rows[anchor], strict=True)]
            diffs.append((min(coords[:-1]), coords[-1]))
    joint = sorted(max(s, t) for s, t in diffs)
    radius = joint[k - 1]
    require(radius > 0, "zero radius")
    require(joint.count(radius) == 1 and sum(j < radius for j in joint) == k - 1, "multiple shell rows")
    return 1 + sum(s < radius for s, t in diffs), 1 + sum(t < radius for s, t in diffs)


def expect_refusal(rows, message):
    try:
        count(rows, 0, 1)
    except ValueError as error:
        require(str(error) == message, "different refusal")
    else:
        raise ValueError("invalid controls admitted")


def main():
    output = []
    for dimension in (2, 3):
        for perturbed in (False, True):
            anchors_and_ranks = 0
            average_checks = 0
            for n in range(2, 13):
                scale = 2**n
                rows = []
                for i in range(n):
                    first = scale * 2**i
                    target = (scale + int(perturbed)) * 2**i
                    rows.append((first, target) if dimension == 2 else (first, 2*first, target))
                for k in range(1, n):
                    upper = harmonic(n-1) - harmonic(k-1) - (Fraction(1, k) if perturbed else 0)
                    locals_at_rank = []
                    for anchor in range(n):
                        x, y = count(rows, anchor, k)
                        require((x, y) == (k + int(perturbed), k), "count pair")
                        local = harmonic(k-1) + harmonic(n-1) - harmonic(x-1) - harmonic(y-1)
                        require(local == upper, "local upper")
                        locals_at_rank.append(local)
                        anchors_and_ranks += 1
                    require(sum(locals_at_rank) / n == upper, "mean upper")
                    average_checks += 1
            output.append(dict(dimension=dimension, perturbed=perturbed, n_min=2, n_max=12,
                               local_checks=anchors_and_ranks, mean_checks=average_checks))
    expect_refusal([(0, 0), (0, 0)], "zero radius")
    expect_refusal([(0, 0), (1, 2), (2, 1)], "multiple shell rows")
    require(count([(0, 0), (2, 1)], 0, 1) == (1, 2), "opposite active component")
    print(json.dumps({"panels": output, "controls": 3}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
