"""Exact diagnosis of the small-delta trials of the retired binary64 one-Lambda test.

It replays archive/check_one_lambda_binary64_v1.py with the same seed and the same sequence of
random draws. For every trial whose binary64 delta lies in (0, 1e-7), it converts the binary64
arrays p and q to exact rationals and reports:

* sum(q) - sum(p), which must be zero if q is a probability law;
* the exact delta = ||q - p||_1 and the exact Lambda = log(p_min / (p_min - delta/2));
* the largest exact |c^u(z;q) - c^u(z;p)| over supported z, antichains and u, and its ratio to
  the exact Lambda; and
* the binary64 ratio that the retired test recorded.

Logarithms of exact rational ratios use 60 significant decimal digits.
"""
import decimal
import itertools
import math
import random
from fractions import Fraction

decimal.getcontext().prec = 60
random.seed(1)


def antichains(n):
    subs = [frozenset(c) for r in range(1, n + 1) for c in itertools.combinations(range(n), r)]
    out = []
    for r in range(1, len(subs) + 1):
        for combo in itertools.combinations(subs, r):
            if all(not (a < b or b < a) for a, b in itertools.combinations(combo, 2)):
                out.append(combo)
    return out


def masses(p, cells, ns, z, ac):
    s, t = z[:ns], z[ns]
    pa = sum((p[c] for c in cells if any(all(c[i] == s[i] for i in A) for A in ac)), Fraction(0))
    pc = sum((p[c] for c in cells if c[ns] == t), Fraction(0))
    pb = sum((p[c] for c in cells
              if c[ns] == t and any(all(c[i] == s[i] for i in A) for A in ac)), Fraction(0))
    return pa, pc, pb


def dln(x):
    x = Fraction(x)
    return (decimal.Decimal(x.numerator) / decimal.Decimal(x.denominator)).ln()


def float_cums(p, cells, ns, z, ac):
    s, t = z[:ns], z[ns]
    pa = sum(p[c] for c in cells if any(all(c[i] == s[i] for i in A) for A in ac))
    pc = sum(p[c] for c in cells if c[ns] == t)
    pb = sum(p[c] for c in cells if c[ns] == t and any(all(c[i] == s[i] for i in A) for A in ac))
    plus = -math.log(pa)
    minus = math.log(pc / pb)
    return plus, minus, plus - minus


