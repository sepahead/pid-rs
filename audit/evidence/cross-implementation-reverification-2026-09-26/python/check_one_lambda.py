"""Exact-rational stress test of the one-Lambda local cumulative bound.

Source: DEPENDENCY_COLORED_SXPID_CONCENTRATION.md, Sections 5.1-5.3, Equations (9)-(11).

Premises: p and q are probability laws on one finite source-target alphabet, supp(q) is a subset
of supp(p), and delta = ||q - p||_1 < 2 p_min. Claim: for every supported realization z and every
nonempty antichain alpha, |c^u(z;q) - c^u(z;p)| <= Lambda = log(p_min / (p_min - delta/2)) for
u in {+, -, sx}.

Construction. Every law is a vector of integers over one common denominator, so every event
probability is exact. Mass moves from donor cells to a disjoint set of receiver cells. Hence q is
again a probability law, its support equals supp(p), and delta is exactly twice the moved mass.
One quarter of the trials use a small delta (down to about 1e-12 p_min) to cover the regime in
which a binary64 construction loses the premises.

Evaluation. Every ratio |c^u(z;q) - c^u(z;p)| / Lambda is computed from the same integers with
80-digit decimal logarithms of exact rational quotients. For the smallest tested Lambda (about
1e-12), the rounding error of a computed ratio is below 1e-66. The script exits with status 1 if
any ratio exceeds 1 + 1e-60.
"""
import decimal
import itertools
import math
import random
import sys

TRIALS = 4000
SEED = 1
SCALE = 10**12  # integer resolution for the moved mass
TOLERANCE = decimal.Decimal("1e-60")
decimal.getcontext().prec = 80
random.seed(SEED)


def antichains(n):
    subsets = [frozenset(c) for r in range(1, n + 1) for c in itertools.combinations(range(n), r)]
    out = []
    for r in range(1, len(subsets) + 1):
        for combo in itertools.combinations(subsets, r):
            if all(not (a < b or b < a) for a, b in itertools.combinations(combo, 2)):
                out.append(tuple(sorted(tuple(sorted(a)) for a in combo)))
    return out


EVENT_CACHE = {}


def events(alphabet):
    """Index lists of A_alpha(s), C(t) and B_alpha(s,t) for every cell z and antichain alpha."""
    key = tuple(alphabet)
    if key not in EVENT_CACHE:
        ns = len(alphabet) - 1
        cells = list(itertools.product(*[range(a) for a in alphabet]))
        table = {}
        for zi, z in enumerate(cells):
            c_idx = [i for i, c in enumerate(cells) if c[ns] == z[ns]]
            for ac in antichains(ns):
                a_idx = [i for i, c in enumerate(cells)
                         if any(all(c[k] == z[k] for k in a) for a in ac)]
                b_idx = [i for i in a_idx if cells[i][ns] == z[ns]]
                table[(zi, ac)] = (a_idx, c_idx, b_idx)
        EVENT_CACHE[key] = (cells, table)
    return EVENT_CACHE[key]


def split(total, count):
    """Split a positive integer into `count` positive-or-zero integer parts with random shares."""
    shares = [random.random() + 1e-6 for _ in range(count)]
    s = sum(shares)
    parts = [int(total * x / s) for x in shares]
    parts[0] += total - sum(parts)
    return parts


LOG_CACHE = {}


def dlog_ratio(num, den):
    key = (num, den)
    if key not in LOG_CACHE:
        LOG_CACHE[key] = (decimal.Decimal(num) / decimal.Decimal(den)).ln()
    return LOG_CACHE[key]


