"""Check the finite categorical third-source budget by counting finite source events."""

import argparse
from collections import Counter
from fractions import Fraction
from functools import cache
from itertools import combinations, combinations_with_replacement, product
import json
from math import prod


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def subsets(items, minimum=0):
    ordered = tuple(items)
    for count in range(minimum, len(ordered) + 1):
        yield from combinations(ordered, count)


def below(left, right):
    return all(any((small & large) == small for small in left) for large in right)


def minimal_members(family):
    return tuple(x for x in family if all((x & y) != y for y in family if y != x))


MASKS = tuple(range(1, 8))
NODES = tuple(a for a in subsets(MASKS, 1) if minimal_members(a) == a)
ORDER = tuple(sorted(NODES, key=lambda a: (sum(below(b, a) for b in NODES), a)))
LOWER = {a: tuple(b for b in ORDER if a != b and below(b, a)) for a in ORDER}
OUTSIDE = tuple(a for a in ORDER if not below(a, (3,)))
require(len(ORDER) == len(set(ORDER)) == 18, "three-source antichains")
require(set(OUTSIDE) == {(4,), (5,), (6,), (5, 6), (7,)}, "five outside positions")


@cache
def possible_positive(masks):
    """Possible antichain of the positive lists in the logarithm series."""
    proper = sorted(set(masks) - {7})
    result = set()
    for selected in subsets(proper, 1):
        complement = [s for s in MASKS if all((s & y) != s for y in selected)]
        require(bool(complement), "a proper union of principal lower sets")
        result.add(minimal_members(complement))
    return frozenset(result)


def observe(law):
    """Return both local and averaged exponentials and the five-position gap."""
    require(type(law) is dict, "expected a dictionary of counts")
    require(all(type(z) is tuple and len(z) == 4 for z in law), "four fields per row")
    require(
        all(type(w) is int and w >= 0 for w in law.values()),
        "nonnegative integer counts",
    )
    table = {z: w for z, w in law.items() if w}
    require(bool(table), "at least one occupied joint row")
    rows = tuple(table)
    total = sum(table.values())
    averages = {node: [Fraction(1), Fraction(1)] for node in ORDER}
    local = {}
    combinations_per_node = 0
    for reference, weight in table.items():
        agree = {
            group: {
                row
                for row in rows
                if all(row[j] == reference[j] for j in range(3) if group & (1 << j))
            }
            for group in MASKS
        }
        event = {node: set.union(*(agree[group] for group in node)) for node in ORDER}
        two_parts = []
        for pool in (rows, tuple(row for row in rows if row[3] == reference[3])):
            mass = sum(table[row] for row in pool)
            values = {}
            for node in ORDER:
                good = sum(table[row] for row in pool if row in event[node])
                cumulative = Fraction(mass, good)
                values[node] = cumulative / prod(values[prior] for prior in LOWER[node])
                require(values[node] >= 1, "nonnegative categorical component")
            mask_set = frozenset(
                sum((row[j] == reference[j]) << j for j in range(3)) for row in pool
            )
            require(
                {node for node, value in values.items() if value > 1}
                == possible_positive(mask_set),
                "positive-list support disagrees with exact inversion",
            )
            two_parts.append(values)
            combinations_per_node += len(ORDER)
        prior, conditioned = two_parts
        require(
            all(conditioned[node] == 1 or prior[node] > 1 for node in ORDER),
            "conditional support outside unconditional support",
        )
        local[reference] = prior, conditioned
        for node in ORDER:
            averages[node][0] *= prior[node] ** weight
            averages[node][1] *= conditioned[node] ** weight
    entropy, conditional = Fraction(1), Fraction(1)
    for row, weight in table.items():
        first_two = sum(c for z, c in table.items() if z[:2] == row[:2])
        all_three = sum(c for z, c in table.items() if z[:3] == row[:3])
        pair_target = sum(
            c for z, c in table.items() if z[:2] == row[:2] and z[3] == row[3]
        )
        entropy *= Fraction(first_two, all_three) ** weight
        conditional *= Fraction(pair_target, weight) ** weight
    cuts = [averages[node] for node in OUTSIDE]
    require(
        (prod(z[0] for z in cuts), prod(z[1] for z in cuts)) == (entropy, conditional),
        "outside totals",
    )
    absolute = prod(max(p / q, q / p) for p, q in cuts)
    gap = entropy * conditional / absolute
    require(gap == prod(min(p, q) for p, q in cuts) ** 2, "identity for the deficit")
    require((gap == 1) == (conditional == 1), "criterion for equality")
    labels = len({z[2] for z in table})
    if conditional > 1:
        bound = minimum_factor(total, labels)
        require(gap >= bound, "claimed minimum exceeds the table result")
    return {
        "N": total,
        "ell": labels,
        "A": entropy,
        "B": conditional,
        "M": absolute,
        "gap": gap,
        "local": local,
        "averages": averages,
        "local_component_count": combinations_per_node,
    }


def minimum_factor(total, labels):
    """The exponential of N times the least positive gap, when it can exist."""
    require(
        type(total) is int and type(labels) is int and 2 <= labels <= total,
        "need 2 <= ell <= N",
    )
    available = total - labels + 2
    small = available // 2
    large = available - small
    return (Fraction(small + 1, small) * Fraction(large + 1, large)) ** 2


def witness(total, labels):
    minimum_factor(total, labels)
    available = total - labels + 2
    small = available // 2
    large = available - small
    table = {(0, 0, 0, 0): 1, (0, 0, 1, 0): 1}
    for label, count in enumerate([small - 1, large - 1] + [1] * (labels - 2)):
        if count:
            group = label + 1
            table[group, 0, label, group] = count
    return table


