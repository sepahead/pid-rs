"""Fault-injection test of threshold shared-exclusion forecasts, version 3.

Inputs: the three UCI Occupancy Detection files (training, test, test2), verified by SHA-256.
Every forecaster is fitted on the training recording only. Faults are injected only into the
evaluation recordings. Every random choice uses a fixed seed. Output: JSON on standard output.

Changes from version 2 (retained as fault_tolerant_experiment_v2.py):
  * primary analysis on the four physical sensors (temperature, humidity, light, CO2); humidity
    ratio is derived by the provider from temperature and humidity, so the five-sensor analysis
    is kept as a secondary analysis with that caveat;
  * block-bootstrap sensitivity with blocks of 60, 360 and 720 rows;
  * mismatched budgets: assumed budget f in {1, 2} with injected fault count k in {0, 1, 2};
  * expected loss when only a fraction rho of rows is faulted, from the clean and faulted
    per-row losses;
  * an oblivious forecast that falls back to the prior for states unseen in training;
  * two oracle smoothings: one added count per label on likelihood-weighted counts, and a
    pseudo-count equal to the likelihood-weighted mass of one average training row;
  * diagnostics: unseen clean states, unseen state-label pairs (where Theorem 2 does not apply),
    clamped values and occupancy rates;
  * the three-sensor subset study with every Spearman correlation, including the negative ones.

Encoding: each sensor is cut into four equal-width levels between its training minimum and
maximum; evaluation values outside that range are clamped. The target is binary occupancy.
Forecasts use one added count per label after selecting their training rows, except where stated.
Random and stuck losses are averaged over 20 injection seeds. Intervals are 95% percentile
intervals of a circular moving-block bootstrap over rows (2000 resamples, fixed seed). The rows are
a time series; the intervals describe variation within these recordings, not population
uncertainty. This is development evidence on previously examined recordings.
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

import numpy as np

ALL_SENSORS = ["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]
PHYSICAL = (0, 1, 2, 3)
EVERY = (0, 1, 2, 3, 4)
FILES = {
    "training": ("datatraining.txt", "b2c4d0ce2b9e4e453c476f7125ef31aeec2d1f5c7f5572d0e80de3df6521ab56"),
    "test": ("datatest.txt", "1b92c7c1b2838963464fa891a610cf3c5db4becb7189189b29b330107a584c7f"),
    "test2": ("datatest2.txt", "d026d1bd5aeccd4aff4f3b3710d48e40613bd5fc370db7e61bbdcaa50d985095"),
}
BINS = 4
SEED = 20260926
INJECTION_SEEDS = 20
BLOCKS = (60, 360, 720)
RESAMPLES = 2000
RHOS = (0.05, 0.1, 0.25, 0.5, 1.0)
LABELS = (0, 1)


def load(directory, name, digest):
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
    return {s: (min(float(r[s]) for r in rows), max(float(r[s]) for r in rows)) for s in ALL_SENSORS}


def encode(rows, edges):
    out, clamped = [], Counter()
    for row in rows:
        state = []
        for sensor in ALL_SENSORS:
            low, high = edges[sensor]
            value = float(row[sensor])
            if value < low or value > high:
                clamped[sensor] += 1
            x = min(max(value, low), high)
            index = int((x - low) / (high - low) * BINS) if high > low else 0
            state.append(min(index, BINS - 1))
        out.append((tuple(state), int(row["Occupancy"])))
    return out, dict(clamped)


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


class Model:
    """Training counts restricted to the sensors `keep`."""

    def __init__(self, data, keep):
        self.keep = tuple(keep)
        self.m = len(self.keep)
        self.joint = Counter((tuple(s[i] for i in self.keep), t) for s, t in data)
        self.states = Counter()
        for (s, _), c in self.joint.items():
            self.states[s] += c
        self.n_rows = len(data)
        self.target = Counter(t for _, t in data)

    def restrict(self, s):
        return tuple(s[i] for i in self.keep)

    def _smoothed(self, predicate):
        num = {t: 1 for t in LABELS}
        for (s, t), c in self.joint.items():
            if predicate(s):
                num[t] += c
        total = sum(num.values())
        return {t: num[t] / total for t in LABELS}

    def prior(self, r, f, k, kind):
        total = self.n_rows + 2
        return {t: (self.target[t] + 1) / total for t in LABELS}

    def oblivious(self, r, f, k, kind):
        return self._smoothed(lambda s: s == r)

    def oblivious_backoff(self, r, f, k, kind):
        if self.states.get(r, 0) == 0:
            return self.prior(r, f, k, kind)
        return self._smoothed(lambda s: s == r)

    def consistency(self, r, f, k, kind):
        return self._smoothed(lambda s: hamming(s, r) <= f)

    def subset_ensemble(self, r, f, k, kind):
        subsets = list(itertools.combinations(range(self.m), self.m - f))
        parts = [self._smoothed(lambda s, a=a: all(s[i] == r[i] for i in a)) for a in subsets]
        return {t: sum(p[t] for p in parts) / len(parts) for t in LABELS}

    def single_average(self, r, f, k, kind):
        parts = [self._smoothed(lambda s, i=i: s[i] == r[i]) for i in range(self.m)]
        return {t: sum(p[t] for p in parts) / len(parts) for t in LABELS}

    def _likelihood(self, r, k, kind):
        fault_sets = list(itertools.combinations(range(self.m), k)) if k else [()]

        def likelihood(s):
            total = 0.0
            for fs in fault_sets:
                weight = 1.0
                for i in range(self.m):
                    if i in fs:
                        if kind == "random":
                            weight *= (1.0 / (BINS - 1)) if r[i] != s[i] else 0.0
                        elif kind == "stuck":
                            weight *= 1.0 if r[i] == BINS - 1 else 0.0
                        else:
                            raise ValueError(kind)
                    elif r[i] != s[i]:
                        weight = 0.0
                        break
                total += weight / len(fault_sets)
            return total
        return likelihood

    def oracle(self, r, f, k, kind):
        """Bayes forecast under the injected fault model; one added count per label."""
        likelihood = self._likelihood(r, k, kind)
        num = {t: 1.0 for t in LABELS}
        for (s, t), c in self.joint.items():
            num[t] += c * likelihood(s)
        total = sum(num.values())
        return {t: num[t] / total for t in LABELS}

    def oracle_row_unit(self, r, f, k, kind):
        """Same, with a pseudo-count equal to the weighted mass of one average training row."""
        likelihood = self._likelihood(r, k, kind)
        weighted = {t: 0.0 for t in LABELS}
        for (s, t), c in self.joint.items():
            weighted[t] += c * likelihood(s)
        pseudo = sum(weighted.values()) / self.n_rows
        if pseudo == 0.0:
            return self.prior(r, f, k, kind)
        num = {t: weighted[t] + pseudo for t in LABELS}
        total = sum(num.values())
        return {t: num[t] / total for t in LABELS}


FAULT_FREE = ["prior", "oblivious", "oblivious_backoff", "consistency", "subset_ensemble",
              "single_average"]
ORACLES = ["oracle", "oracle_row_unit"]


def corrupt(s, fault_set, kind, rng):
    r = list(s)
    for i in fault_set:
        if kind == "random":
            r[i] = rng.choice([b for b in range(BINS) if b != s[i]])
        elif kind == "stuck":
            r[i] = BINS - 1
        else:
            raise ValueError(kind)
    return tuple(r)


def per_row_losses(model, data, f, k, kind, seed):
    """Per-row log loss for each forecaster; random kinds are averaged over injection seeds."""
    names = FAULT_FREE + (ORACLES if kind in ("random", "stuck") and k > 0 else [])
    cache = {}

    def forecast(name, r):
        key = (name, r)
        if key not in cache:
            cache[key] = getattr(model, name)(r, f, k, kind)
        return cache[key]

    losses = {name: [0.0] * len(data) for name in names}
    if kind in ("random", "stuck") and k > 0:
        for j in range(INJECTION_SEEDS):
            rng = random.Random(seed + 7919 * j)
            for row, (s_full, t) in enumerate(data):
                s = model.restrict(s_full)
                fault_set = tuple(sorted(rng.sample(range(model.m), k)))
                r = corrupt(s, fault_set, kind, rng)
                for name in names:
                    losses[name][row] += -math.log(forecast(name, r)[t]) / INJECTION_SEEDS
        return losses
    for row, (s_full, t) in enumerate(data):
        s = model.restrict(s_full)
        if kind == "none":
            reports = [s]
        elif kind == "worst":
            reports = []
            for fs in itertools.combinations(range(model.m), k):
                for values in itertools.product(range(BINS), repeat=k):
                    r = list(s)
                    for i, v in zip(fs, values):
                        r[i] = v
                    reports.append(tuple(r))
        else:
            raise ValueError(kind)
        for name in names:
            losses[name][row] = max(-math.log(forecast(name, r)[t]) for r in reports)
    return losses


def block_bootstrap_intervals(series_list, block, seed):
    """95% percentile intervals of the circular moving-block bootstrap mean, for many series.

    Each resample concatenates ceil(n / block) circular blocks with uniform random starts and
    truncates to n rows. Block sums come from prefix sums of the doubled series, so every resample
    costs O(n / block) per series; the estimator is the same as explicit index resampling.
    """
    data = np.asarray(series_list, dtype=float)
    count, n = data.shape
    rng = np.random.default_rng(seed)
    blocks = math.ceil(n / block)
    last = n - (blocks - 1) * block
    prefix = np.concatenate(
        [np.zeros((count, 1)), np.cumsum(np.concatenate([data, data], axis=1), axis=1)], axis=1)
    starts = rng.integers(0, n, size=(RESAMPLES, blocks))
    full = prefix[:, starts[:, :-1] + block] - prefix[:, starts[:, :-1]]
    tail = prefix[:, starts[:, -1] + last] - prefix[:, starts[:, -1]]
    means = np.sort((full.sum(axis=2) + tail) / n, axis=1)
    low = means[:, int(0.025 * RESAMPLES)]
    high = means[:, int(0.975 * RESAMPLES) - 1]
    return [[float(a), float(b)] for a, b in zip(low, high)]


def summarize(losses, seed):
    out = {}
    n = len(losses["consistency"])
    for name, values in losses.items():
        out[name] = {"mean": sum(values) / n}
    others = [name for name in losses if name != "consistency"]
    diffs = [[a - b for a, b in zip(losses["consistency"], losses[other])] for other in others]
    intervals = {block: block_bootstrap_intervals(diffs, block, seed + block) for block in BLOCKS}
    for index, other in enumerate(others):
        entry = {"mean": sum(diffs[index]) / n}
        for block in BLOCKS:
            entry[f"ci95_block{block}"] = intervals[block][index]
        out[f"consistency-{other}"] = entry
    return out


def theorem2_report(model, data, losses_worst, f):
    """Rows whose training law gives positive mass to the true state and label."""
    supported, bound_total, violations = [], 0.0, 0
    for row, (s_full, t) in enumerate(data):
        s = model.restrict(s_full)
        c = model.joint.get((s, t), 0)
        if c > 0:
            supported.append(row)
            # Theorem 2 for the unsmoothed training law: loss <= -log p(s', t).
            bound = -math.log(c / model.n_rows)
            bound_total += bound
    n_sup = len(supported)
    supported_set = set(supported)
    unsupported = [row for row in range(len(data)) if row not in supported_set]
    mean = lambda rows: (sum(losses_worst["consistency"][r] for r in rows) / len(rows)) if rows else None
    return {
        "rows_with_training_support": n_sup,
        "fraction_without_training_support": 1 - n_sup / len(data),
        "mean_bound_on_supported_rows": bound_total / n_sup if n_sup else None,
        "mean_worst_case_consistency_loss_supported": mean(supported),
        "mean_worst_case_consistency_loss_unsupported": mean(unsupported),
    }


def cumulative_hamming(data, keep, f):
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
            for q in range(i, j + 1):
                r[order[q]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def analysis(train, evaluation, keep, label):
    model = Model(train, keep)
    result = {
        "sensors": [ALL_SENSORS[i] for i in keep],
        "training_profile": {str(f): cumulative_hamming(train, keep, f) for f in range(len(keep))},
        "training_mi": mutual_information(train, keep),
        "recordings": {},
    }
    for split_index, (split, data) in enumerate(evaluation.items()):
        clean_states = [model.restrict(s) for s, _ in data]
        diagnostics = {
            "rows": len(data),
            "occupied_fraction": sum(t for _, t in data) / len(data),
            "fraction_clean_states_unseen_in_training":
                sum(1 for s in clean_states if model.states.get(s, 0) == 0) / len(data),
        }
        conditions = {}
        for f in (1, 2):
            for k in (0, 1, 2):
                kinds = ["none"] if k == 0 else ["random", "stuck"]
                for kind in kinds:
                    seed = SEED + 1000 * split_index + 97 * f + 13 * k + {"none": 0, "random": 1, "stuck": 2}[kind]
                    losses = per_row_losses(model, data, f, k, kind, seed)
                    conditions[f"f={f},k={k},{kind}"] = summarize(losses, seed + 5)
            seed = SEED + 1000 * split_index + 97 * f + 3
            worst = per_row_losses(model, data, f, f, "worst", seed)
            conditions[f"f={f},k={f},worst"] = summarize(worst, seed + 5)
            conditions[f"f={f},k={f},worst"]["theorem2"] = theorem2_report(model, data, worst, f)
        # Expected loss when only a fraction rho of rows is faulted (random faults, k = f).
        partial = {}
        for f in (1, 2):
            clean = conditions[f"f={f},k=0,none"]
            faulted = conditions[f"f={f},k={f},random"]
            for other in ("oblivious", "oblivious_backoff", "subset_ensemble", "single_average", "prior"):
                gap_clean = clean[f"consistency-{other}"]["mean"]
                gap_fault = faulted[f"consistency-{other}"]["mean"]
                entry = {f"rho={rho}": (1 - rho) * gap_clean + rho * gap_fault for rho in RHOS}
                entry["break_even_rho"] = (gap_clean / (gap_clean - gap_fault)
                                           if gap_clean > 0 and gap_fault < 0 else None)
                partial[f"f={f}: consistency-{other}"] = entry
        result["recordings"][split] = {"diagnostics": diagnostics, "conditions": conditions,
                                       "partial_fault_rate": partial}
    return result


def main(directory):
    d = Path(directory)
    raw = {k: load(d, name, digest) for k, (name, digest) in FILES.items()}
    edges = fit_edges(raw["training"])
    encoded = {k: encode(v, edges) for k, v in raw.items()}
    data = {k: v[0] for k, v in encoded.items()}
    evaluation = {"test": data["test"], "test2": data["test2"]}
    train = data["training"]
    result = {
        "schema": "pid-rs.fault-tolerant-shared-exclusions-experiment.v3",
        "bins": BINS, "seed": SEED, "injection_seeds": INJECTION_SEEDS,
        "block_lengths_rows": list(BLOCKS), "bootstrap_resamples": RESAMPLES,
        "training_occupied_fraction": sum(t for _, t in train) / len(train),
        "clamped_values": {k: v[1] for k, v in encoded.items()},
        "humidity_ratio_given_temperature_humidity_training_nats": None,
    }
    # Conditional entropy of the humidity-ratio level given the temperature and humidity levels.
    joint = Counter((s[0], s[1], s[4]) for s, _ in train)
    pair = Counter((s[0], s[1]) for s, _ in train)
    n = len(train)
    result["humidity_ratio_given_temperature_humidity_training_nats"] = -sum(
        c / n * math.log(c / pair[(a, b)]) for (a, b, _), c in joint.items())
    hr = Counter(s[4] for s, _ in train)
    result["humidity_ratio_entropy_training_nats"] = -sum(c / n * math.log(c / n) for c in hr.values())
    result["primary_four_physical_sensors"] = analysis(train, evaluation, PHYSICAL, "four")
    result["secondary_five_sensors"] = analysis(train, evaluation, EVERY, "five")

    subsets = []
    for keep in itertools.combinations(EVERY, 3):
        sub = Model(train, keep)
        row = {
            "sensors": [ALL_SENSORS[i] for i in keep],
            "training_mi": mutual_information(train, keep),
            "training_ft1": cumulative_hamming(train, keep, 1),
            "training_ft2": cumulative_hamming(train, keep, 2),
            "training_min_mi_after_one_erasure": min(
                mutual_information(train, tuple(j for j in keep if j != i)) for i in keep),
        }
        for split, rows in evaluation.items():
            for kind, k in (("none", 0), ("random", 1), ("worst", 1)):
                losses = per_row_losses(sub, rows, 1, k, kind, SEED + 31)
                row[f"{split}/{kind}"] = {name: sum(v) / len(v) for name, v in losses.items()}
        subsets.append(row)
    result["three_sensor_subsets"] = subsets
    correlations = {}
    for split in evaluation:
        for criterion in ("training_mi", "training_ft1", "training_ft2", "training_min_mi_after_one_erasure"):
            for kind, name in (("none", "oblivious"), ("none", "consistency"), ("random", "oblivious"),
                               ("random", "consistency"), ("worst", "oblivious"), ("worst", "consistency")):
                x = [r[criterion] for r in subsets]
                y = [-r[f"{split}/{kind}"][name] for r in subsets]
                correlations[f"{split}: {criterion} vs -{kind}/{name} loss"] = spearman(x, y)
    result["spearman_rank_correlations_over_10_subsets"] = correlations
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
