"""Compare the copy-target identity with all 18 local signed categorical atoms."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path


REFERENCE_SHA = "00b52c8e5e514d3bac05190352489aa6954814e06efff0b321cacafdb7122940"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference(filename):
    require(sha256(filename.read_bytes()).hexdigest() == REFERENCE_SHA, "reference identity")
    handle = spec_from_file_location("finite_budget_reference", filename)
    module = module_from_spec(handle)
    handle.loader.exec_module(module)
    return module


def observations(matrix):
    require(len(matrix) > 0 and len(matrix[0]) > 0, "nonempty matrix")
    require(all(len(row) == len(matrix[0]) for row in matrix), "rectangular matrix")
    require(all(type(c) is int and c >= 0 for row in matrix for c in row),
            "integer cell counts")
    weights = {(x, w): c for x, row in enumerate(matrix) for w, c in enumerate(row) if c}
    require(bool(weights), "positive total")
    return weights


def star_components(weights):
    graph = {}
    for x, w in weights:
        a, b = (0, x), (1, w)
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    remaining = set(graph)
    while remaining:
        start = remaining.pop()
        active = [start]
        branch_vertices = 0
        while active:
            node = active.pop()
            branch_vertices += len(graph[node]) >= 2
            for other in graph[node]:
                if other in remaining:
                    remaining.remove(other)
                    active.append(other)
        if branch_vertices > 1:
            return False
    return True


def check_one(matrix, exact):
    weights = observations(matrix)
    observed = exact.observe({(x, 0, w, x): c for (x, w), c in weights.items()})
    total = sum(weights.values())
    row, column = Counter(), Counter()
    for (x, w), count in weights.items():
        row[x] += count
        column[w] += count
    # Each factor is the exponential of the local information in nats.
    expected_mass = Fraction(1)
    for (x, w), count in weights.items():
        a, b = row[x], column[w]
        union = a + b - count
        correction = Fraction(a * b, count * union)
        require(correction >= 1, "the sign of the correction at an occupied cell")
        expected = {
            (1, 4): Fraction(total, union),
            (1,): Fraction(union, a),
            (4,): 1 / correction,
            (5,): correction,
        }
        prior, conditioned = observed["local"][(x, 0, w, x)]
        require(all(prior[node] / conditioned[node] == expected.get(node, 1)
                    for node in exact.ORDER), "all 18 local signed atoms")
        expected_mass *= correction ** (2 * count)
    require(observed["M"] == expected_mass, "five-position absolute mass")
    require((expected_mass == 1) == star_components(weights), "star components")
    return expected_mass, total, len(weights)


def covered_shapes(exact):
    result = []
    for height, width, largest in [(2, 2, 2), (2, 3, 2), (3, 3, 1)]:
        zero = positive = cells = 0
        for flat in product(range(largest + 1), repeat=height*width):
            if not any(flat):
                continue
            matrix = [flat[i:i+width] for i in range(0, len(flat), width)]
            mass, _, occupied = check_one(matrix, exact)
            cells += occupied
            if mass == 1:
                zero += 1
            else:
                positive += 1
        require(zero + positive == (largest + 1) ** (height * width) - 1, "coverage")
        result.append({"shape": [height, width], "largest_cell_count": largest,
                       "zero_mass": zero, "positive_mass": positive,
                       "local_signed_comparisons": 18 * cells})
    return result


def adverse(exact):
    uniform = [[1,1],[1,1]]
    positive, n, _ = check_one(uniform, exact)
    require(positive > 1, "independence can have positive absolute mass")
    changed_target = exact.observe({(x,0,w,0):1 for x,w in product(range(2), repeat=2)})
    duplicated_source = exact.observe({(x,w,w,x):1 for x,w in product(range(2), repeat=2)})
    reversed_target = exact.observe({(x,0,w,w):1 for x,w in product(range(2), repeat=2)})
    require(changed_target["M"] == duplicated_source["M"] == 1 != positive, "copy and constant premises")
    require(reversed_target["M"] != positive, "choice of target")
    first = [[1,0,0],[0,1,1],[0,1,0]]
    second = [[0,1,0],[1,0,1],[0,1,0]]
    first_mass, _, _ = check_one(first, exact)
    second_mass, _, _ = check_one(second, exact)
    require(first_mass == Fraction(16,9) and second_mass == 1,
            "same marginals and two different local support structures")
    require(any(sum(v > 0 for v in row) > 1 for row in second)
            and any(sum(v > 0 for v in col) > 1 for col in zip(*second)), "mixed star orientations")
    weighted, new_n, _ = check_one([[1, 2], [3, 4]], exact)
    require(weighted**n != positive**new_n, "magnitudes differ after reweighting common support")
    refused = []
    for label, invalid in [("negative", [[-1, 2]]), ("boolean", [[True]]),
                           ("fractional count", [[Fraction(1, 2)]]),
                           ("zero total", [[0]]), ("ragged", [[1],[0,2]])]:
        try:
            observations(invalid)
        except ValueError:
            refused.append(label)
        else:
            raise ValueError("accepted invalid matrix: " + label)
    return {"domain_refusals": refused,
            "complete_uniform_exp_NM": str(positive),
            "weighted_same_support_exp_NM": str(weighted),
            "constant_target_exp_NM": str(changed_target["M"]),
            "duplicate_middle_source_exp_NM": str(duplicated_source["M"]),
            "target_copies_third_exp_NM": str(reversed_target["M"]),
            "paired_exp_four_M": [str(first_mass), str(second_mass)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    engine = reference(args.reference)
    print(json.dumps({"censuses": covered_shapes(engine), "controls": adverse(engine),
                      "factor": "exp(N M), with M in nats and N the input total",
                      "general_reference_sha256": REFERENCE_SHA},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
