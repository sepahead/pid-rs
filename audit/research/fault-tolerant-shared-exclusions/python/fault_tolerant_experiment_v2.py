"""Fault-injection test of threshold shared-exclusion forecasts on the UCI office recordings.

Inputs: the three UCI Occupancy Detection files (training, test, test2), verified by SHA-256.
Every forecaster is fitted on the training recording only. Faults are injected only into the
evaluation recordings. Every random choice uses a fixed seed. Output: JSON on standard output.

Encoding: five sensors (temperature, humidity, light, CO2, humidity ratio), each mapped to four
equal-width bins between its training minimum and maximum; evaluation values outside that range
are clamped. The target is the binary occupancy label.

Forecasters for a reported source state r (all use add-one smoothing over the two labels):
  prior            training label frequencies, ignoring r;
  oblivious        training rows whose state equals r;
  consistency_f    training rows within Hamming distance f of r (the MGW event of the
                   threshold antichain of all (m-f)-subsets);
  subset_ensemble  average over all (m-f)-subsets a of the forecast from rows that equal r on a;
  single_average   average over sensors i of the forecast from rows that equal r on sensor i;
  oracle           Bayes posterior under the injected fault model, known only to this forecaster.

Fault kinds: none; random (f distinct sensors, each replaced by a different uniform bin);
stuck_max (f distinct sensors report the top bin); adversarial (for each row and forecaster, the
worst report among all reports that differ from the truth on at most f sensors).

Uncertainty: per-row losses are averaged over 20 injection seeds, then a circular moving-block
bootstrap over evaluation rows (block length 60 rows, about one hour; 2000 resamples; fixed seed)
gives 95% percentile intervals for mean losses and paired differences. The rows are a time
series, so the block bootstrap is a descriptive dependence-aware interval, not a calibrated
population statement. This is development evidence on previously examined recordings.
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
INJECTION_SEEDS = 20
BLOCK = 60
RESAMPLES = 2000
FORECASTERS = ["prior", "oblivious", "consistency", "subset_ensemble", "single_average", "oracle"]


def load(directory: Path, name: str, digest: str) -> list[dict[str, str]]:
    raw = (directory / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise SystemExit(f"{name}: SHA-256 mismatch")
    # The header names 7 fields; each data row has 8 because a quoted row number comes first.
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


def fit_edges(rows):
    return {s: (min(float(r[s]) for r in rows), max(float(r[s]) for r in rows)) for s in SENSORS}


def encode(rows, edges):
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


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


class Model:
    """Training counts restricted to the sensors `keep` (indices into SENSORS)."""

    def __init__(self, data, keep):
        self.keep = tuple(keep)
        self.m = len(self.keep)
        self.joint = Counter((tuple(s[i] for i in self.keep), t) for s, t in data)
        self.n_rows = len(data)
        self.target = Counter(t for _, t in data)
        self.labels = (0, 1)

    def restrict(self, s):
        return tuple(s[i] for i in self.keep)

    def _smoothed(self, predicate):
        num = {t: 1 for t in self.labels}
        for (s, t), c in self.joint.items():
            if predicate(s):
                num[t] += c
        total = sum(num.values())
        return {t: num[t] / total for t in self.labels}

    def prior(self, r, f, kind):
        total = self.n_rows + 2
        return {t: (self.target[t] + 1) / total for t in self.labels}

    def oblivious(self, r, f, kind):
        return self._smoothed(lambda s: s == r)

    def consistency(self, r, f, kind):
        return self._smoothed(lambda s: hamming(s, r) <= f)

    def subset_ensemble(self, r, f, kind):
        subsets = list(itertools.combinations(range(self.m), self.m - f))
        parts = [self._smoothed(lambda s, a=a: all(s[i] == r[i] for i in a)) for a in subsets]
        return {t: sum(p[t] for p in parts) / len(parts) for t in self.labels}

    def single_average(self, r, f, kind):
        parts = [self._smoothed(lambda s, i=i: s[i] == r[i]) for i in range(self.m)]
        return {t: sum(p[t] for p in parts) / len(parts) for t in self.labels}

    def oracle(self, r, f, kind):
        fault_sets = list(itertools.combinations(range(self.m), f)) if f else [()]

        def likelihood(s):
            total = 0.0
            for fs in fault_sets:
                weight = 1.0
                for i in range(self.m):
                    if i in fs:
                        if kind == "random":
                            weight *= (1.0 / (BINS - 1)) if r[i] != s[i] else 0.0
                        elif kind == "stuck_max":
                            weight *= 1.0 if r[i] == BINS - 1 else 0.0
                        else:
                            raise ValueError(kind)
                    elif r[i] != s[i]:
                        weight = 0.0
                        break
                total += weight / len(fault_sets)
            return total

        num = {t: 1.0 for t in self.labels}
        for (s, t), c in self.joint.items():
            num[t] += c * likelihood(s)
        total = sum(num.values())
        return {t: num[t] / total for t in self.labels}


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


def per_row_losses(model, data, budget, kind, seed):
    """Per-row log loss for each forecaster; random kinds are averaged over injection seeds."""
    names = [n for n in FORECASTERS if n != "oracle" or kind in ("random", "stuck_max")]
    cache = {}

    def forecast(name, r):
        key = (name, r)
        if key not in cache:
            cache[key] = getattr(model, name)(r, budget, kind)
        return cache[key]

    losses = {name: [0.0] * len(data) for name in names}
    if kind in ("random", "stuck_max"):
        for k in range(INJECTION_SEEDS):
            rng = random.Random(seed + 7919 * k)
            for row, (s_full, t) in enumerate(data):
                s = model.restrict(s_full)
                fault_set = tuple(sorted(rng.sample(range(model.m), budget)))
                r = corrupt(s, fault_set, kind, rng)
                for name in names:
                    losses[name][row] += -math.log(forecast(name, r)[t]) / INJECTION_SEEDS
        return losses
    for row, (s_full, t) in enumerate(data):
        s = model.restrict(s_full)
        if kind == "none":
            reports = [s]
        else:  # adversarial
            reports = []
            for fs in itertools.combinations(range(model.m), budget):
                for values in itertools.product(range(BINS), repeat=budget):
                    r = list(s)
                    for i, v in zip(fs, values):
                        r[i] = v
                    reports.append(tuple(r))
        for name in names:
            losses[name][row] = max(-math.log(forecast(name, r)[t]) for r in reports)
    return losses


def block_bootstrap(series_by_name, seed):
    """Circular moving-block bootstrap of the mean; returns 95% percentile intervals."""
    n = len(next(iter(series_by_name.values())))
    rng = random.Random(seed)
    blocks = math.ceil(n / BLOCK)
    means = {name: [] for name in series_by_name}
    for _ in range(RESAMPLES):
        starts = [rng.randrange(n) for _ in range(blocks)]
        index = [(start + j) % n for start in starts for j in range(BLOCK)][:n]
        for name, series in series_by_name.items():
            means[name].append(sum(series[i] for i in index) / n)
    out = {}
    for name, values in means.items():
        values.sort()
        out[name] = [values[int(0.025 * RESAMPLES)], values[int(0.975 * RESAMPLES) - 1]]
    return out


def summarize(losses, seed):
    names = list(losses)
    series = {name: losses[name] for name in names}
    for other in names:
        if other != "consistency":
            series[f"consistency-{other}"] = [a - b for a, b in zip(losses["consistency"], losses[other])]
    intervals = block_bootstrap(series, seed)
    n = len(losses[names[0]])
    return {key: {"mean": sum(values) / n, "ci95": intervals[key]} for key, values in series.items()}


def cumulative_hamming(data, keep, f):
    """Plug-in net cumulative of the (m-f)-of-m antichain: H(T) - E[-log q_f(T|S)], no smoothing."""
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
    ps, pt = Counter(), Counter()
    for (s, t), c in law.items():
        ps[s] += c
        pt[t] += c
    return sum(c / n * math.log(c * n / (ps[s] * pt[t])) for (s, t), c in law.items())


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return cov / (sx * sy)


def main(directory: str) -> None:
    d = Path(directory)
    raw = {k: load(d, name, digest) for k, (name, digest) in FILES.items()}
    edges = fit_edges(raw["training"])
    data = {k: encode(v, edges) for k, v in raw.items()}
    train = data["training"]
    everyone = tuple(range(len(SENSORS)))
    result = {
        "schema": "pid-rs.fault-tolerant-shared-exclusions-experiment.v2",
        "bins": BINS, "sensors": SENSORS, "seed": SEED, "injection_seeds": INJECTION_SEEDS,
        "block_length_rows": BLOCK, "bootstrap_resamples": RESAMPLES,
        "rows": {k: len(v) for k, v in data.items()},
        "occupied_rows": {k: sum(t for _, t in v) for k, v in data.items()},
        "training_profile_all_sensors": {
            str(f): cumulative_hamming(train, everyone, f) for f in range(len(SENSORS))},
        "training_mi_all_sensors": mutual_information(train, everyone),
    }
    model = Model(train, everyone)
    table = {}
    for split_index, split in enumerate(("test", "test2")):
        for budget in (1, 2):
            for kind in ("none", "random", "stuck_max", "adversarial"):
                seed = SEED + 1000 * split_index + 97 * budget + {"none": 0, "random": 1,
                                                                   "stuck_max": 2, "adversarial": 3}[kind]
                losses = per_row_losses(model, data[split], budget, kind, seed)
                table[f"{split}/f={budget}/{kind}"] = summarize(losses, seed + 5)
    result["fault_injection_all_sensors"] = table

    subsets = []
    for keep in itertools.combinations(everyone, 3):
        sub = Model(train, keep)
        row = {
            "sensors": [SENSORS[i] for i in keep],
            "training_mi": mutual_information(train, keep),
            "training_ft1": cumulative_hamming(train, keep, 1),
            "training_ft2": cumulative_hamming(train, keep, 2),
            "training_min_mi_after_one_erasure": min(
                mutual_information(train, tuple(j for j in keep if j != i)) for i in keep),
        }
        for split in ("test", "test2"):
            for kind in ("none", "random", "adversarial"):
                losses = per_row_losses(sub, data[split], 1, kind, SEED + 31)
                row[f"{split}/{kind}"] = {name: sum(v) / len(v) for name, v in losses.items()}
        subsets.append(row)
    result["three_sensor_subsets"] = subsets
    correlations = {}
    for split in ("test", "test2"):
        for criterion in ("training_mi", "training_ft1", "training_ft2",
                          "training_min_mi_after_one_erasure"):
            for kind, name in (("random", "consistency"), ("random", "oblivious"),
                               ("none", "oblivious"), ("adversarial", "consistency")):
                x = [r[criterion] for r in subsets]
                y = [-r[f"{split}/{kind}"][name] for r in subsets]
                correlations[f"{split}: {criterion} vs -{kind}/{name} loss"] = spearman(x, y)
    result["spearman_rank_correlations_over_10_subsets"] = correlations
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
