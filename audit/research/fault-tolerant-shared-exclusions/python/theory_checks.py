"""Numerical checks of the fault-tolerance reading of MGW shared exclusions.

Every probability is an exact rational. Logarithms are binary64 and used only for the
information values; the validity bound is checked in exact rational arithmetic. Fixed seed.

Checks:
  C1  For random laws with 2-4 sources, the averaged net cumulative of the threshold antichain
      alpha_f equals H(T) - E[-log q_f(T|S)], computed from the Hamming ball, and equals the sum
      of the atoms in the down-set of alpha_f (dense zeta solve).
  C2  I(S;T), computed directly as sum p log p(s,t)/(p(s)p(t)), equals the top-node cumulative;
      and I(S;T) minus the alpha_f cumulative equals the sum of the atoms not below alpha_f.
      The atoms come from the zeta solve, so the second part also checks the solve.
  C3  Validity: for every supported (s', t) and every report r within Hamming distance f of s',
      q_f(t | r) >= p(s', t), exactly.
  C4  The informative component E[-log p(ball_f(S))] never increases with f.
  C5  Exact profiles of two small examples (three-bit parity; a copied target with a duplicated
      noise pair), printed as rational ratios.
The script exits with status 1 if C1-C4 find a violation (tolerance 1e-12 nats for C1-C2).
"""
import itertools
import math
import random
import sys
from fractions import Fraction

import numpy as np

random.seed(7)
TOLERANCE = 1e-12


def antichains(n):
    subs = [frozenset(c) for r in range(1, n + 1) for c in itertools.combinations(range(n), r)]
    out = []
    for r in range(1, len(subs) + 1):
        for combo in itertools.combinations(subs, r):
            if all(not (a < b or b < a) for a, b in itertools.combinations(combo, 2)):
                out.append(frozenset(combo))
    return out


def leq(a, b):
    return all(any(x <= y for x in a) for y in b)


def random_law(alphabet, support_probability):
    cells = list(itertools.product(*[range(k) for k in alphabet]))
    weights = {c: random.randint(1, 1000) ** random.choice([1, 2, 3])
               for c in cells if random.random() < support_probability}
    if not weights:
        weights[cells[0]] = 1
    total = sum(weights.values())
    return {c: Fraction(w, total) for c, w in weights.items()}


def net_cumulative(law, n, alpha):
    pt = {}
    for z, q in law.items():
        pt[z[n]] = pt.get(z[n], 0) + q
    total = 0.0
    for z, q in law.items():
        s, t = z[:n], z[n]
        pa = sum(w for y, w in law.items() if any(all(y[i] == s[i] for i in a) for a in alpha))
        pta = sum(w for y, w in law.items()
                  if y[n] == t and any(all(y[i] == s[i] for i in a) for a in alpha))
        total += float(q) * math.log(pta / (pt[t] * pa))
    return total


def ball(law, n, s, f):
    return [y for y in law if sum(y[i] != s[i] for i in range(n)) <= f]


def hamming_gain(law, n, f):
    pt = {}
    for z, q in law.items():
        pt[z[n]] = pt.get(z[n], 0) + q
    h_t = -sum(float(q) * math.log(q) for q in pt.values())
    loss = 0.0
    for z, q in law.items():
        members = ball(law, n, z[:n], f)
        pb = sum(law[y] for y in members)
        pbt = sum(law[y] for y in members if y[n] == z[n])
        loss += float(q) * -math.log(pbt / pb)
    return h_t - loss


def informative(law, n, f):
    return sum(float(q) * -math.log(sum(law[y] for y in ball(law, n, z[:n], f)))
               for z, q in law.items())


