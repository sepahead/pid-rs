"""Separate categorical check of MGW SxPID (2-4 sources) and Williams-Beer I_min (2-3 sources).

Input: the JSON file written by rust/audit_dump_discrete.rs (rows plus pid-rs outputs).
Method: exact Fraction probabilities from the rows, binary64 logarithms, a separate antichain
enumeration, and Mobius inversion by solving the zeta system Z x = c with numpy. pid-rs instead
subtracts lower atoms in topological order. The informative and misinformative pointwise terms
are computed; the net term is their difference. Every subset mutual information and the
two-source MI terms are compared too. Output: the largest absolute difference per
quantity. The script exits with status 1 if the input is malformed or if any difference exceeds
TOLERANCE (1e-12 nats, far above the observed maximum of about 8e-16).
"""
import itertools
import json
import math
import sys
from collections import Counter
from fractions import Fraction

import numpy as np

TOLERANCE = 1e-12


def reject_duplicate_keys(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise SystemExit(f"duplicate JSON key in {keys!r}")
    return dict(pairs)


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SystemExit(f"{label}: expected a finite number, got {value!r}")
    return float(value)


def unique_index(entries, label):
    index = {to_key(x["antichain"]): x for x in entries}
    if len(index) != len(entries):
        raise SystemExit(f"{label}: duplicate antichain in the pid-rs output")
    return index


with open(sys.argv[1], encoding="utf-8") as handle:
    cases = json.load(handle, object_pairs_hook=reject_duplicate_keys)
if not isinstance(cases, list) or len(cases) != 60:
    raise SystemExit("expected exactly 60 cases")
if Counter(case.get("n_sources") for case in cases) != Counter({2: 20, 3: 20, 4: 20}):
    raise SystemExit("expected 20 cases each for 2, 3 and 4 sources")
EXPECTED_ANTICHAINS = {2: 4, 3: 18, 4: 166}


def numbers(values, length, label):
    if not isinstance(values, list) or len(values) != length:
        raise SystemExit(f"{label}: expected a list of {length} numbers")
    return [number(value, label) for value in values]


def subsets(n):
    out = []
    for r in range(1, n + 1):
        for c in itertools.combinations(range(n), r):
            out.append(frozenset(c))
    return out


def antichains(n):
    subs = subsets(n)
    res = []
    for r in range(1, len(subs) + 1):
        for combo in itertools.combinations(subs, r):
            ok = all(not (a < b or b < a) for a, b in itertools.combinations(combo, 2))
            if ok:
                res.append(frozenset(combo))
    return res


def leq(a, b):
    return all(any(A <= B for A in a) for B in b)


def to_key(mask_list):
    return frozenset(frozenset(i for i in range(8) if m >> i & 1) for m in mask_list)


def pmf_of(rows):
    c = Counter(rows)
    n = len(rows)
    return {k: Fraction(v, n) for k, v in c.items()}


def sxpid(sources, target):
    ns = len(sources)
    rows = list(zip(*sources, target))
    pmf = pmf_of(rows)
    acs = antichains(ns)
    m = len(acs)
    Z = np.array([[1.0 if leq(b, a) else 0.0 for b in acs] for a in acs])
    avg_plus = np.zeros(m)
    avg_minus = np.zeros(m)
    for rlz, p in pmf.items():
        s, t = rlz[:ns], rlz[ns]
        p_t = sum(q for r, q in pmf.items() if r[ns] == t)
        cp = np.zeros(m)
        cm = np.zeros(m)
        for idx, a in enumerate(acs):
            def ev(r):
                return any(all(r[i] == s[i] for i in A) for A in a)
            pa = sum(q for r, q in pmf.items() if ev(r))
            pta = sum(q for r, q in pmf.items() if ev(r) and r[ns] == t)
            cp[idx] = -math.log(pa)
            cm[idx] = math.log(p_t / pta)
        pip = np.linalg.solve(Z, cp)
        pim = np.linalg.solve(Z, cm)
        avg_plus += float(p) * pip
        avg_minus += float(p) * pim
    return acs, avg_plus, avg_minus


def mi(xrows, yrows):
    n = len(xrows)
    pxy = Counter(zip(xrows, yrows))
    px = Counter(xrows)
    py = Counter(yrows)
    return sum((c / n) * math.log(c * n / (px[x] * py[y])) for (x, y), c in pxy.items())


def ispec(srows, trows):
    n = len(srows)
    pst = Counter(zip(srows, trows))
    ps = Counter(srows)
    pt = Counter(trows)
    out = {}
    for t, ct in pt.items():
        out[t] = sum((c / ct) * math.log(c * n / (ps[s] * ct)) for (s, tt), c in pst.items() if tt == t)
    return out, pt, n


def imin_red(sources, target, ac):
    specs = []
    for A in ac:
        srows = list(zip(*[sources[i] for i in sorted(A)]))
        spec, pt, n = ispec(srows, target)
        specs.append(spec)
    return sum((ct / n) * min(sp[t] for sp in specs) for t, ct in pt.items())


worst = {}


def upd(name, diff):
    worst[name] = max(worst.get(name, 0.0), abs(number(diff, name)))


for ci, case in enumerate(cases):
    ns = case["n_sources"]
    sources = case["sources"]
    target = case["target"]
    acs, ap, am = sxpid(sources, target)
    ref = {frozenset(a): (p, q) for a, p, q in zip(acs, ap, am)}
    if len(case["n"]) != EXPECTED_ANTICHAINS[ns]:
        raise SystemExit(f"case {ci}: expected {EXPECTED_ANTICHAINS[ns]} antichains")
    got = unique_index(case["n"], f"case {ci} n-source output")
    if set(got) != set(ref):
        raise SystemExit(f"case {ci}: antichain sets differ ({len(got)} vs {len(ref)})")
    for k, (p, q) in ref.items():
        g = got[k]
        upd(f"n{ns}_plus", number(g["plus"], "plus") - p)
        upd(f"n{ns}_minus", number(g["minus"], "minus") - q)
        upd(f"n{ns}_net", number(g["net"], "net") - (p - q))
    # joint MI and reconstruction
    joint = mi(list(zip(*sources)), target)
    upd(f"n{ns}_jointmi", number(case["n_joint_mi"], "n_joint_mi") - joint)
    # Subset mutual information of the general path: entry i belongs to source bitmask i + 1.
    subset_mis = numbers(case["n_subset_mis"], 2**ns - 1, f"case {ci} n_subset_mis")
    for index, got_mi in enumerate(subset_mis):
        members = [j for j in range(ns) if (index + 1) >> j & 1]
        upd(f"n{ns}_subset_mi", got_mi - mi(list(zip(*[sources[j] for j in members])), target))
    upd(f"n{ns}_sum_atoms_vs_mi", sum(number(g["net"], "net") for g in case["n"]) - joint)
    if ns == 2:
        two = case["two"]
        names = {"red": [{0}, {1}], "unq1": [{0}], "unq2": [{1}], "syn": [{0, 1}]}
        if not isinstance(two, dict) or set(two) != set(names) | {"mi"}:
            raise SystemExit(f"case {ci}: two-source output must have exactly mi, red, syn, unq1, unq2")
        mi_terms = numbers(two["mi"], 3, f"case {ci} two-source mi")
        for got_mi, ref_mi in zip(mi_terms, [mi(sources[0], target), mi(sources[1], target),
                                             mi(list(zip(*sources)), target)]):
            upd("two_mi_terms", got_mi - ref_mi)
        for nm, sets in names.items():
            key = frozenset(frozenset(s) for s in sets)
            p, q = ref[key]
            plus, minus = numbers(two[nm], 2, f"case {ci} two-source {nm}")
            upd("two_plus", plus - p)
            upd("two_minus", minus - q)
        # I_min 2
        r = imin_red(sources, target, [{0}, {1}])
        i1 = mi(sources[0], target)
        i2 = mi(sources[1], target)
        i12 = mi(list(zip(*sources)), target)
        exp = [r, i1 - r, i2 - r, i12 - i1 - i2 + r, i1, i2, i12]
        for a, b in zip(numbers(case["imin2"], 7, f"case {ci} imin2"), exp):
            upd("imin2", a - b)
    if ns == 3:
        got3 = unique_index(case["three"], f"case {ci} three-source output")
        if set(got3) != set(ref):
            raise SystemExit(f"case {ci}: three-source antichain sets differ")
        for k, (p, q) in ref.items():
            upd("three_plus", number(got3[k]["plus"], "three plus") - p)
            upd("three_minus", number(got3[k]["minus"], "three minus") - q)
        # I_min 3 independent
        acs3 = antichains(3)
        reds = np.array([imin_red(sources, target, a) for a in acs3])
        Z = np.array([[1.0 if leq(b, a) else 0.0 for b in acs3] for a in acs3])
        atoms = np.linalg.solve(Z, reds)
        refi = {a: (atoms[i], reds[i]) for i, a in enumerate(acs3)}
        if set(unique_index(case["imin3"], f"case {ci} I_min output")) != set(refi):
            raise SystemExit(f"case {ci}: I_min antichain sets differ")
        for x in case["imin3"]:
            k = to_key(x["antichain"])
            upd("imin3_atom", number(x["atom"], "imin3 atom") - refi[k][0])
            upd("imin3_red", number(x["red"], "imin3 red") - refi[k][1])

for k, v in sorted(worst.items()):
    print(f"{k:24s} max|diff| = {v:.3e}")
print("cases:", len(cases))
failed = sorted(k for k, v in worst.items() if not v <= TOLERANCE)
print(f"tolerance {TOLERANCE:.0e} nats:", "FAIL " + ", ".join(failed) if failed else "PASS")
sys.exit(1 if failed else 0)
