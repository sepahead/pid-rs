"""Cross-check: pid-rs atoms summed over a threshold down-set equal the Hamming-ball log-score gain.

Input: the categorical dump retained with the cross-implementation re-verification report,
audit/evidence/cross-implementation-reverification-2026-09-26/inputs/discrete_dump.json. It holds
60 seeded systems with 2, 3 or 4 sources, their rows, and the averaged atoms that pid-rs
`discrete_sxpid_n` returned.

For each system and each fault budget f = 0, ..., m-1, the script computes two numbers:

1. the sum of the pid-rs averaged net atoms over the down-set of the threshold antichain
   alpha_f = {all (m-f)-subsets of the sources}, using the redundancy order of the antichains;
2. directly from the rows, H(T) - E[-log q_f(T | S)], where q_f(t | s) is the empirical
   probability of target t among the rows within Hamming distance f of s.

By the Mobius inversion, (1) is the averaged net cumulative term of alpha_f, and by the threshold
lemma its event is the Hamming ball, so (1) and (2) must agree. The script exits with status 1 if
a consumed input field is malformed or if any difference exceeds 1e-12 nats.
Unrelated output fields in the shared dump are not validated by this check.
"""
import itertools
import json
import math
import sys
from collections import Counter

TOLERANCE = 1e-12


def reject_duplicate_keys(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise SystemExit(f"duplicate JSON key in {keys!r}")
    return dict(pairs)


def reject_constant(value):
    raise SystemExit(f"nonfinite JSON constant: {value}")


def antichain_of(masks):
    return frozenset(frozenset(i for i in range(8) if m >> i & 1) for m in masks)


def leq(a, b):
    """Redundancy order: a <= b when every collection of b contains a collection of a."""
    return all(any(x <= y for x in a) for y in b)


def hamming_gain(rows, m, f):
    law = Counter(rows)
    n = len(rows)
    target = Counter(r[m] for r in rows)
    h_t = -sum((c / n) * math.log(c / n) for c in target.values())
    loss = 0.0
    for z, c in law.items():
        s, t = z[:m], z[m]
        ball = [(y, cy) for y, cy in law.items() if sum(y[i] != s[i] for i in range(m)) <= f]
        pb = sum(cy for _, cy in ball)
        pbt = sum(cy for y, cy in ball if y[m] == t)
        loss += (c / n) * -math.log(pbt / pb)
    return h_t - loss


def validated_case(case, index):
    if type(case) is not dict:
        raise SystemExit(f"system {index}: expected an object")
    m = case.get("n_sources")
    if type(m) is not int or m not in (2, 3, 4):
        raise SystemExit(f"system {index}: expected 2, 3 or 4 sources")
    sources, target = case.get("sources"), case.get("target")
    if type(sources) is not list or len(sources) != m or type(target) is not list or not target:
        raise SystemExit(f"system {index}: invalid source/target shape")
    for column in sources + [target]:
        if type(column) is not list or len(column) != len(target):
            raise SystemExit(f"system {index}: unequal or missing rows")
        if any(type(value) is not int or not 0 <= value <= 0xFFFF_FFFF for value in column):
            raise SystemExit(f"system {index}: expected u32 category labels")
    entries = case.get("n")
    if type(entries) is not list or len(entries) != {2: 4, 3: 18, 4: 166}[m]:
        raise SystemExit(f"system {index}: unexpected antichain count")
    atoms = {}
    for entry in entries:
        if type(entry) is not dict:
            raise SystemExit(f"system {index}: expected an atom object")
        masks, value = entry.get("antichain"), entry.get("net")
        if type(masks) is not list or not masks:
            raise SystemExit(f"system {index}: empty or malformed antichain")
        if any(type(mask) is not int or not 0 < mask < (1 << m) for mask in masks):
            raise SystemExit(f"system {index}: invalid source mask")
        if len(set(masks)) != len(masks) or any(
            a & b in (a, b) for a, b in itertools.combinations(masks, 2)
        ):
            raise SystemExit(f"system {index}: comparable or repeated source collections")
        key = antichain_of(masks)
        if key in atoms:
            raise SystemExit(f"system {index}: duplicate antichain")
        try:
            finite = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise SystemExit(f"system {index}: expected a finite numeric atom")
        atoms[key] = value
    # Every key is valid and distinct; the complete carrier has 4, 18 or 166 nodes.
    return m, list(zip(*sources, target)), atoms


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_threshold_down_sets.py <categorical-dump.json>")
    with open(sys.argv[1], encoding="utf-8") as handle:
        cases = json.load(handle, object_pairs_hook=reject_duplicate_keys, parse_constant=reject_constant)
    if not isinstance(cases, list) or len(cases) != 60:
        raise SystemExit("expected exactly 60 systems")
    worst = {}
    arities = Counter()
    for index, case in enumerate(cases):
        m, rows, atoms = validated_case(case, index)
        arities[m] += 1
        for f in range(m):
            alpha_f = frozenset(frozenset(c) for c in itertools.combinations(range(m), m - f))
            down_set_sum = sum(v for beta, v in atoms.items() if leq(beta, alpha_f))
            direct = hamming_gain(rows, m, f)
            key = f"m={m}, f={f}"
            if not math.isfinite(down_set_sum) or not math.isfinite(direct):
                raise SystemExit(f"system {index}, {key}: nonfinite result")
            residual = abs(down_set_sum - direct)
            if not math.isfinite(residual):
                raise SystemExit(f"system {index}, {key}: nonfinite residual")
            worst[key] = max(worst.get(key, 0.0), residual)
    if arities != Counter({2: 20, 3: 20, 4: 20}):
        raise SystemExit("expected 20 systems for each source count")
    for key in sorted(worst):
        print(f"{key}: max |down-set sum of pid-rs atoms - Hamming log-score gain| = {worst[key]:.3e}")
    failed = [key for key, value in worst.items() if not value <= TOLERANCE]
    print(f"systems: {len(cases)}; tolerance {TOLERANCE:.0e} nats:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
