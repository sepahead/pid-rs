"""Randomized stress test of the one-Lambda local cumulative bound.

Source: DEPENDENCY_COLORED_SXPID_CONCENTRATION.md, Section 5.3. Fixed seed 1, 4000 trials.

Claim: supp(q) subset supp(p), delta=||q-p||_1 < 2 pmin, then for every supported z and antichain
alpha, |c^u(z;q)-c^u(z;p)| <= Lambda = log(pmin/(pmin-delta/2)) for u in {+,-,sx}.
"""
import itertools
import math
import random

random.seed(1)


def antichains(n):
    subs = [frozenset(c) for r in range(1, n + 1) for c in itertools.combinations(range(n), r)]
    out = []
    for r in range(1, len(subs) + 1):
        for combo in itertools.combinations(subs, r):
            if all(not (a < b or b < a) for a, b in itertools.combinations(combo, 2)):
                out.append(combo)
    return out


def cums(p, cells, ns, z, ac):
    s, t = z[:ns], z[ns]
    pa = sum(p[c] for c in cells if any(all(c[i] == s[i] for i in A) for A in ac))
    pc = sum(p[c] for c in cells if c[ns] == t)
    pb = sum(p[c] for c in cells if c[ns] == t and any(all(c[i] == s[i] for i in A) for A in ac))
    plus = -math.log(pa)
    minus = math.log(pc / pb)
    return plus, minus, plus - minus


worst_ratio = 0.0
worst = None
worst_tiny = (0.0,)
for trial in range(4000):
    ns = random.choice([2, 2, 3])
    alph = [random.choice([2, 2, 3]) for _ in range(ns)] + [random.choice([2, 3])]
    cells = list(itertools.product(*[range(a) for a in alph]))
    # random support subset
    supp = [c for c in cells if random.random() < 0.7] or [cells[0]]
    w = [random.random() ** random.choice([1, 3, 6]) + 1e-3 for _ in supp]
    tot = sum(w)
    p = {c: 0.0 for c in cells}
    for c, x in zip(supp, w):
        p[c] = x / tot
    pmin = min(p[c] for c in supp)
    delta = random.uniform(0.05, 0.999) * 2 * pmin
    # adversarial-ish perturbation: move delta/2 mass from a few donors to a few receivers in supp
    q = dict(p)
    k_d = random.randint(1, min(3, len(supp)))
    donors = random.sample(supp, k_d)
    receivers = random.sample(supp, random.randint(1, min(3, len(supp))))
    move = delta / 2
    # take from donors proportionally but never below 0
    dw = [random.random() for _ in donors]
    ok = True
    for d, x in zip(donors, dw):
        amt = move * x / sum(dw)
        if amt > q[d]:
            ok = False
        q[d] -= amt
    if not ok:
        continue
    rw = [random.random() for _ in receivers]
    for r, x in zip(receivers, rw):
        q[r] += move * x / sum(rw)
    d_actual = sum(abs(q[c] - p[c]) for c in cells)
    if d_actual >= 2 * pmin or d_actual == 0:
        continue
    tiny = d_actual < 1e-7
    lam = math.log(pmin / (pmin - d_actual / 2))
    for ac in antichains(ns):
        for z in supp:
            if q[z] <= 0:
                continue
            a = cums(p, cells, ns, z, ac)
            b = cums(q, cells, ns, z, ac)
            for u in range(3):
                r = abs(a[u] - b[u]) / lam
                if tiny:
                    if r > worst_tiny[0]:
                        worst_tiny = (r, ns, alph, u, sorted(sorted(x) for x in ac), z, d_actual, lam)
                elif r > worst_ratio:
                    worst_ratio = r
                    worst = (ns, alph, u, sorted(sorted(x) for x in ac), z, d_actual, pmin, a[u], b[u], lam)
print("trials with delta >= 1e-7: max |dc|/Lambda =", repr(worst_ratio))
print("argmax:", worst)
print("trials with 0 < delta < 1e-7 (binary64 rounding regime): max |dc|/Lambda =", repr(worst_tiny[0]))
print("argmax:", worst_tiny[1:])
