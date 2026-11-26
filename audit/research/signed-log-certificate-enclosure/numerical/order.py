"""Invert the three-source incidence matrix by rational row operations on explicit sets."""
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import runpy
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def branches(key):
    return tuple(frozenset(i for i in range(3) if mask & (1 << i)) for mask in key)


def order(lower, upper):
    return all(any(small <= large for small in branches(lower)) for large in branches(upper))


def antichains():
    result = []
    for length in range(1, 8):
        for key in combinations(range(1, 8), length):
            family = branches(key)
            if all(not (a <= b or b <= a) for a, b in combinations(family, 2)):
                result.append(key)
    return tuple(result)


def inverse(matrix):
    size = len(matrix)
    augmented = [[Fraction(a) for a in row] + [Fraction(i == j) for j in range(size)]
                 for i, row in enumerate(matrix)]
    for j in range(size):
        pivot = next(i for i in range(j, size) if augmented[i][j])
        augmented[j], augmented[pivot] = augmented[pivot], augmented[j]
        value = augmented[j][j]
        augmented[j] = [entry / value for entry in augmented[j]]
        for i in range(size):
            if i != j:
                factor = augmented[i][j]
                augmented[i] = [left-factor*right for left, right in zip(augmented[i], augmented[j], strict=True)]
    require(all(augmented[i][j] == int(i == j) for i in range(size) for j in range(size)),
            "left block is identity")
    rows = [row[size:] for row in augmented]
    require(all(a.denominator == 1 for row in rows for a in row), "integral inverse")
    return tuple(tuple(int(a) for a in row) for row in rows)


def run(path):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2",
            "original arithmetic")
    keys = antichains()
    require(len(keys) == 18 and all(order((1, 2, 4), key) and order(key, (7,)) for key in keys),
            "bottom, top and full carrier")
    require(order((1, 2), (3,)) and not order((3,), (1, 2)), "named strict orientation")
    matrix = tuple(tuple(int(order(col, row)) for col in keys) for row in keys)
    inv = inverse(matrix)
    for left, right in ((matrix, inv), (inv, matrix)):
        require(all(sum(x*y for x,y in zip(left[i],col,strict=True)) == int(i==j)
                    for i in range(len(keys)) for j,col in enumerate(zip(*right,strict=True))),
                "two exact inverse identities")
    original_key, original_matrix, original_inverse = runpy.run_path(str(path))["lattice"]()
    require(keys == original_key and matrix == original_matrix and inv == original_inverse,
            "exact published names, incidence and inverse")
    norms = [sum(abs(a) for a in row) for row in inv]
    require(max(norms) <= 18, "bound assumed in small-N argument")
    return {"three_source_keys": keys, "incidence": matrix, "inverse_rows": inv,
            "absolute_row_sums": norms, "largest_row_sum": max(norms), "largest_entry": max(abs(a) for row in inv for a in row),
            "left_and_right_identity_entries": 2*len(keys)**2, "native_source_entries_per_matrix":len(keys)**2}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), sort_keys=True, separators=(",", ":")))
