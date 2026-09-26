"""Separate brute-force check of KSG1 MI, Ehrlich source-disjunction redundancy, PID2 and PID3.

Input: the JSON file written by rust/audit_dump_continuous.rs. Method: dense Chebyshev distance
matrices, strict counts below the k-th joint radius, and digamma values at integers from the
harmonic identity psi(m) = H_(m-1) - gamma. H is summed with math.fsum over binary64 reciprocals
and gamma is its binary64 value, so these digamma values are accurate to rounding, not exact.
Local terms are compared for I(S1;T) only. Output: the largest absolute difference per quantity.
The script exits with status 1 if the input is malformed, if the research full PID3 lattice is
absent, or if any difference exceeds TOLERANCE (1e-12 nats; the observed maximum is about 9e-16).
"""
import itertools
import json
import math
import sys

import numpy as np

EULER = 0.5772156649015329
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


def psi_int(m):
    return math.fsum(1.0 / j for j in range(1, m)) - EULER


def cheb(a):
    # a: (n, d) -> (n, n) Chebyshev distance matrix
    return np.max(np.abs(a[:, None, :] - a[None, :, :]), axis=2)


def ksg1(dx, dy, k):
    n = dx.shape[0]
    terms = []
    for i in range(n):
        joint = np.maximum(dx[i], dy[i])
        joint = np.delete(joint, i)
        eps = np.sort(joint)[k - 1]
        ex = np.delete(dx[i], i)
        ey = np.delete(dy[i], i)
        nx = int(np.sum(ex < eps))
        ny = int(np.sum(ey < eps))
        terms.append(psi_int(k) + psi_int(n) - psi_int(nx + 1) - psi_int(ny + 1))
    return math.fsum(terms) / n, terms


def disj(ds_list, dt, k):
    n = dt.shape[0]
    ds = np.minimum.reduce(ds_list) if len(ds_list) > 1 else ds_list[0]
    terms = []
    for i in range(n):
        joint = np.delete(np.maximum(dt[i], ds[i]), i)
        eps = np.sort(joint)[k - 1]
        na = 1 + int(np.sum(np.delete(ds[i], i) < eps))
        nt = 1 + int(np.sum(np.delete(dt[i], i) < eps))
        terms.append(psi_int(k) + psi_int(n) - psi_int(na) - psi_int(nt))
    return math.fsum(terms) / n


def antichain_masks():
    masks = range(1, 8)
    out = set()
    for r in range(1, 8):
        for combo in itertools.combinations(masks, r):
            if all(a & b not in (a, b) for a, b in itertools.combinations(combo, 2)):
                out.add(frozenset(combo))
    return out


ANTICHAINS3 = antichain_masks()
assert len(ANTICHAINS3) == 18


def lattice_entries(entries, label, allow_abstention):
    if not isinstance(entries, list) or len(entries) != 18:
        raise SystemExit(f"{label}: expected 18 lattice entries")
    keys = [frozenset(r["sets"]) for r in entries]
    if len(set(keys)) != 18 or set(keys) != ANTICHAINS3:
        raise SystemExit(f"{label}: lattice entries are not the 18 distinct antichains")
    for r in entries:
        if r["value"] is None and not allow_abstention:
            raise SystemExit(f"{label}: unexpected abstention")
        if r["value"] is not None:
            number(r["value"], label)
    if all(r["value"] is None for r in entries):
        raise SystemExit(f"{label}: every entry abstained")


with open(sys.argv[1], encoding="utf-8") as handle:
    cases = json.load(handle, object_pairs_hook=reject_duplicate_keys)
if not isinstance(cases, list) or len(cases) != 6:
    raise SystemExit("expected exactly 6 cases")
worst_overall = 0.0
abstentions = 0
for c in cases:
    n, d, k = c["n"], c["d"], c["k"]
    S = [np.array(c[f"s{i}"]).reshape(n, d) for i in range(3)]
    T = np.array(c["t"]).reshape(n, d)
    D = [cheb(s) for s in S]
    DT = cheb(T)
    i0, loc = ksg1(D[0], DT, k)
    i1, _ = ksg1(D[1], DT, k)
    i01, _ = ksg1(np.maximum(D[0], D[1]), DT, k)
    red = disj([D[0], D[1]], DT, k)
    if len(c["ksg_local_s0_t"]) != n or len(c["pid2"]) != 4:
        raise SystemExit(f"case n={n}: wrong local-term or PID2 length")
    out = {
        "ksg_s0_t": number(c["ksg_s0_t"], "ksg_s0_t") - i0,
        "ksg_s1_t": number(c["ksg_s1_t"], "ksg_s1_t") - i1,
        "ksg_s0s1_t": number(c["ksg_s0s1_t"], "ksg_s0s1_t") - i01,
        "ksg_local": max(abs(number(a, "ksg_local") - b) for a, b in zip(c["ksg_local_s0_t"], loc)),
        "isx": number(c["isx_s0_s1_t"], "isx") - red,
    }
    pid2_ref = [red, i0 - red, i1 - red, i01 - i0 - i1 + red]
    out["pid2"] = max(abs(number(a, "pid2") - b) for a, b in zip(c["pid2"], pid2_ref))

    def ant_red(sets):
        ds_list = []
        for m in sets:
            members = [D[j] for j in range(3) if m >> j & 1]
            ds_list.append(np.maximum.reduce(members) if len(members) > 1 else members[0])
        return disj(ds_list, DT, k)

    lattice_entries(c["inc_pid3"], f"case n={n} incomplete PID3", allow_abstention=True)
    worst_inc = 0.0
    for r in c["inc_pid3"]:
        if r["value"] is None:
            abstentions += 1
        else:
            worst_inc = max(worst_inc, abs(number(r["value"], "inc_pid3") - ant_red(r["sets"])))
    out["inc_pid3"] = worst_inc
    if not isinstance(c["full_pid3"], list):
        raise SystemExit(f"case n={n}: the full PID3 lattice is absent: {c['full_pid3']!r}")
    lattice_entries(c["full_pid3"], f"case n={n} full PID3", allow_abstention=False)
    out["full_pid3"] = max(abs(number(r["value"], "full_pid3") - ant_red(r["sets"]))
                           for r in c["full_pid3"])
    worst_overall = max(worst_overall, *(abs(v) for v in out.values()))
    print(f"n={n:4d} d={d} k={k}  I0={i0:+.4f} red={red:+.4f}  ",
          "  ".join(f"{a}={b:.1e}" for a, b in out.items()))
print(f"cases: {len(cases)}; abstaining incomplete-PID3 entries: {abstentions}")
print(f"largest difference {worst_overall:.1e}; tolerance {TOLERANCE:.0e} nats:",
      "PASS" if worst_overall <= TOLERANCE else "FAIL")
sys.exit(0 if worst_overall <= TOLERANCE else 1)