def census_cases():
    alphabet = tuple(product(range(2), repeat=4))
    for total in range(1, 4):
        for observed in combinations_with_replacement(alphabet, total):
            yield dict(Counter(observed))


def sharp_cases():
    return [(n, labels) for n in range(2, 17) for labels in range(2, n + 1)] + [
        (25, 2),
        (25, 3),
        (25, 25),
    ]


def adverse():
    base = (0, 0, 0, 0)

    def second(other):
        return observe({base: 1, other: 1})

    # Removing the target, source 1 or source 2 changes the conditioning in these rows.
    target = second((0, 0, 1, 1))
    s1 = second((1, 0, 1, 0))
    s2 = second((0, 1, 1, 0))
    require(
        target["A"] == 4 and target["B"] == 1, "target changes the conditional entropy"
    )
    require(s1["A"] == s2["A"] == 1, "either of the first two can determine source 3")
    require(
        second((0, 0, 1, 0))["gap"] == 16,
        "merging either conditioning variable creates a false conflict",
    )
    constant = observe({(0, 0, 0, 0): 3})
    require(
        constant["ell"] == 1 and constant["B"] == constant["gap"] == 1, "constant case"
    )
    negative = observe({(a, 0, b, a): 1 for a, b in product(range(2), repeat=2)})
    require(
        negative["averages"][(4,)][0] < negative["averages"][(4,)][1],
        "false component dominance",
    )
    require(
        any(
            p[node] > 1 and q[node] == 1
            for p, q in target["local"].values()
            for node in ORDER
        ),
        "converse to support implication fails",
    )
    exact = observe(witness(6, 2))
    require(
        exact["gap"] == Fraction(256, 81) < minimum_factor(6, 3),
        "declared unused label raises a false bound",
    )
    require(exact["gap"] < Fraction(4), "too large proposed lower factor")
    atom_zero = second((0, 0, 1, 0))
    require(
        atom_zero["B"] == 4 and atom_zero["M"] == 1,
        "positive entropy with zero signed mass",
    )
    doubled = {z: 2 * w for z, w in witness(6, 2).items()}
    repeated = observe(doubled)
    require(
        repeated["gap"] == exact["gap"] ** 2 > minimum_factor(12, 2),
        "repetition and fixed sample size",
    )
    zeros = {**witness(6, 2), (9, 9, 9, 9): 0}
    require(
        observe(zeros)["gap"] == exact["gap"] and observe(zeros)["ell"] == 2,
        "unoccupied name ignored",
    )
    invalid = [
        {},
        {base: 0},
        {base: -1},
        {base: True},
        {base: Fraction(1, 2)},
        {(0, 0, 0): 1},
    ]
    for case in invalid:
        try:
            observe(case)
        except ValueError:
            continue
        raise ValueError("invalid table accepted")
    return {
        "rejected_invalid_count_inputs": len(invalid),
        "target_conditioning": True,
        "both_conditioning_sources": True,
        "signed_component_dominance_refuted": True,
        "converse_support_implication_refuted": True,
        "overstated_or_unoccupied_bound_refuted": True,
        "count_repetition": True,
        "zero_count_ignored": True,
    }


def main(controls=False):
    census = Counter()
    minima = {}
    local_count = 0
    for table in census_cases():
        record = observe(table)
        local_count += record["local_component_count"]
        total = record["N"]
        census[total, "all"] += 1
        if record["B"] > 1:
            census[total, "positive_B"] += 1
            key = total, record["ell"]
            minima[key] = min(minima.get(key, record["gap"]), record["gap"])
        else:
            census[total, "zero_B"] += 1
    require(
        [census[n, "all"] for n in (1, 2, 3)] == [16, 136, 816],
        "binary table domain incomplete",
    )
    require(
        all(value == minimum_factor(*key) for key, value in minima.items()),
        "small labelled-domain minima",
    )
    sharp = []
    for n, ell in sharp_cases():
        o = observe(witness(n, ell))
        local_count += o["local_component_count"]
        require(
            o["N"] == n and o["ell"] == ell and o["A"] == o["B"] == 4,
            "input totals or entropy of the shared pair",
        )
        require(o["gap"] == minimum_factor(n, ell), "attaining construction")
        require(
            o["averages"][(4,)][1] == 4
            and all(o["averages"][i][1] == 1 for i in OUTSIDE if i != (4,)),
            "conditional mass is concentrated on the singleton third source",
        )
        sharp.append({"N": n, "ell": ell, "exp_N_gap": str(o["gap"])})
    result = {
        "units": "All listed ratios are exp(N times the quantity in nats).",
        "binary_labelled_census": [
            {
                "N": n,
                "tables": census[n, "all"],
                "B_positive": census[n, "positive_B"],
                "B_zero": census[n, "zero_B"],
            }
            for n in (1, 2, 3)
        ],
        "binary_observed_minima": [
            {"N": n, "ell": ell, "exp_N_gap": str(value)}
            for (n, ell), value in sorted(minima.items())
        ],
        "sharp_witnesses": sharp,
        "sharp_witness_count": len(sharp),
        "all18_local_component_checks_on_census_and_witnesses": local_count,
    }
    if controls:
        result["adverse_controls"] = adverse()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="also exercise the false claims and invalid tables",
    )
    print(json.dumps(main(parser.parse_args().self_test), indent=2, sort_keys=True))
