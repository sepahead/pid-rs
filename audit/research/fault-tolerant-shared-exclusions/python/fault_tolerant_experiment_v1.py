"""Fault-tolerant information on the UCI office recordings: definitions and fault-injection test.

Inputs: the three UCI Occupancy Detection files (training, test, test2), verified by SHA-256.
All forecasters are fitted on the training recording only. Faults are injected only into the
evaluation recordings. Every random choice uses a fixed seed. Output: JSON on standard output.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

SENSORS = ["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]
FILES = {
    "training": ("datatraining.txt", "b2c4d0ce2b9e4e453c476f7125ef31aeec2d1f5c7f5572d0e80de3df6521ab56"),
    "test": ("datatest.txt", "1b92c7c1b2838963464fa891a610cf3c5db4becb7189189b29b330107a584c7f"),
    "test2": ("datatest2.txt", "d026d1bd5aeccd4aff4f3b3710d48e40613bd5fc370db7e61bbdcaa50d985095"),
}
BINS = 4
SEED = 20260926


def load(directory: Path, name: str, digest: str) -> list[dict[str, str]]:
    raw = (directory / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise SystemExit(f"{name}: SHA-256 mismatch")
    # The UCI files have a header of 7 names but 8 fields per row: a quoted row number comes first.
    with (directory / name).open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = []
        for row in reader:
            if len(row) == len(header) + 1:
                row = row[1:]
            if len(row) != len(header):
                raise SystemExit(f"{name}: unexpected field count {len(row)}")
            rows.append(dict(zip(header, row)))
        return rows


def fit_edges(rows: list[dict[str, str]]) -> dict[str, tuple[float, float]]:
    edges = {}
    for sensor in SENSORS:
        values = [float(row[sensor]) for row in rows]
        edges[sensor] = (min(values), max(values))
    return edges


def encode(rows, edges) -> list[tuple[tuple[int, ...], int]]:
    """Equal-width training bins; evaluation values outside the training range are clamped."""
    out = []
    for row in rows:
        state = []
        for sensor in SENSORS:
            low, high = edges[sensor]
            x = min(max(float(row[sensor]), low), high)
            index = int((x - low) / (high - low) * BINS) if high > low else 0
            state.append(min(index, BINS - 1))
        out.append((tuple(state), int(row["Occupancy"])))
    return out


def hamming(a, b) -> int:
    return sum(x != y for x, y in zip(a, b))


class Model:
    """Training counts restricted to a sensor subset `keep` (indices into SENSORS)."""

    def __init__(self, data, keep):
        self.keep = tuple(keep)
        self.joint = Counter((tuple(s[i] for i in keep), t) for s, t in data)
        self.states = sorted({s for s, _ in self.joint})
        self.n_rows = len(data)
        self.target = Counter(t for _, t in data)
        self.targets = sorted(self.target)

    def restrict(self, s):
        return tuple(s[i] for i in self.keep)

    def prior(self, t):
        return (self.target[t] + 1) / (self.n_rows + len(self.targets))

    def _smoothed(self, predicate, t):
        # Add-one smoothing over the target alphabet for every event-conditioned forecast.
        num = sum(c for (s, tt), c in self.joint.items() if tt == t and predicate(s))
        den = sum(c for (s, tt), c in self.joint.items() if predicate(s))
        return (num + 1) / (den + len(self.targets))

    def oblivious(self, r, t):
        rr = self.restrict(r)
        return self._smoothed(lambda s: s == rr, t)

    def consistency(self, r, t, f):
        rr = self.restrict(r)
        return self._smoothed(lambda s: hamming(s, rr) <= f, t)

    def subset_ensemble(self, r, t, f):
        rr = self.restrict(r)
        m = len(rr)
        subsets = list(itertools.combinations(range(m), m - f))
        return sum(self._smoothed(lambda s, a=a: all(s[i] == rr[i] for i in a), t)
                   for a in subsets) / len(subsets)

    def oracle(self, r, t, f, kind):
        """Bayes posterior under the injected fault model (known to the oracle only)."""
        rr = self.restrict(r)
        m = len(rr)
        fault_sets = list(itertools.combinations(range(m), f)) if f else [()]

        def likelihood(s):
            total = 0.0
            for fs in fault_sets:
                w = 1.0
                for i in range(m):
                    if i in fs:
                        if kind == "random":
                            w *= (1.0 / (BINS - 1)) if rr[i] != s[i] else 0.0
                        elif kind == "stuck_max":
                            w *= 1.0 if rr[i] == BINS - 1 else 0.0
                        else:
                            raise ValueError(kind)
                    elif rr[i] != s[i]:
                        w = 0.0
                        break
                total += w / len(fault_sets)
            return total

        num = sum(c * likelihood(s) for (s, tt), c in self.joint.items() if tt == t)
        den = sum(c * likelihood(s) for (s, tt), c in self.joint.items())
        return (num + 1) / (den + len(self.targets))

    def single_average(self, r, t):
        rr = self.restrict(r)
        return sum(self._smoothed(lambda s, i=i: s[i] == rr[i], t)
                   for i in range(len(rr))) / len(rr)


def fault_tolerant_information(data, keep, f):
    """Plug-in SxPID cumulative of the (m-f)-of-m antichain via Hamming balls (no smoothing)."""
    law = Counter((tuple(s[i] for i in keep), t) for s, t in data)
    n = len(data)
    target = Counter(t for _, t in data)
    h_t = -sum(c / n * math.log(c / n) for c in target.values())
    loss = 0.0
    for (s, t), c in law.items():
        ball = [(d, tt, cc) for (d, tt), cc in law.items() if hamming(d, s) <= f]
        pb = sum(cc for _, _, cc in ball)
        pbt = sum(cc for _, tt, cc in ball if tt == t)
        loss += c / n * -math.log(pbt / pb)
    return h_t - loss


def mutual_information(data, keep):
    law = Counter((tuple(s[i] for i in keep), t) for s, t in data)
    n = len(data)
    ps = Counter()
    pt = Counter()
    for (s, t), c in law.items():
        ps[s] += c
        pt[t] += c
    return sum(c / n * math.log(c * n / (ps[s] * pt[t])) for (s, t), c in law.items())


FORECASTERS = ["prior", "oblivious", "consistency", "subset_ensemble", "single_average", "oracle"]


def forecast(model, name, r, t, f, kind):
    if name == "oracle":
        return model.oracle(r, t, f, kind)
    if name == "prior":
        return model.prior(t)
    if name == "oblivious":
        return model.oblivious(r, t)
    if name == "consistency":
        return model.consistency(r, t, f)
    if name == "subset_ensemble":
        return model.subset_ensemble(r, t, f)
    if name == "single_average":
        return model.single_average(r, t)
    raise ValueError(name)


def corrupt(s, fault_set, kind, rng):
    r = list(s)
    for i in fault_set:
        if kind == "random":
            r[i] = rng.choice([b for b in range(BINS) if b != s[i]])
        elif kind == "stuck_max":
            r[i] = BINS - 1
        else:
            raise ValueError(kind)
    return tuple(r)


def evaluate(model, data, budget, injected, kind, seed):
    """Mean log loss and Brier score per forecaster.

    `budget` is the fault budget the forecasters assume; `injected` faults of type `kind` are
    applied to every evaluation row. The oracle knows the injected fault model; for clean rows
    and adversarial faults it is omitted because no single fault model describes them.
    """
    rng = random.Random(seed)
    m = len(model.keep)
    cache = {}
    names = [n for n in FORECASTERS
             if n != "oracle" or (injected > 0 and kind in ("random", "stuck_max"))]
    totals = {name: [0.0, 0.0] for name in names}
    for s_full, t in data:
        s = model.restrict(s_full)
        if kind == "adversarial":
            reports = []
            for fs in itertools.combinations(range(m), injected):
                for values in itertools.product(range(BINS), repeat=len(fs)):
                    r = list(s)
                    for i, v in zip(fs, values):
                        r[i] = v
                    reports.append(tuple(r))
        elif injected == 0:
            reports = [s]
        else:
            fault_set = tuple(sorted(rng.sample(range(m), injected)))
            reports = [corrupt(s, fault_set, kind, rng)]
        for name in names:
            worst = None
            for r in reports:
                key = (name, r)
                if key not in cache:
                    cache[key] = {tt: forecast(model, name, _lift(model, r), tt,
                                               injected if name == "oracle" else budget, kind)
                                  for tt in model.targets}
                q = cache[key]
                loss = -math.log(q[t])
                brier = sum((q[tt] - (1.0 if tt == t else 0.0)) ** 2 for tt in model.targets)
                if worst is None or loss > worst[0]:
                    worst = (loss, brier)
            totals[name][0] += worst[0]
            totals[name][1] += worst[1]
    n = len(data)
    return {name: {"log_loss": v[0] / n, "brier": v[1] / n} for name, v in totals.items()}


def _lift(model, r_restricted):
    # Forecast methods restrict their input; supply a full-length vector with the kept coordinates.
    full = [0] * len(SENSORS)
    for position, index in enumerate(model.keep):
        full[index] = r_restricted[position]
    return tuple(full)


def main(directory: str) -> None:
    d = Path(directory)
    raw = {k: load(d, name, digest) for k, (name, digest) in FILES.items()}
    edges = fit_edges(raw["training"])
    data = {k: encode(v, edges) for k, v in raw.items()}
    train = data["training"]
    everyone = tuple(range(len(SENSORS)))
    result = {
        "schema": "pid-rs.fault-tolerant-information-experiment.v1",
        "bins": BINS,
        "sensors": SENSORS,
        "seed": SEED,
        "profile_training_all_sensors": {
            str(f): fault_tolerant_information(train, everyone, f) for f in range(len(SENSORS))
        },
        "mi_training_all_sensors": mutual_information(train, everyone),
    }
    # 1. Fault injection with all five sensors.
    model = Model(train, everyone)
    table = {}
    for split_index, split in enumerate(("test", "test2")):
        for budget in (1, 2):
            for kind in ("none", "random", "stuck_max", "adversarial"):
                injected = 0 if kind == "none" else budget
                seed = SEED + 1000 * split_index + 97 * budget
                table[f"{split}/budget={budget}/{kind}"] = evaluate(
                    model, data[split], budget, injected, kind, seed)
    result["fault_injection_all_sensors"] = table
    # 2. Three-sensor subsets: design criteria versus clean and adversarial performance.
    subsets = []
    for keep in itertools.combinations(everyone, 3):
        sub = Model(train, keep)
        row = {
            "sensors": [SENSORS[i] for i in keep],
            "mi_training": mutual_information(train, keep),
            "ft1_training": fault_tolerant_information(train, keep, 1),
            "ft2_training": fault_tolerant_information(train, keep, 2),
        }
        for split in ("test", "test2"):
            row[f"{split}_clean_budget1"] = evaluate(sub, data[split], 1, 0, "none", SEED)
            row[f"{split}_adversarial_budget1"] = evaluate(sub, data[split], 1, 1, "adversarial", SEED)
        subsets.append(row)
    result["three_sensor_subsets"] = subsets
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