exact_maxima = {0: decimal.Decimal(0), 1: decimal.Decimal(0), 2: decimal.Decimal(0)}
exact_argmax = {0: None, 1: None, 2: None}
attained = {0: 0, 1: 0, 2: 0}
evaluations = 0
small_trials = 0
smallest_ratio_delta = None
used = 0
for trial in range(TRIALS):
    ns = random.choice([2, 2, 3])
    alphabet = [random.choice([2, 2, 3]) for _ in range(ns)] + [random.choice([2, 3])]
    cells, table = events(alphabet)
    supp = [i for i in range(len(cells)) if random.random() < 0.7]
    if len(supp) < 2:
        continue
    weights = {i: 1 + int((random.random() ** random.choice([1, 3, 6])) * 10**6) for i in supp}
    w = [weights.get(i, 0) * SCALE for i in range(len(cells))]  # p = w / D, D = sum(w)
    w_min = min(w[i] for i in supp)
    if random.random() < 0.25:
        u = 10 ** random.uniform(-12, -1.3)
        small_trials += 1
    else:
        u = random.uniform(0.05, 0.999)
    move = int(u * w_min)  # delta/2 = move / D, strictly below p_min = w_min / D
    if move == 0:
        continue
    k_d = random.randint(1, min(3, len(supp) - 1))
    donors = random.sample(supp, k_d)
    rest = [i for i in supp if i not in donors]
    receivers = random.sample(rest, random.randint(1, min(3, len(rest))))
    v = list(w)
    for i, amount in zip(donors, split(move, len(donors))):
        v[i] -= amount
    for i, amount in zip(receivers, split(move, len(receivers))):
        v[i] += amount
    assert sum(v) == sum(w) and all(v[i] > 0 for i in supp)
    assert all(v[i] == 0 for i in range(len(cells)) if i not in supp)
    delta_twice_d = sum(abs(a - b) for a, b in zip(v, w))
    assert delta_twice_d == 2 * move and move < w_min
    used += 1
    lam_exact = dlog_ratio(w_min, w_min - move)
    if smallest_ratio_delta is None or move / w_min < smallest_ratio_delta:
        smallest_ratio_delta = move / w_min
    for zi in supp:
        for ac in antichains(ns):
            a_idx, c_idx, b_idx = table[(zi, ac)]
            pa, pc, pb = (sum(w[i] for i in idx) for idx in (a_idx, c_idx, b_idx))
            qa, qc, qb = (sum(v[i] for i in idx) for idx in (a_idx, c_idx, b_idx))
            # c+ difference: log(P(A)/Q(A)); c- difference: log(Q(C) P(B) / (Q(B) P(C))).
            e_plus = dlog_ratio(pa, qa)
            e_minus = dlog_ratio(qc * pb, qb * pc)
            evaluations += 1
            for u_index, change in enumerate((abs(e_plus), abs(e_minus), abs(e_plus - e_minus))):
                ratio = change / lam_exact
                if ratio >= 1 - TOLERANCE:
                    attained[u_index] += 1
                if ratio > exact_maxima[u_index]:
                    exact_maxima[u_index] = ratio
                    exact_argmax[u_index] = (trial, alphabet, [list(a) for a in ac], cells[zi],
                                             f"{move / w_min:.3e}")

names = ["informative c+", "misinformative c-", "net c_sx"]
print(f"trials used: {used} of {TRIALS} (seed {SEED}); small-delta trials drawn: {small_trials}")
print(f"(realization, antichain) evaluations: {evaluations}; every ratio computed with 80 digits")
print(f"smallest tested delta/(2 p_min): {smallest_ratio_delta:.3e}")
violation = False
for u_index, name in enumerate(names):
    print(f"{name}: max |dc|/Lambda = {exact_maxima[u_index]:.40f}")
    print(f"  evaluations with ratio equal to 1 within 1e-60: {attained[u_index]}")
    print(f"  argmax (trial, alphabet, antichain, realization, delta/(2 p_min)) = "
          f"{exact_argmax[u_index]}")
    if exact_maxima[u_index] > 1 + TOLERANCE:
        violation = True
print("violations of Equation (11):", "YES" if violation else "none")
sys.exit(1 if violation else 0)
