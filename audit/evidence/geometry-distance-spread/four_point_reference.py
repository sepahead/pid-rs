"""Exact finite comparison for the existing four-point standard-error consumer."""

from fractions import Fraction
from itertools import combinations
import json


def words(seed):
    mask = 2**64 - 1
    state = seed ^ 0xCAFEF00DD15EA5E5
    while True:
        state = (state + 0x9E3779B97F4A7C15) & mask
        value = ((state ^ (state >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        yield value ^ (value >> 31)


def quadruple(stream):
    options = list(range(5))
    picked = []
    for bound in (5, 4, 3, 2):
        threshold = 2**64 % bound
        word = next(stream)
        while word < threshold:
            word = next(stream)
        picked.append(options.pop(word % bound))
    return tuple(sorted(picked))


def main():
    distances = []
    for i in range(5):
        row = []
        for j in range(5):
            ring = min((i - j) % 5, (j - i) % 5)
            value = (Fraction(0), Fraction(1), Fraction(15, 8))[ring]
            row.append(value - Fraction(1, 2**53) if {i, j} == {0, 1} else value)
        distances.append(row)
    for i in range(5):
        for j in range(5):
            achieved = max(abs(a-b) for a, b in zip(distances[i], distances[j]))
            if achieved != distances[i][j]:
                raise ValueError("distance-vector embedding changed the metric")
    deltas = {}
    for ids in combinations(range(5), 4):
        i, j, k, l = ids
        pairs = sorted((distances[i][j] + distances[k][l],
                        distances[i][k] + distances[j][l],
                        distances[i][l] + distances[j][k]))
        deltas[ids] = (pairs[-1] - pairs[-2]) / 2
    stream = words(0)
    drawn = [quadruple(stream) for _ in range(16)]
    selected = [deltas[q] for q in drawn]
    if len(set(selected)) != 2:
        raise ValueError("sample failed to exercise both represented values")
    mean = sum(selected) / len(selected)
    se_squared = sum((x - mean)**2 for x in selected) / (16 * 15)
    return {"seed": 0, "sample_count": 16,
            "delta_by_quadruple": {str(k): str(v) for k, v in deltas.items()},
            "count_by_delta": {str(v): selected.count(v) for v in sorted(set(selected))},
            "ideal_mean_of_drawn_values": str(mean),
            "sample_mean_standard_error_squared": str(se_squared)}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, indent=2))
