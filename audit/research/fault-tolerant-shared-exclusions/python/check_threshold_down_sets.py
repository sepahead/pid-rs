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
the input is malformed or if any difference exceeds 1e-12 nats.
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


def main():
    with open(sys.argv[1], encoding="utf-8") as handle:
        cases = json.load(handle, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(cases, list) or len(cases) != 60:
        raise SystemExit("expected exactly 60 systems")
    worst = {}
    for index, case in enumerate(cases):
        m = case["n_sources"]
        rows = list(zip(*case["sources"], case["target"]))
        atoms = {antichain_of(a["antichain"]): a["net"] for a in case["n"]}
        if len(atoms) != len(case["n"]) or len(atoms) != {2: 4, 3: 18, 4: 166}[m]:
            raise SystemExit(f"system {index}: unexpected or duplicate antichains")
        for value in atoms.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SystemExit(f"system {index}: non-numeric atom")
        for f in range(m):
            alpha_f = frozenset(frozenset(c) for c in itertools.combinations(range(m), m - f))
            down_set_sum = sum(v for beta, v in atoms.items() if leq(beta, alpha_f))
            direct = hamming_gain(rows, m, f)
            key = f"m={m}, f={f}"
            worst[key] = max(worst.get(key, 0.0), abs(down_set_sum - direct))
    for key in sorted(worst):
        print(f"{key}: max |down-set sum of pid-rs atoms - Hamming log-score gain| = {worst[key]:.3e}")
    failed = [key for key, value in worst.items() if not value <= TOLERANCE]
    print(f"systems: {len(cases)}; tolerance {TOLERANCE:.0e} nats:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