rows = []
large = (0.0,)
for trial in range(4000):
    ns = random.choice([2, 2, 3])
    alph = [random.choice([2, 2, 3]) for _ in range(ns)] + [random.choice([2, 3])]
    cells = list(itertools.product(*[range(a) for a in alph]))
    supp = [c for c in cells if random.random() < 0.7] or [cells[0]]
    w = [random.random() ** random.choice([1, 3, 6]) + 1e-3 for _ in supp]
    tot = sum(w)
    p = {c: 0.0 for c in cells}
    for c, x in zip(supp, w):
        p[c] = x / tot
    pmin = min(p[c] for c in supp)
    delta = random.uniform(0.05, 0.999) * 2 * pmin
    q = dict(p)
    k_d = random.randint(1, min(3, len(supp)))
    donors = random.sample(supp, k_d)
    receivers = random.sample(supp, random.randint(1, min(3, len(supp))))
    move = delta / 2
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
    if not d_actual < 1e-7:
        lam = math.log(pmin / (pmin - d_actual / 2))
        for ac in antichains(ns):
            for z in supp:
                if q[z] <= 0:
                    continue
                a = float_cums(p, cells, ns, z, ac)
                b = float_cums(q, cells, ns, z, ac)
                for u in range(3):
                    r = abs(a[u] - b[u]) / lam
                    if r > large[0]:
                        large = (r, trial, dict(p), dict(q), cells, ns, supp, ac, z, u)
        continue
    # Exact analysis of the binary64 arrays actually tested.
    pe = {c: Fraction(p[c]) for c in cells}
    qe = {c: Fraction(q[c]) for c in cells}
    mass_gap = sum(qe.values()) - sum(pe.values())
    delta_exact = sum(abs(qe[c] - pe[c]) for c in cells)
    pmin_exact = min(pe[c] for c in supp)
    lam_exact = dln(pmin_exact / (pmin_exact - delta_exact / 2))
    lam_float = math.log(pmin / (pmin - d_actual / 2))
    worst_exact = decimal.Decimal(0)
    worst_float = 0.0
    for ac in antichains(ns):
        for z in supp:
            if q[z] <= 0:
                continue
            pa, pc, pb = masses(pe, cells, ns, z, ac)
            qa, qc, qb = masses(qe, cells, ns, z, ac)
            e_plus = dln(pa / qa)
            e_minus = dln((qc * pb) / (qb * pc))
            worst_exact = max(worst_exact, abs(e_plus), abs(e_minus), abs(e_plus - e_minus))
            a = float_cums(p, cells, ns, z, ac)
            b = float_cums(q, cells, ns, z, ac)
            worst_float = max(worst_float, *(abs(a[u] - b[u]) for u in range(3)))
    if sorted(donors) == sorted(receivers):
        overlap = f"same {len(donors)} cell" + ("s" if len(donors) > 1 else "")
    elif set(donors) & set(receivers):
        overlap = "partly shared"
    else:
        overlap = "disjoint"
    changed = [c for c in cells if qe[c] != pe[c]]
    changed_masses = "/".join(f"{float(pe[c] / pmin_exact):.2f}" for c in changed)
    rows.append((trial, overlap, changed_masses, float(mass_gap), float(delta_exact),
                 float(mass_gap) / float(delta_exact),
                 f"{lam_float:.3e}", f"{float(lam_exact):.3e}", f"{float(worst_exact):.3e}",
                 f"{float(worst_exact / lam_exact) if lam_exact else float('nan'):.4f}",
                 f"{worst_float / lam_float:.4f}"))

print("trial | donor and receiver sets | changed-cell masses / p_min | sum(q)-sum(p) exact | "
      "delta exact | gap/delta | Lambda binary64 | Lambda exact | max |dc| exact | exact ratio | "
      "binary64 ratio")
for row in rows:
    print(" | ".join(str(x) if not isinstance(x, float) else f"{x:.3e}" for x in row))
print(f"{len(rows)} trials with 0 < binary64 delta < 1e-7")

# Exact analysis of the largest binary64 ratio among trials with delta >= 1e-7.
r, trial, p, q, cells, ns, supp, ac, z, u = large
pe = {c: Fraction(p[c]) for c in cells}
qe = {c: Fraction(q[c]) for c in cells}
removed = sum(max(pe[c] - qe[c], Fraction(0)) for c in cells)
added = sum(max(qe[c] - pe[c], Fraction(0)) for c in cells)
pmin_exact = min(pe[c] for c in supp)
delta_exact = removed + added
pa, pc, pb = masses(pe, cells, ns, z, ac)
qa, qc, qb = masses(qe, cells, ns, z, ac)
changes = (abs(dln(pa / qa)), abs(dln((qc * pb) / (qb * pc))),
           abs(dln(pa / qa) - dln((qc * pb) / (qb * pc))))
lam_delta = dln(pmin_exact / (pmin_exact - delta_exact / 2))
lam_removed = dln(pmin_exact / (pmin_exact - removed))
print()
print(f"largest binary64 ratio with delta >= 1e-7: {r!r} (trial {trial}, component {u})")
print(f"  exact mass removed minus mass added: {float(removed - added):.3e}")
print(f"  exact ratio to Lambda(delta = ||q - p||_1): {changes[u] / lam_delta:.30f}")
print(f"  exact ratio to log(p_min/(p_min - removed mass)): {changes[u] / lam_removed:.30f}")