def main():
    worst_identity = 0.0
    worst_cost = 0.0
    worst_top = 0.0
    validity_checks = 0
    violations = []
    for _ in range(300):
        n = random.choice([2, 3, 4])
        alphabet = [random.choice([2, 3]) for _ in range(n)] + [random.choice([2, 3])]
        law = random_law(alphabet, 0.75)
        acs = antichains(n)
        zeta = np.array([[1.0 if leq(b, a) else 0.0 for b in acs] for a in acs])
        cumulative = np.array([net_cumulative(law, n, a) for a in acs])
        atoms = np.linalg.solve(zeta, cumulative)
        top = acs.index(frozenset([frozenset(range(n))]))
        ps, pt = {}, {}
        for z, q in law.items():
            ps[z[:n]] = ps.get(z[:n], 0) + q
            pt[z[n]] = pt.get(z[n], 0) + q
        mi = sum(float(q) * math.log(q / (ps[z[:n]] * pt[z[n]])) for z, q in law.items())
        worst_top = max(worst_top, abs(mi - cumulative[top]))
        informative_profile = []
        for f in range(n):
            alpha_f = frozenset(frozenset(c) for c in itertools.combinations(range(n), n - f))
            index = acs.index(alpha_f)
            down = sum(atoms[j] for j, b in enumerate(acs) if leq(b, alpha_f))
            not_below = sum(atoms[j] for j, b in enumerate(acs) if not leq(b, alpha_f))
            direct = hamming_gain(law, n, f)
            worst_identity = max(worst_identity, abs(direct - cumulative[index]),
                                 abs(direct - down))
            worst_cost = max(worst_cost, abs((mi - cumulative[index]) - not_below))
            informative_profile.append(informative(law, n, f))
            # C3: exact validity for every supported truth and every report within distance f.
            for z, q in law.items():
                s, t = z[:n], z[n]
                for r in itertools.product(*[range(k) for k in alphabet[:n]]):
                    if sum(r[i] != s[i] for i in range(n)) > f:
                        continue
                    members = ball(law, n, r, f)
                    pb = sum(law[y] for y in members)
                    pbt = sum(law[y] for y in members if y[n] == t)
                    validity_checks += 1
                    if not (pb > 0 and pbt / pb >= q):
                        violations.append(("validity", alphabet, z, r, f))
        if any(informative_profile[f + 1] > informative_profile[f] + 1e-12 for f in range(n - 1)):
            violations.append(("informative monotonicity", alphabet, informative_profile))
    print(f"C1 max |Hamming gain - cumulative|, |Hamming gain - down-set atom sum| = {worst_identity:.3e}")
    print(f"C2 max |I(S;T) direct - top-node cumulative| = {worst_top:.3e}; "
          f"max |(I(S;T) - cumulative) - sum of atoms not below alpha_f| = {worst_cost:.3e}")
    print(f"C3 exact validity checks: {validity_checks}; violations: "
          f"{sum(1 for v in violations if v[0] == 'validity')}")
    print(f"C4 informative-component increases with f: "
          f"{sum(1 for v in violations if v[0] == 'informative monotonicity')}")

    # C5: exact example profiles.
    bits = (0, 1)

    def uniform(rows):
        rows = list(rows)
        law = {}
        for row in rows:
            law[row] = law.get(row, 0) + Fraction(1, len(rows))
        return law

    examples = {
        "three-bit parity T = S1 xor S2 xor S3":
            uniform((a, b, c, a ^ b ^ c) for a in bits for b in bits for c in bits),
        "copy T = S1 with duplicated noise S2 = S3":
            uniform((a, b, b, a) for a in bits for b in bits),
    }
    for name, law in examples.items():
        pieces = []
        for f in range(3):
            pt = {}
            for z, q in law.items():
                pt[z[3]] = pt.get(z[3], 0) + q
            ratios = {}
            for z, q in law.items():
                members = ball(law, 3, z[:3], f)
                pb = sum(law[y] for y in members)
                pbt = sum(law[y] for y in members if y[3] == z[3])
                ratio = pbt / (pb * pt[z[3]])
                ratios[ratio] = ratios.get(ratio, 0) + q
            value = sum(float(m) * math.log(r) for r, m in ratios.items())
            pieces.append(f"f={f}: sum of mass x log({', '.join(f'{r}' for r in ratios)}) = {value:+.6f}")
        print(f"C5 {name}: " + "; ".join(pieces))
    failed = (worst_identity > TOLERANCE or worst_cost > TOLERANCE or worst_top > TOLERANCE
              or violations)
    print("result:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
