#!/usr/bin/env python3
"""Compare the three changes in local shared information with exact integer arithmetic.

The original September program defines the 4,000 trial slots, random draws and
scale. This check repeats that finite design. Floating-point draws select the
integer laws. All decisions on a selected law use Python integers.
"""
import argparse
from functools import lru_cache
import hashlib
from itertools import combinations, product
import json
import random


TRIALS = 4_000
SEED = 1
SCALE = 10**12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def shares(rng, total, count):
    weights = [rng.random() + 1e-6 for _ in range(count)]
    weight_sum = sum(weights)
    parts = [int(total * x / weight_sum) for x in weights]
    parts[0] += total - sum(parts)
    return parts


def trials():
    rng = random.Random(SEED)
    for trial in range(TRIALS):
        sources = rng.choice([2, 2, 3])
        alphabet = [rng.choice([2, 2, 3]) for _ in range(sources)] + [rng.choice([2, 3])]
        cells = tuple(product(*(range(a) for a in alphabet)))
        support = [i for i in range(len(cells)) if rng.random() < 0.7]
        if len(support) < 2:
            yield trial, alphabet, False, None
            continue
        positive = {i: 1 + int((rng.random() ** rng.choice([1, 3, 6])) * 10**6) for i in support}
        before = [positive.get(i, 0) * SCALE for i in range(len(cells))]
        small = rng.random() < 0.25
        u = 10 ** rng.uniform(-12, -1.3) if small else rng.uniform(0.05, 0.999)
        move = int(u * min(before[i] for i in support))
        if move == 0:
            yield trial, alphabet, small, None
            continue
        donor_count = rng.randint(1, min(3, len(support) - 1))
        donors = rng.sample(support, donor_count)
        others = [i for i in support if i not in donors]
        receivers = rng.sample(others, rng.randint(1, min(3, len(others))))
        after = before.copy()
        for i, amount in zip(donors, shares(rng, move, len(donors)), strict=True):
            after[i] -= amount
        for i, amount in zip(receivers, shares(rng, move, len(receivers)), strict=True):
            after[i] += amount
        yield trial, alphabet, small, (support, before, after, move)


@lru_cache(maxsize=None)
def incidence(alphabet):
    cells = tuple(product(*(range(a) for a in alphabet)))
    sources = range(len(alphabet) - 1)
    groups = [frozenset(g) for k in range(1, len(sources) + 1) for g in combinations(sources, k)]
    antichains = [combo for k in range(1, len(groups) + 1) for combo in combinations(groups, k)
                  if all(not (a < b or b < a) for a, b in combinations(combo, 2))]
    result = []
    for cell in cells:
        target = tuple(j for j, other in enumerate(cells) if other[-1] == cell[-1])
        events = []
        for antichain in antichains:
            source = tuple(j for j, other in enumerate(cells)
                           if any(all(cell[i] == other[i] for i in g) for g in antichain))
            events.append((source, tuple(j for j in target if j in source)))
        result.append((target, events))
    return result


def law_premises(support, before, after, move):
    require(len(before) == len(after) and len(before) > 0, "different or empty alphabets")
    require(all(type(v) is int and v >= 0 for u in (before, after) for v in u), "invalid cell mass")
    occupied = [i for i, w in enumerate(before) if w]
    require(len(occupied) >= 2 and occupied == support == [i for i, w in enumerate(after) if w],
            "the two laws must have the same recorded support")
    require(sum(before) == sum(after), "total mass changed")
    minimum = min(before[i] for i in occupied)
    require(type(move) is int and 0 < move < minimum, "move is outside the stated range")
    require(sum(abs(p - q) for p, q in zip(before, after, strict=True)) == 2 * move,
            "the recorded move does not give the actual total variation")
    return minimum


def relation(numerator, denominator, minimum, move):
    """Return -1, 0 or 1 for |log(numerator/denominator)| compared with Lambda."""
    require(min(numerator, denominator, minimum - move, move) > 0, "positive factors required")
    high, low = max(numerator, denominator), min(numerator, denominator)
    difference = high * (minimum - move) - low * minimum
    return (difference > 0) - (difference < 0)


def observe():
    cases = evaluations = small_trials = 0
    equality = [0, 0, 0]
    larger = [0, 0, 0]
    hasher = hashlib.sha256()
    for trial, alphabet, small, selected in trials():
        small_trials += int(small)
        if selected is None:
            continue
        support, before, after, move = selected
        minimum = law_premises(support, before, after, move)
        cases += 1
        row = json.dumps([trial, alphabet, before, after], separators=(",", ":")).encode("ascii")
        hasher.update(row + bytes([10]))
        rows = incidence(tuple(alphabet))
        for i in support:
            target, events = rows[i]
            pc = sum(before[j] for j in target)
            qc = sum(after[j] for j in target)
            for source, joint in events:
                pa = sum(before[j] for j in source)
                qa = sum(after[j] for j in source)
                pb = sum(before[j] for j in joint)
                qb = sum(after[j] for j in joint)
                factors = ((pa, qa), (qc * pb, qb * pc), (pa * qb * pc, qa * qc * pb))
                for k, (top, bottom) in enumerate(factors):
                    order = relation(top, bottom, minimum, move)
                    equality[k] += order == 0
                    larger[k] += order > 0
                evaluations += 1
    require(not any(larger), "a change exceeds the proposed bound")
    return {"seed": SEED, "trial_slots": TRIALS, "laws": cases, "small_draws": small_trials,
            "law_sha256": hasher.hexdigest(), "cell_antichain_pairs": evaluations,
            "larger": larger, "equal": equality, "strictly_below": [evaluations - k for k in equality],
            "order": ["informative", "misinformative", "signed"]}


def self_test():
    for upper, lower, expected in [(3, 2, 0), (2, 3, 0), (1, 1, -1), (2, 1, 1)]:
        require(relation(upper, lower, 3, 1) == expected, "positive, inverse and order controls")
    near = 10**70
    require(relation(near + 1, near, near, 1) == -1 and 10**60 * near < near**2 - 1,
            "near equality remains strict")
    require(law_premises([0, 1, 2], [near + 1, near, near], [near, near + 1, near], 1) == near,
            "the near-bound example is a genuine constant-total law")
    bad = [([0, 1], [3, 3], [2, 3], 1), ([0, 1], [3, 3, 0], [2, 3, 1], 1),
           ([0, 1], [3, 3], [2, 4], 2), ([0, 1], [3, 3], [0, 6], 3),
           ([0, 1], [3, 3], [2.0, 4], 1), ([0, 1], [3, 3], [2, 4], True)]
    for args in bad:
        try:
            law_premises(*args)
        except ValueError:
            continue
        raise ValueError("invalid law passed the premise check")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="also check the premise and equality controls")
    options = parser.parse_args()
    if options.self_test:
        self_test()
    print(json.dumps(observe(), indent=2, sort_keys=True))
